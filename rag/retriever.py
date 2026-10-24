# rag/retriever.py — top-k card retrieval. Same code is used by both modes.
import pickle
import numpy as np
from config import INDEX_PATH, RETRIEVAL_TOP_K

class Retriever:
    def __init__(self, path=INDEX_PATH):
        with open(path, "rb") as f:
            d = pickle.load(f)
        self.cards = d["cards"]
        self.vec = d["vectorizer"]
        self.tfidf = d["tfidf"]

    def query(self, text: str, k: int = RETRIEVAL_TOP_K):
        q = self.vec.transform([text])
        scores = (self.tfidf @ q.T).toarray().ravel()
        idx = np.argsort(scores)[::-1][:k]
        return [{**self.cards[i], "_score": float(scores[i])} for i in idx]