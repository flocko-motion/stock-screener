# Bugs (fix bugs first bofore working on TODOs)

## A JS bug in gofins-ui
SymbolList.tsx:318 The `value` prop supplied to <select> must be a scalar value if `multiple` is false.

Check the render method of `SymbolList`.
SymbolList.tsx:326 The `value` prop supplied to <select> must be a scalar value if `multiple` is false.

Check the render method of `SymbolList`.
SymbolList.tsx:334 The `value` prop supplied to <select> must be a scalar value if `multiple` is false.

Check the render method of `SymbolList`.
client:865 [vite] server connection lost. Polling for restart...
Navigated to chrome-error://chromewebdata/
Navigated to http://localhost:5173/
react-dom_client.js?v=7cfb0357:20101 Download the React DevTools for a better development experience: https://react.dev/link/react-devtools
SymbolList.tsx:318 The `value` prop supplied to <select> must be a scalar value if `multiple` is false.

Check the render method of `SymbolList`.
SymbolList.tsx:326 The `value` prop supplied to <select> must be a scalar value if `multiple` is false.

Check the render method of `SymbolList`.
SymbolList.tsx:334 The `value` prop supplied to <select> must be a scalar value if `multiple` is false.

Check the render method of `SymbolList`.
﻿


# TODO list for gofins, in order of priority

## ✅ Refactor API with Chi
- DONE: Migrated to Chi router
- DONE: Added /api/errors endpoints (GET list, DELETE clear)
- TODO: Create UI tab for errors

## Tab "Errors"
- Show recent errors from database
- Button to clear all errors
- Auto-refresh every 30s


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


