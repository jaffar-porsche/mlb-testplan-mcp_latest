"""Agile Hive team operations — list teams, get features by team, version management."""

import logging
import re
from datetime import date
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from client import jira, http_session
from config import JIRA_BASE_URL, JIRA_PAT, PROXIES
from utils.agile_hive import (
    discover_agile_hive_fields,
    extract_agile_hive_fields,
    build_team_name_cache,
    resolve_team_name_via_api,
)

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Teams"])


def _request_get(path: str, params: dict = None):
    """Make an authenticated GET request to the Jira REST API."""
    url = f"{JIRA_BASE_URL}{path}"
    return http_session.get(
        url,
        params=params,
        timeout=15,
    )


@router.get(
    "/teams",
    summary="List Agile Hive teams visible in a project's features",
    operation_id="list_teams",
)
async def list_teams(
    project_key: str = Query(
        description="Project key to scan for teams (e.g. ARTDIAGUPD)"
    ),
    max_results: int = Query(default=100, description="Max features to scan"),
):
    """List distinct teams found across features in a project.

    Scans active features (not Funnel/Closed/Resolved) and extracts
    unique Team and Teams Involved values with their IDs.
    This enables resolving team names to IDs for JQL queries.
    """
    field_ids = discover_agile_hive_fields(jira)

    if not field_ids.get("team") and not field_ids.get("teams_involved"):
        raise HTTPException(
            status_code=501,
            detail="Agile Hive team fields (Team, Teams Involved) not found on this Jira instance. "
            "Run GET /fields to inspect available custom fields.",
        )

    # Build team name cache first (Leading Team has names, Teams Involved doesn't)
    build_team_name_cache(
        jira, project_key, field_ids, JIRA_BASE_URL, JIRA_PAT, PROXIES
    )

    # Query features to extract team values
    jql = (
        f"project = {project_key} "
        f"AND issuetype in (Feature) "
        f'AND status not in ("Funnel", "Closed", "Resolved")'
    )

    # Request the specific custom fields we need
    fields_to_fetch = ["summary"]
    if field_ids.get("team"):
        fields_to_fetch.append(field_ids["team"])
    if field_ids.get("teams_involved"):
        fields_to_fetch.append(field_ids["teams_involved"])

    try:
        issues = jira.search_issues(
            jql, maxResults=max_results, fields=",".join(fields_to_fetch)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"JQL search failed: {e}")

    # Collect distinct teams
    teams_map: dict[str, dict] = {}  # id -> {id, name, role, count}

    for issue in issues:
        ah = extract_agile_hive_fields(issue, field_ids)

        team = ah.get("team")
        if team and team.get("id"):
            tid = team["id"]
            if tid not in teams_map:
                teams_map[tid] = {
                    "id": tid,
                    "name": team.get("name"),
                    "role": "leading_team",
                    "feature_count": 0,
                }
            teams_map[tid]["feature_count"] += 1

        for t in ah.get("teams_involved", []):
            if t and t.get("id"):
                tid = t["id"]
                if tid not in teams_map:
                    teams_map[tid] = {
                        "id": tid,
                        "name": t.get("name"),
                        "role": "teams_involved",
                        "feature_count": 0,
                    }
                teams_map[tid]["feature_count"] += 1

    # Try to resolve names for teams that don't have one (Teams Involved IDs)
    # via the Atlassian Teams REST API
    for tid, team_data in teams_map.items():
        if not team_data.get("name"):
            name = resolve_team_name_via_api(tid, JIRA_BASE_URL, JIRA_PAT, PROXIES)
            if name:
                team_data["name"] = name

    teams_list = sorted(
        teams_map.values(), key=lambda t: t["feature_count"], reverse=True
    )

    return {
        "project": project_key,
        "field_ids": {
            "team": field_ids.get("team"),
            "teams_involved": field_ids.get("teams_involved"),
        },
        "total_teams": len(teams_list),
        "teams": teams_list,
        "_note": "Team names are resolved via Leading Team field and AgileHiveProgramBoard "
        "issue properties. Any remaining unnamed teams use Agile Hive IDs — "
        "use the numeric ID directly in team/features queries.",
    }


