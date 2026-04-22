import streamlit as st
import pandas as pd
from io import BytesIO

# -----------------------------
# BRAND THEME (Co-op Bank Kenya inspired)
# Primary: #064E3B  | Accent: #7ADCB4  [1](https://brandfetch.com/co-opbank.co.ke)
# -----------------------------
COOP_GREEN = "#064E3B"
COOP_MINT = "#7ADCB4"
COOP_BG = "#F4FBF8"
TEXT_DARK = "#0F172A"
TEXT_MUTED = "#475569"
BORDER = "rgba(6, 78, 59, 0.18)"

APP_VERSION = "1.0"
OWNER = "Internal Audit"
MAX_SCORE = 200.0  # hard cap

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

    if amount_m < 1.0:
        pct = interpolate(amount_m, 0.0, 1.0, 0.0, 70.0)
        return round(pct, 2), "Unsatisfactory", "Below 1m"

    if 1.0 <= amount_m <= 5.0:
        pct = interpolate(amount_m, 1.0, 5.0, 71.0, 90.0)
        return round(pct, 2), "Needs Improvement", "1–5m"

    # Gap 5–6 (not defined): map to start of next band
    if 5.0 < amount_m < 6.0:
        return 91.0, "Met Expectations", "6–20m (mapped for 5–6 gap)"

    if 6.0 <= amount_m <= 20.0:
        pct = interpolate(amount_m, 6.0, 20.0, 91.0, 105.0)
        return round(pct, 2), "Met Expectations", "6–20m"

    # Gap 20–21 (not defined): map to start of next band
    if 20.0 < amount_m < 21.0:
        return 106.0, "Exceeds Expectations", "21–100m (mapped for 20–21 gap)"

    if 21.0 <= amount_m <= 100.0:
        pct = interpolate(amount_m, 21.0, 100.0, 106.0, 124.0)
        return round(pct, 2), "Exceeds Expectations", "21–100m"

    # Over 100: linear 100–200 => 125–200 then cap
    pct = interpolate(amount_m, 100.0, 200.0, 125.0, 200.0)
    pct = min(pct, MAX_SCORE)
    return round(pct, 2), "Exceptional", "Over 100m"

def make_matrix_df():
    return pd.DataFrame([
        {"Amount Band (M)": "Below 1m",  "Rating": "Unsatisfactory",      "Score % Range": "<70%"},
        {"Amount Band (M)": "1–5m",      "Rating": "Needs Improvement",   "Score % Range": "71–90%"},
        {"Amount Band (M)": "6–20m",     "Rating": "Met Expectations",    "Score % Range": "91–105%"},
        {"Amount Band (M)": "21–100m",   "Rating": "Exceeds Expectations","Score % Range": "106–124%"},
        {"Amount Band (M)": "Over 100m", "Rating": "Exceptional",         "Score % Range": "125–200%"},
    ])

def df_to_excel_bytes(df: pd.DataFrame) -> bytes:
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Result")
    return output.getvalue()

def rating_badge(rating: str):
    """Return (bg, fg, border) colors for rating pill."""
    palette = {
        "Unsatisfactory": ("rgba(239,68,68,0.12)", "#b91c1c", "rgba(239,68,68,0.35)"),
        "Needs Improvement": ("rgba(245,158,11,0.12)", "#92400e", "rgba(245,158,11,0.35)"),
        "Met Expectations": ("rgba(34,197,94,0.12)", "#166534", "rgba(34,197,94,0.35)"),
        "Exceeds Expectations": ("rgba(59,130,246,0.12)", "#1d4ed8", "rgba(59,130,246,0.35)"),
        "Exceptional": (f"rgba(122,220,180,0.22)", COOP_GREEN, f"rgba(6,78,59,0.35)"),
    }
    return palette.get(rating, (COOP_BG, TEXT_DARK, BORDER))

# -----------------------------
# PAGE CONFIG
# -----------------------------
st.set_page_config(
    page_title="Income Leakage Score Calculator",
    page_icon="✅",
    layout="wide"
)

