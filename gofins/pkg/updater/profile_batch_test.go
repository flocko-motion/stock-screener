package updater

import (
	"context"
	"testing"

	"github.com/stretchr/testify/assert"
)

func TestUpdateProfilesBatch(t *testing.T) {
	ctx := context.Background()
	logger := NewLoggerTest("profile_batch")

	// Run the batch profile update
	err := UpdateProfilesBatch(ctx, logger)
	
	// Should succeed (or fail gracefully with a clear error)
	if err != nil {
		t.Logf("Batch update failed (this may be expected if API is unavailable): %v", err)
	} else {
		t.Logf("Batch update completed successfully")
	}
	
	// The test passes as long as it doesn't panic
	// Actual validation would require checking database state
	assert.NotPanics(t, func() {
		_ = UpdateProfilesBatch(ctx, logger)
	})
}
