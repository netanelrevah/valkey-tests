# ruff: noqa: F841, ANN002, ANN201
import time

import pytest

from tests.valkey_test_client import ValkeyTestClient

"""
set testmodule file normalize tests/modules/block_keyspace_notification.so
"""

pytestmark = [pytest.mark.modules]


"""
r module load testmodule
"""


def test_blocking_keyspace_notification_one(r: ValkeyTestClient) -> None:
    """
    test {Blocking keyspace notification one} {
        wait_for_blocked_clients_count 0
        r b_keyspace.clear
        assert_equal "1" [r hset a b c]
        assert_equal "{event hset key a}" [r b_keyspace.events]
    }
    """
    wait_for_blocked_clients_count(0)
    r.run("b_keyspace.clear")
    assert "1" == r.run("hset", "a", "b", "c")
    assert "{event hset key a}" == r.run("b_keyspace.events")


def test_blocking_keyspace_notification_two(r: ValkeyTestClient) -> None:
    """
    test {Blocking keyspace notification two} {
        wait_for_blocked_clients_count 0
        r b_keyspace.clear
        set rd1 [valkey_deferring_client]
        $rd1 hset b c d
        after 500
        set rd2 [valkey_deferring_client]
        $rd2 hset c d e
        wait_for_blocked_clients_count 2
        assert_equal "" [r b_keyspace.events]
        wait_for_blocked_clients_count 1
        assert_equal "{event hset key b}" [r b_keyspace.events]
        wait_for_blocked_clients_count 0
        assert_equal "{event hset key b} {event hset key c}" [r b_keyspace.events]
    }
    """
    wait_for_blocked_clients_count(0)
    r.run("b_keyspace.clear")
    rd1 = valkey_deferring_client()
    rd1.run("hset", "b", "c", "d")
    time.sleep(500 / 1000)
    rd2 = valkey_deferring_client()
    rd2.run("hset", "c", "d", "e")
    wait_for_blocked_clients_count(2)
    assert "" == r.run("b_keyspace.events")
    wait_for_blocked_clients_count(1)
    assert "{event hset key b}" == r.run("b_keyspace.events")
    wait_for_blocked_clients_count(0)
    assert "{event hset key b} {event hset key c}" == r.run("b_keyspace.events")


def test_blocking_keyspace_notification_with_pipelining_hset_after_hget(r: ValkeyTestClient) -> None:
    """
    test {Blocking keyspace notification with pipelining hset after hget} {
        wait_for_blocked_clients_count 0
        r b_keyspace.clear
        set rd1 [valkey_deferring_client]
        $rd1 hset key_10 field_10 value_10
        wait_for_blocked_clients_count 0
        assert_equal "1" [$rd1 read]
        pause_process [srv 0 pid]
        # Queue up three commands
        $rd1 hget key_10 field_10
        $rd1 hset key_10 value_10 ss
        $rd1 hget key_10 field_10
        set start [clock milliseconds]; # Record time before unblocking
        resume_process [srv 0 pid]
        assert_equal "value_10" [$rd1 read]
        set first_hget [expr [clock milliseconds] - $start];
        assert_equal "1" [$rd1 read]
        set first_hset [expr [clock milliseconds] - $start];
        assert_equal "value_10" [$rd1 read]
        set second_hget [expr [clock milliseconds] - $start];
        assert {[expr {$first_hget * 10 < $first_hset}]}
        assert {[expr {$second_hget - $first_hset <= 50}]}
        wait_for_blocked_clients_count 0
    }
    """
    wait_for_blocked_clients_count(0)
    r.run("b_keyspace.clear")
    rd1 = valkey_deferring_client()
    rd1.run("hset", "key_10", "field_10", "value_10")
    wait_for_blocked_clients_count(0)
    assert "1" == rd1.run("read")
    pause_process(srv(0, "pid"))
    rd1.run("hget", "key_10", "field_10")
    rd1.run("hset", "key_10", "value_10", "ss")
    rd1.run("hget", "key_10", "field_10")
    start = clock("milliseconds")
    resume_process(srv(0, "pid"))
    assert "value_10" == rd1.run("read")
    first_hget = expr(clock("milliseconds"), "-", start)
    assert "1" == rd1.run("read")
    first_hset = expr(clock("milliseconds"), "-", start)
    assert "value_10" == rd1.run("read")
    second_hget = expr(clock("milliseconds"), "-", start)
    assert expr("$first_hget * 10 < $first_hset")
    assert expr("$second_hget - $first_hset <= 50")
    wait_for_blocked_clients_count(0)


def test_blocking_keyspace_notification_with_pipelining_hget_after_hset(r: ValkeyTestClient) -> None:
    """
    test {Blocking keyspace notification with pipelining hget after hset} {
        wait_for_blocked_clients_count 0
        r b_keyspace.clear
        set rd1 [valkey_deferring_client]
        pause_process [srv 0 pid]
        $rd1 hset key_2 field_1 value_1
        $rd1 hget key_2 field_1
        resume_process [srv 0 pid]
        wait_for_blocked_clients_count 1
        assert_equal "" [r b_keyspace.events]
        wait_for_blocked_clients_count 0
        assert_equal "{event hset key key_2}" [r b_keyspace.events]
        assert_equal "1" [$rd1 read]
        assert_equal "value_1" [$rd1 read]
    }
    """
    wait_for_blocked_clients_count(0)
    r.run("b_keyspace.clear")
    rd1 = valkey_deferring_client()
    pause_process(srv(0, "pid"))
    rd1.run("hset", "key_2", "field_1", "value_1")
    rd1.run("hget", "key_2", "field_1")
    resume_process(srv(0, "pid"))
    wait_for_blocked_clients_count(1)
    assert "" == r.run("b_keyspace.events")
    wait_for_blocked_clients_count(0)
    assert "{event hset key key_2}" == r.run("b_keyspace.events")
    assert "1" == rd1.run("read")
    assert "value_1" == rd1.run("read")


