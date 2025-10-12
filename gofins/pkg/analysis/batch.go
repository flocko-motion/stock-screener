package analysis

import (
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
func AnalyzeBatch(database *db.DB, tickers []string, from, to time.Time, interval db.PriceInterval, histConfig HistogramConfig) ([]SymbolStats, error) {
	// Fetch all prices in a single batch query
	pricesMap, err := database.GetPricesBatch(tickers, from, to, interval)
	if err != nil {
		return nil, err
	}

	// Analyze each symbol in parallel
	var mu sync.Mutex
	var wg sync.WaitGroup
	results := make([]SymbolStats, 0, len(tickers))

	for _, ticker := range tickers {
		ticker := ticker // Capture for goroutine
		prices, ok := pricesMap[ticker]
		if !ok || len(prices) == 0 {
			continue
		}

		wg.Add(1)
		go func() {
			defer wg.Done()

			stats := AnalyzeYoY(prices, histConfig)

			// Only include symbols with YoY data
			if stats.Count > 0 {
				mu.Lock()
				results = append(results, SymbolStats{
					Ticker: ticker,
					Stats:  stats,
				})
				mu.Unlock()
			}
		}()
	}

	wg.Wait()

	return results, nil
}
