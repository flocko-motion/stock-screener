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
	ProfileBatchSize      = 50
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

	// Calculate ETA
	var eta string
	if rate > 0 {
		etaSeconds := float64(currentStale) / rate
		eta = formatDuration(time.Duration(etaSeconds * float64(time.Second)))
	} else {
		eta = "unknown"
	}

	fmt.Printf("Fetched %d profiles | ✓ %d\t❌ %d\t⚠️  %d | %d left\t| %.1f/s\t| ETA %s\n",
		total,
		len(stats.Updated),
		len(stats.NotFound),
		len(stats.Failed),
		elapsed.Seconds(),
		rate,
		currentStale,
		eta)

	if len(stats.NotFound) > 0 && len(stats.NotFound) <= 10 {
		fmt.Printf("  Not found: %v\n", stats.NotFound)
	}
	if len(stats.Failed) > 0 && len(stats.Failed) <= 10 {
		fmt.Printf("  Failed: %v\n", stats.Failed)
	}
}

func formatDuration(d time.Duration) string {
	days := int(d.Hours() / 24)
	hours := int(d.Hours()) % 24
	minutes := int(d.Minutes()) % 60
	seconds := int(d.Seconds()) % 60

	if days > 0 {
		return fmt.Sprintf("%dd %dh %dm %ds", days, hours, minutes, seconds)
	}
	if hours > 0 {
		return fmt.Sprintf("%dh %dm %ds", hours, minutes, seconds)
	}
	if minutes > 0 {
		return fmt.Sprintf("%dm %ds", minutes, seconds)
	}
	return fmt.Sprintf("%ds", seconds)
}
