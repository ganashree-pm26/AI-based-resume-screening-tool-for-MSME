"""
jd_pdf_parser.py 
FINAL CLEAN VERSION – PDF + DOCX, Skills, Responsibilities, Tech Stack, Domain, Embedding
"""

import os
import re
from typing import List, Dict, Any

import pdfplumber
from pdf2image import convert_from_path
import pytesseract
from docx import Document

import spacy
import yake
import numpy as np
from sentence_transformers import SentenceTransformer

# =====================================================================
#  LOAD MODELS (small + fast)
# =====================================================================

embed_model = SentenceTransformer("paraphrase-MiniLM-L3-v2")

try:
    nlp = spacy.load("en_core_web_sm")
except:
    nlp = spacy.blank("en")

yake_extractor = yake.KeywordExtractor(lan="en", n=2, top=20)

# =====================================================================
#  EXTRACT TEXT (PDF + DOCX)
# =====================================================================

def extract_text_from_pdf(path: str) -> str:
    text = ""
    try:
        with pdfplumber.open(path) as pdf:
            for page in pdf.pages:
                t = page.extract_text()
                if t:
                    text += t + "\n"
    except:
        pass

    # If real text was extracted, return it
    if len(text.strip()) > 200:
        return text

    # OCR fallback (for scanned PDFs)
    try:
        images = convert_from_path(path, dpi=300)
        ocr = ""
        for img in images:
            ocr += pytesseract.image_to_string(img) + "\n"
        return ocr
    except:
        return text


def extract_text_from_docx(path: str) -> str:
    doc = Document(path)
    lines = [p.text for p in doc.paragraphs if p.text.strip()]
    return "\n".join(lines)


def clean_text(t: str) -> str:
    t = t.replace("\n", " ").replace("\r", " ")
    t = re.sub(r"\s+", " ", t)
    return t.strip()


# =====================================================================
#  FIND LIKELY REQUIREMENT / SKILL SECTION
# =====================================================================

SECTION_HEADERS = [
    "requirements", "qualifications", "skills",
    "what we are looking for", "you will", "responsibilities"
]

def find_requirement_lines(raw: str) -> List[str]:
    lines = [l.strip() for l in raw.splitlines() if l.strip()]
    lowered = [l.lower() for l in lines]

    start = None
    for i, l in enumerate(lowered):
        if any(h in l for h in SECTION_HEADERS):
            start = i
            break

    if start is not None:
        block = []
        for j in range(start+1, len(lines)):
            l = lines[j].strip()

            if l == "":
                break
            if l.isupper() and len(l) < 50:
                break
            if any(h in l.lower() for h in SECTION_HEADERS):
                break

            block.append(l)

        # prefer bullets or short requirement style
        candidates = [l for l in block if re.match(r"^[\-\*\•]", l) or "," in l]
        return candidates or block

    # fallback: collect bullet lines
    bullets = [l for l in lines if re.match(r"^[\-\*\•]", l)]
    return bullets or lines[:200]


# =====================================================================
#  SKILL EXTRACTION (strict, no noise)
# =====================================================================

TECH_HINTS = [
    "python","java","javascript","c++","c#","react","angular","node","django","flask",
    "aws","azure","gcp","sql","nosql","docker","kubernetes","rest","api","android","ios",
    "html","css","swift","ui","ux","sdk","objective","tensorflow","pytorch"
]

IGNORE = {
    "experience","preferred","year","years","ability","knowledge",
    "team","work","candidate","company","including","role","intern"
}

TECH_TOKEN_RE = re.compile(
    r"\b([A-Za-z][A-Za-z0-9\+\#\.\-]{1,40}(?:\s[A-Za-z0-9\+\#\.\-]{1,40})?)\b"
)

def is_tech_like(tok: str) -> bool:
    t = tok.lower()
    return any(h in t for h in TECH_HINTS) or (tok.isupper() and len(tok) <= 5)


def extract_skills(lines: List[str]) -> List[str]:
    skills = []
    for line in lines:
        parts = re.split(r"[,/;]| and ", line, flags=re.I)
        for p in parts:
            toks = TECH_TOKEN_RE.findall(p)
            for t in toks:
                t2 = t.strip()
                if t2.lower() in IGNORE:
                    continue
                if len(t2.split()) > 6:
                    continue
                if is_tech_like(t2):
                    skills.append(t2)

    unique = []
    seen = set()
    for s in skills:
        k = s.lower()
        if k not in seen:
            seen.add(k)
            unique.append(s)

    return unique[:50]


# =====================================================================
#  RESPONSIBILITIES (corrected & reliable)
# =====================================================================

