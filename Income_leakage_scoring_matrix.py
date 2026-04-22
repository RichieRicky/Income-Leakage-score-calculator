import streamlit as st
import pandas as pd
from io import BytesIO

# -----------------------------
# CONFIG
# -----------------------------
APP_VERSION = "1.0"
OWNER = "Internal Audit"
MAX_SCORE = 200.0

PRIMARY_GREEN = "#064E3B"
LIGHT_BG = "#F4FBF8"
TEXT_DARK = "#0F172A"
TEXT_MUTED = "#475569"
BORDER = "rgba(6,78,59,0.18)"


# -----------------------------
# SCORING LOGIC
# -----------------------------
def interpolate(value, x0, x1, y0, y1):
    if x1 == x0:
        return y1
    return y0 + (value - x0) * (y1 - y0) / (x1 - x0)


def calculate_score(amount_m):
    if amount_m < 0:
        return None, "Invalid", "Amount cannot be negative"

    if amount_m < 1:
        pct = interpolate(amount_m, 0, 1, 0, 70)
        return round(pct, 2), "Unsatisfactory", "Below 1m"

    if amount_m <= 5:
        pct = interpolate(amount_m, 1, 5, 71, 90)
        return round(pct, 2), "Needs Improvement", "1–5m"

    if 5 < amount_m < 6:
        return 91.0, "Met Expectations", "6–20m"

    if amount_m <= 20:
        pct = interpolate(amount_m, 6, 20, 91, 105)
        return round(pct, 2), "Met Expectations", "6–20m"

    if 20 < amount_m < 21:
        return 106.0, "Exceeds Expectations", "21–100m"

    if amount_m <= 100:
        pct = interpolate(amount_m, 21, 100, 106, 124)
        return round(pct, 2), "Exceeds Expectations", "21–100m"

    pct = interpolate(amount_m, 100, 200, 125, 200)
    pct = min(pct, MAX_SCORE)
    return round(pct, 2), "Exceptional", "Over 100m"


def make_matrix_df():
    return pd.DataFrame([
        {"Amount Band (M)": "Below 1m", "Rating": "Unsatisfactory", "Score % Range": "<70%"},
        {"Amount Band (M)": "1–5m", "Rating": "Needs Improvement", "Score % Range": "71–90%"},
        {"Amount Band (M)": "6–20m", "Rating": "Met Expectations", "Score % Range": "91–105%"},
        {"Amount Band (M)": "21–100m", "Rating": "Exceeds Expectations", "Score % Range": "106–124%"},
        {"Amount Band (M)": "Over 100m", "Rating": "Exceptional", "Score % Range": "125–200%"},
    ])


def to_excel_bytes(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Result")
    return output.getvalue()


# -----------------------------
# PAGE SETUP
# -----------------------------
st.set_page_config(
    page_title="Income Leakage Score Calculator",
    page_icon="✅",
    layout="wide"
)

# -----------------------------
# CLEAN UI STYLING
# -----------------------------
st.markdown(
    f"""
    <style>
      .stApp {{
        background: linear-gradient(180deg, #ffffff, {LIGHT_BG});
      }}

      .block-container {{
        padding-top: 1.2rem;
      }}

      .header-card {{
        background: linear-gradient(135deg, {PRIMARY_GREEN}, #0b6b53);
        border-radius: 18px;
        padding: 20px 22px;
        color: white;
        box-shadow: 0 10px 28px rgba(2,44,33,0.18);
      }}

      .header-card h1 {{
        margin: 0;
        font-size: 1.6rem;
        font-weight: 700;
      }}

      .header-card p {{
        margin-top: 6px;
        opacity: 0.9;
      }}

      .result-card {{
        background: white;
        border-radius: 18px;
        padding: 18px;
        border: 1px solid {BORDER};
        box-shadow: 0 10px 20px rgba(2,44,33,0.08);
      }}

      .label {{
        color: {TEXT_MUTED};
        font-size: 0.9rem;
      }}

      .value {{
        color: {TEXT_DARK};
        font-size: 1.4rem;
        font-weight: 800;
      }}

      button {{
        border-radius: 14px !important;
      }}
    </style>
    """,
    unsafe_allow_html=True
)

# -----------------------------
# HEADER
# -----------------------------
st.markdown(
    """
    <div class="header-card">
        <h1>Income Leakage Score Calculator</h1>
        <p>
            Enter the amount (in millions) to determine the Rating and Percentage Score
            based on the approved scoring matrix.
        </p>
    </div>
    """,
    unsafe_allow_html=True
)

st.write("")

# -----------------------------
# TABS
# -----------------------------
tab_calc, tab_matrix, tab_about = st.tabs(["✅ Calculator", "📋 Matrix", "ℹ️ About"])

with tab_calc:
    col1, col2 = st.columns([1.1, 0.9], gap="large")

    with col1:
        st.subheader("Enter Amount")

        with st.form("calc_form"):
            amount = st.number_input(
                "Amount (Millions)",
                min_value=0.0,
                value=None,
                step=0.1,
                format="%.1f",
                placeholder="e.g. 40"
            )
            submitted = st.form_submit_button("Calculate")

        if submitted:
            if amount is None:
                st.warning("Please enter an amount in millions.")
            else:
                pct, rating, band = calculate_score(amount)

                st.markdown(
                    f"""
                    <div class="result-card">
                        <div class="label">Rating</div>
                        <div class="value">{rating}</div>

                        <div style="height:10px"></div>

                        <div class="label">Percentage Score</div>
                        <div class="value">{pct}%</div>

                        <div style="height:10px"></div>

                        <div class="label">Band</div>
                        <div style="font-weight:600">{band}</div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

                result_df = pd.DataFrame([{
                    "Amount (M)": amount,
                    "Band": band,
                    "Rating": rating,
                    "Percentage Score (%)": pct
                }])

                st.write("")
                st.subheader("Download Result")

                c1, c2 = st.columns(2)
                with c1:
                    st.download_button(
                        "⬇️ Download CSV",
                        result_df.to_csv(index=False).encode("utf-8"),
                        "income_leakage_score.csv",
                        "text/csv"
                    )

                with c2:
                    st.download_button(
                        "⬇️ Download Excel",
                        to_excel_bytes(result_df),
                        "income_leakage_score.xlsx",
                        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )

    with col2:
        st.subheader("Scoring Matrix")
        st.table(make_matrix_df())

with tab_matrix:
    st.subheader("Scoring Matrix")
    st.table(make_matrix_df())

with tab_about:
    st.subheader("About")
    st.markdown(
        f"""
        - Purpose: Convert leakage amounts into performance scores
        - Method: Linear scoring within each band
        - Maximum score capped at **{int(MAX_SCORE)}%**
        - Owner: **{OWNER}**
        """
    )

st.markdown("---")
st.caption(f"Version {APP_VERSION} | Owner: {OWNER}")
