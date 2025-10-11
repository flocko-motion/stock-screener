package db

import (
	"database/sql"
	"fmt"
	"strings"
	"time"

	"github.com/flocko-motion/gofins/pkg/files"
	_ "github.com/lib/pq"
)

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

// Symbol represents a stock symbol in the database
type Symbol struct {
	Ticker            string
	Exchange          *string
	LastPriceUpdate   *time.Time
	LastProfileUpdate *time.Time
	Name              *string
	Type              *string
	Currency          *string
	Sector            *string
	Industry          *string
	Country           *string
	Description       *string
	Website           *string
	ISIN              *string
	Inception         *time.Time
}

// MonthlyPrice represents monthly price data
type MonthlyPrice struct {
	Date         time.Time
	Open         float64
	High         float64
	Low          float64
	Avg          float64
	Close        float64
	SymbolTicker string
}

// SaveSymbol inserts or updates a symbol profile
func (db *DB) PutSymbol(s *Symbol) error {
	query := `
		INSERT INTO symbols (
			ticker, exchange, last_profile_update, name, type, currency,
			sector, industry, country, description, website, isin, inception
		) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
		ON CONFLICT (ticker) DO UPDATE SET
			exchange = EXCLUDED.exchange,
			last_profile_update = EXCLUDED.last_profile_update,
			name = EXCLUDED.name,
			type = EXCLUDED.type,
			currency = EXCLUDED.currency,
			sector = EXCLUDED.sector,
			industry = EXCLUDED.industry,
			country = EXCLUDED.country,
			description = EXCLUDED.description,
			website = EXCLUDED.website,
			isin = EXCLUDED.isin,
			inception = EXCLUDED.inception
	`

	_, err := db.conn.Exec(
		query,
		s.Ticker, s.Exchange, s.LastProfileUpdate, s.Name, s.Type, s.Currency,
		s.Sector, s.Industry, s.Country, s.Description, s.Website, s.ISIN, s.Inception,
	)

	return err
}

// GetSymbol retrieves a symbol by ticker
func (db *DB) GetSymbol(ticker string) (*Symbol, error) {
	query := `
		SELECT ticker, exchange, last_price_update, last_profile_update,
			   name, type, currency, sector, industry, country,
			   description, website, isin, inception
		FROM symbols
		WHERE ticker = $1
	`

	s := &Symbol{}
	err := db.conn.QueryRow(query, ticker).Scan(
		&s.Ticker, &s.Exchange, &s.LastPriceUpdate, &s.LastProfileUpdate,
		&s.Name, &s.Type, &s.Currency, &s.Sector, &s.Industry, &s.Country,
		&s.Description, &s.Website, &s.ISIN, &s.Inception,
	)

	if err == sql.ErrNoRows {
		return nil, nil
	}
	if err != nil {
		return nil, err
	}

	return s, nil
}

// SaveMonthlyPrices batch inserts monthly price data
func (db *DB) PutMonthlyPrices(prices []MonthlyPrice) error {
	if len(prices) == 0 {
		return nil
	}

	tx, err := db.conn.Begin()
	if err != nil {
		return fmt.Errorf("failed to begin transaction: %w", err)
	}
	defer tx.Rollback()

	stmt, err := tx.Prepare(`
		INSERT INTO monthly_prices (date, open, high, low, avg, close, symbol_ticker)
		VALUES ($1, $2, $3, $4, $5, $6, $7)
		ON CONFLICT (date, symbol_ticker) DO UPDATE SET
			open = EXCLUDED.open,
			high = EXCLUDED.high,
			low = EXCLUDED.low,
			avg = EXCLUDED.avg,
			close = EXCLUDED.close
	`)
	if err != nil {
		return fmt.Errorf("failed to prepare statement: %w", err)
	}
	defer stmt.Close()

	for _, p := range prices {
		_, err := stmt.Exec(p.Date, p.Open, p.High, p.Low, p.Avg, p.Close, p.SymbolTicker)
		if err != nil {
			return fmt.Errorf("failed to insert price for %s: %w", p.SymbolTicker, err)
		}
	}

	if err := tx.Commit(); err != nil {
		return fmt.Errorf("failed to commit transaction: %w", err)
	}

	return nil
}

// GetMonthlyPrices retrieves monthly prices for a symbol
func (db *DB) GetMonthlyPrices(ticker string, from, to time.Time) ([]MonthlyPrice, error) {
	query := `
		SELECT date, open, high, low, avg, close, symbol_ticker
		FROM monthly_prices
		WHERE symbol_ticker = $1 AND date >= $2 AND date <= $3
		ORDER BY date ASC
	`

	rows, err := db.conn.Query(query, ticker, from, to)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var prices []MonthlyPrice
	for rows.Next() {
		var p MonthlyPrice
		if err := rows.Scan(&p.Date, &p.Open, &p.High, &p.Low, &p.Avg, &p.Close, &p.SymbolTicker); err != nil {
			return nil, err
		}
		prices = append(prices, p)
	}

	return prices, rows.Err()
}

// GetAllTickers returns all ticker symbols in the database
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

// DeleteSymbols removes symbols not in the provided list
func (db *DB) DeleteSymbols(keepTickers []string) error {
	if len(keepTickers) == 0 {
		return nil
	}

	// Build placeholders for SQL IN clause
	placeholders := make([]string, len(keepTickers))
	args := make([]interface{}, len(keepTickers))
	for i, ticker := range keepTickers {
		placeholders[i] = fmt.Sprintf("$%d", i+1)
		args[i] = ticker
	}

	query := fmt.Sprintf("DELETE FROM symbols WHERE ticker NOT IN (%s)", strings.Join(placeholders, ","))
	_, err := db.conn.Exec(query, args...)
	return err
}

// GetStaleProfiles returns symbols with outdated profiles (older than threshold or null)
func (db *DB) GetStaleProfiles(limit int, olderThan time.Time) ([]string, error) {
	query := `
		SELECT ticker FROM symbols
		WHERE last_profile_update IS NULL OR last_profile_update < $1
		ORDER BY last_profile_update ASC NULLS FIRST
		LIMIT $2
	`

	rows, err := db.conn.Query(query, olderThan, limit)
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
