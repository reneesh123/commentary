let rows = [];
let filtered = [];
let page = 1;
const pageSize = 20;
const results = new Map();

const $ = (id) => document.getElementById(id);
const esc = (v) => String(v ?? "").replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#039;"}[c]));

function gradeClass(g){ return g === "Good" ? "good" : g === "Average" ? "average" : "needs"; }

function render(){
  const q = $("search").value.toLowerCase().trim();
  const gf = $("gradeFilter").value;
  filtered = rows.filter(r => {
    const text = [r.record_id,r.area,r.sector,r.segment,r.commentary].join(" ").toLowerCase();
    const result = results.get(r.record_id);
    return text.includes(q) && (!gf || (result && result.grade === gf));
  });
  const pages = Math.max(1, Math.ceil(filtered.length / pageSize));
  if(page > pages) page = pages;
  const visible = filtered.slice((page-1)*pageSize, page*pageSize);
  $("tableBody").innerHTML = visible.map(rowHtml).join("");
  $("pageInfo").textContent = `Page ${page} of ${pages} · ${filtered.length} rows`;
  $("rowCount").textContent = `${rows.length} commentaries`;
}

function rowHtml(r){
  const result = results.get(r.record_id);
  const moveClass = r.difference >= 0 ? "move-positive" : "move-negative";
  let feedback = '<div class="empty-feedback">Click Evaluate with AI.</div>';
  let details = '<div class="empty-feedback">Score breakdown and improvement suggestions will appear here.</div>';
  if(result){
    if(result.error){
      feedback = `<div class="error"><strong>AI evaluation failed</strong><br>${esc(result.error)}</div>`;
      details = `<div class="details-title">Next step</div><div class="suggestion">${esc(result.error)}<br><br>Check the FastAPI terminal for the full error.</div>`;
    } else { feedback = scoreSummaryHtml(result); details = scoreDetailsHtml(result); }
  }
  return `<tr id="row-${r.record_id}">
    <td><strong>${r.record_id}</strong></td>
    <td class="context"><strong>${esc(r.area)}</strong><span>${esc(r.sector)}</span><span>${esc(r.segment)}</span></td>
    <td class="number">${Number(r.prev_month_value).toFixed(1)}</td>
    <td class="number">${Number(r.current_month_value).toFixed(1)}</td>
    <td class="number ${moveClass}">${Number(r.difference).toFixed(1)}</td>
    <td class="commentary-col"><textarea class="commentary" id="commentary-${r.record_id}">${esc(r.commentary)}</textarea><button type="button" class="eval-btn" data-record-id="${r.record_id}">Evaluate with AI</button></td>
    <td class="feedback">${feedback}</td>
    <td class="score-details">${details}</td>
  </tr>`;
}

function scoreSummaryHtml(result){
  const coverage = result.dimensions.find(x => x.name === "Explains >80% of move");
  return `<div class="result-header"><span class="score">${result.total_score}</span><span class="grade ${gradeClass(result.grade)}">${esc(result.grade)}</span></div>
    <div class="coverage"><strong>${coverage ? `${coverage.score}/50 — ${coverage.status === "pass" ? "80% move coverage achieved" : "80% move coverage not achieved"}` : "Move coverage"}</strong><div class="small">${esc(coverage?.evidence || "")}</div></div>
    <div class="mini-summary">${result.dimensions.map(d => `<div class="mini-dim"><span>${esc(d.name)}</span><b>${d.score}/${d.weight}</b></div>`).join("")}</div>`;
}

function scoreDetailsHtml(result){
  const weak = result.dimensions.filter(d => d.score < d.weight);
  const suggestions = weak.filter(d => d.improvement).map(d => `<div class="suggestion"><div class="suggestion-title">${esc(d.name)} — ${d.score}/${d.weight}</div><div>${esc(d.improvement)}</div></div>`).join("");
  return `<div class="details-title">Why this score?</div>${result.dimensions.map(d => `<div class="detail-row"><div class="detail-head"><span>${esc(d.name)}</span><b>${d.score}/${d.weight}</b></div><div class="detail-evidence">${esc(d.evidence)}</div></div>`).join("")}
    <div class="details-title improve-heading">How to improve</div>${suggestions || `<div class="all-good">No scoring gaps identified.</div>`}
    ${result.llm_analysis?.suggested_improvement ? `<div class="suggestion"><div class="suggestion-title">AI overall suggestion</div><div>${esc(result.llm_analysis.suggested_improvement)}</div></div>` : ""}`;
}

async function evaluateRow(id, button){
  const row = rows.find(x => x.record_id === id);
  const textarea = $(`commentary-${id}`);
  if(!row || !textarea){ alert(`Could not find row ${id}.`); return; }
  const commentary = textarea.value.trim();
  if(!commentary){ alert("Please enter commentary before evaluating."); return; }

  button.disabled = true;
  button.textContent = "Connecting to AI...";
  button.classList.add("busy");
  const feedbackCell = document.querySelector(`#row-${id} .feedback`);
  feedbackCell.innerHTML = '<div class="loading-ai"><strong>AI evaluation in progress...</strong><br>Extracting drivers, quantified amounts and move coverage.</div>';

  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 90000);
  try{
    const res = await fetch("/api/evaluate", {
      method:"POST",
      headers:{"Content-Type":"application/json"},
      body:JSON.stringify({record_id:id, commentary}),
      signal:controller.signal
    });
    const raw = await res.text();
    let data;
    try { data = JSON.parse(raw); } catch { throw new Error(`Server returned non-JSON response (HTTP ${res.status}).`); }
    if(!res.ok) throw new Error(data.detail || `Evaluation failed (HTTP ${res.status})`);
    results.set(id,data);
    button.disabled = false;
    button.textContent = "Re-evaluate with AI";
    render();
  }catch(e){
    const msg = e.name === "AbortError" ? "The AI request took longer than 90 seconds and was cancelled." : e.message;
    results.set(id,{error:msg});
    render();
    alert(`AI evaluation failed for row ${id}:\n\n${msg}`);
  }finally{ clearTimeout(timeout); }
}

async function load(){
  $("tableBody").innerHTML = '<tr><td colspan="8" class="loading-cell">Loading commentaries...</td></tr>';
  try{
    const res = await fetch("/api/commentaries?ts=" + Date.now(), {cache:"no-store"});
    const raw = await res.text();
    let data; try { data = JSON.parse(raw); } catch { throw new Error(`Invalid server response (HTTP ${res.status}).`); }
    if(!res.ok || !Array.isArray(data)) throw new Error(data.detail || `Could not load commentaries (HTTP ${res.status}).`);
    rows = data; filtered = rows; page = 1; render();
  }catch(e){
    rows=[]; filtered=[]; $("rowCount").textContent="Unable to load";
    $("tableBody").innerHTML=`<tr><td colspan="8"><div class="error"><strong>Could not load commentaries</strong><br>${esc(e.message)}</div></td></tr>`;
  }
}

window.addEventListener("DOMContentLoaded", () => {
  $("tableBody").addEventListener("click", (event) => {
    const button = event.target.closest(".eval-btn");
    if(!button) return;
    event.preventDefault();
    const id = Number(button.dataset.recordId);
    evaluateRow(id, button);
  });
  $("search").addEventListener("input",()=>{page=1;render()});
  $("gradeFilter").addEventListener("change",()=>{page=1;render()});
  $("prevPage").addEventListener("click",()=>{if(page>1){page--;render()}});
  $("nextPage").addEventListener("click",()=>{if(page<Math.ceil(filtered.length/pageSize)){page++;render()}});
  $("reload").addEventListener("click",load);
  load();
});
