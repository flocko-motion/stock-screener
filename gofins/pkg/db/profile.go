package db

import (
	"database/sql"
	"fmt"
	"strings"
	"time"

	"github.com/flocko-motion/gofins/pkg/calculator"
	"github.com/flocko-motion/gofins/pkg/types"
)

// PutSymbols inserts or updates multiple symbol profiles using batched transactions
// Automatically handles large datasets by batching into chunks of 1000 symbols
func PutSymbols(symbols []types.Symbol) error {
	if len(symbols) == 0 {
		return nil
	}

	const batchSize = 1000
	totalSymbols := len(symbols)

	// Only show detailed progress for larger updates
	showProgress := totalSymbols > 100
	startTime := time.Now()

	// Process in batches
	for i := 0; i < totalSymbols; i += batchSize {
		end := i + batchSize
		if end > totalSymbols {
			end = totalSymbols
		}

		batch := symbols[i:end]

		if err := putSymbolsBatch(batch); err != nil {
			return fmt.Errorf("failed to insert batch %d-%d: %w", i+1, end, err)
		}

		if showProgress {
			count := i*batchSize + len(batch)
			dbLogger.ProgressShort(count, totalSymbols-count, time.Since(startTime))
		}
	}

	return nil
}

// putSymbolsBatch inserts a single batch of symbols in one transaction
func putSymbolsBatch(symbols []types.Symbol) error {
	db := Db()
	tx, err := db.conn.Begin()
	if err != nil {
		return fmt.Errorf("failed to begin transaction: %w", err)
	}
	defer tx.Rollback()

	stmt, err := tx.Prepare(`
		INSERT INTO symbols (
			ticker, exchange, last_price_update, last_profile_update, 
			last_price_status, last_profile_status,
			name, type, currency, sector, industry, country, description, website, isin, cik, inception, oldest_price,
			is_actively_trading, market_cap, primary_listing, ath12m, current_price_usd, current_price_time
		) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19, $20, $21, $22, $23, $24)
		ON CONFLICT (ticker) DO UPDATE SET
			exchange = COALESCE(EXCLUDED.exchange, symbols.exchange),
			last_price_update = COALESCE(EXCLUDED.last_price_update, symbols.last_price_update),
			last_profile_update = COALESCE(EXCLUDED.last_profile_update, symbols.last_profile_update),
			last_price_status = COALESCE(EXCLUDED.last_price_status, symbols.last_price_status),
			last_profile_status = COALESCE(EXCLUDED.last_profile_status, symbols.last_profile_status),
			name = COALESCE(EXCLUDED.name, symbols.name),
			type = COALESCE(EXCLUDED.type, symbols.type),
			currency = COALESCE(EXCLUDED.currency, symbols.currency),
			sector = COALESCE(EXCLUDED.sector, symbols.sector),
			industry = COALESCE(EXCLUDED.industry, symbols.industry),
			country = COALESCE(EXCLUDED.country, symbols.country),
			description = COALESCE(EXCLUDED.description, symbols.description),
			website = COALESCE(EXCLUDED.website, symbols.website),
			isin = COALESCE(EXCLUDED.isin, symbols.isin),
			cik = COALESCE(EXCLUDED.cik, symbols.cik),
			inception = COALESCE(EXCLUDED.inception, symbols.inception),
			oldest_price = COALESCE(EXCLUDED.oldest_price, symbols.oldest_price),
			is_actively_trading = COALESCE(EXCLUDED.is_actively_trading, symbols.is_actively_trading),
			market_cap = COALESCE(EXCLUDED.market_cap, symbols.market_cap),
			primary_listing = COALESCE(EXCLUDED.primary_listing, symbols.primary_listing),
			ath12m = COALESCE(EXCLUDED.ath12m, symbols.ath12m),
			current_price_usd = COALESCE(EXCLUDED.current_price_usd, symbols.current_price_usd),
			current_price_time = COALESCE(EXCLUDED.current_price_time, symbols.current_price_time)
	`)
	if err != nil {
		return fmt.Errorf("failed to prepare statement: %w", err)
	}
	defer stmt.Close()

	for _, s := range symbols {
		_, err := stmt.Exec(
			s.Ticker, s.Exchange, s.LastPriceUpdate, s.LastProfileUpdate,
			s.LastPriceStatus, s.LastProfileStatus,
			s.Name, s.Type, s.Currency, s.Sector, s.Industry, s.Country, s.Description, s.Website, s.ISIN, s.CIK, s.Inception, s.OldestPrice,
			s.IsActivelyTrading, s.MarketCap, s.PrimaryListing, s.Ath12M, s.CurrentPriceUsd, s.CurrentPriceTime,
		)
		if err != nil {
			return fmt.Errorf("failed to insert symbol %s: %w", s.Ticker, err)
		}
	}

	if err := tx.Commit(); err != nil {
		return fmt.Errorf("failed to commit transaction: %w", err)
	}

	return nil
}

