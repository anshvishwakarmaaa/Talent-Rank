# AI Resume Matching & Candidate Ranking System

Paste/upload a Job Description, upload 10+ resumes (PDF/DOCX), and get a ranked, explainable shortlist.

**Stack:** FastAPI · pypdf / python-docx · Sentence Transformers (`all-MiniLM-L6-v2`, TF-IDF fallback) · scikit-learn · vanilla JS dashboard (served by FastAPI, no build step).

## Run
```bash
python -m venv venv && source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
python scripts/make_samples.py                        # 12 synthetic resumes + sample JD -> ./samples
uvicorn app:app --reload --app-dir backend            # open http://127.0.0.1:8000
```
In the UI: paste `samples/sample_jd.txt`, select all `samples/resume_*` files, click **Analyze & Rank**.
First run downloads the ~90 MB embedding model; offline, the app automatically uses TF-IDF (the UI shows which engine ran).

## Architecture
```
frontend/index.html   JD input, resume upload, ranking table, candidate detail panel
backend/app.py        POST /api/analyze  (multipart: jd_text|jd_file + resumes[])
backend/resume_parser.py  text extraction, name/email/phone/education/experience/skills parsing, JD requirement extraction
backend/matcher.py    skill taxonomy, semantic similarity, scoring + explanations
scripts/make_samples.py   synthetic test data (no real personal info)
```
Pipeline: extract text → parse fields → extract JD requirements (required vs nice-to-have lines containing "preferred/plus/nice to have") → score each resume → sort → return JSON with full per-candidate analysis (the dashboard renders both table and detail view from it).

## Matching algorithm (how the % is calculated)
`Match % = 45·Skills + 30·Semantic + 20·Experience + 5·Education` (each component 0–1)

| Component | Weight | Method |
|---|---|---|
| Skills | 45% | Taxonomy match with aliases (`k8s`→kubernetes, `postgres`→postgresql). Required skill present = 1.0; **related** skill present (e.g. Flask for FastAPI, PyTorch for TensorFlow) = 0.5; else 0. Nice-to-have skills contribute 10% of this component. |
| Semantic | 30% | Each JD line is embedded; for each, the best-matching resume chunk (cosine) is taken; averaged and rescaled to 0–1. Captures relevant experience that exact keywords miss. |
| Experience | 20% | `min(candidate_years / required_years, 1)`. Years = max of explicit "N years" claims and merged date ranges (2019–Present). |
| Education | 5% | 1.0 if JD asks for no degree or resume lists one, else 0.3. |

Every result includes matched / partial / missing skills, the component breakdown, and plain-language reasons.

## Known limitations / next steps
- Skill taxonomy is hand-curated (~45 skills); extend `SKILLS` or swap in spaCy `EntityRuler`/ESCO.
- Layout-heavy or scanned PDFs need OCR. Results are not persisted (add PostgreSQL/MongoDB for history).
- Weights are heuristic; calibrate against recruiter-labelled data.
