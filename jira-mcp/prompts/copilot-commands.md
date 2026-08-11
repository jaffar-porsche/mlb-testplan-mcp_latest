# GitHub Copilot Chat Commands for Jira MCP

> **Note:** All examples use fictional project names (MYAPP, WEBAPP, etc.) and issue keys (MYAPP-123, MYAPP-456, etc.). Replace these with your actual project keys and issue numbers.

This file contains specific commands and patterns optimized for GitHub Copilot Chat when using the Jira MCP Server.

## Using @jira Mention

When the Jira MCP Server is configured, you can use `@jira` to target your questions specifically at the Jira integration:

```
@jira show me open issues in MYAPP project
@jira create a task to update documentation
@jira get details for MYAPP-123
```

## Quick Commands

### Issue Search
```
@jira find open MYAPP issues
@jira show high priority bugs
@jira list my assigned tasks
@jira search for issues about "authentication"
@jira get issue MYAPP-456
```

### Issue Creation
```
@jira create task in MYAPP: "Update API docs"
@jira create bug: "Login fails on mobile"
@jira create story: "As a user, I want password reset"
@jira create epic: "Azure Migration Phase 2"
```

### Issue Updates
```
@jira update MYAPP-123 status to "In Progress"
@jira change MYAPP-456 priority to High
@jira assign MYAPP-789 to john.doe
@jira add comment to MYAPP-100: "Need DevOps coordination"
@jira link MYAPP-456 to epic MYAPP-100
```

### Attachments
```
@jira show attachments on MYAPP-456
@jira list attachments for PROJECT-789
```

## Conversational Patterns

### Pattern 1: Search → Filter → Action
```
You: @jira show MYAPP issues

Copilot: [Shows all MYAPP issues]

You: Only the open ones

Copilot: [Filters to open issues]

You: Which are high priority?

Copilot: [Filters to high priority]

You: Move the first one to In Progress

Copilot: [Updates status of first issue]
```

### Pattern 2: Create → Verify → Enhance
```
You: @jira create task "Setup database backups"

Copilot: [Creates task]

You: Show me the issue

Copilot: [Displays created issue]

You: Add it to epic MYAPP-456

Copilot: [Links to epic]

You: Set priority to High

Copilot: [Updates priority]
```

### Pattern 3: Query → Details → Update
```
You: @jira find issues assigned to me

Copilot: [Lists your assigned issues]

You: Show details for the first one

Copilot: [Shows full details]

You: Add comment "Will complete by Friday"

Copilot: [Adds comment]
```

### Pattern 4: Epic Management
```
You: @jira create epic "Cost Optimization"

Copilot: [Creates epic]

You: Create 3 stories under this epic for VM optimization

Copilot: [Creates 3 linked stories]

You: Show all issues in this epic

Copilot: [Lists epic and children]
```

## Context-Aware Commands

Copilot understands context from previous messages:

```
You: @jira show MYAPP-123

Copilot: [Shows issue details]

You: Move it to In Progress
# "it" refers to MYAPP-123

Copilot: [Updates status]

You: Add comment "Starting work"
# Still operates on MYAPP-123

Copilot: [Adds comment]

You: Assign to me
# Still MYAPP-123

Copilot: [Assigns to you]
```

## Batch Operations

```
@jira show all unassigned MYAPP tasks and assign them to team members based on workload

@jira find all high priority bugs and create a summary report

@jira list all issues updated today and group by status

@jira find issues in "Code Review" for more than 3 days
```

## Project Management Commands

### Sprint Planning
```
@jira show sprint backlog for WEBAPP
@jira list all ready-for-dev issues in MYAPP
@jira find unassigned stories in current sprint
@jira show velocity for last 3 sprints
```

### Daily Standup
```
@jira what did I work on yesterday?
@jira show my open issues ordered by priority
@jira find issues I'm blocked on
@jira list issues I updated in last 24 hours
```

### Code Review
```
@jira show all issues in Code Review status
@jira find my PRs waiting for review
@jira list issues ready for testing
```

### Release Management
```
@jira find all issues for version 2.1
@jira show issues with label "release-blocker"
@jira list completed features this sprint
```

## Advanced JQL via Copilot

You can ask Copilot to construct complex JQL queries:

```
@jira find issues created last week that are high priority and unassigned

Copilot executes: created >= -7d AND priority = High AND assignee = EMPTY

@jira show bugs in WEBAPP from last month that are still open

Copilot executes: project = WEBAPP AND issuetype = Bug AND created >= -30d AND statusCategory != Done
```

## Error Recovery

If something goes wrong, Copilot can help debug:

```
You: @jira update MYAPP-999 to "In Progress"

Copilot: Issue MYAPP-999 not found

You: Show me MYAPP issues starting with 99

Copilot: [Shows MYAPP-990, MYAPP-991, MYAPP-992]

You: Update MYAPP-992 to "In Progress"

Copilot: [Successfully updates]
```

## Workflow Helpers

### Bug Triage
```
@jira show all new bugs
# Copilot lists bugs in "Open" status

Which ones are critical?
# Copilot filters to critical priority

Move the first two to "Ready for Dev"
# Copilot updates status
```

### Feature Planning
```
@jira create epic "User Profile Redesign"
# Copilot creates epic

Create 5 stories for this epic covering different aspects
# Copilot creates linked stories

Show me the epic with all stories
# Copilot displays hierarchy
```