@router.get(
    "/team/features",
    summary="Get features for a team, optionally filtered by PI",
    operation_id="get_team_features",
)
async def get_team_features(
    team: str = Query(
        description="Team name or Agile Hive team ID. "
        "If a name is given, it is resolved to an ID via the Team/Teams Involved fields."
    ),
    project_key: str = Query(
        default="ARTDIAGUPD",
        description="Jira project key to search in",
    ),
    pi: Optional[str] = Query(
        default=None,
        description="Program Increment version name to filter by (e.g. PI-26.2)",
    ),
    include_funnel: bool = Query(
        default=True,
        description="Include features in Funnel status (included by default to capture planned/wished features)",
    ),
    include_closed: bool = Query(
        default=False,
        description="Include Closed/Resolved features (excluded by default)",
    ),
    max_results: int = Query(default=50, description="Max results to return"),
):
    """Get features assigned to or involving a specific team.

    Builds a JQL query using the Agile Hive Team and Teams Involved fields.
    Accepts either a team ID (numeric) or a team name (resolved via field scan).
    """
    field_ids = discover_agile_hive_fields(jira)

    if not field_ids.get("team") and not field_ids.get("teams_involved"):
        raise HTTPException(
            status_code=501,
            detail="Agile Hive team fields not found on this Jira instance.",
        )

    # Build team name cache for cross-referencing
    build_team_name_cache(
        jira, project_key, field_ids, JIRA_BASE_URL, JIRA_PAT, PROXIES
    )

    # Resolve team name to ID(s).
    # Leading Team and Teams Involved use different ID spaces:
    #   - Team (Leading Team): Atlassian Teams IDs, resolvable via /rest/teams-api
    #   - Teams Involved: Agile Hive IDs, names not available via API
    # When resolving by name, we match against Leading Team (which has names).
    # When the user provides a numeric ID, we detect which field it belongs to.
    team_id = team.strip()
    team_id_source = None  # "leading_team", "teams_involved", or None (unknown)

    if not team_id.isdigit():
        resolved = await _resolve_team_name(team_id, project_key, field_ids)
        if not resolved:
            raise HTTPException(
                status_code=404,
                detail=f"Team '{team}' not found in project {project_key}. "
                f"Use GET /teams?project_key={project_key} to list available teams.",
            )
        team_id, team_id_source = resolved
    else:
        # Numeric ID — check if it resolves via Atlassian Teams API
        name = resolve_team_name_via_api(team_id, JIRA_BASE_URL, JIRA_PAT, PROXIES)
        if name:
            team_id_source = "leading_team"
        else:
            team_id_source = "teams_involved"

    # Build JQL
    clauses = [f"project = {project_key}", "issuetype in (Feature)"]

    # Use the team ID only in the field it belongs to (different ID spaces)
    team_conditions = []
    if team_id_source == "leading_team" and field_ids.get("team"):
        team_conditions.append(f"Team = {team_id}")
    elif team_id_source == "teams_involved" and field_ids.get("teams_involved"):
        team_conditions.append(f'"Teams Involved" in ({team_id})')
    else:
        # Unknown source — only use Team field (safer, avoids cross-ID-space errors)
        if field_ids.get("team"):
            team_conditions.append(f"Team = {team_id}")

    if team_conditions:
        clauses.append(f"({' OR '.join(team_conditions)})")

    excluded_statuses = []
    if not include_funnel:
        excluded_statuses.append('"Funnel"')
    if not include_closed:
        excluded_statuses.extend(['"Closed"', '"Resolved"'])
    if excluded_statuses:
        clauses.append(f"status not in ({', '.join(excluded_statuses)})")

    if pi:
        clauses.append(f'fixVersion = "{pi}"')

    jql = " AND ".join(clauses) + ' ORDER BY "Cost of Delay" DESC'

    # Fetch features with Agile Hive fields
    fields_to_fetch = ["summary", "status", "fixVersions", "priority"]
    if field_ids.get("team"):
        fields_to_fetch.append(field_ids["team"])
    if field_ids.get("teams_involved"):
        fields_to_fetch.append(field_ids["teams_involved"])
    if field_ids.get("cost_of_delay"):
        fields_to_fetch.append(field_ids["cost_of_delay"])

    try:
        issues = jira.search_issues(
            jql, maxResults=max_results, fields=",".join(fields_to_fetch)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"JQL search failed: {e}")

    results = []
    for issue in issues:
        ah = extract_agile_hive_fields(issue, field_ids)
        feature = {
            "key": issue.key,
            "summary": getattr(issue.fields, "summary", "N/A"),
            "status": getattr(issue.fields.status, "name", "Unknown")
            if hasattr(issue.fields, "status") and issue.fields.status
            else "Unknown",
            "priority": getattr(issue.fields.priority, "name", None)
            if hasattr(issue.fields, "priority") and issue.fields.priority
            else None,
            "fixVersions": [
                v.name for v in getattr(issue.fields, "fixVersions", []) or []
            ],
            "url": f"{JIRA_BASE_URL}/browse/{issue.key}",
        }
        feature.update(ah)
        results.append(feature)

    return {
        "team_id": team_id,
        "team_query": team,
        "project": project_key,
        "pi": pi,
        "jql": jql,
        "total": len(results),
        "features": results,
    }


