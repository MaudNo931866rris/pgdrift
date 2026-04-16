"""Tests for pgdrift.policy."""
import pytest
from pathlib import Path
from pgdrift.policy import (
    PolicyRule, save_policy, load_policy, list_policies,
    delete_policy, evaluate_policy, PolicyViolation,
)
from pgdrift.diff import DriftReport, TableDiff


@pytest.fixture()
def policy_dir(tmp_path):
    return tmp_path / "policies"


def _empty_report():
    return DriftReport(source="src", target="tgt", added_tables=[], removed_tables=[], modified_tables=[])


def _drift_report(added=0, removed=0, modified=0):
    def _td(name):
        return TableDiff(table=name, added_columns=[], removed_columns=[], modified_columns=[])
    return DriftReport(
        source="src", target="tgt",
        added_tables=[_td(f"a{i}") for i in range(added)],
        removed_tables=[_td(f"r{i}") for i in range(removed)],
        modified_tables=[_td(f"m{i}") for i in range(modified)],
    )


def test_save_creates_file(policy_dir):
    rule = PolicyRule(name="strict")
    save_policy(rule, policy_dir)
    assert (policy_dir / "strict.json").exists()


def test_roundtrip(policy_dir):
    rule = PolicyRule(name="p1", max_added_tables=2, max_removed_tables=0, allow_destructive=False)
    save_policy(rule, policy_dir)
    loaded = load_policy("p1", policy_dir)
    assert loaded.max_added_tables == 2
    assert loaded.allow_destructive is False


def test_load_returns_none_for_missing(policy_dir):
    assert load_policy("nope", policy_dir) is None


def test_list_returns_names(policy_dir):
    save_policy(PolicyRule(name="a"), policy_dir)
    save_policy(PolicyRule(name="b"), policy_dir)
    assert list_policies(policy_dir) == ["a", "b"]


def test_delete_removes_file(policy_dir):
    save_policy(PolicyRule(name="x"), policy_dir)
    assert delete_policy("x", policy_dir) is True
    assert load_policy("x", policy_dir) is None


def test_delete_missing_returns_false(policy_dir):
    assert delete_policy("missing", policy_dir) is False


def test_evaluate_passes_empty_report():
    rule = PolicyRule(name="r", max_added_tables=5)
    result = evaluate_policy(rule, _empty_report())
    assert result.passed


def test_evaluate_fails_on_too_many_added():
    rule = PolicyRule(name="r", max_added_tables=1)
    result = evaluate_policy(rule, _drift_report(added=3))
    assert not result.passed
    assert any("Added" in v.message for v in result.violations)


def test_evaluate_fails_on_removed_when_no_destructive():
    rule = PolicyRule(name="r", allow_destructive=False)
    result = evaluate_policy(rule, _drift_report(removed=1))
    assert not result.passed


def test_evaluate_multiple_violations():
    rule = PolicyRule(name="r", max_added_tables=0, max_removed_tables=0)
    result = evaluate_policy(rule, _drift_report(added=1, removed=1))
    assert len(result.violations) == 2
