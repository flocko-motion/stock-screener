package types

import "time"

// PriceData represents price data (daily, weekly, or monthly)
type PriceData struct {
	Date         time.Time
	Open         float64
	High         float64
	Low          float64
	Avg          float64
	Close        float64
	YoY          *float64
	SymbolTicker string
}
