import httpx, os, json

os.environ.pop("HTTP_PROXY", None); os.environ.pop("HTTPS_PROXY", None)
os.environ.pop("http_proxy", None); os.environ.pop("https_proxy", None)

PROXY = "http://localhost:8000"
EXEC_KEY = "MLBEVO-19688"

# 1. Get all test runs for this execution
r = httpx.get(f"{PROXY}/xray/testruns", params={"testExecKey": EXEC_KEY, "limit": 100}, timeout=30)
data = r.json()
runs = data if isinstance(data, list) else data.get("testRuns", data.get("runs", data.get("results", [])))
print(f"Total runs: {len(runs)}")

fail_runs = [run for run in runs if str(run.get("status", "")).upper() == "FAIL"]
print(f"FAIL runs: {len(fail_runs)}")

for run in fail_runs[:5]:
    run_id = run.get("id")
    print(f"\n--- FAIL run {run_id} ---")
    # Fetch run detail
    r2 = httpx.get(f"{PROXY}/xray/testrun/{run_id}", timeout=30)
    detail = r2.json()
    print("Comment field:", json.dumps(detail.get("comment"), indent=2))
    print("Steps sample:", json.dumps(detail.get("steps", [])[:1], indent=2))
