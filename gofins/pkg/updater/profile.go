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
	ProfileBatchSize      = 100
	ProfileUpdateInterval = 30 * 24 * time.Hour
	ProfileWorkers        = 10
)

func UpdateProfiles(ctx context.Context, database *db.DB, fmpClient *fmp.Client) {
	threshold := time.Now().Add(-ProfileUpdateInterval)

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

		fmt.Printf("Updating %d profiles with %d workers...\n", len(tickers), ProfileWorkers)

		// Stats tracking
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
		printStats(stats)
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

func printStats(stats *UpdateStats) {
	fmt.Println("\n=== Batch Complete ===")
	fmt.Printf("✓ Updated:   %d\n", len(stats.Updated))
	fmt.Printf("✗ Not found: %d\n", len(stats.NotFound))
	fmt.Printf("✗ Failed:    %d\n", len(stats.Failed))

	if len(stats.NotFound) > 0 && len(stats.NotFound) <= 10 {
		fmt.Printf("  Not found: %v\n", stats.NotFound)
	}
	if len(stats.Failed) > 0 && len(stats.Failed) <= 10 {
		fmt.Printf("  Failed: %v\n", stats.Failed)
	}
	fmt.Println()
}
