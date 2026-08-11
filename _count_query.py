import httpx, json

# Route through the local proxy (port 8000) which handles auth internally
jql = 'issuetype = "Test Execution" AND labels = TA_Execution AND resolved >= 2026-04-01 AND resolved <= 2026-06-30'

r = httpx.get(
    "http://localhost:8000/search_issues",
    params={"jql": jql, "max_results": 1},
    timeout=30,
    follow_redirects=True,
)
print("HTTP", r.status_code)
print("response:", r.text[:300])

