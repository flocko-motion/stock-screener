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

## Schema Migrations

### Adding a Column

```bash
docker-compose exec -T postgres psql -U fins -d fins -c "
ALTER TABLE symbols 
ADD COLUMN IF NOT EXISTS oldest_price TIMESTAMP WITH TIME ZONE;
"
```

### Removing a Column

```bash
docker-compose exec -T postgres psql -U fins -d fins -c "
ALTER TABLE symbols 
DROP COLUMN IF EXISTS oldest_price;
"
```

### Creating an Index

```bash
docker-compose exec -T postgres psql -U fins -d fins -c "
CREATE INDEX IF NOT EXISTS idx_symbols_oldest_price 
ON symbols(oldest_price);
"
```

## Data Queries

### View Table Statistics

```bash
# Count symbols
docker-compose exec -T postgres psql -U fins -d fins -c "
SELECT COUNT(*) as total_symbols FROM symbols;
"

# Count by type
docker-compose exec -T postgres psql -U fins -d fins -c "
SELECT type, COUNT(*) as count 
FROM symbols 
GROUP BY type;
"

# Check price data coverage
docker-compose exec -T postgres psql -U fins -d fins -c "
SELECT 
  COUNT(*) as total,
  COUNT(oldest_price) as with_price_data,
  COUNT(*) - COUNT(oldest_price) as without_price_data
FROM symbols;
"
```

### Export Data

```bash
# Export to CSV
docker-compose exec -T postgres psql -U fins -d fins -c "
COPY (SELECT * FROM symbols WHERE market_cap > 1000000000) 
TO STDOUT WITH CSV HEADER;
" > symbols_export.csv

# Create a backup
docker-compose exec -T postgres pg_dump -U fins fins > backup_$(date +%Y%m%d).sql
```

### Import Data

```bash
# Restore from backup
docker-compose exec -T postgres psql -U fins -d fins < backup_20241016.sql
```

## Useful Queries

### Find symbols without price data

```bash
docker-compose exec -T postgres psql -U fins -d fins -c "
SELECT ticker, name, inception, oldest_price
FROM symbols
WHERE oldest_price IS NULL
AND last_price_update IS NOT NULL
LIMIT 20;
"
```

### Check price history gaps

```bash
docker-compose exec -T postgres psql -U fins -d fins -c "
SELECT 
  ticker,
  inception,
  oldest_price,
  EXTRACT(YEAR FROM AGE(oldest_price, inception)) as years_gap
FROM symbols
WHERE inception IS NOT NULL 
  AND oldest_price IS NOT NULL
  AND oldest_price > inception + INTERVAL '1 year'
ORDER BY years_gap DESC
LIMIT 20;
"
```

### Database size

```bash
docker-compose exec -T postgres psql -U fins -d fins -c "
SELECT 
  pg_size_pretty(pg_database_size('fins')) as database_size,
  pg_size_pretty(pg_total_relation_size('symbols')) as symbols_table_size,
  pg_size_pretty(pg_total_relation_size('monthly_prices')) as monthly_prices_size,
  pg_size_pretty(pg_total_relation_size('weekly_prices')) as weekly_prices_size;
"
```

## Troubleshooting

### Check if database is running

```bash
docker-compose ps postgres
```

### View database logs

```bash
docker-compose logs postgres
docker-compose logs -f postgres  # Follow logs
```

### Restart database

```bash
docker-compose restart postgres
```

### Reset database (WARNING: deletes all data)

```bash
docker-compose down
rm -rf ~/.fins/postgres/data
docker-compose up -d postgres
```

## Connection Details

- **Host**: localhost
- **Port**: 5432
- **Database**: fins
- **User**: fins
- **Password**: stored in `~/.fins/config/db.env`

## psql Interactive Commands

Once inside `psql` (via `docker-compose exec postgres psql -U fins -d fins`):

```sql
\dt              -- List all tables
\d table_name    -- Describe table structure
\l               -- List all databases
\du              -- List all users
\q               -- Quit psql
\?               -- Help on psql commands
\h               -- Help on SQL commands
\timing          -- Toggle query timing
\x               -- Toggle expanded display
```
