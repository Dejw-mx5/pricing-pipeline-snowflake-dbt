"""
Airflow DAG: orchestrates the daily pricing ELT.

  generate_and_load  ->  dbt deps  ->  dbt run  ->  dbt snapshot  ->  dbt test

Assumes the repo is mounted and Snowflake creds are available as env vars
(e.g. from an Airflow Connection or the Astro .env). Adjust PROJECT_DIR /
DBT_DIR to match your deployment.
"""
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator

PROJECT_DIR = "/usr/local/airflow/include/pricing-elt"
DBT_DIR = f"{PROJECT_DIR}/dbt"

default_args = {
    "owner": "david",
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    dag_id="pricing_elt",
    description="Competitor-pricing ELT: ingest -> dbt build -> SCD2 snapshot -> test",
    start_date=datetime(2026, 1, 1),
    schedule="@daily",
    catchup=False,
    default_args=default_args,
    tags=["snowflake", "dbt", "elt"],
) as dag:

    ingest = BashOperator(
        task_id="generate_and_load",
        bash_command=(
            f"cd {PROJECT_DIR} && "
            "python ingestion/generate_and_load.py --date {{ ds }}"
        ),
    )

    dbt_deps = BashOperator(
        task_id="dbt_deps",
        bash_command=f"cd {DBT_DIR} && dbt deps",
    )

    dbt_run = BashOperator(
        task_id="dbt_run",
        bash_command=f"cd {DBT_DIR} && dbt run --target dev",
    )

    dbt_snapshot = BashOperator(
        task_id="dbt_snapshot",
        bash_command=f"cd {DBT_DIR} && dbt snapshot --target dev",
    )

    dbt_test = BashOperator(
        task_id="dbt_test",
        bash_command=f"cd {DBT_DIR} && dbt test --target dev",
    )

    # snapshot runs before marts refresh in a real run; kept linear here for clarity
    ingest >> dbt_deps >> dbt_snapshot >> dbt_run >> dbt_test
