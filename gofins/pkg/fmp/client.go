package fmp

import (
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"os"
	"path/filepath"
	"sort"
	"strings"
	"sync"
	"time"

	"github.com/flocko-motion/gofins/pkg/f"
	"github.com/flocko-motion/gofins/pkg/files"
	"github.com/flocko-motion/gofins/pkg/log"
	"github.com/flocko-motion/gofins/pkg/ratelimit"
)

var logger = log.New("FMP")

func init() {
	// Clean up cache files older than 7 days at startup
	cleanupOldCache()
}

// getCacheDir returns the cache directory path
func getCacheDir() (string, error) {
	homeDir, err := os.UserHomeDir()
	if err != nil {
		return "", err
	}
	return filepath.Join(homeDir, ".gofins", "cache"), nil
}

// cleanupOldCache removes cache files older than 7 days
func cleanupOldCache() {
	cacheDir, err := getCacheDir()
	if err != nil {
		return // Silently fail - cache cleanup is not critical
	}
	
	// Check if cache directory exists
	if _, err := os.Stat(cacheDir); os.IsNotExist(err) {
		return // No cache directory, nothing to clean
	}
	
	// Read all files in cache directory
	entries, err := os.ReadDir(cacheDir)
	if err != nil {
		return // Silently fail
	}
	
	now := time.Now()
	maxAge := 7 * 24 * time.Hour
	removedCount := 0
	
	for _, entry := range entries {
		if entry.IsDir() {
			continue
		}
		
		info, err := entry.Info()
		if err != nil {
			continue
		}
		
		// Check if file is older than 7 days
		if now.Sub(info.ModTime()) > maxAge {
			filePath := filepath.Join(cacheDir, entry.Name())
			if err := os.Remove(filePath); err == nil {
				removedCount++
			}
		}
	}
	
	if removedCount > 0 {
		logger.Printf("Cleaned up %d old cache files\n", removedCount)
	}
}

const (
	BaseURL           = "https://financialmodelingprep.com"
	RequestsPerMinute = 3000 // ultimate: 3000 starter: 300
	MaxRetries        = 5
	BaseRetryDelay    = 3 * time.Second
	ApiKeyPathDefault = "~/.fins/config/financialmodelingprep.key"
)

// Client handles all FMP API interactions
type Client struct {
	apiKey      string
	httpClient  *http.Client
	rateLimiter *ratelimit.Limiter
}

var (
	globalClient *Client
	clientOnce   sync.Once
)

// Fmp returns the global FMP client, initializing it on first call
func Fmp() *Client {
	clientOnce.Do(func() {
		client, err := newClient(nil)
		if err != nil {
			panic(fmt.Sprintf("Failed to initialize FMP client: %v", err))
		}
		globalClient = client
	})
	return globalClient
}

// newClient creates a new FMP API client
func newClient(apiKeyPath *string) (*Client, error) {
	if apiKeyPath == nil {
		apiKeyPath = f.Ptr(ApiKeyPathDefault)
	}
	// Read API key from file
	apiKey, err := readAPIKey(*apiKeyPath)
	if err != nil {
		return nil, fmt.Errorf("failed to read API key: %w", err)
	}

	// Validate API key
	if len(apiKey) < 10 {
		return nil, fmt.Errorf("invalid API key: too short")
	}

	// Create HTTP client with connection pooling
	httpClient := &http.Client{
		Timeout: 30 * time.Second,
		Transport: &http.Transport{
			MaxIdleConns:        10,
			MaxIdleConnsPerHost: 10,
			MaxConnsPerHost:     10,
			IdleConnTimeout:     90 * time.Second,
		},
	}

	// Create rate limiter
	limiter := ratelimit.NewLimiter(RequestsPerMinute)

	return &Client{
		apiKey:      apiKey,
		httpClient:  httpClient,
		rateLimiter: limiter,
	}, nil
}

// readAPIKey reads the API key from the specified file path
func readAPIKey(apiKeyPath string) (string, error) {
	// Expand path (handle ~ and convert to absolute path)
	expandedPath, err := files.ExpandPath(apiKeyPath)
	if err != nil {
		return "", fmt.Errorf("failed to expand path: %w", err)
	}

	data, err := os.ReadFile(expandedPath)
	if err != nil {
		return "", err
	}
	return strings.TrimSpace(string(data)), nil
}

