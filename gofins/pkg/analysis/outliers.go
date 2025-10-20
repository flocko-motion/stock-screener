package analysis

import (
	"math"
	"sort"
)

// BalancedYoYOutlierRemoval demonstrates the recommended approach for YoY data.
// This combines multiple strategies for robust outlier handling.
func BalancedYoYOutlierRemoval(yoyPercentages []float64) []float64 {
	// Strategy 1: First remove impossible values (e.g., > 10000% or < -100%)
	// YoY can't be less than -100% (complete loss) and values > 10000% are likely errors
	filtered := RemoveOutliersAbsolute(yoyPercentages, -100.0, 10000.0)

	// Strategy 2: Then use IQR method to remove statistical outliers
	// Using multiplier=1.5 for moderate outlier removal
	// This handles cases where prices near zero cause extreme but "valid" percentages
	filtered = RemoveOutliersIQR(filtered, 1.5)

	return filtered
}

// ConservativeYoYOutlierRemoval uses a more conservative approach.
// Only removes the most extreme outliers.
func ConservativeYoYOutlierRemoval(yoyPercentages []float64) []float64 {
	// Use absolute bounds with wider range
	filtered := RemoveOutliersAbsolute(yoyPercentages, -100.0, 50000.0)

	// Use IQR with higher multiplier (only extreme outliers)
	filtered = RemoveOutliersIQR(filtered, 3.0)

	return filtered
}

// WinsorizedYoYData caps extreme values instead of removing them.
// This preserves data points while limiting their impact on statistics.
// Good when you want to keep all data points but reduce outlier influence.
func WinsorizedYoYData(yoyPercentages []float64) []float64 {
	// First apply absolute bounds
	filtered := RemoveOutliersAbsolute(yoyPercentages, -100.0, 10000.0)

	// Then winsorize at 5th and 95th percentiles
	return WinsorizeOutliers(filtered, 5, 95)
}

// RemoveOutliers removes the specified percentile of values from both ends of the array.
// For example, if percentile is 75, then 25% of data points are removed (12.5% from each end).
// The number of elements to remove from each side is rounded up.
func RemoveOutliers(values []float64, percentile int) []float64 {
	if len(values) == 0 || percentile <= 0 || percentile >= 100 {
		return values
	}

	// Make a copy and sort it
	sorted := make([]float64, len(values))
	copy(sorted, values)
	sort.Float64s(sorted)

	// Calculate percentage to remove from each end
	removePercent := float64(100-percentile) / 2.0 / 100.0

	// Calculate number of elements to remove from each end (rounded up)
	removeCount := int(math.Ceil(float64(len(sorted)) * removePercent))

	// If we would remove all or more elements, return empty slice
	if removeCount*2 >= len(sorted) {
		return []float64{}
	}

	// Return the middle portion
	return sorted[removeCount : len(sorted)-removeCount]
}

// RemoveOutliersIQR removes outliers using the Interquartile Range (IQR) method.
// This is more robust for data with extreme outliers like YoY percentages.
// Values outside [Q1 - multiplier*IQR, Q3 + multiplier*IQR] are removed.
// A typical multiplier is 1.5 (moderate) or 3.0 (only extreme outliers).
func RemoveOutliersIQR(values []float64, multiplier float64) []float64 {
	if len(values) < 4 {
		return values
	}

	// Sort the values
	sorted := make([]float64, len(values))
	copy(sorted, values)
	sort.Float64s(sorted)

	// Calculate Q1 (25th percentile) and Q3 (75th percentile)
	q1Index := len(sorted) / 4
	q3Index := (3 * len(sorted)) / 4
	q1 := sorted[q1Index]
	q3 := sorted[q3Index]

	iqr := q3 - q1
	lowerBound := q1 - multiplier*iqr
	upperBound := q3 + multiplier*iqr

	// Filter values within bounds
	result := make([]float64, 0, len(values))
	for _, v := range sorted {
		if v >= lowerBound && v <= upperBound {
			result = append(result, v)
		}
	}

	return result
}

// RemoveOutliersStdDev removes outliers using standard deviation method.
// Values outside [mean - numStdDev*stddev, mean + numStdDev*stddev] are removed.
// Typical values: 2.0 (95% confidence) or 3.0 (99.7% confidence).
func RemoveOutliersStdDev(values []float64, numStdDev float64) []float64 {
	if len(values) < 2 {
		return values
	}

	// Calculate mean
	sum := 0.0
	for _, v := range values {
		sum += v
	}
	mean := sum / float64(len(values))

	// Calculate standard deviation
	sumSquaredDiff := 0.0
	for _, v := range values {
		diff := v - mean
		sumSquaredDiff += diff * diff
	}
	stdDev := math.Sqrt(sumSquaredDiff / float64(len(values)))

	// Filter values within bounds
	lowerBound := mean - numStdDev*stdDev
	upperBound := mean + numStdDev*stdDev

	result := make([]float64, 0, len(values))
	for _, v := range values {
		if v >= lowerBound && v <= upperBound {
			result = append(result, v)
		}
	}

	return result
}

// RemoveOutliersAbsolute removes values outside absolute min/max bounds.
// Useful for YoY percentage data where you know reasonable limits.
// For example, minValue=-100 (can't lose more than 100%) and maxValue=1000 (10x growth cap).
func RemoveOutliersAbsolute(values []float64, minValue, maxValue float64) []float64 {
	if len(values) == 0 {
		return values
	}

	result := make([]float64, 0, len(values))
	for _, v := range values {
		if v >= minValue && v <= maxValue {
			result = append(result, v)
		}
	}

	return result
}

// WinsorizeOutliers caps extreme values instead of removing them.
// Values below the lower percentile are set to that percentile value.
// Values above the upper percentile are set to that percentile value.
// For example, percentileLow=5, percentileHigh=95 caps the extreme 5% on each end.
func WinsorizeOutliers(values []float64, percentileLow, percentileHigh int) []float64 {
	if len(values) == 0 || percentileLow >= percentileHigh {
		return values
	}

	// Sort to find percentile values
	sorted := make([]float64, len(values))
	copy(sorted, values)
	sort.Float64s(sorted)

	// Find percentile indices
	// For a 10-element array with percentileLow=10, percentileHigh=90:
	// - lowIndex should be 1 (10th percentile = index 1)
	// - highIndex should be 8 (90th percentile = index 8, not 9)
	lowIndex := int(math.Floor(float64(len(sorted)-1) * float64(percentileLow) / 100.0))
	highIndex := int(math.Floor(float64(len(sorted)-1) * float64(percentileHigh) / 100.0))

	if lowIndex < 0 {
		lowIndex = 0
	}
	if highIndex >= len(sorted) {
		highIndex = len(sorted) - 1
	}

	lowValue := sorted[lowIndex]
	highValue := sorted[highIndex]

	// Cap values in original order
	result := make([]float64, len(values))
	for i, v := range values {
		if v < lowValue {
			result[i] = lowValue
		} else if v > highValue {
			result[i] = highValue
		} else {
			result[i] = v
		}
	}

	return result
}
