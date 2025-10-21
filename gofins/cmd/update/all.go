package update

import (
	"context"
	"fmt"

	"github.com/flocko-motion/gofins/pkg/updater"
	"github.com/spf13/cobra"
)

var allCmd = &cobra.Command{
	Use:   "all",
	Short: "Run all updaters in sequence (symbols -> profiles -> prices -> dedupe), repeat every 8h",
	RunE: func(cmd *cobra.Command, args []string) error {
		fmt.Println("Starting all updaters in continuous mode...")
		fmt.Println("Order: symbols -> profiles -> prices -> dedupe")
		fmt.Println("Cycle repeats every 8 hours")
		fmt.Println()
		ctx := context.Background()
		updater.RunAllUpdaters(ctx)
		return nil
	},
}

func init() {
	Cmd.AddCommand(allCmd)
}
