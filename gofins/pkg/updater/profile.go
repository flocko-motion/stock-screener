package updater

import (
	"context"
	"sync"
	"time"

	"github.com/flocko-motion/gofins/pkg/db"
	"github.com/flocko-motion/gofins/pkg/fmp"
)

const (
	ProfileUpdateInterval = 30 * 24 * time.Hour
	ProfileWorkers        = 3
	ProfileBatchSize      = 20
)

func UpdateProfiles(ctx context.Context, database *db.DB, fmpClient *fmp.Client) {
	log := NewLogger("Profile")

	totalStale, err := database.CountStaleProfiles(thresholdProfile())
	if err != nil {
		log.Error("Failed to count stale profiles: %v\n", err)
		return
	}

	log.Started(totalStale, ProfileWorkers)

	for {
		select {
		case <-ctx.Done():
			log.Stopped()
			return
		default:
		}

		tickers, err := database.GetStaleProfiles(ProfileBatchSize, thresholdProfile())
		if err != nil {
			log.Error("Failed to get stale profiles: %v\n", err)
			return
		}

		if len(tickers) == 0 {
			const sleepTimeHours = 8
			log.AllDone(sleepTimeHours)
			time.Sleep(time.Duration(sleepTimeHours) * time.Hour)
			continue
		}

		currentStale, _ := database.CountStaleProfiles(thresholdProfile())
		log.Batch(currentStale, len(tickers))

		// Stats tracking
		startTime := time.Now()
		var statsMu sync.Mutex
		stats := &UpdateStats{
			Updated:  make([]string, 0),
			NotFound: make([]string, 0),
			Failed:   make([]string, 0),
		}

		// Worker pool
		tickerChan := make(chan string, len(tickers))
		var wg sync.WaitGroup

		// Start workers
		for i := 0; i < ProfileWorkers; i++ {
			wg.Add(1)
			go func() {
				defer wg.Done()
				for ticker := range tickerChan {
					result := updateProfile(ticker, database, fmpClient)
					statsMu.Lock()
					switch result {
					case "updated":
						stats.Updated = append(stats.Updated, ticker)
					case "not_found":
						stats.NotFound = append(stats.NotFound, ticker)
					case "failed":
						stats.Failed = append(stats.Failed, ticker)
					}
					statsMu.Unlock()
				}
			}()
		}

		// Send tickers to workers
		for _, ticker := range tickers {
			tickerChan <- ticker
		}
		close(tickerChan)

		// Wait for all workers to finish
		wg.Wait()

		// Print stats
		elapsed := time.Since(startTime)
		currentStale, _ = database.CountStaleProfiles(thresholdProfile())
		log.Stats(len(stats.Updated), len(stats.NotFound), len(stats.Failed), currentStale, elapsed)
		log.NotFoundList(stats.NotFound)
		log.FailedList(stats.Failed)

	}
}

type UpdateStats struct {
	Updated  []string
	NotFound []string
	Failed   []string
}

func updateProfile(ticker string, database *db.DB, fmpClient *fmp.Client) string {
	profile, err := fmpClient.GetProfile(ticker)
	now := time.Now()

	if err != nil {
		if fmp.IsNotFoundError(err) {
			status := StatusNotFound
			database.PutSymbol(&db.Symbol{
				Ticker:            ticker,
				LastProfileUpdate: &now,
				LastProfileStatus: &status,
			})
			return StatusNotFound
		}
		status := StatusFailed
		database.PutSymbol(&db.Symbol{
			Ticker:            ticker,
			LastProfileUpdate: &now,
			LastProfileStatus: &status,
		})
		return StatusFailed
	}

	var inception *time.Time
	if profile.IPODate != "" {
		if t, err := time.Parse("2006-01-02", profile.IPODate); err == nil {
			inception = &t
		}
	}

	status := StatusOK
	symbol := &db.Symbol{
		Ticker:            ticker,
		Name:              &profile.CompanyName,
		Exchange:          &profile.Exchange,
		Sector:            &profile.Sector,
		Industry:          &profile.Industry,
		Country:           &profile.Country,
		Description:       &profile.Description,
		Website:           &profile.Website,
		Inception:         inception,
		LastProfileUpdate: &now,
		LastProfileStatus: &status,
	}

	if err := database.PutSymbol(symbol); err != nil {
		failStatus := StatusFailed
		database.PutSymbol(&db.Symbol{
			Ticker:            ticker,
			LastProfileUpdate: &now,
			LastProfileStatus: &failStatus,
		})
		return StatusFailed
	}

	return StatusOK
}
