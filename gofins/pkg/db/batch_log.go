package db

import (
	"fmt"
	"time"
)

type BatchUpdateLog struct {
	ID               int
	UpdaterName      string
	StartedAt        time.Time
	CompletedAt      *time.Time
	Status           string
	SymbolsProcessed int
	SymbolsUpdated   int
	ErrorMessage     *string
}

// StartBatchUpdate creates a new batch update log entry
func StartBatchUpdate(updaterName string) (int, error) {
	db := Db()

	var id int
	err := db.conn.QueryRow(`
		INSERT INTO batch_update_log (updater_name, started_at, status)
		VALUES ($1, $2, 'running')
		RETURNING id
	`, updaterName, time.Now()).Scan(&id)

	if err != nil {
		return 0, fmt.Errorf("failed to start batch update log: %w", err)
	}

	return id, nil
}

// CompleteBatchUpdate marks a batch update as completed
func CompleteBatchUpdate(id int, symbolsProcessed, symbolsUpdated int) error {
	db := Db()

	_, err := db.conn.Exec(`
		UPDATE batch_update_log
		SET completed_at = $1,
		    status = 'completed',
		    symbols_processed = $2,
		    symbols_updated = $3
		WHERE id = $4
	`, time.Now(), symbolsProcessed, symbolsUpdated, id)

	if err != nil {
		return fmt.Errorf("failed to complete batch update log: %w", err)
	}

	return nil
}

// FailBatchUpdate marks a batch update as failed
func FailBatchUpdate(id int, errorMessage string) error {
	db := Db()

	_, err := db.conn.Exec(`
		UPDATE batch_update_log
		SET completed_at = $1,
		    status = 'failed',
		    error_message = $2
		WHERE id = $3
	`, time.Now(), errorMessage, id)

	if err != nil {
		return fmt.Errorf("failed to mark batch update as failed: %w", err)
	}

	return nil
}

// GetLastBatchUpdate returns the last batch update for a given updater
func GetLastBatchUpdate(updaterName string) (*BatchUpdateLog, error) {
	db := Db()

	var log BatchUpdateLog
	err := db.conn.QueryRow(`
		SELECT id, updater_name, started_at, completed_at, status, 
		       symbols_processed, symbols_updated, error_message
		FROM batch_update_log
		WHERE updater_name = $1
		  AND status = 'completed'
		ORDER BY started_at DESC
		LIMIT 1
	`, updaterName).Scan(
		&log.ID, &log.UpdaterName, &log.StartedAt, &log.CompletedAt,
		&log.Status, &log.SymbolsProcessed, &log.SymbolsUpdated, &log.ErrorMessage,
	)

	if err != nil {
		return nil, err
	}

	return &log, nil
}

// DeleteBatchUpdate deletes all batch update logs for a given updater
func DeleteBatchUpdate(updaterName string) error {
	db := Db()

	_, err := db.conn.Exec(`
		DELETE FROM batch_update_log
		WHERE updater_name = $1
	`, updaterName)

	if err != nil {
		return fmt.Errorf("failed to delete batch update logs: %w", err)
	}

	return nil
}
