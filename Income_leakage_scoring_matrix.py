import streamlit as st
import pandas as pd
from io import BytesIO

# -----------------------------
# Config
# -----------------------------
APP_VERSION = "1.0"
OWNER = "Internal Audit"
MAX_SCORE = 200.0  # hard cap

# Scoring matrix (amounts in millions)
# Each band has: min_amount, max_amount, min_score_pct, max_score_pct, rating
BANDS = [
    {"min_a": 0.0,  "max_a": 1.0,   "min_p": 0.0,   "max_p": 70.0,  "rating": "Unsatisfactory"},
    {"min_a": 1.0,  "max_a": 5.0,   "min_p": 71.0,  "max_p": 90.0,  "rating": "Needs Improvement"},
    {"min_a": 6.0,  "max_a": 20.0,  "min_p": 91.0,  "max_p": 105.0, "rating": "Met Expectations"},
    {"min_a": 21.0, "max_a": 100.0, "min_p": 106.0, "max_p": 124.0, "rating": "Exceeds Expectations"},
    # "Over 100m" band: we'll treat 100–200 as linear to 200%, then cap above 200
    {"min_a": 100.0, "max_a": 200.0, "min_p": 125.0, "max_p": 200.0, "rating": "Exceptional"},
]


def interpolate(value, x0, x1, y0, y1):
    """Linear interpolation. If x0==x1, return y1 to avoid division errors."""
    if x1 == x0:
        return y1
    return y0 + (value - x0) * (y1 - y0) / (x1 - x0)


def calculate_score(amount_m):
    """
    amount_m: amount in millions (float)
    Returns: (percent_score, rating, band_label)
    """
    if amount_m < 0:
        return None, "Invalid", "Amount cannot be negative"

    # Handle 0–1 band (pro-rata to 70%)
    if amount_m < 1.0:
        pct = interpolate(amount_m, 0.0, 1.0, 0.0, 70.0)
        return round(pct, 2), "Unsatisfactory", "Below 1m"

    # 1–5
    if 1.0 <= amount_m <= 5.0:
        pct = interpolate(amount_m, 1.0, 5.0, 71.0, 90.0)
        return round(pct, 2), "Needs Improvement", "1–5m"

    # 5–6 gap: not explicitly defined in your matrix.
    # Common treatment: treat 5–6 as the start of the next band at 91%.
    if 5.0 < amount_m < 6.0:
        return 91.0, "Met Expectations", "6–20m (mapped for 5–6 gap)"

    # 6–20
    if 6.0 <= amount_m <= 20.0:
        pct = interpolate(amount_m, 6.0, 20.0, 91.0, 105.0)
        return round(pct, 2), "Met Expectations", "6–20m"

    # 20–21 gap: treat 20–21 as start of next band at 106%
    if 20.0 < amount_m < 21.0:
        return 106.0, "Exceeds Expectations", "21–100m (mapped for 20–21 gap)"

    # 21–100
    if 21.0 <= amount_m <= 100.0:
        pct = interpolate(amount_m, 21.0, 100.0, 106.0, 124.0)
        return round(pct, 2), "Exceeds Expectations", "21–100m"

    # Over 100: 100–200 linear to 200%, then cap
    pct = interpolate(amount_m, 100.0, 200.0, 125.0, 200.0)
    pct = min(pct, MAX_SCORE)
    return round(pct, 2), "Exceptional", "Over 100m"


def make_matrix_df():
    return pd.DataFrame([
        {"Amount Band (M)": "Below 1m",    "Rating": "Unsatisfactory",     "Score % Range": "<70%"},
        {"Amount Band (M)": "1–5m",        "Rating": "Needs Improvement",  "Score % Range": "71–90%"},
        {"Amount Band (M)": "6–20m",       "Rating": "Met Expectations",   "Score % Range": "91–105%"},
        {"Amount Band (M)": "21–100m",     "Rating": "Exceeds Expectations","Score % Range": "106–124%"},
        {"Amount Band (M)": "Over 100m",   "Rating": "Exceptional",        "Score % Range": "125–200%"},
    ])


def df_to_excel_bytes(df: pd.DataFrame) -> bytes:
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Result")
    return output.getvalue()


# -----------------------------
# UI
# -----------------------------
st.set_page_config(page_title="Income Leakage Score Calculator", layout="centered")
st.title("Income Leakage Score Calculator")

with st.expander("How to use", expanded=True):
    st.markdown(
        "- Enter the **amount in millions (M)**.\n"
        "- Click **Calculate**.\n"
        "- The app shows the **Rating** and **Percentage Score**.\n"
        "- Use the download buttons to export the result (CSV / Excel)."
    )

st.subheader("Scoring Matrix")
st.table(make_matrix_df())

st.divider()

# Use a form so the app only calculates when user clicks submit
# (Forms batch widget changes until submit) [2](https://docs.streamlit.io/develop/api-reference/execution-flow/st.form)
with st.form("score_form", clear_on_submit=False):
    amount_m = st.number_input(
        "Enter amount (in millions, e.g., 40 for 40M)",
        min_value=0.0,
        value=None,              # allows 'no value yet' and returns None until user inputs [4](https://docs.streamlit.io/develop/api-reference/widgets/st.number_input)
        step=0.1,
        format="%.1f",
        placeholder="Type a number e.g., 40"
    )
    submitted = st.form_submit_button("Calculate")

if submitted:
    if amount_m is None:
        st.warning("Please enter a value first (amount in millions).")
    else:
        pct, rating, band = calculate_score(float(amount_m))

        if pct is None:
            st.error(band)  # contains the error message in this case
        else:
            st.success(f"Rating: {rating}")
            st.info(f"Percentage Score: {pct}%")
            st.write(f"Band: **{band}**")

            # Build a simple result row for exporting
            result_df = pd.DataFrame([{
                "Amount (M)": float(amount_m),
                "Band": band,
                "Rating": rating,
                "Percentage Score (%)": pct
            }])

            st.subheader("Download Result")
            csv_bytes = result_df.to_csv(index=False).encode("utf-8")
            xlsx_bytes = df_to_excel_bytes(result_df)

            # Download buttons (Streamlit built-in) [1](https://docs.streamlit.io/develop/api-reference/widgets/st.download_button)
            st.download_button(
                label="⬇️ Download CSV",
                data=csv_bytes,
                file_name="income_leakage_score_result.csv",
                mime="text/csv"
            )

            st.download_button(
                label="⬇️ Download Excel",
                data=xlsx_bytes,
                file_name="income_leakage_score_result.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

st.markdown("---")
st.caption(f"Version {APP_VERSION} | Scoring capped at {int(MAX_SCORE)}% | Owner: {OWNER}")
