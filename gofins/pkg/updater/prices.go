package updater

import (
	"context"
	"sort"
	"sync"
	"time"

	"github.com/flocko-motion/gofins/pkg/calculator"
	"github.com/flocko-motion/gofins/pkg/db"
	"github.com/flocko-motion/gofins/pkg/fmp"
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

func UpdatePrices(ctx context.Context, database *db.DB, fmpClient *fmp.Client) {
	log := NewLogger("Prices")

	totalStale, err := database.CountStalePrices()
	if err != nil {
		log.Error("Failed to count stale prices: %v\n", err)
		return
	}

	log.Started(totalStale, PriceWorkers)

	for {
		select {
		case <-ctx.Done():
			log.Stopped()
			return
		default:
		}

		symbols, err := database.GetSymbolsWithStalePrices(PriceBatchSize)
		if err != nil {
			log.Error("Failed to get stale prices: %v\n", err)
			return
		}

		if len(symbols) == 0 {
			const sleepTimeHours = 8
			log.AllDone(sleepTimeHours)
			time.Sleep(time.Duration(sleepTimeHours) * time.Hour)
			continue
		}

		currentStale, _ := database.CountStalePrices()
		log.Batch(currentStale, len(symbols))

		startTime := time.Now()
		var statsMu sync.Mutex
		stats := &PriceStats{
			Updated:  make([]string, 0),
			NotFound: make([]string, 0),
			Failed:   make([]string, 0),
		}

		// Worker pool
		tickerChan := make(chan string, len(symbols))
		var wg sync.WaitGroup

		for i := 0; i < PriceWorkers; i++ {
			wg.Add(1)
			go func() {
				defer wg.Done()
				for ticker := range tickerChan {
					result := updatePrices(ticker, database, fmpClient)
					statsMu.Lock()
					switch result {
					case StatusOK:
						stats.Updated = append(stats.Updated, ticker)
					case StatusNotFound:
						stats.NotFound = append(stats.NotFound, ticker)
					case StatusFailed:
						stats.Failed = append(stats.Failed, ticker)
					}
					statsMu.Unlock()
				}
			}()
		}

		for _, symbol := range symbols {
			tickerChan <- symbol.Ticker
		}
		close(tickerChan)

		wg.Wait()

		elapsed := time.Since(startTime)
		currentStale, _ = database.CountStalePrices()
		log.Stats(len(stats.Updated), len(stats.NotFound), len(stats.Failed), currentStale, elapsed)
		log.NotFoundList(stats.NotFound)
		log.FailedList(stats.Failed)
	}
}

func updatePrices(ticker string, database *db.DB, fmpClient *fmp.Client) string {
	dailyPrices, err := fmpClient.FetchPriceHistory(ticker)
	now := time.Now()

	if err != nil {
		if fmp.IsNotFoundError(err) {
			status := StatusNotFound
			database.PutSymbol(&types.Symbol{
				Ticker:          ticker,
				LastPriceUpdate: &now,
				LastPriceStatus: &status,
			})
			return StatusNotFound
		}
		status := StatusFailed
		database.PutSymbol(&types.Symbol{
			Ticker:          ticker,
			LastPriceUpdate: &now,
			LastPriceStatus: &status,
		})
		return StatusFailed
	}

	// Sort by date
	sort.Slice(dailyPrices, func(i, j int) bool {
		return dailyPrices[i].Date < dailyPrices[j].Date
	})

	// Single-loop conversion: daily → weekly + monthly + YoY
	monthly, weekly := calculator.ConvertPrices(dailyPrices, ticker)

	// Save to database
	if err := database.PutMonthlyPrices(monthly); err != nil {
		return StatusFailed
	}
	if err := database.PutWeeklyPrices(weekly); err != nil {
		return StatusFailed
	}

	// Parse oldest price date
	var oldestPrice *time.Time
	if len(dailyPrices) > 0 {
		if parsed, err := time.Parse("2006-01-02", dailyPrices[0].Date); err == nil {
			oldestPrice = &parsed
		}
	}

	// Update last_price_update timestamp and oldest_price
	status := StatusOK
	database.PutSymbol(&types.Symbol{
		Ticker:          ticker,
		LastPriceUpdate: &now,
		LastPriceStatus: &status,
		OldestPrice:     oldestPrice,
	})

	return StatusOK
}

