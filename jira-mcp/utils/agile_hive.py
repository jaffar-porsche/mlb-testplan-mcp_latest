"""Agile Hive field discovery and extraction utilities.

Field architecture:
- Team (Leading Team): Uses Atlassian Teams IDs. Values come with names.
  Resolvable via /rest/teams-api/1.0/team/{id}.
- Teams Involved: Uses Agile Hive internal IDs. Values are bare numeric strings
  WITHOUT names. The Agile Hive REST API requires session auth (not PAT), so
  these IDs cannot be resolved directly. However, team names CAN be extracted
  from Jira issue properties:
    - AgileHiveProgramBoard stores team names per PI in
      planningIntervalSprintInfoByPiId.{piId}.team
    - For features with exactly one Teams Involved entry, this gives a 1:1
      mapping from the Agile Hive ID to the team name.
"""

import logging
from typing import Optional

from client import http_session

logger = logging.getLogger(__name__)

# Cache for discovered field IDs (populated once per server lifetime)
_field_cache: Optional[dict] = None

# Cache mapping team ID → team name (built from Leading Team field which
# includes names, used to enrich Teams Involved which only returns IDs)
_team_name_cache: dict[str, str] = {}


def discover_agile_hive_fields(jira_client) -> dict:
    """Discover Agile Hive custom field IDs from Jira field metadata.

    Queries jira.fields() and matches by name to find:
    - Team (Leading Team)
    - Teams Involved
    - Cost of Delay

    Returns dict with keys: team, teams_involved, cost_of_delay
    Each value is the customfield_XXXXX ID or None if not found.
    """
    global _field_cache
    if _field_cache is not None:
        return _field_cache

    result = {
        "team": None,
        "teams_involved": None,
        "cost_of_delay": None,
    }

    try:
        all_fields = jira_client.fields()
        for field in all_fields:
            name_lower = field["name"].lower().strip()
            field_id = field["id"]

            if name_lower == "team":
                result["team"] = field_id
                logger.info(f"Discovered Team field: {field_id}")
            elif name_lower == "teams involved":
                result["teams_involved"] = field_id
                logger.info(f"Discovered Teams Involved field: {field_id}")
            elif name_lower == "cost of delay":
                result["cost_of_delay"] = field_id
                logger.info(f"Discovered Cost of Delay field: {field_id}")
    except Exception as e:
        logger.warning(f"Failed to discover Agile Hive fields: {e}")

    _field_cache = result
    return result


def _parse_team_value(value) -> Optional[dict]:
    """Parse a single team value from a custom field into {id, name}."""
    if value is None:
        return None

    # Object with .name attribute (jira Resource)
    if hasattr(value, "name"):
        return {
            "id": str(getattr(value, "id", "")),
            "name": value.name,
        }

    # Dict with name/value keys
    if isinstance(value, dict):
        name = value.get("name") or value.get("value") or value.get("displayName")
        return {
            "id": str(value.get("id", "")),
            "name": name,
        }

    # Primitive (string or number) — likely just an ID
    return {"id": str(value), "name": None}


def _register_team_name(team_id: str, name: Optional[str]):
    """Cache a team ID → name mapping for cross-referencing."""
    if team_id and name:
        _team_name_cache[team_id] = name


def _lookup_team_name(team_id: str) -> Optional[str]:
    """Look up a cached team name by ID."""
    return _team_name_cache.get(team_id)


def resolve_team_name_via_api(
    team_id: str, base_url: str, pat: str, proxies=None
) -> Optional[str]:
    """Resolve a team name via the Atlassian Teams REST API.

    Works for Leading Team IDs (Atlassian Teams). Returns None for
    Agile Hive Teams Involved IDs (different ID space).

    Note: ``pat`` and ``proxies`` are accepted for API compatibility but
    the shared ``http_session`` (which already carries auth) is used instead.
    """
    cached = _lookup_team_name(team_id)
    if cached:
        return cached

    try:
        r = http_session.get(
            f"{base_url}/rest/teams-api/1.0/team/{team_id}",
            timeout=10,
        )
        if r.status_code == 200:
            data = r.json()
            name = data.get("title")
            if name:
                _register_team_name(team_id, name)
                return name
    except Exception as e:
        logger.debug(f"Teams API lookup failed for {team_id}: {e}")
    return None


def _resolve_teams_via_issue_properties(
    issue_keys: list[str],
    teams_involved_ids: dict[str, list[str]],
    base_url: str,
    pat: str,
    proxies=None,
):
    """Resolve Teams Involved IDs to names via AgileHiveProgramBoard issue properties.

    For features with exactly ONE Teams Involved entry, the ProgramBoard property
    contains the team name in planningIntervalSprintInfoByPiId.{piId}.team,
    giving a direct 1:1 mapping from Agile Hive ID to team name.

    Note: ``pat`` and ``proxies`` are accepted for API compatibility but
    the shared ``http_session`` (which already carries auth) is used instead.

    Args:
        issue_keys: List of issue keys to check properties for.
        teams_involved_ids: Mapping of issue_key → list of Teams Involved IDs.
        base_url: Jira base URL.
        pat: Personal access token (unused, kept for API compat).
        proxies: Optional proxy config (unused, kept for API compat).
    """
    for key in issue_keys:
        ti_ids = teams_involved_ids.get(key, [])
        # Only useful for single-involved features (1:1 mapping)
        if len(ti_ids) != 1:
            continue
        ti_id = ti_ids[0]
        # Skip if already resolved
        if _lookup_team_name(ti_id):
            continue

        try:
            r = http_session.get(
                f"{base_url}/rest/api/2/issue/{key}/properties/AgileHiveProgramBoard",
                timeout=10,
            )
            if r.status_code != 200:
                continue
            data = r.json().get("value", {})
            pi_info = data.get("planningIntervalSprintInfoByPiId", {})
            # Extract team name from any PI entry (they all reference the same team)
            for _pi_id, pi_data in pi_info.items():
                team_name = pi_data.get("team")
                if team_name:
                    _register_team_name(ti_id, team_name)
                    logger.debug(
                        f"Resolved Teams Involved {ti_id} → {team_name} via {key}"
                    )
                    break
        except Exception as e:
            logger.debug(f"Issue property lookup failed for {key}: {e}")


