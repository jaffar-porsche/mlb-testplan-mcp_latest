import httpx, os

os.environ.pop("HTTP_PROXY", None); os.environ.pop("HTTPS_PROXY", None)
os.environ.pop("http_proxy", None); os.environ.pop("https_proxy", None)

JQL = 'issuetype = "Test Execution" AND labels = TA_Execution AND resolved >= 2026-04-01 AND resolved <= 2026-06-30'
r = httpx.get(
    "http://127.0.0.1:8080/tmp/jql-fail-report",
    params={"jql": JQL, "max_executions": 5},
    timeout=120,
)
print("HTTP", r.status_code)
print(r.text[:3000])
