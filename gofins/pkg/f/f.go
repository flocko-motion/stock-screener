package f

import (
	"crypto/sha256"
	"fmt"
	"time"

	"github.com/google/uuid"
)

// First returns the first value from a pair, ignoring the second (useful for ignoring errors)
func First[T any, U any](first T, _ U) T {
	return first
}

// Ptr returns a pointer to the given value
func Ptr[T any](v T) *T {
	return &v
}

// MaybeDateToMaybeString converts a nullable time.Time to a nullable formatted string
func MaybeDateToMaybeString(d *time.Time, format string) *string {
	if d == nil {
		return nil
	}
	str := d.Format(format)
	return &str
}

// MaybeToString converts a nullable value to a string, returning ifNil if the value is nil
func MaybeToString[T any](value *T, ifNil string) string {
	if value == nil {
		return ifNil
	}
	return fmt.Sprintf("%v", *value)
}

// MaybeBoolToString converts a nullable bool to a string, returning ifNil if the value is nil
func MaybeBoolToString(value *bool, ifNil string) string {
	if value == nil {
		return ifNil
	}
	return fmt.Sprintf("%t", *value)
}

// MaybeDateToString converts a nullable time.Time to a formatted string, returning ifNil if the value is nil
func MaybeDateToString(value *time.Time, format string, ifNil string) string {
	if value == nil {
		return ifNil
	}
	return value.Format(format)
}

// MaybeFloat64ToString converts a nullable float64 to a formatted string, returning ifNil if the value is nil
func MaybeFloat64ToString(value *float64, format string, ifNil string) string {
	if value == nil {
		return ifNil
	}
	return fmt.Sprintf(format, *value)
}

// MaybeInt64ToString converts a nullable int64 to a formatted string, returning ifNil if the value is nil
func MaybeInt64ToString(value *int64, format string, ifNil string) string {
	if value == nil {
		return ifNil
	}
	return fmt.Sprintf(format, *value)
}

// Keys returns all keys from a map as a slice (unsorted)
func Keys[K comparable, V any](m map[K]V) []K {
	keys := make([]K, 0, len(m))
	for k := range m {
		keys = append(keys, k)
	}
	return keys
}

// DurationToString formats a duration in a human-readable way
func DurationToString(d time.Duration) string {
	days := int(d.Hours() / 24)
	hours := int(d.Hours()) % 24
	minutes := int(d.Minutes()) % 60
	seconds := int(d.Seconds()) % 60

	if days > 0 {
		return fmt.Sprintf("%dd %dh %dm %ds", days, hours, minutes, seconds)
	}
	if hours > 0 {
		return fmt.Sprintf("%dh %dm %ds", hours, minutes, seconds)
	}
	if minutes > 0 {
		return fmt.Sprintf("%dm %ds", minutes, seconds)
	}
	return fmt.Sprintf("%ds", seconds)
}

// SecondsToString converts seconds (as float64) to a human-readable duration string
func SecondsToString(seconds float64) string {
	return DurationToString(time.Duration(seconds * float64(time.Second)))
}

// StringToUUID converts a string to a stable UUID using SHA-256 hash
func StringToUUID(s string) uuid.UUID {
	hash := sha256.Sum256([]byte(s))
	// Use first 16 bytes of hash as UUID
	var uuidBytes [16]byte
	copy(uuidBytes[:], hash[:16])
	return uuid.UUID(uuidBytes)
}
