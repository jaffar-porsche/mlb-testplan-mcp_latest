# JIRA MCP Server - Complete API Contracts

## Overview
This document provides comprehensive API contracts for all endpoints in the JIRA MCP Server. The server provides full CRUD operations for JIRA issues, including advanced features like epic linking, attachment management, and issue searching.

**Base URL:** `http://localhost:8000`  
**Server:** FastAPI with JIRA Python library integration  
**Authentication:** JIRA Personal Access Token (PAT)

---

## API Endpoints Summary

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/create_issue` | Create a new JIRA issue with optional epic link, components, labels |
| GET | `/issue/{issue_key}` | Retrieve comprehensive issue details (incl. Agile Hive fields) |
| PUT | `/issue/{issue_key}` | Update existing issue fields |
| GET | `/search_issues` | Search issues using JQL queries (incl. Agile Hive fields) |
| GET | `/issue/{issue_key}/hierarchy` | Get issue hierarchy as markdown tree |
| GET | `/issue/{epic_key}/roadmap` | Get Epic roadmap grouped by PI |
| GET | `/teams` | List Agile Hive teams visible in a project's features |
| GET | `/team/features` | Get features for a team by name or ID, filterable by PI |
| GET | `/versions` | List project versions (PIs) with dates and temporal status |
| GET | `/versions/{version_id}/summary` | Build release summary from linked issues grouped by type |
| PUT | `/versions/{version_id}` | Update project version fields (description, dates, status) |
| GET | `/fields` | List all Jira fields (discover custom field IDs) |
| POST | `/issue/{issue_key}/attachments` | Upload file attachment to issue |
| GET | `/issue/{issue_key}/attachments` | List all attachments on issue |
| DELETE | `/issue/{issue_key}/attachments/{attachment_id}` | Delete specific attachment |
| GET | `/board/{board_id}/sprints` | Get sprints from a board with optional state filter |
| GET | `/sprint/{sprint_id}` | Get sprint details |
| POST | `/sprint/{sprint_id}/issue` | Move issues to a sprint |
| DELETE | `/sprint/{sprint_id}/issue` | Remove issues from sprint (move to backlog) |
| GET | `/users/search` | Search users by name, username, or email (optionally scoped to project) |
| GET | `/servicedesks` | List available Jira Service Desk portals |
| GET | `/servicedesk/request/{request_key}` | Get Service Desk request details (status, participants, history) |
| GET | `/servicedesk/request/{request_key}/comments` | Get comments on a Service Desk request |
| POST | `/servicedesk/request/{request_key}/comments` | Add a comment to a Service Desk request |
| GET | `/servicedesk/requests` | Search Service Desk requests by ownership, status, text |
| GET | `/issue/{issue_key}/remotelink` | List remote links (web links) on an issue |
| POST | `/issue/{issue_key}/remotelink` | Add a remote link (web link) to an issue |
| DELETE | `/issue/{issue_key}/remotelink/{link_id}` | Delete a remote link from an issue |
| GET | `/xray/testset/{set_key}/tests` | List tests in an xRay Test Set |
| POST | `/xray/testset/{set_key}/tests` | Add tests to an xRay Test Set |
| DELETE | `/xray/testset/{set_key}/tests/{test_key}` | Remove a test from an xRay Test Set |

---

### 1. Create Issue Endpoint

**Endpoint:** `POST /create_issue`

**Description:** Create a new JIRA issue with optional epic link, components, labels, and assignee

#### Request Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `project_key` | string | ✅ Yes | - | The project key (e.g., "SLIM", "DEVX") |
| `summary` | string | ✅ Yes | - | Issue summary/title |
| `description` | string | ✅ Yes | - | Issue description |
| `issuetype` | string | ❌ No | "Task" | Issue type ("Task", "Bug", "Story", etc.) |
| `epic_link` | string | ❌ No | null | Epic key to link this issue to (e.g., "SLIM-84") |
| `components` | list[string] | ❌ No | null | List of component names (e.g., ["PDDI", "Backend"]) |
| `labels` | list[string] | ❌ No | null | List of labels to add (e.g., ["urgent", "tech-debt"]) |
| `assignee` | string | ❌ No | null | Username to assign the issue to |
| `versions` | list[string] | ❌ No | null | List of affectsVersion names (e.g., ["PI-26.2"]) |
| `fix_versions` | list[string] | ❌ No | null | List of fixVersion names (e.g., ["PI-26.2"]) |

#### Request Examples

**HTTP Request:**
```http
POST /create_issue
Content-Type: application/x-www-form-urlencoded

project_key=SLIM&summary=New+feature&description=Implement+new+functionality&issuetype=Task&epic_link=SLIM-84
```

**cURL Command:**
```bash
curl -X POST "http://localhost:8000/create_issue" \
  -d "project_key=SLIM" \
  -d "summary=New feature implementation" \
  -d "description=Detailed description of the feature" \
  -d "issuetype=Task" \
  -d "epic_link=SLIM-84"
```

**Python Requests:**
```python
import requests

response = requests.post("http://localhost:8000/create_issue", data={
    "project_key": "SLIM",
    "summary": "New feature implementation",
    "description": "Detailed description of the feature",
    "issuetype": "Task",
    "epic_link": "SLIM-84"
})
```

#### Response Format

**Success Response (200):**
```json
{
  "key": "SLIM-89",
  "id": "6206789",
  "url": "https://api.skyway.porsche.com/jira/browse/SLIM-89",
  "epic_link": "SLIM-84"
}
```

**Error Response (500):**
```json
{
  "detail": "Failed to create issue: <error_message>"
}
```

---

### 2. Update Issue Endpoint

**Endpoint:** `PUT /issue/{issue_key}`

**Description:** Update an existing JIRA issue with optional epic link modification

#### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `issue_key` | string | ✅ Yes | The issue key (e.g., "SLIM-89") |

#### Request Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `summary` | string | ❌ No | - | New summary text |
| `description` | string | ❌ No | - | New description text |
| `assignee` | string | ❌ No | - | Username or account ID of assignee (use "Unassigned" to unassign) |
| `status` | string | ❌ No | - | New status name (must match available transitions) |
| `priority` | string | ❌ No | - | New priority ("High", "Medium", "Low", etc.) |
| `labels` | list | ❌ No | - | List of labels to set |
| `comment` | string | ❌ No | - | Add a comment to the issue |
| `transition_comment` | string | ❌ No | - | Comment to include with status transition (required by some workflows like ISMS) |
| `epic_link` | string | ❌ No | - | Epic key to link to, or "remove" to unlink from epic |
| `versions` | list[string] | ❌ No | - | List of affectsVersion names to set (e.g., ["PI-26.2"]). Pass empty list to clear. |
| `fix_versions` | list[string] | ❌ No | - | List of fixVersion names to set (e.g., ["PI-26.2"]). Pass empty list to clear. |

#### Epic Link Parameter Values

| Value | Effect |
|-------|--------|
| `"SLIM-84"` | Links the issue to epic SLIM-84 |
| `"SLIM-54"` | Links the issue to epic SLIM-54 (changes epic if already linked) |
| `"remove"` | Removes the epic link (unlinks from current epic) |
| `null` or omitted | No change to epic link |

#### Request Examples

**Update Epic Link:**
```bash
curl -X PUT "http://localhost:8000/issue/SLIM-89?epic_link=SLIM-84"
```

**Remove Epic Link:**
```bash
curl -X PUT "http://localhost:8000/issue/SLIM-89?epic_link=remove"
```

**Update Multiple Fields Including Epic:**
```bash
curl -X PUT "http://localhost:8000/issue/SLIM-89" \
  -d "summary=Updated summary" \
  -d "priority=High" \
  -d "epic_link=SLIM-84" \
  -d "comment=Updated with new epic link"
```

**Set affectsVersion (PI planning):**
```bash
curl -X PUT "http://localhost:8000/issue/ARTDIAGUPD-1694?versions=PI-26.1"
```

**Clear fixVersions:**
```bash
curl -X PUT "http://localhost:8000/issue/SLIM-89?fix_versions="
```

**Status Transition with Required Comment (e.g., ISMS workflows):**
```bash
curl -X PUT "http://localhost:8000/issue/ISMS-16463" \
  -d "status=I confirm responsibility/criticality/risk" \
  -d "transition_comment=Confirming responsibility. Remediation tracked in PCDSXSU-1763."
