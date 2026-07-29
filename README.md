# Warehouse Inventory Analytics Dashboard

A Streamlit dashboard analyzing ~5,000 warehouse movement records to answer
five business questions about stock discrepancies, supplier pricing, and
stockout risk. Full written answers are in [`BUSINESS_ANSWERS.md`](./BUSINESS_ANSWERS.md).

## Approach

I started by exploring the raw movement log rather than trusting any field
at face value (e.g. I checked whether `status = 'Discrepancy'` actually
corresponds to broken stock math before using it — it doesn't always, so I
treated it as its own signal rather than re-deriving it). From there:

1. Cleaned obvious data issues (15 exact duplicate rows) without touching
   anything that looked like a real business signal (negative stock,
   discrepancy flags, supplier pricing anomalies — those *are* the analysis).
2. Answered each business question with a specific, reproducible
   calculation (grouped rates, a chi-square significance test, correlation
   checks, SKU-level oversell ranking) — see `app.py` for the exact logic
   behind every chart.
3. Built a single-page Streamlit dashboard so the numbers behind each answer
   are interactive and filterable by warehouse/movement type, rather than
   static screenshots.

Data quality caveats and everything I chose *not* to "fix" are documented in
Q4 of `BUSINESS_ANSWERS.md`.

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

Then open the local URL Streamlit prints (typically `http://localhost:8501`).

## Deploy (Streamlit Community Cloud — free)

1. Push this repo to a public GitHub repo.
2. Go to [share.streamlit.io](https://share.streamlit.io), sign in with
   GitHub.
3. Click **New app**, select this repo/branch, set the main file to
   `app.py`, and deploy.
4. Streamlit Cloud installs `requirements.txt` automatically and gives you a
   public URL (`https://<your-app-name>.streamlit.app`).

## Repo structure

```
.
├── app.py                     # Streamlit dashboard (all 5 questions)
├── inventory_movements.csv    # Source data
├── requirements.txt
├── README.md
└── BUSINESS_ANSWERS.md        # Written answers, methods, caveats
```
