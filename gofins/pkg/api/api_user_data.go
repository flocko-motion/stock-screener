package api

import (
	"encoding/json"
	"net/http"
	"strconv"
	"strings"
)

// handleFavorites handles favorite operations
// POST /api/favorites/{ticker} - Toggle favorite
// GET /api/favorites - List all favorites
func (s *Server) handleFavorites(w http.ResponseWriter, r *http.Request) {
	path := strings.TrimPrefix(r.URL.Path, "/api/favorites")
	
	if r.Method == "GET" && path == "" {
		// List all favorites
		tickers, err := s.db.GetFavorites()
		if err != nil {
			http.Error(w, err.Error(), http.StatusInternalServerError)
			return
		}
		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(tickers)
		return
	}

	if r.Method == "POST" {
		// Toggle favorite
		ticker := strings.Trim(path, "/")
		if ticker == "" {
			http.Error(w, "ticker required", http.StatusBadRequest)
			return
		}

		isFavorite, err := s.db.ToggleFavorite(ticker)
		if err != nil {
			http.Error(w, err.Error(), http.StatusInternalServerError)
			return
		}

		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(map[string]bool{"isFavorite": isFavorite})
		return
	}

	http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
}

// handleRatings handles rating operations
// POST /api/ratings/{ticker} - Add new rating
// GET /api/ratings/{ticker} - Get latest rating
// GET /api/ratings/{ticker}/history - Get rating history
// GET /api/ratings - Get all latest ratings
// DELETE /api/ratings/{id} - Delete rating by ID
func (s *Server) handleRatings(w http.ResponseWriter, r *http.Request) {
	path := strings.TrimPrefix(r.URL.Path, "/api/ratings")

	if r.Method == "GET" && path == "" {
		// Get all latest ratings
		ratings, err := s.db.GetAllLatestRatings()
		if err != nil {
			http.Error(w, err.Error(), http.StatusInternalServerError)
			return
		}
		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(ratings)
		return
	}

	parts := strings.Split(strings.Trim(path, "/"), "/")
	if len(parts) == 0 || parts[0] == "" {
		http.Error(w, "ticker required", http.StatusBadRequest)
		return
	}

	ticker := parts[0]

	if r.Method == "GET" {
		if len(parts) == 2 && parts[1] == "history" {
			// Get rating history
			ratings, err := s.db.GetRatingHistory(ticker)
			if err != nil {
				http.Error(w, err.Error(), http.StatusInternalServerError)
				return
			}
			w.Header().Set("Content-Type", "application/json")
			json.NewEncoder(w).Encode(ratings)
			return
		}

		// Get latest rating
		rating, err := s.db.GetLatestRating(ticker)
		if err != nil {
			http.Error(w, err.Error(), http.StatusInternalServerError)
			return
		}
		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(rating)
		return
	}

	if r.Method == "POST" {
		// Add new rating
		var req struct {
			Rating int     `json:"rating"`
			Notes  *string `json:"notes"`
		}

		if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
			http.Error(w, "Invalid request body", http.StatusBadRequest)
			return
		}

		if req.Rating < -5 || req.Rating > 5 {
			http.Error(w, "Rating must be between -5 and 5", http.StatusBadRequest)
			return
		}

		rating, err := s.db.AddRating(ticker, req.Rating, req.Notes)
		if err != nil {
			http.Error(w, err.Error(), http.StatusInternalServerError)
			return
		}

		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusCreated)
		json.NewEncoder(w).Encode(rating)
		return
	}

	if r.Method == "DELETE" {
		// Delete rating by ID
		ratingID, err := strconv.Atoi(ticker)
		if err != nil {
			http.Error(w, "Invalid rating ID", http.StatusBadRequest)
			return
		}

		if err := s.db.DeleteRating(ratingID); err != nil {
			http.Error(w, err.Error(), http.StatusInternalServerError)
			return
		}

		w.WriteHeader(http.StatusNoContent)
		return
	}

	http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
}
