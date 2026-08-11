# Prompt Examples for JIRA MCP Server

This document provides natural language prompt examples for using the JIRA MCP Server across all issue types and operations. These examples demonstrate how to interact with the server using conversational requests for user stories, tasks, bugs, epics, subtasks, and more.

## Basic Issue Creation

### Creating Different Issue Types

**User Stories**
```
Create a user story in project WEBAPP: "As a customer, I want to track my order status so that I know when to expect delivery". Set story points to 5 and assign to the frontend team.
```

**Tasks**
```
Create a technical task in BACKEND project: "Implement Redis caching for user sessions". Set priority to High and assign to the backend team lead.
```

**Bug Reports**
```
Create a bug report in MOBILE project: "App crashes when user uploads large images". Priority: Critical. Steps to reproduce: 1) Open camera, 2) Take high-res photo, 3) Try to upload. Expected: Upload succeeds. Actual: App crashes.
```

**Improvements**
```
Create an improvement item in PERF project: "Optimize database queries for user dashboard". Add technical details about current performance metrics and target improvements.
```

**Research Tasks**
```
Create a research task in TECH project: "Evaluate new frontend frameworks for 2025 roadmap". Set time estimate to 2 weeks and assign to architecture team.
```

### Simple Issue Operations

**Basic Updates**
```
Update issue WEBAPP-123 to change priority from Medium to High and add comment "Customer escalation - needs immediate attention".
```

**Status Changes**
```
Move issue API-456 from "In Progress" to "Code Review" and assign to team lead for review.
```

**Assignment Changes**
```
Reassign bug MOBILE-789 from john.doe to jane.smith because John is on vacation this week.
```

## Issue Management by Type and Priority

### User Story Management

**User Story with Acceptance Criteria**
```
Create user story in PROJECT-X: "As an admin, I want to manage user permissions so that I can control access to sensitive data". Add description with acceptance criteria:
- Admin can view all user roles
- Admin can modify user permissions  
- Changes are logged for audit
- Email notifications sent to affected users
```

**Story Point Assignment**
```
For all user stories in project WEBAPP, assign story points based on complexity:
- Simple UI stories: 2 points
- Backend integration stories: 5 points  
- Complex algorithm stories: 8 points
- Research stories: 3 points
```

### Task Breakdown and Management

**Task Breakdown**
```
I need to break down the work for implementing OAuth integration. Create these tasks in AUTH project:
1. "Research OAuth2 providers" - assign to senior developer
2. "Design authentication flow" - assign to architect  
3. "Implement OAuth endpoints" - assign to backend team
4. "Add OAuth UI components" - assign to frontend team
5. "Write OAuth integration tests" - assign to QA team
```

**Subtask Creation**
```
Add a task "Update API documentation" to project DOC. Set it as a subtask under issue DOC-100 and assign to technical writer.
```

### Bug Management Workflows

**Bug with Environment Details**
```
Create critical bug in CLOUD project: "Database connection timeout in production". Include environment details:
- Environment: Production
- Browser: Chrome 120
- OS: Windows 11
- Time: 2025-11-04 14:30 UTC
- Error: Connection timeout after 30 seconds
- Affected users: ~500 customers
```

**Bug Triage**
```
Triage all new bugs in project MOBILE:
- Critical bugs: assign to senior developers immediately
- High bugs: add to current sprint
- Medium bugs: schedule for next sprint
- Low bugs: move to backlog
```

### Priority-Based Operations

**High Priority Issues**
```
Create a critical bug in PROD project: "Payment processing fails for international cards". Set priority to Highest, assign to payments team, and add label "production-issue".
```

```
Show me all High priority user stories in project MOBILE that are not assigned to anyone. I need to distribute them across the team.
```

**Low Priority Cleanup**
```
Find all Low priority improvement items in LEGACY project that haven't been updated in 6 months. I want to close outdated ones and reassign relevant ones.
```

## Epic Management and Linking

### Creating Issues with Epic Links

