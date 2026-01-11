# Troubleshooting Guide

This guide helps resolve common issues when running the blockchain data ingestion system.

## Quick Diagnostic Commands

```bash
# Check if all services are running
docker compose ps

# View logs for all services
docker compose logs

# View logs for specific service
docker compose logs collector
docker compose logs dashboard
docker compose logs clickhouse

# Check ClickHouse connectivity
curl -u default:clickhouse_password "http://localhost:8123/?query=SELECT%201"

# Check collector API
curl http://localhost:8000

# Check dashboard
curl http://localhost:3001
```

## Common Issues

### 1. Docker Issues

#### Problem: `docker compose` command not found

**Error:**
```
docker: 'compose' is not a docker command.
```

**Solution:**
- Update Docker Desktop to version 4.0+ (includes Compose V2)
- Or use legacy command: `docker-compose` (with hyphen)

**Verify Docker Version:**
```bash
docker --version  # Should be 20.10+
docker compose version  # Should be 2.0+
```

#### Problem: Port already in use

**Error:**
```
Error starting userland proxy: listen tcp4 0.0.0.0:3001: bind: address already in use
```

**Solution 1:** Stop conflicting service
```bash
# Find process using port 3001
lsof -i :3001
# OR on Windows
netstat -ano | findstr :3001

# Kill the process
kill -9 <PID>
```

**Solution 2:** Change port in docker-compose.yml
```yaml
dashboard:
  ports:
    - "3002:3000"  # Change 3001 to 3002
```

#### Problem: Not enough memory

**Error:**
```
ClickHouse died unexpectedly
collector exited with code 137
```

**Solution:**
1. Increase Docker memory allocation:
   - Docker Desktop → Preferences → Resources
   - Set memory to at least 8GB (16GB recommended)

2. Reduce collection interval:
   ```bash
   # In .env file
   COLLECTION_INTERVAL_SECONDS=120  # Change from 60 to 120
   ```

3. Limit collection time:
   ```bash
   MAX_COLLECTION_TIME_MINUTES=5  # Change from 10 to 5
   ```

### 2. Database Issues

#### Problem: ClickHouse won't start

**Error:**
```
clickhouse-1  | DB::Exception: Cannot create database
```

**Solution:**
1. **Clean database files:**
   ```bash
   docker compose down
   sudo rm -rf data/clickhouse/*
   docker compose up -d
   ```

2. **Check disk space:**
   ```bash
   df -h  # Ensure > 10GB free
   ```

3. **Check file permissions:**
   ```bash
   ls -la data/clickhouse/
   # Should be writable by Docker user
   ```

#### Problem: Can't connect to ClickHouse

**Error:**
```
Connection refused (localhost:8123)
```

**Solution:**
1. **Verify ClickHouse is running:**
   ```bash
   docker compose ps clickhouse
   # Should show "Up"
   ```

2. **Test connection:**
   ```bash
   curl -u default:clickhouse_password "http://localhost:8123/?query=SELECT%201"
   # Should return: 1
   ```

3. **Check logs:**
   ```bash
   docker compose logs clickhouse | tail -50
   ```

#### Problem: Database schema not created

**Symptoms:**
- Dashboard shows "No data available"
- Collector logs show "Table doesn't exist"

**Solution:**
```bash
# Restart ClickHouse to run init scripts
docker compose restart clickhouse

# Wait 10 seconds, then verify tables exist
docker compose exec clickhouse clickhouse-client --password clickhouse_password --query "SHOW TABLES"
# Should show: bitcoin_blocks, bitcoin_transactions, solana_blocks, solana_transactions, data_quality
```

### 3. Collector Issues

#### Problem: Collector fails to start

**Error:**
```
ModuleNotFoundError: No module named 'fastapi'
```

**Solution:**
```bash
# Rebuild collector image
docker compose build collector
docker compose up -d collector
```

