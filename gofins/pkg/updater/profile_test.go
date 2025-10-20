package updater

import (
	"fmt"
	"testing"

	"github.com/stretchr/testify/assert"
)

func TestUpdateProfileLight(t *testing.T) {
	ticker := "QAMC.QA" // put ticker to debug here

	logger := NewLoggerTest("profile")

	updateProfile(ticker, true, logger)
}

func TestUpdateProfileCurrencyConversion(t *testing.T) {
	tickerUSD := "EBAY"   // US ticker in USD
	tickerEUR := "EBA.DE" // German ticker in EUR

	// Fetch profiles from FMP (test mode - no DB writes, but returns the symbol object)
	fmt.Printf("\n=== Profile Currency Conversion Test ===\n")

	logger := NewLoggerTest("profile")

	symbolUSD, statusUSD := updateProfile(tickerUSD, true, logger)
	fmt.Printf("USD ticker: %s - status: %s\n", tickerUSD, statusUSD)
	assert.Equal(t, "ok", statusUSD)
	assert.NotNil(t, symbolUSD, "Symbol should be returned even in test mode")

	symbolEUR, statusEUR := updateProfile(tickerEUR, true, logger)
	fmt.Printf("EUR ticker: %s - status: %s\n", tickerEUR, statusEUR)
	assert.Equal(t, "ok", statusEUR)
	assert.NotNil(t, symbolEUR, "Symbol should be returned even in test mode")

	fmt.Printf("\n=== Current Database State ===\n")
	fmt.Printf("USD Symbol:\n")
	if symbolUSD.Currency != nil {
		fmt.Printf("  Currency: %s\n", *symbolUSD.Currency)
	} else {
		fmt.Printf("  Currency: <nil>\n")
	}
	if symbolUSD.MarketCap != nil {
		fmt.Printf("  Market Cap: $%d\n", *symbolUSD.MarketCap)
	} else {
		fmt.Printf("  Market Cap: <nil>\n")
	}

	fmt.Printf("\nEUR Symbol:\n")
	if symbolEUR.Currency != nil {
		fmt.Printf("  Currency: %s\n", *symbolEUR.Currency)
	} else {
		fmt.Printf("  Currency: <nil>\n")
	}
	if symbolEUR.MarketCap != nil {
		fmt.Printf("  Market Cap: $%d\n", *symbolEUR.MarketCap)
	} else {
		fmt.Printf("  Market Cap: <nil>\n")
	}

	// Currency must be populated
	assert.NotNil(t, symbolUSD.Currency, "USD symbol must have currency field populated")
	assert.NotNil(t, symbolEUR.Currency, "EUR symbol must have currency field populated")

	if symbolUSD.Currency != nil {
		assert.Equal(t, "USD", *symbolUSD.Currency, "EBAY should be in USD")
	}
	if symbolEUR.Currency != nil {
		assert.Equal(t, "EUR", *symbolEUR.Currency, "EBA.DE should be in EUR")
	}

	// Market cap should be populated and positive
	assert.NotNil(t, symbolUSD.MarketCap, "USD symbol must have market cap")
	assert.NotNil(t, symbolEUR.MarketCap, "EUR symbol must have market cap")

	if symbolUSD.MarketCap != nil {
		assert.Greater(t, *symbolUSD.MarketCap, int64(0), "Market cap should be positive")
	}
	if symbolEUR.MarketCap != nil {
		assert.Greater(t, *symbolEUR.MarketCap, int64(0), "Market cap should be positive")
	}

	// Both are the same company (eBay), so market caps should be within 5% after conversion
	if symbolUSD.MarketCap != nil && symbolEUR.MarketCap != nil {
		mcapUSD := float64(*symbolUSD.MarketCap)
		mcapEUR := float64(*symbolEUR.MarketCap)

		// Calculate percentage difference
		diff := (mcapUSD - mcapEUR) / mcapUSD * 100
		if diff < 0 {
			diff = -diff
		}

		fmt.Printf("\n=== Market Cap Comparison ===\n")
		fmt.Printf("USD Market Cap: $%.2f billion\n", mcapUSD/1e9)
		fmt.Printf("EUR Market Cap (converted): $%.2f billion\n", mcapEUR/1e9)
		fmt.Printf("Difference: %.2f%%\n", diff)

		tolerance := 2.0
		assert.Less(t, diff, tolerance, "Market caps should be within %f%% of each other (same company)", tolerance)
	}

	fmt.Printf("\n=== Test Mode ===\n")
	fmt.Printf("This test fetches from FMP and verifies currency conversion logic.\n")
	fmt.Printf("No database writes are performed (testMode=true).\n")
	fmt.Printf("To update all symbols in production, run: gofins update-profiles\n")
}
