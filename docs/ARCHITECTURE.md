# System Architecture Deep Dive

This document provides a technical deep dive into the system architecture, design decisions, and implementation patterns used in this blockchain data ingestion project.

## System Overview

The system follows a **three-tier architecture** optimized for real-time data ingestion and analysis:

```
┌─────────────────────────────────────────────────────────────────────┐
│                          PRESENTATION TIER                          │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │            Next.js Dashboard (Port 3001)                     │  │
│  │  • Real-time metrics visualization                          │  │
│  │  • Paginated data preview (10 rows/page)                    │  │
│  │  • Collection control (start/stop)                          │  │
│  │  • Auto-refresh (5s metrics, 10s preview)                   │  │
│  └──────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
                               ▲
                               │ HTTP/REST
                               │
┌──────────────────────────────┼──────────────────────────────────────┐
│                    APPLICATION TIER                                 │
│                              │                                      │
│  ┌───────────────────────────┴──────────────────────────────────┐  │
│  │         FastAPI Collector (Port 8000)                        │  │
│  │  • Orchestration endpoints (/start, /stop, /status)         │  │
│  │  • Data collection threads (Bitcoin, Solana)                │  │
│  │  • Data validation and quality checks                       │  │
│  │  • Thread-safe state management                             │  │
│  └──────────────────────────────────────────────────────────────┘  │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                               │ HTTP (ClickHouse Connect)
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                           DATA TIER                                 │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │        ClickHouse Database (Port 8123)                       │  │
│  │  • Columnar storage engine                                   │  │
│  │  • Compression codecs (ZSTD, Delta, DoubleDelta)            │  │
│  │  • Optimized for analytical queries                         │  │
│  │  • 4 main tables + 1 data quality table                     │  │
│  └──────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
                               ▲
                               │
                    External Blockchain RPCs
                (Bitcoin: https://blockchain.info)
                (Solana: https://api.mainnet-beta.solana.com)
```

## Data Flow Architecture

### 1. Collection Flow (Write Path)

```
External RPC Endpoint
     │
     │ HTTPS/JSON-RPC
     ▼
Bitcoin/Solana Collector Thread
     │
     │ Parse & Validate
     ▼
Data Validator (VERACITY)
     │
     │ Check thresholds
     ▼
ClickHouse Batch Insert
     │
     │ Compressed Write
     ▼
ClickHouse Storage (MergeTree)
```

**Key Design Decisions:**

1. **Threaded Collection:** Each blockchain runs in its own thread to prevent blocking
2. **Batch Inserts:** Collect 10 records before inserting (reduces write overhead)
3. **Data Validation:** Quality checks before storage (see `data_quality` table)
4. **Compression:** ZSTD codec reduces storage by ~70%

### 2. Query Flow (Read Path)

```
Dashboard (Next.js)
     │
     │ HTTP GET
     ▼
Next.js API Route
     │
     │ ClickHouse Connect
     ▼
ClickHouse Query Engine
     │
     │ Columnar Scan
     ▼
JSON Response
     │
     │ HTTP Response
     ▼
React Component (SWR Cache)
```

**Key Design Decisions:**

1. **SWR (Stale-While-Revalidate):** Client-side caching with auto-refresh
2. **Pagination:** Client-side (10 rows/page) to reduce DOM rendering
3. **Column Selection:** Only query needed columns (reduces data transfer)
4. **Materialized Views:** Not used initially (can add for aggregations)

## Technology Choices & Rationale

### Why ClickHouse?

**Chosen Over:** PostgreSQL, MySQL, MongoDB

**Reasons:**
1. **Columnar Storage:** Perfect for analytical queries (e.g., "aggregate all fees")
2. **Compression:** Built-in codecs reduce storage 5-10x
3. **Performance:** Sub-second queries on billions of rows
4. **Time-Series Support:** Native timestamp functions and partitioning
5. **No Indexing Required:** Skips and pruning work automatically

