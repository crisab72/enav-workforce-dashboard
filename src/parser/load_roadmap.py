import pandas as pd

def load_roadmap_data(file_path):

    xls = pd.ExcelFile(file_path, engine="openpyxl")
    sheet_names = xls.sheet_names

    frames = []

    for sheet in sheet_names:

        # Skippa fogli non di interesse
        if sheet.lower() in ["assegnazioni", "tot", "summary", "dash"]:
            continue

        # Carica il foglio
        df = pd.read_excel(file_path, sheet_name=sheet, engine="openpyxl")

        # Determina tipo impianto automaticamente
        if "ACC" in sheet.upper():
            tipo = "ACC"
        elif sheet.upper() in ["AEROPORTI STRATEGICI", "AEROPORTI STRATEGICO", "AEROPORTI STRATEGICI 2025"]:
            tipo = "STRATEGICO"
        elif sheet.upper() in ["REGIONAL AIRPORTS", "REGIONALI", "AEROPORTI REGIONALI"]:
            tipo = "REGIONALE"
        else:
            # Per fogli tipo “FIUMICINO”, “PALERMO”, “CATANIA”… → aeroporto normale
            tipo = "AEROPORTO"

        # Normalizzazione automatica
        df_norm = normalize_sheet(df, sheet, tipo)

        if df_norm is not None:
            frames.append(df_norm)

    if not frames:
        raise ValueError("Nessun foglio valido trovato in roadmap.xlsx")

    df_all = pd.concat(frames, ignore_index=True)

    # Aggregazione finale
    df_all = (
        df_all.groupby(["anno","mese","impianto","tipo_impianto"], as_index=False)
        .sum()
    )

    return df_all


def normalize_sheet(df, sheet, tipo):
    """
    Estrattore generico che si adatta alla struttura:
    - colonna anno
    - mese riconosciuto dalle righe (o ripetuto)
    - colonne FABBISOGNO HC TEORICO, PRESENTI, ingressi, cessazioni
    """

    df = df.copy()

    # Trova colonne disponibili
    col_map = {
        "hc_effettivi": ["PRESENTI", "PRESENTE", "HC PRESENTI"],
        "hc_previsti": ["FABBISOGNO HC TEORICO", "TEORICI", "FABBISOGNO"],
        "ingressi": ["INGRESSI"],
        "cessazioni": ["CESSAZIONI", "USCITE"]
    }

    out = {}

    # -----------------------------------------
    # TROVA ANNO E MESE (colonne obbligatorie)
    # -----------------------------------------
    if "anno" in df.columns:
        out["anno"] = df["anno"]
    else:
        # spesso è la prima colonna con valori 2025/2026/2027
        first_col = df.iloc[:,0]
        if first_col.dtype in ["int64", "float64"]:
            out["anno"] = first_col
        else:
            return None  # foglio non strutturato

    if "mese" in df.columns:
        out["mese"] = df["mese"]
    else:
        # Se non esiste colonna mese, assumo mese=1 (valore placeholder)
        out["mese"] = 1

    # -----------------------------------------
    # TROVA LE COLONNE NUMERICHE
    # -----------------------------------------
    for target, candidates in col_map.items():
        found = None
        for c in candidates:
            if c in df.columns:
                found = df[c]
                break
        if found is None:
            out[target] = 0
        else:
            out[target] = pd.to_numeric(found, errors="coerce").fillna(0)

    # -----------------------------------------
    # IMPIANTO E TIPO
    # -----------------------------------------

    out_df = pd.DataFrame(out)
    out_df["impianto"] = sheet.upper()
    out_df["tipo_impianto"] = tipo

    # -----------------------------------------
    # FTE = HC (regola ENAV)
    # -----------------------------------------
    out_df["fte_effettivi"] = out_df["hc_effettivi"]
    out_df["fte_previsti"] = out_df["hc_previsti"]

    # Se il foglio è vuoto
    if out_df["anno"].isna().all():
        return None

    return out_df[[
        "anno","mese","impianto","tipo_impianto",
        "hc_effettivi","hc_previsti",
        "fte_effettivi","fte_previsti",
        "ingressi","cessazioni"
    ]]
