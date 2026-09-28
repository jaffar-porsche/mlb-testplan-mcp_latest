# MLB TestPlan MCP

MLB TestPlan MCP is a local and Azure-hosted toolset for analyzing Jira Xray test plans, Confluence-based test-plan pages, FAIL and BLOCKED execution results, KPM mappings, and related test-report workflows.

The repository contains three cooperating services:

| Service | Port | Purpose |
|---|---:|---|
| `mlb-testplan` | `8080` | Main dashboard and API in [server.py](server.py) |
| `jira-mcp` | `8000` | Jira and Xray proxy service in [jira-mcp](jira-mcp) |
| `confluence-mcp` | `8001` | Confluence proxy service in [confluence-mcp](confluence-mcp) |

The main user entry point is the dashboard served by the root app. The helper services provide the Jira, Xray, and Confluence data that the dashboard depends on.

## What This Project Does

This project is used to:

1. Parse Confluence test-plan pages and resolve test plans by region and working group.
2. Analyze Xray FAIL and BLOCKED test runs across individual plans and aggregated views.
3. Extract KPM IDs and comments from test-run details.
4. Export report data to Excel.
5. Provide a local dashboard for interactive analysis.
6. Run locally on a Windows workstation and in Azure Container Apps.

## Repository Layout

| Path | Purpose |
|---|---|
| [server.py](server.py) | Main FastAPI dashboard/API service |
| [dashboard.html](dashboard.html) | Frontend dashboard UI |
| [start-all-mcp.bat](start-all-mcp.bat) | Starts all three local services |
| [jira-mcp](jira-mcp) | Jira and Xray proxy service |
| [confluence-mcp](confluence-mcp) | Confluence proxy service |
| [Dockerfile](Dockerfile) | Root app container image build |
| [docker-compose.yml](docker-compose.yml) | Local multi-service container layout |
| [AZURE_DEPLOY_CHEATSHEET.md](AZURE_DEPLOY_CHEATSHEET.md) | Short deployment reference |

## Prerequisites

For local development on Windows:

1. Python 3.11 or newer available on `PATH`.
2. Network access to Jira, Confluence, and Xray endpoints.
3. Valid Jira and Confluence Personal Access Tokens.
4. Windows Terminal is recommended, but not required.

## Local Setup

### 1. Clone the repository

```powershell
git clone https://github.com/porsche-code/mlb-testplan-mcp.git
cd mlb-testplan-mcp
```

If you are using the maintained GitHub mirror instead of the original remote, clone the mirror you normally work with.

### 2. Add your environment files

This project expects local `.env` files for the dependent services. These files are not committed.

Create them from the provided examples where available, then fill in your own PAT values.

Typical setup:

```powershell
copy jira-mcp\.env.example jira-mcp\.env
copy confluence-mcp\.env.example confluence-mcp\.env
```

If your local root service also uses a repo-root `.env`, keep that file alongside [server.py](server.py).

### 3. Add your PAT values

At minimum, configure the PATs in the service `.env` files:

`jira-mcp/.env`

```text
JIRA_PAT=your_jira_pat_here
JIRA_BASE_URL=https://api.skyway.porsche.com/jira
HTTP_PROXY=http://http-proxy.porsche.org:3128
HTTPS_PROXY=http://http-proxy.porsche.org:3133
```

`confluence-mcp/.env`

```text
CONFLUENCE_PAT=your_confluence_pat_here
CONFLUENCE_BASE_URL=https://api.skyway.porsche.com/confluence
HTTP_PROXY=http://http-proxy.porsche.org:3128
HTTPS_PROXY=http://http-proxy.porsche.org:3133
```

Notes:

1. Use your own PAT values. Do not commit them.
2. If a required PAT is missing, the corresponding service will fail at startup.
3. The dashboard `Update PAT` action updates local configuration only. Azure-hosted services must be updated separately in Azure.

## Run Locally

### Recommended startup flow

The easiest local workflow is:

1. Add your `.env` files.
2. Insert your Jira and Confluence PAT values.
3. Double-click [start-all-mcp.bat](start-all-mcp.bat).
4. Wait for all three local services to start.
5. Open the dashboard.

### Start all services

Double-click [start-all-mcp.bat](start-all-mcp.bat).

What the script does:

1. Stops older processes that are still using ports `8080`, `8000`, or `8001`.
2. Creates virtual environments if needed.
3. Installs or refreshes Python dependencies if needed.
4. Starts the root app, Jira MCP, and Confluence MCP together.

### Local URLs

After startup, use these URLs:

| URL | Purpose |
|---|---|
| `http://localhost:8080/` | Root service |
| `http://localhost:8080/dashboard` | Main dashboard |
| `http://localhost:8000/docs` | Jira MCP API playground |
| `http://localhost:8001/docs` | Confluence MCP API playground |

If you specifically want to open the dashboard UI file path in the browser, use the served dashboard route instead of opening [dashboard.html](dashboard.html) directly from disk. The UI expects the backend APIs to be available on `localhost`.

## How To Use Locally

Typical local usage:

1. Start all services with [start-all-mcp.bat](start-all-mcp.bat).
2. Open `http://localhost:8080/dashboard`.
3. Select or enter the Confluence page ID you want to analyze.
4. Use FAIL Overview, FAIL All, BLOCKED All, or related dashboard actions.
5. Export results when needed.

