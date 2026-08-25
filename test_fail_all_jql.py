"""
Unit tests for the get_fail_all combined-JQL builder.

These tests only exercise the pure JQL-string helper
(_build_fail_all_combined_jql) — no live jira-mcp/confluence-mcp services
required. They verify the per-Test-Plan "{KEY}- fail" testRunStatus
convention required by this Xray instance (a shared "FAIL" literal across
Test Plans does not match).
"""
from server import _build_fail_all_combined_jql


def test_combined_jql_single_test_plan():
    jql = _build_fail_all_combined_jql(["MLBEVO-17817"])
    assert jql == '(testPlanTests(MLBEVO-17817) AND testRunStatus = "MLBEVO-17817- fail")'


def test_combined_jql_two_test_plans():
    jql = _build_fail_all_combined_jql(["MLBEVO-17817", "MLBEVO-17820"])
    assert jql == (
        '(testPlanTests(MLBEVO-17817) AND testRunStatus = "MLBEVO-17817- fail") OR '
        '(testPlanTests(MLBEVO-17820) AND testRunStatus = "MLBEVO-17820- fail")'
    )


def test_combined_jql_all_testing_ece_working_groups():
    keys = ["MLBEVO-17821", "MLBEVO-17819", "MLBEVO-17818", "MLBEVO-17820", "MLBEVO-17817"]
    jql = _build_fail_all_combined_jql(keys)
    expected = " OR ".join(
        f'(testPlanTests({k}) AND testRunStatus = "{k}- fail")' for k in keys
    )
    assert jql == expected
    # Each Test Plan's clause must reference its OWN key in testRunStatus,
    # never a shared "FAIL" literal.
    for k in keys:
        assert f'testRunStatus = "{k}- fail"' in jql
    assert '"FAIL"' not in jql


def test_combined_jql_empty_list():
    assert _build_fail_all_combined_jql([]) == ""