def test_blocking_keyspace_notif_during_multi(r: ValkeyTestClient) -> None:
    """
    test {Blocking keyspace notif during multi} {
        wait_for_blocked_clients_count 0
        r b_keyspace.clear
        r multi
        r hset d e f
        r hset e f g
        assert_equal "1 1" [r exec]
        # Nothing should be blocked inside the transaction
        assert_equal [s 0 blocked_clients] 0
        assert_equal [r b_keyspace.events] ""
        # In the background, the work should still occur
        wait_for_condition 1000 50 {
            [string match "{event hset key *} {event hset key *}" [set latest [r b_keyspace.events]]]
        } else {
            fail "Keyspace event not propagated within 5 seconds"
        }
    }
    """
    wait_for_blocked_clients_count(0)
    r.run("b_keyspace.clear")
    r.run("multi")
    r.run("hset", "d", "e", "f")
    r.run("hset", "e", "f", "g")
    assert "1 1" == r.run("exec")
    assert s(0, "blocked_clients") == 0
    assert r.run("b_keyspace.events") == ""
    wait_for_condition(
        1000,
        50,
        '            [string match "{event hset key *} {event hset key *}" [set latest [r b_keyspace.events]]]\n        ',
        "else",
        '            fail "Keyspace event not propagated within 5 seconds"\n        ',
    )


def test_event_that_fires_twice(r: ValkeyTestClient) -> None:
    """
    test {Event that fires twice} {
        wait_for_blocked_clients_count 0
        r b_keyspace.clear
        r hset f g h
        wait_for_blocked_clients_count 0
        assert_equal "OK" [r b_keyspace.clear]
        set rd1 [valkey_deferring_client]
        $rd1 RENAME f g
        # Only one blocked client
        assert_equal [s 0 blocked_clients] 1
        assert_equal "" [r b_keyspace.events]
        # We should still see async processing for both events, which could be processed in either order
        wait_for_condition 1000 50 {
            [string match "{event rename_* key *} {event rename_* key *}" [set latest [r b_keyspace.events]]]
        } else {
            fail "Rename event not propagated within 5 seconds: latest value ${latest}"
        }
    }
    """
    wait_for_blocked_clients_count(0)
    r.run("b_keyspace.clear")
    r.run("hset", "f", "g", "h")
    wait_for_blocked_clients_count(0)
    assert "OK" == r.run("b_keyspace.clear")
    rd1 = valkey_deferring_client()
    rd1.run("RENAME", "f", "g")
    assert s(0, "blocked_clients") == 1
    assert "" == r.run("b_keyspace.events")
    wait_for_condition(
        1000,
        50,
        '            [string match "{event rename_* key *} {event rename_* key *}" [set latest [r b_keyspace.events]]]\n        ',
        "else",
        '            fail "Rename event not propagated within 5 seconds: latest value ${latest}"\n        ',
    )


def test_server_created_keyspace_notification(r: ValkeyTestClient) -> None:
    """
    test {Server-created keyspace notification} {
        wait_for_blocked_clients_count 0
        r b_keyspace.clear
        assert_equal "1" [r hset h i j]
        assert_equal "1" [r expire h 1]
        assert_equal [s 0 blocked_clients] 0
        # Expire will proceed processing in the background as we haven't
        # enabled blocking for the command yet.
        wait_for_condition 1000 50 {
            [r b_keyspace.events] eq "{event hset key h} {event expire key h}"
        } else {
            fail "Expire event not propagated within 5 seconds"
        }
        assert_equal "OK" [r b_keyspace.clear]
        # Expiration should happen in the background
        wait_for_condition 1000 50 {
            [r b_keyspace.events] eq "{event expired key h}"
        } else {
            fail "Expired event not propagated within 5 seconds"
        }
    }
    """
    wait_for_blocked_clients_count(0)
    r.run("b_keyspace.clear")
    assert "1" == r.run("hset", "h", "i", "j")
    assert "1" == r.run("expire", "h", 1)
    assert s(0, "blocked_clients") == 0
    wait_for_condition(
        1000,
        50,
        '            [r b_keyspace.events] eq "{event hset key h} {event expire key h}"\n        ',
        "else",
        '            fail "Expire event not propagated within 5 seconds"\n        ',
    )
    assert "OK" == r.run("b_keyspace.clear")
    wait_for_condition(
        1000,
        50,
        '            [r b_keyspace.events] eq "{event expired key h}"\n        ',
        "else",
        '            fail "Expired event not propagated within 5 seconds"\n        ',
    )


def test_unload_the_module_testblockingkeyspacenotif(r: ValkeyTestClient) -> None:
    """
    test "Unload the module - testblockingkeyspacenotif" {
        assert_equal {OK} [r module unload testblockingkeyspacenotif]
    }
    """
    assert "OK" == r.run("module", "unload", "testblockingkeyspacenotif")


# --- stubs for unimplemented TCL helpers ---


def clock(*args):
    raise NotImplementedError("clock")


def expr(*args):
    raise NotImplementedError("expr")


def pause_process(*args):
    raise NotImplementedError("pause_process")


def resume_process(*args):
    raise NotImplementedError("resume_process")


def s(*args):
    raise NotImplementedError("s")


def srv(*args):
    raise NotImplementedError("srv")


def valkey_deferring_client(*args):
    raise NotImplementedError("valkey_deferring_client")


def wait_for_blocked_clients_count(*args):
    raise NotImplementedError("wait_for_blocked_clients_count")


def wait_for_condition(*args):
    raise NotImplementedError("wait_for_condition")
