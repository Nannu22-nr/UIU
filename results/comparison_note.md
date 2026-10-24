# Comparison note (max one page)

## Weakness identified in baseline
Baseline retrieves top-k cards and sends them to the Groq model with a prompt that asks for citations and honest missing-information handling. However, it does not check whether the retrieved cards' prerequisites and exclusions actually apply to the case. As a result, excluded cards (e.g. NSAID advice) can appear in the retrieved set and be echoed, and missing fields are left to the model's discretion.

## Improvement and why it should help
One change: a rule-based applicability check plus targeted missing-information question selection, applied before the same Groq call with the same prompt template plus an applicability report block. It makes exclusions explicit and converts silent gaps into explicit questions without changing model, corpus, retrieval, or cases.

## Falsification criterion (stated before running)
If Improved mode does not increase the "missing info handled without guessing" pass count by at least 1 out of 6 cases versus Baseline, the improvement is not supported.

## Results summary
- Baseline: __/24 checks passed.
- Improved: __/24 checks passed.
- Change: __ checks.
- Time cost: baseline avg __ s; improved avg __ s (applicability check adds __ s).
- Token cost: baseline avg __ tokens; improved avg __ tokens.

## One failure / limitation (honest)
Case: __ | Mode: __ | Check: __
What happened: __.
Likely cause: __.
Alternative explanation (model variability / retrieval variance): __.
Next test: __.

## If all checks passed
Hardest case: C5 (ambiguous). Remaining untested limitation: real-world free-text with typos/abbreviations; multi-disease comorbidity not covered by these six cases.

## Cost of the improvement
The applicability check is rule-based and runs locally (~0.01-0.05 s, no extra Groq call). Added prompt tokens: ~200-400 per case. An LLM-based applicability check would double cost and latency; we did not do that.

## Honesty
Six self-authored cases. Not clinical validation. AI assistance used for code scaffolding; all cited evidence verified against the supplied PDFs.