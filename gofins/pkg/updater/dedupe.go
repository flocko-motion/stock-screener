package updater

import (
	"time"

	"github.com/flocko-motion/gofins/pkg/db"
	"github.com/flocko-motion/gofins/pkg/f"
	"github.com/flocko-motion/gofins/pkg/fmp"
	"github.com/flocko-motion/gofins/pkg/log"
	"github.com/flocko-motion/gofins/pkg/types"
)

func DedupeSymbols() {
	log := NewLogger("Dedupe")

	for {
		if err := dedupeSymbolsImpl(log); err != nil {
			log.Errorf("Dedupe failed: %v\n", err)
		}
		time.Sleep(time.Hour * 24 * 7) // Sleep for 7 days
	}
}

func DedupeSymbolsOnce() error {
	log := NewLogger("Dedupe")
	return dedupeSymbolsImpl(log)
}

func dedupeSymbolsImpl(log *log.Logger) error {
	log.Printf("Starting deduplication...\n")

	// Phase 1: Process symbols with CIK
	cikUpdated, cikFailed, err := dedupeByCIK(log)
	if err != nil {
		return err
	}

	// Phase 2: Process stocks without CIK by name
	nameUpdated, nameFailed, err := dedupeByName(log)
	if err != nil {
		return err
	}

	log.Printf("✓ Completed: %d CIK-based, %d name-based | Failed: %d CIK, %d name\n",
		cikUpdated, nameUpdated, cikFailed, nameFailed)

	return nil
}

// dedupeByCIK groups symbols by CIK and identifies primary listings
func dedupeByCIK(log *log.Logger) (int, int, error) {
	symbols, err := db.GetSymbolsWithCIK()
	if err != nil {
		return 0, 0, err
	}

	log.Printf("Processing %d symbols with CIK...\n", len(symbols))

	// Group symbols by CIK
	cikGroups := make(map[string][]types.Symbol)
	for _, symbol := range symbols {
		if symbol.CIK != nil && *symbol.CIK != "" {
			cikGroups[*symbol.CIK] = append(cikGroups[*symbol.CIK], symbol)
		}
	}

	updated := 0
	failed := 0

	// Process each CIK group
	groupCount := 0
	totalGroups := len(cikGroups)
	startTime := time.Now()

	for cik, group := range cikGroups {
		if len(group) <= 1 {
			continue // Skip single-symbol groups
		}
		groupCount++

		// Find primary ticker for this group
		primaryTicker, err := findPrimaryByCIK(cik, group)
		if err != nil {
			log.Errorf("Failed to find primary for CIK %s: %v\n", cik, err)
			failed += len(group)
			continue
		}

		// Build list of secondary tickers
		var secondaryTickers []string
		for _, symbol := range group {
			if symbol.Ticker != primaryTicker {
				secondaryTickers = append(secondaryTickers, symbol.Ticker)
			}
		}

		// Update the entire group in one transaction
		if err := db.UpdatePrimaryListingGroup(primaryTicker, secondaryTickers); err != nil {
			log.Errorf("Failed to update group for CIK %s: %v\n", cik, err)
			failed += len(group)
		} else {
			updated += len(group)
		}

		// Log progress every 100 groups with ETA
		if groupCount%100 == 0 {
			elapsed := time.Since(startTime)
			rate := float64(groupCount) / elapsed.Seconds()
			remaining := totalGroups - groupCount
			var eta string
			if rate > 0 {
				eta = f.SecondsToString(float64(remaining) / rate)
			} else {
				eta = "unknown"
			}
			log.Printf("Progress: %d/%d groups | %d symbols | ETA %s @ %.1f groups/s\n",
				groupCount, totalGroups, updated, eta, rate)
		}
	}

	log.Printf("✓ CIK-based: %d groups, %d symbols updated, %d failed\n", groupCount, updated, failed)

	return updated, failed, nil
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

// dedupeByName groups stocks without CIK by exact name match
func dedupeByName(log *log.Logger) (int, int, error) {
	symbols, err := db.GetStockSymbolsWithoutCIK()
	if err != nil {
		return 0, 0, err
	}

	log.Printf("Processing %d stocks without CIK...\n", len(symbols))

	// Group symbols by exact name
	nameGroups := make(map[string][]types.Symbol)
	for _, symbol := range symbols {
		if symbol.Name != nil && *symbol.Name != "" {
			nameGroups[*symbol.Name] = append(nameGroups[*symbol.Name], symbol)
		}
	}

	updated := 0
	failed := 0

	// Process each name group
	groupCount := 0
	totalGroups := len(nameGroups)
	startTime := time.Now()

	for name, group := range nameGroups {
		if len(group) <= 1 {
			continue // Skip single-symbol groups
		}
		groupCount++

		// Find primary ticker for this group
		primaryTicker := findPrimaryByOldestPrice(group)

		// Build list of secondary tickers
		var secondaryTickers []string
		for _, symbol := range group {
			if symbol.Ticker != primaryTicker {
				secondaryTickers = append(secondaryTickers, symbol.Ticker)
			}
		}

		// Update the entire group in one transaction
		if err := db.UpdatePrimaryListingGroup(primaryTicker, secondaryTickers); err != nil {
			log.Errorf("Failed to update group for name '%s': %v\n", name, err)
			failed += len(group)
		} else {
			updated += len(group)
		}

		// Log progress every 100 groups with ETA
		if groupCount%100 == 0 {
			elapsed := time.Since(startTime)
			rate := float64(groupCount) / elapsed.Seconds()
			remaining := totalGroups - groupCount
			var eta string
			if rate > 0 {
				eta = f.SecondsToString(float64(remaining) / rate)
			} else {
				eta = "unknown"
			}
			log.Printf("Progress: %d/%d groups | %d symbols | ETA %s @ %.1f groups/s\n",
				groupCount, totalGroups, updated, eta, rate)
		}
	}

	log.Printf("✓ Name-based: %d groups, %d symbols updated, %d failed\n", groupCount, updated, failed)

	return updated, failed, nil
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
