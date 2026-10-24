# llm/client.py — connects the prototype to an existing API model (Groq).
import os
from config import GROQ_API_KEY, GROQ_MODEL, LLM_TEMPERATURE, LLM_MAX_TOKENS

def call_llm(prompt: str) -> dict:
    """Returns {'text': str, 'backend': str, 'usage': dict}."""
    if not GROQ_API_KEY or GROQ_API_KEY.startswith("your_"):
        return {"text": "[ERROR] GROQ_API_KEY not set in .env", "backend": "no-key", "usage": {}}

    from groq import Groq
    client = Groq(api_key=GROQ_API_KEY)
    resp = client.chat.completions.create(
        model=GROQ_MODEL,
        temperature=LLM_TEMPERATURE,
        max_tokens=LLM_MAX_TOKENS,
        messages=[
            {"role": "system",
             "content": "You are a careful clinical protocol assistant. Use only the retrieved cards."},
            {"role": "user", "content": prompt},
        ],
    )
    text = resp.choices[0].message.content
    usage = {}
    try:
        u = resp.usage
        usage = {
            "prompt_tokens": u.prompt_tokens,
            "completion_tokens": u.completion_tokens,
            "total_tokens": u.total_tokens,
        }
    except Exception:
        pass
    return {"text": text, "backend": f"groq:{GROQ_MODEL}", "usage": usage}