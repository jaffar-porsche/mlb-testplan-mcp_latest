# VS Code Integration Guide for Confluence MCP Server

This guide explains how to integrate the Confluence MCP (Model Context Protocol) server with VS Code's Agent Mode, enabling you to interact with Confluence directly through GitHub Copilot Chat.

## Overview

The Confluence MCP server provides a bridge between VS Code's AI agent and your Confluence instance, allowing you to:
- Create, read, and update Confluence pages
- Search across Confluence content
- List available spaces
- Manage page hierarchies

All through natural language interactions with GitHub Copilot in VS Code.

## Prerequisites

- VS Code with GitHub Copilot extension enabled
- Python 3.10 or later
- Access to Confluence with a Personal Access Token (PAT)

## Quick Setup

#### 1. Configure Environment

+ Navigate to the `confluence-mcp` directory, i.e.

```bash
# Navigate to the confluence-mcp directory
cd confluence-mcp
```

+ Create a `.env` file in the `confluence-mcp` directory:

```env
CONFLUENCE_PAT=your_confluence_personal_access_token_here
```

#### 2. Start the Confluence MCP Server

Start the Confluence MCP server using either `start-mcp.bat` (Windows) or `start-mcp.sh` (Linux/macOS)

##### Windows (PowerShell/Command Prompt)
```cmd
start-mcp.bat
```

##### Linux/macOS
```bash
./start-mcp.sh
```

 The following steps are performed automatically:

- The script checks for a suitable Python version (3.10+ required)
- If a virtual environment (`venv`) does not exist or uses an incompatible Python version, it will be (re)created
- The script activates the virtual environment
- If the venv was recreated, dependencies are installed from `requirements.txt` (if present) or a default package list
- The MCP server is started on `http://localhost:8001/mcp/`

This means you do not need to manually install dependencies before starting the server—the script will handle it for you if needed.

##### Note:
**The server will start on `http://localhost:8001/mcp/`**

#### 3. Add MCP Server to VS Code

1. Open VS Code
2. Press `Ctrl+Shift+P` (Windows/Linux) or `Cmd+Shift+P` (macOS)
3. Run the command: **MCP: Add Server**
4. Choose **"Add from URL"**
5. Enter: `http://localhost:8001/mcp/`
6. Give it a name: `Confluence MCP Server`
7. VS Code will automatically detect and configure the server

##### Example Configuration

Update your `mcp.json` file as follows:

```jsonc
{
	"servers": {
		"MCP confluence server": {
			"url": "http://localhost:8001/mcp",
			"type": "http"
		}
	},
	"inputs": []
}
```



## Using the MCP Server in VS Code

### Enabling Agent Mode

1. Open GitHub Copilot Chat in VS Code
2. Type `@copilot` to enter agent mode
3. The Confluence MCP tools will be available automatically

### Available Tools

The Confluence MCP server provides these tools through VS Code:

#### 1. **Create Page** (`mcp_mcp_confluenc_create_page_create_page_post`)
Create new Confluence pages with rich content.

**Example prompts:**
- "Create a new page in the PROJ space titled 'Project Overview' with a basic structure"
- "Add a page called 'Meeting Notes' under the existing page ID 12345"

#### 2. **Get Page** (`mcp_mcp_confluenc_get_page_page__page_id__get`)
Retrieve existing page content and metadata.

**Example prompts:**
- "Show me the content of page ID 67890"
- "What's on the project documentation page?"

#### 3. **Update Page** (`mcp_mcp_confluenc_update_page_page__page_id__put`)
Modify existing pages with new content or titles.

**Example prompts:**
- "Update page ID 12345 with the latest project status"
- "Change the title of the documentation page to 'Updated Documentation'"

#### 4. **Search Content** (`mcp_mcp_confluenc_search_content_search_get`)
Find pages across Confluence using search terms.

