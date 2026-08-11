# Best Practices for Using Jira MCP Server

> **Note:** All project names (MYAPP, WEBAPP, BACKEND, etc.) and issue keys (MYAPP-123, MYAPP-456, etc.) used in examples throughout this document are fictional and for demonstration purposes only.

## Query Best Practices

### 1. Use Specific JQL for Better Results
**Good:**
```
project = MYAPP AND statusCategory != Done AND priority IN (High, Critical)
```

**Better:**
```
project = MYAPP AND statusCategory != Done AND priority IN (High, Critical) AND assignee != EMPTY ORDER BY updated DESC
```

**Why:** More specific queries return more relevant results and reduce noise.

### 2. Limit Result Sets
Always use `max_results` parameter for large queries to avoid overwhelming responses:
```
?jql=project = WEBAPP&max_results=50
```

### 3. Order Results Appropriately
Add ORDER BY clauses to get most relevant results first:
- `ORDER BY priority DESC` - Most important first
- `ORDER BY updated DESC` - Most recent changes
- `ORDER BY created DESC` - Newest issues first
- `ORDER BY duedate ASC` - Approaching deadlines

### 4. Use Date Ranges
Instead of returning all issues, filter by time:
```jql
updated >= -7d                    # Last 7 days
created >= startOfWeek()          # This week
duedate <= 7d                     # Due in next week
```

## Issue Creation Best Practices

### 1. Provide Complete Information
**Minimal (Not Recommended):**
```json
{
  "project_key": "MYAPP",
  "summary": "Fix bug"
}
```

**Better:**
```json
{
  "project_key": "MYAPP",
  "summary": "Fix database timeout in user profile service",
  "description": "Users experiencing timeout when loading profiles. Error occurs after 30s. Affects ~500 users daily.",
  "issuetype": "Bug",
  "priority": "High",
  "labels": ["production", "database", "performance"]
}
```

### 2. Use Descriptive Summaries
**Bad:** "Fix issue"
**Good:** "Fix database connection timeout in production environment"
**Best:** "Resolve PostgreSQL connection pool exhaustion causing 30s timeouts in user profile service"

### 3. Link to Epics When Appropriate
Always link stories/tasks to their parent epic for better organization:
```json
{
  "project_key": "MYAPP",
  "summary": "Implement auto-scaling for services",
  "issuetype": "Story",
  "epic_link": "MYAPP-100"
}
```

### 4. Choose Correct Issue Type
- **Epic** - Large initiative spanning multiple sprints
- **Story** - User-facing feature with acceptance criteria
- **Task** - Technical work item
- **Bug** - Defect needing fix
- **Subtask** - Breakdown of larger issue
- **Improvement** - Enhancement to existing functionality

## Update Best Practices

### 1. Update Only What You Need
Don't send full issue payload. Only include fields to change:
```json
{
  "status": "In Progress",
  "comment": "Starting work on this"
}
```

### 2. Add Meaningful Comments
**Bad:** "Updated"
**Good:** "Started implementation. Will complete by EOD tomorrow."
**Best:** "Started implementation. Completed database schema changes. Next: API endpoint development. ETA: EOD tomorrow."

### 3. Respect Workflow Transitions
Not all status changes are valid. Check available transitions first:
- Get issue details to see available transitions
- Use exact status names from available transitions
- Some transitions may require additional fields

### 4. Batch Related Updates
Instead of multiple separate updates:
```json
{
  "status": "In Progress",
  "assignee": "john.doe",
  "priority": "High",
  "comment": "Escalated issue - taking ownership"
}
```

## Search Best Practices

### 1. Start Broad, Then Refine
Begin with general search, then add filters based on results:
```
1. project = MYAPP
2. project = MYAPP AND statusCategory != Done
3. project = MYAPP AND statusCategory != Done AND priority = High
```

### 2. Use Appropriate Operators
- `=` for exact match
- `!=` for exclusion
- `IN (val1, val2)` for multiple values
- `~` for text contains
- `IS EMPTY` / `IS NOT EMPTY` for null checks
- `>`, `<`, `>=`, `<=` for comparisons

### 3. Leverage Standard Fields
Commonly useful fields:
- `project` - Project key
- `status` / `statusCategory` - Current state
- `assignee` - Who's working on it
- `reporter` - Who created it
- `priority` - Importance level
- `issuetype` - Type of issue
- `created` / `updated` - Timestamps
- `labels` - Tags
- `"Epic Link"` - Parent epic

### 4. Use Functions
JQL provides helpful functions:
- `currentUser()` - Your username
- `startOfWeek()` / `endOfWeek()` - Week boundaries
- `startOfMonth()` / `endOfMonth()` - Month boundaries
- `now()` - Current timestamp

## Attachment Management Best Practices

### 1. Name Files Descriptively
**Bad:** "image.png", "file.txt"
**Good:** "error-screenshot-2026-02-17.png", "performance-test-results.txt"

### 2. Include Relevant Information
When uploading logs or reports, add a comment explaining the context:
```
Uploading error logs from production incident on 2026-02-17 14:30 UTC
```

### 3. Clean Up Old Attachments
Periodically review and remove outdated attachments to keep issues clean.

### 4. Use Appropriate File Types
- Logs: `.txt`, `.log`
- Screenshots: `.png`, `.jpg`
- Documents: `.pdf`, `.docx`
- Data: `.csv`, `.json`
- Diagrams: `.png`, `.svg`, `.drawio`

## Performance Best Practices

### 1. Avoid Over-Fetching
Request only the data you need:
- Use specific JQL queries
- Limit result set size
- Search in specific projects

