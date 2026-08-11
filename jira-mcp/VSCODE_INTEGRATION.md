# VS Code Integration Guide for Jira MCP Server

This guide explains how to integrate the Jira MCP (Model Context Protocol) server with VS Code's GitHub Copilot, enabling you to interact with Jira directly through natural language.

## Overview

The Jira MCP server provides a bridge between VS Code's AI agent and your Jira instance, allowing you to:
- Create, read, and update Jira issues
- Search issues using JQL
- Manage issue hierarchies and epics  
- Handle attachments
- View sprints and roadmaps

All through natural language interactions with GitHub Copilot in VS Code.

## Prerequisites

- VS Code with GitHub Copilot extension enabled
- Python 3.10 or later
- Jira Personal Access Token (PAT)

## Quick Setup

### 1. Configure Environment

Navigate to the `jira-mcp` directory and create a `.env` file:

```env
JIRA_PAT=your_jira_personal_access_token_here
JIRA_BASE_URL=https://cicd.skyway.porsche.com
MCP_PORT=8000

# Optional: Proxy settings
HTTP_PROXY=your-proxy-url
HTTPS_PROXY=your-proxy-url
```

### 2. Start the Jira MCP Server

**Windows:**
```cmd
start-mcp.bat
```

**Linux/macOS:**
```bash
./start-mcp.sh
```

The script will automatically:
- Check for Python 3.10+
- Create/update virtual environment if needed
- Install dependencies
- Start server on `http://localhost:8000/mcp/`

### 3. Add MCP Server to VS Code

1. Open VS Code
2. Press `Ctrl+Shift+P` (Windows/Linux) or `Cmd+Shift+P` (macOS)
3. Run command: **MCP: Add Server**
4. Choose **"Add from URL"**
5. Enter: `http://localhost:8000/mcp`
6. Give it a name: `Jira MCP Server`

#### Example Configuration

Your `mcp.json` should look like this:

```jsonc
{
  "servers": {
    "Jira MCP Server": {
      "url": "http://localhost:8000/mcp",
      "type": "http"
    }
  },
  "inputs": []
}
```

## Using the MCP Server in VS Code

### Basic Usage

1. Open GitHub Copilot Chat in VS Code
2. Start chatting - the Jira MCP tools are available automatically
3. Example queries:
   - "Create a new task in project MYPROJ"
   - "Show me the details of issue MYPROJ-123"
   - "Search for all open issues assigned to me"
   - "Get the hierarchy for epic MYPROJ-100"

### Available Operations

The MCP server exposes these operations as tools:

#### Issue Management
- **Create Issue** - Create new issues with optional epic linking
- **Get Issue** - Retrieve comprehensive issue details
- **Update Issue** - Modify issue fields, change status, add comments
- **Search Issues** - Search using JQL queries

#### Hierarchy & Planning
- **Get Issue Hierarchy** - View epic → feature → story relationships
- **Get Epic Roadmap** - PI-based roadmap with feature commitments
- **List Sprints** - Browse available sprints for a board
- **Get Sprint Details** - View issues in a specific sprint

#### Attachments
- **Upload Attachment** - Add files to issues
- **List Attachments** - View all attachments on an issue
- **Delete Attachment** - Remove attachments

#### Projects & Links
- **List Projects** - Browse available Jira projects
- **Create Issue Link** - Link related issues
- **Delete Issue Link** - Remove issue links

### Example Conversations

**Creating an issue:**
```
You: Create a new story in project MYPROJ titled "Add user authentication" 
     and link it to epic MYPROJ-50

Copilot: [Uses create_issue tool] 
         ✓ Created issue MYPROJ-789: Add user authentication
         Linked to epic MYPROJ-50
```

**Viewing hierarchy:**
```
You: Show me the full hierarchy under epic MYPROJ-100

Copilot: [Uses get_issue_hierarchy tool]
         MYPROJ-100: User Management Epic | 15/30 done (50%)
           MyPROJ-101: User Registration (Done)
             MYPROJ-105: Create signup form (Done)
             MYPROJ-106: Add email verification (In Progress)
           MYPROJ-102: User Profile (In Progress)
             ...
```

**Searching issues:**
```
You: Find all high priority issues assigned to me that are in progress

Copilot: [Uses search_issues tool with JQL]
         Found 3 issues:
         - MYPROJ-123: Fix authentication bug
         - MYPROJ-456: Implement payment gateway
         - MYPROJ-789: Add user analytics
```

## Troubleshooting

### Server Connection Issues

If VS Code can't connect to the MCP server:

1. **Check server is running:**
   ```powershell
   # Test the endpoints
   curl http://localhost:8000/docs
   ```

2. **Verify the URL in mcp.json:**
   - Should be `http://localhost:8000/mcp` (without trailing slash preferred)
   - Type should be `"http"`

3. **Check firewall/antivirus:**
   - Ensure localhost port 8000 is accessible
   - Try a different port by setting `MCP_PORT` in `.env`

### Authentication Errors

If you see Jira authentication errors:

1. **Verify your PAT is valid:**
   - Check `.env` file has correct `JIRA_PAT`
   - Verify the PAT hasn't expired
   - Test manually: `curl -H "Authorization: Bearer YOUR_PAT" https://cicd.skyway.porsche.com/rest/api/2/myself`

2. **Check proxy settings:**
   - If behind corporate proxy, ensure `HTTP_PROXY` and `HTTPS_PROXY` are set

### Tool Warnings in Logs

You may see warnings like:
```
WARNING: Tool 'get_issue_issue__issue_key__get' not listed, no validation will be performed
```

**This is non-critical** - the tools still work correctly. This is a known fastapi-mcp integration issue that doesn't affect functionality.

### Direct HTTP Testing

If you need to test the server directly (outside VS Code):

**REST API (no special headers):**
```bash
curl http://localhost:8000/projects
curl http://localhost:8000/issue/MYPROJ-123
```

**MCP Protocol (requires SSE headers):**
```bash
curl -X POST "http://localhost:8000/mcp" \
  -H "Accept: application/json, text/event-stream" \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}},"id":1}'
```

Note: Direct MCP protocol testing requires session management and is complex. Use VS Code integration instead.

## Additional Resources

- [OpenAPI Documentation](http://localhost:8000/docs) - Interactive API documentation when server is running