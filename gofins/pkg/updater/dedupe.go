package updater

import (
	"sync"
	"sync/atomic"
	"time"

	"github.com/flocko-motion/gofins/pkg/db"
	"github.com/flocko-motion/gofins/pkg/fmp"
	"github.com/flocko-motion/gofins/pkg/log"
	"github.com/flocko-motion/gofins/pkg/types"
)

// DedupeConfig holds configuration for deduplication runs
type DedupeConfig struct {
	MaxGroups int      // Maximum number of groups to process (0 = unlimited)
	Symbols   []string // Specific symbols to include (empty = all symbols)
}

func DedupeSymbols() {
	log := NewLogger("Dedupe")
	config := &DedupeConfig{MaxGroups: 0} // unlimited

	for {
		if err := dedupeSymbolsImpl(log, config); err != nil {
			log.Errorf("Dedupe failed: %v\n", err)
		}
		time.Sleep(time.Hour * 24 * 7) // Sleep for 7 days
	}
}

func DedupeSymbolsOnce() error {
	return DedupeSymbolsOnceWithConfig(nil)
}

func DedupeSymbolsOnceWithConfig(config *DedupeConfig) error {
	if config == nil {
		config = &DedupeConfig{MaxGroups: 0} // unlimited
	}
	log := NewLogger("Dedupe")
	return dedupeSymbolsImpl(log, config)
}

func dedupeSymbolsImpl(log *log.Logger, config *DedupeConfig) error {
	// Check if we already ran today
	lastRun, err := db.GetLastBatchUpdate("dedupe")
	if err == nil && lastRun != nil && lastRun.CompletedAt != nil {
		today := time.Now().Truncate(24 * time.Hour)
		lastRunDay := lastRun.CompletedAt.Truncate(24 * time.Hour)
		if today.Equal(lastRunDay) {
			log.Printf("Dedupe already ran today at %s, skipping\n", lastRun.CompletedAt.Format("15:04:05"))
			return nil
		}
	}

	log.Printf("Starting deduplication (CIK and Name in parallel)...\n")
	if config.MaxGroups > 0 {
		log.Printf("Limited to %d groups per deduper\n", config.MaxGroups)
	}
	startTime := time.Now()

	// Start batch log
	batchID, err := db.StartBatchUpdate("dedupe")
	if err != nil {
		log.Errorf("Failed to start batch log: %v\n", err)
		// Continue anyway
	}

	// Run CIK and Name dedupe concurrently (they operate on different symbol sets)
	var wg sync.WaitGroup
	var cikUpdated, cikFailed, nameUpdated, nameFailed int
	var cikErr, nameErr error

	// Phase 1: Process symbols with CIK
	// wg.Add(1)
	// go func() {
	// 	defer wg.Done()
	// 	cikUpdated, cikFailed, cikErr = dedupeByCIK(config)
	// }()

	// Phase 2: Process stocks without CIK by name
	wg.Add(1)
	go func() {
		defer wg.Done()
		nameUpdated, nameFailed, nameErr = dedupeByName(config)
	}()

	wg.Wait()

	if cikErr != nil {
		return cikErr
	}
	if nameErr != nil {
		return nameErr
	}

	// Show combined results
	totalUpdated := cikUpdated + nameUpdated
	totalFailed := cikFailed + nameFailed
	elapsed := time.Since(startTime)
	log.ProgressShort(totalUpdated+totalFailed, 0, elapsed)

	// Complete batch log
	if batchID > 0 {
		totalProcessed := totalUpdated + totalFailed
		if err := db.CompleteBatchUpdate(batchID, totalProcessed, totalUpdated); err != nil {
			log.Errorf("Failed to complete batch log: %v\n", err)
		}
	}

	return nil
}

