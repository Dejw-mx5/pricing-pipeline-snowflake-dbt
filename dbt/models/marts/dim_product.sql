{#
  Current-state product dimension, sourced from the SCD2 snapshot
  (dbt_valid_to is null = the current version of each product).
#}
with current_cost as (

    select
        product_id,
        product_name,
        category,
        unit_cost,
        dbt_valid_from as cost_effective_from
    from {{ ref('snap_product_cost') }}
    where dbt_valid_to is null

)

select
    product_id,
    product_name,
    category,
    unit_cost,
    cost_effective_from
from current_cost
