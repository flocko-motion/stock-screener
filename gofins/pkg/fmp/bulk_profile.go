package fmp

import (
	"encoding/csv"
	"fmt"
	"io"
	"strconv"
	"strings"
	"time"
)

// GetBulkProfiles fetches all company profiles from the bulk endpoint
// The API is paginated, so we fetch all pages and merge them
func GetBulkProfiles() ([]*Profile, error) {
	return Fmp().getBulkProfiles()
}

// getBulkProfiles is the internal implementation that has access to private fields
func (c *Client) getBulkProfiles() ([]*Profile, error) {
	var allProfiles []*Profile
	part := 0

	for {
		endpoint := fmt.Sprintf("stable/profile-bulk?part=%d", part)
		
		// Use the FMP client's raw GET method (handles rate limiting and API key)
		body, err := c.apiGetRaw(endpoint, nil)
		if err != nil {
			// Check if this is a 400 error indicating we've reached the end of pagination
			if strings.Contains(err.Error(), "status 400") || strings.Contains(err.Error(), "Invalid or missing query parameter") {
				logger.Printf("Reached end of pagination at part %d\n", part)
				break
			}
			return nil, fmt.Errorf("failed to fetch bulk profiles part %d: %w", part, err)
		}

		// Parse CSV
		reader := csv.NewReader(body)
		reader.LazyQuotes = true
		
		// Read header
		header, err := reader.Read()
		if err != nil {
			body.Close()
			if err == io.EOF {
				break // Empty response, we're done
			}
			return nil, fmt.Errorf("failed to read CSV header for part %d: %w", part, err)
		}

		// Create column index map
		colIndex := make(map[string]int)
		for i, col := range header {
			colIndex[col] = i
		}

		// Read all records
		var profiles []*Profile
		for {
			record, err := reader.Read()
			if err == io.EOF {
				break
			}
			if err != nil {
				body.Close()
				return nil, fmt.Errorf("failed to read CSV record for part %d: %w", part, err)
			}

			profile := parseProfileFromCSV(record, colIndex)
			if profile != nil {
				profiles = append(profiles, profile)
			}
		}
		body.Close()

		// If we got no profiles, we've reached the end
		if len(profiles) == 0 {
			break
		}

		allProfiles = append(allProfiles, profiles...)
		logger.Printf("Fetched part %d: %d profiles (total: %d)\n", part, len(profiles), len(allProfiles))
		
		part++
		
		// Safety limit to prevent infinite loops
		if part > 100 {
			return nil, fmt.Errorf("too many pages (>100), stopping")
		}
		
		// Small delay between pages to be nice to the API
		time.Sleep(100 * time.Millisecond)
	}

	logger.Printf("Fetched all profiles: %d total\n", len(allProfiles))
	return allProfiles, nil
}

// parseProfileFromCSV parses a single CSV record into a Profile
func parseProfileFromCSV(record []string, colIndex map[string]int) *Profile {
	getCol := func(name string) string {
		if idx, ok := colIndex[name]; ok && idx < len(record) {
			return strings.TrimSpace(record[idx])
		}
		return ""
	}

	getFloat := func(name string) float64 {
		val := getCol(name)
		if val == "" {
			return 0
		}
		f, _ := strconv.ParseFloat(val, 64)
		return f
	}

	getBool := func(name string) bool {
		val := strings.ToLower(getCol(name))
		return val == "true" || val == "1" || val == "yes"
	}

	symbol := getCol("symbol")
	if symbol == "" {
		return nil // Skip records without a symbol
	}

	return &Profile{
		Symbol:            symbol,
		CompanyName:       getCol("companyName"),
		Exchange:          getCol("exchange"),
		Currency:          getCol("currency"),
		Industry:          getCol("industry"),
		Sector:            getCol("sector"),
		Country:           getCol("country"),
		CIK:               getCol("cik"),
		MarketCap:         getFloat("marketCap"),
		Price:             getFloat("price"),
		CEO:               getCol("ceo"),
		Description:       getCol("description"),
		Website:           getCol("website"),
		IPODate:           getCol("ipoDate"),
		FullTimeEmployees: getCol("fullTimeEmployees"),
		IsActivelyTrading: getBool("isActivelyTrading"),
		IsEtf:             getBool("isEtf"),
		IsFund:            getBool("isFund"),
		IsAdr:             getBool("isAdr"),
	}
}
