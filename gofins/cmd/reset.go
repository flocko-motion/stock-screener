package cmd

import "github.com/spf13/cobra"

// resetCmd is the parent command for reset-related subcommands
var resetCmd = &cobra.Command{
	Use:   "reset",
	Short: "Reset data to trigger fresh updates",
}

func init() {
	// Attach existing reset subcommands under `reset`
	resetCmd.AddCommand(resetPricesCmd)
	resetCmd.AddCommand(resetProfileCmd)

	// Register the parent on the root command
	rootCmd.AddCommand(resetCmd)
}
