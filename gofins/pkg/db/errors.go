package db

import (
	"time"
)

// ErrorEntry represents an error logged during system operations
type ErrorEntry struct {
	ID        int       `json:"id"`
	Timestamp time.Time `json:"timestamp"`
	Source    string    `json:"source"`    // e.g., "updater.symbols", "api.handler"
	ErrorType string    `json:"errorType"` // e.g., "network", "database", "validation"
	Message   string    `json:"message"`
	Details   *string   `json:"details,omitempty"`
}

// LogError logs an error to the database
func LogError(source, errorType, message string, details *string) error {
	db := Db()
	query := `
		INSERT INTO errors (source, error_type, message, details)
		VALUES ($1, $2, $3, $4)
	`
	_, err := db.conn.Exec(query, source, errorType, message, details)
	return err
}

// GetRecentErrors retrieves the most recent errors
func GetRecentErrors(limit int) ([]ErrorEntry, error) {
	db := Db()
	query := `
		SELECT id, timestamp, source, error_type, message, details
		FROM errors
		ORDER BY timestamp DESC
		LIMIT $1
	`

	rows, err := db.conn.Query(query, limit)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var errors []ErrorEntry
	for rows.Next() {
		var e ErrorEntry
		if err := rows.Scan(&e.ID, &e.Timestamp, &e.Source, &e.ErrorType, &e.Message, &e.Details); err != nil {
			return nil, err
		}
		errors = append(errors, e)
	}

	return errors, rows.Err()
}

// GetErrorsBySource retrieves errors for a specific source
func GetErrorsBySource(source string, limit int) ([]ErrorEntry, error) {
	db := Db()
	query := `
		SELECT id, timestamp, source, error_type, message, details
		FROM errors
		WHERE source = $1
		ORDER BY timestamp DESC
		LIMIT $2
	`

	rows, err := db.conn.Query(query, source, limit)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var errors []ErrorEntry
	for rows.Next() {
		var e ErrorEntry
		if err := rows.Scan(&e.ID, &e.Timestamp, &e.Source, &e.ErrorType, &e.Message, &e.Details); err != nil {
			return nil, err
		}
		errors = append(errors, e)
	}

	return errors, rows.Err()
}

// CountErrorsSince counts errors since a given timestamp
func CountErrorsSince(since time.Time) (int, error) {
	db := Db()
	query := `SELECT COUNT(*) FROM errors WHERE timestamp >= $1`

	var count int
	err := db.conn.QueryRow(query, since).Scan(&count)
	return count, err
}

// ClearOldErrors deletes errors older than the specified duration
func ClearOldErrors(olderThan time.Duration) (int, error) {
	db := Db()
	cutoff := time.Now().Add(-olderThan)
	query := `DELETE FROM errors WHERE timestamp < $1`

	result, err := db.conn.Exec(query, cutoff)
	if err != nil {
		return 0, err
	}

	rowsAffected, err := result.RowsAffected()
	return int(rowsAffected), err
}
