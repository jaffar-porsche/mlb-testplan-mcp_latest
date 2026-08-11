import httpx, json, os

os.environ.pop("HTTP_PROXY", None)
os.environ.pop("HTTPS_PROXY", None)
os.environ.pop("http_proxy", None)
os.environ.pop("https_proxy", None)

JQL = 'issuetype = "Test Execution" AND labels = TA_Execution AND resolved >= 2026-04-01 AND resolved <= 2026-06-30'

r = httpx.get(
    "http://localhost:8000/search_issues",
    params={"jql": JQL, "startAt": 0, "maxResults": 5},
    timeout=30,
)
print("HTTP", r.status_code)
data = r.json()
print("Top-level keys:", list(data.keys()))
print("total:", data.get("total"))
issues = data.get("issues", [])
print("Issues returned:", len(issues))
for iss in issues[:5]:
    print(" -", iss.get("key"), iss.get("summary", "")[:60])

# Also try key at top level
if isinstance(data, list):
    print("Response is a LIST, first 3:", [i.get("key") for i in data[:3]])