@router.get(
    "/fields",
    summary="List all Jira fields (useful for discovering custom field IDs)",
    operation_id="list_fields",
)
async def list_fields(
    search: Optional[str] = Query(
        default=None,
        description="Filter fields by name (case-insensitive substring match)",
    ),
):
    """List all Jira fields with their IDs and names.

    Useful for discovering custom field IDs for Agile Hive fields,
    story points, or any other custom field.
    """
    try:
        all_fields = jira.fields()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch fields: {e}")

    results = []
    for field in all_fields:
        if search and search.lower() not in field["name"].lower():
            continue
        results.append(
            {
                "id": field["id"],
                "name": field["name"],
                "custom": field.get("custom", False),
                "schema": field.get("schema", {}),
            }
        )

    results.sort(key=lambda f: f["name"].lower())

    return {"total": len(results), "fields": results}


@router.get(
    "/versions",
    summary="List project versions (Program Increments) with dates and status",
    operation_id="list_versions",
)
async def list_versions(
    project_key: str = Query(
        default="ARTDIAGUPD",
        description="Jira project key",
    ),
    pi_only: bool = Query(
        default=True,
        description="Only return PI versions (matching PI-YY.Q pattern). "
        "Set to false to list all versions.",
    ),
):
    """List project versions with release dates and status.

    Versions follow the PI-YY.Q naming convention (e.g. PI-26.2 = 2026 Q2).
    Each version is annotated with a temporal status:
    - past: release date is in the past
    - current: start date <= today <= release date
    - next: the first future PI after current
    - future: all other upcoming PIs

    Use this to resolve natural language like "next PI" or "current PI"
    to the exact version name needed for /team/features queries.
    """
    try:
        versions = jira.project_versions(project_key)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch versions: {e}")

    pi_pattern = re.compile(r"^PI-\d{2}\.\d$")
    today = date.today()

    results = []
    for v in versions:
        name = getattr(v, "name", "")
        if pi_only and not pi_pattern.match(name):
            continue

        start_date_str = getattr(v, "startDate", None)
        release_date_str = getattr(v, "releaseDate", None)
        released = getattr(v, "released", False)

        start_date = date.fromisoformat(start_date_str) if start_date_str else None
        release_date = (
            date.fromisoformat(release_date_str) if release_date_str else None
        )

        results.append(
            {
                "id": v.id,
                "name": name,
                "description": getattr(v, "description", None),
                "startDate": start_date_str,
                "releaseDate": release_date_str,
                "released": released,
                "_start": start_date,
                "_release": release_date,
            }
        )

    # Sort by name (PI-YY.Q sorts correctly lexicographically)
    results.sort(key=lambda v: v["name"])

    # Annotate temporal status
    found_current = False
    found_next = False
    for v in results:
        s, r = v.pop("_start"), v.pop("_release")
        if v["released"]:
            v["status"] = "past"
        elif s and r and s <= today <= r:
            v["status"] = "current"
            found_current = True
        elif r and r < today:
            v["status"] = "past"
        elif not found_next and (not s or s > today):
            v["status"] = "next"
            found_next = True
        else:
            v["status"] = "future"

    # If no explicit current found but there's a PI where start <= today and
    # release date is missing, mark it based on position
    if not found_current and not found_next:
        for v in results:
            if v["status"] != "past":
                v["status"] = "next"
                break

    return {
        "project": project_key,
        "today": today.isoformat(),
        "total": len(results),
        "versions": results,
    }


