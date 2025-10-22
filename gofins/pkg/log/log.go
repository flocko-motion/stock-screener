package log

import (
	"fmt"
	"time"

	"github.com/flocko-motion/gofins/pkg/f"
	"github.com/flocko-motion/gofins/pkg/types"
)

// ANSI color codes
const (
	colorReset  = "\033[0m"
	colorRed    = "\033[31m"
	colorYellow = "\033[33m"
	colorGreen  = "\033[32m"
	colorCyan   = "\033[36m"
)

// Log levels
const (
	LevelInfo  = "info"
	LevelWarn  = "warn"
	LevelError = "error"
)

// Logger provides structured logging with timestamps and optional DB persistence
type Logger struct {
	prefix      string
	test        bool
	errorLogger types.ErrorLogger // Optional DB logger for errors
}

// New creates a new logger with the given prefix
func New(prefix string) *Logger {
	return &Logger{
		prefix: fmt.Sprintf("%-8s", prefix), // Fixed width 8 chars
	}
}

// NewTest creates a test logger that doesn't write to DB
func NewTest(prefix string) *Logger {
	return &Logger{
		prefix: fmt.Sprintf("%-8s", prefix),
		test:   true,
	}
}

// WithErrorLogger adds a DB error logger for persisting errors
func (l *Logger) WithErrorLogger(errorLogger types.ErrorLogger) *Logger {
	l.errorLogger = errorLogger
	return l
}

// Printf logs a formatted message with timestamp (alias for Infof)
func (l *Logger) Printf(format string, args ...interface{}) {
	l.Infof(format, args...)
}

// Infof logs an info-level message
func (l *Logger) Infof(format string, args ...interface{}) {
	timestamp := time.Now().Format("15:04:05.000")
	message := fmt.Sprintf(format, args...)
	fmt.Printf("[%s][%s] %s", timestamp, l.prefix, message)
}

// Warnf logs a warning message in yellow
func (l *Logger) Warnf(format string, args ...interface{}) {
	timestamp := time.Now().Format("15:04:05.000")
	message := fmt.Sprintf(format, args...)
	fmt.Printf("%s[%s][%s] ⚠️  %s%s", colorYellow, timestamp, l.prefix, message, colorReset)

	// Log to database if error logger is configured
	if !l.test && l.errorLogger != nil {
		source := "updater." + trimSpace(l.prefix)
		_ = l.errorLogger.LogError(source, LevelWarn, message, nil)
	}
}

// Errorf logs an error message in red and persists to DB
func (l *Logger) Errorf(format string, args ...interface{}) {
	timestamp := time.Now().Format("15:04:05.000")
	message := fmt.Sprintf(format, args...)
	fmt.Printf("%s[%s][%s] ✗ %s%s", colorRed, timestamp, l.prefix, message, colorReset)

	// Log to database if error logger is configured
	if !l.test && l.errorLogger != nil {
		source := "updater." + trimSpace(l.prefix)
		_ = l.errorLogger.LogError(source, LevelError, message, nil)
	}
}

// Error logs an error message (alias for Errorf for backward compatibility)
func (l *Logger) Error(format string, args ...interface{}) {
	l.Errorf(format, args...)
}

// Started logs the start of an update process
func (l *Logger) Started(total, workers int) {
	l.Printf("  Started: %5d stale, %d workers\n", total, workers)
}

// Batch logs batch processing info (currently unused but kept for compatibility)
func (l *Logger) Batch(remaining, batchSize int) {
	// Intentionally empty - can be enabled for debugging
}

// Progress logs standardized progress with ETA and rate
// success: number of successful items
// failed: number of failed items
// warnings: number of items with warnings
// remaining: number of items still to process
// elapsed: time elapsed since start
func (l *Logger) Progress(success, failed, warnings, remaining int, elapsed time.Duration) {
	total := success + failed + warnings
	rate := float64(total) / elapsed.Seconds()

	var eta string
	if rate > 0 {
		etaSeconds := float64(remaining) / rate
		eta = f.SecondsToString(etaSeconds)
	} else {
		eta = "unknown"
	}

	l.Printf("✓ %d\t❌ %d\t⚠️  %d | ETA %s for %d left @ %.1f/s\n",
		success, failed, warnings, eta, remaining, rate)
}

// ProgressShort logs compact progress (for quick operations like DB writes)
// count: number of items processed
// remaining: number of items left (0 if complete)
// elapsed: time elapsed
func (l *Logger) ProgressShort(count, remaining int, elapsed time.Duration) {
	rate := float64(count) / elapsed.Seconds()
	
	if remaining > 0 {
		// Show ETA for ongoing operations
		var eta string
		if rate > 0 {
			etaSeconds := float64(remaining) / rate
			eta = f.SecondsToString(etaSeconds)
		} else {
			eta = "unknown"
		}
		l.Printf("✓ %d | ETA %s for %d left @ %.0f/s\n", count, eta, remaining, rate)
	} else {
		// Completion message
		l.Printf("✓ %d in %.1fs @ %.0f/s\n", count, elapsed.Seconds(), rate)
	}
}

// Stats logs progress statistics (legacy method for prices updater)
func (l *Logger) Stats(success, notFound, failed, remaining int, elapsed time.Duration) {
	total := success + notFound + failed
	rate := float64(total) / elapsed.Seconds()

	var eta string
	if rate > 0 {
		etaSeconds := float64(remaining) / rate
		eta = f.SecondsToString(etaSeconds)
	} else {
		eta = "unknown"
	}

	l.Printf("✓ %3d\t❌ %3d\t⚠️  %3d | ETA %10s for %5d left @ %.1f/s\n",
		success, notFound, failed, eta, remaining, rate)
}

// AllDone logs completion
func (l *Logger) AllDone(sleepHours int) {
	l.Printf("✓ All up to date! Sleeping for %d hours...\n", sleepHours)
}

// Stopped logs shutdown
func (l *Logger) Stopped() {
	l.Printf("  Stopped\n")
}

// NotFoundList logs a list of not found tickers
func (l *Logger) NotFoundList(tickers []string) {
	if len(tickers) > 0 && len(tickers) <= 10 {
		l.Printf("  Not found: %v\n", tickers)
	}
}

// FailedList logs a list of failed tickers
func (l *Logger) FailedList(tickers []string) {
	if len(tickers) > 0 && len(tickers) <= 10 {
		l.Printf("  Failed: %v\n", tickers)
	}
}

// Helper functions

func trimSpace(s string) string {
	result := ""
	for _, c := range s {
		if c != ' ' {
			result += string(c)
		}
	}
	return result
}
