import os
import requests
from datetime import datetime, timedelta

# Gestion transparente de l'environnement local vs GitHub Actions
try:
    from dotenv import load_dotenv
    load_dotenv()
except ModuleNotFoundError:
    pass

def main():
    # 1. Définition de la fenêtre temporelle temporelle (J-1)
    hier = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    aujourdhui = datetime.now().strftime('%Y-%m-%d')
    where_clause = f"date >= '{hier}' AND date < '{aujourdhui}'"
    
    # 2. Appel de l'API avec le filtre
    url = "https://opendata.paris.fr/api/explore/v2.1/catalog/datasets/comptage-velo-donnees-compteurs/exports/json"
    params = {
        "where": where_clause
    }
    
    print(f"Extraction des données depuis l'API pour la période : {where_clause}")
    response = requests.get(url, params=params)
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

    # 4. Envoi par lots (chunks) vers le Webhook Fivetran
    webhook_url = os.environ.get("FIVETRAN_WEBHOOK_URL")
    if not webhook_url:
        raise ValueError("La variable d'environnement FIVETRAN_WEBHOOK_URL est manquante.")
        
    headers = {"Content-Type": "application/json"}
    chunk_size = 2000
    
    print(f"Début de l'envoi vers Fivetran par lots de {chunk_size}...")
    
    for i in range(0, len(cleaned_records), chunk_size):
        chunk = cleaned_records[i : i + chunk_size]
        push_response = requests.post(webhook_url, json=chunk, headers=headers)
        push_response.raise_for_status()
        print(f"Lot {i // chunk_size + 1} envoyé (Code: {push_response.status_code})")

    print("Synchronisation terminée avec succès.")

if __name__ == "__main__":
    main()