package updater

import (
	"context"
	"fmt"
	"sort"
	"sync"
	"time"

	"github.com/flocko-motion/gofins/pkg/db"
	"github.com/flocko-motion/gofins/pkg/fmp"
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

		tickers, err := database.GetStalePrices(PriceBatchSize)
		if err != nil {
			log.Error("Failed to get stale prices: %v\n", err)
			return
		}

		if len(tickers) == 0 {
			const sleepTimeHours = 8
			log.AllDone(sleepTimeHours)
			time.Sleep(time.Duration(sleepTimeHours) * time.Hour)
			continue
		}

		currentStale, _ := database.CountStalePrices()
		log.Batch(currentStale, len(tickers))

		startTime := time.Now()
		var statsMu sync.Mutex
		stats := &PriceStats{
			Updated:  make([]string, 0),
			NotFound: make([]string, 0),
			Failed:   make([]string, 0),
		}

		// Worker pool
		tickerChan := make(chan string, len(tickers))
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

		for _, ticker := range tickers {
			tickerChan <- ticker
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
			database.PutSymbol(&db.Symbol{
				Ticker:          ticker,
				LastPriceUpdate: &now,
				LastPriceStatus: &status,
			})
			return StatusNotFound
		}
		status := StatusFailed
		database.PutSymbol(&db.Symbol{
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
	monthly, weekly := convertPrices(dailyPrices, ticker)

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
	database.PutSymbol(&db.Symbol{
		Ticker:          ticker,
		LastPriceUpdate: &now,
		LastPriceStatus: &status,
		OldestPrice:     oldestPrice,
	})

	return StatusOK
}

func convertPrices(dailyPrices []fmp.DailyPrice, ticker string) ([]db.PriceData, []db.PriceData) {
	if len(dailyPrices) == 0 {
		return nil, nil
	}

	var monthly []db.PriceData
	var weekly []db.PriceData
	monthlyYoY := make(map[string]float64) // Store monthly closes for YoY calculation
	weeklyYoY := make(map[string]float64)  // Store weekly closes for YoY calculation

	var currentMonth, currentWeek time.Time
	var monthData, weekData aggregator

	for _, daily := range dailyPrices {
		date, err := time.Parse("2006-01-02", daily.Date)
		if err != nil {
			continue
		}

		// Monthly aggregation
		monthStart := time.Date(date.Year(), date.Month(), 1, 0, 0, 0, 0, time.UTC)
		if currentMonth.IsZero() || !monthStart.Equal(currentMonth) {
			if !currentMonth.IsZero() {
				monthly = append(monthly, monthData.toMonthly(currentMonth, ticker, monthlyYoY))
			}
			currentMonth = monthStart
			monthData = aggregator{}
		}
		monthData.add(daily.Open, daily.High, daily.Low, daily.Close)

		// Weekly aggregation (Monday-Sunday)
		weekStart := startOfWeek(date)
		if currentWeek.IsZero() || !weekStart.Equal(currentWeek) {
			if !currentWeek.IsZero() {
				weekly = append(weekly, weekData.toWeekly(currentWeek, ticker, weeklyYoY))
			}
			currentWeek = weekStart
			weekData = aggregator{}
		}
		weekData.add(daily.Open, daily.High, daily.Low, daily.Close)
	}

	// Flush last periods
	if !currentMonth.IsZero() {
		monthly = append(monthly, monthData.toMonthly(currentMonth, ticker, monthlyYoY))
	}
	if !currentWeek.IsZero() {
		weekly = append(weekly, weekData.toWeekly(currentWeek, ticker, weeklyYoY))
	}

	return monthly, weekly
}

type aggregator struct {
	open     float64
	high     float64
	low      float64
	closeSum float64
	count    int
	close    float64
}

func (a *aggregator) add(open, high, low, close float64) {
	if a.count == 0 {
		a.open = open
		a.high = high
		a.low = low
	} else {
		if high > a.high {
			a.high = high
		}
		if low < a.low {
			a.low = low
		}
	}
	a.closeSum += close
	a.close = close
	a.count++
}

func (a *aggregator) toMonthly(date time.Time, ticker string, yoyMap map[string]float64) db.PriceData {
	avg := a.closeSum / float64(a.count)

	// Calculate YoY
	var yoy *float64
	key := fmt.Sprintf("%s-%d-%02d", ticker, date.Year(), date.Month())
	lastYearKey := fmt.Sprintf("%s-%d-%02d", ticker, date.Year()-1, date.Month())

	if lastYearClose, exists := yoyMap[lastYearKey]; exists && lastYearClose > 0 {
		yoyValue := ((a.close - lastYearClose) / lastYearClose) * 100
		yoy = &yoyValue
	}
	yoyMap[key] = a.close

	return db.PriceData{
		Date:         date,
		Open:         a.open,
		High:         a.high,
		Low:          a.low,
		Avg:          avg,
		Close:        a.close,
		YoY:          yoy,
		SymbolTicker: ticker,
	}
}

func (a *aggregator) toWeekly(date time.Time, ticker string, yoyMap map[string]float64) db.PriceData {
	avg := a.closeSum / float64(a.count)

	// Calculate YoY (52 weeks ago)
	var yoy *float64
	key := fmt.Sprintf("%s-%d-%02d-%02d", ticker, date.Year(), date.Month(), date.Day())

	// Find the date 52 weeks ago
	yearAgo := date.AddDate(0, 0, -364) // 52 weeks = 364 days
	lastYearKey := fmt.Sprintf("%s-%d-%02d-%02d", ticker, yearAgo.Year(), yearAgo.Month(), yearAgo.Day())

	if lastYearClose, exists := yoyMap[lastYearKey]; exists && lastYearClose > 0 {
		yoyValue := ((a.close - lastYearClose) / lastYearClose) * 100
		yoy = &yoyValue
	}
	yoyMap[key] = a.close

	return db.PriceData{
		Date:         date,
		Open:         a.open,
		High:         a.high,
		Low:          a.low,
		Avg:          avg,
		Close:        a.close,
		YoY:          yoy,
		SymbolTicker: ticker,
	}
}

func startOfWeek(date time.Time) time.Time {
	// Get Monday of the week
	weekday := int(date.Weekday())
	if weekday == 0 {
		weekday = 7 // Sunday = 7
	}
	return date.AddDate(0, 0, -(weekday - 1)).Truncate(24 * time.Hour)
}