#### Problem: RPC endpoint failures

**Error in logs:**
```
Error fetching Bitcoin block: Connection timeout
```

**Solutions:**

1. **Check internet connection:**
   ```bash
   ping blockchain.info  # Bitcoin RPC
   ping api.mainnet-beta.solana.com  # Solana RPC
   ```

2. **Use alternative RPC:**
   ```bash
   # In .env file
   BITCOIN_RPC_URL=https://blockstream.info/api
   SOLANA_RPC_URL=https://solana-api.projectserum.com
   ```

3. **Increase timeout:**
   ```bash
   # In collector/main.py, increase timeout
   response = requests.get(url, timeout=30)  # Changed from 10 to 30
   ```

#### Problem: Collection stops unexpectedly

**Symptoms:**
- "is_running" shows true but no new data
- Collector logs show no activity

**Solution:**
```bash
# Manually stop collection
curl -X POST http://localhost:8000/api/stop

# Restart collector
docker compose restart collector

# Start collection again via dashboard
```

### 4. Dashboard Issues

#### Problem: Dashboard shows blank page

**Symptoms:**
- Browser shows white screen
- Console shows JavaScript errors

**Solution 1:** Clear browser cache
```
Chrome: Cmd+Shift+R (Mac) or Ctrl+Shift+R (Windows)
Firefox: Cmd+Shift+Delete (Mac) or Ctrl+Shift+Delete (Windows)
```

**Solution 2:** Rebuild dashboard
```bash
docker compose build dashboard
docker compose up -d dashboard
```

**Solution 3:** Check browser console
```
F12 → Console tab
Look for error messages
```

#### Problem: Dashboard not updating

**Symptoms:**
- Dashboard loads but data doesn't refresh
- Metrics stuck at old values

**Solution:**
1. **Check SWR refresh:**
   - Open DevTools → Network tab
   - Should see requests every 5-10 seconds

2. **Force refresh:**
   - Click browser refresh button
   - Or clear cache (Cmd/Ctrl + Shift + R)

3. **Verify backend is running:**
   ```bash
   curl http://localhost:3001/api/status
   # Should return JSON with is_running, etc.
   ```

#### Problem: Pagination not working

**Symptoms:**
- Next/Previous buttons don't respond
- All records shown on one page

**Solution:**
```bash
# Check browser console for errors
# F12 → Console

# Verify component is loaded
# Should see < 10 rows per table if data > 10

# Rebuild dashboard if needed
docker compose build dashboard
docker compose up -d dashboard
```

### 5. Data Collection Issues

#### Problem: No data being collected

**Symptoms:**
- All metrics show 0
- "No data available" in preview tables

**Diagnostic Steps:**
1. **Check collection status:**
   ```bash
   curl http://localhost:8000/api/status
   # is_running should be true
   ```

2. **Check collector logs:**
   ```bash
   docker compose logs collector --tail=100
   # Look for "Collected Bitcoin block" messages
   ```

3. **Verify database tables:**
   ```bash
   docker compose exec clickhouse clickhouse-client --password clickhouse_password --query "SELECT count() FROM bitcoin_blocks"
   # Should be > 0 after a few minutes
   ```

**Solution:**
```bash
# Restart entire system
docker compose down
docker compose up -d

# Start collection
# Go to http://localhost:3001 and click Start button
```

#### Problem: Data collection very slow

**Symptoms:**
- Only a few records after many minutes
- Bitcoin blocks not incrementing

**Explanation:**
- Bitcoin blocks are mined every ~10 minutes (by design)
- This is NOT a bug - it's how Bitcoin works

**To See Faster Collection:**
1. Use Solana (new block every ~400ms)
2. Or query historical Bitcoin data in exercises

#### Problem: Duplicate data

**Symptoms:**
- Same block appears multiple times
- Record counts don't match blockchain

