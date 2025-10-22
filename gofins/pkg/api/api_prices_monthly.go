package api

import (
	"encoding/json"
	"net/http"

	"github.com/flocko-motion/gofins/pkg/db"
	"github.com/go-chi/chi/v5"
	"time"
)

func (s *Server) handleGetMonthlyPrices(w http.ResponseWriter, r *http.Request) {
	ticker := chi.URLParam(r, "ticker")
	if ticker == "" {
		http.Error(w, "ticker required", http.StatusBadRequest)
		return
	}

	// Default to last 5 years
	to := time.Now()
	from := to.AddDate(-5, 0, 0)

	prices, err := db.GetMonthlyPrices(ticker, from, to)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]interface{}{
		"ticker": ticker,
		"from":   from,
		"to":     to,
		"count":  len(prices),
		"prices": prices,
	})
}
