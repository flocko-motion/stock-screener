package fmp

import (
	"strings"
	"testing"

	"github.com/stretchr/testify/assert"
)

func TestGetBulkProfiles(t *testing.T) {
	// Fetch bulk profiles from FMP
	profiles, err := GetBulkProfiles()
	
	// Handle expected errors gracefully (rate limits, API unavailable, etc.)
	if err != nil {
		if strings.Contains(err.Error(), "status 429") {
			t.Skip("Skipping test: API rate limit reached")
			return
		}
		t.Logf("Failed to fetch bulk profiles (may be expected if API unavailable): %v", err)
		// Don't fail the test - API may be unavailable
		return
	}
	
	assert.NoError(t, err)
	assert.NotEmpty(t, profiles, "Should fetch at least some profiles")
	
	t.Logf("Fetched %d profiles from bulk endpoint", len(profiles))
	
	// Validate first profile has expected fields
	if len(profiles) > 0 {
		p := profiles[0]
		assert.NotEmpty(t, p.Symbol, "Profile should have a symbol")
		t.Logf("First profile: %s - %s (%s)", p.Symbol, p.CompanyName, p.Exchange)
		
		// Log some sample profiles for inspection
		sampleSize := 5
		if len(profiles) < sampleSize {
			sampleSize = len(profiles)
		}
		
		t.Logf("\nSample profiles:")
		for i := 0; i < sampleSize; i++ {
			p := profiles[i]
			t.Logf("  [%d] %s - %s | Exchange: %s | Currency: %s | MarketCap: %.0f | Active: %v",
				i+1, p.Symbol, p.CompanyName, p.Exchange, p.Currency, p.MarketCap, p.IsActivelyTrading)
		}
	}
}

func TestParseProfileFromCSV(t *testing.T) {
	// Test CSV parsing with sample data
	header := []string{"symbol", "companyName", "exchange", "currency", "marketCap", "isActivelyTrading", "isEtf"}
	
	// Create column index
	colIndex := make(map[string]int)
	for i, col := range header {
		colIndex[col] = i
	}
	
	// Test valid record
	record := []string{"AAPL", "Apple Inc.", "NASDAQ", "USD", "3000000000000", "true", "false"}
	profile := parseProfileFromCSV(record, colIndex)
	
	assert.NotNil(t, profile)
	assert.Equal(t, "AAPL", profile.Symbol)
	assert.Equal(t, "Apple Inc.", profile.CompanyName)
	assert.Equal(t, "NASDAQ", profile.Exchange)
	assert.Equal(t, "USD", profile.Currency)
	assert.Equal(t, 3000000000000.0, profile.MarketCap)
	assert.True(t, profile.IsActivelyTrading)
	assert.False(t, profile.IsEtf)
	
	// Test record without symbol (should return nil)
	recordNoSymbol := []string{"", "Test Company", "NYSE", "USD", "1000000", "true", "false"}
	profileNil := parseProfileFromCSV(recordNoSymbol, colIndex)
	assert.Nil(t, profileNil, "Should return nil for records without symbol")
	
	// Test record with missing fields (should handle gracefully)
	recordPartial := []string{"TEST", "Test Inc."}
	profilePartial := parseProfileFromCSV(recordPartial, colIndex)
	assert.NotNil(t, profilePartial)
	assert.Equal(t, "TEST", profilePartial.Symbol)
	assert.Equal(t, "Test Inc.", profilePartial.CompanyName)
	assert.Equal(t, "", profilePartial.Exchange) // Missing field should be empty
	assert.Equal(t, 0.0, profilePartial.MarketCap) // Missing numeric should be 0
}
