# Smart Travel Recommender

A simple Streamlit app that recommends travel destinations using:
1. Maximum daily budget (USD)
2. Preferred climate

## Files

```text
SmartTravelRecommender/
├── app.py
├── requirements.txt
└── README.md
```

The app downloads the CSV from Travel City Index automatically. If you prefer,
download `travelcityindex-cities.csv` and place it beside `app.py`.

Dataset: https://travelcityindex.com/data/travelcityindex-cities.csv  
Dataset information and attribution: https://travelcityindex.com/dataset  
License: CC BY 4.0. Credit Travel City Index (travelcityindex.com).

## Run locally

1. Install Python.
2. Open a terminal in this folder.
3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Start the app:

```bash
streamlit run app.py
```

## Recommendation logic

- Cities with `budget_usd_day` above the user's budget are filtered out.
- Annual average temperature is calculated from the 12 monthly high and low
  temperature averages.
- Remaining cities are ranked by how close their average temperature is to
  the middle of the selected climate range.
- The displayed match score represents temperature similarity only.

Daily costs are modeled estimates, not guaranteed prices. The app uses annual
average climate because the interface intentionally asks for only two inputs;
seasonal differences may therefore be hidden.
