package files

import (
	"bufio"
	"fmt"
	"os"
	"path/filepath"
	"strings"
)

// ExpandPath expands ~ to home directory and converts to absolute path
func ExpandPath(path string) (string, error) {
	// Expand ~ to home directory
	if strings.HasPrefix(path, "~/") {
		home, err := os.UserHomeDir()
		if err != nil {
			return "", err
		}
		path = filepath.Join(home, path[2:])
	}

	// Convert to absolute path
	absPath, err := filepath.Abs(path)
	if err != nil {
		return "", err
	}

	return absPath, nil
}

// ReadEnvFile reads a .env file and returns a map of key-value pairs
func ReadEnvFile(path string) (map[string]string, error) {
	expanded, err := ExpandPath(path)
	if err != nil {
		return nil, err
	}

	file, err := os.Open(expanded)
	if err != nil {
		return nil, err
	}
	defer file.Close()

	env := make(map[string]string)
	scanner := bufio.NewScanner(file)
	for scanner.Scan() {
		line := strings.TrimSpace(scanner.Text())
		if line == "" || strings.HasPrefix(line, "#") {
			continue
		}
		parts := strings.SplitN(line, "=", 2)
		if len(parts) == 2 {
			env[parts[0]] = parts[1]
		}
	}

	if err := scanner.Err(); err != nil {
		return nil, err
	}

	return env, nil
}

// GetEnvValue reads a specific key from an env file
func GetEnvValue(path, key string) (string, error) {
	env, err := ReadEnvFile(path)
	if err != nil {
		return "", err
	}

	value, ok := env[key]
	if !ok {
		return "", fmt.Errorf("%s not found in %s", key, path)
	}

	return value, nil
}