// GetSymbol retrieves a symbol by ticker
func GetSymbol(ticker string) (*types.Symbol, error) {
	db := Db()
	query := `
		SELECT s.ticker, s.exchange, s.last_price_update, s.last_profile_update,
			   s.last_price_status, s.last_profile_status,
			   s.name, s.type, s.currency, s.sector, s.industry, s.country,
			   s.description, s.website, s.isin, s.cik, s.inception, s.oldest_price, s.is_actively_trading, s.market_cap, s.primary_listing,
			   s.ath12m, s.current_price_usd, s.current_price_time,
			   COALESCE(f.ticker IS NOT NULL, false) as is_favorite
		FROM symbols s
		LEFT JOIN user_favorites f ON s.ticker = f.ticker
		WHERE s.ticker = $1
	`

	s := &types.Symbol{}
	err := db.conn.QueryRow(query, ticker).Scan(
		&s.Ticker, &s.Exchange, &s.LastPriceUpdate, &s.LastProfileUpdate,
		&s.LastPriceStatus, &s.LastProfileStatus,
		&s.Name, &s.Type, &s.Currency, &s.Sector, &s.Industry, &s.Country,
		&s.Description, &s.Website, &s.ISIN, &s.CIK, &s.Inception, &s.OldestPrice, &s.IsActivelyTrading, &s.MarketCap, &s.PrimaryListing,
		&s.Ath12M, &s.CurrentPriceUsd, &s.CurrentPriceTime,
		&s.IsFavorite,
	)

	if err == sql.ErrNoRows {
		return nil, nil
	}
	if err != nil {
		return nil, err
	}

	return s, nil
}

// GetAllTickers returns all tickers from the symbols table
func GetAllTickers() ([]string, error) {
	db := Db()
	rows, err := db.conn.Query("SELECT ticker FROM symbols")
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var tickers []string
	for rows.Next() {
		var ticker string
		if err := rows.Scan(&ticker); err != nil {
			return nil, err
		}
		tickers = append(tickers, ticker)
	}

	return tickers, rows.Err()
}

// DeactivateSymbolsNotInList marks symbols not in the provided list as inactive
func DeactivateSymbolsNotInList(keepTickers []string) error {
	db := Db()
	if len(keepTickers) == 0 {
		return nil
	}

	// Get all current tickers from database
	allTickers, err := GetAllTickers()
	if err != nil {
		return fmt.Errorf("failed to get all tickers: %w", err)
	}

	// Build a set of tickers to keep
	keepSet := make(map[string]bool, len(keepTickers))
	for _, ticker := range keepTickers {
		keepSet[ticker] = true
	}

	// Find tickers to deactivate (in DB but not in keep list)
	var toDeactivate []string
	for _, ticker := range allTickers {
		if !keepSet[ticker] {
			toDeactivate = append(toDeactivate, ticker)
		}
	}

	if len(toDeactivate) == 0 {
		return nil // Nothing to deactivate
	}

	// Deactivate in batches to avoid parameter limit
	batchSize := 10000
	totalToDeactivate := len(toDeactivate)
	showProgress := totalToDeactivate > 100
	startTime := time.Now()

	for i := 0; i < totalToDeactivate; i += batchSize {
		end := i + batchSize
		if end > totalToDeactivate {
			end = totalToDeactivate
		}
		batch := toDeactivate[i:end]

		// Build placeholders for this batch
		placeholders := make([]string, len(batch))
		args := make([]interface{}, len(batch))
		for j, ticker := range batch {
			placeholders[j] = fmt.Sprintf("$%d", j+1)
			args[j] = ticker
		}

		query := fmt.Sprintf("UPDATE symbols SET is_actively_trading = false WHERE ticker IN (%s)", strings.Join(placeholders, ","))
		if _, err := db.conn.Exec(query, args...); err != nil {
			return fmt.Errorf("failed to deactivate batch: %w", err)
		}

		if showProgress {
			count := end
			dbLogger.ProgressShort(count, totalToDeactivate-count, time.Since(startTime))
		}
	}

	return nil
}

