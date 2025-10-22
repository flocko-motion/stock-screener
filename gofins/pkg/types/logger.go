package types

// ErrorLogger is the minimal interface needed for logging errors to DB
// This avoids circular dependencies between logger and db packages
type ErrorLogger interface {
	LogError(source, level, message string, metadata map[string]interface{}) error
}
