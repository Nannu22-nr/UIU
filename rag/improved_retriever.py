# rag/improved_retriever.py
# The single clearly identified change: applicability checking and targeted
# missing-information question selection. Retrieval, model, prompt template and
# input cases stay the same as Baseline.

from rag.retriever import Retriever

def _norm(s: str) -> str:
    return (s or "").lower()

def applicability_report(cards, case_text):
    """For each retrieved card decide: applicable / excluded / applicable_with_gaps,
    with short reasons. Rule-based and transparent; no extra LLM call."""
    report = []
    for c in cards:
        reasons = []
        status = "applicable"

        for ex in (c.get("exclusions") or []):
            words = [w for w in _norm(ex).replace(",", " ").split() if len(w) > 4]
            hits = [w for w in words if w in _norm(case_text)]
            if hits:
                status = "excluded"
                reasons.append(f"exclusion triggered: '{ex}' (matched: {hits[:2]})")

        for mi in (c.get("missing_information") or []):
            words = [w for w in _norm(mi).replace(",", " ").split() if len(w) > 3]
            if words and not any(w in _norm(case_text) for w in words):
                reasons.append(f"missing: '{mi}'")

        if status == "applicable" and reasons:
            status = "applicable_with_gaps"

        report.append({
            "card_id": c["card_id"],
            "disease": c["disease"],
            "status": status,
            "notes": reasons or ["prerequisites/exclusions appear satisfied by case text"],
        })
    return report

def targeted_questions(report):
    """Convert 'missing: X' notes into explicit questions."""
    qs = []
    for r in report:
        for n in r["notes"]:
            if n.startswith("missing:"):
                field = n.replace("missing:", "").strip().strip("'")
                qs.append(f"[{r['card_id']}] Please confirm: {field}")
    seen, out = set(), []
    for q in qs:
        if q not in seen:
            seen.add(q)
            out.append(q)
    return out

class ImprovedRetriever(Retriever):
    def query_with_report(self, case_text, k=None):
        cards = self.query(case_text, k=k) if k else self.query(case_text)
        report = applicability_report(cards, case_text)
        questions = targeted_questions(report)
        return cards, report, questions