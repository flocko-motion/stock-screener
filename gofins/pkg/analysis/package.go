package analysis

import (
	"fmt"
	"os"
	"path/filepath"
	"time"

	"github.com/flocko-motion/gofins/pkg/db"
	"github.com/flocko-motion/gofins/pkg/types"
	"github.com/flocko-motion/gofins/pkg/f"
	"github.com/google/uuid"
)

func logf(format string, args ...interface{}) {
	fmt.Printf("[ANALYSIS] "+format, args...)
}

// AnalysisPackageConfig defines the parameters for creating an analysis package
type AnalysisPackageConfig struct {
	PackageID    string
	Name         string
	UserID       uuid.UUID
	Interval     types.PriceInterval
	TimeFrom     time.Time
	TimeTo       time.Time
	HistConfig   HistogramConfig
	McapMin      *int64
	InceptionMax *time.Time
	Tickers      []string
	PathPlots    string
	SaveToDB     bool // If true, save results to database during batch analysis
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

func PathPlots(packageID string) string {
	return filepath.Join(f.First(os.UserHomeDir()), "gofins", "plots", packageID)
}

func PathPlot(packageID string, plotType PlotType, ticker string) string {
	fname := fmt.Sprintf("%s_%s.png", ticker, plotType)
	return filepath.Join(PathPlots(packageID), fname)
}

type PlotType string

const (
	PlotTypeChart     PlotType = "chart"
	PlotTypeHistogram PlotType = "histogram"
)

// CreatePackage creates a new analysis package and processes all symbols
func CreatePackage(database *db.DB, config AnalysisPackageConfig) (string, error) {
	// Generate package ID
	config.PackageID = uuid.New().String()
	config.PathPlots = PathPlots(config.PackageID)

	// Create package metadata
	pkg := &types.AnalysisPackage{
		ID:           config.PackageID,
		Name:         config.Name,
		CreatedAt:    time.Now(),
		Interval:     string(config.Interval),
		TimeFrom:     config.TimeFrom,
		TimeTo:       config.TimeTo,
		HistBins:     config.HistConfig.NumBins,
		HistMin:      config.HistConfig.Min,
		HistMax:      config.HistConfig.Max,
		UserID:       config.UserID,
		McapMin:      config.McapMin,
		InceptionMax: config.InceptionMax,
		Status:       "processing",
	}

	if err := db.CreateAnalysisPackage(pkg); err != nil {
		return "", err
	}

	go processPackage(config)

	return config.PackageID, nil
}

func processPackage(config AnalysisPackageConfig) {
	var err error
	logf("Starting package processing: %s (ID: %s)\n", config.Name, config.PackageID)
	logf("%s config raw: %+v\n", config.PackageID, config)
	logf("%s Config: Interval=%s, TimeFrom=%s, TimeTo=%s, McapMin=%s, InceptionMax=%s, HistBins(min/max/bins)=%f/%f/%d\n",
		config.PackageID,
		config.Interval, config.TimeFrom.Format("2006-01-02"), config.TimeTo.Format("2006-01-02"),
		f.MaybeToString(config.McapMin, "<nil>"),
		f.MaybeToString(config.InceptionMax, "<nil>"),
		config.HistConfig.Min, config.HistConfig.Max, config.HistConfig.NumBins)

	if config.McapMin != nil {
		logf("%s Market cap filter: >= %d\n", config.PackageID, *config.McapMin)
	}
	if config.InceptionMax != nil {
		logf("%s Inception filter: <= %s\n", config.PackageID, config.InceptionMax.Format("2006-01-02"))
	}

	logf("%s Fetching filtered tickers...\n", config.PackageID)
	config.Tickers, err = db.GetFilteredTickers(config.McapMin, config.InceptionMax)
	if err != nil {
		logf("ERROR: Failed to get filtered tickers: %v\n", err)
		db.UpdateAnalysisPackageStatus(config.UserID, config.PackageID, "failed", 0)
		return
	}

	logf("%s Found %d tickers to analyze\n", config.PackageID, len(config.Tickers))
	if len(config.Tickers) > 0 {
		sampleSize := min(5, len(config.Tickers))
		logf("%s First %d tickers: %v\n", config.PackageID, sampleSize, config.Tickers[:sampleSize])
	} else {
		logf("%s WARNING: No tickers found, nothing to analyze\n", config.PackageID)
		db.UpdateAnalysisPackageStatus(config.UserID, config.PackageID, "ready", 0)
		return
	}

	logf("%s Starting batch analysis of %d symbols...\n", config.PackageID, len(config.Tickers))
	config.SaveToDB = true // Enable database saving
	startTime := time.Now()
	results, err := AnalyzeBatch(config)
	if err != nil {
		logf("%s ERROR: Batch analysis failed: %v\n", config.PackageID, err)
		db.UpdateAnalysisPackageStatus(config.UserID, config.PackageID, "failed", 0)
		return
	}
	elapsed := time.Since(startTime)

	logf("%s Batch analysis completed in %v (%d results)\n", config.PackageID, elapsed, len(results))
	if len(results) > 0 {
		logf("%s Throughput: %.1f symbols/sec\n", config.PackageID, float64(len(results))/elapsed.Seconds())
	}

	logf("%s Package processing complete: %d results\n", config.PackageID, len(results))
	db.UpdateAnalysisPackageStatus(config.UserID, config.PackageID, "ready", len(results))
	logf("%s Package %s is now ready\n", config.PackageID, config.PackageID)
}
