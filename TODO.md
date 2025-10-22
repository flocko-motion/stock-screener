# Bugs (fix bugs first before working on TODOs)

## Weekly YoY data has N/A blocks in 2020-2021
Weekly prices show blocks of N/A YoY values during 2020-2021 period (e.g., AAPL from July 2020 to April 2021). Pattern shows every other week has N/A, suggesting missing weekly price data or calculation issue for that period. Need to investigate why YoY calculation fails for these specific weeks.

## ✅ FIXED: SymbolList select value bug

# TODO list for gofins, in order of priority

## ✅ Refactor API with Chi

## ✅ Tab "Errors"

## ✅ Tab "Notes"

## ✅ List of ratings in stock details view

## ✅ Tab "Favorites"

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

**Target**: Single Linux server with Docker

**Architecture**:
- 3 Docker containers: `gofins-ui`, `gofins-api`, `gofins-db`
- Apache reverse proxy on host (port 80) with .htaccess auth
- Systemd manages Docker containers

**Deployment method**: Git-based with Docker builds

**Directory structure**:
```
/opt/stock-screener/          # Git repo
  ├── gofins/                 # Go backend
  │   └── Dockerfile
  ├── gofins-ui/              # React frontend
  │   └── Dockerfile
  ├── docker-compose.yml
  └── deploy.sh               # Build & restart containers
```

**Deploy script** (`deploy.sh`):
```bash
#!/bin/bash
cd /opt/stock-screener
git pull
HASH=$(git rev-parse --short HEAD)
docker-compose build --build-arg GIT_HASH=$HASH
docker-compose up -d
```

**Docker containers**:
- `gofins-db`: PostgreSQL with persistent volume
- `gofins-api`: Go server on port 8080, tagged with git hash
- `gofins-ui`: Nginx serving React build, tagged with git hash

**Apache config** (on host):
- Proxy `/api/*` → `http://localhost:8080/api/*`
- Serve static files → proxy to `gofins-ui` container
- .htaccess auth sets `X-Remote-User` header

**Systemd service**:
- `gofins.service` - Manages docker-compose
- Auto-restart on failure

## ✅ Multi-User Support

All user data (ratings, favorites, notes, analyses) properly isolated per user. Uses Apache .htaccess auth (X-Remote-User header) or config file for localhost. Admin-only features (errors tab) restricted to default user.