## Troubleshooting Local Startup

1. If Python is not found, install Python and ensure it is on `PATH`.
2. If one service crashes immediately, inspect that service terminal window first. The most common cause is a missing or invalid PAT in a `.env` file.
3. If data does not load, verify that all three services are running and reachable on `8080`, `8000`, and `8001`.
4. If the dashboard loads but features fail, verify the Jira and Confluence MCP services at their `/docs` endpoints.

## Azure Deployment Overview

This repository is also deployed to Azure Container Apps.

Deployed apps:

1. `mlb-testplan`
2. `jira-mcp`
3. `confluence-mcp`

Azure details used in this repository:

| Item | Value |
|---|---|
| Branch | `pre-final` |
| Resource Group | `mlb-testplan-mj-rg` |
| Azure Container Registry | `mjmlbtestplanacr2026` |

Important rule:

Git push alone does not update Azure. You must build a new image and update the matching Container App.

## Azure Container App URLs

| App | URL |
|---|---|
| Root dashboard app | `https://mlb-testplan.purpleplant-c6aa08b1.germanywestcentral.azurecontainerapps.io/` |
| Root dashboard UI | `https://mlb-testplan.purpleplant-c6aa08b1.germanywestcentral.azurecontainerapps.io/dashboard` |
| Jira MCP docs playground | `https://jira-mcp.purpleplant-c6aa08b1.germanywestcentral.azurecontainerapps.io/docs` |
| Confluence MCP docs playground | `https://confluence-mcp.purpleplant-c6aa08b1.germanywestcentral.azurecontainerapps.io/docs` |

Use the `/docs` endpoints as the API playgrounds for the Jira MCP and Confluence MCP services.

## Azure Cloud Shell Workflow

### Pull the latest code

```bash
cd ~/mlb-testplan-mcp_latest
git fetch origin
git checkout pre-final
git pull origin pre-final
```

### Verify the current Cloud Shell commit

```bash
git rev-parse HEAD
```

## Deploy Root App Changes To Azure

Use this when you change root-level files such as [server.py](server.py), [dashboard.html](dashboard.html), or the root [Dockerfile](Dockerfile).

Replace `vNEXT` with a new image tag such as `v4`, `v5`, or `v6`.

```bash
cd ~/mlb-testplan-mcp_latest
git pull origin pre-final
az acr build -r mjmlbtestplanacr2026 -t mlb-testplan:vNEXT -f Dockerfile .
az containerapp update \
  --name mlb-testplan \
  --resource-group mlb-testplan-mj-rg \
  --image mjmlbtestplanacr2026.azurecr.io/mlb-testplan:vNEXT
```

## Deploy Jira MCP Changes To Azure

Use this when you change files under [jira-mcp](jira-mcp).

```bash
cd ~/mlb-testplan-mcp_latest
git pull origin pre-final
az acr build -r mjmlbtestplanacr2026 -t jira-mcp:vNEXT -f jira-mcp/Dockerfile .
az containerapp update \
  --name jira-mcp \
  --resource-group mlb-testplan-mj-rg \
  --image mjmlbtestplanacr2026.azurecr.io/jira-mcp:vNEXT
```

## Deploy Confluence MCP Changes To Azure

Use this when you change files under [confluence-mcp](confluence-mcp).

```bash
cd ~/mlb-testplan-mcp_latest
git pull origin pre-final
az acr build -r mjmlbtestplanacr2026 -t confluence-mcp:vNEXT -f confluence-mcp/Dockerfile .
az containerapp update \
  --name confluence-mcp \
  --resource-group mlb-testplan-mj-rg \
  --image mjmlbtestplanacr2026.azurecr.io/confluence-mcp:vNEXT
```

## Azure Verification Commands

### Check the deployed image

```bash
az containerapp show \
  --name mlb-testplan \
  --resource-group mlb-testplan-mj-rg \
  --query "properties.template.containers[].image" \
  -o tsv
```

### List revisions

```bash
az containerapp revision list \
  --name mlb-testplan \
  --resource-group mlb-testplan-mj-rg \
  --query "[].{name:name,active:properties.active,createdTime:properties.createdTime,healthState:properties.healthState}" \
  -o table
```

### Check the traffic target

```bash
az containerapp show \
  --name mlb-testplan \
  --resource-group mlb-testplan-mj-rg \
  --query "properties.configuration.ingress.traffic" \
  -o json
```

### Check whether the deployed dashboard contains a UI change

Example: verify that the `Update PAT` button exists in the served dashboard.

```bash
curl -s https://mlb-testplan.purpleplant-c6aa08b1.germanywestcentral.azurecontainerapps.io/dashboard | grep -n "Update PAT"
```

## Azure Notes

1. Always use a new image tag. Do not reuse old tags.
2. If Azure still looks old after deployment, check the active revision and the currently deployed image tag.
3. If the deployed HTML contains the new feature but the browser does not show it, the problem is usually browser cache.
4. The root dashboard app depends on the Jira MCP and Confluence MCP services. If one helper service is stale or unhealthy, dashboard features may partially fail.

## Related Documentation

For a shorter Azure-only reference, see [AZURE_DEPLOY_CHEATSHEET.md](AZURE_DEPLOY_CHEATSHEET.md).
