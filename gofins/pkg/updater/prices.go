package updater

import (
	"context"
	"fmt"
	"sort"
	"sync"
	"time"

	"github.com/flocko-motion/gofins/pkg/calculator"
	"github.com/flocko-motion/gofins/pkg/db"
	"github.com/flocko-motion/gofins/pkg/fmp"
	"github.com/flocko-motion/gofins/pkg/forex"
	"github.com/flocko-motion/gofins/pkg/log"
	"github.com/flocko-motion/gofins/pkg/types"
)

const (
	PriceUpdateInterval = 7 * 24 * time.Hour // Update weekly
)

type PriceUpdateConfig struct {
	Workers         int
	BatchSize       int
	WriteToDb       bool
	EnableProfiling bool
	MaxSymbols      int // 0 = unlimited
}

func DefaultPriceUpdateConfig() PriceUpdateConfig {
	return PriceUpdateConfig{
		Workers:         8,
		BatchSize:       200,
		WriteToDb:       true,
		EnableProfiling: false,
		MaxSymbols:      0,
	}
}

func TestPriceUpdateConfig() PriceUpdateConfig {
	return PriceUpdateConfig{
		Workers:         1,
		BatchSize:       10,
		WriteToDb:       false,
		EnableProfiling: true,
		MaxSymbols:      100,
	}
}

type PriceStats struct {
	Updated        []string
	NotFound       []string
	Failed         []string
	FailureReasons map[string]string // ticker -> error message
}

var (
	batchWriteMutex sync.Mutex
	writeJobCounter int
)

// batchWritePrices writes collected price data to database in background
// Blocks if another batch write is in progress, then runs in background
// Ensures only one background write happens at a time

func batchWritePrices(symbols []types.Symbol, monthly []types.PriceData, weekly []types.PriceData, config PriceUpdateConfig, log *log.Logger) {
	// Wait for any previous batch write to complete, then start new one
	// writeJob := writeJobCounter
	// writeJobCounter++
	// log.Printf("[PRICES BATCH WRITE %d] aquire lock \n", writeJob)
	batchWriteMutex.Lock()
	// log.Printf("[PRICES BATCH WRITE %d] lock acquired - starting write\n", writeJob)

	go func() {
		defer batchWriteMutex.Unlock()

		if len(symbols) == 0 {
			return // Empty call for shutdown sync
		}

		if !config.WriteToDb {
			return // Skip write in test mode
		}

		// startTime := time.Now()

		// Run all 3 writes concurrently for 3x speedup
		var wg sync.WaitGroup

		if len(monthly) > 0 {
			wg.Add(1)
			go func() {
				defer wg.Done()
				if err := db.PutMonthlyPrices(monthly); err != nil {
					log.Errorf("Failed to batch write monthly prices: %v\n", err)
				}
			}()
		}

		if len(weekly) > 0 {
			wg.Add(1)
			go func() {
				defer wg.Done()
				if err := db.PutWeeklyPrices(weekly); err != nil {
					log.Errorf("Failed to batch write weekly prices: %v\n", err)
				}
			}()
		}

		if len(symbols) > 0 {
			wg.Add(1)
			go func() {
				defer wg.Done()
				if err := db.PutSymbols(symbols); err != nil {
					log.Errorf("Failed to batch write symbols: %v\n", err)
				}
			}()
		}

		wg.Wait()
		// duration := time.Since(startTime)
		// log.Printf("batch write #%d: %d symbols, %d monthly, %d weekly in %v\n",
		// writeJob, len(symbols), len(monthly), len(weekly), duration)
	}()
}

func UpdatePrices(ctx context.Context) {
	log := NewLogger("Prices")
	config := DefaultPriceUpdateConfig()

	for {
		select {
		case <-ctx.Done():
			log.Stopped()
			return
		default:
		}

		if err := updatePricesImpl(log, config); err != nil {
			log.Errorf("Price update failed: %v\n", err)
		}

		const sleepTimeHours = 8
		log.AllDone(sleepTimeHours)
		time.Sleep(time.Duration(sleepTimeHours) * time.Hour)
	}
}

func UpdatePricesOnce() error {
	log := NewLogger("Prices")
	config := DefaultPriceUpdateConfig()
	return updatePricesImpl(log, config)
}

