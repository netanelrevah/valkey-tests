# ruff: noqa: PLR2004, F841, RUF043, ANN002, ANN201
import time
from fnmatch import fnmatch

import pytest

from tests.valkey_test_client import ValkeyTestClient

pytestmark = [pytest.mark.pause_network]


def test_test_check_paused_info_in_info_clients(r: ValkeyTestClient) -> None:
    """
    test "Test check paused info in info clients" {
        assert_equal [s paused_reason] "none"
        assert_equal [s paused_actions] "none"
        assert_equal [s paused_timeout_milliseconds] 0

        r client PAUSE 10000 WRITE
        assert_equal [s paused_reason] "client_pause"
        assert_equal [s paused_actions] "write"
        after 1000
        set timeout [s paused_timeout_milliseconds]
        assert {$timeout > 0 && $timeout <= 9000}
        r client unpause

        r multi
        r client PAUSE 1000 ALL
        r info clients
        set res [r exec]
        assert_match "*paused_reason:client_pause*" $res
        assert_match "*paused_actions:all*" $res

        r client unpause
        assert_equal [s paused_reason] "none"
        assert_equal [s paused_actions] "none"
        assert_equal [s paused_timeout_milliseconds] 0
    }
    """
    assert s("paused_reason") == "none"
    assert s("paused_actions") == "none"
    assert s("paused_timeout_milliseconds") == 0
    r.run("client", "PAUSE", 10000, "WRITE")
    assert s("paused_reason") == "client_pause"
    assert s("paused_actions") == "write"
    time.sleep(1000 / 1000)
    timeout = s("paused_timeout_milliseconds")
    assert (timeout > 0) and (timeout <= 9000)
    r.run("client", "unpause")
    r.run("multi")
    r.run("client", "PAUSE", 1000, "ALL")
    r.run("info", "clients")
    res = r.run("exec")
    assert fnmatch(str(res), "*paused_reason:client_pause*")
    assert fnmatch(str(res), "*paused_actions:all*")
    r.run("client", "unpause")
    assert s("paused_reason") == "none"
    assert s("paused_actions") == "none"
    assert s("paused_timeout_milliseconds") == 0


def test_test_read_commands_are_not_blocked_by_client_pause(r: ValkeyTestClient) -> None:
    """
    test "Test read commands are not blocked by client pause" {
        r client PAUSE 100000 WRITE
        set rd [valkey_deferring_client]
        $rd GET FOO
        $rd PING
        $rd INFO
        assert_equal [s 0 blocked_clients] 0
        r client unpause
        $rd close
    }
    """
    r.run("client", "PAUSE", 100000, "WRITE")
    rd = ValkeyTestClient.create_from(r)
    rd.run("GET", "FOO")
    rd.run("PING")
    rd.run("INFO")
    assert s(0, "blocked_clients") == 0
    r.run("client", "unpause")
    rd.run("close")


def test_test_old_pause_all_takes_precedence_over_new_pause_write_less_restrictive(r: ValkeyTestClient) -> None:
    """
    test "Test old pause-all takes precedence over new pause-write (less restrictive)" {
        # Scenario:
        # 1. Run 'PAUSE ALL' for 200msec
        # 2. Run 'PAUSE WRITE' for 10 msec
        # 3. Wait 50msec
        # 4. 'GET FOO'.
        # Expected that:
        # - While the time of the second 'PAUSE' is shorter than first 'PAUSE',
        #   pause-client feature will stick to the longer one, i.e, will be paused
        #   up to 200msec.
        # - The GET command will be postponed ~200msec, even though last command
        #   paused only WRITE. This is because the first 'PAUSE ALL' command is
        #   more restrictive than the second 'PAUSE WRITE' and pause-client feature
        #   preserve most restrictive configuration among multiple settings.
        set rd [valkey_deferring_client]
        $rd SET FOO BAR

        set test_start_time [clock milliseconds]
        r client PAUSE 200 ALL
        r client PAUSE 20 WRITE
        after 50
        $rd get FOO
        set elapsed [expr {[clock milliseconds]-$test_start_time}]
        assert_lessthan 200 $elapsed
    }
    """
    rd = ValkeyTestClient.create_from(r)
    rd.run("SET", "FOO", "BAR")
    test_start_time = clock("milliseconds")
    r.run("client", "PAUSE", 200, "ALL")
    r.run("client", "PAUSE", 20, "WRITE")
    time.sleep(50 / 1000)
    rd.run("get", "FOO")
    elapsed = expr("[clock milliseconds]-$test_start_time")
    assert_lessthan(200, elapsed)


