"""Skill taxonomy + scoring.
Final score (0-100) = 45% skill coverage + 30% semantic similarity + 20% experience fit + 5% education."""
import os, re
import numpy as np

SKILLS = {
 "python": ["python"], "java": ["java"], "javascript": ["javascript", "js", "node.js", "nodejs"],
 "typescript": ["typescript"], "react": ["react", "react.js", "reactjs"], "angular": ["angular"],
 "fastapi": ["fastapi"], "django": ["django"], "flask": ["flask"],
 "spring boot": ["spring boot", "springboot", "spring"], "sql": ["sql", "mysql", "postgresql", "postgres", "sqlite"],
 "postgresql": ["postgresql", "postgres"], "mongodb": ["mongodb", "mongo"], "redis": ["redis"],
 "docker": ["docker"], "kubernetes": ["kubernetes", "k8s"], "aws": ["aws", "amazon web services"],
 "azure": ["azure"], "gcp": ["gcp", "google cloud"], "git": ["git", "github", "gitlab"],
 "rest api": ["rest api", "rest apis", "restful"], "microservices": ["microservices", "microservice"],
 "ci/cd": ["ci/cd", "jenkins", "github actions"], "linux": ["linux"],
 "machine learning": ["machine learning", "ml"], "deep learning": ["deep learning", "neural networks"],
 "nlp": ["nlp", "natural language processing"], "pytorch": ["pytorch"], "tensorflow": ["tensorflow", "keras"],
 "scikit-learn": ["scikit-learn", "sklearn"], "pandas": ["pandas"], "numpy": ["numpy"],
 "spacy": ["spacy"], "transformers": ["transformers", "hugging face", "huggingface", "bert"],
 "html": ["html", "html5"], "css": ["css", "css3", "tailwind"], "tableau": ["tableau"], "power bi": ["power bi", "powerbi"],
 "data analysis": ["data analysis", "data analytics"], "agile": ["agile", "scrum"],
}
# Related skills earn half credit (explainable stand-in for semantic skill matching)
RELATED = {
 "fastapi": ["flask", "django"], "flask": ["fastapi", "django"], "django": ["flask", "fastapi"],
 "react": ["angular", "javascript", "typescript"], "angular": ["react"], "postgresql": ["sql", "mongodb"],
 "mongodb": ["postgresql", "sql"], "sql": ["postgresql"], "pytorch": ["tensorflow"], "tensorflow": ["pytorch"],
 "spacy": ["nlp", "transformers"], "transformers": ["nlp", "pytorch"], "kubernetes": ["docker"],
 "aws": ["azure", "gcp"], "azure": ["aws", "gcp"], "gcp": ["aws", "azure"], "spring boot": ["java"],
 "machine learning": ["scikit-learn", "deep learning"], "nlp": ["transformers", "spacy"],
}
_PATTERNS = {s: re.compile(r"(?<![\w+#.])(?:%s)(?![\w+#])" % "|".join(re.escape(a) for a in al), re.I)
             for s, al in SKILLS.items()}

def find_skills(text: str) -> set:
    return {s for s, p in _PATTERNS.items() if p.search(text)}

# ---------- dynamic (non-taxonomy) skill extraction from any JD ----------
_CTX = re.compile(r"skills?|experience|proficien|knowledge|familiar|expertise|tools?|technolog|stack|framework|librar|languages|platforms?|requirements?|must have|hands-on", re.I)
_LEAD = re.compile(r"^(?:strong|hands-on|good|solid|working|proven|deep|basic|advanced|excellent|experience|knowledge|proficiency|familiarity|expertise|understanding|of|with|in|using|on|and|or|the|a|an|skills?|tools?|etc\.?)\s+", re.I)
_STOP = {"years","year","team","teams","communication","ability","work","working","degree","bachelor","master","preferred","required","plus","nice","have","we","you","will","strong","skills","experience","knowledge","related","field","candidates","candidate","role","responsibilities","requirements","qualifications","company","looking","engineer","developer","etc"}

def extract_jd_terms(text: str) -> set:
    """Generic skill/tool phrases (1-3 words) from requirement-style lines; works for any domain."""
    out = set()
    for line in text.splitlines():
        if not _CTX.search(line): continue
        seg = line.split(":", 1)[1] if ":" in line else line
        for part in re.split(r",|;|/|\||\(|\)|\band\b|\bor\b|\.\s", seg):
            p = part.strip(" .-•*\t")
            for _ in range(4): p = _LEAD.sub("", p)
            w = p.split()
            if not (1 <= len(w) <= 3) or p.lower() in _STOP or any(x.lower() in _STOP for x in w): continue
            if (any(c.isupper() for c in p) or any(c in p for c in ".+#")) and not find_skills(p) and len(p) > 1:
                out.add(p.lower())
    return out

