"""Issue CRUD operations, hierarchy traversal, and roadmap endpoints."""
import logging
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import PlainTextResponse

from client import jira
from config import JIRA_BASE_URL
from utils.sprint import discover_sprint_field, extract_sprint_info
from utils.hierarchy import build_hierarchy_markdown, build_roadmap_markdown
from utils.agile_hive import discover_agile_hive_fields, extract_agile_hive_fields

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Issues"])


def _find_epic_link_field():
    """Find the Epic Link field ID dynamically."""
    try:
        all_fields = jira.fields()
        for field in all_fields:
            if field['name'].lower() == 'epic link':
                return field['id']
    except Exception:
        pass
    return 'customfield_10000'  # Fallback


def _resolve_version_names(project_key: str, version_names: list[str]) -> list[dict]:
    """Resolve version names to Jira version objects {"name": ..., "id": ...}.

    Raises HTTPException if any version name is not found in the project.
    """
    if not version_names:
        return []
    project_versions = jira.project_versions(project_key)
    version_map = {v.name: v.id for v in project_versions}
    resolved = []
    for name in version_names:
        if name not in version_map:
            available = sorted(version_map.keys())
            raise HTTPException(
                status_code=400,
                detail=f"Version '{name}' not found in project {project_key}. "
                       f"Available versions: {', '.join(available[-20:])}"
            )
        resolved.append({"name": name, "id": version_map[name]})
    return resolved


@router.post("/create_issue", summary="Create a new Jira issue", operation_id="create_issue")
async def create_issue(
    project_key: str,
    summary: str,
    description: str,
    issuetype: str = "Task",
    epic_link: Optional[str] = None,
    components: Optional[List[str]] = Query(default=None, description="List of component names", json_schema_extra={"items": {"type": "string"}}),
    labels: Optional[List[str]] = Query(default=None, description="List of labels", json_schema_extra={"items": {"type": "string"}}),
    assignee: Optional[str] = None,
    versions: Optional[List[str]] = Query(default=None, description="List of affectsVersion names (e.g., ['PI-26.2'])", json_schema_extra={"items": {"type": "string"}}),
    fix_versions: Optional[List[str]] = Query(default=None, description="List of fixVersion names (e.g., ['PI-26.2'])", json_schema_extra={"items": {"type": "string"}}),
):
    """
    Create a new Jira issue.

    Parameters:
    - project_key: The project key (e.g., SLIM, DEVX)
    - summary: Issue summary/title
    - description: Issue description
    - issuetype: Issue type (default: "Task")
    - epic_link: Epic key to link this issue to (e.g., SLIM-123)
    - components: List of component names (e.g., ["PDDI", "Backend"])
    - labels: List of labels to add
    - assignee: Username to assign the issue to
    - versions: List of affectsVersion names (e.g., ["PI-26.2"])
    - fix_versions: List of fixVersion names (e.g., ["PI-26.2"])
    """
    try:
        issue_dict = {
            "project": {"key": project_key},
            "summary": summary,
            "description": description,
            "issuetype": {"name": issuetype},
        }

        if components:
            issue_dict["components"] = [{"name": comp} for comp in components]

        if labels:
            issue_dict["labels"] = labels

        if assignee:
            issue_dict["assignee"] = {"name": assignee}

        if versions:
            issue_dict["versions"] = _resolve_version_names(project_key, versions)

        if fix_versions:
            issue_dict["fixVersions"] = _resolve_version_names(project_key, fix_versions)

        if epic_link:
            try:
                epic_link_field = _find_epic_link_field()
                issue_dict[epic_link_field] = epic_link
            except Exception as epic_error:
                logger.warning(f"Could not link to epic {epic_link}: {epic_error}")

        new_issue = jira.create_issue(fields=issue_dict)

        result = {
            "key": new_issue.key,
            "id": new_issue.id,
            "url": f"{JIRA_BASE_URL}/browse/{new_issue.key}"
        }

        if epic_link:
            result["epic_link"] = epic_link

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create issue: {e}")


