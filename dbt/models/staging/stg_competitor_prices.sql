with source as (

    select * from {{ source('raw', 'competitor_prices') }}

),

renamed as (

    select
        product_id,
        competitor,
        price::number(12, 2) as price,
        captured_at,
        loaded_at
    from source

)

select * from renamed
