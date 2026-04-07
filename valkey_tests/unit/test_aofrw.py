# ruff: noqa: F841, ANN001, ANN002, ANN201
import time
from fnmatch import fnmatch

import pytest

from tests.valkey_test_client import ValkeyTestClient

pytestmark = [pytest.mark.aofrw_external_skip_logreqres_skip]


"""
r config set appendonly yes
"""


"""
r config set auto-aof-rewrite-percentage 0
"""


"""
waitForBgrewriteaof r
"""


"""
r config set aof-use-rdb-preamble rdbpre
"""


@pytest.mark.parametrize(["rdbpre"], [("yes"), ("no")])
def test_aof_rewrite_during_write_load_rdb_preamble_rdbpre(r: ValkeyTestClient, rdbpre) -> None:
    """
    test "AOF rewrite during write load: RDB preamble=$rdbpre" {
        # Start with an empty db
        r flushall

        # Start a write load for 10 seconds
        set master [srv 0 client]
        set master_host [srv 0 host]
        set master_port [srv 0 port]
        set load_handle0 [start_write_load $master_host $master_port 10]
        set load_handle1 [start_write_load $master_host $master_port 10]
        set load_handle2 [start_write_load $master_host $master_port 10]
        set load_handle3 [start_write_load $master_host $master_port 10]
        set load_handle4 [start_write_load $master_host $master_port 10]

        # Make sure the instance is really receiving data
        wait_for_condition 50 100 {
            [r dbsize] > 0
        } else {
            fail "No write load detected."
        }

        # After 3 seconds, start a rewrite, while the write load is still
        # active.
        after 3000
        r bgrewriteaof
        waitForBgrewriteaof r

        # Let it run a bit more so that we'll append some data to the new
        # AOF.
        after 1000

        # Stop the processes generating the load if they are still active
        stop_write_load $load_handle0
        stop_write_load $load_handle1
        stop_write_load $load_handle2
        stop_write_load $load_handle3
        stop_write_load $load_handle4

        # Make sure no more commands processed, before taking debug digest
        wait_load_handlers_disconnected

        # Get the data set digest
        set d1 [debug_digest]

        # Load the AOF
        r debug loadaof
        set d2 [debug_digest]

        # Make sure they are the same
        assert {$d1 eq $d2}
    }
    """
    r.run("flushall")
    master = srv(0, "client")
    master_host = srv(0, "host")
    master_port = srv(0, "port")
    load_handle0 = start_write_load(master_host, master_port, 10)
    load_handle1 = start_write_load(master_host, master_port, 10)
    load_handle2 = start_write_load(master_host, master_port, 10)
    load_handle3 = start_write_load(master_host, master_port, 10)
    load_handle4 = start_write_load(master_host, master_port, 10)
    wait_for_condition(50, 100, lambda: r.run("dbsize") > 0, lambda: fail("No write load detected."))
    time.sleep(3000 / 1000)
    r.run("bgrewriteaof")
    wait_for_bgrewriteaof("r")
    time.sleep(1000 / 1000)
    stop_write_load(load_handle0)
    stop_write_load(load_handle1)
    stop_write_load(load_handle2)
    stop_write_load(load_handle3)
    stop_write_load(load_handle4)
    wait_load_handlers_disconnected()
    d1 = debug_digest()
    r.run("debug", "loadaof")
    d2 = debug_digest()
    assert d1 == d2


pytestmark = [pytest.mark.aofrw_external_skip]


