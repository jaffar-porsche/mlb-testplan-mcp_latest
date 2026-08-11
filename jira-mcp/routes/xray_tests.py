"""xRay Test step routes — CRUD for manual test steps and their attachments."""
from typing import Optional

from fastapi import APIRouter, Body, Query

from config import XRAY_BASE_URL
from utils.xray import (
    build_step_fields as _build_step_fields,
    proxy_response as _proxy_response,
    raise_for_xray as _raise_for_xray,
    request_xray as _request_xray,
)
from routes.xray_models import EvidenceFileInput, TestStepCreate, TestStepUpdate

router = APIRouter(tags=["xRay - Tests"])


@router.get(
    "/xray/test/{test_key}/steps",
    summary="Retrieve all manual test steps for an xRay Test definition",
    operation_id="xray_get_test_steps",
)
async def xray_get_test_steps(
    test_key: str,
    testVersion: Optional[str] = Query(None, description="Optional test version identifier (for example v1)"),
):
    """
    Retrieve all manual test steps defined for a Test issue.

    Returns all steps with their action, data, expected result fields, and attachments.
    Test Step fields are identified by name and can be of type:
    - Data (Toggle, Number, Date, Date Time fields)
    - Option (Single Select, Multiple Select, Radio Button fields)
    - Wiki (Native fields, Single/Multiple Line fields)

    Parameters:
    - test_key: Jira issue key of the Test (e.g. PROJ-123)
    - testVersion: Optional test version identifier when a specific version must be targeted

    Returns: Array of steps with id, index, fields (keyed by name), attachments array
    """
    params = {"testVersion": testVersion} if testVersion is not None else None
    resp = _request_xray(
        "GET",
        f"{XRAY_BASE_URL}/api/test/{test_key}/steps",
        params=params,
    )
    _raise_for_xray(resp, f"GET test steps {test_key}")
    return _proxy_response(resp)


@router.post(
    "/xray/test/{test_key}/steps",
    summary="Create a new manual test step for an xRay Test",
    operation_id="xray_create_test_step",
)
async def xray_create_test_step(
    test_key: str,
    testVersion: str = Query(..., description="Test version identifier (e.g. manual_1)"),
    step: TestStepCreate = Body(...),
):
    """
    Create a new manual test step for a Test issue.

    Field value formatting rules:
    - Toggle: 'true', 'false', '0', or '1'
    - Number: string containing number (e.g. '320', '320.5')
    - Single Select/Radio: single option string (not case-sensitive)
    - Multiple Select: array of option strings (not case-sensitive)
    - Date: 'yyyy-MM-dd' format
    - DateTime: UTC 'yyyy-MM-dd'T'HH:mm'Z' format
    ALL REQUIRED FIELDS MUST BE PROVIDED.

    Parameters:
    - test_key: Jira issue key of the Test (e.g. PROJ-123)
    - test_version: Test version identifier (e.g. manual_1)
    - step: Step with action (required), data, result, attachments

    Returns: Created step ID and attachment IDs, plus warnings if any
    """
    fields = _build_step_fields(step.action, step.data, step.result)
    if step.call_test_issue_key and not fields and not step.attachments:
        payload: dict | str = step.call_test_issue_key
    else:
        payload = {"fields": fields}
        if step.attachments:
            payload["attachments"] = [attachment.model_dump() for attachment in step.attachments]
    resp = _request_xray(
        "POST",
        f"{XRAY_BASE_URL}/api/test/{test_key}/steps",
        params={"testVersion": testVersion},
        json=payload,
    )
    _raise_for_xray(resp, f"POST test step {test_key}")
    return _proxy_response(resp)


@router.get(
    "/xray/test/{test_key}/steps/{step_id}",
    summary="Retrieve a single test step by ID with its action, data, and expected result",
    operation_id="xray_get_test_step",
)
async def xray_get_test_step(test_key: str, step_id: int):
    """
    Retrieve a single manual test step by its numeric ID.

    Returns: Step object with id, index, fields keyed by name, attachments
    """
    resp = _request_xray("GET", f"{XRAY_BASE_URL}/api/test/{test_key}/steps/{step_id}")
    _raise_for_xray(resp, f"GET test step {test_key}/{step_id}")
    return _proxy_response(resp)


@router.put(
    "/xray/test/{test_key}/steps/{step_id}",
    summary="Update action, data, or expected result of a test step",
    operation_id="xray_update_test_step",
)
async def xray_update_test_step(test_key: str, step_id: str, step: TestStepUpdate):
    """
    Update an existing manual test step fields and attachments.

    Field value formatting follows same rules as step creation.
    Delete field by sending empty value ('', [], null). REQUIRED FIELDS: cannot be empty.

    Parameters: test_key, step_id, updated step (fields, attachments to add/remove)

    Returns: Updated step ID and attachment IDs with warnings
    """
    fields = _build_step_fields(step.action, step.data, step.result)
    if step.call_test_issue_key and not fields and not step.attachments_to_add and not step.attachments_to_remove:
        payload: dict | str = step.call_test_issue_key
    else:
        payload = {}
        if fields:
            payload["fields"] = fields
        if step.attachments_to_add or step.attachments_to_remove:
            payload["attachments"] = {}
            if step.attachments_to_add:
                payload["attachments"]["add"] = [attachment.model_dump() for attachment in step.attachments_to_add]
            if step.attachments_to_remove:
                payload["attachments"]["remove"] = step.attachments_to_remove
    resp = _request_xray(
        "PUT",
        f"{XRAY_BASE_URL}/api/test/{test_key}/steps/{step_id}",
        json=payload,
    )
    _raise_for_xray(resp, f"PUT test step {test_key}/{step_id}")
    return _proxy_response(resp)


@router.delete(
    "/xray/test/{test_key}/steps/{step_id}",
    summary="Delete a step from an xRay Test",
    operation_id="xray_delete_test_step",
)
async def xray_delete_test_step(test_key: str, step_id: str):
    """
    Delete a manual test step from a Test issue.

    Step and all data including attachments are permanently removed.

    Returns: 204 No Content on success
    """
    resp = _request_xray("DELETE", f"{XRAY_BASE_URL}/api/test/{test_key}/steps/{step_id}")
    _raise_for_xray(resp, f"DELETE test step {test_key}/{step_id}")
    return _proxy_response(resp)


@router.get(
    "/xray/test/{test_key}/steps/{step_id}/attachments",
    summary="List attachments of an xRay Test step",
    operation_id="xray_get_test_step_attachments",
)
async def xray_get_test_step_attachments(test_key: str, step_id: int):
    """
    Retrieve all attachments from a test step.

    Returns: Array of file objects with id, filename, contentType, URL
    """
    resp = _request_xray("GET", f"{XRAY_BASE_URL}/api/test/{test_key}/steps/{step_id}/attachments")
    _raise_for_xray(resp, f"GET test step attachments {test_key}/{step_id}")
    return _proxy_response(resp)


@router.delete(
    "/xray/test/{test_key}/steps/{step_id}/attachments/{attachment_id}",
    summary="Delete an attachment from an xRay Test step",
    operation_id="xray_delete_test_step_attachment",
)
async def xray_delete_test_step_attachment(test_key: str, step_id: int, attachment_id: int):
    """
    Delete a single attachment from a test step.

    Returns: 204 No Content on success
    """
    resp = _request_xray(
        "DELETE",
        f"{XRAY_BASE_URL}/api/test/{test_key}/steps/{step_id}/attachment/{attachment_id}",
    )
    _raise_for_xray(resp, f"DELETE test step attachment {test_key}/{step_id}/{attachment_id}")
    return _proxy_response(resp)
