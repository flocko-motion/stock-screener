package updater

import (
	"context"
	"fmt"
	"sort"
	"sync"
	"time"

	"github.com/flocko-motion/gofins/pkg/calculator"
	"github.com/flocko-motion/gofins/pkg/db"
	"github.com/flocko-motion/gofins/pkg/f"
	"github.com/flocko-motion/gofins/pkg/fmp"
	"github.com/flocko-motion/gofins/pkg/forex"
	"github.com/flocko-motion/gofins/pkg/types"
)

const (
	PriceUpdateInterval = 7 * 24 * time.Hour // Update weekly
	PriceWorkers        = 8
	PriceBatchSize      = 200
)

type PriceStats struct {
	Updated      []string
	NotFound     []string
	Failed       []string
	FailureReasons map[string]string // ticker -> error message
}

func UpdatePrices(ctx context.Context) {
	log := NewLogger("Prices")

	for {
		select {
		case <-ctx.Done():
			log.Stopped()
			return
		default:
		}

		if err := updatePricesImpl(log); err != nil {
			log.Error("Price update failed: %v\n", err)
		}

		const sleepTimeHours = 8
		log.AllDone(sleepTimeHours)
		time.Sleep(time.Duration(sleepTimeHours) * time.Hour)
	}
}

func UpdatePricesOnce() error {
	log := NewLogger("Prices")
	return updatePricesImpl(log)
}

func updatePricesImpl(log *Logger) error {
	totalStale, err := db.CountStalePrices()
	if err != nil {
		return err
	}

	log.Started(totalStale, PriceWorkers)

	for {
		symbols, err := db.GetSymbolsWithStalePrices(PriceBatchSize)
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

		// Worker pool
		symbolChan := make(chan types.Symbol, len(symbols))
		var wg sync.WaitGroup

		for i := 0; i < PriceWorkers; i++ {
			wg.Add(1)
			go func() {
				defer wg.Done()
				for symbol := range symbolChan {
					updatedSymbol, _, _, err := updatePrices(symbol, false)
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
				}
			}()
		}

		for _, symbol := range symbols {
			symbolChan <- symbol
		}
		close(symbolChan)

		wg.Wait()

		elapsed := time.Since(startTime)
		currentStale, _ = db.CountStalePrices()
		log.Stats(len(stats.Updated), len(stats.NotFound), len(stats.Failed), currentStale, elapsed)
		log.NotFoundList(stats.NotFound)
		log.FailedList(stats.Failed)
		
		// Show sample failure reasons if there are failures
		if len(stats.FailureReasons) > 0 && len(stats.FailureReasons) <= 5 {
			for ticker, reason := range stats.FailureReasons {
				log.Printf("  ⚠️  %s: %s\n", ticker, reason)
			}
		} else if len(stats.FailureReasons) > 5 {
			// Show first 5 failures
			count := 0
			for ticker, reason := range stats.FailureReasons {
				if count >= 5 {
					break
				}
				log.Printf("  ⚠️  %s: %s\n", ticker, reason)
				count++
			}
			log.Printf("  ... and %d more failures\n", len(stats.FailureReasons)-5)
		}
	}
}

func updatePrices(symbol types.Symbol, testMode bool) (types.Symbol, []types.PriceData, []types.PriceData, error) {
	dailyPrices, err := fmp.FetchPriceHistory(symbol.Ticker)
	now := time.Now()

	if err != nil {
		status := types.StatusFailed
		if fmp.IsNotFoundError(err) {
			status = types.StatusNotFound
		}

		symbol.LastPriceUpdate = &now
		symbol.LastPriceStatus = &status
		if !testMode {
			db.PutSymbols([]types.Symbol{symbol})
		}

		return symbol, nil, nil, err
	}

	// Sort by date
	sort.Slice(dailyPrices, func(i, j int) bool {
		return dailyPrices[i].Date < dailyPrices[j].Date
	})

	// Single-loop conversion: daily → weekly + monthly + YoY
	monthly, weekly := calculator.ConvertPrices(dailyPrices, symbol.Ticker)
	if symbol.Currency != nil && *symbol.Currency != "USD" {
		monthly, weekly = convertForexPrices(monthly, weekly, *symbol.Currency)
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

	// Save to database
	if !testMode {
		if err := db.PutMonthlyPrices(monthly); err != nil {
			failStatus := types.StatusFailed
			symbol.LastPriceStatus = &failStatus
			db.PutSymbols([]types.Symbol{symbol})
			
			// Log foreign key violations as errors
			_ = db.LogError("updater.prices", "db_constraint_violation",
				fmt.Sprintf("Failed to insert monthly prices for %s: %v", symbol.Ticker, err), nil)
			
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

	return symbol, monthly, weekly, nil
}

// convertForexPrices converts stock prices from a foreign currency to USD
func convertForexPrices(monthly, weekly []types.PriceData, currency string) ([]types.PriceData, []types.PriceData) {
	convertedMonthly := make([]types.PriceData, len(monthly))
	for i, price := range monthly {
		convertedMonthly[i] = types.PriceData{
			Date:  price.Date,
			Open:  f.First(forex.ConvertToUsd(price.Open, currency, price.Date)),
			Close: f.First(forex.ConvertToUsd(price.Close, currency, price.Date)),
			High:  f.First(forex.ConvertToUsd(price.High, currency, price.Date)),
			Low:   f.First(forex.ConvertToUsd(price.Low, currency, price.Date)),
			Avg:   f.First(forex.ConvertToUsd(price.Avg, currency, price.Date)),
		}
	}

	convertedWeekly := make([]types.PriceData, len(weekly))
	for i, price := range weekly {
		convertedWeekly[i] = types.PriceData{
			Date:  price.Date,
			Open:  f.First(forex.ConvertToUsd(price.Open, currency, price.Date)),
			Close: f.First(forex.ConvertToUsd(price.Close, currency, price.Date)),
			High:  f.First(forex.ConvertToUsd(price.High, currency, price.Date)),
			Low:   f.First(forex.ConvertToUsd(price.Low, currency, price.Date)),
			Avg:   f.First(forex.ConvertToUsd(price.Avg, currency, price.Date)),
		}
	}

	return convertedMonthly, convertedWeekly
}