def test_test_new_pause_time_is_smaller_than_old_one_then_old_time_preserved(r: ValkeyTestClient) -> None:
    """
    test "Test new pause time is smaller than old one, then old time preserved" {
        r client PAUSE 60000 WRITE
        r client PAUSE 10 WRITE
        after 100
        set rd [valkey_deferring_client]
        $rd SET FOO BAR
        wait_for_blocked_clients_count 1 100 10

        r client unpause
        assert_match "OK" [$rd read]
        $rd close
    }
    """
    r.run("client", "PAUSE", 60000, "WRITE")
    r.run("client", "PAUSE", 10, "WRITE")
    time.sleep(100 / 1000)
    rd = ValkeyTestClient.create_from(r)
    rd.run("SET", "FOO", "BAR")
    wait_for_blocked_clients_count(1, 100, 10)
    r.run("client", "unpause")
    assert fnmatch(str(rd.run("read")), "OK")
    rd.run("close")


def test_test_write_commands_are_paused_by_ro(r: ValkeyTestClient) -> None:
    """
    test "Test write commands are paused by RO" {
        r client PAUSE 60000 WRITE

        set rd [valkey_deferring_client]
        $rd SET FOO BAR
        wait_for_blocked_clients_count 1 50 100

        r client unpause
        assert_match "OK" [$rd read]
        $rd close
    }
    """
    r.run("client", "PAUSE", 60000, "WRITE")
    rd = ValkeyTestClient.create_from(r)
    rd.run("SET", "FOO", "BAR")
    wait_for_blocked_clients_count(1, 50, 100)
    r.run("client", "unpause")
    assert fnmatch(str(rd.run("read")), "OK")
    rd.run("close")


def test_test_special_commands_are_paused_by_ro(r: ValkeyTestClient) -> None:
    """
    test "Test special commands are paused by RO" {
        r PFADD pause-hll test
        r client PAUSE 100000 WRITE

        # Test that pfcount, which can replicate, is also blocked
        set rd [valkey_deferring_client]
        $rd PFCOUNT pause-hll
        wait_for_blocked_clients_count 1 50 100

        # Test that publish, which adds the message to the replication
        # stream is blocked.
        set rd2 [valkey_deferring_client]
        $rd2 publish foo bar
        wait_for_blocked_clients_count 2 50 100

        r client unpause
        assert_match "1" [$rd read]
        assert_match "0" [$rd2 read]
        $rd close
        $rd2 close
    }
    """
    r.run("PFADD", "pause-hll", "test")
    r.run("client", "PAUSE", 100000, "WRITE")
    rd = ValkeyTestClient.create_from(r)
    rd.run("PFCOUNT", "pause-hll")
    wait_for_blocked_clients_count(1, 50, 100)
    rd2 = ValkeyTestClient.create_from(r)
    rd2.run("publish", "foo", "bar")
    wait_for_blocked_clients_count(2, 50, 100)
    r.run("client", "unpause")
    assert fnmatch(str(rd.run("read")), "1")
    assert fnmatch(str(rd2.run("read")), "0")
    rd.run("close")
    rd2.run("close")