```

**Python Requests:**
```python
import requests

# Update epic link
response = requests.put("http://localhost:8000/issue/SLIM-89", params={
    "epic_link": "SLIM-84"
})

# Remove epic link
response = requests.put("http://localhost:8000/issue/SLIM-89", params={
    "epic_link": "remove"
})

# Update multiple fields
response = requests.put("http://localhost:8000/issue/SLIM-89", params={
    "summary": "Updated summary",
    "priority": "High",
    "epic_link": "SLIM-84",
    "comment": "Updated with new epic link"
})
```

#### Response Format

**Success Response (200):**
```json
{
  "success": true,
  "message": "Issue SLIM-89 updated successfully",
  "key": "SLIM-89",
  "summary": "Updated summary",
  "status": "Open",
  "assignee": "John Doe",
  "url": "https://api.skyway.porsche.com/jira/browse/SLIM-89",
  "epic_link": "SLIM-84",
  "versions": [{"name": "PI-26.1", "id": "82213"}],
  "fixVersions": []
}
```

**Error Response (400) - Invalid Version Name:**
```json
{
  "detail": "Version 'PI-99.9' not found in project SLIM. Available versions: PI-25.4, PI-26.1, PI-26.2"
}
```

**Error Response (400) - Invalid Status Transition:**
```json
{
  "detail": "Invalid status transition. Available transitions: In Progress, Done, Closed"
}
```

**Error Response (500) - General Error:**
```json
{
  "detail": "Failed to update issue: <error_message>"
}
```

---

### 3. Get Issue Endpoint (Enhanced with Epic Link)

**Endpoint:** `GET /issue/{issue_key}`

**Description:** Retrieve comprehensive details for a specific JIRA issue including epic link information

#### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `issue_key` | string | ✅ Yes | The issue key (e.g., "SLIM-89") |

#### Request Examples

**cURL Command:**
```bash
curl -X GET "http://localhost:8000/issue/SLIM-89"
```

**Python Requests:**
```python
import requests

response = requests.get("http://localhost:8000/issue/SLIM-89")
issue_details = response.json()
```

#### Response Format with Epic Link

**Success Response (200):**
```json
{
  "key": "SLIM-89",
  "id": "6206789",
  "self": "https://api.skyway.porsche.com/jira/rest/api/2/issue/6206789",
  "url": "https://api.skyway.porsche.com/jira/browse/SLIM-89",
  
  "summary": "Issue summary",
  "description": "Detailed issue description",
  "issuetype": {
    "name": "Task",
    "id": "10001",
    "iconUrl": "https://api.skyway.porsche.com/jira/images/icons/issuetypes/task.png"
  },
  "status": {
    "name": "Open",
    "id": "1",
    "category": "To Do"
  },
  
  "assignee": {
    "displayName": "John Doe",
    "emailAddress": "john.doe@porsche.com",
    "accountId": "557058:f58131cb-b67d-43c7-b30d-6b58b40bd077"
  },
  "reporter": {
    "displayName": "Jane Smith",
    "emailAddress": "jane.smith@porsche.com",
    "accountId": "557058:a25131cb-b67d-43c7-b30d-6b58b40bd089"
  },
  "creator": {
    "displayName": "Jane Smith",
    "emailAddress": "jane.smith@porsche.com"
  },
  
  "created": "2025-11-04T10:30:00.000+0000",
  "updated": "2025-11-04T14:30:00.000+0000",
  "resolutiondate": null,
  "duedate": "2025-11-15T00:00:00.000+0000",
  
  "project": {
    "key": "SLIM",
    "name": "SLIM",
    "id": "10100"
  },
  
  "priority": {
    "name": "Medium",
    "id": "3",
    "iconUrl": "https://api.skyway.porsche.com/jira/images/icons/priorities/medium.svg"
  },
  "resolution": {
    "name": "Unresolved",
    "description": null
  },
  
  "environment": "Production",
  "labels": ["backend", "api", "enhancement"],
  "components": [
    {
      "name": "API",
      "id": "10200"
    }
  ],
  "fixVersions": [
    {
      "name": "v2.1.0",
      "id": "10300",
      "released": false
    }
  ],
  "versions": [
    {
      "name": "v2.0.0",
      "id": "10299",
      "released": true
    }
  ],
  
  "timetracking": {
    "originalEstimate": 28800,
    "remainingEstimate": 14400,
    "timeSpent": 14400
  },
  
  "epic_link": "SLIM-84",
  "epic_details": {
    "key": "SLIM-84",
    "summary": "SLIM@Cloud 2.0 on Azure",
    "status": "Open"
  },
  
  "story_points": 5,
  
  "subtasks": [
    {
      "key": "SLIM-90",
      "summary": "Subtask summary",
      "status": "Open"
    }
  ],
  "parent": null,
  
  "watches": {
    "watchCount": 3,
    "isWatching": true
  },
  "votes": {
    "votes": 2,
    "hasVoted": false
  },
  
  "availableTransitions": [
    {
      "id": "11",
      "name": "In Progress"
    },
    {
      "id": "21",
      "name": "Done"
    }
  ],
  
  "commentsCount": 2,
  "latestComments": [
    {
      "id": "10001",
      "author": "John Doe",
      "body": "Working on this now",
      "created": "2025-11-04T14:00:00.000+0000"
    },
    {
      "id": "10002",
      "author": "Jane Smith",
      "body": "Please prioritize this",
      "created": "2025-11-04T14:30:00.000+0000"
    }
  ]
}
```

**Error Response (500):**
```json
{
  "detail": "Failed to fetch issue: <error_message>"
},
}
```

---

### 4. Search Issues Endpoint

**Endpoint:** `GET /search_issues`

**Description:** Search JIRA issues using JQL (JIRA Query Language)

#### Request Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `jql` | string | ✅ Yes | - | JQL query string (e.g., "project = SLIM AND status = Open") |
| `max_results` | integer | ❌ No | 10 | Maximum number of results to return |

#### Request Examples

**Search by Project:**
```bash
curl -X GET "http://localhost:8000/search_issues?jql=project%20%3D%20SLIM"
```

**Search by Status and Project:**
```bash
curl -X GET "http://localhost:8000/search_issues?jql=project%20%3D%20SLIM%20AND%20status%20%3D%20Open&max_results=20"
```

**Python Requests:**
```python
import requests

# Search for open issues in SLIM project
response = requests.get("http://localhost:8000/search_issues", params={
    "jql": "project = SLIM AND status = Open",
    "max_results": 20
})

# Search for issues assigned to specific user
response = requests.get("http://localhost:8000/search_issues", params={
    "jql": "assignee = currentUser() AND status != Done"
})
```

#### Response Format

**Success Response (200):**
```json
{
  "issues": [
    {
      "key": "SLIM-89",
      "summary": "Issue summary",
      "status": "Open",
      "issuetype": "Task"
    },
    {
      "key": "SLIM-88",
      "summary": "Another issue",
      "status": "In Progress",
      "issuetype": "Bug"
    }
  ]
}
```

**Error Response (500):**
```json
{
  "detail": "Failed to search issues: <error_message>"
}
```

---

### 5. Get Issue Hierarchy Endpoint

**Endpoint:** `GET /issue/{issue_key}/hierarchy`

**Description:** Traverse and return the issue hierarchy as a token-efficient markdown outline. Optimized for LLM consumption with ~3-4x fewer tokens than JSON equivalent.

#### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `issue_key` | string | ✅ Yes | The root issue key (e.g., "AFTERSALES-203") |

#### Query Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `depth` | integer | ❌ No | 3 | Maximum depth to traverse (1-5) |
| `exclude_closed` | boolean | ❌ No | false | Hide issues with Closed/Done/Resolved/Cancelled/Rejected status |

#### Hierarchy Type Filtering Rules

The endpoint applies logical hierarchy rules to prevent circular references:

| Parent Type | Allowed Children |
|-------------|------------------|
| Portfolio Epic | Feature only |
| Epic | Feature, Story, Task |
| Feature | Story, User Story, Task, Enabler |
| Story / User Story | Task, Sub-task |

#### Request Examples

**cURL Command:**
```bash
# Full hierarchy with stats
curl -X GET "http://localhost:8000/issue/AFTERSALES-203/hierarchy?depth=3"

