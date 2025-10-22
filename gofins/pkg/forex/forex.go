package forex

import (
	"fmt"
	"time"

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

	ts, err := GetCachedForex(currency)
	if err != nil {
		return 0, fmt.Errorf("failed to get forex data for %s: %w", currency, err)
	}
	
	return ConvertToUsdWithTimeSeries(amount, ts, date)
}

// ConvertToUsdWithTimeSeries converts using pre-fetched forex data (avoids mutex lock)
func ConvertToUsdWithTimeSeries(amount float64, ts *ForexTimeSeries, date time.Time) (float64, error) {

	if date.After(ts.TimeTo) && date.Sub(ts.TimeTo) <= 7*24*time.Hour {
		date = ts.TimeTo
	}

	// Direct lookup - caller must provide correct date (week/month start)
	priceData, exists := ts.Data[date]
	if !exists {
		// If date is up to 7 days after the latest available date, use the latest date
		if date.After(ts.TimeTo) && date.Sub(ts.TimeTo) <= 7*24*time.Hour {
			priceData, exists = ts.Data[ts.TimeTo]
		}

		if !exists {
			return 0, fmt.Errorf("no forex data at %s", date.Format("2006-01-02"))
		}
	}

	return amount * priceData.Close, nil
}

// GetCachedForex retrieves forex data from cache, fetching if necessary
func GetCachedForex(currency string) (*ForexTimeSeries, error) {
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
