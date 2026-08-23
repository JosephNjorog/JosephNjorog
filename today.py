"""
today.py — refreshes dark_mode.svg / light_mode.svg with live GitHub data.

Runs on a schedule via .github/workflows/update-profile.yml.

Requires one repo secret:
  ACCESS_TOKEN — a Personal Access Token (classic) with `repo` + `read:user`
                 scopes, OR a fine-grained token with read access to your
                 repositories and profile. The default GITHUB_TOKEN cannot
                 see private repos / full contribution history, so a PAT
                 is required for accurate numbers.

What it computes:
  - Repos          -> public + private repos you own (non-fork)
  - Contributed To -> distinct repos you've contributed to (incl. others')
  - Stars          -> total stargazers across your owned repos
  - Commits (YEAR) -> your commit contributions so far this calendar year
  - Lines of Code  -> net (additions - deletions) across your owned repos,
                       via the GitHub "contributor stats" endpoint
  - Followers      -> your follower count

Numbers are written into the SVG by matching `id="..."` on the relevant
<text>/<tspan> nodes, so re-running this script is idempotent and never
touches layout, styling, or the portrait.
"""

import os
import re
import sys
import json
import time
import datetime
import requests

USERNAME = os.environ.get("GITHUB_PROFILE_USER", "JosephNjorog")
TOKEN = os.environ.get("ACCESS_TOKEN") or os.environ.get("GITHUB_TOKEN")

if not TOKEN:
    sys.exit("No ACCESS_TOKEN / GITHUB_TOKEN available in the environment.")

GRAPHQL_URL = "https://api.github.com/graphql"
REST_ROOT = "https://api.github.com"
HEADERS_GQL = {"Authorization": f"bearer {TOKEN}"}
HEADERS_REST = {
    "Authorization": f"token {TOKEN}",
    "Accept": "application/vnd.github+json",
}

CACHE_PATH = "cache/loc_cache.json"


def gql(query: str, variables: dict) -> dict:
    r = requests.post(
        GRAPHQL_URL, json={"query": query, "variables": variables}, headers=HEADERS_GQL
    )
    r.raise_for_status()
    payload = r.json()
    if "errors" in payload:
        raise RuntimeError(payload["errors"])
    return payload["data"]


def fetch_profile_overview():
    """Repos, forks flag, stargazers, default branch, contributed-to count, followers."""
    query = """
    query($login: String!, $cursor: String) {
      user(login: $login) {
        followers { totalCount }
        repositoriesContributedTo(first: 1, contributionTypes: [COMMIT, ISSUE, PULL_REQUEST, REPOSITORY]) {
          totalCount
        }
        repositories(first: 100, after: $cursor, ownerAffiliations: OWNER, isFork: false, privacy: null) {
          totalCount
          pageInfo { hasNextPage endCursor }
          nodes {
            name
            stargazerCount
            defaultBranchRef { name }
          }
        }
      }
    }
    """
    repos = []
    cursor = None
    followers = 0
    contributed_to = 0
    while True:
        data = gql(query, {"login": USERNAME, "cursor": cursor})
        user = data["user"]
        followers = user["followers"]["totalCount"]
        contributed_to = user["repositoriesContributedTo"]["totalCount"]
        page = user["repositories"]
        repos.extend(page["nodes"])
        if page["pageInfo"]["hasNextPage"]:
            cursor = page["pageInfo"]["endCursor"]
        else:
            break
    return repos, followers, contributed_to


def fetch_commits_this_year():
    year = datetime.datetime.utcnow().year
    since = f"{year}-01-01T00:00:00Z"
    until = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    query = """
    query($login: String!, $from: DateTime!, $to: DateTime!) {
      user(login: $login) {
        contributionsCollection(from: $from, to: $to) {
          totalCommitContributions
          restrictedContributionsCount
        }
      }
    }
    """
    data = gql(query, {"login": USERNAME, "from": since, "to": until})
    cc = data["user"]["contributionsCollection"]
    return cc["totalCommitContributions"] + cc["restrictedContributionsCount"], year


