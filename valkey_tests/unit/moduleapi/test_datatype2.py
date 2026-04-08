# ruff: noqa: PLR2004, ANN002, ANN201

import pytest

from tests.valkey_test_client import ValkeyTestClient

"""
set testmodule file normalize tests/modules/datatype2.so
"""

pytestmark = [pytest.mark.modules]


def test_datatype2_test_mem_alloc_and_free(r: ValkeyTestClient) -> None:
    """
    test "datatype2: test mem alloc and free" {
        r flushall

        r select 0
        assert_equal 3 [r mem.alloc k1 3]
        assert_equal 2 [r mem.alloc k2 2]

        r select 1
        assert_equal 1 [r mem.alloc k1 1]
        assert_equal 5 [r mem.alloc k2 5]

        r select 0
        assert_equal 1 [r mem.free k1]
        assert_equal 1 [r mem.free k2]

        r select 1
        assert_equal 1 [r mem.free k1]
        assert_equal 1 [r mem.free k2]
    }
    """
    r.run("flushall")
    r.run("select", 0)
    assert 3 == r.run("mem.alloc", "k1", 3)
    assert 2 == r.run("mem.alloc", "k2", 2)
    r.run("select", 1)
    assert 1 == r.run("mem.alloc", "k1", 1)
    assert 5 == r.run("mem.alloc", "k2", 5)
    r.run("select", 0)
    assert 1 == r.run("mem.free", "k1")
    assert 1 == r.run("mem.free", "k2")
    r.run("select", 1)
    assert 1 == r.run("mem.free", "k1")
    assert 1 == r.run("mem.free", "k2")


def test_datatype2_test_del_and_unlink(r: ValkeyTestClient) -> None:
    """
    test "datatype2: test del and unlink" {
        r flushall

        assert_equal 100 [r mem.alloc k1 100]
        assert_equal 60 [r mem.alloc k2 60]

        assert_equal 1 [r unlink k1]
        assert_equal 1 [r del k2]
    }
    """
    r.run("flushall")
    assert 100 == r.run("mem.alloc", "k1", 100)
    assert 60 == r.run("mem.alloc", "k2", 60)
    assert 1 == r.run("unlink", "k1")
    assert 1 == r.run("del", "k2")


def test_datatype2_test_read_and_write(r: ValkeyTestClient) -> None:
    """
    test "datatype2: test read and write" {
        r flushall

        assert_equal 3 [r mem.alloc k1 3]

        set data datatype2
        assert_equal [string length $data] [r mem.write k1 0 $data]
        assert_equal $data [r mem.read k1 0]
    }
    """
    r.run("flushall")
    assert 3 == r.run("mem.alloc", "k1", 3)
    data = "datatype2"
    assert len(data) == r.run("mem.write", "k1", 0, data)
    assert data == r.run("mem.read", "k1", 0)


def test_datatype2_test_rdb_save_and_load(r: ValkeyTestClient) -> None:
    """
    test "datatype2: test rdb save and load" {
        r flushall

        r select 0
        set data k1
        assert_equal 3 [r mem.alloc k1 3]
        assert_equal [string length $data] [r mem.write k1 1 $data]

        set data k2
        assert_equal 2 [r mem.alloc k2 2]
        assert_equal [string length $data] [r mem.write k2 0 $data]

        r select 1
        set data k3
        assert_equal 3 [r mem.alloc k3 3]
        assert_equal [string length $data] [r mem.write k3 1 $data]

        set data k4
        assert_equal 2 [r mem.alloc k4 2]
        assert_equal [string length $data] [r mem.write k4 0 $data]

        r bgsave
        waitForBgsave r
        r debug reload

        r select 0
        assert_equal k1 [r mem.read k1 1]
        assert_equal k2 [r mem.read k2 0]

        r select 1
        assert_equal k3 [r mem.read k3 1]
        assert_equal k4 [r mem.read k4 0]
    }
    """
    r.run("flushall")
    r.run("select", 0)
    data = "k1"
    assert 3 == r.run("mem.alloc", "k1", 3)
    assert len(data) == r.run("mem.write", "k1", 1, data)
    data = "k2"
    assert 2 == r.run("mem.alloc", "k2", 2)
    assert len(data) == r.run("mem.write", "k2", 0, data)
    r.run("select", 1)
    data = "k3"
    assert 3 == r.run("mem.alloc", "k3", 3)
    assert len(data) == r.run("mem.write", "k3", 1, data)
    data = "k4"
    assert 2 == r.run("mem.alloc", "k4", 2)
    assert len(data) == r.run("mem.write", "k4", 0, data)
    r.run("bgsave")
    wait_for_bgsave("r")
    r.run("debug", "reload")
    r.run("select", 0)
    assert "k1" == r.run("mem.read", "k1", 1)
    assert "k2" == r.run("mem.read", "k2", 0)
    r.run("select", 1)
    assert "k3" == r.run("mem.read", "k3", 1)
    assert "k4" == r.run("mem.read", "k4", 0)


