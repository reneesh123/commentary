import time
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
import os

from .models import EvaluationRequest
from .data_provider import load_commentaries, get_commentary
from .scoring import score_analysis, total_score, grade

BASE=Path(__file__).resolve().parent.parent
load_dotenv(BASE/".env")
FRONTEND=BASE/"frontend"

app=FastAPI(title="Valuation Commentary Reviewer", version="2.0")

@app.get("/")
def home():
    return FileResponse(FRONTEND/"index.html")

@app.get("/api/health")
def health():
    return {"status":"ok"}

@app.get("/api/commentaries")
def commentaries():
    try:
        rows = load_commentaries()
        return [x.model_dump() for x in rows]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not load commentaries: {type(e).__name__}: {e}")

@app.get("/api/config")
def config():
    key = os.getenv("OPENAI_API_KEY", "").strip()
    return {"openai_key_configured": bool(key and key != "your_key_here"), "model": os.getenv("OPENAI_MODEL", "gpt-5.6-luna")}

@app.get("/api/debug")
def debug():
    rows = load_commentaries()
    return {"status":"ok", "count":len(rows), "first_record":rows[0].model_dump() if rows else None}

@app.get("/api/evaluate-ping")
def evaluate_ping():
    return {"status":"ready", "message":"Evaluation endpoint is reachable."}

@app.post("/api/evaluate")
def evaluate(req: EvaluationRequest):
    started=time.perf_counter()
    try:
        from .llm import analyse_commentary
        row=get_commentary(req.record_id)
        analysis=analyse_commentary(req.commentary, row)
        dims=score_analysis(analysis,row)
        score=total_score(dims)
        return {
            "record_id": row.record_id,
            "commentary": req.commentary,
            "dimensions":[x.model_dump() for x in dims],
            "total_score":score,
            "grade":grade(score),
            "llm_analysis":analysis.model_dump(),
            "processing_ms":round((time.perf_counter()-started)*1000)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

app.mount("/static",StaticFiles(directory=FRONTEND),name="static")
