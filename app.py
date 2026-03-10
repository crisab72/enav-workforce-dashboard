import streamlit as st
import pandas as pd
import plotly.express as px

# ============================================================
# PAGE CONFIG
# ============================================================
st.set_page_config(
    page_title="ENAV Workforce Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# ENAV DARK CORPORATE THEME (CSS)
# ============================================================
st.markdown(
    """
    <style>
    html, body, [class*="css"]  {
        background-color: #020617 !important;  /* very dark navy */
    }
    .block-container {
        padding-top: 1.8rem;
        padding-bottom: 1.8rem;
    }

    h1, h2, h3, h4 {
        color: #E5E7EB !important;
        font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }
    h2 {
        font-size: 1.4rem;
        font-weight: 700;
        margin-bottom: 0.2rem;
    }
    h3 {
        font-size: 1.1rem;
        font-weight: 600;
        margin-bottom: 0.2rem;
    }
    p, span, label, li {
        color: #9CA3AF !important;
        font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }

    /* KPI cards (st.metric) */
    div.stMetric {
        background-color: #0B1120;
        padding: 12px 16px;
        border-radius: 14px;
        border: 1px solid #1F2937;
        box-shadow: 0 18px 45px rgba(15,23,42,0.9);
    }
    div.stMetric > label {
        color: #9CA3AF !important;
        font-size: 0.7rem;
        text-transform: uppercase;
        letter-spacing: 0.06em;
    }
    div.stMetric > div {
        color: #F9FAFB !important;
        font-size: 1.2rem;
        font-weight: 600;
    }

    /* Generic card container */
    .section-card {
        background-color: #020617;
        padding: 18px 20px;
        border-radius: 16px;
        border: 1px solid #1F2937;
        box-shadow: 0 20px 60px rgba(15,23,42,0.95);
        margin-bottom: 14px;
    }

    .stDataFrame {
        border-radius: 14px;
        border: 1px solid #1F2937;
        overflow: hidden;
    }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background-color: #020617 !important;
        border-right: 1px solid #111827;
    }
    section[data-testid="stSidebar"] h2, section[data-testid="stSidebar"] h3 {
        color: #E5E7EB !important;
    }

    header[data-testid="stHeader"] {
        background: transparent !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# ============================================================
# PLACEHOLDER DATA (2026–2031)
# ============================================================

YEARS = [2026, 2027, 2028, 2029, 2030, 2031]
FACILITIES = ["Fiumicino", "Palermo", "Catania", "Bari", "Cagliari",
              "Rome ACC", "Milan ACC", "Padova ACC"]

# Trend ENAV totale (HC)
overview_trend = pd.DataFrame({
    "Year": YEARS,
    "HC Actual":   [2205, 2180, 2150, 2120, 2100, 2080],
    "HC Required": [2380, 2360, 2340, 2320, 2300, 2280],
})

# Mobility per anno
mobility_years = pd.DataFrame({
    "Year": YEARS,
    "Hiring": [60, 62, 65, 63, 61, 60],
    "Exits":  [48, 50, 52, 49, 47, 46],
    "Upskilling": [20, 21, 23, 22, 21, 20],
    "Reskilling": [15, 17, 19, 18, 17, 16],
})

# Dati per facility (HC per anno)
records = []
for fac in FACILITIES:
    base_req = 0
    base_act = 0
    if "ACC" in fac:
        base_req = 320
        base_act = 300
    elif fac == "Fiumicino":
        base_req = 70
        base_act = 60
    else:
        base_req = 60
        base_act = 52

    for y in YEARS:
        # variazioni fittizie per dare dinamica
        delta = (y - 2026) * 1
        records.append({
            "Facility": fac,
            "Year": y,
            "HC Required": base_req + delta,
            "HC Actual": base_act + max(-3, 3 - (y - 2026)),  # esempio
        })

facility_df = pd.DataFrame(records)
facility_df["FTE Required"] = facility_df["HC Required"]
facility_df["FTE Actual"] = facility_df["HC Actual"]

# ============================================================
# SIDEBAR – FILTERS
# ============================================================

st.sidebar.title("ENAV – Workforce Dashboard")

year_selected = st.sidebar.selectbox(
    "Select Year", YEARS, index=0
)

facility_selected = st.sidebar.selectbox(
    "Select Facility (right column)", FACILITIES, index=0
)

st.sidebar.markdown(
    "<small>Data are mock values for layout and interaction demo.</small>",
    unsafe_allow_html=True
)

# Filtri applicati ai dataset
overview_year_row = overview_trend[overview_trend["Year"] == year_selected].iloc[0]
mobility_year_row = mobility_years[mobility_years["Year"] == year_selected].iloc[0]

facility_year_df = facility_df[facility_df["Year"] == year_selected]
facility_selected_row = facility_year_df[facility_year_df["Facility"] == facility_selected].iloc[0]

# ============================================================
# LAYOUT PRINCIPALE – 3 COLONNE AFFIANCATE
# ============================================================

st.markdown(f"### ENAV – Workforce Dashboard · Year {year_selected}")

col_overview, col_mobility, col_facility = st.columns(3)

# ------------------------------------------------------------
# COLUMN 1 – WORKFORCE OVERVIEW
# ------------------------------------------------------------
with col_overview:
    st.markdown("#### ENAV – Workforce Overview")

    k1, k2, k3 = st.columns(3)
    k1.metric("HC Actual", f"{overview_year_row['HC Actual']:,.0f}")
    k2.metric("HC Required", f"{overview_year_row['HC Required']:,.0f}")
    gap_hc = overview_year_row["HC Actual"] - overview_year_row["HC Required"]
    k3.metric("HC Gap", f"{gap_hc:,.0f}")

    k4, k5, k6 = st.columns(3)
    k4.metric("FTE Actual", f"{overview_year_row['HC Actual']:,.0f}")
    k5.metric("FTE Required", f"{overview_year_row['HC Required']:,.0f}")
    k6.metric("FTE Gap", f"{gap_hc:,.0f}")

    # Trend ENAV totale
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown("##### HC / FTE Trend – ENAV Total (2026–2031)")
    fig_trend = px.line(
        overview_trend,
        x="Year",
        y=["HC Actual", "HC Required"],
        markers=True,
        color_discrete_sequence=["#0EA5E9", "#EF4444"],
    )
    fig_trend.update_layout(
        template="plotly_dark",
        height=260,
        legend_title_text=""
    )
    st.plotly_chart(fig_trend, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # Tabella per facility (solo anno selezionato)
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown("##### Workforce by Facility (selected year)")
    table = facility_year_df.copy()
    table["HC Gap"] = table["HC Actual"] - table["HC Required"]
    table["Coverage %"] = (table["HC Actual"] / table["HC Required"]).map(
        lambda x: f"{x:.1%}"
    )
    st.dataframe(
        table[["Facility", "HC Actual", "HC Required", "HC Gap", "Coverage %"]],
        use_container_width=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)

# ------------------------------------------------------------
# COLUMN 2 – WORKFORCE MOBILITY
# ------------------------------------------------------------
with col_mobility:
    st.markdown("#### ENAV – Workforce Mobility")

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Hiring", f"{mobility_year_row['Hiring']}")
    m2.metric("Exits", f"{mobility_year_row['Exits']}")
    m3.metric("Upskilling", f"{mobility_year_row['Upskilling']}")
    m4.metric("Reskilling", f"{mobility_year_row['Reskilling']}")

    # Hiring & Exits per anno
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown("##### Hiring & Exits per Year (2026–2031)")
    df_melt = mobility_years.melt(
        id_vars="Year",
        value_vars=["Hiring", "Exits"],
        var_name="Type",
        value_name="Count",
    )
    fig_hire_exit = px.bar(
        df_melt,
        x="Year",
        y="Count",
        color="Type",
        barmode="group",
        color_discrete_map={"Hiring": "#22C55E", "Exits": "#EF4444"},
    )
    fig_hire_exit.update_layout(
        template="plotly_dark",
        height=260,
        legend_title_text=""
    )
    st.plotly_chart(fig_hire_exit, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # Mobility breakdown (donut)
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown("##### Mobility Breakdown (selected year)")
    donut_df = pd.DataFrame({
        "Type": ["Hiring", "Exits", "Upskilling", "Reskilling"],
        "Value": [
            mobility_year_row["Hiring"],
            mobility_year_row["Exits"],
            mobility_year_row["Upskilling"],
            mobility_year_row["Reskilling"],
        ],
    })
    fig_donut = px.pie(
        donut_df,
        names="Type",
        values="Value",
        hole=0.55,
        color="Type",
        color_discrete_map={
            "Hiring": "#22C55E",
            "Exits": "#EF4444",
            "Upskilling": "#38BDF8",
            "Reskilling": "#F97316",
        },
    )
    fig_donut.update_layout(
        template="plotly_dark",
        height=260,
        legend_title_text=""
    )
    st.plotly_chart(fig_donut, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

# ------------------------------------------------------------
# COLUMN 3 – FACILITY DASHBOARD (single facility)
# ------------------------------------------------------------
with col_facility:
    st.markdown(f"#### ENAV – {facility_selected} (Facility Dashboard)")

    # KPI impianto
    f1, f2, f3 = st.columns(3)
    f1.metric("HC Actual", f"{facility_selected_row['HC Actual']}")
    f2.metric("HC Required", f"{facility_selected_row['HC Required']}")
    gap_fac = facility_selected_row["HC Actual"] - facility_selected_row["HC Required"]
    f3.metric("HC Gap", f"{gap_fac}")

    # Mobility locale (mock)
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown("##### Local Mobility (example)")
    fig_local_pie = px.pie(
        names=["Transfers", "Temporary Assignments", "Exits"],
        values=[35, 12, 4],
        hole=0.55,
        color_discrete_sequence=["#0EA5E9", "#38BDF8", "#EF4444"],
    )
    fig_local_pie.update_layout(
        template="plotly_dark",
        height=220,
        legend_title_text=""
    )
    st.plotly_chart(fig_local_pie, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # Distribuzione per Qualification (CTA/EAV/SUP/TRN)
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown("##### Workforce by Qualification (example)")
    qual_df = pd.DataFrame({
        "Qualification": ["CTA", "EAV", "SUP", "TRN"],
        "Headcount": [30, 18, 7, 5],
    })
    fig_qual = px.bar(
        qual_df,
        x="Qualification",
        y="Headcount",
        color_discrete_sequence=["#0EA5E9"],
    )
    fig_qual.update_layout(
        template="plotly_dark",
        height=220,
        showlegend=False
    )
    st.plotly_chart(fig_qual, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)