# Only active work (exclude closed items)
curl -X GET "http://localhost:8000/issue/AFTERSALES-203/hierarchy?depth=3&exclude_closed=true"
```

**Python Requests:**
```python
import requests

# Full hierarchy
response = requests.get("http://localhost:8000/issue/AFTERSALES-203/hierarchy", params={
    "depth": 3
})
hierarchy_markdown = response.text

# Only active work
response = requests.get("http://localhost:8000/issue/AFTERSALES-203/hierarchy", params={
    "depth": 2,
    "exclude_closed": True
})
active_work = response.text
```

#### Response Format

**Content-Type:** `text/plain`

**Success Response (200):**
```
AFTERSALES-203: [DSW] PDA/Recommender (Implementing) [Portfolio Epic] | 30/51 done (58%) | 35 Storys, 13 Features, 2 Enablers
  ARTDIAGUPD-1412: [POD] Deeplink to create Job/QLine... (In Progress) [Feature]
    PCDSXRD-1118: User Navigation to PCSS... (In Progress) [Story]
  ARTDIAGUPD-1589: PDA: API to retrieve GFF solution space... (In Progress) [Feature]
    DSWAA-42: Create PDA context service (Resolved) [Story]
    DSWAA-67: Create GFF service for retrieving solution space (Resolved) [Story]
  ARTDIAGUPD-1590: PDA: industrialization in cloud infra (In Progress) [Feature]
    DSWAA-2: Create service for exposing results to FE (In Progress) [Story]
    DSWAA-78: Implement monitoring & logging concept... (In Progress) [Enabler]
```

**Output Format:**
- Root line: `{KEY}: {Summary} ({Status}) [{IssueType}] | {done}/{total} done ({pct}%) | {type breakdown}`
- Child lines: `{indent}{KEY}: {Summary} ({Status}) [{IssueType}]`
- Indentation: 2 spaces per hierarchy level
- Plain text (not JSON) for minimal token usage
- Stats exclude root issue from counts

**Error Response (404):**
```json
{
  "detail": "Issue INVALID-123 not found or has no hierarchy"
}
```

**Error Response (500):**
```json
{
  "detail": "Failed to fetch hierarchy: <error_message>"
}
```

#### Use Cases

1. **Initiative Overview:** Get complete view of Epic → Features → Stories
2. **Sprint Planning:** Understand work breakdown structure
3. **Status Reporting:** See status of all related issues at once
4. **LLM Context:** Provide hierarchy context to AI assistants efficiently

---

### 6. Get Epic Roadmap Endpoint

**Endpoint:** `GET /issue/{epic_key}/roadmap`

**Description:** Get a PI-based roadmap view for an Epic's features, showing commitments by Program Increment.

#### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `epic_key` | string | ✅ Yes | The Epic key (e.g., "AFTERSALES-203") |

#### Query Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `include_stories` | boolean | ❌ No | false | Show story completion count per feature |
| `exclude_closed` | boolean | ❌ No | false | Hide completed features |

#### PI Commitment Semantics

| Field | Meaning |
|-------|---------|
| `fixVersion` set | **Committed** - Team has committed to deliver in this PI |
| `affectedVersion` only | **Planned** - Target PI, not yet committed |
| Neither set | **Unversioned** - Not yet planned |

#### Request Examples

**cURL Command:**
```bash
# Basic roadmap
curl -X GET "http://localhost:8000/issue/AFTERSALES-203/roadmap"

# With story counts and excluding closed features
curl -X GET "http://localhost:8000/issue/AFTERSALES-203/roadmap?include_stories=true&exclude_closed=true"
```

**Python Requests:**
```python
import requests

# Full roadmap with story counts
response = requests.get("http://localhost:8000/issue/AFTERSALES-203/roadmap", params={
    "include_stories": True
})
roadmap = response.text

# Active work only
response = requests.get("http://localhost:8000/issue/AFTERSALES-203/roadmap", params={
    "exclude_closed": True
})
active_roadmap = response.text
```

#### Response Format

**Content-Type:** `text/plain`

**Success Response (200):**
```
AFTERSALES-203: [DSW] PDA/Recommender Roadmap | 13 features across 4 PIs

## PI-25.4 (Committed) | 1/5 done
  ✓ ARTDIAGUPD-1412: Deeplink to PCSS (In Progress) [4/6 stories]
  ✓ ARTDIAGUPD-1589: API to retrieve GFF (In Progress) [5/5 stories]
  ✓ ARTDIAGUPD-1590: Industrialization (In Progress) [6/13 stories]

## PI-26.1 (Planned) | 0/3 done
  ○ ARTDIAGUPD-1659: Add tool for VAL warnings (Funnel)
  ○ ARTDIAGUPD-1660: Enable H2 recommender (Funnel)

## Unversioned | 0/1 done
  ○ ARTDIAGUPD-1661: Display PDA results (Funnel)
```

**Output Format:**
- Header: `{EPIC_KEY}: {Summary} Roadmap | {count} features across {count} PIs`
- PI Section: `## {PI} (Committed|Planned) | {done}/{total} done`
- Feature line: `{✓|○} {KEY}: {Summary} ({Status}) [{stories}]`
- ✓ = Committed (fixVersion set)
- ○ = Planned or Unversioned

#### Use Cases

1. **PI Planning:** See what's committed vs planned for upcoming PIs
2. **Roadmap Reviews:** Understand feature distribution across time
3. **Progress Tracking:** Monitor completion status per PI
4. **LLM Context:** Provide roadmap context for planning discussions

---

### 7. List Teams Endpoint

**Endpoint:** `GET /teams`

**Description:** List distinct Agile Hive teams found across features in a project. Team names are resolved via Leading Team field values and AgileHiveProgramBoard issue properties.

#### Query Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `project_key` | string | Yes | - | Project key to scan for teams (e.g. ARTDIAGUPD) |
| `max_results` | integer | No | 100 | Max features to scan |

#### Request Examples

```bash
curl -X GET "http://localhost:8000/teams?project_key=ARTDIAGUPD"
```

#### Response Format

**Success Response (200):**
```json
{
  "project": "ARTDIAGUPD",
  "field_ids": {
    "team": "customfield_10201",
    "teams_involved": "customfield_17319"
  },
  "total_teams": 22,
  "teams": [
    {
      "id": "17433",
      "name": "DSW - PTES",
      "role": "teams_involved",
      "feature_count": 28
    },
    {
      "id": "18947",
      "name": "DSW - Diagnostics",
      "role": "leading_team",
      "feature_count": 18
    }
  ]
}
```

#### Team Name Resolution

Names are resolved through a multi-phase approach:
1. **Leading Team field** — returns names directly (Atlassian Teams IDs)
2. **AgileHiveProgramBoard issue properties** — for features with exactly one Teams Involved entry, the team name is extracted from `planningIntervalSprintInfoByPiId.{piId}.team`
3. **Atlassian Teams API** — fallback for individual ID lookups via `/rest/teams-api/1.0/team/{id}`

Teams Involved IDs that only appear in multi-involved features may remain unnamed.

---

### 8. Get Team Features Endpoint

**Endpoint:** `GET /team/features`

**Description:** Get features assigned to or involving a specific team. Accepts team name (substring match) or numeric Agile Hive team ID. Automatically routes to the correct JQL field based on ID space.

#### Query Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `team` | string | Yes | - | Team name or Agile Hive team ID |
| `project_key` | string | No | ARTDIAGUPD | Jira project key |
| `pi` | string | No | null | Program Increment version name (e.g. PI-26.1) |
| `include_closed` | boolean | No | false | Include Funnel/Closed/Resolved features |
| `max_results` | integer | No | 50 | Max results to return |

#### Request Examples

