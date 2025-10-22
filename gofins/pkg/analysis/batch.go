package analysis

import (
	"encoding/json"
	"fmt"
	"path/filepath"
	"sync"
	"time"

	"github.com/flocko-motion/gofins/pkg/db"
)

// SymbolStats contains YoY statistics for a single symbol
type SymbolStats struct {
	Ticker string
	Stats  Stats
}

// AnalyzeBatch performs YoY analysis on multiple symbols using batch query
// Returns statistics for each symbol that has YoY data
func AnalyzeBatch(config AnalysisPackageConfig) ([]SymbolStats, error) {
	// Fetch all prices in a single batch query
	pricesMap, err := db.GetPricesBatch(config.Tickers, config.TimeFrom, config.TimeTo, config.Interval)
	if err != nil {
		return nil, err
	}

	// Analyze each symbol in parallel
	var mu sync.Mutex
	var wg sync.WaitGroup
	results := make([]SymbolStats, 0, len(config.Tickers))
	processed := 0
	totalTickers := len(config.Tickers)

	// Start a progress reporter goroutine
	progressTicker := time.NewTicker(2 * time.Second)
	defer progressTicker.Stop()

	go func() {
		for range progressTicker.C {
			mu.Lock()
			currentProcessed := processed
			currentResults := len(results)
			mu.Unlock()

			if currentProcessed > 0 {
				logf("%s Progress: %d/%d processed, %d results (%.1f%%)\n",
					config.PackageID,
					currentProcessed, totalTickers, currentResults, float64(currentProcessed)/float64(totalTickers)*100)
				
				// Update package status in database with current progress
				db.UpdateAnalysisPackageStatus(config.UserID, config.PackageID, "processing", currentResults)
			}
		}
	}()

	// Track rejection reasons
	rejectionReasons := make(map[string]int)
	var rejectionMu sync.Mutex

	for _, ticker := range config.Tickers {
		ticker := ticker // Capture for goroutine
		prices, ok := pricesMap[ticker]
		
		// Check rejection reasons
		var rejected bool
		var reason string
		
		if !ok {
			rejected = true
			reason = "no_price_data"
		} else if len(prices) == 0 {
			rejected = true
			reason = "empty_price_data"
		} else if prices[0].Date.After(config.TimeFrom.AddDate(1, 0, 0)) {
			rejected = true
			reason = "insufficient_history"
		}
		
		if rejected {
			rejectionMu.Lock()
			rejectionReasons[reason]++
			rejectionMu.Unlock()
			
			mu.Lock()
			processed++
			mu.Unlock()
			continue
		}

		wg.Add(1)
		go func() {
			defer wg.Done()

			stats := AnalyzeYoY(prices, config.HistConfig)

			// Only include symbols with YoY data
			if stats.Count > 0 {
				if config.PathPlots != "" {
					if err = PlotChart(ChartOptions{
						TimeFrom:   config.TimeFrom,
						TimeTo:     config.TimeTo,
						Ticker:     ticker,
						Prices:     prices,
						Stats:      stats,
						OutputPath: filepath.Join(config.PathPlots, fmt.Sprintf("%s_%s.png", ticker, PlotTypeChart)),
						LimitY:     true, // Default to limiting Y-axis
					}); err != nil {
						logf("%s ERROR: Failed to generate plot: %v\n", config.PackageID, err)
					}
					if err = PlotHistogram(ticker, stats, filepath.Join(config.PathPlots, fmt.Sprintf("%s_%s.png", ticker, PlotTypeHistogram))); err != nil {
						logf("%s ERROR: Failed to generate histogram: %v\n", config.PackageID, err)
					}
				}

				// Save to database immediately if requested
				if config.SaveToDB {
					histogramJSON, _ := json.Marshal(stats.Histogram)
					db.SaveAnalysisResult(
						config.UserID, config.PackageID, ticker,
						stats.Count, stats.Mean, stats.StdDev, stats.Variance,
						stats.Min, stats.Max, histogramJSON,
					)
				}

				mu.Lock()
				results = append(results, SymbolStats{
					Ticker: ticker,
					Stats:  stats,
				})
				mu.Unlock()
			}

			mu.Lock()
			processed++
			mu.Unlock()
		}()
	}

	wg.Wait()

	logf("%s Batch analysis complete: %d/%d symbols with YoY data\n", config.PackageID, len(results), len(config.Tickers))
	
	// Log rejection statistics
	totalRejected := 0
	for _, count := range rejectionReasons {
		totalRejected += count
	}
	if totalRejected > 0 {
		logf("%s Rejection summary: %d symbols rejected\n", config.PackageID, totalRejected)
		for reason, count := range rejectionReasons {
			percentage := float64(count) / float64(len(config.Tickers)) * 100
			logf("%s   - %s: %d (%.1f%%)\n", config.PackageID, reason, count, percentage)
		}
	}
	
	if config.SaveToDB {
		logf("%s All results saved to database\n", config.PackageID)
	}

	return results, nil
}
