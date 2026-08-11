"""Shared xRay route helper functions."""
from datetime import datetime
from typing import Optional

from fastapi import HTTPException, Response
from fastapi.responses import JSONResponse

from client import jira
from config import XRAY_BASE_URL
from xray_client import xray


def raise_for_xray(response, context: str):
    """Raise HTTPException with xRay error details if the response is not 2xx."""
    if response.status_code >= 400:
        try:
            detail = response.json()
        except Exception:
            detail = response.text or response.reason
        raise HTTPException(status_code=response.status_code, detail=f"{context}: {detail}")


def proxy_response(response):
    """Return an HTTP response that mirrors the upstream xRay payload/status."""
    content_type = response.headers.get("content-type", "")
    if "application/json" in content_type.lower():
        if not response.content:
            return Response(status_code=response.status_code)
        try:
            return JSONResponse(status_code=response.status_code, content=response.json())
        except Exception:
            return Response(content=response.content, status_code=response.status_code, media_type="application/json")

    media_type = content_type.split(";")[0] if content_type else None
    if not response.content:
        return Response(status_code=response.status_code, media_type=media_type)
    return Response(content=response.content, status_code=response.status_code, media_type=media_type)


def request_xray(
    method: str,
    url: str,
    params: Optional[dict] = None,
    json: Optional[dict | list | str] = None,
):
    """Send a request to the xRay v2 API without version fallback."""
    method = method.upper()
    if method == "GET":
        return xray.get(url, params=params)
    if method == "POST":
        return xray.post(url, params=params, json=json)
    if method == "PUT":
        return xray.put(url, params=params, json=json)
    if method == "DELETE":
        return xray.delete(url, params=params)
    raise ValueError(f"Unsupported method: {method}")


def get_xray(url: str, params: Optional[dict] = None):
    """Send a GET request to the xRay v2 API."""
    return request_xray("GET", url, params=params)


def get_testruns(
    test_exec_key: Optional[str] = None,
    test_plan_key: Optional[str] = None,
    test_set_key: Optional[str] = None,
    page: int = 1,
    limit: int = 50,
):
    """Get Test Runs from xRay using the supported context query parameters."""
    params = {"page": page, "limit": min(limit, 100)}
    if test_exec_key:
        params["testExecKey"] = test_exec_key
    if test_plan_key:
        params["testPlanKey"] = test_plan_key
    if test_set_key:
        params["testSetKey"] = test_set_key

    resp = get_xray(f"{XRAY_BASE_URL}/api/testruns", params=params)
    raise_for_xray(resp, "GET testruns")
    return resp


def get_testplan_tests(
    plan_key: str,
    page: int = 1,
    limit: int = 50,
):
    """Get Tests linked to a Test Plan using xRay test plan endpoints."""
    params = {"page": page, "limit": min(limit, 100)}
    resp = get_xray(f"{XRAY_BASE_URL}/api/testplan/{plan_key}/test", params=params)
    raise_for_xray(resp, f"GET testplan tests {plan_key}")
    return resp


def get_testexec_tests(
    exec_key: str,
    page: int = 1,
    limit: int = 50,
    detailed: Optional[bool] = None,
):
    """Get Tests linked to a Test Execution using xRay test execution endpoints."""
    params = {"page": page, "limit": min(limit, 100)}
    if detailed is not None:
        params["detailed"] = str(detailed).lower()
    resp = get_xray(f"{XRAY_BASE_URL}/api/testexec/{exec_key}/test", params=params)
    raise_for_xray(resp, f"GET test execution tests {exec_key}")
    return resp



def build_step_fields(action: Optional[str], data: Optional[str], result: Optional[str]) -> dict:
    """Build xRay v2 step fields payload from simplified MCP input."""
    fields: dict[str, str] = {}
    if action is not None:
        fields["Action"] = action
    if data is not None:
        fields["Data"] = data
    if result is not None:
        fields["Expected Result"] = result
    return fields


def extract_items(payload: object):
    """Extract list payloads from common xRay response envelope shapes."""
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        for key in ("tests", "testExecutions", "data", "results", "items"):
            value = payload.get(key)
            if isinstance(value, list):
                return value
    return []


def parse_datetime(value: Optional[str]):
    """Parse ISO date/time strings into datetime objects."""
    if not value:
        return None
    candidate = value.strip()
    if candidate.endswith("Z"):
        candidate = candidate[:-1] + "+00:00"
    try:
        return datetime.fromisoformat(candidate)
    except ValueError:
        return None


def extract_test_key(item: dict):
    """Extract a test key from known xRay payload shapes."""
    return (
        item.get("testKey")
        or item.get("key")
        or item.get("issueKey")
        or (item.get("test") or {}).get("key")
        or (item.get("test") or {}).get("testKey")
    )


def extract_execution_key(item: dict):
    """Extract a test execution key from known xRay payload shapes."""
    return item.get("key") or item.get("testExecKey") or item.get("testExecutionKey")


def extract_execution_datetime(item: dict):
    """Pick the most suitable execution datetime field from an execution payload."""
    for key in ("finishDate", "executionDate", "endDate", "updated", "created", "startDate"):
        parsed = parse_datetime(item.get(key))
        if parsed:
            return item.get(key), parsed
    return None, None


def extract_status_value(item: dict):
    """Extract run status from known xRay payload shapes."""
    status = item.get("status")
    if isinstance(status, str):
        return status
    if isinstance(status, dict):
        return status.get("name") or status.get("value") or status.get("key")
    return None


def extract_comment_value(item: dict):
    """Extract comment text from known xRay payload shapes."""
    comment = item.get("comment")
    if isinstance(comment, str):
        return comment
    if isinstance(comment, dict):
        return comment.get("value") or comment.get("text")
    return None


def extract_run_datetime(item: dict):
    """Pick the most suitable timestamp from a test run payload."""
    for key in ("finish", "end", "updated", "created", "start", "executionDate", "finishDate"):
        parsed = parse_datetime(item.get(key))
        if parsed:
            return item.get(key), parsed
    return None, None


def get_jira_issue_metadata(issue_key: str):
    """Get test metadata from Jira issue endpoint using the test issue key."""
    try:
        issue = jira.issue(issue_key)
    except Exception:
        return {}

    fields = getattr(issue, "fields", None)
    if not fields:
        return {}

    issuetype = getattr(fields, "issuetype", None)
    return {
        "summary": getattr(fields, "summary", None),
        "testType": getattr(issuetype, "name", None) if issuetype else None,
    }


__all__ = [
    "build_step_fields",
    "extract_comment_value",
    "extract_execution_datetime",
    "extract_execution_key",
    "extract_items",
    "extract_run_datetime",
    "extract_status_value",
    "extract_test_key",
    "get_jira_issue_metadata",
    "get_testexec_tests",
    "get_testplan_tests",
    "get_testruns",
    "get_xray",
    "proxy_response",
    "raise_for_xray",
    "request_xray",
]