### 2. Cache Results When Appropriate
If querying same data repeatedly, cache results locally.

### 3. Use Pagination
For large result sets, implement pagination:
```
?jql=...&max_results=50&start_at=0    # First 50
?jql=...&max_results=50&start_at=50   # Next 50
```

### 4. Avoid Redundant Requests
Combine operations when possible instead of multiple round trips.

## Security Best Practices

### 1. Protect Your PAT
- Never commit `.env` file to git
- Store PAT securely
- Rotate PAT regularly
- Use least privilege access

### 2. Validate User Input
When creating issues from user input, validate and sanitize data.

### 3. Use Appropriate Permissions
Ensure your PAT has only necessary permissions:
- Read access for queries
- Write access for updates
- Admin access only if required

### 4. Log Sensitive Operations
Keep audit trail of:
- Issue creation
- Status changes
- Deletions
- Attachment uploads

## Workflow Best Practices

### 1. Follow Team Conventions
Adhere to your team's:
- Naming conventions
- Label standards
- Priority definitions
- Workflow processes

### 2. Keep Issues Updated
- Update status as work progresses
- Add comments for significant changes
- Link related issues
- Close completed work

### 3. Use Labels Consistently
Define standard labels:
- `urgent`, `blocker` - Priority
- `bug`, `feature`, `tech-debt` - Type
- `frontend`, `backend`, `devops` - Component
- `needs-review`, `needs-testing` - State

### 4. Link Related Work
- Link to related issues
- Reference PRs and commits
- Connect to epics
- Note dependencies

## Error Handling Best Practices

### 1. Handle Common Errors
- 404: Issue not found - verify issue key
- 403: Forbidden - check permissions
- 400: Bad request - validate input
- 401: Unauthorized - check PAT

### 2. Provide Fallback Options
If one approach fails, try alternative:
```
1. Try updating status directly
2. If fails, check available transitions
3. Use correct transition name
```

### 3. Validate Before Creating
Check if similar issues exist before creating new ones.

### 4. Confirm Operations
After creating/updating, verify the operation succeeded:
```
1. Create issue
2. Get issue to confirm creation
3. Verify fields are set correctly
```

## Team Collaboration Best Practices

### 1. Use @mentions in Comments
When commenting, mention relevant people:
```
@john.doe - Can you review the database schema changes?
```

### 2. Keep Stakeholders Informed
Update issues with progress, blockers, and decisions.

### 3. Use Appropriate Notifications
Consider who will be notified by your actions.

### 4. Document Decisions
Record important decisions in issue comments for future reference.

## Automation Best Practices

### 1. Automate Repetitive Tasks
Create scripts for common operations:
- Daily status reports
- Issue cleanup
- Bulk updates
- Notification triggers

### 2. Use Webhooks for Events
Configure webhooks to react to Jira events automatically.

### 3. Implement Validation
Add validation before automated operations to prevent errors.

### 4. Monitor Automation
Track automated operations and handle failures gracefully.

## JQL Query Patterns

### Common Patterns

**My Open Work:**
```jql
assignee = currentUser() AND statusCategory != Done ORDER BY priority DESC
```

**Recent Activity:**
```jql
project = MYAPP AND updated >= -7d ORDER BY updated DESC
```

**Upcoming Deadlines:**
```jql
duedate <= 7d AND statusCategory != Done ORDER BY duedate ASC
```

**High Priority Backlog:**
```jql
project = WEBAPP AND status = "Ready for Dev" AND priority IN (High, Critical)
```

**Blocked Issues:**
```jql
status = Blocked OR labels = blocked
```

**Unassigned Work:**
```jql
project = MYAPP AND assignee = EMPTY AND statusCategory != Done
```

**Epic Progress:**
```jql
"Epic Link" = MYAPP-100 AND statusCategory = Done
```

**Overdue Issues:**
```jql
duedate < now() AND statusCategory != Done
```

## Common Pitfalls to Avoid

### 1. Don't Use Generic Summaries
❌ "Fix bug"
✅ "Fix login timeout on mobile app"

### 2. Don't Skip Descriptions
Always add description with context, even if brief.

### 3. Don't Ignore Workflow Rules
Respect your team's workflow and required fields.

### 4. Don't Create Duplicate Issues
Search before creating to avoid duplicates.

### 5. Don't Over-Assign
Assign issues to one person at a time for accountability.

### 6. Don't Leave Issues Stale
Update or close issues that are no longer relevant.

### 7. Don't Forget to Link Epic
Always link stories/tasks to parent epics for tracking.

### 8. Don't Use Too Many Labels
Use labels judiciously - too many reduces their value.

## Integration Best Practices

### 1. Use with CI/CD
Integrate with pipelines to:
- Create issues from failed builds
- Update issues on deployments
- Add comments with build/deployment info

### 2. Link with Version Control
Reference Jira issues in commits:
```
git commit -m "MYAPP-123: Update API documentation"
```

### 3. Connect with Monitoring
Create issues automatically from alerts and incidents.

### 4. Sync with Other Tools
Keep Jira in sync with:
- Confluence for documentation
- Slack for notifications
- GitHub/GitLab for code

## Reporting Best Practices

### 1. Create Standard Queries
Save commonly used JQL queries for easy access.

### 2. Track Metrics
Monitor key metrics:
- Velocity (issues completed per sprint)
- WIP (work in progress)
- Cycle time
- Bug rate

### 3. Generate Regular Reports
Create automated reports for:
- Sprint retrospectives
- Weekly status updates
- Monthly summaries

### 4. Use Filters and Dashboards
Leverage Jira filters and dashboards for visualization.