**Trade-offs:**
- Not ACID compliant (eventual consistency)
- Not ideal for transactional workloads
- Limited UPDATE/DELETE support (designed for append-only)

### Why FastAPI (Python)?

**Chosen Over:** Express.js (Node), Flask, Django

**Reasons:**
1. **Async Support:** Non-blocking I/O for concurrent RPC calls
2. **Type Hints:** Pydantic models ensure data validation
3. **Auto Documentation:** Swagger UI at /docs
4. **Performance:** Comparable to Node.js for I/O-bound tasks
5. **Libraries:** Rich ecosystem for blockchain (web3.py, solana.py)

**Trade-offs:**
- Global Interpreter Lock (GIL) - solved with threading for I/O
- Larger container size than Node.js

### Why Next.js 16?

**Chosen Over:** React SPA, Vue.js, Streamlit

**Reasons:**
1. **Server Components:** Reduced JavaScript bundle size
2. **API Routes:** Built-in backend (no separate Express server)
3. **Turbopack:** Fast rebuilds during development
4. **Production Ready:** Standalone mode for Docker deployment
5. **TypeScript:** Type safety throughout the stack

**Trade-offs:**
- Steeper learning curve than plain React
- App Router complexity (vs Pages Router)

## ClickHouse Schema Design

### Table Design Philosophy

**Pattern:** Each table represents a single blockchain entity with time-series ordering.

```sql
CREATE TABLE bitcoin_blocks (
    block_height UInt64,           -- Primary key (sequential)
    block_hash String,              -- Unique identifier
    timestamp DateTime,             -- Event time
    ...                            -- Additional columns
    collected_at DateTime DEFAULT now()  -- Ingestion time
) ENGINE = MergeTree()
ORDER BY (timestamp, block_height);
```

**Key Decisions:**

1. **MergeTree Engine:** Best for append-only time-series data
2. **ORDER BY:** Timestamp first (common filter), then primary key
3. **No PRIMARY KEY:** ClickHouse doesn't enforce uniqueness (we handle upstream)
4. **DateTime vs DateTime64:** Second precision sufficient for blocks
5. **String vs FixedString:** Variable-length hashes use String

### Compression Strategy

**Codecs Applied:**

| Column Type | Codec | Reasoning |
|------------|-------|-----------|
| Timestamps | `CODEC(DoubleDelta, ZSTD)` | Sequential times delta-encode well |
| Counters (height, nonce) | `CODEC(Delta, ZSTD)` | Sequential integers |
| Hashes (tx_hash, block_hash) | `CODEC(ZSTD)` | Random strings, ZSTD general-purpose |
| Fees, Difficulty | `CODEC(ZSTD)` | Variable, use general compression |

**Impact:**
- Raw data: ~100GB for 1M blocks
- Compressed: ~15-20GB (80% reduction)

### Data Quality Table

```sql
CREATE TABLE data_quality (
    check_time DateTime,
    blockchain LowCardinality(String),
    metric_name LowCardinality(String),
    status String,
    details String
) ENGINE = MergeTree()
ORDER BY check_time;
```

**Purpose:** Track VERACITY violations (5th V of Big Data)

**Examples:**
- Timestamp out of range (clock skew detection)
- Negative fees (data corruption)
- Duplicate blocks (collection errors)

## API Design Patterns

### RESTful Endpoints

**Collector API (`/api/...`):**

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/start` | POST | Start data collection threads |
| `/stop` | POST | Stop collection and cleanup |
| `/status` | GET | Get collection state (is_running, start_time, counts, records_per_second) |

**Dashboard API (`/api/...`):**

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/data` | GET | Get aggregated metrics |
| `/preview/{blockchain}-{entity}` | GET | Get paginated preview (550 records) |

### Status Endpoint Response Structure

The `/status` endpoint returns comprehensive collection metrics:

```json
{
  "is_running": boolean,
  "started_at": "ISO8601 timestamp",
  "stopped_at": "ISO8601 timestamp",
  "total_records": number,
  "total_size_bytes": number,
  "records_per_second": number
}
```

