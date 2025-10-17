package db

import (
	"database/sql"
	"fmt"
	"strings"
	"time"

	"github.com/flocko-motion/gofins/pkg/types"
)


// PutSymbol inserts or updates a symbol profile
// Only updates non-nil fields to avoid overwriting data from other updaters
func PutSymbol(s *types.Symbol) error {
	db := Db()
	query := `
		INSERT INTO symbols (
			ticker, exchange, last_price_update, last_profile_update, 
			last_price_status, last_profile_status,
			name, type, currency, sector, industry, country, description, website, isin, inception, oldest_price,
			is_actively_trading, market_cap
		) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19)
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
			inception = COALESCE(EXCLUDED.inception, symbols.inception),
			oldest_price = COALESCE(EXCLUDED.oldest_price, symbols.oldest_price),
			is_actively_trading = COALESCE(EXCLUDED.is_actively_trading, symbols.is_actively_trading),
			market_cap = COALESCE(EXCLUDED.market_cap, symbols.market_cap)
	`

	_, err := db.conn.Exec(
		query,
		s.Ticker, s.Exchange, s.LastPriceUpdate, s.LastProfileUpdate,
		s.LastPriceStatus, s.LastProfileStatus,
		s.Name, s.Type, s.Currency, s.Sector, s.Industry, s.Country, s.Description, s.Website, s.ISIN, s.Inception, s.OldestPrice,
		s.IsActivelyTrading, s.MarketCap,
	)

	return err
}

// GetSymbol retrieves a symbol by ticker
func GetSymbol(ticker string) (*types.Symbol, error) {
	db := Db()
	query := `
		SELECT ticker, exchange, last_price_update, last_profile_update,
			   last_price_status, last_profile_status,
			   name, type, currency, sector, industry, country,
			   description, website, isin, inception, oldest_price, is_actively_trading, market_cap
		FROM symbols
		WHERE ticker = $1
	`

	s := &types.Symbol{}
	err := db.conn.QueryRow(query, ticker).Scan(
		&s.Ticker, &s.Exchange, &s.LastPriceUpdate, &s.LastProfileUpdate,
		&s.LastPriceStatus, &s.LastProfileStatus,
		&s.Name, &s.Type, &s.Currency, &s.Sector, &s.Industry, &s.Country,
		&s.Description, &s.Website, &s.ISIN, &s.Inception, &s.OldestPrice, &s.IsActivelyTrading, &s.MarketCap,
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
	for i := 0; i < len(toDeactivate); i += batchSize {
		end := i + batchSize
		if end > len(toDeactivate) {
			end = len(toDeactivate)
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
	}

	logf("Deactivated %d obsolete symbols\n", len(toDeactivate))
	return nil
}

// GetActiveSymbols returns all actively trading stocks (excludes indices and secondary listings)
func GetActiveSymbols() ([]types.Symbol, error) {
	db := Db()
	query := `
		SELECT 
			s.ticker, s.exchange, s.name, s.type, s.currency, s.sector, s.industry, s.country, 
			s.inception, s.oldest_price, s.market_cap,
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
		WHERE s.is_actively_trading = true
		  AND (s.type = $1 OR s.type IS NULL)
		  AND s.type != $2
		ORDER BY s.ticker
	`

	rows, err := db.conn.Query(query, types.TypeStock, types.TypeSecondary)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var symbols []types.Symbol
	for rows.Next() {
		var s types.Symbol
		if err := rows.Scan(
			&s.Ticker, &s.Exchange, &s.Name, &s.Type, &s.Currency, &s.Sector, &s.Industry, &s.Country, &s.Inception, &s.OldestPrice, &s.MarketCap,
			&s.IsFavorite, &s.UserRating,
		); err != nil {
			return nil, err
		}
		symbols = append(symbols, s)
	}

	return symbols, rows.Err()
}

// GetStaleProfiles returns symbols with outdated profiles (older than threshold or null)
// Excludes indices and secondary listings (they don't need profile updates)
func GetStaleProfiles(limit int) ([]string, error) {
	db := Db()
	query := `
		SELECT ticker FROM symbols
		WHERE (last_profile_update IS NULL OR last_profile_update < $1)
		  AND (type IS NULL OR (type != $2 AND type != $3))
		ORDER BY last_profile_update ASC NULLS FIRST
		LIMIT $4
	`

	rows, err := db.conn.Query(query, GetProfileThreshold(), types.TypeIndex, types.TypeSecondary, limit)
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
