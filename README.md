# Pricing ELT — Snowflake · dbt · Airflow

End-to-end pricing ELT pipeline on Snowflake and dbt. Ingests competitor pricing feeds, loads them raw into Snowflake, transforms through staging and marts layers, tracks product cost history with an SCD Type 2 snapshot, and loads price observations incrementally.

## Architecture

```
                   ┌──────────────┐
  pricing feeds ──►│  ingestion   │  Python → Snowflake RAW schema
                   │generate_and  │
                   │  _load.py    │
                   └──────┬───────┘
                          │
          ┌───────────────▼─────────────────┐
          │            Snowflake             │
          │  RAW ──dbt──► STAGING ──► MARTS  │
          │         └──► SNAPSHOTS (SCD2)    │
          └───────────────┬─────────────────┘
                          │
      ┌─────────────────────▼──────────────────────┐
      │                 Airflow DAG                  │
      │  load ► dbt run ► dbt snapshot ► dbt test   │
      └─────────────────────────────────────────────┘

  GitHub Actions: PR ► sqlfluff lint ► dbt build (CI schema)
```

## Data model

**Sources (RAW schema)**
- `products` — product_id, product_name, category, cost, loaded_at
- `competitor_prices` — product_id, competitor, price, captured_at, loaded_at

**Staging**
- `stg_products` — typed, renamed columns
- `stg_competitor_prices` — typed, renamed columns

**Snapshot (SCD2)**
- `snap_product_cost` — one row per product-cost version with `dbt_valid_from` / `dbt_valid_to`; `dbt_valid_to IS NULL` = current version

**Marts**
- `dim_product` — current product dimension sourced from the snapshot
- `fct_competitor_price` — incremental fact of price observations, merged on `(product_id, competitor, captured_at)`
- `fct_price_position` — our unit cost vs competitor min/avg/max; `price_index = unit_cost / avg(competitor_price)`

## Setup

**1. Snowflake**

Sign up for a free trial. Create the warehouse and database:

```sql
CREATE WAREHOUSE IF NOT EXISTS WH_DEV WAREHOUSE_SIZE=XSMALL AUTO_SUSPEND=60;
CREATE DATABASE IF NOT EXISTS PRICING;
CREATE SCHEMA IF NOT EXISTS PRICING.RAW;
```

**2. Python env**

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env    # fill in Snowflake credentials
```

**3. Load raw data**

Run twice with different dates to populate incremental history and trigger SCD2 changes:

```bash
python ingestion/generate_and_load.py --date 2026-01-01
python ingestion/generate_and_load.py --date 2026-01-02
```

**4. dbt**

```bash
cd dbt
cp profiles.example.yml ~/.dbt/profiles.yml
dbt deps
dbt snapshot
dbt run
dbt test
dbt docs generate && dbt docs serve
```

`dbt snapshot` must run before `dbt run` — `dim_product` depends on the snapshot table.