**Ingestion Rate Calculation:**
- **Formula:** `total_records / elapsed_seconds`
- **Elapsed Time:**
  - If running: `now() - started_at`
  - If stopped: `stopped_at - started_at`
- **Edge Cases:** Returns `0.0` if:
  - Collection not started
  - Elapsed time < 1 second
  - Total records = 0
- **Precision:** Rounded to 2 decimal places

### State Management

**Collector State:**
- Global `is_running` flag (thread-safe with locks)
- Thread references (for clean shutdown)
- Start timestamp (for auto-stop timer)

**Dashboard State:**
- **Server:** Stateless (queries ClickHouse on demand)
- **Client:** SWR cache (stale-while-revalidate pattern)

### Error Handling Philosophy

**Principle:** Fail gracefully but alert clearly.

1. **RPC Failures:** Log error, retry with exponential backoff
2. **Database Errors:** Stop collection, return 500 error
3. **Validation Failures:** Log to `data_quality`, continue
4. **Network Errors:** Retry 3x, then pause collection

## Dashboard State Management

### SWR Pattern

```typescript
const { data, error, isLoading, mutate } = useSWR(
  '/api/status',
  fetcher,
  { refreshInterval: 5000 }  // Auto-refresh every 5s
)
```

**Benefits:**
1. **Automatic Revalidation:** Data stays fresh
2. **Cache Management:** Reduces redundant API calls
3. **Error Handling:** Built-in error states
4. **Optimistic Updates:** Mutate before API response

### Pagination State

**Decision:** Client-side pagination (not server-side)

**Rationale:**
- 550 records ~= 50KB compressed (acceptable transfer size)
- Simplifies API (no page/limit params)
- Better UX (instant page switches)
- Reduces backend query load

**Implementation:**
```typescript
const [currentPage, setCurrentPage] = useState(1)
const paginatedData = useMemo(() =>
  data.slice((currentPage - 1) * ROWS_PER_PAGE, currentPage * ROWS_PER_PAGE),
  [data, currentPage]
)
```

## Scaling Considerations

### Current Limits

- **Collection Rate:** ~1 block/10 minutes (Bitcoin), ~400ms/block (Solana)
- **Storage Growth:** ~10GB/month (both chains)
- **Query Performance:** Sub-second for up to 10M rows

### Scaling Strategies

#### 1. Horizontal Scaling (Multiple Collectors)

```
Load Balancer
     │
     ├─► Collector 1 (Bitcoin)
     ├─► Collector 2 (Solana)
     └─► Collector 3 (Ethereum)
```

