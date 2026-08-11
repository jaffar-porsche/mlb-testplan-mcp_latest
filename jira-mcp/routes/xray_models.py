"""Shared Pydantic request/response models for xRay routes."""
from typing import Any, Optional

from fastapi import HTTPException
from pydantic import BaseModel, Field, model_validator


class EvidenceFileInput(BaseModel):
    data: str = Field(..., description="Base64 encoded file content")
    filename: str = Field(..., description="Attachment file name")
    contentType: str = Field(..., description="Attachment MIME type")


class KeysBody(BaseModel):
    keys: list[str] = Field(..., description="List of issue keys", json_schema_extra={"items": {"type": "string"}})


class ProjectKeysBody(BaseModel):
    project_keys: list[str] = Field(..., description="List of project keys", json_schema_extra={"items": {"type": "string"}})


class TestStepCreate(BaseModel):
    action: str = Field(..., description="Step action/description")
    data: Optional[str] = Field(None, description="Step test data")
    result: Optional[str] = Field(None, description="Expected result")
    attachments: Optional[list[EvidenceFileInput]] = Field(default_factory=list, description="Attachments to add to the step", json_schema_extra={"items": {"$ref": "#/components/schemas/EvidenceFileInput"}})
    call_test_issue_key: Optional[str] = Field(None, description="Optional issue key for a call-test step")


class TestStepUpdate(BaseModel):
    action: Optional[str] = Field(None, description="Step action/description")
    data: Optional[str] = Field(None, description="Step test data")
    result: Optional[str] = Field(None, description="Expected result")
    attachments_to_add: Optional[list[EvidenceFileInput]] = Field(default_factory=list, description="Attachments to add", json_schema_extra={"items": {"$ref": "#/components/schemas/EvidenceFileInput"}})
    attachments_to_remove: Optional[list[int]] = Field(default_factory=list, description="Attachment ids to remove", json_schema_extra={"items": {"type": "integer"}})
    call_test_issue_key: Optional[str] = Field(None, description="Optional issue key for a call-test step")


class TestRunStatusUpdate(BaseModel):
    status: str = Field(..., description="New status (e.g. PASS, FAIL, TODO, EXECUTING)")
    comment: Optional[str] = Field(None, description="Optional comment for the status update")


class DefectUpdateModel(BaseModel):
    add: Optional[list[str]] = Field(None, description="Defect keys to add", json_schema_extra={"items": {"type": "string"}})
    remove: Optional[list[str]] = Field(None, description="Defect keys to remove", json_schema_extra={"items": {"type": "string"}})


class EvidenceUpdateModel(BaseModel):
    add: Optional[list[EvidenceFileInput]] = Field(None, description="Evidence files to add", json_schema_extra={"items": {"$ref": "#/components/schemas/EvidenceFileInput"}})
    remove: Optional[list[str]] = Field(None, description="Evidence identifiers to remove (IDs or keys)", json_schema_extra={"items": {"type": "string"}})


class StepResultUpdateModel(BaseModel):
    id: Optional[int] = Field(None, description="Step result id")
    status: Optional[str] = Field(None, description="Step result status")
    comment: Optional[str] = Field(None, description="Step result comment")
    defects: Optional[DefectUpdateModel] = Field(None, description="Defects to add or remove")
    evidences: Optional[EvidenceUpdateModel] = Field(None, description="Evidence files to add or remove")
    actualResult: Optional[str] = Field(None, description="Actual result text")


class IterationUpdateModel(BaseModel):
    status: Optional[str] = Field(None, description="Iteration status")
    steps: Optional[list[StepResultUpdateModel]] = Field(None, description="Step result updates", json_schema_extra={"items": {"$ref": "#/components/schemas/StepResultUpdateModel"}})


class IterationStatusUpdateModel(BaseModel):
    id: int = Field(..., description="Iteration id")
    status: str = Field(..., description="Iteration status")


class TestRunCustomFieldValueModel(BaseModel):
    value: Optional[Any] = Field(None, description="Custom field value (string for single, list of strings for multi-select)")


class CustomFieldUpdateModel(BaseModel):
    id: int = Field(..., description="Custom field id")
    value: Optional[Any] = Field(None, description="Custom field value (string, list of strings, boolean, etc.)")


class TestRunUpdateModel(BaseModel):
    status: Optional[str] = Field(None, description="Test run status")
    comment: Optional[str] = Field(None, description="Test run comment")
    assignee: Optional[str] = Field(None, description="Assignee username")
    defects: Optional[DefectUpdateModel] = Field(None, description="Defects to add or remove")
    evidences: Optional[EvidenceUpdateModel] = Field(None, description="Evidence files to add or remove")
    customFields: Optional[list[CustomFieldUpdateModel]] = Field(None, description="Test run custom field updates", json_schema_extra={"items": {"$ref": "#/components/schemas/CustomFieldUpdateModel"}})
    iterations: Optional[list[IterationStatusUpdateModel]] = Field(None, description="Iteration status updates", json_schema_extra={"items": {"$ref": "#/components/schemas/IterationStatusUpdateModel"}})
    steps: Optional[list[StepResultUpdateModel]] = Field(None, description="Direct step result updates", json_schema_extra={"items": {"$ref": "#/components/schemas/StepResultUpdateModel"}})
    examples: Optional[dict[str, Any]] = Field(None, description="Examples update block")


class TestRunsQueryModel(BaseModel):
    testExecKey: Optional[str] = Field(None, description="The Test Execution issue key")
    testExecutionKey: Optional[str] = Field(None, description="Alias of testExecKey")
    testKey: Optional[str] = Field(None, description="The Test issue key")
    testPlanKey: Optional[str] = Field(None, description="The Test Plan issue key")
    includeTestFields: Optional[str] = Field(None, description="Comma-separated Test issue custom fields")
    savedFilterId: Optional[str] = Field(None, description="Jira filter ID or name containing Test Executions")
    limit: int = Field(50, ge=1, le=100, description="Maximum number of Test Runs")
    page: int = Field(1, ge=1, description="Result page number")

    @property
    def resolved_test_exec_key(self) -> Optional[str]:
        return self.testExecKey or self.testExecutionKey

    @model_validator(mode="after")
    def validate_context(self):
        if not any([self.resolved_test_exec_key, self.testPlanKey, self.savedFilterId]):
            raise HTTPException(
                status_code=400,
                detail="One of testExecKey (or testExecutionKey), testPlanKey, or savedFilterId is required.",
            )
        if self.testKey and not self.resolved_test_exec_key:
            raise HTTPException(
                status_code=400,
                detail="testKey may only be used with testExecKey or testExecutionKey.",
            )
        return self
