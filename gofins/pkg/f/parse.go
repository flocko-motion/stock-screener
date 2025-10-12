package f

import (
	"fmt"
	"strconv"
	"strings"
	"time"
)

// ParseMarketCap parses market cap strings like "1B", "3.5T", "500M" into int64
func ParseMarketCap(s string) (int64, error) {
	s = strings.TrimSpace(strings.ToUpper(s))
	if s == "" {
		return 0, fmt.Errorf("empty market cap string")
	}

	// Determine multiplier
	var multiplier int64 = 1
	var numStr string

	if strings.HasSuffix(s, "T") {
		multiplier = 1_000_000_000_000 // Trillion
		numStr = strings.TrimSuffix(s, "T")
	} else if strings.HasSuffix(s, "B") {
		multiplier = 1_000_000_000 // Billion
		numStr = strings.TrimSuffix(s, "B")
	} else if strings.HasSuffix(s, "M") {
		multiplier = 1_000_000 // Million
		numStr = strings.TrimSuffix(s, "M")
	} else if strings.HasSuffix(s, "K") {
		multiplier = 1_000 // Thousand
		numStr = strings.TrimSuffix(s, "K")
	} else {
		// No suffix, parse as-is
		numStr = s
	}

	// Parse the numeric part
	value, err := strconv.ParseFloat(numStr, 64)
	if err != nil {
		return 0, fmt.Errorf("invalid number: %s", numStr)
	}

	return int64(value * float64(multiplier)), nil
}

// ParseDate parses dates in YYYY, YYYY-MM or YYYY-MM-DD format
func ParseDate(s string) (time.Time, error) {
	s = strings.TrimSpace(s)

	// Try YYYY-MM-DD first
	if t, err := time.Parse("2006-01-02", s); err == nil {
		return t, nil
	}

	// Try YYYY-MM (defaults to first day of month)
	if t, err := time.Parse("2006-01", s); err == nil {
		return t, nil
	}

	// Try YYYY (defaults to January 1st)
	if t, err := time.Parse("2006", s); err == nil {
		return t, nil
	}

	return time.Time{}, fmt.Errorf("invalid date format (expected YYYY, YYYY-MM or YYYY-MM-DD)")
}
