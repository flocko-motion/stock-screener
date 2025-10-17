package fmp

import (
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"os"
	"strings"
	"sync"
	"time"

	"github.com/flocko-motion/gofins/pkg/f"
	"github.com/flocko-motion/gofins/pkg/files"
	"github.com/flocko-motion/gofins/pkg/ratelimit"
)

func logf(format string, args ...interface{}) {
	fmt.Printf("[FMP] "+format, args...)
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
			logf("Network error (attempt %d/%d): %v\n", attempt+1, MaxRetries, err)
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
			logf("Rate limit hit on %s - recovering...\n", endpoint)
			c.rateLimiter.LogRequest(endpoint, "rate-limit")
			if recErr := c.rateLimiter.RecoverFromLimit(); recErr != nil {
				return recErr
			}
			continue
		}

		// Check for bad request (don't retry)
		if IsBadRequestError(err) {
			logf("Bad request on %s: %v\n", endpoint, err)
			c.rateLimiter.LogRequest(endpoint, "bad-request")
			return err
		}

		// Other errors - retry with backoff
		logf("API error (attempt %d/%d) on %s: %v\n", attempt+1, MaxRetries, endpoint, err)
		lastErr = err
		c.rateLimiter.LogRequest(endpoint, fmt.Sprintf("error-%d", attempt))
		delay := BaseRetryDelay * time.Duration(1<<uint(attempt))
		time.Sleep(delay)
	}

	logf("Request failed after %d attempts: %v\n", MaxRetries, lastErr)
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
