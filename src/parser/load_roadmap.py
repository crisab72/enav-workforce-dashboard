from pathlib import Path
import pandas as pd
import streamlit as st

# Mappatura mesi in italiano → numero mese
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
    """
    Legge roadmap.xlsx e restituisce il dataset unificato per la dashboard.
    Ogni riga del DataFrame finale rappresenta:
    (anno, mese, impianto, tipo_impianto) con HC/FTE effettivi e previsti,
    ingressi e cessazioni.
    """

    xls = pd.ExcelFile(file_path, engine="openpyxl")
    sheet_names = xls.sheet_names

    frames = []

    for sheet in sheet_names:
        sheet_up = sheet.upper()

        # Salta fogli "tecnici" che non contengono dati mensili
        if sheet_up in ["ASSEGNAZIONI", "ASSEGNZIONI", "TOT", "SUMMARY"]:
            continue

        # Legge il foglio SENZA header, così possiamo trovare la riga giusta
        df_raw = pd.read_excel(
            file_path, sheet_name=sheet, engine="openpyxl", header=None
        )

        # Classificazione tipo impianto
        if "ACC" in sheet_up:
            tipo = "ACC"
            df_norm = parse_acc_layout(df_raw, sheet_up)
        else:
            # FIUMICINO, PALERMO, CIAMPINO, OLBIA, ALGHERO, ecc.
            # e anche eventuali "Aeroporti Strategici" / "Regional Airports"
            tipo = "AEROPORTO"
            df_norm = parse_airport_layout(df_raw, sheet_up)

        if df_norm is not None and not df_norm.empty:
            frames.append(df_norm)

    # Se nessun foglio è stato riconosciuto, non mandiamo in crash la app
    if not frames:
        st.error(
            "⚠️ Nessun foglio valido trovato in roadmap.xlsx. "
            "Dobbiamo ancora affinare il parser per la struttura reale dei fogli."
        )
        # Ritorno DataFrame vuoto ma con le colonne che la dashboard si aspetta
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

    # Concatena tutti i fogli normalizzati
    df_all = pd.concat(frames, ignore_index=True)

    # Aggregazione finale di sicurezza
    df_all = (
        df_all.groupby(
            ["anno", "mese", "impianto", "tipo_impianto"], as_index=False
        )
        .sum()
    )

    return df_all


def parse_airport_layout(df_raw: pd.DataFrame, sheet_name: str) -> pd.DataFrame:
    """
    Parsing fogli aeroportuali tipo FIUMICINO / PALERMO / CIAMPINO / ecc.

    Layout tipico:
    - colonna sinistra: anni (2026/2027/...) spesso in celle unite
    - colonna accanto: mesi (GENNAIO, FEBBRAIO, ...)
    - riga header con: 'FABBISOGNO HC TEORICO', 'PRESENTI', 'DELTA',
      'Mobilità', 'Cessazioni', 'Temporanei', ecc.
    """

    df = df_raw.copy()

    # 1) Trova la riga che contiene "FABBISOGNO HC TEORICO" → header
    header_row_candidates = df.apply(
        lambda row: row.astype(str)
        .str.upper()
        .str.contains("FABBISOGNO HC TEORICO")
        .any(),
        axis=1,
    )
    header_idxs = df.index[header_row_candidates].tolist()
    if not header_idxs:
        # foglio non nel layout atteso
        return None

    header_idx = header_idxs[0]
    header = df.iloc[header_idx].astype(str).str.strip()

    # Dati a partire dalla riga successiva
    data = df.iloc[header_idx + 1 :].reset_index(drop=True)
    data.columns = header

    # Ausiliario per trovare anno/mese (usa il df_raw originale)
    aux = df_raw.iloc[header_idx + 1 :].reset_index(drop=True)

    # 2) Colonna Anno
    year_col = None
    for col in aux.columns:
        col_values = pd.to_numeric(aux[col], errors="coerce")
        # se in quella colonna c'è almeno un valore fra 2020 e 2040,
        # assumo che sia la colonna degli anni
        if col_values.between(2020, 2040).sum() >= 1:
            year_col = col
            break

    if year_col is None:
        return None

    anni = pd.to_numeric(aux[year_col], errors="coerce").ffill()

    # 3) Colonna Mese (GENNAIO, FEBBRAIO, ...)
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

    # 4) Filtra righe che hanno anno e mese validi
    mask_valid = mesi_num.notna() & anni.notna()
    if not mask_valid.any():
        return None

    data_valid = data.loc[mask_valid].copy()
    data_valid["anno"] = anni.loc[mask_valid].astype(int)
    data_valid["mese"] = mesi_num.loc[mask_valid].astype(int)

    # 5) Funzione di supporto per estrarre colonne numeriche candidate
    def get_col_or_zero(df_in: pd.DataFrame, candidates):
        for c in candidates:
            if c in df_in.columns:
                return pd.to_numeric(df_in[c], errors="coerce").fillna(0)
        return pd.Series(0, index=df_in.index)

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
        [
            "Temporanei",
            "Temporanei Assegnazioni Mobilità",
            "INGRESSI",
        ],
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
    Parser semplificato per fogli ACC (ACC ROMA, ACC MILANO, ACC PADOVA).
    Usa lo stesso trucco: trova la riga con 'FABBISOGNO HC TEORICO'
    e 'PRESENTI', poi deriva anno/mese dalle colonne a sinistra.
    """

    df = df_raw.copy()

    header_row_candidates = df.apply(
        lambda row: row.astype(str)
        .str.upper()
        .str.contains("FABBISOGNO HC TEORICO")
        .any(),
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

    # Anno
    year_col = None
    for col in aux.columns:
        col_values = pd.to_numeric(aux[col], errors="coerce")
        if col_values.between(2020, 2040).sum() >= 1:
            year_col = col
            break
    if year_col is None:
        return None
    anni = pd.to_numeric(aux[year_col], errors="coerce").ffill()

    # Mese (se presente come testo, altrimenti default=1)
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
        mesi_num = pd.Series(1, index=anni.index)

    mask_valid = anni.notna()
    if not mask_valid.any():
        return None

    data_valid = data.loc[mask_valid].copy()
    data_valid["anno"] = anni.loc[mask_valid].astype(int)
    data_valid["mese"] = mesi_num.loc[mask_valid].fillna(1).astype(int)

    def get_col_or_zero(df_in: pd.DataFrame, candidates):
        for c in candidates:
            if c in df_in.columns:
                return pd.to_numeric(df_in[c], errors="coerce").fillna(0)
        return pd.Series(0, index=df_in.index)

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
