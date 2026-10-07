import os
import requests
from datetime import datetime, timedelta
import dlt

# Gestion transparente de l'environnement local vs GitHub Actions
try:
    from dotenv import load_dotenv
    load_dotenv()
except ModuleNotFoundError:
    pass




def main():
    # 1. Définition de la fenêtre temporelle (J-3 pour pallier les retards d'API)
    debut = (datetime.now() - timedelta(days=3)).strftime('%Y-%m-%d')
    aujourdhui = datetime.now().strftime('%Y-%m-%d')
    where_clause = f"date >= '{debut}' AND date < '{aujourdhui}'"
    
    # 2. Appel de l'API OpenData Paris (export complet en un seul JSON)
    url = "https://opendata.paris.fr/api/explore/v2.1/catalog/datasets/comptage-velo-donnees-compteurs/exports/json"
    params = {
        "where": where_clause
    }
    
    print(f"Extraction des données depuis l'API pour la période : {where_clause}")
    response = requests.get(url, params=params, timeout=60)
    response.raise_for_status()
    
    raw_records = response.json()
    print(f"{len(raw_records)} lignes récupérées.")
    
    if not raw_records:
        print("Aucune donnée à traiter. Fin du script.")
        return

    # 3. Traitement et aplatissement des coordonnées
    cleaned_records = []
    for record in raw_records:
        coords = record.get("coordinates") or {}
        
        cleaned_records.append({
            "id_compteur": record.get("id_compteur"),
            "nom_compteur": record.get("nom_compteur"),
            "id": record.get("id"),
            "date": record.get("date"),
            "sum_counts": record.get("sum_counts"),
            "latitude": float(coords.get("lat")) if coords.get("lat") is not None else None,
            "longitude": float(coords.get("lon")) if coords.get("lon") is not None else None,
            "installation_date": record.get("installation_date")
        })

    # 4. Ingestion directe dans Snowflake via dlt
    print("Initialisation du pipeline dlt vers Snowflake...")
   


    destination = dlt.destinations.snowflake(
        credentials={
            "host": "NNQYAZT-ZJ00048",
            "username": os.environ.get("SNOWFLAKE_USER"),
            "password": os.environ.get("SNOWFLAKE_PASSWORD"),
            "database": os.environ.get("SNOWFLAKE_DATABASE", "BIKE_MOBILITY"),
            "warehouse": os.environ.get("SNOWFLAKE_WAREHOUSE", "FIVETRAN_WH"),
            "role": os.environ.get("SNOWFLAKE_ROLE", "FIVETRAN_ROLE"),
        }
    )

    pipeline = dlt.pipeline(
        pipeline_name="paris_bikes_pipeline",
        destination=destination,
        dataset_name="raw_bike_traffic"
    )


    print(f"Chargement de {len(cleaned_records)} lignes dans Snowflake (table 'event')...")
    load_info = pipeline.run(
        cleaned_records,
        table_name="EVENT",
        write_disposition="append"
    )

    print(load_info)
    print("Synchronisation Snowflake terminée avec succès.")

if __name__ == "__main__":
    main()