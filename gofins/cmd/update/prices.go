package update

import (
	"fmt"

	"github.com/flocko-motion/gofins/pkg/updater"
	"github.com/spf13/cobra"
)

var pricesCmd = &cobra.Command{
	Use:   "prices",
	Short: "Run price update once (fetch historical prices from FMP)",
	RunE: func(cmd *cobra.Command, args []string) error {
		fmt.Println("Running price update...")
		if err := updater.UpdatePricesOnce(); err != nil {
			return fmt.Errorf("price update failed: %w", err)
		}
		fmt.Println("Price update completed successfully")
		return nil
	},
}

func init() {
	Cmd.AddCommand(pricesCmd)
}
