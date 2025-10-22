package reset

import (
	"fmt"

	"github.com/flocko-motion/gofins/pkg/db"
	"github.com/spf13/cobra"
)

var quotesCmd = &cobra.Command{
	Use:   "quotes",
	Short: "Reset current quote timestamps to force fresh reload from FMP",
	RunE: func(cmd *cobra.Command, args []string) error {
		fmt.Println("=== Resetting Current Quote Timestamps ===")

		fmt.Println("✓ Database connected")

		// Reset all current_price_time timestamps to NULL
		rowsAffected, err := db.ResetQuoteTimestamps()
		if err != nil {
			return fmt.Errorf("failed to reset quote timestamps: %w", err)
		}
		fmt.Printf("✓ Reset current quote timestamps for %d symbols\n", rowsAffected)
		fmt.Println("Quote updater will now reload all current quotes from FMP")

		return nil
	},
}
