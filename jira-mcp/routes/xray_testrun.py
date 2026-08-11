"""xRay Test Run routes — test run management, iterations, step results, and status resets."""
from typing import Optional

from fastapi import APIRouter, Depends

from config import XRAY_BASE_URL
from utils.xray import (
    proxy_response as _proxy_response,
    raise_for_xray as _raise_for_xray,
    request_xray as _request_xray,
)
from routes.xray_models import (
    EvidenceFileInput,
    IterationUpdateModel,
    StepResultUpdateModel,
    TestRunCustomFieldValueModel,
    TestRunStatusUpdate,
    TestRunUpdateModel,
    TestRunsQueryModel,
)

router = APIRouter(tags=["xRay - Test Runs"])

from fastapi import Query as _Query


@router.get(
    "/xray/testrun",
    summary="Get step-level results for a test within an execution",
    operation_id="xray_get_test_run",
)
async def xray_get_test_run(
    test_exec_issue_key: str = _Query(..., alias="testExecIssueKey"),
    test_issue_key: str = _Query(..., alias="testIssueKey"),
):
    """
    Retrieve a specific Test Run by Test Execution key + Test key combination.

    Returns all Test Run details: status, steps/iterations, custom fields, evidence, defects.
    For iterated runs with dataset: shows iterations with parameter values resolved.
    For single-run tests: shows direct step results.

    Parameters: testExecIssueKey, testIssueKey (both required)
    """
    params = {
        "testExecIssueKey": test_exec_issue_key,
        "testIssueKey": test_issue_key,
    }
    resp = _request_xray("GET", f"{XRAY_BASE_URL}/api/testrun", params=params)
    _raise_for_xray(resp, f"GET testrun {test_exec_issue_key}/{test_issue_key}")
    return _proxy_response(resp)


@router.get(
    "/xray/testruns",
    summary="List xRay Test Runs",
    operation_id="xray_get_test_runs",
)
async def xray_get_test_runs(
    query: TestRunsQueryModel = Depends(),
):
    """
    Retrieve all Test Runs from a supported context configured by query parameters.

    Context options:
    - Test Execution: all tests run in an execution
    - Test Execution + Test: single test run in execution
    - Test Plan: all test runs across executions associated with plan
    - JQL Filter: test runs from filter results

    Returns: Paginated array of Test Run objects
    """
    params = {"limit": query.limit, "page": query.page}
    if query.resolved_test_exec_key:
        params["testExecKey"] = query.resolved_test_exec_key
    if query.testKey:
        params["testKey"] = query.testKey
    if query.testPlanKey:
        params["testPlanKey"] = query.testPlanKey
    if query.includeTestFields:
        params["includeTestFields"] = query.includeTestFields
    if query.savedFilterId:
        params["savedFilterId"] = query.savedFilterId
    resp = _request_xray("GET", f"{XRAY_BASE_URL}/api/testruns", params=params)
    _raise_for_xray(resp, "GET testruns")
    return _proxy_response(resp)


@router.get(
    "/xray/testrun/{run_id}",
    summary="Retrieve all step results from an xRay Test Run execution",
    operation_id="xray_get_test_run_by_id",
)
async def xray_get_test_run_by_id(run_id: str):
    """
    Retrieve a Test Run by its numeric ID with all execution details.

    Returns: test run with status, step results/iterations, custom fields, evidence, defects
    """
    resp = _request_xray("GET", f"{XRAY_BASE_URL}/api/testrun/{run_id}")
    _raise_for_xray(resp, f"GET testrun {run_id}")
    return _proxy_response(resp)


@router.put(
    "/xray/testrun/{run_id}",
    summary="Update an xRay Test Run",
    operation_id="xray_update_test_run",
)
async def xray_update_test_run(run_id: str, body: TestRunUpdateModel):
    """
    Update Test Run status, steps, evidence, custom fields, assignee.

    Field value formatting follows same rules as step creation (see xray_create_test_step).
    Delete custom field values by sending null or empty value.
    IMPORTANT: Cannot update steps if Run has multiple iterations.
    IMPORTANT: Cannot set to final status with empty required custom fields.

    Returns: Updated run ID and evidence IDs with any warnings
    """
    resp = _request_xray(
        "PUT",
        f"{XRAY_BASE_URL}/api/testrun/{run_id}",
        json=body.model_dump(exclude_none=True),
    )
    _raise_for_xray(resp, f"PUT testrun {run_id}")
    return _proxy_response(resp)


