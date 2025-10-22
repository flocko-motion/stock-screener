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

## Beta correlation

- beta correlation should be added to analysis module (can't be in profile itself, because we need to specify a time range and a reference index)
- we should offer a dropdown of a few handselected indices as reference index: NXP, SPX .. maybe a few more
- beta should be added as another column
- the score formula needs beta as third ingredient..so we need three sliders, one for each weight: stddev, mü, beta


