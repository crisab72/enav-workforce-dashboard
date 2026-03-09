import streamlit as st
import pandas as pd
import plotly.express as px

from src.parser.transform import load_combined_dataset

st.set_page_config(
    page_title="ENAV – Workforce Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("ENAV – Workforce Overview")
st.caption("Rostering & Pianificazione organici – Dashboard interattiva")

# Carica dataset combinato
df = load_combined_dataset()

# Sidebar – Filtri
st.sidebar.header("Filtri")

anni = sorted(df['anno'].unique())
mesi = sorted(df['mese'].unique())

anno_sel = st.sidebar.selectbox("Anno", anni, index=len(anni)-1)
mese_sel = st.sidebar.selectbox("Mese", ["Tutti"] + list(mesi))

df_fil = df[df['anno'] == anno_sel]

if mese_sel != "Tutti":
    df_fil = df_fil[df_fil['mese'] == mese_sel]

# KPI
col1, col2, col3, col4, col5, col6 = st.columns(6)

col1.metric("HC Effettivi", int(df_fil["hc_effettivi"].sum()))
col2.metric("HC Previsti", int(df_fil["hc_previsti"].sum()))
col3.metric("Delta HC", int(df_fil["hc_effettivi"].sum() - df_fil["hc_previsti"].sum()))

col4.metric("FTE Effettivi", int(df_fil["fte_effettivi"].sum()))
col5.metric("FTE Previsti", int(df_fil["fte_previsti"].sum()))
col6.metric("Delta FTE", int(df_fil["fte_effettivi"].sum() - df_fil["fte_previsti"].sum()))

st.divider()

# Trend HC/FTE per anno
df_year = (
    df.groupby("anno")
    .agg({"hc_effettivi": "sum", "hc_previsti": "sum",
          "fte_effettivi": "sum", "fte_previsti": "sum"})
    .reset_index()
)

fig = px.line(
    df_year,
    x="anno",
    y=["hc_effettivi", "hc_previsti", "fte_effettivi", "fte_previsti"],
    markers=True,
    title="Trend HC/FTE Totale ENAV"
)
fig.update_layout(template="plotly_dark")

st.plotly_chart(fig, use_container_width=True)

st.divider()

# Ingressi e cessazioni
colA, colB = st.columns(2)

df_ing = df_fil.groupby("anno")["ingressi"].sum().reset_index()
df_ces = df_fil.groupby("anno")["cessazioni"].sum().reset_index()

fig_ing = px.bar(df_ing, x="anno", y="ingressi", title="Ingressi per anno")
fig_ing.update_layout(template="plotly_dark")
colA.plotly_chart(fig_ing, use_container_width=True)

fig_ces = px.bar(df_ces, x="anno", y="cessazioni", title="Cessazioni per anno")
fig_ces.update_layout(template="plotly_dark")
colB.plotly_chart(fig_ces, use_container_width=True)

st.divider()

# Tabella impianti
st.subheader("Analisi Impianti (HC/FTE)")

df_imp = (
    df_fil.groupby(["impianto", "tipo_impianto"])
    .agg({
        "hc_effettivi": "sum",
        "hc_previsti": "sum",
        "fte_effettivi": "sum",
        "fte_previsti": "sum",
        "ingressi":"sum",
        "cessazioni":"sum"
    })
    .reset_index()
)

df_imp["delta_hc"] = df_imp["hc_effettivi"] - df_imp["hc_previsti"]
df_imp["delta_fte"] = df_imp["fte_effettivi"] - df_imp["fte_previsti"]

df_imp["copertura_hc"] = df_imp["hc_effettivi"] / df_imp["hc_previsti"]
df_imp["copertura_fte"] = df_imp["fte_effettivi"] / df_imp["fte_previsti"]

st.dataframe(
    df_imp.style.format({
        "copertura_hc": "{:.1%}",
        "copertura_fte": "{:.1%}"
    }),
    use_container_width=True
)