**Epic Link Creation**
```
Create a new JIRA issue in project DEVX with summary "Implement user authentication API" and description "Add OAuth2 authentication endpoints for user login and registration". Link this issue to epic DEVX-100.
```

**Multiple Field Creation with Epic**
```
Create a bug report in project MOBILE with title "App crashes on iOS 15" and description "Users report frequent crashes when opening the profile screen on iOS 15 devices". Set priority to High and link to epic MOBILE-45.
```

**Story Creation with Epic**
```
Add a new user story to project WEB: "As a customer, I want to reset my password via email so that I can regain access to my account". Link this to the authentication epic WEB-200 and set story points to 3.
```

### Epic Link Management Workflows

**Multi-Step Epic Operations**
```
I need to manage epic relationships for my project:

1. Create a task titled "Setup database schema" in project BACKEND, link it to epic BACKEND-50
2. Then create another task "Implement API endpoints" in the same project, also linked to BACKEND-50  
3. After creation, move the first task to "In Progress" status
4. Finally, unlink the second task from the epic
```

**Epic Reorganization**
```
I'm reorganizing my project structure:
- Move issue API-123 from epic API-10 to epic API-20
- Move issue API-124 from epic API-10 to epic API-20  
- Add comment to both issues: "Moved to new epic due to scope refinement"
- Set both issues to High priority
```

### Epic Updates and Modifications

**Changing Epic Links**
```
Update issue PROJ-123 to:
- Change the epic link from PROJ-10 to PROJ-15
- Set priority to High
- Add comment "Moved to new epic due to scope change"
```

**Epic Link Removal**
```
Remove the epic link from issue WEBAPP-456 and add a comment explaining that this task is now standalone and no longer part of the original epic scope.
```

**Conditional Epic Updates**
```
If issue CLOUD-789 is currently linked to epic CLOUD-100, remove that link and instead link it to epic CLOUD-200. Also update the summary to include "[Migrated]" prefix.
```

## Advanced Search and Filtering

### Issue Type Filtering and Search

**Search by Issue Type**
```
Search for all open user stories in project WEBAPP that contain "authentication" in the title or description. I need to consolidate auth-related work.
```

**Find Unassigned Work**
```
Find all tasks in DEVOPS project that are assigned to "john.doe" and show their current status. I need to check his workload.
```

**Cross-Type Dependencies**
```
Show me all bugs that are blocking user stories in project MOBILE. I need to prioritize bug fixes to unblock feature development.
```

### Advanced Search Queries

**Complex Filtering**
```
Search for issues in project API that meet these criteria:
- Created in the last 30 days
- Priority is High or Critical  
- Status is not "Done"
- Assignee is from the backend team
- Has label "customer-reported"
```

**Epic-Based Searches**
```
Find all issues linked to epic FEATURE-100 that are:
- Still in "To Do" status
- Assigned to developers who are currently on vacation
- Need to be reassigned before sprint starts
```

## Bulk Operations and Automation

### Bulk Epic Assignment

**Bulk Epic Linking**
```
Search for all open tasks in project API that are currently unlinked to any epic, then link them all to epic API-200 "Infrastructure Improvements" and set their priority to Medium.
```

**Epic-Based Status Updates**
```
Find all issues linked to epic MOBILE-50 that are currently in "To Do" status and move them to "In Progress". Add a comment to each: "Starting epic MOBILE-50 implementation phase".
```

**Epic Cleanup**
```
Search for all completed issues that are still linked to epic LEGACY-10. Remove their epic links and add a comment "Completed - unlinked from legacy epic".
```

### Bulk Issue Management

**Status Transitions by Type**
```
Move all completed tasks in epic RELEASE-30 to "Done" status and all user stories to "Ready for Testing". Add comment "Release 3.0 feature complete".
```

**Bulk Status Updates**
```
For all bugs in project WEB with priority "Medium" or lower, if they haven't been updated in 30 days, move them to "Backlog" status with comment "Moved to backlog due to inactivity".
```

