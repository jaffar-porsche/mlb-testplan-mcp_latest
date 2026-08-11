"""xRay Test Plan routes — test plan management and async aggregation job."""
import asyncio
import uuid
from typing import Any, Optional

from fastapi import APIRouter, Body, HTTPException

from config import XRAY_BASE_URL
from utils.xray import (
    extract_comment_value as _extract_comment_value,
    extract_execution_datetime as _extract_execution_datetime,
    extract_execution_key as _extract_execution_key,
    extract_items as _extract_items,
    extract_run_datetime as _extract_run_datetime,
    extract_status_value as _extract_status_value,
    extract_test_key as _extract_test_key,
    get_testexec_tests as _get_testexec_tests,
    get_testplan_tests as _get_testplan_tests,
    proxy_response as _proxy_response,
    raise_for_xray as _raise_for_xray,
    request_xray as _request_xray,
)
from routes.xray_models import KeysBody

router = APIRouter(tags=["xRay - Test Plans"])

AGGREGATE_PAGE_LIMIT = 100
AGGREGATE_MAX_PAGES = 200
AGGREGATE_POLL_AFTER_SECONDS = 2
AGGREGATE_MAX_CONCURRENT_EXECUTIONS = 8

JOB_STORE: dict[str, dict[str, Any]] = {}


def _set_job_progress(job_id: str, **progress: Any):
    job = JOB_STORE.get(job_id)
    if not job:
        return
    job["progress"] = progress


#jaf-(old+new)
async def run_aggregation_job(job_id: str, plan_key: str):
    """Optimized aggregation: fast runs API + enriched execution metadata."""

    job = JOB_STORE.get(job_id)
    if not job:
        return

    try:
        job["status"] = "processing"

        tests_items: list[dict[str, Any]] = []
        all_runs: list[dict[str, Any]] = []

        # -----------------------------
        # Step 1: Fetch tests (metadata)
        # -----------------------------
        for page in range(1, AGGREGATE_MAX_PAGES + 1):
            _set_job_progress(job_id, stage="fetching_tests", page=page)

            resp = await asyncio.to_thread(
                _get_testplan_tests,
                plan_key,
                page,
                AGGREGATE_PAGE_LIMIT,
            )

            page_items = _extract_items(resp.json())
            if not page_items:
                break

            tests_items.extend([i for i in page_items if isinstance(i, dict)])

            if len(page_items) < AGGREGATE_PAGE_LIMIT:
                break

        # -----------------------------
        # Step 2: Fetch ALL runs (FAST)
        # -----------------------------
        for page in range(1, AGGREGATE_MAX_PAGES + 1):
            _set_job_progress(job_id, stage="fetching_runs", page=page)

            resp = await asyncio.to_thread(
                _request_xray,
                "GET",
                f"{XRAY_BASE_URL}/api/testruns",
                {
                    "testPlanKey": plan_key,
                    "page": page,
                    "limit": AGGREGATE_PAGE_LIMIT,
                },
            )

            await asyncio.to_thread(
                _raise_for_xray,
                resp,
                f"GET testruns for plan {plan_key}",
            )

            page_items = _extract_items(resp.json())
            if not page_items:
                break

            all_runs.extend([i for i in page_items if isinstance(i, dict)])

            if len(page_items) < AGGREGATE_PAGE_LIMIT:
                break

        # -----------------------------
        # Step 3: Collect execution keys
        # -----------------------------
        execution_keys = {
            run.get("testExecKey") or run.get("testExecutionKey")
            for run in all_runs
            if run.get("testExecKey") or run.get("testExecutionKey")
        }

        execution_meta: dict[str, dict[str, Any]] = {}

        # Fetch execution metadata (batched, not per run)
        for exec_key in execution_keys:
            try:
                resp = await asyncio.to_thread(
                    _request_xray,
                    "GET",
                    f"{XRAY_BASE_URL}/api/testexecution/{exec_key}",
                )
                await asyncio.to_thread(
                    _raise_for_xray,
                    resp,
                    f"GET execution {exec_key}",
                )

                data = resp.json()

                execution_meta[exec_key] = {
                    "summary": data.get("summary"),
                    "executionDate": data.get("executionDate"),
                }

            except Exception:
                # Don't fail entire job for one execution
                execution_meta[exec_key] = {}

        # -----------------------------
        # Step 4: Build latest run per test
        # -----------------------------
        latest_run_by_test: dict[str, dict[str, Any]] = {}
        execution_count_by_test: dict[str, int] = {}

        for run in all_runs:
            test_key = _extract_test_key(run)
            if not test_key:
                continue

            execution_count_by_test[test_key] = (
                execution_count_by_test.get(test_key, 0) + 1
            )

            run_date_raw, run_dt = _extract_run_datetime(run)
            exec_key = run.get("testExecKey") or run.get("testExecutionKey")

            candidate_order = run.get("id", 0)

            current = latest_run_by_test.get(test_key)
            should_replace = False

            if not current:
                should_replace = True
            elif run_dt and current.get("dt"):
                should_replace = run_dt > current["dt"]
            elif run_dt and not current.get("dt"):
                should_replace = True
            elif not run_dt and not current.get("dt"):
                should_replace = candidate_order > current.get("order", 0)

            if should_replace:
                exec_info = execution_meta.get(exec_key, {})

                latest_run_by_test[test_key] = {
                    "testExecutionKey": exec_key,
                    "testExecutionSummary": exec_info.get("summary"),
                    "executionDate": run_date_raw or exec_info.get("executionDate"),
                    "latestRunStatus": _extract_status_value(run),
                    "comment": _extract_comment_value(run),
                    "dt": run_dt,
                    "order": candidate_order,
                }

        # -----------------------------
        # Step 5: Map tests
        # -----------------------------
        tests_by_key: dict[str, dict[str, Any]] = {}

        for item in tests_items:
            test_key = _extract_test_key(item)
            if test_key and test_key not in tests_by_key:
                tests_by_key[test_key] = item

        # -----------------------------
        # Step 6: Build final result
        # -----------------------------
        status_counts: dict[str, int] = {}
        per_test_latest_status: list[dict[str, Any]] = []

        for test_key in sorted(tests_by_key.keys()):
            test_item = tests_by_key[test_key]
            latest_run = latest_run_by_test.get(test_key)

            latest_status = (
                test_item.get("latestStatus")
                or _extract_status_value(test_item)
                or (latest_run or {}).get("latestRunStatus")
            )

            if latest_status:
                status_counts[latest_status] = (
                    status_counts.get(latest_status, 0) + 1
                )

            per_test_latest_status.append(
                {
                    "testKey": test_key,
                    "summary": test_item.get("summary"),
                    "testType": test_item.get("testType"),
                    "latestStatus": latest_status,
                    "comment": (latest_run or {}).get("comment"),
                    "executionCount": execution_count_by_test.get(test_key, 0),
                    "testExecutionKey": (latest_run or {}).get("testExecutionKey"),
                    "testExecutionSummary": (latest_run or {}).get("testExecutionSummary"),
                    "executionDate": (latest_run or {}).get("executionDate"),
                }
            )

        # -----------------------------
        # Step 7: Finalize job
        # -----------------------------
        job["status"] = "completed"
        job["result"] = {
            "testPlanKey": plan_key,
            "summary": {
                "totalTests": len(tests_by_key),
                "statusCounts": status_counts,
            },
            "perTestLatestStatus": per_test_latest_status,
        }

    except Exception as exc:
        job["status"] = "failed"
        job["error"] = str(exc)

