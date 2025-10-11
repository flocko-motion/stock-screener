package cmd

import (
	"context"
	"fmt"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/flocko-motion/gofins/pkg/db"
	"github.com/flocko-motion/gofins/pkg/fmp"
	"github.com/flocko-motion/gofins/pkg/updater"
	"github.com/spf13/cobra"
)

var apiKeyPath string

var serverCmd = &cobra.Command{
	Use:   "server",
	Short: "Run FINS in server mode",
	RunE: func(cmd *cobra.Command, args []string) error {
		fmt.Println("=== Initializing ===")
		database, err := db.NewDB()
		if err != nil {
			return fmt.Errorf("failed to connect to database: %w", err)
		}
		defer database.Close()
		fmt.Println("✓ Database connected")

		fmpClient, err := fmp.NewClient(apiKeyPath)
		if err != nil {
			return fmt.Errorf("failed to create FMP client: %w", err)
		}
		fmt.Println("✓ FMP client ready")

		fmt.Println("\n=== Syncing Symbol List ===")
		if err := updater.SyncSymbols(database, fmpClient); err != nil {
			return fmt.Errorf("symbol sync failed: %w", err)
		}

		// Setup context for graceful shutdown
		ctx, cancel := context.WithCancel(cmd.Context())
		defer cancel()

		sigChan := make(chan os.Signal, 1)
		signal.Notify(sigChan, os.Interrupt, syscall.SIGTERM)

		fmt.Println("\n=== Starting Profile Updater ===")
		go updater.UpdateProfiles(ctx, database, fmpClient)

		fmt.Println("✓ Server running (Ctrl+C to stop)")
		<-sigChan
		fmt.Println("\nShutting down...")
		cancel()
		time.Sleep(time.Second)
		fmt.Println("✓ Server stopped")
		return nil
	},
}

func init() {
	rootCmd.AddCommand(serverCmd)

	serverCmd.Flags().StringVar(&apiKeyPath, "api-key", "~/.fins/config/financialmodelingprep.key",
		"Path to FMP API key file")
}
