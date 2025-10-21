package fmp

import (
	"encoding/json"
	"fmt"
	"io"
	"time"
)

// GetBulkProfiles fetches all company profiles from the bulk endpoint
// The API is paginated, so we fetch all pages and merge them
func GetBulkProfiles() ([]*Profile, error) {
	return Fmp().getBulkProfiles()
}

// getBulkProfiles is the internal implementation that has access to private fields
func (c *Client) getBulkProfiles() ([]*Profile, error) {
	var allProfiles []*Profile
	part := 0

	for {
		endpoint := fmt.Sprintf("stable/profile-bulk?part=%d", part)
		
		// Use the FMP client's raw GET method (handles rate limiting and API key)
		body, err := c.apiGetRaw(endpoint, nil)
		if err != nil {
			return nil, fmt.Errorf("failed to fetch bulk profiles part %d: %w", part, err)
		}

		// Parse JSON
		bodyBytes, err := io.ReadAll(body)
		body.Close()
		if err != nil {
			return nil, fmt.Errorf("failed to read response body: %w", err)
		}

		var profiles []*Profile
		if err := json.Unmarshal(bodyBytes, &profiles); err != nil {
			return nil, fmt.Errorf("failed to parse JSON for part %d: %w", part, err)
		}

		// If we got no profiles, we've reached the end
		if len(profiles) == 0 {
			break
		}

		allProfiles = append(allProfiles, profiles...)
		logf("Fetched part %d: %d profiles (total: %d)\n", part, len(profiles), len(allProfiles))
		
		part++
		
		// Safety limit to prevent infinite loops
		if part > 100 {
			return nil, fmt.Errorf("too many pages (>100), stopping")
		}
		
		// Small delay between pages to be nice to the API
		time.Sleep(100 * time.Millisecond)
	}

	logf("Fetched all profiles: %d total\n", len(allProfiles))
	return allProfiles, nil
}