def load_cache() -> dict:
    if os.path.exists(CACHE_PATH):
        with open(CACHE_PATH) as f:
            return json.load(f)
    return {}


def save_cache(cache: dict):
    os.makedirs(os.path.dirname(CACHE_PATH), exist_ok=True)
    with open(CACHE_PATH, "w") as f:
        json.dump(cache, f, indent=2)


def repo_loc(owner: str, repo: str, cache: dict) -> tuple[int, int]:
    """Net (additions, deletions) authored by USERNAME in one repo, cached
    per default-branch HEAD sha so unchanged repos skip the API call."""
    head_resp = requests.get(f"{REST_ROOT}/repos/{owner}/{repo}", headers=HEADERS_REST)
    if head_resp.status_code != 200:
        return 0, 0
    default_branch = head_resp.json().get("default_branch")
    if not default_branch:
        return 0, 0

    branch_resp = requests.get(
        f"{REST_ROOT}/repos/{owner}/{repo}/branches/{default_branch}", headers=HEADERS_REST
    )
    head_sha = branch_resp.json().get("commit", {}).get("sha", "")

    cache_key = f"{owner}/{repo}"
    cached = cache.get(cache_key)
    if cached and cached.get("sha") == head_sha:
        return cached["additions"], cached["deletions"]

    # GitHub computes this asynchronously the first time; retry briefly.
    additions = deletions = 0
    for attempt in range(4):
        resp = requests.get(
            f"{REST_ROOT}/repos/{owner}/{repo}/stats/contributors", headers=HEADERS_REST
        )
        if resp.status_code == 202:
            time.sleep(2.5)
            continue
        if resp.status_code != 200 or not isinstance(resp.json(), list):
            break
        for entry in resp.json():
            author = entry.get("author") or {}
            if author.get("login", "").lower() == USERNAME.lower():
                for week in entry.get("weeks", []):
                    additions += week.get("a", 0)
                    deletions += week.get("d", 0)
        break

    cache[cache_key] = {"sha": head_sha, "additions": additions, "deletions": deletions}
    return additions, deletions


def fmt(n: int) -> str:
    return f"{n:,}"


def update_svg(path: str, values: dict):
    with open(path, "r", encoding="utf-8") as f:
        svg = f.read()

    for tspan_id, value in values.items():
        pattern = rf'(id="{re.escape(tspan_id)}">)(.*?)(</)'
        svg, count = re.subn(pattern, rf"\g<1>{value}\g<3>", svg, count=1)
        if count == 0:
            print(f"::warning::id '{tspan_id}' not found in {path}")

    with open(path, "w", encoding="utf-8") as f:
        f.write(svg)


def main():
    print(f"Fetching live GitHub data for {USERNAME}...")
    repos, followers, contributed_to = fetch_profile_overview()
    commits_this_year, year = fetch_commits_this_year()
    stars = sum(r["stargazerCount"] for r in repos)

    cache = load_cache()
    total_additions = total_deletions = 0
    for r in repos:
        a, d = repo_loc(USERNAME, r["name"], cache)
        total_additions += a
        total_deletions += d
    save_cache(cache)

    net_loc = total_additions - total_deletions
    loc_display = f"+{fmt(net_loc)}" if net_loc >= 0 else f"-{fmt(abs(net_loc))}"

    values = {
        "repo_data": fmt(len(repos)),
        "contrib_data": fmt(contributed_to),
        "star_data": fmt(stars),
        "commit_data": fmt(commits_this_year),
        "loc_data": loc_display,
        "follower_data": fmt(followers),
        "sync_date": datetime.datetime.utcnow().strftime("%Y-%m-%d"),
    }

    # relabel the "Commits (YEAR)" row for the current year automatically
    for path in ("dark_mode.svg", "light_mode.svg"):
        with open(path) as f:
            svg = f.read()
        svg = re.sub(r"Commits \(\d{4}\)", f"Commits ({year})", svg)
        with open(path, "w") as f:
            f.write(svg)
        update_svg(path, values)

    print("Done:", json.dumps(values, indent=2))


if __name__ == "__main__":
    main()
