#!/usr/bin/env python3
"""
Fetch public profile counters from the public GitHub API -- no token, no auth:
public repos, followers, and total merged pull requests authored.
Writes data/stats.json, consumed by render_stats_svg.py.
Run daily by .github/workflows/update-profile-art.yml.
"""
import datetime
import json
import os

import requests

USERNAME = os.environ.get("GH_PROFILE_USER", "khadimmbaye0")
API = "https://api.github.com"
HEADERS = {
    "User-Agent": "profile-readme-bot/1.0",
    "Accept": "application/vnd.github+json",
}
# Use the built-in Actions token when present (raises API rate limits).
# Locally it's absent -- the public endpoints work unauthenticated too.
TOKEN = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
if TOKEN:
    HEADERS["Authorization"] = f"Bearer {TOKEN}"
OUT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "stats.json")


def get(url):
    resp = requests.get(url, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    return resp.json()


def main():
    user = get(f"{API}/users/{USERNAME}")
    prs = get(f"{API}/search/issues?q=author:{USERNAME}+type:pr+is:merged&per_page=1")

    data = {
        "username": USERNAME,
        "generated_at": datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "public_repos": user["public_repos"],
        "followers": user["followers"],
        "merged_prs": prs["total_count"],
    }

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w") as f:
        json.dump(data, f, indent=2)
    print(f"wrote {OUT_PATH}: {data['merged_prs']} merged PRs, "
          f"{data['public_repos']} public repos, {data['followers']} followers")


if __name__ == "__main__":
    main()
