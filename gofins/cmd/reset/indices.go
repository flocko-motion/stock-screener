package reset

import (
	"fmt"

	"github.com/flocko-motion/gofins/pkg/db"
	"github.com/spf13/cobra"
)

var indicesCmd = &cobra.Command{
	Use:   "indices",
	Short: "Reset update timestamps for indices",
	RunE: func(cmd *cobra.Command, args []string) error {
		fmt.Println("=== Resetting Index Update Timestamps ===")

		database, err := db.NewDB()
		if err != nil {
			return fmt.Errorf("failed to connect to database: %w", err)
		}
		defer database.Close()
		fmt.Println("✓ Database connected")

		// Reset timestamps for indices and ensure they're marked as actively trading
		result, err := database.Exec(`
			UPDATE symbols 
			SET last_price_update = NULL, 
			    last_price_status = NULL,
			    last_profile_update = NULL,
			    last_profile_status = NULL,
			    is_actively_trading = true
			WHERE type = $1
		`, db.TypeIndex)
		if err != nil {
			return fmt.Errorf("failed to reset index timestamps: %w", err)
		}

		rowsAffected, _ := result.RowsAffected()
		fmt.Printf("✓ Reset update timestamps for %d indices\n", rowsAffected)
		fmt.Println("Price and profile updaters will now reload all index data from FMP")

		return nil
	},
}
