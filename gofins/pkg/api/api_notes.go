package api

import (
	"encoding/json"
	"net/http"

	"github.com/flocko-motion/gofins/pkg/db"
)

// handleListNotes returns all ratings that have notes, sorted by creation time (newest first)
func (s *Server) handleListNotes(w http.ResponseWriter, r *http.Request) {
	userID := getUserID(r)
	notes, err := db.GetAllNotesChronological(userID)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(notes)
}
