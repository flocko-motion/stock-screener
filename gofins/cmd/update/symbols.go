package update

import (
	"fmt"

	"github.com/flocko-motion/gofins/pkg/updater"
	"github.com/spf13/cobra"
)

var symbolsCmd = &cobra.Command{
	Use:   "symbols",
	Short: "Run symbol sync once (fetch symbol list from FMP)",
	RunE: func(cmd *cobra.Command, args []string) error {
		fmt.Println("Running symbol sync...")
		if err := updater.SyncSymbolsOnce(); err != nil {
			return fmt.Errorf("symbol sync failed: %w", err)
		}
		fmt.Println("Symbol sync completed successfully")
		return nil
	},
}

func init() {
	Cmd.AddCommand(symbolsCmd)
}
