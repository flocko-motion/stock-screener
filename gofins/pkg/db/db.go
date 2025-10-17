package db

import (
	"database/sql"
	"fmt"
	"sync"
	"time"

	"github.com/flocko-motion/gofins/pkg/files"
	_ "github.com/lib/pq"
)

func logf(format string, args ...interface{}) {
	fmt.Printf("[DB] "+format+"\n", args...)
}

type DB struct {
	conn *sql.DB
}

var (
	globalDB *DB
	dbOnce   sync.Once
)

// Db returns the global database connection, initializing it on first call
// Panics if the connection cannot be established
func Db() *DB {
	dbOnce.Do(func() {
		db, err := NewDB()
		if err != nil {
			panic(fmt.Sprintf("Failed to initialize database connection: %v", err))
		}
		globalDB = db
	})
	return globalDB
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
