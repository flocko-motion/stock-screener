package api

import (
	"context"
	"encoding/json"
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

func (s *Server) handleHealth(w http.ResponseWriter, r *http.Request) {
	json.NewEncoder(w).Encode(map[string]string{"status": "ok"})
}

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

func (s *Server) handleListSymbols(w http.ResponseWriter, r *http.Request) {
	tickers, err := s.db.GetAllTickers()
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]interface{}{
		"count":   len(tickers),
		"tickers": tickers,
	})
}

func (s *Server) handleGetMonthlyPrices(w http.ResponseWriter, r *http.Request) {
	ticker := r.URL.Path[len("/api/prices/monthly/"):]
	if ticker == "" {
		http.Error(w, "ticker required", http.StatusBadRequest)
		return
	}

	// Default to last 5 years
	to := time.Now()
	from := to.AddDate(-5, 0, 0)

	prices, err := s.db.GetMonthlyPrices(ticker, from, to)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]interface{}{
		"ticker": ticker,
		"from":   from,
		"to":     to,
		"count":  len(prices),
		"prices": prices,
	})
}
