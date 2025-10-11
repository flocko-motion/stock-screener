package updater

import (
	"fmt"

	"github.com/flocko-motion/gofins/pkg/db"
	"github.com/flocko-motion/gofins/pkg/fmp"
)

func SyncSymbols(database *db.DB, fmpClient *fmp.Client) error {
	// Fetch full symbols list from FMP
	stocks, err := fmpClient.FetchStockList()
	if err != nil {
		return fmt.Errorf("failed to fetch stock list: %w", err)
	}
	fmt.Printf("✓ Fetched %d stocks from FMP\n", len(stocks))

	// Get existing tickers from database
	dbTickers, err := database.GetAllTickers()
	if err != nil {
		return fmt.Errorf("failed to get DB tickers: %w", err)
	}
	fmt.Printf("  Found %d symbols in database\n", len(dbTickers))

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
	fmt.Printf("✓ Added %d new symbols\n", newCount)

	return nil
}
