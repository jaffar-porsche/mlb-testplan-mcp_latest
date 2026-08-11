# Jira MCP Server Prompts

> **Note:** All examples in this documentation use fictional project names (MYAPP, WEBAPP, PROJECT, etc.) and issue keys (MYAPP-123, PROJECT-456, etc.) for demonstration purposes. When using these prompts, replace them with your actual Jira project keys and issue numbers.

This directory contains context, sample prompts, and best practices for using the Jira MCP Server with AI assistants like GitHub Copilot.

## Files

### [context.md](context.md)
Complete context about the Jira MCP Server:
- Overview of capabilities
- Available operations and endpoints
- Authentication details
- Common Jira projects at Porsche
- JQL query syntax
- Issue types and statuses
- Integration modes
- Response formats

**Use this file to:** Understand what the Jira MCP Server can do and how it works.

### [sample-prompts.md](sample-prompts.md)
Curated collection of example prompts for common tasks:
- Quick start prompts
- Project management scenarios
- Bug management workflows
- Development workflow prompts
- Reporting and analytics
- Advanced query examples
- Attachment management
- Bulk operations
- Time-sensitive queries

**Use this file to:** Get started quickly with ready-to-use prompt examples.

### [best-practices.md](best-practices.md)
Comprehensive best practices guide:
- Query optimization
- Issue creation guidelines
- Update strategies
- Search patterns
- Attachment management
- Performance optimization
- Security considerations
- Error handling
- Team collaboration
- Automation tips
- Common pitfalls to avoid

**Use this file to:** Learn how to use the Jira MCP Server effectively and efficiently.

### [copilot-commands.md](copilot-commands.md)
GitHub Copilot-specific commands and patterns:
- @jira mention commands
- Conversational patterns
- Context-aware commands
- Batch operations
- Workflow helpers
- Integration with code
- Natural language variations
- Role-specific patterns
- Daily workflow examples

**Use this file to:** Master GitHub Copilot Chat interactions with Jira MCP Server.

## Quick Start

### 1. Basic Issue Search
```
Show me all open issues in the MYAPP project
```

### 2. Create an Issue
```
Create a new task in MYAPP project: "Update API documentation"
```

### 3. Update an Issue
```
Update MYAPP-123 to change status to "In Progress" and add comment "Starting work on this"
```

### 4. Search with Filters
```
Find all high priority bugs in WEBAPP project that are not done
```

### 5. Get Issue Details
```
Get details for issue MYAPP-456
```

## Using with GitHub Copilot

These prompts are designed to work naturally with GitHub Copilot when the Jira MCP Server is configured. Simply ask questions or make requests in natural language, and Copilot will use the MCP tools to interact with Jira.

### Example Session
```
You: @jira show me open MYAPP issues

Copilot: [Lists 20 open issues in MYAPP project]

You: Which ones are related to FinOps?

Copilot: [Filters results to FinOps-related issues]

You: Update MYAPP-456 to high priority

Copilot: [Updates the issue and confirms]
```

## JQL Quick Reference

### Common Queries
```jql
# My open work
assignee = currentUser() AND statusCategory != Done

# Project backlog
project = MYAPP AND statusCategory != Done ORDER BY priority DESC

# Recent updates
updated >= -7d ORDER BY updated DESC

# High priority items
priority IN (High, Critical) AND statusCategory != Done

# Epic progress
"Epic Link" = MYAPP-100
```

### Date Functions
- `now()` - Current time
- `startOfDay()`, `endOfDay()`
- `startOfWeek()`, `endOfWeek()`
- `startOfMonth()`, `endOfMonth()`
- `startOfYear()`, `endOfYear()`

### Operators
- `=` Equals
- `!=` Not equals
- `>`, `<`, `>=`, `<=` Comparisons
- `IN (val1, val2)` In list
- `NOT IN (val1, val2)` Not in list
- `~` Contains text
- `!~` Does not contain text
- `IS EMPTY`, `IS NOT EMPTY` Null checks
- `WAS`, `WAS IN`, `WAS NOT` Historical checks
- `CHANGED` Field changed

## Common Issue Types

| Type | Description | Use When |
|------|-------------|----------|
| **Epic** | Large body of work | Planning major initiatives |
| **Story** | User story with acceptance criteria | User-facing features |
| **Task** | Technical work item | General tasks and technical work |
| **Bug** | Defect or issue | Reporting problems |
| **Subtask** | Breakdown of parent issue | Splitting work into smaller pieces |
| **Improvement** | Enhancement | Improving existing functionality |

## Common Status Values

| Status | Category | Description |
|--------|----------|-------------|
| **Open** | To Do | New, not started |
| **Ready for Dev** | To Do | Ready to work on |
| **In Dev** | In Progress | Currently being developed |
| **In Progress** | In Progress | Work in progress |
| **Code Review** | In Progress | Pending review |
| **Testing** | In Progress | In QA/testing |
| **Done** | Done | Completed |
| **Closed** | Done | Closed |

## Priority Levels

| Priority | When to Use |
|----------|-------------|
| **Critical** | System down, blocking all users |
| **High** | Major functionality impaired, many users affected |
| **Medium** | Normal priority, default for most issues |
| **Low** | Minor issue, workaround available |
| **Lowest** | Nice to have, cosmetic issues |

## Useful Links

- [Jira MCP Server README](../README.md)
- [API Contracts](../API_CONTRACTS.md)
- [VS Code Integration](../VSCODE_INTEGRATION.md)
- [Extended Prompt Examples](../PROMPTS_EXAMPLES.md)
- [Get your PAT](https://skyway.porsche.com/jira/plugins/servlet/desk/portal/1)

## Tips for Effective Usage

1. **Be Specific** - Include project keys, issue types, and clear criteria
2. **Use JQL** - Learn basic JQL for powerful searches
3. **Link to Epics** - Always link stories/tasks to parent epics
4. **Add Context** - Include descriptions and comments for clarity
5. **Follow Workflow** - Respect your team's workflow and conventions
6. **Update Regularly** - Keep issue status current
7. **Use Labels** - Tag issues consistently with labels
8. **Attach Files** - Add relevant screenshots, logs, or documents

## Getting Help

If you encounter issues or need help:
1. Check the [context.md](context.md) for understanding capabilities
2. Review [sample-prompts.md](sample-prompts.md) for examples
3. Consult [best-practices.md](best-practices.md) for guidance
4. Verify your PAT is valid and has correct permissions
5. Check server logs for error details

## Contributing

To add new prompts or improve documentation:
1. Add examples to [sample-prompts.md](sample-prompts.md)
2. Update best practices in [best-practices.md](best-practices.md)
3. Keep context current in [context.md](context.md)
4. Test prompts before adding them

---

**Happy Issue Tracking! 🚀**