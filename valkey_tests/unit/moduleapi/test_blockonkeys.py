# ruff: noqa: ANN002, ANN201

import pytest

from tests.valkey_test_client import ValkeyTestClient

"""
set testmodule file normalize tests/modules/blockonkeys.so
"""

pytestmark = [pytest.mark.modules]


"""
r module load testmodule
"""


def test_module_client_blocked_on_keys_circular_bpoppush(r: ValkeyTestClient) -> None:
    """
    test "Module client blocked on keys: Circular BPOPPUSH" {
        set rd1 [valkey_deferring_client]
        set rd2 [valkey_deferring_client]

        r del src dst

        $rd1 fsl.bpoppush src dst 0
        wait_for_blocked_clients_count 1

        $rd2 fsl.bpoppush dst src 0
        wait_for_blocked_clients_count 2

        r fsl.push src 42
        wait_for_blocked_clients_count 0

        assert_equal {42} [r fsl.getall src]
        assert_equal {} [r fsl.getall dst]
    }
    """
    rd1 = valkey_deferring_client()
    rd2 = valkey_deferring_client()
    r.run("del", "src", "dst")
    rd1.run("fsl.bpoppush", "src", "dst", 0)
    wait_for_blocked_clients_count(1)
    rd2.run("fsl.bpoppush", "dst", "src", 0)
    wait_for_blocked_clients_count(2)
    r.run("fsl.push", "src", 42)
    wait_for_blocked_clients_count(0)
    assert "42" == r.run("fsl.getall", "src")
    assert "" == r.run("fsl.getall", "dst")


def test_module_client_blocked_on_keys_self_referential_bpoppush(r: ValkeyTestClient) -> None:
    """
    test "Module client blocked on keys: Self-referential BPOPPUSH" {
        set rd1 [valkey_deferring_client]

        r del src

        $rd1 fsl.bpoppush src src 0
        wait_for_blocked_clients_count 1
        r fsl.push src 42

        assert_equal {42} [r fsl.getall src]
    }
    """
    rd1 = valkey_deferring_client()
    r.run("del", "src")
    rd1.run("fsl.bpoppush", "src", "src", 0)
    wait_for_blocked_clients_count(1)
    r.run("fsl.push", "src", 42)
    assert "42" == r.run("fsl.getall", "src")


def test_module_client_blocked_on_keys_bpoppush_unblocked_by_timer(r: ValkeyTestClient) -> None:
    """
    test "Module client blocked on keys: BPOPPUSH unblocked by timer" {
        set rd1 [valkey_deferring_client]

        r del src dst

        set repl [attach_to_replication_stream]

        $rd1 fsl.bpoppush src dst 0
        wait_for_blocked_clients_count 1

        r fsl.pushtimer src 9000 10
        wait_for_blocked_clients_count 0

        assert_equal {9000} [r fsl.getall dst]
        assert_equal {} [r fsl.getall src]

        assert_replication_stream $repl {
            {select *}
            {fsl.push src 9000}
            {fsl.bpoppush src dst 0}
        }

        close_replication_stream $repl
    } {} {needs:repl}
    """
    rd1 = valkey_deferring_client()
    r.run("del", "src", "dst")
    repl = attach_to_replication_stream()
    rd1.run("fsl.bpoppush", "src", "dst", 0)
    wait_for_blocked_clients_count(1)
    r.run("fsl.pushtimer", "src", 9000, 10)
    wait_for_blocked_clients_count(0)
    assert "9000" == r.run("fsl.getall", "dst")
    assert "" == r.run("fsl.getall", "src")
    assert_replication_stream(
        repl, "            {select *}\n            {fsl.push src 9000}\n            {fsl.bpoppush src dst 0}\n        "
    )
    close_replication_stream(repl)


def test_module_client_blocked_on_keys_no_metadata_no_block(r: ValkeyTestClient) -> None:
    """
    test {Module client blocked on keys (no metadata): No block} {
        r del k
        r fsl.push k 33
        r fsl.push k 34
        r fsl.bpop k 0
    } {34}
    """
    r.run("del", "k")
    r.run("fsl.push", "k", 33)
    r.run("fsl.push", "k", 34)
    assert r.run("fsl.bpop", "k", 0) == "34"


