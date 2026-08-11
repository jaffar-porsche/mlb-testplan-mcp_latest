"""Pydantic models for request validation."""
from pydantic import BaseModel
from typing import Optional


class CreatePageRequest(BaseModel):
    space_key: str
    title: str
    body: str
    parent_id: Optional[str] = None


class UpdatePageRequest(BaseModel):
    title: Optional[str] = None
    body: Optional[str] = None


class MovePageRequest(BaseModel):
    parent_id: Optional[str] = None  # Target parent page ID, or null/omitted to move to space root


class AddCommentRequest(BaseModel):
    body: str
