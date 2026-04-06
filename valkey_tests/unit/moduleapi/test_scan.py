# ruff: noqa: ANN002, ANN201

import pytest

from tests.valkey_test_client import ValkeyTestClient

"""
set testmodule file normalize tests/modules/scan.so
"""

pytestmark = [pytest.mark.modules]


"""
r module load testmodule
"""


@pytest.mark.xfail(reason="not implemented")
def test_module_scan_keyspace(r: ValkeyTestClient) -> None:
    """
    test {Module scan keyspace} {
        # the module create a scan command with filtering which also return values
        r set x 1
        r set y 2
        r set z 3
        r hset h f v
        lsort [r scan.scan_strings]
    } {{x 1} {y 2} {z 3}}
    """
    r.run("set", "x", 1)
    r.run("set", "y", 2)
    r.run("set", "z", 3)
    r.run("hset", "h", "f", "v")
    # TODO: lsort r scan.scan_strings
    assert False


@pytest.mark.xfail(reason="not implemented")
def test_module_scan_hash_listpack(r: ValkeyTestClient) -> None:
    """
    test {Module scan hash listpack} {
        r hmset hh f1 v1 f2 v2
        assert_encoding listpack hh
        lsort [r scan.scan_key hh]
    } {{f1 v1} {f2 v2}}
    """
    r.run("hmset", "hh", "f1", "v1", "f2", "v2")
    assert_encoding("listpack", "hh")
    # TODO: lsort r scan.scan_key hh
    assert False


@pytest.mark.xfail(reason="not implemented")
def test_module_scan_hash_listpack_with_int_value(r: ValkeyTestClient) -> None:
    """
    test {Module scan hash listpack with int value} {
        r hmset hh1 f1 1
        assert_encoding listpack hh1
        lsort [r scan.scan_key hh1]
    } {{f1 1}}
    """
    r.run("hmset", "hh1", "f1", 1)
    assert_encoding("listpack", "hh1")
    # TODO: lsort r scan.scan_key hh1
    assert False


@pytest.mark.xfail(reason="not implemented")
def test_module_scan_hash_dict(r: ValkeyTestClient) -> None:
    """
    test {Module scan hash dict} {
        r config set hash-max-ziplist-entries 2
        r hmset hh3 f1 v1 f2 v2 f3 v3
        assert_encoding hashtable hh3
        lsort [r scan.scan_key hh3]
    } {{f1 v1} {f2 v2} {f3 v3}}
    """
    r.run("config", "set", "hash-max-ziplist-entries", 2)
    r.run("hmset", "hh3", "f1", "v1", "f2", "v2", "f3", "v3")
    assert_encoding("hashtable", "hh3")
    # TODO: lsort r scan.scan_key hh3
    assert False


@pytest.mark.xfail(reason="not implemented")
def test_module_scan_zset_listpack(r: ValkeyTestClient) -> None:
    """
    test {Module scan zset listpack} {
        r zadd zz 1 f1 2 f2
        assert_encoding listpack zz
        lsort [r scan.scan_key zz]
    } {{f1 1} {f2 2}}
    """
    r.run("zadd", "zz", 1, "f1", 2, "f2")
    assert_encoding("listpack", "zz")
    # TODO: lsort r scan.scan_key zz
    assert False


@pytest.mark.xfail(reason="not implemented")
def test_module_scan_zset_skiplist(r: ValkeyTestClient) -> None:
    """
    test {Module scan zset skiplist} {
        r config set zset-max-ziplist-entries 2
        r zadd zz1 1 f1 2 f2 3 f3
        assert_encoding skiplist zz1
        lsort [r scan.scan_key zz1]
    } {{f1 1} {f2 2} {f3 3}}
    """
    r.run("config", "set", "zset-max-ziplist-entries", 2)
    r.run("zadd", "zz1", 1, "f1", 2, "f2", 3, "f3")
    assert_encoding("skiplist", "zz1")
    # TODO: lsort r scan.scan_key zz1
    assert False


@pytest.mark.xfail(reason="not implemented")
def test_module_scan_set_intset(r: ValkeyTestClient) -> None:
    """
    test {Module scan set intset} {
        r del ss
        r sadd ss 1 2
        assert_encoding intset ss
        lsort [r scan.scan_key ss]
    } {{1 {}} {2 {}}}
    """
    r.run("del", "ss")
    r.run("sadd", "ss", 1, 2)
    assert_encoding("intset", "ss")
    # TODO: lsort r scan.scan_key ss
    assert False


@pytest.mark.xfail(reason="not implemented")
def test_module_scan_set_dict(r: ValkeyTestClient) -> None:
    """
    test {Module scan set dict} {
        r del ssa
        r config set set-max-intset-entries 2
        r sadd ssa 1 2 ; # Created as intset
        r sadd ssa 3   ; # Converted to hashtable
        assert_encoding hashtable ssa
        lsort [r scan.scan_key ssa]
    } {{1 {}} {2 {}} {3 {}}}
    """
    r.run("del", "ssa")
    r.run("config", "set", "set-max-intset-entries", 2)
    r.run("sadd", "ssa", 1, 2)
    r.run("sadd", "ssa", 3)
    assert_encoding("hashtable", "ssa")
    # TODO: lsort r scan.scan_key ssa
    assert False


@pytest.mark.xfail(reason="not implemented")
def test_module_scan_set_listpack(r: ValkeyTestClient) -> None:
    """
    test {Module scan set listpack} {
        r del ss1
        r sadd ss1 a b c
        assert_encoding listpack ss1
        lsort [r scan.scan_key ss1]
    } {{a {}} {b {}} {c {}}}
    """
    r.run("del", "ss1")
    r.run("sadd", "ss1", "a", "b", "c")
    assert_encoding("listpack", "ss1")
    # TODO: lsort r scan.scan_key ss1
    assert False


def test_unload_the_module_scan(r: ValkeyTestClient) -> None:
    """
    test "Unload the module - scan" {
        assert_equal {OK} [r module unload scan]
    }
    """
    assert "OK" == r.run("module", "unload", "scan")


# --- stubs for unimplemented TCL helpers ---


def assert_encoding(*args):
    raise NotImplementedError("assert_encoding")
