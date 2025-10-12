package api

import (
	"encoding/json"
	"net/http"
)

func (s *Server) handleGetSymbol(w http.ResponseWriter, r *http.Request) {
	ticker := r.URL.Path[len("/api/symbol/"):]
	if ticker == "" {
		http.Error(w, "ticker required", http.StatusBadRequest)
		return
	}

	symbol, err := s.db.GetSymbol(ticker)
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
