package forex

import (
	"math/rand"
	"testing"
	"time"

	"github.com/flocko-motion/gofins/pkg/calculator"
	"github.com/flocko-motion/gofins/pkg/types"
)

func BenchmarkForexConversion(b *testing.B) {
	currency := "JPY"
	
	// Generate mock price data (279 monthly + 1209 weekly = realistic symbol)
	monthly := generateMockPrices(279)
	weekly := generateMockPrices(1209)
	
	b.Run("FirstCall_WithAPIFetch", func(b *testing.B) {
		// Clear cache to force API fetch
		globalCache = nil
		
		b.ResetTimer()
		for i := 0; i < b.N; i++ {
			convertMockPrices(monthly, weekly, currency)
		}
	})
	
	b.Run("SecondCall_Cached", func(b *testing.B) {
		// Cache already populated from FirstCall benchmark
		b.ResetTimer()
		for i := 0; i < b.N; i++ {
			convertMockPrices(monthly, weekly, currency)
		}
	})
}

func generateMockPrices(count int) []types.PriceData {
	prices := make([]types.PriceData, count)
	now := time.Now()
	
	for i := 0; i < count; i++ {
		prices[i] = types.PriceData{
			Date:  calculator.StartOfMonth(now.AddDate(0, -i, 0)),
			Open:  rand.Float64() * 100,
			Close: rand.Float64() * 100,
			High:  rand.Float64() * 100,
			Low:   rand.Float64() * 100,
			Avg:   rand.Float64() * 100,
		}
	}
	
	return prices
}

func convertMockPrices(monthly, weekly []types.PriceData, currency string) {
	// Simulate the actual conversion logic
	for _, price := range monthly {
		_, _ = ConvertToUsd(price.Close, currency, price.Date)
	}
	for _, price := range weekly {
		_, _ = ConvertToUsd(price.Close, currency, price.Date)
	}
}

func BenchmarkJustMapLookup(b *testing.B) {
	// Pre-populate cache
	currency := "JPY"
	testDate := calculator.StartOfMonth(time.Now())
	_, _ = ConvertToUsd(1.0, currency, testDate)
	
	// Get the cached data
	ts, _ := GetCachedForex(currency)
	
	b.Run("DirectMapLookup", func(b *testing.B) {
		b.ResetTimer()
		for i := 0; i < b.N; i++ {
			for j := 0; j < 1488; j++ {
				date := calculator.StartOfMonth(time.Now().AddDate(0, -j, 0))
				_ = ts.Data[date]
			}
		}
	})
	
	b.Run("ThroughConvertToUsd", func(b *testing.B) {
		b.ResetTimer()
		for i := 0; i < b.N; i++ {
			for j := 0; j < 1488; j++ {
				date := calculator.StartOfMonth(time.Now().AddDate(0, -j, 0))
				_, _ = ConvertToUsd(1.0, currency, date)
			}
		}
	})
}
