package reset

import (
	"fmt"

	"github.com/flocko-motion/gofins/pkg/db"
	"github.com/flocko-motion/gofins/pkg/f"
	"github.com/flocko-motion/gofins/pkg/types"
	"github.com/spf13/cobra"
)

var oldestPriceCmd = &cobra.Command{
	Use:   "oldest-price",
	Short: "Recalculate oldest_price field for all symbols based on existing price data",
	RunE: func(cmd *cobra.Command, args []string) error {
		fmt.Println("Recalculating oldest_price for all symbols...")

		// Get all tickers
		tickers, err := db.GetAllTickers()
		if err != nil {
			return fmt.Errorf("failed to get tickers: %w", err)
		}

		fmt.Printf("Found %d symbols to process\n", len(tickers))

		updated := 0
		noData := 0
		failed := 0
		noDataSymbols := []string{}

		for i, ticker := range tickers {
			if i%100 == 0 && i > 0 {
				fmt.Printf("Progress: %d/%d (updated: %d, no data: %d, failed: %d)\n",
					i, len(tickers), updated, noData, failed)
			}

			// Get oldest monthly price for this ticker
			oldestDate, err := db.GetOldestPriceDate(ticker)
			if err != nil {
				_ = db.LogError("reset.oldest_price", "database", "Failed to query oldest price", f.Ptr(err.Error()))
				failed++
				continue
			}

			if oldestDate == nil {
				noData++
				noDataSymbols = append(noDataSymbols, ticker)
				continue
			}

			// Update the symbol with oldest_price
			if err := db.PutSymbols([]types.Symbol{{
				Ticker:      ticker,
				OldestPrice: oldestDate,
			}}); err != nil {
				_ = db.LogError("reset.oldest_price", "database", "Failed to update symbol", f.Ptr(err.Error()))
				failed++
				continue
			}

			updated++
		}

		fmt.Printf("\n Complete: %d updated, %d with no data, %d failed\n", updated, noData, failed)

		// Print symbols with no data
		if len(noDataSymbols) > 0 {
			fmt.Printf("\nSymbols with no price data (%d total):\n", len(noDataSymbols))

			// Print first 100
			limit := 100
			if len(noDataSymbols) < limit {
				limit = len(noDataSymbols)
			}

			for i := 0; i < limit; i++ {
				fmt.Printf("  %s\n", noDataSymbols[i])
			}

			if len(noDataSymbols) > 100 {
				fmt.Printf("  ... and %d more\n", len(noDataSymbols)-100)
			}
		}

		return nil
	},
}

func init() {
	Cmd.AddCommand(oldestPriceCmd)
}