def test_test_read_or_admin_multi_execs_are_not_blocked_by_pause_ro(r: ValkeyTestClient) -> None:
    """
    test "Test read/admin multi-execs are not blocked by pause RO" {
        r SET FOO BAR
        r client PAUSE 100000 WRITE
        set rr [valkey_client]
        assert_equal [$rr MULTI] "OK"
        assert_equal [$rr PING] "QUEUED"
        assert_equal [$rr GET FOO] "QUEUED"
        assert_match "PONG BAR" [$rr EXEC]
        assert_equal [s 0 blocked_clients] 0
        r client unpause
        $rr close
    }
    """
    r.run("SET", "FOO", "BAR")
    r.run("client", "PAUSE", 100000, "WRITE")
    rr = ValkeyTestClient.create_from(r)
    assert rr.run("MULTI") == "OK"
    assert rr.run("PING") == "QUEUED"
    assert rr.run("GET", "FOO") == "QUEUED"
    assert fnmatch(str(rr.run("EXEC")), "PONG BAR")
    assert s(0, "blocked_clients") == 0
    r.run("client", "unpause")
    rr.run("close")


def test_test_write_multi_execs_are_blocked_by_pause_ro(r: ValkeyTestClient) -> None:
    """
    test "Test write multi-execs are blocked by pause RO" {
        set rd [valkey_deferring_client]
        $rd MULTI
        assert_equal [$rd read] "OK"
        $rd SET FOO BAR
        assert_equal [$rd read] "QUEUED"
        r client PAUSE 60000 WRITE
        $rd EXEC
        wait_for_blocked_clients_count 1 50 100
        r client unpause
        assert_match "OK" [$rd read]
        $rd close
    }
    """
    rd = ValkeyTestClient.create_from(r)
    rd.run("MULTI")
    assert rd.run("read") == "OK"
    rd.run("SET", "FOO", "BAR")
    assert rd.run("read") == "QUEUED"
    r.run("client", "PAUSE", 60000, "WRITE")
    rd.run("EXEC")
    wait_for_blocked_clients_count(1, 50, 100)
    r.run("client", "unpause")
    assert fnmatch(str(rd.run("read")), "OK")
    rd.run("close")


def test_test_scripts_are_blocked_by_pause_ro(r: ValkeyTestClient) -> None:
    """
    test "Test scripts are blocked by pause RO" {
        r client PAUSE 60000 WRITE
        set rd [valkey_deferring_client]
        set rd2 [valkey_deferring_client]
        $rd EVAL "return 1" 0

        # test a script with a shebang and no flags for coverage
        $rd2 EVAL {#!lua
            return 1
        } 0

        wait_for_blocked_clients_count 2 50 100
        r client unpause
        assert_match "1" [$rd read]
        assert_match "1" [$rd2 read]
        $rd close
        $rd2 close
    }
    """
    r.run("client", "PAUSE", 60000, "WRITE")
    rd = ValkeyTestClient.create_from(r)
    rd2 = ValkeyTestClient.create_from(r)
    rd.run("EVAL", "return 1", 0)
    rd2.run("EVAL", "#!lua\n            return 1\n        ", 0)
    wait_for_blocked_clients_count(2, 50, 100)
    r.run("client", "unpause")
    assert fnmatch(str(rd.run("read")), "1")
    assert fnmatch(str(rd2.run("read")), "1")
    rd.run("close")
    rd2.run("close")


