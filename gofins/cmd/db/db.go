package db

import "github.com/spf13/cobra"

// Cmd is the parent command for database inspection subcommands
var Cmd = &cobra.Command{
	Use:   "db",
	Short: "Database inspection commands",
}

func init() {
	// Attach db subcommands
	Cmd.AddCommand(schemaCmd)
	Cmd.AddCommand(errorsCmd)
	Cmd.AddCommand(sqlCmd)
}
