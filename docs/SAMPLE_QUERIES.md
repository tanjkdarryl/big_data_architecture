# Sample Queries for Blockchain Data Exploration

This document provides a comprehensive set of SQL queries for exploring and analyzing Bitcoin and Solana blockchain data collected in ClickHouse. These queries are designed to help students understand data analysis patterns and gain insights into blockchain activity.

## Table of Contents

1. [Basic Queries](#basic-queries)
2. [Aggregation Queries](#aggregation-queries)
3. [Time-Series Analysis](#time-series-analysis)
4. [Cross-Chain Comparisons](#cross-chain-comparisons)
5. [Advanced Analytics](#advanced-analytics)
6. [Pagination and Data Quality](#pagination-and-data-quality)

---

## Basic Queries

### View Recent Bitcoin Blocks

```sql
SELECT 
    block_height,
    block_hash,
    timestamp,
    transaction_count,
    size,
    weight
FROM bitcoin_blocks
ORDER BY block_height DESC
LIMIT 10;
```

### Check Solana Transaction Status Distribution

```sql
SELECT 
    status,
    count() AS count
FROM solana_transactions
GROUP BY status;
```

---

## Aggregation Queries

### Bitcoin Transaction Fee Statistics

```sql
SELECT 
    min(fee) AS min_fee,
    max(fee) AS max_fee,
    avg(fee) AS avg_fee,
    median(fee) AS median_fee,
    sum(fee) AS total_fees
FROM bitcoin_transactions;
```

### Average Transactions Per Block by Blockchain

```sql
SELECT
    'Bitcoin' AS blockchain,
    avg(transaction_count) AS avg_tx_per_block
FROM bitcoin_blocks

UNION ALL

SELECT
    'Solana' AS blockchain,
    avg(transaction_count) AS avg_tx_per_block
FROM solana_blocks;
```

---

## Time-Series Analysis

### Bitcoin Transaction Volume by Day

```sql
SELECT 
    toDate(timestamp) AS day,
    count() AS transaction_count,
    sum(fee) AS total_fees,
    avg(fee) AS avg_fee
FROM bitcoin_transactions
GROUP BY day
ORDER BY day;
```

### Solana Success Rate Over Time

```sql
SELECT 
    toStartOfHour(timestamp) AS hour,
    countIf(status = 'success') AS successful,
    countIf(status = 'failed') AS failed,
    (countIf(status = 'success') * 100.0 / count()) AS success_rate_percent
FROM solana_transactions
GROUP BY hour
ORDER BY hour;
```

---

## Cross-Chain Comparisons

### Block Production Rate Comparison

```sql
WITH bitcoin_rate AS (
    SELECT
        'Bitcoin' AS chain,
        count() / (max(timestamp) - min(timestamp)) * 3600 AS blocks_per_hour
    FROM bitcoin_blocks
),
solana_rate AS (
    SELECT
        'Solana' AS chain,
        count() / (max(timestamp) - min(timestamp)) * 3600 AS blocks_per_hour
    FROM solana_blocks
)
SELECT * FROM bitcoin_rate
UNION ALL
SELECT * FROM solana_rate;
```

### Transaction Throughput Comparison

```sql
SELECT
    'Bitcoin' AS blockchain,
    count() AS total_transactions,
    count() / (max(timestamp) - min(timestamp)) AS tx_per_second
FROM bitcoin_transactions

UNION ALL

SELECT
    'Solana' AS blockchain,
    count() AS total_transactions,
    count() / (max(timestamp) - min(timestamp)) AS tx_per_second
FROM solana_transactions;
```

### Data Collection Performance by Source

```sql
SELECT 
    source,
    count() AS collection_events,
    sum(records_collected) AS total_records,
    avg(collection_duration_ms) AS avg_duration_ms,
    sum(error_count) AS total_errors,
    (sum(error_count) * 100.0 / count()) AS error_rate_percent
FROM collection_metrics
GROUP BY source
ORDER BY total_records DESC;
```

### Verify API's Ingestion Rate Calculation

Compare the API's `records_per_second` value with database calculations:

```sql
-- Calculate ingestion rate from collection_state table
SELECT
    total_records,
    started_at,
    CASE
        WHEN is_running = 1 THEN now()
        ELSE stopped_at
    END as end_time,
    dateDiff('second', started_at,
        CASE WHEN is_running = 1 THEN now() ELSE stopped_at END
    ) as elapsed_seconds,
    round(total_records * 1.0 / dateDiff('second', started_at,
        CASE WHEN is_running = 1 THEN now() ELSE stopped_at END
    ), 2) as calculated_records_per_second
FROM collection_state
WHERE id = 1;
```

**Verification:**
1. Run this query in ClickHouse
2. Check API response: `curl http://localhost:8000/api/status`
3. Compare `calculated_records_per_second` (SQL) with `records_per_second` (API)
4. They should match (within rounding differences)

**Example Output:**
```
total_records: 15432
elapsed_seconds: 1234
calculated_records_per_second: 12.51
```

API response should show: `"records_per_second": 12.51`

---

## Advanced Analytics

### Bitcoin Block Size Analysis

```sql
SELECT 
    toDate(timestamp) AS day,
    avg(size) AS avg_size_bytes,
    avg(weight) AS avg_weight,
    max(size) AS max_size_bytes,
    avg(transaction_count) AS avg_tx_count
FROM bitcoin_blocks
GROUP BY day
ORDER BY day;
```

### Solana Slot Time Distribution

```sql
SELECT 
    slot,
    timestamp,
    timestamp - lagInFrame(timestamp) OVER (ORDER BY slot) AS time_since_previous_slot
FROM solana_blocks
ORDER BY slot DESC
LIMIT 100;
```

### Calculate Total Data Volume by Table

```sql
SELECT 
    table,
    sum(rows) AS total_rows,
    formatReadableSize(sum(bytes)) AS uncompressed_size,
    formatReadableSize(sum(bytes_on_disk)) AS compressed_size,
    round((1 - sum(bytes_on_disk) / sum(bytes)) * 100, 2) AS compression_ratio_percent
FROM system.parts
WHERE database = 'blockchain_data' AND active = 1
GROUP BY table
ORDER BY sum(bytes) DESC;
```

### Collection Metrics Summary

```sql
SELECT 
    source,
    min(metric_time) AS first_collection,
    max(metric_time) AS last_collection,
    sum(records_collected) AS total_records,
    avg(collection_duration_ms) AS avg_duration_ms,
    sum(error_count) AS total_errors
FROM collection_metrics
GROUP BY source;
```

---

## Pagination and Data Quality

### Paginated Results (Server-Side Pattern)

When implementing server-side pagination, use `LIMIT` and `OFFSET` to fetch specific pages:

```sql
-- Page 1: First 10 records
SELECT
    block_height,
    block_hash,
    timestamp,
    transaction_count
FROM bitcoin_blocks
ORDER BY timestamp DESC
LIMIT 10 OFFSET 0;

-- Page 2: Records 11-20
SELECT
    block_height,
    block_hash,
    timestamp,
    transaction_count
FROM bitcoin_blocks
ORDER BY timestamp DESC
LIMIT 10 OFFSET 10;

-- Page 3: Records 21-30
SELECT
    block_height,
    block_hash,
    timestamp,
    transaction_count
FROM bitcoin_blocks
ORDER BY timestamp DESC
LIMIT 10 OFFSET 20;

-- General formula: OFFSET = (page_number - 1) * rows_per_page
```

### Calculate Total Pages

To show pagination controls, calculate the total number of pages:

```sql
SELECT
    count() AS total_records,
    ceil(count() / 10.0) AS total_pages_for_10_per_page,
    ceil(count() / 25.0) AS total_pages_for_25_per_page,
    ceil(count() / 50.0) AS total_pages_for_50_per_page
FROM bitcoin_transactions;
```

### Optimal Page Size Based on Data Size

Calculate the ideal page size based on average row byte size (targeting 4KB response):

```sql
SELECT
    'bitcoin_blocks' AS table_name,
    count() AS total_rows,
    avg(length(toString(block_hash)) +
        length(toString(timestamp)) +
        8 + 8 + 4 + 4 + 4) AS avg_row_bytes,
    ceil(4096 / avg(length(toString(block_hash)) +
        length(toString(timestamp)) +
        8 + 8 + 4 + 4 + 4)) AS optimal_page_size_for_4kb
FROM bitcoin_blocks
LIMIT 1000;

-- Apply to transactions table
SELECT
    'solana_transactions' AS table_name,
    count() AS total_rows,
    avg(length(toString(signature)) +
        length(toString(timestamp)) +
        length(toString(signer)) +
        8 + 4) AS avg_row_bytes,
    ceil(4096 / avg(length(toString(signature)) +
        length(toString(timestamp)) +
        length(toString(signer)) +
        8 + 4)) AS optimal_page_size_for_4kb
FROM solana_transactions
LIMIT 1000;
```

### Client-Side Pagination (Fetch All, Paginate in UI)

When dataset is small enough (< 1000 rows), fetch all records and paginate client-side:

```sql
-- Fetch all recent records (dashboard uses this approach)
SELECT
    block_height,
    block_hash,
    timestamp,
    transaction_count,
    size,
    weight
FROM bitcoin_blocks
ORDER BY timestamp DESC
LIMIT 550;  -- Fetch enough for ~55 pages at 10 rows/page
```

**Advantages of Client-Side Pagination:**
- Instant page transitions (no API calls)
- Reduced backend query load
- Simpler API design

**Trade-offs:**
- Larger initial data transfer
- Not suitable for very large datasets

### Data Quality Checks

Query the `data_quality` table to identify issues:

```sql
-- View all data quality issues
SELECT
    check_time,
    blockchain,
    metric_name,
    status,
    details
FROM data_quality
WHERE status = 'ERROR'
ORDER BY check_time DESC
LIMIT 20;

-- Count issues by blockchain
SELECT
    blockchain,
    metric_name,
    count() AS issue_count
FROM data_quality
WHERE status = 'ERROR'
GROUP BY blockchain, metric_name
ORDER BY issue_count DESC;

-- Data quality over time
SELECT
    toStartOfDay(check_time) AS day,
    blockchain,
    countIf(status = 'OK') AS passed_checks,
    countIf(status = 'ERROR') AS failed_checks,
    (countIf(status = 'OK') * 100.0 / count()) AS pass_rate_percent
FROM data_quality
GROUP BY day, blockchain
ORDER BY day, blockchain;
```

### Pagination Performance Comparison

Compare query execution time for different pagination approaches:

```sql
-- Approach 1: Simple OFFSET (slower for high offsets)
SELECT * FROM bitcoin_blocks
ORDER BY block_height DESC
LIMIT 10 OFFSET 10000;

-- Approach 2: Keyset pagination (faster for high offsets)
-- First query to get initial page
SELECT * FROM bitcoin_blocks
ORDER BY block_height DESC
LIMIT 10;

-- Subsequent pages use WHERE clause instead of OFFSET
SELECT * FROM bitcoin_blocks
WHERE block_height < 825000  -- Last block_height from previous page
ORDER BY block_height DESC
LIMIT 10;
```

**Performance Tip**: For large datasets (> 1M rows), keyset pagination (Approach 2) is significantly faster than OFFSET-based pagination because it doesn't require scanning skipped rows.

---

## Tips for Query Optimization

1. **Use Appropriate Time Ranges**: When querying large datasets, always filter by timestamp to reduce the amount of data scanned.

   ```sql
   WHERE timestamp >= now() - INTERVAL 1 HOUR
   ```

2. **Leverage Partitioning**: The tables are partitioned by month. Queries that filter by date will automatically benefit from partition pruning.

3. **Use PREWHERE for Filtering**: ClickHouse's `PREWHERE` clause can improve query performance by filtering data before reading all columns.

   ```sql
   SELECT * FROM bitcoin_blocks
   PREWHERE block_height > 800000
   WHERE transaction_count > 100;
   ```

4. **Aggregate Before Joining**: When joining tables, aggregate data first to reduce the size of intermediate results.

5. **Monitor Query Performance**: Use the `EXPLAIN` statement to understand query execution plans.

   ```sql
   EXPLAIN SELECT * FROM bitcoin_blocks WHERE block_height > 800000;
   ```

---

## Additional Resources

- [ClickHouse SQL Reference](https://clickhouse.com/docs/en/sql-reference/)
- [ClickHouse Query Optimization](https://clickhouse.com/docs/en/guides/improving-query-performance/)
- [ClickHouse Functions](https://clickhouse.com/docs/en/sql-reference/functions/)
