package updater

import (
	"context"
	"fmt"
	"sync"
	"time"

	"github.com/flocko-motion/gofins/pkg/db"
	"github.com/flocko-motion/gofins/pkg/f"
	"github.com/flocko-motion/gofins/pkg/fmp"
	"github.com/flocko-motion/gofins/pkg/forex"
	"github.com/flocko-motion/gofins/pkg/log"
	"github.com/flocko-motion/gofins/pkg/types"
)

const (
	ProfileBatchUpdateInterval = 30 * 24 * time.Hour
	ProfileBulkBatchSize       = 1000 // Write to DB in batches
)

var (
	profileBatchUpdaterRunning bool
	profileBatchUpdaterMutex   sync.Mutex
)

// UpdateProfilesBatch fetches bulk profile data and updates all profiles
func UpdateProfilesBatch(ctx context.Context, log *log.Logger) error {
	log.Printf("Starting batch profile update\n")

	// Check if profiles were already updated today
	tickersNeedingUpdate, err := db.GetTickersNeedingProfileUpdate()
	if err != nil {
		log.Errorf("Failed to get tickers needing profile update: %v\n", err)
		return fmt.Errorf("failed to get tickers needing profile update: %w", err)
	}

	if len(tickersNeedingUpdate) == 0 {
		log.Printf("✓ All profiles already up-to-date\n")
		return nil
	}

	log.Printf("  %d tickers need profile updates\n", len(tickersNeedingUpdate))

	// Record start time to mark stale profiles later
	batchStartTime := time.Now()

	// Start batch update log
	logID, err := db.StartBatchUpdate("profile_batch")
	if err != nil {
		log.Errorf("Failed to start batch update log: %v\n", err)
		return fmt.Errorf("failed to start batch update log: %w", err)
	}

	// Fetch bulk profile data from FMP
	profiles, err := fmp.GetBulkProfiles()
	if err != nil {
		log.Errorf("Failed to fetch bulk profiles: %v\n", err)
		_ = db.FailBatchUpdate(logID, fmt.Sprintf("Failed to fetch bulk profiles: %v", err))
		return fmt.Errorf("failed to fetch bulk profiles: %w", err)
	}
	log.Printf("  Fetched %d profiles from FMP\n", len(profiles))

	// Filter to only profiles that need updating
	filteredProfiles := make([]*fmp.Profile, 0, len(tickersNeedingUpdate))
	for _, profile := range profiles {
		if tickersNeedingUpdate[profile.Symbol] {
			filteredProfiles = append(filteredProfiles, profile)
		}
	}
	profiles = filteredProfiles

	log.Printf("  Filtered to %d profiles that need updates\n", len(profiles))
	
	if len(profiles) == 0 {
		log.Printf("✓ No profiles to update (tickers needing updates not in FMP bulk data)\n")
		_ = db.CompleteBatchUpdate(logID, 0, 0)
		return nil
	}

	// Convert to symbols with USD market caps
	now := time.Now()
	weekStart := time.Date(now.Year(), now.Month(), now.Day(), 0, 0, 0, 0, time.UTC)
	symbols := convertProfilesToSymbols(profiles, weekStart, log)
	log.Printf("  Converted %d profiles to symbols\n", len(symbols))

	// Update database in batches
	updated, err := updateProfilesInBatches(symbols, log)
	if err != nil {
		log.Errorf("Failed to update profiles: %v\n", err)
		_ = db.FailBatchUpdate(logID, fmt.Sprintf("Failed to update profiles: %v", err))
		return fmt.Errorf("failed to update profiles: %w", err)
	}

	// Mark stale profiles as not found (profiles that weren't in this batch)
	// Only do this if we actually processed profiles - otherwise we'd incorrectly mark everything as not found
	var staleCount int64
	if len(profiles) > 0 {
		staleCount, err = db.MarkStaleProfilesAsNotFound(batchStartTime)
		if err != nil {
			log.Errorf("Failed to mark stale profiles as not found: %v\n", err)
		} else if staleCount > 0 {
			log.Printf("  Marked %d stale profiles as not found\n", staleCount)
		}
	}

	// Complete batch update log
	if err := db.CompleteBatchUpdate(logID, len(profiles), updated); err != nil {
		log.Errorf("Failed to complete batch update log: %v\n", err)
	}

	log.Printf("✓ Batch profile update complete: %d/%d symbols updated, %d marked as not found\n", updated, len(profiles), staleCount)
	return nil
}