// apiGet makes a GET request to the FMP API with rate limiting and retries
func (c *Client) apiGet(endpoint string, params map[string]string, result interface{}) error {
	// Build URL with parameters
	reqURL, err := c.buildURL(endpoint, params)
	if err != nil {
		return err
	}

	// Retry loop with exponential backoff
	var lastErr error
	for attempt := 0; attempt < MaxRetries; attempt++ {
		// Wait for rate limit
		if err := c.rateLimiter.Wait(); err != nil {
			return fmt.Errorf("rate limiter error: %w", err)
		}

		// Make the request
		resp, err := c.httpClient.Get(reqURL)
		if err != nil {
			logger.Printf("Network error (attempt %d/%d): %v\n", attempt+1, MaxRetries, err)
			lastErr = err
			delay := BaseRetryDelay * time.Duration(1<<uint(attempt))
			time.Sleep(delay)
			continue
		}

		// Handle response
		err = c.handleResponse(resp, endpoint, result)
		resp.Body.Close()

		if err == nil {
			c.rateLimiter.LogRequest(endpoint, "ok")
			return nil
		}

		// Check for rate limit error
		if IsRateLimitError(err) {
			logger.Printf("Rate limit hit on %s - recovering...\n", endpoint)
			c.rateLimiter.LogRequest(endpoint, "rate-limit")
			if recErr := c.rateLimiter.RecoverFromLimit(); recErr != nil {
				return recErr
			}
			continue
		}

		// Check for bad request (don't retry)
		if IsBadRequestError(err) {
			logger.Printf("Bad request on %s: %v\n", endpoint, err)
			c.rateLimiter.LogRequest(endpoint, "bad-request")
			return err
		}

		// Other errors - retry with backoff
		logger.Printf("API error (attempt %d/%d) on %s: %v\n", attempt+1, MaxRetries, endpoint, err)
		lastErr = err
		c.rateLimiter.LogRequest(endpoint, fmt.Sprintf("error-%d", attempt))
		delay := BaseRetryDelay * time.Duration(1<<uint(attempt))
		time.Sleep(delay)
	}

	logger.Printf("Request failed after %d attempts: %v\n", MaxRetries, lastErr)
	return fmt.Errorf("request failed after %d attempts: %w", MaxRetries, lastErr)
}

// buildURL constructs the full URL with query parameters
func (c *Client) buildURL(endpoint string, params map[string]string) (string, error) {
	baseURL := fmt.Sprintf("%s/%s", BaseURL, endpoint)

	u, err := url.Parse(baseURL)
	if err != nil {
		return "", err
	}

	// Add parameters
	q := u.Query()
	for key, value := range params {
		q.Set(key, value)
	}
	q.Set("apikey", c.apiKey)

	u.RawQuery = q.Encode()
	return u.String(), nil
}

// getCacheKey generates a cache key from endpoint, params, and current date
func getCacheKey(endpoint string, params map[string]string) string {
	// Get current date (YYYY-MM-DD)
	date := time.Now().Format("2006-01-02")
	
	// Sort params alphabetically for consistent hashing
	var keys []string
	for k := range params {
		keys = append(keys, k)
	}
	sort.Strings(keys)
	
	// Build string to hash: endpoint + sorted params + date
	var sb strings.Builder
	sb.WriteString(endpoint)
	for _, k := range keys {
		sb.WriteString("|")
		sb.WriteString(k)
		sb.WriteString("=")
		sb.WriteString(params[k])
	}
	sb.WriteString("|")
	sb.WriteString(date)
	
	// Hash it
	hash := sha256.Sum256([]byte(sb.String()))
	return hex.EncodeToString(hash[:])
}

// getCachePath returns the cache file path for a given cache key
func getCachePath(cacheKey string) (string, error) {
	cacheDir, err := getCacheDir()
	if err != nil {
		return "", err
	}
	return filepath.Join(cacheDir, cacheKey), nil
}

// readFromCache attempts to read cached response
func readFromCache(cacheKey string) ([]byte, error) {
	cachePath, err := getCachePath(cacheKey)
	if err != nil {
		return nil, err
	}
	
	data, err := os.ReadFile(cachePath)
	if err != nil {
		return nil, err // Cache miss or read error
	}
	
	return data, nil
}

// writeToCache writes response data to cache
func writeToCache(cacheKey string, data []byte) error {
	cachePath, err := getCachePath(cacheKey)
	if err != nil {
		return err
	}
	
	// Create cache directory if it doesn't exist
	cacheDir := filepath.Dir(cachePath)
	if err := os.MkdirAll(cacheDir, 0755); err != nil {
		return err
	}
	
	return os.WriteFile(cachePath, data, 0644)
}

