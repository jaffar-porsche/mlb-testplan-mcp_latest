"""Hierarchy traversal utilities for Epic/Feature/Story trees."""
import logging
from typing import Dict, List, Optional, Set

from config import HIERARCHY_RULES, CLOSED_STATUSES
from client import jira

logger = logging.getLogger(__name__)


class HierarchyStats:
    """Track statistics during hierarchy traversal."""

    def __init__(self):
        self.total = 0
        self.done = 0
        self.by_type: Dict[str, int] = {}
        self.by_status: Dict[str, int] = {}

    def add(self, issue_type: str, status: str):
        self.total += 1
        status_lower = status.lower()
        if status_lower in CLOSED_STATUSES:
            self.done += 1
        self.by_type[issue_type] = self.by_type.get(issue_type, 0) + 1
        self.by_status[status] = self.by_status.get(status, 0) + 1

    def summary(self) -> str:
        if self.total == 0:
            return ""
        pct = int((self.done / self.total) * 100) if self.total > 0 else 0
        type_summary = ", ".join(
            f"{v} {k}s"
            for k, v in sorted(self.by_type.items(), key=lambda x: -x[1])
            if k.lower() not in ["portfolio epic", "epic"]
        )
        return f" | {self.done}/{self.total} done ({pct}%) | {type_summary}"


def get_issue_links(issue_key: str) -> List:
    """Get issue links for a specific issue."""
    try:
        issue = jira.issue(issue_key, fields='issuelinks')
        return getattr(issue.fields, 'issuelinks', []) or []
    except Exception as e:
        logger.warning(f"Failed to get issue links for {issue_key}: {e}")
        return []


def is_closed_status(status: str) -> bool:
    """Check if a status is considered closed."""
    return status.lower() in CLOSED_STATUSES


def get_child_issues(
    issue_key: str,
    parent_type: str,
    exclude_closed: bool = False
) -> List[Dict]:
    """Get child issues via issue links, applying hierarchy type filtering."""
    children = []
    links = get_issue_links(issue_key)

    # Determine allowed child types for this parent
    allowed_types = HIERARCHY_RULES.get(parent_type.lower(), set())

    for link in links:
        try:
            link_type = getattr(link, 'type', None)
            if not link_type:
                continue

            link_name = getattr(link_type, 'name', '').lower()
            outward_desc = getattr(link_type, 'outward', '').lower()
            inward_desc = getattr(link_type, 'inward', '').lower()

            child_issue = None

            # Check for parent-child relationships
            if hasattr(link, 'outwardIssue') and link.outwardIssue:
                if 'child' in outward_desc or link_name in ['parent-child', 'hierarchy']:
                    child_issue = link.outwardIssue
            elif hasattr(link, 'inwardIssue') and link.inwardIssue:
                if 'parent' in inward_desc or link_name in ['parent-child', 'hierarchy']:
                    child_issue = link.inwardIssue

            if child_issue:
                child_type = getattr(child_issue.fields.issuetype, 'name', 'Unknown').lower()
                child_status = (
                    getattr(child_issue.fields.status, 'name', 'Unknown')
                    if hasattr(child_issue.fields, 'status') and child_issue.fields.status
                    else 'Unknown'
                )

                # Apply type filtering if rules exist, otherwise allow all
                if not allowed_types or child_type in allowed_types:
                    # Apply closed filter if requested
                    if exclude_closed and is_closed_status(child_status):
                        continue
                    children.append({
                        "key": child_issue.key,
                        "summary": getattr(child_issue.fields, 'summary', 'N/A'),
                        "status": child_status,
                        "issuetype": getattr(child_issue.fields.issuetype, 'name', 'Unknown')
                    })
        except Exception as e:
            logger.warning(f"Error processing link for {issue_key}: {e}")
            continue

    return children


def build_hierarchy_markdown(
    issue_key: str,
    depth: int = 3,
    current_depth: int = 0,
    visited: Optional[Set[str]] = None,
    exclude_closed: bool = False,
    stats: Optional[HierarchyStats] = None,
    is_root: bool = True
) -> str:
    """Recursively build markdown hierarchy tree."""
    if visited is None:
        visited = set()
    if stats is None:
        stats = HierarchyStats()

    # Prevent infinite loops
    if issue_key in visited or current_depth > depth:
        return ""
    visited.add(issue_key)

    lines = []
    indent = "  " * current_depth

    try:
        issue = jira.issue(issue_key)
        summary = getattr(issue.fields, 'summary', 'N/A')
        status = (
            getattr(issue.fields.status, 'name', 'Unknown')
            if hasattr(issue.fields, 'status') and issue.fields.status
            else 'Unknown'
        )
        issue_type = getattr(issue.fields.issuetype, 'name', 'Unknown')

        # Skip closed issues if filter is enabled (but always show root)
        if exclude_closed and is_closed_status(status) and not is_root:
            return ""

        # Track stats (excluding root)
        if not is_root:
            stats.add(issue_type, status)

        # Build the line - root gets stats appended at the end
        line = f"{indent}{issue_key}: {summary} ({status}) [{issue_type}]"

        # Get and process children first to collect stats
        child_lines = []
        if current_depth < depth:
            children = get_child_issues(issue_key, issue_type, exclude_closed=exclude_closed)
            for child in children:
                child_output = build_hierarchy_markdown(
                    child["key"],
                    depth=depth,
                    current_depth=current_depth + 1,
                    visited=visited,
                    exclude_closed=exclude_closed,
                    stats=stats,
                    is_root=False
                )
                if child_output:
                    child_lines.append(child_output)

        # Append stats to root line
        if is_root:
            line += stats.summary()

        lines.append(line)
        lines.extend(child_lines)

    except Exception as e:
        logger.warning(f"Failed to fetch issue {issue_key}: {e}")
        lines.append(f"{indent}{issue_key}: [Error fetching issue]")

    return "\n".join(lines)


