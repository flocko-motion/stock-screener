package api

import (
	"encoding/json"
	"fmt"
	"net/http"
	"os"
	"strings"

	"github.com/flocko-motion/gofins/pkg/analysis"
	"github.com/flocko-motion/gofins/pkg/db"
	"github.com/flocko-motion/gofins/pkg/types"
	"github.com/go-chi/chi/v5"
)

// UpdateAnalysisRequest represents the request body for updating an analysis
type UpdateAnalysisRequest struct {
	Name string `json:"name"`
}

// handleAnalyses handles REST operations on /api/analyses
// GET  /api/analyses - List all analyses
// POST /api/analyses - Create new analysis
func (s *Server) handleAnalyses(w http.ResponseWriter, r *http.Request) {
	switch r.Method {
	case http.MethodGet:
		s.handleListAnalyses(w, r)
	case http.MethodPost:
		s.handleCreateAnalysis(w, r)
	default:
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
	}
}

// handleListAnalyses lists all analysis packages
func (s *Server) handleListAnalyses(w http.ResponseWriter, r *http.Request) {
	userID := getUserID(r)
	packages, err := analysis.ListPackages(userID)
	if err != nil {
		http.Error(w, "Failed to list analyses: "+err.Error(), http.StatusInternalServerError)
		return
	}

	// Ensure we return an empty array instead of null
	if packages == nil {
		packages = []types.AnalysisPackage{}
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(packages)
}

// handleAnalysisRouting routes requests to appropriate handlers
func (s *Server) handleAnalysisRouting(w http.ResponseWriter, r *http.Request) {
	path := strings.TrimPrefix(r.URL.Path, "/api/analysis/")

	// Route to /results endpoint
	if strings.Contains(path, "/results") {
		s.handleAnalysisResults(w, r)
		return
	}

	// Route to /profile endpoint
	if strings.Contains(path, "/profile/") {
		s.handleSymbolProfile(w, r)
		return
	}

	if strings.Contains(path, fmt.Sprintf("/%s/", analysis.PlotTypeHistogram)) {
		s.handleAnalysisChart(w, r, analysis.PlotTypeHistogram)
		return
	} else if strings.Contains(path, fmt.Sprintf("/%s/", analysis.PlotTypeChart)) {
		s.handleAnalysisChart(w, r, analysis.PlotTypeChart)
		return
	}
	// Default: handle package operations (GET/PUT/DELETE)
	s.handleAnalysis(w, r)
}

// handleAnalysis handles REST operations on /api/analysis/{id}
// GET    /api/analysis/{id} - Get single analysis
// PUT    /api/analysis/{id} - Update analysis (rename)
// DELETE /api/analysis/{id} - Delete analysis
func (s *Server) handleAnalysis(w http.ResponseWriter, r *http.Request) {
	// Extract ID from URL parameter
	packageID := chi.URLParam(r, "id")

	if packageID == "" {
		http.Error(w, "Package ID required", http.StatusBadRequest)
		return
	}

	switch r.Method {
	case http.MethodGet:
		s.handleGetAnalysis(w, r, packageID)
	case http.MethodPut:
		s.handleUpdateAnalysis(w, r, packageID)
	case http.MethodDelete:
		s.handleDeleteAnalysis(w, r, packageID)
	default:
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
	}
}

// handleGetAnalysis retrieves a single analysis package
func (s *Server) handleGetAnalysis(w http.ResponseWriter, r *http.Request, packageID string) {
	userID := getUserID(r)
	pkg, err := analysis.GetPackage(userID, packageID)
	if err != nil {
		http.Error(w, "Failed to get analysis: "+err.Error(), http.StatusInternalServerError)
		return
	}

	if pkg == nil {
		http.Error(w, "Analysis not found", http.StatusNotFound)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(pkg)
}

// handleUpdateAnalysis updates an analysis package (currently just name)
func (s *Server) handleUpdateAnalysis(w http.ResponseWriter, r *http.Request, packageID string) {
	var req UpdateAnalysisRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "Invalid request body", http.StatusBadRequest)
		return
	}

	if req.Name == "" {
		http.Error(w, "Name is required", http.StatusBadRequest)
		return
	}

	userID := getUserID(r)
	pkg, err := analysis.UpdatePackageName(userID, packageID, req.Name)
	if err != nil {
		http.Error(w, "Failed to update analysis: "+err.Error(), http.StatusInternalServerError)
		return
	}

	if pkg == nil {
		http.Error(w, "Analysis not found", http.StatusNotFound)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(pkg)
}

// handleDeleteAnalysis deletes an analysis package
func (s *Server) handleDeleteAnalysis(w http.ResponseWriter, r *http.Request, packageID string) {
	userID := getUserID(r)
	err := analysis.DeletePackage(userID, packageID)
	if err != nil {
		http.Error(w, "Failed to delete analysis: "+err.Error(), http.StatusInternalServerError)
		return
	}

	w.WriteHeader(http.StatusNoContent)
}

// handleAnalysisResults retrieves all results for an analysis package
// GET /api/analysis/{id}/results
func (s *Server) handleAnalysisResults(w http.ResponseWriter, r *http.Request) {
	// Extract packageID from path
	path := strings.TrimPrefix(r.URL.Path, "/api/analysis/")
	path = strings.TrimSuffix(path, "/results")
	packageID := strings.TrimSuffix(path, "/")

	if packageID == "" {
		http.Error(w, "Package ID required", http.StatusBadRequest)
		return
	}

	userID := getUserID(r)
	results, err := db.GetAnalysisResults(userID, packageID)
	if err != nil {
		http.Error(w, "Failed to get results: "+err.Error(), http.StatusInternalServerError)
		return
	}

	// Return empty array instead of null
	if results == nil {
		results = []types.AnalysisResult{}
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(results)
}

// handleAnalysisChart serves PNG chart images
// GET /api/analysis/{id}/chart/{ticker}
func (s *Server) handleAnalysisChart(w http.ResponseWriter, r *http.Request, plotType analysis.PlotType) {
	// Extract packageID and ticker from path
	path := strings.TrimPrefix(r.URL.Path, "/api/analysis/")
	parts := strings.Split(path, fmt.Sprintf("/%s/", plotType))

	if len(parts) != 2 {
		http.Error(w, "Invalid path format", http.StatusBadRequest)
		return
	}

	packageID := parts[0]
	ticker := strings.TrimSuffix(parts[1], "/")
	packageID = strings.ReplaceAll(packageID, "..", "")
	ticker = strings.ReplaceAll(ticker, "..", "")

	// Construct chart path
	chartPath := analysis.PathPlot(packageID, plotType, ticker)

	// Check if file exists
	if _, err := os.Stat(chartPath); os.IsNotExist(err) {
		http.Error(w, "Chart not found", http.StatusNotFound)
		return
	}

	// Serve the PNG file
	w.Header().Set("Content-Type", "image/png")
	http.ServeFile(w, r, chartPath)
}

// handleSymbolProfile retrieves profile information for a symbol
// GET /api/analysis/{id}/profile/{ticker}
func (s *Server) handleSymbolProfile(w http.ResponseWriter, r *http.Request) {
	// Extract packageID and ticker from path
	path := strings.TrimPrefix(r.URL.Path, "/api/analysis/")
	parts := strings.Split(path, "/profile/")

	if len(parts) != 2 {
		http.Error(w, "Invalid path format", http.StatusBadRequest)
		return
	}

	packageID := parts[0]
	ticker := strings.TrimSuffix(parts[1], "/")
	packageID = strings.ReplaceAll(packageID, "..", "")
	ticker = strings.ReplaceAll(ticker, "..", "")

	// Get symbol profile from database
	symbol, err := db.GetSymbol(ticker)
	if err != nil {
		http.Error(w, "Failed to get symbol profile: "+err.Error(), http.StatusInternalServerError)
		return
	}

	if symbol == nil {
		http.Error(w, "Symbol not found", http.StatusNotFound)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(symbol)
}
