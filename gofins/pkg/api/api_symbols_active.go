package api

import (
	"encoding/json"
	"github.com/flocko-motion/gofins/pkg/db"
	"net/http"
)

func (s *Server) handleListActiveSymbols(w http.ResponseWriter, r *http.Request) {
	// Get all active symbols
	symbols, err := db.GetActiveSymbols()
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]interface{}{
		"symbols": symbols,
		"total":   len(symbols),
	})
}
