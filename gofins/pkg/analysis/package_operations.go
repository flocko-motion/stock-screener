package analysis

import (
	"fmt"
	"os"
	"path/filepath"

	"github.com/flocko-motion/gofins/pkg/db"
)

// GetPackage retrieves a package by ID
func GetPackage(database *db.DB, packageID string) (*db.AnalysisPackage, error) {
	return database.GetAnalysisPackage(packageID)
}

// ListPackages returns all analysis packages
func ListPackages(database *db.DB) ([]db.AnalysisPackage, error) {
	return database.ListAnalysisPackages()
}

// UpdatePackageName updates the name of an analysis package
func UpdatePackageName(database *db.DB, packageID string, name string) (*db.AnalysisPackage, error) {
	// Check if package exists
	pkg, err := database.GetAnalysisPackage(packageID)
	if err != nil {
		return nil, err
	}
	if pkg == nil {
		return nil, nil // Not found
	}

	// Update in database
	if err := database.UpdateAnalysisPackageName(packageID, name); err != nil {
		return nil, err
	}

	// Return updated package
	pkg.Name = name
	return pkg, nil
}

// DeletePackage deletes an analysis package and its associated files
func DeletePackage(database *db.DB, packageID string) error {
	// First, check if package exists
	pkg, err := database.GetAnalysisPackage(packageID)
	if err != nil {
		return fmt.Errorf("failed to get package: %w", err)
	}
	if pkg == nil {
		return fmt.Errorf("package not found")
	}

	// Delete from database first
	if err := database.DeleteAnalysisPackage(packageID); err != nil {
		return fmt.Errorf("failed to delete package from database: %w", err)
	}

	// Clean up PNG files if they exist
	plotsDir := PathPlots(packageID)
	if err := cleanupPackageFiles(packageID, plotsDir); err != nil {
		// Log the error but don't fail the deletion since DB is already cleaned
		fmt.Printf("[ANALYSIS] Warning: Failed to cleanup files for package %s: %v\n", packageID, err)
	}

	return nil
}

// cleanupPackageFiles removes all files associated with a package
func cleanupPackageFiles(packageID, plotsDir string) error {
	// Check if plots directory exists
	if _, err := os.Stat(plotsDir); os.IsNotExist(err) {
		return nil // Directory doesn't exist, nothing to clean up
	}

	// Find all PNG files in the plots directory
	pattern := filepath.Join(plotsDir, "*.png")
	matches, err := filepath.Glob(pattern)
	if err != nil {
		return fmt.Errorf("failed to find PNG files: %w", err)
	}

	// Delete each PNG file
	deletedCount := 0
	for _, file := range matches {
		if err := os.Remove(file); err != nil {
			fmt.Printf("[ANALYSIS] Warning: Failed to delete file %s: %v\n", file, err)
		} else {
			deletedCount++
		}
	}

	// Try to remove the entire directory if it's empty
	if err := os.Remove(plotsDir); err != nil {
		// Directory not empty or other error - that's fine, we cleaned the files
		fmt.Printf("[ANALYSIS] Note: Could not remove directory %s (may not be empty)\n", plotsDir)
	} else {
		fmt.Printf("[ANALYSIS] Removed plots directory for package %s\n", packageID)
	}

	fmt.Printf("[ANALYSIS] Cleaned up %d PNG files for package %s\n", deletedCount, packageID)
	return nil
}
