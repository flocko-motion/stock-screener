# Logging System Migration

## Overview
Centralized logging system with timestamps, log levels, colors, and DB persistence.

## New Package: `pkg/log`

### Features
- **Timestamps**: All logs include millisecond-precision timestamps `[HH:MM:SS.mmm]`
- **Log Levels**: `Info`, `Warn`, `Error`
- **Colors**: 
  - Warnings: Yellow `⚠️`
  - Errors: Red `✗`
- **DB Persistence**: Errors and warnings automatically logged to database
- **Dependency Injection**: Uses `types.ErrorLogger` interface to avoid circular dependencies

### Usage

```go
import "github.com/flocko-motion/gofins/pkg/log"

// Create logger with DB error logging
log := log.New("MyService").WithErrorLogger(db.Db())

// Or create test logger (no DB logging)
log := log.NewTest("TestService")

// Log messages
log.Infof("Processing %d items\n", count)           // Info (no color)
log.Warnf("Slow response: %v\n", duration)          // Yellow warning
log.Errorf("Failed to connect: %v\n", err)          // Red error (saved to DB)
```

### Migration Status

#### ✅ Completed
- Created `pkg/log` package with full logging functionality
- Created `pkg/types/logger.go` interface for dependency injection
- Implemented `types.ErrorLogger` on `*db.DB`
- Added timestamps to DB logger
- Added log levels and colors

#### ⚠️ Pending
- Update all `pkg/updater` files to use `*log.Logger` instead of local `*Logger`
- Replace `log.Error()` calls with `log.Errorf()` where appropriate
- Replace generic `log.Printf()` with `log.Warnf()` for warnings
- Test all updater functions

### Example Output

```
[12:25:30.123][Prices  ] Processing 100 symbols...
[12:25:32.456][Prices  ] ⚠️  Slow API response: 2.3s
[12:25:35.789][Prices  ] ✗ Failed to fetch prices for AAPL: connection timeout
[12:25:36.012][DB      ] Updating 200 symbols in batches of 1000...
```

## Benefits

1. **Consistent formatting** across all components
2. **Easy debugging** with precise timestamps
3. **Visual distinction** of errors and warnings with colors
4. **Automatic error tracking** in database
5. **No circular dependencies** via interface injection
6. **Backward compatible** - `Printf()` still works

## Next Steps

1. Run `go build ./...` to check for compilation errors
2. Fix any remaining `*Logger` → `*log.Logger` type references
3. Update error handling to use `Errorf()` instead of `Error()`
4. Test with `go test ./pkg/updater/...`
5. Deploy and monitor colored output in production