@router.put(
    "/xray/testrun/{run_id}/status",
    summary="Update the status of a Test Run",
    operation_id="xray_update_test_run_status",
)
async def xray_update_test_run_status(run_id: str, body: TestRunStatusUpdate):
    """
    Quickly update only the Test Run execution status without updating steps.

    Parameters: run_id, status (e.g. PASS, FAIL, TODO, EXECUTING), optional comment

    Returns: Updated run ID and evidence IDs
    """
    payload: dict = {"status": body.status}
    if body.comment:
        payload["comment"] = body.comment
    resp = _request_xray("PUT", f"{XRAY_BASE_URL}/api/testrun/{run_id}", json=payload)
    _raise_for_xray(resp, f"PUT testrun {run_id}")
    return _proxy_response(resp)


@router.get(
    "/xray/testrun/{run_id}/status",
    summary="Get the status of a Test Run",
    operation_id="xray_get_test_run_status",
)
async def xray_get_test_run_status(run_id: str):
    """
    Retrieve the current execution status of a Test Run.

    Returns: Status object with status value (PASS, FAIL, TODO, etc.)
    """
    resp = _request_xray("GET", f"{XRAY_BASE_URL}/api/testrun/{run_id}/status")
    _raise_for_xray(resp, f"GET testrun status {run_id}")
    return _proxy_response(resp)


@router.get(
    "/xray/testrun/{run_id}/customfield/{custom_field_id}",
    summary="Get an xRay Test Run custom field",
    operation_id="xray_get_test_run_custom_field",
)
async def xray_get_test_run_custom_field(run_id: str, custom_field_id: str):
    """
    Retrieve a Test Run custom field's current value.

    Returns: Custom field object with id, name, value (type depends on field type)
    """
    resp = _request_xray("GET", f"{XRAY_BASE_URL}/api/testrun/{run_id}/customfield/{custom_field_id}")
    _raise_for_xray(resp, f"GET testrun custom field {run_id}/{custom_field_id}")
    return _proxy_response(resp)


@router.put(
    "/xray/testrun/{run_id}/customfield/{custom_field_id}",
    summary="Update an xRay Test Run custom field",
    operation_id="xray_update_test_run_custom_field",
)
async def xray_update_test_run_custom_field(run_id: str, custom_field_id: str, body: TestRunCustomFieldValueModel):
    """
    Update a Test Run custom field value.

    Use field formatting rules: Toggle ('true'/'false'/'0'/'1'), Number (string),
    Select (option string or array), Date ('yyyy-MM-dd'), DateTime (UTC ISO).
    Delete by sending null or empty value. IMPORTANT: Cannot delete required fields.

    Returns: 204 No Content on success
    """
    resp = _request_xray(
        "PUT",
        f"{XRAY_BASE_URL}/api/testrun/{run_id}/customfield/{custom_field_id}",
        json=body.model_dump(exclude_none=True),
    )
    _raise_for_xray(resp, f"PUT testrun custom field {run_id}/{custom_field_id}")
    return _proxy_response(resp)


@router.get(
    "/xray/testrun/{run_id}/iteration/{iteration_id}",
    summary="Get an xRay Test Run iteration",
    operation_id="xray_get_test_run_iteration",
)
async def xray_get_test_run_iteration(run_id: str, iteration_id: str):
    """
    Retrieve a single iteration from a data-driven Test Run.

    Returns: iteration status, dataset parameters with values, resolved step details
    """
    resp = _request_xray("GET", f"{XRAY_BASE_URL}/api/testrun/{run_id}/iteration/{iteration_id}")
    _raise_for_xray(resp, f"GET testrun iteration {run_id}/{iteration_id}")
    return _proxy_response(resp)


@router.put(
    "/xray/testrun/{run_id}/iteration/{iteration_id}",
    summary="Update an xRay Test Run iteration",
    operation_id="xray_update_test_run_iteration",
)
async def xray_update_test_run_iteration(run_id: str, iteration_id: str, body: IterationUpdateModel):
    """
    Update a data-driven Test Run iteration's status and step execution results.

    Returns: Updated step results with their IDs
    """
    resp = _request_xray(
        "PUT",
        f"{XRAY_BASE_URL}/api/testrun/{run_id}/iteration/{iteration_id}",
        json=body.model_dump(exclude_none=True),
    )
    _raise_for_xray(resp, f"PUT testrun iteration {run_id}/{iteration_id}")
    return _proxy_response(resp)


