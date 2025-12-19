# resume_parser.py
from jd_pdf_parser import parse_job_description_pdf

def parse_resume_file(path: str):
    """
    Returns a standardized resume dict with keys:
    - candidate_name
    - skills (list)
    - responsibilities (list)
    - seniority_level
    - domain
    - embedding (list)
    - cleaned_text
    """
    out = parse_job_description_pdf(path)

    # Simple name heuristic: first non-empty line or first sentence
    cleaned = out.get("cleaned_text", "")
    name_guess = ""
    if cleaned:
        # take first line before a newline or first sentence
        name_guess = cleaned.strip().split("\n")[0].split(".")[0][:80].strip()

    out["candidate_name"] = name_guess or Path(path).stem
    return out