def test_test_ro_scripts_are_not_blocked_by_pause_ro(r: ValkeyTestClient) -> None:
    """
    test "Test RO scripts are not blocked by pause RO" {
        r set x y
        # create a function for later
        r FUNCTION load replace {#!lua name=f1
            server.register_function{
                function_name='f1',
                callback=function() return "hello" end,
                flags={'no-writes'}
            }
        }

        r client PAUSE 6000000 WRITE
        set rr [valkey_client]

        # test an eval that's for sure not in the script cache
        assert_equal [$rr EVAL {#!lua flags=no-writes
                return 'unique script'
            } 0
        ] "unique script"

        # for sanity, repeat that EVAL on a script that's already cached
        assert_equal [$rr EVAL {#!lua flags=no-writes
                return 'unique script'
            } 0
        ] "unique script"

        # test EVAL_RO on a unique script that's for sure not in the cache
        assert_equal [$rr EVAL_RO {
            return redis.call('GeT', 'x')..' unique script'
            } 1 x
        ] "y unique script"

        # test with evalsha
        set sha [$rr script load {#!lua flags=no-writes
                return 2
            }]
        assert_equal [$rr EVALSHA $sha 0] 2

        # test with function
        assert_equal [$rr fcall f1 0] hello

        r client unpause
        $rr close
    }
    """
    r.run("set", "x", "y")
    r.run(
        "FUNCTION",
        "load",
        "replace",
        "#!lua name=f1\n            server.register_function{\n                function_name='f1',\n                callback=function() return \"hello\" end,\n                flags={'no-writes'}\n            }\n        ",
    )
    r.run("client", "PAUSE", 6000000, "WRITE")
    rr = ValkeyTestClient.create_from(r)
    assert (
        rr.run("EVAL", "#!lua flags=no-writes                return 'unique script'            ", 0) == "unique script"
    )
    assert (
        rr.run("EVAL", "#!lua flags=no-writes                return 'unique script'            ", 0) == "unique script"
    )
    assert (
        rr.run("EVAL_RO", "            return redis.call('GeT', 'x')..' unique script'            ", 1, "x")
        == "y unique script"
    )
    sha = rr.run("script", "load", "#!lua flags=no-writes                return 2            ")
    assert rr.run("EVALSHA", sha, 0) == 2
    assert rr.run("fcall", "f1", 0) == "hello"
    r.run("client", "unpause")
    rr.run("close")


def test_test_read_only_scripts_in_multi_exec_are_not_blocked_by_pause_ro(r: ValkeyTestClient) -> None:
    """
    test "Test read-only scripts in multi-exec are not blocked by pause RO" {
        r SET FOO BAR
        r client PAUSE 100000 WRITE
        set rr [valkey_client]
        assert_equal [$rr MULTI] "OK"
        assert_equal [$rr EVAL {#!lua flags=no-writes
                return 12
            } 0
        ] QUEUED
        assert_equal [$rr EVAL {#!lua flags=no-writes
                return 13
            } 0
        ] QUEUED
        assert_match "12 13" [$rr EXEC]
        assert_equal [s 0 blocked_clients] 0
        r client unpause
        $rr close
    }
    """
    r.run("SET", "FOO", "BAR")
    r.run("client", "PAUSE", 100000, "WRITE")
    rr = ValkeyTestClient.create_from(r)
    assert rr.run("MULTI") == "OK"
    assert rr.run("EVAL", "#!lua flags=no-writes                return 12            ", 0) == "QUEUED"
    assert rr.run("EVAL", "#!lua flags=no-writes                return 13            ", 0) == "QUEUED"
    assert fnmatch(str(rr.run("EXEC")), "12 13")
    assert s(0, "blocked_clients") == 0
    r.run("client", "unpause")
    rr.run("close")


def test_test_write_scripts_in_multi_exec_are_blocked_by_pause_ro(r: ValkeyTestClient) -> None:
    """
    test "Test write scripts in multi-exec are blocked by pause RO" {
        set rd [valkey_deferring_client]
        set rd2 [valkey_deferring_client]

        # one with a shebang
        $rd MULTI
        assert_equal [$rd read] "OK"
        $rd EVAL {#!lua
                return 12
            } 0
        assert_equal [$rd read] "QUEUED"

        # one without a shebang
        $rd2 MULTI
        assert_equal [$rd2 read] "OK"
        $rd2 EVAL {#!lua
                return 13
            } 0
        assert_equal [$rd2 read] "QUEUED"

        r client PAUSE 60000 WRITE
        $rd EXEC
        $rd2 EXEC
        wait_for_blocked_clients_count 2 50 100
        r client unpause
        assert_match "12" [$rd read]
        assert_match "13" [$rd2 read]
        $rd close
        $rd2 close
    }
    """
    rd = ValkeyTestClient.create_from(r)
    rd2 = ValkeyTestClient.create_from(r)
    rd.run("MULTI")
    assert rd.run("read") == "OK"
    rd.run("EVAL", "#!lua\n                return 12\n            ", 0)
    assert rd.run("read") == "QUEUED"
    rd2.run("MULTI")
    assert rd2.run("read") == "OK"
    rd2.run("EVAL", "#!lua\n                return 13\n            ", 0)
    assert rd2.run("read") == "QUEUED"
    r.run("client", "PAUSE", 60000, "WRITE")
    rd.run("EXEC")
    rd2.run("EXEC")
    wait_for_blocked_clients_count(2, 50, 100)
    r.run("client", "unpause")
    assert fnmatch(str(rd.run("read")), "12")
    assert fnmatch(str(rd2.run("read")), "13")
    rd.run("close")
    rd2.run("close")


