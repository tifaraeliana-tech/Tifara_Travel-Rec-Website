import streamlit as st
import pandas as pd
import numpy as np

# -------------------------------------------------
# Smart Travel City Recommender
# Dataset: Travel City Index (CC BY 4.0)
# -------------------------------------------------

st.set_page_config(
    page_title="Smart Travel Recommender",
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

@st.cache_data
def load_data():
    """Load the CSV locally first, then try the public dataset URL."""
    try:
        return pd.read_csv(LOCAL_DATA)
    except FileNotFoundError:
        return pd.read_csv(DATA_URL)

def prepare_data(df):
    """Create one annual average temperature value per city."""
    df = df.copy()

    high_cols = [f"{month}_temp_high_c" for month in MONTHS]
    low_cols = [f"{month}_temp_low_c" for month in MONTHS]

    # Convert numeric columns safely.
    required_numeric = ["budget_usd_day"] + high_cols + low_cols
    for col in required_numeric:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Annual average of monthly daytime highs and nighttime lows.
    available_high = [c for c in high_cols if c in df.columns]
    available_low = [c for c in low_cols if c in df.columns]

    if not available_high or not available_low:
        raise ValueError("The dataset does not contain the expected monthly temperature columns.")

    df["avg_temp_c"] = (
        df[available_high].mean(axis=1) +
        df[available_low].mean(axis=1)
    ) / 2

    # Keep only rows with the fields needed for recommendations.
    df = df.dropna(subset=["city", "country", "budget_usd_day", "avg_temp_c"])
    return df

def recommend_cities(df, daily_budget, climate_preference):
    """Filter by budget and rank cities by climate match."""
    minimum, maximum = CLIMATE_RANGES[climate_preference]

    # Budget is treated as the user's maximum daily budget.
    matches = df[df["budget_usd_day"] <= daily_budget].copy()

    if minimum is not None and maximum is not None:
        target_temp = (minimum + maximum) / 2
    elif maximum is not None:
        target_temp = maximum - 2.5
    else:
        target_temp = minimum + 2.5

    if matches.empty:
        return matches, target_temp

    # Smaller temperature difference = better climate match.
    matches["temperature_difference"] = (
        matches["avg_temp_c"] - target_temp
    ).abs()

    # Rank primarily by climate match, then by lower daily cost.
    matches = matches.sort_values(
        by=["temperature_difference", "budget_usd_day"],
        ascending=[True, True]
    )

    # A simple, transparent score based on temperature difference.
    matches["match_score"] = (
        100 - (matches["temperature_difference"] * 5)
    ).clip(lower=0, upper=100)

    return matches.head(5), target_temp

# ---------------- PAGE DESIGN ----------------

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}
.block-container {
    max-width: 1100px;
    padding-top: 2rem;
    padding-bottom: 3rem;
}
.hero {
    background: linear-gradient(120deg, #123b52, #167d83);
    padding: 2.6rem 2rem;
    border-radius: 18px;
    color: white;
    margin-bottom: 2rem;
}
.hero h1 {
    color: white;
    font-size: 2.35rem;
    margin-bottom: .5rem;
}
.hero p {
    color: #e1f5f3;
    font-size: 1.05rem;
    margin-bottom: 0;
}
.result-card {
    border: 1px solid #dbe5e8;
    border-radius: 14px;
    padding: 1.2rem;
    margin-bottom: .8rem;
    background: white;
}
.small-label {
    color: #61747c;
    font-size: .85rem;
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="hero">
    <div style="font-size:13px; letter-spacing:2px; text-transform:uppercase;">
        ✈️ Smart Travel · City Discovery
    </div>
    <h1>Find Your Next Destination</h1>
    <p>Discover cities that fit your daily budget and preferred climate.</p>
</div>
""", unsafe_allow_html=True)

# ---------------- USER INPUTS ----------------

st.subheader("Your travel preferences")
st.write("Choose just two things. We'll find cities that best match them.")

col1, col2 = st.columns(2)

with col1:
    daily_budget = st.number_input(
        "Your maximum daily budget (USD)",
        min_value=1.0,
        max_value=1000.0,
        value=100.0,
        step=5.0,
        help="This is your estimated daily destination budget, not including flights."
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
    raw_data = load_data()
    cities = prepare_data(raw_data)

    if search:
        recommendations, target_temp = recommend_cities(
            cities, daily_budget, climate_preference
        )

        st.divider()
        st.subheader("Your recommended destinations")

        if recommendations.empty:
            cheapest = cities.sort_values("budget_usd_day").head(3)
            st.warning(
                "No cities in the dataset have an estimated daily budget "
                "within your limit. Here are three of the least expensive cities instead."
            )
            recommendations = cheapest

        st.caption(
            f"Showing up to 5 cities · Maximum budget: ${daily_budget:,.0f}/day · "
            f"Preferred climate: {climate_preference}"
        )

        for _, city in recommendations.iterrows():
            score = city.get("match_score", np.nan)
            score_text = f"{score:.0f}%" if pd.notna(score) else "Budget alternatives"

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

        st.info(
            "How matching works: cities over your budget are excluded. "
            "The remaining cities are ranked by how close their annual average "
            "temperature is to the middle of your selected climate range. "
            "The match score measures temperature similarity, not overall trip quality."
        )

    with st.expander("About the dataset and recommendation method"):
        st.write(
            "This app uses the Travel City Index dataset. Daily costs are modeled "
            "estimates, not guaranteed real-world prices. Temperature is calculated "
            "as the average of the 12 monthly high and low temperature averages. "
            "Because no travel month is requested, the recommendation uses an annual "
            "average and may hide seasonal differences."
        )
        st.markdown(
            '[Dataset source: Travel City Index](https://travelcityindex.com/dataset) '
            '· Licensed under CC BY 4.0.'
        )

except Exception as error:
    st.error(
        "I couldn't load the city dataset. Check your internet connection or "
        "place travelcityindex-cities.csv in the same folder as app.py."
    )
    st.caption(f"Technical details: {error}")
