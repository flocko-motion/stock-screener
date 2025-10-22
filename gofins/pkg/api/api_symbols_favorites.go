package api

import (
	"encoding/json"
	"github.com/flocko-motion/gofins/pkg/db"
	"net/http"
)

func (s *Server) handleListFavoriteSymbols(w http.ResponseWriter, r *http.Request) {
	// Get favorite symbols (filtered in SQL)
	symbols, err := db.GetFavoriteSymbols()
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