@router.get(
    "/xray/testrun/{run_id}/iteration/{iteration_id}/steps",
    summary="List xRay Test Run iteration step results",
    operation_id="xray_get_test_run_iteration_steps",
)
async def xray_get_test_run_iteration_steps(run_id: str, iteration_id: str):
    """
    Retrieve all step results within a Test Run iteration.

    Returns: Array of step result objects with status, comment, evidence, defects
    """
    resp = _request_xray("GET", f"{XRAY_BASE_URL}/api/testrun/{run_id}/iteration/{iteration_id}/step")
    _raise_for_xray(resp, f"GET testrun iteration steps {run_id}/{iteration_id}")
    return _proxy_response(resp)


@router.get(
    "/xray/testrun/{run_id}/iteration/{iteration_id}/steps/{step_result_id}",
    summary="Get an xRay Test Run iteration step result",
    operation_id="xray_get_test_run_iteration_step",
)
async def xray_get_test_run_iteration_step(run_id: str, iteration_id: str, step_result_id: str):
    """
    Retrieve a single step result from a Test Run iteration.

    Returns: Step with index, fields, status, comment, evidence, defects, actual result
    """
    resp = _request_xray(
        "GET",
        f"{XRAY_BASE_URL}/api/testrun/{run_id}/iteration/{iteration_id}/step/{step_result_id}",
    )
    _raise_for_xray(resp, f"GET testrun iteration step {run_id}/{iteration_id}/{step_result_id}")
    return _proxy_response(resp)


@router.put(
    "/xray/testrun/{run_id}/iteration/{iteration_id}/steps/{step_result_id}",
    summary="Update an xRay Test Run iteration step result",
    operation_id="xray_update_test_run_iteration_step",
)
async def xray_update_test_run_iteration_step(
    run_id: str,
    iteration_id: str,
    step_result_id: str,
    body: StepResultUpdateModel,
):
    """Update a single step result within an iteration."""
    resp = _request_xray(
        "PUT",
        f"{XRAY_BASE_URL}/api/testrun/{run_id}/iteration/{iteration_id}/step/{step_result_id}",
        json=body.model_dump(exclude_none=True),
    )
    _raise_for_xray(resp, f"PUT testrun iteration step {run_id}/{iteration_id}/{step_result_id}")
    return _proxy_response(resp)


@router.get(
    "/xray/testrun/{run_id}/iteration/{iteration_id}/steps/{step_result_id}/status",
    summary="Get an xRay Test Run iteration step result status",
    operation_id="xray_get_test_run_iteration_step_status",
)
async def xray_get_test_run_iteration_step_status(run_id: str, iteration_id: str, step_result_id: str):
    """Retrieve the current step result status."""
    resp = _request_xray(
        "GET",
        f"{XRAY_BASE_URL}/api/testrun/{run_id}/iteration/{iteration_id}/step/{step_result_id}/status",
    )
    _raise_for_xray(resp, f"GET testrun iteration step status {run_id}/{iteration_id}/{step_result_id}")
    return _proxy_response(resp)


@router.put(
    "/xray/testrun/{run_id}/iteration/{iteration_id}/steps/{step_result_id}/status",
    summary="Update an xRay Test Run iteration step result status",
    operation_id="xray_update_test_run_iteration_step_status",
)
async def xray_update_test_run_iteration_step_status(
    run_id: str,
    iteration_id: str,
    step_result_id: str,
    status: str,
):
    """Update a step result status using the v2 status query contract."""
    resp = _request_xray(
        "PUT",
        f"{XRAY_BASE_URL}/api/testrun/{run_id}/iteration/{iteration_id}/step/{step_result_id}/status",
        params={"status": status},
    )
    _raise_for_xray(resp, f"PUT testrun iteration step status {run_id}/{iteration_id}/{step_result_id}")
    return _proxy_response(resp)


@router.get(
    "/xray/testrun/{run_id}/iteration/{iteration_id}/steps/{step_result_id}/attachments",
    summary="List evidences for an xRay Test Run iteration step result",
    operation_id="xray_get_test_run_iteration_step_attachments",
)
async def xray_get_test_run_iteration_step_attachments(run_id: str, iteration_id: str, step_result_id: str):
    """Retrieve step result evidences."""
    resp = _request_xray(
        "GET",
        f"{XRAY_BASE_URL}/api/testrun/{run_id}/iteration/{iteration_id}/step/{step_result_id}/attachment",
    )
    _raise_for_xray(resp, f"GET testrun iteration step attachments {run_id}/{iteration_id}/{step_result_id}")
    return _proxy_response(resp)


