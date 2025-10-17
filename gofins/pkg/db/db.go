package db

import (
	"database/sql"
	"fmt"
	"strings"
	"time"

	"github.com/flocko-motion/gofins/pkg/files"
	"github.com/flocko-motion/gofins/pkg/types"
	"github.com/lib/pq"
)

func logf(format string, args ...interface{}) {
	fmt.Printf("[DB] "+format+"\n", args...)
}

type DB struct {
	conn *sql.DB
}

// NewDB creates a new database connection with hardcoded config
func NewDB() (*DB, error) {
	// Read password from config
	password, err := files.GetEnvValue("~/.fins/config/db.env", "POSTGRES_PASSWORD")
	if err != nil {
		return nil, fmt.Errorf("failed to read DB password: %w", err)
	}

	connStr := fmt.Sprintf("host=localhost port=5432 user=fins password=%s dbname=fins sslmode=disable", password)

	conn, err := sql.Open("postgres", connStr)
	if err != nil {
		return nil, fmt.Errorf("failed to open database: %w", err)
	}

	// Test connection
	if err := conn.Ping(); err != nil {
		return nil, fmt.Errorf("failed to ping database: %w", err)
	}

	// Configure connection pool
	conn.SetMaxOpenConns(25)
	conn.SetMaxIdleConns(5)
	conn.SetConnMaxLifetime(5 * time.Minute)

	return &DB{conn: conn}, nil
}

// Close closes the database connection
func (db *DB) Close() error {
	return db.conn.Close()
}

// Exec executes a query without returning rows
func (db *DB) Exec(query string, args ...interface{}) (sql.Result, error) {
	return db.conn.Exec(query, args...)
}

// Query executes a query that returns rows
func (db *DB) Query(query string, args ...interface{}) (*sql.Rows, error) {
	return db.conn.Query(query, args...)
}

// Symbol represents a stock symbol in the database
type Symbol struct {
	Ticker            string     `json:"ticker"`
	Exchange          *string    `json:"exchange,omitempty"`
	LastPriceUpdate   *time.Time `json:"lastPriceUpdate,omitempty"`
	LastProfileUpdate *time.Time `json:"lastProfileUpdate,omitempty"`
	LastPriceStatus   *string    `json:"lastPriceStatus,omitempty"`
	LastProfileStatus *string    `json:"lastProfileStatus,omitempty"`
	Name              *string    `json:"name,omitempty"`
	Type              *string    `json:"type,omitempty"`
	Currency          *string    `json:"currency,omitempty"`
	Sector            *string    `json:"sector,omitempty"`
	Industry          *string    `json:"industry,omitempty"`
	Country           *string    `json:"country,omitempty"`
	Description       *string    `json:"description,omitempty"`
	Website           *string    `json:"website,omitempty"`
	ISIN              *string    `json:"isin,omitempty"`
	Inception         *time.Time `json:"inception,omitempty"`
	OldestPrice       *time.Time `json:"oldestPrice,omitempty"`
	IsActivelyTrading *bool      `json:"isActivelyTrading,omitempty"`
	MarketCap         *int64     `json:"marketCap,omitempty"`
	IsFavorite        bool       `json:"isFavorite"`
	UserRating        *int       `json:"userRating,omitempty"`
}


