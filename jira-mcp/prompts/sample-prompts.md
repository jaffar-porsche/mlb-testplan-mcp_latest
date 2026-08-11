# Sample Prompts for Jira MCP Server

> **Note:** All project names (MYAPP, WEBAPP, MOBILE, etc.) and issue keys (MYAPP-123, PROJECT-456, etc.) shown in this document are examples only and do not represent real Jira items.

## Quick Start Prompts

### Finding Issues
```
Show me all open issues in the MYAPP project
```

```
Find all high priority bugs that are not done
```

```
List issues assigned to me that are still open
```

```
Search for issues related to "authentication" in project WEBAPP
```

```
Get details for issue MYAPP-123
```

### Creating Issues
```
Create a new task in MYAPP project: "Update documentation for API endpoints"
```

```
Create a bug report in MOBILE project with summary "App crashes on startup" and description "The app crashes immediately after launch on iOS 15"
```

```
Create a user story in WEBAPP: "As a user, I want to reset my password so that I can regain access to my account"
```

```
Create an epic in INFRA project called "Cloud Migration Phase 2"
```

### Updating Issues
```
Update MYAPP-456 to change status to "In Progress" and add comment "Started working on this task"
```

```
Change the priority of MYAPP-789 to High
```

```
Reassign issue WEBAPP-123 to john.smith
```

```
Add comment to MYAPP-100: "Need to coordinate with DevOps team before proceeding"
```

### Managing Attachments
```
Upload the file "architecture-diagram.png" to issue MYAPP-100
```

```
Show me all attachments on issue PROJECT-456
```

```
Delete the attachment with ID 12345 from issue MYAPP-789
```

## Project Management Scenarios

### Sprint Planning
```
Show me all open stories in WEBAPP project with priority High or higher
```

```
Find all issues in sprint "Sprint 24" that are not done yet
```

```
List all unassigned tasks in the BACKEND project
```

```
Get all issues created in the last 7 days for project INFRA
```

### Epic Management
```
Create an epic in MYAPP: "Cost Optimization Initiative"
```

```
Link issue MYAPP-456 to epic MYAPP-100
```

```
Show me all issues linked to epic MYAPP-100
```

```
Create a new story in MYAPP and link it to epic MYAPP-100: "Implement auto-scaling for services"
```

### Status Tracking
```
Move issue MYAPP-200 from "Open" to "In Dev"
```

```
Show me all issues that are currently in "Code Review" status
```

```
Find issues that have been "In Progress" for more than 2 weeks
```

### Team Coordination
```
Find all issues assigned to the frontend team in WEBAPP project
```

```
Show me issues where I'm the reporter but not the assignee
```

```
List all blocked issues in project INFRA
```

## Bug Management Prompts

### Reporting Bugs
```
Create a critical bug in BACKEND: "Database connection timeout in production" with description including environment details and steps to reproduce
```

```
Report a bug in MOBILE project: "Image upload fails for files larger than 5MB" and set priority to High
```

### Bug Tracking
```
Show me all open bugs in project WEBAPP sorted by priority
```

```
Find critical and high priority bugs that have been open for more than 5 days
```

```
List all bugs assigned to me
```

### Bug Resolution
```
Update bug MOBILE-789 to status "Testing" and add comment "Fix deployed to staging environment"
```

```
Close bug WEBAPP-456 and add resolution comment "Fixed in version 2.1.3"
```

## Development Workflow Prompts

### Daily Standup
```
Show me issues I worked on yesterday (updated in last 24 hours where I'm assignee)
```

```
List all my open issues ordered by priority
```

```
Find issues I'm assigned to that are blocked or waiting
```

### Code Review
```
Show me all issues in "Code Review" status for project BACKEND
```

```
Move MYAPP-300 to "Code Review" and add comment "PR #456 ready for review"
```

### Deployment Tracking
```
Find all issues with label "ready-for-deployment" in project WEBAPP
```

```
Create a task "Deploy version 2.1 to production" and link it to epic WEBAPP-100
```

## Reporting & Analytics Prompts

### Status Reports
```
Show me all issues completed in the last sprint (last 2 weeks, status = Done)
```

```
Find all issues created this month in project MYAPP
```

```
Count how many issues are in each status for project WEBAPP
```

### Work Tracking
```
Show me all issues I've commented on in the last week
```

```
Find issues I created that are still open
```

```
List all issues updated in the last 3 days in project INFRA
```

## Advanced Query Prompts

### Complex Searches
```
Find all stories and tasks in MYAPP project that are either "In Dev" or "Ready for Dev" and have priority Medium or higher
```

```
Show me issues in WEBAPP project created in last 30 days that have no assignee
```

```
Find all subtasks in project BACKEND where parent issue is "In Progress"
```

### Epic & Dependency Management
```
Show me all epics in INFRA project with their linked issues
```

```
Find issues in MYAPP that are not linked to any epic
```

```
List all blocked issues and their blockers in project WEBAPP
```

## Attachment Management Prompts

### Uploading Files
```
Attach the log file "error-logs-2026-02-17.txt" to bug MYAPP-400
```

```
Upload architecture diagram to epic MYAPP-100
```

```
Attach screenshots to bug report MOBILE-456
```

### Managing Attachments
```
List all attachments on issue PROJECT-789 and show their sizes
```

```
Remove the outdated attachment from issue MYAPP-300
```

```
Show me which issues in MYAPP project have attachments
```

## Bulk Operations Prompts

### Batch Updates
```
Update all issues in MYAPP project with label "urgent" to priority High
```

```
Add label "needs-review" to all issues in "Code Review" status
```

```
Assign all unassigned tasks in sprint to team members
```

### Cleanup Tasks
```
Find all issues in WEBAPP that haven't been updated in 90 days
```

```
Show me duplicate or related issues for MYAPP-500
```

```
List all issues that are missing descriptions in project BACKEND
```

## Workflow-Specific Prompts

### DevOps Tasks
```
Create a task in INFRA: "Update Kubernetes cluster to version 1.28" with priority High
```

```
Find all infrastructure-related issues in project MYAPP
```

### Documentation Tasks
```
Create a documentation task: "Update API documentation for authentication endpoints"
```

```
Find all issues with label "documentation" that are not done
```

### Testing & QA
```
Create a test task in WEBAPP: "Test new login flow on all browsers"
```

```
Find all issues in "Testing" status that have been there for more than 3 days
```

## Time-Sensitive Prompts

### Urgent Issues
```
Show me all critical and blocker issues across all projects
```

```
Find issues with "urgent" label that are still open
```

```
List all issues with due date in the next 7 days
```

### Overdue Tracking
```
Find all issues past their due date in project WEBAPP
```

```
Show me issues that have been "In Progress" for more than 2 weeks
```

## Tips for Effective Prompts

1. **Be Specific**: Include project keys, issue types, and status values
2. **Use Natural Language**: The AI understands conversational requests
3. **Combine Criteria**: Filter by multiple fields (project, status, priority, assignee)
4. **Specify Output**: Request specific information you need (just keys, full details, counts)
5. **Context Matters**: Mention relevant context (sprint, team, timeframe)
6. **Follow Up**: Ask follow-up questions to refine results

## Example Conversational Flow

```
User: Show me open issues in MYAPP project

AI: [Lists 20 open MYAPP issues]

User: Which ones are related to performance?

AI: [Filters to show performance-related issues]

User: Update MYAPP-456 to high priority

AI: [Updates issue and confirms]

User: Great, now assign it to john.doe

AI: [Updates assignment and confirms]
```