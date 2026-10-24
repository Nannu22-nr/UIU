# build_index.py — store and index canonical cards in a simple RAG store.
# Run this ONCE before starting the app. It creates index/rag_index.pkl.
import json, os, pickle
from sklearn.feature_extraction.text import TfidfVectorizer
from config import CARDS_PATH, INDEX_PATH

def card_to_text(c: dict) -> str:
    parts = [
        c.get("disease", ""),
        c.get("clinical_category", ""),
        " ".join(c.get("symptoms_or_prerequisites", []) or []),
        c.get("recommended_action", ""),
        " ".join(c.get("exclusions", []) or []),
        " ".join(c.get("missing_information", []) or []),
        c.get("evidence_passage", ""),
    ]
    return " || ".join(p for p in parts if p)

def main():
    if not os.path.exists(CARDS_PATH):
        raise SystemExit("Missing cards.jsonl — copy your Question 1 dataset here.")
    cards = [json.loads(l) for l in open(CARDS_PATH, encoding="utf-8") if l.strip()]
    texts = [card_to_text(c) for c in cards]
    vec = TfidfVectorizer(ngram_range=(1, 2), min_df=1, sublinear_tf=True)
    X = vec.fit_transform(texts)
    os.makedirs(os.path.dirname(INDEX_PATH), exist_ok=True)
    with open(INDEX_PATH, "wb") as f:
        pickle.dump({"cards": cards, "vectorizer": vec, "tfidf": X}, f)
    print(f"[index] wrote {len(cards)} cards to {INDEX_PATH}")

if __name__ == "__main__":
    main()