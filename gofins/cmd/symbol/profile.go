package symbol

import (
	"fmt"

	"github.com/flocko-motion/gofins/pkg/db"
	"github.com/flocko-motion/gofins/pkg/f"
	"github.com/spf13/cobra"
)

var profileCmd = &cobra.Command{
	Use:   "profile <ticker>",
	Short: "Show profile information for a symbol",
	Long:  "Display detailed profile information for a specific symbol ticker",
	Args:  cobra.ExactArgs(1),
	RunE: func(cmd *cobra.Command, args []string) error {
		ticker := args[0]

		symbol, err := db.GetSymbol(ticker)
		if err != nil {
			return fmt.Errorf("failed to get symbol: %w", err)
		}

		if symbol == nil {
			fmt.Printf("Symbol %s not found in database\n", ticker)
			return nil
		}

		// Display symbol information
		fmt.Printf("\n=== Symbol Profile: %s ===\n\n", ticker)

		fmt.Printf("%-20s %s\n", "Ticker:", symbol.Ticker)
		fmt.Printf("%-20s %s\n", "Name:", f.MaybeToString(symbol.Name, "n/a"))
		fmt.Printf("%-20s %s\n", "Exchange:", f.MaybeToString(symbol.Exchange, "n/a"))
		fmt.Printf("%-20s %s\n", "Type:", f.MaybeToString(symbol.Type, "n/a"))
		fmt.Printf("%-20s %s\n", "Currency:", f.MaybeToString(symbol.Currency, "n/a"))
		fmt.Printf("%-20s %s\n", "Country:", f.MaybeToString(symbol.Country, "n/a"))
		fmt.Printf("%-20s %s\n", "Sector:", f.MaybeToString(symbol.Sector, "n/a"))
		fmt.Printf("%-20s %s\n", "Industry:", f.MaybeToString(symbol.Industry, "n/a"))
		fmt.Printf("%-20s %s\n", "Market Cap:", f.MaybeInt64ToString(symbol.MarketCap, "$%d", "n/a"))
		fmt.Printf("%-20s %s\n", "Inception:", f.MaybeDateToString(symbol.Inception, "2006-01-02", "n/a"))
		fmt.Printf("%-20s %s\n", "Oldest Price:", f.MaybeDateToString(symbol.OldestPrice, "2006-01-02", "n/a"))
		fmt.Printf("%-20s %s\n", "Current Price:", f.MaybeFloat64ToString(symbol.CurrentPriceUsd, "$%.2f", "n/a"))
		fmt.Printf("%-20s %s\n", "ATH 12M:", f.MaybeFloat64ToString(symbol.Ath12M, "%.2f", "n/a"))
		fmt.Printf("%-20s %s\n", "Actively Trading:", f.MaybeBoolToString(symbol.IsActivelyTrading, "n/a"))
		fmt.Printf("%-20s %s\n", "Primary Listing:", f.MaybeToString(symbol.PrimaryListing, "n/a"))

		fmt.Println("\n--- Update Status ---")
		fmt.Printf("%-20s %s\n", "Profile Update:", f.MaybeDateToString(symbol.LastProfileUpdate, "2006-01-02 15:04", "n/a"))
		fmt.Printf("%-20s %s\n", "Profile Status:", f.MaybeToString(symbol.LastProfileStatus, "n/a"))
		fmt.Printf("%-20s %s\n", "Price Update:", f.MaybeDateToString(symbol.LastPriceUpdate, "2006-01-02 15:04", "n/a"))
		fmt.Printf("%-20s %s\n", "Price Status:", f.MaybeToString(symbol.LastPriceStatus, "n/a"))

		fmt.Printf("\n%-20s %s\n", "Website:", f.MaybeToString(symbol.Website, "n/a"))
		fmt.Printf("\n%s\n", f.MaybeToString(symbol.Description, "n/a"))

		return nil
	},
}

func init() {
	Cmd.AddCommand(profileCmd)
}
