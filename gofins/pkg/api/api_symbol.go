package api

import (
	"encoding/json"
	"github.com/flocko-motion/gofins/pkg/db"
	"net/http"
	"strings"

	"github.com/flocko-motion/gofins/pkg/analysis"
)

func (s *Server) handleGetSymbol(w http.ResponseWriter, r *http.Request) {
	path := r.URL.Path[len("/api/symbol/"):]
	if path == "" {
		http.Error(w, "ticker required", http.StatusBadRequest)
		return
	}

	// Route to chart/histogram handlers if path contains them
	if strings.Contains(path, "/histogram") {
		s.handleSymbolChart(w, r, analysis.PlotTypeHistogram)
		return
	} else if strings.Contains(path, "/chart") {
		s.handleSymbolChart(w, r, analysis.PlotTypeChart)
		return
	}

	// Otherwise, return symbol profile
	ticker := strings.TrimSpace(path)
	profile, err := db.GetSymbolProfile(ticker)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
	if profile == nil {
		http.Error(w, "symbol not found", http.StatusNotFound)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(profile)
}