**Solution:**
1. **Check data quality table:**
   ```sql
   SELECT * FROM data_quality WHERE status = 'ERROR'
   ORDER BY check_time DESC LIMIT 10;
   ```

2. **Stop and clean:**
   ```bash
   # Stop collection
   docker compose down

   # Remove duplicate data
   ./scripts/cleanup.sh

   # Restart fresh
   docker compose up -d
   ```

### 6. Metrics Issues

#### Problem: Ingestion Rate shows 0.00 /sec

**Symptoms:**
- "Ingestion Rate" card displays "0.00 /sec"
- Collection is running
- Total Records is increasing

**Causes:**
1. **Collection just started** (elapsed time < 1 second)
2. **No records collected yet** (waiting for first blockchain response)
3. **Timestamp synchronization issue** (system clock skew)

**Solution:**
1. **Wait 2-3 seconds:**
   - Metric updates every 5 seconds
   - Initial calculation may show 0 briefly

2. **Verify collection is actually running:**
   ```bash
   curl http://localhost:8000/api/status
   # Check "is_running": true
   ```

3. **Check collector logs:**
   ```bash
   docker compose logs collector --tail=20
   # Look for "Collected Bitcoin block" or "Collected Solana block" messages
   ```

4. **Verify database connection:**
   ```bash
   docker compose exec clickhouse clickhouse-client --password clickhouse_password --query "SELECT count() FROM collection_state"
   # Should return: 1
   ```

#### Problem: Ingestion Rate seems too high or too low

**Symptoms:**
- Ingestion Rate shows 100+ /sec (unexpectedly high)
- Or shows 0.001 /sec (unexpectedly low)

**Diagnostic Steps:**
1. **Manual calculation:**
   ```sql
   SELECT
       total_records,
       dateDiff('second', started_at, now()) as elapsed,
       round(total_records / dateDiff('second', started_at, now()), 2) as manual_rate
   FROM collection_state
   WHERE id = 1;
   ```

2. **Compare with API:**
   ```bash
   curl http://localhost:8000/api/status | grep records_per_second
   ```

3. **Check for timestamp issues:**
   - Ensure Docker container time matches host time
   - Check for clock skew: `docker compose exec collector date`

**Expected Rates:**
- Bitcoin only: 0.1-0.2 records/sec (blocks mined every ~10 min)
- Solana only: 2-5 records/sec (blocks produced every ~400ms)
- Both combined: 2-5 records/sec aggregate

### 7. Performance Issues

#### Problem: Queries are slow

**Symptoms:**
- Dashboard takes > 5 seconds to load
- Preview tables timeout

**Solution:**
1. **Check data volume:**
   ```sql
   SELECT
       table,
       sum(rows) as total_rows,
       formatReadableSize(sum(bytes_on_disk)) as size
   FROM system.parts
   WHERE database = 'default'
   GROUP BY table;
   ```

2. **If > 1M rows, add indexes:**
   ```sql
   -- Example: Add index on timestamp
   ALTER TABLE bitcoin_blocks
   ADD INDEX idx_timestamp timestamp TYPE minmax GRANULARITY 3;
   ```

3. **Reduce refresh interval:**
   ```typescript
   // In dashboard/app/hooks/usePreviewData.ts
   refreshInterval: 30000,  // Change from 10000 to 30000 (30s)
   ```

#### Problem: High memory usage

**Symptoms:**
- Docker Desktop shows > 12GB memory use
- System becomes slow

**Solution:**
1. **Limit collection:**
   ```bash
   # In .env
   MAX_COLLECTION_TIME_MINUTES=3
   MAX_DATA_SIZE_GB=2
   ```

2. **Reduce batch size:**
   ```python
   # In collector/*.py
   batch_size = 5  # Change from 10 to 5
   ```

3. **Restart services:**
   ```bash
   docker compose restart
   ```

### 8. Environment Issues

#### Problem: .env file not found

**Error:**
```
Error: .env file not found
```

