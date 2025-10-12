package fmp

type DailyPrice struct {
	Date  string  `json:"date"`
	Open  float64 `json:"adjOpen"`
	High  float64 `json:"adjHigh"`
	Low   float64 `json:"adjLow"`
	Close float64 `json:"adjClose"`
}

func (c *Client) FetchPriceHistory(ticker string) ([]DailyPrice, error) {
	var prices []DailyPrice
	params := map[string]string{
		"symbol": ticker,
	}

	if err := c.apiGet("stable/historical-price-eod/dividend-adjusted", params, &prices); err != nil {
		return nil, err
	}

	if len(prices) == 0 {
		return nil, &NotFoundError{Ticker: ticker}
	}

	return prices, nil
}
