# Report Export Specification

## Purpose

Exports fail and blocked test reports as downloadable XLSX spreadsheets or PDF documents so users can share and archive analysis results outside the dashboard.

## Requirements

### Requirement: REQ-RE-001 XLSX Export Endpoints
The system SHALL expose `GET /export/fail/{issue_key}.xlsx` and `GET /export/blocked/{issue_key}.xlsx` endpoints in `server.py` that convert report results into a formatted XLSX workbook using `pandas.ExcelWriter` with the `xlsxwriter` engine, including a bold header row, autofilter, and frozen header pane.

#### Scenario: Fail results exist for the issue key
- **GIVEN** `xray_get_fail_report_historical(issue_key)` returns one or more results
- **WHEN** `GET /export/fail/{issue_key}.xlsx` is requested
- **THEN** the system SHALL build a DataFrame via `_results_to_dataframe` with columns test_key, summary, test_exec_key, run_id, status, kpm_id, comment, assignee_name, assignee_email, and children_keys
- **AND** the system SHALL stream the workbook back with `Content-Disposition: attachment; filename="{issue_key}_Fails.xlsx"`

#### Scenario: No results to export
- **GIVEN** the underlying fail or blocked report returns an empty results list for `issue_key`
- **WHEN** the corresponding export endpoint is requested
- **THEN** the system SHALL respond with HTTP 404 and detail "No FAIL results to export." or "No BLOCKED results to export." respectively

### Requirement: REQ-RE-002 PDF Export Endpoints
The system SHALL expose `GET /export/fail/{issue_key}.pdf` and `GET /export/blocked/{issue_key}.pdf` endpoints that render the report as HTML via `_build_html_report` and convert it to a PDF using a headless browser page's `.pdf(format='A4', print_background=True)` call.

#### Scenario: Rendering the PDF
- **GIVEN** report results are available for `issue_key`
- **WHEN** a PDF export endpoint is requested
- **THEN** the system SHALL generate an HTML table via `_build_html_report(title, df)` styled with a bordered table and shaded header row
- **AND** the system SHALL return the resulting PDF bytes as a `StreamingResponse` with media type `application/pdf` and a `Content-Disposition: attachment` filename of the form `{issue_key}_Fails.pdf` or `{issue_key}_Blocked.pdf`

### Requirement: REQ-RE-003 Data Normalization for Export
The system SHALL normalize report row data before export, flattening nested `assignee` objects into `assignee_name`/`assignee_email` fields and joining nested `children` records into a comma-separated `children_keys` string via `_results_to_dataframe`.

#### Scenario: Row contains nested assignee and children
- **GIVEN** a report result row with an `assignee` object and a `children` list of dicts
- **WHEN** `_results_to_dataframe` processes that row
- **THEN** the system SHALL extract `assignee_name` from `displayName` (falling back to `name`) and `assignee_email` from `emailAddress`
- **AND** the system SHALL join all child `key` values into `children_keys` separated by ", "