def test_test_may_replicate_commands_are_rejected_in_ro_scripts(r: ValkeyTestClient) -> None:
    """
    test "Test may-replicate commands are rejected in RO scripts" {
        # that's specifically important for CLIENT PAUSE WRITE
        assert_error {ERR Write commands are not allowed from read-only scripts. script:*} {
            r EVAL_RO "return redis.call('publish','ch','msg')" 0
        }
        assert_error {ERR Write commands are not allowed from read-only scripts. script:*} {
            r EVAL {#!lua flags=no-writes
                return redis.call('publish','ch','msg')
            } 0
        }
        # make sure that publish isn't blocked from a non-RO script
        assert_equal [r EVAL "return redis.call('publish','ch','msg')" 0] 0
    }
    """
    with pytest.raises(
        Exception, match="ERR\\ Write\\ commands\\ are\\ not\\ allowed\\ from\\ read\\-only\\ scripts\\.\\ script:.*"
    ):
        r.run("EVAL_RO", "return redis.call('publish','ch','msg')", 0)
    with pytest.raises(
        Exception, match="ERR\\ Write\\ commands\\ are\\ not\\ allowed\\ from\\ read\\-only\\ scripts\\.\\ script:.*"
    ):
        r.run("EVAL", "#!lua flags=no-writes\n                return redis.call('publish','ch','msg')\n            ", 0)
    assert r.run("EVAL", "return redis.call('publish','ch','msg')", 0) == 0


def test_test_multiple_clients_can_be_queued_up_and_unblocked(r: ValkeyTestClient) -> None:
    """
    test "Test multiple clients can be queued up and unblocked" {
        r client PAUSE 60000 WRITE
        set clients [list [valkey_deferring_client] [valkey_deferring_client] [valkey_deferring_client]]
        foreach client $clients {
            $client SET FOO BAR
        }

        wait_for_blocked_clients_count 3 50 100
        r client unpause
        foreach client $clients {
            assert_match "OK" [$client read]
            $client close
        }
    }
    """
    r.run("client", "PAUSE", 60000, "WRITE")
    clients = [ValkeyTestClient.create_from(r), ValkeyTestClient.create_from(r), ValkeyTestClient.create_from(r)]
    foreach("client", clients, "            $client SET FOO BAR\n        ")
    wait_for_blocked_clients_count(3, 50, 100)
    r.run("client", "unpause")
    foreach("client", clients, '            assert_match "OK" [$client read]\n            $client close\n        ')


def test_test_clients_with_syntax_errors_will_get_responses_immediately(r: ValkeyTestClient) -> None:
    """
    test "Test clients with syntax errors will get responses immediately" {
        r client PAUSE 100000 WRITE
        catch {r set FOO} err
        assert_match "ERR wrong number of arguments for 'set' command" $err
        r client unpause
    }
    """
    r.run("client", "PAUSE", 100000, "WRITE")
    err = None
    try:
        err = r.run("set", "FOO")
    except Exception as _catch_err:
        err = str(_catch_err)
    assert fnmatch(str(err), "ERR wrong number of arguments for 'set' command")
    r.run("client", "unpause")


