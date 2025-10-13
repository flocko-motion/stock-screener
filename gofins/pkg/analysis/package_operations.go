package analysis

import "github.com/flocko-motion/gofins/pkg/db"

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

// DeletePackage deletes an analysis package
func DeletePackage(database *db.DB, packageID string) error {
	return database.DeleteAnalysisPackage(packageID)
}
