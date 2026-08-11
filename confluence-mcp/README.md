# Confluence MCP Server

Easily connect to Confluence via MCP using a Private Access Token (PAT).

## Getting Started

1. [Create a PAT](https://skyway.porsche.com/jira/plugins/servlet/desk/portal/1/create/9141) using the Service Desk
2. Copy your PAT to a `.env` file (see `.env.example` for guidance)
3. Configure additional settings if needed:
   - Set `CONFLUENCE_BASE_URL` if using a different Confluence instance
   - Set proxy variables (`HTTP_PROXY`, `HTTPS_PROXY`) if behind a corporate firewall
   - Set `MCP_PORT` to configure the server port (default is 8001)
   - Set `MCP_TRANSPORT` to `http` (default) or `stdio` to select the MCP transport protocol

### Option 1: Docker

Run the Confluence MCP server using Docker:

```
# From the confluence-mcp directory
docker-compose up -d

# Or from the parent mcporsche directory to run all MCP servers
cd ..
docker-compose up -d confluence-mcp
```

The server will be available at:
```
http://localhost:8001/mcp/
```

To stop the server:
```bash
docker-compose down
```

### Option 2: Local Installation

Start the server:
```bash
./start-mcp.sh
```

Configure your MCP Client to use the server URL:
```
http://localhost:<MCP_Port>/mcp/
```
     
i.e.
```
http://localhost:8001/mcp/
```

## Available Endpoints

### Pages

#### Create Page
- **POST** `/create_page`
- Create a new Confluence page in a specified space
- Parameters:
  - `space_key`: The key of the space where the page will be created
  - `title`: The title of the new page
  - `body`: The content of the page (in Confluence storage format)
  - `parent_id` *(optional)*: ID of the parent page

#### Create Page (Simplified)
- **POST** `/create_page_simple`
- Simplified page creation using the library's default method
- Same parameters as `/create_page`

#### Get Page
- **GET** `/page/{page_id}`
- Retrieve details for a specific Confluence page
- Returns page content, metadata, version, and URL

#### Update Page
- **PUT** `/page/{page_id}`
- Update an existing Confluence page
- Parameters:
  - `title` *(optional)*: New title for the page
  - `body` *(optional)*: New content for the page

#### Delete Page
- **DELETE** `/page/{page_id}`
- Delete a Confluence page (moves to trash, restorable from Confluence UI)
- Parameters:
  - `cascade` *(optional)*: `"false"` (default) reparents child pages to the space root. `"true"` deletes the page and ALL descendant pages recursively.
- When `cascade=false` and the page has children, the response includes a `warning` and `reparented_children` list

**Example:**
```bash
# Delete a leaf page
curl -X DELETE "http://localhost:8001/page/2347613274"

# Delete a page and all its children
curl -X DELETE "http://localhost:8001/page/2347613274?cascade=true"
```

#### Move Page
- **PUT** `/page/{page_id}/move`
- Move a page under a new parent, or to the space root
- All child pages move with it. Circular references are rejected.
- Parameters:
  - `parent_id` *(optional)*: Target parent page ID. Omit or `null` to move to space root.

**Example:**
```bash
curl -X PUT "http://localhost:8001/page/12345/move" \
  -H "Content-Type: application/json" \
  -d '{"parent_id": "55555"}'
```

### Hierarchy

#### Get Child Pages
- **GET** `/page/{page_id}/children`
- Retrieve direct child pages of a specific page
- Parameters:
  - `start` *(optional)*: Pagination offset (default 0)
  - `limit` *(optional)*: Max results per request (default 50, max 200)
  - `fetch_all` *(optional)*: `"true"` to fetch ALL children regardless of limit (use with caution on large trees)
- Response includes `has_more` (based on `_links.next`, not size) for reliable pagination

#### Get Page Ancestors
- **GET** `/page/{page_id}/ancestors`
- Retrieve the ancestor (parent) chain from root to immediate parent
- Returns `ancestors` list, `depth`, `page_title`, and `space`

### Search

#### Search Content (Text)
- **GET** `/search`
- Full-text search across page content and titles (wraps query in `text~` CQL)
- Parameters:
  - `query`: The text to search for
  - `space_key` *(optional)*: Restrict search to a single space
  - `limit` *(optional)*: Max results (default 10)

#### Search CQL (Raw)
- **GET** `/search_cql`
- Execute a raw CQL (Confluence Query Language) query for structural searches
- Parameters:
  - `cql`: The CQL query string
  - `limit` *(optional)*: Max results (default 25)

**Example CQL queries:**
```bash
# All pages in a space
curl "http://localhost:8001/search_cql?cql=type%20%3D%20page%20AND%20space%20%3D%20TEST"

# Pages under a parent
curl "http://localhost:8001/search_cql?cql=type%20%3D%20page%20AND%20ancestor%20%3D%2012345"

# Recently modified
curl "http://localhost:8001/search_cql?cql=type%20%3D%20page%20AND%20lastModified%20%3E%20now('-7d')"

# Pages by label
curl "http://localhost:8001/search_cql?cql=type%20%3D%20page%20AND%20label%20%3D%20'architecture'"
```

#### Simple Search (Title)
- **GET** `/search_simple`
- Search within a specific space by title (case-insensitive substring match). Paginates through all pages internally.
- Parameters:
  - `space_key`: The Confluence space key
  - `query` *(optional)*: Title filter. Omit to list all pages.
  - `start` *(optional)*: Pagination offset (default 0)
  - `limit` *(optional)*: Max results (default 50, max 200)

### Spaces

#### List Spaces
- **GET** `/spaces`
- List all available Confluence spaces
- Returns space keys, names, and types

#### List Space Pages
- **GET** `/space/{space_key}/pages`
- List all pages in a space, including each page's parent ID
- Useful for discovering orphan pages and understanding the full page tree
- Parameters:
  - `start` *(optional)*: Pagination offset (default 0)
  - `limit` *(optional)*: Max results per request (default 100, max 200)

### Users

#### Search Users
- **GET** `/users/search`
- Search for Confluence users by display name or username
- Uses CQL search (`type = "user" AND user.fullname ~ "query"`), falls back to exact username lookup on older Confluence versions
- Parameters:
  - `query`: Name or username to search for
  - `max_results` *(optional)*: Maximum number of results (default 10, max 50)
- Returns: `{total, users: [{username, displayName, userKey, type}]}`

**Example:**
```bash
curl "http://localhost:8001/users/search?query=sandro&max_results=5"
```

### Comments

#### Add Comment
- **POST** `/page/{page_id}/comments`
- Add a comment to a Confluence page
- Parameters:
  - `body`: The comment text (Confluence storage format HTML or plain text)

#### Get Comments
- **GET** `/page/{page_id}/comments`
- Retrieve comments from a Confluence page
- Parameters:
  - `limit` *(optional)*: Maximum number of comments (default 25)

#### Delete Comment
- **DELETE** `/page/{page_id}/comments/{comment_id}`
- Delete a comment from a page

### Health & Connection

#### Health Check
- **GET** `/health`
- Simple health check returning service status

#### Test Connection
- **GET** `/test_connection`
- Test Confluence authentication and return user info

## Environment Variables

Create a `.env` file with the following variables:

### Required
```
CONFLUENCE_PAT=your_confluence_personal_access_token_here
```

### Optional
```
# Confluence base URL (default: https://api.skyway.porsche.com/confluence)
CONFLUENCE_BASE_URL=https://your-confluence-instance.com

# Proxy settings (only if needed)
HTTP_PROXY=http://proxy-server:port
HTTPS_PROXY=http://proxy-server:port

# Server port (default: 8001)
MCP_Port=8001

# MCP transport protocol (default: http)
# 'http': SSE/HTTP transport – compatible with Claude Code and most MCP clients
# 'stdio': stdio transport – compatible with VS Code Copilot and similar tools
# MCP_TRANSPORT=http
```

### Example .env file
```
CONFLUENCE_PAT=ATATTxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
CONFLUENCE_BASE_URL=https://api.skyway.porsche.com/confluence
HTTP_PROXY=http://http-proxy.porsche.org:3128
HTTPS_PROXY=http://http-proxy.porsche.org:3133
MCP_Port=8001
MCP_TRANSPORT=http
```

**Note:** The proxy settings are only required if you're behind a corporate firewall. If no proxy environment variables are set, the server will connect directly to Confluence.

## Content Format

When creating or updating pages, the body content should be in Confluence's storage format. This is similar to HTML but with Confluence-specific markup. For example:

```html
<h1>My Page Title</h1>
<p>This is a paragraph with <strong>bold text</strong> and <em>italic text</em>.</p>
<ul>
<li>List item 1</li>
<li>List item 2</li>
</ul>
```

## Limitations
- Content must be provided in Confluence storage format (HTML-like)
- Deleted pages are moved to trash (restorable from Confluence UI)
- `search_simple` fetches all pages in a space to filter by title — may be slow on very large spaces (1000+ pages)

## Examples

### Creating a Simple Page
```python
# Example API call to create a page
POST /create_page
{
    "space_key": "TEST",
    "title": "My New Page",
    "body": "<h1>Welcome</h1><p>This is my new page content.</p>"
}
```

### Searching for Content
```python
# Example API call to search
GET /search?query=project%20documentation&space_key=PROJ&limit=5
```

> Feel free to provide feedback if you encounter any issues!

## Testing the Server

The confluence-mcp comes with several test clients to help you verify the server functionality:

### 1. Interactive Python Test Client
```bash
python test_client.py
```
Features:
- Interactive menu-driven interface
- Test all endpoints with custom data
- Connection testing
- Pretty-printed JSON responses

### 2. Simple Automated Test
```bash
python simple_test.py
```
- Runs automated tests with sample data
- Quick verification that all endpoints work
- Demonstrates basic API usage

### 3. Postman Collection
Import `confluence-mcp.postman_collection.json` into Postman for GUI-based testing:
- Pre-configured requests for all endpoints
- Environment variables for easy customization
- Automatic extraction of page IDs for dependent requests

### 4. Command Line Testing

**Linux/macOS (cURL):**
```bash
chmod +x test_curl.sh
./test_curl.sh
```

**Windows (PowerShell):**
```powershell
.\test_powershell.ps1
```

### Test Configuration
Before running tests, make sure to:
1. Update the `SPACE_KEY` variable in test scripts to a valid Confluence space
2. Ensure your `.env` file contains a valid `CONFLUENCE_PAT`
3. Start the server with `./start-mcp.sh` or `start-mcp.bat`

## Troubleshooting

### Line Ending Issues (Windows + Git Bash)
If you see `$'\r': command not found`, you have a line ending issue:

**Quick Fix:**
```bash
# Option 1: Use the fix script
chmod +x fix-lineendings.sh
./fix-lineendings.sh

# Option 2: Use Windows batch file instead
start-mcp.bat

# Option 3: Clean reset
rm -rf venv
./setup.sh
```

### Common Issues
- **`CONFLUENCE_PAT environment variable is not set`**: Edit your `.env` file
- **`Cannot connect to server`**: Make sure the server is running on port 8001
- **Search failures**: Try the `/search_simple` endpoint instead
- **Permission errors**: Verify your PAT has the correct permissions

## Integration Guides

The [**integration**](./integration/) directory contains documents for integration of the Confluence MCP server with various tools and platforms - see [`VSCode_integration.md`](integration/vscode/VSCode_integration.md)

These guides provide practical examples and templates for AI-assisted Confluence workflows, making it easy to integrate the server into your development environment and AI tools.

## API Documentation

You can view and interact with the full API documentation at *http://localhost:8001/docs*:

```
http://localhost:<MCP_Port>/docs/
```

## Confluence PAT Expiration

Confluence Personal Access Tokens (PAT) expire after **30 days**. When your token expires:

1. Generate a new token via the [Create Request](https://skyway.porsche.com/jira/plugins/servlet/desk/portal/1/create/9141).
2. Update your `.env` file with the new token.
3. Restart the MCP server to apply the changes.

If your PAT is expired, authentication and API calls will fail until you renew it.