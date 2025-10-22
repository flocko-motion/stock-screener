# Bugs (fix bugs first before working on TODOs)

## Weekly YoY data has N/A blocks in 2020-2021
Weekly prices show blocks of N/A YoY values during 2020-2021 period (e.g., AAPL from July 2020 to April 2021). Pattern shows every other week has N/A, suggesting missing weekly price data or calculation issue for that period. Need to investigate why YoY calculation fails for these specific weeks.

## ✅ FIXED: SymbolList select value bug
Fixed by ensuring filter values from sessionStorage are always strings, not arrays or objects.

# TODO list for gofins, in order of priority

## ✅ Refactor API with Chi
- DONE: Migrated to Chi router
- DONE: Added /api/errors endpoints (GET list, DELETE clear)
- DONE: Created UI tab for errors

## ✅ Tab "Errors"
- DONE: Show recent errors from database
- DONE: Button to clear all errors
- DONE: Auto-refresh every 30s


## ✅ Tab "Notes"
- DONE: Tab showing notes grouped by ticker
- DONE: Notes sorted chronologically (oldest→newest) to show opinion evolution
- DONE: Click ticker to open symbol detail
- DONE: Shows latest rating with stars in header
- DONE: Individual notes show numeric rating (-5 to +5)
- DONE: Arrow indicators (↑/↓) when rating changes
- DONE: Fetches ALL notes (no limit)
- DONE: ISO date format (YYYY-MM-DD)

## ✅ List of ratings in stock details view
- DONE: Rating history shown in SymbolDetail component
- DONE: Delete button for each rating
- DONE: Ratings sorted chronologically (oldest→newest) to show opinion evolution
- DONE: Added API endpoints: GET /ratings/{ticker}/history and DELETE /ratings/{id}

## ✅ Tab "Favorites"
- DONE: Tab showing favorite stocks
- DONE: Uses same SymbolList component with defaultFavoritesOnly=true
- DONE: Filter box is now collapsible (Show/Hide Filters button)
- DONE: Filters collapsed by default to save space
- DONE: All stock lists now have collapsible filters

## Journal / Notebook Feature

**Concept**: Unified research journal mixing ratings and freeform notes

**Database Design**:
- Keep `user_ratings` table as-is (optimized for ticker-specific queries)
- Add new `user_journal` table for freeform notes:
  - id, title, content, type ('note'|'idea'|'news'|'strategy'), tags (JSON), created_at, updated_at
- Add `journal_tickers` junction table (many-to-many):
  - journal_id, ticker
  - Allows notes to link to 0, 1, or multiple tickers

**UI/UX**:
- New "Journal" tab showing unified timeline of ratings + notes
- Each entry shows type icon (⭐ rating, 📝 note, 💡 idea, 📰 news)
- Ratings displayed as special note type with numeric badge
- Linked tickers shown as clickable badges
- Filter by: type, ticker, tag, date range
- Full-text search across all content
- Quick capture: floating "+" button or hotkey

**Features**:
- Create standalone notes (research, ideas, strategies)
- Link notes to multiple tickers
- Tag/categorize entries
- View all entries related to a ticker (in symbol detail view)
- Export journal to markdown/PDF
- Auto-link ticker mentions in text (e.g., $AAPL)

**Implementation Phases**:
1. Phase 1: Basic notes (create, edit, delete, link to tickers)
2. Phase 2: Tags, categories, rich text/markdown editor
3. Phase 3: Unified timeline view mixing ratings + notes
4. Phase 4: Advanced features (attachments, export, auto-linking)

**API Endpoints**:
- GET/POST /api/journal - List/create entries
- GET/PUT/DELETE /api/journal/{id} - CRUD operations
- GET /api/journal/ticker/{ticker} - All entries mentioning ticker
- POST/DELETE /api/journal/{id}/tickers - Link/unlink tickers
- GET /api/timeline - Unified view of ratings + journal entries

## Beta correlation

