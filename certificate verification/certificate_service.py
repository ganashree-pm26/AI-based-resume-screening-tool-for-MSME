from typing import Dict
from datetime import datetime, timedelta
from certificate_pipeline import process_certificate

def verify_claim(parsed: Dict, claimed_name: str, claimed_course: str) -> Dict:
    def norm(s):
        return (s or "").strip().lower()

    return {
        "name_matches": norm(parsed.get("student_name")) == norm(claimed_name),
        "course_matches": norm(parsed.get("course_title")) == norm(claimed_course),
        "has_id": parsed.get("roll_or_id") is not None,
        "has_score": parsed.get("score_percent") is not None,
    }

def compute_validity_generic(parsed: Dict, years_valid: int = 3) -> Dict:
    """
    Very generic validity: looks at issue_info line, tries to find year & month.
    If found, treats end of that month as issue date and adds 'years_valid'.
    """
    info = parsed.get("issue_info")
    if not info:
        return {"issue_date": None, "valid_till": None, "is_currently_valid": None}

    try:
        # try to find month & year like "Jul" and "2025"
        month_map = {
            "Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4,
            "May": 5, "Jun": 6, "Jul": 7, "Aug": 8,
            "Sep": 9, "Oct": 10, "Nov": 11, "Dec": 12,
        }
        month = None
        for abbr, num in month_map.items():
            if abbr in info:
                month = num
                break
        year_match = None
        m =  re.search(r"(\d{4})", info)
        if m:
            year_match = int(m.group(1))

        if not month or not year_match:
            raise ValueError("no month/year found")

        # assume issue date = last day of that month
        if month == 12:
            issue_date = datetime(year_match, 12, 31)
        else:
            first_next = datetime(year_match, month + 1, 1)
            issue_date = first_next - timedelta(days=1)

        valid_till = datetime(issue_date.year + years_valid, issue_date.month, issue_date.day)
        now = datetime.now()
        is_valid = now <= valid_till

        return {
            "issue_date": issue_date,
            "valid_till": valid_till,
            "is_currently_valid": is_valid,
        }
    except Exception:
        return {"issue_date": None, "valid_till": None, "is_currently_valid": None}

def handle_uploaded_certificate(image_path: str, claimed_name: str, claimed_course: str) -> Dict:
    parsed = process_certificate(image_path)
    checks = verify_claim(parsed, claimed_name, claimed_course)
    validity = compute_validity_generic(parsed, years_valid=3)

    validity_out = {
        "issue_date": validity["issue_date"].strftime("%Y-%m-%d") if validity["issue_date"] else None,
        "valid_till": validity["valid_till"].strftime("%Y-%m-%d") if validity["valid_till"] else None,
        "is_currently_valid": validity["is_currently_valid"],
    }

    return {
        "parsed": parsed,
        "checks": checks,
        "validity": validity_out,
    }
