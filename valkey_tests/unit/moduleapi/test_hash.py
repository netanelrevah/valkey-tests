# ruff: noqa: PLR2004, RUF043

import pytest

from tests.valkey_test_client import ValkeyTestClient

"""
set testmodule file normalize tests/modules/hash.so
"""

pytestmark = [pytest.mark.modules]


def test_module_hash_set(r: ValkeyTestClient) -> None:
    """
    test {Module hash set} {
        r set k mystring
        assert_error "WRONGTYPE*" {r hash.set k "" hello world}
        r del k
        # "" = count updates and deletes of existing fields only
        assert_equal 0 [r hash.set k "" squirrel yes]
        # "a" = COUNT_ALL = count inserted, modified and deleted fields
        assert_equal 2 [r hash.set k "a" banana no sushi whynot]
        # "n" = NX = only add fields not already existing in the hash
        # "x" = XX = only replace the value for existing fields
        assert_equal 0 [r hash.set k "n" squirrel hoho what nothing]
        assert_equal 1 [r hash.set k "na" squirrel hoho something nice]
        assert_equal 0 [r hash.set k "xa" new stuff not inserted]
        assert_equal 1 [r hash.set k "x" squirrel ofcourse]
        assert_equal 1 [r hash.set k "" sushi :delete: none :delete:]
        r hgetall k
    } {squirrel ofcourse banana no what nothing something nice}
    """
    r.run("set", "k", "mystring")
    with pytest.raises(Exception, match="WRONGTYPE.*"):
        r.run("hash.set", "k", "", "hello", "world")
    r.run("del", "k")
    assert 0 == r.run("hash.set", "k", "", "squirrel", "yes")
    assert 2 == r.run("hash.set", "k", "a", "banana", "no", "sushi", "whynot")
    assert 0 == r.run("hash.set", "k", "n", "squirrel", "hoho", "what", "nothing")
    assert 1 == r.run("hash.set", "k", "na", "squirrel", "hoho", "something", "nice")
    assert 0 == r.run("hash.set", "k", "xa", "new", "stuff", "not", "inserted")
    assert 1 == r.run("hash.set", "k", "x", "squirrel", "ofcourse")
    assert 1 == r.run("hash.set", "k", "", "sushi", ":delete:", "none", ":delete:")
    assert r.run("hgetall", "k") == "squirrel ofcourse banana no what nothing something nice"


def test_unload_the_module_hash(r: ValkeyTestClient) -> None:
    """
    test "Unload the module - hash" {
        assert_equal {OK} [r module unload hash]
    }
    """
    assert "OK" == r.run("module", "unload", "hash")
