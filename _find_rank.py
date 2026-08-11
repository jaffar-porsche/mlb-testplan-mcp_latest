import httpx, os

os.environ.pop("HTTP_PROXY", None)
os.environ.pop("HTTPS_PROXY", None)
os.environ.pop("http_proxy", None)
os.environ.pop("https_proxy", None)

PROXY = "http://localhost:8000"
TARGET = "MLBEVO-19688"
TARGET_RESOLVED = "2026-06-25"  # resolved this date

# Count issues resolved strictly AFTER this date → position = that count + 1
jql_after = (
    'issuetype = "Test Execution" AND labels = TA_Execution '
    'AND resolved >= 2026-04-01 AND resolved <= 2026-06-30 '
    f'AND resolved > {TARGET_RESOLVED}'
)

r = httpx.get(
    f"{PROXY}/search_issues",
    params={"jql": jql_after, "max_results": 2000},
    timeout=60,
)
data = r.json()
issues = data if isinstance(data, list) else data.get("issues", [])
print(f"Issues resolved after {TARGET_RESOLVED}: {len(issues)}")
print(f"=> {TARGET} is at approximately position {len(issues) + 1}")
print(f"=> max_executions needs to be >= {len(issues) + 1}")
