package updater

import (
	"fmt"
	"time"

	"github.com/flocko-motion/gofins/pkg/db"
	"github.com/flocko-motion/gofins/pkg/f"
	"github.com/flocko-motion/gofins/pkg/fmp"
)

func SyncSymbols(database *db.DB, fmpClient *fmp.Client) {
	log := NewLogger("Symbols")

	for {
		if err := syncSymbolsImpl(database, fmpClient, log); err != nil {
			log.Error("Symbol sync failed: %v\n", err)
		}
		time.Sleep(time.Hour * 24 * 7) // Sleep for 7 days
	}
}

func SyncSymbolsOnce(database *db.DB, fmpClient *fmp.Client) error {
	log := NewLogger("Symbols")
	return syncSymbolsImpl(database, fmpClient, log)
}

func syncSymbolsImpl(database *db.DB, fmpClient *fmp.Client, log *Logger) error {
	// Fetch stocks
	stocks, err := fmpClient.FetchStockList()
	if err != nil {
		return fmt.Errorf("failed to fetch stock list: %w", err)
	}
	log.Printf("✓ Fetched %d stocks from FMP\n", len(stocks))

	// Fetch indices
	indices, err := fmpClient.FetchIndexList()
	if err != nil {
		return fmt.Errorf("failed to fetch index list: %w", err)
	}
	log.Printf("✓ Fetched %d indices from FMP\n", len(indices))

	// Fetch delisted companies
	delisted, err := fmpClient.FetchDelistedCompanies()
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

	dbTickers, err := database.GetAllTickers()
	if err != nil {
		return fmt.Errorf("failed to get DB tickers: %w", err)
	}
	log.Printf("  Found %d symbols in database\n", len(dbTickers))

	// Build keep list from all symbols
	keepList := make([]string, 0, len(allSymbols))
	for _, symbol := range allSymbols {
		keepList = append(keepList, symbol.Symbol)
	}
	if err := database.DeactivateSymbolsNotInList(keepList); err != nil {
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

			dbSymbol := &db.Symbol{
				Ticker: symbol.Symbol,
			}

			// Set type for indices
			if symbol.IsIndex() {
				dbSymbol.Type = f.Ptr(string(db.TypeIndex))
				dbSymbol.IsActivelyTrading = f.Ptr(true)
			} else {
				dbSymbol.Type = f.Ptr(string(db.TypeStock))
			}

			if err := database.PutSymbol(dbSymbol); err != nil {
				return fmt.Errorf("failed to insert %s: %w", symbol.Symbol, err)
			}
			newCount++
		}
	}

	log.Printf("✓ Added %d new symbols\n", newCount)
	return nil
}
