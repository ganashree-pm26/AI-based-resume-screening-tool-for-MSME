# google_finder.py

import os
import requests
from pathlib import Path
from urllib.parse import urlparse
from dotenv import load_dotenv
from time import sleep

load_dotenv()

SERPER_KEY = os.getenv("SERPER_API_KEY")
OUT_DIR = Path("downloaded_resumes")
OUT_DIR.mkdir(exist_ok=True)


# ---------------------------------------------------------------------------
# BUILD SMART GOOGLE SEARCH QUERIES
# ---------------------------------------------------------------------------
def build_queries(jd_title: str, skills: list, domain: str, limit=8):
    jd_title = jd_title or "Software Engineer"
    domain = domain or ""

    skills_str = " ".join(f'"{s}"' for s in skills[:5])

    queries = [
        f'"{jd_title}" resume filetype:pdf',
        f'"{jd_title}" cv filetype:pdf',
        f'{skills_str} resume filetype:pdf',
        f'{domain} "{jd_title}" resume filetype:pdf',
        f'"{jd_title}" resume',
        f'"{jd_title}" cv pdf',
    ]

    # EXTRA POWERFUL QUERY BOOSTERS
    extra_queries = [
        '"software engineer resume" filetype:pdf',
        '"computer science resume" filetype:pdf',
        '"developer resume" filetype:pdf',
        '"intern resume" filetype:pdf',
        '"fresher resume" filetype:pdf',
        '"student resume" filetype:pdf',
    ]

    queries.extend(extra_queries)

    # Remove duplicates but keep order
    unique_queries = []
    for q in queries:
        if q not in unique_queries:
            unique_queries.append(q)

    return unique_queries[:limit]


# ---------------------------------------------------------------------------
# SERPER SEARCH
# ---------------------------------------------------------------------------
def serper_search(query, max_results=10):
    if not SERPER_KEY:
        raise RuntimeError("❌ SERPER_API_KEY not found in .env file.")

    url = "https://google.serper.dev/search"

    headers = {
        "X-API-KEY": SERPER_KEY,
        "Content-Type": "application/json",
    }
    payload = {"q": query, "num": max_results}

    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=20)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        print(f"[Serper Error] {e}")
        return {"organic": []}


# ---------------------------------------------------------------------------
# EXTRACT RESUME LINKS
# ---------------------------------------------------------------------------
def extract_resume_urls(response_json):
    urls = []

    for item in response_json.get("organic", []):
        link = item.get("link") or ""
        title = (item.get("title") or "").lower()

        if not link:
            continue

        # Strip parameters
        link = link.split("?")[0]

        lower = link.lower()

        # ACCEPT MORE FILE TYPES (IMPORTANT!)
        if (
            lower.endswith(".pdf")
            or lower.endswith(".docx")
            or "pdf" in lower  # catches non-standard pdf links
            or "resume" in lower
            or "cv" in lower
        ):
            urls.append(link)
            continue

        # EXTRA heuristic: if title contains 'resume'
        if "resume" in title or "cv" in title:
            urls.append(link)

    # Unique list
    return list(dict.fromkeys(urls))


# ---------------------------------------------------------------------------
# DOWNLOAD FILE
# ---------------------------------------------------------------------------
def download_file(url):
    filename = url.split("/")[-1]

    # if no filename, generate a safe one
    if not filename or "." not in filename:
        filename = f"resume_{abs(hash(url))}.pdf"

    local_path = OUT_DIR / filename

    try:
        response = requests.get(url, stream=True, timeout=25)
        response.raise_for_status()

        with open(local_path, "wb") as f:
            for chunk in response.iter_content(1024 * 16):
                if chunk:
                    f.write(chunk)

        return str(local_path)

    except Exception as e:
        print(f"[Download Failed] {url} → {e}")
        return None


# ---------------------------------------------------------------------------
# FULL PIPELINE (core function)
# ---------------------------------------------------------------------------
def find_candidates_for_jd(jd_data, parse_and_score_fn, max_downloads=10):
    jd_title = jd_data.get("title") or jd_data.get("job_title") or "Software Engineer"
    skills = jd_data.get("skills", []) or []
    domain = jd_data.get("domain", "") or ""

    print("\n====== BUILDING SMART QUERIES ======")
    queries = build_queries(jd_title, skills, domain, limit=8)

    all_urls = []

    print("\n====== SEARCHING GOOGLE ======")
    for q in queries:
        print(f"[QUERY] {q}")
        serper_json = serper_search(q)
        urls = extract_resume_urls(serper_json)
        print(f"  → Found {len(urls)} links")
        all_urls.extend(urls)
        sleep(0.3)  # prevent rate limit

    # Deduplicate
    all_urls = list(dict.fromkeys(all_urls))
    print(f"\nTotal unique links found: {len(all_urls)}")

    if len(all_urls) == 0:
        print("No URLs found.")
        return []

    # -------------------------------------------------------------------
    # Download + parse resumes
    # -------------------------------------------------------------------
    results = []
    downloaded = 0

    print("\n====== DOWNLOADING & MATCHING RESUMES ======")

    for link in all_urls:
        if downloaded >= max_downloads:
            break

        print(f"Downloading: {link}")
        file_path = download_file(link)

        if not file_path:
            continue

        try:
            result_obj = parse_and_score_fn(file_path, jd_data, source_url=link)
            results.append(result_obj)
            downloaded += 1

            print(f" ✓ Parsed + scored candidate #{downloaded}")

        except Exception as e:
            print(f"[Parse Error] {file_path}: {e}")

        sleep(0.3)

    # Sort by best match score
    results.sort(key=lambda x: x.get("final_score", 0), reverse=True)

    return results
