# Quick Start Reference

One-page command reference for the blockchain data ingestion system.

## Initial Setup

```bash
# Clone repository
git clone https://github.com/YOUR_USERNAME/big_data_architecture.git
cd big_data_architecture

# Copy environment template
cp .env.example .env

# Start all services
docker compose up -d

# Wait 30 seconds for services to initialize
sleep 30

# Open dashboard
open http://localhost:3001  # Mac
# OR
start http://localhost:3001  # Windows
```

## Essential Commands

### Docker Operations

```bash
# Start all services (detached)
docker compose up -d

# Start and view logs
docker compose up

# Stop all services
docker compose down

# Restart specific service
docker compose restart collector

# View logs
docker compose logs -f collector  # Follow logs
docker compose logs --tail=100    # Last 100 lines

# Check status
docker compose ps

# Rebuild after code changes
docker compose build
docker compose up -d
```

### Data Collection

```bash
# Start collection (via dashboard)
# Go to http://localhost:3001 and click "Start Collection"

# OR via API
curl -X POST http://localhost:8000/api/start

# Stop collection
curl -X POST http://localhost:8000/api/stop

# Check status
curl http://localhost:8000/api/status
```

### Database Queries

```bash
# Connect to ClickHouse client
docker compose exec clickhouse clickhouse-client --password clickhouse_password

# Run single query
docker compose exec clickhouse clickhouse-client --password clickhouse_password \
  --query "SELECT count() FROM bitcoin_blocks"

# Query via HTTP
curl -u default:clickhouse_password \
  "http://localhost:8123/?query=SELECT%20count()%20FROM%20bitcoin_blocks"
```

### Common Queries

```sql
-- Count records
SELECT count() FROM bitcoin_blocks;
SELECT count() FROM solana_transactions;

-- Latest blocks
SELECT * FROM bitcoin_blocks ORDER BY timestamp DESC LIMIT 10;
SELECT * FROM solana_blocks ORDER BY timestamp DESC LIMIT 10;

-- Aggregation
SELECT
    toStartOfHour(timestamp) AS hour,
    count() AS blocks,
    sum(transaction_count) AS transactions
FROM bitcoin_blocks
GROUP BY hour
ORDER BY hour DESC
LIMIT 24;

-- Data size
SELECT
    table,
    sum(rows) as rows,
    formatReadableSize(sum(bytes_on_disk)) as size
FROM system.parts
WHERE database = 'default'
GROUP BY table;
```

## Key Endpoints

| Service | URL | Purpose |
|---------|-----|---------|
| Dashboard | http://localhost:3001 | Real-time monitoring UI |
| Collector API | http://localhost:8000 | Data collection API |
| Collector Docs | http://localhost:8000/docs | Auto-generated API docs |
| ClickHouse HTTP | http://localhost:8123 | Database HTTP interface |
| ClickHouse Client | Port 9000 | Native protocol (TCP) |

## API Response Examples

### Status Endpoint

```bash
curl http://localhost:8000/api/status
```

**Response:**
```json
{
  "is_running": true,
  "started_at": "2026-01-10T14:30:00Z",
  "stopped_at": null,
  "total_records": 15432,
  "total_size_bytes": 2147483648,
  "records_per_second": 12.45
}
```

**Field Descriptions:**
- `is_running`: Whether collection is currently active
- `started_at`: ISO8601 timestamp when collection started
- `stopped_at`: ISO8601 timestamp when collection stopped (null if running)
- `total_records`: Total count across all blockchain tables
- `total_size_bytes`: Compressed storage size in ClickHouse
- `records_per_second`: Average ingestion rate since collection started

## Ports Reference

```
3001 → Dashboard (Next.js)
8000 → Collector API (FastAPI)
8123 → ClickHouse HTTP
9000 → ClickHouse Native (TCP)
```

## Quick Troubleshooting

```bash
# Problem: Port already in use
lsof -i :3001  # Find process
kill -9 <PID>  # Kill process

# Problem: Service won't start
docker compose logs <service-name>

# Problem: Out of memory
docker stats  # Check resource usage
# Increase Docker memory: Docker Desktop → Preferences → Resources

# Problem: Database won't start
docker compose down
sudo rm -rf data/clickhouse/*
docker compose up -d

# Problem: No data collecting
# 1. Check logs: docker compose logs collector
# 2. Verify status: curl http://localhost:8000/api/status
# 3. Start collection: Click "Start" in dashboard
```

## File Locations

