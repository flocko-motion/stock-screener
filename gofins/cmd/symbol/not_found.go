package symbol

import (
	"fmt"

	"github.com/flocko-motion/gofins/pkg/db"
	"github.com/flocko-motion/gofins/pkg/types"
	"github.com/spf13/cobra"
)

var notFoundCmd = &cobra.Command{
	Use:   "not-found",
	Short: "List symbols with not_found status",
	Long:  "Display all symbols that have a not_found status for profile or price updates",
	RunE: func(cmd *cobra.Command, args []string) error {
		// Get symbols with not_found profile status
		profileNotFound, err := db.GetSymbolsByStatus(types.StatusNotFound, "profile")
		if err != nil {
			return fmt.Errorf("failed to get symbols with not_found profile status: %w", err)
		}

		// Get symbols with not_found price status
		priceNotFound, err := db.GetSymbolsByStatus(types.StatusNotFound, "price")
		if err != nil {
			return fmt.Errorf("failed to get symbols with not_found price status: %w", err)
		}

		// Display results
		if len(profileNotFound) > 0 {
			fmt.Printf("\n=== Profile Not Found (%d symbols) ===\n", len(profileNotFound))
			fmt.Printf("%-15s %-40s %-15s %s\n", "TICKER", "NAME", "EXCHANGE", "LAST ATTEMPT")
			fmt.Println("────────────────────────────────────────────────────────────────────────────────────────")
			for _, symbol := range profileNotFound {
				name := "N/A"
				if symbol.Name != nil {
					name = *symbol.Name
				}
				exchange := "N/A"
				if symbol.Exchange != nil {
					exchange = *symbol.Exchange
				}
				lastAttempt := "N/A"
				if symbol.LastProfileUpdate != nil {
					lastAttempt = symbol.LastProfileUpdate.Format("2006-01-02 15:04")
				}
				fmt.Printf("%-15s %-40s %-15s %s\n", symbol.Ticker, truncate(name, 40), exchange, lastAttempt)
			}
		}

		if len(priceNotFound) > 0 {
			fmt.Printf("\n=== Price Not Found (%d symbols) ===\n", len(priceNotFound))
			fmt.Printf("%-15s %-40s %-15s %s\n", "TICKER", "NAME", "EXCHANGE", "LAST ATTEMPT")
			fmt.Println("────────────────────────────────────────────────────────────────────────────────────────")
			for _, symbol := range priceNotFound {
				name := "N/A"
				if symbol.Name != nil {
					name = *symbol.Name
				}
				exchange := "N/A"
				if symbol.Exchange != nil {
					exchange = *symbol.Exchange
				}
				lastAttempt := "N/A"
				if symbol.LastPriceUpdate != nil {
					lastAttempt = symbol.LastPriceUpdate.Format("2006-01-02 15:04")
				}
				fmt.Printf("%-15s %-40s %-15s %s\n", symbol.Ticker, truncate(name, 40), exchange, lastAttempt)
			}
		}

		if len(profileNotFound) == 0 && len(priceNotFound) == 0 {
			fmt.Println("No symbols with not_found status")
		}

		return nil
	},
}

func truncate(s string, maxLen int) string {
	if len(s) <= maxLen {
		return s
	}
	return s[:maxLen-3] + "..."
}

func init() {
	Cmd.AddCommand(notFoundCmd)
}