# ---------------------------------------------------------------------------
# Test Plan endpoints
# ---------------------------------------------------------------------------

@router.post(
    "/xray/testplan/{plan_key}/aggregate",
    summary="Start asynchronous aggregation for an xRay Test Plan",
    operation_id="xray_start_test_plan_aggregation",
)
async def xray_start_test_plan_aggregation(plan_key: str):
    """
    Start an asynchronous background job to aggregate all Tests and Test Executions under a Test Plan.

    Use the returned jobId with xray_get_test_plan_aggregation_status to check progress.

    Returns: jobId for polling, status='processing', pollAfterSeconds interval
    """
    job_id = str(uuid.uuid4())
    JOB_STORE[job_id] = {
        "jobId": job_id,
        "planKey": plan_key,
        "status": "queued",
        "progress": {},
    }
    asyncio.create_task(run_aggregation_job(job_id, plan_key))
    return {
        "jobId": job_id,
        "status": "processing",
        "pollAfterSeconds": AGGREGATE_POLL_AFTER_SECONDS,
    }


@router.get(
    "/xray/testplan/{plan_key}/aggregate/{job_id}",
    summary="Get asynchronous aggregation job status for an xRay Test Plan",
    operation_id="xray_get_test_plan_aggregation_status",
)
async def xray_get_test_plan_aggregation_status(plan_key: str, job_id: str):
    """
    Poll the status of a Test Plan aggregation job.

    Returns 'processing' with progress until complete, then 'completed' with result.
    Use pollAfterSeconds to determine safe polling interval.

    Returns: status (processing/completed/failed), progress, result on completion
    """
    job = JOB_STORE.get(job_id)
    if not job or job.get("planKey") != plan_key:
        raise HTTPException(status_code=404, detail=f"Aggregation job not found for {plan_key}/{job_id}")

    status = job.get("status")
    if status == "completed":
        return {
            "status": "completed",
            "result": job.get("result"),
        }
    if status == "failed":
        return {
            "status": "failed",
            "error": job.get("error", "Aggregation job failed"),
            "progress": job.get("progress", {}),
            "pollAfterSeconds": AGGREGATE_POLL_AFTER_SECONDS,
        }

    return {
        "status": "processing",
        "progress": job.get("progress", {}),
        "pollAfterSeconds": AGGREGATE_POLL_AFTER_SECONDS,
    }


