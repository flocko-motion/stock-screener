package user

import (
	"fmt"

	"github.com/flocko-motion/gofins/pkg/db"
	"github.com/spf13/cobra"
)

var deleteCmd = &cobra.Command{
	Use:   "delete [username]",
	Short: "Delete a user",
	Args:  cobra.ExactArgs(1),
	RunE: func(cmd *cobra.Command, args []string) error {
		username := args[0]
		
		// Check if user exists
		user, err := db.GetUser(username)
		if err != nil {
			return fmt.Errorf("failed to check user: %w", err)
		}
		if user == nil {
			return fmt.Errorf("user '%s' not found", username)
		}
		
		// Delete user
		if err := db.DeleteUser(username); err != nil {
			return fmt.Errorf("failed to delete user: %w", err)
		}
		
		fmt.Printf("✓ User '%s' deleted (ID: %s)\n", username, user.ID)
		
		return nil
	},
}

func init() {
	UserCmd.AddCommand(deleteCmd)
}
