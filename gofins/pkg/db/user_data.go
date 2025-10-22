package db

import (
	"database/sql"
	"time"
)

// UserRating represents a rating given to a symbol
type UserRating struct {
	ID        int       `json:"id"`
	Ticker    string    `json:"ticker"`
	Rating    int       `json:"rating"` // -5 to +5
	Notes     *string   `json:"notes"`
	CreatedAt time.Time `json:"createdAt"`
}

// ToggleFavorite adds or removes a symbol from favorites
func ToggleFavorite(ticker string) (bool, error) {
	db := Db()
	// Check if already favorited
	var exists bool
	err := db.conn.QueryRow("SELECT EXISTS(SELECT 1 FROM user_favorites WHERE ticker = $1)", ticker).Scan(&exists)
	if err != nil {
		return false, err
	}

	if exists {
		// Remove from favorites
		_, err = db.conn.Exec("DELETE FROM user_favorites WHERE ticker = $1", ticker)
		return false, err
	} else {
		// Add to favorites
		_, err = db.conn.Exec("INSERT INTO user_favorites (ticker) VALUES ($1)", ticker)
		return true, err
	}
}

// IsFavorite checks if a symbol is favorited
func IsFavorite(ticker string) (bool, error) {
	db := Db()
	var exists bool
	err := db.conn.QueryRow("SELECT EXISTS(SELECT 1 FROM user_favorites WHERE ticker = $1)", ticker).Scan(&exists)
	return exists, err
}

// GetFavorites returns all favorited tickers
func GetFavorites() ([]string, error) {
	db := Db()
	rows, err := db.conn.Query("SELECT ticker FROM user_favorites ORDER BY created_at DESC")
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var tickers []string
	for rows.Next() {
		var ticker string
		if err := rows.Scan(&ticker); err != nil {
			return nil, err
		}
		tickers = append(tickers, ticker)
	}
	return tickers, rows.Err()
}

// AddRating adds a new rating for a symbol
func AddRating(ticker string, rating int, notes *string) (*UserRating, error) {
	db := Db()
	if rating < -5 || rating > 5 {
		return nil, sql.ErrNoRows
	}

	var r UserRating
	err := db.conn.QueryRow(
		"INSERT INTO user_ratings (ticker, rating, notes) VALUES ($1, $2, $3) RETURNING id, ticker, rating, notes, created_at",
		ticker, rating, notes,
	).Scan(&r.ID, &r.Ticker, &r.Rating, &r.Notes, &r.CreatedAt)

	if err != nil {
		return nil, err
	}
	return &r, nil
}

// GetLatestRating returns the most recent rating for a symbol
func GetLatestRating(ticker string) (*UserRating, error) {
	db := Db()
	var r UserRating
	err := db.conn.QueryRow(
		"SELECT id, ticker, rating, notes, created_at FROM user_ratings WHERE ticker = $1 ORDER BY created_at DESC LIMIT 1",
		ticker,
	).Scan(&r.ID, &r.Ticker, &r.Rating, &r.Notes, &r.CreatedAt)

	if err == sql.ErrNoRows {
		return nil, nil
	}
	if err != nil {
		return nil, err
	}
	return &r, nil
}

// GetRatingHistory returns all ratings for a symbol
func GetRatingHistory(ticker string) ([]UserRating, error) {
	db := Db()
	rows, err := db.conn.Query(
		"SELECT id, ticker, rating, notes, created_at FROM user_ratings WHERE ticker = $1 ORDER BY created_at DESC",
		ticker,
	)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var ratings []UserRating
	for rows.Next() {
		var r UserRating
		if err := rows.Scan(&r.ID, &r.Ticker, &r.Rating, &r.Notes, &r.CreatedAt); err != nil {
			return nil, err
		}
		ratings = append(ratings, r)
	}
	return ratings, rows.Err()
}

// GetAllLatestRatings returns the latest rating for each rated symbol
func GetAllLatestRatings() (map[string]*UserRating, error) {
	db := Db()
	rows, err := db.conn.Query(`
		SELECT DISTINCT ON (ticker) id, ticker, rating, notes, created_at
		FROM user_ratings
		ORDER BY ticker, created_at DESC
	`)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	ratings := make(map[string]*UserRating)
	for rows.Next() {
		var r UserRating
		if err := rows.Scan(&r.ID, &r.Ticker, &r.Rating, &r.Notes, &r.CreatedAt); err != nil {
			return nil, err
		}
		ratings[r.Ticker] = &r
	}
	return ratings, rows.Err()
}

// DeleteRating deletes a rating by ID
func DeleteRating(id int) error {
	db := Db()
	_, err := db.conn.Exec("DELETE FROM user_ratings WHERE id = $1", id)
	return err
}

// GetAllNotesChronological returns all ratings that have notes, sorted by creation time (newest first)
func GetAllNotesChronological() ([]UserRating, error) {
	db := Db()
	rows, err := db.conn.Query(`
		SELECT id, ticker, rating, notes, created_at
		FROM user_ratings
		WHERE notes IS NOT NULL AND notes != ''
		ORDER BY created_at DESC
	`)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var notes []UserRating
	for rows.Next() {
		var r UserRating
		if err := rows.Scan(&r.ID, &r.Ticker, &r.Rating, &r.Notes, &r.CreatedAt); err != nil {
			return nil, err
		}
		notes = append(notes, r)
	}

	return notes, rows.Err()
}
