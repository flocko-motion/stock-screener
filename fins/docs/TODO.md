# Column Commands 
- Bundle all column commands into dsl/commands/column
- Make sure, that commands are correctly categorized (column commands add columns to a basket!)
- open question: filter/sort are implicitly adding columns (if they act on a not-yet-existing column!), does that make them column commands?

# Command organisation
- Essential commands that implement the language syntax should be in the man commands/ folder. Plugin commands that add additional functions that are not essential, should be in subfolders... e.g. column commands. That speaks for having filter/sort in the main folder and all the additional column generators in /column/


