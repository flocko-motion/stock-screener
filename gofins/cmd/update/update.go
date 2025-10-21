package update

import "github.com/spf13/cobra"

// Cmd is the parent command for update-related subcommands
var Cmd = &cobra.Command{
	Use:   "update",
	Short: "Update data from external sources",
}
