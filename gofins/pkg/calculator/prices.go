package calculator

import (
	"fmt"
	"time"

	"github.com/flocko-motion/gofins/pkg/fmp"
	"github.com/flocko-motion/gofins/pkg/types"
)

// ConvertPrices converts daily prices to monthly and weekly aggregated data
func ConvertPrices(dailyPrices []fmp.PriceDataRaw, ticker string) (monthly, weekly []types.PriceData) {
	if len(dailyPrices) == 0 {
		return nil, nil
	}

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
		weekStart := StartOfWeek(date)
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

func (a *aggregator) toMonthly(date time.Time, ticker string, yoyMap map[string]float64) types.PriceData {
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

	return types.PriceData{
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

func (a *aggregator) toWeekly(date time.Time, ticker string, yoyMap map[string]float64) types.PriceData {
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

	return types.PriceData{
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

// StartOfWeek returns the Monday of the week for the given date in UTC
func StartOfWeek(date time.Time) time.Time {
	// Convert to UTC first to ensure consistent date handling
	date = date.UTC()
	// Get Monday of the week
	weekday := int(date.Weekday())
	if weekday == 0 {
		weekday = 7 // Sunday = 7
	}
	monday := date.AddDate(0, 0, -(weekday - 1))
	return time.Date(monday.Year(), monday.Month(), monday.Day(), 0, 0, 0, 0, time.UTC)
}

// StartOfMonth returns the first day of the month for the given date
func StartOfMonth(date time.Time) time.Time {
	return time.Date(date.Year(), date.Month(), 1, 0, 0, 0, 0, time.UTC)
}

func StartOfDay(date time.Time) time.Time {
	return time.Date(date.Year(), date.Month(), date.Day(), 0, 0, 0, 0, time.UTC)
}

// IsStartOfWeek returns true if the given date is a Monday (start of week)
func IsStartOfWeek(date time.Time) bool {
	return date.Weekday() == time.Monday
}

// IsStartOfMonth returns true if the given date is the 1st of the month
func IsStartOfMonth(date time.Time) bool {
	return date.Day() == 1
}

func Yesterday() time.Time {
	return StartOfDay(time.Now().AddDate(0, 0, -1))
}

// ConvertForexPrices converts forex data to a single time series map
// Takes first price of each period (no averaging needed for exchange rates)
// Returns map keyed by date (daily, week start Monday, or month start) for efficient lookups
func ConvertForexPrices(forexData []fmp.ForexData, currency string) (timeFrom time.Time, timeTo time.Time, data map[time.Time]types.PriceData) {
	if len(forexData) == 0 {
		return time.Time{}, time.Time{}, nil
	}

	data = make(map[time.Time]types.PriceData)

	for _, fx := range forexData {
		date, err := time.Parse("2006-01-02", fx.Date)
		if err != nil {
			continue
		}

		date = StartOfDay(date)

		if timeFrom.IsZero() || date.Before(timeFrom) {
			timeFrom = date
		}
		if date.After(timeTo) {
			timeTo = date
		}

		data[date] = types.PriceData{
			Date:         date,
			Close:        fx.Price,
			SymbolTicker: currency,
		}
	}

	return timeFrom, timeTo, data
}
