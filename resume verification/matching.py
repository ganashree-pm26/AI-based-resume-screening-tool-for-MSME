# matching.py
import numpy as np
from numpy.linalg import norm
from jd_pdf_parser import embed_model

def cosine(a, b):
    a = np.array(a, dtype=float)
    b = np.array(b, dtype=float)
    return float(np.dot(a, b) / (norm(a) * norm(b) + 1e-9))

def skill_overlap_score(jd_skills, res_skills):
    jd = set(s.lower() for s in jd_skills)
    rs = set(s.lower() for s in res_skills)
    if not jd:
        return 0.0, [], list(rs)
    matched = sorted(list(jd & rs))
    missing = sorted(list(jd - rs))
    # recall and precision
    recall = len(matched) / len(jd) if jd else 0.0
    precision = len(matched) / (len(rs) or 1)
    score = 0.6 * recall + 0.4 * precision
    return score, matched, missing

def responsibilities_similarity(jd_resps, res_resps):
    if not jd_resps or not res_resps:
        return 0.0
    jd_text = " ".join(jd_resps)
    res_text = " ".join(res_resps)
    v1 = embed_model.encode([jd_text])[0]
    v2 = embed_model.encode([res_text])[0]
    return cosine(v1, v2)

def compute_match_for_resume(resume_obj: dict, jd_obj: dict, source_url: str = None):
    """
    resume_obj: parsed resume dict (from parse_resume_file)
    jd_obj: parsed JD dict
    returns: dict with final_score, breakdown, missing, matched, resume fields, source_url
    """
    s_skill, matched, missing = skill_overlap_score(jd_obj.get("skills", []), resume_obj.get("skills", []))
    s_embed = 0.0
    try:
        s_embed = cosine(jd_obj.get("embedding", []), resume_obj.get("embedding", []))
    except Exception:
        s_embed = 0.0
    s_resp = responsibilities_similarity(jd_obj.get("responsibilities", []), resume_obj.get("responsibilities", []))

    # Weighted sum — you can tune
    weights = {"skill": 0.55, "embed": 0.30, "resp": 0.15}
    final = weights["skill"] * s_skill + weights["embed"] * s_embed + weights["resp"] * s_resp

    result = {
        "candidate_name": resume_obj.get("candidate_name", ""),
        "path": resume_obj.get("path", ""),
        "skills": resume_obj.get("skills", []),
        "matched_skills": matched,
        "missing_skills": missing,
        "skill_score": s_skill,
        "embed_score": s_embed,
        "resp_score": s_resp,
        "final_score": final,
        "source_url": source_url,
        "cleaned_text": resume_obj.get("cleaned_text", "")
    }
    return result
