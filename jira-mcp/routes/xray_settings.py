"""xRay Settings & metadata routes — license, statuses, datasets, project config, and issue types."""
from typing import Optional

from fastapi import APIRouter, Body, File, Query, UploadFile

from config import XRAY_BASE_URL
from utils.xray import (
    proxy_response as _proxy_response,
    raise_for_xray as _raise_for_xray,
    request_xray as _request_xray,
)
from routes.xray_models import ProjectKeysBody
from xray_client import xray

router = APIRouter(tags=["xRay - Settings"])


@router.get(
    "/xray/statuses",
    summary="Get configured xRay test statuses",
    operation_id="xray_get_test_statuses",
)
async def xray_get_test_statuses():
    """
    Retrieve all test statuses configured in this xRay instance
    (e.g. PASS, FAIL, TODO, EXECUTING and any custom statuses).
    """
    resp = _request_xray("GET", f"{XRAY_BASE_URL}/api/settings/teststatuses")
    _raise_for_xray(resp, "GET test statuses")
    return _proxy_response(resp)


@router.get(
    "/xray/license",
    summary="Get xRay license information",
    operation_id="xray_get_license",
)
async def xray_get_license():
    """Retrieve xRay license status."""
    resp = _request_xray("GET", f"{XRAY_BASE_URL}/api/xraylicense")
    _raise_for_xray(resp, "GET xraylicense")
    return _proxy_response(resp)


@router.get(
    "/xray/project/{project_id}/settings/customfields/testruns",
    summary="Get xRay Test Run custom field metadata for a project",
    operation_id="xray_get_project_test_run_custom_fields",
)
async def xray_get_project_test_run_custom_fields(project_id: str):
    """Retrieve project-level test run custom field metadata."""
    resp = _request_xray("GET", f"{XRAY_BASE_URL}/api/project/{project_id}/settings/customfields/testruns")
    _raise_for_xray(resp, f"GET project test run custom fields {project_id}")
    return _proxy_response(resp)


@router.get(
    "/xray/project/{project_id}/settings/customfields/teststeps",
    summary="Get xRay Test Step custom field metadata for a project",
    operation_id="xray_get_project_test_step_custom_fields",
)
async def xray_get_project_test_step_custom_fields(project_id: str):
    """Retrieve project-level test step custom field metadata."""
    resp = _request_xray("GET", f"{XRAY_BASE_URL}/api/project/{project_id}/settings/customfields/teststeps")
    _raise_for_xray(resp, f"GET project test step custom fields {project_id}")
    return _proxy_response(resp)


@router.get(
    "/xray/dataset/export",
    summary="Export xRay dataset as CSV",
    operation_id="xray_export_dataset",
)
async def xray_export_dataset(
    test_issue_id: Optional[str] = Query(None, alias="testIssueId"),
    test_issue_key: Optional[str] = Query(None, alias="testIssueKey"),
    test_version: Optional[str] = Query(None, alias="testVersion"),
    context_issue_id: Optional[str] = Query(None, alias="contextIssueId"),
    context_issue_key: Optional[str] = Query(None, alias="contextIssueKey"),
    resolved: Optional[str] = None,
):
    """Export a dataset as CSV."""
    params = {
        k: v
        for k, v in {
            "testIssueId": test_issue_id,
            "testIssueKey": test_issue_key,
            "testVersion": test_version,
            "contextIssueId": context_issue_id,
            "contextIssueKey": context_issue_key,
            "resolved": resolved,
        }.items()
        if v is not None
    }
    resp = _request_xray("GET", f"{XRAY_BASE_URL}/api/dataset/export", params=params)
    _raise_for_xray(resp, "GET dataset export")
    return _proxy_response(resp)


@router.post(
    "/xray/dataset/import",
    summary="Import xRay dataset from CSV",
    operation_id="xray_import_dataset",
)
async def xray_import_dataset(
    file: UploadFile = File(..., description="CSV file containing dataset values"),
    test_issue_id: Optional[str] = Query(None, alias="testIssueId"),
    test_issue_key: Optional[str] = Query(None, alias="testIssueKey"),
    test_version: Optional[str] = Query(None, alias="testVersion"),
    context_issue_id: Optional[str] = Query(None, alias="contextIssueId"),
    context_issue_key: Optional[str] = Query(None, alias="contextIssueKey"),
):
    """Import a CSV dataset into a test or context issue."""
    session = xray._get_session()
    headers = {k: v for k, v in session.headers.items() if k.lower() != "content-type"}
    params = {
        k: v
        for k, v in {
            "testIssueId": test_issue_id,
            "testIssueKey": test_issue_key,
            "testVersion": test_version,
            "contextIssueId": context_issue_id,
            "contextIssueKey": context_issue_key,
        }.items()
        if v is not None
    }
    content = await file.read()
    resp = session.post(
        f"{XRAY_BASE_URL}/api/dataset/import",
        params=params,
        files={"file": (file.filename, content, file.content_type or "text/csv")},
        headers=headers,
    )
    _raise_for_xray(resp, "POST dataset import")
    return _proxy_response(resp)


@router.get(
    "/xray/testrepository/{project_key}/folders/{folder_id}",
    summary="Get xRay Test Repository folder metadata",
    operation_id="xray_get_test_repository_folder",
)
async def xray_get_test_repository_folder(project_key: str, folder_id: int):
    """Retrieve a test repository folder by project key and folder id."""
    resp = _request_xray("GET", f"{XRAY_BASE_URL}/api/testrepository/{project_key}/folders/{folder_id}")
    _raise_for_xray(resp, f"GET test repository folder {project_key}/{folder_id}")
    return _proxy_response(resp)


@router.get(
    "/xray/settings/requirement-projects",
    summary="List xRay requirement projects",
    operation_id="xray_get_requirement_projects",
)
async def xray_get_requirement_projects():
    """List projects activated for xRay requirement coverage."""
    resp = _request_xray("GET", f"{XRAY_BASE_URL}/api/settings/requirementProjects")
    _raise_for_xray(resp, "GET requirement projects")
    return _proxy_response(resp)


@router.post(
    "/xray/settings/requirement-projects",
    summary="Activate xRay requirement projects",
    operation_id="xray_add_requirement_projects",
)
async def xray_add_requirement_projects(body: ProjectKeysBody = Body(...)):
    """Activate xRay requirement coverage for projects."""
    resp = _request_xray("POST", f"{XRAY_BASE_URL}/api/settings/requirementProjects", json=body.project_keys)
    _raise_for_xray(resp, "POST requirement projects")
    return _proxy_response(resp)


@router.get(
    "/xray/issue-types",
    summary="List xRay issue types",
    operation_id="xray_get_issue_types",
)
async def xray_get_issue_types():
    """Retrieve the list of xRay issue types."""
    resp = _request_xray("GET", f"{XRAY_BASE_URL}/api/xrayIssueTypes")
    _raise_for_xray(resp, "GET xray issue types")
    return _proxy_response(resp)


@router.post(
    "/xray/issue-types/screen-schemes",
    summary="Install xRay issue type screen schemes",
    operation_id="xray_install_issue_type_screen_schemes",
)
async def xray_install_issue_type_screen_schemes(body: ProjectKeysBody = Body(...)):
    """Install xRay issue type screen schemes for projects."""
    resp = _request_xray(
        "POST",
        f"{XRAY_BASE_URL}/api/xrayIssueTypes/issueTypeScreenSchemes",
        json=body.project_keys,
    )
    _raise_for_xray(resp, "POST xray issue type screen schemes")
    return _proxy_response(resp)
