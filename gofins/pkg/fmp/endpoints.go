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

// Symbol represents a symbol (stock or index) from FMP
type Symbol struct {
	Symbol   string `json:"symbol"`
	Name     string `json:"name"`
	Exchange string `json:"exchange"`
}

// IsIndex returns true if the symbol is an index (ticker starts with ^)
func (s *Symbol) IsIndex() bool {
	return len(s.Symbol) > 0 && s.Symbol[0] == '^'
}

// Profile represents a company profile from FMP
type Profile struct {
	Symbol            string  `json:"symbol"`
	CompanyName       string  `json:"companyName"`
	Exchange          string  `json:"exchange"`
	Currency          string  `json:"currency"`
	Industry          string  `json:"industry"`
	Sector            string  `json:"sector"`
	Country           string  `json:"country"`
	CIK               string  `json:"cik"`
	MarketCap         float64 `json:"marketCap"` // Changed to float64 as FMP returns decimals
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
func GetProfile(ticker string) (*Profile, error) {
	c := Fmp()
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

// GetProfileByCIK fetches the primary listing profile for a company by CIK
func GetProfileByCIK(cik string) (*Profile, error) {
	c := Fmp()
	var profiles []Profile
	params := map[string]string{
		"cik": cik,
	}

	if err := c.apiGet("stable/profile-cik", params, &profiles); err != nil {
		return nil, err
	}

	if len(profiles) == 0 {
		return nil, &NotFoundError{Ticker: cik}
	}

	return &profiles[0], nil
}

// GetHistoricalPrices fetches historical price data for a ticker
func GetHistoricalPrices(ticker string, from, to time.Time) (*HistoricalPriceResponse, error) {
	c := Fmp()
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
func FetchStockList() ([]Symbol, error) {
	c := Fmp()
	var symbols []Symbol
	params := map[string]string{}

	if err := c.apiGet("stable/stock-list", params, &symbols); err != nil {
		return nil, err
	}

	return symbols, nil
}

// FetchIndexList fetches the complete list of indices from FMP
func FetchIndexList() ([]Symbol, error) {
	c := Fmp()
	var symbols []Symbol
	params := map[string]string{}

	if err := c.apiGet("stable/index-list", params, &symbols); err != nil {
		return nil, err
	}

	return symbols, nil
}

// FetchDelistedCompanies fetches all delisted companies from FMP with pagination
func FetchDelistedCompanies() ([]Symbol, error) {
	c := Fmp()
	allDelisted := []Symbol{}
	page := 0
	limit := 100

	for {
		var pageResults []Symbol
		params := map[string]string{
			"page":  fmt.Sprintf("%d", page),
			"limit": fmt.Sprintf("%d", limit),
		}

		if err := c.apiGet("stable/delisted-companies", params, &pageResults); err != nil {
			return nil, fmt.Errorf("failed to fetch page %d: %w", page, err)
		}

		// If we got no results, we've reached the end
		if len(pageResults) == 0 {
			break
		}

		allDelisted = append(allDelisted, pageResults...)

		// If we got fewer results than the limit, we've reached the end
		if len(pageResults) < limit {
			break
		}

		page++
	}

	return allDelisted, nil
}
