package error

import (
	"fmt"
	"time"

	"github.com/flocko-motion/gofins/pkg/db"
	"github.com/spf13/cobra"
)

var (
	listLimit  int
	listSource string
)

var listCmd = &cobra.Command{
	Use:   "list",
	Short: "List recent errors in short form",
	Long:  "Display a list of recent errors with ID, timestamp, source, and message",
	RunE: func(cmd *cobra.Command, args []string) error {
		var errors []db.ErrorEntry
		var err error

		if listSource != "" {
			errors, err = db.GetErrorsBySource(listSource, listLimit)
			if err != nil {
				return fmt.Errorf("failed to get errors: %w", err)
			}
		} else {
			errors, err = db.GetRecentErrors(listLimit)
			if err != nil {
				return fmt.Errorf("failed to get errors: %w", err)
			}
		}

		if len(errors) == 0 {
			fmt.Println("No errors found")
			return nil
		}

		// Header
		fmt.Printf("%-6s %-20s %-25s %s\n", "ID", "TIMESTAMP", "SOURCE", "MESSAGE")
		fmt.Println("─────────────────────────────────────────────────────────────────────────────────────")

		// List errors
		for _, e := range errors {
			timestamp := e.Timestamp.Format("2006-01-02 15:04:05")
			message := e.Message
			if len(message) > 50 {
				message = message[:47] + "..."
			}
			fmt.Printf("%-6d %-20s %-25s %s\n", e.ID, timestamp, e.Source, message)
		}

		fmt.Println()

		// Show count in last 24h
		since := time.Now().Add(-24 * time.Hour)
		count, err := db.CountErrorsSince(since)
		if err == nil {
			fmt.Printf("Total errors in last 24h: %d\n", count)
		}

		return nil
	},
}

func init() {
	Cmd.AddCommand(listCmd)

	listCmd.Flags().IntVarP(&listLimit, "limit", "n", 50, "Number of errors to show")
	listCmd.Flags().StringVarP(&listSource, "source", "s", "", "Filter by source (e.g., 'updater.symbols')")
}
