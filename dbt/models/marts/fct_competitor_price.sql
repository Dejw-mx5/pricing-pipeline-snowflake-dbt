{#
  Incremental fact of competitor price observations.
  Only rows newer than the max captured_at already loaded are merged in.
#}
{{
    config(
        materialized='incremental',
        unique_key='price_event_id',
        incremental_strategy='merge'
    )
}}

with prices as (

    select * from {{ ref('stg_competitor_prices') }}

),

final as (

    select
        {{ dbt_utils.generate_surrogate_key(['product_id', 'competitor', 'captured_at']) }} as price_event_id,
        product_id,
        competitor,
        price,
        captured_at,
        loaded_at
    from prices

)

select * from final

{% if is_incremental() %}
where captured_at > (select coalesce(max(captured_at), '1900-01-01') from {{ this }})
{% endif %}
