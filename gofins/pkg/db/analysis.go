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

// AnalysisResult represents a stored analysis result
type AnalysisResult struct {
	PackageID     string     `json:"-"`
	Ticker        string     `json:"symbol"`
	Count         int        `json:"-"`
	Mean          float64    `json:"mean"`
	StdDev        float64    `json:"stddev"`
	Variance      float64    `json:"-"`
	Min           float64    `json:"min"`
	Max           float64    `json:"max"`
	InceptionDate *time.Time `json:"inception"`
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

// GetAnalysisResults retrieves all results for a package
func (db *DB) GetAnalysisResults(packageID string) ([]AnalysisResult, error) {
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

	var results []AnalysisResult
	for rows.Next() {
		var r AnalysisResult
		if err := rows.Scan(&r.PackageID, &r.Ticker, &r.Count, &r.Mean, &r.StdDev, &r.Variance, &r.Min, &r.Max, &r.InceptionDate); err != nil {
			return nil, err
		}
		results = append(results, r)
	}

	return results, rows.Err()
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
	var symbolCount sql.NullInt64
	err := db.conn.QueryRow(query, packageID).Scan(
		&pkg.ID, &pkg.Name, &pkg.CreatedAt, &pkg.Interval, &pkg.TimeFrom, &pkg.TimeTo,
		&pkg.HistBins, &pkg.HistMin, &pkg.HistMax, &pkg.McapMin, &pkg.InceptionMax,
		&symbolCount, &pkg.Status,
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
		var symbolCount sql.NullInt64
		if err := rows.Scan(
			&pkg.ID, &pkg.Name, &pkg.CreatedAt, &pkg.Interval, &pkg.TimeFrom, &pkg.TimeTo,
			&pkg.HistBins, &pkg.HistMin, &pkg.HistMax, &pkg.McapMin, &pkg.InceptionMax,
			&symbolCount, &pkg.Status,
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

// UpdateAnalysisPackageName updates the name of a package
func (db *DB) UpdateAnalysisPackageName(packageID string, name string) error {
	query := `UPDATE analysis_packages SET name = $1 WHERE id = $2`
	_, err := db.conn.Exec(query, name, packageID)
	return err
}

// DeleteAnalysisPackage deletes a package (CASCADE will delete results)
func (db *DB) DeleteAnalysisPackage(packageID string) error {
	query := `DELETE FROM analysis_packages WHERE id = $1`
	_, err := db.conn.Exec(query, packageID)
	return err
}
