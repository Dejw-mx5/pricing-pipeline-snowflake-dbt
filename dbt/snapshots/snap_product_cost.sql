{#
  SCD Type 2 history of product unit cost.
  dbt tracks changes to `unit_cost` and maintains:
    dbt_valid_from / dbt_valid_to  (NULL dbt_valid_to = current version)
#}
{% snapshot snap_product_cost %}

    {{
        config(
            target_schema='snapshots',
            unique_key='product_id',
            strategy='check',
            check_cols=['unit_cost']
        )
    }}

    select
        product_id,
        product_name,
        category,
        unit_cost,
        loaded_at
    from {{ ref('stg_products') }}

{% endsnapshot %}
