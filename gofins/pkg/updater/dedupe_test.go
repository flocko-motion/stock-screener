package updater

import (
	"testing"

	"github.com/flocko-motion/gofins/pkg/db"
)

func TestDedupeByName(t *testing.T) {
	config := &DedupeConfig{
		Symbols: []string{"AAPL", "APC.DE"},
	}

	updated, failed, err := dedupeByName(config)
	if err != nil {
		t.Fatalf("dedupeByName failed: %v", err)
	}

	t.Logf("Updated: %d, Failed: %d", updated, failed)

	if updated == 0 {
		t.Fatal("Expected at least some symbols to be updated")
	}

	// Check if any primary_listing entries exist
	symbols, err := db.GetSymbolsWithCIK()
	if err != nil {
		t.Fatalf("Failed to get symbols: %v", err)
	}

	primaryCount := 0
	secondaryCount := 0
	for _, sym := range symbols {
		if sym.PrimaryListing != nil {
			if *sym.PrimaryListing == "" {
				primaryCount++
			} else {
				secondaryCount++
			}
		}
	}

	t.Logf("Found %d primary listings and %d secondary listings", primaryCount, secondaryCount)

	if primaryCount == 0 {
		t.Fatal("Expected at least some primary listings to be set")
	}
	if secondaryCount == 0 {
		t.Fatal("Expected at least some secondary listings to be set")
	}
}
