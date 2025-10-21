package db

import (
	"fmt"
	"time"

	"github.com/flocko-motion/gofins/pkg/db"
	"github.com/spf13/cobra"
)

var (
	errorsLimit  int
	errorsSource string
	errorsClear  int
)

var errorsCmd = &cobra.Command{
	Use:   "errors",
	Short: "View and manage system errors",
	RunE: func(cmd *cobra.Command, args []string) error {
		// Clear old errors if requested
		if errorsClear > 0 {
			deleted, err := db.ClearOldErrors(time.Duration(errorsClear) * 24 * time.Hour)
			if err != nil {
				return fmt.Errorf("failed to clear errors: %w", err)
			}
			fmt.Printf("✓ Deleted %d errors older than %d days\n", deleted, errorsClear)
			return nil
		}

		// Get errors
		var errors []db.ErrorEntry
		var err error

		if errorsSource != "" {
			errors, err = db.GetErrorsBySource(errorsSource, errorsLimit)
			if err != nil {
				return fmt.Errorf("failed to get errors: %w", err)
			}
			fmt.Printf("=== Errors from '%s' (limit %d) ===\n\n", errorsSource, errorsLimit)
		} else {
			errors, err = db.GetRecentErrors(errorsLimit)
			if err != nil {
				return fmt.Errorf("failed to get errors: %w", err)
			}
			fmt.Printf("=== Recent Errors (limit %d) ===\n\n", errorsLimit)
		}

		if len(errors) == 0 {
			fmt.Println("No errors found")
			return nil
		}

		for _, e := range errors {
			fmt.Printf("[%s] %s\n", e.Timestamp.Format("2006-01-02 15:04:05"), e.Source)
			fmt.Printf("  Type: %s\n", e.ErrorType)
			fmt.Printf("  Message: %s\n", e.Message)
			if e.Details != nil {
				fmt.Printf("  Details: %s\n", *e.Details)
			}
			fmt.Println()
		}

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
	errorsCmd.Flags().IntVarP(&errorsLimit, "limit", "n", 50, "Number of errors to show")
	errorsCmd.Flags().StringVarP(&errorsSource, "source", "s", "", "Filter by source (e.g., 'updater.symbols')")
	errorsCmd.Flags().IntVar(&errorsClear, "clear", 0, "Clear errors older than N days")
}
