package reset

import (
	"fmt"

	"github.com/flocko-motion/gofins/pkg/db"
	"github.com/spf13/cobra"
)

var profilesCmd = &cobra.Command{
	Use:   "profiles",
	Short: "Reset profile update timestamps to force fresh reload from FMP",
	RunE: func(cmd *cobra.Command, args []string) error {
		fmt.Println("=== Resetting Profile Update Timestamps ===")
		rowsAffected, err := db.ResetProfileTimestamps()
		if err != nil {
			return fmt.Errorf("failed to reset profile timestamps: %w", err)
		}
		fmt.Printf("✓ Reset profile update timestamps for %d symbols\n", rowsAffected)
		fmt.Println("Profile updater will now reload all profile data from FMP")

		return nil
	},
}
