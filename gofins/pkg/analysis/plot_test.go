package analysis

import (
	"testing"
	"time"

	"github.com/flocko-motion/gofins/pkg/db"
)

func TestPlot(t *testing.T) {
	// Connect to database
	database, err := db.NewDB()
	if err != nil {
		t.Fatalf("Failed to connect to DB: %v", err)
	}
	defer database.Close()

	to := time.Now()
	from := time.Date(2009, 1, 1, 0, 0, 0, 0, time.UTC)

	const symbol = "AIG"

	prices, err := database.GetWeeklyPrices(symbol, from, to)
	if err != nil {
		t.Fatalf("Failed to fetch prices: %v", err)
	}

	if len(prices) == 0 {
		t.Skip("No price data for " + symbol)
	}

	t.Logf("Fetched %d price points for %s", len(prices), symbol)

	// Analyze YoY
	histConfig := HistogramConfig{
		NumBins: 100,
		Min:     -80.0,
		Max:     80.0,
	}

	stats := AnalyzeYoY(prices, histConfig)

	t.Logf("YoY Stats: Count=%d, Mean=%.2f%%, StdDev=%.2f%%, Range=[%.2f%%, %.2f%%]",
		stats.Count, stats.Mean, stats.StdDev, stats.Min, stats.Max)

	// Generate plots
	pricePath := "/tmp/aapl_price_chart.png"
	histPath := "/tmp/aapl_histogram.png"

	if err := PlotYoYAnalysis(symbol, prices, stats, pricePath); err != nil {
		t.Fatalf("Failed to generate price plot: %v", err)
	}

	if err := PlotHistogram(symbol, stats, histPath); err != nil {
		t.Fatalf("Failed to generate histogram: %v", err)
	}

	t.Logf("Price plot saved to: %s", pricePath)
	t.Logf("Histogram saved to: %s", histPath)
}
