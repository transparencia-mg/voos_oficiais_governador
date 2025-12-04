import pandas as pd
import glob
import os

INPUT_PATTERN = "data/voos_*.csv"
OUTPUT_FOLDER = "data/normalized/"

os.makedirs(OUTPUT_FOLDER, exist_ok=True)

for f in glob.glob(INPUT_PATTERN):
    print("Processando:", f)

    # LER CSV COM ; e LATIN1
    df = pd.read_csv(f, dtype=str, sep=";", encoding="latin1")

    # MAPA DE RENOMEAÇÃO
    rename_map = {
        "Número DB": "Diario_de_Bordo",
        "Horas Voadas": "Horas_Voadas",
        "Órgáo": "Orgao",
        "Órgáos": "Orgao",
        "Órgão": "Orgao",
        "Órgãos": "Orgao",
        "Data": "Data",
        "Origem": "Origem",
        "Destino": "Destino",
        "Aeronave": "Aeronave",
        "Histórico": "Situacao",
        "Nome": "Passageiros",
    }

    # RENOMEAR COLUNAS
    df = df.rename(columns=rename_map)

    # LIMPAR ESPAÇOS E ACENTOS COMUNS NAS COLUNAS
    df.columns = df.columns.str.strip()

    # CRIAR COLUNA ANO
    if "Data" in df.columns:
        df["Ano"] = df["Data"].str[-4:]

    # SALVAR NORMALIZADO
    out = os.path.join(OUTPUT_FOLDER, os.path.basename(f))
    df.to_csv(out, index=False, encoding="utf-8")
    print("Gerado:", out)




