# Bugs (fix bugs first before working on TODOs)

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


