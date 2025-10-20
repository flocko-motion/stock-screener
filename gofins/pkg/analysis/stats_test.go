package analysis

import (
	"fmt"
	"math"
	"testing"
)

func TestRemoveOutliers(t *testing.T) {
	values := []float64{-171099218523, 2, 4, 6, 8, 10, 21323772474823882383232}
	values = RemoveOutliers(values, 90)
	fmt.Println(values)
	if len(values) != 5 {
		t.Errorf("Expected 5 values, got %d", len(values))
	}
}

func TestCalculate(t *testing.T) {
	values := []float64{2, 4, 6, 8, 10}
	config := HistogramConfig{
		NumBins: 5,
		Min:     0,
		Max:     12,
	}

	stats := Calculate(values, config)

	// Check mean
	if stats.Mean != 6.0 {
		t.Errorf("Mean = %v, want 6.0", stats.Mean)
	}

	// Check variance
	expectedVariance := 8.0
	if math.Abs(stats.Variance-expectedVariance) > 0.0001 {
		t.Errorf("Variance = %v, want %v", stats.Variance, expectedVariance)
	}

	// Check stddev
	expectedStdDev := math.Sqrt(8.0)
	if math.Abs(stats.StdDev-expectedStdDev) > 0.0001 {
		t.Errorf("StdDev = %v, want %v", stats.StdDev, expectedStdDev)
	}

	// Check min/max
	if stats.Min != 2 {
		t.Errorf("Min = %v, want 2", stats.Min)
	}

	if stats.Max != 10 {
		t.Errorf("Max = %v, want 10", stats.Max)
	}

	// Check count
	if stats.Count != 5 {
		t.Errorf("Count = %v, want 5", stats.Count)
	}
}

func TestHistogramWithOutliers(t *testing.T) {
	values := []float64{-15, -5, 0, 5, 10, 15, 25, 30, 105}
	config := HistogramConfig{
		NumBins: 5,
		Min:     0,
		Max:     100,
	}

	stats := Calculate(values, config)
	bins := stats.Histogram

	if len(bins) != 5 {
		t.Errorf("Expected 5 bins, got %d", len(bins))
	}

	// Bins are: [0,20), [20,40), [40,60), [60,80), [80,100)
	// Values: -15, -5 -> bin 0 (outliers)
	//         0, 5, 10, 15 -> bin 0 [0,20)
	//         25, 30 -> bin 1 [20,40)
	//         105 -> bin 4 (outlier)

	totalCount := 0
	for _, bin := range bins {
		totalCount += bin.Count
	}

	if totalCount != len(values) {
		t.Errorf("Total count across bins should be %d, got %d", len(values), totalCount)
	}

	// First bin should include low outliers plus values in [0,20)
	if bins[0].Count != 6 { // -15, -5, 0, 5, 10, 15
		t.Errorf("First bin should have 6 values, got %d", bins[0].Count)
	}

	// Last bin should have high outliers
	if bins[4].Count != 1 { // 105
		t.Errorf("Last bin should have 1 value (outlier), got %d", bins[4].Count)
	}
}
