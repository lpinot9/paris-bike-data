{{ config(
    materialized='table'
) }}

with staging as (

    select * from {{ ref('stg_bike_traffic__counts') }}

),

ranked_counters as (

    select
        counter_id,
        counter_name,
        latitude,
        longitude,
        recorded_at,
        row_number() over (
            partition by counter_id
            order by recorded_at desc
        ) as rn
    from staging

),

latest_counter_info as (

    select
        counter_id,
        counter_name,
        latitude,
        longitude
    from ranked_counters
    where rn = 1

),

traffic_stats as (

    select
        counter_id,
        min(recorded_at) as first_seen_at,
        max(recorded_at) as last_seen_at,
        count(*) as total_records_count
    from staging
    group by counter_id

)

select
    c.counter_id,
    c.counter_name,
    c.latitude,
    c.longitude,
    s.first_seen_at,
    s.last_seen_at,
    s.total_records_count,
    -- Statut actif si des données ont été reçues récemment (moins de 7 jours)
    case
        when s.last_seen_at >= dateadd('day', -7, current_timestamp()) then true
        else false
    end as is_active
from latest_counter_info c
left join traffic_stats s
    on c.counter_id = s.counter_id