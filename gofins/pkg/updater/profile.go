package updater

import (
	"context"
	"sync"
	"time"

	"github.com/flocko-motion/gofins/pkg/db"
	"github.com/flocko-motion/gofins/pkg/f"
	"github.com/flocko-motion/gofins/pkg/fmp"
	"github.com/flocko-motion/gofins/pkg/types"
)

const (
	ProfileUpdateInterval = 30 * 24 * time.Hour
	ProfileWorkers        = 8
	ProfileBatchSize      = 200
)

func UpdateProfiles(ctx context.Context) {
	log := NewLogger("Profile")

	totalStale, err := db.Db().CountStaleProfiles()
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

		tickers, err := db.Db().GetStaleProfiles(ProfileBatchSize)
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

		currentStale, _ := db.Db().CountStaleProfiles()
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
					result := updateProfile(ticker)
					statsMu.Lock()
					switch result {
					case types.StatusOK:
						stats.Updated = append(stats.Updated, ticker)
					case types.StatusNotFound:
						stats.NotFound = append(stats.NotFound, ticker)
					case types.StatusFailed:
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
		currentStale, _ = db.Db().CountStaleProfiles()
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

func updateProfile(ticker string) string {
	profile, err := fmp.Fmp().GetProfile(ticker)
	now := time.Now()

	if err != nil {
		if fmp.IsNotFoundError(err) {
			status := types.StatusNotFound
			db.Db().PutSymbol(&types.Symbol{
				Ticker:            ticker,
				LastProfileUpdate: &now,
				LastProfileStatus: &status,
			})
			return types.StatusNotFound
		}
		status := types.StatusFailed
		db.Db().PutSymbol(&types.Symbol{
			Ticker:            ticker,
			LastProfileUpdate: &now,
			LastProfileStatus: &status,
		})
		return types.StatusFailed
	}

	var inception *time.Time
	if profile.IPODate != "" {
		if t, err := time.Parse("2006-01-02", profile.IPODate); err == nil {
			inception = &t
		}
	}

	// Detect secondary listings by comparing exchange with primary listing
	symbolType := deriveType(profile)

	symbol := &types.Symbol{
		Ticker:            ticker,
		Name:              f.Ptr(profile.CompanyName),
		Exchange:          f.Ptr(profile.Exchange),
		Type:              f.Ptr(symbolType),
		Sector:            f.Ptr(profile.Sector),
		Industry:          f.Ptr(profile.Industry),
		Country:           f.Ptr(profile.Country),
		Description:       f.Ptr(profile.Description),
		Website:           f.Ptr(profile.Website),
		Inception:         inception,
		LastProfileUpdate: f.Ptr(now),
		LastProfileStatus: f.Ptr(types.StatusOK),
		IsActivelyTrading: f.Ptr(profile.IsActivelyTrading),
		MarketCap:         f.Ptr(int64(profile.MarketCap)), // Convert float64 to int64
	}

	if err := db.Db().PutSymbol(symbol); err != nil {
		failStatus := types.StatusFailed
		db.Db().PutSymbol(&types.Symbol{
			Ticker:            ticker,
			LastProfileUpdate: &now,
			LastProfileStatus: &failStatus,
		})
		return types.StatusFailed
	}

	return types.StatusOK
}

func deriveType(profile *fmp.Profile) string {
	if profile.IsEtf {
		return types.TypeETF
	}
	if profile.IsFund {
		return types.TypeFund
	}
	if profile.IsAdr {
		return types.TypeADR
	}

	// Check if this is a secondary listing by comparing with primary exchange
	if profile.CIK != "" {
		primaryProfile, err := fmp.Fmp().GetProfileByCIK(profile.CIK)
		if err == nil && primaryProfile.Exchange != profile.Exchange {
			// Different exchange than primary = secondary listing
			return types.TypeSecondary
		}
	}

	return types.TypeStock
}
