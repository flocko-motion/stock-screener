package config

import (
	"testing"

	"github.com/stretchr/testify/assert"
)

func TestLoadConfig(t *testing.T) {
	cfg, err := Load()
	assert.NoError(t, err)
	assert.NotNil(t, cfg)
	assert.NotEmpty(t, cfg.DefaultUser)
	
	t.Logf("Default user: %s", cfg.DefaultUser)
}

func TestGetDefaultUser(t *testing.T) {
	user, err := GetDefaultUser()
	assert.NoError(t, err)
	assert.NotEmpty(t, user)
	
	t.Logf("Default user: %s", user)
}
