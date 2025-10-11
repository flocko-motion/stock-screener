package fmp

import (
	"fmt"
	"strconv"
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
	MarketCap         float64 `json:"mktCap"`
	Price             float64 `json:"price"`
	CEO               string  `json:"ceo"`
	Description       string  `json:"description"`
	Website           string  `json:"website"`
	IPODate           string  `json:"ipoDate"`
	FullTimeEmployees string  `json:"fullTimeEmployees"`
}

// Quote represents a stock quote
type Quote struct {
	Symbol        string  `json:"symbol"`
	Name          string  `json:"name"`
	Price         float64 `json:"price"`
	Change        float64 `json:"change"`
	PercentChange float64 `json:"changesPercentage"`
	DayLow        float64 `json:"dayLow"`
	DayHigh       float64 `json:"dayHigh"`
	YearLow       float64 `json:"yearLow"`
	YearHigh      float64 `json:"yearHigh"`
	MarketCap     float64 `json:"marketCap"`
	Volume        int64   `json:"volume"`
	AvgVolume     int64   `json:"avgVolume"`
	Open          float64 `json:"open"`
	PreviousClose float64 `json:"previousClose"`
	Timestamp     int64   `json:"timestamp"`
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

// ScreenResult represents a single result from the stock screener
type ScreenResult struct {
	Symbol    string  `json:"symbol"`
	Name      string  `json:"companyName"`
	MarketCap float64 `json:"marketCap"`
	Sector    string  `json:"sector"`
	Industry  string  `json:"industry"`
	Country   string  `json:"country"`
	Exchange  string  `json:"exchangeShortName"`
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

// GetQuote fetches the real-time quote for a ticker
func (c *Client) GetQuote(ticker string) (*Quote, error) {
	var quotes []Quote
	params := map[string]string{
		"symbol": ticker,
	}

	if err := c.apiGet("api/v3/quote/"+ticker, params, &quotes); err != nil {
		return nil, err
	}

	if len(quotes) == 0 {
		return nil, fmt.Errorf("no quote found for ticker: %s", ticker)
	}

	return &quotes[0], nil
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

// ScreenParams contains parameters for the stock screener
type ScreenParams struct {
	MarketCapMin *int64
	MarketCapMax *int64
	Type         string // "all", "stock", "etf", "fund"
	Sector       string
	Industry     string
	Country      string
	Exchange     string
	Limit        int
}

// Screen performs a stock screen with the given parameters
func (c *Client) Screen(params ScreenParams) ([]string, error) {
	apiParams := make(map[string]string)

	if params.Limit > 0 {
		apiParams["limit"] = strconv.Itoa(params.Limit)
	} else {
		apiParams["limit"] = "1000"
	}

	if params.MarketCapMin != nil {
		apiParams["marketCapMoreThan"] = strconv.FormatInt(*params.MarketCapMin, 10)
	}

	if params.MarketCapMax != nil {
		apiParams["marketCapLowerThan"] = strconv.FormatInt(*params.MarketCapMax, 10)
	}

	switch params.Type {
	case "etf":
		apiParams["isEtf"] = "true"
	case "fund":
		apiParams["isFund"] = "true"
	case "stock":
		apiParams["isStock"] = "true"
	}

	if params.Sector != "" {
		apiParams["sector"] = params.Sector
	}

	if params.Industry != "" {
		apiParams["industry"] = params.Industry
	}

	if params.Country != "" {
		apiParams["country"] = params.Country
	}

	if params.Exchange != "" {
		apiParams["exchange"] = params.Exchange
	}

	var results []ScreenResult
	if err := c.apiGet("stable/company-screener", apiParams, &results); err != nil {
		return nil, err
	}

	// Extract symbols
	symbols := make([]string, len(results))
	for i, result := range results {
		symbols[i] = result.Symbol
	}

	return symbols, nil
}

// Search searches for companies by query string
func (c *Client) Search(query string) ([]ScreenResult, error) {
	params := map[string]string{
		"query": query,
	}

	var results []ScreenResult
	if err := c.apiGet("api/v3/search", params, &results); err != nil {
		return nil, err
	}

	return results, nil
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