// dedupeByCIK groups symbols by CIK and identifies primary listings
func dedupeByCIK(config *DedupeConfig) (int, int, error) {
	log := NewLogger("Dedupe.CIK")
	symbols, err := db.GetSymbolsWithCIK()
	if err != nil {
		return 0, 0, err
	}

	log.Printf("Processing %d symbols with CIK...\n", len(symbols))

	// Group symbols by CIK
	cikGroups := make(map[string][]types.Symbol)
	for _, symbol := range symbols {
		if symbol.CIK != nil {
			cikGroups[*symbol.CIK] = append(cikGroups[*symbol.CIK], symbol)
		}
	}

	// Filter to only groups with multiple symbols
	type cikGroup struct {
		cik   string
		group []types.Symbol
	}
	var groups []cikGroup
	for cik, group := range cikGroups {
		if len(group) > 1 {
			// If specific symbols are requested, only include groups containing those symbols
			if len(config.Symbols) > 0 {
				hasRequestedSymbol := false
				for _, sym := range group {
					for _, requested := range config.Symbols {
						if sym.Ticker == requested {
							hasRequestedSymbol = true
							break
						}
					}
					if hasRequestedSymbol {
						break
					}
				}
				if !hasRequestedSymbol {
					continue
				}
			}
			groups = append(groups, cikGroup{cik, group})
		}
	}

	// Limit groups if MaxGroups is set
	if config.MaxGroups > 0 && len(groups) > config.MaxGroups {
		log.Printf("Limiting to first %d groups (out of %d)\n", config.MaxGroups, len(groups))
		groups = groups[:config.MaxGroups]
	}

	totalGroups := len(groups)
	var groupCount, updated, failed atomic.Int32
	startTime := time.Now()

	// Process groups concurrently with workers
	const numWorkers = 16
	workChan := make(chan cikGroup, numWorkers*2)
	var wg sync.WaitGroup

	// Start workers
	for i := 0; i < numWorkers; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			for item := range workChan {
				// Find primary ticker for this group
				primaryTicker, err := findPrimaryByCIK(item.cik, item.group)
				if err != nil {
					log.Errorf("Failed to find primary for CIK %s: %v\n", item.cik, err)
					failed.Add(int32(len(item.group)))
					groupCount.Add(1)
					continue
				}

				// Build list of secondary tickers
				var secondaryTickers []string
				for _, symbol := range item.group {
					if symbol.Ticker != primaryTicker {
						secondaryTickers = append(secondaryTickers, symbol.Ticker)
					}
				}

				// Update the entire group in one transaction
				if err := db.UpdatePrimaryListingGroup(primaryTicker, secondaryTickers); err != nil {
					log.Errorf("Failed to update group for CIK %s: %v\n", item.cik, err)
					failed.Add(int32(len(item.group)))
				} else {
					updated.Add(int32(len(item.group)))
				}

				count := int(groupCount.Add(1))
				// Log progress every 100 groups
				if count%100 == 0 {
					elapsed := time.Since(startTime)
					remaining := totalGroups - count
					log.Progress(int(updated.Load()), int(failed.Load()), 0, remaining, elapsed)
				}
			}
		}()
	}

	// Send work to workers
	for _, group := range groups {
		workChan <- group
	}
	close(workChan)
	wg.Wait()

	elapsed := time.Since(startTime)
	total := int(updated.Load()) + int(failed.Load())
	log.ProgressShort(total, 0, elapsed)

	return int(updated.Load()), int(failed.Load()), nil
}

// findPrimaryByCIK determines the primary listing for a CIK group
func findPrimaryByCIK(cik string, group []types.Symbol) (string, error) {
	// Query FMP to get the primary listing
	primaryProfile, err := fmp.GetProfileByCIK(cik)
	if err != nil {
		// If FMP fails, fall back to first symbol in group
		return group[0].Ticker, nil
	}

	// Find the symbol that matches the primary exchange
	for _, symbol := range group {
		if symbol.Exchange != nil && *symbol.Exchange == primaryProfile.Exchange {
			return symbol.Ticker, nil
		}
	}

	// If no match found, return the first symbol
	return group[0].Ticker, nil
}