## Issue Relationships and Dependencies

### Parent-Child Relationships

**Creating Subtasks**
```
Create a story "Implement user registration" in AUTH project, then create these subtasks under it:
- "Design registration form UI"
- "Add validation logic"  
- "Implement backend API"
- "Add email verification"
- "Write integration tests"
```

### Dependency Management

**Creating Dependencies**
```
Create dependency link: Story AUTH-100 "User login" blocks Story PROFILE-50 "User dashboard". The dashboard can't be completed until login is implemented.
```

**Issue Linking**
```
Link bug MOBILE-200 as "caused by" user story MOBILE-150. The new login feature introduced this authentication bug.
```

## Agile and Sprint Management

### Sprint Planning

**Sprint Capacity Planning**
```
I have 40 story points capacity for next sprint. Show me user stories and tasks from epic WEBAPP-50 that total close to 40 points, prioritizing High priority items first.
```

**Sprint Item Selection**
```
For the upcoming sprint, I need to move 5 issues from epic BACKLOG-100 to epic SPRINT-15. Show me the lowest priority items in the backlog epic first.
```

### Release Management

**Release Preparation**
```
For release WEBAPP-2.0, gather all completed user stories, tasks, and bugs. Generate a release notes summary grouping by:
- New Features (user stories)
- Improvements (enhancement tasks)  
- Bug Fixes (resolved bugs)
```

**Version Planning**
```
Plan version 3.1 by selecting user stories and improvements from backlog that:
- Are estimated at 3 points or less
- Don't depend on other incomplete work
- Are labeled "quick-win"
```

## Quality Assurance Workflows

### Testing Task Creation

**Automated Test Task Creation**
```
For each user story in epic PAYMENT-100, automatically create corresponding test tasks:
- "Test [story name] - happy path"
- "Test [story name] - error scenarios"  
- "Test [story name] - edge cases"
Assign all test tasks to QA team.
```

### Information Retrieval and Validation

**Epic Information Retrieval**
```
Get detailed information for issue MOBILE-789 including its epic link details. I want to see which epic it belongs to and the current status of that epic.
```

**Epic Validation Before Creation**
```
Before creating a new issue, verify that epic CLOUD-25 exists and is still open. If valid, create a task "Configure monitoring alerts" linked to that epic.
```

**Epic Status Overview**
```
Show me all issues linked to epic DATA-100, including their current status, assignee, and priority. I want to understand the overall epic progress.
```

## Time-Based and Scheduling Operations

### Deadline-Driven Operations

**Deadline Management**
```
All issues in epic RELEASE-30 need to be completed by end of month. Show me which ones are at risk and might need priority adjustment or reassignment.
```

**Historical Analysis**
```
Show me all issues that were linked to epic ARCHIVED-10 in the past 30 days. I want to see the completion timeline for that epic.
```

## Team Management and Collaboration

### Workload Distribution

**Team Workload Analysis**
```
I need to balance the workload for epic FEATURE-200. Show me how many issues each team member has assigned within this epic, and suggest redistributions if needed.
```

**Team Communication**
```
Send an update to all issues in epic MIGRATION-50: "Migration phase 1 complete. Please review your tasks and update status accordingly. Next standup: tomorrow 9 AM."
```

**Performance Tracking**
```
Track the velocity for epic PERFORMANCE-100. How many story points have been completed each week? Are we on track for the target completion date?
```

### Epic Assignment by Team

**Team-Based Epic Assignment**
```
Create 3 tasks for epic TEAM-50:
1. "Frontend implementation" - assign to frontend team member, link to TEAM-50
2. "Backend API development" - assign to backend team member, link to TEAM-50  
3. "QA test planning" - assign to QA team member, link to TEAM-50
Set all to same priority as the epic.
```

## Advanced Scenarios and Problem Solving

### Epic Migration and Reorganization

