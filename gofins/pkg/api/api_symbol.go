package api

import (
	"encoding/json"
	"net/http"
	"strings"

	"github.com/flocko-motion/gofins/pkg/analysis"
	"github.com/flocko-motion/gofins/pkg/db"
	"github.com/go-chi/chi/v5"
)

func (s *Server) handleGetSymbol(w http.ResponseWriter, r *http.Request) {
	ticker := chi.URLParam(r, "ticker")
	if ticker == "" {
		http.Error(w, "ticker required", http.StatusBadRequest)
		return
	}

	ticker = strings.TrimSpace(ticker)
	symbol, err := db.GetSymbol(ticker)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
	if symbol == nil {
		http.Error(w, "symbol not found", http.StatusNotFound)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(symbol)
}

func (s *Server) handleSymbolChartRoute(w http.ResponseWriter, r *http.Request) {
	s.handleSymbolChart(w, r, analysis.PlotTypeChart)
}

func (s *Server) handleSymbolHistogramRoute(w http.ResponseWriter, r *http.Request) {
	s.handleSymbolChart(w, r, analysis.PlotTypeHistogram)
}
