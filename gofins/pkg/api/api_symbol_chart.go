package api

import (
	"fmt"
	"net/http"
	"os"
	"path/filepath"
	"strings"
	"time"

	"github.com/flocko-motion/gofins/pkg/db"

	"github.com/flocko-motion/gofins/pkg/analysis"
)

// handleSymbolChart generates and serves PNG chart images for a symbol using full price history
// GET /api/symbol/{ticker}/chart
// GET /api/symbol/{ticker}/histogram
func (s *Server) handleSymbolChart(w http.ResponseWriter, r *http.Request, plotType analysis.PlotType) {
	// Extract ticker from path
	path := strings.TrimPrefix(r.URL.Path, "/api/symbol/")
	parts := strings.Split(path, fmt.Sprintf("/%s", plotType))
	if len(parts) < 1 {
		http.Error(w, "Invalid path", http.StatusBadRequest)
		return
	}

	ticker := parts[0]
	// Sanitize ticker to prevent path traversal
	ticker = strings.ReplaceAll(ticker, "..", "")
	ticker = strings.ReplaceAll(ticker, "/", "")

	// Generate chart on-the-fly and serve directly
	imageData, err := s.generateSymbolChart(ticker, plotType)
	if err != nil {
		http.Error(w, fmt.Sprintf("Failed to generate chart: %v", err), http.StatusInternalServerError)
		return
	}

	// Serve the PNG data directly
	w.Header().Set("Content-Type", "image/png")
	w.Header().Set("Content-Length", fmt.Sprintf("%d", len(imageData)))
	w.Write(imageData)
}

func (s *Server) generateSymbolChart(ticker string, plotType analysis.PlotType) ([]byte, error) {
	// Get the symbol info
	symbol, err := db.GetSymbol(ticker)
	if err != nil {
		return nil, fmt.Errorf("failed to get symbol: %w", err)
	}

	if symbol.OldestPrice == nil {
		return nil, fmt.Errorf("no price history available for %s", ticker)
	}

	// Get monthly prices for full history
	timeFrom := *symbol.OldestPrice
	timeTo := time.Now()

	prices, err := db.GetMonthlyPrices(ticker, timeFrom, timeTo)
	if err != nil {
		return nil, fmt.Errorf("failed to get prices: %w", err)
	}

	if len(prices) == 0 {
		return nil, fmt.Errorf("no price data available for %s", ticker)
	}

	// Calculate statistics
	histConfig := analysis.HistogramConfig{NumBins: 100, Min: -80.0, Max: 80.0}
	stats := analysis.AnalyzeYoY(prices, histConfig)

	// Generate the plot to a temp file
	tempDir := filepath.Join(os.TempDir(), "gofins-charts")
	if err := os.MkdirAll(tempDir, 0755); err != nil {
		return nil, fmt.Errorf("failed to create temp dir: %w", err)
	}

	tempFile := filepath.Join(tempDir, fmt.Sprintf("%s_%s_%d.png", ticker, plotType, time.Now().UnixNano()))
	defer os.Remove(tempFile) // Clean up after serving

	if plotType == analysis.PlotTypeChart {
		// Generate price chart
		if err := analysis.PlotChart(analysis.ChartOptions{
			TimeFrom:   timeFrom,
			TimeTo:     timeTo,
			Ticker:     ticker,
			Prices:     prices,
			Stats:      stats,
			OutputPath: tempFile,
			LimitY:     false, // Default to limiting Y-axis
		}); err != nil {
			return nil, fmt.Errorf("failed to create chart: %w", err)
		}
	} else if plotType == analysis.PlotTypeHistogram {
		// Generate histogram
		if err := analysis.PlotHistogram(ticker, stats, tempFile); err != nil {
			return nil, fmt.Errorf("failed to create histogram: %w", err)
		}
	} else {
		return nil, fmt.Errorf("unknown plot type: %s", plotType)
	}

	// Read the file into memory
	data, err := os.ReadFile(tempFile)
	if err != nil {
		return nil, fmt.Errorf("failed to read chart file: %w", err)
	}

	return data, nil
}
