package db

import (
	"database/sql"
	"fmt"
	"time"

	"github.com/flocko-motion/gofins/pkg/types"
	"github.com/lib/pq"
)

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
func (db *DB) GetPrices(ticker string, from, to time.Time, interval types.PriceInterval) ([]types.PriceData, error) {
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
	return db.GetPrices(ticker, from, to, types.IntervalMonthly)
}

// GetWeeklyPrices retrieves weekly prices for a symbol
func (db *DB) GetWeeklyPrices(ticker string, from, to time.Time) ([]types.PriceData, error) {
	return db.GetPrices(ticker, from, to, types.IntervalWeekly)
}

// GetPricesBatch retrieves price data for multiple symbols in a single query
// Returns a map of ticker -> []PriceData
func (db *DB) GetPricesBatch(tickers []string, from, to time.Time, interval types.PriceInterval) (map[string][]types.PriceData, error) {
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
	// logf("[DB] Parameters: PriceUpdateTypes=%v, mcapMin=%v, inceptionMax=%v, status=%s\n", PriceUpdateTypes, mcapMin, inceptionMax, types.StatusOK)

	rows, err := db.conn.Query(query, pq.Array(types.PriceUpdateTypes), mcapMin, inceptionMax, types.StatusOK)
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

// GetSymbolsWithStalePrices returns symbols with outdated price data
// Returns Symbol structs with only ticker and currency populated
func (db *DB) GetSymbolsWithStalePrices(limit int) ([]types.Symbol, error) {
	query := `
		SELECT ticker, currency FROM symbols
		WHERE (last_price_update IS NULL OR last_price_update < $1)
		  AND is_actively_trading = true
		  AND type = ANY($2)
		ORDER BY last_price_update ASC NULLS FIRST
		LIMIT $3
	`

	rows, err := db.conn.Query(query, GetPriceThreshold(), pq.Array(types.PriceUpdateTypes), limit)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var symbols []types.Symbol
	for rows.Next() {
		var s types.Symbol
		if err := rows.Scan(&s.Ticker, &s.Currency); err != nil {
			return nil, err
		}
		symbols = append(symbols, s)
	}

	return symbols, rows.Err()
}

// GetPriceThreshold returns the threshold for stale prices (1st of current month at noon UTC)
func GetPriceThreshold() time.Time {
	now := time.Now().UTC()
	return time.Date(now.Year(), now.Month(), 1, 12, 0, 0, 0, time.UTC)
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
	err := db.conn.QueryRow(query, GetPriceThreshold(), pq.Array(types.PriceUpdateTypes)).Scan(&count)
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
