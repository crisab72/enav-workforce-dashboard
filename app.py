import streamlit as st
import plotly.express as px
import pandas as pd

# ----------------------------------------------------
# PAGE CONFIG
# ----------------------------------------------------
st.set_page_config(
    page_title="ENAV Workforce Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ----------------------------------------------------
# CORPORATE THEME (ENAV DARK)
# ----------------------------------------------------
st.markdown(
    """
    <style>
    /* BACKGROUND ----------------------------------------------------- */
    html, body, [class*="css"]  {
        background-color: #020617 !important;  /* very dark navy */
    }
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }

    /* TITLES --------------------------------------------------------- */
    h1, h2, h3, h4 {
        color: #E5E7EB !important;            /* light gray */
        font-family: system-ui, -apple-system, BlinkMacSystemFont,
                     "Segoe UI", sans-serif;
    }
    h2 {
        font-size: 1.6rem;
        font-weight: 700;
    }
    h3 {
        font-size: 1.2rem;
        font-weight: 600;
        margin-bottom: 0.4rem;
    }

    /* TEXT ----------------------------------------------------------- */
    p, span, label, .stMarkdown {
        color: #9CA3AF !important;           /* muted text */
        font-family: system-ui, -apple-system, BlinkMacSystemFont,
                     "Segoe UI", sans-serif;
    }

    /* KPI CARDS (st.metric) ----------------------------------------- */
    div.stMetric {
        background-color: #0B1120;           /* card background */
        padding: 14px 18px;
        border-radius: 16px;
        border: 1px solid #1F2937;
        box-shadow: 0 18px 45px rgba(15,23,42,0.8);
    }
    div.stMetric > label {
        color: #9CA3AF !important;
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.04em;
    }
    div.stMetric > div {
        color: #F9FAFB !important;
        font-size: 1.6rem;
        font-weight: 600;
    }

    /* GENERIC CARDS -------------------------------------------------- */
    .section-card {
        background-color: #020617;          /* slightly darker than metric */
        padding: 22px 26px;
        border-radius: 18px;
        border: 1px solid #1F2937;
        box-shadow: 0 20px 60px rgba(15,23,42,0.9);
        margin-bottom: 20px;
    }

    /* DATAFRAME ------------------------------------------------------ */
    .stDataFrame {
        border-radius: 14px;
        border: 1px solid #1F2937;
        overflow: hidden;
    }

    /* SIDEBAR -------------------------------------------------------- */
    section[data-testid="stSidebar"] {
        background-color: #020617 !important;
        border-right: 1px solid #111827;
    }
    section[data-testid="stSidebar"] h2, section[data-testid="stSidebar"] h3 {
        color: #E5E7EB !important;
    }

    /* REMOVE STREAMLIT DEFAULT TOP PADDING --------------------------- */
    header[data-testid="stHeader"] {
        background: transparent !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ----------------------------------------------------
# SIDEBAR NAVIGATION
# ----------------------------------------------------
st.sidebar.title("ENAV – Dashboard Navigation")
page = st.sidebar.radio(
    "Choose section:",
    ["Workforce Overview", "Workforce Mobility", "Facility Dashboard (Fiumicino)"],
)

st.sidebar.markdown(
    "<small>Mockup layout · ENAV corporate dark theme</small>",
    unsafe_allow_html=True,
)

# ----------------------------------------------------
# PLACEHOLDER DATA (for visuals)
# ----------------------------------------------------
trend_df = pd.DataFrame(
    {
        "Year": [2020, 2021, 2022, 2023, 2024],
        "HC Actual": [2300, 2280, 2250, 2200, 2180],
        "HC Required": [2500, 2450, 2400, 2380, 2350],
    }
)

mobility_years = pd.DataFrame(
    {
        "Year": [2022, 2023, 2024],
        "Hiring": [45, 58, 65],
        "Exits": [38, 41, 52],
    }
)

facility_table = pd.DataFrame(
    {
        "Facility": [
            "Rome ACC",
            "Milan ACC",
            "Padova ACC",
            "Fiumicino",
            "Palermo",
            "Catania",
            "Bari",
        ],
        "HC Actual": [320, 295, 280, 60, 54, 52, 48],
        "HC Required": [350, 310, 300, 70, 60, 58, 55],
    }
)
facility_table["FTE Actual"] = facility_table["HC Actual"]
facility_table["FTE Required"] = facility_table["HC Required"]
facility_table["HC Gap"] = facility_table["HC Actual"] - facility_table["HC Required"]
facility_table["Coverage %"] = (
    facility_table["HC Actual"] / facility_table["HC Required"]
).map(lambda x: f"{x:.1%}")

# ----------------------------------------------------
# PAGE 1 – WORKFORCE OVERVIEW
# ----------------------------------------------------
if page == "Workforce Overview":
    st.markdown("## ENAV – Workforce Overview")
    st.markdown(
        "Global view of operational workforce across all ENAV facilities "
        "(ACC, strategic and regional airports)."
    )

    # KPI row
    k1, k2, k3, k4, k5, k6 = st.columns(6)
    k1.metric("HC Actual", "2,205")
    k2.metric("HC Required", "2,380")
    k3.metric("HC Gap", "-175")
    k4.metric("FTE Actual", "2,205")
    k5.metric("FTE Required", "2,380")
    k6.metric("FTE Gap", "-175")

    st.markdown("")

    # Charts row
    col_left, col_right = st.columns([2.2, 1.8])

    with col_left:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown("### HC / FTE Trend – ENAV Total")
        fig = px.line(
            trend_df,
            x="Year",
            y=["HC Actual", "HC Required"],
            markers=True,
            color_discrete_sequence=["#0EA5E9", "#EF4444"],
        )
        fig.update_layout(template="plotly_dark", height=320, legend_title_text="")
        st.plotly_chart(fig, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with col_right:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown("### CTA / EAV Split (Example)")
        pie_df = pd.DataFrame(
            {"Category": ["CTA", "EAV"], "FTE": [1800, 405]}
        )
        fig_pie = px.pie(
            pie_df,
            names="Category",
            values="FTE",
            color="Category",
            color_discrete_map={"CTA": "#0EA5E9", "EAV": "#F97316"},
        )
        fig_pie.update_layout(template="plotly_dark", height=320, legend_title_text="")
        st.plotly_chart(fig_pie, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # Table
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown("### Workforce by Facility (summary view)")
    st.dataframe(facility_table, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

# ----------------------------------------------------
# PAGE 2 – WORKFORCE MOBILITY
# ----------------------------------------------------
elif page == "Workforce Mobility":
    st.markdown("## ENAV – Workforce Mobility")
    st.markdown(
        "Hiring, exits, upskilling and reskilling for ENAV operational workforce."
    )

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Hiring", "65")
    k2.metric("Exits", "52")
    k3.metric("Upskilling", "23")
    k4.metric("Reskilling", "19")

    st.markdown("")

    # Hiring & Exits per year
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown("### Hiring & Exits per Year")
    df_melt = mobility_years.melt(
        id_vars="Year", value_vars=["Hiring", "Exits"], var_name="Type", value_name="Count"
    )
    fig = px.bar(
        df_melt,
        x="Year",
        y="Count",
        color="Type",
        barmode="group",
        color_discrete_map={"Hiring": "#22C55E", "Exits": "#EF4444"},
    )
    fig.update_layout(template="plotly_dark", height=320, legend_title_text="")
    st.plotly_chart(fig, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # Mobility breakdown + trend
    colA, colB = st.columns(2)

    with colA:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown("### Mobility Breakdown (Example)")
        fig2 = px.pie(
            names=["Hiring", "Exits", "Upskilling", "Reskilling"],
            values=[65, 52, 23, 19],
            color_discrete_sequence=["#22C55E", "#EF4444", "#38BDF8", "#F97316"],
        )
        fig2.update_layout(template="plotly_dark", height=320, legend_title_text="")
        st.plotly_chart(fig2, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with colB:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown("### Mobility Trend (Example index)")
        trend_mob = pd.DataFrame(
            {
                "Year": [2020, 2021, 2022, 2023, 2024],
                "Mobility Index": [100, 110, 120, 115, 118],
            }
        )
        fig3 = px.line(
            trend_mob,
            x="Year",
            y="Mobility Index",
            markers=True,
            color_discrete_sequence=["#0EA5E9"],
        )
        fig3.update_layout(template="plotly_dark", height=320, showlegend=False)
        st.plotly_chart(fig3, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

# ----------------------------------------------------
# PAGE 3 – FACILITY DASHBOARD (FIUMICINO)
# ----------------------------------------------------
else:
    st.markdown("## ENAV – FIUMICINO (Facility Dashboard)")
    st.markdown(
        "Local workforce metrics, mobility and qualification breakdown for the Fiumicino facility."
    )

    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("HC Actual", "60")
    k2.metric("HC Required", "70")
    k3.metric("HC Gap", "-10")
    k4.metric("Hiring YTD", "7")
    k5.metric("Exits YTD", "4")

    st.markdown("")

    # Monthly HC trend
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown("### Monthly HC Trend")
    monthly_df = pd.DataFrame(
        {"Month": ["Jan", "Feb", "Mar", "Apr", "May", "Jun"], "HC": [60, 58, 59, 60, 61, 60]}
    )
    fig = px.line(
        monthly_df,
        x="Month",
        y="HC",
        markers=True,
        color_discrete_sequence=["#0EA5E9"],
    )
    fig.update_layout(template="plotly_dark", height=300, showlegend=False)
    st.plotly_chart(fig, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

    colA, colB = st.columns(2)

    with colA:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown("### Mobility Breakdown")
        figA = px.pie(
            names=["Transfers", "Temporary Assignments", "Exits"],
            values=[35, 12, 4],
            color_discrete_sequence=["#38BDF8", "#0EA5E9", "#EF4444"],
        )
        figA.update_layout(template="plotly_dark", height=320, legend_title_text="")
        st.plotly_chart(figA, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with colB:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown("### Workforce by Qualification")
        figB = px.bar(
            pd.DataFrame(
                {"Qualification": ["CTA", "EAV", "SUP", "TRN"], "Headcount": [30, 18, 7, 5]}
            ),
            x="Qualification",
            y="Headcount",
            color_discrete_sequence=["#0EA5E9"],
        )
        figB.update_layout(template="plotly_dark", height=320, showlegend=False)
        st.plotly_chart(figB, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
