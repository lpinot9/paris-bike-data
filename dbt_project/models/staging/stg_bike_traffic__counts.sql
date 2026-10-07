{{ config(
    materialized='view'
) }}

with source_data as (

    select * from {{ source('raw_bike_traffic', 'EVENT') }}

),

renamed_and_cast as (

    select
        -- Identifiants & clés métier
        trim(id_compteur::varchar) as counter_id,
        trim(nom_compteur::varchar) as counter_name,
        
        -- Dimensions temporelles ajustées sur le fuseau de Paris
        convert_timezone('UTC', 'Europe/Paris', date::timestamp_ntz) as recorded_at,
        date_trunc('day', convert_timezone('UTC', 'Europe/Paris', date::timestamp_ntz))::date as recorded_date,
        date_part('hour', convert_timezone('UTC', 'Europe/Paris', date::timestamp_ntz))::integer as recorded_hour,
        
        -- Métriques de comptage
        coalesce(sum_counts::integer, 0) as hourly_bike_count,
        
        -- Géolocalisation
        latitude::float as latitude,
        longitude::float as longitude,
        
        -- Métadonnées techniques dlt
        _dlt_load_id::varchar as dlt_load_id

    from source_data
    where
        -- Exclusion des enregistrements d'initialisation ou incomplets
        id_compteur is not null
        and date is not null

),

deduplicated as (

    -- Dédoublonnage sur la clé naturelle : conservation de l'extraction la plus récente
    select
        *,
        row_number() over (
            partition by counter_id, recorded_at
            order by dlt_load_id desc
        ) as row_num
    from renamed_and_cast

)

select
    counter_id,
    counter_name,
    recorded_at,
    recorded_date,
    recorded_hour,
    hourly_bike_count,
    latitude,
    longitude,
    dlt_load_id
from deduplicated
where row_num = 1