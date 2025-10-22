package api

import (
	"encoding/json"
	"net/http"

	"github.com/flocko-motion/gofins/pkg/db"
)

func (s *Server) handleListErrors(w http.ResponseWriter, r *http.Request) {
	errors, err := db.GetRecentErrors(100)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(errors)
}

func (s *Server) handleClearErrors(w http.ResponseWriter, r *http.Request) {
	count, err := db.ClearAllErrors()
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]interface{}{
		"deleted": count,
	})
}
