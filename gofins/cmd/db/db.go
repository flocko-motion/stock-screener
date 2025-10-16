package db

import "github.com/spf13/cobra"

// Cmd is the parent command for database-related subcommands
var Cmd = &cobra.Command{
	Use:   "db",
	Short: "Database inspection and management commands",
}

func init() {
	// Attach db subcommands
	Cmd.AddCommand(schemaCmd)
}
