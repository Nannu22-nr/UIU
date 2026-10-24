# AIMScribe Question 2 — Groq-backed Clinical Protocol Recommender

Two-mode prototype (Baseline vs Improved). It reads patient symptoms (no disease name required),
retrieves canonical protocol cards from Question 1, and asks a Groq-hosted LLM for:
probable diagnosis, investigations, medication planning, and advice — with evidence citations.

## Setup
```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 1) copy your Question 1 dataset here
cp ../cards.jsonl cards.jsonl

# 2) add Groq key
cp .env.example .env
# edit .env and paste GROQ_API_KEY

# 3) build index (creates index/rag_index.pkl)
python build_index.py

# 4) run
streamlit run app.py