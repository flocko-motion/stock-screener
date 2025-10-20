package db

import (
	"slices"
	"testing"
	"time"

	"github.com/flocko-motion/gofins/pkg/f"
	"github.com/stretchr/testify/assert"
)

func TestGetFiltered(t *testing.T) {
	tickers, err := GetFilteredTickers(f.Ptr(int64(1_000_000_000)),
		f.Ptr(time.Date(2009, 1, 1, 0, 0, 0, 0, time.UTC)))
	assert.NoError(t, err)
	assert.NotNil(t, tickers)
	assert.False(t, slices.Contains(tickers, "FNMA"))
}
