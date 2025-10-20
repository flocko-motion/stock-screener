package forex

import (
	"fmt"
	"slices"
	"strings"
	"time"

	"github.com/flocko-motion/gofins/pkg/f"
	"github.com/flocko-motion/gofins/pkg/types"
)

// ForexTimeSeries holds forex data for a currency pair
// Data is keyed by date (either week start Monday or month start)
type ForexTimeSeries struct {
	Data          map[time.Time]types.PriceData
	TimeTo        time.Time
	TimeFrom      time.Time
	LastFetchTime time.Time
}

// ConvertToUsd converts an amount using the forex rate for the given date
// Date should be a week start (Monday) or month start (1st) - no date calculation is performed
func ConvertToUsd(amount float64, currency string, date time.Time) (float64, error) {
	if currency == "USD" {
		return amount, nil
	}

	ts, err := getCachedForex(currency)
	if err != nil {
		return 0, fmt.Errorf("failed to get forex data for %s: %w", currency, err)
	}

	// Direct lookup - caller must provide correct date (week/month start)
	priceData, exists := ts.Data[date]
	if !exists {
		keys := f.Keys(ts.Data)
		keyStrs := make([]string, len(keys))
		for i, k := range keys {
			keyStrs[i] = k.Format("2006-01-02")
		}
		slices.Sort(keyStrs)
		return 0, fmt.Errorf("no forex data for %s at %s, available keys: %s", currency, date.Format("2006-01-02"), strings.Join(keyStrs, ", "))
	}

	return amount * priceData.Close, nil
}

// getCachedForex retrieves forex data from cache, fetching if necessary
func getCachedForex(currency string) (*ForexTimeSeries, error) {
	if globalCache == nil {
		initCache()
	}

	globalCache.mu.Lock()
	defer globalCache.mu.Unlock()

	ts, exists := globalCache.data[currency]
	if !exists {
		if err := globalCache.fetchAndStore(currency); err != nil {
			return nil, err
		}
		ts = globalCache.data[currency]
	}

	return ts, nil
}
