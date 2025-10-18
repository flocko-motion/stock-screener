package db

import (
	"fmt"

	"github.com/flocko-motion/gofins/pkg/updater"
	"github.com/spf13/cobra"
)

var profilesCmd = &cobra.Command{
	Use:   "profiles",
	Short: "Run profile update once (fetch company profiles from FMP)",
	RunE: func(cmd *cobra.Command, args []string) error {
		fmt.Println("Running profile update...")
		if err := updater.UpdateProfilesOnce(); err != nil {
			return fmt.Errorf("profile update failed: %w", err)
		}
		fmt.Println("Profile update completed successfully")
		return nil
	},
}

func init() {
	Cmd.AddCommand(profilesCmd)
}
