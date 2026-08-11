import httpx, os, json

os.environ.pop("HTTP_PROXY", None); os.environ.pop("HTTPS_PROXY", None)
os.environ.pop("http_proxy", None); os.environ.pop("https_proxy", None)

PROXY = "http://localhost:8000"
EXEC_KEY = "MLBEVO-19688"

# Get the FAIL run
r = httpx.get(f"{PROXY}/xray/testruns", params={"testExecKey": EXEC_KEY, "limit": 100}, timeout=30)
data = r.json()
runs = data if isinstance(data, list) else data.get("testRuns", data.get("runs", data.get("results", [])))

for run in runs:
    status = run.get("status", "")
    if isinstance(status, dict):
        status = status.get("name") or ""
    if "FAIL" in str(status).upper():
        run_id = run.get("id")
        test_key = (run.get("testKey") or run.get("key") or run.get("issueKey")
                    or (run.get("test") or {}).get("key"))
        print(f"FAIL run_id={run_id}, test_key={test_key}")
        print(f"Full run dict keys: {list(run.keys())}")
        print(json.dumps(run, indent=2))
