package updater

import (
	"context"
	"fmt"
	"sync"
	"time"

	"github.com/flocko-motion/gofins/pkg/calculator"
	"github.com/flocko-motion/gofins/pkg/db"
	"github.com/flocko-motion/gofins/pkg/fmp"
	"github.com/flocko-motion/gofins/pkg/forex"
	"github.com/flocko-motion/gofins/pkg/log"
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
func UpdateQuotes(ctx context.Context, date time.Time, log *log.Logger) error {
	log.Printf("Starting quote update for %s\n", date.Format("2006-01-02"))

	// Get list of tickers that need quote updates (not from yesterday)
	tickersNeedingUpdate, err := db.GetTickersNeedingQuoteUpdate()
	if err != nil {
		log.Errorf("Failed to get tickers needing update: %v\n", err)
		return fmt.Errorf("failed to get tickers needing update: %w", err)
	}

	if len(tickersNeedingUpdate) == 0 {
		log.Printf("✓ All quotes already up-to-date\n")
		return nil
	}

	log.Printf("  %d tickers need quote updates\n", len(tickersNeedingUpdate))

	// Start batch update log
	logID, err := db.StartBatchUpdate("quote")
	if err != nil {
		log.Errorf("Failed to start batch update log: %v\n", err)
		return fmt.Errorf("failed to start batch update log: %w", err)
	}

	// Check if we can do incremental price history updates
	isStartOfWeek := calculator.IsStartOfWeek(date)
	isStartOfMonth := calculator.IsStartOfMonth(date)

	var weeklyUpdateMap, monthlyUpdateMap map[string]bool
	if isStartOfWeek || isStartOfMonth {
		log.Printf("  Today is start of week/month - checking for incremental price updates\n")
		weeklyUpdateMap, monthlyUpdateMap, err = getSymbolsNeedingIncrementalUpdate(date, log)
		if err != nil {
			log.Errorf("Failed to get incremental update candidates: %v\n", err)
			// Continue anyway - not critical
		} else {
			total := len(weeklyUpdateMap) + len(monthlyUpdateMap)
			if total > 0 {
				log.Printf("  Found %d symbols eligible for incremental updates (%d weekly, %d monthly)\n",
					total, len(weeklyUpdateMap), len(monthlyUpdateMap))
			}
		}
	}

	// Fetch all symbol currencies from database
	symbolCurrencies, err := db.GetAllSymbolCurrencies()
	if err != nil {
		log.Errorf("Failed to get symbol currencies: %v\n", err)
		_ = db.FailBatchUpdate(logID, fmt.Sprintf("Failed to get symbol currencies: %v", err))
		return fmt.Errorf("failed to get symbol currencies: %w", err)
	}
	log.Printf("  Loaded %d symbols with currencies\n", len(symbolCurrencies))

	// Fetch bulk EOD data from FMP
	bulkQuotes, err := fmp.GetBulkEOD(date)
	if err != nil {
		log.Errorf("Failed to fetch bulk EOD: %v\n", err)
		_ = db.FailBatchUpdate(logID, fmt.Sprintf("Failed to fetch bulk EOD: %v", err))
		return fmt.Errorf("failed to fetch bulk EOD: %w", err)
	}
	log.Printf("  Fetched %d quotes from FMP\n", len(bulkQuotes))

	// Filter to only quotes that need updating
	filteredQuotes := make(map[string]*types.PriceData)
	for ticker, priceData := range bulkQuotes {
		if tickersNeedingUpdate[ticker] {
			filteredQuotes[ticker] = priceData
		}
	}

	log.Printf("  Filtered to %d quotes that need updates\n", len(filteredQuotes))

	// Convert prices to USD and prepare for database update
	// Use yesterday as the quote date (normalized to start of day)
	yesterday := calculator.Yesterday()
	quotes := convertQuotesToUSD(filteredQuotes, symbolCurrencies, yesterday, log)
	log.Printf("  Converted %d quotes to USD\n", len(quotes))

	// Process incremental price history updates if applicable
	incrementalUpdates := 0
	if len(weeklyUpdateMap) > 0 || len(monthlyUpdateMap) > 0 {
		incrementalUpdates = processIncrementalPriceUpdates(quotes, bulkQuotes, weeklyUpdateMap, monthlyUpdateMap, date, log)
		if incrementalUpdates > 0 {
			log.Printf("  ✓ Applied %d incremental price history updates\n", incrementalUpdates)
		}
	}

	// Update database (batching handled in db.UpdateQuotes)
	if err := db.UpdateQuotes(quotes); err != nil {
		log.Errorf("Failed to update quotes: %v\n", err)
		_ = db.FailBatchUpdate(logID, fmt.Sprintf("Failed to update quotes: %v", err))
		return fmt.Errorf("failed to update quotes: %w", err)
	}
	updated := len(quotes)

	// Complete batch update log
	if err := db.CompleteBatchUpdate(logID, len(bulkQuotes), updated); err != nil {
		log.Errorf("Failed to complete batch update log: %v\n", err)
	}

	log.Printf("✓ Quote update complete: %d/%d symbols updated\n", updated, len(bulkQuotes))
	return nil
}

// convertQuotesToUSD converts quotes to USD based on symbol currencies
func convertQuotesToUSD(bulkQuotes map[string]*types.PriceData, symbolCurrencies map[string]string, date time.Time, log *log.Logger) []types.Symbol {
	var quotes []types.Symbol
	conversionErrors := 0

	// Normalize the date to start of day for consistency
	normalizedDate := calculator.StartOfDay(date)

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
			CurrentPriceTime: &normalizedDate,
		})
	}

	if conversionErrors > 0 {
		log.Warnf("%d currency conversion errors\n", conversionErrors)
	}

	return quotes
}