**Example prompts:**
- "Search for pages about 'API documentation' in the DEV space"
- "Find all pages mentioning 'deployment process'"

#### 5. **List Spaces** (`mcp_mcp_confluenc_list_spaces_spaces_get`)
Discover available Confluence spaces.

**Example prompts:**
- "What Confluence spaces are available?"
- "Show me all the spaces I have access to"

### Tool Picker and Control

VS Code's tool picker gives you control over which MCP tools the agent can access:

1. When prompted, you'll see available tools
2. Select which tools you want to enable for the current session
3. You can enable/disable tools at any time during the conversation

## Example Workflows

### Creating Documentation

```
@copilot Create a new project documentation page in the PROJ space. Include sections for:
- Project Overview
- Architecture
- Getting Started
- API Reference
```

### Content Management

```
@copilot Search for all pages in the DEV space that mention "database migration" and then update the main database page with a summary of the findings.
```

### Knowledge Discovery

```
@copilot List all available spaces, then search for onboarding documentation across all of them.
```

## Security and Best Practices

### Secure Token Management

VS Code's MCP integration supports secure token storage:

- Use input variables for PATs (marked as `secret: true`)
- Tokens are encrypted and stored securely by VS Code
- Never commit tokens to source control

### Access Control

- The tool picker lets you control which tools are available per session
- Review tool descriptions before enabling them
- You can revoke tool access at any time

### Content Format

When working with Confluence content:
- Content should be in Confluence storage format (HTML-like)
- The MCP server handles format conversion automatically
- Rich formatting is supported (bold, italic, lists, tables, etc.)

## Troubleshooting

### Common Issues

**Server won't start:**
- Check that Python dependencies are installed: `pip install -r requirements.txt`
- Verify the CONFLUENCE_PAT environment variable is set
- Ensure port 8001 is available

**VS Code can't connect:**
- Confirm the server is running on `http://localhost:8001/mcp/`
- Check VS Code's MCP server logs in the Output panel
- Try restarting both the server and VS Code

**Authentication failures:**
- Verify your Confluence PAT is valid and has appropriate permissions
- Check if your network requires proxy settings
- Confirm the Confluence base URL is correct

### Debugging

To enable detailed logging:

1. Start the server with debug mode:
   ```bash
   uvicorn mcp_server:app --host localhost --port 8001 --log-level debug
   ```

2. Check VS Code's Output panel for MCP-related logs

3. Use the test scripts in the repository:
   ```bash
   python test_client.py
   ```

### Network Configuration

For corporate environments:
- The server includes proxy configuration for Porsche networks
- Modify the `PROXIES` settings in `mcp_server.py` as needed
- Ensure your firewall allows connections to the Confluence API

## Advanced Usage

### Custom Tool Development

The MCP server can be extended with additional tools:

1. Add new endpoints to `mcp_server.py`
2. Implement the FastAPI MCP decorators
3. Restart the server to make new tools available

### Integration with Other Systems

The Confluence MCP server can work alongside other MCP servers:
- GitHub MCP Server for repository operations
- Azure MCP Server for cloud resources
- Custom MCP servers for internal tools

## Further Resources

- [VS Code MCP Documentation](https://code.visualstudio.com/docs/copilot/chat/mcp-servers)
- [Model Context Protocol Specification](https://modelcontextprotocol.io/)
- [VS Code Agent Mode Guide](https://code.visualstudio.com/docs/copilot/chat/chat-agent-mode)
- [Confluence REST API Documentation](https://developer.atlassian.com/cloud/confluence/rest/v2/)

## Support

For issues specific to this MCP server:
1. Check the server logs for error messages
2. Verify your Confluence permissions
3. Test the API endpoints directly using the provided test scripts
4. Review the VS Code MCP integration documentation

---

**Note:** This integration leverages VS Code's native MCP support introduced in recent updates, providing a seamless and secure way to extend GitHub Copilot's capabilities with Confluence integration.