```bash
# By name (works for both Leading Team and Teams Involved)
curl -X GET "http://localhost:8000/team/features?team=Coding+Cult&project_key=ARTDIAGUPD"

# By name with PI filter
curl -X GET "http://localhost:8000/team/features?team=Diagnostics&pi=PI-25.4"

# By numeric ID
curl -X GET "http://localhost:8000/team/features?team=32306&project_key=ARTDIAGUPD"
```

#### Response Format

**Success Response (200):**
```json
{
  "team_id": "32306",
  "team_query": "Coding Cult",
  "project": "ARTDIAGUPD",
  "pi": null,
  "jql": "project = ARTDIAGUPD AND issuetype in (Feature) AND (\"Teams Involved\" in (32306)) AND ...",
  "total": 3,
  "features": [
    {
      "key": "ARTDIAGUPD-1579",
      "summary": "Feature title",
      "status": "In Progress",
      "priority": "Medium",
      "fixVersions": ["PI-25.4"],
      "url": "https://api.skyway.porsche.com/jira/browse/ARTDIAGUPD-1579",
      "team": {"id": "18947", "name": "DSW - Diagnostics"},
      "teams_involved": [{"id": "32306", "name": "DSW - Coding Cult"}],
      "cost_of_delay": "26.0"
    }
  ]
}
```

#### ID Space Handling

The Team (Leading Team) and Teams Involved fields use different ID namespaces:
- **Leading Team** — Atlassian Teams IDs, used with `Team = {id}` in JQL
- **Teams Involved** — Agile Hive IDs, used with `"Teams Involved" in ({id})` in JQL

When a name is provided, the endpoint resolves it against both fields and routes to the correct JQL clause. When a numeric ID is provided, it probes the Atlassian Teams API to determine the source field.

**Error Response (404):**
```json
{
  "detail": "Team 'Unknown Team' not found in project ARTDIAGUPD. Use GET /teams?project_key=ARTDIAGUPD to list available teams."
}
```

---

### 9. List Versions (Program Increments) Endpoint

**Endpoint:** `GET /versions`

**Description:** List project versions with release dates and temporal status annotations. Each PI version is annotated as past/current/next/future based on today's date. Use this to resolve natural language like "next PI" or "current PI" to the exact version name needed for `/team/features` queries.

#### Query Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `project_key` | string | No | ARTDIAGUPD | Jira project key |
| `pi_only` | boolean | No | true | Only return PI versions (matching PI-YY.Q pattern) |

#### Request Examples

```bash
# PI versions only (default)
curl -X GET "http://localhost:8000/versions?project_key=ARTDIAGUPD"

# All versions including non-PI
curl -X GET "http://localhost:8000/versions?project_key=ARTDIAGUPD&pi_only=false"
```

#### Response Format

**Success Response (200):**
```json
{
  "project": "ARTDIAGUPD",
  "today": "2026-02-25",
  "total": 16,
  "versions": [
    {
      "id": "65871",
      "name": "PI-25.4",
      "description": "Porsche 2025.49",
      "startDate": "2025-12-05",
      "releaseDate": "2026-03-23",
      "released": false,
      "status": "current"
    },
    {
      "id": "82213",
      "name": "PI-26.1",
      "description": "Porsche 2026.11",
      "startDate": "2026-03-27",
      "releaseDate": "2026-06-15",
      "released": false,
      "status": "next"
    }
  ]
}
```

#### Status Values

| Status | Meaning |
|--------|---------|
| `past` | Release date is in the past or version is marked released |
| `current` | Start date <= today <= release date |
| `next` | The first future PI after the current one |
| `future` | All other upcoming PIs |

#### Typical Workflow

```bash
# 1. Find the next PI
curl -s "http://localhost:8000/versions" | jq '.versions[] | select(.status == "next")'
# → PI-26.1

# 2. Get features for a team in that PI
curl -s "http://localhost:8000/team/features?team=Diagnostics&pi=PI-26.1"
```

---

### 10. Get Version Release Summary Endpoint

**Endpoint:** `GET /versions/{version_id}/summary`

**Description:** Build a release summary for a version based on its linked issues. Fetches all issues with that `fixVersion`, groups them by issue type, and produces a structured plain-text summary. Use this to generate release descriptions, then optionally refine with an LLM before calling Update Version.

#### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `version_id` | string | Yes | The version ID (numeric, from list_versions response) |

#### Query Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `project_key` | string | Yes | - | Jira project key (e.g. GFS, ARTDIAGUPD) |
| `max_length` | integer | No | 16384 | Maximum length of the generated summary in characters. Jira version description field limit is 16,384 bytes. |

#### Request Examples

```bash
# Basic summary
curl -X GET "http://localhost:8000/versions/110436/summary?project_key=GFS"

# With custom max length
curl -X GET "http://localhost:8000/versions/110436/summary?project_key=GFS&max_length=4096"
```

#### Response Format

**Success Response (200):**
```json
{
  "version_id": "110436",
  "version_name": "JRV-25.37-7",
  "project": "GFS",
  "issue_count": 18,
  "issues_by_type": {"Enabler": 1, "Story": 17},
  "summary_text": "Release JRV-25.37-7\n\nEnabler (1):\n  - GFS-19598: Rotate DB Credentials Prod [Closed]\n\nStory (17):\n  - GFS-18968: Upgrade all lambdas to NodeJS22 [Closed]\n  ...",
  "summary_length": 1458,
  "max_length": 16384,
  "truncated": false,
  "issues": [
    {
      "key": "GFS-19598",
      "summary": "Rotate DB Credentials Prod",
      "status": "Closed",
      "issuetype": "Enabler",
      "priority": "Medium"
    }
  ]
}
```

| Field | Type | Description |
|-------|------|-------------|
| `version_id` | string | The version ID |
| `version_name` | string | Version display name |
| `project` | string | Jira project key |
| `issue_count` | integer | Total number of linked issues |
| `issues_by_type` | object | Map of issue type name → count |
| `summary_text` | string | Structured plain-text summary grouped by issue type |
| `summary_length` | integer | Length of summary_text in characters |
| `max_length` | integer | The max_length parameter that was applied |
| `truncated` | boolean | Whether the summary was truncated to fit max_length |
| `issues` | list | Raw issue list with key, summary, status, issuetype, priority |

**Error Response (500) — Version not found:**
```json
{
  "detail": "Failed to fetch version: Version not found"
}
```

**Error Response (500) — Issue search failure:**
```json
{
  "detail": "Failed to search issues for version: JQL syntax error"
}
```

#### Typical Workflow

```bash
# 1. Find the version ID
curl -s "http://localhost:8000/versions?project_key=GFS&pi_only=false" | jq '.versions[] | {id, name}'

# 2. Get the release summary
curl -s "http://localhost:8000/versions/110436/summary?project_key=GFS"

# 3. Update version description with the summary (or an AI-refined version)
curl -X PUT "http://localhost:8000/versions/110436?description=NodeJS+22+upgrade,+logging+overhaul,+DB+key+rotation"
```

---

### 11. Update Version Endpoint

**Endpoint:** `PUT /versions/{version_id}`

**Description:** Update an existing Jira project version (release). Only provided fields are updated; omitted fields remain unchanged. Use this to set version descriptions (e.g. from Get Version Release Summary), change dates, or mark versions as released/archived.

#### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `version_id` | string | Yes | The version ID (numeric, from list_versions response) |

#### Query Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `description` | string | No | null | New description text |
| `name` | string | No | null | New version name |
| `released` | boolean | No | null | Mark as released (true) or unreleased (false) |
| `archived` | boolean | No | null | Mark as archived (true) or unarchived (false) |
| `release_date` | string | No | null | Release date in YYYY-MM-DD format |
| `start_date` | string | No | null | Start date in YYYY-MM-DD format |

At least one field must be provided.

#### Request Examples

```bash
# Update description only
curl -X PUT "http://localhost:8000/versions/110436?description=NodeJS+22+upgrade,+logging+overhaul,+DB+key+rotation"

# Mark as released with a date
curl -X PUT "http://localhost:8000/versions/110436?released=true&release_date=2025-11-03"

# Update multiple fields
curl -X PUT "http://localhost:8000/versions/110436?description=Updated&released=false&release_date=2026-01-01"
```

#### Response Format

