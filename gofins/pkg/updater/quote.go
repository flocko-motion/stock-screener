package updater

import (
	"context"
	"fmt"
	"sync"
	"time"

	"github.com/flocko-motion/gofins/pkg/db"
	"github.com/flocko-motion/gofins/pkg/fmp"
	"github.com/flocko-motion/gofins/pkg/forex"
	"github.com/flocko-motion/gofins/pkg/types"
)

const (
	QuoteUpdateInterval = 24 * time.Hour
	QuoteBatchSize      = 1000 // Write to DB in batches
)

var (
	quoteUpdaterRunning bool
	quoteUpdaterMutex   sync.Mutex
)

// UpdateQuotes fetches bulk EOD data and updates current prices for all symbols
func UpdateQuotes(ctx context.Context, date time.Time, log *Logger) error {
	log.Printf("Starting quote update for %s\n", date.Format("2006-01-02"))

	// Start batch update log
	logID, err := db.StartBatchUpdate("quote")
	if err != nil {
		log.Error("Failed to start batch update log: %v\n", err)
		return fmt.Errorf("failed to start batch update log: %w", err)
	}

	// Fetch all symbol currencies from database
	symbolCurrencies, err := db.GetAllSymbolCurrencies()
	if err != nil {
		log.Error("Failed to get symbol currencies: %v\n", err)
		_ = db.FailBatchUpdate(logID, fmt.Sprintf("Failed to get symbol currencies: %v", err))
		return fmt.Errorf("failed to get symbol currencies: %w", err)
	}
	log.Printf("  Loaded %d symbols with currencies\n", len(symbolCurrencies))

	// Fetch bulk EOD data from FMP
	bulkQuotes, err := fmp.GetBulkEOD(date)
	if err != nil {
		log.Error("Failed to fetch bulk EOD: %v\n", err)
		_ = db.FailBatchUpdate(logID, fmt.Sprintf("Failed to fetch bulk EOD: %v", err))
		return fmt.Errorf("failed to fetch bulk EOD: %w", err)
	}
	log.Printf("  Fetched %d quotes from FMP\n", len(bulkQuotes))

	// Convert prices to USD and prepare for database update
	weekStart := time.Date(date.Year(), date.Month(), date.Day(), 0, 0, 0, 0, time.UTC)
	quotes := convertQuotesToUSD(bulkQuotes, symbolCurrencies, weekStart, log)
	log.Printf("  Converted %d quotes to USD\n", len(quotes))

	// Update database in batches
	updated, err := updateQuotesInBatches(quotes, log)
	if err != nil {
		log.Error("Failed to update quotes: %v\n", err)
		_ = db.FailBatchUpdate(logID, fmt.Sprintf("Failed to update quotes: %v", err))
		return fmt.Errorf("failed to update quotes: %w", err)
	}

	// Complete batch update log
	if err := db.CompleteBatchUpdate(logID, len(bulkQuotes), updated); err != nil {
		log.Error("Failed to complete batch update log: %v\n", err)
	}

	log.Printf("✓ Quote update complete: %d/%d symbols updated\n", updated, len(bulkQuotes))
	return nil
}

// convertQuotesToUSD converts quotes to USD based on symbol currencies
func convertQuotesToUSD(bulkQuotes map[string]*types.PriceData, symbolCurrencies map[string]string, date time.Time, log *Logger) []types.Symbol {
	var quotes []types.Symbol
	conversionErrors := 0

	for symbol, quote := range bulkQuotes {
		currency, hasCurrency := symbolCurrencies[symbol]
		if !hasCurrency {
			// Symbol not in our database, skip
			continue
		}

		var closeUSD float64

		// Convert to USD if needed
		if currency == "" || currency == "USD" {
			closeUSD = quote.Close
		} else {
			converted, err := forex.ConvertToUsd(quote.Close, currency, date)
			if err != nil {
				conversionErrors++
				// Log to database for persistence
				_ = db.LogError("updater.quote", "conversion_error", 
					fmt.Sprintf("Failed to convert %s from %s to USD: %v", symbol, currency, err), 
					nil)
				continue
			}
			closeUSD = converted
		}

		quotes = append(quotes, types.Symbol{
			Ticker:           symbol,
			CurrentPriceUsd:  &closeUSD,
			CurrentPriceTime: &quote.Date,
		})
	}

	if conversionErrors > 0 {
		log.Printf("⚠️  %d currency conversion errors (logged to database)\n", conversionErrors)
	}

	return quotes
}

// updateQuotesInBatches updates quotes in the database in batches
func updateQuotesInBatches(quotes []types.Symbol, log *Logger) (int, error) {
	totalUpdated := 0

	for i := 0; i < len(quotes); i += QuoteBatchSize {
		end := i + QuoteBatchSize
		if end > len(quotes) {
			end = len(quotes)
		}

		batch := quotes[i:end]

		// Update batch using database module
		if err := db.UpdateQuoteBatch(batch); err != nil {
			return totalUpdated, fmt.Errorf("failed to update batch %d-%d: %w", i+1, end, err)
		}

		totalUpdated += len(batch)
		log.Printf("Updated batch %d-%d (%d/%d symbols)\n", i+1, end, totalUpdated, len(quotes))
	}

	return totalUpdated, nil
}

// RunQuoteUpdater runs the quote updater in a loop
func RunQuoteUpdater(ctx context.Context, wg *sync.WaitGroup, log *Logger) {
	defer wg.Done()

	// Singleton check
	quoteUpdaterMutex.Lock()
	if quoteUpdaterRunning {
		log.Printf("Quote updater already running, skipping\n")
		quoteUpdaterMutex.Unlock()
		return
	}
	quoteUpdaterRunning = true
	quoteUpdaterMutex.Unlock()

	defer func() {
		quoteUpdaterMutex.Lock()
		quoteUpdaterRunning = false
		quoteUpdaterMutex.Unlock()
	}()

	ticker := time.NewTicker(QuoteUpdateInterval)
	defer ticker.Stop()

	// Run immediately on start
	yesterday := time.Now().AddDate(0, 0, -1)
	if err := UpdateQuotes(ctx, yesterday, log); err != nil {
		log.Error("Quote update failed: %v\n", err)
	}

	for {
		select {
		case <-ctx.Done():
			log.Printf("Quote updater stopped\n")
			return
		case <-ticker.C:
			yesterday := time.Now().AddDate(0, 0, -1)
			if err := UpdateQuotes(ctx, yesterday, log); err != nil {
				log.Error("Quote update failed: %v\n", err)
			}
		}
	}
}
