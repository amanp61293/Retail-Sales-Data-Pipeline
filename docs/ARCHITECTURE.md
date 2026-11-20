# Architecture and Data Model

## Implemented path

1. `scripts/extract_data.py` requests Iowa public dataset `1263`; it validates a ZIP archive and extracts CSV part files.
2. `scripts/validate_data.py` checks source columns, required values, dates, numeric fields and negative-record counts in pandas chunks.
3. `scripts/load_snapshot.py` validates 23-column headers and part sizes against the archive, calculates SHA-256 checksums, and constructs a deterministic manifest/batch ID.
4. The loader archives all parts at `s3://<bucket>/snapshots/2026/<batch_id>/`, verifies existing object metadata, downloads and hashes copies, and writes a `manifest.json`.
5. Python uploads these verified CSV parts to a temporary **Snowflake internal stage**, copies into a temporary candidate table, validates row counts/required values and checks aggregate metrics.
6. A transaction uses `INSERT OVERWRITE` to replace the existing `RAW.LIQUOR_SALES` content and inserts an audit record into `RAW.INGESTION_HISTORY`. The candidate table and stage are temporary.
7. dbt builds `STAGING.STG_LIQUOR_SALES` (view), then `ANALYTICS.DIM_STORE`, `DIM_PRODUCT`, `DIM_DATE` and `FACT_SALES` (tables). Generic and singular tests check nulls, key uniqueness, relationships, reconciliation and row multiplicity.
8. A separately run SQL script creates `ANALYTICS.VW_TABLEAU_SALES`. Its results were exported to a local CSV and loaded into the packaged Tableau Public workbook; this export/publish step is **not in GitHub Actions**.

**Important:** `raw/2026/` contains files from the earlier S3 phase. `snapshots/2026/` is the content-addressed archive used by the active loader. The original external S3 stage failed with `sts:AssumeRole`; the production path is Python-mediated, not native Snowflake external-stage loading.

## Warehouse grain and keys

| Object | Grain | Selection/key |
|---|---|---|
| `RAW.LIQUOR_SALES` | One source CSV row | No declared unique business row ID |
| `STAGING.STG_LIQUOR_SALES` | One raw row | Trims descriptive strings; preserves multiplicity |
| `ANALYTICS.FACT_SALES` | One source sale line | `invoice_id`, `store_no`, `product_key`, `date_key` plus measures; no unique fact key |
| `ANALYTICS.DIM_STORE` | One store number | `store_no`; descriptive attributes selected via `MAX_BY` |
| `ANALYTICS.DIM_PRODUCT` | One product identity combination | SHA2 of `item_no`, nullable `category_code`, `vendor_number`, `bottle_volume_ml`; attributes chosen by `ROW_NUMBER` |
| `ANALYTICS.DIM_DATE` | One observed transaction day | Numeric `YYYYMMDD` date key |
| `ANALYTICS.VW_TABLEAU_SALES` | Month × store × product category attributes | Monthly sales, bottles, volumes, line count and negative adjustments |

Fact lines are intentionally **not** deduplicated by invoice ID or invoice/product combination. Source row repetition can be legitimate; the staging/fact multiplicity test compares occurrences of projected row values.

## Data-quality controls

- The loader checks source CSV columns and per-file row counts against `COPY INTO` results.
- Candidate and published tables are reconciled by row count, sum of sales dollars, missing categories, negative records and `HASH_AGG(*)`.
- dbt singular tests check raw/staging and staging/fact aggregates, join fan-out, product grain and fact multiplicity.
- Monetary amounts use Snowflake fixed-precision numeric types; negative transactions are retained. Null category codes are permitted by design.

## Deliberate constraints and open risks

- **Not arbitrary-dataset ready:** Schema and models depend on Iowa's 23-column retail data layout.
- **Store descriptive fields:** `MAX_BY` on latest transaction date has potential nondeterminism when multiple different values tie on that date. A targeted name/address/city diagnostic returned no conflicts during development; this does not prove all attributes are deterministic for future data.
- **Snapshot consistency:** The same-snapshot rerun was verified. A checksum manifest plus full replacement is not a comprehensive CDC/merge solution or proof of concurrency safety. The manifest is uploaded before warehouse publication and can therefore exist for a failed load.
- **Raw lineage:** The table does not persist batch ID or original file row number for every line. The ingestion-history table records batch-level metadata.
- **Recovery:** The extractor's ZIP/folder replacement is not fully atomic across interruption points. Multiple concurrent pipeline writers are not formally supported; GitHub Actions concurrency reduces overlap within this workflow only.
- **Reporting view:** Defined under `sql/04_tableau_reporting_view.sql` but not built by dbt or workflow. Tableau Public uses a packaged extract rather than direct automated refresh.