- beta correlation should be added to analysis module (can't be in profile itself, because we need to specify a time range and a reference index)
- we should offer a dropdown of a few handselected indices as reference index: NXP, SPX .. maybe a few more
- beta should be added as another column
- the score formula needs beta as third ingredient..so we need three sliders, one for each weight: stddev, mü, beta

## Deployment Setup

**Target**: Single Linux server, single user (expandable to friends later)

**Stack**:
- Apache on port 80 (serves React build + proxies /api to backend)
- Go API server on localhost:8080 (systemd service)
- PostgreSQL (system package)

**Deployment method**: Git-based (simple, transparent, easy rollback)

**Directory structure**:
```
/opt/stock-screener/          # Git repo
  ├── gofins/                 # Go backend
  ├── gofins-ui/              # React frontend
  └── update.sh               # Deployment script
/var/www/html/gofins/         # Built React files (served by Apache)
```

**Update process**:
```bash
ssh server "sudo /opt/stock-screener/update.sh"
```

**Apache config**:
- Proxy `/api/*` → `http://localhost:8080/api/*`
- Serve static files from `/var/www/html/gofins/`
- SPA fallback to `index.html`

**Systemd services**:
- `gofins-api.service` - Go backend
- Auto-restart on failure

## Multi-User Support (Minimal Concept)

**Goal**: Let a few friends use the app with separate ratings/notes/favorites

**Authentication**: Apache .htaccess with hand-edited user list (no signup, no password reset)

**User identification**:
1. Web: Apache sets `X-Remote-User` header after auth
2. CLI/Local: Read from `~/.gofins/config.yaml` (default user)
3. Go server hashes username → UUID (stable user ID)
4. Store UUID in context, use for all queries
5. UI displays username in header

**Config file** (`~/.gofins/config.yaml`):
```yaml
default_user: "yourname"  # Used for CLI commands and localhost API calls
```

**User resolution logic** (in middleware/context):
```go
func getUserID(r *http.Request) uuid.UUID {
    var username string
    
    // 1. Check X-Remote-User header (from Apache auth)
    if user := r.Header.Get("X-Remote-User"); user != "" {
        username = user
    } else {
        // 2. Fallback to config file default user
        username = config.GetDefaultUser() // reads ~/.gofins/config.yaml
    }
    
    // 3. Hash username to stable UUID
    return hashUsernameToUUID(username)
}
```

**CLI behavior**:
- All CLI commands use default user from config
- `go run . symbol profile AAPL` → uses your configured user
- `go run . rating add AAPL 5 "Great company"` → adds rating for your user
- No need to pass user flag to every command

**Database changes**:
```sql
-- Add user_id to user-specific tables
ALTER TABLE user_ratings ADD COLUMN user_id UUID NOT NULL DEFAULT '00000000-0000-0000-0000-000000000000';
ALTER TABLE user_favorites ADD COLUMN user_id UUID NOT NULL DEFAULT '00000000-0000-0000-0000-000000000000';
ALTER TABLE user_journal ADD COLUMN user_id UUID NOT NULL DEFAULT '00000000-0000-0000-0000-000000000000';

-- Add indexes
CREATE INDEX idx_user_ratings_user ON user_ratings(user_id);
CREATE INDEX idx_user_favorites_user ON user_favorites(user_id);
CREATE INDEX idx_user_journal_user ON user_journal(user_id);

-- Composite unique constraints
ALTER TABLE user_ratings DROP CONSTRAINT IF EXISTS user_ratings_pkey;
ALTER TABLE user_ratings ADD PRIMARY KEY (user_id, ticker, created_at);
ALTER TABLE user_favorites ADD UNIQUE (user_id, ticker);
```

**Code changes**:
- Middleware: Extract `X-Remote-User` → hash to UUID → store in context
- All user-specific queries: Add `WHERE user_id = $1`
- Affected endpoints: `/api/ratings/*`, `/api/favorites/*`, `/api/notes`, `/api/journal/*`
- Symbol/price/analysis data: Shared (no user_id filter)

**UI changes**:
- Show username in top-right corner
- No other changes needed

**Migration for existing data**:
```sql
-- Set all existing data to default user (you)
UPDATE user_ratings SET user_id = 'your-uuid-here';
UPDATE user_favorites SET user_id = 'your-uuid-here';
```

**Effort**: ~2-3 hours (schema changes, middleware, query updates)


