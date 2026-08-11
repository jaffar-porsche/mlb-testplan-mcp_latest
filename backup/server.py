import re
import os
import httpx
from fastapi import FastAPI, Query
from fastapi_mcp import FastApiMCP
from dotenv import load_dotenv

load_dotenv()

XRAY_BASE_URL = os.getenv("XRAY_BASE_URL", "http://localhost:8000")
LOCAL_API_URL  = os.getenv("LOCAL_API_URL",  "http://localhost:8001")
CONFLUENCE_PAGE_ID = os.getenv("CONFLUENCE_PAGE_ID", "2378907792")
PROXY = os.getenv("HTTP_PROXY", "http://http-proxy.porsche.org:3133")

ALIASES = {
    "fail": "FAIL",
    "america": "Testing NAR",
    "europe": "Testing ECE", "ece": "Testing ECE",
    "north america": "Testing NAR", "nar": "Testing NAR",
    "japan": "Testing JPN", "jpn": "Testing JPN",
    "korea": "Testing KOR", "kor": "Testing KOR",
    "taiwan": "Testing TWN", "twn": "Testing TWN",
    "hk": "Testing Hong Kong", "hong kong": "Testing Hong Kong",
    "hmi": "Core HMI / GBK", "gbk": "Core HMI / GBK",
    "media": "Media / Tuner (Entertainment)",
    "tuner": "Media / Tuner (Entertainment)",
    "entertainment": "Media / Tuner (Entertainment)",
    "app store": "App Store / 3rd Party",
    "phone connectivity": "Phone-Connectivity-SPI",
    "spi": "Phone-Connectivity-SPI",
    "applications": "WS Applications",
    "platform": "WS Platform",
    "system": "WS System",
    "failed": "FAIL", "failure": "FAIL", "failures": "FAIL",
    "passed": "PASS", "blocked": "BLOCKED", "aborted": "ABORTED",
}

PRODUCT_OWNERS = [
    "Hans Georg Wahl", "Deepak Illoth Veetil", "Elena Florez",
    "Martin Melle", "Regina Haeussermann",
]

METADATA = ["Total Scope", "Orphans", "Not Yet Planned", "Planned"]

def get_client(timeout=30):
    return httpx.Client(proxy=PROXY, timeout=timeout, verify=False)

def get_local_client(timeout=30):
    transport = httpx.HTTPTransport(proxy=None)
    return httpx.Client(
        timeout=timeout,
        verify=False,
        transport=transport,
        trust_env=False
    )
app = FastAPI(title="MLB TestPlan MCP", version="1.0.0")

# -- Tool 1: Parse keywords ----------------------------------------------------

@app.get("/parse-keywords", operation_id="parse_keywords",
         summary="Step 1: Parse user prompt and extract canonical keywords")
def parse_keywords(prompt: str = Query(..., description="Raw user prompt")):
    prompt_lower = prompt.lower()
    result = {
        "raw_prompt": prompt,
        "workstream": None,
        "working_group": None,
        "product_owner": None,
        "location": None,
        "metadata": None,
        "status": None,
        "test_plan_key": None,
        "kpm_id": None,
        "free_text": [],
    }
    matched_terms = set()
    for alias, canonical in ALIASES.items():
        if alias.lower() in prompt_lower:
            matched_terms.add(alias.lower())
            if canonical in ("WS Applications", "WS Platform", "WS System"):
                result["workstream"] = canonical
            elif canonical.startswith("Testing "):
                result["location"] = canonical
            elif canonical in ("PASS","FAIL","BLOCKED","ABORTED","TODO","EXECUTING"):
                result["status"] = canonical
            elif canonical in ("Total Scope","Orphans","Not Yet Planned","Planned"):
                result["metadata"] = canonical
            else:
                result["working_group"] = canonical
    for owner in PRODUCT_OWNERS:
        if owner.lower() in prompt_lower:
            result["product_owner"] = owner
            matched_terms.add(owner.lower())
            break
    for item in METADATA:
        if item.lower() in prompt_lower:
            result["metadata"] = item
            matched_terms.add(item.lower())
    kpm_match = re.search(r"\bKPM-\d+\b", prompt, re.IGNORECASE)
    if kpm_match:
        result["kpm_id"] = kpm_match.group(0).upper()
    jira_matches = re.findall(r"\b[A-Z][A-Z0-9]+-\d+\b", prompt)
    for key in jira_matches:
        if not key.upper().startswith("KPM-"):
            result["test_plan_key"] = key
            break
    reserved = set(a.lower() for a in ALIASES.keys())
    reserved.update({"pass","fail","blocked","aborted","todo","executing","total","scope","orphans","not","yet","planned"})
    for owner in PRODUCT_OWNERS:
        reserved.update(owner.lower().split())
    tokens = re.findall(r"\b[\w/-]+\b", prompt)
    free_text = []
    for token in tokens:
        if re.fullmatch(r"[A-Z][A-Z0-9]+-\d+", token):
            continue
        if token.lower() in reserved:
            continue
        free_text.append(token)
    result["free_text"] = free_text
    return result

# -- Tool 2: Confluence page ---------------------------------------------------

# NEW
@app.get("/confluence/page/{page_id}", operation_id="get_confluence_page",
         summary="Step 2: Retrieve Test Plan SOP page from Confluence")
def get_confluence_page(page_id: str = CONFLUENCE_PAGE_ID):
    with get_local_client(timeout=30) as client:
        resp = client.get(f"{LOCAL_API_URL}/page/{page_id}")
        if resp.status_code == 301 or resp.status_code == 302:
            redirect_url = resp.headers.get("location")
            resp = client.get(redirect_url)
        resp.raise_for_status()
        data = resp.json()
        return {
            "id": data.get("id"),
            "title": data.get("title"),
            "space": data.get("space"),
            "version": data.get("version"),
            "body": data.get("body"),
            "url": data.get("url"),
        }

