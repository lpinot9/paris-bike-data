{{ config(
    materialized='table'
) }}

with staging as (

    select * from {{ ref('stg_bike_traffic__counts') }}

),

enriched_traffic as (

    select
        -- Clé surrogate synthétique pour la table de faits
        {{ dbt_utils.generate_surrogate_key(['counter_id', 'recorded_at']) if execute and var('use_dbt_utils', false) else 'md5(concat(counter_id, \'_\', recorded_at))' }} as traffic_event_id,
        
        -- Clé étrangère vers dim_bike_counters
        counter_id,
        
        -- Dimensions temporelles
        recorded_at,
        recorded_date,
        recorded_hour,
        dayname(recorded_at) as day_of_week_name,
        dayofweek(recorded_at) as day_of_week_num,
        
        -- Indicateurs de contexte d'usage
        case 
            when dayofweek(recorded_at) in (0, 6) then true 
            else false 
        end as is_weekend,
        
        case 
            when recorded_hour between 7 and 9 then 'Morning Peak'
            when recorded_hour between 17 and 19 then 'Evening Peak'
            when recorded_hour between 10 and 16 then 'Daytime Off-Peak'
            else 'Night'
        end as time_window,
        
        -- Métriques
        hourly_bike_count,
        
        -- Traçabilité
        fivetran_synced_at

    from staging

)

select * from enriched_traffic