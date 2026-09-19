# Commentary Reviewer — 500-row FastAPI + OpenAI version

This version loads the supplied `valuation-commentary-sample-500.xlsx` into
`data/commentaries.json` and presents the 500 commentaries in a proper web
table.

Each row contains:
- Record ID
- Area
- Sector
- Segment
- Previous month value
- Current month value
- Difference
- Editable commentary
- AI feedback in the same row

## Scoring framework

The key requirement is that **50% of the total score is whether the
commentary explains at least 80% of the absolute month-on-month valuation
move**.

Weights:
- Explains >80% of move: 50
- Driver identification: 15
- Quantification: 10
- Attribution: 10
- Specificity: 10
- Clarity: 5
- Total: 100

For move coverage, the LLM is instructed to extract only explicitly
quantified, causally attributed amounts. Python then compares that explained
amount against the database Difference.

Example:
- Database move = -13.9
- Commentary explains $7.4m + $6.5m = $13.9m
- Coverage = 100%
- Coverage score = 50/50

If the commentary explains $8m of a $13.9m move:
- Coverage = 57.6%
- Coverage score = 28.8/50

The LLM does NOT calculate the final score.

## Run

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt
Copy-Item .env.example .env
notepad .env
uvicorn backend.main:app --reload
```

Open:
http://127.0.0.1:8000

The expected-assessments sheet is stored separately as
`data/expected_assessments.json` for future benchmarking; it is not shown to
the end user.

## Next integration

The current 500-row file is static JSON so the UI works immediately.
`backend/data_provider.py` is the replacement point for your MDX database.
The UI can then load the live Area/Sector/Segment/values/commentary inventory
from the database rather than from the sample file.

## UI scoring details
Each evaluated row now has separate columns for the AI score and a detailed score breakdown with dimension-level evidence and targeted suggestions for improving the score. The 50-point move-coverage criterion remains the largest component.


## Troubleshooting v8
Open http://127.0.0.1:8000/api/evaluate-ping. It should return status ready.
