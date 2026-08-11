# Jira MCP Server Context

> **Note:** All project names (MYAPP, WEBAPP, INFRA, etc.) and issue keys (MYAPP-123, PROJECT-456, etc.) used in examples are fictional and for demonstration purposes only.

## Overview
The Jira MCP (Model Context Protocol) Server provides seamless integration with Porsche Jira instances, allowing AI agents to interact with Jira issues through natural language commands. It uses Private Access Tokens (PAT) for secure authentication.

## Core Capabilities

### 1. Issue Search & Retrieval
- Search issues using JQL (Jira Query Language)
- Get detailed issue information including fields, comments, transitions
- Filter by project, status, assignee, type, and more
- Support for complex queries with multiple conditions

### 2. Issue Creation & Management
- Create various issue types: Story, Task, Bug, Epic, Subtask, Improvement
- Link issues to epics during creation
- Update existing issues (summary, description, status, assignee, priority)
- Add comments to issues
- Manage labels and components

### 3. Issue Transitions
- Move issues through workflow states (Open → In Dev → Code Review → Done)
- Automatically detect available transitions for each issue
- Respect workflow rules and required fields

### 4. Attachment Management
- Upload files to issues (documents, images, logs)
- List all attachments on an issue
- Delete attachments when needed
- Support for multiple file types

### 5. Epic Management
- Create epics to organize work
- Link stories/tasks to epics
- Update epic links on existing issues
- Remove epic links

### 6. Service Desk Access
- List available Service Desk portals
- Retrieve request details (status history, participants, reporter)
- Read request comments (public and internal)
- Add comments to requests (public or internal)
- Search requests by ownership, status, and text
- Access tickets that return 403 via the standard Jira REST API (e.g. ITSA project)

## Available Operations

### Search Issues
```
GET /search_issues?jql={query}&max_results={limit}
```
Search for issues using JQL syntax. Supports pagination and complex queries.

### Get Issue Details
```
GET /issue/{issue_key}
```
Retrieve comprehensive information about a specific issue including:
- Issue fields (summary, description, status, priority)
- Assignee and reporter information
- Time tracking and estimates
- Comments and worklogs
- Available transitions
- Related issues and epic links

### Create Issue
```
POST /create_issue
```
Create a new issue with specified fields:
- Required: `project_key`, `summary`, `issuetype`
- Optional: `description`, `epic_link`, `assignee`, `priority`, `labels`

### Update Issue
```
PUT /issue/{issue_key}
```
Update any modifiable field on an issue:
- Change summary or description
- Update status (triggers transitions)
- Reassign to different users
- Add comments
- Modify epic links
- Update priority and labels

### Upload Attachment
```
POST /issue/{issue_key}/attachments
```
Upload files to an issue (multipart/form-data).

### List Attachments
```
GET /issue/{issue_key}/attachments
```
Get all attachments associated with an issue.

### Delete Attachment
```
DELETE /issue/{issue_key}/attachments/{attachment_id}
```
Remove a specific attachment from an issue.

### List Service Desks
```
GET /servicedesks?limit={limit}&start={start}
```
List all available Jira Service Desk portals. Returns service desk ID, project key, and project name.

### Get Service Desk Request
```
GET /servicedesk/request/{request_key}
```
Retrieve details for a Service Desk request including status history, participants, and reporter. Works for tickets that return 403 via the standard Jira REST API (e.g. ITSA project).

### Get Service Desk Request Comments
```
GET /servicedesk/request/{request_key}/comments?public={true|false}&limit={limit}
```
Get comments on a Service Desk request. Filter to public (customer-visible) or include internal comments.

### Add Service Desk Request Comment
```
POST /servicedesk/request/{request_key}/comments?body={text}&public={true|false}
```
Add a comment to a Service Desk request. Supports public (customer-visible) and internal comments.

### Search Service Desk Requests
```
GET /servicedesk/requests?service_desk_id={id}&request_ownership={ownership}&request_status={status}&search_term={text}
```
Search for Service Desk requests by ownership, status, and text. Supports filtering by specific service desk.
- `request_ownership`: `OWNED_REQUESTS` (requests you created - default), `PARTICIPATED_REQUESTS` (participant only, excludes reporter), `ALL_REQUESTS` (creator or participant)

## Authentication
Uses Private Access Token (PAT) stored in `.env` file:
```
JIRA_BASE_URL=https://api.skyway.porsche.com/jira
JIRA_PAT=your_token_here
```


Get your PAT from: https://skyway.porsche.com/jira/plugins/servlet/desk/portal/1

## Example Jira Projects
- **MYAPP** - Main application project
- **WEBAPP** - Web application development
- **MOBILE** - Mobile app development
- **BACKEND** - Backend services
- **API** - API development
- **INFRA** - Infrastructure and operations
- **DOC** - Documentation tasks

## JQL Examples

### Find open issues in a project
```jql
project = MYAPP AND statusCategory != Done
```

### Find issues assigned to you
```jql
assignee = currentUser() AND status != Done
```

### Find high priority bugs
```jql
issuetype = Bug AND priority = High AND status != Done
```

### Find issues in specific sprint
```jql
project = WEBAPP AND sprint = "Sprint 24"
```

### Find recently updated issues
```jql
updated >= -7d ORDER BY updated DESC
```

### Find issues by epic
```jql
"Epic Link" = MYAPP-100
```

## Issue Types
- **Epic** - Large body of work with multiple stories
- **Story** - User story with acceptance criteria
- **Task** - Technical task or work item
- **Bug** - Defect or issue to fix
- **Subtask** - Smaller task under a parent issue
- **Improvement** - Enhancement to existing functionality

## Common Status Values
- **Open** - New, not started
- **Ready for Dev** - Ready to be worked on
- **In Dev** / **In Progress** - Currently being worked on
- **Code Review** - Pending review
- **Testing** - In QA/testing phase
- **Done** / **Closed** - Completed

## Best Use Cases
1. **Project Management** - Track and update issues, search for specific work items
2. **Bug Tracking** - Create bug reports with detailed information, track resolution
3. **Sprint Planning** - Query issues for sprint planning, update priorities
4. **Reporting** - Search for issues to generate reports and metrics
5. **Automation** - Automatically create/update issues based on events
6. **Documentation** - Attach files and documents to issues
7. **Workflow Management** - Move issues through workflow states

## Integration Points
- Works with GitHub Copilot via MCP protocol
- Compatible with Claude and other AI assistants
- REST API for programmatic access
- STDIO mode for command-line integration

## Server Modes
1. **HTTP Mode** - REST API on http://localhost:8000
2. **MCP Mode** - MCP protocol on http://localhost:8000/mcp
3. **STDIO Mode** - Standard input/output for CLI tools

## Response Formats
All responses are JSON with standardized structure:
```json
{
  "success": true,
  "message": "Operation completed successfully",
  "data": { ... }
}
```

Error responses include:
```json
{
  "success": false,
  "error": "Error description",
  "details": "Additional error details"
}
```