// dedupeByName groups stocks by exact name match
func dedupeByName(config *DedupeConfig) (int, int, error) {
	log := NewLogger("Dedupe.Name")
	symbols, err := db.GetStockSymbolsForNameDedupe()
	if err != nil {
		return 0, 0, err
	}

	log.Printf("Processing %d stocks by name...\n", len(symbols))

	// Group symbols by exact name
	nameGroups := make(map[string][]types.Symbol)
	for _, symbol := range symbols {
		if symbol.Name != nil && *symbol.Name != "" {
			nameGroups[*symbol.Name] = append(nameGroups[*symbol.Name], symbol)
		}
	}

	// Filter to only groups with multiple symbols
	type nameGroup struct {
		name  string
		group []types.Symbol
	}
	var groups []nameGroup
	for name, group := range nameGroups {
		if len(group) > 1 {
			// If specific symbols are requested, only include groups containing those symbols
			if len(config.Symbols) > 0 {
				hasRequestedSymbol := false
				for _, sym := range group {
					for _, requested := range config.Symbols {
						if sym.Ticker == requested {
							hasRequestedSymbol = true
							break
						}
					}
					if hasRequestedSymbol {
						break
					}
				}
				if !hasRequestedSymbol {
					continue
				}
			}
			groups = append(groups, nameGroup{name, group})
		}
	}

	// Limit groups if MaxGroups is set
	if config.MaxGroups > 0 && len(groups) > config.MaxGroups {
		log.Printf("Limiting to first %d groups (out of %d)\n", config.MaxGroups, len(groups))
		groups = groups[:config.MaxGroups]
	}

	totalGroups := len(groups)
	var groupCount, updated, failed atomic.Int32
	startTime := time.Now()

	// Process groups concurrently with workers
	const numWorkers = 16
	workChan := make(chan nameGroup, numWorkers*2)
	var wg sync.WaitGroup

	// Start workers
	for i := 0; i < numWorkers; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			for item := range workChan {
				// Find primary ticker for this group
				primaryTicker := findPrimaryByOldestPrice(item.group)

				// Build list of secondary tickers
				var secondaryTickers []string
				for _, symbol := range item.group {
					if symbol.Ticker != primaryTicker {
						secondaryTickers = append(secondaryTickers, symbol.Ticker)
					}
				}

				// Update the entire group in one transaction
				if err := db.UpdatePrimaryListingGroup(primaryTicker, secondaryTickers); err != nil {
					log.Errorf("Failed to update group for name '%s': %v\n", item.name, err)
					failed.Add(int32(len(item.group)))
				} else {
					updated.Add(int32(len(item.group)))
				}

				count := int(groupCount.Add(1))
				// Log progress every 100 groups
				if count%1000 == 0 {
					elapsed := time.Since(startTime)
					remaining := totalGroups - count
					log.Progress(int(updated.Load()), int(failed.Load()), 0, remaining, elapsed)
				}
			}
		}()
	}

	// Send work to workers
	for _, group := range groups {
		workChan <- group
	}
	close(workChan)
	wg.Wait()

	elapsed := time.Since(startTime)
	total := int(updated.Load()) + int(failed.Load())
	log.ProgressShort(total, 0, elapsed)

	return int(updated.Load()), int(failed.Load()), nil
}

// findPrimaryByOldestPrice finds the symbol with the oldest price date
func findPrimaryByOldestPrice(group []types.Symbol) string {
	if len(group) == 0 {
		return ""
	}

	primary := group[0]
	for _, symbol := range group[1:] {
		// If current primary has no oldest price, use this symbol
		if primary.OldestPrice == nil {
			primary = symbol
			continue
		}

		// If this symbol has an older price, use it
		if symbol.OldestPrice != nil && symbol.OldestPrice.Before(*primary.OldestPrice) {
			primary = symbol
		}
	}

	return primary.Ticker
}