// apiGetRaw makes a GET request and returns the raw response body (for non-JSON endpoints like CSV)
// Automatically caches responses based on endpoint, params, and date
func (c *Client) apiGetRaw(endpoint string, params map[string]string) (io.ReadCloser, error) {
	// Generate cache key
	cacheKey := getCacheKey(endpoint, params)
	
	// Try to read from cache first
	if cachedData, err := readFromCache(cacheKey); err == nil {
		// Check if this is a cached error
		if strings.HasPrefix(string(cachedData), "ERROR:") {
			errorMsg := strings.TrimPrefix(string(cachedData), "ERROR:")
			logger.Printf("⚡ Cache HIT (error cached) for %s - returning cached error\n", endpoint)
			return nil, fmt.Errorf("%s", errorMsg)
		}
		logger.Printf("⚡ Cache HIT for %s - %d bytes\n", endpoint, len(cachedData))
		return io.NopCloser(strings.NewReader(string(cachedData))), nil
	}
	
	logger.Printf("Cache MISS for %s - fetching from API\n", endpoint)
	
	// Build URL with parameters
	reqURL, err := c.buildURL(endpoint, params)
	if err != nil {
		return nil, err
	}

	// Wait for rate limit
	if err := c.rateLimiter.Wait(); err != nil {
		return nil, fmt.Errorf("rate limiter error: %w", err)
	}

	// Make the request
	resp, err := c.httpClient.Get(reqURL)
	if err != nil {
		return nil, fmt.Errorf("request failed: %w", err)
	}

	// Read response body
	body, _ := io.ReadAll(resp.Body)
	resp.Body.Close()

	// Check status code
	if resp.StatusCode != http.StatusOK {
		errorMsg := fmt.Sprintf("API error: status %d - %s", resp.StatusCode, string(body))
		
		// Cache 400 errors (invalid parameters, end of pagination, etc.)
		if resp.StatusCode == http.StatusBadRequest {
			cachedError := []byte("ERROR:" + errorMsg)
			if err := writeToCache(cacheKey, cachedError); err != nil {
				logger.Printf("Warning: failed to cache error: %v\n", err)
			}
		}
		
		return nil, fmt.Errorf("%s", errorMsg)
	}

	c.rateLimiter.LogRequest(endpoint, "ok")
	
	// Write successful response to cache (ignore errors - caching is best-effort)
	if err := writeToCache(cacheKey, body); err != nil {
		logger.Printf("Warning: failed to write to cache: %v\n", err)
	}
	
	// Sleep for 30 seconds to be nice to the API
	logger.Printf("Sleeping 30s to be nice to the API...\n")
	time.Sleep(30 * time.Second)
	
	// Return the body as a ReadCloser
	return io.NopCloser(strings.NewReader(string(body))), nil
}

// handleResponse processes the HTTP response
func (c *Client) handleResponse(resp *http.Response, endpoint string, result interface{}) error {
	// Read body
	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return fmt.Errorf("failed to read response body: %w", err)
	}

	// Check status code
	switch resp.StatusCode {
	case http.StatusOK:
		// Parse JSON response
		if err := json.Unmarshal(body, result); err != nil {
			return fmt.Errorf("failed to parse JSON response: %w\nRaw response: %s", err, string(body))
		}
		return nil

	case http.StatusBadRequest:
		return &BadRequestError{Message: string(body)}

	case http.StatusPaymentRequired:
		return &RateLimitError{Message: string(body)}

	case http.StatusTooManyRequests:
		return &RateLimitError{Message: "too many requests"}

	default:
		return fmt.Errorf("API error: status %d - %s", resp.StatusCode, string(body))
	}
}

// Shutdown gracefully shuts down the client
func Shutdown() {
	Fmp().Shutdown()
}

func (c *Client) Shutdown() {
	c.rateLimiter.Shutdown()
}

// Error types
type BadRequestError struct {
	Message string
}

func (e *BadRequestError) Error() string {
	return fmt.Sprintf("bad request: %s", e.Message)
}

func IsBadRequestError(err error) bool {
	_, ok := err.(*BadRequestError)
	return ok
}

type RateLimitError struct {
	Message string
}

func (e *RateLimitError) Error() string {
	return fmt.Sprintf("rate limit exceeded: %s", e.Message)
}

func IsRateLimitError(err error) bool {
	_, ok := err.(*RateLimitError)
	return ok
}
