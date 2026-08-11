---
description: Routes MLB-Testplan requests to the correct specialist agent
applyTo: "**"
---

# MLB-Testplan Agent Index

All operations use **only** the `mlb-testplan` MCP tools.
Never use Jira MCP, Confluence MCP, or GitLab MCP for these workflows.

---

## Agent Routing — which agent to call

| What the user wants | Agent to use |
|---|---|
| Fail report for a specific test plan (region + WG) | **FailReport** |
| Blocked report for a specific test plan | **BlockedReport** |
| All test plans for an entire region (e.g. all of Testing ECE) | **ExpandTestPlans** |
| All test plans for an entire working group (e.g. all Navigation) | **ExpandTestPlans** |
| Fail report across a JQL query / multiple executions | **JqlFailReport** |
| Just find the test plan key for a region + WG | **TestPlanLookup** |

---

## Quick Reference

### FailReport
```
"show fail report for navigation ECE"
"which tests are failing in core HMI NAR"
"get KPMs for media tuner testing JPN"
```
→ Resolves key → gets FAILs → maps run IDs → extracts KPMs → markdown table

### BlockedReport
```
"show blocked report for navigation ECE"
"which tests are blocked in testing NAR"
```
→ Resolves key → fetches blocked list → markdown table

### ExpandTestPlans
```
"fetch all of testing ECE"              ← region only
"show all regions for navigation"       ← working group only
"all test plans for digital assistant"
```
→ Returns grouped test plan keys. User then picks one to run FailReport/BlockedReport on.

### JqlFailReport
```
"fail report for JQL: issuetype = 'Test Execution' AND project = MLBEVO"
"scan all ECE test executions in PI-26.2"
```
→ Scans up to 1000 executions from JQL → FAILs + KPMs → markdown table

### TestPlanLookup
```
"what is the test plan key for navigation ECE"
"find the MLBEVO key for digital assistant NAR"
```
→ Resolves and returns just the key

---

## Known Regions
| Alias | Full Name |
|---|---|
| ECE, europe | Testing ECE |
| NAR, north america | Testing NAR |
| JPN, japan | Testing JPN |
| KOR, korea | Testing KOR |
| TWN, taiwan | Testing TWN |
| HK, hong kong | Testing Hong-Kong |
| macau | Testing Macau |

## Known Working Groups
Navigation, Digital assistant, Phone-Connectivity-SPI, Core HMI / GBK,
Media / Tuner (Entertainment), App Store / 3rd Party, System Audio, Car, Sport Apps

---

## MCP Server
- URL: `http://localhost:8080`
- Start: `python server.py` in the `mlb-testplan-mcp` folder
- Docs: `http://localhost:8080/docs`
- Dashboard: `http://localhost:8080/dashboard`