def test_module_client_blocked_on_keys_no_metadata_timeout(r: ValkeyTestClient) -> None:
    """
    test {Module client blocked on keys (no metadata): Timeout} {
        r del k
        set rd [valkey_deferring_client]
        $rd fsl.bpop k 1
        assert_equal {Request timedout} [$rd read]
    }
    """
    r.run("del", "k")
    rd = valkey_deferring_client()
    rd.run("fsl.bpop", "k", 1)
    assert "Request timedout" == rd.run("read")


def test_module_client_blocked_on_keys_no_metadata_blocked(r: ValkeyTestClient) -> None:
    """
    test {Module client blocked on keys (no metadata): Blocked} {
        r del k
        set rd [valkey_deferring_client]
        $rd fsl.bpop k 0
        wait_for_blocked_clients_count 1
        r fsl.push k 34
        assert_equal {34} [$rd read]
    }
    """
    r.run("del", "k")
    rd = valkey_deferring_client()
    rd.run("fsl.bpop", "k", 0)
    wait_for_blocked_clients_count(1)
    r.run("fsl.push", "k", 34)
    assert "34" == rd.run("read")


def test_module_client_blocked_on_keys_with_metadata_no_block(r: ValkeyTestClient) -> None:
    """
    test {Module client blocked on keys (with metadata): No block} {
        r del k
        r fsl.push k 34
        r fsl.bpopgt k 30 0
    } {34}
    """
    r.run("del", "k")
    r.run("fsl.push", "k", 34)
    assert r.run("fsl.bpopgt", "k", 30, 0) == "34"


def test_module_client_blocked_on_keys_with_metadata_timeout(r: ValkeyTestClient) -> None:
    """
    test {Module client blocked on keys (with metadata): Timeout} {
        r del k
        set rd [valkey_deferring_client]
        $rd client id
        set cid [$rd read]
        r fsl.push k 33
        $rd fsl.bpopgt k 35 1
        assert_equal {Request timedout} [$rd read]
        r client kill id $cid ;# try to smoke-out client-related memory leak
    }
    """
    r.run("del", "k")
    rd = valkey_deferring_client()
    rd.run("client", "id")
    cid = rd.run("read")
    r.run("fsl.push", "k", 33)
    rd.run("fsl.bpopgt", "k", 35, 1)
    assert "Request timedout" == rd.run("read")
    r.run("client", "kill", "id", cid)


def test_module_client_blocked_on_keys_with_metadata_blocked_case_1(r: ValkeyTestClient) -> None:
    """
    test {Module client blocked on keys (with metadata): Blocked, case 1} {
        r del k
        set rd [valkey_deferring_client]
        $rd client id
        set cid [$rd read]
        r fsl.push k 33
        $rd fsl.bpopgt k 33 0
        wait_for_blocked_clients_count 1
        r fsl.push k 34
        assert_equal {34} [$rd read]
        r client kill id $cid ;# try to smoke-out client-related memory leak
    }
    """
    r.run("del", "k")
    rd = valkey_deferring_client()
    rd.run("client", "id")
    cid = rd.run("read")
    r.run("fsl.push", "k", 33)
    rd.run("fsl.bpopgt", "k", 33, 0)
    wait_for_blocked_clients_count(1)
    r.run("fsl.push", "k", 34)
    assert "34" == rd.run("read")
    r.run("client", "kill", "id", cid)


def test_module_client_blocked_on_keys_with_metadata_blocked_case_2(r: ValkeyTestClient) -> None:
    """
    test {Module client blocked on keys (with metadata): Blocked, case 2} {
        r del k
        r fsl.push k 32
        set rd [valkey_deferring_client]
        $rd fsl.bpopgt k 35 0
        wait_for_blocked_clients_count 1
        r fsl.push k 33
        r fsl.push k 34
        r fsl.push k 35
        r fsl.push k 36
        assert_equal {36} [$rd read]
    }
    """
    r.run("del", "k")
    r.run("fsl.push", "k", 32)
    rd = valkey_deferring_client()
    rd.run("fsl.bpopgt", "k", 35, 0)
    wait_for_blocked_clients_count(1)
    r.run("fsl.push", "k", 33)
    r.run("fsl.push", "k", 34)
    r.run("fsl.push", "k", 35)
    r.run("fsl.push", "k", 36)
    assert "36" == rd.run("read")


