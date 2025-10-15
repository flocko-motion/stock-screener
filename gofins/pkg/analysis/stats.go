package analysis

import (
	"math"
)

// Stats contains comprehensive statistical measures
type Stats struct {
	Count           int
	Mean            float64
	Variance        float64
	StdDev          float64
	Min             float64
	Max             float64
	Histogram       []HistogramBin
	HistogramConfig HistogramConfig
}

// Calculate performs all statistical calculations in a single pass
func Calculate(values []float64, histConfig HistogramConfig) Stats {
	if len(values) == 0 {
		return Stats{}
	}

	// First pass: calculate sum, min, max
	sum := 0.0
	min := values[0]
	max := values[0]

	for _, v := range values {
		sum += v
		if v < min {
			min = v
		}
		if v > max {
			max = v
		}
	}

	mean := sum / float64(len(values))

	// Second pass: calculate variance and histogram
	sumSquaredDiff := 0.0
	histogram := initHistogram(histConfig)

	for _, v := range values {
		// Variance calculation
		diff := v - mean
		sumSquaredDiff += diff * diff

		// Histogram binning
		addToHistogram(histogram, v, histConfig)
	}

	variance := sumSquaredDiff / float64(len(values))

	return Stats{
		Count:           len(values),
		Mean:            mean,
		Variance:        variance,
		StdDev:          math.Sqrt(variance),
		Min:             min,
		Max:             max,
		Histogram:       histogram,
		HistogramConfig: histConfig,
	}
}

// HistogramConfig defines the configuration for histogram generation
type HistogramConfig struct {
	NumBins    int     // Number of bins
	Min        float64 // Minimum value (values below go to first bin)
	Max        float64 // Maximum value (values above go to last bin)
	Percentile int     // which percentile to use for outlier removal
}

// HistogramBin represents a single bin in a histogram
type HistogramBin struct {
	Min   float64 // Lower bound (inclusive)
	Max   float64 // Upper bound (exclusive, except for last bin)
	Count int     // Number of values in this bin
}

// initHistogram initializes histogram bins with zero counts
func initHistogram(config HistogramConfig) []HistogramBin {
	if config.NumBins <= 0 {
		return nil
	}

	bins := make([]HistogramBin, config.NumBins)
	binWidth := (config.Max - config.Min) / float64(config.NumBins)

	for i := 0; i < config.NumBins; i++ {
		bins[i].Min = config.Min + float64(i)*binWidth
		bins[i].Max = config.Min + float64(i+1)*binWidth
		bins[i].Count = 0
	}

	return bins
}

// addToHistogram adds a value to the appropriate histogram bin
func addToHistogram(bins []HistogramBin, value float64, config HistogramConfig) {
	if len(bins) == 0 {
		return
	}

	// Check for invalid values (NaN, Inf)
	if math.IsNaN(value) || math.IsInf(value, 0) {
		// Skip invalid values
		return
	}

	binWidth := (config.Max - config.Min) / float64(config.NumBins)
	var binIndex int

	if value < config.Min {
		// Outlier below min -> first bin
		binIndex = 0
	} else if value >= config.Max {
		// Outlier above max -> last bin
		binIndex = config.NumBins - 1
	} else {
		// Normal case: calculate bin index
		binIndex = int((value - config.Min) / binWidth)
		// Clamp to valid range (handles floating point edge cases and outliers)
		if binIndex < 0 {
			binIndex = 0
		}
		if binIndex >= config.NumBins {
			binIndex = config.NumBins - 1
		}
	}

	bins[binIndex].Count++
}
