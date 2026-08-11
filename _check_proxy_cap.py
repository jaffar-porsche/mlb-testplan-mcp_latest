import httpx, os

os.environ.pop("HTTP_PROXY", None); os.environ.pop("HTTPS_PROXY", None)
os.environ.pop("http_proxy", None); os.environ.pop("https_proxy", None)

JQL = 'issuetype = "Test Execution" AND labels = TA_Execution AND resolved >= 2026-04-01 AND resolved <= 2026-06-30'

for n in [500, 750, 1000, 1200]:
    r = httpx.get("http://localhost:8000/search_issues", params={"jql": JQL, "max_results": n}, timeout=60)
    issues = r.json().get("issues", [])
    print(f"max_results={n} -> got {len(issues)} issues")
