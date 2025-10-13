package f

import (
	"fmt"
	"time"
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
