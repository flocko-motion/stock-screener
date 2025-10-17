package updater

import (
	"fmt"
	"testing"

	"github.com/flocko-motion/gofins/pkg/db"
	"github.com/stretchr/testify/assert"
)

func TestUpdateProfileCurrencyConversion(t *testing.T) {
	tickerUSD := "EBAY"   // US ticker in USD
	tickerEUR := "EBA.DE" // German ticker in EUR

	// Fetch profiles from FMP (test mode - no DB writes)
	fmt.Printf("\n=== Profile Currency Conversion Test ===\n")
	
	statusUSD := updateProfileInternal(tickerUSD, true)
	fmt.Printf("USD ticker: %s - status: %s\n", tickerUSD, statusUSD)
	assert.Equal(t, "ok", statusUSD)

	statusEUR := updateProfileInternal(tickerEUR, true)
	fmt.Printf("EUR ticker: %s - status: %s\n", tickerEUR, statusEUR)
	assert.Equal(t, "ok", statusEUR)

	// Now fetch from database to see current state
	symbolUSD, err := db.GetSymbol(tickerUSD)
	assert.NoError(t, err)
	assert.NotNil(t, symbolUSD)
	
	symbolEUR, err := db.GetSymbol(tickerEUR)
	assert.NoError(t, err)
	assert.NotNil(t, symbolEUR)

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

	fmt.Printf("\n=== Note ===\n")
	fmt.Printf("If currency is nil, you need to update profiles:\n")
	fmt.Printf("  Run: gofins update-profiles\n")
}
