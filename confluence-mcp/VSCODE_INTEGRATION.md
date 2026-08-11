# VS Code Integration Guide for Confluence MCP Server

This guide explains how to integrate the Confluence MCP (Model Context Protocol) server with VS Code's GitHub Copilot, enabling you to interact with Confluence directly through natural language.

## Overview

The Confluence MCP server provides a bridge between VS Code's AI agent and your Confluence instance, allowing you to:
- Create and update Confluence pages
- Search for content using CQL (Confluence Query Language)
- Navigate page hierarchies
- List and browse spaces
- Manage documentation directly from VS Code

All through natural language interactions with GitHub Copilot in VS Code.

## Prerequisites

- VS Code with GitHub Copilot extension enabled
- Python 3.10 or later
- Confluence Personal Access Token (PAT)

## Quick Setup

### 1. Configure Environment

Navigate to the `confluence-mcp` directory and create a `.env` file:

```env
CONFLUENCE_PAT=your_confluence_personal_access_token_here
CONFLUENCE_BASE_URL=https://api.skyway.porsche.com/confluence
MCP_PORT=8001

# Optional: Proxy settings
HTTP_PROXY=http://http-proxy.porsche.org:3128
HTTPS_PROXY=http://http-proxy.porsche.org:3133
```

### 2. Start the Confluence MCP Server

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
- Start server on `http://localhost:8001/mcp/`

### 3. Add MCP Server to VS Code

1. Open VS Code
2. Press `Ctrl+Shift+P` (Windows/Linux) or `Cmd+Shift+P` (macOS)
3. Run command: **MCP: Add Server**
4. Choose **"Add from URL"**
5. Enter: `http://localhost:8001/mcp`
6. Give it a name: `Confluence MCP Server`

#### Example Configuration

Your `mcp.json` should look like this:

```jsonc
{
  "servers": {
    "Confluence MCP Server": {
      "url": "http://localhost:8001/mcp",
      "type": "http"
    }
  },
  "inputs": []
}
```

## Using the MCP Server in VS Code

### Basic Usage

1. Open GitHub Copilot Chat in VS Code
2. Start chatting - the Confluence MCP tools are available automatically
3. Example queries:
   - "Create a new page in space PROJ with title 'Architecture Overview'"
   - "Show me the details of page 12345678"
   - "Search for 'API documentation' in the TECH space"
   - "List all available Confluence spaces"
   - "Get the child pages under page 87654321"

### Available Operations

The MCP server exposes these operations as tools:

#### Page Management
- **Create Page** - Create a new Confluence page in a specified space with optional parent
- **Create Page Simple** - Simplified API for creating pages with less configuration
- **Get Page** - Retrieve comprehensive page details including content and metadata
- **Update Page** - Modify page title and/or content
- **Get Child Pages** - List all child pages of a specific page
- **Get Page Ancestors** - View the breadcrumb trail of parent pages

#### Search & Discovery
- **Search Content** - Search using CQL (Confluence Query Language) with advanced filters
- **Search Simple** - Quick search within a specific space
- **List Spaces** - Browse all available Confluence spaces

#### Connection Management
- **Health Check** - Verify the MCP server is running
- **Test Connection** - Validate Confluence authentication and connectivity

### Example Conversations

**Creating a page:**
```
You: Create a new page in space PROJ titled "API Documentation" 
     with a heading and some initial content

Copilot: [Uses create_page tool] 
         ✓ Created page: API Documentation (ID: 12345678)
         URL: https://skyway.porsche.com/confluence/pages/viewpage.action?pageId=12345678
```

**Searching content:**
```
You: Find all pages about "authentication" in the DEV space

Copilot: [Uses search_content tool]
         Found 5 pages:
         - User Authentication Flow (ID: 11111111)
         - OAuth2 Implementation Guide (ID: 22222222)
         - API Authentication Best Practices (ID: 33333333)
         - SSO Configuration (ID: 44444444)
         - Authentication Troubleshooting (ID: 55555555)
```