// SaveSymbol inserts or updates a symbol profile
// Only updates non-nil fields to avoid overwriting data from other updaters
func (db *DB) PutSymbol(s *Symbol) error {
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
func (db *DB) GetSymbol(ticker string) (*Symbol, error) {
	query := `
		SELECT ticker, exchange, last_price_update, last_profile_update,
			   last_price_status, last_profile_status,
			   name, type, currency, sector, industry, country,
			   description, website, isin, inception, oldest_price, is_actively_trading, market_cap
		FROM symbols
		WHERE ticker = $1
	`

	s := &Symbol{}
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

// GetOldestPriceDate returns the oldest price date for a ticker from monthly_prices
func (db *DB) GetOldestPriceDate(ticker string) (*time.Time, error) {
	query := `
		SELECT MIN(date) 
		FROM monthly_prices 
		WHERE symbol_ticker = $1
	`

	var oldestDate *time.Time
	err := db.conn.QueryRow(query, ticker).Scan(&oldestDate)
	
	if err == sql.ErrNoRows || oldestDate == nil {
		return nil, nil
	}
	if err != nil {
		return nil, err
	}

	return oldestDate, nil
}

// PutMonthlyPrices batch inserts monthly price data
func (db *DB) PutMonthlyPrices(prices []types.PriceData) error {
	if len(prices) == 0 {
		return nil
	}

	tx, err := db.conn.Begin()
	if err != nil {
		return fmt.Errorf("failed to begin transaction: %w", err)
	}
	defer tx.Rollback()

	stmt, err := tx.Prepare(`
		INSERT INTO monthly_prices (date, open, high, low, avg, close, yoy, symbol_ticker)
		VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
		ON CONFLICT (date, symbol_ticker) DO UPDATE SET
			open = EXCLUDED.open,
			high = EXCLUDED.high,
			low = EXCLUDED.low,
			avg = EXCLUDED.avg,
			close = EXCLUDED.close,
			yoy = EXCLUDED.yoy
	`)
	if err != nil {
		return fmt.Errorf("failed to prepare statement: %w", err)
	}
	defer stmt.Close()

	for _, p := range prices {
		_, err := stmt.Exec(p.Date, p.Open, p.High, p.Low, p.Avg, p.Close, p.YoY, p.SymbolTicker)
		if err != nil {
			return fmt.Errorf("failed to insert price for %s: %w", p.SymbolTicker, err)
		}
	}

	if err := tx.Commit(); err != nil {
		return fmt.Errorf("failed to commit transaction: %w", err)
	}

	return nil
}

// PutWeeklyPrices batch inserts weekly price data
func (db *DB) PutWeeklyPrices(prices []types.PriceData) error {
	if len(prices) == 0 {
		return nil
	}

	tx, err := db.conn.Begin()
	if err != nil {
		return fmt.Errorf("failed to begin transaction: %w", err)
	}
	defer tx.Rollback()

	stmt, err := tx.Prepare(`
		INSERT INTO weekly_prices (date, open, high, low, avg, close, yoy, symbol_ticker)
		VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
		ON CONFLICT (date, symbol_ticker) DO UPDATE SET
			open = EXCLUDED.open,
			high = EXCLUDED.high,
			low = EXCLUDED.low,
			avg = EXCLUDED.avg,
			close = EXCLUDED.close,
			yoy = EXCLUDED.yoy
	`)
	if err != nil {
		return fmt.Errorf("failed to prepare statement: %w", err)
	}
	defer stmt.Close()

	for _, p := range prices {
		_, err := stmt.Exec(p.Date, p.Open, p.High, p.Low, p.Avg, p.Close, p.YoY, p.SymbolTicker)
		if err != nil {
			return fmt.Errorf("failed to insert price for %s: %w", p.SymbolTicker, err)
		}
	}

	if err := tx.Commit(); err != nil {
		return fmt.Errorf("failed to commit transaction: %w", err)
	}

	return nil
}

// GetPrices retrieves price data for a symbol at the specified interval
func (db *DB) GetPrices(ticker string, from, to time.Time, interval PriceInterval) ([]types.PriceData, error) {
	tableName := string(interval) + "_prices"

	query := fmt.Sprintf(`
		SELECT date, open, high, low, avg, close, yoy, symbol_ticker
		FROM %s
		WHERE symbol_ticker = $1 AND date >= $2 AND date <= $3
		ORDER BY date ASC
	`, tableName)

	rows, err := db.conn.Query(query, ticker, from, to)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var prices []types.PriceData
	for rows.Next() {
		var p types.PriceData
		if err := rows.Scan(&p.Date, &p.Open, &p.High, &p.Low, &p.Avg, &p.Close, &p.YoY, &p.SymbolTicker); err != nil {
			return nil, err
		}
		prices = append(prices, p)
	}

	return prices, rows.Err()
}

// GetMonthlyPrices retrieves monthly prices for a symbol
func (db *DB) GetMonthlyPrices(ticker string, from, to time.Time) ([]types.PriceData, error) {
	return db.GetPrices(ticker, from, to, IntervalMonthly)
}

// GetWeeklyPrices retrieves weekly prices for a symbol
func (db *DB) GetWeeklyPrices(ticker string, from, to time.Time) ([]types.PriceData, error) {
	return db.GetPrices(ticker, from, to, IntervalWeekly)
}

// GetPricesBatch retrieves price data for multiple symbols in a single query
// Returns a map of ticker -> []PriceData
func (db *DB) GetPricesBatch(tickers []string, from, to time.Time, interval PriceInterval) (map[string][]types.PriceData, error) {
	if len(tickers) == 0 {
		return make(map[string][]types.PriceData), nil
	}

	tableName := string(interval) + "_prices"

	query := fmt.Sprintf(`
		SELECT date, open, high, low, avg, close, yoy, symbol_ticker
		FROM %s
		WHERE symbol_ticker = ANY($1) AND date >= $2 AND date <= $3
		ORDER BY symbol_ticker, date ASC
	`, tableName)

	rows, err := db.conn.Query(query, pq.Array(tickers), from, to)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	result := make(map[string][]types.PriceData)
	for rows.Next() {
		var p types.PriceData
		if err := rows.Scan(&p.Date, &p.Open, &p.High, &p.Low, &p.Avg, &p.Close, &p.YoY, &p.SymbolTicker); err != nil {
			return nil, err
		}
		result[p.SymbolTicker] = append(result[p.SymbolTicker], p)
	}

	return result, rows.Err()
}

// GetFilteredTickers returns tickers matching filters (for analysis packages)
func (db *DB) GetFilteredTickers(mcapMin *int64, inceptionMax *time.Time) ([]string, error) {
	// Be lenient on price table presence: allow any interval that has data.
	// Still prioritize/reflect requested interval in logs.
	query := `
        SELECT DISTINCT s.ticker FROM symbols s
        WHERE s.is_actively_trading = true
          AND s.type = ANY($1)
          AND ($2::BIGINT IS NULL OR s.market_cap >= $2)
          AND ($3::TIMESTAMP IS NULL OR s.inception <= $3)
          AND s.last_price_status = $4
          AND s.last_price_update IS NOT NULL
  		  AND s.exchange NOT IN ('OTC','PINK', 'GREY', 'OTCQB', 'OTCQX')
        ORDER BY s.ticker
    `

	// logf("[DB] GetFilteredTickers query (interval=%s): %s\n", string(interval), query)
	// logf("[DB] Parameters: PriceUpdateTypes=%v, mcapMin=%v, inceptionMax=%v, status=%s\n", PriceUpdateTypes, mcapMin, inceptionMax, StatusOK)

	rows, err := db.conn.Query(query, pq.Array(PriceUpdateTypes), mcapMin, inceptionMax, StatusOK)
	if err != nil {
		logf("[DB] Query error: %v\n", err)
		return nil, err
	}
	defer rows.Close()
	logf("[DB] Query executed successfully, reading results...\n")

	var tickers []string
	for rows.Next() {
		var ticker string
		if err := rows.Scan(&ticker); err != nil {
			logf("[DB] Error scanning ticker: %v\n", err)
			return nil, err
		}
		tickers = append(tickers, ticker)
	}

	if err := rows.Err(); err != nil {
		logf("[DB] Error iterating rows: %v\n", err)
		return nil, err
	}

	logf("[DB] GetFilteredTickers returned %d tickers\n", len(tickers))
	return tickers, nil
}

// GetTickersWithPrices returns tickers that have price data (limited to specified count)
func (db *DB) GetTickersWithPrices(limit int) ([]string, error) {
	query := `
		SELECT DISTINCT symbol_ticker FROM monthly_prices 
		ORDER BY symbol_ticker 
		LIMIT $1
	`

	rows, err := db.conn.Query(query, limit)
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

func (db *DB) GetAllTickers() ([]string, error) {
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
func (db *DB) DeactivateSymbolsNotInList(keepTickers []string) error {
	if len(keepTickers) == 0 {
		return nil
	}

	// Get all current tickers from database
	allTickers, err := db.GetAllTickers()
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
func (db *DB) GetActiveSymbols() ([]Symbol, error) {
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

	rows, err := db.conn.Query(query, TypeStock, TypeSecondary)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var symbols []Symbol
	for rows.Next() {
		var s Symbol
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
func (db *DB) GetStaleProfiles(limit int) ([]string, error) {
	query := `
		SELECT ticker FROM symbols
		WHERE (last_profile_update IS NULL OR last_profile_update < $1)
		  AND (type IS NULL OR (type != $2 AND type != $3))
		ORDER BY last_profile_update ASC NULLS FIRST
		LIMIT $4
	`

	rows, err := db.conn.Query(query, GetProfileThreshold(), TypeIndex, TypeSecondary, limit)
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

// Symbol types
const (
	TypeStock     = "stock"
	TypeETF       = "etf"
	TypeFund      = "fund"
	TypeADR       = "adr"
	TypeIndex     = "index"
	TypeSecondary = "secondary" // Secondary exchange listing (duplicate of primary)
)

// PriceUpdateTypes defines which symbol types should receive price updates
var PriceUpdateTypes = []string{TypeStock, TypeADR, TypeIndex}

// PriceInterval represents the time interval for price data
type PriceInterval string

const (
	IntervalMonthly PriceInterval = "monthly"
	IntervalWeekly  PriceInterval = "weekly"
)

// Price status constants (mirror updater statuses)
const (
	StatusOK       = "ok"
	StatusNotFound = "not_found"
	StatusFailed   = "failed"
)

// GetProfileThreshold returns the threshold for stale profiles (30 days ago)
func GetProfileThreshold() time.Time {
	return time.Now().UTC().AddDate(0, 0, -30)
}

// GetPriceThreshold returns the threshold for stale prices (1st of current month at noon UTC)
func GetPriceThreshold() time.Time {
	now := time.Now().UTC()
	return time.Date(now.Year(), now.Month(), 1, 12, 0, 0, 0, time.UTC)
}

// CountSymbols returns the total number of symbols
func (db *DB) CountSymbols() (int, error) {
	query := `SELECT COUNT(*) FROM symbols`

	var count int
	err := db.conn.QueryRow(query).Scan(&count)
	return count, err
}

// CountActivelyTrading returns the count of actively trading symbols
func (db *DB) CountActivelyTrading() (int, error) {
	query := `SELECT COUNT(*) FROM symbols WHERE is_actively_trading = true`

	var count int
	err := db.conn.QueryRow(query).Scan(&count)
	return count, err
}

// CountStaleProfiles returns the count of stale profiles
// Excludes indices as they don't have profile endpoints
func (db *DB) CountStaleProfiles() (int, error) {
	query := `
		SELECT COUNT(*) FROM symbols
		WHERE (last_profile_update IS NULL OR last_profile_update < $1)
		  AND (type IS NULL OR type != $2)
	`

	var count int
	err := db.conn.QueryRow(query, GetProfileThreshold(), TypeIndex).Scan(&count)
	return count, err
}

// GetOldestProfileUpdate returns the oldest profile update timestamp
func (db *DB) GetOldestProfileUpdate() (*time.Time, error) {
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

// GetStalePrices returns symbols with outdated price data
func (db *DB) GetStalePrices(limit int) ([]string, error) {
	query := `
		SELECT ticker FROM symbols
		WHERE (last_price_update IS NULL OR last_price_update < $1)
		  AND is_actively_trading = true
		  AND type = ANY($2)
		ORDER BY last_price_update ASC NULLS FIRST
		LIMIT $3
	`

	rows, err := db.conn.Query(query, GetPriceThreshold(), pq.Array(PriceUpdateTypes), limit)
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

// CountStalePrices returns the count of stale prices
func (db *DB) CountStalePrices() (int, error) {
	query := `
		SELECT COUNT(*) FROM symbols
		WHERE (last_price_update IS NULL OR last_price_update < $1)
		  AND is_actively_trading = true
		  AND type = ANY($2)
	`

	var count int
	err := db.conn.QueryRow(query, GetPriceThreshold(), pq.Array(PriceUpdateTypes)).Scan(&count)
	return count, err
}

// GetOldestPriceUpdate returns the oldest price update timestamp (only for actively trading symbols)
func (db *DB) GetOldestPriceUpdate() (*time.Time, error) {
	query := `
		SELECT MIN(last_price_update) FROM symbols
		WHERE last_price_update IS NOT NULL
		  AND is_actively_trading = true
	`

	var oldest *time.Time
	err := db.conn.QueryRow(query).Scan(&oldest)
	if err == sql.ErrNoRows {
		return nil, nil
	}
	return oldest, err
}
