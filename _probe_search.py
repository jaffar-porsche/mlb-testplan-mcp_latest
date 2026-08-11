import httpx, os

os.environ.pop("HTTP_PROXY", None); os.environ.pop("HTTPS_PROXY", None)
os.environ.pop("http_proxy", None); os.environ.pop("https_proxy", None)

PROXY = "http://localhost:8000"
JQL = 'issuetype = "Test Execution" AND labels = TA_Execution AND resolved >= 2026-04-01 AND resolved <= 2026-06-30'

# Try different param names for pagination
for params in [
    {"jql": JQL, "startAt": 10, "maxResults": 5},
    {"jql": JQL, "start_at": 10, "max_results": 5},
    {"jql": JQL, "offset": 10, "limit": 5},
    {"jql": JQL, "page": 2, "limit": 5},
    {"jql": JQL, "page": 2, "per_page": 5},
]:
    r = httpx.get(f"{PROXY}/search_issues", params=params, timeout=30)
    data = r.json()
    issues = data if isinstance(data, list) else data.get("issues", [])
    keys = [i.get("key") or i.get("issueKey") for i in issues[:3]]
    print(f"params={list(params.keys())[1:]}: {len(issues)} issues, first={keys[:2]}")
