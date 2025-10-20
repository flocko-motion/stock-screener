package updater

import (
	"context"
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
	Updated  []string
	NotFound []string
	Failed   []string
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
			Updated:  make([]string, 0),
			NotFound: make([]string, 0),
			Failed:   make([]string, 0),
		}

		// Worker pool
		symbolChan := make(chan types.Symbol, len(symbols))
		var wg sync.WaitGroup

		for i := 0; i < PriceWorkers; i++ {
			wg.Add(1)
			go func() {
				defer wg.Done()
				for symbol := range symbolChan {
					updatedSymbol, _, _ := updatePrices(symbol, false)
					statsMu.Lock()
					if updatedSymbol.LastPriceStatus != nil {
						switch *updatedSymbol.LastPriceStatus {
						case types.StatusOK:
							stats.Updated = append(stats.Updated, symbol.Ticker)
						case types.StatusNotFound:
							stats.NotFound = append(stats.NotFound, symbol.Ticker)
						case types.StatusFailed:
							stats.Failed = append(stats.Failed, symbol.Ticker)
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
	}
}

func updatePrices(symbol types.Symbol, testMode bool) (types.Symbol, []types.PriceData, []types.PriceData) {
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
			db.PutSymbol(&symbol)
		}

		return symbol, nil, nil
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

	// Update symbol metadata
	status := types.StatusOK
	symbol.LastPriceUpdate = &now
	symbol.LastPriceStatus = &status
	symbol.OldestPrice = oldestPrice

	// Save to database
	if !testMode {
		if err := db.PutMonthlyPrices(monthly); err != nil {
			failStatus := types.StatusFailed
			symbol.LastPriceStatus = &failStatus
			db.PutSymbol(&symbol)
			return symbol, monthly, weekly
		}
		if err := db.PutWeeklyPrices(weekly); err != nil {
			failStatus := types.StatusFailed
			symbol.LastPriceStatus = &failStatus
			db.PutSymbol(&symbol)
			return symbol, monthly, weekly
		}
		db.PutSymbol(&symbol)
	}

	return symbol, monthly, weekly
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