def test_module_client_blocked_on_keys_with_metadata_blocked_del(r: ValkeyTestClient) -> None:
    """
    test {Module client blocked on keys (with metadata): Blocked, DEL} {
        r del k
        r fsl.push k 32
        set rd [valkey_deferring_client]
        $rd fsl.bpopgt k 35 0
        wait_for_blocked_clients_count 1
        r del k
        assert_error {*UNBLOCKED key no longer exists*} {$rd read}
    }
    """
    r.run("del", "k")
    r.run("fsl.push", "k", 32)
    rd = valkey_deferring_client()
    rd.run("fsl.bpopgt", "k", 35, 0)
    wait_for_blocked_clients_count(1)
    r.run("del", "k")
    assert_error("*UNBLOCKED key no longer exists*", "$rd read")


def test_module_client_blocked_on_keys_with_metadata_blocked_flushall(r: ValkeyTestClient) -> None:
    """
    test {Module client blocked on keys (with metadata): Blocked, FLUSHALL} {
        r del k
        r fsl.push k 32
        set rd [valkey_deferring_client]
        $rd fsl.bpopgt k 35 0
        wait_for_blocked_clients_count 1
        r flushall
        assert_error {*UNBLOCKED key no longer exists*} {$rd read}
    }
    """
    r.run("del", "k")
    r.run("fsl.push", "k", 32)
    rd = valkey_deferring_client()
    rd.run("fsl.bpopgt", "k", 35, 0)
    wait_for_blocked_clients_count(1)
    r.run("flushall")
    assert_error("*UNBLOCKED key no longer exists*", "$rd read")


def test_module_client_blocked_on_keys_with_metadata_blocked_swapdb_no_key(r: ValkeyTestClient) -> None:
    """
    test {Module client blocked on keys (with metadata): Blocked, SWAPDB, no key} {
        r select 9
        r del k
        r fsl.push k 32
        set rd [valkey_deferring_client]
        $rd fsl.bpopgt k 35 0
        wait_for_blocked_clients_count 1
        r swapdb 0 9
        assert_error {*UNBLOCKED key no longer exists*} {$rd read}
    }
    """
    r.run("select", 9)
    r.run("del", "k")
    r.run("fsl.push", "k", 32)
    rd = valkey_deferring_client()
    rd.run("fsl.bpopgt", "k", 35, 0)
    wait_for_blocked_clients_count(1)
    r.run("swapdb", 0, 9)
    assert_error("*UNBLOCKED key no longer exists*", "$rd read")


def test_module_client_blocked_on_keys_with_metadata_blocked_swapdb_key_exists_case_1(r: ValkeyTestClient) -> None:
    """
    test {Module client blocked on keys (with metadata): Blocked, SWAPDB, key exists, case 1} {
        ;# Key exists on other db, but wrong type
        r flushall
        r select 9
        r fsl.push k 32
        r select 0
        r lpush k 38
        r select 9
        set rd [valkey_deferring_client]
        $rd fsl.bpopgt k 35 0
        wait_for_blocked_clients_count 1
        r swapdb 0 9
        assert_error {*UNBLOCKED key no longer exists*} {$rd read}
        r select 9
    }
    """
    r.run("flushall")
    r.run("select", 9)
    r.run("fsl.push", "k", 32)
    r.run("select", 0)
    r.run("lpush", "k", 38)
    r.run("select", 9)
    rd = valkey_deferring_client()
    rd.run("fsl.bpopgt", "k", 35, 0)
    wait_for_blocked_clients_count(1)
    r.run("swapdb", 0, 9)
    assert_error("*UNBLOCKED key no longer exists*", "$rd read")
    r.run("select", 9)


def test_module_client_blocked_on_keys_with_metadata_blocked_swapdb_key_exists_case_2(r: ValkeyTestClient) -> None:
    """
    test {Module client blocked on keys (with metadata): Blocked, SWAPDB, key exists, case 2} {
        ;# Key exists on other db, with the right type, but the value doesn't allow to unblock
        r flushall
        r select 9
        r fsl.push k 32
        r select 0
        r fsl.push k 34
        r select 9
        set rd [valkey_deferring_client]
        $rd fsl.bpopgt k 35 0
        wait_for_blocked_clients_count 1
        r swapdb 0 9
        assert_equal {1} [s 0 blocked_clients]
        r fsl.push k 38
        assert_equal {38} [$rd read]
        r select 9
    }
    """
    r.run("flushall")
    r.run("select", 9)
    r.run("fsl.push", "k", 32)
    r.run("select", 0)
    r.run("fsl.push", "k", 34)
    r.run("select", 9)
    rd = valkey_deferring_client()
    rd.run("fsl.bpopgt", "k", 35, 0)
    wait_for_blocked_clients_count(1)
    r.run("swapdb", 0, 9)
    assert "1" == s(0, "blocked_clients")
    r.run("fsl.push", "k", 38)
    assert "38" == rd.run("read")
    r.run("select", 9)


