package types

import "time"

// Symbol represents a stock symbol in the database
type Symbol struct {
	Ticker            string     `json:"ticker"`
	Exchange          *string    `json:"exchange,omitempty"`
	LastPriceUpdate   *time.Time `json:"lastPriceUpdate,omitempty"`
	LastProfileUpdate *time.Time `json:"lastProfileUpdate,omitempty"`
	LastPriceStatus   *string    `json:"lastPriceStatus,omitempty"`
	LastProfileStatus *string    `json:"lastProfileStatus,omitempty"`
	Name              *string    `json:"name,omitempty"`
	Type              *string    `json:"type,omitempty"`
	Currency          *string    `json:"currency,omitempty"`
	Sector            *string    `json:"sector,omitempty"`
	Industry          *string    `json:"industry,omitempty"`
	Country           *string    `json:"country,omitempty"`
	Description       *string    `json:"description,omitempty"`
	Website           *string    `json:"website,omitempty"`
	ISIN              *string    `json:"isin,omitempty"`
	CIK               *string    `json:"cik,omitempty"`
	Inception         *time.Time `json:"inception,omitempty"`
	OldestPrice       *time.Time `json:"oldestPrice,omitempty"`
	IsActivelyTrading *bool      `json:"isActivelyTrading,omitempty"`
	MarketCap         *int64     `json:"marketCap,omitempty"`
	PrimaryListing    *string    `json:"primaryListing,omitempty"`
	Ath12M            *float64   `json:"ath12m,omitempty"`
	CurrentPriceUsd   *float64   `json:"currentPriceUsd,omitempty"`
	CurrentPriceTime  *time.Time `json:"currentPriceTime,omitempty"`
	IsFavorite        bool       `json:"isFavorite"`
	UserRating        *int       `json:"userRating,omitempty"`
}

// Symbol types
const (
	TypeStock = "stock"
	TypeETF   = "etf"
	TypeFund  = "fund"
	TypeADR   = "adr"
	TypeIndex = "index"
	// Note: Secondary listings are now identified by the PrimaryListing field
	// rather than a separate type, so they maintain their TypeStock classification
)

// PriceUpdateTypes defines which symbol types should receive price updates
var PriceUpdateTypes = []string{TypeStock, TypeADR, TypeIndex}
