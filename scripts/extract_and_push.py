import os
import sys
import json
import requests

from dotenv import load_dotenv
load_dotenv()  # Charge automatiquement les variables définies dans .env

# Récupération de l'URL via variable d'environnement (sécurité)
FIVETRAN_WEBHOOK_URL = os.environ.get("FIVETRAN_WEBHOOK_URL")

if not FIVETRAN_WEBHOOK_URL:
    print("Erreur : la variable FIVETRAN_WEBHOOK_URL est absente.")
    sys.exit(1)

PARIS_API_URL = (
    "https://opendata.paris.fr/api/explore/v2.1/catalog/datasets/"
    "comptage-velo-donnees-compteurs/records"
    "?limit=100&order_by=date%20desc"
)

def run():
    print("1. Appel à l'API Paris Open Data...")
    try:
        res = requests.get(PARIS_API_URL, timeout=30)
        res.raise_for_status()
    except requests.RequestException as e:
        print(f"Erreur lors de la requête Open Data : {e}")
        sys.exit(1)

    records = res.json().get("results", [])
    print(f"2. {len(records)} enregistrements récupérés.")

    if not records:
        print("Aucune donnée disponible.")
        return

    # Normalisation du payload JSON pour Fivetran
    payload = []
    for row in records:
        coords = row.get("coordinates") or {}
        
        lat = coords.get("lat")
        lon = coords.get("lon")

        payload.append({
            "id_compteur": row.get("id_compteur"),
            "nom_compteur": row.get("nom_compteur"),
            "id": row.get("id"),
            "date": row.get("date"),
            "sum_counts": row.get("sum_counts"),
            "latitude": lat,
            "longitude": lon,
            "installation_date": row.get("date_installation")
        })

    print("3. Envoi du lot vers le webhook Fivetran...")
    try:
        fivetran_res = requests.post(
            FIVETRAN_WEBHOOK_URL,
            headers={"Content-Type": "application/json"},
            data=json.dumps(payload),
            timeout=30
        )
        fivetran_res.raise_for_status()
        print(f"Succès : {len(payload)} lignes transmises à Fivetran.")
    except requests.RequestException as e:
        print(f"Erreur lors de l'envoi à Fivetran : {e}")
        sys.exit(1)

if __name__ == "__main__":
    run()