package forex

import (
	"fmt"
	"time"

	"github.com/flocko-motion/gofins/pkg/types"
)

// ForexTimeSeries holds forex data for a currency pair
type ForexTimeSeries struct {
	Weekly        []types.PriceData
	Monthly       []types.PriceData
	LastFetchTime time.Time
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
