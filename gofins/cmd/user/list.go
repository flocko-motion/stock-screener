package user

import (
	"fmt"

	"github.com/flocko-motion/gofins/pkg/db"
	"github.com/spf13/cobra"
)

var listCmd = &cobra.Command{
	Use:   "list",
	Short: "List all users",
	RunE: func(cmd *cobra.Command, args []string) error {
		users, err := db.ListUsers()
		if err != nil {
			return fmt.Errorf("failed to list users: %w", err)
		}
		
		if len(users) == 0 {
			fmt.Println("No users found")
			return nil
		}
		
		fmt.Printf("Users (%d):\n\n", len(users))
		fmt.Printf("%-20s %-36s %s\n", "NAME", "ID", "CREATED")
		fmt.Println("--------------------------------------------------------------------------------")
		
		for _, user := range users {
			fmt.Printf("%-20s %-36s %s\n",
				user.Name,
				user.ID.String(),
				user.CreatedAt.Format("2006-01-02 15:04:05"))
		}
		
		return nil
	},
}

func init() {
	UserCmd.AddCommand(listCmd)
}
