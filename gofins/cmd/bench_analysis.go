package cmd

import (
	"fmt"
	"time"

	"github.com/flocko-motion/gofins/pkg/analysis"
	"github.com/flocko-motion/gofins/pkg/db"
	"github.com/flocko-motion/gofins/pkg/types"
	"github.com/spf13/cobra"
)

var benchAnalysisCmd = &cobra.Command{
	Use:   "bench-analysis",
	Short: "Benchmark YoY analysis performance",
	RunE: func(cmd *cobra.Command, args []string) error {
		// Get 100 stocks that have price data
		tickers, err := db.GetTickersWithPrices(100)
		if err != nil {
			return fmt.Errorf("failed to get tickers: %w", err)
		}

		if len(tickers) == 0 {
			fmt.Println("No symbols with price data found!")
			return nil
		}

		fmt.Printf("Benchmarking YoY analysis on %d symbols...\n", len(tickers))
		fmt.Printf("First few tickers: %v\n", tickers[:min(5, len(tickers))])

		// Histogram config: 2.5% bins from -50% to +100%
		histConfig := analysis.HistogramConfig{
			NumBins: int((100 - (-50)) / 2.5), // 150 / 2.5 = 60 bins
			Min:     -50.0,
			Max:     100.0,
		}

		fmt.Printf("Histogram: %d bins, range [%.1f%%, %.1f%%]\n\n",
			histConfig.NumBins, histConfig.Min, histConfig.Max)

		// Time range for prices
		to := time.Now()
		from := to.AddDate(-5, 0, 0)

		// ===== Method 1: Individual queries =====
		fmt.Println("=== Method 1: Individual Queries ===")
		startIndividual := time.Now()
		successCount := 0

		for i, ticker := range tickers {
			prices, err := db.GetMonthlyPrices(ticker, from, to)
			if err != nil {
				if i < 5 {
					errMsg := fmt.Sprintf("Error fetching prices for %s: %v", ticker, err)
					_ = db.LogError("bench.analysis", "database", "Failed to fetch prices", &errMsg)
				}
				continue
			}
			if len(prices) == 0 {
				if i < 5 {
					fmt.Printf("[%s] No prices found\n", ticker)
				}
				continue
			}

			// Analyze YoY
			start := time.Now()
			stats := analysis.AnalyzeYoY(prices, histConfig)
			elapsed := time.Since(start)

			if i < 5 {
				fmt.Printf("[%s] Prices: %d, YoY count: %d\n", ticker, len(prices), stats.Count)
			}

			if stats.Count > 0 {
				successCount++
				if i < 5 { // Show details for first 5
					fmt.Printf("[%s] %d datapoints | Mean: %.2f%% | StdDev: %.2f%% | Range: [%.2f%%, %.2f%%] | Time: %v\n",
						ticker, stats.Count, stats.Mean, stats.StdDev, stats.Min, stats.Max, elapsed)
				}
			}
		}

		individualElapsed := time.Since(startIndividual)
		individualSuccess := successCount

		fmt.Printf("Processed: %d symbols\n", individualSuccess)
		fmt.Printf("Total time: %v\n", individualElapsed)
		if individualSuccess > 0 {
			fmt.Printf("Average per symbol: %v\n", individualElapsed/time.Duration(individualSuccess))
			fmt.Printf("Throughput: %.1f symbols/sec\n\n", float64(individualSuccess)/individualElapsed.Seconds())
		}

		// ===== Method 2: Batch Analysis =====
		fmt.Println("=== Method 2: Batch Analysis ===")
		startBatch := time.Now()

		results, err := analysis.AnalyzeBatch(analysis.AnalysisPackageConfig{
			Tickers:    tickers,
			TimeFrom:   from,
			TimeTo:     to,
			Interval:   types.IntervalMonthly,
			HistConfig: histConfig,
		})
		if err != nil {
			return fmt.Errorf("failed to batch analyze: %w", err)
		}

		// Show first 5 results
		for i, result := range results {
			if i < 5 {
				fmt.Printf("[%s] %d datapoints | Mean: %.2f%% | StdDev: %.2f%%\n",
					result.Ticker, result.Stats.Count, result.Stats.Mean, result.Stats.StdDev)
			}
		}

		batchElapsed := time.Since(startBatch)
		batchSuccess := len(results)

		fmt.Printf("Processed: %d symbols\n", batchSuccess)
		fmt.Printf("Total time: %v\n", batchElapsed)
		if batchSuccess > 0 {
			fmt.Printf("Average per symbol: %v\n", batchElapsed/time.Duration(batchSuccess))
			fmt.Printf("Throughput: %.1f symbols/sec\n\n", float64(batchSuccess)/batchElapsed.Seconds())
		}

		// ===== Comparison =====
		fmt.Println("=== Comparison ===")
		if individualSuccess > 0 && batchSuccess > 0 {
			speedup := float64(individualElapsed) / float64(batchElapsed)
			fmt.Printf("Batch is %.2fx faster than individual queries\n", speedup)
		}

		return nil
	},
}

func init() {
	rootCmd.AddCommand(benchAnalysisCmd)
}