# -----------------------------
# CUSTOM CSS (UI polish)
# -----------------------------
st.markdown(
    f"""
    <style>
      :root {{
        --coop-green: {COOP_GREEN};
        --coop-mint: {COOP_MINT};
        --coop-bg: {COOP_BG};
        --text-dark: {TEXT_DARK};
        --text-muted: {TEXT_MUTED};
        --border: {BORDER};
      }}

      /* App background */
      .stApp {{
        background: linear-gradient(180deg, #ffffff 0%, var(--coop-bg) 100%);
      }}

      /* Reduce top padding */
      .block-container {{
        padding-top: 1.2rem;
        padding-bottom: 2rem;
      }}

      /* Title header card */
      .hero {{
        background: linear-gradient(135deg, rgba(6,78,59,0.95), rgba(6,78,59,0.75));
        border: 1px solid rgba(255,255,255,0.16);
        border-radius: 18px;
        padding: 18px 18px;
        box-shadow: 0 10px 28px rgba(2, 44, 33, 0.18);
        color: #fff;
      }}
      .hero h1 {{
        font-size: 1.6rem;
        margin: 0 0 6px 0;
        letter-spacing: 0.2px;
      }}
      .hero p {{
        margin: 0;
        color: rgba(255,255,255,0.85);
        font-size: 0.98rem;
      }}
      .hero .chip {{
        display: inline-block;
        padding: 6px 10px;
        margin-top: 10px;
        border-radius: 999px;
        background: rgba(122,220,180,0.18);
        border: 1px solid rgba(122,220,180,0.28);
        font-size: 0.85rem;
      }}

      /* Buttons */
      .stButton > button, .stDownloadButton > button {{
        background: var(--coop-green) !important;
        color: white !important;
        border: 1px solid rgba(6,78,59,0.4) !important;
        border-radius: 14px !important;
        padding: 0.55rem 0.9rem !important;
        box-shadow: 0 10px 18px rgba(6,78,59,0.15);
        transition: transform 0.04s ease-in-out, filter 0.12s ease-in-out;
      }}
      .stButton > button:hover, .stDownloadButton > button:hover {{
        filter: brightness(1.05);
        transform: translateY(-1px);
      }}

      /* Number input container */
      [data-testid="stNumberInput"] {{
        background: rgba(255,255,255,0.85);
        border-radius: 14px;
        border: 1px solid var(--border);
        padding: 10px 12px;
      }}

      /* Tables */
      .stTable {{
        border-radius: 14px;
        overflow: hidden;
        border: 1px solid var(--border);
      }}

      /* Section headings */
      h2, h3, h4 {{
        color: var(--text-dark);
      }}

      /* Metric cards */
      .metric-card {{
        background: rgba(255,255,255,0.9);
        border: 1px solid var(--border);
        border-radius: 18px;
        padding: 14px 14px;
        box-shadow: 0 10px 20px rgba(2, 44, 33, 0.08);
      }}
      .metric-title {{
        color: var(--text-muted);
        font-size: 0.86rem;
        margin: 0 0 4px 0;
      }}
      .metric-value {{
        color: var(--text-dark);
        font-weight: 750;
        font-size: 1.4rem;
        margin: 0;
      }}

      /* Rating pill */
      .pill {{
        display:inline-flex;
        align-items:center;
        gap:8px;
        padding: 8px 12px;
        border-radius: 999px;
        font-weight: 650;
        font-size: 0.92rem;
        border: 1px solid var(--border);
      }}

      /* Footer */
      .footer {{
        color: var(--text-muted);
        font-size: 0.85rem;
      }}
    </style>
    """,
    unsafe_allow_html=True
)

# -----------------------------
# HEADER
# -----------------------------
st.markdown(
    f"""
    <div class="hero">
      <h1>Income Leakage Score Calculator</h1>
      <p>Enter the amount (in millions) to get the <b>Rating</b> and <b>Percentage Score</b> based on the approved matrix.</p>
      <div class="chip">Max Score: 200%</div>
    </div>
    """,
    unsafe_allow_html=True
)

st.write("")  # spacing

