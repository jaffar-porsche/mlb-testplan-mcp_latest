"""Tests for utility modules."""
import pytest
from unittest.mock import MagicMock


def test_sprint_utils_imports():
    """Test sprint utility module can be imported."""
    from utils.sprint import extract_sprint_info

    assert callable(extract_sprint_info)


def test_hierarchy_utils_imports():
    """Test hierarchy utility module can be imported."""
    from utils.hierarchy import (
        HierarchyStats,
        build_hierarchy_markdown,
        get_child_issues,
        is_closed_status,
    )

    assert callable(build_hierarchy_markdown)
    assert callable(get_child_issues)
    assert callable(is_closed_status)


def test_hierarchy_stats():
    """Test HierarchyStats tracking."""
    from utils.hierarchy import HierarchyStats

    stats = HierarchyStats()
    assert stats.total == 0
    assert stats.done == 0

    # Add some issues
    stats.add("Story", "In Progress")
    assert stats.total == 1
    assert stats.done == 0

    stats.add("Task", "Done")
    assert stats.total == 2
    assert stats.done == 1


def test_is_closed_status():
    """Test closed status detection."""
    from utils.hierarchy import is_closed_status

    assert is_closed_status("Done") is True
    assert is_closed_status("Closed") is True
    assert is_closed_status("done") is True
    assert is_closed_status("In Progress") is False
    assert is_closed_status("Open") is False


def test_extract_sprint_info_no_sprint():
    """Test sprint extraction returns None when no sprint fields present."""
    from utils.sprint import extract_sprint_info
    import config

    config.SPRINT_FIELD_ID = None

    mock_issue = MagicMock()
    mock_issue.fields = MagicMock()

    # Make all fallback field lookups return None
    for fid in config._SPRINT_FIELD_FALLBACKS:
        setattr(mock_issue.fields, fid, None)

    result = extract_sprint_info(mock_issue)
    assert result is None


def test_extract_sprint_info_object_format():
    """Test sprint extraction with newer Jira object format (list of sprint objects)."""
    from utils.sprint import extract_sprint_info
    import config

    config.SPRINT_FIELD_ID = "customfield_10004"

    sprint_obj = MagicMock()
    sprint_obj.id = 226994
    sprint_obj.name = "PI-26.1 - S1 - PCDSXWS"
    sprint_obj.state = "ACTIVE"
    sprint_obj.startDate = "2026-03-10"
    sprint_obj.endDate = "2026-03-24"
    sprint_obj.goal = "Deliver HVB fix"

    mock_issue = MagicMock()
    mock_issue.fields = MagicMock()
    mock_issue.fields.customfield_10004 = [sprint_obj]

    result = extract_sprint_info(mock_issue)
    assert result is not None
    assert result["id"] == 226994
    assert result["name"] == "PI-26.1 - S1 - PCDSXWS"
    assert result["state"] == "ACTIVE"
    assert result["startDate"] == "2026-03-10"
    assert result["endDate"] == "2026-03-24"
    assert result["goal"] == "Deliver HVB fix"


def test_extract_sprint_info_string_format():
    """Test sprint extraction with older Jira Data Center string format."""
    from utils.sprint import extract_sprint_info
    import config

    config.SPRINT_FIELD_ID = "customfield_10004"

    mock_issue = MagicMock()
    mock_issue.fields = MagicMock()
    mock_issue.fields.customfield_10004 = (
        "com.atlassian.greenhopper.service.sprint.Sprint@1a2b3c"
        "[id=226994,rapidViewId=108739,state=ACTIVE,"
        "name=PI-26.1 - S1 - PCDSXWS,startDate=<null>,endDate=<null>,"
        "completeDate=<null>,activatedDate=2026-03-10T08:00:00.000+01:00,"
        "sequence=226994,goal=,autoStartStop=false]"
    )

    result = extract_sprint_info(mock_issue)
    assert result is not None
    assert result["id"] == "226994"
    assert result["name"] == "PI-26.1 - S1 - PCDSXWS"
    assert result["state"] == "ACTIVE"