ACTION_VERBS = [
    "work","design","build","develop","maintain","lead","manage","implement",
    "coordinate","analyze","optimize","test","debug","collaborate","deploy",
    "monitor","research","create","integrate","drive","participate","support"
]

FILTER_OUT = [
    "visa is the world's leader",
    "we are not a bank",
    "we are a global team",
    "financial literacy",
    "digital commerce to millions",
]

def extract_responsibilities(raw: str) -> List[str]:
    sents = re.split(r"(?<=[\.\n])\s+", raw)
    res = []

    for s in sents:
        s0 = s.strip()
        if len(s0) < 25 or len(s0) > 220:
            continue

        low = s0.lower()

        if low.startswith("you will") or "you will" in low:
            res.append(s0)
            continue

        if any(v in low for v in ACTION_VERBS):
            res.append(s0)

    # remove marketing lines
    cleaned = []
    for r in res:
        if any(bad in r.lower() for bad in FILTER_OUT):
            continue
        cleaned.append(r)

    return list(dict.fromkeys(cleaned))


# =====================================================================
#  SENIORITY DETECTION
# =====================================================================

def extract_seniority(text: str) -> str:
    t = text.lower()
    if "intern" in t:
        return "Intern"
    if any(x in t for x in ["senior","sr.","lead","principal","staff"]):
        return "Senior"
    if "mid" in t or "intermediate" in t:
        return "Mid"
    if "junior" in t or "entry level" in t:
        return "Junior"
    return "Not Specified"


# =====================================================================
#  TECH STACK FROM SKILLS
# =====================================================================

TECH_FILTER = TECH_HINTS

def extract_tech_stack(skills: List[str]) -> List[str]:
    final = []
    for s in skills:
        if any(k in s.lower() for k in TECH_FILTER):
            final.append(s)
    return final or skills[:6]


# =====================================================================
#  DOMAIN DETECTION (embeddings)
# =====================================================================

DOMAIN_TEXTS = {
    "Finance": "fintech banking payments commerce transactions credit cards",
    "AI": "machine learning nlp deep learning neural networks",
    "Cloud": "aws azure gcp cloud devops kubernetes infrastructure",
    "Healthcare": "hospital healthcare medical clinical patient",
    "Security": "cyber security vulnerabilities encryption risk"
}

domain_vectors = embed_model.encode(list(DOMAIN_TEXTS.values()), convert_to_numpy=True)
domain_names = list(DOMAIN_TEXTS.keys())

def extract_domain(text: str) -> str:
    v = embed_model.encode([text], convert_to_numpy=True)[0]
    sims = np.dot(domain_vectors, v) / (np.linalg.norm(domain_vectors, axis=1)*np.linalg.norm(v) + 1e-9)
    idx = int(np.argmax(sims))
    return domain_names[idx] if sims[idx] > 0.42 else "General"


# =====================================================================
#  KEYWORDS + EMBEDDINGS
# =====================================================================

def extract_keywords(text: str) -> List[str]:
    kw = yake_extractor.extract_keywords(text)
    return [k for k, _ in kw][:12]

def get_embedding(text: str):
    return embed_model.encode([text])[0].tolist()


# =====================================================================
#  MAIN PARSE FUNCTION
# =====================================================================

def parse_job_description_pdf(path: str) -> Dict[str, Any]:
    path = os.path.abspath(path)

    if path.endswith(".pdf"):
        raw = extract_text_from_pdf(path)
    elif path.endswith(".docx"):
        raw = extract_text_from_docx(path)
    else:
        raise ValueError("Unsupported file type. Only PDF or DOCX accepted.")

    if not raw or len(raw.strip()) < 10:
        raise ValueError("File contains no readable text.")

    cleaned = clean_text(raw)

    req_lines = find_requirement_lines(raw)
    skills = extract_skills(req_lines)

    # fallback: scan short lines if needed
    if not skills:
        all_lines = [l.strip() for l in raw.splitlines() if l.strip() and len(l.strip()) < 140]
        skills = extract_skills(all_lines)

    responsibilities = extract_responsibilities(raw)
    seniority = extract_seniority(raw)
    domain = extract_domain(cleaned)
    tech_stack = extract_tech_stack(skills)
    keywords = extract_keywords(cleaned)
    embedding = get_embedding(cleaned)

    return {
        "cleaned_text": cleaned,
        "skills": skills,
        "responsibilities": responsibilities,
        "seniority_level": seniority,
        "tech_stack": tech_stack,
        "keywords": keywords,
        "domain": domain,
        "embedding": embedding
    }