@router.post(
    "/xray/testrun/{run_id}/iteration/{iteration_id}/steps/{step_result_id}/attachments",
    summary="Add an evidence to an xRay Test Run iteration step result",
    operation_id="xray_add_test_run_iteration_step_attachment",
)
async def xray_add_test_run_iteration_step_attachment(
    run_id: str,
    iteration_id: str,
    step_result_id: str,
    body: EvidenceFileInput,
):
    """Add a step result evidence."""
    resp = _request_xray(
        "POST",
        f"{XRAY_BASE_URL}/api/testrun/{run_id}/iteration/{iteration_id}/step/{step_result_id}/attachment",
        json=body.model_dump(),
    )
    _raise_for_xray(resp, f"POST testrun iteration step attachment {run_id}/{iteration_id}/{step_result_id}")
    return _proxy_response(resp)


@router.delete(
    "/xray/testrun/{run_id}/iteration/{iteration_id}/steps/{step_result_id}/attachments",
    summary="Delete evidences by filename from an xRay Test Run iteration step result",
    operation_id="xray_delete_test_run_iteration_step_attachments_by_filename",
)
async def xray_delete_test_run_iteration_step_attachments_by_filename(
    run_id: str,
    iteration_id: str,
    step_result_id: str,
    filename: str,
):
    """Delete all evidences with the given filename."""
    resp = _request_xray(
        "DELETE",
        f"{XRAY_BASE_URL}/api/testrun/{run_id}/iteration/{iteration_id}/step/{step_result_id}/attachment",
        params={"filename": filename},
    )
    _raise_for_xray(resp, f"DELETE testrun iteration step attachments {run_id}/{iteration_id}/{step_result_id}")
    return _proxy_response(resp)


@router.delete(
    "/xray/testrun/{run_id}/iteration/{iteration_id}/steps/{step_result_id}/attachments/{attachment_id}",
    summary="Delete an evidence from an xRay Test Run iteration step result",
    operation_id="xray_delete_test_run_iteration_step_attachment",
)
async def xray_delete_test_run_iteration_step_attachment(
    run_id: str,
    iteration_id: str,
    step_result_id: str,
    attachment_id: str,
):
    """Delete a single step result evidence by attachment id."""
    resp = _request_xray(
        "DELETE",
        f"{XRAY_BASE_URL}/api/testrun/{run_id}/iteration/{iteration_id}/step/{step_result_id}/attachment/{attachment_id}",
    )
    _raise_for_xray(resp, f"DELETE testrun iteration step attachment {run_id}/{iteration_id}/{step_result_id}/{attachment_id}")
    return _proxy_response(resp)


@router.put(
    "/xray/testrunstatus/reset",
    summary="Reset xRay Test Run status",
    operation_id="xray_reset_test_run_status",
)
async def xray_reset_test_run_status(
    keys: Optional[str] = None,
    filter: Optional[str] = None,
    jql: Optional[str] = None,
):
    """Reset test run status using keys, filter, or JQL."""
    params = {k: v for k, v in {"keys": keys, "filter": filter, "jql": jql}.items() if v is not None}
    resp = _request_xray("PUT", f"{XRAY_BASE_URL}/api/testrunstatus/reset", params=params)
    _raise_for_xray(resp, "PUT testrunstatus reset")
    return _proxy_response(resp)


@router.put(
    "/xray/requirementstatus/reset",
    summary="Reset xRay Requirement status",
    operation_id="xray_reset_requirement_status",
)
async def xray_reset_requirement_status(
    keys: Optional[str] = None,
    filter: Optional[str] = None,
    jql: Optional[str] = None,
):
    """Reset requirement status using keys, filter, or JQL."""
    params = {k: v for k, v in {"keys": keys, "filter": filter, "jql": jql}.items() if v is not None}
    resp = _request_xray("PUT", f"{XRAY_BASE_URL}/api/requirementstatus/reset", params=params)
    _raise_for_xray(resp, "PUT requirementstatus reset")
    return _proxy_response(resp)
