"""
Generate synthetic pricing feeds and load them into the Snowflake RAW schema.

Run for two different dates to see incremental loading and SCD2 in action:
    python ingestion/generate_and_load.py --date 2026-01-01
    python ingestion/generate_and_load.py --date 2026-01-02
"""
import argparse
import os
import random
from datetime import datetime

import snowflake.connector
from dotenv import load_dotenv
from faker import Faker

load_dotenv()
fake = Faker()

CATEGORIES = ["Connectors", "Sensors", "Cables", "Controllers", "Power"]
COMPETITORS = ["AlphaParts", "BetaSupply", "GammaDist"]
N_PRODUCTS = 50


def connect():
    return snowflake.connector.connect(
        account=os.environ["SNOWFLAKE_ACCOUNT"],
        user=os.environ["SNOWFLAKE_USER"],
        password=os.environ["SNOWFLAKE_PASSWORD"],
        role=os.environ.get("SNOWFLAKE_ROLE"),
        warehouse=os.environ["SNOWFLAKE_WAREHOUSE"],
        database=os.environ["SNOWFLAKE_DATABASE"],
        schema=os.environ.get("SNOWFLAKE_SCHEMA", "RAW"),
    )


def ensure_tables(cur):
    cur.execute("CREATE SCHEMA IF NOT EXISTS RAW")
    cur.execute("""
        CREATE TABLE IF NOT EXISTS RAW.PRODUCTS (
            product_id    INT,
            product_name  STRING,
            category      STRING,
            cost          NUMBER(12,2),
            loaded_at     TIMESTAMP_NTZ
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS RAW.COMPETITOR_PRICES (
            product_id   INT,
            competitor   STRING,
            price        NUMBER(12,2),
            captured_at  TIMESTAMP_NTZ,
            loaded_at    TIMESTAMP_NTZ
        )
    """)


def load_products(cur, run_ts, seed):
    """Full refresh of products; on the 2nd+ run some costs drift (drives SCD2)."""
    random.seed(seed)
    cur.execute("DELETE FROM RAW.PRODUCTS")
    rows = []
    for pid in range(1, N_PRODUCTS + 1):
        base = round(random.uniform(5, 500), 2)
        # nudge ~20% of costs on later runs so the snapshot captures a new version
        cost = round(base * random.choice([1.0, 1.0, 1.0, 1.0, 1.08]), 2)
        rows.append((pid, f"{random.choice(CATEGORIES)} Part {pid}",
                     random.choice(CATEGORIES), cost, run_ts))
    cur.executemany(
        "INSERT INTO RAW.PRODUCTS (product_id, product_name, category, cost, loaded_at) "
        "VALUES (%s, %s, %s, %s, %s)", rows)
    return len(rows)


def load_prices(cur, run_ts, seed):
    """Append a day's competitor price observations (drives incremental load)."""
    random.seed(seed + 1)
    rows = []
    for pid in range(1, N_PRODUCTS + 1):
        for comp in COMPETITORS:
            price = round(random.uniform(5, 550), 2)
            rows.append((pid, comp, price, run_ts, run_ts))
    cur.executemany(
        "INSERT INTO RAW.COMPETITOR_PRICES (product_id, competitor, price, captured_at, loaded_at) "
        "VALUES (%s, %s, %s, %s, %s)", rows)
    return len(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", required=True, help="feed date YYYY-MM-DD")
    args = ap.parse_args()
    run_ts = datetime.strptime(args.date, "%Y-%m-%d")
    seed = int(run_ts.timestamp())

    conn = connect()
    try:
        cur = conn.cursor()
        ensure_tables(cur)
        p = load_products(cur, run_ts, seed)
        c = load_prices(cur, run_ts, seed)
        conn.commit()
        print(f"[{args.date}] loaded {p} products, {c} competitor prices into RAW")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
