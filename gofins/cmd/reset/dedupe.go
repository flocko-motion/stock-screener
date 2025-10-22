package reset

import (
	"fmt"

	"github.com/flocko-motion/gofins/pkg/db"
	"github.com/spf13/cobra"
)

var dedupeCmd = &cobra.Command{
	Use:   "dedupe",
	Short: "Reset all primary_listing fields and dedupe timestamp",
	Long:  "Clears all primary_listing fields and resets the dedupe batch timestamp, allowing deduplication to run fresh",
	RunE: func(cmd *cobra.Command, args []string) error {
		fmt.Println("Resetting all primary_listing fields...")
		
		count, err := db.ResetPrimaryListings()
		if err != nil {
			return fmt.Errorf("failed to reset primary listings: %w", err)
		}
		
		fmt.Printf("Successfully reset %d symbols\n", count)
		
		fmt.Println("Resetting dedupe timestamp...")
		err = db.DeleteBatchUpdate("dedupe")
		if err != nil {
			return fmt.Errorf("failed to reset dedupe timestamp: %w", err)
		}
		
		fmt.Println("Dedupe reset complete - ready to run again")
		return nil
	},
}

func init() {
	Cmd.AddCommand(dedupeCmd)
}