def get_feature_with_versions(feature_key: str, include_stories: bool = False) -> Optional[Dict]:
    """Get feature details including version info and optionally story counts."""
    try:
        issue = jira.issue(feature_key)

        fix_versions = []
        affected_versions = []

        if hasattr(issue.fields, 'fixVersions') and issue.fields.fixVersions:
            fix_versions = [v.name for v in issue.fields.fixVersions]

        if hasattr(issue.fields, 'versions') and issue.fields.versions:
            affected_versions = [v.name for v in issue.fields.versions]

        feature_data = {
            "key": issue.key,
            "summary": getattr(issue.fields, 'summary', 'N/A'),
            "status": (
                getattr(issue.fields.status, 'name', 'Unknown')
                if hasattr(issue.fields, 'status') and issue.fields.status
                else 'Unknown'
            ),
            "issuetype": getattr(issue.fields.issuetype, 'name', 'Unknown'),
            "fix_versions": fix_versions,
            "affected_versions": affected_versions,
            "is_committed": len(fix_versions) > 0
        }

        # Optionally get story counts
        if include_stories:
            children = get_child_issues(feature_key, feature_data["issuetype"])
            total_stories = len(children)
            done_stories = sum(1 for c in children if c["status"].lower() in CLOSED_STATUSES)
            feature_data["story_count"] = f"{done_stories}/{total_stories}"

        return feature_data
    except Exception as e:
        logger.warning(f"Failed to get feature {feature_key}: {e}")
        return None


def build_roadmap_markdown(
    epic_key: str,
    include_stories: bool = False,
    exclude_closed: bool = False
) -> str:
    """Build a PI-based roadmap for an Epic's features."""
    lines = []

    try:
        # Get the Epic
        epic = jira.issue(epic_key)
        epic_summary = getattr(epic.fields, 'summary', 'N/A')

        # Get all Features under this Epic
        features = get_child_issues(epic_key, "portfolio epic", exclude_closed=False)
        if not features:
            features = get_child_issues(epic_key, "epic", exclude_closed=False)

        # Collect feature details with versions
        feature_details = []
        for f in features:
            detail = get_feature_with_versions(f["key"], include_stories=include_stories)
            if detail:
                # Apply closed filter if requested
                if exclude_closed and detail["status"].lower() in CLOSED_STATUSES:
                    continue
                feature_details.append(detail)

        # Group features by PI
        # Priority: fix_versions (committed) > affected_versions (planned) > unversioned
        pi_groups: Dict[str, Dict[str, List]] = {}
        unversioned = []

        for feature in feature_details:
            # Determine the PI for this feature
            if feature["fix_versions"]:
                # Committed - use fixVersion
                for pi in feature["fix_versions"]:
                    if pi not in pi_groups:
                        pi_groups[pi] = {"committed": [], "planned": []}
                    pi_groups[pi]["committed"].append(feature)
            elif feature["affected_versions"]:
                # Planned - use affectedVersion
                for pi in feature["affected_versions"]:
                    if pi not in pi_groups:
                        pi_groups[pi] = {"committed": [], "planned": []}
                    pi_groups[pi]["planned"].append(feature)
            else:
                unversioned.append(feature)

        # Sort PIs (they follow PI-YY.Q format, so string sort works)
        sorted_pis = sorted(pi_groups.keys())

        # Build header
        total_features = len(feature_details)
        total_pis = len(sorted_pis) + (1 if unversioned else 0)
        lines.append(f"{epic_key}: {epic_summary} Roadmap | {total_features} features across {total_pis} PIs")
        lines.append("")

        # Build PI sections
        for pi in sorted_pis:
            group = pi_groups[pi]
            committed = group["committed"]
            planned = group["planned"]

            # Determine PI status
            all_features = committed + planned
            done_count = sum(1 for f in all_features if f["status"].lower() in CLOSED_STATUSES)
            total_count = len(all_features)

            if committed:
                pi_label = f"## {pi} (Committed)"
            else:
                pi_label = f"## {pi} (Planned)"

            lines.append(f"{pi_label} | {done_count}/{total_count} done")

            # List committed features first
            for feature in committed:
                line = f"  ✓ {feature['key']}: {feature['summary']} ({feature['status']})"
                if include_stories and "story_count" in feature:
                    line += f" [{feature['story_count']} stories]"
                lines.append(line)

            # Then planned features
            for feature in planned:
                line = f"  ○ {feature['key']}: {feature['summary']} ({feature['status']})"
                if include_stories and "story_count" in feature:
                    line += f" [{feature['story_count']} stories]"
                lines.append(line)

            lines.append("")

        # Unversioned section
        if unversioned:
            done_count = sum(1 for f in unversioned if f["status"].lower() in CLOSED_STATUSES)
            lines.append(f"## Unversioned | {done_count}/{len(unversioned)} done")
            for feature in unversioned:
                line = f"  ○ {feature['key']}: {feature['summary']} ({feature['status']})"
                if include_stories and "story_count" in feature:
                    line += f" [{feature['story_count']} stories]"
                lines.append(line)
            lines.append("")

        return "\n".join(lines)

    except Exception as e:
        logger.warning(f"Failed to build roadmap for {epic_key}: {e}")
        return f"{epic_key}: [Error building roadmap: {e}]"
