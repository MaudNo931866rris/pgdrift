"""Tests for pgdrift.plugin registry."""

import pytest

from pgdrift import plugin


@pytest.fixture(autouse=True)
def _reset_registry():
    """Ensure the plugin registry is empty before and after every test."""
    plugin.clear()
    yield
    plugin.clear()


def _dummy_formatter():
    pass


def _dummy_linter():
    pass


def test_register_valid_hook_stores_callable():
    plugin.register("formatter", _dummy_formatter)
    assert _dummy_formatter in plugin.get_plugins("formatter")


def test_get_plugins_returns_empty_list_for_unknown_hook():
    result = plugin.get_plugins("formatter")
    assert result == []


def test_register_invalid_hook_raises_value_error():
    with pytest.raises(ValueError, match="Unknown hook"):
        plugin.register("nonexistent", _dummy_formatter)


def test_register_multiple_plugins_under_same_hook():
    plugin.register("linter", _dummy_formatter)
    plugin.register("linter", _dummy_linter)
    result = plugin.get_plugins("linter")
    assert len(result) == 2
    assert _dummy_formatter in result
    assert _dummy_linter in result


def test_clear_specific_hook_removes_only_that_hook():
    plugin.register("formatter", _dummy_formatter)
    plugin.register("linter", _dummy_linter)
    plugin.clear(hook="formatter")
    assert plugin.get_plugins("formatter") == []
    assert _dummy_linter in plugin.get_plugins("linter")


def test_clear_all_removes_everything():
    plugin.register("formatter", _dummy_formatter)
    plugin.register("linter", _dummy_linter)
    plugin.clear()
    assert plugin.list_hooks() == []


def test_list_hooks_returns_only_populated_hooks():
    plugin.register("formatter", _dummy_formatter)
    hooks = plugin.list_hooks()
    assert "formatter" in hooks
    assert "linter" not in hooks


def test_get_plugins_returns_copy():
    plugin.register("exporter", _dummy_formatter)
    first = plugin.get_plugins("exporter")
    first.append(_dummy_linter)
    second = plugin.get_plugins("exporter")
    assert _dummy_linter not in second