def test_turning_off_aof_kills_the_background_writing_child_if_any(r: ValkeyTestClient) -> None:
    """
    test {Turning off AOF kills the background writing child if any} {
        r config set appendonly yes
        waitForBgrewriteaof r

        # start a slow AOFRW
        r set k v
        r config set rdb-key-save-delay 10000000
        r bgrewriteaof

        # disable AOF and wait for the child to be killed
        r config set appendonly no
        wait_for_condition 50 100 {
            [string match {*Killing*AOF*child*} [exec tail -5 < [srv 0 stdout]]]
        } else {
            fail "Can't find 'Killing AOF child' into recent logs"
        }
        r config set rdb-key-save-delay 0
    }
    """
    r.run("config", "set", "appendonly", "yes")
    wait_for_bgrewriteaof("r")
    r.run("set", "k", "v")
    r.run("config", "set", "rdb-key-save-delay", 10000000)
    r.run("bgrewriteaof")
    r.run("config", "set", "appendonly", "no")
    wait_for_condition(
        50,
        100,
        lambda: string("match", "*Killing*AOF*child*", exec_("tail", -5, "<", srv(0, "stdout"))),
        lambda: fail("Can't find 'Killing AOF child' into recent logs"),
    )
    r.run("config", "set", "rdb-key-save-delay", 0)


"""
foreach d {string int} {
    foreach e {listpack quicklist} {
        test "AOF rewrite of list with $e encoding, $d data" {
            r flushall
            if {$e eq {listpack}} {
                r config set list-max-listpack-size -2
                set len 10
            } else {
                r config set list-max-listpack-size 10
                set len 1000
            }
            for {set j 0} {$j < $len} {incr j} {
                if {$d eq {string}} {
                    set data [randstring 0 16 alpha]
                } else {
                    set data [randomInt 4000000000]
                }
                r lpush key $data
            }
            assert_equal [r object encoding key] $e
            set d1 [debug_digest]
            r bgrewriteaof
            waitForBgrewriteaof r
            r debug loadaof
            set d2 [debug_digest]
            if {$d1 ne $d2} {
                error "assertion:$d1 is not equal to $d2"
            }
        }
    }
}
"""


"""
foreach d {string int} {
    foreach e {intset hashtable} {
        test "AOF rewrite of set with $e encoding, $d data" {
            r flushall
            if {$e eq {intset}} {set len 10} else {set len 1000}
            for {set j 0} {$j < $len} {incr j} {
                if {$d eq {string}} {
                    set data [randstring 0 16 alpha]
                } else {
                    set data [randomInt 4000000000]
                }
                r sadd key $data
            }
            if {$d ne {string}} {
                assert_equal [r object encoding key] $e
            }
            set d1 [debug_digest]
            r bgrewriteaof
            waitForBgrewriteaof r
            r debug loadaof
            set d2 [debug_digest]
            if {$d1 ne $d2} {
                error "assertion:$d1 is not equal to $d2"
            }
        }
    }
}
"""


"""
foreach d {string int} {
    foreach e {listpack hashtable} {
        test "AOF rewrite of hash with $e encoding, $d data" {
            r flushall
            if {$e eq {listpack}} {set len 10} else {set len 1000}
            for {set j 0} {$j < $len} {incr j} {
                if {$d eq {string}} {
                    set data [randstring 0 16 alpha]
                } else {
                    set data [randomInt 4000000000]
                }
                r hset key $data $data
            }
            assert_equal [r object encoding key] $e
            set d1 [debug_digest]
            r bgrewriteaof
            waitForBgrewriteaof r
            r debug loadaof
            set d2 [debug_digest]
            if {$d1 ne $d2} {
                error "assertion:$d1 is not equal to $d2"
            }
        }
    }
}
"""


"""
foreach d {string int} {
    foreach e {listpack skiplist} {
        test "AOF rewrite of zset with $e encoding, $d data" {
            r flushall
            if {$e eq {listpack}} {set len 10} else {set len 1000}
            for {set j 0} {$j < $len} {incr j} {
                if {$d eq {string}} {
                    set data [randstring 0 16 alpha]
                } else {
                    set data [randomInt 4000000000]
                }
                r zadd key [expr rand()] $data
            }
            assert_equal [r object encoding key] $e
            set d1 [debug_digest]
            r bgrewriteaof
            waitForBgrewriteaof r
            r debug loadaof
            set d2 [debug_digest]
            if {$d1 ne $d2} {
                error "assertion:$d1 is not equal to $d2"
            }
        }
    }
}
"""