def test_module_client_blocked_on_keys_with_metadata_blocked_swapdb_key_exists_case_3(r: ValkeyTestClient) -> None:
    """
    test {Module client blocked on keys (with metadata): Blocked, SWAPDB, key exists, case 3} {
        ;# Key exists on other db, with the right type, the value allows to unblock
        r flushall
        r select 9
        r fsl.push k 32
        r select 0
        r fsl.push k 38
        r select 9
        set rd [valkey_deferring_client]
        $rd fsl.bpopgt k 35 0
        wait_for_blocked_clients_count 1
        r swapdb 0 9
        assert_equal {38} [$rd read]
        r select 9
    }
    """
    r.run("flushall")
    r.run("select", 9)
    r.run("fsl.push", "k", 32)
    r.run("select", 0)
    r.run("fsl.push", "k", 38)
    r.run("select", 9)
    rd = valkey_deferring_client()
    rd.run("fsl.bpopgt", "k", 35, 0)
    wait_for_blocked_clients_count(1)
    r.run("swapdb", 0, 9)
    assert "38" == rd.run("read")
    r.run("select", 9)


def test_module_client_blocked_on_keys_with_metadata_blocked_client_kill(r: ValkeyTestClient) -> None:
    """
    test {Module client blocked on keys (with metadata): Blocked, CLIENT KILL} {
        r del k
        r fsl.push k 32
        set rd [valkey_deferring_client]
        $rd client id
        set cid [$rd read]
        $rd fsl.bpopgt k 35 0
        wait_for_blocked_clients_count 1
        r client kill id $cid ;# try to smoke-out client-related memory leak
    }
    """
    r.run("del", "k")
    r.run("fsl.push", "k", 32)
    rd = valkey_deferring_client()
    rd.run("client", "id")
    cid = rd.run("read")
    rd.run("fsl.bpopgt", "k", 35, 0)
    wait_for_blocked_clients_count(1)
    r.run("client", "kill", "id", cid)


def test_module_client_blocked_on_keys_with_metadata_blocked_client_unblock_timeout(r: ValkeyTestClient) -> None:
    """
    test {Module client blocked on keys (with metadata): Blocked, CLIENT UNBLOCK TIMEOUT} {
        r del k
        r fsl.push k 32
        set rd [valkey_deferring_client]
        $rd client id
        set cid [$rd read]
        $rd fsl.bpopgt k 35 0
        wait_for_blocked_clients_count 1
        r client unblock $cid timeout ;# try to smoke-out client-related memory leak
        assert_equal {Request timedout} [$rd read]
    }
    """
    r.run("del", "k")
    r.run("fsl.push", "k", 32)
    rd = valkey_deferring_client()
    rd.run("client", "id")
    cid = rd.run("read")
    rd.run("fsl.bpopgt", "k", 35, 0)
    wait_for_blocked_clients_count(1)
    r.run("client", "unblock", cid, "timeout")
    assert "Request timedout" == rd.run("read")


def test_module_client_blocked_on_keys_with_metadata_blocked_client_unblock_error(r: ValkeyTestClient) -> None:
    """
    test {Module client blocked on keys (with metadata): Blocked, CLIENT UNBLOCK ERROR} {
        r del k
        r fsl.push k 32
        set rd [valkey_deferring_client]
        $rd client id
        set cid [$rd read]
        $rd fsl.bpopgt k 35 0
        wait_for_blocked_clients_count 1
        r client unblock $cid error ;# try to smoke-out client-related memory leak
        assert_error "*unblocked*" {$rd read}
    }
    """
    r.run("del", "k")
    r.run("fsl.push", "k", 32)
    rd = valkey_deferring_client()
    rd.run("client", "id")
    cid = rd.run("read")
    rd.run("fsl.bpopgt", "k", 35, 0)
    wait_for_blocked_clients_count(1)
    r.run("client", "unblock", cid, "error")
    assert_error("*unblocked*", "$rd read")