def test_extract_sprint_info_list_of_strings_format():
    """Test sprint extraction with Jira DC list-of-strings format."""
    from utils.sprint import extract_sprint_info
    import config

    config.SPRINT_FIELD_ID = "customfield_10004"

    closed_sprint = (
        "com.atlassian.greenhopper.service.sprint.Sprint@aaa"
        "[id=200000,rapidViewId=108739,state=CLOSED,"
        "name=PI-25.4 - S4 - PCDSXWS,startDate=<null>,endDate=<null>]"
    )
    active_sprint = (
        "com.atlassian.greenhopper.service.sprint.Sprint@bbb"
        "[id=226994,rapidViewId=108739,state=ACTIVE,"
        "name=PI-26.1 - S1 - PCDSXWS,startDate=<null>,endDate=<null>]"
    )

    mock_issue = MagicMock()
    mock_issue.fields = MagicMock()
    mock_issue.fields.customfield_10004 = [closed_sprint, active_sprint]

    result = extract_sprint_info(mock_issue)
    assert result is not None
    # Should pick the last (most recent) sprint
    assert result["id"] == "226994"
    assert result["name"] == "PI-26.1 - S1 - PCDSXWS"
    assert result["state"] == "ACTIVE"


def test_extract_sprint_info_uses_discovered_field_first():
    """Test that discovered SPRINT_FIELD_ID takes precedence over fallbacks."""
    from utils.sprint import extract_sprint_info
    import config

    config.SPRINT_FIELD_ID = "customfield_10004"

    sprint_obj = MagicMock()
    sprint_obj.id = 111
    sprint_obj.name = "Discovered Sprint"
    sprint_obj.state = "ACTIVE"
    sprint_obj.startDate = None
    sprint_obj.endDate = None
    sprint_obj.goal = None

    fallback_obj = MagicMock()
    fallback_obj.id = 999
    fallback_obj.name = "Fallback Sprint"
    fallback_obj.state = "FUTURE"
    fallback_obj.startDate = None
    fallback_obj.endDate = None
    fallback_obj.goal = None

    mock_issue = MagicMock()
    mock_issue.fields = MagicMock()
    mock_issue.fields.customfield_10004 = [sprint_obj]
    mock_issue.fields.customfield_10020 = [fallback_obj]

    result = extract_sprint_info(mock_issue)
    assert result["id"] == 111
    assert result["name"] == "Discovered Sprint"


def test_discover_sprint_field():
    """Test dynamic sprint field discovery from Jira fields metadata."""
    from utils.sprint import discover_sprint_field
    import config

    config.SPRINT_FIELD_ID = None  # reset

    mock_jira = MagicMock()
    mock_jira.fields.return_value = [
        {"id": "customfield_10001", "name": "Story Points", "schema": {"custom": "com.atlassian.jira.plugin.system.customfieldtypes:float"}},
        {"id": "customfield_10004", "name": "Sprint", "schema": {"custom": "com.pyxis.greenhopper.jira:gh-sprint"}},
        {"id": "customfield_10010", "name": "Epic Link", "schema": {"custom": "com.pyxis.greenhopper.jira:gh-epic-link"}},
    ]

    result = discover_sprint_field(mock_jira)
    assert result == "customfield_10004"
    assert config.SPRINT_FIELD_ID == "customfield_10004"


def test_discover_sprint_field_caches():
    """Test that discovery result is cached and not re-queried."""
    from utils.sprint import discover_sprint_field
    import config

    config.SPRINT_FIELD_ID = "customfield_99999"

    mock_jira = MagicMock()
    result = discover_sprint_field(mock_jira)

    assert result == "customfield_99999"
    mock_jira.fields.assert_not_called()


def test_discover_sprint_field_not_found():
    """Test discovery returns None when no sprint field exists."""
    from utils.sprint import discover_sprint_field
    import config

    config.SPRINT_FIELD_ID = None

    mock_jira = MagicMock()
    mock_jira.fields.return_value = [
        {"id": "customfield_10001", "name": "Story Points", "schema": {"custom": "com.atlassian.jira.plugin.system.customfieldtypes:float"}},
    ]

    result = discover_sprint_field(mock_jira)
    assert result is None


