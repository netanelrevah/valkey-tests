# ruff: noqa: PLR2004

import pytest

from tests.valkey_test_client import ValkeyTestClient

"""
set testmodule file normalize tests/modules/rdbloadsave.so
"""

pytestmark = [pytest.mark.modules]


"""
r module load testmodule
"""


@pytest.mark.xfail(reason="not implemented")
def test_module_rdbloadsave_sanity(r: ValkeyTestClient) -> None:
    """
    test "Module rdbloadsave sanity" {
        r test.sanity

        # Try to load non-existing file
        assert_error {*No such file or directory*} {r test.rdbload sanity.rdb}

        r set x 1
        assert_equal OK [r test.rdbsave sanity.rdb]

        r flushdb
        assert_equal OK [r test.rdbload sanity.rdb]
        assert_equal 1 [r get x]
    }
    """
    r.run("test.sanity")
    # TODO: assert_error {*No such file or directory*} {r test.rdbload sanity.rdb}
    r.run("set", "x", 1)
    assert "OK" == r.run("test.rdbsave", "sanity.rdb")
    r.run("flushdb")
    assert "OK" == r.run("test.rdbload", "sanity.rdb")
    assert 1 == r.run("get", "x")


@pytest.mark.xfail(reason="not implemented")
def test_module_rdbloadsave_test_with_pipelining(r: ValkeyTestClient) -> None:
    """
    test "Module rdbloadsave test with pipelining" {
        r config set save ""
        r config set loading-process-events-interval-bytes 1024
        r config set key-load-delay 50
        r flushdb

        populate 3000 a 1024
        r set x 111
        assert_equal [r dbsize] 3001

        assert_equal OK [r test.rdbsave blabla.rdb]
        r flushdb
        assert_equal [r dbsize] 0

        # Send commands with pipeline. First command will call RM_RdbLoad() in
        # the command callback. While loading RDB, the server can go to networking to
        # reply -LOADING. By sending commands in pipeline, we verify it doesn't
        # cause a problem.
        # e.g. the server won't try to process next message of the current client
        # while it is in the command callback for that client   .
        set rd1 [valkey_deferring_client]
        $rd1 test.rdbload blabla.rdb

        wait_for_condition 50 100 {
            [s loading] eq 1
        } else {
            fail "Redis did not start loading or loaded RDB too fast"
        }

        $rd1 get x
        $rd1 dbsize

        assert_equal OK [$rd1 read]
        assert_equal 111 [$rd1 read]
        assert_equal 3001 [$rd1 read]
        r flushdb
        r config set key-load-delay 0
    }
    """
    r.run("config", "set", "save", "")
    r.run("config", "set", "loading-process-events-interval-bytes", 1024)
    r.run("config", "set", "key-load-delay", 50)
    r.run("flushdb")
    # TODO: populate 3000 a 1024
    r.run("set", "x", 111)
    assert r.run("dbsize") == 3001
    assert "OK" == r.run("test.rdbsave", "blabla.rdb")
    r.run("flushdb")
    assert r.run("dbsize") == 0
    # TODO: set rd1 valkey_deferring_client
    # TODO: $rd1 test.rdbload blabla.rdb
    # TODO: wait_for_condition 50 100 {
    #       [s loading] eq 1
    #   } else {
    #       fail "Redis did not start loading or loaded RDB too fast"
    #   }
    # TODO: $rd1 get x
    # TODO: $rd1 dbsize
    # TODO: assert_equal OK $rd1 read
    # TODO: assert_equal 111 $rd1 read
    # TODO: assert_equal 3001 $rd1 read
    r.run("flushdb")
    r.run("config", "set", "key-load-delay", 0)


