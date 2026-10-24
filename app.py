import os, json, time, datetime
from pathlib import Path
import streamlit as st
from config import RETRIEVAL_TOP_K, IMPROVEMENT, GROQ_MODEL
from rag.retriever import Retriever
from rag.improved_retriever import ImprovedRetriever
from llm.client import call_llm

st.set_page_config(page_title="AIMScribe Q2 Recommender", layout="wide")
st.title("Clinical Protocol Recommender - Dengue / Hypertension / Cholera / Chikungunya")
st.caption("Prototype for assessment. Not for clinical use. Model: Groq.")

# ---------- Sidebar ----------
with st.sidebar:
    st.header("Mode")
    mode = st.radio("Select mode", ["Baseline", "Improved"], index=0)
    st.caption(f"Improved change: {IMPROVEMENT['name']}")
    st.caption(f"Groq model: {GROQ_MODEL}")

    st.header("Load a demo case")
    case_files = sorted(os.listdir("cases")) if os.path.isdir("cases") else []
    case_choice = st.selectbox("Case", ["(manual input)"] + case_files)
    if case_choice != "(manual input)":
        with open(os.path.join("cases", case_choice), encoding="utf-8") as f:
            st.session_state["case"] = json.load(f)
    else:
        st.session_state["case"] = {}

    st.header("Settings")
    st.write("Retrieval top-k:", RETRIEVAL_TOP_K)
    st.write("Temperature: 0.0 (fixed for both modes)")

# ---------- Patient input ----------
case = st.session_state.get("case", {})

col1, col2 = st.columns(2)
with col1:
    complaints = st.text_area("Chief complaints / symptoms", value=case.get("complaints", ""), height=100)
    duration = st.text_input("Illness duration", value=str(case.get("duration", "")))
    age = st.text_input("Age", value=str(case.get("age", "")))
    sex_opts = ["", "Male", "Female", "Other"]
    sex_val = case.get("sex", "")
    sex = st.selectbox("Sex", sex_opts, index=sex_opts.index(sex_val) if sex_val in sex_opts else 0)
with col2:
    history = st.text_area("Medical history", value=case.get("history", ""), height=80)
    meds = st.text_area("Current medicines", value=case.get("medicines", ""), height=60)
    allergies = st.text_area("Allergies", value=case.get("allergies", ""), height=60)
    extra = st.text_area("Other details (vitals, labs, pregnancy, etc.)", value=case.get("extra", ""), height=80)

case_text = (
    f"Chief complaints: {complaints}\n"
    f"Duration: {duration}\n"
    f"Age: {age}; Sex: {sex}\n"
    f"History: {history}\n"
    f"Medicines: {meds}\n"
    f"Allergies: {allergies}\n"
    f"Other: {extra}\n"
)

# ---------- Prompt ----------
def build_prompt(cards, applicability=None, questions=None):
    card_lines = []
    for c in cards:
        card_lines.append(
            f"- CARD {c['card_id']} | {c['disease']} | {c['clinical_category']}\n"
            f"  prerequisites: {c.get('symptoms_or_prerequisites')}\n"
            f"  action: {c.get('recommended_action')}\n"
            f"  exclusions: {c.get('exclusions')}\n"
            f"  missing_information: {c.get('missing_information')}\n"
            f"  evidence: {c.get('evidence_passage')} "
            f"({c.get('source_title')} {c.get('source_version')} p.{c.get('source_pdf_page')})\n"
        )
    cards_joined = "\n".join(card_lines)

    extra = ""
    if applicability:
        extra += "\n=== APPLICABILITY REPORT ===\n"
        for r in applicability:
            extra += f"- {r['card_id']}: {r['status']} | {'; '.join(r['notes'])}\n"
    if questions:
        extra += "\n=== QUESTIONS TO ASK OR STATE AS UNKNOWN ===\n"
        for q in questions:
            extra += f"- {q}\n"

    return (
        "You are a careful clinical assistant. Use ONLY the retrieved protocol cards below.\n"
        "Do NOT use outside medical knowledge. Do NOT guess missing information.\n\n"
        "PATIENT CASE\n" + case_text + "\n\n"
        "=== RETRIEVED CARDS ===\n" + cards_joined + "\n"
        "=== END CARDS ===\n" + extra + "\n"
        "TASK: Produce four sections:\n"
        "1. PROBABLE DIAGNOSIS - likely disease(s), short reason, supporting symptoms. "
        "Say 'probable' not 'confirmed'.\n"
        "2. INVESTIGATIONS - test, purpose, timing/conditions stated in the cards.\n"
        "3. MEDICATION PLANNING - medicine, dose, route, frequency, duration, instructions, "
        "restrictions. If a dose is missing from the cards, say so explicitly.\n"
        "4. ADVICE - self-care, follow-up, warning signs, referral.\n\n"
        "RULES:\n"
        "- Beside every recommendation, cite the card ID and source page in brackets.\n"
        "- If a prerequisite or medication field is missing, write 'Unknown: <field>' and "
        "continue with what IS supported.\n"
        "- If an exclusion is triggered, do NOT recommend the excluded action; explain why.\n"
        "- Do not invent doses, pages, or cards.\n\n"
        "Answer:\n"
    )

