# Retail Sales Data Pipeline

An automated ELT pipeline that downloads Iowa's public 2026 liquor sales export, validates it, archives content-addressed snapshots in Amazon S3, loads a validated snapshot into Snowflake, builds a dimensional model with dbt, and powers a Tableau Public dashboard.

**[View the Tableau Public dashboard](https://public.tableau.com/app/profile/aman.patel1274/viz/IowaRetailSalesAnalytics2026/RetailSalesAnalytics)**

> **Status (November 2026):** An end-to-end GitHub Actions run on the `dev` branch succeeded. Snowflake's **direct S3 external stage remains unavailable** in this AWS account, so Python downloads the verified S3 snapshot and uploads it to a Snowflake **internal** stage. Tableau Public currently uses a **manually exported** reporting dataset, not an automatic live Snowflake connection. The Snowflake trial is time-limited; see [operations and limitations](docs/OPERATIONS.md).

## Architecture

```text
Iowa public export (ZIP containing CSV parts)
    |  scripts/extract_data.py / validate_data.py
    v
Local validated CSV files
    |  scripts/load_snapshot.py: SHA-256 file manifest
    v
AWS S3: snapshots/2026/<content-derived batch_id>/
    |  Python downloads and verifies snapshot
    v
Snowflake internal stage -> temporary candidate table -> RAW.LIQUOR_SALES
    |  dbt source and staging model
    v
STAGING.STG_LIQUOR_SALES (view)
    |  dbt
    v
ANALYTICS.FACT_SALES and DIM_STORE / DIM_PRODUCT / DIM_DATE
    |  SQL: sql/04_tableau_reporting_view.sql
    v
ANALYTICS.VW_TABLEAU_SALES -> exported CSV -> Tableau Public workbook

GitHub Actions runs extract -> validate -> Python tests -> load -> dbt build/tests.
```

See [architecture and modeling](docs/ARCHITECTURE.md) for grain, snapshot behavior, and important design decisions.

## Dataset and verified example

- **Source:** Iowa public data portal dataset `1263`, `https://idh-be.iowa.gov/api/v1/datasets/1263/rows.csv`.
- Despite the `.csv` URL, the response has been a ZIP archive with multiple CSV part files containing **23 columns**.
- **Verified November 2026 warehouse snapshot:** 2,029,764 sales lines, $340,415,973.82 sum of `sales_dollars`, 24,780,504 net bottles, 2,237 stores, and dates through October 30, 2026. These are snapshot-specific, **not fixed assertions** for future source updates.
- Negative-valued adjustments are retained. Blank `category_code` is allowed. The project does not assume `invoice_id` or `(invoice_id, item_no)` uniquely identifies a sales line.
- Sales amounts should not be represented as comprehensive consumer-facing retail revenue without source-semantic confirmation.

## Repository map

| Path | Purpose |
|---|---|
| `scripts/extract_data.py` | Download and validate ZIP structure; extract CSVs |
| `scripts/validate_data.py` | Chunked source validation |
| `scripts/load_snapshot.py` | S3 snapshot/archive/verification and Snowflake ingestion |
| `scripts/upload_to_s3.py`, `verify_s3_upload.py` | Earlier raw-prefix upload/check utilities |
| `sql/01_snowflake_setup.sql`, `03_raw_data_load.sql` | Initial Snowflake database and raw-table setup |
| `sql/02_s3_integration.sql` | **Historical, unsuccessful external-stage attempt**, not the active ingestion path |
| `sql/04_tableau_reporting_view.sql` | Tableau-ready Snowflake aggregation view, **run separately** |
| `retail_sales_dbt/` | dbt staging, fact/dim models, generic and singular tests, analyses |
| `.github/workflows/retail_pipeline.yml` | CI/CD manual, push-test and monthly scheduled workflow configuration |
| `tableau/Iowa_Retail_Sales_Analytics.twbx` | Packaged Tableau Public workbook with an extract |
| `tests/` | Python unit tests and extraction tests |
| `docs/` | Architecture, operations, setup, constraints, evidence checklist |

## Running locally

**Prerequisites:** Python 3.13, access to an AWS S3 bucket with read/write privileges, a configured Snowflake account/warehouse/schema/raw table, a Snowflake key-pair-authenticated user with sufficient permissions, and a Snowflake-compatible dbt profile. The repo does **not** provision IAM, Snowflake service identities, or the Tableau dashboard automatically. See [setup](docs/SETUP.md).

Windows PowerShell, from repository root:

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt

# Local AWS profile must already be configured and authenticated.
$env:AWS_PROFILE = 'retail-pipeline'
$env:S3_BUCKET_NAME = '<your-bucket>'
$env:SNOWFLAKE_ACCOUNT = '<account-identifier>'
$env:SNOWFLAKE_USER = '<login-name>'
$env:SNOWFLAKE_ROLE = '<authorized-role>'
$env:SNOWFLAKE_KEY_PATH = "$HOME\.dbt\snowflake_private_key.p8"
$secure = Read-Host 'Snowflake key passphrase' -AsSecureString
$env:DBT_KEY_PASSPHRASE = [System.Net.NetworkCredential]::new('', $secure).Password

python scripts/extract_data.py
python scripts/validate_data.py
python -m pytest tests/ -v
python scripts/load_snapshot.py

cd retail_sales_dbt
dbt debug
dbt build
```

The dbt project uses a **user-level** `~/.dbt/profiles.yml` for local runs; `retail_sales_dbt/ci/profiles.yml` is an environment-variable-only template for CI. Do not commit local profiles containing credentials or private keys.

## Tests and repeat processing

- dbt: 40 generic tests and 5 singular reconciliation/integrity tests were reported passing in development. Execute `dbt build` to rebuild models and run tests.
- Python: 17 tests were reported passing in development. Execute `python -m pytest tests/ -v`.
- The loader computes a SHA-256 manifest, uses a content-derived batch ID, validates downloaded S3 files, loads to a candidate table, compares candidate and published metrics, and records an ingestion-history row. Re-running the same snapshot was verified without increasing warehouse row count or totals.
- **Scope:** Repeat-safe full-snapshot replacement was verified for the same input. Concurrent writers, independent recovery from every failure point, arbitrary source changes, and general-purpose CSV ingestion have **not** been comprehensively demonstrated.

## Automation and reporting

The workflow can be started manually and has a monthly cron expression (`17 12 5 * *`). **Scheduled GitHub Actions workflows run only from the repository default branch**, and the schedule must be disabled when the Snowflake trial is no longer operational. The successful test run was on `dev`, not proof of a future scheduled run.

To reproduce the current Tableau view on a Snowflake account, separately execute `sql/04_tableau_reporting_view.sql`, query the view, export a CSV, and refresh the packaged Tableau workbook. The workbook is published at the link above. Tableau Public does not currently auto-refresh from this pipeline.

## Safety, cost and limitations

- AWS CI uses a dedicated **least-privilege IAM user with access keys in GitHub Secrets** because OIDC setup was unavailable on this AWS Free Plan account. Rotate/revoke keys when retiring the demo.
- Snowflake CI uses a dedicated RSA-key service user and limited `RETAIL_PIPELINE_ROLE`; keys and passphrases live in GitHub Secrets.
- Snowflake's time-limited trial and any AWS usage limits can stop cloud runs. **Do not upgrade to paid service without deliberately reviewing charges.** Disable the monthly workflow when the demo is retired.
- Tableau Public is public. Do not upload private customer data or secrets to the workbook.
- `sql/02_s3_integration.sql` is retained to document a real unresolved IAM `sts:AssumeRole` issue. The working data path uses Python and an internal stage.

More details: [Setup](docs/SETUP.md) · [Architecture](docs/ARCHITECTURE.md) · [Operations and limitations](docs/OPERATIONS.md)
