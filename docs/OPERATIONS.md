# Operations, Cost and Known Limitations

## Verified development milestones

- Initial raw snapshot: **1,814,856** sales records; **$301,459,397.84** net field sum; 26 missing category codes; 1,412 negative records.
- After a successful GitHub Actions end-to-end run, the observed 2026 export had **2,029,764** records; **$340,415,973.82** in net sales, **24,780,504** bottles, **2,237** active stores, transaction dates through **October 30, 2026**. Counts are evidence for a particular export, not permanent constraints.
- A successful GitHub Actions run on `dev` was shown on November 20, 2026; the run was approximately **1 minute 57 seconds**.
- In development, the user reported **17 Python tests passing** and **45 dbt tests passing**, plus repeated model and ingestion executions without aggregate drift. The current review of the ZIP is static; no cloud execution was performed as part of the review.
- Tableau Public dashboard published and user confirmed the public URL works. The Top 10 Stores action filter was corrected with a table calculation using **Compute Using: Table (Down)**.

## Monthly run behavior

The workflow downloads the public export afresh, validates files, creates/checks a deterministic S3 snapshot, loads Snowflake and rebuilds dbt tables. If Iowa's export has not changed, a repeat batch preserves warehouse measures. Ingestion history can have multiple records for repeated batch runs; batch ID is **not** a unique row constraint there.

The `schedule` trigger exists in YAML but GitHub Actions scheduled workflows run from the **default branch only**. Before merging to `main`, decide whether the schedule should be activated. A green manual or push run is not proof of a scheduled production execution.

## Snowflake trial end and retirement

As of November 20, 2026, the Snowflake UI showed **$396 of $400 trial credits remaining** but approximately **5 days** left. The account may stop running warehouse operations when the trial expires even with unused credit. The source fetch and S3 operations may still work, but the workflow normally stops during Snowflake connection/build. Tableau Public's existing published extract is independent of the live warehouse.

**Recommended retirement procedure before trial expiry:**

1. Preserve screenshots/logs of the successful workflow, dbt tests and warehouse metrics. Avoid displaying any secrets.
2. Preserve a packaged Tableau workbook and verify the public published dashboard.
3. Disable the scheduled workflow: remove/comment the `schedule:` trigger in `.github/workflows/retail_pipeline.yml` and commit to `main`, or disable the workflow from GitHub's Actions UI. Verify the monthly trigger is no longer active.
4. Suspend the Snowflake warehouse if no further tests are needed; check cost monitor and resources. Do not upgrade to paid billing without approval.
5. Rotate/revoke the dedicated AWS CI access keys and Snowflake CI private key/service user when retiring cloud access. This prevents exposure of dormant long-lived credentials.
6. Leave the source, tests, reports and (public) dashboard in GitHub so the implementation can be studied or recreated on another account.

## Issues and resolutions

| Issue | Actual outcome |
|---|---|
| Iowa `.csv` URL returned ZIP | Python checks ZIP validity/CRC and extracts multiple CSV parts |
| Empty `category_code` values caused numeric load failures | Snowflake CSV options `NULL_IF = ('')` and `EMPTY_FIELD_AS_NULL = TRUE` |
| IAM `sts:AssumeRole` failed for native Snowflake S3 stage | Unresolved; implemented Python-verified S3-to-internal-stage bridge |
| AWS Free Plan did not expose OIDC provider setup | Dedicated least-privilege IAM user/access keys in GitHub Secrets |
| Snowflake SSO JWT error | Key-pair authentication with correct Snowflake login name |
| dbt key-path and Windows environment differences | Fresh Python 3.13 virtual environment; key file outside repository |
| Duplicate-looking source invoice/item pairs | Retained source-line multiplicity; dbt row-multiplicity reconciliation test |
| Tableau county map action blanked Top 10 Stores | Replaced native Top-N with dynamic table calculation and selected Table (Down) |
| Dashboard KPI was restricted to top categories | Removed unintended global scope of ranking filter |

## Outstanding production hardening

- Direct Snowflake external-stage access is still broken. Python bridge works but requires a client transfer of all source files.
- Dashboard export/republish is manual. `sql/04_tableau_reporting_view.sql` is not run by GitHub Actions.
- Automated infrastructure bootstrapping of AWS and Snowflake user/role setup is not provided.
- Python extraction replacement can be interrupted between ZIP swap and extracted-folder replacement; no complete rollback protocol.
- No formal concurrent-writer protection across independent processes/cloud workflows; GitHub Actions only serializes its own named concurrency group.
- Same-snapshot repeatability and tests were validated, not a full fault-injection campaign or an arbitrary-source generalized framework.
- Version-pinned dependencies include a pre-release dbt Core package; consider dependency refresh separately, after regression testing.
