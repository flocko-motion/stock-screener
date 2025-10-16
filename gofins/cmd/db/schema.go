package db

import (
	"fmt"
	"strings"

	"github.com/flocko-motion/gofins/pkg/db"
	"github.com/spf13/cobra"
)

var schemaCmd = &cobra.Command{
	Use:   "schema",
	Short: "Display database schema and table structures",
	RunE: func(cmd *cobra.Command, args []string) error {
		database, err := db.NewDB()
		if err != nil {
			return fmt.Errorf("failed to connect to database: %w", err)
		}
		defer database.Close()

		fmt.Println("=== FINS Database Schema ===")
		fmt.Println()

		return displaySchema(database)
	},
}

type columnInfo struct {
	tableName    string
	columnName   string
	dataType     string
	isNullable   string
	columnDefault *string
}

func displaySchema(database *db.DB) error {
	// Query schema from information_schema
	query := `
		SELECT 
			c.table_name,
			c.column_name,
			c.data_type,
			c.is_nullable,
			c.column_default
		FROM information_schema.columns c
		WHERE c.table_schema = 'public'
		ORDER BY c.table_name, c.ordinal_position
	`

	rows, err := database.Query(query)
	if err != nil {
		return fmt.Errorf("failed to query schema: %w", err)
	}
	defer rows.Close()

	// Group columns by table
	tables := make(map[string][]columnInfo)
	var tableOrder []string

	for rows.Next() {
		var col columnInfo
		if err := rows.Scan(&col.tableName, &col.columnName, &col.dataType, &col.isNullable, &col.columnDefault); err != nil {
			return fmt.Errorf("failed to scan column: %w", err)
		}

		if _, exists := tables[col.tableName]; !exists {
			tableOrder = append(tableOrder, col.tableName)
			tables[col.tableName] = []columnInfo{}
		}
		tables[col.tableName] = append(tables[col.tableName], col)
	}

	if err := rows.Err(); err != nil {
		return fmt.Errorf("error iterating rows: %w", err)
	}

	// Display each table
	for _, tableName := range tableOrder {
		displayTable(tableName, tables[tableName])
		fmt.Println()
	}

	return nil
}

func displayTable(tableName string, columns []columnInfo) {
	// Print table header
	width := 70
	fmt.Println(strings.Repeat("─", width))
	fmt.Printf("Table: %s\n", tableName)
	fmt.Println(strings.Repeat("─", width))
	fmt.Printf("%-25s %-20s %-15s\n", "Column", "Type", "Nullable")
	fmt.Println(strings.Repeat("─", width))

	// Print columns
	for _, col := range columns {
		nullable := "NULL"
		if col.isNullable == "NO" {
			nullable = "NOT NULL"
		}
		
		// Format data type
		dataType := strings.ToUpper(col.dataType)
		
		fmt.Printf("%-25s %-20s %-15s\n", col.columnName, dataType, nullable)
	}
	
	fmt.Println(strings.Repeat("─", width))
}
