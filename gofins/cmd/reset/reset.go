package reset

import "github.com/spf13/cobra"

// Cmd is the parent command for reset-related subcommands
var Cmd = &cobra.Command{
	Use:   "reset",
	Short: "Reset data to trigger fresh updates",
}

func init() {
	// Attach reset subcommands
	Cmd.AddCommand(pricesCmd)
	Cmd.AddCommand(profilesCmd)
	Cmd.AddCommand(indicesCmd)
	Cmd.AddCommand(quotesCmd)
}