**Epic Migration**
```
I need to migrate all issues from epic OLD-50 to epic NEW-75:
1. Search for all issues linked to OLD-50
2. Update each issue to link to NEW-75 instead
3. Add comment "Migrated from OLD-50 to NEW-75"
4. Update the epic field and add a label "migrated"
```

**Conditional Epic Linking**
```
Create a new task "Optimize database queries" in project PERF. If epic PERF-100 "Performance Improvements" exists and is open, link the task to it. Otherwise, create it without an epic link and notify me.
```

**Epic Hierarchy Management**
```
I'm working with a complex epic structure:
- Create subtask "Design user interface" under DESIGN-200
- Link it to epic DESIGN-10 "UI/UX Improvements"
- Set assignee to the same person assigned to the epic
- Copy the epic's labels to this subtask
```

### Integration and Automation

**Cross-Project Integration**
```
Create a dependency link between issue FRONTEND-200 (in epic FRONTEND-50) and issue BACKEND-300 (in epic BACKEND-75). The frontend task depends on the backend completion.
```

**Automated Workflows**
```
Set up an automation: whenever an issue linked to epic TESTING-100 moves to "Done", automatically update the epic's progress percentage and notify the epic owner.
```

**External Tool Integration**
```
When I create issues linked to epic DEPLOY-50, automatically create corresponding entries in our deployment tracking spreadsheet. Use the issue key and summary as identifiers.
```

## Error Handling and Validation

### Epic Link Validation

**Epic Link Validation**
```
Try to link issue DEV-456 to epic DEV-999. If the epic doesn't exist, create the issue without an epic link and add a comment "Epic DEV-999 not found - created without epic link".
```

**Epic Status Validation**
```
Before linking issue TEST-123 to epic TEST-50, verify that the epic is not in "Done" or "Closed" status. If it is, link to epic TEST-60 instead and add an explanation comment.
```

**Bulk Validation**
```
Check all issues in project AUDIT that have epic links. Verify that their linked epics still exist and are in valid status. Report any issues with broken or invalid epic links.
```

### Error Recovery Operations

**Batch Corrections**
```
I accidentally linked 10 issues to the wrong epic. They should be linked to CORRECT-100 instead of WRONG-200. Find all issues linked to WRONG-200 today and move them to the correct epic.
```

**Data Validation**
```
Validate that all issues in epic RELEASE-400 have the required fields filled: assignee, priority, and story points. Report any that are missing these fields.
```

**Rollback Operations**
```
Something went wrong with my last epic reorganization. Restore all issues that were linked to epic BACKUP-50 yesterday back to their original epic assignments.
```

## Conversational Style Variations

### Communication Styles

**Casual/Informal Style**
```
Hey, can you quickly create a task called "Fix the login bug" in the WEBAPP project? Just link it to that epic we discussed - WEBAPP-50. Thanks!
```

**Polite/Formal Style**
```
Please create a new issue in project MOBILE with the title "Implement push notifications feature". I would appreciate if you could link this to epic MOBILE-25 and set the priority to High. Thank you.
```

**Direct/Concise Style**
```
New task: "Database migration script" in DATA project. Link to DATA-100. Priority: Critical.
```

### Question-Based Interactions

**Verification Questions**
```
Is issue API-456 currently linked to any epic? If so, which one? I need to verify the epic assignment before making changes.
```

**Status Inquiry**
```
What's the current status of all issues linked to epic CLOUD-200? Are there any that are blocked or overdue?
```

**Comparison Questions**
```
Which epic has more open issues: MOBILE-10 or MOBILE-20? Show me the breakdown by status for both.
```

### Conditional Logic Prompts

**If-Then Scenarios**
```
If issue DEV-789 exists and is in "To Do" status, then link it to epic DEV-100 and move it to "In Progress". Otherwise, create a new issue with these details and link it to the epic.
```

**Multiple Conditions**
```
Check if epic DESIGN-50 is still open. If yes, create a new task "Update wireframes" and link it there. If the epic is closed, create the task without an epic link and notify me.
```

