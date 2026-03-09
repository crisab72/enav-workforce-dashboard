import pandas as pd
from pathlib import Path
import streamlit as st

ITALIAN_MONTHS = {
    "GENNAIO": 1,
    "FEBBRAIO": 2,
    "MARZO": 3,
    "APRILE": 4,
    "MAGGIO": 5,
    "GIUGNO": 6,
    "LUGLIO": 7,
    "AGOSTO": 8,
    "SETTEMBRE": 9,
    "OTTOBRE": 10,
    "NOVEMBRE": 11,
    "DICEMBRE": 12,
}

def load_roadmap_data(file_path: Path) -> pd.DataFrame:
    """Legge roadmap.xlsx e restituisce il dataset unificato per la dashboard."""

    xls = pd.ExcelFile(file_path, engine="openpyxl")
    sheet_names = xls.sheet_names

    frames = []

    for sheet in sheet_names:
        sheet_up = sheet.upper()

        # saltiamo fogli “tecnici” che non contengono dati di organico mensile
        if sheet_up in ["ASSEGNAZIONI", "ASSEGNZIONI", "TOT", "SUMMARY"]:
            continue

        df_raw = pd.read_excel(file_path, sheet_name=sheet, engine="openpyxl", header=None)

        if "ACC" in sheet_up:
            # fogli tipo ACC ROMA / ACC MILANO / ACC PADOVA
            df_norm = parse_acc_layout(df_raw, sheet_up)
        else:
            # fogli tipo FIUMICINO, PALERMO, CIAMPINO, ecc. + eventuali “Aeroporti Strategici / Regional Airports”
            df_norm = parse_airport_layout(df_raw, sheet_up)

        if df_norm is not None and not df_norm.empty:
            frames.append(df_norm)

    if not frames:
        st.error(
            "⚠️ Nessun foglio valido trovato in roadmap.xlsx. "
            "Dobbiamo ancora affinare il parser per la struttura dei fogli."
        )
        # DataFrame vuoto con colonne attese
        return pd.DataFrame(
            columns=[
                "anno",
                "mese",
                "impianto",
                "tipo_impianto",
                "hc_effettivi",
                "hc_previsti",
                "fte_effettivi",
                "fte_previsti",
                "ingressi",
                "cessazioni",
            ]
        )

    df_all = pd.concat(frames, ignore_index=True)

    # Aggregazione finale per sicurezza
    df_all = (
        df_all.groupby(
            ["anno", "mese", "impianto", "tipo_impianto"], as_index=False
        )
        .sum()
    )

    return df_all


def parse_airport_layout(df_raw: pd.DataFrame, sheet_name: str) -> pd.DataFrame:
    """
    Parsing fogli aeroportuali tipo FIUMICINO / PALERMO / CIAMPINO, ecc.
    Layout:
    - colonna mesi con stringhe (GENNAIO, FEBBRAIO, ...)
    - colonna anni con valori 2026/2027/... (spesso in celle unite)
    - una riga contiene le intestazioni 'FABBISOGNO HC TEORICO', 'PRESENTI', 'DELTA', 'Mobilità', 'Cessazioni', 'Temporanei'
    """

    df = df_raw.copy()

    # Trova la riga header: quella che contiene "FABBISOGNO HC TEORICO"
    header_row_candidates = df.apply(
        lambda row: row.astype(str).str.upper().str.contains("FABBISOGNO HC TEORICO").any(),
        axis=1,
    )
    header_idxs = df.index[header_row_candidates].tolist()
    if not header_idxs:
        return None  # foglio non nel layout atteso

    header_idx = header_idxs[0]
    header = df.iloc[header_idx].astype(str).str.strip()

    # Data a partire dalla riga dopo l'header
    data = df.iloc[header_idx + 1 :].reset_index(drop=True)
    data.columns = header

    # Aggiungiamo le colonne 'Anno' e 'Mese' dalle colonne a sinistra (fuori header)
    # Per farlo, usiamo il df_raw (senza header) limitato alle stesse righe
    aux = df_raw.iloc[header_idx + 1 :].reset_index(drop=True)

    # ---- Anno ----
    # Cerchiamo una colonna che contenga numeri tipo 2025–2035
    year_col = None
    for col in aux.columns:
        col_values = pd.to_numeric(aux[col], errors="coerce")
        if col_values.between(2020, 2040).sum() >= 1:
            year_col = col
            break

    if year_col is None:
        return None

    anni = pd.to_numeric(aux[year_col], errors="coerce")
    anni = anni.ffill()  # 2026 riempie tutte le righe sotto finché non cambia

    # ---- Mese ----
    # Cerchiamo una colonna con stringhe che corrispondono ai mesi italiani
    month_col = None
    for col in aux.columns:
        values_str = aux[col].astype(str).str.upper().str.strip()
        if values_str.isin(ITALIAN_MONTHS.keys()).sum() >= 3:
            month_col = col
            break

    if month_col is None:
        return None

    mesi_str = aux[month_col].astype(str).str.upper().str.strip()
    mesi_num = mesi_str.map(ITALIAN_MONTHS)

    # Filtriamo solo le righe con mese riconosciuto
    mask_valid = mesi_num.notna() & anni.notna()
    if not mask_valid.any():
        return None

    data_valid = data.loc[mask_valid].copy()
    data_valid["anno"] = anni.loc[mask_valid].astype(int)
    data_valid["mese"] = mesi_num.loc[mask_valid].astype(int)

    # ---- Mappatura colonne numeriche ----
    def get_col_or_zero(df_in: pd.DataFrame, candidates):
        for c in candidates:
            if c in df_in.columns:
                return pd.to_numeric(df_in[c], errors="coerce").fillna(0)
        return 0

    hc_prev = get_col_or_zero(
        data_valid,
        ["FABBISOGNO HC TEORICO", "FABBISOGNO", "TEORICI"],
    )
    hc_eff = get_col_or_zero(
        data_valid,
        ["PRESENTI", "PRESENTE", "HC PRESENTI"],
    )

    ingressi = get_col_or_zero(
        data_valid,
        ["Temporanei", "Temporanei Assegnazioni Mobilità", "INGRESSI"],
    )
    cessazioni = get_col_or_zero(
        data_valid,
        ["Cessazioni", "USCITE"],
    )

    out = pd.DataFrame(
        {
            "anno": data_valid["anno"],
            "mese": data_valid["mese"],
            "impianto": sheet_name.upper(),
            "tipo_impianto": "AEROPORTO",
            "hc_effettivi": hc_eff,
            "hc_previsti": hc_prev,
            "fte_effettivi": hc_eff,  # H35/H36 = 1 FTE
            "fte_previsti": hc_prev,
            "ingressi": ingressi,
            "cessazioni": cessazioni,
        }
    )

    return out


