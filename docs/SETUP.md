# Reproduction and Setup

This repository is a working project, **not** a complete infrastructure-as-code bootstrap. The instructions below separate committed automation from initial resources that were created manually. Use your own accounts and never hardcode credentials.

## Prerequisites

- Python **3.13** and the pinned project dependencies.
- AWS S3 bucket in `us-east-2` and an IAM identity permitted to list/get/put the chosen snapshot prefix (plus multipart abort). For GitHub Actions, create a least-privilege CI user and store its access keys in GitHub Secrets. OIDC was unavailable in the original AWS Free Plan account.
- Snowflake account and warehouse, database `RETAIL_SALES_DB`, schemas `RAW`, `STAGING` and `ANALYTICS`; create baseline objects with `sql/01_snowflake_setup.sql` and `sql/03_raw_data_load.sql`. **Do not run the historical `COPY INTO` section blindly** on an empty internal stage. The Python snapshot loader uses the table definition, not that manual COPY workflow.
- A key-pair Snowflake user with permission to read/write `RAW.LIQUOR_SALES`, create a temporary table/stage in `RAW`, read/write `RAW.INGESTION_HISTORY`, use the warehouse, and create/replace dbt objects under the STAGING and ANALYTICS schemas. In development `RETAIL_PIPELINE_CI` and `RETAIL_PIPELINE_ROLE` were configured manually; these are **not** auto-created by the repository.
- A dbt Snowflake profile named `retail_sales_dbt`, matching the committed `dbt_project.yml`. Store your local credentials in `$HOME/.dbt/profiles.yml`; the CI template is `retail_sales_dbt/ci/profiles.yml`.

## Local PowerShell workflow

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt

$env:AWS_PROFILE = '<your configured AWS profile>'
$env:S3_BUCKET_NAME = '<your S3 bucket>'
$env:SNOWFLAKE_ACCOUNT = '<your Snowflake account identifier>'
$env:SNOWFLAKE_USER = '<your Snowflake login name>'
$env:SNOWFLAKE_ROLE = '<authorized role>'
$env:SNOWFLAKE_KEY_PATH = "$HOME\.dbt\snowflake_private_key.p8"
$secure = Read-Host 'Key passphrase' -AsSecureString
$env:DBT_KEY_PASSPHRASE = [System.Net.NetworkCredential]::new('', $secure).Password

python scripts/extract_data.py
python scripts/validate_data.py
python -m pytest tests/ -v
python scripts/load_snapshot.py
cd retail_sales_dbt
dbt debug
dbt build
```

The local dbt profile must use the correct Snowflake login name (not necessarily the case-sensitive Snowflake user object identifier). Restore a fresh virtual environment on each computer; do not copy `.venv` between machines.

## GitHub Actions configuration

Workflow file: `.github/workflows/retail_pipeline.yml`.

Required repository secrets:

- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `S3_BUCKET_NAME`
- `SNOWFLAKE_ACCOUNT`
- `SNOWFLAKE_USER`
- `SNOWFLAKE_PRIVATE_KEY` (entire PEM file)
- `SNOWFLAKE_KEY_PASSPHRASE`

The workflow writes the private key to a temporary runner file with restrictive permissions, runs AWS/Snowflake connection checks, extracts source data, executes Python tests, loads the snapshot and builds/tests dbt models.

- Manual dispatch requires a workflow file available on the default branch and the correct permissions.
- The `push` trigger is currently limited to changes to the workflow file on `dev`.
- Monthly cron (`17 12 5 * *`) runs **only on the default branch** once the workflow is merged there, and should be disabled at demo retirement.
- A successful `dev` workflow execution was observed in November 2026; this is not a guarantee that a new account's IAM, permissions, or dependencies are preconfigured.

## Reporting and dashboard

1. With the database, analytics models and role grants ready, execute `sql/04_tableau_reporting_view.sql` in Snowflake.
2. Reconcile `SELECT COUNT(*), SUM(transaction_lines), SUM(net_sales) FROM RETAIL_SALES_DB.ANALYTICS.VW_TABLEAU_SALES` with your current warehouse snapshot.
3. Export query results to CSV (the original run used `data/reporting/tableau_sales.csv`).
4. Open `tableau/Iowa_Retail_Sales_Analytics.twbx` in Tableau Public/Desktop and replace or refresh the CSV/extract connection as needed.
5. Test filters and rankings before publishing to Tableau Public. Published data is public.

The current workbook is available at https://public.tableau.com/app/profile/aman.patel1274/viz/IowaRetailSalesAnalytics2026/RetailSalesAnalytics . It does **not** automatically update from Snowflake.

## Security

Never commit private keys, passphrases, AWS access keys, `.env`, the local user-level dbt profile or private business CSVs. The S3 bucket is private. To retire the demo, disable the schedule and revoke/delete the dedicated AWS IAM user access key and Snowflake CI key/user as appropriate.