**Fallback Logic**
```
Try to link issue TEST-300 to epic TEST-50. If that epic doesn't exist, link it to TEST-60 instead. If neither exists, just update the issue without an epic link.
```

## Domain-Specific Scenarios

### Development Workflow

**CI/CD Pipeline Management**
```
For our CI/CD epic DEV-500, create issues for each stage: "Setup pipeline", "Configure testing", "Deploy staging", "Production deployment". Link all to the epic and assign to the DevOps team.
```

### Customer Support

**Customer Escalation**
```
Customer reported issue escalated to SUPPORT-300. Create a high-priority task "Investigate customer data loss" linked to epic SUPPORT-50 and assign to senior developer immediately.
```

### Security Operations

**Security Audit Response**
```
Security audit found vulnerabilities. Create tasks for each finding and link them to epic SECURITY-200: "Fix SQL injection in login", "Update encryption keys", "Patch authentication service".
```

### Multi-Language and Localization

**Internationalization**
```
For our localization epic INTL-100, create separate tasks for each language: "German translation", "French translation", "Spanish translation". Set different due dates based on market priority.
```

**Regional Deployments**
```
Epic GLOBAL-200 needs regional breakdown. Create sub-epics for each region (EMEA, APAC, Americas) and distribute existing issues based on regional requirements.
```

## Creative and Exploratory Scenarios

### Pattern Analysis

**Brainstorming Support**
```
I'm planning a new feature epic. Before I create it, show me similar epics from the past 6 months in projects MOBILE and WEB. I want to learn from previous approaches.
```

**Pattern Recognition**
```
Analyze epic BUGS-200 and identify patterns in the linked issues. Are there common components, assignees, or root causes that might help us prevent similar bugs?
```

**Optimization Suggestions**
```
Look at epic PERFORMANCE-150 and suggest ways to reorganize or split the work. Are there too many issues? Should some be moved to a different epic?
```

---

## Usage Guidelines

### Effective Prompt Characteristics
- **Clear Intent**: State exactly what you want to accomplish
- **Specific Details**: Include project keys, issue keys, epic keys
- **Context Awareness**: Reference related work or dependencies
- **Action-Oriented**: Use clear action verbs (create, update, link, search)
- **Conditional Logic**: Handle edge cases and error scenarios

### Prompt Patterns to Avoid
- Vague references without specific keys or identifiers
- Ambiguous timeframes or conditions
- Missing project context
- Unclear success criteria
- Complex nested logic that's hard to parse

### Best Practices
1. **Start Simple**: Begin with basic operations before complex workflows
2. **Be Explicit**: Don't assume the system knows your project structure
3. **Include Validation**: Ask for confirmation on important operations
4. **Plan for Errors**: Include fallback scenarios in your prompts
5. **Use Examples**: Reference specific issue or epic keys when possible

These examples demonstrate the versatility and adaptability of natural language interactions with the JIRA MCP Server across all issue types and scenarios!

### Problem-Solving Prompts

**Troubleshooting**
```
I'm having issues with epic CLOUD-300. Some team members say their tasks aren't showing up under this epic. Can you verify all issues that should be linked to CLOUD-300?
```

**Cleanup Tasks**
```
Our project has gotten messy. Find all issues in project LEGACY that don't have epic links but probably should. Group them by component or theme so I can assign them to appropriate epics.
```

**Audit and Compliance**
```
For compliance reporting, I need a complete list of all issues created this quarter that are linked to epic SECURITY-100. Include their current status and any security labels.
```

### Team Management Prompts

**Workload Distribution**
```
I need to balance the workload for epic FEATURE-200. Show me how many issues each team member has assigned within this epic, and suggest redistributions if needed.
```

**Team Communication**
```
Send an update to all issues in epic MIGRATION-50: "Migration phase 1 complete. Please review your tasks and update status accordingly. Next standup: tomorrow 9 AM."
```

