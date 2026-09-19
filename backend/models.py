from typing import List, Optional, Literal
from pydantic import BaseModel

class CommentaryRow(BaseModel):
    record_id: int
    area: str
    sector: str
    segment: str
    prev_month_value: float
    current_month_value: float
    difference: float
    commentary: str

class ExtractedAmount(BaseModel):
    amount: float
    direction: Literal["positive", "negative", "neutral", "unknown"] = "unknown"
    evidence: str = ""

class LLMDriver(BaseModel):
    driver: str
    amount: Optional[float] = None
    direction: Literal["positive", "negative", "neutral", "unknown"] = "unknown"
    entities: List[str] = []
    attribution: str = ""
    evidence: str = ""

class LLMAnalysis(BaseModel):
    explained_move_amount: float
    explained_move_evidence: str
    coverage_assessment: str
    amounts: List[ExtractedAmount]
    drivers: List[LLMDriver]
    clarity_assessment: str
    specificity_assessment: str
    missing_information: List[str]
    suggested_improvement: str

class DimensionScore(BaseModel):
    name: str
    weight: int
    score: float
    status: Literal["pass", "partial", "fail"]
    evidence: str
    improvement: str = ""

class EvaluationRequest(BaseModel):
    record_id: int
    commentary: str

class EvaluationResponse(BaseModel):
    record_id: int
    commentary: str
    dimensions: List[DimensionScore]
    total_score: float
    grade: Literal["Good", "Average", "Needs work"]
    llm_analysis: LLMAnalysis
    processing_ms: int
