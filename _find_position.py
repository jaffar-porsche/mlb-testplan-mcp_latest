"""Find the position of MLBEVO-19668 in the JQL result set."""
import httpx, os

os.environ.pop("HTTP_PROXY", None)
os.environ.pop("HTTPS_PROXY", None)
os.environ.pop("http_proxy", None)
os.environ.pop("https_proxy", None)

PROXY = "http://localhost:8000"
JQL = 'issuetype = "Test Execution" AND labels = TA_Execution AND resolved >= 2026-04-01 AND resolved <= 2026-06-30'
TARGET = "MLBEVO-19688"

start = 0
page_size = 50
position = None
total = None

while True:
    r = httpx.get(
        f"{PROXY}/search_issues",
        params={"jql": JQL, "startAt": start, "maxResults": page_size},
        timeout=60,
    )
    data = r.json()
    issues = data.get("issues", [])
    if total is None:
        total = data.get("total", "?")
        print(f"Total issues in JQL: {total}")

    for i, issue in enumerate(issues):
        key = issue.get("key", "")
        if key == TARGET:
            position = start + i + 1  # 1-based
            print(f"\nFound {TARGET} at position {position} (0-based index: {start + i})")
            print(f"=> max_executions must be >= {position}")
            break

    if position is not None:
        break

    if len(issues) < page_size:
        print(f"\n{TARGET} NOT found in {total} results.")
        break

    start += page_size
    print(f"  Scanned {start} so far...")

print("Done.")
