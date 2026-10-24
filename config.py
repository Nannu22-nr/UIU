# config.py — all shared settings.
# Baseline and Improved differ only by the one change implemented in rag/improved_retriever.py.
# Model, temperature, top-k and prompt template stay fixed in both modes.

import os
import streamlit as st
from dotenv import load_dotenv

# লোকাল মেশিনে .env ফাইল লোড করবে
load_dotenv()

# Retrieval (identical in both modes)
RETRIEVAL_TOP_K = 6
INDEX_PATH = "index/rag_index.pkl"
CARDS_PATH = "cards.jsonl"

# Model (identical in both modes)
# Streamlit Cloud Secrets অথবা লোকাল .env থেকে API Key নেওয়া
try:
    if "GROQ_API_KEY" in st.secrets:
        GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
        GROQ_MODEL = st.secrets.get("GROQ_MODEL", "openai/gpt-oss-120b")
    else:
        raise KeyError
except Exception:
    # লোকাল মেশিনের জন্য fallback (.env)
    GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
    GROQ_MODEL = os.environ.get("GROQ_MODEL", "openai/gpt-oss-120b")

LLM_TEMPERATURE = 0.0
LLM_MAX_TOKENS = 1400

# The one clearly identified change that defines Improved mode
IMPROVEMENT = {
    "name": "Applicability-check + targeted missing-information question selection",
    "where": "rag/improved_retriever.py, called before the LLM in app.py Improved branch",
    "what_changes": (
        "For each retrieved card, compare its 'exclusions' and 'missing_information' "
        "against the patient text. Flag excluded cards and list missing fields as explicit "
        "questions. Pass these to the same Groq model with the same prompt template plus an "
        "applicability report block."
    ),
    "cost": (
        "One local rule-based pre-step (no extra LLM call). Adds ~0.01-0.05 s latency and "
        "~200-400 prompt tokens per case. No additional API call."
    ),
    "falsification": (
        "If Improved mode does not increase the count of 'missing info handled without guessing' "
        "passes by at least 1 out of 6 cases versus Baseline, the improvement is not supported."
    ),
}