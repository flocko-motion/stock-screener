package analysis

import (
	"testing"
)

func TestOutlierMethods(t *testing.T) {
	// Simulated YoY percentage data with extreme outliers from near-zero prices
	yoyData := []float64{
		-50, -20, -10, -5, 0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50,
		136499900.0, // Extreme outlier from price near zero
	}

	t.Run("Original percentile method", func(t *testing.T) {
		result := RemoveOutliers(yoyData, 75)
		t.Logf("Percentile (75%%): removed %d values, kept %d", len(yoyData)-len(result), len(result))
		t.Logf("Result: %v", result)
	})

	t.Run("IQR method - moderate", func(t *testing.T) {
		result := RemoveOutliersIQR(yoyData, 1.5)
		t.Logf("IQR (1.5x): removed %d values, kept %d", len(yoyData)-len(result), len(result))
		t.Logf("Result: %v", result)
	})

	t.Run("IQR method - conservative", func(t *testing.T) {
		result := RemoveOutliersIQR(yoyData, 3.0)
		t.Logf("IQR (3.0x): removed %d values, kept %d", len(yoyData)-len(result), len(result))
		t.Logf("Result: %v", result)
	})

	t.Run("StdDev method", func(t *testing.T) {
		result := RemoveOutliersStdDev(yoyData, 2.0)
		t.Logf("StdDev (2.0σ): removed %d values, kept %d", len(yoyData)-len(result), len(result))
		t.Logf("Result: %v", result)
	})

	t.Run("Absolute bounds", func(t *testing.T) {
		result := RemoveOutliersAbsolute(yoyData, -100.0, 1000.0)
		t.Logf("Absolute (-100%% to 1000%%): removed %d values, kept %d", len(yoyData)-len(result), len(result))
		t.Logf("Result: %v", result)
	})

	t.Run("Winsorization", func(t *testing.T) {
		result := WinsorizeOutliers(yoyData, 5, 95)
		t.Logf("Winsorize (5-95%%): capped values, kept all %d", len(result))
		t.Logf("Result: %v", result)
	})

	t.Run("Recommended combined approach", func(t *testing.T) {
		result := BalancedYoYOutlierRemoval(yoyData)
		t.Logf("Recommended: removed %d values, kept %d", len(yoyData)-len(result), len(result))
		t.Logf("Result: %v", result)
	})
}

func TestIQRWithRealisticYoYData(t *testing.T) {
	// More realistic YoY data with a few extreme outliers
	yoyData := []float64{
		-80, -60, -40, -30, -20, -15, -10, -5, 0, 2, 5, 8, 10, 12, 15,
		18, 20, 25, 30, 35, 40, 50, 60, 80, 100, 150, 200,
		15000, // Extreme outlier from near-zero price
	}

	result := RemoveOutliersIQR(yoyData, 1.5)

	if len(result) == 0 {
		t.Error("IQR removed all values")
	}

	// Check that extreme outlier was removed
	hasExtreme := false
	for _, v := range result {
		if v > 10000 {
			hasExtreme = true
			break
		}
	}

	if hasExtreme {
		t.Error("IQR failed to remove extreme outlier")
	}

	t.Logf("IQR kept %d/%d values", len(result), len(yoyData))
}

func TestAbsoluteBoundsForYoY(t *testing.T) {
	yoyData := []float64{
		-150, // Impossible: can't lose more than 100%
		-50, 0, 50, 100, 200,
		50000, // Likely error: 500x growth
	}

	result := RemoveOutliersAbsolute(yoyData, -100.0, 1000.0)

	if len(result) != 5 {
		t.Errorf("Expected 5 values after absolute filtering, got %d", len(result))
	}

	// Verify bounds
	for _, v := range result {
		if v < -100 || v > 1000 {
			t.Errorf("Value %f outside bounds [-100, 1000]", v)
		}
	}
}

func TestWinsorization(t *testing.T) {
	values := []float64{1, 2, 3, 4, 5, 6, 7, 8, 9, 100}

	result := WinsorizeOutliers(values, 10, 90)

	// Should keep all values but cap the extreme ones
	if len(result) != len(values) {
		t.Errorf("Winsorization should keep all values, got %d instead of %d", len(result), len(values))
	}

	// The extreme value (100) should be capped
	maxVal := result[0]
	for _, v := range result {
		if v > maxVal {
			maxVal = v
		}
	}

	if maxVal == 100 {
		t.Error("Extreme value was not capped by winsorization")
	}

	t.Logf("Original max: 100, Winsorized max: %f", maxVal)
}
