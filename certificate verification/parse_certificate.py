import re

raw_text = """
bh Elite f

¢Sz NPTEL ONLINE CERTIFICATION |
A = (Funded by the MoE, Govt. of India) Skill India

This certificate is awarded to
DHRUTHI RUDRANGI
for successfully completing the course

Introduction to Graph Algorithms

with a consolidated score of 93 %

Online Assignments | 25/25 Proctored Exam | 67.5/75

Total number of candidates certified in this course: 398

Jul-Sep 2025 Prof. L. Umanand

NPTEL Coordinator & Chair, Centre for Continuing
Education, IISc Bangalore

(8 week course)

Indian Institute of Science Bangalore

No. of credits recommended: 2 or 3

Roll No: NPTEL25CS1248132103561 To verify the certificate
"""

def parse_nptel_certificate(text: str) -> dict:
    lines = [l.strip() for l in text.splitlines() if l.strip()]

    data = {
        "platform": "NPTEL",
        "student_name": None,
        "course_title": None,
        "score_percent": None,
        "exam_score": None,
        "assignment_score": None,
        "duration": None,
        "session": None,
        "instructor": None,
        "roll_no": None,
        "credits_recommended": None,
    }

    # Name: line after "This certificate is awarded to"
    for i, line in enumerate(lines):
        if "This certificate is awarded to" in line:
            if i + 1 < len(lines):
                data["student_name"] = lines[i + 1]
            break

    # Course title: line after "for successfully completing the course"
    for i, line in enumerate(lines):
        if "for successfully completing the course" in line:
            if i + 1 < len(lines):
                data["course_title"] = lines[i + 1]
            break

    # Score percentage
    m = re.search(r"(\d+)\s*%", text)
    if m:
        data["score_percent"] = int(m.group(1))

    # Assignment and exam scores
    m_assign = re.search(r"Online Assignments\s*\|\s*([0-9.]+)/([0-9.]+)", text)
    if m_assign:
        data["assignment_score"] = f"{m_assign.group(1)}/{m_assign.group(2)}"

    m_exam = re.search(r"Proctored Exam\s*\|\s*([0-9.]+)/([0-9.]+)", text)
    if m_exam:
        data["exam_score"] = f"{m_exam.group(1)}/{m_exam.group(2)}"

    # Session and instructor: e.g. "Jul-Sep 2025 Prof. L. Umanand"
    m_session = re.search(r"([A-Za-z]{3}-[A-Za-z]{3}\s+\d{4})\s+(Prof\.[^\n]+)", text)
    if m_session:
        data["session"] = m_session.group(1)
        data["instructor"] = m_session.group(2)

    # Duration: "(8 week course)"
    m_dur = re.search(r"\(([^)]*week course[^)]*)\)", text)
    if m_dur:
        data["duration"] = m_dur.group(1)

    # Credits
    m_cred = re.search(r"No\. of credits recommended:\s*([0-9or ]+)", text)
    if m_cred:
        data["credits_recommended"] = m_cred.group(1).strip()

    # Roll number
    m_roll = re.search(r"Roll No:\s*([A-Z0-9]+)", text)
    if m_roll:
        data["roll_no"] = m_roll.group(1)

    return data


if __name__ == "__main__":
    parsed = parse_nptel_certificate(raw_text)
    print(parsed)
