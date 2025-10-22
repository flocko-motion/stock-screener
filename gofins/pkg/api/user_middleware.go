package api

import (
	"context"
	"net/http"

	"github.com/flocko-motion/gofins/pkg/config"
	"github.com/flocko-motion/gofins/pkg/f"
	"github.com/google/uuid"
)

type contextKey string

const userIDKey contextKey = "userID"

// userMiddleware extracts user from X-Remote-User header (Apache) or config file
func (s *Server) userMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		var username string

		// 1. Check if dev user override is set (--user flag)
		if s.devUser != "" {
			username = s.devUser
		} else if user := r.Header.Get("X-Remote-User"); user != "" {
			// 2. Check X-Remote-User header (from Apache .htaccess auth)
			username = user
		} else {
			// 3. Fallback to config file default user (for CLI/localhost)
			var err error
			username, err = config.GetDefaultUser()
			if err != nil {
				http.Error(w, "Failed to get user: "+err.Error(), http.StatusInternalServerError)
				return
			}
		}

		// 4. Convert username to UUID
		userID := f.StringToUUID(username)

		// 5. Store in context
		ctx := context.WithValue(r.Context(), userIDKey, userID)
		next.ServeHTTP(w, r.WithContext(ctx))
	})
}

// getUserID extracts the user ID from the request context
func getUserID(r *http.Request) uuid.UUID {
	userID, ok := r.Context().Value(userIDKey).(uuid.UUID)
	if !ok {
		// This should never happen if middleware is properly configured
		return uuid.Nil
	}
	return userID
}

// adminOnlyMiddleware restricts access to admin user (default user from config)
func (s *Server) adminOnlyMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		// Get current user ID from context
		userID := getUserID(r)
		
		// Get admin user ID (default user from config)
		defaultUser, err := config.GetDefaultUser()
		if err != nil {
			http.Error(w, "Failed to get admin user", http.StatusInternalServerError)
			return
		}
		adminID := f.StringToUUID(defaultUser)
		
		// Check if current user is admin
		if userID != adminID {
			http.Error(w, "Forbidden: admin access required", http.StatusForbidden)
			return
		}
		
		next.ServeHTTP(w, r)
	})
}
