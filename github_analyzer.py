import requests
import base64
import re

# -------------------------------
# Helper: Clean README text
# -------------------------------
def clean_readme(text):
    if not text:
        return ""
    text = re.sub(r"<[^>]+>", "", text)        # remove HTML tags
    text = re.sub(r"[#*_>`-]", " ", text)      # remove markdown symbols
    return " ".join(text.split())


# --------------------------------
# Score calculation
# --------------------------------
def compute_repo_score(meta):
    score = 0

    # Stars
    score += min(meta["stars"], 50) * 0.5

    # Forks
    score += min(meta["forks"], 20) * 0.3

    # Issues
    if meta["open_issues"] == 0:
        score += 5
    else:
        score += 2

    # README quality
    readme_len = len(meta["readme"])
    if readme_len > 2000:
        score += 15
    elif readme_len > 1000:
        score += 10
    elif readme_len > 300:
        score += 5
    else:
        score += 1

    # Languages count
    score += min(len(meta["languages"]), 5) * 2

    # Activity (recent updates)
    score += 10

    return round(score, 2)


# --------------------------------
# Fetch README
# --------------------------------
def fetch_readme(username, repo):
    url = f"https://api.github.com/repos/{username}/{repo}/readme"
    res = requests.get(url)
    if res.status_code != 200:
        return ""
    content = res.json().get("content", "")
    try:
        decoded = base64.b64decode(content).decode("utf-8", errors="ignore")
        return clean_readme(decoded)
    except:
        return ""


# --------------------------------
# Fetch languages
# --------------------------------
def fetch_languages(username, repo):
    url = f"https://api.github.com/repos/{username}/{repo}/languages"
    res = requests.get(url)
    if res.status_code != 200:
        return []
    return list(res.json().keys())


# --------------------------------
# MAIN FUNCTION
# --------------------------------
def analyze_github_profile(username):
    print(f"\nAnalyzing GitHub profile: {username}\n")

    url = f"https://api.github.com/users/{username}/repos"
    res = requests.get(url)

    if res.status_code != 200:
        print("Invalid username or API limit reached.")
        return

    repos = res.json()

    if len(repos) == 0:
        print("No public repositories found.")
        return

    profile_score = 0
    detailed_results = []

    for repo in repos:
        repo_name = repo["name"]

        print(f"Processing repository: {repo_name}...")

        readme = fetch_readme(username, repo_name)
        languages = fetch_languages(username, repo_name)

        meta = {
            "name": repo_name,
            "stars": repo["stargazers_count"],
            "forks": repo["forks_count"],
            "open_issues": repo["open_issues_count"],
            "languages": languages,
            "readme": readme
        }

        repo_score = compute_repo_score(meta)
        profile_score += repo_score

        detailed_results.append({
            "repo": repo_name,
            "meta": meta,
            "score": repo_score
        })

    # ----------------------------
    # Final Profile Score
    # ----------------------------
    profile_score = round(profile_score / len(repos), 2)

    print("\n--------------- RESULTS ---------------\n")
    print(f"Overall Profile Score: {profile_score}/100\n")

    for item in detailed_results:
        print(f"Repository: {item['repo']}")
        print(f" - Score: {item['score']}")
        print(f" - Stars: {item['meta']['stars']}")
        print(f" - Forks: {item['meta']['forks']}")
        print(f" - Issues: {item['meta']['open_issues']}")
        print(f" - Languages: {item['meta']['languages']}")
        print(f" - README length: {len(item['meta']['readme'])}")
        print()

    print("---------------------------------------\n")


# --------------------------------
# Run with input
# --------------------------------
if __name__ == "__main__":
    username = input("Enter your GitHub username: ").strip()
    analyze_github_profile(username)