func updatePricesImpl(log *log.Logger, config PriceUpdateConfig) error {
	// Ensure last batch write completes before exit
	defer batchWritePrices(nil, nil, nil, config, log)

	totalStale, err := db.CountStalePrices()
	if err != nil {
		return err
	}

	log.Started(totalStale, config.Workers)

	processedCount := 0

	for {
		batchSize := config.BatchSize
		if config.MaxSymbols > 0 && processedCount+batchSize > config.MaxSymbols {
			batchSize = config.MaxSymbols - processedCount
			if batchSize <= 0 {
				log.Printf("Reached max symbols limit (%d)\n", config.MaxSymbols)
				return nil
			}
		}

		symbols, err := db.GetSymbolsWithStalePrices(batchSize)
		if err != nil {
			return err
		}

		if len(symbols) == 0 {
			return nil
		}

		currentStale, _ := db.CountStalePrices()
		log.Batch(currentStale, len(symbols))

		startTime := time.Now()
		var statsMu sync.Mutex
		stats := &PriceStats{
			Updated:        make([]string, 0),
			NotFound:       make([]string, 0),
			Failed:         make([]string, 0),
			FailureReasons: make(map[string]string),
		}

		// Collect results for batch writing
		var resultsMu sync.Mutex
		updatedSymbols := make([]types.Symbol, 0)
		monthlyPrices := make([]types.PriceData, 0)
		weeklyPrices := make([]types.PriceData, 0)

		// Worker pool
		symbolChan := make(chan types.Symbol, len(symbols))
		var wg sync.WaitGroup

		// log.Printf("  starting next cycle with %d workers\n", config.Workers)
		for i := 0; i < config.Workers; i++ {
			wg.Add(1)
			go func() {
				defer wg.Done()
				for symbol := range symbolChan {
					// Process with WriteToDb=false to collect data
					workerConfig := config
					workerConfig.WriteToDb = false
					updatedSymbol, monthly, weekly, err := updatePrices(symbol, workerConfig, log)

					statsMu.Lock()
					if updatedSymbol.LastPriceStatus != nil {
						switch *updatedSymbol.LastPriceStatus {
						case types.StatusOK:
							stats.Updated = append(stats.Updated, symbol.Ticker)
						case types.StatusNotFound:
							stats.NotFound = append(stats.NotFound, symbol.Ticker)
						case types.StatusFailed:
							stats.Failed = append(stats.Failed, symbol.Ticker)
							if err != nil {
								stats.FailureReasons[symbol.Ticker] = err.Error()
							}
						}
					}
					statsMu.Unlock()

					// Collect results for batch write (always collect, even in tests)
					if updatedSymbol.LastPriceStatus != nil && *updatedSymbol.LastPriceStatus == types.StatusOK {
						resultsMu.Lock()
						updatedSymbols = append(updatedSymbols, updatedSymbol)
						monthlyPrices = append(monthlyPrices, monthly...)
						weeklyPrices = append(weeklyPrices, weekly...)
						resultsMu.Unlock()
					}
				}
			}()
		}

		for _, symbol := range symbols {
			symbolChan <- symbol
		}
		close(symbolChan)

		wg.Wait()

		// Batch write all results in background
		if len(updatedSymbols) > 0 {
			batchWritePrices(updatedSymbols, monthlyPrices, weeklyPrices, config, log)
		}
		// log.Printf("  cycle completed - now writing in db\n")

		processedCount += len(symbols)

		elapsed := time.Since(startTime)
		currentStale, _ = db.CountStalePrices()
		log.Stats(len(stats.Updated), len(stats.NotFound), len(stats.Failed), currentStale, elapsed)
		log.NotFoundList(stats.NotFound)
		log.FailedList(stats.Failed)

		// Show sample failure reasons if there are failures
		if len(stats.FailureReasons) > 0 && len(stats.FailureReasons) <= 5 {
			for ticker, reason := range stats.FailureReasons {
				log.Warnf("%s: %s\n", ticker, reason)
			}
		} else if len(stats.FailureReasons) > 5 {
			// Show first 5 failures
			count := 0
			for ticker, reason := range stats.FailureReasons {
				if count >= 5 {
					break
				}
				log.Warnf("%s: %s\n", ticker, reason)
				count++
			}
			log.Warnf("... and %d more failures\n", len(stats.FailureReasons)-5)
		}
	}
}

