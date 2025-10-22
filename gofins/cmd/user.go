package cmd

import "github.com/flocko-motion/gofins/cmd/user"

func init() {
	// Register the user command and its subcommands
	rootCmd.AddCommand(user.UserCmd)
}
