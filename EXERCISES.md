# Hands-On Exercises: Blockchain Data Ingestion

Step-by-step exercises for exploring blockchain data engineering concepts. Each exercise includes learning objectives, instructions, and expected outputs.

## Prerequisites

Before starting these exercises, ensure you have:
- Docker and Docker Compose installed
- Project running (`./start.sh` or `docker compose up -d`)
- Access to dashboard at http://localhost:8501
- (Optional) SQL client or Python environment for direct queries

---

## Table of Contents

### Getting Started
- [Exercise 1: System Verification](#exercise-1-system-verification)
- [Exercise 2: Start Your First Collection](#exercise-2-start-your-first-collection)
- [Exercise 3: Explore the Dashboard](#exercise-3-explore-the-dashboard)

### SQL Exploration
- [Exercise 4: Basic Block Queries](#exercise-4-basic-block-queries)
- [Exercise 5: Transaction Analysis](#exercise-5-transaction-analysis)
- [Exercise 6: Cross-Chain Comparisons](#exercise-6-cross-chain-comparisons)

### Data Analysis
- [Exercise 7: Time-Series Analysis](#exercise-7-time-series-analysis)
- [Exercise 8: Storage and Compression](#exercise-8-storage-and-compression)
- [Exercise 9: Performance Metrics](#exercise-9-performance-metrics)

### The 5Vs of Big Data
- [Exercise 10: Understanding Volume](#exercise-10-understanding-volume)
- [Exercise 11: Measuring Velocity](#exercise-11-measuring-velocity)
- [Exercise 12: Exploring Variety](#exercise-12-exploring-variety)
- [Exercise 13: Veracity and Data Quality](#exercise-13-veracity-and-data-quality)
- [Exercise 14: Extracting Value](#exercise-14-extracting-value)

### Extension Challenges
- [Challenge A: Add a New Metric](#challenge-a-add-a-new-metric)
- [Challenge B: Create a Custom Query](#challenge-b-create-a-custom-query)
- [Challenge C: Modify Collection Parameters](#challenge-c-modify-collection-parameters)

---

## Getting Started

### Exercise 1: System Verification

**Learning Objectives:**
- Understand the multi-container architecture
- Verify all services are running correctly
- Learn to check service logs

**Instructions:**

1. Open a terminal and navigate to the project directory:
   ```bash
   cd blockchain-ingestion
   ```

2. Check that all containers are running:
   ```bash
   docker compose ps
   ```

3. Verify ClickHouse is responding:
   ```bash
   docker compose exec clickhouse clickhouse-client \
     --password clickhouse_password \
     --query "SELECT 'ClickHouse is working!' as message"
   ```

4. Check the collector API health:
   ```bash
   curl http://localhost:8000/health
   ```

5. Open the dashboard in your browser: http://localhost:8501

**Questions to Consider:**
- What happens if you stop the ClickHouse container? Try `docker compose stop clickhouse` and observe the error messages.
- Why do we have three separate containers instead of one monolithic application?
- How do containers communicate with each other? (Hint: check `docker-compose.yml`)

---

### Exercise 2: Start Your First Collection

**Learning Objectives:**
- Start and stop data collection
- Observe real-time data ingestion
- Understand collection status indicators

**Instructions:**

1. Open the dashboard at http://localhost:8501

2. Observe the initial state:
   - Status should show "Stopped" (red indicator)
   - Total Records might be 0 or show data from previous sessions
   - Charts may be empty

3. Click the **"Start Collection"** button

4. Watch the dashboard update (auto-refreshes every 5 seconds):
   - Status changes to "Running" (green indicator)
   - Record counts begin increasing
   - Charts start showing data points

5. Wait 2-3 minutes to collect some data

6. Click **"Stop Collection"**

7. Verify data was collected by running:
   ```bash
   docker compose exec clickhouse clickhouse-client \
     --password clickhouse_password \
     --database blockchain_data \
     --query "SELECT count() FROM bitcoin_blocks"
   ```

   **Expected Output:** A number greater than 0 (e.g., `15` after 2-3 minutes)

**Questions to Consider:**
- Why does Solana collect more transactions per block than Bitcoin?
- What happens when you hit the safety limits (10 minutes or 5GB)?
- Why might the record count increase unevenly across blockchains?

---

### Exercise 3: Explore the Dashboard

**Learning Objectives:**
- Understand dashboard components
- Interpret collection metrics
- Identify performance characteristics of each blockchain

**Instructions:**

1. Start collection if not already running

2. Observe the **Collection Status** section:
   - What does "Safety Limits: 10min / 5GB" mean?
   - Why might we need safety limits in an educational environment?

3. Watch the **Records by Blockchain Source** chart:
   - Which blockchain shows the most transactions?
   - Is the ratio between blocks and transactions different for each chain?

4. Examine the **Collection Performance** section:
   - Which blockchain has the fastest collection duration?
   - Which has the slowest? Why might that be?

5. Check the **Storage Details** section:
   - What is the compression ratio showing?
   - Why is blockchain data highly compressible?

**Questions to Consider:**
- Why does Solana show "success" and "failed" transaction statuses while others don't?
- What causes collection duration variations?
- Why is the compression ratio important for big data applications?

---

## SQL Exploration

### Exercise 4: Basic Block Queries

**Learning Objectives:**
- Query blockchain data using SQL
- Understand block structure differences across chains
- Practice basic SELECT, ORDER BY, and LIMIT clauses

**Instructions:**

1. **Open a new terminal window** (keep dashboard open in browser)

2. **Connect to ClickHouse interactive SQL client**:
   ```bash
   docker compose exec clickhouse clickhouse-client \
     --password clickhouse_password \
     --database blockchain_data
   ```

   **What this command does:**
   - `docker compose exec clickhouse`: Execute command inside the ClickHouse container
   - `clickhouse-client`: Start interactive SQL client (similar to `psql` for PostgreSQL)
   - `--password clickhouse_password`: Authenticate (password defined in .env file)
   - `--database blockchain_data`: Connect to our blockchain database

3. **You should see a prompt**:
   ```
   clickhouse :)
   ```
   This means you're connected! The smiley face is ClickHouse's CLI prompt.

4. **Test the connection**:
   ```sql
   SHOW TABLES;
   ```

   **Expected output** (8 tables):
   ```
   bitcoin_blocks
   bitcoin_transactions
   collection_metrics
   collection_state
   ethereum_blocks
   ethereum_transactions
   solana_blocks
   solana_transactions
   ```

   If you see 8 tables, you're ready to query!

5. **Try your first query**:
   ```sql
   SELECT count() FROM solana_transactions;
   ```

   **Expected**: A number > 0 if you've run collection (e.g., 450).
   If 0, start collection in the dashboard first (Exercise 2).

6. **Exit when done**:
   ```sql
   EXIT;
   ```
   or press `Ctrl+D`

7. Run the following queries from **SAMPLE_QUERIES.md**:
   - "View Recent Bitcoin Blocks" - Shows latest block data
   - "View Recent Solana Blocks" - Shows latest slot/block data
   - Compare block structures using cross-chain comparison queries

Alternatively, experiment with your own queries to explore block structures.

**Questions to Consider:**
- Why does Bitcoin use Proof-of-Work (nonce) while Solana uses Proof-of-History?
- What does `slot - parent_slot` tell us about Solana block production?
- Why do blockchains have different block identifiers (block_height vs slot)?

---

### Exercise 5: Transaction Analysis

**Learning Objectives:**
- Analyze transaction data patterns
- Understand fee structures across blockchains
- Practice aggregation queries (COUNT, AVG, SUM)

**Instructions:**

Run the following queries from **SAMPLE_QUERIES.md - Aggregation Queries**:
1. "Bitcoin Transaction Fee Statistics" - Analyzes min/max/avg/median fees
2. "Check Solana Transaction Status Distribution" - Shows success vs failed transactions

Try modifying these queries to answer additional questions like:
- What's the average number of inputs/outputs per Bitcoin transaction?
- What percentage of Solana transactions fail?

**Questions to Consider:**
- Why might some Solana transactions fail?
- How would you convert Satoshis to BTC? (Hint: divide by 100,000,000)
- What do the input_count and output_count patterns tell you about Bitcoin's UTXO model?

---

### Exercise 6: Cross-Chain Comparisons

**Learning Objectives:**
- Compare blockchain characteristics using SQL
- Understand throughput and fee differences
- Practice UNION ALL for multi-table queries

**Instructions:**

Run the following queries from **SAMPLE_QUERIES.md - Cross-Chain Comparisons**:
1. "Average Transactions Per Block by Blockchain"
2. "Block Production Rate Comparison"
3. "Transaction Throughput Comparison"

These queries demonstrate how to use UNION ALL to compare metrics across Bitcoin and Solana.

**Questions to Consider:**
- Why does Bitcoin show fewer transactions per block than actual?
- Which chain appears to have the highest throughput based on your data?
- What would you need to fairly compare transaction fees in USD?

---

## Data Analysis

### Exercise 7: Time-Series Analysis

**Learning Objectives:**
- Perform time-based aggregations
- Use ClickHouse time functions (toStartOfMinute, toStartOfHour)
- Identify trends in blockchain data

**Instructions:**

Run the following queries from **SAMPLE_QUERIES.md - Time-Series Analysis**:
1. "Bitcoin Transaction Volume by Day" - Shows daily transaction patterns
2. "Solana Success Rate Over Time" - Tracks hourly success rates

Also explore collection performance using queries from the "Advanced Analytics" section:
- "Collection Metrics Summary" - Analyzes collection performance by source

Try modifying these queries to:
- Group by different time intervals (minute, hour, day, week)
- Calculate moving averages or trends
- Identify peak activity periods

**Questions to Consider:**
- Why might gas utilization vary between blocks?
- What patterns do you see in collection performance?
- How would you detect anomalies in the data?

---

### Exercise 8: Storage and Compression

**Learning Objectives:**
- Understand ClickHouse storage internals
- Analyze compression effectiveness
- Query system tables for metadata

**Instructions:**

1. View storage details for all tables:
   ```sql
   SELECT
       table,
       formatReadableSize(sum(bytes)) as uncompressed,
       formatReadableSize(sum(bytes_on_disk)) as compressed,
       round((1 - sum(bytes_on_disk) / sum(bytes)) * 100, 2) as compression_pct,
       sum(rows) as total_rows
   FROM system.parts
   WHERE database = 'blockchain_data' AND active = 1
   GROUP BY table
   ORDER BY sum(bytes) DESC;
   ```

   **Expected Output (format):**
   ```
   ┌─table──────────────────┬─uncompressed─┬─compressed─┬─compression_pct─┬─total_rows─┐
   │ solana_transactions    │ 2.50 MiB     │ 350.00 KiB │           86.33 │      13400 │
   │ bitcoin_transactions   │ 150.00 KiB   │  25.00 KiB │           83.33 │          1 │
   │ solana_blocks          │ 120.00 KiB   │  20.00 KiB │           83.33 │        274 │
   │ bitcoin_blocks         │  45.00 KiB   │   8.00 KiB │           82.22 │         13 │
   └────────────────────────┴──────────────┴────────────┴─────────────────┴────────────┘
   ```

2. View partition information:
   ```sql
   SELECT
       table,
       partition,
       count() as parts,
       sum(rows) as rows,
       formatReadableSize(sum(bytes_on_disk)) as size
   FROM system.parts
   WHERE database = 'blockchain_data' AND active = 1
   GROUP BY table, partition
   ORDER BY table, partition;
   ```

3. Analyze column-level compression:
   ```sql
   SELECT
       table,
       column,
       formatReadableSize(sum(column_bytes_on_disk)) as compressed_size,
       formatReadableSize(sum(column_data_uncompressed_bytes)) as uncompressed_size
   FROM system.parts_columns
   WHERE database = 'blockchain_data' AND active = 1
   GROUP BY table, column
   ORDER BY table, sum(column_data_uncompressed_bytes) DESC;
   ```

4. Understand why blockchain data compresses well:
   ```sql
   SELECT
       uniq(block_hash) as unique_hashes,
       uniq(slot) as unique_slots,
       count() as total_rows,
       round(uniq(status) * 100.0 / count(), 2) as status_cardinality_pct
   FROM solana_transactions;
   ```

**Questions to Consider:**
- Which table has the best compression ratio? Why?
- What does the partition column (YYYYMM format) represent?
- Why does low cardinality (few unique values) improve compression?

---

### Exercise 9: Performance Metrics

**Learning Objectives:**
- Analyze collection performance
- Identify errors and their causes
- Calculate throughput metrics

**Instructions:**

1. Calculate overall collection statistics:
   ```sql
   SELECT
       source,
       count() as collection_events,
       sum(records_collected) as total_records,
       round(avg(records_collected), 2) as avg_records_per_event,
       round(avg(collection_duration_ms), 2) as avg_duration_ms,
       sum(error_count) as total_errors,
       round(sum(error_count) * 100.0 / count(), 2) as error_rate_pct
   FROM collection_metrics
   GROUP BY source;
   ```

2. Find collection errors (if any):
   ```sql
   SELECT
       metric_time,
       source,
       error_message
   FROM collection_metrics
   WHERE error_count > 0
   ORDER BY metric_time DESC
   LIMIT 10;
   ```

3. Calculate overall events per second:
   ```sql
   WITH
       (SELECT min(metric_time) FROM collection_metrics) as start_time,
       (SELECT max(metric_time) FROM collection_metrics) as end_time,
       (SELECT sum(records_collected) FROM collection_metrics) as total_records
   SELECT
       total_records,
       dateDiff('second', start_time, end_time) as duration_seconds,
       round(total_records / dateDiff('second', start_time, end_time), 2) as events_per_second;
   ```

4. Identify slow collection cycles:
   ```sql
   SELECT
       metric_time,
       source,
       collection_duration_ms,
       records_collected
   FROM collection_metrics
   WHERE collection_duration_ms > 1000
   ORDER BY collection_duration_ms DESC
   LIMIT 10;
   ```

**Questions to Consider:**
- What causes collection errors?
- How does the collection interval (5 seconds default) affect throughput?
- What might be the bottleneck: API rate limits or database insertion?

---

## The 5Vs of Big Data

These exercises help you understand the 5Vs framework through hands-on exploration of your collected data.

### Exercise 10: Understanding Volume

**Learning Objectives:**
- Quantify data volume in the system
- Understand compression ratios and storage efficiency
- Project storage requirements for production scale

**Instructions:**

1. Calculate total data volume collected:
   ```sql
   SELECT
       'Bitcoin Blocks' as table_name,
       count() as row_count,
       formatReadableSize(sum(length(block_hash) + length(merkle_root) +
                              length(previous_block_hash))) as estimated_string_size
   FROM bitcoin_blocks
   UNION ALL
   SELECT
       'Solana Blocks',
       count(),
       formatReadableSize(sum(length(block_hash) + length(previous_block_hash)))
   FROM solana_blocks
   UNION ALL
   SELECT
       'Bitcoin Transactions',
       count(),
       formatReadableSize(sum(length(tx_hash) + length(block_hash)))
   FROM bitcoin_transactions
   UNION ALL
   SELECT
       'Solana Transactions',
       count(),
       formatReadableSize(sum(length(signature) + length(block_hash)))
   FROM solana_transactions;
   ```

2. Analyze compression effectiveness:
   ```sql
   SELECT
       table,
       sum(rows) as total_rows,
       formatReadableSize(sum(bytes)) as uncompressed,
       formatReadableSize(sum(bytes_on_disk)) as compressed,
       round(sum(bytes) / sum(bytes_on_disk), 2) as compression_ratio
   FROM system.parts
   WHERE database = 'blockchain_data' AND active = 1
   GROUP BY table
   ORDER BY sum(bytes) DESC;
   ```

3. Project storage needs: If Bitcoin's full blockchain is ~500GB and Solana grows ~100GB/month, estimate how much compressed storage you'd need for 1 year of full chain data.

**Questions to Consider:**
- Why does blockchain data compress so well?
- How does partitioning help manage volume?
- What happens when volume exceeds available storage?

---

### Exercise 11: Measuring Velocity

**Learning Objectives:**
- Measure data generation rates across chains
- Understand collection throughput
- Compare high-velocity vs low-velocity data sources

**Instructions:**

1. Calculate block production rates:
   ```sql
   SELECT
       'Bitcoin' as chain,
       count() as blocks,
       min(timestamp) as first_block,
       max(timestamp) as last_block,
       dateDiff('minute', min(timestamp), max(timestamp)) as minutes_spanned,
       round(count() * 60.0 / dateDiff('minute', min(timestamp), max(timestamp)), 2) as blocks_per_hour
   FROM bitcoin_blocks
   WHERE timestamp > now() - INTERVAL 1 HOUR
   UNION ALL
   SELECT
       'Solana',
       count(),
       min(timestamp),
       max(timestamp),
       dateDiff('minute', min(timestamp), max(timestamp)),
       round(count() * 60.0 / dateDiff('minute', min(timestamp), max(timestamp)), 2)
   FROM solana_blocks
   WHERE timestamp > now() - INTERVAL 1 HOUR;
   ```

2. Measure transaction velocity:
   ```sql
   SELECT
       source,
       count() as transactions,
       round(count() / 60.0, 2) as tx_per_second
   FROM (
       SELECT 'bitcoin' as source, timestamp FROM bitcoin_transactions
       WHERE timestamp > now() - INTERVAL 1 MINUTE
       UNION ALL
       SELECT 'solana', timestamp FROM solana_transactions
       WHERE timestamp > now() - INTERVAL 1 MINUTE
   )
   GROUP BY source;
   ```

3. Analyze collection performance:
   ```sql
   SELECT
       source,
       round(avg(collection_duration_ms), 2) as avg_duration_ms,
       round(avg(records_collected), 2) as avg_records,
       round(avg(records_collected) * 1000.0 / avg(collection_duration_ms), 2) as records_per_second
   FROM collection_metrics
   WHERE metric_time > now() - INTERVAL 10 MINUTE
   GROUP BY source;
   ```

**Questions to Consider:**
- Which blockchain generates data faster?
- How does velocity affect your collection strategy?
- What would happen if Solana's velocity doubled?

---

### Exercise 12: Exploring Variety

**Learning Objectives:**
- Compare data structures across blockchains
- Understand schema differences
- Appreciate the challenge of data normalization

**Instructions:**

1. Compare block structures:
   ```sql
   -- Bitcoin block structure
   DESCRIBE bitcoin_blocks;

   -- Solana block structure
   DESCRIBE solana_blocks;
   ```

2. Identify unique fields per chain:
   ```sql
   -- Bitcoin-specific: merkle_root, nonce, difficulty (PoW)
   SELECT
       'Bitcoin' as chain,
       avg(difficulty) as avg_difficulty,
       max(nonce) as max_nonce,
       count(DISTINCT merkle_root) as unique_merkle_roots
   FROM bitcoin_blocks;

   -- Solana-specific: slot, parent_slot, skipped slots
   SELECT
       'Solana' as chain,
       avg(slot - parent_slot - 1) as avg_skipped_slots,
       max(slot - block_height) as total_skipped_slots,
       count() as total_blocks
   FROM solana_blocks;
   ```

3. Compare transaction models:
   ```sql
   -- Bitcoin UTXO model (inputs/outputs)
   SELECT
       'Bitcoin' as chain,
       round(avg(input_count), 2) as avg_inputs,
       round(avg(output_count), 2) as avg_outputs,
       round(avg(fee), 2) as avg_fee_satoshis
   FROM bitcoin_transactions;

   -- Solana signature model (success/failed)
   SELECT
       'Solana' as chain,
       countIf(status = 'success') as successful,
       countIf(status = 'failed') as failed,
       round(avg(fee), 2) as avg_fee_lamports
   FROM solana_transactions;
   ```

**Questions to Consider:**
- Why does Bitcoin have merkle_root but Solana doesn't?
- What does the UTXO model tell us that Solana's model doesn't?
- How would you add Ethereum data with gas and Wei to this schema?

---

### Exercise 13: Veracity and Data Quality

**Learning Objectives:**
- Understand data quality dimensions
- Query the data quality table
- Identify and investigate quality issues

**Instructions:**

1. Check overall data quality:
   ```sql
   SELECT
       source,
       record_type,
       quality_level,
       count() as occurrences,
       round(avg(quality_score), 3) as avg_quality_score
   FROM data_quality
   GROUP BY source, record_type, quality_level
   ORDER BY source, record_type, quality_level;
   ```

2. Find specific quality issues:
   ```sql
   SELECT
       detected_at,
       source,
       record_type,
       record_id,
       issues,
       warnings
   FROM data_quality
   WHERE issue_count > 0
   ORDER BY detected_at DESC
   LIMIT 20;
   ```

3. Analyze quality trends over time:
   ```sql
   SELECT
       toStartOfMinute(detected_at) as minute,
       source,
       count() as quality_events,
       sum(issue_count) as total_issues,
       sum(warning_count) as total_warnings,
       round(avg(quality_score), 3) as avg_score
   FROM data_quality
   GROUP BY minute, source
   ORDER BY minute DESC, source
   LIMIT 30;
   ```

4. Check for Solana skipped slots (consistency check):
   ```sql
   SELECT
       slot,
       parent_slot,
       slot - parent_slot - 1 as skipped_slots,
       timestamp
   FROM solana_blocks
   WHERE slot - parent_slot > 5
   ORDER BY skipped_slots DESC
   LIMIT 10;
   ```

5. Verify Bitcoin timestamp consistency:
   ```sql
   SELECT
       block_height,
       timestamp,
       dateDiff('minute', timestamp, now()) as minutes_ago,
       CASE
           WHEN timestamp > now() THEN 'FUTURE - INVALID'
           WHEN dateDiff('hour', timestamp, now()) > 24 THEN 'VERY OLD'
           ELSE 'OK'
       END as timestamp_status
   FROM bitcoin_blocks
   ORDER BY block_height DESC
   LIMIT 10;
   ```

**Questions to Consider:**
- What types of quality issues are most common?
- How would you alert on quality degradation?
- Why is veracity especially important for financial data like blockchain?

---

### Exercise 14: Extracting Value

**Learning Objectives:**
- Transform raw data into business insights
- Answer analytical questions
- Create actionable metrics

**Instructions:**

1. **Fee Analysis** - Which chain is cheaper?
   ```sql
   SELECT
       'Bitcoin' as chain,
       'Satoshi' as unit,
       round(avg(fee), 2) as avg_fee,
       round(avg(fee) * 0.00000001 * 45000, 4) as approx_usd  -- Assuming $45k BTC
   FROM bitcoin_transactions
   UNION ALL
   SELECT
       'Solana',
       'Lamport',
       round(avg(fee), 2),
       round(avg(fee) * 0.000000001 * 100, 6)  -- Assuming $100 SOL
   FROM solana_transactions;
   ```

2. **Network Health** - Transaction success rates:
   ```sql
   SELECT
       toStartOfHour(timestamp) as hour,
       countIf(status = 'success') as successful,
       countIf(status = 'failed') as failed,
       round(countIf(status = 'success') * 100.0 / count(), 2) as success_rate_pct
   FROM solana_transactions
   GROUP BY hour
   ORDER BY hour DESC
   LIMIT 24;
   ```

3. **Throughput Comparison**:
   ```sql
   SELECT
       chain,
       sum(tx_count) as total_transactions,
       count() as total_blocks,
       round(sum(tx_count) * 1.0 / count(), 2) as avg_tx_per_block,
       round(sum(tx_count) / dateDiff('second', min(ts), max(ts)), 2) as tx_per_second
   FROM (
       SELECT 'Bitcoin' as chain, transaction_count as tx_count, timestamp as ts
       FROM bitcoin_blocks
       UNION ALL
       SELECT 'Solana', transaction_count, timestamp
       FROM solana_blocks
   )
   GROUP BY chain;
   ```

4. **Data Pipeline ROI** - Storage efficiency value:
   ```sql
   SELECT
       table,
       sum(rows) as rows,
       formatReadableSize(sum(bytes)) as would_need_uncompressed,
       formatReadableSize(sum(bytes_on_disk)) as actually_using,
       formatReadableSize(sum(bytes) - sum(bytes_on_disk)) as storage_saved,
       round((sum(bytes) - sum(bytes_on_disk)) / 1024 / 1024 * 0.023, 4) as dollars_saved_per_month
       -- AWS S3 ~$0.023/GB/month
   FROM system.parts
   WHERE database = 'blockchain_data' AND active = 1
   GROUP BY table;
   ```

**Questions to Consider:**
- What business decisions could these insights drive?
- How would you visualize these metrics for stakeholders?
- What additional value could you extract with more data?

---

## Extension Challenges

### Challenge A: Add a New Metric

**Difficulty:** Intermediate
**Objective:** Add a new metric to track in the collection_metrics table.

**Ideas:**
1. Track the latest block number/slot for each chain
2. Add a "blocks_behind" metric showing how far behind current chain tip
3. Track API response times separately from total collection time

**Steps:**
1. Modify the collector Python code (`collector/collectors/*.py`)
2. Update the metrics INSERT statement
3. Test the change by restarting the collector

**Hints:**
- Look at how `records_collected` is tracked
- You may need to alter the collection_metrics table schema

---

### Challenge B: Create a Custom Query

**Difficulty:** Intermediate
**Objective:** Write a query to answer one of these questions:

1. **Block Time Analyzer:** Calculate average time between Solana slots
2. **Fee Analyzer:** Calculate the average fee per byte for Bitcoin transactions
3. **Reliability Report:** Which blockchain has the most consistent block times?

**Example Solution (Fee Analyzer):**
```sql
SELECT
    round(avg(fee * 1.0 / size), 4) as satoshi_per_byte,
    round(avg(fee * 1.0 / weight), 4) as satoshi_per_weight_unit
FROM bitcoin_transactions
WHERE size > 0 AND weight > 0;
```

**Challenge:** Write queries for all three questions!

---

### Challenge C: Modify Collection Parameters

**Difficulty:** Beginner
**Objective:** Experiment with different collection configurations.

**Instructions:**

1. Edit the `.env` file to change:
   ```bash
   # Change collection interval from 5 to 10 seconds
   COLLECTION_INTERVAL_SECONDS=10

   # Reduce safety limits for testing
   MAX_COLLECTION_TIME_MINUTES=5
   ```

2. Restart the services:
   ```bash
   docker compose down && docker compose up -d
   ```

3. Start collection and observe:
   - How does collection frequency change?
   - Does the error rate change?
   - How do the dashboard charts look different?

4. Try disabling one blockchain:
   ```bash
   # In .env file
   BITCOIN_ENABLED=false
   ```

   Observe the dashboard with only Solana enabled.

5. **Reset** to original settings when done!
