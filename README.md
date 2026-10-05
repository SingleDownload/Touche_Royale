# Touché Royale — Cost & Compliance Decision Model (Streamlit)

An interactive decision-support tool for assessing the cost structure of Touché
Royale's UAE market entry. It is **not a forecast**: it models cost structure,
not sales, and contains no revenue or profit projection.

Every figure is one of three types:
- **Verified** — sourced rate/rule (5% duty, 5% VAT, CEPA 0%, Montaji fee)
- **Founder input** — base, finishing and fixed costs you enter
- **Derived** — calculated live from the two above

## Run locally
```bash
pip install -r requirements.txt
streamlit run app.py
```
Then open the URL Streamlit prints (default http://localhost:8501).

## Host it (free)
1. Push this folder to a public GitHub repo.
2. Go to https://share.streamlit.io, connect the repo, and set the main file to `app.py`.
3. Streamlit Community Cloud installs `requirements.txt` and serves the app at a shareable URL.

## Files
- `app.py` — the application
- `requirements.txt` — dependencies
- `README.md` — this file

## Note
Freight and 3PL figures are benchmark ranges to refine with quotes; defaults are
illustrative. This is decision-support, not financial advice.
