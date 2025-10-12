package db

import (
	"database/sql"
	"time"
)

// AnalysisPackage represents stored analysis metadata
type AnalysisPackage struct {
	ID           string
	Name         string
	CreatedAt    time.Time
	Interval     string
	TimeFrom     time.Time
	TimeTo       time.Time
	HistBins     int
	HistMin      float64
	HistMax      float64
	McapMin      *int64
	InceptionMax *time.Time
	SymbolCount  int
	Status       string
}

// CreateAnalysisPackage inserts a new analysis package with status='processing'
func (db *DB) CreateAnalysisPackage(pkg *AnalysisPackage) error {
	query := `
		INSERT INTO analysis_packages (
			id, name, created_at, interval, time_from, time_to,
			hist_bins, hist_min, hist_max, mcap_min, inception_max, status
		) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
	`

	_, err := db.conn.Exec(query,
		pkg.ID, pkg.Name, pkg.CreatedAt, pkg.Interval,
		pkg.TimeFrom, pkg.TimeTo,
		pkg.HistBins, pkg.HistMin, pkg.HistMax,
		pkg.McapMin, pkg.InceptionMax, pkg.Status,
	)

	return err
}

// UpdateAnalysisPackageStatus updates the status and symbol count of a package
func (db *DB) UpdateAnalysisPackageStatus(packageID string, status string, symbolCount int) error {
	query := `UPDATE analysis_packages SET status = $1, symbol_count = $2 WHERE id = $3`
	_, err := db.conn.Exec(query, status, symbolCount, packageID)
	return err
}

// SaveAnalysisResult saves a single analysis result
func (db *DB) SaveAnalysisResult(packageID, ticker string, count int, mean, stddev, variance, min, max float64, histogramJSON []byte) error {
	query := `
		INSERT INTO analysis_results (
			package_id, ticker, count, mean, stddev, variance, min, max, histogram
		) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
	`

	_, err := db.conn.Exec(query,
		packageID, ticker, count, mean, stddev, variance, min, max, histogramJSON,
	)

	return err
}

// GetAnalysisPackage retrieves a package by ID
func (db *DB) GetAnalysisPackage(packageID string) (*AnalysisPackage, error) {
	query := `
		SELECT id, name, created_at, interval, time_from, time_to,
		       hist_bins, hist_min, hist_max, mcap_min, inception_max, symbol_count, status
		FROM analysis_packages
		WHERE id = $1
	`

	pkg := &AnalysisPackage{}
	err := db.conn.QueryRow(query, packageID).Scan(
		&pkg.ID, &pkg.Name, &pkg.CreatedAt, &pkg.Interval, &pkg.TimeFrom, &pkg.TimeTo,
		&pkg.HistBins, &pkg.HistMin, &pkg.HistMax, &pkg.McapMin, &pkg.InceptionMax,
		&pkg.SymbolCount, &pkg.Status,
	)

	if err == sql.ErrNoRows {
		return nil, nil
	}

	return pkg, err
}

// ListAnalysisPackages returns all analysis packages
func (db *DB) ListAnalysisPackages() ([]AnalysisPackage, error) {
	query := `
		SELECT id, name, created_at, interval, time_from, time_to,
		       hist_bins, hist_min, hist_max, mcap_min, inception_max, symbol_count, status
		FROM analysis_packages
		ORDER BY created_at DESC
	`

	rows, err := db.conn.Query(query)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var packages []AnalysisPackage
	for rows.Next() {
		var pkg AnalysisPackage
		if err := rows.Scan(
			&pkg.ID, &pkg.Name, &pkg.CreatedAt, &pkg.Interval, &pkg.TimeFrom, &pkg.TimeTo,
			&pkg.HistBins, &pkg.HistMin, &pkg.HistMax, &pkg.McapMin, &pkg.InceptionMax,
			&pkg.SymbolCount, &pkg.Status,
		); err != nil {
			return nil, err
		}
		packages = append(packages, pkg)
	}

	return packages, rows.Err()
}

// DeleteAnalysisPackage deletes a package (CASCADE will delete results)
func (db *DB) DeleteAnalysisPackage(packageID string) error {
	query := `DELETE FROM analysis_packages WHERE id = $1`
	_, err := db.conn.Exec(query, packageID)
	return err
}