**Performance Tracking**
```
Track the velocity for epic PERFORMANCE-100. How many story points have been completed each week? Are we on track for the target completion date?
```

### Integration and Automation Prompts

**Cross-Project Links**
```
Create a dependency link between issue FRONTEND-200 (in epic FRONTEND-50) and issue BACKEND-300 (in epic BACKEND-75). The frontend task depends on the backend completion.
```

**Automated Workflows**
```
Set up an automation: whenever an issue linked to epic TESTING-100 moves to "Done", automatically update the epic's progress percentage and notify the epic owner.
```

**External Tool Integration**
```
When I create issues linked to epic DEPLOY-50, automatically create corresponding entries in our deployment tracking spreadsheet. Use the issue key and summary as identifiers.
```

### Creative and Exploratory Prompts

**Brainstorming Support**
```
I'm planning a new feature epic. Before I create it, show me similar epics from the past 6 months in projects MOBILE and WEB. I want to learn from previous approaches.
```

**Pattern Recognition**
```
Analyze epic BUGS-200 and identify patterns in the linked issues. Are there common components, assignees, or root causes that might help us prevent similar bugs?
```

**Optimization Suggestions**
```
Look at epic PERFORMANCE-150 and suggest ways to reorganize or split the work. Are there too many issues? Should some be moved to a different epic?
```

### Error Recovery and Validation Prompts

**Batch Corrections**
```
I accidentally linked 10 issues to the wrong epic. They should be linked to CORRECT-100 instead of WRONG-200. Find all issues linked to WRONG-200 today and move them to the correct epic.
```

**Data Validation**
```
Validate that all issues in epic RELEASE-400 have the required fields filled: assignee, priority, and story points. Report any that are missing these fields.
```

**Rollback Operations**
```
Something went wrong with my last epic reorganization. Restore all issues that were linked to epic BACKUP-50 yesterday back to their original epic assignments.
```

### Domain-Specific Prompts

**Development Workflow**
```
For our CI/CD epic DEV-500, create issues for each stage: "Setup pipeline", "Configure testing", "Deploy staging", "Production deployment". Link all to the epic and assign to the DevOps team.
```

**Customer Support**
```
Customer reported issue escalated to SUPPORT-300. Create a high-priority task "Investigate customer data loss" linked to epic SUPPORT-50 and assign to senior developer immediately.
```

**Security Operations**
```
Security audit found vulnerabilities. Create tasks for each finding and link them to epic SECURITY-200: "Fix SQL injection in login", "Update encryption keys", "Patch authentication service".
```

### Multi-Language and Localization Prompts

**Internationalization**
```
For our localization epic INTL-100, create separate tasks for each language: "German translation", "French translation", "Spanish translation". Set different due dates based on market priority.
```

**Regional Deployments**
```
Epic GLOBAL-200 needs regional breakdown. Create sub-epics for each region (EMEA, APAC, Americas) and distribute existing issues based on regional requirements.
```

---

## Prompt Style Guidelines

### Effective Prompt Characteristics
- **Clear Intent**: State exactly what you want to accomplish
- **Specific Details**: Include project keys, issue keys, epic keys
- **Context Awareness**: Reference related work or dependencies
- **Action-Oriented**: Use clear action verbs (create, update, link, search)
- **Conditional Logic**: Handle edge cases and error scenarios

### Prompt Patterns to Avoid
- Vague references without specific keys or identifiers
- Ambiguous timeframes or conditions
- Missing project context
- Unclear success criteria
- Complex nested logic that's hard to parse

### Best Practices
1. **Start Simple**: Begin with basic operations before complex workflows
2. **Be Explicit**: Don't assume the system knows your project structure
3. **Include Validation**: Ask for confirmation on important operations
4. **Plan for Errors**: Include fallback scenarios in your prompts
5. **Use Examples**: Reference specific issue or epic keys when possible

These additional variations demonstrate the versatility and adaptability of natural language interactions with the JIRA MCP Server!