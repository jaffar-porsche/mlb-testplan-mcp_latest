"""Sprint extraction utilities with dynamic field discovery."""
import logging
import re
from typing import Dict, Optional

import config

logger = logging.getLogger(__name__)


def discover_sprint_field(jira_client) -> Optional[str]:
    """Discover the Sprint custom field ID from Jira field metadata.

    Queries jira.fields() and matches by schema type to find the
    Greenhopper sprint field. Caches the result in config.SPRINT_FIELD_ID.

    Returns the customfield_XXXXX ID or None if not found.
    """
    if config.SPRINT_FIELD_ID is not None:
        return config.SPRINT_FIELD_ID

    try:
        all_fields = jira_client.fields()
        for field in all_fields:
            schema = field.get("schema", {})
            custom_type = schema.get("custom", "")
            # Match the Greenhopper sprint field type
            if "gh-sprint" in custom_type:
                config.SPRINT_FIELD_ID = field["id"]
                logger.info(f"Discovered Sprint field: {field['id']} (name: {field['name']})")
                return config.SPRINT_FIELD_ID

            # Also match by name as fallback
            if field["name"].lower().strip() == "sprint" and field.get("custom"):
                config.SPRINT_FIELD_ID = field["id"]
                logger.info(f"Discovered Sprint field by name: {field['id']}")
                return config.SPRINT_FIELD_ID

    except Exception as e:
        logger.warning(f"Failed to discover Sprint field: {e}")

    # Fall back to trying known field IDs
    logger.warning("Sprint field not discovered, will try fallbacks")
    return None


def extract_sprint_info(issue) -> Optional[Dict]:
    """Extract sprint info from issue custom fields.

    Handles both list format (newer Jira) and string format (older Jira).

    Args:
        issue: Jira issue object with fields attribute

    Returns:
        Dict with sprint info (id, name, state, dates, goal) or None
    """
    # Try discovered field first, then fallbacks
    field_ids_to_try = []
    if config.SPRINT_FIELD_ID:
        field_ids_to_try.append(config.SPRINT_FIELD_ID)
    field_ids_to_try.extend(
        fid for fid in config._SPRINT_FIELD_FALLBACKS
        if fid != config.SPRINT_FIELD_ID
    )

    for field_id in field_ids_to_try:
        sprint_data = getattr(issue.fields, field_id, None)
        if not sprint_data:
            continue

        # Handle list format (newer Jira)
        if isinstance(sprint_data, list) and sprint_data:
            # Take the last active/future sprint (most relevant)
            sprint = sprint_data[-1] if len(sprint_data) > 1 else sprint_data[0]
            if hasattr(sprint, 'id'):
                return {
                    "id": sprint.id,
                    "name": getattr(sprint, 'name', None),
                    "state": getattr(sprint, 'state', None),
                    "startDate": str(getattr(sprint, 'startDate', None)) if getattr(sprint, 'startDate', None) else None,
                    "endDate": str(getattr(sprint, 'endDate', None)) if getattr(sprint, 'endDate', None) else None,
                    "goal": getattr(sprint, 'goal', None)
                }

        # Handle string format (older Jira)
        # Format: "com.atlassian.greenhopper.service.sprint.Sprint@...[id=123,name=Sprint 1,state=ACTIVE,...]"
        if isinstance(sprint_data, str):
            match = re.search(r"id=(\d+).*?name=([^,\]]+)", sprint_data)
            if match:
                state_match = re.search(r"state=([^,\]]+)", sprint_data)
                return {
                    "id": match.group(1),
                    "name": match.group(2),
                    "state": state_match.group(1) if state_match else None,
                    "startDate": None,
                    "endDate": None,
                    "goal": None
                }

        # Handle list of strings (Jira Data Center sometimes returns this)
        if isinstance(sprint_data, list) and sprint_data and isinstance(sprint_data[0], str):
            raw = sprint_data[-1]
            match = re.search(r"id=(\d+).*?name=([^,\]]+)", raw)
            if match:
                state_match = re.search(r"state=([^,\]]+)", raw)
                return {
                    "id": match.group(1),
                    "name": match.group(2),
                    "state": state_match.group(1) if state_match else None,
                    "startDate": None,
                    "endDate": None,
                    "goal": None
                }

    return None