# -----------------------------
# SIDEBAR
# -----------------------------
with st.sidebar:
    st.markdown(f"### Controls")
    st.caption("Use the calculator tab to compute and export a result.")
    st.markdown("---")
    st.markdown("### Quick Notes")
    st.markdown(
        "- Input is in **millions (M)**\n"
        "- Output is **% Score** + **Rating**\n"
        f"- Max score capped at **{int(MAX_SCORE)}%**"
    )
    st.markdown("---")
    st.caption(f"Version {APP_VERSION} • Owner: {OWNER}")

# -----------------------------
# MAIN TABS
# -----------------------------
tab_calc, tab_matrix, tab_about = st.tabs(["✅ Calculator", "📋 Matrix", "ℹ️ About"])

with tab_calc:
    left, right = st.columns([1.15, 0.85], gap="large")

    with left:
        st.subheader("Enter Amount")
        st.caption("Example: 40 means 40M")

        # Use a form so calculation only runs on submit [2](https://github.com/karunkri/Financial-Score-Prediction-App)
        with st.form("score_form", clear_on_submit=False):
            amount_m = st.number_input(
                "Amount (Millions)",
                min_value=0.0,
                value=None,      # allows empty until user provides input [4](https://www.youtube.com/watch?v=yNTtLZ4zfA0)
                step=0.1,
                format="%.1f",
                placeholder="Type e.g., 40"
            )
            submitted = st.form_submit_button("Calculate")

        if submitted:
            if amount_m is None:
                st.warning("Please enter a value first (amount in millions).")
            else:
                pct, rating, band = calculate_score(float(amount_m))
                if pct is None:
                    st.error(band)
                else:
                    bg, fg, br = rating_badge(rating)

                    # Output cards
                    st.markdown(
                        f"""
                        <div class="metric-card">
                          <div class="pill" style="background:{bg}; color:{fg}; border:1px solid {br};">
                            ✅ Rating: <span style="font-weight:800">{rating}</span>
                          </div>
                          <div style="height:10px"></div>
                          <p class="metric-title">Percentage Score</p>
                          <p class="metric-value">{pct}%</p>
                          <div style="height:8px"></div>
                          <p class="metric-title">Band</p>
                          <p style="margin:0; color:{TEXT_DARK}; font-weight:650;">{band}</p>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

                    # Export table
                    result_df = pd.DataFrame([{
                        "Amount (M)": float(amount_m),
                        "Band": band,
                        "Rating": rating,
                        "Percentage Score (%)": pct
                    }])

                    st.write("")
                    st.subheader("Download Result")

                    csv_bytes = result_df.to_csv(index=False).encode("utf-8")
                    xlsx_bytes = df_to_excel_bytes(result_df)

                    c1, c2 = st.columns(2)
                    with c1:
                        st.download_button(
                            label="⬇️ Download CSV",
                            data=csv_bytes,
                            file_name="income_leakage_score_result.csv",
                            mime="text/csv"
                        )  # [3](https://docs.streamlit.io/develop/api-reference/execution-flow/st.form)
                    with c2:
                        st.download_button(
                            label="⬇️ Download Excel",
                            data=xlsx_bytes,
                            file_name="income_leakage_score_result.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )  # [3](https://docs.streamlit.io/develop/api-reference/execution-flow/st.form)

    with right:
        st.subheader("Quick Guide")
        st.markdown(
            "- **Step 1:** Type amount in millions (M)\n"
            "- **Step 2:** Click **Calculate**\n"
            "- **Step 3:** Download result (CSV/Excel)"
        )
        st.write("")

        st.subheader("Matrix Snapshot")
        st.table(make_matrix_df())

with tab_matrix:
    st.subheader("Scoring Matrix")
    st.caption("Reference bands and percentage ranges.")
    st.table(make_matrix_df())

with tab_about:
    st.subheader("About this tool")
    st.markdown(
        "- Purpose: Convert **amount (M)** into a **% score** and **rating**\n"
        "- Method: Linear scoring within each band\n"
        f"- Cap: Scores above maximum are capped at **{int(MAX_SCORE)}%**"
    )
    st.info("Tip: Keep this link in Teams for quick access by the team.")

st.markdown("---")
st.markdown(
    f"<div class='footer'>Version {APP_VERSION} | Scoring capped at {int(MAX_SCORE)}% | Owner: {OWNER}</div>",
    unsafe_allow_html=True
)
