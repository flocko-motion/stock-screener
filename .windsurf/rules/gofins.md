---
trigger: always_on
---

You can use gofins to work with the db:
gofins db schema // show schema
gofins db sql -q ".." // execute sql direclty
or use "go run . <command>" in gofins/

Always pass through context.Context - as "ctx". We want all worker threads to react to shutdown signals.

use the TODO.md in project root to see what's to be done - you can also write into it, but don't be verbose, keep it short - it's the users list,  not yours. 