// getFilteredSymbols returns symbols with optional additional WHERE conditions
func getFilteredSymbols(additionalWhere []string) ([]types.Symbol, error) {
	db := Db()

	// Base WHERE conditions
	whereConditions := []string{
		"s.is_actively_trading = true",
		"(s.type = $1 OR s.type IS NULL)",
		"(s.primary_listing IS NULL OR s.primary_listing = '')",
	}

	// Add any additional conditions
	whereConditions = append(whereConditions, additionalWhere...)

	// Build WHERE clause
	whereClause := "WHERE " + whereConditions[0]
	for _, condition := range whereConditions[1:] {
		whereClause += "\n\t\t  AND " + condition
	}

	query := `
		SELECT 
			s.ticker, s.exchange, s.name, s.type, s.currency, s.sector, s.industry, s.country, 
			s.inception, s.oldest_price, s.market_cap, s.ath12m, s.current_price_usd,
			COALESCE(f.ticker IS NOT NULL, false) as is_favorite,
			r.rating
		FROM symbols s
		LEFT JOIN user_favorites f ON s.ticker = f.ticker
		LEFT JOIN LATERAL (
			SELECT rating 
			FROM user_ratings 
			WHERE ticker = s.ticker 
			ORDER BY created_at DESC 
			LIMIT 1
		) r ON true
		` + whereClause + `
		ORDER BY s.ticker
	`

	rows, err := db.conn.Query(query, types.TypeStock)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var symbols []types.Symbol
	for rows.Next() {
		var s types.Symbol
		if err := rows.Scan(
			&s.Ticker, &s.Exchange, &s.Name, &s.Type, &s.Currency, &s.Sector, &s.Industry, &s.Country, &s.Inception, &s.OldestPrice, &s.MarketCap, &s.Ath12M, &s.CurrentPriceUsd,
			&s.IsFavorite, &s.UserRating,
		); err != nil {
			return nil, err
		}
		symbols = append(symbols, s)
	}

	return symbols, rows.Err()
}

// GetActiveSymbols returns all actively trading stocks (excludes indices and secondary listings)
func GetActiveSymbols() ([]types.Symbol, error) {
	return getFilteredSymbols(nil)
}

// GetFavoriteSymbols returns only favorited actively trading stocks
func GetFavoriteSymbols() ([]types.Symbol, error) {
	return getFilteredSymbols([]string{"f.ticker IS NOT NULL"})
}

// GetStaleProfiles returns symbols with outdated profiles (older than threshold or null)
// Excludes indices and secondary listings (they don't need profile updates)
func GetStaleProfiles(limit int) ([]string, error) {
	db := Db()
	query := `
		SELECT ticker FROM symbols
		WHERE (last_profile_update IS NULL OR last_profile_update < $1)
		  AND (type IS NULL OR type != $2)
		  AND (primary_listing IS NULL OR primary_listing = '')
		ORDER BY last_profile_update ASC NULLS FIRST
		LIMIT $3
	`

	rows, err := db.conn.Query(query, GetProfileThreshold(), types.TypeIndex, limit)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var tickers []string
	for rows.Next() {
		var ticker string
		if err := rows.Scan(&ticker); err != nil {
			return nil, err
		}
		tickers = append(tickers, ticker)
	}

	return tickers, rows.Err()
}

// GetProfileThreshold returns the threshold for stale profiles (30 days ago)
func GetProfileThreshold() time.Time {
	return time.Now().UTC().AddDate(0, 0, -30)
}

// CountSymbols returns the total number of symbols
func CountSymbols() (int, error) {
	db := Db()
	query := `SELECT COUNT(*) FROM symbols`

	var count int
	err := db.conn.QueryRow(query).Scan(&count)
	return count, err
}

// CountActivelyTrading returns the count of actively trading symbols
func CountActivelyTrading() (int, error) {
	db := Db()
	query := `SELECT COUNT(*) FROM symbols WHERE is_actively_trading = true`

	var count int
	err := db.conn.QueryRow(query).Scan(&count)
	return count, err
}

