import pandas as pd
from pathlib import Path
from .load_roadmap import load_roadmap_data
from .load_report import load_report_data

DATA_PATH = Path("data")

def load_combined_dataset():

    roadmap_file = DATA_PATH / "roadmap.xlsx"
    report_file = DATA_PATH / "report.xlsx"

    df_main = load_roadmap_data(roadmap_file)
    df_dim = load_report_data(report_file)

    # (Opzionale) arricchimento futuro con anagrafica:
    # df_main = df_main.merge(df_dim, on="impianto", how="left")

    return df_main
