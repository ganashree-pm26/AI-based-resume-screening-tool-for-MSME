import re
from typing import Dict

def parse_generic_certificate(text: str) -> Dict:
    lines = [l.strip() for l in text.splitlines() if l.strip()]

    data = {
        "student_name": None,
        "course_title": None,
        "score_percent": None,
        "issue_info": None,
        "roll_or_id": None,
        "provider_guess": None,
    }

    # Provider: first line with CERTIFICATION/CERTIFICATE/ONLINE
    for line in lines[:5]:
        if any(word in line.upper() for word in ["CERTIFICATION", "CERTIFICATE", "ONLINE"]):
            data["provider_guess"] = line
            break

    # Name: line IMMEDIATELY AFTER "awarded to" / "presented to" / "certify"
    award_phrases = ["awarded to", "presented to", "certify that", "certificate is awarded"]
    for i, line in enumerate(lines):
        if any(phrase in line.lower() for phrase in award_phrases):
            if i + 1 < len(lines):
                candidate = lines[i + 1].strip()
                if candidate and len(candidate.split()) >= 2:  # Full name
                    data["student_name"] = candidate
            break

    # Course: line IMMEDIATELY AFTER "completing the course" / "completed course"
    course_phrases = ["completing the course", "completed course", "course entitled"]
    for i, line in enumerate(lines):
        if any(phrase in line.lower() for phrase in course_phrases):
            if i + 1 < len(lines):
                candidate = lines[i + 1].strip()
                if candidate and len(candidate.split()) >= 2:  # Course title
                    data["course_title"] = candidate
            break

    # Score: any line with "%"
    for line in lines:
        if "%" in line:
            m = re.search(r"(\d{1,3})\s*%", line)
            if m:
                data["score_percent"] = int(m.group(1))
                break

    # ID: "Roll No:", "ID:", "Certificate No:"
    for line in lines:
        if re.search(r"(Roll No|Roll Number|ID|Cert No)\s*[:\-]?", line, re.IGNORECASE):
            m = re.search(r"([A-Z0-9]{10,})", line)
            if m:
                data["roll_or_id"] = m.group(1)
                break

    # Session/Date: line with "MMM-MMM YYYY" pattern
    for line in lines:
        if re.search(r"[A-Z][a-z]{2}-[A-Z][a-z]{2}\s+\d{4}", line):
            data["issue_info"] = line
            break

    return data
