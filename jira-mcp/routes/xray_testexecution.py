"""xRay Test Execution routes — listing and retrieving test executions."""
from typing import Optional

from fastapi import APIRouter

from utils.xray import (
    get_testexec_tests as _get_testexec_tests,
    proxy_response as _proxy_response,
)

router = APIRouter(tags=["xRay - Test Executions"])


@router.get(
    "/xray/testexecution/{exec_key}",
    summary="Get xRay Test Execution details with all execution metadata",
    operation_id="xray_get_test_execution",
)
async def xray_get_test_execution(exec_key: str):
    """
    Retrieve metadata and all Test Runs for a Test Execution issue.

    Returns Test Execution details and paginated list of all Test Runs within it.
    Each Test Run includes status, test key, assignee, step results/iterations.

    Parameters: exec_key - Jira issue key of Test Execution (e.g. PROJ-789)
    """
    resp = _get_testexec_tests(exec_key=exec_key, page=1, limit=100)
    return _proxy_response(resp)


@router.get(
    "/xray/testexecution/{exec_key}/tests",
    summary="List all test runs and step execution results in an xRay Test Execution",
    operation_id="xray_get_test_execution_tests",
)
async def xray_get_test_execution_tests(
    exec_key: str,
    page: Optional[int] = 1,
    limit: Optional[int] = 50,
    detailed: Optional[bool] = False,
):
    """
    Retrieve all Test Runs within a Test Execution.

    Each Test Run includes: status, test/execution keys, assignee, timestamps,
    step results (or iterations for data-driven tests), custom fields, defects, evidence.

    Parameters:
    - exec_key: Jira issue key of Test Execution (e.g. PROJ-789)
    - page: Page number for pagination (1-indexed, default: 1)
    - limit: Results per page, max 100 (default: 50)
    - detailed: Include full step details (default: false)

    Returns: Array of Test Run objects with complete execution data
    """
    resp = _get_testexec_tests(exec_key=exec_key, page=page, limit=limit, detailed=detailed)
    return _proxy_response(resp)
