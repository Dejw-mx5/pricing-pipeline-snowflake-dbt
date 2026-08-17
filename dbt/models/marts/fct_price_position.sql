{#
  Our cost vs the competitor market, per product.
  price_index = our unit_cost / market average price (lower = we're cheaper).
#}
with prices as (

    select
        product_id,
        min(price) as competitor_min_price,
        avg(price) as competitor_avg_price,
        max(price) as competitor_max_price,
        count(*)   as observation_count
    from {{ ref('fct_competitor_price') }}
    group by product_id

),

product as (

    select product_id, product_name, category, unit_cost
    from {{ ref('dim_product') }}

)

select
    p.product_id,
    p.product_name,
    p.category,
    p.unit_cost,
    pr.competitor_min_price,
    pr.competitor_avg_price,
    pr.competitor_max_price,
    pr.observation_count,
    round(p.unit_cost / nullif(pr.competitor_avg_price, 0), 3) as price_index
from product p
left join prices pr on pr.product_id = p.product_id
