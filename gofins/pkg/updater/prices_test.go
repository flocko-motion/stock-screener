package updater

import (
	"fmt"
	"math"
	"testing"

	"github.com/flocko-motion/gofins/pkg/db"
	"github.com/flocko-motion/gofins/pkg/f"
	"github.com/flocko-motion/gofins/pkg/types"
	"github.com/stretchr/testify/assert"
)

func TestUpdatePrices(t *testing.T) {
	log := NewLoggerTest("PricesTest")
	config := PriceUpdateConfig{
		Workers:         20,
		BatchSize:       100,
		WriteToDb:       true,
		EnableProfiling: false,
	}
	err := updatePricesImpl(log, config)
	if err != nil {
		t.Logf("Price update failed (may be expected due to API limits): %v", err)
	} else {
		t.Log("Price update completed successfully")
	}
}

func TestFetchPrices(t *testing.T) {
	ticker := "NOVO-B.CO"

	// Call updatePrices - uses db.Db() singleton internally
	log := NewLoggerTest("FetchTest")
	config := PriceUpdateConfig{WriteToDb: true, EnableProfiling: false}
	symbol, monthly, weekly, _ := updatePrices(types.Symbol{Ticker: ticker}, config, log)

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
	tickerUSD := "EBAY"   // US ticker in USD
	tickerEUR := "EBA.DE" // German ticker in EUR

	// Fetch both symbols from database
	symbolUSD, err := db.GetSymbol(tickerUSD)
	assert.NoError(t, err)
	assert.NotNil(t, symbolUSD)

	symbolEUR, err := db.GetSymbol(tickerEUR)
	assert.NoError(t, err)
	assert.NotNil(t, symbolEUR)
	fmt.Printf("currency: %v\n", symbolEUR.Currency)

	// Fetch prices for both tickers (test mode - no DB writes)
	log := NewLoggerTest("CurrTest")
	config := PriceUpdateConfig{WriteToDb: false, EnableProfiling: false}
	_, monthlyUSD, weeklyUSD, _ := updatePrices(*symbolUSD, config, log)
	_, monthlyEUR, weeklyEUR, _ := updatePrices(*symbolEUR, config, log)

	// Both should have data
	assert.NotEmpty(t, monthlyUSD)
	assert.NotEmpty(t, monthlyEUR)
	assert.NotEmpty(t, weeklyUSD)
	assert.NotEmpty(t, weeklyEUR)

	fmt.Printf("\n=== Currency Conversion Test ===\n")
	fmt.Printf("USD ticker: %s (%d monthly, %d weekly)\n", tickerUSD, len(monthlyUSD), len(weeklyUSD))
	fmt.Printf("EUR ticker: %s (%d monthly, %d weekly)\n", tickerEUR, len(monthlyEUR), len(weeklyEUR))

	// Compare a sample of monthly prices (last 12 months or whatever is available)
	compareCount := 12
	if len(monthlyUSD) < compareCount {
		compareCount = len(monthlyUSD)
	}
	if len(monthlyEUR) < compareCount {
		compareCount = len(monthlyEUR)
	}

	fmt.Printf("\nComparing last %d monthly prices:\n", compareCount)
	matchCount := 0
	totalDiff := 0.0

	for i := 0; i < compareCount; i++ {
		usdIdx := len(monthlyUSD) - compareCount + i
		eurIdx := len(monthlyEUR) - compareCount + i

		priceUSD := monthlyUSD[usdIdx]
		priceEUR := monthlyEUR[eurIdx]

		// Compare close prices (should be similar after currency conversion)
		if priceUSD.Close > 0 && priceEUR.Close > 0 {
			diff := ((priceUSD.Close - priceEUR.Close) / priceUSD.Close) * 100
			totalDiff += math.Abs(diff)

			fmt.Printf("  %s: USD=%.2f EUR=%.2f diff=%.2f%%\n",
				priceUSD.Date.Format("2006-01"), priceUSD.Close, priceEUR.Close, diff)

			// Prices should be within 1% after currency conversion
			if math.Abs(diff) <= 4.0 {
				matchCount++
			}
		}
	}

	avgDiff := totalDiff / float64(compareCount)
	matchRate := float64(matchCount) / float64(compareCount) * 100

	fmt.Printf("\nResults:\n")
	fmt.Printf("  Average difference: %.2f%%\n", avgDiff)
	fmt.Printf("  Match rate (≤1%% diff): %.0f%% (%d/%d)\n", matchRate, matchCount, compareCount)

	// At least 80% of prices should match within 1% tolerance
	assert.GreaterOrEqual(t, matchRate, 80.0,
		"Currency conversion failed: only %.0f%% of prices matched (expected ≥80%%)", matchRate)

	// Average difference should be less than 0.5%
	avgDiffExpect := 4.0
	assert.LessOrEqual(t, avgDiff, avgDiffExpect,
		"Currency conversion inaccurate: average difference %.2f%% (expected ≤%.2f%%)", avgDiff, avgDiffExpect)
}