**Viewing page hierarchy:**
```
You: Show me all child pages under the Architecture Overview page (ID: 12345678)

Copilot: [Uses get_child_pages tool]
         Architecture Overview has 4 child pages:
         - System Architecture (ID: 12345680)
         - Database Design (ID: 12345681)
         - API Architecture (ID: 12345682)
         - Security Architecture (ID: 12345683)
```

**Updating a page:**
```
You: Update page 12345678 to add information about the new API endpoint

Copilot: [Uses get_page to retrieve current content, then update_page]
         ✓ Successfully updated page 12345678
         Version: 3 → 4
```

## Content Format Guidelines

### Confluence Storage Format

When creating or updating pages, content should be in Confluence's storage format (similar to HTML):

**Basic Formatting:**
```html
<h1>Main Heading</h1>
<h2>Subheading</h2>
<p>This is a paragraph with <strong>bold</strong> and <em>italic</em> text.</p>
```

**Lists:**
```html
<ul>
  <li>Unordered item 1</li>
  <li>Unordered item 2</li>
</ul>

<ol>
  <li>Ordered item 1</li>
  <li>Ordered item 2</li>
</ol>
```

**Code Blocks:**
```html
<ac:structured-macro ac:name="code">
  <ac:parameter ac:name="language">python</ac:parameter>
  <ac:plain-text-body><![CDATA[
def hello_world():
    print("Hello, World!")
  ]]></ac:plain-text-body>
</ac:structured-macro>
```

**Tables:**
```html
<table>
  <tbody>
    <tr>
      <th>Header 1</th>
      <th>Header 2</th>
    </tr>
    <tr>
      <td>Cell 1</td>
      <td>Cell 2</td>
    </tr>
  </tbody>
</table>
```

**Links:**
```html
<p>Visit <a href="https://example.com">this website</a> for more info.</p>
```

### Tips for AI-Assisted Content Creation

When using Copilot to generate Confluence pages:
- Describe the structure you want: "Create a page with sections for Overview, Requirements, and Implementation"
- The AI will automatically format content in Confluence storage format
- You can ask for specific macros: "Include a table of contents macro"
- Request specific formatting: "Make the heading bold and add bullet points"

## Advanced CQL Search Examples

The MCP server supports powerful Confluence Query Language (CQL) searches:

**Search by type and space:**
```
You: Search for all pages in space TECH that contain "API"
Copilot uses CQL: type=page AND space=TECH AND text~"API"
```

**Search by creator and date:**
```
You: Find pages created by john.doe in the last 7 days
Copilot uses CQL: creator=john.doe AND created >= now("-7d")
```

**Search by label:**
```
You: Find all pages tagged with "architecture" and "draft"
Copilot uses CQL: label="architecture" AND label="draft"
```

## Troubleshooting

### Server Connection Issues

If VS Code can't connect to the MCP server:

1. **Check server is running:**
   ```powershell
   # Test the health endpoint
   curl http://localhost:8001/health
   
   # Test Confluence connection
   curl http://localhost:8001/test_connection
   ```

2. **Verify the URL in mcp.json:**
   - Should be `http://localhost:8001/mcp` (note: port 8001 for Confluence, 8000 for Jira)
   - Type should be `"http"`

3. **Check firewall/antivirus:**
   - Ensure localhost port 8001 is accessible
   - Try a different port by setting `MCP_PORT` in `.env`

### Authentication Errors

If you see Confluence authentication errors:

