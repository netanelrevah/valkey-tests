# ruff: noqa: ANN002, ANN201

import pytest

from tests.valkey_test_client import ValkeyTestClient

"""
set testmodule file normalize tests/modules/hash_stringref.so
"""

pytestmark = [pytest.mark.modules]


def test_module_hash_set(r: ValkeyTestClient) -> None:
    """
    test {Module hash set} {
        r del k
        set status [catch {r hash.set_stringref k f hello} errmsg]
        assert {$status == 1}
        r hset k f hello1
        assert_equal "0" [r hash.has_stringref k f]
        r hash.set_stringref k f hello1
        assert_equal "hello1" [r hget k f]
        assert_equal "1" [r hash.has_stringref k f]
    }
    """
    r.run("del", "k")
    status = catch("r hash.set_stringref k f hello", "errmsg")
    assert status == 1
    r.run("hset", "k", "f", "hello1")
    assert "0" == r.run("hash.has_stringref", "k", "f")
    r.run("hash.set_stringref", "k", "f", "hello1")
    assert "hello1" == r.run("hget", "k", "f")
    assert "1" == r.run("hash.has_stringref", "k", "f")


def test_unload_the_module_hash(r: ValkeyTestClient) -> None:
    """
    test "Unload the module - hash" {
        assert_equal {OK} [r module unload hash.stringref]
    }
    """
    assert "OK" == r.run("module", "unload", "hash.stringref")


# --- stubs for unimplemented TCL helpers ---


def catch(*args):
    raise NotImplementedError("catch")
