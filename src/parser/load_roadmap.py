from pathlib import Path
import pandas as pd
import streamlit as st

# Mappatura mesi in italiano → numero mese
ITALIAN_MONTHS = {
    "GENNAIO": 1, "FEBBRAIO": 2, "MARZO": 3, "APRILE": 4, "MAGGIO": 5, "GIUGNO": 6,
    "LUGLIO": 7, "AGOSTO": 8, "SETTEMBRE": 9, "OTTOBRE": 10, "NOVEMBRE": 11, "DICEMBRE": 12
}

def load_roadmap_data(file_path: Path) -> pd.DataFrame:
    """Legge roadmap.xlsx e restituisce dataset unificato senza crash."""
    xls = pd.ExcelFile(file_path, engine="openpyxl")
    frames = []

    for sheet in xls.sheet_names:
        sheet_up = sheet.upper()

        # Salta fogli “tecnici”
        if sheet_up in ["ASSEGNAZIONI", "ASSEGNZIONI", "TOT", "SUMMARY"]:
            continue

        # Legge il foglio senza header
        df_raw = pd.read_excel(file_path, sheet_name=sheet, engine="openpyxl", header=None)

        # Determina tipo impianto
        if "ACC" in sheet_up:
            df_norm = parse_acc_layout(df_raw, sheet_up)
        else:
            df_norm = parse_airport_layout(df_raw, sheet_up)

        if df_norm is not None and not df_norm.empty:
            frames.append(df_norm)

    # Se ZERO fogli riconosciuti → NON crashare
    if not frames:
        st.error(
            "⚠️ Nessun foglio valido trovato in roadmap.xlsx. "
            "Dobbiamo affinare il parser alle intestazioni reali dei fogli."
        )
        return pd.DataFrame(columns=[
            "anno","mese","impianto","tipo_impianto",
            "hc_effettivi","hc_previsti",
            "fte_effettivi","fte_previsti",
            "ingressi","cessazioni"
        ])

    df_all = pd.concat(frames, ignore_index=True)

    df_all = (
        df_all.groupby(
            ["anno","mese","impianto","tipo_impianto"], as_index=False
        ).sum()
    )

    return df_all


def parse_airport_layout(df_raw: pd.DataFrame, sheet_name: str) -> pd.DataFrame:
    df = df_raw.copy()

    # 1) Riconosci la riga con “FABBISOGNO HC TEORICO”
    header_candidates = df.apply(
        lambda row: row.astype(str).str.upper().str.contains("FABBISOGNO HC TEORICO").any(),
        axis=1
    )
    idxs = df.index[header_candidates].tolist()
    if not idxs:
        return None

    header_idx = idxs[0]
    header = df.iloc[header_idx].astype(str).str.strip()

    # 2) Righe dei dati
    data = df.iloc[header_idx + 1:].reset_index(drop=True)
    data.columns = header

    aux = df_raw.iloc[header_idx + 1:].reset_index(drop=True)

    # 3) Trova colonna anno
    year_col = None
    for col in aux.columns:
        values = pd.to_numeric(aux[col], errors="coerce")
        if values.between(2020, 2040).sum() >= 1:
            year_col = col
            break
    if year_col is None:
        return None

    anni = pd.to_numeric(aux[year_col], errors="coerce").ffill()

    # 4) Trova colonna mese
    month_col = None
    for col in aux.columns:
        s = aux[col].astype(str).str.upper().str.strip()
        if s.isin(ITALIAN_MONTHS.keys()).sum() >= 3:
            month_col = col
            break
    if month_col is None:
        return None

    mesi = aux[month_col].astype(str).str.upper().str.strip().map(ITALIAN_MONTHS)

    valid = mesi.notna() & anni.notna()
    if not valid.any():
        return None

    data = data.loc[valid].copy()
    data["anno"] = anni.loc[valid].astype(int)
    data["mese"] = mesi.loc[valid].astype(int)

    # Utility per colonne numeriche
    def pick(df_in, names):
        for n in names:
            if n in df_in.columns:
                return pd.to_numeric(df_in[n], errors="coerce").fillna(0)
        return pd.Series(0, index=df_in.index)

    hc_prev = pick(data, ["FABBISOGNO HC TEORICO","FABBISOGNO","TEORICI"])
    hc_eff = pick(data, ["PRESENTI","PRESENTE","HC PRESENTI"])
    ingressi = pick(data, ["INGRESSI","Temporanei","Mobilità","Assegnazioni"])
    cessazioni = pick(data, ["Cessazioni","USCITE"])

    return pd.DataFrame({
        "anno": data["anno"],
        "mese": data["mese"],
        "impianto": sheet_name,
        "tipo_impianto": "AEROPORTO",
        "hc_effettivi": hc_eff,
        "hc_previsti": hc_prev,
        "fte_effettivi": hc_eff,
        "fte_previsti": hc_prev,
        "ingressi": ingressi,
        "cessazioni": cessazioni
    })


def parse_acc_layout(df_raw: pd.DataFrame, sheet_name: str) -> pd.DataFrame:
    """Parser simile per i fogli ACC."""
    return None  # lo aggiustiamo dopo, ora bypassiamo gli ACC
