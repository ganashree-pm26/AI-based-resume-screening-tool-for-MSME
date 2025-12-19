import requests
import base64
import re
from dotenv import load_dotenv
import os

# --------------------------------
# LOAD GITHUB TOKEN
# --------------------------------
load_dotenv()
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

HEADERS = {}
if GITHUB_TOKEN:
    HEADERS = {"Authorization": f"token {GITHUB_TOKEN}"}

# --------------------------------
# CLEAN README
# --------------------------------
def clean_readme(text):
    if not text:
        return ""
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"[#*_>`-]", " ", text)
    return " ".join(text.split())


# --------------------------------
# SCORE FUNCTION
# --------------------------------
def compute_repo_score(meta):
    score = 0
    score += min(meta["stars"], 50) * 0.5
    score += min(meta["forks"], 20) * 0.3
    score += 5 if meta["open_issues"] == 0 else 2

    readme_len = len(meta["readme"])
    if readme_len > 2000: score += 15
    elif readme_len > 1000: score += 10
    elif readme_len > 300: score += 5
    else: score += 1

    score += min(len(meta["languages"]), 5) * 2
    score += 10

    return round(score, 2)


# --------------------------------
# FETCH README
# --------------------------------
def fetch_readme(username, repo):
    url = f"https://api.github.com/repos/{username}/{repo}/readme"
    res = requests.get(url, headers=HEADERS)

    if res.status_code != 200:
        return ""

    content = res.json().get("content", "")
    try:
        decoded = base64.b64decode(content).decode("utf-8", errors="ignore")
        return clean_readme(decoded)
    except:
        return ""


# --------------------------------
# FETCH LANGUAGES
# --------------------------------
def fetch_languages(username, repo):
    url = f"https://api.github.com/repos/{username}/{repo}/languages"
    res = requests.get(url, headers=HEADERS)

    if res.status_code != 200:
        return []
    return list(res.json().keys())


# --------------------------------
# RECURSIVE FETCH CODE FILES
# --------------------------------
def fetch_repo_files_recursive(api_url):
    code_files = []

    try:
        res = requests.get(api_url, headers=HEADERS)
        items = res.json()
    except:
        return []

    if not isinstance(items, list):
        return []

    for item in items:
        if item["type"] == "dir":
            code_files += fetch_repo_files_recursive(item["url"])

        elif item["type"] == "file" and item["name"].endswith(
            (".py", ".js", ".jsx", ".ts", ".java", ".cpp", ".c", ".go")
        ):
            code_files.append(item["download_url"])

    return code_files


def fetch_repo_files(username, repo):
    api_url = f"https://api.github.com/repos/{username}/{repo}/contents"
    return fetch_repo_files_recursive(api_url)


# --------------------------------
# DOWNLOAD RAW CODE
# --------------------------------
def download_raw_code(url):
    try:
        r = requests.get(url, headers=HEADERS)
        if r.status_code == 200:
            return r.text
    except:
        return ""
    return ""


# --------------------------------
# SKILL PATTERNS
# --------------------------------
CODE_SKILL_PATTERNS = {
    r"import numpy|np\.": "NumPy",
    r"import pandas|pd\.": "Pandas",
    r"from sklearn": "Scikit-Learn",
    r"import torch": "PyTorch",
    r"import tensorflow": "TensorFlow",
    r"matplotlib": "Matplotlib",
    r"seaborn": "Seaborn",
    r"flask": "Flask",
    r"django": "Django",
    r"React\.|useState|useEffect": "ReactJS",
    r"express\(": "Express.js",
    r"node\.js|npm": "Node.js",
    r"import java": "Java",
    r"#include <": "C/C++",
    r"def ": "Python",
    r"console\.log": "JavaScript",
    r"package main": "Go",
}

def extract_skills_from_code(code_text):
    found = set()
    for pattern, skill in CODE_SKILL_PATTERNS.items():
        if re.search(pattern, code_text, re.IGNORECASE):
            found.add(skill)
    return list(found)


# --------------------------------
# MAIN PROFILE ANALYSIS
# --------------------------------
def analyze_github_profile(username):
    url = f"https://api.github.com/users/{username}/repos"
    res = requests.get(url, headers=HEADERS)

    if res.status_code != 200:
        raise ValueError("Invalid username or GitHub API rate limit reached.")

    repos = res.json()
    if len(repos) == 0:
        raise ValueError("No public repositories found.")

    profile_score = 0
    detailed_results = []

    for repo in repos:
        repo_name = repo["name"]

        readme = fetch_readme(username, repo_name)
        languages = fetch_languages(username, repo_name)

        file_urls = fetch_repo_files(username, repo_name)
        code_skills = set()

        for file_url in file_urls:
            code_text = download_raw_code(file_url)
            code_skills.update(extract_skills_from_code(code_text))

        meta = {
            "name": repo_name,
            "stars": repo["stargazers_count"],
            "forks": repo["forks_count"],
            "open_issues": repo["open_issues_count"],
            "languages": languages,
            "readme": readme,
            "code_skills": list(code_skills)
        }

        repo_score = compute_repo_score(meta)
        profile_score += repo_score

        detailed_results.append({
            "repo": repo_name,
            "meta": meta,
            "score": repo_score
        })

    profile_score = round(profile_score / len(repos), 2)

    return profile_score, detailed_results
