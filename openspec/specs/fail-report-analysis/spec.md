# Fail Report Analysis Specification

## Purpose

Generates a structured failure report for a given test plan by resolving the test plan key, fetching FAIL test runs from Xray, mapping them to run IDs, and extracting KPM defect identifiers from run comments so agents and users can quickly triage failures.

## Requirements

### Requirement: REQ-FR-001 Test Plan Key Resolution
The system SHALL resolve a `test_plan_key` from a user's raw prompt via the `parse_keywords` tool exposed in `server.py`, extracting `location` and `working_group` before proceeding with fail analysis.

#### Scenario: Test plan key present in prompt
- **GIVEN** a user prompt containing an explicit Jira test plan key (e.g. `MLBEVO-17821`)
- **WHEN** `parse_keywords` is called with the raw prompt
- **THEN** the system SHALL return the resolved `test_plan_key` directly

#### Scenario: Test plan key missing but region and working group present
- **GIVEN** `parse_keywords` returns a null `test_plan_key` along with a `location` and `working_group`
- **WHEN** the FailReport workflow proceeds
- **THEN** the system SHALL call `get_confluence_testplans` with `location` and `working_group` to resolve the key
- **AND** the system MUST NOT proceed to fetch failed tests until a `test_plan_key` is resolved

### Requirement: REQ-FR-002 FAIL Test Retrieval and Run Mapping
The system SHALL retrieve all tests with `latestStatus = FAIL` for the resolved `test_plan_key` via `get_failed_tests`, enumerate test executions via `get_test_plan_executions`, and map each failed test to its run ID and test execution key via `map_failed_runs`, which paginates the `xray/testruns` endpoint 100 runs per page.

#### Scenario: Failed tests exist
- **GIVEN** a `test_plan_key` with one or more FAIL tests
- **WHEN** `get_failed_tests` is called
- **THEN** the system SHALL return a `failed_keys` list of test issue keys with `latestStatus = FAIL`
- **AND** `map_failed_runs` SHALL paginate fully through all `xray/testruns` pages rather than stopping at page 1

#### Scenario: No failed tests
- **GIVEN** a `test_plan_key` with zero FAIL tests
- **WHEN** `get_failed_tests` returns an empty `failed_keys` list
- **THEN** the system SHALL report "No failing tests found" and stop the workflow without calling downstream mapping tools

### Requirement: REQ-FR-003 KPM Defect Extraction
The system SHALL extract KPM defect identifiers from each failed run's comment field via `analyze_failed_tests_with_kpms`, which fetches `xray/testrun/{run_id}` for every mapped run and searches the comment text for KPM patterns including `KPM: <id>`, `KPM Problem - <id>`, `kpmweb...id=<id>`, `KPM-<id>`, and standalone 8-digit numbers starting with `1`.

#### Scenario: Comment contains a recognizable KPM pattern
- **GIVEN** a run comment containing text matching one of the documented KPM patterns
- **WHEN** `analyze_failed_tests_with_kpms` processes that run
- **THEN** the system SHALL extract the KPM ID(s) into the run's `kpm_ids` field
- **AND** the system SHALL group the report summary by which KPM appears in which test keys

#### Scenario: Comment has no KPM pattern
- **GIVEN** a run comment with no matching KPM pattern
- **WHEN** `analyze_failed_tests_with_kpms` processes that run
- **THEN** the system SHALL report `kpm_ids` as empty for that run
- **AND** the system MUST NOT guess or fabricate a KPM identifier

### Requirement: REQ-FR-004 Errors Reported Separately
The system SHALL surface any per-run errors encountered while fetching `xray/testrun/{run_id}` data as a distinct `errors[]` collection rather than silently dropping affected rows.

#### Scenario: Run fetch fails for one test
- **GIVEN** `analyze_failed_tests_with_kpms` encounters an error retrieving one run's details
- **WHEN** the overall analysis completes
- **THEN** the system SHALL list that error separately from the successfully analyzed rows
- **AND** the report generation SHOULD continue processing the remaining runs
