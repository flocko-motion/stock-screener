package cmd

import "github.com/flocko-motion/gofins/cmd/update"

func init() {
	// Register the update command and its subcommands
	rootCmd.AddCommand(update.Cmd)
}
