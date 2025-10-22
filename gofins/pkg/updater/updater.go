package updater

import (
	"github.com/flocko-motion/gofins/pkg/db"
	"github.com/flocko-motion/gofins/pkg/log"
)

// NewLogger creates a logger with DB error logging enabled
func NewLogger(prefix string) *log.Logger {
	return log.New(prefix).WithErrorLogger(db.Db())
}

// NewLoggerTest creates a test logger without DB error logging
func NewLoggerTest(prefix string) *log.Logger {
	return log.NewTest(prefix)
}
