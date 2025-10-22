package updater

import (
	"fmt"
	"time"

	"github.com/flocko-motion/gofins/pkg/db"
	"github.com/flocko-motion/gofins/pkg/f"
	"github.com/flocko-motion/gofins/pkg/fmp"
	"github.com/flocko-motion/gofins/pkg/log"
	"github.com/flocko-motion/gofins/pkg/types"
)

func SyncSymbols() {
	log := NewLogger("Symbols")

	for {
		if err := syncSymbolsImpl(log); err != nil {
			log.Errorf("Symbol sync failed: %v\n", err)
		}
		time.Sleep(time.Hour * 24 * 7) // Sleep for 7 days
	}
}

func SyncSymbolsOnce() error {
	log := NewLogger("Symbols")
	return syncSymbolsImpl(log)
}

func syncSymbolsImpl(log *log.Logger) error {
	// Check if we already ran today
	lastRun, err := db.GetLastBatchUpdate("symbols")
	if err == nil && lastRun != nil && lastRun.CompletedAt != nil {
		today := time.Now().Truncate(24 * time.Hour)
		lastRunDay := lastRun.CompletedAt.Truncate(24 * time.Hour)
		if today.Equal(lastRunDay) {
			log.Printf("Symbol sync already ran today at %s, skipping\n", lastRun.CompletedAt.Format("15:04:05"))
			return nil
		}
	}

	// Start batch log
	batchID, err := db.StartBatchUpdate("symbols")
	if err != nil {
		log.Errorf("Failed to start batch log: %v\n", err)
		// Continue anyway
	}

	// Fetch stocks
	stocks, err := fmp.FetchStockList()
	if err != nil {
		if batchID > 0 {
			db.FailBatchUpdate(batchID, err.Error())
		}
		return fmt.Errorf("failed to fetch stock list: %w", err)
	}
	log.Printf("✓ Fetched %d stocks from FMP\n", len(stocks))

	// Fetch indices
	indices, err := fmp.FetchIndexList()
	if err != nil {
		return fmt.Errorf("failed to fetch index list: %w", err)
	}
	log.Printf("✓ Fetched %d indices from FMP\n", len(indices))

	// Fetch delisted companies
	delisted, err := fmp.FetchDelistedCompanies()
	if err != nil {
		return fmt.Errorf("failed to fetch delisted companies: %w", err)
	}
	log.Printf("✓ Fetched %d delisted companies from FMP\n", len(delisted))

	// Build delisted map for fast lookup
	delistedMap := make(map[string]bool)
	for _, d := range delisted {
		delistedMap[d.Symbol] = true
	}

	// Combine all symbols and filter out delisted ones
	allSymbols := append(stocks, indices...)
	filteredSymbols := make([]fmp.Symbol, 0, len(allSymbols))
	delistedCount := 0

	for _, symbol := range allSymbols {
		if !delistedMap[symbol.Symbol] {
			filteredSymbols = append(filteredSymbols, symbol)
		} else {
			delistedCount++
		}
	}

	if delistedCount > 0 {
		log.Printf("  Filtered out %d delisted symbols\n", delistedCount)
	}

	allSymbols = filteredSymbols

	dbTickers, err := db.GetAllTickers()
	if err != nil {
		return fmt.Errorf("failed to get DB tickers: %w", err)
	}
	log.Printf("  Found %d symbols in database\n", len(dbTickers))

	// Build keep list from all symbols
	keepList := make([]string, 0, len(allSymbols))
	for _, symbol := range allSymbols {
		keepList = append(keepList, symbol.Symbol)
	}
	if err := db.DeactivateSymbolsNotInList(keepList); err != nil {
		return fmt.Errorf("failed to deactivate old symbols: %w", err)
	}

	// Build DB ticker map
	dbTickerMap := make(map[string]bool)
	for _, ticker := range dbTickers {
		dbTickerMap[ticker] = true
	}

	// Add new symbols (stubs only)
	newCount := 0
	for _, symbol := range allSymbols {
		if !dbTickerMap[symbol.Symbol] {

			dbSymbol := &types.Symbol{
				Ticker: symbol.Symbol,
			}

			// Set type for indices
			if symbol.IsIndex() {
				dbSymbol.Type = f.Ptr(string(types.TypeIndex))
				dbSymbol.IsActivelyTrading = f.Ptr(true)
			} else {
				dbSymbol.Type = f.Ptr(string(types.TypeStock))
			}

			if err := db.PutSymbols([]types.Symbol{*dbSymbol}); err != nil {
				return fmt.Errorf("failed to insert %s: %w", symbol.Symbol, err)
			}
			newCount++
		}
	}

	log.Printf("✓ Added %d new symbols\n", newCount)
	
	// Complete batch log
	if batchID > 0 {
		totalProcessed := len(allSymbols)
		if err := db.CompleteBatchUpdate(batchID, totalProcessed, newCount); err != nil {
			log.Errorf("Failed to complete batch log: %v\n", err)
		}
	}
	
	return nil
}
