package user

import (
	"fmt"

	"github.com/flocko-motion/gofins/pkg/db"
	"github.com/spf13/cobra"
)

var createCmd = &cobra.Command{
	Use:   "create [username]",
	Short: "Create a new user",
	Args:  cobra.ExactArgs(1),
	RunE: func(cmd *cobra.Command, args []string) error {
		username := args[0]
		
		// Check if user already exists
		existing, err := db.GetUser(username)
		if err != nil {
			return fmt.Errorf("failed to check existing user: %w", err)
		}
		if existing != nil {
			return fmt.Errorf("user '%s' already exists (ID: %s)", username, existing.ID)
		}
		
		// Create user
		user, err := db.CreateUser(username)
		if err != nil {
			return fmt.Errorf("failed to create user: %w", err)
		}
		
		fmt.Printf("✓ User created:\n")
		fmt.Printf("  Name: %s\n", user.Name)
		fmt.Printf("  ID:   %s\n", user.ID)
		fmt.Printf("  Created: %s\n", user.CreatedAt.Format("2006-01-02 15:04:05"))
		
		return nil
	},
}

func init() {
	UserCmd.AddCommand(createCmd)
}