1. **Verify your PAT is valid:**
   - Check `.env` file has correct `CONFLUENCE_PAT`
   - Verify the PAT hasn't expired
   - Create a new PAT via [Service Desk](https://skyway.porsche.com/jira/plugins/servlet/desk/portal/1/create/9141) if needed

2. **Test connection manually:**
   ```powershell
   curl -H "Authorization: Bearer YOUR_PAT" https://api.skyway.porsche.com/confluence/rest/api/content?limit=1
   ```

3. **Check proxy settings:**
   - If behind corporate proxy, ensure `HTTP_PROXY` and `HTTPS_PROXY` are set
   - Verify proxy URLs are correct (e.g., `http://http-proxy.porsche.org:3128`)

### Content Format Issues

If pages aren't rendering correctly:

1. **Check storage format:**
   - Ensure content uses Confluence storage format (HTML-like), not wiki markup
   - Validate macro syntax is correct

2. **Test with simple content first:**
   ```
   You: Create a simple test page with just a heading and paragraph
   ```

3. **View created page in browser:**
   - Check the URL provided in the response
   - Edit in Confluence UI to see the storage format

### Tool Warnings in Logs

You may see warnings like:
```
WARNING: Tool 'create_page_create_page_post' not listed, no validation will be performed
```

**This is non-critical** - the tools still work correctly. This is a known fastapi-mcp integration issue that doesn't affect functionality.

### Direct HTTP Testing

If you need to test the server directly (outside VS Code):

**Health Check:**
```bash
curl http://localhost:8001/health
```

**Test Connection:**
```bash
curl http://localhost:8001/test_connection
```

**List Spaces:**
```bash
curl http://localhost:8001/spaces
```

**Search Content:**
```bash
curl "http://localhost:8001/search?query=documentation&limit=5"
```

**MCP Protocol (requires SSE headers):**
```bash
curl -X POST "http://localhost:8001/mcp" \
  -H "Accept: application/json, text/event-stream" \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}},"id":1}'
```

Note: Direct MCP protocol testing requires session management and is complex. Use VS Code integration instead.

## Common Use Cases

### Documentation Maintenance

**Use Copilot to:**
- "Create a release notes page for version 2.5.0 in the RELEASES space"
- "Update the API documentation page to include the new /users endpoint"
- "Find all outdated pages that mention 'deprecated API v1'"

### Knowledge Base Navigation

**Use Copilot to:**
- "Show me all pages under the Team Onboarding section"
- "List the breadcrumb trail for page 12345678"
- "Find all child pages of the Architecture space home page"

### Content Organization

**Use Copilot to:**
- "List all spaces I have access to"
- "Search for pages labeled 'review-needed' in the PROJ space"
- "Find pages modified in the last week in the DEV space"

### Collaborative Editing

**Use Copilot to:**
- "Get the current content of the API Guide page so I can update it"
- "Create a child page under the existing Design Docs page for mobile architecture"
- "Search for pages created by the architecture team this month"

## Best Practices

### Working with Pages

1. **Always check existing content before updating:**
   - Use `get_page` to retrieve current content
   - Preserve existing information unless explicitly replacing it

2. **Use descriptive titles:**
   - Make page titles clear and searchable
   - Follow your team's naming conventions

3. **Organize with hierarchies:**
   - Create parent-child relationships for better structure
   - Use `parent_id` when creating related pages

### Searching Effectively

1. **Start broad, then narrow:**
   - Begin with simple keyword searches
   - Add space filters and date ranges as needed

2. **Use labels for categorization:**
   - Search by labels to find related content
   - Combine multiple labels for precise results

3. **Leverage CQL for complex queries:**
   - Learn basic CQL syntax for advanced searches
   - Use date ranges, creators, and content types

### Content Creation

1. **Use templates when possible:**
   - Ask Copilot to create pages with standard structures
   - Define section headings before generating content

2. **Preview in Confluence:**
   - Always review AI-generated content in the Confluence UI
   - Make final formatting adjustments in the editor if needed

3. **Iterate incrementally:**
   - Create basic structure first
   - Add detailed content in subsequent updates

## Additional Resources

- [OpenAPI Documentation](http://localhost:8001/docs) - Interactive API documentation when server is running
- [Confluence REST API Documentation](https://developer.atlassian.com/cloud/confluence/rest/v2/intro/)
- [Confluence Storage Format Reference](https://confluence.atlassian.com/doc/confluence-storage-format-790796544.html)
- [CQL (Confluence Query Language) Reference](https://developer.atlassian.com/cloud/confluence/cql/)

## Feedback and Support

If you encounter issues or have suggestions for improvement:
- Check the [README.md](README.md) for additional setup information
- Review server logs for detailed error messages
- Test connectivity using the provided test scripts
- Ensure your PAT has appropriate permissions for the operations you're attempting

---

**Happy documenting! 📝**
