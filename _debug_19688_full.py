import httpx, os, json

os.environ.pop("HTTP_PROXY", None); os.environ.pop("HTTPS_PROXY", None)
os.environ.pop("http_proxy", None); os.environ.pop("https_proxy", None)

# Step 1: Get 500 executions from the JQL (same as the endpoint does)
JQL = 'issuetype = "Test Execution" AND labels = TA_Execution AND resolved >= 2026-04-01 AND resolved <= 2026-06-30'
r = httpx.get("http://localhost:8000/search_issues", params={"jql": JQL, "max_results": 500}, timeout=120)
data = r.json()
issues = data if isinstance(data, list) else data.get("issues", [])
keys = [i.get("key") or i.get("issueKey") for i in issues]
print(f"Executions returned: {len(keys)}")

TARGET = "MLBEVO-19688"
if TARGET in keys:
    print(f"{TARGET} is at position {keys.index(TARGET)+1}")
else:
    print(f"{TARGET} NOT in the 500 keys from search_issues")
    print(f"Last 5 keys: {keys[-5:]}")

# Step 2: Directly scan MLBEVO-19688 for FAILs
print(f"\nDirect scan of {TARGET}:")
r2 = httpx.get("http://localhost:8000/xray/testruns", params={"testExecKey": TARGET, "limit": 100}, timeout=30)
runs = r2.json()
if isinstance(runs, list):
    pass
else:
    runs = runs.get("testRuns", runs.get("runs", runs.get("results", [])))
fail_runs = [run for run in runs if "FAIL" in str(run.get("status", "")).upper()]
print(f"  Total runs: {len(runs)}, FAIL runs: {len(fail_runs)}")
for run in fail_runs:
    print(f"  FAIL run_id={run.get('id')} testKey={run.get('testKey')} comment={str(run.get('comment',''))[:50]}")

# Step 3: Call the actual endpoint with max_executions=210 (201+buffer)
print(f"\nCalling /tmp/jql-fail-report with max_executions=210...")
r3 = httpx.get(
    "http://127.0.0.1:8080/tmp/jql-fail-report",
    params={"jql": JQL, "max_executions": 210},
    timeout=600,
)
print(f"HTTP {r3.status_code}")
resp = r3.json()
print(f"executions_scanned: {resp.get('executions_scanned')}")
exec_list = resp.get("executions_list", [])
print(f"executions_list count: {len(exec_list)}")
if TARGET in exec_list:
    print(f"{TARGET} IS in executions_list at position {exec_list.index(TARGET)+1}")
else:
    print(f"{TARGET} NOT in executions_list")

results = resp.get("results", [])
print(f"total_fail: {resp.get('total_fail')}, results count: {len(results)}")
matching = [r for r in results if r.get("test_exec_key") == TARGET]
print(f"Results from {TARGET}: {len(matching)}")
for m in matching:
    print(f"  {m}")
