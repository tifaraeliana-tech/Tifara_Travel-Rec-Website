import streamlit as st
import pandas as pd
import numpy as np

# ---------------- PAGE SETTINGS ----------------
st.set_page_config(
    page_title="The Travel Edit",
    page_icon="✈️",
    layout="wide"
)

DATA_URL = "https://travelcityindex.com/data/travelcityindex-cities.csv"
LOCAL_DATA = "travelcityindex-cities.csv"

MONTHS = [
    "jan", "feb", "mar", "apr", "may", "jun",
    "jul", "aug", "sep", "oct", "nov", "dec"
]

CLIMATE_RANGES = {
    "Cool (below 15°C)": (None, 15),
    "Mild (15–22°C)": (15, 22),
    "Warm (22–28°C)": (22, 28),
    "Hot (above 28°C)": (28, None),
}

# ---------------- DATA & RECOMMENDATION ----------------
@st.cache_data
def load_data():
    try:
        return pd.read_csv(LOCAL_DATA)
    except FileNotFoundError:
        return pd.read_csv(DATA_URL)


def prepare_data(df):
    df = df.copy()
    high_cols = [f"{month}_temp_high_c" for month in MONTHS]
    low_cols = [f"{month}_temp_low_c" for month in MONTHS]

    for col in ["budget_usd_day"] + high_cols + low_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    available_high = [col for col in high_cols if col in df.columns]
    available_low = [col for col in low_cols if col in df.columns]

    if not available_high or not available_low:
        raise ValueError("The dataset is missing monthly temperature columns.")

    df["avg_temp_c"] = (
        df[available_high].mean(axis=1) + df[available_low].mean(axis=1)
    ) / 2

    return df.dropna(subset=["city", "country", "budget_usd_day", "avg_temp_c"])


def recommend_cities(df, daily_budget, climate_preference):
    minimum, maximum = CLIMATE_RANGES[climate_preference]
    matches = df[df["budget_usd_day"] <= daily_budget].copy()

    if minimum is not None and maximum is not None:
        target_temp = (minimum + maximum) / 2
    elif maximum is not None:
        target_temp = maximum - 2.5
    else:
        target_temp = minimum + 2.5

    if matches.empty:
        return matches

    matches["temperature_difference"] = (
        matches["avg_temp_c"] - target_temp
    ).abs()
    matches = matches.sort_values(
        by=["temperature_difference", "budget_usd_day"],
        ascending=[True, True]
    )
    matches["match_score"] = (
        100 - matches["temperature_difference"] * 5
    ).clip(lower=0, upper=100)

    return matches.head(5)


# ---------------- PAGE DESIGN ----------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@1,400;1,500;1,600;1,700&display=swap');

html, body, [class*="css"], [data-testid="stAppViewContainer"] {
    font-family: 'Playfair Display', Georgia, serif !important;
    font-style: italic !important;
}

.block-container {
    max-width: 1100px;
    padding-top: 1.5rem;
    padding-bottom: 3rem;
}

.hero {
    background-image: linear-gradient(rgba(20, 28, 25, 0.42), rgba(20, 28, 25, 0.55)),
        url('https://i.pinimg.com/1200x/29/ad/b3/29adb3d01648148b2c4b2326db4e7ab8.jpg');
    background-size: cover;
    background-position: center;
    min-height: 280px;
    padding: 3.2rem 2.5rem;
    border-radius: 16px;
    color: white;
    margin-bottom: 2rem;
    position: relative;
}

.hero h1 {
    color: white;
    font-size: 2.8rem;
    font-weight: 600;
    margin: 1.2rem 0 0.5rem 0;
}

.hero p {
    color: white;
    font-size: 1.15rem;
    margin: 0;
}

.author {
    position: absolute;
    top: 18px;
    right: 22px;
    color: white;
    font-size: 0.95rem;
    letter-spacing: 1px;
}

.result-card {
    border: 1px solid #ded8ce;
    border-radius: 12px;
    padding: 1rem 1.2rem;
    margin-bottom: 0.8rem;
    background: rgba(255, 255, 255, 0.92);
}

div.stButton > button {
    border-radius: 10px;
    font-family: 'Playfair Display', Georgia, serif;
    font-style: italic;
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="hero">
    <div class="author">Tifara 11 Evan</div>
    <div style="font-size: 13px; letter-spacing: 2px; text-transform: uppercase;">
        ✈️ Travel City Discovery
    </div>
    <h1>The Travel Edit</h1>
    <p>Find a destination that fits your budget and your preferred climate.</p>
</div>
""", unsafe_allow_html=True)

# ---------------- USER INPUTS ----------------
st.subheader("Your travel preferences")
col1, col2 = st.columns(2)

with col1:
    daily_budget = st.number_input(
        "Your maximum daily budget (USD)",
        min_value=1.0,
        max_value=1000.0,
        value=100.0,
        step=5.0
    )

with col2:
    climate_preference = st.selectbox(
        "What climate do you prefer?",
        options=list(CLIMATE_RANGES.keys()),
        index=2
    )

search = st.button("Find my destinations ✨", type="primary", use_container_width=True)

# ---------------- RECOMMENDATIONS ----------------
try:
    cities = prepare_data(load_data())

    if search:
        recommendations = recommend_cities(cities, daily_budget, climate_preference)
        st.divider()
        st.subheader("Your recommended destinations")

        if recommendations.empty:
            st.warning("No cities fit this budget. Here are three of the least expensive cities instead.")
            recommendations = cities.sort_values("budget_usd_day").head(3)

        for _, city in recommendations.iterrows():
            score = city.get("match_score", np.nan)
            score_text = f"{score:.0f}%" if pd.notna(score) else "Budget alternative"

            st.markdown('<div class="result-card">', unsafe_allow_html=True)
            left, middle, right = st.columns([2, 1, 1])

            with left:
                st.markdown(f"### 📍 {city['city']}, {city['country']}")
                st.caption(f"Average annual temperature: {city['avg_temp_c']:.1f}°C")

            with middle:
                st.metric("Estimated daily budget", f"${city['budget_usd_day']:.0f}")

            with right:
                st.metric("Climate match", score_text)

            page_url = city.get("page_url")
            if pd.notna(page_url):
                st.markdown(f"[Explore this city]({page_url})")

            st.markdown("</div>", unsafe_allow_html=True)

    # Dataset attribution retained in brief form for the dataset's CC BY 4.0 license.
    st.caption("Dataset: Travel City Index · CC BY 4.0")

except Exception as error:
    st.error("I couldn't load the city dataset. Check your internet connection or place travelcityindex-cities.csv beside app.py.")
    st.caption(f"Technical details: {error}")