# -- Tool 3: Get failed tests --------------------------------------------------
@app.get("/testplan/{test_plan_key}/failed-tests", operation_id="get_failed_tests",
         summary="Step 3: Get all tests with latestStatus=FAIL from Xray")
def get_failed_tests(test_plan_key: str, page: int = Query(1), limit: int = Query(100)):
    all_tests = []
    current_page = page
    with get_local_client(timeout=60) as client:
        while True:
            resp = client.get(
                f"{XRAY_BASE_URL}/xray/testplan/{test_plan_key}/tests",
                params={"page": current_page, "limit": limit}
            )
            resp.raise_for_status()
            data = resp.json()
            # extract items using same logic as your xray helper
            if isinstance(data, list):
                items = data
            elif isinstance(data, dict):
                items = next(
                    (data[k] for k in ("tests","testExecutions","data","results","items") if isinstance(data.get(k), list)),
                    []
                )
            else:
                items = []
            if not items:
                break
            all_tests.extend(items)
            if len(items) < limit:
                break
            current_page += 1

    # extract status using same logic as your extract_status_value helper
    def get_status(item):
        status = item.get("status") or item.get("latestStatus")
        if isinstance(status, str):
            return status.upper()
        if isinstance(status, dict):
            return (status.get("name") or status.get("value") or status.get("key") or "").upper()
        return ""

    # extract key using same logic as your extract_test_key helper
    def get_key(item):
        return (
            item.get("testKey")
            or item.get("key")
            or item.get("issueKey")
            or (item.get("test") or {}).get("key")
            or (item.get("test") or {}).get("testKey")
        )

    failed = [t for t in all_tests if get_status(t) == "FAIL"]

    return {
        "test_plan_key": test_plan_key,
        "total_fetched": len(all_tests),
        "total_failed": len(failed),
        "failed_keys": [get_key(t) for t in failed],
        "failed_tests": failed,
    }
# -- Tool 4: Get test run details + KPMs --------------------------------------
@app.get("/testplan/{test_plan_key}/testrun/{test_key}", operation_id="get_test_run_details",
         summary="Step 4: Get run details and extract KPM IDs from comments")
def get_test_run_details(test_plan_key: str, test_key: str):
    run_id = None
    matched_run = None

    with get_local_client(timeout=60) as client:
        for pg in range(1, 10):
            resp = client.get(
                f"{XRAY_BASE_URL}/xray/testruns",
                params={"testPlanKey": test_plan_key, "page": pg, "limit": 100}
            )
            if resp.status_code != 200:
                break
            data = resp.json()
            if isinstance(data, list):
                runs = data
            elif isinstance(data, dict):
                runs = next(
                    (data[k] for k in ("tests","testExecutions","data","results","items") if isinstance(data.get(k), list)),
                    []
                )
            else:
                runs = []
            if not runs:
                break
            for run in runs:
                # match using extract_test_key logic
                key = (
                    run.get("testKey")
                    or run.get("key")
                    or run.get("issueKey")
                    or (run.get("test") or {}).get("key")
                    or (run.get("test") or {}).get("testKey")
                )
                if key == test_key:
                    run_id = run.get("id")
                    matched_run = run
                    break
            if run_id:
                break

    if not run_id:
        return {"error": f"No run found for {test_key} in {test_plan_key}"}

    # get full run detail
    with get_local_client(timeout=30) as client:
        resp = client.get(f"{XRAY_BASE_URL}/xray/testrun/{run_id}")
        resp.raise_for_status()
        detail = resp.json()

    # extract comment using extract_comment_value logic
    comment = detail.get("comment")
    if isinstance(comment, dict):
        comment = comment.get("value") or comment.get("text") or ""
    comment = comment or ""

    # extract status using extract_status_value logic
    status = detail.get("status")
    if isinstance(status, dict):
        status = status.get("name") or status.get("value") or status.get("key")

    # extract KPM IDs
    kpm_ids = []
    for pattern in [r"KPM[:\s#-]+(\d+)", r"KPM Problem\s*-\s*(\d+)", r"kpmweb[^\s]*id=(\d+)"]:
        kpm_ids.extend(re.findall(pattern, comment, re.IGNORECASE))

    return {
        "test_key": test_key,
        "run_id": run_id,
        "status": status,
        "comment": comment,
        "kpm_ids": list(set(kpm_ids)),
        "raw": detail,
    }
# -- Tool 5: Full pipeline -----------------------------------------------------

@app.get("/testplan/{test_plan_key}/analyze", operation_id="analyze_failed_tests_with_kpms",
         summary="Steps 3+4 combined: all FAILs with KPM comments in one call")
def analyze_failed_tests_with_kpms(test_plan_key: str):
    failed = get_failed_tests(test_plan_key)
    if not failed["failed_keys"]:
        return {"message": "No FAIL tests found.", "test_plan_key": test_plan_key}
    results = [get_test_run_details(test_plan_key, key) for key in failed["failed_keys"]]
    kpm_summary = {}
    for r in results:
        for kpm in r.get("kpm_ids", []):
            kpm_summary.setdefault(kpm, []).append(r.get("test_key"))
    return {
        "test_plan_key": test_plan_key,
        "total_failed": failed["total_failed"],
        "results": results,
        "kpm_summary": kpm_summary,
    }

# -- Mount MCP + run -----------------------------------------------------------
# NEW
mcp = FastApiMCP(app)
mcp.mount(mount_path="/mcp")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8080)
