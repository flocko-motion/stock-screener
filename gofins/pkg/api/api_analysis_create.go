package api

import (
	"encoding/json"
	"net/http"
	"time"

	"github.com/flocko-motion/gofins/pkg/analysis"
	"github.com/flocko-motion/gofins/pkg/db"
	"github.com/flocko-motion/gofins/pkg/f"
)

type CreateAnalysisRequest struct {
	Name         string  `json:"name"`
	Interval     string  `json:"interval"`  // "weekly" or "monthly"
	TimeFrom     string  `json:"time_from"` // YYYY, YYYY-MM or YYYY-MM-DD
	TimeTo       string  `json:"time_to"`   // YYYY, YYYY-MM or YYYY-MM-DD
	HistBins     int     `json:"hist_bins"`
	HistMin      float64 `json:"hist_min"`
	HistMax      float64 `json:"hist_max"`
	McapMin      *string `json:"mcap_min"`      // e.g., "1B", "500M"
	InceptionMax *string `json:"inception_max"` // YYYY, YYYY-MM or YYYY-MM-DD
}

type CreateAnalysisResponse struct {
	PackageID string `json:"package_id"`
	Status    string `json:"status"`
}

// handleCreateAnalysis creates a new analysis package
// POST /api/analyses
func (s *Server) handleCreateAnalysis(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	var req CreateAnalysisRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "Invalid request body", http.StatusBadRequest)
		return
	}

	// Parse time_from with default
	timeFromStr := req.TimeFrom
	if timeFromStr == "" {
		timeFromStr = "2009" // Default to 2009
	}

	timeFrom, err := f.ParseDate(timeFromStr)
	if err != nil {
		http.Error(w, "Invalid time_from: "+err.Error(), http.StatusBadRequest)
		return
	}

	// Parse time_to with default (first of current month)
	timeToStr := req.TimeTo
	if timeToStr == "" {
		now := time.Now()
		timeToStr = now.Format("2006-01") + "-01" // First of current month
	}

	timeTo, err := f.ParseDate(timeToStr)
	if err != nil {
		http.Error(w, "Invalid time_to: "+err.Error(), http.StatusBadRequest)
		return
	}

	// Parse interval with default
	intervalStr := req.Interval
	if intervalStr == "" {
		intervalStr = "weekly" // Default to weekly
	}

	var interval db.PriceInterval
	if intervalStr == "weekly" {
		interval = db.IntervalWeekly
	} else if intervalStr == "monthly" {
		interval = db.IntervalMonthly
	} else {
		http.Error(w, "Invalid interval (must be 'weekly' or 'monthly')", http.StatusBadRequest)
		return
	}

	// Parse mcap_min with default
	var mcapMin *int64
	if req.McapMin != nil && *req.McapMin != "" {
		parsed, err := f.ParseMarketCap(*req.McapMin)
		if err != nil {
			http.Error(w, "Invalid mcap_min format: "+err.Error(), http.StatusBadRequest)
			return
		}
		mcapMin = &parsed
	} else {
		defaultMcap := int64(100_000_000)
		mcapMin = &defaultMcap
	}

	// Parse optional inception_max
	var inceptionMax *time.Time
	if req.InceptionMax != nil && *req.InceptionMax != "" {
		parsed, err := f.ParseDate(*req.InceptionMax)
		if err != nil {
			http.Error(w, "Invalid inception_max: "+err.Error(), http.StatusBadRequest)
			return
		}
		inceptionMax = &parsed
	}

	// Use defaults for histogram config if not provided
	histBins := req.HistBins
	if histBins == 0 {
		histBins = 100 // Default from test
	}

	histMin := req.HistMin
	histMax := req.HistMax
	if histMin == 0 && histMax == 0 {
		histMin = -80.0 // Default from test
		histMax = 80.0  // Default from test
	}

	// Create analysis package
	config := analysis.AnalysisPackageConfig{
		Name:         req.Name,
		Interval:     interval,
		TimeFrom:     timeFrom,
		TimeTo:       timeTo,
		HistConfig:   analysis.HistogramConfig{NumBins: histBins, Min: histMin, Max: histMax},
		McapMin:      mcapMin,
		InceptionMax: inceptionMax,
	}

	packageID, err := analysis.CreatePackage(s.db, config)
	if err != nil {
		http.Error(w, "Failed to create package: "+err.Error(), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(CreateAnalysisResponse{
		PackageID: packageID,
		Status:    "processing",
	})
}