def test_module_client_blocked_on_keys_no_timeout_cb_client_unblock_timeout(r: ValkeyTestClient) -> None:
    """
    test {Module client blocked on keys, no timeout CB, CLIENT UNBLOCK TIMEOUT} {
        r del k
        set rd [valkey_deferring_client]
        $rd client id
        set cid [$rd read]
        $rd fsl.bpop k 0 NO_TO_CB
        wait_for_blocked_clients_count 1
        assert_equal [r client unblock $cid timeout] {0}
        $rd close
    }
    """
    r.run("del", "k")
    rd = valkey_deferring_client()
    rd.run("client", "id")
    cid = rd.run("read")
    rd.run("fsl.bpop", "k", 0, "NO_TO_CB")
    wait_for_blocked_clients_count(1)
    assert r.run("client", "unblock", cid, "timeout") == "0"
    rd.run("close")


def test_module_client_blocked_on_keys_no_timeout_cb_client_unblock_error(r: ValkeyTestClient) -> None:
    """
    test {Module client blocked on keys, no timeout CB, CLIENT UNBLOCK ERROR} {
        r del k
        set rd [valkey_deferring_client]
        $rd client id
        set cid [$rd read]
        $rd fsl.bpop k 0 NO_TO_CB
        wait_for_blocked_clients_count 1
        assert_equal [r client unblock $cid error] {0}
        $rd close
    }
    """
    r.run("del", "k")
    rd = valkey_deferring_client()
    rd.run("client", "id")
    cid = rd.run("read")
    rd.run("fsl.bpop", "k", 0, "NO_TO_CB")
    wait_for_blocked_clients_count(1)
    assert r.run("client", "unblock", cid, "error") == "0"
    rd.run("close")


def test_module_client_re_blocked_on_keys_after_woke_up_on_wrong_type(r: ValkeyTestClient) -> None:
    """
    test {Module client re-blocked on keys after woke up on wrong type} {
        r del k
        set rd [valkey_deferring_client]
        $rd fsl.bpop k 0
        wait_for_blocked_clients_count 1
        r lpush k 12
        r lpush k 13
        r lpush k 14
        r del k
        r fsl.push k 34
        assert_equal {34} [$rd read]
        assert_equal {1} [r get fsl_wrong_type] ;# first lpush caused one wrong-type wake-up
    }
    """
    r.run("del", "k")
    rd = valkey_deferring_client()
    rd.run("fsl.bpop", "k", 0)
    wait_for_blocked_clients_count(1)
    r.run("lpush", "k", 12)
    r.run("lpush", "k", 13)
    r.run("lpush", "k", 14)
    r.run("del", "k")
    r.run("fsl.push", "k", 34)
    assert "34" == rd.run("read")
    assert "1" == r.run("get", "fsl_wrong_type")


def test_module_client_blocked_on_keys_woken_up_by_lpush(r: ValkeyTestClient) -> None:
    """
    test {Module client blocked on keys woken up by LPUSH} {
        r del k
        set rd [valkey_deferring_client]
        $rd blockonkeys.popall k
        wait_for_blocked_clients_count 1
        r lpush k 42 squirrel banana
        assert_equal {banana squirrel 42} [$rd read]
        $rd close
    }
    """
    r.run("del", "k")
    rd = valkey_deferring_client()
    rd.run("blockonkeys.popall", "k")
    wait_for_blocked_clients_count(1)
    r.run("lpush", "k", 42, "squirrel", "banana")
    assert "banana squirrel 42" == rd.run("read")
    rd.run("close")


def test_module_client_unblocks_blpop(r: ValkeyTestClient) -> None:
    """
    test {Module client unblocks BLPOP} {
        r del k
        set rd [valkey_deferring_client]
        $rd blpop k 3
        wait_for_blocked_clients_count 1
        r blockonkeys.lpush k 42
        assert_equal {k 42} [$rd read]
        $rd close
    }
    """
    r.run("del", "k")
    rd = valkey_deferring_client()
    rd.run("blpop", "k", 3)
    wait_for_blocked_clients_count(1)
    r.run("blockonkeys.lpush", "k", 42)
    assert "k 42" == rd.run("read")
    rd.run("close")


