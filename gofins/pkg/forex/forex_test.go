package forex

import (
	"fmt"
	"testing"
	"time"

	"github.com/flocko-motion/gofins/pkg/fmp"
	"github.com/stretchr/testify/assert"
)

func TestGetUsdForexRawData(t *testing.T) {
	// First, let's check what raw data we get from FMP
	symbol := "EURUSD"

	fmt.Printf("\n=== Testing Raw Forex Data from FMP ===\n")
	fmt.Printf("Fetching %s...\n", symbol)

	forexData, err := fmp.FetchForexHistory(symbol)
	assert.NoError(t, err, "Should fetch raw forex data")
	assert.NotEmpty(t, forexData, "Should have raw data")

	fmt.Printf("Got %d raw data points\n", len(forexData))
	fmt.Printf("First 5 raw data points:\n")
	for i := 0; i < 5 && i < len(forexData); i++ {
		fmt.Printf("  %d: Date=%s, Price=%.4f\n",
			i, forexData[i].Date, forexData[i].Price)
	}

	// The issue is that FMP's light endpoint returns zeros for forex
	// This is a known limitation - we need to use a different approach
	t.Log("NOTE: FMP light endpoint returns zeros for forex data")
	t.Log("This is why currency conversion is failing")
}

func TestGetUsdForexRawDataILS(t *testing.T) {
	// First, let's check what raw data we get from FMP
	symbol := "ILSUSD"

	fmt.Printf("\n=== Testing Raw Forex Data from FMP ===\n")
	fmt.Printf("Fetching %s...\n", symbol)

	forexData, err := fmp.FetchForexHistory(symbol)
	assert.NoError(t, err, "Should fetch raw forex data")
	assert.NotEmpty(t, forexData, "Should have raw data")

	fmt.Printf("Got %d raw data points\n", len(forexData))
	fmt.Printf("First 5 raw data points:\n")
	for i := 0; i < 5 && i < len(forexData); i++ {
		fmt.Printf("  %d: Date=%s, Price=%.4f\n",
			i, forexData[i].Date, forexData[i].Price)
	}

	// The issue is that FMP's light endpoint returns zeros for forex
	// This is a known limitation - we need to use a different approach
	t.Log("NOTE: FMP light endpoint returns zeros for forex data")
	t.Log("This is why currency conversion is failing")
}

func TestGetUsdForex(t *testing.T) {
	// Test with EUR to USD conversion
	currency := "EUR"
	timeTo := time.Now()
	timeFrom := timeTo.AddDate(0, -1, 0) // 1 month ago

	weekly, monthly, err := GetUsdForex(timeFrom, timeTo, currency)
	assert.NoError(t, err, "Should fetch forex data without error")
	assert.NotEmpty(t, weekly, "Should have weekly data")
	assert.NotEmpty(t, monthly, "Should have monthly data")

	fmt.Printf("\n=== Forex Data for %s ===\n", currency)
	fmt.Printf("Weekly data points: %d\n", len(weekly))
	fmt.Printf("Monthly data points: %d\n", len(monthly))

	// Check that prices are not zero
	if len(weekly) > 0 {
		fmt.Printf("First weekly: Date=%s, Close=%.4f\n", weekly[0].Date.Format("2006-01-02"), weekly[0].Close)
		assert.Greater(t, weekly[0].Close, 0.0, "Weekly forex rate should be greater than 0")
	}

	if len(monthly) > 0 {
		fmt.Printf("First monthly: Date=%s, Close=%.4f\n", monthly[0].Date.Format("2006-01-02"), monthly[0].Close)
		assert.Greater(t, monthly[0].Close, 0.0, "Monthly forex rate should be greater than 0")
	}
}

func TestConvertToUsdMonthly(t *testing.T) {
	// Test converting 1000 ILS to USD
	amount := 1000.0
	currency := "ILS"
	date := time.Now()

	converted, err := ConvertToUsdMonthly(amount, currency, date)
	assert.NoError(t, err, "Should convert without error")

	fmt.Printf("\n=== Currency Conversion Test ===\n")
	fmt.Printf("Original: %.2f %s\n", amount, currency)
	fmt.Printf("Converted: %.2f USD\n", converted)
	fmt.Printf("Exchange rate: %.4f\n", converted/amount)

	// ILS to USD rate should be around 0.25-0.30 typically
	assert.Greater(t, converted, 0.0, "Converted amount should be greater than 0")
	assert.Greater(t, converted, amount*0.2, "Converted amount should be reasonable (> 20% of original)")
	assert.Less(t, converted, amount*0.4, "Converted amount should be reasonable (< 40% of original)")

	// Verify the rate is not zero
	rate := converted / amount
	assert.Greater(t, rate, 0.0, "Exchange rate should not be zero")
	fmt.Printf("✓ Exchange rate is valid: %.4f\n", rate)
}

func TestConvertToUsdWeekly(t *testing.T) {
	// Test converting 1000 ILS to USD
	amount := 1000.0
	currency := "EUR"
	date := time.Now()

	converted, err := ConvertToUsdWeekly(amount, currency, date)
	assert.NoError(t, err, "Should convert without error")

	fmt.Printf("\n=== Weekly Currency Conversion Test ===\n")
	fmt.Printf("Original: %.2f %s\n", amount, currency)
	fmt.Printf("Converted: %.2f USD\n", converted)
	fmt.Printf("Exchange rate: %.4f\n", converted/amount)

	// EUR to USD rate should be around 1.0-1.2 typically
	assert.Greater(t, converted, 0.0, "Converted amount should be greater than 0")
	assert.Greater(t, converted, amount*0.8, "Converted amount should be reasonable (> 80% of original)")
	assert.Less(t, converted, amount*2.0, "Converted amount should be reasonable (< 200% of original)")

	// Verify the rate is not zero
	rate := converted / amount
	assert.Greater(t, rate, 0.0, "Exchange rate should not be zero")
	fmt.Printf("✓ Exchange rate is valid: %.4f\n", rate)
}

func TestConvertUsdToUsd(t *testing.T) {
	// USD to USD should return the same amount
	amount := 1000.0
	currency := "USD"
	date := time.Now()

	converted, err := ConvertToUsdMonthly(amount, currency, date)
	assert.NoError(t, err)
	assert.Equal(t, amount, converted, "USD to USD should return same amount")
}

func TestGetUsdForexEmptyCurrency(t *testing.T) {
	timeTo := time.Now()
	timeFrom := timeTo.AddDate(0, -1, 0)

	_, _, err := GetUsdForex(timeFrom, timeTo, "")
	assert.Error(t, err, "Should error on empty currency")
	assert.Contains(t, err.Error(), "currency cannot be empty")
}

func TestGetUsdForexInvalidTimeRange(t *testing.T) {
	timeTo := time.Now()
	timeFrom := timeTo.AddDate(0, 1, 0) // Future date

	_, _, err := GetUsdForex(timeFrom, timeTo, "EUR")
	assert.Error(t, err, "Should error when timeFrom is after timeTo")
	assert.Contains(t, err.Error(), "must be before or equal to")
}