def test_test_eviction_is_skipped_during_client_pause(r: ValkeyTestClient) -> None:
    """
    test "Test eviction is skipped during client pause" {
        r flushall
        set evicted_keys [s 0 evicted_keys]

        r multi
        r set foo{t} bar
        r config set maxmemory-policy allkeys-random
        r config set maxmemory 1
        r client PAUSE 50000 WRITE
        r exec

        # No keys should actually have been evicted.
        assert_match $evicted_keys [s 0 evicted_keys]

        # The previous config set triggers a time event, but due to the pause,
        # no eviction has been made. After the unpause, a eviction will happen.
        r client unpause
        wait_for_condition 1000 10 {
            [expr $evicted_keys + 1] eq [s 0 evicted_keys]
        } else {
            fail "Key is not evicted"
        }

        r config set maxmemory 0
        r config set maxmemory-policy noeviction
    }
    """
    r.run("flushall")
    evicted_keys = s(0, "evicted_keys")
    r.run("multi")
    r.run("set", "foo{t}", "bar")
    r.run("config", "set", "maxmemory-policy", "allkeys-random")
    r.run("config", "set", "maxmemory", 1)
    r.run("client", "PAUSE", 50000, "WRITE")
    r.run("exec")
    assert fnmatch(str(s(0, "evicted_keys")), str(evicted_keys))
    r.run("client", "unpause")
    wait_for_condition(
        1000, 10, lambda: expr(evicted_keys, "+", 1) == s(0, "evicted_keys"), lambda: fail("Key is not evicted")
    )
    r.run("config", "set", "maxmemory", 0)
    r.run("config", "set", "maxmemory-policy", "noeviction")


def test_test_both_active_and_passive_expires_are_skipped_during_client_pause(r: ValkeyTestClient) -> None:
    """
    test "Test both active and passive expires are skipped during client pause" {
        set expired_keys [s 0 expired_keys]
        r multi
        r set foo{t} bar{t} PX 10
        r set bar{t} foo{t} PX 10
        r client PAUSE 50000 WRITE
        r exec

        wait_for_condition 10 100 {
            [r get foo{t}] == {} && [r get bar{t}] == {}
        } else {
            fail "Keys were never logically expired"
        }

        # No keys should actually have been expired
        assert_match $expired_keys [s 0 expired_keys]

        r client unpause

        # Force the keys to expire
        r get foo{t}
        r get bar{t}

        # Now that clients have been unpaused, expires should go through
        assert_match [expr $expired_keys + 2] [s 0 expired_keys]
    }
    """
    expired_keys = s(0, "expired_keys")
    r.run("multi")
    r.run("set", "foo{t}", "bar{t}", "PX", 10)
    r.run("set", "bar{t}", "foo{t}", "PX", 10)
    r.run("client", "PAUSE", 50000, "WRITE")
    r.run("exec")
    wait_for_condition(
        10,
        100,
        lambda: (r.run("get", "foo{t}") == "") and (r.run("get", "bar{t}") == ""),
        lambda: fail("Keys were never logically expired"),
    )
    assert fnmatch(str(s(0, "expired_keys")), str(expired_keys))
    r.run("client", "unpause")
    r.run("get", "foo{t}")
    r.run("get", "bar{t}")
    assert fnmatch(str(s(0, "expired_keys")), str(expr(expired_keys, "+", 2)))


