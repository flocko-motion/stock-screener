package api

import (
	"context"
	"fmt"
	"net/http"
	"time"

	"github.com/flocko-motion/gofins/pkg/db"
)

type Server struct {
	db     *db.DB
	server *http.Server
}

func NewServer(database *db.DB, port int) *Server {
	s := &Server{
		db: database,
	}

	mux := http.NewServeMux()
	mux.HandleFunc("/api/symbol/", s.handleGetSymbol)
	mux.HandleFunc("/api/symbols", s.handleListSymbols)
	mux.HandleFunc("/api/symbols/active", s.handleListActiveSymbols)
	mux.HandleFunc("/api/prices/monthly/", s.handleGetMonthlyPrices)
	mux.HandleFunc("/api/health", s.handleHealth)

	// RESTful analysis endpoints
	mux.HandleFunc("/api/analyses", s.handleAnalyses)         // GET (list) / POST (create)
	mux.HandleFunc("/api/analysis/", s.handleAnalysisRouting) // Route to specific handlers

	// User data endpoints
	mux.HandleFunc("/api/favorites", s.handleFavorites)   // GET (list) / POST /{ticker} (toggle)
	mux.HandleFunc("/api/favorites/", s.handleFavorites)  // POST /{ticker} (toggle)
	mux.HandleFunc("/api/ratings", s.handleRatings)       // GET (all latest)
	mux.HandleFunc("/api/ratings/", s.handleRatings)      // GET/POST /{ticker}

	// Wrap with CORS middleware
	handler := corsMiddleware(mux)

	s.server = &http.Server{
		Addr:    fmt.Sprintf(":%d", port),
		Handler: handler,
	}

	return s
}

// corsMiddleware adds CORS headers to allow frontend access
func corsMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Access-Control-Allow-Origin", "*")
		w.Header().Set("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
		w.Header().Set("Access-Control-Allow-Headers", "Content-Type")

		// Handle preflight requests
		if r.Method == "OPTIONS" {
			w.WriteHeader(http.StatusOK)
			return
		}

		next.ServeHTTP(w, r)
	})
}

func (s *Server) Start(ctx context.Context) error {
	go func() {
		<-ctx.Done()
		shutdownCtx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
		defer cancel()
		s.server.Shutdown(shutdownCtx)
	}()

	fmt.Printf("REST API server listening on %s\n", s.server.Addr)
	if err := s.server.ListenAndServe(); err != http.ErrServerClosed {
		return err
	}
	return nil
}
