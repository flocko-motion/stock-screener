package error

import (
	"database/sql"
	"fmt"
	"strconv"

	"github.com/flocko-motion/gofins/pkg/db"
	"github.com/spf13/cobra"
)

var infoCmd = &cobra.Command{
	Use:   "info <error-id>",
	Short: "Show detailed information about a specific error",
	Long:  "Display all details for a specific error by its ID",
	Args:  cobra.ExactArgs(1),
	RunE: func(cmd *cobra.Command, args []string) error {
		errorID, err := strconv.Atoi(args[0])
		if err != nil {
			return fmt.Errorf("invalid error ID: %s", args[0])
		}

		errorEntry, err := db.GetErrorByID(errorID)
		if err != nil {
			if err == sql.ErrNoRows {
				return fmt.Errorf("error with ID %d not found", errorID)
			}
			return fmt.Errorf("failed to get error: %w", err)
		}

		// Display full error details
		fmt.Printf("=== Error #%d ===\n\n", errorEntry.ID)
		fmt.Printf("Timestamp:  %s\n", errorEntry.Timestamp.Format("2006-01-02 15:04:05 MST"))
		fmt.Printf("Source:     %s\n", errorEntry.Source)
		fmt.Printf("Type:       %s\n", errorEntry.ErrorType)
		fmt.Printf("Message:    %s\n", errorEntry.Message)
		
		if errorEntry.Details != nil && *errorEntry.Details != "" {
			fmt.Printf("\nDetails:\n%s\n", *errorEntry.Details)
		}

		return nil
	},
}

func init() {
	Cmd.AddCommand(infoCmd)
}