**Success Response (200):**
```json
{
  "id": "110436",
  "name": "JRV-25.37-7",
  "description": "NodeJS 22 upgrade, logging overhaul, DB key rotation",
  "startDate": null,
  "releaseDate": "2025-11-03",
  "released": true,
  "archived": false,
  "updated_fields": ["description"]
}
```

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | The version ID |
| `name` | string | Version display name |
| `description` | string | Current description (after update) |
| `startDate` | string/null | Start date (YYYY-MM-DD) or null |
| `releaseDate` | string/null | Release date (YYYY-MM-DD) or null |
| `released` | boolean | Whether the version is marked as released |
| `archived` | boolean | Whether the version is archived |
| `updated_fields` | list | List of field names that were updated |

**Error Response (400) — No fields provided:**
```json
{
  "detail": "No fields to update. Provide at least one of: description, name, released, archived, release_date, start_date."
}
```

**Error Response (500) — Jira API failure:**
```json
{
  "detail": "Failed to update version: Permission denied"
}
```

---

### 12. List Fields Endpoint

**Endpoint:** `GET /fields`

**Description:** List all Jira fields with their IDs and names. Useful for discovering custom field IDs for Agile Hive fields, story points, or any other custom field.

#### Query Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `search` | string | No | null | Filter fields by name (case-insensitive substring match) |

#### Request Examples

```bash
curl -X GET "http://localhost:8000/fields?search=team"
```

#### Response Format

**Success Response (200):**
```json
{
  "total": 2,
  "fields": [
    {
      "id": "customfield_10201",
      "name": "Team",
      "custom": true,
      "schema": {"type": "any", "custom": "com.atlassian.teams:rm-teams-custom-field-team"}
    },
    {
      "id": "customfield_17319",
      "name": "Teams Involved",
      "custom": true,
      "schema": {"type": "any", "custom": "net.seibertmedia.agilehive.agile-hive-plugin:teams-involved"}
    }
  ]
}
```

---

### 13. Upload Attachment Endpoint

**Endpoint:** `POST /issue/{issue_key}/attachments`

**Description:** Upload a file attachment to a JIRA issue

#### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `issue_key` | string | ✅ Yes | The issue key (e.g., "SLIM-89") |

#### Request Body

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `file` | file | ✅ Yes | The file to upload (multipart/form-data) |

#### Request Examples

**cURL Command:**
```bash
curl -X POST "http://localhost:8000/issue/SLIM-89/attachments" \
  -F "file=@/path/to/document.pdf"
```

**Python Requests:**
```python
import requests

# Upload a file
with open("document.pdf", "rb") as file:
    response = requests.post(
        "http://localhost:8000/issue/SLIM-89/attachments",
        files={"file": file}
    )
```

#### Response Format

**Success Response (200):**
```json
{
  "success": true,
  "message": "Attachment uploaded successfully to SLIM-89",
  "attachment": {
    "id": "10123",
    "filename": "document.pdf",
    "size": 1024000,
    "mimeType": "application/pdf",
    "created": "2025-11-04T14:30:00.000+0000",
    "author": "John Doe"
  },
  "issue_url": "https://api.skyway.porsche.com/jira/browse/SLIM-89"
}
```

**Error Response (500):**
```json
{
  "detail": "Failed to upload attachment: <error_message>"
}
```

---

### 14. List Attachments Endpoint

**Endpoint:** `GET /issue/{issue_key}/attachments`

**Description:** Get a list of all attachments on a JIRA issue

#### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `issue_key` | string | ✅ Yes | The issue key (e.g., "SLIM-89") |

#### Request Examples

**cURL Command:**
```bash
curl -X GET "http://localhost:8000/issue/SLIM-89/attachments"
```

**Python Requests:**
```python
import requests

response = requests.get("http://localhost:8000/issue/SLIM-89/attachments")
attachments = response.json()["attachments"]
```

#### Response Format

**Success Response (200):**
```json
{
  "issue_key": "SLIM-89",
  "attachment_count": 2,
  "attachments": [
    {
      "id": "10123",
      "filename": "document.pdf",
      "size": 1024000,
      "mimeType": "application/pdf",
      "created": "2025-11-04T14:30:00.000+0000",
      "author": "John Doe",
      "content_url": "https://api.skyway.porsche.com/jira/secure/attachment/10123/document.pdf"
    },
    {
      "id": "10124",
      "filename": "screenshot.png",
      "size": 256000,
      "mimeType": "image/png",
      "created": "2025-11-04T15:45:00.000+0000",
      "author": "Jane Smith",
      "content_url": "https://api.skyway.porsche.com/jira/secure/attachment/10124/screenshot.png"
    }
  ]
}
```

**Error Response (500):**
```json
{
  "detail": "Failed to list attachments: <error_message>"
}
```

---

### 15. Delete Attachment Endpoint

**Endpoint:** `DELETE /issue/{issue_key}/attachments/{attachment_id}`

**Description:** Delete a specific attachment from a JIRA issue

#### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `issue_key` | string | ✅ Yes | The issue key (e.g., "SLIM-89") |
| `attachment_id` | string | ✅ Yes | The attachment ID to delete |

#### Request Examples

**cURL Command:**
```bash
curl -X DELETE "http://localhost:8000/issue/SLIM-89/attachments/10123"
```

**Python Requests:**
```python
import requests

response = requests.delete("http://localhost:8000/issue/SLIM-89/attachments/10123")
```

#### Response Format

**Success Response (200):**
```json
{
  "success": true,
  "message": "Attachment 'document.pdf' deleted successfully from SLIM-89",
  "attachment_id": "10123"
}
```

**Error Response (500):**
```json
{
  "detail": "Failed to delete attachment: <error_message>"
}
```

---

### 16. Get Board Sprints Endpoint

**Endpoint:** `GET /board/{board_id}/sprints`

**Description:** Get all sprints from a specific JIRA board with optional state filtering. Essential for boards with 50+ sprints where pagination would otherwise hide the active sprint.

#### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `board_id` | string | ✅ Yes | The Agile board ID |

#### Query Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `state` | string | ❌ No | null | Filter by sprint state: "active", "future", "closed" |

#### Request Examples

**cURL Command:**
```bash
# Get active sprint only
curl -X GET "http://localhost:8000/board/108739/sprints?state=active"

# Get all sprints (paginated, max 50)
curl -X GET "http://localhost:8000/board/108739/sprints"
```

#### Response Format

**Success Response (200):**
```json
{
  "board_id": "108739",
  "total_sprints": 1,
  "sprints": [
    {
      "id": 222907,
      "name": "PI-25.4 - S6 - PCDSXWS",
      "state": "active",
      "startDate": "2026-02-11T12:00:00.000+01:00",
      "endDate": "2026-02-25T11:59:00.000+01:00",
      "completeDate": null,
      "originBoardId": 108739,
      "goal": "Sprint goal text (if set)"
    }
  ]
}
```

---

### 17. Get Sprint Details Endpoint

**Endpoint:** `GET /sprint/{sprint_id}`

**Description:** Get detailed information about a specific sprint.

#### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `sprint_id` | string | ✅ Yes | The sprint ID |

#### Response Format

**Success Response (200):**
```json
{
  "id": 222907,
  "name": "PI-25.4 - S6 - PCDSXWS",
  "state": "active",
  "startDate": "2026-02-11T12:00:00.000+01:00",
  "endDate": "2026-02-25T11:59:00.000+01:00",
  "completeDate": null,
  "goal": "Sprint goal text",
  "originBoardId": 108739
}
```

---

### 18. Move Issues to Sprint Endpoint

**Endpoint:** `POST /sprint/{sprint_id}/issue`

**Description:** Move one or more issues to a sprint. Issues will be removed from their current sprint if applicable.

#### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `sprint_id` | string | ✅ Yes | The target sprint ID |

#### Request Body

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `issue_keys` | list[string] | ✅ Yes | List of issue keys to move (e.g., ["PROJ-123", "PROJ-456"]) |

#### Request Examples

**cURL Command:**
```bash
curl -X POST "http://localhost:8000/sprint/222907/issue" \
  -H "Content-Type: application/json" \
  -d '{"issue_keys": ["PCDSXWS-872", "PCDSXWS-873"]}'
```

