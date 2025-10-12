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

	// Parse time_from
	timeFrom, err := f.ParseDate(req.TimeFrom)
	if err != nil {
		http.Error(w, "Invalid time_from: "+err.Error(), http.StatusBadRequest)
		return
	}

	// Parse time_to
	timeTo, err := f.ParseDate(req.TimeTo)
	if err != nil {
		http.Error(w, "Invalid time_to: "+err.Error(), http.StatusBadRequest)
		return
	}

	// Parse interval
	var interval db.PriceInterval
	if req.Interval == "weekly" {
		interval = db.IntervalWeekly
	} else if req.Interval == "monthly" {
		interval = db.IntervalMonthly
	} else {
		http.Error(w, "Invalid interval (must be 'weekly' or 'monthly')", http.StatusBadRequest)
		return
	}

	// Parse optional mcap_min
	var mcapMin *int64
	if req.McapMin != nil && *req.McapMin != "" {
		parsed, err := f.ParseMarketCap(*req.McapMin)
		if err != nil {
			http.Error(w, "Invalid mcap_min format: "+err.Error(), http.StatusBadRequest)
			return
		}
		mcapMin = &parsed
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

	// Create analysis package
	config := analysis.AnalysisPackageConfig{
		Name:         req.Name,
		Interval:     interval,
		TimeFrom:     timeFrom,
		TimeTo:       timeTo,
		HistConfig:   analysis.HistogramConfig{NumBins: req.HistBins, Min: req.HistMin, Max: req.HistMax},
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
