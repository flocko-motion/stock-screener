package analysis

import (
	"encoding/json"
	"time"

	"github.com/flocko-motion/gofins/pkg/db"
	"github.com/google/uuid"
)

// AnalysisPackageConfig defines the parameters for creating an analysis package
type AnalysisPackageConfig struct {
	Name         string
	Interval     db.PriceInterval
	TimeFrom     time.Time
	TimeTo       time.Time
	HistConfig   HistogramConfig
	McapMin      *int64
	InceptionMax *time.Time
}

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
}

// AnalysisResult represents a single symbol's analysis result
type AnalysisResult struct {
	PackageID string
	Ticker    string
	Count     int
	Mean      float64
	StdDev    float64
	Variance  float64
	Min       float64
	Max       float64
	Histogram []HistogramBin
	ChartPath *string
}

// CreatePackage creates a new analysis package and processes all symbols
func CreatePackage(database *db.DB, config AnalysisPackageConfig) (string, error) {
	// Generate package ID
	packageID := uuid.New().String()

	// Create package metadata
	pkg := &db.AnalysisPackage{
		ID:           packageID,
		Name:         config.Name,
		CreatedAt:    time.Now(),
		Interval:     string(config.Interval),
		TimeFrom:     config.TimeFrom,
		TimeTo:       config.TimeTo,
		HistBins:     config.HistConfig.NumBins,
		HistMin:      config.HistConfig.Min,
		HistMax:      config.HistConfig.Max,
		McapMin:      config.McapMin,
		InceptionMax: config.InceptionMax,
		Status:       "processing",
	}

	if err := database.CreateAnalysisPackage(pkg); err != nil {
		return "", err
	}

	// Launch background processing
	go processPackage(database, packageID, config)

	return packageID, nil
}

func processPackage(database *db.DB, packageID string, config AnalysisPackageConfig) {
	// Get filtered tickers
	tickers, err := database.GetFilteredTickers(config.McapMin, config.InceptionMax)
	if err != nil {
		database.UpdateAnalysisPackageStatus(packageID, "failed", 0)
		return
	}

	// Batch analyze
	results, err := AnalyzeBatch(database, tickers, config.TimeFrom, config.TimeTo, config.Interval, config.HistConfig)
	if err != nil {
		database.UpdateAnalysisPackageStatus(packageID, "failed", 0)
		return
	}

	// Save results to database
	for _, result := range results {
		histogramJSON, _ := json.Marshal(result.Stats.Histogram)

		database.SaveAnalysisResult(
			packageID, result.Ticker,
			result.Stats.Count, result.Stats.Mean, result.Stats.StdDev, result.Stats.Variance,
			result.Stats.Min, result.Stats.Max, histogramJSON,
		)
	}

	// Update package status to 'ready'
	database.UpdateAnalysisPackageStatus(packageID, "ready", len(results))
}