```
big_data_architecture/
├── README.md              # Main documentation
├── docker-compose.yml     # Service orchestration
├── .env                   # Your local config (copy from .env.example)
├── docs/
│   ├── EXERCISES.md       # Hands-on exercises
│   ├── GLOSSARY.md        # Terminology reference
│   ├── SAMPLE_QUERIES.md  # Query examples
│   ├── ARCHITECTURE.md    # Technical deep dive
│   └── TROUBLESHOOTING.md # Error solutions
├── collector/
│   ├── main.py            # FastAPI app
│   └── collectors/        # Bitcoin & Solana collectors
├── dashboard/
│   ├── app/page.tsx       # Main dashboard
│   └── app/api/           # API routes
└── data/
    └── clickhouse/        # Database files (auto-created)
```

## Environment Variables

Key variables in `.env`:

```bash
# Database
CLICKHOUSE_USER=default
CLICKHOUSE_PASSWORD=clickhouse_password
CLICKHOUSE_DB=default

# Collection Settings
COLLECTION_INTERVAL_SECONDS=60
MAX_COLLECTION_TIME_MINUTES=10
MAX_DATA_SIZE_GB=5

# RPC Endpoints (optional - has defaults)
BITCOIN_RPC_URL=https://blockchain.info
SOLANA_RPC_URL=https://api.mainnet-beta.solana.com
```

## Development Workflow

```bash
# Make code changes
# ...

# Rebuild affected service
docker compose build collector  # or dashboard

# Restart to apply changes
docker compose up -d collector

# View logs
docker compose logs -f collector

# Test changes
curl http://localhost:8000/api/status
open http://localhost:3001
```

## Data Management

```bash
# View data size
du -sh data/clickhouse/

# Backup database
tar -czf clickhouse-backup-$(date +%Y%m%d).tar.gz data/clickhouse/

# Complete cleanup (removes all data)
docker compose down
./scripts/cleanup.sh
# OR manually:
sudo rm -rf data/clickhouse/*

# Start fresh
docker compose up -d
```

## Testing Queries

```bash
# Use ClickHouse client
docker compose exec clickhouse clickhouse-client --password clickhouse_password

# Inside client (clickhouse-client>)
USE default;                                    # Select database
SHOW TABLES;                                    # List tables
DESCRIBE bitcoin_blocks;                        # Show schema
SELECT count() FROM bitcoin_blocks;             # Count records
SELECT * FROM bitcoin_blocks LIMIT 5;           # Preview data
\q                                             # Exit client
```

## Performance Monitoring

```bash
# Docker resource usage
docker stats

# Database queries
docker compose exec clickhouse clickhouse-client --password clickhouse_password \
  --query "SELECT query, elapsed, formatReadableSize(memory_usage) as memory \
           FROM system.query_log \
           WHERE type = 'QueryFinish' \
           ORDER BY event_time DESC LIMIT 10"

# Disk usage
docker compose exec clickhouse du -sh /var/lib/clickhouse/
```

## Useful Aliases

Add to your `~/.bashrc` or `~/.zshrc`:

```bash
# Navigation
alias bda='cd ~/path/to/big_data_architecture'

# Docker shortcuts
alias dcup='docker compose up -d'
alias dcdown='docker compose down'
alias dclogs='docker compose logs -f'
alias dcps='docker compose ps'

# ClickHouse client
alias ch='docker compose exec clickhouse clickhouse-client --password clickhouse_password'

# Quick queries
alias btccount='docker compose exec clickhouse clickhouse-client --password clickhouse_password --query "SELECT count() FROM bitcoin_blocks"'
alias solcount='docker compose exec clickhouse clickhouse-client --password clickhouse_password --query "SELECT count() FROM solana_blocks"'
```

## Next Steps

1. Review [EXERCISES.md](EXERCISES.md) for hands-on practice
2. Explore [SAMPLE_QUERIES.md](SAMPLE_QUERIES.md) for query patterns
3. Read [ARCHITECTURE.md](ARCHITECTURE.md) for technical details
4. Check [TROUBLESHOOTING.md](TROUBLESHOOTING.md) if issues arise

## Quick Links

- Main Documentation: [README.md](../README.md)
- Exercises: [EXERCISES.md](EXERCISES.md)
- Glossary: [GLOSSARY.md](GLOSSARY.md)
- Sample Queries: [SAMPLE_QUERIES.md](SAMPLE_QUERIES.md)
- Architecture: [ARCHITECTURE.md](ARCHITECTURE.md)
- Troubleshooting: [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
- Contributing: [CONTRIBUTING.md](../CONTRIBUTING.md)
