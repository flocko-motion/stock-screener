package updater

import (
	"context"
	"time"
)

// RunAllUpdaters runs all updaters in sequence: symbols -> profiles -> prices -> dedupe
// After completing a full cycle, it sleeps for 8 hours before repeating
func RunAllUpdaters(ctx context.Context) {
	log := NewLogger("All")
	log.Printf("Starting all updaters (symbols -> profiles -> prices -> dedupe)\n")

	for {
		log.Printf("Starting full update cycle...\n")
		cycleStart := time.Now()

		// Step 1: Sync symbols
		log.Printf("Step 1/4: Syncing symbols...\n")
		if err := SyncSymbolsOnce(); err != nil {
			log.Error("Symbol sync failed: %v\n", err)
		}

		// Step 2: Update profiles
		log.Printf("Step 2/4: Updating profiles...\n")
		if err := UpdateProfilesBatch(ctx, log); err != nil {
			log.Error("Profile update failed: %v\n", err)
		}

		// once we have all profiles we can update EOD quotes
		go RunQuoteUpdater(ctx, nil, log)

		// Step 3: Update prices
		log.Printf("Step 3/4: Updating prices...\n")
		if err := UpdatePricesOnce(); err != nil {
			log.Error("Price update failed: %v\n", err)
		}

		// Step 4: Deduplicate
		log.Printf("Step 4/4: Deduplicating symbols...\n")
		if err := DedupeSymbolsOnce(); err != nil {
			log.Error("Deduplication failed: %v\n", err)
		}

		cycleDuration := time.Since(cycleStart)
		log.Printf("✓ Full cycle completed in %s\n", formatDuration(cycleDuration))

		// Sleep for 8 hours before next cycle
		const sleepHours = 8
		log.Printf("Sleeping for %d hours before next cycle...\n", sleepHours)
		time.Sleep(time.Hour * time.Duration(sleepHours))
	}
}
