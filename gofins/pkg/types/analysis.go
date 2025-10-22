package types

import (
	"time"

	"github.com/google/uuid"
)

// AnalysisPackage represents stored analysis metadata
type AnalysisPackage struct {
	ID           string
	Name         string
	CreatedAt    time.Time
	Interval     string
	TimeFrom     time.Time
	TimeTo       time.Time
	HistBins     int
	HistMin      float64
	HistMax      float64
	McapMin      *int64
	InceptionMax *time.Time
	SymbolCount  int
	Status       string
	UserID       uuid.UUID
}

// AnalysisResult represents a stored analysis result
type AnalysisResult struct {
	PackageID     string     `json:"-"`
	Ticker        string     `json:"symbol"`
	Count         int        `json:"-"`
	Mean          float64    `json:"mean"`
	StdDev        float64    `json:"stddev"`
	Variance      float64    `json:"-"`
	Min           float64    `json:"min"`
	Max           float64    `json:"max"`
	InceptionDate *time.Time `json:"inception"`
}
