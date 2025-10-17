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
		rowsAffected, err := db.ResetIndexTimestamps()
		if err != nil {
			return fmt.Errorf("failed to reset index timestamps: %w", err)
		}
		fmt.Printf("✓ Reset update timestamps for %d indices\n", rowsAffected)
		fmt.Println("Price and profile updaters will now reload all index data from FMP")

		return nil
	},
}