#### Response Format

**Success Response (200):**
```json
{
  "success": true,
  "message": "Moved 2 issue(s) to sprint 222907",
  "sprint_id": "222907",
  "issues": ["PCDSXWS-872", "PCDSXWS-873"]
}
```

---

### 19. Remove Issues from Sprint Endpoint

**Endpoint:** `DELETE /sprint/{sprint_id}/issue`

**Description:** Remove issues from a sprint and move them to the backlog.

#### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `sprint_id` | string | ✅ Yes | The sprint ID (for context) |

#### Request Body

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `issue_keys` | list[string] | ✅ Yes | List of issue keys to remove |

#### Response Format

**Success Response (200):**
```json
{
  "success": true,
  "message": "Removed 1 issue(s) from sprint to backlog",
  "sprint_id": "222907",
  "issues": ["PCDSXWS-872"]
}
```

---

### 20. Search Users Endpoint

Search for Jira users by name, username, or email. When `project_key` is provided, results are limited to users assignable to that project (respects project permission schemes).

**Endpoint:** `GET /users/search`

#### Query Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `query` | string | Yes | - | Search string (matches display name, username, or email) |
| `project_key` | string | No | null | Only return users assignable to this project |
| `max_results` | integer | No | 10 | Maximum results to return (max: 50) |

#### Request Examples

```bash
# Search all users by name
curl -X GET "http://localhost:8000/users/search?query=sandro"

# Search users assignable to a specific project
curl -X GET "http://localhost:8000/users/search?query=laura&project_key=DSWTEAMSYS"

# Search by email
curl -X GET "http://localhost:8000/users/search?query=matheja&max_results=5"
```

#### Response Format

```json
{
  "total": 1,
  "users": [
    {
      "username": "tjrpp43",
      "displayName": "Manke, Sandro (FDC2_EXTERN)",
      "emailAddress": "net.sandro.manke@mhp.com",
      "active": true
    }
  ]
}
```

#### Use Cases

- **Find assignee username:** Search by display name, get the `username` field to use with `update_issue` assignee parameter
- **Verify project access:** Use `project_key` to confirm a user can be assigned issues in a given project
- **Resolve user identity:** Look up email address or display name from a username

---

### 21. List Service Desks Endpoint

**Endpoint:** `GET /servicedesks`

**Description:** List all Jira Service Desk portals accessible to the current user. The standard Jira REST API (`/rest/api/2/issue`) returns 403 for Service Desk projects (e.g. ITSA) because they use a different permission model. These endpoints use the `/rest/servicedeskapi` API with the same PAT.

#### Query Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `limit` | integer | ❌ No | 50 | Max results per page |
| `start` | integer | ❌ No | 0 | Pagination offset |

#### Request Examples

**cURL Command:**
```bash
curl -X GET "http://localhost:8000/servicedesks?limit=10"
```

**Python Requests:**
```python
import requests

response = requests.get("http://localhost:8000/servicedesks", params={"limit": 10})
desks = response.json()["servicedesks"]
```

#### Response Format

**Success Response (200):**
```json
{
  "total": 50,
  "start": 0,
  "isLastPage": false,
  "servicedesks": [
    {"id": "2001", "projectKey": "ITSA", "projectName": "IT Systemabsicherung"},
    {"id": "741", "projectKey": "CCCAH", "projectName": "Connect Helpdesk"}
  ]
}
```

**Error Response (502):**
```json
{
  "detail": "Service Desk API error: <error_message>"
}
```

---

### 22. Get Service Desk Request Endpoint

**Endpoint:** `GET /servicedesk/request/{request_key}`

**Description:** Retrieve details for a Jira Service Desk request including request type, current status, status history, participants, and reporter. Works for tickets that return 403 via the standard Jira REST API.

#### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `request_key` | string | ✅ Yes | The issue key (e.g., "ITSA-7571") |

#### Request Examples

**cURL Command:**
```bash
curl -X GET "http://localhost:8000/servicedesk/request/ITSA-7571"
```

**Python Requests:**
```python
import requests

response = requests.get("http://localhost:8000/servicedesk/request/ITSA-7571")
request_details = response.json()
```

#### Response Format

**Success Response (200):**
```json
{
  "issueKey": "ITSA-7571",
  "issueId": "6173343",
  "currentStatus": "SDE-Termin und Wrap-up",
  "currentStatusDate": "15/Jan/2026 23:04",
  "requestType": {
    "name": "Sicherheitsfreigabe (DE)",
    "description": "IT security clearance request"
  },
  "serviceDesk": {
    "id": "2001",
    "projectKey": "ITSA",
    "projectName": "IT Systemabsicherung"
  },
  "reporter": {
    "displayName": "Matheja, Ben (FDC2)",
    "emailAddress": "ben.matheja@porsche.de",
    "username": "P341939",
    "active": true
  },
  "createdDate": "24/Oct/2025 15:18",
  "statusHistory": [
    {"status": "SDE-Termin und Wrap-up", "date": "15/Jan/2026 23:04"},
    {"status": "Wartend auf SDE-Termin", "date": "04/Nov/2025 11:34"},
    {"status": "Created", "date": "24/Oct/2025 15:18"}
  ],
  "participants": [
    {
      "displayName": "Hemminger, Dirk (FDC2)",
      "emailAddress": "dirk.hemminger@porsche.de",
      "username": "P328191",
      "active": true
    }
  ],
  "portalUrl": "https://skyway.porsche.com/jira/servicedesk/customer/portal/2001/ITSA-7571"
}
```

**Error Response (404):**
```json
{
  "detail": "Request ITSA-9999 not found in any Service Desk."
}
```

**Error Response (502):**
```json
{
  "detail": "Service Desk API error: <error_message>"
}
```

---

### 23. Get Service Desk Request Comments Endpoint

**Endpoint:** `GET /servicedesk/request/{request_key}/comments`

**Description:** Get comments on a Jira Service Desk request. Can filter to public (customer-visible) comments only or include internal comments.

#### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `request_key` | string | ✅ Yes | The issue key (e.g., "ITSA-7571") |

#### Query Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `public` | boolean | ❌ No | true | If true, return only public (customer-visible) comments. Set to false to include internal comments. |
| `limit` | integer | ❌ No | 50 | Max comments to return |
| `start` | integer | ❌ No | 0 | Pagination offset |

#### Request Examples

**cURL Command:**
```bash
# Public comments only (default)
curl -X GET "http://localhost:8000/servicedesk/request/ITSA-7571/comments?limit=5"

# Include internal comments
curl -X GET "http://localhost:8000/servicedesk/request/ITSA-7571/comments?public=false"
```

**Python Requests:**
```python
import requests

response = requests.get("http://localhost:8000/servicedesk/request/ITSA-7571/comments", params={
    "public": True,
    "limit": 10
})
comments = response.json()["comments"]
```

#### Response Format

**Success Response (200):**
```json
{
  "requestKey": "ITSA-7571",
  "total": 7,
  "isLastPage": true,
  "comments": [
    {
      "id": "9155464",
      "body": "Please authorize the group on all inserted links.",
      "public": true,
      "author": {
        "displayName": "Info Sec Robot",
        "emailAddress": "robot@porsche.de",
        "username": "ITSA.InfoSecRobot",
        "active": true
      },
      "created": "24/Oct/2025 15:19"
    }
  ]
}
```

**Error Response (404):**
```json
{
  "detail": "Request ITSA-9999 not found."
}
```

---

### 24. Add Service Desk Request Comment Endpoint

**Endpoint:** `POST /servicedesk/request/{request_key}/comments`

**Description:** Add a comment to a Jira Service Desk request. This uses the Service Desk API which works for tickets that return 403 via the standard Jira REST API (e.g. SUPPHW, ITSA projects). Supports both public (customer-visible) and internal comments.

#### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `request_key` | string | ✅ Yes | The issue key (e.g., "SUPPHW-97147") |

#### Query Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `body` | string | ✅ Yes | - | The comment text |
| `public` | boolean | ❌ No | true | If true, the comment is visible to the customer. If false, it is an internal comment. |

#### Request Examples