def parse_extra(s: str) -> set:
    return {t.strip().lower() for t in re.split(r"[,\n;]", s or "") if t.strip()}

def present(skill: str, text: str) -> bool:
    return bool(re.search(r"(?<![\w+#])%s(?![\w+#])" % re.escape(skill), text, re.I))

# ---------- semantic similarity ----------
_model, _fallback = None, False
def _get_model():
    global _model, _fallback
    if os.environ.get("USE_TFIDF") == "1": _fallback = True   # skip model download entirely
    if _model is None and not _fallback:
        try:
            from sentence_transformers import SentenceTransformer
            _model = SentenceTransformer("all-MiniLM-L6-v2")
        except Exception:
            _fallback = True
    return _model

def engine_name():
    _get_model()
    return "tfidf-fallback" if _fallback else "sentence-transformers/all-MiniLM-L6-v2"

def _chunks(text):
    parts = [p.strip() for p in re.split(r"\n+|(?<=[.!?])\s+", text) if len(p.strip()) > 25]
    return parts or [text[:400]]

def semantic_similarity(jd_text: str, resume_text: str) -> float:
    """For each JD line take the best-matching resume chunk, then average. Normalised to 0-1."""
    jd_c, rs_c = _chunks(jd_text), _chunks(resume_text)
    model = _get_model()
    if model is not None:
        a = model.encode(jd_c, normalize_embeddings=True); b = model.encode(rs_c, normalize_embeddings=True)
        raw = float((a @ b.T).max(axis=1).mean()); lo, hi = 0.15, 0.65
    else:
        from sklearn.feature_extraction.text import TfidfVectorizer
        v = TfidfVectorizer(stop_words="english", ngram_range=(1, 2)).fit(jd_c + rs_c)
        raw = float((v.transform(jd_c) @ v.transform(rs_c).T).toarray().max(axis=1).mean()); lo, hi = 0.0, 0.4
    return float(np.clip((raw - lo) / (hi - lo), 0, 1))

# ---------- scoring ----------
def score_candidate(jd: dict, jd_text: str, cand: dict) -> dict:
    have = set(cand["skills"])
    req, nice = jd["required_skills"], jd["nice_to_have"]
    matched, partial, missing = [], {}, []
    for s in req:
        if s in have or (s not in SKILLS and present(s, cand["text"])): matched.append(s)
        else:
            rel = [r for r in RELATED.get(s, []) if r in have]
            if rel: partial[s] = rel
            else: missing.append(s)
    nice_matched = [s for s in nice if s in have]
    skill_score = (len(matched) + 0.5 * len(partial)) / len(req) if req else 0.5
    if nice: skill_score = 0.9 * skill_score + 0.1 * len(nice_matched) / len(nice)
    sem = semantic_similarity(jd_text, cand["text"])
    need, got = jd["min_experience_years"], cand["experience_years"]
    exp_score = 1.0 if need == 0 else min(got / need, 1.0)
    edu_score = 1.0 if (not jd["education"] or cand["education"]) else 0.3
    total = 100 * (0.45 * skill_score + 0.30 * sem + 0.20 * exp_score + 0.05 * edu_score)
    reasons = [
        f"Skills: {len(matched)}/{len(req)} required matched" + (f", {len(partial)} partially via related skills" if partial else "") + f" → {skill_score*100:.0f}% (weight 45%).",
        f"Semantic similarity of resume content to JD: {sem*100:.0f}% (weight 30%).",
        (f"Experience: {got:g} yrs vs {need:g} required → {exp_score*100:.0f}% (weight 20%)." if need
         else f"Experience: {got:g} yrs; JD states no minimum (full credit)."),
        "Education requirement met." if edu_score == 1 else "No matching degree found (−3.5 pts).",
    ]
    if missing: reasons.append("Missing required skills: " + ", ".join(missing) + ".")
    return {"score": round(total, 1), "matched_skills": matched, "partial_skills": partial,
            "missing_skills": missing, "nice_matched": nice_matched,
            "breakdown": {"skills": round(skill_score*100), "semantic": round(sem*100),
                          "experience": round(exp_score*100), "education": round(edu_score*100)},
            "experience_comparison": {"required": need, "candidate": got}, "reasons": reasons}
