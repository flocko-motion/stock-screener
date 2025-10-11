package updater

import (
	"context"
	"fmt"
	"sync"
	"time"

	"github.com/flocko-motion/gofins/pkg/db"
	"github.com/flocko-motion/gofins/pkg/fmp"
)

const (
	ProfileUpdateInterval = 30 * 24 * time.Hour
	ProfileWorkers        = 3
	ProfileBatchSize      = ProfileWorkers * 3
)

func UpdateProfiles(ctx context.Context, database *db.DB, fmpClient *fmp.Client) {
	threshold := time.Now().Add(-ProfileUpdateInterval)

	// Get initial count
	totalStale, err := database.CountStaleProfiles(threshold)
	if err != nil {
		fmt.Printf("✗ Failed to count stale profiles: %v\n", err)
		return
	}

	fmt.Printf("Profile updater started: %d stale profiles, %d workers\n", totalStale, ProfileWorkers)

	for {
		select {
		case <-ctx.Done():
			fmt.Println("Profile updater stopped")
			return
		default:
		}

		tickers, err := database.GetStaleProfiles(ProfileBatchSize, threshold)
		if err != nil {
			fmt.Printf("✗ Failed to get stale profiles: %v\n", err)
			return
		}

		if len(tickers) == 0 {
			fmt.Println("✓ All profiles up to date!")
			time.Sleep(time.Minute)
			continue
		}

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
		currentStale, _ := database.CountStaleProfiles(threshold)
		printStats(stats, elapsed, currentStale)
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
			// Mark as attempted so we don't retry constantly
			database.PutSymbol(&db.Symbol{
				Ticker:            ticker,
				LastProfileUpdate: &now,
			})
			return "not_found"
		}
		return "failed"
	}

	var inception *time.Time
	if profile.IPODate != "" {
		if t, err := time.Parse("2006-01-02", profile.IPODate); err == nil {
			inception = &t
		}
	}

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
	}

	if err := database.PutSymbol(symbol); err != nil {
		return "failed"
	}

	return "updated"
}

func printStats(stats *UpdateStats, elapsed time.Duration, currentStale int) {
	total := len(stats.Updated) + len(stats.NotFound) + len(stats.Failed)
	rate := float64(total) / elapsed.Seconds()

	fmt.Printf("Fetched %d profiles | ✓ %d good\t✗ %d not-found\t✗ %d failed | %.1fs (%.1f/s) | %d remaining\n",
		total,
		len(stats.Updated),
		len(stats.NotFound),
		len(stats.Failed),
		elapsed.Seconds(),
		rate, currentStale)

	if len(stats.NotFound) > 0 && len(stats.NotFound) <= 10 {
		fmt.Printf("  Not found: %v\n", stats.NotFound)
	}
	if len(stats.Failed) > 0 && len(stats.Failed) <= 10 {
		fmt.Printf("  Failed: %v\n", stats.Failed)
	}
}
