package updater

import (
	"fmt"
	"testing"

	"github.com/flocko-motion/gofins/pkg/db"
	"github.com/flocko-motion/gofins/pkg/f"
	"github.com/flocko-motion/gofins/pkg/types"
	"github.com/stretchr/testify/assert"
)

func TestFetchPrices(t *testing.T) {
	ticker := "EBAY"

	// Call updatePrices - uses db.Db() singleton internally
	symbol, monthly, weekly := updatePrices(types.Symbol{Ticker: ticker})

	assert.Equal(t, ticker, symbol.Ticker)
	assert.NotNil(t, symbol.LastPriceStatus)
	assert.Equal(t, types.StatusOK, *symbol.LastPriceStatus)

	assert.NotEmpty(t, monthly)
	assert.NotEmpty(t, weekly)

	fmt.Printf("Fetched %d monthly and %d weekly prices for %s\n", len(monthly), len(weekly), ticker)
	for i, price := range monthly {
		fmt.Printf("monthly %d: %s\n", i, f.MaybeToString(price.YoY, "n/a"))
	}
	for i, price := range weekly {
		fmt.Printf("weekly %d: %s\n", i, f.MaybeToString(price.YoY, "n/a"))
	}
}

func TestFetchPricesCurrencyConversion(t *testing.T) {
	ticker := "EBA.DE"

	// Connect to database to fetch symbol profile
	database, err := db.NewDB()
	assert.NoError(t, err)
	defer database.Close()

	// Fetch symbol from database
	symbol, err := database.GetSymbol(ticker)
	assert.NoError(t, err)
	assert.NotNil(t, symbol)

	// Call updatePrices with nil database to skip DB writes
	updatedSymbol, monthly, weekly := updatePrices(*symbol)

	assert.Equal(t, ticker, updatedSymbol.Ticker)
	assert.NotNil(t, updatedSymbol.LastPriceStatus)
	assert.Equal(t, types.StatusOK, *updatedSymbol.LastPriceStatus)

	assert.NotEmpty(t, monthly)
	assert.NotEmpty(t, weekly)

	fmt.Printf("Fetched %d monthly and %d weekly prices for %s\n", len(monthly), len(weekly), ticker)
	for i, price := range monthly {
		fmt.Printf("monthly %d: %s\n", i, f.MaybeToString(price.YoY, "n/a"))
	}
	for i, price := range weekly {
		fmt.Printf("weekly %d: %s\n", i, f.MaybeToString(price.YoY, "n/a"))
	}
}