@router.get("/issue/{issue_key}", summary="Get Jira issue details", operation_id="get_issue")
async def get_issue(issue_key: str):
    """Retrieve comprehensive details for a specific Jira issue."""
    try:
        discover_sprint_field(jira)
        issue = jira.issue(issue_key, expand='changelog,renderedFields,names,transitions,operations')

        issue_data = {
            "key": issue.key,
            "id": issue.id,
            "self": issue.self,
            "url": f"{JIRA_BASE_URL}/browse/{issue.key}",

            # Basic fields
            "summary": issue.fields.summary,
            "description": issue.fields.description or "No description provided",
            "issuetype": {
                "name": issue.fields.issuetype.name,
                "id": issue.fields.issuetype.id,
                "iconUrl": getattr(issue.fields.issuetype, 'iconUrl', None)
            },
            "status": {
                "name": issue.fields.status.name,
                "id": issue.fields.status.id,
                "category": getattr(issue.fields.status.statusCategory, 'name', 'Unknown') if hasattr(issue.fields.status, 'statusCategory') and issue.fields.status.statusCategory else 'Unknown'
            },

            # People
            "assignee": {
                "displayName": issue.fields.assignee.displayName if issue.fields.assignee else "Unassigned",
                "emailAddress": getattr(issue.fields.assignee, 'emailAddress', None) if issue.fields.assignee else None,
                "accountId": getattr(issue.fields.assignee, 'accountId', None) if issue.fields.assignee else None
            },
            "reporter": {
                "displayName": issue.fields.reporter.displayName if issue.fields.reporter else "Unknown",
                "emailAddress": getattr(issue.fields.reporter, 'emailAddress', None) if issue.fields.reporter else None,
                "accountId": getattr(issue.fields.reporter, 'accountId', None) if issue.fields.reporter else None
            },
            "creator": {
                "displayName": issue.fields.creator.displayName if hasattr(issue.fields, 'creator') and issue.fields.creator else "Unknown",
                "emailAddress": getattr(issue.fields.creator, 'emailAddress', None) if hasattr(issue.fields, 'creator') and issue.fields.creator else None
            },

            # Dates
            "created": str(issue.fields.created) if issue.fields.created else None,
            "updated": str(issue.fields.updated) if issue.fields.updated else None,
            "resolutiondate": str(issue.fields.resolutiondate) if hasattr(issue.fields, 'resolutiondate') and issue.fields.resolutiondate else None,
            "duedate": str(issue.fields.duedate) if hasattr(issue.fields, 'duedate') and issue.fields.duedate else None,

            # Project info
            "project": {
                "key": issue.fields.project.key,
                "name": issue.fields.project.name,
                "id": issue.fields.project.id
            },

            # Priority and resolution
            "priority": {
                "name": getattr(issue.fields.priority, 'name', None) if hasattr(issue.fields, 'priority') and issue.fields.priority else None,
                "id": getattr(issue.fields.priority, 'id', None) if hasattr(issue.fields, 'priority') and issue.fields.priority else None,
                "iconUrl": getattr(issue.fields.priority, 'iconUrl', None) if hasattr(issue.fields, 'priority') and issue.fields.priority else None,
            },
            "resolution": {
                "name": issue.fields.resolution.name if hasattr(issue.fields, 'resolution') and issue.fields.resolution else "Unresolved",
                "description": getattr(issue.fields.resolution, 'description', None) if hasattr(issue.fields, 'resolution') and issue.fields.resolution else None
            },

            # Additional fields
            "environment": getattr(issue.fields, 'environment', None),
            "labels": getattr(issue.fields, 'labels', []),
            "components": [{"name": comp.name, "id": comp.id} for comp in getattr(issue.fields, 'components', [])],
            "fixVersions": [{"name": ver.name, "id": ver.id, "released": getattr(ver, 'released', False)} for ver in getattr(issue.fields, 'fixVersions', [])],
            "versions": [{"name": ver.name, "id": ver.id, "released": getattr(ver, 'released', False)} for ver in getattr(issue.fields, 'versions', [])],

            # Time tracking
            "timetracking": {
                "originalEstimate": getattr(issue.fields, 'timeoriginalestimate', None),
                "remainingEstimate": getattr(issue.fields, 'timeestimate', None),
                "timeSpent": getattr(issue.fields, 'timespent', None)
            } if hasattr(issue.fields, 'timeoriginalestimate') else None,

            # Epic link
            "epic_link": None,

            # Sprint information
            "sprint": extract_sprint_info(issue),

            # Custom fields
            "story_points": getattr(issue.fields, 'customfield_10016', None),

            # Agile Hive fields (Team, Teams Involved, Cost of Delay)
            "team": None,
            "teams_involved": None,
            "cost_of_delay": None,

            # Subtasks and links
            "subtasks": [{"key": subtask.key, "summary": subtask.fields.summary, "status": subtask.fields.status.name} for subtask in getattr(issue.fields, 'subtasks', [])],
            "parent": {"key": issue.fields.parent.key, "summary": issue.fields.parent.fields.summary} if hasattr(issue.fields, 'parent') and issue.fields.parent else None,

            # Issue links (for hierarchy/dependency relationships)
            "issuelinks": [],

            # Watchers and votes
            "watches": {
                "watchCount": getattr(issue.fields.watches, 'watchCount', 0) if hasattr(issue.fields, 'watches') else 0,
                "isWatching": getattr(issue.fields.watches, 'isWatching', False) if hasattr(issue.fields, 'watches') else False
            },
            "votes": {
                "votes": getattr(issue.fields.votes, 'votes', 0) if hasattr(issue.fields, 'votes') else 0,
                "hasVoted": getattr(issue.fields.votes, 'hasVoted', False) if hasattr(issue.fields, 'votes') else False
            }
        }

        # Extract epic link
        try:
            epic_link_field = _find_epic_link_field()
            epic_link_value = getattr(issue.fields, epic_link_field, None)

            if epic_link_value:
                issue_data["epic_link"] = epic_link_value
                try:
                    epic_issue = jira.issue(epic_link_value)
                    issue_data["epic_details"] = {
                        "key": epic_issue.key,
                        "summary": epic_issue.fields.summary,
                        "status": epic_issue.fields.status.name
                    }
                except Exception:
                    issue_data["epic_details"] = {"key": epic_link_value}

        except Exception as e:
            logger.warning(f"Failed to extract epic link for {issue_key}: {e}")

        # Extract Agile Hive fields
        try:
            ah_field_ids = discover_agile_hive_fields(jira)
            ah_data = extract_agile_hive_fields(issue, ah_field_ids)
            issue_data.update(ah_data)
        except Exception as e:
            logger.warning(f"Failed to extract Agile Hive fields for {issue_key}: {e}")

        # Extract issue links (parent-child, blocks, relates, etc.)
        try:
            raw_links = getattr(issue.fields, 'issuelinks', []) or []
            formatted_links = []
            for link in raw_links:
                link_info = {
                    "id": getattr(link, 'id', None),
                    "type": {
                        "name": getattr(link.type, 'name', None) if hasattr(link, 'type') else None,
                        "inward": getattr(link.type, 'inward', None) if hasattr(link, 'type') else None,
                        "outward": getattr(link.type, 'outward', None) if hasattr(link, 'type') else None,
                    }
                }
                # Add outward issue if present
                if hasattr(link, 'outwardIssue') and link.outwardIssue:
                    link_info["outwardIssue"] = {
                        "key": link.outwardIssue.key,
                        "summary": getattr(link.outwardIssue.fields, 'summary', None),
                        "status": getattr(link.outwardIssue.fields.status, 'name', None) if hasattr(link.outwardIssue.fields, 'status') else None,
                        "issuetype": getattr(link.outwardIssue.fields.issuetype, 'name', None) if hasattr(link.outwardIssue.fields, 'issuetype') else None,
                    }
                # Add inward issue if present
                if hasattr(link, 'inwardIssue') and link.inwardIssue:
                    link_info["inwardIssue"] = {
                        "key": link.inwardIssue.key,
                        "summary": getattr(link.inwardIssue.fields, 'summary', None),
                        "status": getattr(link.inwardIssue.fields.status, 'name', None) if hasattr(link.inwardIssue.fields, 'status') else None,
                        "issuetype": getattr(link.inwardIssue.fields.issuetype, 'name', None) if hasattr(link.inwardIssue.fields, 'issuetype') else None,
                    }
                formatted_links.append(link_info)
            issue_data["issuelinks"] = formatted_links
        except Exception as e:
            logger.warning(f"Failed to extract issue links for {issue_key}: {e}")

        # Add available transitions
        try:
            transitions = jira.transitions(issue)
            issue_data["availableTransitions"] = [{"id": t['id'], "name": t['name']} for t in transitions]
        except Exception as e:
            logger.warning(f"Failed to get transitions for {issue_key}: {e}")
            issue_data["availableTransitions"] = []

        # Add comments count
        try:
            comments = jira.comments(issue)
            issue_data["commentsCount"] = len(comments)
            issue_data["latestComments"] = [
                {
                    "id": comment.id,
                    "author": comment.author.displayName,
                    "body": comment.body,
                    "created": str(comment.created)
                } for comment in comments[-3:]
            ]
        except Exception as e:
            logger.warning(f"Failed to get comments for {issue_key}: {e}")
            issue_data["commentsCount"] = 0
            issue_data["latestComments"] = []

        return issue_data

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch issue: {e}")