@router.get(
    "/versions/{version_id}/summary",
    summary="Get version release summary from linked issues",
    operation_id="get_version_summary",
)
async def get_version_summary(
    version_id: str,
    project_key: str = Query(
        description="Jira project key (needed to query issues by fixVersion name)",
    ),
    max_length: int = Query(
        default=16384,
        description="Maximum length of the generated summary in characters. "
        "Jira version description field limit is 16384 bytes.",
    ),
):
    """Build a release summary for a version based on its linked issues.

    Fetches the version, queries all issues with that fixVersion,
    and produces a structured plain-text summary grouped by issue type.

    The summary respects max_length and truncates gracefully if needed.
    Use the result as input for update_version to set the release description,
    or refine it further before updating.

    Parameters:
    - version_id: The version ID (numeric, from list_versions response)
    - project_key: Jira project key (e.g. ARTDIAGUPD)
    - max_length: Max characters for the summary (default 16384)
    """
    # Fetch version metadata
    try:
        version = jira.version(version_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch version: {e}")

    version_name = getattr(version, "name", "Unknown")

    # Query issues linked to this version via fixVersion
    jql = f'project = {project_key} AND fixVersion = "{version_name}" ORDER BY issuetype ASC, key ASC'
    try:
        issues = jira.search_issues(
            jql,
            maxResults=200,
            fields="summary,status,issuetype,priority",
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to search issues for version: {e}"
        )

    # Group issues by type
    grouped: dict[str, list[dict]] = {}
    for issue in issues:
        itype = (
            getattr(issue.fields.issuetype, "name", "Other")
            if hasattr(issue.fields, "issuetype") and issue.fields.issuetype
            else "Other"
        )
        status = (
            getattr(issue.fields.status, "name", "Unknown")
            if hasattr(issue.fields, "status") and issue.fields.status
            else "Unknown"
        )
        priority = (
            getattr(issue.fields.priority, "name", None)
            if hasattr(issue.fields, "priority") and issue.fields.priority
            else None
        )
        grouped.setdefault(itype, []).append(
            {
                "key": issue.key,
                "summary": getattr(issue.fields, "summary", "N/A"),
                "status": status,
                "priority": priority,
            }
        )

    # Build structured summary text
    lines = [f"Release {version_name}", ""]
    issue_count = 0
    for itype in sorted(grouped.keys()):
        type_issues = grouped[itype]
        lines.append(f"{itype} ({len(type_issues)}):")
        for item in type_issues:
            status_tag = f" [{item['status']}]" if item["status"] else ""
            lines.append(f"  - {item['key']}: {item['summary']}{status_tag}")
            issue_count += 1
        lines.append("")

    summary_text = "\n".join(lines).rstrip()

    # Truncate if exceeding max_length
    truncated = False
    if len(summary_text.encode("utf-8")) > max_length:
        truncated = True
        # Truncate by lines to avoid cutting mid-line
        while lines and len("\n".join(lines).encode("utf-8")) > max_length - 20:
            if lines[-1] == "":
                lines.pop()
            else:
                lines.pop()
        lines.append("... (truncated)")
        summary_text = "\n".join(lines).rstrip()

    return {
        "version_id": version.id,
        "version_name": version_name,
        "project": project_key,
        "issue_count": issue_count,
        "issues_by_type": {
            itype: len(items) for itype, items in sorted(grouped.items())
        },
        "summary_text": summary_text,
        "summary_length": len(summary_text),
        "max_length": max_length,
        "truncated": truncated,
        "issues": [
            {
                "key": item["key"],
                "summary": item["summary"],
                "status": item["status"],
                "issuetype": itype,
                "priority": item["priority"],
            }
            for itype in sorted(grouped.keys())
            for item in grouped[itype]
        ],
    }


@router.put(
    "/versions/{version_id}",
    summary="Update a project version (release)",
    operation_id="update_version",
)
async def update_version(
    version_id: str,
    description: Optional[str] = Query(
        default=None,
        description="New description for the version",
    ),
    name: Optional[str] = Query(
        default=None,
        description="New name for the version",
    ),
    released: Optional[bool] = Query(
        default=None,
        description="Whether the version is released",
    ),
    archived: Optional[bool] = Query(
        default=None,
        description="Whether the version is archived",
    ),
    release_date: Optional[str] = Query(
        default=None,
        description="Release date in YYYY-MM-DD format",
    ),
    start_date: Optional[str] = Query(
        default=None,
        description="Start date in YYYY-MM-DD format",
    ),
):
    """Update an existing Jira project version (release).

    Only provided fields are updated; omitted fields remain unchanged.
    Use this to update version descriptions, names, dates, or release status.

    Parameters:
    - version_id: The version ID (numeric, from list_versions response)
    - description: New description text
    - name: New version name
    - released: Mark as released (true) or unreleased (false)
    - archived: Mark as archived (true) or unarchived (false)
    - release_date: Release date (YYYY-MM-DD)
    - start_date: Start date (YYYY-MM-DD)
    """
    kwargs = {}
    if description is not None:
        kwargs["description"] = description
    if name is not None:
        kwargs["name"] = name
    if released is not None:
        kwargs["released"] = released
    if archived is not None:
        kwargs["archived"] = archived
    if release_date is not None:
        kwargs["releaseDate"] = release_date
    if start_date is not None:
        kwargs["startDate"] = start_date

    if not kwargs:
        raise HTTPException(
            status_code=400,
            detail="No fields to update. Provide at least one of: "
            "description, name, released, archived, release_date, start_date.",
        )

    try:
        version = jira.version(version_id)
        version.update(**kwargs)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update version: {e}")

    return {
        "id": version.id,
        "name": getattr(version, "name", None),
        "description": getattr(version, "description", None),
        "startDate": getattr(version, "startDate", None),
        "releaseDate": getattr(version, "releaseDate", None),
        "released": getattr(version, "released", False),
        "archived": getattr(version, "archived", False),
        "updated_fields": list(kwargs.keys()),
    }


async def _resolve_team_name(
    name: str, project_key: str, field_ids: dict
) -> Optional[tuple[str, str]]:
    """Resolve a team name to its ID and source field.

    Performs a case-insensitive substring match against Team and
    Teams Involved values in the project's features.

    Returns:
        Tuple of (team_id, source) where source is "leading_team" or
        "teams_involved", or None if not found.
    """
    jql = (
        f"project = {project_key} "
        f"AND issuetype in (Feature) "
        f'AND status not in ("Funnel", "Closed", "Resolved")'
    )

    fields_to_fetch = ["summary"]
    if field_ids.get("team"):
        fields_to_fetch.append(field_ids["team"])
    if field_ids.get("teams_involved"):
        fields_to_fetch.append(field_ids["teams_involved"])

    try:
        issues = jira.search_issues(
            jql, maxResults=200, fields=",".join(fields_to_fetch)
        )
    except Exception:
        return None

    name_lower = name.lower()

    for issue in issues:
        ah = extract_agile_hive_fields(issue, field_ids)

        team = ah.get("team")
        if team and team.get("name") and name_lower in team["name"].lower():
            return team["id"], "leading_team"

        for t in ah.get("teams_involved", []):
            if t and t.get("name") and name_lower in t["name"].lower():
                return t["id"], "teams_involved"

    return None
