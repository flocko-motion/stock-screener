package fmp

import (
	"encoding/csv"
	"fmt"
	"io"
	"strconv"
	"time"

	"github.com/flocko-motion/gofins/pkg/types"
)

// GetBulkEOD fetches bulk end-of-day data for a specific date
func GetBulkEOD(date time.Time) (map[string]*types.PriceData, error) {
	return Fmp().getBulkEOD(date)
}

// getBulkEOD is the internal implementation that has access to private fields
func (c *Client) getBulkEOD(date time.Time) (map[string]*types.PriceData, error) {
	dateStr := date.Format("2006-01-02")
	endpoint := fmt.Sprintf("stable/eod-bulk?date=%s", dateStr)
	
	// Use the FMP client's raw GET method (handles rate limiting and API key)
	body, err := c.apiGetRaw(endpoint, nil)
	if err != nil {
		return nil, fmt.Errorf("failed to fetch bulk EOD: %w", err)
	}
	defer body.Close()

	// Parse CSV
	reader := csv.NewReader(body)

	// Skip header
	if _, err := reader.Read(); err != nil {
		return nil, fmt.Errorf("failed to read CSV header: %w", err)
	}

	quotes := make(map[string]*types.PriceData)
	for {
		record, err := reader.Read()
		if err == io.EOF {
			break
		}
		if err != nil {
			return nil, fmt.Errorf("failed to read CSV record: %w", err)
		}

		if len(record) < 8 {
			continue // Skip malformed records
		}

		symbol := record[0]
		dateStr := record[1]
		openStr := record[2]
		lowStr := record[3]
		highStr := record[4]
		closeStr := record[5]
		// record[6] is adjClose, record[7] is volume - we don't use these

		// Parse date
		quoteDate, err := time.Parse("2006-01-02", dateStr)
		if err != nil {
			continue // Skip invalid dates
		}

		// Parse prices
		open, err := strconv.ParseFloat(openStr, 64)
		if err != nil {
			continue
		}
		high, err := strconv.ParseFloat(highStr, 64)
		if err != nil {
			continue
		}
		low, err := strconv.ParseFloat(lowStr, 64)
		if err != nil {
			continue
		}
		close, err := strconv.ParseFloat(closeStr, 64)
		if err != nil || close <= 0 {
			continue // Skip invalid prices
		}

		// Calculate average price
		avg := (open + high + low + close) / 4.0

		quotes[symbol] = &types.PriceData{
			SymbolTicker: symbol,
			Date:         quoteDate,
			Open:         open,
			High:         high,
			Low:          low,
			Avg:          avg,
			Close:        close,
		}
	}

	return quotes, nil
}
