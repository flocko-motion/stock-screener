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
	mux.HandleFunc("/api/prices/monthly/", s.handleGetMonthlyPrices)
	mux.HandleFunc("/api/health", s.handleHealth)

	s.server = &http.Server{
		Addr:    fmt.Sprintf(":%d", port),
		Handler: mux,
	}

	return s
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
