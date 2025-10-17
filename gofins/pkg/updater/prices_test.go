package updater

import (
	"fmt"
	"sort"
	"testing"

	"github.com/flocko-motion/gofins/pkg/calculator"
	"github.com/flocko-motion/gofins/pkg/f"
	"github.com/flocko-motion/gofins/pkg/fmp"
	"github.com/stretchr/testify/assert"
)

func TestFetchPrices(t *testing.T) {
	ticker := "AAPL"
	fmpClient, err := fmp.NewClient(nil)
	assert.NoError(t, err)

	dailyPrices, err := fmpClient.FetchPriceHistory(ticker)
	assert.NoError(t, err)
	assert.NotNil(t, dailyPrices)

	sort.Slice(dailyPrices, func(i, j int) bool {
		return dailyPrices[i].Date < dailyPrices[j].Date
	})
	// Single-loop conversion: daily → weekly + monthly + YoY
	monthly, weekly := calculator.ConvertPrices(dailyPrices, ticker)

	for i, price := range monthly {
		fmt.Printf("monthly %d: %s\n", i, f.MaybeToString(price.YoY, "n/a"))
	}
	for i, price := range weekly {
		fmt.Printf("weekly %d: %s\n", i, f.MaybeToString(price.YoY, "n/a"))
	}

}
