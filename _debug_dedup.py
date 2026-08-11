import httpx, os

os.environ.pop("HTTP_PROXY", None); os.environ.pop("HTTPS_PROXY", None)
os.environ.pop("http_proxy", None); os.environ.pop("https_proxy", None)

PROXY = "http://localhost:8000"
TEST_KEY = "MLBEVO-11973"
OUR_RUN_ID = 17998041

# Find all test runs for this test key across all executions
r = httpx.get(f"{PROXY}/xray/testruns", params={"testKey": TEST_KEY, "limit": 100}, timeout=30)
data = r.json()
runs = data if isinstance(data, list) else data.get("testRuns", data.get("runs", data.get("results", [])))
print(f"All runs for {TEST_KEY}: {len(runs)}")
for run in runs:
    rid = run.get("id")
    status = run.get("status", "")
    if isinstance(status, dict):
        status = status.get("name") or ""
    exec_key = run.get("testExecKey", "?")
    comment = run.get("comment", "")
    marker = " <-- OURS" if rid == OUR_RUN_ID else ""
    marker += " *** NEWER" if rid and rid > OUR_RUN_ID and "FAIL" in str(status).upper() else ""
    print(f"  run_id={rid} status={status} exec={exec_key} comment={str(comment)[:30]}{marker}")
