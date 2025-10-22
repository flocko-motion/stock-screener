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


## Tab "Notes"

- another tab for notes sorted by time they were taken.. to see what was noted down recently

## Tab "Favorites"

- tab by favourites sorted by rating
- same filter box as standard stocks list
- filter box should be made foldable, so that it doesn't take up too much space in a default view

## Beta correlation

- beta correlation should be added to analysis module (can't be in profile itself, because we need to specify a time range and a reference index)
- we should offer a dropdown of a few handselected indices as reference index: NXP, SPX .. maybe a few more
- beta should be added as another column
- the score formula needs beta as third ingredient..so we need three sliders, one for each weight: stddev, mü, beta


