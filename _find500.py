import httpx, os

os.environ.pop("HTTP_PROXY", None); os.environ.pop("HTTPS_PROXY", None)
os.environ.pop("http_proxy", None); os.environ.pop("https_proxy", None)

JQL = 'issuetype = "Test Execution" AND labels = TA_Execution AND resolved >= 2026-04-01 AND resolved <= 2026-06-30'
TARGET = "MLBEVO-19688"

r = httpx.get(
    "http://localhost:8000/search_issues",
    params={"jql": JQL, "max_results": 500},
    timeout=120,
)
data = r.json()
issues = data if isinstance(data, list) else data.get("issues", [])
print("Count:", len(issues))
keys = [i.get("key") or i.get("issueKey") for i in issues]
if TARGET in keys:
    print(f"{TARGET} found at position {keys.index(TARGET) + 1}")
else:
    print(f"{TARGET} NOT in results. Last 3: {keys[-3:]}")
