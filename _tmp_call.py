import httpx, json, os

os.environ.pop("HTTP_PROXY", None)
os.environ.pop("HTTPS_PROXY", None)
os.environ.pop("http_proxy", None)
os.environ.pop("https_proxy", None)

jql = 'issuetype = "Test Execution" AND labels = TA_Execution AND resolved >= 2026-04-01 AND resolved <= 2026-06-30'

# Change offset + max_executions to scan in chunks:
#   offset=0,   max_executions=100  -> executions 1-100
#   offset=100, max_executions=100  -> executions 101-200
#   offset=200, max_executions=100  -> executions 201-300
OFFSET = 0
CHUNK  = 100

r = httpx.get(
    "http://127.0.0.1:8080/tmp/jql-fail-report",
    params={"jql": jql, "max_executions": CHUNK, "offset": OFFSET},
    timeout=600,
)
print("HTTP", r.status_code)
print(json.dumps(r.json(), indent=2))
