# Database Management

This document describes how to interact with the PostgreSQL database running in Docker.

## Quick Reference

### Connect to Database

```bash
# Interactive psql shell
docker-compose exec postgres psql -U fins -d fins

# Execute a single command
docker-compose exec -T postgres psql -U fins -d fins -c "SELECT COUNT(*) FROM symbols;"
```

### Common Commands

```bash
# List all tables
docker-compose exec -T postgres psql -U fins -d fins -c "\dt"

# Describe a table structure
docker-compose exec -T postgres psql -U fins -d fins -c "\d symbols"

# Run a SQL file
docker-compose exec -T postgres psql -U fins -d fins -f /path/to/file.sql

# Execute multi-line SQL
docker-compose exec -T postgres psql -U fins -d fins << EOF
SELECT ticker, name, market_cap 
FROM symbols 
WHERE market_cap > 1000000000 
LIMIT 10;
EOF
```

### as a subcommand

use "gofins db schema" or "go run . db schema" in gofins/ to print the db schema.