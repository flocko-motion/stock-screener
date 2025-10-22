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
	"github.com/flocko-motion/gofins/pkg/f"
	"github.com/flocko-motion/gofins/pkg/updater"
	"github.com/spf13/cobra"
)

var noUpdates bool
var devUser string

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
		apiServer := api.NewServer(db.Db(), 8080, devUser)
		go apiServer.Start(ctx)
		if devUser != "" {
			fmt.Printf("✓ REST API server listening on :8080 (DEV MODE - all requests as user '%s')\n", devUser)
		} else {
			fmt.Println("✓ REST API server listening on :8080")
		}

		// Start updaters only if --no-updates is not set
		fmt.Println("\n=== Starting Services ===")
		if !noUpdates {
			go updater.RunAllUpdaters(ctx)
		} else {
			fmt.Println("⚠️  Updates disabled - working with existing data only")
		}

		fmt.Println("✓ Server running (Ctrl+C to stop)")
		<-sigChan
		fmt.Println("\nShutting down...")
		cancel()
		time.Sleep(time.Second)

		// Graceful shutdown
		if err := db.PrepareForShutdown(); err != nil {
			_ = db.LogError("server.shutdown", "database", "Failed to close database connection", f.Ptr(err.Error()))
		}

		fmt.Println("✓ Server stopped")
		return nil
	},
}

func init() {
	rootCmd.AddCommand(serverCmd)

	serverCmd.Flags().BoolVar(&noUpdates, "no-updates", false,
		"Disable all data updates and work with existing data only")
	serverCmd.Flags().StringVar(&devUser, "user", "",
		"Development mode - override user for all requests (e.g., --user=alice)")
}
