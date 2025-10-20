package error

import (
	"fmt"
	"testing"
	"time"

	"github.com/flocko-motion/gofins/pkg/db"
	"github.com/flocko-motion/gofins/pkg/f"
	"github.com/stretchr/testify/assert"
)

func TestErrorCommands(t *testing.T) {
	// Log a test error to the database with unique identifier
	uniqueID := fmt.Sprintf("test-%d", time.Now().UnixNano())
	testMessage := fmt.Sprintf("Test error message for command testing [%s]", uniqueID)
	testDetails := fmt.Sprintf("This is a test error created by the error command test [%s]", uniqueID)
	
	err := db.LogError("test.error_cmd", "test", testMessage, f.Ptr(testDetails))
	assert.NoError(t, err, "Should log error to database")

	// Get recent errors to find our test error
	errors, err := db.GetRecentErrors(10)
	assert.NoError(t, err, "Should retrieve recent errors")
	assert.NotEmpty(t, errors, "Should have at least one error")

	// Find our test error
	var testErrorID int
	found := false
	for _, e := range errors {
		if e.Source == "test.error_cmd" && e.Message == testMessage {
			testErrorID = e.ID
			found = true
			assert.Equal(t, "test", e.ErrorType, "Error type should match")
			assert.NotNil(t, e.Details, "Details should not be nil")
			if e.Details != nil {
				assert.Equal(t, testDetails, *e.Details, "Details should match")
			}
			break
		}
	}
	assert.True(t, found, "Should find the test error in recent errors")

	// Get error by ID
	errorEntry, err := db.GetErrorByID(testErrorID)
	assert.NoError(t, err, "Should retrieve error by ID")
	assert.NotNil(t, errorEntry, "Error entry should not be nil")
	assert.Equal(t, testErrorID, errorEntry.ID, "Error ID should match")
	assert.Equal(t, "test.error_cmd", errorEntry.Source, "Source should match")
	assert.Equal(t, testMessage, errorEntry.Message, "Message should match")

	// Clear all errors
	deleted, err := db.ClearAllErrors()
	assert.NoError(t, err, "Should clear all errors")
	assert.GreaterOrEqual(t, deleted, 1, "Should delete at least one error")

	// Verify errors are cleared
	errors, err = db.GetRecentErrors(10)
	assert.NoError(t, err, "Should retrieve errors after clear")
	assert.Empty(t, errors, "Should have no errors after clear")

	// Verify specific error is gone
	errorEntry, err = db.GetErrorByID(testErrorID)
	assert.Error(t, err, "Should error when trying to get deleted error")
	assert.Nil(t, errorEntry, "Error entry should be nil after deletion")
}