def parse_acc_layout(df_raw: pd.DataFrame, sheet_name: str) -> pd.DataFrame:
    """
    Parser semplificato per fogli ACC (ACC ROMA / ACC MILANO / ACC PADOVA).
    Usa lo stesso trucco: trova riga con 'FABBISOGNO HC TEORICO' e 'PRESENTI'.
    """

    df = df_raw.copy()

    header_row_candidates = df.apply(
        lambda row: row.astype(str).str.upper().str.contains("FABBISOGNO HC TEORICO").any(),
        axis=1,
    )
    header_idxs = df.index[header_row_candidates].tolist()
    if not header_idxs:
        return None

    header_idx = header_idxs[0]
    header = df.iloc[header_idx].astype(str).str.strip()
    data = df.iloc[header_idx + 1 :].reset_index(drop=True)
    data.columns = header

    aux = df_raw.iloc[header_idx + 1 :].reset_index(drop=True)

    # Anno (come sopra)
    year_col = None
    for col in aux.columns:
        col_values = pd.to_numeric(aux[col], errors="coerce")
        if col_values.between(2020, 2040).sum() >= 1:
            year_col = col
            break
    if year_col is None:
        return None
    anni = pd.to_numeric(aux[year_col], errors="coerce").ffill()

    # Mese (se presente o fallback a 1–12)
    month_col = None
    for col in aux.columns:
        values_str = aux[col].astype(str).str.upper().str.strip()
        if values_str.isin(ITALIAN_MONTHS.keys()).sum() >= 3:
            month_col = col
            break

    if month_col is not None:
        mesi_str = aux[month_col].astype(str).str.upper().str.strip()
        mesi_num = mesi_str.map(ITALIAN_MONTHS)
    else:
        # se non abbiamo mesi, mettiamo mese=1 per tutte le righe valide
        mesi_num = pd.Series(1, index=anni.index)

    mask_valid = anni.notna()
    data_valid = data.loc[mask_valid].copy()
    data_valid["anno"] = anni.loc[mask_valid].astype(int)
    data_valid["mese"] = mesi_num.loc[mask_valid].fillna(1).astype(int)

    def get_col_or_zero(df_in: pd.DataFrame, candidates):
        for c in candidates:
            if c in df_in.columns:
                return pd.to_numeric(df_in[c], errors="coerce").fillna(0)
        return 0

    hc_prev = get_col_or_zero(
        data_valid,
        ["FABBISOGNO HC TEORICO", "FABBISOGNO", "TEORICI"],
    )
    hc_eff = get_col_or_zero(
        data_valid,
        ["PRESENTI", "PRESENTE", "HC PRESENTI"],
    )
    ingressi = get_col_or_zero(data_valid, ["INGRESSI"])
    cessazioni = get_col_or_zero(data_valid, ["CESSAZIONI", "USCITE"])

    out = pd.DataFrame(
        {
            "anno": data_valid["anno"],
            "mese": data_valid["mese"],
            "impianto": sheet_name.upper(),
            "tipo_impianto": "ACC",
            "hc_effettivi": hc_eff,
            "hc_previsti": hc_prev,
            "fte_effettivi": hc_eff,
            "fte_previsti": hc_prev,
            "ingressi": ingressi,
            "cessazioni": cessazioni,
        }
    )

    return out
