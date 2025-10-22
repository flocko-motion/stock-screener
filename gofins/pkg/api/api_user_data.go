package api

import (
	"encoding/json"
	"net/http"
	"strconv"

	"github.com/flocko-motion/gofins/pkg/db"
	"github.com/go-chi/chi/v5"
)

// handleFavorites handles favorite operations
// POST /api/favorites/{ticker} - Toggle favorite
// GET /api/favorites - List all favorites
func (s *Server) handleFavorites(w http.ResponseWriter, r *http.Request) {
	userID := getUserID(r)
	ticker := chi.URLParam(r, "ticker")
	
	if r.Method == "GET" && ticker == "" {
		// List all favorites
		tickers, err := db.GetFavorites(userID)
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
		if ticker == "" {
			http.Error(w, "ticker required", http.StatusBadRequest)
			return
		}

		isFavorite, err := db.ToggleFavorite(userID, ticker)
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
	userID := getUserID(r)
	ticker := chi.URLParam(r, "ticker")

	if r.Method == "GET" && ticker == "" {
		// Get all latest ratings
		ratings, err := db.GetAllLatestRatings(userID)
		if err != nil {
			http.Error(w, err.Error(), http.StatusInternalServerError)
			return
		}
		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(ratings)
		return
	}

	if ticker == "" {
		http.Error(w, "ticker required", http.StatusBadRequest)
		return
	}

	if r.Method == "GET" {
		// Get latest rating
		rating, err := db.GetLatestRating(userID, ticker)
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

		rating, err := db.AddRating(userID, ticker, req.Rating, req.Notes)
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

		if err := db.DeleteRating(userID, ratingID); err != nil {
			http.Error(w, err.Error(), http.StatusInternalServerError)
			return
		}

		w.WriteHeader(http.StatusNoContent)
		return
	}

	http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
}

// handleRatingHistory returns rating history for a ticker
func (s *Server) handleRatingHistory(w http.ResponseWriter, r *http.Request) {
	userID := getUserID(r)
	ticker := chi.URLParam(r, "ticker")
	if ticker == "" {
		http.Error(w, "ticker required", http.StatusBadRequest)
		return
	}

	ratings, err := db.GetRatingHistory(userID, ticker)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(ratings)
}

// handleDeleteRating deletes a rating by ID
func (s *Server) handleDeleteRating(w http.ResponseWriter, r *http.Request) {
	userID := getUserID(r)
	idStr := chi.URLParam(r, "id")
	if idStr == "" {
		http.Error(w, "id required", http.StatusBadRequest)
		return
	}

	id, err := strconv.Atoi(idStr)
	if err != nil {
		http.Error(w, "invalid id", http.StatusBadRequest)
		return
	}

	if err := db.DeleteRating(userID, id); err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.WriteHeader(http.StatusNoContent)
}
