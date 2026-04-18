import pytest
from pgdrift.ownership import (
    load_ownership,
    set_owner,
    remove_owner,
    get_owner,
    list_owners,
)


@pytest.fixture
def owner_dir(tmp_path):
    return str(tmp_path)


def test_load_returns_empty_when_no_file(owner_dir):
    result = load_ownership(owner_dir)
    assert result == {}


def test_set_owner_persists(owner_dir):
    set_owner("public.users", "alice", owner_dir)
    result = load_ownership(owner_dir)
    assert result["public.users"] == "alice"


def test_set_owner_overwrites_existing(owner_dir):
    set_owner("public.users", "alice", owner_dir)
    set_owner("public.users", "bob", owner_dir)
    assert get_owner("public.users", owner_dir) == "bob"


def test_set_column_owner(owner_dir):
    set_owner("public.users.email", "security-team", owner_dir)
    assert get_owner("public.users.email", owner_dir) == "security-team"


def test_remove_existing_owner_returns_true(owner_dir):
    set_owner("public.orders", "team-a", owner_dir)
    result = remove_owner("public.orders", owner_dir)
    assert result is True
    assert get_owner("public.orders", owner_dir) is None


def test_remove_missing_owner_returns_false(owner_dir):
    result = remove_owner("public.nonexistent", owner_dir)
    assert result is False


def test_list_owners_returns_all(owner_dir):
    set_owner("public.users", "alice", owner_dir)
    set_owner("public.orders", "bob", owner_dir)
    owners = list_owners(owner_dir)
    assert len(owners) == 2
    assert owners["public.users"] == "alice"
    assert owners["public.orders"] == "bob"


def test_get_owner_returns_none_for_missing(owner_dir):
    assert get_owner("public.missing", owner_dir) is None
