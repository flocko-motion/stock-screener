package fmp

import "strings"

// PriceDataRaw represents raw daily price data from FMP API (JSON format)
type PriceDataRaw struct {
	Date  string  `json:"date"`
	Open  float64 `json:"adjOpen"`
	High  float64 `json:"adjHigh"`
	Low   float64 `json:"adjLow"`
	Close float64 `json:"adjClose"`
}

// FetchPriceHistory fetches historical price data for a ticker.
// Automatically detects index symbols (starting with ^) and routes to the correct endpoint.
func FetchPriceHistory(ticker string) ([]PriceDataRaw, error) {
	c := Fmp()
	var prices []PriceDataRaw
	var endpoint string
	params := map[string]string{
		"symbol": ticker,
		"from":   "1900-01-01",
	}

	// Index symbols (starting with ^) use a different endpoint
	if strings.HasPrefix(ticker, "^") {
		endpoint = "stable/historical-price-eod/full"
	} else {
		endpoint = "stable/historical-price-eod/dividend-adjusted"
	}

	if err := c.apiGet(endpoint, params, &prices); err != nil {
		return nil, err
	}

	if len(prices) == 0 {
		return nil, &NotFoundError{Ticker: ticker}
	}

	return prices, nil
}

// ForexDataRaw represents raw forex data from FMP API light endpoint
// The light endpoint returns a simplified structure with just price and volume
type ForexData struct {
	Symbol string  `json:"symbol"`
	Date   string  `json:"date"`
	Price  float64 `json:"price"` // The exchange rate
	Volume int64   `json:"volume"`
}

// FetchForexHistory fetches historical forex data.
// Symbol should be in format like "EURUSD", "GBPUSD", etc.
func FetchForexHistory(symbol string) ([]ForexData, error) {
	c := Fmp()
	var forexData []ForexData
	params := map[string]string{
		"symbol": symbol,
	}

	// Use the light endpoint for forex historical data
	endpoint := "stable/historical-price-eod/light"

	if err := c.apiGet(endpoint, params, &forexData); err != nil {
		return nil, err
	}

	if len(forexData) == 0 {
		return nil, &NotFoundError{Ticker: symbol}
	}

	return forexData, nil
}