@router.get(
    "/xray/testplan/{plan_key}/tests",
    summary="List all tests defined in an xRay Test Plan",
    operation_id="xray_get_test_plan_tests",
)
async def xray_get_test_plan_tests(
    plan_key: str,
    page: Optional[int] = 1,
    limit: Optional[int] = 50,
):
    """
    Retrieve all Tests defined in a Test Plan (paginated).

    Returns: Array of Test objects with their test keys, summaries, types

    Parameters: plan_key, page (1-indexed), limit (max 100)
    """
    resp = _get_testplan_tests(plan_key=plan_key, page=page, limit=limit)
    return _proxy_response(resp)


@router.post(
    "/xray/testplan/{plan_key}/tests",
    summary="Add Tests or Test Sets to an xRay Test Plan",
    operation_id="xray_add_test_plan_tests",
)
async def xray_add_test_plan_tests(
    plan_key: str,
    body: KeysBody = Body(...),
):
    """
    Associate one or more Tests or Test Sets with a Test Plan.

    Parameters: plan_key, keys (array of test/test-set issue keys)

    Returns: Success/error response
    """
    resp = _request_xray("POST", f"{XRAY_BASE_URL}/api/testplan/{plan_key}/test", json=body.keys)
    _raise_for_xray(resp, f"POST testplan tests {plan_key}")
    return _proxy_response(resp)

# Source - https://stackoverflow.com/a/7696966
# Posted by Petr Viktorin, modified by community. See post 'Timeline' for change history
# Retrieved 2026-04-23, License - CC BY-SA 4.0

'''
This is a multiline
comment.


'''

@router.delete(
    "/xray/testplan/{plan_key}/tests/{test_key}",
    summary="Remove a Test from an xRay Test Plan",
    operation_id="xray_remove_test_plan_test",
)
async def xray_remove_test_plan_test(plan_key: str, test_key: str):
    """
    Remove a Test from a Test Plan.

    Returns: 204 No Content on success
    """
    resp = _request_xray("DELETE", f"{XRAY_BASE_URL}/api/testplan/{plan_key}/test/{test_key}")
    _raise_for_xray(resp, f"DELETE testplan test {plan_key}/{test_key}")
    return _proxy_response(resp)


@router.get(
    "/xray/testplan/{plan_key}/testexecutions",
    summary="List Test Executions in an xRay Test Plan",
    operation_id="xray_get_test_plan_test_executions",
)
async def xray_get_test_plan_test_executions(
    plan_key: str,
    page: Optional[int] = 1,
    limit: Optional[int] = 50,
):
    """
    Retrieve all Test Execution issues associated with a Test Plan (paginated).

    Returns: Array of Test Execution objects with their keys and metadata
    """
    params = {"page": page, "limit": min(limit, 100)}
    resp = _request_xray("GET", f"{XRAY_BASE_URL}/api/testplan/{plan_key}/testexecution", params=params)
    _raise_for_xray(resp, f"GET testplan test executions {plan_key}")
    return _proxy_response(resp)


@router.post(
    "/xray/testplan/{plan_key}/testexecutions",
    summary="Add Test Executions to an xRay Test Plan",
    operation_id="xray_add_test_plan_test_executions",
)
async def xray_add_test_plan_test_executions(
    plan_key: str,
    body: KeysBody = Body(...),
):
    """
    Associate one or more Test Executions with a Test Plan.

    Parameters: plan_key, keys (array of test-execution issue keys)

    Returns: Success/error response
    """
    resp = _request_xray("POST", f"{XRAY_BASE_URL}/api/testplan/{plan_key}/testexecution", json=body.keys)
    _raise_for_xray(resp, f"POST testplan test executions {plan_key}")
    return _proxy_response(resp)


@router.delete(
    "/xray/testplan/{plan_key}/testexecutions/{exec_key}",
    summary="Remove a Test Execution from an xRay Test Plan",
    operation_id="xray_remove_test_plan_test_execution",
)
async def xray_remove_test_plan_test_execution(plan_key: str, exec_key: str):
    """
    Remove a Test Execution from a Test Plan.

    Returns: 204 No Content on success
    """
    resp = _request_xray("DELETE", f"{XRAY_BASE_URL}/api/testplan/{plan_key}/testexecution/{exec_key}")
    _raise_for_xray(resp, f"DELETE testplan test execution {plan_key}/{exec_key}")
    return _proxy_response(resp)