// UpdateQuotesOnce runs a single quote update for yesterday's date
func UpdateQuotesOnce(ctx context.Context) error {
	log := NewLogger("Quotes")
	yesterday := time.Now().AddDate(0, 0, -1)
	return UpdateQuotes(ctx, yesterday, log)
}

// getSymbolsNeedingIncrementalUpdate returns two maps of symbols that need incremental updates
// Returns weeklyMap[ticker]bool and monthlyMap[ticker]bool
func getSymbolsNeedingIncrementalUpdate(date time.Time, log *log.Logger) (map[string]bool, map[string]bool, error) {
	weeklyMap := make(map[string]bool)
	monthlyMap := make(map[string]bool)

	// Get symbols with stale prices
	symbols, err := db.GetSymbolsWithStalePrices(10000)
	if err != nil {
		return nil, nil, fmt.Errorf("failed to get stale symbols: %w", err)
	}

	isStartOfWeek := calculator.IsStartOfWeek(date)
	isStartOfMonth := calculator.IsStartOfMonth(date)
	todayWeekStart := calculator.StartOfWeek(date)
	todayMonthStart := calculator.StartOfMonth(date)

	for _, symbol := range symbols {
		// Check weekly
		if isStartOfWeek {
			latestWeekly, err := db.GetLatestPriceDate(symbol.Ticker, types.IntervalWeekly)
			if err == nil && latestWeekly != nil {
				expectedNext := latestWeekly.AddDate(0, 0, 7) // One week later
				if expectedNext.Equal(todayWeekStart) {
					weeklyMap[symbol.Ticker] = true
				}
			}
		}

		// Check monthly
		if isStartOfMonth {
			latestMonthly, err := db.GetLatestPriceDate(symbol.Ticker, types.IntervalMonthly)
			if err == nil && latestMonthly != nil {
				expectedNext := latestMonthly.AddDate(0, 1, 0) // One month later
				if expectedNext.Equal(todayMonthStart) {
					monthlyMap[symbol.Ticker] = true
				}
			}
		}
	}

	return weeklyMap, monthlyMap, nil
}

// processIncrementalPriceUpdates appends price points for symbols in the weekly and monthly maps
func processIncrementalPriceUpdates(quotes []types.Symbol, bulkQuotes map[string]*types.PriceData, weeklyMap, monthlyMap map[string]bool, date time.Time, log *log.Logger) int {
	updated := 0

	weekStart := calculator.StartOfWeek(date)
	monthStart := calculator.StartOfMonth(date)

	for _, quote := range quotes {
		// Get the raw price data for this symbol
		priceData, exists := bulkQuotes[quote.Ticker]
		if !exists {
			continue
		}

		// Check if needs weekly update
		if weeklyMap[quote.Ticker] {
			if err := appendPricePoint(priceData, weekStart, types.IntervalWeekly); err != nil {
				log.Errorf("Failed to append weekly price for %s: %v\n", quote.Ticker, err)
			} else {
				updated++
			}
		}

		// Check if needs monthly update
		if monthlyMap[quote.Ticker] {
			if err := appendPricePoint(priceData, monthStart, types.IntervalMonthly); err != nil {
				log.Errorf("Failed to append monthly price for %s: %v\n", quote.Ticker, err)
			} else {
				updated++
			}
		}
	}

	return updated
}

// appendPricePoint creates and appends a price point to the database
func appendPricePoint(priceData *types.PriceData, periodStart time.Time, interval types.PriceInterval) error {
	newPrice := types.PriceData{
		Date:         periodStart,
		Open:         priceData.Open,
		High:         priceData.High,
		Low:          priceData.Low,
		Close:        priceData.Close,
		Avg:          priceData.Close, // Use close as avg for single-day period
		SymbolTicker: priceData.SymbolTicker,
	}
	return db.AppendSinglePrice(newPrice, interval)
}

// RunQuoteUpdater runs the quote updater in a loop
func RunQuoteUpdater(ctx context.Context, wg *sync.WaitGroup, log *log.Logger) {
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
		log.Errorf("Quote update failed: %v\n", err)
	}

	for {
		select {
		case <-ctx.Done():
			log.Printf("Quote updater stopped\n")
			return
		case <-ticker.C:
			yesterday := time.Now().AddDate(0, 0, -1)
			if err := UpdateQuotes(ctx, yesterday, log); err != nil {
				log.Errorf("Quote update failed: %v\n", err)
			}
		}
	}
}