@pytest.mark.xfail(reason="not implemented")
def test_module_rdbloadsave_with_aof(r: ValkeyTestClient) -> None:
    """
    test "Module rdbloadsave with aof" {
        r config set save ""

        # Enable the AOF
        r config set appendonly yes
        r config set auto-aof-rewrite-percentage 0 ; # Disable auto-rewrite.
        waitForBgrewriteaof r

        r set k v1
        assert_equal OK [r test.rdbsave aoftest.rdb]

        r set k v2
        r config set rdb-key-save-delay 10000000
        r bgrewriteaof

        # RM_RdbLoad() should kill aof fork
        assert_equal OK [r test.rdbload aoftest.rdb]

        wait_for_condition 50 100 {
            [string match {*Killing*AOF*child*} [exec tail -20 < [srv 0 stdout]]]
        } else {
            fail "Can't find 'Killing AOF child' in recent log lines"
        }

        # Verify that AOF is active.
        assert_equal 1 [s aof_enabled]

        # Verify the value in the loaded rdb
        assert_equal v1 [r get k]

        r flushdb
        r config set rdb-key-save-delay 0
        r config set appendonly no
    }
    """
    r.run("config", "set", "save", "")
    r.run("config", "set", "appendonly", "yes")
    r.run("config", "set", "auto-aof-rewrite-percentage", 0)
    # TODO: waitForBgrewriteaof r
    r.run("set", "k", "v1")
    assert "OK" == r.run("test.rdbsave", "aoftest.rdb")
    r.run("set", "k", "v2")
    r.run("config", "set", "rdb-key-save-delay", 10000000)
    r.run("bgrewriteaof")
    assert "OK" == r.run("test.rdbload", "aoftest.rdb")
    # TODO: wait_for_condition 50 100 {
    #       [string match {*Killing*AOF*child*} [exec tail -20 < [srv 0 stdout]]]
    #   } else {
    #       fail "Can't find 'Killing AOF child' in recent log lines"
    #   }
    # TODO: assert_equal 1 s aof_enabled
    assert "v1" == r.run("get", "k")
    r.run("flushdb")
    r.run("config", "set", "rdb-key-save-delay", 0)
    r.run("config", "set", "appendonly", "no")


@pytest.mark.xfail(reason="not implemented")
def test_module_rdbloadsave_with_bgsave(r: ValkeyTestClient) -> None:
    """
    test "Module rdbloadsave with bgsave" {
        r flushdb
        r config set save ""

        r set k v1
        assert_equal OK [r test.rdbsave bgsave.rdb]

        r set k v2
        r config set rdb-key-save-delay 500000
        r bgsave

        # RM_RdbLoad() should kill RDB fork
        assert_equal OK [r test.rdbload bgsave.rdb]

        wait_for_condition 10 1000 {
            [string match {*Background*saving*terminated*} [exec tail -20 < [srv 0 stdout]]]
        } else {
            fail "Can't find 'Background saving terminated' in recent log lines"
        }

        assert_equal v1 [r get k]
        r flushall
        waitForBgsave r
        r config set rdb-key-save-delay 0
    }
    """
    r.run("flushdb")
    r.run("config", "set", "save", "")
    r.run("set", "k", "v1")
    assert "OK" == r.run("test.rdbsave", "bgsave.rdb")
    r.run("set", "k", "v2")
    r.run("config", "set", "rdb-key-save-delay", 500000)
    r.run("bgsave")
    assert "OK" == r.run("test.rdbload", "bgsave.rdb")
    # TODO: wait_for_condition 10 1000 {
    #       [string match {*Background*saving*terminated*} [exec tail -20 < [srv 0 stdout]]]
    #   } else {
    #       fail "Can't find 'Background saving terminated' in recent log lines"
    #   }
    assert "v1" == r.run("get", "k")
    r.run("flushall")
    # TODO: waitForBgsave r
    r.run("config", "set", "rdb-key-save-delay", 0)


@pytest.mark.xfail(reason="not implemented")
def test_module_rdbloadsave_calls_rdbsave_in_a_module_fork(r: ValkeyTestClient) -> None:
    """
    test "Module rdbloadsave calls rdbsave in a module fork" {
        r flushdb
        r config set save ""
        r config set rdb-key-save-delay 500000

        r set k v1

        # Module will call RM_Fork() before calling RM_RdbSave()
        assert_equal OK [r test.rdbsave_fork rdbfork.rdb]
        assert_equal [s module_fork_in_progress] 1

        wait_for_condition 10 1000 {
            [status r module_fork_in_progress] == "0"
        } else {
            fail "Module fork didn't finish"
        }

        r set k v2
        assert_equal OK [r test.rdbload rdbfork.rdb]
        assert_equal v1 [r get k]

        r config set rdb-key-save-delay 0
    }
    """
    r.run("flushdb")
    r.run("config", "set", "save", "")
    r.run("config", "set", "rdb-key-save-delay", 500000)
    r.run("set", "k", "v1")
    assert "OK" == r.run("test.rdbsave_fork", "rdbfork.rdb")
    # TODO: assert_equal s module_fork_in_progress 1
    # TODO: wait_for_condition 10 1000 {
    #       [status r module_fork_in_progress] == "0"
    #   } else {
    #       fail "Module fork didn't finish"
    #   }
    r.run("set", "k", "v2")
    assert "OK" == r.run("test.rdbload", "rdbfork.rdb")
    assert "v1" == r.run("get", "k")
    r.run("config", "set", "rdb-key-save-delay", 0)


def test_unload_the_module_rdbloadsave(r: ValkeyTestClient) -> None:
    """
    test "Unload the module - rdbloadsave" {
        assert_equal {OK} [r module unload rdbloadsave]
    }
    """
    assert "OK" == r.run("module", "unload", "rdbloadsave")
