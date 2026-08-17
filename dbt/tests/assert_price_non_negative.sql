-- Singular data test: no competitor price should ever be negative.
-- Fails (returns rows) if the invariant is violated.
select
    price_event_id,
    product_id,
    competitor,
    price
from {{ ref('fct_competitor_price') }}
where price < 0
