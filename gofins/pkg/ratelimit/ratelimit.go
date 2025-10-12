package ratelimit

import (
	"sync"
	"time"
)

// Limiter implements a token bucket rate limiter with thread-safe operations
type Limiter struct {
	interval     time.Duration
	lastRequest  time.Time
	mu           sync.Mutex
	requestLog   []RequestLog
	logMu        sync.Mutex
	shutdownChan chan struct{}
	isShutdown   bool
}

// RequestLog tracks each API request for debugging
type RequestLog struct {
	Timestamp time.Time
	Endpoint  string
	Result    string
}

// NewLimiter creates a new rate limiter with specified requests per minute
func NewLimiter(requestsPerMinute int) *Limiter {
	// Add 2% buffer for safety
	interval := time.Duration(float64(time.Minute) / float64(requestsPerMinute) * 1.05)

	return &Limiter{
		interval:     interval,
		lastRequest:  time.Time{},
		requestLog:   make([]RequestLog, 0),
		shutdownChan: make(chan struct{}),
	}
}

// Wait blocks until the rate limit allows the next request
// Must hold lock for entire duration to ensure strict rate limiting
func (l *Limiter) Wait() error {
	l.mu.Lock()
	defer l.mu.Unlock()

	if l.isShutdown {
		return ErrShutdown
	}

	now := time.Now()
	elapsed := now.Sub(l.lastRequest)

	if elapsed < l.interval {
		sleepDuration := l.interval - elapsed
		if sleepDuration > 0 {
			// Sleep while holding lock (matches Python implementation)
			time.Sleep(sleepDuration)
		}
	}

	// Update timestamp after sleep
	l.lastRequest = time.Now()
	return nil
}

// RecoverFromLimit waits for recovery period (60 seconds) after hitting rate limit
func (l *Limiter) RecoverFromLimit() error {
	const recoveryTime = 60 * time.Second

	ticker := time.NewTicker(time.Second)
	defer ticker.Stop()

	remaining := int(recoveryTime.Seconds())

	for remaining > 0 {
		select {
		case <-ticker.C:
			remaining--
			// Could add callback here for progress updates
		case <-l.shutdownChan:
			return ErrShutdown
		}
	}

	return nil
}

// LogRequest records an API request for debugging
func (l *Limiter) LogRequest(endpoint, result string) {
	l.logMu.Lock()
	defer l.logMu.Unlock()

	l.requestLog = append(l.requestLog, RequestLog{
		Timestamp: time.Now(),
		Endpoint:  endpoint,
		Result:    result,
	})

	// Keep only last 1000 entries to prevent unbounded growth
	if len(l.requestLog) > 1000 {
		l.requestLog = l.requestLog[len(l.requestLog)-1000:]
	}
}

// GetLog returns a copy of the request log
func (l *Limiter) GetLog() []RequestLog {
	l.logMu.Lock()
	defer l.logMu.Unlock()

	logCopy := make([]RequestLog, len(l.requestLog))
	copy(logCopy, l.requestLog)
	return logCopy
}

// Shutdown signals the limiter to stop accepting new requests
func (l *Limiter) Shutdown() {
	l.mu.Lock()
	defer l.mu.Unlock()

	if !l.isShutdown {
		l.isShutdown = true
		close(l.shutdownChan)
	}
}

// Error types
var (
	ErrShutdown = &ShutdownError{}
)

type ShutdownError struct{}

func (e *ShutdownError) Error() string {
	return "rate limiter shutdown"
}
