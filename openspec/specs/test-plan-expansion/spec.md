# Test Plan Expansion Specification

## Purpose

Expands a single region or working group query into the full set of matching test plan keys across the other dimension, enabling users to discover and bulk-analyze test plans without knowing exact Jira keys in advance.

## Requirements

### Requirement: REQ-TP-001 Query Auto-Detection
The system SHALL accept a raw user phrase as the `query` input to `expand_testplans` and auto-detect whether it refers to a known region or a known working group, without requiring the caller to specify which dimension it is.

#### Scenario: Region phrase supplied
- **GIVEN** a query matching one of the known regions (Testing ECE, Testing NAR, Testing JPN, Testing KOR, Testing TWN, Testing Hong-Kong, Testing Macau)
- **WHEN** `expand_testplans` is called with that query
- **THEN** the system SHALL set `matched_as` to `"region"` in the response
- **AND** the system SHALL group results by working group

#### Scenario: Working group phrase supplied
- **GIVEN** a query matching one of the known working groups (Navigation, Digital assistant, Phone-Connectivity-SPI, Core HMI / GBK, Media / Tuner (Entertainment), App Store / 3rd Party, System Audio, Car, Sport Apps)
- **WHEN** `expand_testplans` is called with that query
- **THEN** the system SHALL set `matched_as` to `"working_group"` in the response
- **AND** the system SHALL group results by region

### Requirement: REQ-TP-002 Grouped Result Structure
The system SHALL return `expand_testplans` results containing `matched_as`, `label`, `total_found`, a `grouped` mapping, and a flat `all` list of `{test_plan_key, region, working_group}` records so downstream consumers can render either a grouped or flat view.

#### Scenario: Building the grouped and flat views
- **GIVEN** `expand_testplans` has resolved a matching region or working group
- **WHEN** the tool assembles its response
- **THEN** the system SHALL populate `grouped` as a mapping from the opposite dimension's labels to lists of test plan keys
- **AND** the system SHALL populate `all` with one entry per matched test plan including both `region` and `working_group`

### Requirement: REQ-TP-003 Scope Boundary with Fail/Blocked Analysis
The system SHALL only invoke `expand_testplans` when the user has NOT specified both a region and a working group simultaneously; when both dimensions are given, the system SHALL defer to the FailReport or BlockedReport workflow instead.

#### Scenario: Both dimensions specified
- **GIVEN** a user prompt specifying both a region and a working group (e.g. "navigation ECE")
- **WHEN** the routing agent evaluates the prompt
- **THEN** the system SHALL use the `parse_keywords` flow (FailReport/BlockedReport) instead of `expand_testplans`

#### Scenario: Single dimension specified
- **GIVEN** a user prompt specifying only a region or only a working group (e.g. "all navigation test plans")
- **WHEN** the routing agent evaluates the prompt
- **THEN** the system SHALL call `expand_testplans` with the user's raw phrase as `query`