def test_test_that_client_pause_starts_at_the_end_of_a_transaction(r: ValkeyTestClient) -> None:
    """
    test "Test that client pause starts at the end of a transaction" {
        r MULTI
        r SET FOO1{t} BAR
        r client PAUSE 60000 WRITE
        r SET FOO2{t} BAR
        r exec

        set rd [valkey_deferring_client]
        $rd SET FOO3{t} BAR

        wait_for_blocked_clients_count 1 50 100

        assert_match "BAR" [r GET FOO1{t}]
        assert_match "BAR" [r GET FOO2{t}]
        assert_match "" [r GET FOO3{t}]

        r client unpause
        assert_match "OK" [$rd read]
        $rd close
    }
    """
    r.run("MULTI")
    r.run("SET", "FOO1{t}", "BAR")
    r.run("client", "PAUSE", 60000, "WRITE")
    r.run("SET", "FOO2{t}", "BAR")
    r.run("exec")
    rd = ValkeyTestClient.create_from(r)
    rd.run("SET", "FOO3{t}", "BAR")
    wait_for_blocked_clients_count(1, 50, 100)
    assert fnmatch(str(r.run("GET", "FOO1{t}")), "BAR")
    assert fnmatch(str(r.run("GET", "FOO2{t}")), "BAR")
    assert fnmatch(str(r.run("GET", "FOO3{t}")), "")
    r.run("client", "unpause")
    assert fnmatch(str(rd.run("read")), "OK")
    rd.run("close")


"""
start_server {tags {needs:repl external:skip}} {
    set master [srv -1 client]
    set master_host [srv -1 host]
    set master_port [srv -1 port]

    # Avoid PINGs
    $master config set repl-ping-replica-period 3600
    r replicaof $master_host $master_port

    wait_for_condition 50 100 {
        [s master_link_status] eq {up}
    } else {
        fail "Replication not started."
    }

    test "Test when replica paused, offset would not grow" {
        $master set foo bar
        set old_master_offset [status $master master_repl_offset]

        wait_for_condition 50 100 {
            [s slave_repl_offset] == [status $master master_repl_offset]
        } else {
            fail "Replication offset not matched."
        }

        r client pause 100000 write
        $master set foo2 bar2

        # Make sure replica received data from master
        wait_for_condition 50 100 {
            [s slave_read_repl_offset] == [status $master master_repl_offset]
        } else {
            fail "Replication not work."
        }

        # Replica would not apply the write command
        assert {[s slave_repl_offset] == $old_master_offset}
        r get foo2
    } {}

    test "Test replica offset would grow after unpause" {
        r client unpause
        wait_for_condition 50 100 {
            [s slave_repl_offset] == [status $master master_repl_offset]
        } else {
            fail "Replication not continue."
        }
        r get foo2
    } {bar2}
}
"""


def test_test_the_randomkey_command_will_not_cause_the_server_to_get_into_an_infinite_loop_during_the_client_pause_write(
    r: ValkeyTestClient,
) -> None:
    """
    test "Test the randomkey command will not cause the server to get into an infinite loop during the client pause write" {
        # first, clear the database to avoid interference from existing keys on the test results
        r flushall

        r multi
        # then set a key with expire time
        r set key value px 3

        # set pause-write model and wait key expired
        r client pause 10000 write
        r exec

        after 5

        wait_for_condition 50 100 {
            [r randomkey] == "key"
        } else {
            fail "execute randomkey failed, caused by the infinite loop"
        }

        r client unpause
        assert_equal [r randomkey] {}
    }
    """
    r.run("flushall")
    r.run("multi")
    r.run("set", "key", "value", "px", 3)
    r.run("client", "pause", 10000, "write")
    r.run("exec")
    time.sleep(5 / 1000)
    wait_for_condition(
        50,
        100,
        lambda: r.run("randomkey") == "key",
        lambda: fail("execute randomkey failed, caused by the infinite loop"),
    )
    r.run("client", "unpause")
    assert r.run("randomkey") == ""


