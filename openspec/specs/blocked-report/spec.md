# Blocked Report Specification

## Purpose

Produces a blocked-test report for a given test plan, listing all tests with BLOCKED status and their associated run and comment details so users can see what is preventing test completion.

## Requirements

### Requirement: REQ-BR-001 Test Plan Key Resolution
The system SHALL resolve the `test_plan_key` for a blocked-report request using the same `parse_keywords` and `get_confluence_testplans` fallback flow used by FailReport, before invoking the blocked-report tool.

#### Scenario: Test plan key resolved directly
- **GIVEN** a user prompt containing an explicit test plan key
- **WHEN** `parse_keywords` is called
- **THEN** the system SHALL use the returned `test_plan_key` for the blocked report lookup

#### Scenario: Test plan key requires lookup
- **GIVEN** `parse_keywords` returns `location` and `working_group` but no `test_plan_key`
- **WHEN** the BlockedReport workflow proceeds
- **THEN** the system SHALL call `get_confluence_testplans` with `location` and `working_group` to resolve the key before calling `xray_get_blocked_report`

### Requirement: REQ-BR-002 Blocked Test Retrieval
The system SHALL fetch all tests with BLOCKED status for the resolved `test_plan_key` via the `xray_get_blocked_report` tool (exposed in `server.py`), returning `test_key`, `test_summary`, `test_exec_key`, `run_id`, `status`, and `comment` for each blocked test.

#### Scenario: Blocked tests exist
- **GIVEN** a `test_plan_key` with one or more tests in BLOCKED status
- **WHEN** `xray_get_blocked_report` is called with `issue_key = test_plan_key`
- **THEN** the system SHALL return a list of blocked-test records with all documented fields populated
- **AND** every returned record's `status` field SHALL be `BLOCKED`

#### Scenario: No blocked tests
- **GIVEN** a `test_plan_key` with zero BLOCKED tests
- **WHEN** `xray_get_blocked_report` returns an empty list
- **THEN** the system SHALL report "No blocked tests found" instead of rendering an empty table

### Requirement: REQ-BR-003 Report Presentation
The system SHOULD present blocked-report results as a markdown table with columns Test Key, Summary, Test Exec Key, Run ID, and Comment, followed by a total count summary.

#### Scenario: Rendering a populated report
- **GIVEN** a non-empty blocked-test list returned from `xray_get_blocked_report`
- **WHEN** the report is rendered for the user
- **THEN** the system SHOULD emit a markdown table of the blocked tests
- **AND** the system SHOULD append a `Total Blocked: N` summary line