def test_datatype2_test_aof_rewrite(r: ValkeyTestClient) -> None:
    """
    test "datatype2: test aof rewrite" {
        r flushall

        r select 0
        set data k1
        assert_equal 3 [r mem.alloc k1 3]
        assert_equal [string length $data] [r mem.write k1 1 $data]

        set data k2
        assert_equal 2 [r mem.alloc k2 2]
        assert_equal [string length $data] [r mem.write k2 0 $data]

        r select 1
        set data k3
        assert_equal 3 [r mem.alloc k3 3]
        assert_equal [string length $data] [r mem.write k3 1 $data]

        set data k4
        assert_equal 2 [r mem.alloc k4 2]
        assert_equal [string length $data] [r mem.write k4 0 $data]

        r bgrewriteaof
        waitForBgrewriteaof r
        r debug loadaof

        r select 0
        assert_equal k1 [r mem.read k1 1]
        assert_equal k2 [r mem.read k2 0]

        r select 1
        assert_equal k3 [r mem.read k3 1]
        assert_equal k4 [r mem.read k4 0]
    }
    """
    r.run("flushall")
    r.run("select", 0)
    data = "k1"
    assert 3 == r.run("mem.alloc", "k1", 3)
    assert len(data) == r.run("mem.write", "k1", 1, data)
    data = "k2"
    assert 2 == r.run("mem.alloc", "k2", 2)
    assert len(data) == r.run("mem.write", "k2", 0, data)
    r.run("select", 1)
    data = "k3"
    assert 3 == r.run("mem.alloc", "k3", 3)
    assert len(data) == r.run("mem.write", "k3", 1, data)
    data = "k4"
    assert 2 == r.run("mem.alloc", "k4", 2)
    assert len(data) == r.run("mem.write", "k4", 0, data)
    r.run("bgrewriteaof")
    wait_for_bgrewriteaof("r")
    r.run("debug", "loadaof")
    r.run("select", 0)
    assert "k1" == r.run("mem.read", "k1", 1)
    assert "k2" == r.run("mem.read", "k2", 0)
    r.run("select", 1)
    assert "k3" == r.run("mem.read", "k3", 1)
    assert "k4" == r.run("mem.read", "k4", 0)


