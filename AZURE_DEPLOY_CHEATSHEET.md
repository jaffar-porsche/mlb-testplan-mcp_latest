# Azure Deploy Cheat Sheet

This repo deploys three Azure Container Apps:

- `mlb-testplan`
- `jira-mcp`
- `confluence-mcp`

Use this workflow whenever you want Azure to reflect your latest GitHub changes.

## Core Rule

GitHub push alone does not update Azure.

Every deployment update is:

1. Change code locally
2. Commit and push to GitHub
3. Pull latest code in Azure Cloud Shell
4. Build a new image tag in ACR
5. Update the matching Container App to that new tag
6. Test the deployed URL

## Repo And Azure Values

- Git branch: `pre-final`
- ACR: `mjmlbtestplanacr2026`
- Resource group: `mlb-testplan-mj-rg`

## Main App Changes

Use this when you change files like:

- `server.py`
- `dashboard.html`
- root `Dockerfile`

### Local machine

```powershell
git add .
git commit -m "feat: describe main app change"
git push github pre-final
```

### Azure Cloud Shell

Replace `vNEXT` with the next tag, for example `v4`, `v5`, `v6`.

```bash
cd ~/mlb-testplan-mcp_latest
git pull
az acr build -r mjmlbtestplanacr2026 -t mlb-testplan:vNEXT -f Dockerfile .
az containerapp update \
  --name mlb-testplan \
  --resource-group mlb-testplan-mj-rg \
  --image mjmlbtestplanacr2026.azurecr.io/mlb-testplan:vNEXT
```

### Test

```text
https://mlb-testplan.purpleplant-c6aa08b1.germanywestcentral.azurecontainerapps.io/
https://mlb-testplan.purpleplant-c6aa08b1.germanywestcentral.azurecontainerapps.io/dashboard
```

## Jira MCP Changes

Use this when you change files under `jira-mcp/`.

### Local machine

```powershell
git add .
git commit -m "feat: describe jira change"
git push github pre-final
```

### Azure Cloud Shell

Replace `vNEXT` with the next tag, for example `v2`, `v3`, `v4`.

```bash
cd ~/mlb-testplan-mcp_latest
git pull
az acr build -r mjmlbtestplanacr2026 -t jira-mcp:vNEXT -f jira-mcp/Dockerfile .
az containerapp update \
  --name jira-mcp \
  --resource-group mlb-testplan-mj-rg \
  --image mjmlbtestplanacr2026.azurecr.io/jira-mcp:vNEXT
```

### Test

```text
https://jira-mcp.purpleplant-c6aa08b1.germanywestcentral.azurecontainerapps.io/docs
```

## Confluence MCP Changes

Use this when you change files under `confluence-mcp/`.

### Local machine

```powershell
git add .
git commit -m "feat: describe confluence change"
git push github pre-final
```

### Azure Cloud Shell

Replace `vNEXT` with the next tag, for example `v2`, `v3`, `v4`.

```bash
cd ~/mlb-testplan-mcp_latest
git pull
az acr build -r mjmlbtestplanacr2026 -t confluence-mcp:vNEXT -f confluence-mcp/Dockerfile .
az containerapp update \
  --name confluence-mcp \
  --resource-group mlb-testplan-mj-rg \
  --image mjmlbtestplanacr2026.azurecr.io/confluence-mcp:vNEXT
```

### Test

```text
https://confluence-mcp.purpleplant-c6aa08b1.germanywestcentral.azurecontainerapps.io/docs
```

## Versioning Rule

Never reuse an old tag.

Examples:

- `mlb-testplan:v3` -> `mlb-testplan:v4`
- `jira-mcp:v1` -> `jira-mcp:v2`
- `confluence-mcp:v1` -> `confluence-mcp:v2`

## Quick Checks

### Check current deployed image

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

## Fast Mental Model

1. Change code
2. Push GitHub
3. Pull in Cloud Shell
4. Build image
5. Update Container App
6. Test URL