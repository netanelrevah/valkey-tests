# ruff: noqa: PLR2004, RUF043

import pytest

from tests.valkey_test_client import ValkeyTestClient

"""
set testmodule file normalize tests/modules/zset.so
"""

pytestmark = [pytest.mark.modules]


def test_module_zset_rem(r: ValkeyTestClient) -> None:
    """
    test {Module zset rem} {
        r del k
        r zadd k 100 hello 200 world
        assert_equal 1 [r zset.rem k hello]
        assert_equal 0 [r zset.rem k hello]
        assert_equal 1 [r exists k]
        # Check that removing the last element deletes the key
        assert_equal 1 [r zset.rem k world]
        assert_equal 0 [r exists k]
    }
    """
    r.run("del", "k")
    r.run("zadd", "k", 100, "hello", 200, "world")
    assert 1 == r.run("zset.rem", "k", "hello")
    assert 0 == r.run("zset.rem", "k", "hello")
    assert 1 == r.run("exists", "k")
    assert 1 == r.run("zset.rem", "k", "world")
    assert 0 == r.run("exists", "k")


def test_module_zset_add(r: ValkeyTestClient) -> None:
    """
    test {Module zset add} {
        r del k
        # Check that failure does not create empty key
        assert_error "ERR ZsetAdd failed" {r zset.add k nan hello}
        assert_equal 0 [r exists k]

        r zset.add k 100 hello
        assert_equal {hello 100} [r zrange k 0 -1 withscores]
    }
    """
    r.run("del", "k")
    with pytest.raises(Exception, match="ERR\\ ZsetAdd\\ failed"):
        r.run("zset.add", "k", float("nan"), "hello")
    assert 0 == r.run("exists", "k")
    r.run("zset.add", "k", 100, "hello")
    assert "hello 100" == r.run("zrange", "k", 0, -1, "withscores")


def test_module_zset_incrby(r: ValkeyTestClient) -> None:
    """
    test {Module zset incrby} {
        r del k
        # Check that failure does not create empty key
        assert_error "ERR ZsetIncrby failed" {r zset.incrby k hello nan}
        assert_equal 0 [r exists k]

        r zset.incrby k hello 100
        assert_equal {hello 100} [r zrange k 0 -1 withscores]
    }
    """
    r.run("del", "k")
    with pytest.raises(Exception, match="ERR\\ ZsetIncrby\\ failed"):
        r.run("zset.incrby", "k", "hello", float("nan"))
    assert 0 == r.run("exists", "k")
    r.run("zset.incrby", "k", "hello", 100)
    assert "hello 100" == r.run("zrange", "k", 0, -1, "withscores")


