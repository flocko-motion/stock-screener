package cmd

import "github.com/flocko-motion/gofins/cmd/symbol"

func init() {
	// Register the symbol command and its subcommands
	rootCmd.AddCommand(symbol.Cmd)
}
