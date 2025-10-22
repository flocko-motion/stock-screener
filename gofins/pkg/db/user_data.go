package db

import (
	"database/sql"
	"time"

	"github.com/flocko-motion/gofins/pkg/f"
	"github.com/flocko-motion/gofins/pkg/types"
	"github.com/google/uuid"
)

// CreateUser creates a new user with a UUID derived from their name
func CreateUser(name string) (*types.User, error) {
	db := Db()

	// Generate stable UUID from username (hash-based)
	userID := f.StringToUUID(name)

	var user types.User
	err := db.conn.QueryRow(`
		INSERT INTO users (id, name, created_at)
		VALUES ($1, $2, NOW())
		RETURNING id, name, created_at
	`, userID, name).Scan(&user.ID, &user.Name, &user.CreatedAt)

	if err != nil {
		return nil, err
	}

	return &user, nil
}

// GetUser retrieves a user by name
func GetUser(name string) (*types.User, error) {
	db := Db()

	var user types.User
	err := db.conn.QueryRow(`
		SELECT id, name, created_at
		FROM users
		WHERE name = $1
	`, name).Scan(&user.ID, &user.Name, &user.CreatedAt)

	if err == sql.ErrNoRows {
		return nil, nil
	}
	if err != nil {
		return nil, err
	}

	return &user, nil
}

// GetUserByID retrieves a user by UUID
func GetUserByID(id uuid.UUID) (*types.User, error) {
	db := Db()

	var user types.User
	err := db.conn.QueryRow(`
		SELECT id, name, created_at
		FROM users
		WHERE id = $1
	`, id).Scan(&user.ID, &user.Name, &user.CreatedAt)

	if err == sql.ErrNoRows {
		return nil, nil
	}
	if err != nil {
		return nil, err
	}

	return &user, nil
}

// ListUsers returns all users
func ListUsers() ([]types.User, error) {
	db := Db()

	rows, err := db.conn.Query(`
		SELECT id, name, created_at
		FROM users
		ORDER BY created_at ASC
	`)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var users []types.User
	for rows.Next() {
		var user types.User
		if err := rows.Scan(&user.ID, &user.Name, &user.CreatedAt); err != nil {
			return nil, err
		}
		users = append(users, user)
	}

	return users, rows.Err()
}

// DeleteUser deletes a user and all their data (ratings, favorites)
func DeleteUser(name string) error {
	db := Db()

	// Get user to find their UUID
	user, err := GetUser(name)
	if err != nil {
		return err
	}
	if user == nil {
		return nil // User doesn't exist, nothing to delete
	}

	// Start transaction
	tx, err := db.conn.Begin()
	if err != nil {
		return err
	}
	defer tx.Rollback()

	// Delete user's ratings
	if _, err := tx.Exec(`DELETE FROM user_ratings WHERE user_id = $1`, user.ID); err != nil {
		return err
	}

	// Delete user's favorites
	if _, err := tx.Exec(`DELETE FROM user_favorites WHERE user_id = $1`, user.ID); err != nil {
		return err
	}

	// Delete user
	if _, err := tx.Exec(`DELETE FROM users WHERE id = $1`, user.ID); err != nil {
		return err
	}

	// Commit transaction
	return tx.Commit()
}

// UserRating represents a rating given to a symbol
type UserRating struct {
	ID        int       `json:"id"`
	Ticker    string    `json:"ticker"`
	Rating    int       `json:"rating"` // -5 to +5
	Notes     *string   `json:"notes"`
	CreatedAt time.Time `json:"createdAt"`
}

// ToggleFavorite adds or removes a symbol from favorites
func ToggleFavorite(userID uuid.UUID, ticker string) (bool, error) {
	db := Db()
	// Check if already favorited
	var exists bool
	err := db.conn.QueryRow("SELECT EXISTS(SELECT 1 FROM user_favorites WHERE user_id = $1 AND ticker = $2)", userID, ticker).Scan(&exists)
	if err != nil {
		return false, err
	}

	if exists {
		// Remove from favorites
		_, err = db.conn.Exec("DELETE FROM user_favorites WHERE user_id = $1 AND ticker = $2", userID, ticker)
		return false, err
	} else {
		// Add to favorites
		_, err = db.conn.Exec("INSERT INTO user_favorites (user_id, ticker) VALUES ($1, $2)", userID, ticker)
		return true, err
	}
}

// IsFavorite checks if a symbol is favorited
func IsFavorite(userID uuid.UUID, ticker string) (bool, error) {
	db := Db()
	var exists bool
	err := db.conn.QueryRow("SELECT EXISTS(SELECT 1 FROM user_favorites WHERE user_id = $1 AND ticker = $2)", userID, ticker).Scan(&exists)
	return exists, err
}

// GetFavorites returns all favorited tickers
func GetFavorites(userID uuid.UUID) ([]string, error) {
	db := Db()
	rows, err := db.conn.Query("SELECT ticker FROM user_favorites WHERE user_id = $1 ORDER BY created_at DESC", userID)
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
func AddRating(userID uuid.UUID, ticker string, rating int, notes *string) (*UserRating, error) {
	db := Db()
	if rating < -5 || rating > 5 {
		return nil, sql.ErrNoRows
	}

	var r UserRating
	err := db.conn.QueryRow(
		"INSERT INTO user_ratings (user_id, ticker, rating, notes) VALUES ($1, $2, $3, $4) RETURNING id, ticker, rating, notes, created_at",
		userID, ticker, rating, notes,
	).Scan(&r.ID, &r.Ticker, &r.Rating, &r.Notes, &r.CreatedAt)

	if err != nil {
		return nil, err
	}
	return &r, nil
}

// GetLatestRating returns the most recent rating for a symbol
func GetLatestRating(userID uuid.UUID, ticker string) (*UserRating, error) {
	db := Db()
	var r UserRating
	err := db.conn.QueryRow(
		"SELECT id, ticker, rating, notes, created_at FROM user_ratings WHERE user_id = $1 AND ticker = $2 ORDER BY created_at DESC LIMIT 1",
		userID, ticker,
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
func GetRatingHistory(userID uuid.UUID, ticker string) ([]UserRating, error) {
	db := Db()
	rows, err := db.conn.Query(
		"SELECT id, ticker, rating, notes, created_at FROM user_ratings WHERE user_id = $1 AND ticker = $2 ORDER BY created_at DESC",
		userID, ticker,
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
func GetAllLatestRatings(userID uuid.UUID) (map[string]*UserRating, error) {
	db := Db()
	rows, err := db.conn.Query(`
		SELECT DISTINCT ON (ticker) id, ticker, rating, notes, created_at
		FROM user_ratings
		WHERE user_id = $1
		ORDER BY ticker, created_at DESC
	`, userID)
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

// DeleteRating deletes a rating by ID (for the given user)
func DeleteRating(userID uuid.UUID, id int) error {
	db := Db()
	_, err := db.conn.Exec("DELETE FROM user_ratings WHERE user_id = $1 AND id = $2", userID, id)
	return err
}

// GetAllNotesChronological returns all ratings that have notes, sorted by creation time (newest first)
func GetAllNotesChronological(userID uuid.UUID) ([]UserRating, error) {
	db := Db()
	rows, err := db.conn.Query(`
		SELECT id, ticker, rating, notes, created_at
		FROM user_ratings
		WHERE user_id = $1 AND notes IS NOT NULL AND notes != ''
		ORDER BY created_at DESC
	`, userID)
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