def test_module_unblocks_module_blocked_on_non_empty_list(r: ValkeyTestClient) -> None:
    """
    test {Module unblocks module blocked on non-empty list} {
        r del k
        r lpush k aa
        # Module client blocks to pop 5 elements from list
        set rd [valkey_deferring_client]
        $rd blockonkeys.blpopn k 5
        wait_for_blocked_clients_count 1
        # Check that RM_SignalKeyAsReady() can wake up BLPOPN
        r blockonkeys.lpush_unblock k bb cc ;# Not enough elements for BLPOPN
        r lpush k dd ee ff                  ;# Doesn't unblock module
        r blockonkeys.lpush_unblock k gg    ;# Unblocks module
        assert_equal {gg ff ee dd cc} [$rd read]
        $rd close
    }
    """
    r.run("del", "k")
    r.run("lpush", "k", "aa")
    rd = valkey_deferring_client()
    rd.run("blockonkeys.blpopn", "k", 5)
    wait_for_blocked_clients_count(1)
    r.run("blockonkeys.lpush_unblock", "k", "bb", "cc")
    r.run("lpush", "k", "dd", "ee", "ff")
    r.run("blockonkeys.lpush_unblock", "k", "gg")
    assert "gg ff ee dd cc" == rd.run("read")
    rd.run("close")


def test_module_explicit_unblock_when_blocked_on_keys(r: ValkeyTestClient) -> None:
    """
    test {Module explicit unblock when blocked on keys} {
        r del k
        r set somekey someval
        # Module client blocks to pop 5 elements from list
        set rd [valkey_deferring_client]
        $rd blockonkeys.blpopn_or_unblock k 5 0
        wait_for_blocked_clients_count 1
        # will now cause the module to trigger pop but instead will unblock the client from the reply_callback
        r lpush k dd
        # we should still get unblocked as the command should not reprocess
        wait_for_blocked_clients_count 0
        assert_equal {Action aborted} [$rd read]
        $rd get somekey
        assert_equal {someval} [$rd read]
        $rd close
    }
    """
    r.run("del", "k")
    r.run("set", "somekey", "someval")
    rd = valkey_deferring_client()
    rd.run("blockonkeys.blpopn_or_unblock", "k", 5, 0)
    wait_for_blocked_clients_count(1)
    r.run("lpush", "k", "dd")
    wait_for_blocked_clients_count(0)
    assert "Action aborted" == rd.run("read")
    rd.run("get", "somekey")
    assert "someval" == rd.run("read")
    rd.run("close")


"""
set master srv 0 client
"""


"""
set master_host srv 0 host
"""


"""
set master_port srv 0 port
"""


"""
start_server list overrides [list loadmodule "$testmodule"] {
    set replica [srv 0 client]
    set replica_host [srv 0 host]
    set replica_port [srv 0 port]

    # Start the replication process...
    $replica replicaof $master_host $master_port
    wait_for_sync $replica

    test {WAIT command on module blocked client on keys} {
        set rd [valkey_deferring_client -1]
        $rd set x y
        $rd read

        pause_process [srv 0 pid]

        $master del k
        $rd fsl.bpop k 0
        wait_for_blocked_client -1
        $master fsl.push k 34
        $master fsl.push k 35
        assert_equal {34} [$rd read]

        assert_equal [$master wait 1 1000] 0
        resume_process [srv 0 pid]
        assert_equal [$master wait 1 1000] 1
        $rd close
        assert_equal {35} [$replica fsl.getall k]
    }
}
"""


# --- stubs for unimplemented TCL helpers ---


def assert_error(*args):
    raise NotImplementedError("assert_error")


def assert_replication_stream(*args):
    raise NotImplementedError("assert_replication_stream")


def attach_to_replication_stream(*args):
    raise NotImplementedError("attach_to_replication_stream")


def close_replication_stream(*args):
    raise NotImplementedError("close_replication_stream")


def s(*args):
    raise NotImplementedError("s")


def valkey_deferring_client(*args):
    raise NotImplementedError("valkey_deferring_client")


def wait_for_blocked_clients_count(*args):
    raise NotImplementedError("wait_for_blocked_clients_count")
