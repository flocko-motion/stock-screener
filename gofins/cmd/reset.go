package cmd

import "github.com/flocko-motion/gofins/cmd/reset"

func init() {
	// Register the reset command and its subcommands
	rootCmd.AddCommand(reset.Cmd)
}