**cURL Command:**
```bash
# Add a public comment
curl -X POST "http://localhost:8000/servicedesk/request/SUPPHW-97147/comments?body=Please+deactivate+the+token&public=true"

# Add an internal comment
curl -X POST "http://localhost:8000/servicedesk/request/SUPPHW-97147/comments?body=Internal+note&public=false"
```

**Python Requests:**
```python
import requests

response = requests.post("http://localhost:8000/servicedesk/request/SUPPHW-97147/comments", params={
    "body": "Please deactivate the token",
    "public": True
})
result = response.json()
```

#### Response Format

**Success Response (200):**
```json
{
  "success": true,
  "message": "Comment added to SUPPHW-97147",
  "comment": {
    "id": "9200001",
    "body": "Please deactivate the token",
    "public": true,
    "author": {
      "displayName": "Matheja, Ben (FDC2)",
      "emailAddress": "ben.matheja@porsche.de",
      "username": "P341939",
      "active": true
    },
    "created": "30/Mar/2026 09:15"
  }
}
```

**Error Response (404):**
```json
{
  "detail": "Request SUPPHW-99999 not found."
}
```

---

### 25. Search Service Desk Requests Endpoint

**Endpoint:** `GET /servicedesk/requests`

**Description:** Search for Service Desk requests by ownership, status, and text. Useful for finding tickets in projects not accessible via the standard Jira REST API (e.g. ITSA).

#### Query Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `service_desk_id` | string | ❌ No | null | Filter by service desk ID (e.g., "2001" for IT Systemabsicherung). Omit to search across all. |
| `request_ownership` | string | ❌ No | OWNED_REQUESTS | Filter by ownership: `OWNED_REQUESTS` (requests you created/reported), `PARTICIPATED_REQUESTS` (participant only, excludes reporter), `ALL_REQUESTS` (creator or participant) |
| `request_status` | string | ❌ No | null | Filter by status: `OPEN_REQUESTS`, `CLOSED_REQUESTS`, `ALL_REQUESTS` |
| `search_term` | string | ❌ No | null | Text to search for in request summaries |
| `limit` | integer | ❌ No | 25 | Max results |
| `start` | integer | ❌ No | 0 | Pagination offset |

#### Request Examples

**cURL Command:**
```bash
# Find your own open requests (reporter=me, default ownership)
curl -X GET "http://localhost:8000/servicedesk/requests?request_status=OPEN_REQUESTS"

# Find all ITSA requests you created
curl -X GET "http://localhost:8000/servicedesk/requests?service_desk_id=2001"

# Search across all service desks
curl -X GET "http://localhost:8000/servicedesk/requests?search_term=security"

# Requests where you are creator or participant
curl -X GET "http://localhost:8000/servicedesk/requests?request_ownership=ALL_REQUESTS&request_status=OPEN_REQUESTS"
```

**Python Requests:**
```python
import requests

# Find ITSA requests
response = requests.get("http://localhost:8000/servicedesk/requests", params={
    "service_desk_id": "2001",
    "request_status": "OPEN_REQUESTS"
})
open_requests = response.json()["requests"]
```

#### Response Format

**Success Response (200):**
```json
{
  "total": 3,
  "start": 0,
  "isLastPage": true,
  "requests": [
    {
      "issueKey": "ITSA-7571",
      "issueId": "6173343",
      "currentStatus": "SDE-Termin und Wrap-up",
      "reporter": {
        "displayName": "Matheja, Ben (FDC2)",
        "emailAddress": "ben.matheja@porsche.de",
        "username": "P341939",
        "active": true
      },
      "createdDate": "24/Oct/2025 15:18"
    }
  ]
}
```

**Error Response (502):**
```json
{
  "detail": "Service Desk API error: <error_message>"
}
```

#### Use Cases

- **Track security clearance requests:** Filter by ITSA service desk to monitor audit tickets
- **Find participated requests:** Default ownership shows all requests you're involved in
- **Search by keyword:** Find specific requests across all service desks

---

### 26. List Remote Links Endpoint

**Endpoint:** `GET /issue/{issue_key}/remotelink`

**Description:** List all remote links (web links) on a Jira issue.

#### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `issue_key` | string | Yes | The issue key (e.g., "PROJ-123") |

#### Success Response (200 OK)

```json
{
  "total": 2,
  "issue_key": "PROJ-123",
  "remote_links": [
    {
      "id": 10001,
      "relationship": "Release Page",
      "url": "https://example.com/release/1.0",
      "title": "Release 1.0",
      "icon_url": "https://example.com/icon.png"
    },
    {
      "id": 10002,
      "relationship": null,
      "url": "https://example.com/docs",
      "title": "Documentation",
      "icon_url": null
    }
  ]
}
```

#### Error Responses

| Status | Description |
|--------|-------------|
| 404 | Issue not found |
| 500 | Failed to list remote links |

---

### 27. Create Remote Link Endpoint

**Endpoint:** `POST /issue/{issue_key}/remotelink`

**Description:** Add a remote link (web link) to a Jira issue.

#### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `issue_key` | string | Yes | The issue key (e.g., "PROJ-123") |

#### Request Body

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `url` | string | Yes | The URL of the remote link |
| `title` | string | Yes | Display title for the link |
| `icon_url` | string | No | URL for a 16x16 icon |
| `relationship` | string | No | Relationship description (e.g., "Release Page") |

#### Success Response (200 OK)

```json
{
  "success": true,
  "message": "Remote link added to PROJ-123",
  "id": 10001,
  "issue_key": "PROJ-123",
  "url": "https://example.com/release/1.0",
  "title": "Release 1.0"
}
```

#### Error Responses

| Status | Description |
|--------|-------------|
| 404 | Issue not found |
| 500 | Failed to create remote link |

---

### 28. Delete Remote Link Endpoint

**Endpoint:** `DELETE /issue/{issue_key}/remotelink/{link_id}`

**Description:** Delete a remote link from a Jira issue by its ID.

#### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `issue_key` | string | Yes | The issue key (e.g., "PROJ-123") |
| `link_id` | string | Yes | The remote link ID (found via list remote links) |

#### Success Response (200 OK)

```json
{
  "success": true,
  "message": "Remote link 10001 deleted from PROJ-123",
  "link_id": "10001"
}
```

#### Error Responses

| Status | Description |
|--------|-------------|
| 404 | Remote link not found on issue |
| 500 | Failed to delete remote link |

---

### 29. List Tests in xRay Test Set Endpoint

**Endpoint:** `GET /xray/testset/{set_key}/tests`

**Description:** Retrieve Tests associated with an xRay Test Set (paginated).

#### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `set_key` | string | Yes | Jira issue key of the Test Set (e.g., `PROJ-321`) |

#### Query Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `page` | integer | No | 1 | Page number (1-indexed) |
| `limit` | integer | No | 50 | Items per page (max 100) |

#### Request Example

```bash
curl -X GET "http://localhost:8000/xray/testset/PROJ-321/tests?page=1&limit=50"
```

#### Response Format

Response is proxied from xRay and contains the list of associated tests.

---

### 30. Add Tests to xRay Test Set Endpoint

**Endpoint:** `POST /xray/testset/{set_key}/tests`

**Description:** Associate one or more Test issues with an xRay Test Set.

#### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `set_key` | string | Yes | Jira issue key of the Test Set |

#### Request Body

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `keys` | list[string] | Yes | List of Test issue keys to add |

#### Request Example

```bash
curl -X POST "http://localhost:8000/xray/testset/PROJ-321/tests" \
  -H "Content-Type: application/json" \
  -d '{"keys": ["PROJ-111", "PROJ-112"]}'
```

#### Response Format

Response is proxied from xRay.

---

### 31. Remove Test from xRay Test Set Endpoint

**Endpoint:** `DELETE /xray/testset/{set_key}/tests/{test_key}`

**Description:** Remove one Test issue from an xRay Test Set.

#### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `set_key` | string | Yes | Jira issue key of the Test Set |
| `test_key` | string | Yes | Jira issue key of the Test to remove |

#### Request Example

```bash
curl -X DELETE "http://localhost:8000/xray/testset/PROJ-321/tests/PROJ-111"
```

#### Response Format

Returns `204 No Content` on success (proxied from xRay).

