package updater

import (
	"context"
	"sync"
	"time"

	"github.com/flocko-motion/gofins/pkg/calculator"
	"github.com/flocko-motion/gofins/pkg/db"
	"github.com/flocko-motion/gofins/pkg/f"
	"github.com/flocko-motion/gofins/pkg/fmp"
	"github.com/flocko-motion/gofins/pkg/forex"
	"github.com/flocko-motion/gofins/pkg/log"
	"github.com/flocko-motion/gofins/pkg/types"
)

const (
	ProfileUpdateInterval = 30 * 24 * time.Hour
	ProfileWorkers        = 8
	ProfileBatchSize      = 200
)

// currencyCodeMap maps non-standard currency codes from FMP to standard ISO codes
var currencyCodeMap = map[string]string{
	"ILA": "ILS", // Israeli New Shekel
	"KWF": "KWD", // Kuwaiti Dinar
}

// normalizeCurrencyCode converts non-standard currency codes to standard ISO codes
func normalizeCurrencyCode(currency string) string {
	if normalized, exists := currencyCodeMap[currency]; exists {
		return normalized
	}
	return currency
}

func UpdateProfiles(ctx context.Context) {
	log := NewLogger("Profile")

	for {
		select {
		case <-ctx.Done():
			log.Stopped()
			return
		default:
		}

		if err := updateProfilesImpl(log); err != nil {
			log.Errorf("Profile update failed: %v\n", err)
		}

		const sleepTimeHours = 8
		log.AllDone(sleepTimeHours)
		time.Sleep(time.Duration(sleepTimeHours) * time.Hour)
	}
}

func UpdateProfilesOnce() error {
	log := NewLogger("Profile")
	return updateProfilesImpl(log)
}

func updateProfilesImpl(log *log.Logger) error {
	totalStale, err := db.CountStaleProfiles()
	if err != nil {
		return err
	}

	log.Started(totalStale, ProfileWorkers)

	for {
		tickers, err := db.GetStaleProfiles(ProfileBatchSize)
		if err != nil {
			return err
		}

		if len(tickers) == 0 {
			return nil
		}

		currentStale, _ := db.CountStaleProfiles()
		log.Batch(currentStale, len(tickers))

		// Stats tracking
		startTime := time.Now()
		var statsMu sync.Mutex
		stats := &UpdateStats{
			Updated:  make([]string, 0),
			NotFound: make([]string, 0),
			Failed:   make([]string, 0),
		}

		// Worker pool
		tickerChan := make(chan string, len(tickers))
		var wg sync.WaitGroup

		// Start workers
		for i := 0; i < ProfileWorkers; i++ {
			wg.Add(1)
			go func() {
				defer wg.Done()
				for ticker := range tickerChan {
					_, result := updateProfile(ticker, false, log)
					statsMu.Lock()
					switch result {
					case types.StatusOK:
						stats.Updated = append(stats.Updated, ticker)
					case types.StatusNotFound:
						stats.NotFound = append(stats.NotFound, ticker)
					case types.StatusFailed:
						stats.Failed = append(stats.Failed, ticker)
					}
					statsMu.Unlock()
				}
			}()
		}

		// Send tickers to workers
		for _, ticker := range tickers {
			tickerChan <- ticker
		}
		close(tickerChan)

		// Wait for all workers to finish
		wg.Wait()

		// Print stats
		elapsed := time.Since(startTime)
		currentStale, _ = db.CountStaleProfiles()
		log.Stats(len(stats.Updated), len(stats.NotFound), len(stats.Failed), currentStale, elapsed)
		log.NotFoundList(stats.NotFound)
		log.FailedList(stats.Failed)
	}
}

type UpdateStats struct {
	Updated  []string
	NotFound []string
	Failed   []string
}

func updateProfile(ticker string, testMode bool, log *log.Logger) (*types.Symbol, string) {
	profile, err := fmp.GetProfile(ticker)
	now := calculator.StartOfWeek(time.Now())

	if err != nil {
		if fmp.IsNotFoundError(err) {
			status := types.StatusNotFound
			if !testMode {
				db.PutSymbols([]types.Symbol{{
					Ticker:            ticker,
					LastProfileUpdate: f.Ptr(time.Now()),
					LastProfileStatus: &status,
				}})
			}
			return nil, types.StatusNotFound
		}
		status := types.StatusFailed
		if !testMode {
			db.PutSymbols([]types.Symbol{{
				Ticker:            ticker,
				LastProfileUpdate: f.Ptr(time.Now()),
				LastProfileStatus: &status,
			}})
		}
		return nil, types.StatusFailed
	}

	var inception *time.Time
	if profile.IPODate != "" {
		if t, err := time.Parse("2006-01-02", profile.IPODate); err == nil {
			inception = &t
		}
	}

	status := types.StatusOK

	// Detect secondary listings by comparing exchange with primary listing
	symbolType := deriveType(profile)

	// Convert market cap to USD if needed
	profile.Currency = normalizeCurrencyCode(profile.Currency)
	marketCapUSD := profile.MarketCap
	if profile.Currency != "" && profile.Currency != "USD" && profile.MarketCap > 0 {
		converted, err := forex.ConvertToUsd(profile.MarketCap, profile.Currency, now)
		if err != nil {
			// Log error but continue with unconverted value
			// This can happen if forex data is not available for the currency
			log.Errorf("Failed to convert market cap for %s from %s to USD: %v (market cap: %.2f)\n",
				ticker, profile.Currency, err, profile.MarketCap)
			status = types.StatusFailed
		} else {
			marketCapUSD = converted
		}
	}

	symbol := &types.Symbol{
		Ticker:            ticker,
		Name:              f.Ptr(profile.CompanyName),
		Exchange:          f.Ptr(profile.Exchange),
		Currency:          f.Ptr(profile.Currency),
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
		MarketCap:         f.Ptr(int64(marketCapUSD)), // Convert float64 to int64, already in USD
	}

	if !testMode {
		if err := db.PutSymbols([]types.Symbol{*symbol}); err != nil {
			failStatus := types.StatusFailed
			db.PutSymbols([]types.Symbol{{
				Ticker:            ticker,
				LastProfileUpdate: f.Ptr(time.Now()),
				LastProfileStatus: &failStatus,
			}})
			return nil, failStatus
		}
	}

	return symbol, types.StatusOK
}

func deriveType(profile *fmp.Profile) string {
	if profile.IsEtf {
		return types.TypeETF
	}
	if profile.IsFund {
		return types.TypeFund
	}
	if profile.IsAdr {
		return types.TypeADR
	}

	return types.TypeStock
}
