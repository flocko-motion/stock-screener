package forex

import (
	"fmt"
	"testing"
	"time"

	"github.com/flocko-motion/gofins/pkg/calculator"
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

func TestConvertToUsd(t *testing.T) {
	// Test converting 1000 ILS to USD
	amount := 1000.0
	currency := "ILS"
	// Use first of month for lookup
	now := time.Now()
	date := time.Date(now.Year(), now.Month(), 1, 0, 0, 0, 0, time.UTC)

	converted, err := ConvertToUsd(amount, currency, date)
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
	// Test converting 1000 EUR to USD using weekly rate
	amount := 1000.0
	currency := "EUR"
	// Use last week's Monday to ensure data exists
	// Make sure to truncate to midnight UTC to match the forex data format
	date := calculator.StartOfWeek(time.Now().AddDate(0, 0, -7))
	fmt.Printf("Looking for date: %s (weekday: %s)\n", date.Format("2006-01-02 15:04:05 MST"), date.Weekday())

	converted, err := ConvertToUsd(amount, currency, date)
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
	date := calculator.StartOfMonth(time.Now())

	converted, err := ConvertToUsd(amount, currency, date)
	assert.NoError(t, err)
	assert.Equal(t, amount, converted, "USD to USD should return same amount")
}
