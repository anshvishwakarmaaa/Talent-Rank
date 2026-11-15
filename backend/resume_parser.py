"""Resume / JD text extraction and structured field parsing."""
import io, re, datetime
from pypdf import PdfReader
from docx import Document
from matcher import find_skills, extract_jd_terms, parse_extra

EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
PHONE = re.compile(r"(?:\+?\d{1,3}[\s-]?)?\(?\d{3,5}\)?[\s-]?\d{3,5}[\s-]?\d{3,5}")
DEGREE = re.compile(r"\b(ph\.?d|m\.?tech|mba|m\.?sc|mca|master(?:'s)?|b\.?tech|b\.?e|b\.?sc|bca|bachelor(?:'s)?)\b", re.I)
YEARS = re.compile(r"(\d{1,2})\s*\+?\s*(?:years?|yrs?)", re.I)
RANGE = re.compile(r"((?:19|20)\d{2})\s*(?:-|–|to)\s*((?:19|20)\d{2}|present|current|now)", re.I)

def extract_text(filename: str, data: bytes) -> str:
    name = filename.lower()
    if name.endswith(".pdf"):
        return "\n".join((p.extract_text() or "") for p in PdfReader(io.BytesIO(data)).pages)
    if name.endswith(".docx"):
        d = Document(io.BytesIO(data))
        parts = [p.text for p in d.paragraphs]
        for t in d.tables:
            parts += [c.text for r in t.rows for c in r.cells]
        return "\n".join(parts)
    if name.endswith(".txt"):
        return data.decode("utf-8", "ignore")
    raise ValueError(f"Unsupported file type: {filename}")

def years_of_experience(text: str) -> float:
    """Max of explicit 'N years' claims and the total of merged date ranges (e.g. 2019-2023)."""
    claims = [int(m) for m in YEARS.findall(text) if int(m) <= 40]
    now, spans = datetime.date.today().year, []
    for a, b in RANGE.findall(text):
        a = int(a); b = now if b.lower() in ("present", "current", "now") else int(b)
        if 0 <= b - a <= 40: spans.append((a, b))
    merged = []
    for a, b in sorted(spans):
        if merged and a <= merged[-1][1]: merged[-1][1] = max(merged[-1][1], b)
        else: merged.append([a, b])
    return float(max(max(claims, default=0), sum(b - a for a, b in merged)))

def parse_resume(filename: str, text: str) -> dict:
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    name = next((l for l in lines[:6] if 1 < len(l.split()) <= 4 and re.fullmatch(r"[A-Za-z .'-]+", l)),
                filename.rsplit(".", 1)[0])
    em = EMAIL.search(text)
    phone = None
    for m in PHONE.finditer(text):
        if 10 <= len(re.sub(r"\D", "", m.group())) <= 13: phone = m.group().strip(); break
    degrees = sorted({d.strip() for d in DEGREE.findall(text)}, key=str.lower)
    if name == filename.rsplit(".", 1)[0] and em:
        name = re.sub(r"[._\d]+", " ", em.group().split("@")[0]).title().strip()
    return {"file": filename, "name": name, "email": em.group() if em else None, "phone": phone,
            "education": degrees, "experience_years": years_of_experience(text),
            "skills": sorted(find_skills(text)), "text": text}

def parse_jd(text: str, extra: str = "") -> dict:
    required, nice = set(), set()
    for line in text.splitlines():
        sk = find_skills(line)
        if re.search(r"nice to have|preferred|bonus|plus\b|good to have|optional", line, re.I): nice |= sk
        else: required |= sk
    for line in text.splitlines():
        t = extract_jd_terms(line)
        if re.search(r"nice to have|preferred|bonus|plus\b|good to have|optional", line, re.I): nice |= t
        else: required |= t
    required |= parse_extra(extra)
    nice -= required
    yrs = [int(m) for m in YEARS.findall(text) if int(m) <= 30]
    edu = sorted({d.strip() for d in DEGREE.findall(text)}, key=str.lower)
    return {"required_skills": sorted(required), "nice_to_have": sorted(nice),
            "min_experience_years": float(min(yrs)) if yrs else 0.0, "education": edu}
