package api

import (
	"encoding/json"
	"net/http"

	"github.com/flocko-motion/gofins/pkg/config"
	"github.com/flocko-motion/gofins/pkg/db"
	"github.com/flocko-motion/gofins/pkg/f"
)

func (s *Server) handleGetCurrentUser(w http.ResponseWriter, r *http.Request) {
	// Get user ID from context
	userID := getUserID(r)
	
	// Get user from database
	user, err := db.GetUserByID(userID)
	if err != nil {
		http.Error(w, "Failed to get user: "+err.Error(), http.StatusInternalServerError)
		return
	}
	
	if user == nil {
		http.Error(w, "User not found", http.StatusNotFound)
		return
	}
	
	// Check if user is admin (matches default user from config)
	defaultUser, err := config.GetDefaultUser()
	if err != nil {
		http.Error(w, "Failed to get admin user", http.StatusInternalServerError)
		return
	}
	adminID := f.StringToUUID(defaultUser)
	user.IsAdmin = (userID == adminID)
	
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(user)
}
