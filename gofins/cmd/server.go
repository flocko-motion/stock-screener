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
	"github.com/flocko-motion/gofins/pkg/updater"
	"github.com/spf13/cobra"
)

var noUpdates bool

var serverCmd = &cobra.Command{
	Use:   "server",
	Short: "Run FINS in server mode",
	RunE: func(cmd *cobra.Command, args []string) error {
		// Setup context for graceful shutdown
		ctx, cancel := context.WithCancel(cmd.Context())
		defer cancel()

		sigChan := make(chan os.Signal, 1)
		signal.Notify(sigChan, os.Interrupt, syscall.SIGTERM)

		// init DB - initialize singleton
		fmt.Println("=== Initializing ===")
		_ = db.Db() // Initialize database singleton (will panic if it fails)
		fmt.Println("✓ Database connected")

		// Start REST API server
		apiServer := api.NewServer(db.Db(), 8080)
		go apiServer.Start(ctx)
		fmt.Println("✓ REST API server listening on :8080")

		// Start updaters only if --no-updates is not set
		fmt.Println("\n=== Starting Services ===")
		if !noUpdates {
			// sync symbols once before starting updaters
			if err := updater.SyncSymbolsOnce(); err != nil {
				return fmt.Errorf("symbol sync failed: %w", err)
			}
			go updater.UpdateProfiles(ctx)
			go updater.UpdatePrices(ctx)
			go updater.SyncSymbols()
		} else {
			fmt.Println("⚠️  Updates disabled - working with existing data only")
		}

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

	serverCmd.Flags().BoolVar(&noUpdates, "no-updates", false,
		"Disable all data updates and work with existing data only")
}
