package config

import (
	"fmt"
	"os"
	"path/filepath"
	"sync"

	"gopkg.in/yaml.v3"
)

type Config struct {
	DefaultUser string `yaml:"default_user"`
}

var (
	instance *Config
	once     sync.Once
	mu       sync.RWMutex
)

// configPath returns the path to the config file
func configPath() string {
	home, err := os.UserHomeDir()
	if err != nil {
		return ".gofins/config.yaml"
	}
	return filepath.Join(home, ".gofins", "config.yaml")
}

// Load reads the config file and returns the Config instance
func Load() (*Config, error) {
	var loadErr error
	once.Do(func() {
		path := configPath()

		// Read the file
		data, err := os.ReadFile(path)
		if err != nil {
			if os.IsNotExist(err) {
				// Config doesn't exist, create template and exit
				loadErr = createTemplate()
				return
			}
			loadErr = fmt.Errorf("failed to read config: %w", err)
			return
		}

		// Parse YAML
		var cfg Config
		if err := yaml.Unmarshal(data, &cfg); err != nil {
			loadErr = fmt.Errorf("failed to parse config: %w", err)
			return
		}

		// Validate required fields
		if cfg.DefaultUser == "" {
			loadErr = fmt.Errorf("default_user is required in config file: %s", path)
			return
		}

		instance = &cfg
	})

	return instance, loadErr
}

// createTemplate creates a template config file and returns an error asking user to edit it
func createTemplate() error {
	path := configPath()

	// Ensure directory exists
	dir := filepath.Dir(path)
	if err := os.MkdirAll(dir, 0755); err != nil {
		return fmt.Errorf("failed to create config directory: %w", err)
	}

	// Template content
	template := `# GoFins Configuration
default_user: "yourname"  # used for CLI commands and localhost API calls
`

	// Write template
	if err := os.WriteFile(path, []byte(template), 0644); err != nil {
		return fmt.Errorf("failed to write config template: %w", err)
	}

	return fmt.Errorf("config file created at %s\nPlease edit it and set your username", path)
}

// Save writes the config to disk
func Save(cfg *Config) error {
	path := configPath()

	// Ensure directory exists
	dir := filepath.Dir(path)
	if err := os.MkdirAll(dir, 0755); err != nil {
		return fmt.Errorf("failed to create config directory: %w", err)
	}

	// Marshal to YAML
	data, err := yaml.Marshal(cfg)
	if err != nil {
		return fmt.Errorf("failed to marshal config: %w", err)
	}

	// Write to file
	if err := os.WriteFile(path, data, 0644); err != nil {
		return fmt.Errorf("failed to write config: %w", err)
	}

	// Update singleton
	mu.Lock()
	instance = cfg
	mu.Unlock()

	return nil
}

// Get returns the current config instance
func Get() (*Config, error) {
	mu.RLock()
	defer mu.RUnlock()

	if instance == nil {
		mu.RUnlock()
		cfg, err := Load()
		mu.RLock()
		if err != nil {
			return nil, err
		}
		return cfg, nil
	}

	return instance, nil
}

// GetDefaultUser returns the default user from config
func GetDefaultUser() (string, error) {
	cfg, err := Get()
	if err != nil {
		return "", err
	}
	return cfg.DefaultUser, nil
}

// SetDefaultUser updates the default user in config
func SetDefaultUser(username string) error {
	cfg, err := Get()
	if err != nil {
		return err
	}
	cfg.DefaultUser = username
	return Save(cfg)
}
