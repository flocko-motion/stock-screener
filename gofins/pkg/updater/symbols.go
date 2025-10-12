package updater

import (
	"fmt"
	"time"

	"github.com/flocko-motion/gofins/pkg/db"
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
	stocks, err := fmpClient.FetchStockList()
	if err != nil {
		return fmt.Errorf("failed to fetch stock list: %w", err)
	}
	log.Printf("✓ Fetched %d stocks from FMP\n", len(stocks))

	dbTickers, err := database.GetAllTickers()
	if err != nil {
		return fmt.Errorf("failed to get DB tickers: %w", err)
	}
	log.Printf("  Found %d symbols in database\n", len(dbTickers))

	// Delete removed symbols
	keepList := make([]string, 0, len(stocks))
	for _, stock := range stocks {
		keepList = append(keepList, stock.Symbol)
	}
	if err := database.DeleteSymbols(keepList); err != nil {
		return fmt.Errorf("failed to delete old symbols: %w", err)
	}

	// Add new symbols (stubs only)
	dbTickerMap := make(map[string]bool)
	for _, ticker := range dbTickers {
		dbTickerMap[ticker] = true
	}

	newCount := 0
	for _, stock := range stocks {
		if !dbTickerMap[stock.Symbol] {
			if err := database.PutSymbol(&db.Symbol{Ticker: stock.Symbol}); err != nil {
				return fmt.Errorf("failed to insert %s: %w", stock.Symbol, err)
			}
			newCount++
		}
	}
	log.Printf("✓ Added %d new symbols\n", newCount)
	return nil
}
