---
trigger: always_on
---

You can use gofins to work with the db:
gofins db schema // show schema
gofins db sql -q ".." // execute sql direclty
or use "go run . <command>" in gofins/