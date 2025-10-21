package symbol

import (
	"fmt"
	"time"

	"github.com/flocko-motion/gofins/pkg/db"
	"github.com/spf13/cobra"
)

var (
	monthlyShowYoY bool
)

var monthlyCmd = &cobra.Command{
	Use:   "monthly [ticker]",
	Short: "Display monthly price history for a symbol",
	Args:  cobra.ExactArgs(1),
	RunE: func(cmd *cobra.Command, args []string) error {
		ticker := args[0]
		
		// Get all monthly prices (from beginning to now)
		from := time.Date(1900, 1, 1, 0, 0, 0, 0, time.UTC)
		to := time.Now()
		
		prices, err := db.GetMonthlyPrices(ticker, from, to)
		if err != nil {
			return fmt.Errorf("failed to get monthly prices: %w", err)
		}
		
		if len(prices) == 0 {
			fmt.Printf("No monthly price data found for %s\n", ticker)
			return nil
		}
		
		// Print header
		if monthlyShowYoY {
			fmt.Printf("%-12s %12s %12s\n", "Date", "Close", "YoY %")
			fmt.Println("----------------------------------------")
		} else {
			fmt.Printf("%-12s %12s\n", "Date", "Close")
			fmt.Println("---------------------------")
		}
		
		// Print prices
		for _, price := range prices {
			dateStr := price.Date.Format("2006-01-02")
			if monthlyShowYoY {
				yoyStr := "N/A"
				if price.YoY != nil {
					yoyStr = fmt.Sprintf("%.2f", *price.YoY)
				}
				fmt.Printf("%-12s %12.2f %12s\n", dateStr, price.Close, yoyStr)
			} else {
				fmt.Printf("%-12s %12.2f\n", dateStr, price.Close)
			}
		}
		
		fmt.Printf("\nTotal: %d monthly prices\n", len(prices))
		return nil
	},
}

func init() {
	Cmd.AddCommand(monthlyCmd)
	monthlyCmd.Flags().BoolVar(&monthlyShowYoY, "yoy", false, "Show YoY percentage column")
}
