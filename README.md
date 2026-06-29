# DataGuard SG 🛡️

> Production-ready data quality pipeline for financial payment data.  
> Built for a Singapore fintech context using CMS Open Payments (15.4M rows).

[![CI](https://github.com/juliazam/dataguard-sg/actions/workflows/ci.yml/badge.svg)](https://github.com/juliazam/dataguard-sg/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.11%20%7C%203.12-blue)]()
[![Docker](https://img.shields.io/badge/docker-ready-blue)]()
[![Tests](https://img.shields.io/badge/tests-25%20passed-brightgreen)]()
[![Coverage](https://img.shields.io/badge/coverage-63%25-yellow)]()
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

## The Problem

Financial data pipelines often process millions of records without automated 
quality checks — errors surface only in downstream analytics, long after 
ingestion.

**CMS Open Payments** publishes 15.4 million payment records annually between 
pharmaceutical companies and healthcare providers. Profiling a 10,000-row 
sample revealed 117 data quality alerts: 15+ constant columns carrying no 
information, 40+ columns with imbalance up to 99.8%, and a heavily skewed 
payment distribution (γ1 = 49.6). Schema documentation did not match actual 
data values — a silent data contract violation.

**DataGuard SG** intercepts these issues at ingestion, before they reach 
analytics:
- Row-level validation catches schema violations (Pydantic)
- Statistical checks flag distributional anomalies (Great Expectations)  
- Every pipeline run is fully traceable (Data Lineage)
- Alerts fire when invalid record rate exceeds 5% threshold

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      DataGuard SG Pipeline                   │
└─────────────────────────────────────────────────────────────┘

  CMS Open Payments API (15.4M rows)
           │
           ▼
  ┌─────────────────┐
  │   1. FETCH      │  fetch_data() — sequential batches with offset tracking
  └────────┬────────┘
           │ DataFrame
           ▼
  ┌─────────────────┐
  │   2. VALIDATE   │  Pydantic — row-level schema validation
  └────────┬────────┘
           │ valid_payments, validation_errors
           ▼
  ┌─────────────────┐
  │ 3. RECONCILE    │  reconcile_counts() — no rows lost or duplicated
  └────────┬────────┘
           │
           ▼
  ┌─────────────────┐
  │ 4. GE CHECKPOINT│  7 Expectations — statistical dataset-level checks
  └────────┬────────┘
           │
           ▼
  ┌─────────────────┐
  │   5. ALERTING   │  threshold-based alerts (email + log levels)
  └────────┬────────┘
           │
           ▼
  ┌─────────────────┐
  │  6. SAVE OUTPUT │  validated_payments_{run_id}.csv → ready for DWH
  └─────────────────┘

  Every step → LineageTracker (JSONL audit log)
```

## Tech Stack

| Tool | Purpose |
|------|---------|
| **Python 3.11/3.12** | Core language |
| **Pydantic v2** | Row-level schema validation and type coercion |
| **Great Expectations 1.x** | Statistical dataset-level quality checks |
| **fg-data-profiling** | Automated EDA and data quality profiling |
| **pandas** | Data manipulation and batch processing |
| **Docker + docker-compose** | Containerisation and reproducible runs |
| **GitHub Actions** | CI/CD — black, flake8, mypy, pytest on every push |
| **pytest** | 25 tests: unit, integration, contract |

## Project Structure

```
dataguard-sg/
├── src/dataguard/
│   ├── models.py          # Pydantic Payment model + enums
│   ├── loader.py          # CMS API client with retry logic
│   ├── validator.py       # Row-level Pydantic validation
│   ├── ge_validator.py    # Great Expectations checkpoint
│   ├── profiler.py        # fg-data-profiling HTML report
│   ├── reconciliation.py  # Row count reconciliation
│   ├── lineage.py         # Audit log (JSONL)
│   ├── alerts.py          # Threshold-based alerting
│   ├── pipeline.py        # Orchestrates all steps
│   └── main.py            # Entry point (argparse)
├── tests/
│   ├── unit/              # Models, alerts, reconciliation, validator
│   ├── integration/       # Full pipeline with mocked API
│   └── contract/          # JSON Schema contract tests
├── contracts/
│   └── transaction_contract.json  # JSON Schema data contract
├── .github/workflows/
│   └── ci.yml             # GitHub Actions CI/CD
├── Dockerfile             # Multi-stage build
├── docker-compose.yml     # Pipeline + volumes
└── config.yaml            # All configuration in one place
```

## How to Run

### Prerequisites
- Docker Desktop
- Python 3.11+

### Option 1 — Docker (recommended)

```bash
git clone https://github.com/juliazam/dataguard-sg.git
cd dataguard-sg
docker-compose up
```

Pipeline runs automatically, processes 500 rows, saves output to `data/output/`.  
On the next run, it continues from where it left off (offset tracking).

### Option 2 — Local

```bash
git clone https://github.com/juliazam/dataguard-sg.git
cd dataguard-sg
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # Mac/Linux
pip install -e ".[dev]"
python src/dataguard/main.py --n-rows 500
```

### Configure batch size

```bash
# Process 1000 rows per run
python src/dataguard/main.py --n-rows 1000
```

## How to Run Tests

```bash
# All tests with coverage
pytest -v

# By type
pytest tests/unit/        -v
pytest tests/integration/ -v
pytest tests/contract/    -v
```

Expected output: **25 passed**, coverage **63%** across core modules.

## Example Output

### Pipeline run

```
2026-06-16 17:05:06 | INFO  | dataguard.loader         | Requested: 500 rows, fetched: 500 rows after deduplication
2026-06-16 17:05:06 | INFO  | dataguard.reconciliation | Data reconciliation successful. All 500 records accounted for (499 valid, 1 invalid).
2026-06-16 17:05:06 | INFO  | dataguard.alerts         | Pipeline successfully passed all validations. Data quality metrics are clean.
```

### Pipeline result

```json
{
  "pipeline_run_id": "9af34b65-ee9c-4cd6-bb69-8e02860285c4",
  "rows_fetched": 500,
  "rows_valid": 499,
  "rows_invalid": 1,
  "reconciliation": {
    "reconciled": true,
    "discrepancy": 0
  },
  "ge_success": true,
  "alert_result": {
    "invalid_rate": 0.002,
    "threshold_exceeded": false,
    "alert_sent": false
  }
}
```

### Lineage log (data/output/lineage_log.jsonl)

Each pipeline run writes 6 audit records — one per step:
`fetch` → `validate` → `reconciliation` → `ge_checkpoint` → `alerting` → `save_output`

### Data profiling report

Run `src/dataguard/profiler.py` to generate `reports/profiling/profile_report.html` —  
an interactive HTML report with distributions, correlations, and 117 data quality alerts
on a 10,000-row random sample.

## Notes

### Data source
[CMS Open Payments 2024](https://openpaymentsdata.cms.gov/datasets) —  
public dataset of payments from pharmaceutical companies to healthcare providers.  
15,385,047 rows, updated January 2026.

### Design decisions
- **Soft enum for `nature_of_payment`** — CMS documentation lists 18 categories,  
  but actual data uses different formatting and wording. A strict enum would reject  
  ~4% of valid records. Great Expectations monitors for unexpected values instead.
- **Sequential offset tracking** — pipeline remembers the last processed row  
  across runs (`data/output/last_offset.json`), enabling incremental processing.
- **Saving validated output** — pipeline saves only valid records to  
  `data/output/validated_payments_{run_id}.csv`, ready for downstream loading  
  into a data warehouse. Transformation and loading are out of scope.

### Limitations
- API rate limits occasionally cause timeouts (retry logic handles up to 3 attempts)
- `loader.py` is not covered by unit tests — HTTP client testing requires  
  additional mocking infrastructure beyond project scope
- Email alerting is a placeholder — integrate SendGrid or AWS SES for production use