def test_client_unblock_is_not_allow_to_unblock_client_blocked_by_client_pause(r: ValkeyTestClient) -> None:
    """
    test "CLIENT UNBLOCK is not allow to unblock client blocked by CLIENT PAUSE" {
        set rd1 [valkey_deferring_client]
        set rd2 [valkey_deferring_client]
        $rd1 client id
        $rd2 client id
        set client_id1 [$rd1 read]
        set client_id2 [$rd2 read]

        r del mylist
        r client pause 100000 write
        $rd1 blpop mylist 0
        $rd2 blpop mylist 0
        wait_for_blocked_clients_count 2 50 100

        # This used to trigger a panic.
        assert_equal 0 [r client unblock $client_id1 timeout]
        # THis used to return a UNBLOCKED error.
        assert_equal 0 [r client unblock $client_id2 error]

        # After the unpause, it must be able to unblock the client.
        r client unpause
        assert_equal 1 [r client unblock $client_id1 timeout]
        assert_equal 1 [r client unblock $client_id2 error]
        assert_equal {} [$rd1 read]
        assert_error "UNBLOCKED*" {$rd2 read}

        $rd1 close
        $rd2 close
    }
    """
    rd1 = ValkeyTestClient.create_from(r)
    rd2 = ValkeyTestClient.create_from(r)
    rd1.run("client", "id")
    rd2.run("client", "id")
    client_id1 = rd1.run("read")
    client_id2 = rd2.run("read")
    r.run("del", "mylist")
    r.run("client", "pause", 100000, "write")
    rd1.run("blpop", "mylist", 0)
    rd2.run("blpop", "mylist", 0)
    wait_for_blocked_clients_count(2, 50, 100)
    assert 0 == r.run("client", "unblock", client_id1, "timeout")
    assert 0 == r.run("client", "unblock", client_id2, "error")
    r.run("client", "unpause")
    assert 1 == r.run("client", "unblock", client_id1, "timeout")
    assert 1 == r.run("client", "unblock", client_id2, "error")
    assert "" == rd1.run("read")
    assert_error("UNBLOCKED*", "$rd2 read")
    rd1.run("close")
    rd2.run("close")


"""
r client unpause
"""


"""
start_cluster 1 1 {tags {"external:skip cluster pause network"}} {
    test "Test check paused info during the cluster failover in info clients" {
        set CLUSTER_PACKET_TYPE_NONE -1
        set CLUSTER_PACKET_TYPE_FAILOVER_AUTH_ACK 6

        assert_equal [s 0 paused_reason] "none"
        assert_equal [s 0 paused_actions] "none"
        assert_equal [s 0 paused_timeout_milliseconds] 0

        # Let replica drop FAILOVER_AUTH_ACK so that the election won't
        # get the enough votes and the election will time out.
        R 1 debug drop-cluster-packet-filter $CLUSTER_PACKET_TYPE_FAILOVER_AUTH_ACK
        R 1 cluster failover
        wait_for_log_messages 0 {"*Manual failover requested by replica*"} 0 10 1000

        # Failover will definitely time out, so on the primary side we will pause for
        # `CLUSTER_MF_TIMEOUT * CLUSTER_MF_PAUSE_MULT` this long.
        assert_equal [s 0 paused_reason] "failover_in_progress"
        assert_equal [s 0 paused_actions] "write"
        assert_morethan [s 0 paused_timeout_milliseconds] 0

        # Let the failover happen, make sure we will clear the paused state.
        R 1 cluster failover takeover
        wait_for_condition 1000 50 {
            [s 0 role] eq {slave} &&
            [s -1 role] eq {master}
        } else {
            fail "The failover does not happen"
        }
        assert_equal [s 0 paused_reason] "none"
        assert_equal [s 0 paused_actions] "none"
        assert_equal [s 0 paused_timeout_milliseconds] 0
    }
}
"""


# --- stubs for unimplemented TCL helpers ---


def assert_error(*args):
    raise NotImplementedError("assert_error")


def assert_lessthan(*args):
    raise NotImplementedError("assert_lessthan")


def clock(*args):
    raise NotImplementedError("clock")


def expr(*args):
    raise NotImplementedError("expr")


def fail(*args):
    raise NotImplementedError("fail")


def foreach(*args):
    raise NotImplementedError("foreach")


def s(*args):
    raise NotImplementedError("s")


def wait_for_blocked_clients_count(*args):
    raise NotImplementedError("wait_for_blocked_clients_count")


def wait_for_condition(*args):
    raise NotImplementedError("wait_for_condition")