@router.put("/issue/{issue_key}", summary="Update Jira issue", operation_id="update_issue")
async def update_issue(
    issue_key: str,
    summary: str = None,
    description: str = None,
    assignee: str = None,
    status: str = None,
    priority: str = None,
    labels: Optional[List[str]] = Query(default=None, description="List of labels to set", json_schema_extra={"items": {"type": "string"}}),
    comment: str = None,
    transition_comment: str = None,
    epic_link: str = None,
    versions: Optional[List[str]] = Query(default=None, description="List of affectsVersion names (e.g., ['PI-26.2']). Use [] to clear.", json_schema_extra={"items": {"type": "string"}}),
    fix_versions: Optional[List[str]] = Query(default=None, description="List of fixVersion names (e.g., ['PI-26.2']). Use [] to clear.", json_schema_extra={"items": {"type": "string"}}),
):
    """
    Update an existing Jira issue. Provide only the fields you want to update.

    Parameters:
    - issue_key: The issue key (e.g., ITDMFC-1496)
    - summary: New summary text
    - description: New description text
    - assignee: Username or account ID (use "Unassigned" to unassign)
    - status: New status name (must match available transitions)
    - priority: New priority name (e.g., "High", "Medium", "Low")
    - labels: List of labels to set
    - comment: Add a comment to the issue
    - transition_comment: Comment to include with the status transition (required by some workflows)
    - epic_link: Epic key to link to, or "remove" to unlink
    - versions: List of affectsVersion names to set (e.g., ["PI-26.2"]). Pass empty list to clear.
    - fix_versions: List of fixVersion names to set (e.g., ["PI-26.2"]). Pass empty list to clear.
    """
    try:
        issue = jira.issue(issue_key)
        update_fields = {}

        if summary is not None:
            update_fields['summary'] = summary
        if description is not None:
            update_fields['description'] = description
        if priority is not None:
            update_fields['priority'] = {'name': priority}
        if labels is not None:
            update_fields['labels'] = labels
        if assignee is not None:
            if assignee.lower() in ["none", "unassigned", ""]:
                update_fields['assignee'] = None
            else:
                update_fields['assignee'] = {'name': assignee}

        # Handle epic link
        if epic_link is not None:
            try:
                epic_link_field = _find_epic_link_field()
                if epic_link.lower() == "remove":
                    update_fields[epic_link_field] = None
                else:
                    update_fields[epic_link_field] = epic_link
            except Exception as epic_error:
                logger.warning(f"Could not update epic link to {epic_link}: {epic_error}")

        # Handle affectsVersion (versions field)
        if versions is not None:
            project_key = issue.fields.project.key
            update_fields['versions'] = _resolve_version_names(project_key, versions)

        # Handle fixVersions
        if fix_versions is not None:
            project_key = issue.fields.project.key
            update_fields['fixVersions'] = _resolve_version_names(project_key, fix_versions)

        if update_fields:
            issue.update(fields=update_fields)

        # Handle status transition
        if status is not None:
            transitions = jira.transitions(issue)
            transition_id = None
            for t in transitions:
                if t['name'].lower() == status.lower():
                    transition_id = t['id']
                    break

            if transition_id:
                # Pass transition_comment if provided (required by some workflows like ISMS)
                jira.transition_issue(issue, transition_id, comment=transition_comment)
            else:
                available_transitions = [t['name'] for t in transitions]
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid status transition. Available: {', '.join(available_transitions)}"
                )

        if comment:
            jira.add_comment(issue, comment)

        # Refresh and return
        issue = jira.issue(issue_key)

        response = {
            "success": True,
            "message": f"Issue {issue_key} updated successfully",
            "key": issue.key,
            "summary": issue.fields.summary,
            "status": issue.fields.status.name,
            "assignee": issue.fields.assignee.displayName if issue.fields.assignee else "Unassigned",
            "url": f"{JIRA_BASE_URL}/browse/{issue.key}",
            "epic_link": None,
            "versions": [{"name": v.name, "id": v.id} for v in getattr(issue.fields, 'versions', []) or []],
            "fixVersions": [{"name": v.name, "id": v.id} for v in getattr(issue.fields, 'fixVersions', []) or []],
        }

        try:
            epic_link_field = _find_epic_link_field()
            epic_link_value = getattr(issue.fields, epic_link_field, None)
            if epic_link_value:
                response["epic_link"] = epic_link_value
        except Exception as e:
            logger.warning(f"Failed to extract epic link for {issue_key}: {e}")

        return response

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update issue: {e}")


