package cmd

import (
	"fmt"

	"github.com/flocko-motion/gofins/pkg/db"
	"github.com/spf13/cobra"
)

var resetProfileCmd = &cobra.Command{
	Use:   "profiles",
	Short: "Reset profile update timestamps to force fresh reload from FMP",
	RunE: func(cmd *cobra.Command, args []string) error {
		fmt.Println("=== Resetting Profile Update Timestamps ===")

		database, err := db.NewDB()
		if err != nil {
			return fmt.Errorf("failed to connect to database: %w", err)
		}
		defer database.Close()
		fmt.Println("✓ Database connected")

		// Reset all last_price_update timestamps to NULL
		result, err := database.Exec(`
			UPDATE symbols 
			SET last_profile_update = NULL, last_profile_status = NULL
		`)
		if err != nil {
			return fmt.Errorf("failed to reset profile timestamps: %w", err)
		}

		rowsAffected, _ := result.RowsAffected()
		fmt.Printf("✓ Reset profile update timestamps for %d symbols\n", rowsAffected)
		fmt.Println("Profile updater will now reload all profile data from FMP")

		return nil
	},
}
