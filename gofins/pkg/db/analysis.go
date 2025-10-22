package db

import (
	"database/sql"

	"github.com/flocko-motion/gofins/pkg/types"
	"github.com/google/uuid"
)

// CreateAnalysisPackage inserts a new analysis package with status='processing'
func CreateAnalysisPackage(pkg *types.AnalysisPackage) error {
	db := Db()
	query := `
		INSERT INTO analysis_packages (
			id, name, created_at, interval, time_from, time_to,
			hist_bins, hist_min, hist_max, mcap_min, inception_max, status, user_id
		) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
	`

	_, err := db.conn.Exec(query,
		pkg.ID, pkg.Name, pkg.CreatedAt, pkg.Interval,
		pkg.TimeFrom, pkg.TimeTo,
		pkg.HistBins, pkg.HistMin, pkg.HistMax,
		pkg.McapMin, pkg.InceptionMax, pkg.Status, pkg.UserID,
	)

	return err
}

// UpdateAnalysisPackageStatus updates the status and symbol count of a package for a specific user
func UpdateAnalysisPackageStatus(userID uuid.UUID, packageID string, status string, symbolCount int) error {
	db := Db()
	query := `UPDATE analysis_packages SET status = $1, symbol_count = $2 WHERE id = $3 AND user_id = $4`
	_, err := db.conn.Exec(query, status, symbolCount, packageID, userID)
	return err
}

// SaveAnalysisResult saves a single analysis result (verifies package ownership)
func SaveAnalysisResult(userID uuid.UUID, packageID, ticker string, count int, mean, stddev, variance, min, max float64, histogramJSON []byte) error {
	db := Db()
	
	// Verify package belongs to user
	var exists bool
	err := db.conn.QueryRow(`SELECT EXISTS(SELECT 1 FROM analysis_packages WHERE id = $1 AND user_id = $2)`, packageID, userID).Scan(&exists)
	if err != nil {
		return err
	}
	if !exists {
		return sql.ErrNoRows // Package doesn't exist or doesn't belong to user
	}
	
	query := `
		INSERT INTO analysis_results (
			package_id, ticker, count, mean, stddev, variance, min, max, histogram
		) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
	`

	_, err = db.conn.Exec(query,
		packageID, ticker, count, mean, stddev, variance, min, max, histogramJSON,
	)

	return err
}

// GetAnalysisResults retrieves all results for a package (verifies package ownership)
func GetAnalysisResults(userID uuid.UUID, packageID string) ([]types.AnalysisResult, error) {
	db := Db()
	
	// Verify package belongs to user
	var exists bool
	err := db.conn.QueryRow(`SELECT EXISTS(SELECT 1 FROM analysis_packages WHERE id = $1 AND user_id = $2)`, packageID, userID).Scan(&exists)
	if err != nil {
		return nil, err
	}
	if !exists {
		return nil, sql.ErrNoRows // Package doesn't exist or doesn't belong to user
	}
	
	query := `
		SELECT ar.package_id, ar.ticker, ar.count, ar.mean, ar.stddev, ar.variance, ar.min, ar.max, s.inception
		FROM analysis_results ar
		JOIN symbols s ON ar.ticker = s.ticker
		WHERE ar.package_id = $1
		ORDER BY ar.mean DESC
	`

	rows, err := db.conn.Query(query, packageID)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var results []types.AnalysisResult
	for rows.Next() {
		var r types.AnalysisResult
		if err := rows.Scan(&r.PackageID, &r.Ticker, &r.Count, &r.Mean, &r.StdDev, &r.Variance, &r.Min, &r.Max, &r.InceptionDate); err != nil {
			return nil, err
		}
		results = append(results, r)
	}

	return results, rows.Err()
}

// GetAnalysisPackage retrieves a package by ID for a specific user
func GetAnalysisPackage(userID uuid.UUID, packageID string) (*types.AnalysisPackage, error) {
	db := Db()
	query := `
		SELECT id, name, created_at, interval, time_from, time_to,
		       hist_bins, hist_min, hist_max, mcap_min, inception_max, symbol_count, status, user_id
		FROM analysis_packages
		WHERE id = $1 AND user_id = $2
	`

	pkg := &types.AnalysisPackage{}
	var symbolCount sql.NullInt64
	err := db.conn.QueryRow(query, packageID, userID).Scan(
		&pkg.ID, &pkg.Name, &pkg.CreatedAt, &pkg.Interval, &pkg.TimeFrom, &pkg.TimeTo,
		&pkg.HistBins, &pkg.HistMin, &pkg.HistMax, &pkg.McapMin, &pkg.InceptionMax,
		&symbolCount, &pkg.Status, &pkg.UserID,
	)

	if err == sql.ErrNoRows {
		return nil, nil
	}

	if symbolCount.Valid {
		pkg.SymbolCount = int(symbolCount.Int64)
	} else {
		pkg.SymbolCount = 0
	}

	return pkg, err
}

// ListAnalysisPackages returns all analysis packages for a specific user
func ListAnalysisPackages(userID uuid.UUID) ([]types.AnalysisPackage, error) {
	db := Db()
	query := `
		SELECT id, name, created_at, interval, time_from, time_to,
		       hist_bins, hist_min, hist_max, mcap_min, inception_max, symbol_count, status, user_id
		FROM analysis_packages
		WHERE user_id = $1
		ORDER BY created_at DESC
	`

	rows, err := db.conn.Query(query, userID)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var packages []types.AnalysisPackage
	for rows.Next() {
		var pkg types.AnalysisPackage
		var symbolCount sql.NullInt64
		if err := rows.Scan(
			&pkg.ID, &pkg.Name, &pkg.CreatedAt, &pkg.Interval, &pkg.TimeFrom, &pkg.TimeTo,
			&pkg.HistBins, &pkg.HistMin, &pkg.HistMax, &pkg.McapMin, &pkg.InceptionMax,
			&symbolCount, &pkg.Status, &pkg.UserID,
		); err != nil {
			return nil, err
		}
		if symbolCount.Valid {
			pkg.SymbolCount = int(symbolCount.Int64)
		} else {
			pkg.SymbolCount = 0
		}
		packages = append(packages, pkg)
	}

	return packages, rows.Err()
}

// UpdateAnalysisPackageName updates the name of a package for a specific user
func UpdateAnalysisPackageName(userID uuid.UUID, packageID string, name string) error {
	db := Db()
	query := `UPDATE analysis_packages SET name = $1 WHERE id = $2 AND user_id = $3`
	_, err := db.conn.Exec(query, name, packageID, userID)
	return err
}

// DeleteAnalysisPackage deletes a package for a specific user (CASCADE will delete results)
func DeleteAnalysisPackage(userID uuid.UUID, packageID string) error {
	db := Db()
	query := `DELETE FROM analysis_packages WHERE id = $1 AND user_id = $2`
	_, err := db.conn.Exec(query, packageID, userID)
	return err
}