def test_datatype2_test_copy(r: ValkeyTestClient) -> None:
    """
    test "datatype2: test copy" {
        r flushall

        r select 0
        set data k1
        assert_equal 3 [r mem.alloc k1 3]
        assert_equal [string length $data] [r mem.write k1 1 $data]
        assert_equal $data [r mem.read k1 1]

        set data k2
        assert_equal 2 [r mem.alloc k2 2]
        assert_equal [string length $data] [r mem.write k2 0 $data]
        assert_equal $data [r mem.read k2 0]

        r select 1
        set data k3
        assert_equal 3 [r mem.alloc k3 3]
        assert_equal [string length $data] [r mem.write k3 1 $data]

        set data k4
        assert_equal 2 [r mem.alloc k4 2]
        assert_equal [string length $data] [r mem.write k4 0 $data]

        assert_equal {total 5 used 2} [r mem.usage 0]
        assert_equal {total 5 used 2} [r mem.usage 1]

        r select 0
        assert_equal 1 [r copy k1 k3]
        assert_equal k1 [r mem.read k3 1]
        assert_equal {total 8 used 3} [r mem.usage 0]
        assert_equal 1 [r copy k2 k1 db 1]

        r select 1
        assert_equal k2 [r mem.read k1 0]
        assert_equal {total 8 used 3} [r mem.usage 0]
        assert_equal {total 7 used 3} [r mem.usage 1]
    }
    """
    r.run("flushall")
    r.run("select", 0)
    data = "k1"
    assert 3 == r.run("mem.alloc", "k1", 3)
    assert len(data) == r.run("mem.write", "k1", 1, data)
    assert data == r.run("mem.read", "k1", 1)
    data = "k2"
    assert 2 == r.run("mem.alloc", "k2", 2)
    assert len(data) == r.run("mem.write", "k2", 0, data)
    assert data == r.run("mem.read", "k2", 0)
    r.run("select", 1)
    data = "k3"
    assert 3 == r.run("mem.alloc", "k3", 3)
    assert len(data) == r.run("mem.write", "k3", 1, data)
    data = "k4"
    assert 2 == r.run("mem.alloc", "k4", 2)
    assert len(data) == r.run("mem.write", "k4", 0, data)
    assert "total 5 used 2" == r.run("mem.usage", 0)
    assert "total 5 used 2" == r.run("mem.usage", 1)
    r.run("select", 0)
    assert 1 == r.run("copy", "k1", "k3")
    assert "k1" == r.run("mem.read", "k3", 1)
    assert "total 8 used 3" == r.run("mem.usage", 0)
    assert 1 == r.run("copy", "k2", "k1", "db", 1)
    r.run("select", 1)
    assert "k2" == r.run("mem.read", "k1", 0)
    assert "total 8 used 3" == r.run("mem.usage", 0)
    assert "total 7 used 3" == r.run("mem.usage", 1)


def test_datatype2_test_swapdb(r: ValkeyTestClient) -> None:
    """
    test "datatype2: test swapdb" {
        r flushall

        r select 0
        set data k1
        assert_equal 5 [r mem.alloc k1 5]
        assert_equal [string length $data] [r mem.write k1 1 $data]
        assert_equal $data [r mem.read k1 1]

        set data k2
        assert_equal 4 [r mem.alloc k2 4]
        assert_equal [string length $data] [r mem.write k2 0 $data]
        assert_equal $data [r mem.read k2 0]

        r select 1
        set data k1
        assert_equal 3 [r mem.alloc k3 3]
        assert_equal [string length $data] [r mem.write k3 1 $data]

        set data k2
        assert_equal 2 [r mem.alloc k4 2]
        assert_equal [string length $data] [r mem.write k4 0 $data]

        assert_equal {total 9 used 2} [r mem.usage 0]
        assert_equal {total 5 used 2} [r mem.usage 1]

        assert_equal OK [r swapdb 0 1]
        assert_equal {total 9 used 2} [r mem.usage 1]
        assert_equal {total 5 used 2} [r mem.usage 0]
    }
    """
    r.run("flushall")
    r.run("select", 0)
    data = "k1"
    assert 5 == r.run("mem.alloc", "k1", 5)
    assert len(data) == r.run("mem.write", "k1", 1, data)
    assert data == r.run("mem.read", "k1", 1)
    data = "k2"
    assert 4 == r.run("mem.alloc", "k2", 4)
    assert len(data) == r.run("mem.write", "k2", 0, data)
    assert data == r.run("mem.read", "k2", 0)
    r.run("select", 1)
    data = "k1"
    assert 3 == r.run("mem.alloc", "k3", 3)
    assert len(data) == r.run("mem.write", "k3", 1, data)
    data = "k2"
    assert 2 == r.run("mem.alloc", "k4", 2)
    assert len(data) == r.run("mem.write", "k4", 0, data)
    assert "total 9 used 2" == r.run("mem.usage", 0)
    assert "total 5 used 2" == r.run("mem.usage", 1)
    assert "OK" == r.run("swapdb", 0, 1)
    assert "total 9 used 2" == r.run("mem.usage", 1)
    assert "total 5 used 2" == r.run("mem.usage", 0)