**Solution:**
```bash
# Copy template
cp .env.example .env

# Verify it exists
ls -la .env
```

#### Problem: Environment variables not loading

**Symptoms:**
- Collector uses default values
- RPC endpoints not configured

**Solution:**
```bash
# Restart services to reload .env
docker compose down
docker compose up -d

# Verify variables are loaded
docker compose exec collector env | grep BITCOIN
```

### 9. Network Issues

#### Problem: Can't access dashboard

**Error:**
```
This site can't be reached
localhost refused to connect
```

**Solution:**
1. **Check if dashboard is running:**
   ```bash
   docker compose ps dashboard
   # Should show "Up" not "Exited"
   ```

2. **Check logs:**
   ```bash
   docker compose logs dashboard
   ```

3. **Try different port:**
   ```bash
   # If 3001 doesn't work, try 3000
   docker compose exec dashboard sh -c "netstat -tuln"
   ```

#### Problem: RPC rate limiting

**Error in logs:**
```
429 Too Many Requests
```

**Solution:**
1. **Increase collection interval:**
   ```bash
   # In .env
   COLLECTION_INTERVAL_SECONDS=120  # Slow down requests
   ```

2. **Use paid RPC endpoint:**
   ```bash
   # Get free API key from Alchemy or Infura
   BITCOIN_RPC_URL=https://eth-mainnet.alchemyapi.io/v2/YOUR_KEY
   ```

## Getting Help

### 1. Check Logs First

Always check logs before asking for help:
```bash
# All services
docker compose logs --tail=100

# Specific service with timestamps
docker compose logs -f --timestamps collector
```

### 2. Verify System Requirements

```bash
# Docker version
docker --version  # Need 20.10+

# Docker Compose version
docker compose version  # Need 2.0+

# Available memory
docker info | grep Memory  # Need 8GB+

# Disk space
df -h  # Need 10GB+
```

### 3. Try Clean Restart

```bash
# Stop everything
docker compose down

# Remove old data
./scripts/cleanup.sh

# Start fresh
docker compose up -d

# Wait 30 seconds
sleep 30

# Open dashboard
open http://localhost:3001
```

### 4. Report Issues

If problem persists, create a GitHub issue with:

1. **Error message** (full text from logs)
2. **Steps to reproduce**
3. **System info:**
   ```bash
   docker --version
   docker compose version
   uname -a  # OS info
   ```
4. **Logs:**
   ```bash
   docker compose logs > logs.txt
   ```

## Prevention Tips

### 1. Regular Maintenance

```bash
# Weekly: Clean old images
docker system prune -a

# Monthly: Backup ClickHouse data
tar -czf clickhouse-backup.tar.gz data/clickhouse/
```

### 2. Monitor Resources

```bash
# Check Docker stats
docker stats

# Should see:
# - ClickHouse: < 4GB memory
# - Collector: < 500MB memory
# - Dashboard: < 200MB memory
```

### 3. Stay Updated

```bash
# Pull latest images
docker compose pull

# Rebuild after updates
docker compose build --no-cache
docker compose up -d
```

## Common Student Mistakes

### 1. Forgetting to start collection

**Symptom:** Dashboard shows 0 records

**Fix:** Click "Start Collection" button in dashboard

### 2. Expecting instant results

**Reminder:** Bitcoin blocks take ~10 minutes. Be patient!

### 3. Not copying .env.example

**Fix:** Always run `cp .env.example .env` first

### 4. Running out of disk space

**Prevention:** Set `MAX_DATA_SIZE_GB=3` in .env

### 5. Not reading error messages

**Tip:** Logs contain helpful error messages. Read them!

## Still Stuck?

1. Review the main [README.md](../README.md)
2. Check [EXERCISES.md](EXERCISES.md) for examples
3. Search [GitHub Issues](https://github.com/YOUR_REPO/issues)
4. Ask in class or office hours
