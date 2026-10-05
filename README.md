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
        ▼ (Script python - Cron horaire)
  [Webhook]
        │
        ▼ (Fivetran)
  [Bucket Google Cloud temporaire contenant uniquement les données de J-1]
        │ (Fivetran)
        ▼
  [Snowflake RAW]
        │
        ▼ (dbt Core)
 ┌──────────────────────────────────────────┐
 │ Staging      -> Typage, dédoublonnage    │
 │ Intermediate -> Spine temporel (pannes)  │
 │ Marts        -> Faits & Dimensions (BI)  │
 └──────────────────────────────────────────┘
        │
        ▼
 [Data Studio]
```

## 🎯 Objectifs & Enjeux Métier

Ce projet simule la mise en place d'un pipeline d'ingénierie analytique pour une direction de la mobilité urbaine, exploitant les données des boucles à induction électromagnétiques de la Ville de Paris couplées aux observations météorologiques.

### Problématiques Métier & Décisionnelles
* **Mesure des flux pendulaires :** Identifier les axes saturés et quantifier l'indice de vélotaf (*Commute Ratio* — part du trafic 7h30-9h30 / 17h30-19h30 par rapport aux heures creuses).
* **Élasticité météo :** Calculer l'impact précis des intempéries (millimètres de pluie, rafales de vent, températures négatives) sur le volume d'usagers selon la typologie des pistes (coronapistes, voies sur berge, pistes bidirectionnelles).

### Défis d'Ingénierie Analytique (DataOps & IoT)
* **Traitement des pannes matérielles (Spine Temporel) :** Les boucles physiques subissent des coupures (travaux de voirie, arrachement de câbles). Une absence de ligne ne doit pas être confondue avec un passage nul : génération d'un `date_spine` horaire pour monitorer le taux de disponibilité (*uptime*) des capteurs.
* **Gouvernance & Qualité :** Application stricte de tests de schéma et de logique métier (unicité des relevés, cohérence des sens de circulation, détection des valeurs aberrantes).

---

## 🛠️ Stack Technique

L'architecture repose sur la *Modern Data Stack* avec une séparation rigoureuse du calcul, du stockage et de la modélisation logique.

| Couche | Outil / Technologie | Rôle & Justification |
| :--- | :--- | :--- |
| **Ingestion** | **GitHub Actions** | Exécution serverless d'un cron horaire interrogeant l'API REST v2.1 de Paris Open Data (0 € d'infrastructure). |
| **Transport & CDC** | **Fivetran (Webhooks)** | Ingestion managée par micro-lots avec transit temporaire sur Google Cloud Storage (Free Tier) et chargement automatisé. |
| **Data Warehouse** | **Snowflake (Enterprise)** | Stockage colonnaire, gestion du cycle de vie (Time Travel), isolation stricte des charges via RBAC et entrepôts dédiés (`X-Small` auto-suspendus). |
| **Transformation** | **dbt (data build tool)** | Modélisation en couches (`staging` $\rightarrow$ `intermediate` $\rightarrow$ `marts`), tests automatisés, documentation intégrée et gestion des incrémentaux. |
| **CI / CD** | **GitHub Actions** | Automatisation des tests de non-régression et compilation du graphe de dépendances dbt lors de chaque Pull Request. |
| **Reporting / BI** | **Looker Studio** | Visualisation décisionnelle connectée directement aux tables de faits et dimensions matérialisées. |

---

## ⚙️ Configuration & Secrets

Ce projet utilise des variables d'environnement pour sécuriser la connexion à Snowflake et au webhook Fivetran. 

### 1. En local
1. Dupliquer le fichier `.env.example` à la racine et  le renommer en `.env` :
2. Renseigner les identifiants réels dans le fichier .env nouvellement créé. (Note : Le fichier .env est ignoré par Git et ne sera jamais partagé).

### 2. Sur GitHub Actions (CI/CD)
1. Aller dans Settings > Secrets and variables > Actions.

2. Cliquer sur New repository secret pour chaque variable suivante :

Va dans Settings > Secrets and variables > Actions.

Clique sur New repository secret pour chaque variable suivante :

SNOWFLAKE_ACCOUNT

SNOWFLAKE_USER

SNOWFLAKE_PASSWORD

SNOWFLAKE_ROLE

SNOWFLAKE_WAREHOUSE

SNOWFLAKE_DATABASE

SNOWFLAKE_SCHEMA

FIVETRAN_WEBHOOK_URL
