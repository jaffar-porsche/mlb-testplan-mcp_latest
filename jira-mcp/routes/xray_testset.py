"""xRay Test Set routes — list/add/remove tests associated with a Test Set."""
from typing import Optional

from fastapi import APIRouter, Body

from config import XRAY_BASE_URL
from utils.xray import (
    proxy_response as _proxy_response,
    raise_for_xray as _raise_for_xray,
    request_xray as _request_xray,
)
from routes.xray_models import KeysBody

router = APIRouter(tags=["xRay - Test Sets"])


@router.get(
    "/xray/testset/{set_key}/tests",
    summary="List Tests in an xRay Test Set",
    operation_id="xray_get_test_set_tests",
)
async def xray_get_test_set_tests(
    set_key: str,
    page: Optional[int] = 1,
    limit: Optional[int] = 50,
):
    """
    Retrieve the list of Tests associated with a Test Set.

    Parameters:
    - set_key: Jira issue key of the Test Set (e.g. PROJ-321)
    - page: Page number for pagination (default: 1)
    - limit: Number of results per page (default: 50, max: 100)
    """
    params = {"page": page, "limit": min(limit, 100)}
    resp = _request_xray("GET", f"{XRAY_BASE_URL}/api/testset/{set_key}/test", params=params)
    _raise_for_xray(resp, f"GET test set tests {set_key}")
    return _proxy_response(resp)


@router.post(
    "/xray/testset/{set_key}/tests",
    summary="Add Tests to an xRay Test Set",
    operation_id="xray_add_test_set_tests",
)
async def xray_add_test_set_tests(
    set_key: str,
    body: KeysBody = Body(...),
):
    """
    Associate one or more Tests with a Test Set.

    Parameters: set_key, keys (array of test issue keys)

    Returns: Success/error response
    """
    resp = _request_xray("POST", f"{XRAY_BASE_URL}/api/testset/{set_key}/test", json=body.keys)
    _raise_for_xray(resp, f"POST test set tests {set_key}")
    return _proxy_response(resp)


@router.delete(
    "/xray/testset/{set_key}/tests/{test_key}",
    summary="Remove a Test from an xRay Test Set",
    operation_id="xray_remove_test_set_test",
)
async def xray_remove_test_set_test(set_key: str, test_key: str):
    """
    Remove a Test from a Test Set.

    Returns: 204 No Content on success
    """
    resp = _request_xray("DELETE", f"{XRAY_BASE_URL}/api/testset/{set_key}/test/{test_key}")
    _raise_for_xray(resp, f"DELETE test set test {set_key}/{test_key}")
    return _proxy_response(resp)
