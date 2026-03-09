import pandas as pd

def load_report_data(file_path):

    df = pd.read_excel(file_path, engine="openpyxl")

    df_dim = df[["Uo","Orario"]].rename(columns={
        "Uo": "impianto",
        "Orario": "categoria"
    })

    return df_dim.drop_duplicates()
