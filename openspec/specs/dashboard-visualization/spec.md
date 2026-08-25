# Dashboard Visualization Specification

## Purpose

Provides a browser-based, Porsche-branded interactive dashboard (`dashboard.html`) that lets users query, view, and act on test plan fail/blocked analysis results without calling the MCP API directly.

## Requirements

### Requirement: REQ-DV-001 Dashboard Data Fetching
The dashboard SHALL fetch test plan analysis data from the `mlb-testplan` server's REST endpoints (e.g. `${BASE}/testplans/expand`, `${BASE}/testplan/{key}/failed-tests`, `${BASE}/xray/blocked-report/{key}`) via client-side `fetch()` calls, using a stored test plan key to drive subsequent requests.

#### Scenario: Loading failed-test stats for a stored test plan
- **GIVEN** a `storedTestPlanKey` has been set in the dashboard session
- **WHEN** the dashboard loads or refreshes fail statistics
- **THEN** the system SHALL call `fetch(`${BASE}/testplan/${storedTestPlanKey}/failed-tests`)`
- **AND** the system SHALL render the resulting counts/tables using the fetched JSON payload

#### Scenario: Expanding a region or working group query from the dashboard
- **GIVEN** a user enters a free-text prompt into the dashboard's expand search box
- **WHEN** the dashboard submits the query
- **THEN** the system SHALL call `fetch(`${BASE}/testplans/expand?query=${encodeURIComponent(prompt)}`)`
- **AND** the system SHALL display the grouped results returned by the endpoint

### Requirement: REQ-DV-002 Report Export Triggers
The dashboard SHALL provide UI actions that trigger the report export endpoints for the currently selected test plan, linking to `${BASE}/export/fail/{key}.xlsx`, `${BASE}/export/fail/{key}.pdf`, `${BASE}/export/blocked/{key}.xlsx`, and `${BASE}/export/blocked/{key}.pdf`.

#### Scenario: User requests a fail XLSX download
- **GIVEN** a `storedTestPlanKey` is set and fail results are displayed
- **WHEN** the user clicks the "Export Fail XLSX" action
- **THEN** the system SHALL navigate to or fetch `${BASE}/export/fail/${storedTestPlanKey}.xlsx`
- **AND** the browser SHALL download the returned attachment using the filename set in its `Content-Disposition` header

### Requirement: REQ-DV-003 Porsche-Branded Styling
The dashboard SHALL render using Porsche Design System v3 tokens defined in `dashboard.html` (e.g. `--pds-color-brand: #d5001c`, `--pds-color-primary: #010205`) and the `911Porscha`/`Porsche Next` font faces, so the UI matches Porsche's visual identity.

#### Scenario: Applying brand color tokens
- **GIVEN** `dashboard.html` is loaded in a browser
- **WHEN** the page renders its header, tables, and action buttons
- **THEN** the system SHOULD apply the CSS custom properties defined under `:root` (colors, border radius, shadows) consistently across components
- **AND** the system SHOULD load the `911Porscha.ttf` font file for branded headings
