package cmd

import "github.com/flocko-motion/gofins/cmd/db"

func init() {
	// Register the db command and its subcommands
	rootCmd.AddCommand(db.Cmd)
}
