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

var (
	globalCache     *cache
	globalCacheLock sync.Mutex
)

// cache manages in-memory forex data with lazy loading
type cache struct {
	mu   sync.RWMutex
	data map[string]*ForexTimeSeries // key: currency code (e.g., "EUR")
}

// initCache initializes the global cache on first use
func initCache() {
	globalCacheLock.Lock()
	defer globalCacheLock.Unlock()

	if globalCache == nil {
		globalCache = &cache{
			data: make(map[string]*ForexTimeSeries),
		}
	}
}

// getUsdForex returns weekly and monthly forex rates for the given currency
// Internal function that works with the global cache
func getUsdForex(timeFrom, timeTo time.Time, currency string) (weekly, monthly []types.PriceData, err error) {
	if globalCache == nil {
		initCache()
	}

	globalCache.mu.Lock()
	defer globalCache.mu.Unlock()

	// Check if we have cached data
	ts, exists := globalCache.data[currency]

	needsFetch := false
	if !exists {
		needsFetch = true
	} else {
		// Check if cached data covers the requested range
		if timeFrom.Before(ts.TimeFrom()) || timeTo.After(ts.TimeTo()) {
			// Check if we already fetched today
			today := time.Now().Truncate(24 * time.Hour)
			lastFetchDay := ts.LastFetchTime.Truncate(24 * time.Hour)

			if !lastFetchDay.Equal(today) {
				needsFetch = true
			}
			// If we fetched today but still don't have the range, return what we have
		}
	}

	if needsFetch {
		if err := globalCache.fetchAndStore(currency); err != nil {
			// If we have some data, return it with the error
			if exists {
				return ts.Weekly, ts.Monthly, fmt.Errorf("partial data available, fetch failed: %w", err)
			}
			return nil, nil, err
		}
		ts = globalCache.data[currency]
	}

	return ts.Weekly, ts.Monthly, nil
}

// fetchAndStore fetches forex data from the API and stores it in cache
func (c *cache) fetchAndStore(currency string) error {
	symbol := fmt.Sprintf("%sUSD", currency)

	rawData, err := fmp.Fmp().FetchForexHistory(symbol)
	if err != nil {
		return fmt.Errorf("failed to fetch forex data for %s: %w", symbol, err)
	}

	if len(rawData) == 0 {
		return fmt.Errorf("no forex data returned for %s", symbol)
	}

	// Convert raw data to time series
	ts, err := convertToTimeSeries(currency, rawData)
	if err != nil {
		return fmt.Errorf("failed to convert forex data: %w", err)
	}

	ts.LastFetchTime = time.Now()
	c.data[currency] = ts

	return nil
}

// convertToTimeSeries converts raw API data to weekly and monthly time series
func convertToTimeSeries(currency string, rawData []fmp.PriceDataRaw) (*ForexTimeSeries, error) {
	if len(rawData) == 0 {
		return nil, fmt.Errorf("no data to convert")
	}

	// Sort by date (oldest first) - FMP returns newest first
	sort.Slice(rawData, func(i, j int) bool {
		return rawData[i].Date < rawData[j].Date
	})

	// Use existing conversion logic from calculator package
	monthlyData, weeklyData := calculator.ConvertPrices(rawData, currency)

	ts := &ForexTimeSeries{
		Weekly:  weeklyData,
		Monthly: monthlyData,
	}

	return ts, nil
}

// Clear removes all cached data
func (c *cache) Clear() {
	c.mu.Lock()
	defer c.mu.Unlock()
	c.data = make(map[string]*ForexTimeSeries)
}

// GetCachedCurrencies returns a list of all cached currencies
func (c *cache) GetCachedCurrencies() []string {
	c.mu.RLock()
	defer c.mu.RUnlock()

	currencies := make([]string, 0, len(c.data))
	for currency := range c.data {
		currencies = append(currencies, currency)
	}
	return currencies
}
