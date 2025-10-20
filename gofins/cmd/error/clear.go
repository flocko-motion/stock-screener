package error

import (
	"fmt"

	"github.com/flocko-motion/gofins/pkg/db"
	"github.com/spf13/cobra"
)

var clearForce bool

var clearCmd = &cobra.Command{
	Use:   "clear",
	Short: "Delete all errors from the database",
	Long:  "Remove all error entries from the database. Use --force to skip confirmation.",
	RunE: func(cmd *cobra.Command, args []string) error {
		// Confirmation unless --force is used
		if !clearForce {
			fmt.Print("This will delete ALL errors from the database. Are you sure? (y/N): ")
			var response string
			fmt.Scanln(&response)
			if response != "y" && response != "Y" {
				fmt.Println("Cancelled")
				return nil
			}
		}

		deleted, err := db.ClearAllErrors()
		if err != nil {
			return fmt.Errorf("failed to clear errors: %w", err)
		}

		fmt.Printf("✓ Deleted %d error(s) from the database\n", deleted)
		return nil
	},
}

func init() {
	Cmd.AddCommand(clearCmd)

	clearCmd.Flags().BoolVarP(&clearForce, "force", "f", false, "Skip confirmation prompt")
}
