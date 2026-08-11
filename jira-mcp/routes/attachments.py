"""Attachment operations for Jira issues."""

import base64
import logging
import os
import tempfile

from fastapi import APIRouter, HTTPException, UploadFile, File

from client import jira, http_session
from config import (
    JIRA_BASE_URL,
    MAX_IMAGE_SIZE,
    MAX_TEXT_SIZE,
    MAX_PDF_SIZE,
    IMAGE_TYPES,
    TEXT_TYPES,
)

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Attachments"])


@router.post(
    "/issue/{issue_key}/attachments",
    summary="Upload attachment to Jira issue",
    operation_id="upload_attachment",
)
async def upload_attachment(issue_key: str, file: UploadFile = File(...)):
    """
    Upload a file attachment to a Jira issue.

    Parameters:
    - issue_key: The issue key (e.g., PROJ-123)
    - file: The file to upload
    """
    try:
        issue = jira.issue(issue_key)

        with tempfile.NamedTemporaryFile(
            delete=False, suffix=os.path.splitext(file.filename)[1]
        ) as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name

        try:
            attachment = jira.add_attachment(
                issue=issue, attachment=temp_file_path, filename=file.filename
            )

            return {
                "success": True,
                "message": f"Attachment uploaded successfully to {issue_key}",
                "attachment": {
                    "id": attachment.id,
                    "filename": attachment.filename,
                    "size": attachment.size,
                    "mimeType": attachment.mimeType,
                    "created": str(attachment.created),
                    "author": attachment.author.displayName
                    if hasattr(attachment, "author")
                    else "Unknown",
                },
                "issue_url": f"{JIRA_BASE_URL}/browse/{issue_key}",
            }
        finally:
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload attachment: {e}")


@router.get(
    "/issue/{issue_key}/attachments",
    summary="List attachments on Jira issue",
    operation_id="list_attachments",
)
async def list_attachments(issue_key: str):
    """
    Get a list of all attachments on a Jira issue.

    Parameters:
    - issue_key: The issue key (e.g., PROJ-123)
    """
    try:
        issue = jira.issue(issue_key)
        attachments = []

        if hasattr(issue.fields, "attachment") and issue.fields.attachment:
            for attachment in issue.fields.attachment:
                attachments.append(
                    {
                        "id": attachment.id,
                        "filename": attachment.filename,
                        "size": attachment.size,
                        "mimeType": attachment.mimeType,
                        "created": str(attachment.created),
                        "author": attachment.author.displayName
                        if hasattr(attachment, "author")
                        else "Unknown",
                        "content_url": attachment.content,
                    }
                )

        return {
            "issue_key": issue_key,
            "attachment_count": len(attachments),
            "attachments": attachments,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list attachments: {e}")


@router.delete(
    "/issue/{issue_key}/attachments/{attachment_id}",
    summary="Delete attachment from Jira issue",
    operation_id="delete_attachment",
)
async def delete_attachment(issue_key: str, attachment_id: str):
    """
    Delete an attachment from a Jira issue.

    Parameters:
    - issue_key: The issue key (e.g., PROJ-123)
    - attachment_id: The ID of the attachment to delete
    """
    try:
        jira.issue(issue_key)  # Verify issue exists

        attachment = jira.attachment(attachment_id)
        filename = attachment.filename
        attachment.delete()

        return {
            "success": True,
            "message": f"Attachment '{filename}' deleted successfully from {issue_key}",
            "attachment_id": attachment_id,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete attachment: {e}")


@router.get(
    "/issue/{issue_key}/attachments/{attachment_id}/download",
    summary="Download attachment content",
    operation_id="download_attachment",
)
async def download_attachment(issue_key: str, attachment_id: str):
    """
    Download attachment content with appropriate encoding.

    Parameters:
    - issue_key: The issue key (e.g., PROJ-123)
    - attachment_id: The attachment ID

    Returns:
    - For images: Base64-encoded content (for multimodal AI analysis)
    - For text files: UTF-8 decoded content
    - For PDFs: Base64-encoded content
    - For other files: Base64-encoded content

    Size limits: Images 10MB, Text 5MB, PDFs 20MB
    """
    try:
        issue = jira.issue(issue_key)

        attachment = None
        if hasattr(issue.fields, "attachment") and issue.fields.attachment:
            for att in issue.fields.attachment:
                if att.id == attachment_id:
                    attachment = att
                    break

        if not attachment:
            raise HTTPException(
                status_code=404,
                detail=f"Attachment {attachment_id} not found on {issue_key}",
            )

        mime_type = attachment.mimeType
        size = int(attachment.size)

        # Size validation
        if mime_type in IMAGE_TYPES and size > MAX_IMAGE_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"Image too large: {size} bytes (max {MAX_IMAGE_SIZE // 1024 // 1024}MB)",
            )
        if mime_type in TEXT_TYPES and size > MAX_TEXT_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"Text file too large: {size} bytes (max {MAX_TEXT_SIZE // 1024 // 1024}MB)",
            )
        if mime_type == "application/pdf" and size > MAX_PDF_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"PDF too large: {size} bytes (max {MAX_PDF_SIZE // 1024 // 1024}MB)",
            )

        # Download content
        response = http_session.get(
            attachment.content,
        )
        response.raise_for_status()
        raw_content = response.content

        # Format based on type
        if mime_type in IMAGE_TYPES:
            return {
                "filename": attachment.filename,
                "mime_type": mime_type,
                "size": size,
                "encoding": "base64",
                "content": base64.b64encode(raw_content).decode("utf-8"),
                "description": "Image content encoded as base64 for multimodal analysis",
            }
        elif mime_type in TEXT_TYPES:
            return {
                "filename": attachment.filename,
                "mime_type": mime_type,
                "size": size,
                "encoding": "utf-8",
                "content": raw_content.decode("utf-8", errors="replace"),
                "description": "Text content decoded as UTF-8",
            }
        elif mime_type == "application/pdf":
            return {
                "filename": attachment.filename,
                "mime_type": mime_type,
                "size": size,
                "encoding": "base64",
                "content": base64.b64encode(raw_content).decode("utf-8"),
                "description": "PDF content encoded as base64",
            }
        else:
            return {
                "filename": attachment.filename,
                "mime_type": mime_type,
                "size": size,
                "encoding": "base64",
                "content": base64.b64encode(raw_content).decode("utf-8"),
                "description": f"Binary content encoded as base64 (type: {mime_type})",
            }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to download attachment: {e}"
        )