def test_aof_rewrite_functions(r: ValkeyTestClient) -> None:
    """
    test "AOF rewrite functions" {
        r flushall
        r FUNCTION LOAD {#!lua name=test
            server.register_function('test', function() return 1 end)
        }
        r bgrewriteaof
        waitForBgrewriteaof r
        r function flush
        r debug loadaof
        assert_equal [r fcall test 0] 1
        r FUNCTION LIST
    } {{library_name test engine LUA functions {{name test description {} flags {}}}}}
    """
    r.run("flushall")
    r.run(
        "FUNCTION",
        "LOAD",
        "#!lua name=test\n            server.register_function('test', function() return 1 end)\n        ",
    )
    r.run("bgrewriteaof")
    wait_for_bgrewriteaof("r")
    r.run("function", "flush")
    r.run("debug", "loadaof")
    assert r.run("fcall", "test", 0) == 1
    assert r.run("FUNCTION", "LIST") == "{library_name test engine LUA functions {{name test description {} flags {}}}}"


def test_bgrewriteaof_is_delayed_if_bgsave_is_in_progress(r: ValkeyTestClient) -> None:
    """
    test {BGREWRITEAOF is delayed if BGSAVE is in progress} {
        r flushall
        r set k v
        r config set rdb-key-save-delay 10000000
        r bgsave
        assert_match {*scheduled*} [r bgrewriteaof]
        assert_equal [s aof_rewrite_scheduled] 1
        r config set rdb-key-save-delay 0
        catch {exec kill -9 [get_child_pid 0]}
        while {[s aof_rewrite_scheduled] eq 1} {
            after 100
        }
    }
    """
    r.run("flushall")
    r.run("set", "k", "v")
    r.run("config", "set", "rdb-key-save-delay", 10000000)
    r.run("bgsave")
    assert fnmatch(str(r.run("bgrewriteaof")), "*scheduled*")
    assert s("aof_rewrite_scheduled") == 1
    r.run("config", "set", "rdb-key-save-delay", 0)
    try:
        exec_("kill", -9, get_child_pid(0))
    except Exception:
        pass
    while_("[s aof_rewrite_scheduled] eq 1", "            after 100\n        ")


def test_bgrewriteaof_is_refused_if_already_in_progress(r: ValkeyTestClient) -> None:
    """
    test {BGREWRITEAOF is refused if already in progress} {
        r config set aof-use-rdb-preamble yes
        r config set rdb-key-save-delay 10000000
        catch {
            r bgrewriteaof
            r bgrewriteaof
        } e
        assert_match {*ERR*already*} $e
        r config set rdb-key-save-delay 0
        catch {exec kill -9 [get_child_pid 0]}
    }
    """
    r.run("config", "set", "aof-use-rdb-preamble", "yes")
    r.run("config", "set", "rdb-key-save-delay", 10000000)
    e = None
    try:
        r.run("bgrewriteaof")
        e = r.run("bgrewriteaof")
    except Exception as _catch_err:
        e = str(_catch_err)
    assert fnmatch(str(e), "*ERR*already*")
    r.run("config", "set", "rdb-key-save-delay", 0)
    try:
        exec_("kill", -9, get_child_pid(0))
    except Exception:
        pass


# --- stubs for unimplemented TCL helpers ---


def debug_digest(*args):
    raise NotImplementedError("debug_digest")


def exec_(*args):
    raise NotImplementedError("exec_")


def fail(*args):
    raise NotImplementedError("fail")


def get_child_pid(*args):
    raise NotImplementedError("get_child_pid")


def s(*args):
    raise NotImplementedError("s")


def srv(*args):
    raise NotImplementedError("srv")


def start_write_load(*args):
    raise NotImplementedError("start_write_load")


def stop_write_load(*args):
    raise NotImplementedError("stop_write_load")


def string(*args):
    raise NotImplementedError("string")


def wait_for_bgrewriteaof(*args):
    raise NotImplementedError("wait_for_bgrewriteaof")


def wait_for_condition(*args):
    raise NotImplementedError("wait_for_condition")


def wait_load_handlers_disconnected(*args):
    raise NotImplementedError("wait_load_handlers_disconnected")


def while_(*args):
    raise NotImplementedError("while_")
