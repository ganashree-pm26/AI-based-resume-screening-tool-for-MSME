# linkedin_finder.py

import os
import requests
from dotenv import load_dotenv
from matching import skill_overlap_score as skill_overlap

load_dotenv()

SERPER_KEY = os.getenv("SERPER_API_KEY")


# ---------------------------------------------------------
# GOOGLE SEARCH FOR LINKEDIN PROFILES  (LEGAL)
# ---------------------------------------------------------
def search_linkedin_profiles(jd_title, jd_skills, location=None, max_results=10):

    # Use only top 2 skills for broader search
    core_skills = jd_skills[:2]
    skills_str = " ".join(f'"{s}"' for s in core_skills)

    loc = f'"{location}"' if location and location != "Not Specified" else ""

    # BROAD LinkedIn search queries (Google SERP performs best with this)
    queries = [
        f'site:linkedin.com/in "{jd_title}" {loc}',
        f'site:linkedin.com/in {skills_str} {loc}',
        f'site:linkedin.com/in "{jd_title}"',
        f'site:linkedin.com/in developer {loc}',
        f'site:linkedin.com/in engineer {loc}',
        f'site:linkedin.com/in software {loc}',
        f'site:linkedin.com/in fresher {loc}',
    ]

    SERPER_URL = "https://google.serper.dev/search"

    headers = {
        "X-API-KEY": SERPER_KEY,
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0",
    }

    profiles = []

    for q in queries:
        payload = {"q": q, "num": max_results}
        print(f"[LinkedIn Query] {q}")

        try:
            response = requests.post(SERPER_URL, json=payload, headers=headers, timeout=20)
            response.raise_for_status()
            data = response.json()
        except Exception as e:
            print("LinkedIn search error:", e)
            continue

        for item in data.get("organic", []):
            link = item.get("link", "")

            if "linkedin.com/in" not in link:
                continue

            profiles.append({
                "url": link,
                "title": item.get("title", ""),
                "snippet": item.get("snippet", "")
            })

    # Remove duplicates
    unique_profiles = {p["url"]: p for p in profiles}
    return list(unique_profiles.values())


# ---------------------------------------------------------
# EXTRACT CANDIDATE INFO FROM GOOGLE SNIPPET
# ---------------------------------------------------------
def extract_candidate(profile):

    title = profile["title"]
    snippet = profile["snippet"]

    # Extract name + headline
    if "–" in title:
        name, headline = title.split("–", 1)
    else:
        parts = title.split("-")
        name = parts[0]
        headline = parts[-1] if len(parts) > 1 else title

    # Extract skills (Google snippets often contain them)
    raw = snippet.replace("·", ",").replace("|", ",").replace("-", ",")
    skills = [s.strip() for s in raw.split(",") if len(s.strip()) > 1]

    return {
        "name": name.strip(),
        "headline": headline.strip(),
        "skills": skills,
        "snippet": snippet,
        "url": profile["url"],
    }


# ---------------------------------------------------------
# MATCH CANDIDATE TO JOB DESCRIPTION
# ---------------------------------------------------------
def evaluate_candidate(candidate, jd):
    score, matched, missing = skill_overlap(jd["skills"], candidate["skills"])

    candidate["match_score"] = round(score * 100, 2)
    candidate["matched_skills"] = matched
    candidate["missing_skills"] = missing

    return candidate


# ---------------------------------------------------------
# MAIN PIPELINE
# ---------------------------------------------------------
def find_linkedin_candidates(jd):

    profiles = search_linkedin_profiles(
        jd_title=jd.get("title", "Software Engineer"),
        jd_skills=jd["skills"],
        location=jd.get("location", "India"),
        max_results=20
    )

    candidates = []

    for p in profiles:
        c = extract_candidate(p)
        scored = evaluate_candidate(c, jd)
        candidates.append(scored)

    candidates.sort(key=lambda x: x["match_score"], reverse=True)
    return candidates
