import os
from openai import OpenAI
from .models import LLMAnalysis, CommentaryRow

SYSTEM_PROMPT = """
You are a valuation-control commentary reviewer.

Assess whether a user's commentary explains the month-on-month valuation movement.
The most important criterion is move coverage.

Rules:
- Treat the absolute Difference as the total move to explain.
- Count only monetary amounts explicitly tied to an economic driver.
- Do not count an amount merely because it appears.
- Do not invent amounts, drivers, entities, or causal relationships.
- Do not double count amounts.
- If a residual/remaining amount is not quantified, it is not explained.
- Named entities are separate from economic drivers.
- Return structured evidence only. Do not calculate an overall score.
"""


def analyse_commentary(commentary: str, row: CommentaryRow) -> LLMAnalysis:
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key or api_key == "your_key_here":
        raise RuntimeError(
            "OPENAI_API_KEY is missing. Add your OpenAI API key to the .env file "
            "in the project root and restart uvicorn."
        )

    model = os.getenv("OPENAI_MODEL", "gpt-5.6-luna").strip()
    client = OpenAI(api_key=api_key)

    prompt = f"""
DATABASE CONTEXT
Area: {row.area}
Sector: {row.sector}
Segment: {row.segment}
Previous month value: {row.prev_month_value}
Current month value: {row.current_month_value}
Difference / total move: {row.difference}

USER COMMENTARY
{commentary}

Identify every explicitly quantified component that is causally attributed to an economic driver. explained_move_amount must be the sum of those components, without double counting. Then assess driver identification, attribution, specificity and clarity. Do not calculate a final score.
"""

    try:
        response = client.responses.parse(
            model=model,
            input=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            text_format=LLMAnalysis,
        )
    except Exception as exc:
        raise RuntimeError(
            f"OpenAI request failed using model '{model}': {type(exc).__name__}: {exc}"
        ) from exc

    if response.output_parsed is None:
        raise RuntimeError("OpenAI returned no structured analysis.")
    return response.output_parsed
