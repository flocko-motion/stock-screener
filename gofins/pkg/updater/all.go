package updater

import (
	"context"
	"time"

	"github.com/flocko-motion/gofins/pkg/f"
)

// RunAllUpdaters runs all updaters in sequence: symbols -> profiles -> quotes -> prices -> dedupe
// Quotes must run before prices to enable incremental price updates
// After completing a full cycle, it sleeps for 8 hours before repeating
func RunAllUpdaters(ctx context.Context) {
	log := NewLogger("All")
	log.Printf("Starting all updaters (symbols -> profiles -> quotes -> prices -> dedupe)\n")

	for {
		log.Printf("Starting full update cycle...\n")
		cycleStart := time.Now()

		// Step 1: Sync symbols
		log.Printf("Step 1/5: Syncing symbols...\n")
		if err := SyncSymbolsOnce(); err != nil {
			log.Errorf("Symbol sync failed: %v\n", err)
		}

		// Step 2: Update profiles
		log.Printf("Step 2/5: Updating profiles...\n")
		if err := UpdateProfilesBatch(ctx, NewLogger("ProfileBatch")); err != nil {
			log.Errorf("Profile update failed: %v\n", err)
		}

		// Step 3: Update EOD quotes (must run before prices for incremental updates)
		log.Printf("Step 3/5: Updating quotes...\n")
		if err := UpdateQuotesOnce(ctx); err != nil {
			log.Errorf("Quote update failed: %v\n", err)
		}

		// Step 4: Update prices (can now use incremental updates from quotes)
		log.Printf("Step 4/5: Updating prices...\n")
		if err := UpdatePricesOnce(); err != nil {
			log.Errorf("Price update failed: %v\n", err)
		}

		// Step 5: Deduplicate
		log.Printf("Step 5/5: Deduplicating symbols...\n")
		if err := DedupeSymbolsOnce(); err != nil {
			log.Errorf("Deduplication failed: %v\n", err)
		}

		cycleDuration := time.Since(cycleStart)
		log.Printf("✓ Full cycle completed in %s\n", f.DurationToString(cycleDuration))

		// Sleep for 8 hours before next cycle
		const sleepHours = 8
		log.Printf("Sleeping for %d hours before next cycle...\n", sleepHours)
		time.Sleep(time.Hour * time.Duration(sleepHours))
	}
}
