package updater

import (
	"fmt"
	"time"
)

const (
	StatusOK       = "ok"
	StatusNotFound = "not_found"
	StatusFailed   = "failed"
)

func threshold() time.Time {
	now := time.Now().UTC()
	threshold := time.Date(now.Year(), now.Month(), 1, 12, 0, 0, 0, time.UTC)
	return threshold
}

func thresholdProfile() time.Time {
	now := time.Now().UTC()
	threshold := time.Date(now.Year(), now.Month(), 1, 20, 0, 0, 0, time.UTC)
	return threshold
}

type Logger struct {
	prefix string
}

func NewLogger(prefix string) *Logger {
	return &Logger{prefix: fmt.Sprintf("%-8s", prefix)} // Fixed width 8 chars
}

func (l *Logger) Printf(format string, args ...interface{}) {
	fmt.Printf("[%s] "+format, append([]interface{}{l.prefix}, args...)...)
}

func (l *Logger) Started(total, workers int) {
	l.Printf("  Started: %5d stale, %d workers\n", total, workers)
}

func (l *Logger) Batch(remaining, batchSize int) {
	// l.Printf("  %5d remaining, update next %3d...\n", remaining, batchSize)
}

func (l *Logger) Stats(success, notFound, failed, remaining int, elapsed time.Duration) {
	total := success + notFound + failed
	rate := float64(total) / elapsed.Seconds()

	var eta string
	if rate > 0 {
		etaSeconds := float64(remaining) / rate
		eta = formatDuration(time.Duration(etaSeconds * float64(time.Second)))
	} else {
		eta = "unknown"
	}

	l.Printf("✓ %3d\t❌ %3d\t⚠️  %3d | ETA %10s for %5d left @ %.1f/s\n",
		success, notFound, failed, eta, remaining, rate)
}

func (l *Logger) AllDone(sleepHours int) {
	l.Printf("✓ All up to date! Sleeping for %d hours...\n", sleepHours)
}

func (l *Logger) Stopped() {
	l.Printf("  Stopped\n")
}

func (l *Logger) Error(format string, args ...interface{}) {
	l.Printf("✗ "+format, args...)
}

func (l *Logger) NotFoundList(tickers []string) {
	if len(tickers) > 0 && len(tickers) <= 10 {
		l.Printf("  Not found: %v\n", tickers)
	}
}

func (l *Logger) FailedList(tickers []string) {
	if len(tickers) > 0 && len(tickers) <= 10 {
		l.Printf("  Failed: %v\n", tickers)
	}
}

func formatDuration(d time.Duration) string {
	days := int(d.Hours() / 24)
	hours := int(d.Hours()) % 24
	minutes := int(d.Minutes()) % 60
	seconds := int(d.Seconds()) % 60

	if days > 0 {
		return fmt.Sprintf("%dd %dh %dm %ds", days, hours, minutes, seconds)
	}
	if hours > 0 {
		return fmt.Sprintf("%dh %dm %ds", hours, minutes, seconds)
	}
	if minutes > 0 {
		return fmt.Sprintf("%dm %ds", minutes, seconds)
	}
	return fmt.Sprintf("%ds", seconds)
}