**Benefits:**
- Separate failures (one chain down doesn't affect others)
- Independent scaling (Solana needs more resources)

**Challenges:**
- Distributed state management
- Database connection pooling

#### 2. ClickHouse Sharding

**When:** > 1TB data or > 100M rows/table

**Strategy:** Shard by blockchain + time range
```sql
CREATE TABLE bitcoin_blocks_distributed AS bitcoin_blocks
ENGINE = Distributed(cluster, default, bitcoin_blocks, rand())
```

#### 3. Materialized Views

**When:** Repetitive aggregations (e.g., hourly metrics)

**Example:**
```sql
CREATE MATERIALIZED VIEW bitcoin_hourly_stats
ENGINE = SummingMergeTree()
ORDER BY (hour, blockchain)
AS SELECT
    toStartOfHour(timestamp) AS hour,
    'bitcoin' AS blockchain,
    count() AS block_count,
    sum(transaction_count) AS total_transactions
FROM bitcoin_blocks
GROUP BY hour;
```

## Security Considerations

### Current Posture

**Secure:**
- Environment variables for credentials
- `.gitignore` excludes .env files
- No hardcoded secrets

**Vulnerable (Educational Context):**
- ClickHouse password in plaintext
- No authentication on dashboard
- No HTTPS/TLS encryption

### Production Recommendations

1. **Secrets Management:** Use Vault, AWS Secrets Manager
2. **Authentication:** Add JWT tokens to dashboard
3. **Authorization:** Role-based access (admin, viewer)
4. **Encryption:** TLS for all network traffic
5. **Rate Limiting:** Prevent API abuse
6. **Input Validation:** Sanitize all user inputs

## Performance Optimization

### ClickHouse Query Optimization

1. **Column Pruning:** `SELECT block_height, timestamp` not `SELECT *`
2. **WHERE Filters:** Always filter on ORDER BY columns first
3. **Limit Early:** Use `LIMIT` before expensive operations
4. **Avoid Joins:** Pre-compute or denormalize instead

### Dashboard Optimization

1. **Code Splitting:** Dynamic imports for large components
2. **Memoization:** `useMemo` for expensive computations
3. **Debouncing:** Prevent rapid API calls
4. **Virtual Scrolling:** For > 1000 rows (not needed with pagination)

### Docker Optimization

1. **Multi-stage Builds:** Reduce final image size
2. **Layer Caching:** Order commands by change frequency
3. **Build Cache:** Mount npm cache to speed up builds

## Monitoring & Observability

### Current Metrics

**Available:**
- Total records per blockchain
- Collection start/stop times
- Data size on disk
- Records per table
- Ingestion Rate (records per second)

**Missing:**
- Query latency percentiles
- Error rates and types
- RPC endpoint health
- Database connection pool stats

### Performance Metrics

**Ingestion Rate (records/sec):**
- Calculated as: `total_records / (current_time - started_at)`
- Provides real-time throughput visibility
- Helps identify:
  - RPC endpoint performance issues
  - Network bottlenecks
  - Collection efficiency
- Expected ranges:
  - Bitcoin: ~0.1-0.2 /sec (blocks every ~10 minutes)
  - Solana: ~2-5 /sec (blocks every ~400ms)
  - Combined: ~2-5 /sec aggregate

### Recommended Additions

1. **Prometheus Exporter:** Expose metrics at `/metrics`
2. **Grafana Dashboard:** Visualize time-series metrics
3. **Logging:** Structured logs with correlation IDs
4. **Alerting:** Slack/Email on collection failures

## Deployment Architecture

### Docker Compose (Current)

**Pros:**
- Simple single-command deployment
- Service dependencies managed
- Volume persistence
- Easy local development

**Cons:**
- Single-host limitation
- No automatic failover
- Manual scaling

### Kubernetes (Future)

**Recommended for Production:**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: blockchain-collector
spec:
  replicas: 3
  template:
    spec:
      containers:
      - name: collector
        image: collector:latest
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
```

**Benefits:**
- Auto-scaling
- Health checks
- Rolling updates
- Load balancing

## Lessons Learned

### What Worked Well

1. **ClickHouse Choice:** Excellent for this use case
2. **Docker Compose:** Perfect for educational deployment
3. **FastAPI Async:** Non-blocking RPC calls
4. **Type Safety:** TypeScript + Pydantic caught bugs early

### What Could Be Improved

1. **Testing:** Add unit tests for collectors
2. **Error Recovery:** Better retry logic for transient failures
3. **Configuration:** More environment variables (less hardcoding)
4. **Documentation:** API schemas with OpenAPI

### Design Trade-offs

1. **Client-side Pagination vs Server-side:**
   - Chose client-side for simplicity
   - Trade-off: Larger initial data transfer

2. **Threading vs Multiprocessing:**
   - Chose threading (I/O-bound tasks)
   - Trade-off: GIL limits CPU-bound work

3. **Real-time vs Batch:**
   - Chose real-time (educational value)
   - Trade-off: Higher complexity than batch

## Further Reading

- [ClickHouse Documentation](https://clickhouse.com/docs)
- [FastAPI Best Practices](https://fastapi.tiangolo.com/tutorial/)
- [Next.js App Router](https://nextjs.org/docs/app)
- [Bitcoin Developer Guide](https://developer.bitcoin.org/devguide/)
- [Solana Documentation](https://docs.solana.com/)
