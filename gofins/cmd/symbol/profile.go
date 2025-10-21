package symbol

import (
	"fmt"

	"github.com/flocko-motion/gofins/pkg/db"
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
		if symbol.Name != nil {
			fmt.Printf("%-20s %s\n", "Name:", *symbol.Name)
		}
		if symbol.Exchange != nil {
			fmt.Printf("%-20s %s\n", "Exchange:", *symbol.Exchange)
		}
		if symbol.Type != nil {
			fmt.Printf("%-20s %s\n", "Type:", *symbol.Type)
		}
		if symbol.Currency != nil {
			fmt.Printf("%-20s %s\n", "Currency:", *symbol.Currency)
		}
		if symbol.Country != nil {
			fmt.Printf("%-20s %s\n", "Country:", *symbol.Country)
		}
		if symbol.Sector != nil {
			fmt.Printf("%-20s %s\n", "Sector:", *symbol.Sector)
		}
		if symbol.Industry != nil {
			fmt.Printf("%-20s %s\n", "Industry:", *symbol.Industry)
		}
		if symbol.MarketCap != nil {
			fmt.Printf("%-20s $%d\n", "Market Cap:", *symbol.MarketCap)
		}
		if symbol.Inception != nil {
			fmt.Printf("%-20s %s\n", "Inception:", symbol.Inception.Format("2006-01-02"))
		}
		if symbol.OldestPrice != nil {
			fmt.Printf("%-20s %s\n", "Oldest Price:", symbol.OldestPrice.Format("2006-01-02"))
		}
		if symbol.Ath12M != nil {
			fmt.Printf("%-20s %.2f\n", "ATH 12M:", *symbol.Ath12M)
		}
		if symbol.IsActivelyTrading != nil {
			fmt.Printf("%-20s %t\n", "Actively Trading:", *symbol.IsActivelyTrading)
		}
		if symbol.PrimaryListing != nil {
			fmt.Printf("%-20s %s\n", "Primary Listing:", *symbol.PrimaryListing)
		}
		
		fmt.Println("\n--- Update Status ---")
		if symbol.LastProfileUpdate != nil {
			fmt.Printf("%-20s %s\n", "Profile Update:", symbol.LastProfileUpdate.Format("2006-01-02 15:04"))
		}
		if symbol.LastProfileStatus != nil {
			fmt.Printf("%-20s %s\n", "Profile Status:", *symbol.LastProfileStatus)
		}
		if symbol.LastPriceUpdate != nil {
			fmt.Printf("%-20s %s\n", "Price Update:", symbol.LastPriceUpdate.Format("2006-01-02 15:04"))
		}
		if symbol.LastPriceStatus != nil {
			fmt.Printf("%-20s %s\n", "Price Status:", *symbol.LastPriceStatus)
		}
		
		if symbol.Website != nil && *symbol.Website != "" {
			fmt.Printf("\n%-20s %s\n", "Website:", *symbol.Website)
		}
		if symbol.Description != nil && *symbol.Description != "" {
			fmt.Printf("\n%s\n", *symbol.Description)
		}
		
		return nil
	},
}

func init() {
	Cmd.AddCommand(profileCmd)
}