def build_team_name_cache(
    jira_client,
    project_key: str,
    field_ids: dict,
    base_url: str = None,
    pat: str = None,
    proxies=None,
):
    """Scan features in a project to build the team ID → name mapping.

    Phase 1: Extract names from Leading Team field (which includes names).
    Phase 2: For Teams Involved IDs still without names, resolve via
             AgileHiveProgramBoard issue properties on single-involved features.
    """
    jql = (
        f"project = {project_key} "
        f"AND issuetype in (Feature) "
        f'AND status not in ("Funnel", "Closed", "Resolved")'
    )

    team_field = field_ids.get("team")
    teams_field = field_ids.get("teams_involved")
    fields_to_fetch = ["summary"]
    if team_field:
        fields_to_fetch.append(team_field)
    if teams_field:
        fields_to_fetch.append(teams_field)

    if not team_field and not teams_field:
        return

    try:
        issues = jira_client.search_issues(
            jql, maxResults=200, fields=",".join(fields_to_fetch)
        )
    except Exception as e:
        logger.warning(f"Failed to build team name cache: {e}")
        return

    # Phase 1: Leading Team names (directly available)
    for issue in issues:
        if team_field:
            raw = getattr(issue.fields, team_field, None)
            if raw is not None:
                parsed = _parse_team_value(raw)
                if parsed and parsed.get("id") and parsed.get("name"):
                    _register_team_name(parsed["id"], parsed["name"])

    # Phase 2: Resolve Teams Involved IDs via issue properties
    if teams_field and base_url and pat:
        # Collect issue keys and their Teams Involved IDs
        issue_keys = []
        teams_involved_ids: dict[str, list[str]] = {}
        for issue in issues:
            raw = getattr(issue.fields, teams_field, None)
            if raw is None:
                continue
            if isinstance(raw, list):
                ids = [str(v) for v in raw]
            else:
                ids = [str(raw)]
            # Only consider features where at least one ID is unresolved
            unresolved = [tid for tid in ids if not _lookup_team_name(tid)]
            if unresolved:
                issue_keys.append(issue.key)
                teams_involved_ids[issue.key] = ids

        if issue_keys:
            _resolve_teams_via_issue_properties(
                issue_keys, teams_involved_ids, base_url, pat, proxies
            )

    logger.info(
        f"Built team name cache: {len(_team_name_cache)} teams from {project_key}"
    )


def extract_agile_hive_fields(issue, field_ids: dict) -> dict:
    """Extract Agile Hive fields from an issue.

    Args:
        issue: Jira issue object
        field_ids: Dict from discover_agile_hive_fields()

    Returns:
        Dict with team, teams_involved, cost_of_delay (only present if non-null)
    """
    result = {}

    # Team (single value — Leading Team)
    team_field = field_ids.get("team")
    if team_field:
        raw = getattr(issue.fields, team_field, None)
        if raw is not None:
            parsed = _parse_team_value(raw)
            if parsed:
                # Cache the name for cross-referencing
                _register_team_name(parsed.get("id", ""), parsed.get("name"))
                result["team"] = parsed

    # Teams Involved (multi-value)
    teams_field = field_ids.get("teams_involved")
    if teams_field:
        raw = getattr(issue.fields, teams_field, None)
        if raw is not None:
            if isinstance(raw, list):
                teams = [_parse_team_value(t) for t in raw]
                teams = [t for t in teams if t]
            else:
                parsed = _parse_team_value(raw)
                teams = [parsed] if parsed else []
            # Enrich teams that have no name from the cache
            for t in teams:
                if t.get("id") and not t.get("name"):
                    cached_name = _lookup_team_name(t["id"])
                    if cached_name:
                        t["name"] = cached_name
            if teams:
                result["teams_involved"] = teams

    # Cost of Delay (numeric or object)
    cod_field = field_ids.get("cost_of_delay")
    if cod_field:
        raw = getattr(issue.fields, cod_field, None)
        if raw is not None:
            if hasattr(raw, "name"):
                result["cost_of_delay"] = raw.name
            elif isinstance(raw, dict):
                result["cost_of_delay"] = raw.get("name") or raw.get("value") or raw
            else:
                result["cost_of_delay"] = raw

    return result


def reset_cache():
    """Reset the field discovery cache (useful for testing)."""
    global _field_cache
    _field_cache = None