def test_datatype2_test_digest(r: ValkeyTestClient) -> None:
    """
    test "datatype2: test digest" {
        r flushall

        r select 0
        set data k1
        assert_equal 3 [r mem.alloc k1 3]
        assert_equal [string length $data] [r mem.write k1 1 $data]
        assert_equal $data [r mem.read k1 1]

        set data k2
        assert_equal 2 [r mem.alloc k2 2]
        assert_equal [string length $data] [r mem.write k2 0 $data]
        assert_equal $data [r mem.read k2 0]

        r select 1
        set data k1
        assert_equal 3 [r mem.alloc k1 3]
        assert_equal [string length $data] [r mem.write k1 1 $data]
        assert_equal $data [r mem.read k1 1]

        set data k2
        assert_equal 2 [r mem.alloc k2 2]
        assert_equal [string length $data] [r mem.write k2 0 $data]
        assert_equal $data [r mem.read k2 0]

        r select 0
        set digest0 [debug_digest]

        r select 1
        set digest1 [debug_digest]

        assert_equal $digest0 $digest1
    }
    """
    r.run("flushall")
    r.run("select", 0)
    data = "k1"
    assert 3 == r.run("mem.alloc", "k1", 3)
    assert len(data) == r.run("mem.write", "k1", 1, data)
    assert data == r.run("mem.read", "k1", 1)
    data = "k2"
    assert 2 == r.run("mem.alloc", "k2", 2)
    assert len(data) == r.run("mem.write", "k2", 0, data)
    assert data == r.run("mem.read", "k2", 0)
    r.run("select", 1)
    data = "k1"
    assert 3 == r.run("mem.alloc", "k1", 3)
    assert len(data) == r.run("mem.write", "k1", 1, data)
    assert data == r.run("mem.read", "k1", 1)
    data = "k2"
    assert 2 == r.run("mem.alloc", "k2", 2)
    assert len(data) == r.run("mem.write", "k2", 0, data)
    assert data == r.run("mem.read", "k2", 0)
    r.run("select", 0)
    digest0 = debug_digest()
    r.run("select", 1)
    digest1 = debug_digest()
    assert digest0 == digest1


def test_datatype2_test_memusage(r: ValkeyTestClient) -> None:
    """
    test "datatype2: test memusage" {
        r flushall

        set data k1
        assert_equal 3 [r mem.alloc k1 3]
        assert_equal [string length $data] [r mem.write k1 1 $data]
        assert_equal $data [r mem.read k1 1]

        set data k2
        assert_equal 3 [r mem.alloc k2 3]
        assert_equal [string length $data] [r mem.write k2 0 $data]
        assert_equal $data [r mem.read k2 0]

        assert_equal [memory_usage k1] [memory_usage k2]
    }
    """
    r.run("flushall")
    data = "k1"
    assert 3 == r.run("mem.alloc", "k1", 3)
    assert len(data) == r.run("mem.write", "k1", 1, data)
    assert data == r.run("mem.read", "k1", 1)
    data = "k2"
    assert 3 == r.run("mem.alloc", "k2", 3)
    assert len(data) == r.run("mem.write", "k2", 0, data)
    assert data == r.run("mem.read", "k2", 0)
    assert memory_usage("k1") == memory_usage("k2")


# --- stubs for unimplemented TCL helpers ---


def debug_digest(*args):
    raise NotImplementedError("debug_digest")


def memory_usage(*args):
    raise NotImplementedError("memory_usage")


def wait_for_bgrewriteaof(*args):
    raise NotImplementedError("wait_for_bgrewriteaof")


def wait_for_bgsave(*args):
    raise NotImplementedError("wait_for_bgsave")
