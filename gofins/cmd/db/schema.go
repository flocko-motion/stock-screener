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
		fmt.Println("=== FINS Database Schema ===")
		fmt.Println()

		return displaySchema()
	},
}

func displaySchema() error {
	// Get schema from database
	columns, err := db.GetSchema()
	if err != nil {
		return fmt.Errorf("failed to query schema: %w", err)
	}

	// Group columns by table
	tables := make(map[string][]db.ColumnInfo)
	var tableOrder []string

	for _, col := range columns {
		if _, exists := tables[col.TableName]; !exists {
			tableOrder = append(tableOrder, col.TableName)
			tables[col.TableName] = []db.ColumnInfo{}
		}
		tables[col.TableName] = append(tables[col.TableName], col)
	}

	// Display each table
	for _, tableName := range tableOrder {
		displayTable(tableName, tables[tableName])
		fmt.Println()
	}

	return nil
}

func displayTable(tableName string, columns []db.ColumnInfo) {
	// Print table header
	width := 70
	fmt.Println(strings.Repeat("─", width))
	fmt.Printf("Table: %s\n", tableName)
	fmt.Println(strings.Repeat("─", width))
	fmt.Printf("%-25s %-20s %-15s\n", "Column", "Type", "Nullable")
	fmt.Println(strings.Repeat("─", width))

	// Print columns
	for _, col := range columns {
		defaultStr := "NULL"
		if col.ColumnDefault != nil {
			defaultStr = *col.ColumnDefault
			if col.IsNullable == "NO" {
				defaultStr = "NOT NULL"
			}
		}
		
		// Format data type
		dataType := strings.ToUpper(col.DataType)
		
		fmt.Printf("%-30s %-15s %-10s %s\n", col.ColumnName, dataType, col.IsNullable, defaultStr)
	}
	
	fmt.Println(strings.Repeat("─", width))
}
