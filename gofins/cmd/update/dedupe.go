package update

import (
	"fmt"

	"github.com/flocko-motion/gofins/pkg/updater"
	"github.com/spf13/cobra"
)

var dedupeCmd = &cobra.Command{
	Use:   "dedupe",
	Short: "Run deduplication once (identify primary/secondary listings)",
	RunE: func(cmd *cobra.Command, args []string) error {
		fmt.Println("Running deduplication...")
		if err := updater.DedupeSymbolsOnce(); err != nil {
			return fmt.Errorf("deduplication failed: %w", err)
		}
		fmt.Println("Deduplication completed successfully")
		return nil
	},
}

func init() {
	Cmd.AddCommand(dedupeCmd)
}
