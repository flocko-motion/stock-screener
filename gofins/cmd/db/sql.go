package db

import (
	"bufio"
	"fmt"
	"os"
	"strings"

	"github.com/flocko-motion/gofins/pkg/db"
	"github.com/spf13/cobra"
)

var (
	sqlQuery string
)

var sqlCmd = &cobra.Command{
	Use:   "sql",
	Short: "Execute raw SQL queries for database administration",
	Long: `Execute raw SQL queries against the database.
	
Examples:
  # Execute a single query via flag
  gofins db sql -q "SELECT COUNT(*) FROM symbols"
  
  # Interactive mode (enter queries line by line, type 'exit' to quit)
  gofins db sql`,
	RunE: func(cmd *cobra.Command, args []string) error {
		database := db.Db()

		// If query provided via flag, execute it and exit
		if sqlQuery != "" {
			return executeQuery(database, sqlQuery)
		}

		// Interactive mode
		fmt.Println("=== Interactive SQL Mode ===")
		fmt.Println("Enter SQL queries (type 'exit' or 'quit' to exit)")
		fmt.Println("Note: Each line is executed as a separate query")
		fmt.Println()

		scanner := bufio.NewScanner(os.Stdin)
		for {
			fmt.Print("sql> ")
			if !scanner.Scan() {
				break
			}

			query := strings.TrimSpace(scanner.Text())
			if query == "" {
				continue
			}

			// Check for exit commands
			if strings.ToLower(query) == "exit" || strings.ToLower(query) == "quit" {
				fmt.Println("Goodbye!")
				break
			}

			if err := executeQuery(database, query); err != nil {
				fmt.Printf("Error: %v\n", err)
			}
			fmt.Println()
		}

		if err := scanner.Err(); err != nil {
			return fmt.Errorf("scanner error: %w", err)
		}

		return nil
	},
}

func executeQuery(database *db.DB, query string) error {
	// Determine if this is a SELECT query or a modification query
	queryLower := strings.ToLower(strings.TrimSpace(query))
	isSelect := strings.HasPrefix(queryLower, "select") ||
		strings.HasPrefix(queryLower, "show") ||
		strings.HasPrefix(queryLower, "describe") ||
		strings.HasPrefix(queryLower, "explain")

	if isSelect {
		return executeSelectQuery(database, query)
	}
	return executeModifyQuery(database, query)
}

func executeSelectQuery(database *db.DB, query string) error {
	rows, err := db.QueryRaw(query)
	if err != nil {
		return fmt.Errorf("query failed: %w", err)
	}
	defer rows.Close()

	// Get column names
	columns, err := rows.Columns()
	if err != nil {
		return fmt.Errorf("failed to get columns: %w", err)
	}

	// Print header
	for i, col := range columns {
		if i > 0 {
			fmt.Print(" | ")
		}
		fmt.Printf("%-20s", col)
	}
	fmt.Println()
	fmt.Println(strings.Repeat("-", len(columns)*23))

	// Print rows
	values := make([]interface{}, len(columns))
	valuePtrs := make([]interface{}, len(columns))
	for i := range values {
		valuePtrs[i] = &values[i]
	}

	rowCount := 0
	for rows.Next() {
		if err := rows.Scan(valuePtrs...); err != nil {
			return fmt.Errorf("failed to scan row: %w", err)
		}

		for i, val := range values {
			if i > 0 {
				fmt.Print(" | ")
			}
			// Format value
			var str string
			if val == nil {
				str = "NULL"
			} else {
				// Handle byte arrays (convert to string)
				switch v := val.(type) {
				case []byte:
					str = string(v)
				default:
					str = fmt.Sprintf("%v", v)
				}
			}
			// Truncate if too long
			if len(str) > 20 {
				str = str[:17] + "..."
			}
			fmt.Printf("%-20s", str)
		}
		fmt.Println()
		rowCount++
	}

	if err := rows.Err(); err != nil {
		return fmt.Errorf("rows error: %w", err)
	}

	fmt.Printf("\n(%d rows)\n", rowCount)
	return nil
}

func executeModifyQuery(database *db.DB, query string) error {
	result, err := db.ExecRaw(query)
	if err != nil {
		return fmt.Errorf("query failed: %w", err)
	}

	rowsAffected, err := result.RowsAffected()
	if err != nil {
		fmt.Println("Query executed successfully")
	} else {
		fmt.Printf("Query executed successfully (%d rows affected)\n", rowsAffected)
	}

	return nil
}

func init() {
	sqlCmd.Flags().StringVarP(&sqlQuery, "query", "q", "", "SQL query to execute (if not provided, enters interactive mode)")
}
