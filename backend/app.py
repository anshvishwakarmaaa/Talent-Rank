import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from fastapi import FastAPI, File, Form, UploadFile, HTTPException, Depends
from fastapi.responses import FileResponse
from resume_parser import extract_text, parse_resume, parse_jd
from matcher import score_candidate, engine_name
from auth import router as auth_router, current_user

app = FastAPI(title="AI Resume Matcher")
app.include_router(auth_router)
FRONTEND = os.path.join(os.path.dirname(__file__), "..", "frontend")

@app.get("/")
def index(): return FileResponse(os.path.join(FRONTEND, "index.html"))

@app.post("/api/analyze")
async def analyze(jd_text: str = Form(""), extra_skills: str = Form(""), jd_file: UploadFile | None = File(None),
                  resumes: list[UploadFile] = File(...), user=Depends(current_user)):
    if jd_file and jd_file.filename:
        jd_text = extract_text(jd_file.filename, await jd_file.read())
    if not jd_text.strip(): raise HTTPException(400, "Provide a job description (paste or upload).")
    jd = parse_jd(jd_text, extra_skills)
    if not jd["required_skills"]: raise HTTPException(400, "No recognisable skills found in the JD.")
    results, errors = [], []
    for f in resumes:
        try:
            cand = parse_resume(f.filename, extract_text(f.filename, await f.read()))
            res = score_candidate(jd, jd_text, cand)
            cand.pop("text"); results.append({**cand, **res})
        except Exception as e:
            errors.append({"file": f.filename, "error": str(e)})
    results.sort(key=lambda r: r["score"], reverse=True)
    for i, r in enumerate(results, 1): r["rank"] = i
    return {"jd": jd, "engine": engine_name(), "candidates": results, "errors": errors}
