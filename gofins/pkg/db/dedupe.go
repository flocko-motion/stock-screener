package db

import (
	"github.com/lib/pq"
	"github.com/flocko-motion/gofins/pkg/types"
)

// GetSymbolsWithCIK returns all stock symbols that have a CIK value
func GetSymbolsWithCIK() ([]types.Symbol, error) {
	db := Db()
	query := `
		SELECT ticker, exchange, cik, primary_listing
		FROM symbols
		WHERE cik IS NOT NULL AND cik != ''
		  AND (type = $1 OR type IS NULL)
		ORDER BY cik, exchange
	`

	rows, err := db.conn.Query(query, types.TypeStock)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var symbols []types.Symbol
	for rows.Next() {
		s := types.Symbol{}
		err := rows.Scan(&s.Ticker, &s.Exchange, &s.CIK, &s.PrimaryListing)
		if err != nil {
			return nil, err
		}
		symbols = append(symbols, s)
	}

	return symbols, rows.Err()
}

// GetStockSymbolsWithoutCIK returns all stock symbols that don't have a CIK value
func GetStockSymbolsWithoutCIK() ([]types.Symbol, error) {
	db := Db()
	query := `
		SELECT ticker, name, oldest_price, primary_listing
		FROM symbols
		WHERE (cik IS NULL OR cik = '')
		  AND (type = $1 OR type IS NULL)
		  AND name IS NOT NULL
		ORDER BY name, oldest_price ASC NULLS LAST
	`

	rows, err := db.conn.Query(query, types.TypeStock)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var symbols []types.Symbol
	for rows.Next() {
		s := types.Symbol{}
		err := rows.Scan(&s.Ticker, &s.Name, &s.OldestPrice, &s.PrimaryListing)
		if err != nil {
			return nil, err
		}
		symbols = append(symbols, s)
	}

	return symbols, rows.Err()
}

// GetStockSymbolsForNameDedupe returns all stock symbols with names for name-based deduplication
func GetStockSymbolsForNameDedupe() ([]types.Symbol, error) {
	db := Db()
	query := `
		SELECT ticker, name, oldest_price, primary_listing
		FROM symbols
		WHERE (type = $1 OR type IS NULL)
		  AND name IS NOT NULL
		ORDER BY name, oldest_price ASC NULLS LAST
	`

	rows, err := db.conn.Query(query, types.TypeStock)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var symbols []types.Symbol
	for rows.Next() {
		s := types.Symbol{}
		err := rows.Scan(&s.Ticker, &s.Name, &s.OldestPrice, &s.PrimaryListing)
		if err != nil {
			return nil, err
		}
		symbols = append(symbols, s)
	}

	return symbols, rows.Err()
}

// ResetPrimaryListings sets all primary_listing fields to NULL
func ResetPrimaryListings() (int, error) {
	db := Db()
	result, err := db.conn.Exec(`UPDATE symbols SET primary_listing = NULL`)
	if err != nil {
		return 0, err
	}
	
	count, err := result.RowsAffected()
	if err != nil {
		return 0, err
	}
	
	return int(count), nil
}

// UpdatePrimaryListingGroup updates primary_listing for a group of symbols
// primaryTicker gets primary_listing = '', all others get primary_listing = primaryTicker
func UpdatePrimaryListingGroup(primaryTicker string, secondaryTickers []string) error {
	db := Db()
	tx, err := db.conn.Begin()
	if err != nil {
		return err
	}
	defer tx.Rollback()

	// Set primary to empty string
	if _, err := tx.Exec("UPDATE symbols SET primary_listing = '' WHERE ticker = $1", primaryTicker); err != nil {
		return err
	}

	// Set all secondaries to point to primary
	if len(secondaryTickers) > 0 {
		query := "UPDATE symbols SET primary_listing = $1 WHERE ticker = ANY($2)"
		if _, err := tx.Exec(query, primaryTicker, pq.Array(secondaryTickers)); err != nil {
			return err
		}
	}

	return tx.Commit()
}
