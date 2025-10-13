package fmp

import (
	"fmt"
	"time"
)

// NotFoundError indicates the requested resource doesn't exist
type NotFoundError struct {
	Ticker string
}

func (e *NotFoundError) Error() string {
	return fmt.Sprintf("no profile found for ticker: %s", e.Ticker)
}

func IsNotFoundError(err error) bool {
	_, ok := err.(*NotFoundError)
	return ok
}

// Stock represents a stock from the stock list
type Stock struct {
	Symbol   string `json:"symbol"`
	Name     string `json:"name"`
	Exchange string `json:"exchange"`
	Type     string `json:"exchangeShortName"`
}

// Profile represents a company profile from FMP
type Profile struct {
	Symbol            string  `json:"symbol"`
	CompanyName       string  `json:"companyName"`
	Exchange          string  `json:"exchange"`
	Industry          string  `json:"industry"`
	Sector            string  `json:"sector"`
	Country           string  `json:"country"`
	MarketCap         int64   `json:"marketCap"`
	Price             float64 `json:"price"`
	CEO               string  `json:"ceo"`
	Description       string  `json:"description"`
	Website           string  `json:"website"`
	IPODate           string  `json:"ipoDate"`
	FullTimeEmployees string  `json:"fullTimeEmployees"`
	IsActivelyTrading bool    `json:"isActivelyTrading"`
	IsEtf             bool    `json:"isEtf"`
	IsFund            bool    `json:"isFund"`
	IsAdr             bool    `json:"isAdr"`
}

// HistoricalPrice represents a historical price data point
type HistoricalPrice struct {
	Date     string  `json:"date"`
	Open     float64 `json:"open"`
	High     float64 `json:"high"`
	Low      float64 `json:"low"`
	Close    float64 `json:"close"`
	AdjClose float64 `json:"adjClose"`
	Volume   int64   `json:"volume"`
}

// HistoricalPriceResponse wraps the historical price data
type HistoricalPriceResponse struct {
	Symbol     string            `json:"symbol"`
	Historical []HistoricalPrice `json:"historical"`
}

// GetProfile fetches the company profile for a ticker
func (c *Client) GetProfile(ticker string) (*Profile, error) {
	var profiles []Profile
	params := map[string]string{
		"symbol": ticker,
	}

	if err := c.apiGet("stable/profile", params, &profiles); err != nil {
		return nil, err
	}

	if len(profiles) == 0 {
		return nil, &NotFoundError{Ticker: ticker}
	}

	return &profiles[0], nil
}

// GetHistoricalPrices fetches historical price data for a ticker
func (c *Client) GetHistoricalPrices(ticker string, from, to time.Time) (*HistoricalPriceResponse, error) {
	params := map[string]string{
		"from": from.Format("2006-01-02"),
		"to":   to.Format("2006-01-02"),
	}

	var response HistoricalPriceResponse
	endpoint := fmt.Sprintf("api/v3/historical-price-full/%s", ticker)

	if err := c.apiGet(endpoint, params, &response); err != nil {
		return nil, err
	}

	return &response, nil
}

// FetchStockList fetches the complete list of stocks from FMP
func (c *Client) FetchStockList() ([]Stock, error) {
	var stocks []Stock
	params := map[string]string{}

	if err := c.apiGet("stable/stock-list", params, &stocks); err != nil {
		return nil, err
	}

	return stocks, nil
}
