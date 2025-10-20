package forex

import (
	"fmt"
	"sort"
	"sync"
	"time"

	"github.com/flocko-motion/gofins/pkg/calculator"
	"github.com/flocko-motion/gofins/pkg/fmp"
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

// getUsdForex returns forex rates for the given currency as a map
// Internal function that works with the global cache
func getUsdForex(timeFrom, timeTo time.Time, currency string) (*ForexTimeSeries, error) {
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
		if timeFrom.Before(ts.TimeFrom) || timeTo.After(ts.TimeTo) {
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
				return ts, fmt.Errorf("partial data available, fetch failed: %w", err)
			}
			return nil, err
		}
		ts = globalCache.data[currency]
	}

	return ts, nil
}

// fetchAndStore fetches forex data from the API and stores it in cache
func (c *cache) fetchAndStore(currency string) error {
	// Currency should already be normalized by the profile updater
	symbol := fmt.Sprintf("%sUSD", currency)

	forexData, err := fmp.FetchForexHistory(symbol)
	if err != nil {
		return fmt.Errorf("failed to fetch forex data for %s: %w", symbol, err)
	}

	if len(forexData) == 0 {
		return fmt.Errorf("no forex data returned for %s", symbol)
	}

	// Sort by date (oldest first) - FMP returns newest first
	sort.Slice(forexData, func(i, j int) bool {
		return forexData[i].Date < forexData[j].Date
	})

	// Convert forex data to time series using calculator
	timeFrom, timeTo, data := calculator.ConvertForexPrices(forexData, currency)

	ts := &ForexTimeSeries{
		Data:          data,
		TimeFrom:      timeFrom,
		TimeTo:        timeTo,
		LastFetchTime: time.Now(),
	}

	c.data[currency] = ts

	return nil
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
