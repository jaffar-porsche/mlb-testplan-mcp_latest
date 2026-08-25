# Common Workflows

- `pip install -r requirements.txt` — Install root server dependencies
- `pip install -r jira-mcp/requirements.txt` — Install jira-mcp dependencies
- `pip install -r confluence-mcp/requirements.txt` — Install confluence-mcp dependencies
- `cd jira-mcp && pytest` — Run jira-mcp tests
- `cd confluence-mcp && pytest` — Run confluence-mcp tests
- `uvicorn server:app --host 0.0.0.0 --port 8080` — Run root MCP server
- `uvicorn mcp_server:app --host 0.0.0.0 --port 8000 --reload` — Run jira-mcp proxy server
- `uvicorn mcp_server:app --host 0.0.0.0 --port 8001 --reload` — Run confluence-mcp proxy server
- `docker-compose up -d` — Build and run all services with Docker Compose
- `playwright install chromium` — Install Playwright browser for PDF export
- `python server.py` — Start mlb-testplan MCP server
- `docker-compose up -d` — Start jira-mcp server via Docker Compose
- `./start-mcp.sh` — Start jira-mcp server locally (Linux/Mac)
- `bash test_mcp_client.sh` — Run jira-mcp bash test client
- `docker-compose up -d` — Start confluence-mcp server via Docker Compose
- `./start-mcp.sh` — Start confluence-mcp server locally
- `python test_client.py` — Run confluence-mcp interactive Python test client
- `python simple_test.py` — Run confluence-mcp automated simple test
