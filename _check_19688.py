import httpx, json, os

os.environ.pop("HTTP_PROXY", None)
os.environ.pop("HTTPS_PROXY", None)
os.environ.pop("http_proxy", None)
os.environ.pop("https_proxy", None)

PROXY = "http://localhost:8000"
TARGET = "MLBEVO-19688"

# 1. Confirm the issue exists and matches criteria
r = httpx.get(f"{PROXY}/issue/{TARGET}", timeout=30)
data = r.json()
print(f"Issue: {TARGET}")
print(f"  Type:     {data.get('issuetype', {}).get('name')}")
print(f"  Labels:   {data.get('labels')}")
print(f"  Resolved: {data.get('resolutiondate')}")
print(f"  Status:   {data.get('status', {}).get('name')}")
print()

# 2. Search specifically for just this issue to confirm it appears in JQL
jql_single = f'issue = {TARGET}'
r2 = httpx.get(f"{PROXY}/search_issues", params={"jql": jql_single, "max_results": 5}, timeout=30)
d2 = r2.json()
issues = d2 if isinstance(d2, list) else d2.get("issues", [])
print(f"Direct JQL search for {TARGET}: {len(issues)} result(s)")

# 3. Search with full JQL + orderBy to check if proxy supports it
jql_ordered = ('issuetype = "Test Execution" AND labels = TA_Execution '
               'AND resolved >= 2026-04-01 AND resolved <= 2026-06-30 '
               'AND project = MLBEVO')
r3 = httpx.get(f"{PROXY}/search_issues", params={"jql": jql_ordered, "max_results": 50}, timeout=30)
d3 = r3.json()
issues3 = d3 if isinstance(d3, list) else d3.get("issues", [])
print(f"\nMLBEVO project only — issues returned: {len(issues3)}")
for iss in issues3[:10]:
    k = iss.get("key") or iss.get("issueKey")
    print(f"  {k}")
