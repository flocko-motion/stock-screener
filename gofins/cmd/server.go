package cmd

import (
	"context"
	"fmt"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/flocko-motion/gofins/pkg/api"
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
		// Setup context for graceful shutdown
		ctx, cancel := context.WithCancel(cmd.Context())
		defer cancel()

		sigChan := make(chan os.Signal, 1)
		signal.Notify(sigChan, os.Interrupt, syscall.SIGTERM)

		// init DB
		fmt.Println("=== Initializing ===")
		database, err := db.NewDB()
		if err != nil {
			return fmt.Errorf("failed to connect to database: %w", err)
		}
		defer database.Close()
		fmt.Println("✓ Database connected")

		// init FMP
		fmpClient, err := fmp.NewClient(apiKeyPath)
		if err != nil {
			return fmt.Errorf("failed to create FMP client: %w", err)
		}
		fmt.Println("✓ FMP client ready")

		// sync symbols once before starting updaters
		fmt.Println("\n=== Starting Services ===")
		if err := updater.SyncSymbolsOnce(database, fmpClient); err != nil {
			return fmt.Errorf("symbol sync failed: %w", err)
		}
		go updater.UpdateProfiles(ctx, database, fmpClient)
		go updater.UpdatePrices(ctx, database, fmpClient)
		go updater.SyncSymbols(database, fmpClient)

		// Start REST API server
		apiServer := api.NewServer(database, 8080)
		go apiServer.Start(ctx)

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