### Cleanup Tasks
```
@jira find issues not updated in 90 days
# Copilot searches stale issues

Show me the first 10
# Copilot limits results

Comment on each "Please review for closure"
# Copilot adds comments to issues
```

## Reporting Commands

```
@jira how many issues are in each status for MYAPP?

@jira show me completion rate for this sprint

@jira what's the average time from "Ready for Dev" to "Done"?

@jira list top 5 contributors this month

@jira show bug resolution time trend
```

## Integration with Code

### Reference Issues in Code
```
You: Show me the code related to MYAPP-123

Copilot: [Searches for references in codebase]

You: @jira get details for MYAPP-123

Copilot: [Shows Jira issue details]

You: Update the issue with implementation notes

Copilot: [Adds comment with code changes]
```

### Create Issues from Code
```
You: This function needs refactoring

Copilot: Shall I create a Jira issue?

You: Yes, create tech debt task in MYAPP

Copilot: [Creates issue with context from code]
```

## Smart Suggestions

Copilot can make intelligent suggestions:

```
You: @jira show MYAPP-123

Copilot: [Shows issue]
Copilot: "This issue has been in 'In Progress' for 15 days. Would you like to update it or add a comment?"

You: @jira create bug "App crashes"

Copilot: [Creates bug]
Copilot: "Would you like to set priority to High and add reproduction steps?"
```

## Time-Saving Shortcuts

### Quick Status Update
```
@jira MYAPP-123 → In Progress
# Updates status

@jira MYAPP-456 → High priority
# Updates priority

@jira MYAPP-789 → assign to me
# Assigns to you

@jira MYAPP-100 → link to MYAPP-789
# Links to epic
```

### Multi-Issue Operations
```
@jira MYAPP-456, MYAPP-123, MYAPP-789 → High priority
# Updates all three

@jira all open MYAPP bugs → assign to qa-team
# Bulk assignment

@jira issues in Code Review > 3 days → add comment "Please review"
# Conditional bulk operation
```

## Natural Language Variations

Copilot understands many ways to ask the same thing:

**Getting Issue Details:**
- `@jira show MYAPP-123`
- `@jira get issue MYAPP-123`
- `@jira fetch details for MYAPP-123`
- `@jira what's the status of MYAPP-123?`
- `@jira tell me about MYAPP-123`

**Searching:**
- `@jira find MYAPP bugs`
- `@jira search for MYAPP bugs`
- `@jira show me MYAPP bugs`
- `@jira list MYAPP bugs`
- `@jira get all MYAPP bugs`

**Updating:**
- `@jira update MYAPP-123 priority to High`
- `@jira change MYAPP-123 to high priority`
- `@jira set MYAPP-123 priority High`
- `@jira make MYAPP-123 high priority`
- `@jira bump MYAPP-123 priority to High`

## Tips for Better Interactions

1. **Start with @jira** - Makes intent clear to Copilot
2. **Be conversational** - Natural language works best
3. **Use context** - Refer to "it", "this issue", "the first one"
4. **Ask follow-ups** - Refine results iteratively
5. **Combine operations** - "Create task and link to epic"
6. **Request summaries** - "Show me a summary of..."
7. **Ask for help** - "How do I...?" or "What's the JQL for...?"

## Common Patterns by Role

### Developer
```
@jira show my issues
@jira what's blocking me?
@jira move <issue> to code review
@jira create tech debt task
@jira find issues related to <component>
```

### QA Engineer
```
@jira show issues ready for testing
@jira create bug report
@jira list all open bugs
@jira find regression issues
@jira mark <issue> as tested
```

### Project Manager
```
@jira show sprint status
@jira list all high priority items
@jira create epic for new initiative
@jira show team workload
@jira generate sprint report
```

### Product Owner
```
@jira show backlog items
@jira prioritize stories
@jira create user story
@jira show epic progress
@jira list completed features
```

## Troubleshooting with Copilot

```
You: @jira update MYAPP-123 to Completed

Copilot: Status "Completed" not available. Available transitions: "In Progress", "Code Review", "Done"

You: Change to Done then

Copilot: [Updates successfully]
```

```
You: @jira create issue in MYAPPP project

Copilot: Project "MYAPPP" not found. Did you mean "MYAPP"?

You: Yes, MYAPP

Copilot: [Creates in correct project]
```

## Best Practices for Copilot Interaction

1. **One operation at a time** - Clear, focused requests
2. **Verify results** - Check Copilot's response
3. **Use project keys** - Always specify project
4. **Be explicit** - State exact issue keys when possible
5. **Leverage context** - Build on previous responses
6. **Ask for clarification** - If response unclear, ask again
7. **Provide feedback** - "That's not quite right, try..."

## Example Daily Workflow

### Morning Standup
```
@jira what did I work on yesterday?
@jira show my tasks for today
@jira are there any blockers?
```

### During Development
```
@jira move MYAPP-123 to In Progress
@jira add comment "Started implementation"
# [Do work]
@jira move MYAPP-123 to Code Review
@jira add comment "PR #456 ready"
```

### Code Review Time
```
@jira show issues waiting for my review
@jira open first issue
# [Review]
@jira add comment "LGTM, approved"
@jira move to Testing
```

### End of Day
```
@jira show what I completed today
@jira update pending issues with status
@jira plan tomorrow's work
```

---

**Pro Tip:** Save frequently used commands as snippets in your IDE for even faster access!