@router.get("/search_issues", summary="Search Jira issues by JQL query", operation_id="search_issues")
async def search_issues(jql: str, max_results: int = 10):
    """Search Jira issues using a JQL query.

    Results include Agile Hive fields (Team, Teams Involved, Cost of Delay)
    when available on the Jira instance.
    """
    try:
        ah_field_ids = discover_agile_hive_fields(jira)
        issues = jira.search_issues(jql, maxResults=max_results)
        results = []
        for issue in issues:
            item = {
                "key": issue.key,
                "summary": getattr(issue.fields, 'summary', 'N/A'),
                "status": getattr(issue.fields.status, 'name', 'Unknown') if hasattr(issue.fields, 'status') and issue.fields.status else 'Unknown',
                "issuetype": getattr(issue.fields.issuetype, 'name', 'Unknown') if hasattr(issue.fields, 'issuetype') and issue.fields.issuetype else 'Unknown',
            }
            # Append Agile Hive fields if present
            try:
                ah_data = extract_agile_hive_fields(issue, ah_field_ids)
                item.update(ah_data)
            except Exception:
                pass
            results.append(item)
        return {"issues": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to search issues: {e}")


@router.get("/issue/{issue_key}/hierarchy", summary="Get issue hierarchy as markdown tree", operation_id="get_issue_hierarchy")
async def get_issue_hierarchy(issue_key: str, depth: int = 3, exclude_closed: str = "false"):
    """
    Traverse and return the issue hierarchy as a token-efficient markdown outline.

    Parameters:
    - issue_key: The root issue key (e.g., AFTERSALES-203)
    - depth: Maximum depth to traverse (default: 3, max: 5)
    - exclude_closed: If "true", hide issues with Closed/Done/Resolved status
    """
    try:
        exclude_closed = str(exclude_closed).lower() in ("true", "1", "yes")
        depth = max(1, min(depth, 5))

        markdown_output = build_hierarchy_markdown(
            issue_key,
            depth=depth,
            exclude_closed=exclude_closed
        )

        if not markdown_output:
            raise HTTPException(status_code=404, detail=f"Issue {issue_key} not found or has no hierarchy")

        return PlainTextResponse(content=markdown_output, media_type="text/plain")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch hierarchy: {e}")


@router.get("/issue/{issue_key}/roadmap", summary="Get Epic roadmap grouped by PI", operation_id="get_issue_roadmap")
async def get_issue_roadmap(issue_key: str, include_stories: str = "false", exclude_closed: str = "false"):
    """
    Get a PI-based roadmap view for an Epic's features.

    Parameters:
    - issue_key: The Epic key (e.g., AFTERSALES-203)
    - include_stories: "true" to show story completion count per feature
    - exclude_closed: "true" to hide completed features
    """
    try:
        include_stories = str(include_stories).lower() in ("true", "1", "yes")
        exclude_closed = str(exclude_closed).lower() in ("true", "1", "yes")

        markdown_output = build_roadmap_markdown(
            issue_key,
            include_stories=include_stories,
            exclude_closed=exclude_closed
        )

        if not markdown_output:
            raise HTTPException(status_code=404, detail=f"Epic {issue_key} not found or has no features")

        return PlainTextResponse(content=markdown_output, media_type="text/plain")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch roadmap: {e}")
