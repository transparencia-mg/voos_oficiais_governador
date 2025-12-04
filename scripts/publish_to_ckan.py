#!/usr/bin/env python3

import os
import sys
import glob
import argparse
import pandas as pd
import requests

CKAN_URL = os.getenv("CKAN_URL")
CKAN_API_KEY = os.getenv("CKAN_API_KEY")

if not CKAN_URL or not CKAN_API_KEY:
    print("ERRO: CKAN_URL e CKAN_API_KEY devem estar definidos nos secrets.", file=sys.stderr)
    sys.exit(1)

HEADERS = {"Authorization": CKAN_API_KEY}
DATASET_ID = "voos_oficiais_governador"  # nome do dataset no CKAN


def ensure_dataset():
    """Garante que o dataset existe; se não existir, cria."""
    r = requests.get(f"{CKAN_URL}/api/3/action/package_show",
                     params={"id": DATASET_ID},
                     headers=HEADERS)

    if r.status_code == 200 and r.json().get("success"):
        return r.json()["result"]

    payload = {
        "name": DATASET_ID,
        "title": "Voos Oficiais do Governador",
        "notes": "Dados de voos oficiais, publicados automaticamente via GitHub Actions."
    }

    r = requests.post(f"{CKAN_URL}/api/3/action/package_create",
                      headers=HEADERS, json=payload)
    r.raise_for_status()
    return r.json()["result"]


def upload_resource(dataset, file_path):
    file_name = os.path.basename(file_path)

    # valida o CSV
    df = pd.read_csv(file_path)
    required_cols = ["data", "origem", "destino"]
    missing = [c for c in required_cols if c not in df.columns]

    if missing:
        print(f"Arquivo {file_name} ignorado — colunas ausentes: {missing}")
        return

    print(f"Publicando {file_name} no CKAN...")

    # verifica resources existentes
    pkg = requests.get(f"{CKAN_URL}/api/3/action/package_show",
                       params={"id": DATASET_ID},
                       headers=HEADERS)
    pkg.raise_for_status()
    resources = pkg.json()["result"].get("resources", [])

    existing = next((r for r in resources if r.get("name") == file_name), None)

    files = {"upload": open(file_path, "rb")}

    if existing:
        print(f"Atualizando resource existente: {existing['id']}")
        r = requests.post(f"{CKAN_URL}/api/3/action/resource_update",
                          headers=HEADERS,
                          data={"id": existing["id"], "name": file_name},
                          files=files)
    else:
        print(f"Criando novo resource {file_name}")
        r = requests.post(f"{CKAN_URL}/api/3/action/resource_create",
                          headers=HEADERS,
                          data={"package_id": DATASET_ID, "name": file_name, "format": "CSV"},
                          files=files)

    r.raise_for_status()
    print("OK publicado:", r.json()["result"]["id"])


def main(pattern):
    dataset = ensure_dataset()

    files = glob.glob(pattern)
    if not files:
        print("Nenhum CSV encontrado com padrão:", pattern)
        return

    for f in files:
        try:
            upload_resource(dataset, f)
        except Exception as e:
            print("Erro ao publicar", f, e)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--pattern", default="voos_*.csv")
    args = parser.parse_args()
    main(args.pattern)


