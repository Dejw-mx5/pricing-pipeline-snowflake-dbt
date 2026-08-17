with source as (

    select * from {{ source('raw', 'products') }}

),

renamed as (

    select
        product_id,
        product_name,
        category,
        cost::number(12, 2) as unit_cost,
        loaded_at
    from source

)

select * from renamed
