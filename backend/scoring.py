from .models import LLMAnalysis, CommentaryRow, DimensionScore

def status(score, weight):
    if score >= weight * .85: return "pass"
    if score >= weight * .50: return "partial"
    return "fail"

def score_analysis(a: LLMAnalysis, row: CommentaryRow):
    total_move = abs(row.difference)
    if total_move == 0:
        coverage = 50.0
        cov_ev = "The database movement is zero; coverage is treated as satisfied."
    else:
        explained = max(0.0, min(abs(a.explained_move_amount), total_move))
        coverage_pct = explained / total_move
        coverage = 50.0 if coverage_pct >= .80 else 50.0 * coverage_pct
        cov_ev = (
            f"Explained quantified movement: {explained:.2f} of {total_move:.2f} "
            f"({coverage_pct:.1%}). The 80% threshold is {'met' if coverage_pct >= .80 else 'not met'}."
        )

    dims = [DimensionScore(
        name="Explains >80% of move", weight=50, score=round(coverage,1),
        status="pass" if coverage >= 50 else ("partial" if coverage >= 25 else "fail"),
        evidence=cov_ev,
        improvement="" if coverage >= 50 else "Explain additional quantified components of the total valuation move."
    )]

    # Remaining 50 points: quantification 10, driver 15, attribution 10, specificity 10, clarity 5
    q = 10.0 if a.amounts else 0.0
    dims.append(DimensionScore(
        name="Quantification", weight=10, score=q, status=status(q,10),
        evidence=f"{len(a.amounts)} amount(s) extracted.",
        improvement="" if q == 10 else "Quantify material components of the move."
    ))

    dcount=len(a.drivers)
    d = 15.0 if dcount >= 2 else (10.0 if dcount == 1 else 0.0)
    dims.append(DimensionScore(
        name="Driver identification", weight=15, score=d, status=status(d,15),
        evidence=f"{dcount} economic driver(s) identified.",
        improvement="" if d == 15 else "Identify the material economic driver(s)."
    ))

    attributed=sum(1 for x in a.drivers if x.attribution.strip())
    at=10.0 if a.drivers and attributed == len(a.drivers) else (5.0 if attributed else 0.0)
    dims.append(DimensionScore(
        name="Attribution", weight=10, score=at, status=status(at,10),
        evidence=f"{attributed} of {dcount} driver(s) has explicit causal attribution.",
        improvement="" if at == 10 else "Make the causal link between each driver and the valuation movement explicit."
    ))

    specificity=10.0 if any(x.entities for x in a.drivers) and all(x.evidence.strip() for x in a.drivers) else (6.0 if a.drivers else 0.0)
    dims.append(DimensionScore(
        name="Specificity", weight=10, score=specificity, status=status(specificity,10),
        evidence=a.specificity_assessment or "Specificity evidence returned by the model.",
        improvement="" if specificity == 10 else "Add concrete names, books, trades, sectors, curves or parameters where relevant."
    ))

    clarity_txt=(a.clarity_assessment or "").lower()
    clarity=5.0 if any(k in clarity_txt for k in ["clear","concise","well structured","easy to understand"]) else (3.0 if clarity_txt else 0.0)
    dims.append(DimensionScore(
        name="Clarity", weight=5, score=clarity, status=status(clarity,5),
        evidence=a.clarity_assessment or "No clarity assessment returned.",
        improvement="" if clarity == 5 else "Use concise wording and make the causal explanation easy to follow."
    ))
    return dims

def total_score(dims):
    return round(sum(d.score for d in dims), 1)

def grade(score):
    if score >= 85: return "Good"
    if score >= 65: return "Average"
    return "Needs work"