# --- Agile Hive utility tests ---


def test_agile_hive_imports():
    """Test agile_hive utility module can be imported."""
    from utils.agile_hive import (
        discover_agile_hive_fields,
        extract_agile_hive_fields,
        build_team_name_cache,
        resolve_team_name_via_api,
        reset_cache,
    )

    assert callable(discover_agile_hive_fields)
    assert callable(extract_agile_hive_fields)
    assert callable(build_team_name_cache)
    assert callable(resolve_team_name_via_api)
    assert callable(reset_cache)


def test_parse_team_value_with_dict():
    """Test _parse_team_value with a dict input."""
    from utils.agile_hive import _parse_team_value

    result = _parse_team_value({"id": "123", "name": "DSW - Test Team"})
    assert result == {"id": "123", "name": "DSW - Test Team"}


def test_parse_team_value_with_object():
    """Test _parse_team_value with an object that has .name attribute."""
    from utils.agile_hive import _parse_team_value

    obj = MagicMock()
    obj.id = 456
    obj.name = "DSW - Mock Team"

    result = _parse_team_value(obj)
    assert result["id"] == "456"
    assert result["name"] == "DSW - Mock Team"


def test_parse_team_value_with_primitive():
    """Test _parse_team_value with a bare numeric ID (Teams Involved case)."""
    from utils.agile_hive import _parse_team_value

    result = _parse_team_value(32306)
    assert result == {"id": "32306", "name": None}


def test_parse_team_value_with_none():
    """Test _parse_team_value returns None for None input."""
    from utils.agile_hive import _parse_team_value

    assert _parse_team_value(None) is None


def test_team_name_cache_register_and_lookup():
    """Test team name cache registration and lookup."""
    from utils.agile_hive import _register_team_name, _lookup_team_name

    _register_team_name("99999", "Test Team")
    assert _lookup_team_name("99999") == "Test Team"

    # None name should not be cached
    _register_team_name("88888", None)
    assert _lookup_team_name("88888") is None


def test_reset_cache():
    """Test that reset_cache clears the field discovery cache."""
    from utils.agile_hive import reset_cache, _field_cache
    import utils.agile_hive as ah

    ah._field_cache = {"team": "customfield_123"}
    assert ah._field_cache is not None

    reset_cache()
    assert ah._field_cache is None


def test_extract_agile_hive_fields_empty():
    """Test extract_agile_hive_fields with no Agile Hive fields."""
    from utils.agile_hive import extract_agile_hive_fields

    mock_issue = MagicMock()
    mock_issue.fields = MagicMock(spec=[])

    result = extract_agile_hive_fields(mock_issue, {})
    assert result == {}


def test_extract_agile_hive_fields_with_team():
    """Test extract_agile_hive_fields extracts team correctly."""
    from utils.agile_hive import extract_agile_hive_fields

    mock_issue = MagicMock()
    mock_issue.fields.customfield_10201 = {"id": "18947", "name": "DSW - Diagnostics"}

    field_ids = {"team": "customfield_10201", "teams_involved": None, "cost_of_delay": None}
    result = extract_agile_hive_fields(mock_issue, field_ids)

    assert result["team"]["id"] == "18947"
    assert result["team"]["name"] == "DSW - Diagnostics"


def test_extract_agile_hive_fields_with_teams_involved_list():
    """Test extract_agile_hive_fields handles Teams Involved as a list of bare IDs."""
    from utils.agile_hive import extract_agile_hive_fields, _register_team_name

    # Pre-populate cache so names can be enriched
    _register_team_name("32306", "DSW - Coding Cult")

    mock_issue = MagicMock()
    mock_issue.fields.customfield_17319 = [32306, 32403]

    field_ids = {"team": None, "teams_involved": "customfield_17319", "cost_of_delay": None}
    result = extract_agile_hive_fields(mock_issue, field_ids)

    assert len(result["teams_involved"]) == 2
    assert result["teams_involved"][0]["id"] == "32306"
    assert result["teams_involved"][0]["name"] == "DSW - Coding Cult"
    # 32403 may or may not have a cached name
    assert result["teams_involved"][1]["id"] == "32403"
