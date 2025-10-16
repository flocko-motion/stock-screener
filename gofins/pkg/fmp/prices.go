package fmp

import "strings"

type DailyPrice struct {
	Date  string  `json:"date"`
	Open  float64 `json:"adjOpen"`
	High  float64 `json:"adjHigh"`
	Low   float64 `json:"adjLow"`
	Close float64 `json:"adjClose"`
}

// FetchPriceHistory fetches historical price data for a ticker.
// Automatically detects index symbols (starting with ^) and routes to the correct endpoint.
func (c *Client) FetchPriceHistory(ticker string) ([]DailyPrice, error) {
	var prices []DailyPrice
	var endpoint string
	params := map[string]string{
		"symbol": ticker,
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