---

## Epic Link Implementation Details

### Field Configuration
- **Field ID:** `customfield_10000`
- **Field Name:** "Epic Link"
- **Dynamic Detection:** The server dynamically detects the epic link field but falls back to `customfield_10000`
- **Validation:** Epic keys are validated against existing epics in JIRA

### Error Handling
- Invalid epic keys are handled gracefully
- Field permission errors are caught and logged
- Epic link failures don't prevent issue creation/update of other fields

### Supported Operations
1. **Create with Epic Link** - Link issue to epic during creation
2. **Update Epic Link** - Change or set epic link on existing issue
3. **Remove Epic Link** - Unlink issue from epic using "remove" parameter
4. **Retrieve Epic Details** - Get epic information when fetching issue details
5. **Epic Validation** - Automatic validation of epic existence and permissions

---

## Complete Implementation Details

### Server Configuration
- **Framework:** FastAPI with uvicorn ASGI server
- **JIRA Integration:** jira-python library
- **Authentication:** JIRA Personal Access Token (PAT)
- **Proxy Support:** Configured for corporate proxy environments

### Epic Link Configuration
- **Field ID:** `customfield_10000`
- **Field Name:** "Epic Link"
- **Dynamic Detection:** Server dynamically detects epic link field with fallback support
- **Validation:** Epic keys are validated against existing epics in JIRA
- **Error Handling:** Graceful handling of invalid epic keys and field permission errors

### Supported Issue Operations
1. **Create Issues** - Full issue creation with all standard and custom fields
2. **Read Issues** - Comprehensive issue details with expanded information
3. **Update Issues** - Partial updates of any editable field
4. **Search Issues** - JQL-powered search with customizable result limits
5. **Manage Attachments** - Upload, list, and delete file attachments
6. **Epic Linking** - Link/unlink issues to epics with validation

### File Upload Support
- **Supported Formats:** All file types (PDF, images, documents, etc.)
- **Size Limits:** Follows JIRA instance limits
- **Temporary Storage:** Secure temporary file handling with cleanup
- **Metadata:** Full attachment metadata including author and timestamps

### Error Handling
- **HTTP Status Codes:** Proper REST API status codes (200, 400, 500)
- **Detailed Messages:** Descriptive error messages for debugging
- **Graceful Degradation:** Operations continue even if optional features fail
- **Validation:** Input validation with clear error responses

### JQL Search Capabilities
Supports full JIRA Query Language including:
- **Project filters:** `project = SLIM`
- **Status filters:** `status = "In Progress"`
- **User filters:** `assignee = currentUser()`
- **Date ranges:** `created >= -30d`
- **Complex queries:** `project = SLIM AND assignee = currentUser() AND status != Done`

---

## Usage Examples and Workflows

### Common Workflow Examples

#### 1. Create Issue with Epic Link
```bash
# Create a task linked to an epic
curl -X POST "http://localhost:8000/create_issue" \
  -d "project_key=SLIM" \
  -d "summary=Implement user authentication" \
  -d "description=Add OAuth2 authentication to the API" \
  -d "issuetype=Task" \
  -d "epic_link=SLIM-84"
```

#### 2. Upload Documentation and Update Issue
```bash
# First upload documentation
curl -X POST "http://localhost:8000/issue/SLIM-89/attachments" \
  -F "file=@technical_spec.pdf"

# Then update the issue with progress
curl -X PUT "http://localhost:8000/issue/SLIM-89" \
  -d "status=In Progress" \
  -d "comment=Technical specification uploaded and implementation started"
```

#### 3. Search and Bulk Operations
```python
import requests

# Search for all open tasks in SLIM project
response = requests.get("http://localhost:8000/search_issues", params={
    "jql": "project = SLIM AND issuetype = Task AND status = Open",
    "max_results": 50
})

issues = response.json()["issues"]

# Update priority for critical issues
for issue in issues:
    if "critical" in issue["summary"].lower():
        requests.put(f"http://localhost:8000/issue/{issue['key']}", params={
            "priority": "High",
            "comment": "Marked as high priority due to critical nature"
        })
```

#### 4. Epic Management Workflow
```python
import requests

# Create epic
epic_response = requests.post("http://localhost:8000/create_issue", data={
    "project_key": "SLIM",
    "summary": "User Management System",
    "description": "Complete user management functionality",
    "issuetype": "Epic"
})
epic_key = epic_response.json()["key"]

# Create linked tasks
tasks = [
    "User registration API",
    "User login functionality", 
    "Password reset feature",
    "User profile management"
]

for task in tasks:
    requests.post("http://localhost:8000/create_issue", data={
        "project_key": "SLIM",
        "summary": task,
        "description": f"Implement {task} as part of user management system",
        "issuetype": "Task",
        "epic_link": epic_key
    })
```

### Integration Examples

#### Python Client Class
```python
import requests
from typing import Optional, List, Dict

class JiraMCPClient:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
    
    def create_issue(self, project_key: str, summary: str, description: str, 
                    issuetype: str = "Task", epic_link: Optional[str] = None) -> Dict:
        response = requests.post(f"{self.base_url}/create_issue", data={
            "project_key": project_key,
            "summary": summary,
            "description": description,
            "issuetype": issuetype,
            "epic_link": epic_link
        })
        return response.json()
    
    def get_issue(self, issue_key: str) -> Dict:
        response = requests.get(f"{self.base_url}/issue/{issue_key}")
        return response.json()
    
    def update_issue(self, issue_key: str, **fields) -> Dict:
        response = requests.put(f"{self.base_url}/issue/{issue_key}", params=fields)
        return response.json()
    
    def search_issues(self, jql: str, max_results: int = 10) -> List[Dict]:
        response = requests.get(f"{self.base_url}/search_issues", params={
            "jql": jql,
            "max_results": max_results
        })
        return response.json()["issues"]
    
    def upload_attachment(self, issue_key: str, file_path: str) -> Dict:
        with open(file_path, "rb") as file:
            response = requests.post(
                f"{self.base_url}/issue/{issue_key}/attachments",
                files={"file": file}
            )
        return response.json()

# Usage
client = JiraMCPClient()
issue = client.create_issue("SLIM", "New feature", "Feature description", epic_link="SLIM-84")
client.upload_attachment(issue["key"], "requirements.pdf")
client.update_issue(issue["key"], status="In Progress", priority="High")
```

---

## Testing and Validation

### Test Coverage
All functionality has been validated with:
- **Epic SLIM-84:** "SLIM@Cloud 2.0 on Azure"
- **Test Issues:** SLIM-86, SLIM-87, SLIM-88
- **Direct JIRA API:** Low-level API calls validated
- **HTTP Endpoints:** All REST endpoints tested
- **Attachment Operations:** File upload/download/delete tested
- **Epic Operations:** Link/unlink/update validated

### Performance Considerations
- **Connection Pooling:** JIRA client reuses connections
- **Proxy Support:** Optimized for corporate network environments
- **Error Recovery:** Robust error handling with retries where appropriate
- **Memory Management:** Temporary files cleaned up automatically

### Security Features
- **Token Authentication:** Secure PAT-based authentication
- **Input Validation:** All inputs validated before processing
- **File Handling:** Secure temporary file management
- **Proxy Integration:** Support for corporate security requirements

---

## Server Deployment

### Starting the Server
```bash
# Development mode
python -m uvicorn mcp_server:app --host localhost --port 8000 --reload

# Production mode
python -m uvicorn mcp_server:app --host 0.0.0.0 --port 8000

# With specific configuration
python -m uvicorn mcp_server:app --host localhost --port 8000 --workers 4
```

### Environment Setup
```bash
# Required environment variables
export JIRA_PAT="your_personal_access_token"

# Optional proxy configuration (already configured in code)
export HTTP_PROXY="http://proxy.company.com:3133"
export HTTPS_PROXY="http://proxy.company.com:3133"
```

### Health Check
```bash
# Check if server is running
curl -X GET "http://localhost:8000/docs"
# Returns OpenAPI documentation if server is healthy
```

This comprehensive API documentation covers all endpoints, provides extensive examples, and includes deployment and integration guidance for the complete JIRA MCP Server functionality.