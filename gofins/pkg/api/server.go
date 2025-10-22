package api

import (
	"context"
	"fmt"
	"net/http"
	"time"

	"github.com/flocko-motion/gofins/pkg/db"
	"github.com/go-chi/chi/v5"
	"github.com/go-chi/chi/v5/middleware"
)

type Server struct {
	db      *db.DB
	server  *http.Server
	devUser string // If set, all requests use this user (dev mode)
}

func NewServer(database *db.DB, port int, devUser string) *Server {
	s := &Server{
		db:      database,
		devUser: devUser,
	}

	r := chi.NewRouter()

	// Middleware
	r.Use(middleware.Logger)
	r.Use(middleware.Recoverer)
	r.Use(corsMiddleware)

	// Routes
	r.Route("/api", func(r chi.Router) {
		// Health
		r.Get("/health", s.handleHealth)

		// Symbols (public - no user context needed)
		r.Get("/symbols", s.handleListSymbols)
		r.Get("/symbols/active", s.handleListActiveSymbols)
		r.Get("/symbol/{ticker}", s.handleGetSymbol)
		r.Get("/symbol/{ticker}/chart", s.handleSymbolChartRoute)
		r.Get("/symbol/{ticker}/histogram", s.handleSymbolHistogramRoute)

		// Prices (public)
		r.Get("/prices/monthly/{ticker}", s.handleGetMonthlyPrices)
		r.Get("/prices/weekly/{ticker}", s.handleGetWeeklyPrices)

		// Admin-only routes (require admin user from config)
		r.Group(func(r chi.Router) {
			r.Use(s.userMiddleware)
			r.Use(s.adminOnlyMiddleware)

			// Errors
			r.Get("/errors", s.handleListErrors)
			r.Delete("/errors", s.handleClearErrors)
		})

		// User-specific routes (require user context)
		r.Group(func(r chi.Router) {
			r.Use(s.userMiddleware)

			// User info
			r.Get("/user", s.handleGetCurrentUser)

			// Analyses
			r.Get("/analyses", s.handleAnalyses)
			r.Post("/analyses", s.handleAnalyses)
			r.Get("/analysis/{id}", s.handleAnalysisRouting)
			r.Put("/analysis/{id}", s.handleAnalysisRouting)
			r.Delete("/analysis/{id}", s.handleAnalysisRouting)

			// Favorites
			r.Get("/symbols/favorites", s.handleListFavoriteSymbols)
			r.Get("/favorites", s.handleFavorites)
			r.Post("/favorites/{ticker}", s.handleFavorites)

			// Ratings
			r.Get("/ratings", s.handleRatings)
			r.Get("/ratings/{ticker}", s.handleRatings)
			r.Post("/ratings/{ticker}", s.handleRatings)
			r.Get("/ratings/{ticker}/history", s.handleRatingHistory)
			r.Delete("/ratings/{id}", s.handleDeleteRating)

			// Notes
			r.Get("/notes", s.handleListNotes)
		})
	})

	s.server = &http.Server{
		Addr:    fmt.Sprintf(":%d", port),
		Handler: r,
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
