import pandas as pd

def load_roadmap_data(file_path):

    sheets_acc = ["ACC ROMA", "ACC MILANO", "ACC PADOVA"]
    sheets_airports = ["Aeroporti Strategici", "Regional Airports"]

    frames = []

    for s in sheets_acc:
        try:
            df = pd.read_excel(file_path, sheet_name=s, engine="openpyxl")
            df_norm = normalize_acc(df, s)
            frames.append(df_norm)
        except:
            pass

    for s in sheets_airports:
        try:
            df = pd.read_excel(file_path, sheet_name=s, engine="openpyxl")
            df_norm = normalize_airports(df, s)
            frames.append(df_norm)
        except:
            pass

    df_all = pd.concat(frames, ignore_index=True)

    df_all = (
        df_all.groupby(["anno","mese","impianto","tipo_impianto"], as_index=False)
              .sum()
    )

    return df_all

def normalize_acc(df, impianto_name):

    df = df.rename(columns={
        "PRESENTI": "hc_effettivi",
        "FABBISOGNO HC TEORICO": "hc_previsti",
    })

    df["impianto"] = impianto_name
    df["tipo_impianto"] = "ACC"

    df["fte_effettivi"] = df["hc_effettivi"]
    df["fte_previsti"] = df["hc_previsti"]

    df["ingressi"] = df.get("ingressi", 0)
    df["cessazioni"] = df.get("cessazioni", 0)

    return df[[
        "anno","mese","impianto","tipo_impianto",
        "hc_effettivi","hc_previsti",
        "fte_effettivi","fte_previsti",
        "ingressi","cessazioni"
    ]]

def normalize_airports(df, sheet_name):

    df = df.rename(columns={
        "PRESENTI": "hc_effettivi",
        "TEORICI": "hc_previsti",
        "IMPIANTO": "impianto"
    })

    df["tipo_impianto"] = "AEROPORTO"

    df["fte_effettivi"] = df["hc_effettivi"]
    df["fte_previsti"] = df["hc_previsti"]

    if "ingressi" not in df: df["ingressi"] = 0
    if "cessazioni" not in df: df["cessazioni"] = 0

    return df[[
        "anno","mese","impianto","tipo_impianto",
        "hc_effettivi","hc_previsti",
        "fte_effettivi","fte_previsti",
        "ingressi","cessazioni"
    ]]
