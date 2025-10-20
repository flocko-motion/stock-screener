package cmd

import "github.com/flocko-motion/gofins/cmd/error"

func init() {
	// Register the error command and its subcommands
	rootCmd.AddCommand(error.Cmd)
}