// CountStaleProfiles returns the count of stale profiles
// Excludes indices as they don't have profile endpoints
func CountStaleProfiles() (int, error) {
	db := Db()
	query := `
		SELECT COUNT(*) FROM symbols
		WHERE (last_profile_update IS NULL OR last_profile_update < $1)
		  AND (type IS NULL OR type != $2)
	`

	var count int
	err := db.conn.QueryRow(query, GetProfileThreshold(), types.TypeIndex).Scan(&count)
	return count, err
}

// GetOldestProfileUpdate returns the oldest profile update timestamp
func GetOldestProfileUpdate() (*time.Time, error) {
	db := Db()
	query := `
		SELECT MIN(last_profile_update) FROM symbols
		WHERE last_profile_update IS NOT NULL
	`

	var oldest *time.Time
	err := db.conn.QueryRow(query).Scan(&oldest)
	if err == sql.ErrNoRows {
		return nil, nil
	}
	return oldest, err
}

// ResetQuoteTimestamps resets all current quote timestamps to force fresh reload
func ResetQuoteTimestamps() (int64, error) {
	db := Db()
	result, err := db.conn.Exec(`
		UPDATE symbols 
		SET current_price_time = NULL
	`)
	if err != nil {
		return 0, err
	}
	return result.RowsAffected()
}

// ResetPriceTimestamps resets all price update timestamps to force fresh reload
func ResetPriceTimestamps() (int64, error) {
	db := Db()
	result, err := db.conn.Exec(`
		UPDATE symbols 
		SET last_price_update = NULL, last_price_status = NULL
	`)
	if err != nil {
		return 0, err
	}
	return result.RowsAffected()
}

// ResetProfileTimestamps resets all profile update timestamps to force fresh reload
func ResetProfileTimestamps() (int64, error) {
	db := Db()
	result, err := db.conn.Exec(`
		UPDATE symbols 
		SET last_profile_update = NULL, last_profile_status = NULL
	`)
	if err != nil {
		return 0, err
	}
	return result.RowsAffected()
}

// GetSymbolsByStatus returns all symbols with a specific status
// statusType should be "profile" or "price"
func GetSymbolsByStatus(status string, statusType string) ([]types.Symbol, error) {
	db := Db()

	var query string
	if statusType == "profile" {
		query = `
			SELECT ticker, exchange, name, type, last_profile_status, last_profile_update
			FROM symbols
			WHERE last_profile_status = $1
			ORDER BY last_profile_update ASC, ticker
		`
	} else if statusType == "price" {
		query = `
			SELECT ticker, exchange, name, type, last_price_status, last_price_update
			FROM symbols
			WHERE last_price_status = $1
			ORDER BY last_price_update ASC, ticker
		`
	} else {
		return nil, nil
	}

	rows, err := db.conn.Query(query, status)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var symbols []types.Symbol
	for rows.Next() {
		var s types.Symbol
		if statusType == "profile" {
			err = rows.Scan(&s.Ticker, &s.Exchange, &s.Name, &s.Type, &s.LastProfileStatus, &s.LastProfileUpdate)
		} else {
			err = rows.Scan(&s.Ticker, &s.Exchange, &s.Name, &s.Type, &s.LastPriceStatus, &s.LastPriceUpdate)
		}
		if err != nil {
			return nil, err
		}
		symbols = append(symbols, s)
	}

	return symbols, rows.Err()
}

// ResetIndexTimestamps resets timestamps for indices and marks them as actively trading
func ResetIndexTimestamps() (int64, error) {
	db := Db()
	result, err := db.conn.Exec(`
		UPDATE symbols 
		SET last_price_update = NULL, 
		    last_price_status = NULL,
		    last_profile_update = NULL,
		    last_profile_status = NULL,
		    is_actively_trading = true
		WHERE type = $1
	`, types.TypeIndex)
	if err != nil {
		return 0, err
	}
	return result.RowsAffected()
}

// GetAllSymbolCurrencies returns a map of ticker -> currency for all symbols
func GetAllSymbolCurrencies() (map[string]string, error) {
	db := Db()

	rows, err := db.conn.Query(`
		SELECT ticker, COALESCE(currency, 'USD') as currency
		FROM symbols
	`)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	currencies := make(map[string]string)
	for rows.Next() {
		var ticker, currency string
		if err := rows.Scan(&ticker, &currency); err != nil {
			return nil, err
		}
		currencies[ticker] = currency
	}

	return currencies, rows.Err()
}