# ---------- Run ----------
if st.button("Generate recommendations", type="primary"):
    if not os.path.exists("index/rag_index.pkl"):
        st.error("Index missing. Run `python build_index.py` first.")
        st.stop()

    if not complaints.strip():
        st.warning("Please enter at least the chief complaints / symptoms.")
        st.stop()

    if mode == "Baseline":
        t0 = time.time()
        cards = Retriever().query(case_text)
        prompt = build_prompt(cards)
        res = call_llm(prompt)
        elapsed = time.time() - t0
        applicability, questions = None, None
    else:
        t0 = time.time()
        cards, applicability, questions = ImprovedRetriever().query_with_report(case_text)
        prompt = build_prompt(cards, applicability, questions)
        res = call_llm(prompt)
        elapsed = time.time() - t0

    if res["backend"] == "no-key":
        st.error("GROQ_API_KEY is not set. Add it to .env and restart.")
        st.stop()

    st.success(f"Done in {elapsed:.2f}s - backend: {res['backend']}")
    if res.get("usage"):
        st.caption(f"Tokens: {res['usage']}")

    st.subheader("1. Patient information")
    st.text(case_text)

    st.subheader("2. Retrieved evidence")
    for c in cards:
        st.write(
            f"**{c['card_id']}** - {c['disease']} / {c['clinical_category']} "
            f"(score {c.get('_score', 0):.3f})"
        )

    if applicability:
        st.subheader("3. Applicability report (Improved mode only)")
        for r in applicability:
            st.write(f"- **{r['card_id']}** -> `{r['status']}` - {'; '.join(r['notes'])}")
        st.subheader("4. Targeted questions (Improved mode only)")
        for q in questions:
            st.write(f"- {q}")

    st.subheader("Recommendations")
    st.markdown(res["text"])

    # ---------- Save output (Bulletproof File/Directory check) ----------
    out_dir = Path("outputs") / mode.lower()
    
    # যদি আগে থেকে একই নামে ফাইল থেকে থাকে, তবে সেটা ডিলিট করে দিন
    if out_dir.exists() and not out_dir.is_dir():
        out_dir.unlink()
        
    out_dir.mkdir(parents=True, exist_ok=True)

    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    label = case_choice.replace(".json", "") if case_choice != "(manual input)" else "manual"
    outpath = out_dir / f"{label}_{ts}.json"

    payload = {
        "mode": mode,
        "case": case_text,
        "retrieved_cards": [c["card_id"] for c in cards],
        "applicability": applicability,
        "questions": questions,
        "output": res["text"],
        "backend": res["backend"],
        "usage": res.get("usage", {}),
        "elapsed_s": round(elapsed, 3),
    }

    with open(outpath, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)

    st.info(f"Saved: {outpath}")
    st.download_button(
        "Download output JSON",
        data=json.dumps(payload, indent=2, ensure_ascii=False),
        file_name=outpath.name,
    )