// convertProfilesToSymbols converts FMP profiles to Symbol types with currency conversion
func convertProfilesToSymbols(profiles []*fmp.Profile, date time.Time, log *log.Logger) []types.Symbol {
	var symbols []types.Symbol
	conversionErrors := 0

	for _, profile := range profiles {
		if profile == nil || profile.Symbol == "" {
			continue
		}

		// Parse inception date
		var inception *time.Time
		if profile.IPODate != "" {
			if t, err := time.Parse("2006-01-02", profile.IPODate); err == nil {
				inception = &t
			}
		}

		status := types.StatusOK
		symbolType := deriveType(profile)

		// Normalize currency code
		currency := normalizeCurrencyCode(profile.Currency)

		// Convert market cap to USD if needed
		marketCapUSD := profile.MarketCap
		if currency != "" && currency != "USD" && profile.MarketCap > 0 {
			converted, err := forex.ConvertToUsd(profile.MarketCap, currency, date)
			if err != nil {
				conversionErrors++
				// Log to database for persistence
				_ = db.LogError("updater.profile_batch", "conversion_error",
					fmt.Sprintf("Failed to convert market cap for %s from %s to USD: %v", profile.Symbol, currency, err),
					nil)
				status = types.StatusFailed
			} else {
				marketCapUSD = converted
			}
		}

		symbol := types.Symbol{
			Ticker:            profile.Symbol,
			Name:              f.Ptr(profile.CompanyName),
			Exchange:          f.Ptr(profile.Exchange),
			Currency:          f.Ptr(currency),
			Type:              f.Ptr(symbolType),
			Sector:            f.Ptr(profile.Sector),
			Industry:          f.Ptr(profile.Industry),
			Country:           f.Ptr(profile.Country),
			Description:       f.Ptr(profile.Description),
			Website:           f.Ptr(profile.Website),
			CIK:               f.Ptr(profile.CIK),
			Inception:         inception,
			LastProfileUpdate: f.Ptr(time.Now()),
			LastProfileStatus: f.Ptr(status),
			IsActivelyTrading: f.Ptr(profile.IsActivelyTrading),
			MarketCap:         f.Ptr(int64(marketCapUSD)),
		}

		symbols = append(symbols, symbol)
	}

	if conversionErrors > 0 {
		log.Warnf("%d currency conversion errors (logged to database)\n", conversionErrors)
	}

	return symbols
}

// updateProfilesInBatches updates profiles in the database
// Batching is handled automatically by PutSymbols
func updateProfilesInBatches(symbols []types.Symbol, log *log.Logger) (int, error) {
	log.Printf("  Updating %d symbols in database...\n", len(symbols))

	if err := db.PutSymbols(symbols); err != nil {
		log.Errorf("Failed to update symbols: %v\n", err)
		return 0, fmt.Errorf("bulk update failed: %w", err)
	}

	log.Printf("  ✓ Updated %d symbols\n", len(symbols))
	return len(symbols), nil
}

// RunProfileBatchUpdater runs the batch profile updater in a loop
func RunProfileBatchUpdater(ctx context.Context, wg *sync.WaitGroup, log *log.Logger) {
	defer wg.Done()

	// Singleton check
	profileBatchUpdaterMutex.Lock()
	if profileBatchUpdaterRunning {
		log.Printf("Profile batch updater already running, skipping\n")
		profileBatchUpdaterMutex.Unlock()
		return
	}
	profileBatchUpdaterRunning = true
	profileBatchUpdaterMutex.Unlock()

	defer func() {
		profileBatchUpdaterMutex.Lock()
		profileBatchUpdaterRunning = false
		profileBatchUpdaterMutex.Unlock()
	}()

	ticker := time.NewTicker(ProfileBatchUpdateInterval)
	defer ticker.Stop()

	// Run immediately on start
	if err := UpdateProfilesBatch(ctx, log); err != nil {
		log.Errorf("Profile batch update failed: %v\n", err)
	}

	for {
		select {
		case <-ctx.Done():
			log.Printf("Profile batch updater stopped\n")
			return
		case <-ticker.C:
			if err := UpdateProfilesBatch(ctx, log); err != nil {
				log.Errorf("Profile batch update failed: %v\n", err)
			}
		}
	}
}
