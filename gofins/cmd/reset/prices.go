package reset

import (
	"fmt"

	"github.com/flocko-motion/gofins/pkg/db"
	"github.com/spf13/cobra"
)

var pricesCmd = &cobra.Command{
	Use:   "prices",
	Short: "Reset price update timestamps to force fresh reload from FMP",
	RunE: func(cmd *cobra.Command, args []string) error {
		fmt.Println("=== Resetting Price Update Timestamps ===")

		database, err := db.NewDB()
		if err != nil {
			return fmt.Errorf("failed to connect to database: %w", err)
		}
		defer database.Close()
		fmt.Println("✓ Database connected")

		// Reset all last_price_update timestamps to NULL
		result, err := database.Exec(`
			UPDATE symbols 
			SET last_price_update = NULL, last_price_status = NULL
		`)
		if err != nil {
			return fmt.Errorf("failed to reset price timestamps: %w", err)
		}

		rowsAffected, _ := result.RowsAffected()
		fmt.Printf("✓ Reset price update timestamps for %d symbols\n", rowsAffected)
		fmt.Println("Price updater will now reload all price data from FMP")

		return nil
	},
}
