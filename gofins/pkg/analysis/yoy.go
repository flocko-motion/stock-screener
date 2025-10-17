package analysis

import (
	"github.com/flocko-motion/gofins/pkg/types"
)

// AnalyzeYoY performs statistical analysis on Year-over-Year data from price data
// Only processes entries that have a non-nil YoY value
func AnalyzeYoY(prices []types.PriceData, histConfig HistogramConfig) Stats {
	// Extract non-nil YoY values
	yoyValues := make([]float64, 0, len(prices))
	for _, p := range prices {
		if p.YoY != nil {
			yoyValues = append(yoyValues, *p.YoY)
		}
	}

	return Calculate(BalancedYoYOutlierRemoval(yoyValues), histConfig)
}
