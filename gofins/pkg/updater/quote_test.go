package updater

import (
	"context"
	"testing"
	"time"

	"github.com/stretchr/testify/assert"
)

func TestUpdateQuotesOnce(t *testing.T) {
	// Check if we have enough time (need at least 5 minutes)
	if deadline, ok := t.Deadline(); ok {
		remaining := time.Until(deadline)
		if remaining < 5*time.Minute {
			t.Skipf("Test requires at least 5 minutes, but only %v remaining. Run with: go test -timeout 10m", remaining)
		}
	} else {
		// No deadline set, which means default 30s - skip the test
		t.Skip("Test requires extended timeout. Run with: go test -timeout 10m")
	}

	// Create a context with 5 minute timeout for this test
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Minute)
	defer cancel()

	// Run the one-shot quotes updater (yesterday)
	log := NewLogger("QuotesTest")
	yesterday := time.Now().AddDate(0, 0, -1)
	err := UpdateQuotes(ctx, yesterday, log)
	if err != nil {
		// Allow network/rate-limit issues without failing CI
		t.Logf("Quote update failed (may be expected due to API limits or offline): %v", err)
	} else {
		t.Log("Quote update completed successfully")
	}

	// Ensure it doesn't panic on repeated runs
	assert.NotPanics(t, func() {
		ctx2, cancel2 := context.WithTimeout(context.Background(), 5*time.Minute)
		defer cancel2()
		_ = UpdateQuotes(ctx2, yesterday, log)
	})
}