func updatePrices(symbol types.Symbol, config PriceUpdateConfig, log *log.Logger) (types.Symbol, []types.PriceData, []types.PriceData, error) {
	startTime := time.Now()

	dailyPrices, err := fmp.FetchPriceHistory(symbol.Ticker)
	fetchDuration := time.Since(startTime)

	now := time.Now()

	if err != nil {
		status := types.StatusFailed
		if fmp.IsNotFoundError(err) {
			status = types.StatusNotFound
		}

		symbol.LastPriceUpdate = &now
		symbol.LastPriceStatus = &status
		if config.WriteToDb {
			db.PutSymbols([]types.Symbol{symbol})
		}

		return symbol, nil, nil, err
	}

	// Sort by date
	sort.Slice(dailyPrices, func(i, j int) bool {
		return dailyPrices[i].Date < dailyPrices[j].Date
	})

	// Single-loop conversion: daily → weekly + monthly + YoY
	convertStart := time.Now()
	monthly, weekly := calculator.ConvertPrices(dailyPrices, symbol.Ticker)
	convertDuration := time.Since(convertStart)

	forexStart := time.Now()
	var forexDuration time.Duration
	if symbol.Currency != nil && *symbol.Currency != "USD" {
		monthly, weekly = convertForexPrices(monthly, weekly, *symbol.Currency)
		forexDuration = time.Since(forexStart)
	}

	// Parse oldest price date
	var oldestPrice *time.Time
	if len(dailyPrices) > 0 {
		if parsed, err := time.Parse("2006-01-02", dailyPrices[0].Date); err == nil {
			oldestPrice = &parsed
		}
	}

	// Calculate ATH12M (all-time high in last 12 months)
	var ath12m *float64
	if len(monthly) > 0 {
		twelveMonthsAgo := now.AddDate(0, -12, 0)
		maxPrice := 0.0
		for _, price := range monthly {
			if price.Date.After(twelveMonthsAgo) && price.High > maxPrice {
				maxPrice = price.High
			}
		}
		if maxPrice > 0 {
			ath12m = &maxPrice
		}
	}

	// Update symbol metadata
	status := types.StatusOK
	symbol.LastPriceUpdate = &now
	symbol.LastPriceStatus = &status
	symbol.OldestPrice = oldestPrice
	symbol.Ath12M = ath12m

	// Save to database (batch write happens at end of batch, not per symbol)
	if config.WriteToDb {
		if err := db.PutMonthlyPrices(monthly); err != nil {
			failStatus := types.StatusFailed
			symbol.LastPriceStatus = &failStatus
			db.PutSymbols([]types.Symbol{symbol})

			// Log foreign key violations as errors
			tickerInfo := symbol.Ticker
			if len(monthly) > 0 {
				tickerInfo = fmt.Sprintf("%s (price data has ticker: %s)", symbol.Ticker, monthly[0].SymbolTicker)
			}
			_ = db.LogError("updater.prices", "db_constraint_violation",
				fmt.Sprintf("Failed to insert monthly prices for %s: %v", tickerInfo, err), nil)

			return symbol, monthly, weekly, fmt.Errorf("failed to insert monthly prices: %w", err)
		}
		if err := db.PutWeeklyPrices(weekly); err != nil {
			failStatus := types.StatusFailed
			symbol.LastPriceStatus = &failStatus
			db.PutSymbols([]types.Symbol{symbol})

			// Log foreign key violations as errors
			_ = db.LogError("updater.prices", "db_constraint_violation",
				fmt.Sprintf("Failed to insert weekly prices for %s: %v", symbol.Ticker, err), nil)

			return symbol, monthly, weekly, fmt.Errorf("failed to insert weekly prices: %w", err)
		}
		db.PutSymbols([]types.Symbol{symbol})
	}

	totalDuration := time.Since(startTime)

	// Log timing breakdown if profiling enabled
	if config.EnableProfiling {
		log.Printf("[TIMING] %s: total=%v fetch=%v convert=%v forex=%v (monthly=%d weekly=%d)\n",
			symbol.Ticker, totalDuration, fetchDuration, convertDuration, forexDuration,
			len(monthly), len(weekly))
	}

	return symbol, monthly, weekly, nil
}

// convertForexPrices converts stock prices from a foreign currency to USD
func convertForexPrices(monthly, weekly []types.PriceData, currency string) ([]types.PriceData, []types.PriceData) {
	// Get forex data once (avoids 1488 mutex locks!)
	ts, err := forex.GetCachedForex(currency)
	if err != nil {
		// If we can't get forex data, return unconverted (better than failing)
		return monthly, weekly
	}

	convertedMonthly := make([]types.PriceData, len(monthly))
	insert := 0
	for _, price := range monthly {
		// Use pre-fetched forex data - no mutex lock!
		rate, err := forex.ConvertToUsdWithTimeSeries(1.0, ts, price.Date)
		if err != nil {
			// Skip this price if no forex data available
			continue
		}

		convertedMonthly[insert] = types.PriceData{
			Date:         price.Date,
			Open:         price.Open * rate,
			Close:        price.Close * rate,
			High:         price.High * rate,
			Low:          price.Low * rate,
			Avg:          price.Avg * rate,
			YoY:          price.YoY,          // Preserve YoY percentage
			SymbolTicker: price.SymbolTicker, // Preserve ticker
		}
		insert++
	}
	convertedMonthly = convertedMonthly[:insert]

	convertedWeekly := make([]types.PriceData, len(weekly))
	insert = 0
	for _, price := range weekly {
		// Use pre-fetched forex data - no mutex lock!
		rate, err := forex.ConvertToUsdWithTimeSeries(1.0, ts, price.Date)
		if err != nil {
			// Skip this price if no forex data available
			continue
		}

		convertedWeekly[insert] = types.PriceData{
			Date:         price.Date,
			Open:         price.Open * rate,
			Close:        price.Close * rate,
			High:         price.High * rate,
			Low:          price.Low * rate,
			Avg:          price.Avg * rate,
			YoY:          price.YoY,          // Preserve YoY percentage
			SymbolTicker: price.SymbolTicker, // Preserve ticker
		}
		insert++
	}
	convertedWeekly = convertedWeekly[:insert]

	return convertedMonthly, convertedWeekly
}
