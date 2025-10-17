package forex

import (
	"fmt"
	"sort"
	"sync"
	"time"

	"github.com/flocko-motion/gofins/pkg/calculator"
	"github.com/flocko-motion/gofins/pkg/fmp"
	"github.com/flocko-motion/gofins/pkg/types"
)

// ForexTimeSeries holds forex data for a currency pair
type ForexTimeSeries struct {
	Weekly        []types.PriceData
	Monthly       []types.PriceData
	LastFetchTime time.Time
}

var (
	globalCache     *cache
	globalCacheLock sync.Mutex
)

// cache manages in-memory forex data with lazy loading
type cache struct {
	mu        sync.RWMutex
	data      map[string]*ForexTimeSeries
	fmpClient *fmp.Client
}

// TimeFrom returns the earliest data point we have
func (ts *ForexTimeSeries) TimeFrom() time.Time {
	if len(ts.Weekly) > 0 {
		return ts.Weekly[0].Date
	}
	if len(ts.Monthly) > 0 {
		return ts.Monthly[0].Date
	}
	return time.Time{}
}

// TimeTo returns the latest data point we have
func (ts *ForexTimeSeries) TimeTo() time.Time {
	if len(ts.Weekly) > 0 {
		return ts.Weekly[len(ts.Weekly)-1].Date
	}
	if len(ts.Monthly) > 0 {
		return ts.Monthly[len(ts.Monthly)-1].Date
	}
	return time.Time{}
}

// initCache initializes the global cache on first use
func initCache() {
	globalCacheLock.Lock()
	defer globalCacheLock.Unlock()

	if globalCache == nil {
		fmpClient, err := fmp.NewClient(nil)
		if err != nil {
			panic(fmt.Sprintf("failed to initialize FMP client for forex: %v", err))
		}
		globalCache = &cache{
			data:      make(map[string]*ForexTimeSeries),
			fmpClient: fmpClient,
		}
	}
}

// GetUsdForex returns weekly and monthly forex rates for converting the given currency to USD
// Auto-initializes on first call. Data is cached in memory.
func GetUsdForex(timeFrom, timeTo time.Time, currency string) (weekly, monthly []types.PriceData, err error) {
	if currency == "" {
		return nil, nil, fmt.Errorf("currency cannot be empty")
	}

	if timeFrom.After(timeTo) {
		return nil, nil, fmt.Errorf("timeFrom (%s) must be before or equal to timeTo (%s)",
			timeFrom.Format("2006-01-02"), timeTo.Format("2006-01-02"))
	}

	return getUsdForex(timeFrom, timeTo, currency)
}

// ConvertToUsdWeekly converts an amount using weekly forex rate for the given date
func ConvertToUsdWeekly(amount float64, currency string, date time.Time) (float64, error) {
	if currency == "USD" {
		return amount, nil
	}

	weekly, _, err := GetUsdForex(date, date, currency)
	if err != nil || len(weekly) == 0 {
		return 0, fmt.Errorf("no weekly forex data for %s at %s: %w", currency, date.Format("2006-01-02"), err)
	}

	return amount * weekly[0].Close, nil
}

// ConvertToUsdMonthly converts an amount using monthly forex rate for the given date
func ConvertToUsdMonthly(amount float64, currency string, date time.Time) (float64, error) {
	if currency == "USD" {
		return amount, nil
	}

	_, monthly, err := GetUsdForex(date, date, currency)
	if err != nil || len(monthly) == 0 {
		return 0, fmt.Errorf("no monthly forex data for %s at %s: %w", currency, date.Format("2006-01-02"), err)
	}

	return amount * monthly[0].Close, nil
}

// getUsdForex returns weekly and monthly forex rates for the given currency
func getUsdForex(timeFrom, timeTo time.Time, currency string) (weekly, monthly []types.PriceData, err error) {
	if globalCache == nil {
		initCache()
	}

	globalCache.mu.Lock()
	defer globalCache.mu.Unlock()

	ts, exists := globalCache.data[currency]
	if !exists {
		if err := globalCache.fetchAndStore(currency); err != nil {
			return nil, nil, err
		}
		ts = globalCache.data[currency]
	}

	return filterDataPoints(ts.Weekly, timeFrom, timeTo), filterDataPoints(ts.Monthly, timeFrom, timeTo), nil
}

func (c *cache) fetchAndStore(currency string) error {
	symbol := fmt.Sprintf("%sUSD", currency)
	rawData, err := c.fmpClient.FetchForexHistory(symbol)
	if err != nil {
		return fmt.Errorf("failed to fetch forex data for %s: %w", symbol, err)
	}
	if len(rawData) == 0 {
		return fmt.Errorf("no forex data returned for %s", symbol)
	}

	ts, err := convertToTimeSeries(currency, rawData)
	if err != nil {
		return fmt.Errorf("failed to convert forex data: %w", err)
	}
	ts.LastFetchTime = time.Now()
	c.data[currency] = ts
	return nil
}

func convertToTimeSeries(currency string, rawData []fmp.PriceDataRaw) (*ForexTimeSeries, error) {
	if len(rawData) == 0 {
		return nil, fmt.Errorf("no data to convert")
	}

	sort.Slice(rawData, func(i, j int) bool {
		return rawData[i].Date < rawData[j].Date
	})

	monthlyData, weeklyData := calculator.ConvertPrices(rawData, currency)

	return &ForexTimeSeries{
		Weekly:  weeklyData,
		Monthly: monthlyData,
	}, nil
}

func filterDataPoints(points []types.PriceData, from, to time.Time) []types.PriceData {
	var filtered []types.PriceData
	for _, point := range points {
		if (point.Date.Equal(from) || point.Date.After(from)) && (point.Date.Equal(to) || point.Date.Before(to)) {
			filtered = append(filtered, point)
		}
	}
	return filtered
}