// MarkStaleProfilesAsNotFound marks all profiles that haven't been updated since the given time as not found
func MarkStaleProfilesAsNotFound(since time.Time) (int64, error) {
	db := Db()

	result, err := db.conn.Exec(`
		UPDATE symbols
		SET last_profile_status = $1
		WHERE last_profile_update < $2
		   OR last_profile_update IS NULL
	`, types.StatusNotFound, since)

	if err != nil {
		return 0, fmt.Errorf("failed to mark stale profiles as not found: %w", err)
	}

	return result.RowsAffected()
}

// GetTickersNeedingProfileUpdate returns tickers that don't have profiles updated yesterday or later
func GetTickersNeedingProfileUpdate() (map[string]bool, error) {
	db := Db()
	yesterday := calculator.Yesterday()

	query := `
		SELECT ticker 
		FROM symbols 
		WHERE last_profile_update IS NULL 
		   OR last_profile_update < $1
	`

	rows, err := db.conn.Query(query, yesterday)
	if err != nil {
		return nil, fmt.Errorf("failed to get tickers needing profile update: %w", err)
	}
	defer rows.Close()

	result := make(map[string]bool)
	for rows.Next() {
		var ticker string
		if err := rows.Scan(&ticker); err != nil {
			return nil, fmt.Errorf("failed to scan ticker: %w", err)
		}
		result[ticker] = true
	}

	return result, rows.Err()
}

// GetTickersNeedingQuoteUpdate returns tickers that don't have quotes from yesterday
func GetTickersNeedingQuoteUpdate() (map[string]bool, error) {
	db := Db()
	yesterday := calculator.StartOfDay(time.Now().AddDate(0, 0, -1))

	query := `
		SELECT ticker 
		FROM symbols 
		WHERE current_price_time IS NULL 
		   OR current_price_time < $1
	`

	rows, err := db.conn.Query(query, yesterday)
	if err != nil {
		return nil, fmt.Errorf("failed to get tickers needing update: %w", err)
	}
	defer rows.Close()

	result := make(map[string]bool)
	for rows.Next() {
		var ticker string
		if err := rows.Scan(&ticker); err != nil {
			return nil, fmt.Errorf("failed to scan ticker: %w", err)
		}
		result[ticker] = true
	}

	return result, rows.Err()
}

// UpdateQuotes updates current prices for symbols using batched transactions
// Automatically handles large datasets by batching into chunks of 1000 symbols
func UpdateQuotes(quotes []types.Symbol) error {
	if len(quotes) == 0 {
		return nil
	}

	const batchSize = 1000
	totalQuotes := len(quotes)
	showProgress := totalQuotes > 100
	startTime := time.Now()

	// Process in batches
	for i := 0; i < totalQuotes; i += batchSize {
		end := i + batchSize
		if end > totalQuotes {
			end = totalQuotes
		}

		batch := quotes[i:end]

		if err := updateQuotesBatch(batch); err != nil {
			return fmt.Errorf("failed to update batch %d-%d: %w", i+1, end, err)
		}

		if showProgress {
			count := end
			dbLogger.ProgressShort(count, totalQuotes-count, time.Since(startTime))
		}
	}

	return nil
}

// updateQuotesBatch updates a single batch of quotes in one transaction
func updateQuotesBatch(quotes []types.Symbol) error {
	db := Db()

	// Use a transaction for batch updates
	tx, err := db.conn.Begin()
	if err != nil {
		return fmt.Errorf("failed to begin transaction: %w", err)
	}
	defer tx.Rollback()

	stmt, err := tx.Prepare(`
		UPDATE symbols
		SET current_price_usd = $1,
		    current_price_time = $2
		WHERE ticker = $3
	`)
	if err != nil {
		return fmt.Errorf("failed to prepare statement: %w", err)
	}
	defer stmt.Close()

	for _, quote := range quotes {
		if quote.CurrentPriceUsd == nil || quote.CurrentPriceTime == nil {
			continue
		}
		_, err := stmt.Exec(quote.CurrentPriceUsd, quote.CurrentPriceTime, quote.Ticker)
		if err != nil {
			return fmt.Errorf("failed to update quote for %s: %w", quote.Ticker, err)
		}
	}

	if err := tx.Commit(); err != nil {
		return fmt.Errorf("failed to commit transaction: %w", err)
	}

	return nil
}