def test_module_zset_rangebylex(r: ValkeyTestClient) -> None:
    """
    test {Module zset rangebylex} {
        # Should give wrong arity error
        assert_error "ERR wrong number of arguments*" {r zset.rangebylex}
        assert_error "ERR wrong number of arguments*" {r zset.revrangebylex}

        # Should give wrong type error
        r del k
        r set k v
        assert_error "WRONGTYPE Operation against a key*" {r zset.rangebylex k - +}

        # Should give invalid range error
        r del k
        r zadd k 0 ele
        assert_error "invalid range" {r zset.rangebylex k - a}
        assert_error "invalid range" {r zset.revrangebylex k - a}

        # Check if the data structure of the sorted set is skiplist
        r del k
        r config set zset-max-listpack-entries 2
        r config set zset-max-listpack-value 64
        for {set i 0} {$i < 4} {incr i} {
            r zadd k 0 "ele$i"
        }
        assert_equal {ele0 ele1 ele2 ele3} [r zset.rangebylex k - +]
        assert_equal {ele3 ele2 ele1 ele0} [r zset.revrangebylex k - +]
        assert_equal {ele1 ele2} [r zset.rangebylex k "(ele0" "(ele3"]
        assert_equal {ele2 ele1} [r zset.revrangebylex k "(ele0" "(ele3"]

        # Check if the data structure of the sorted set is listpack
        r del k
        r config set zset-max-listpack-entries 128
        r config set zset-max-listpack-value 64
        for {set i 0} {$i < 4} {incr i} {
            r zadd k 0 "ele$i"
        }
        assert_equal {ele0 ele1 ele2 ele3} [r zset.rangebylex k - +]
        assert_equal {ele3 ele2 ele1 ele0} [r zset.revrangebylex k - +]
        assert_equal {ele1 ele2} [r zset.rangebylex k "(ele0" "(ele3"]
        assert_equal {ele2 ele1} [r zset.revrangebylex k "(ele0" "(ele3"]
    }
    """
    with pytest.raises(Exception, match="ERR\\ wrong\\ number\\ of\\ arguments.*"):
        r.run("zset.rangebylex")
    with pytest.raises(Exception, match="ERR\\ wrong\\ number\\ of\\ arguments.*"):
        r.run("zset.revrangebylex")
    r.run("del", "k")
    r.run("set", "k", "v")
    with pytest.raises(Exception, match="WRONGTYPE\\ Operation\\ against\\ a\\ key.*"):
        r.run("zset.rangebylex", "k", "-", "+")
    r.run("del", "k")
    r.run("zadd", "k", 0, "ele")
    with pytest.raises(Exception, match="invalid\\ range"):
        r.run("zset.rangebylex", "k", "-", "a")
    with pytest.raises(Exception, match="invalid\\ range"):
        r.run("zset.revrangebylex", "k", "-", "a")
    r.run("del", "k")
    r.run("config", "set", "zset-max-listpack-entries", 2)
    r.run("config", "set", "zset-max-listpack-value", 64)
    i = 0
    while i < 4:
        r.run("zadd", "k", 0, f"ele{i}")
        i += 1
    assert "ele0 ele1 ele2 ele3" == r.run("zset.rangebylex", "k", "-", "+")
    assert "ele3 ele2 ele1 ele0" == r.run("zset.revrangebylex", "k", "-", "+")
    assert "ele1 ele2" == r.run("zset.rangebylex", "k", "(ele0", "(ele3")
    assert "ele2 ele1" == r.run("zset.revrangebylex", "k", "(ele0", "(ele3")
    r.run("del", "k")
    r.run("config", "set", "zset-max-listpack-entries", 128)
    r.run("config", "set", "zset-max-listpack-value", 64)
    i = 0
    while i < 4:
        r.run("zadd", "k", 0, f"ele{i}")
        i += 1
    assert "ele0 ele1 ele2 ele3" == r.run("zset.rangebylex", "k", "-", "+")
    assert "ele3 ele2 ele1 ele0" == r.run("zset.revrangebylex", "k", "-", "+")
    assert "ele1 ele2" == r.run("zset.rangebylex", "k", "(ele0", "(ele3")
    assert "ele2 ele1" == r.run("zset.revrangebylex", "k", "(ele0", "(ele3")


def test_module_zset_members(r: ValkeyTestClient) -> None:
    """
    test {Module zset members} {
        # Should give wrong arity error
        assert_error "ERR wrong number of arguments*" {r zset.members}

        # Should give wrong type error
        r del k
        r set k v
        assert_error "WRONGTYPE Operation against a key*" {r zset.members k}

        # Check if the data structure of the sorted set is skiplist
        r del k
        r config set zset-max-listpack-entries 2
        r config set zset-max-listpack-value 64
        for {set i 0} {$i < 4} {incr i} {
            r zadd k 0 "ele$i"
        }
        assert_equal {ele0 ele1 ele2 ele3} [lsort [r zset.members k]]

        # Check if the data structure of the sorted set is listpack
        r del k
        r config set zset-max-listpack-entries 128
        r config set zset-max-listpack-value 64
        for {set i 0} {$i < 4} {incr i} {
            r zadd k 0 "ele$i"
        }
        assert_equal {ele0 ele1 ele2 ele3} [lsort [r zset.members k]]
    }
    """
    with pytest.raises(Exception, match="ERR\\ wrong\\ number\\ of\\ arguments.*"):
        r.run("zset.members")
    r.run("del", "k")
    r.run("set", "k", "v")
    with pytest.raises(Exception, match="WRONGTYPE\\ Operation\\ against\\ a\\ key.*"):
        r.run("zset.members", "k")
    r.run("del", "k")
    r.run("config", "set", "zset-max-listpack-entries", 2)
    r.run("config", "set", "zset-max-listpack-value", 64)
    i = 0
    while i < 4:
        r.run("zadd", "k", 0, f"ele{i}")
        i += 1
    assert "ele0 ele1 ele2 ele3" == sorted(r.run("zset.members", "k"))
    r.run("del", "k")
    r.run("config", "set", "zset-max-listpack-entries", 128)
    r.run("config", "set", "zset-max-listpack-value", 64)
    i = 0
    while i < 4:
        r.run("zadd", "k", 0, f"ele{i}")
        i += 1
    assert "ele0 ele1 ele2 ele3" == sorted(r.run("zset.members", "k"))


def test_unload_the_module_zset(r: ValkeyTestClient) -> None:
    """
    test "Unload the module - zset" {
        assert_equal {OK} [r module unload zset]
    }
    """
    assert "OK" == r.run("module", "unload", "zset")
