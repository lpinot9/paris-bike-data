# paris-bike-data
Pipeline de données automatisé analysant le trafic cycliste parisien à partir des boucles électromagnétiques de comptage (Paris Open Data) et de données météorologiques.

![Data Stack](https://img.shields.io/badge/Stack-Snowflake%20|%20Fivetran%20|%20dbt%20|%20GitHub%20Actions-blue)
![dbt](https://img.shields.io/badge/dbt-1.8+-orange)
![License](https://img.shields.io/badge/License-MIT-green)

---

## 🏗️ Architecture du Pipeline

```text
[API Paris Open Data]
        │
        ▼ (GitHub Actions - Cron horaire)
  [Script Python]
        │
        ▼ (Webhook)
    [Fivetran]
        │ (Transit GCS)
        ▼
 [Snowflake RAW]
        │
        ▼ (dbt Core / Cloud)
 ┌──────────────────────────────────────────┐
 │ Staging      -> Typage, dédoublonnage    │
 │ Intermediate -> Spine temporel (pannes)  │
 │ Marts        -> Faits & Dimensions (BI)  │
 └──────────────────────────────────────────┘
        │
        ▼
 [Looker Studio / BI Dashboard]
