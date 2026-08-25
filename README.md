# MLB TestPlan MCP

A local toolset that runs three MCP (Model Context Protocol) servers side-by-side:

| Server            | Port | Purpose                                   |
|-------------------|------|--------------------------------------------|
| MLB TestPlan       | 8080 | Main dashboard / test plan server (`server.py`) |
| Jira MCP           | 8000 | Jira integration (`jira-mcp/`)             |
| Confluence MCP     | 8001 | Confluence integration (`confluence-mcp/`) |

All three can be started with a single double-click via `start-all-mcp.bat`.

---

## 1. Clone the repo

```powershell
git clone https://github.com/porsche-code/mlb-testplan-mcp.git
cd mlb-testplan-mcp
```

> Keep the folder structure as-is — `start-all-mcp.bat` expects `jira-mcp/` and
> `confluence-mcp/` as subfolders next to it. It works from any location on disk,
> as long as the folder layout stays intact.

## 2. Add your `.env` files

Each service needs its own `.env` file with credentials (these are git-ignored and
never committed). Copy the provided examples and fill in your own values:

```powershell
copy jira-mcp\.env.example jira-mcp\.env
copy confluence-mcp\.env.example confluence-mcp\.env
```

At minimum you'll need to set, per service:

- **jira-mcp/.env** — your Jira Personal Access Token (PAT) and base URL.
- **confluence-mcp/.env** — your Confluence PAT (`CONFLUENCE_PAT`), base URL, and
  (if you're on the corporate network) the proxy settings:
  ```
  CONFLUENCE_PAT=your_token_here
  CONFLUENCE_BASE_URL=https://api.skyway.porsche.com/confluence
  HTTP_PROXY=http://http-proxy.porsche.org:3128
  HTTPS_PROXY=http://http-proxy.porsche.org:3133
  ```

If the required PAT is missing, the corresponding service will fail to start with a
clear error message telling you which variable is missing.

## 3. Start everything

Double-click **`start-all-mcp.bat`** in the repo root. It will:

1. Stop any previous instances of the 3 servers (frees ports 8080 / 8000 / 8001).
2. Create a Python virtual environment (`venv/`) for each service the first time
   it runs, and install dependencies from each `requirements.txt`.
   - On every run after the first, if `requirements.txt` hasn't changed, the
     install step is skipped — startup is fast.
3. Launch all three servers as tabs in a single Windows Terminal window (falls
   back to 3 separate console windows if Windows Terminal / `wt` isn't installed).

Once running:

- Dashboard: [http://localhost:8080](http://localhost:8080)
- Jira MCP docs: [http://localhost:8000/docs](http://localhost:8000/docs)
- Confluence MCP docs: [http://localhost:8001/docs](http://localhost:8001/docs)

To stop everything, close the terminal window/tabs (or press `Ctrl+C` in each tab).

### Create a desktop shortcut (optional, recommended)

So you don't have to navigate to the repo folder every time:

1. Right-click `start-all-mcp.bat` → **Show more options** → **Send to** →
   **Desktop (create shortcut)**.
2. (Optional) Right-click the new desktop shortcut → **Properties** → **Change Icon**
   to pick something recognizable.
3. Rename the shortcut to something like `Start MLB TestPlan MCP`.

Double-clicking that shortcut from now on runs the whole stack, no terminal typing
required.

## Requirements

- Windows with Python 3.11+ installed and available on PATH (`py`, `python`, or
  `python3` — the script auto-detects whichever is available).
- Network access to the Jira/Confluence Skyway APIs (directly, or via the
  corporate proxy configured in `.env` / `start-all-mcp.bat`).
- Windows Terminal (`wt`) is recommended but not required — the script falls back
  to separate console windows automatically if it's missing.

## Troubleshooting

- **"Python not found"** — install Python and make sure it's on your PATH, then
  re-run the bat file.
- **A service fails to start / crashes immediately** — check its own terminal tab
  for the exact error; usually a missing or invalid `.env` value.
- **Port already in use** — `start-all-mcp.bat` automatically kills whatever is
  listening on 8080/8000/8001 before starting fresh, so this is handled for you.
- **Dependencies re-installing every time** — shouldn't happen; if it does, check
  that `venv\.installed` and `venv\.requirements.snapshot` exist inside each
  service's `venv/` folder after a successful run.
