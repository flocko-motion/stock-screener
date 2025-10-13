package analysis

import (
	"fmt"
	"path/filepath"
	"sync"

	"github.com/flocko-motion/gofins/pkg/db"
)

// SymbolStats contains YoY statistics for a single symbol
type SymbolStats struct {
	Ticker string
	Stats  Stats
}

// AnalyzeBatch performs YoY analysis on multiple symbols using batch query
// Returns statistics for each symbol that has YoY data
func AnalyzeBatch(database *db.DB, config AnalysisPackageConfig) ([]SymbolStats, error) {
	// Fetch all prices in a single batch query
	pricesMap, err := database.GetPricesBatch(config.Tickers, config.TimeFrom, config.TimeTo, config.Interval)
	if err != nil {
		return nil, err
	}

	// Analyze each symbol in parallel
	var mu sync.Mutex
	var wg sync.WaitGroup
	results := make([]SymbolStats, 0, len(config.Tickers))
	processed := 0
	for _, ticker := range config.Tickers {
		ticker := ticker // Capture for goroutine
		prices, ok := pricesMap[ticker]
		if !ok || len(prices) == 0 {
			continue
		}

		wg.Add(1)
		go func() {
			defer wg.Done()

			stats := AnalyzeYoY(prices, config.HistConfig)

			mu.Lock()
			processed++
			currentProcessed := processed
			mu.Unlock()

			// Only include symbols with YoY data
			if stats.Count > 0 {
				if config.PathPlots != "" {
					if err = PlotYoYAnalysis(ticker, prices, stats, filepath.Join(config.PathPlots, fmt.Sprintf("%s_%s.png", ticker, PlotTypeChart))); err != nil {
						logf("%s ERROR: Failed to generate plot: %v\n", config.PackageID, err)
					}
					if err = PlotHistogram(ticker, stats, filepath.Join(config.PathPlots, fmt.Sprintf("%s_%s.png", ticker, PlotTypeHistogram))); err != nil {
						logf("%s ERROR: Failed to generate histogram: %v\n", config.PackageID, err)
					}
				}

				mu.Lock()
				results = append(results, SymbolStats{
					Ticker: ticker,
					Stats:  stats,
				})
				mu.Unlock()
			}

			// Progress reporting every 100 symbols
			if currentProcessed%100 == 0 {
				mu.Lock()
				logf("%s Progress: %d/%d processed, %d with YoY data (%.1f%%)\n",
					config.PackageID,
					currentProcessed, len(config.Tickers), len(results), float64(currentProcessed)/float64(len(config.Tickers))*100)
				mu.Unlock()
			}
		}()
	}

	wg.Wait()

	logf("%s Batch analysis complete: %d/%d symbols with YoY data\n", config.PackageID, len(results), len(config.Tickers))

	return results, nil
}
