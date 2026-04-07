# ruff: noqa: ANN001, ANN002, ANN201
import time

import pytest

from tests.valkey_test_client import ValkeyTestClient

"""
set testmodule file normalize tests/modules/blockedclient.so
"""


"""
set testmodule2 file normalize tests/modules/postnotifications.so
"""


"""
set testmodule3 file normalize tests/modules/blockonkeys.so
"""

pytestmark = [pytest.mark.modules]


"""
r module load testmodule
"""


def test_locked_gil_acquisition_from_async_rm_call(r: ValkeyTestClient) -> None:
    """
    test {Locked GIL acquisition from async RM_Call} {
        assert_equal {OK} [r do_rm_call_async acquire_gil]
    }
    """
    assert "OK" == r.run("do_rm_call_async", "acquire_gil")


def test_blpop_on_async_rm_call_fire_and_forget(r: ValkeyTestClient) -> None:
    """
    test "Blpop on async RM_Call fire and forget" {
        assert_equal {Blocked} [r do_rm_call_fire_and_forget blpop l 0]
        r lpush l a
        assert_equal {0} [r llen l]
    }
    """
    assert "Blocked" == r.run("do_rm_call_fire_and_forget", "blpop", "l", 0)
    r.run("lpush", "l", "a")
    assert "0" == r.run("llen", "l")


def test_blpop_on_threaded_async_rm_call(r: ValkeyTestClient) -> None:
    """
    test "Blpop on threaded async RM_Call" {
        set rd [valkey_deferring_client]

        $rd do_rm_call_async_on_thread blpop l 0
        wait_for_blocked_clients_count 1
        r lpush l a
        assert_equal [$rd read] {l a}
        wait_for_blocked_clients_count 0
        $rd close
    }
    """
    rd = ValkeyTestClient.create_from(r)
    rd.run("do_rm_call_async_on_thread", "blpop", "l", 0)
    wait_for_blocked_clients_count(1)
    r.run("lpush", "l", "a")
    assert rd.run("read") == "l a"
    wait_for_blocked_clients_count(0)
    rd.run("close")


@pytest.mark.xfail(reason="not implemented")
@pytest.mark.parametrize(["cmd"], [("do_rm_call_async"), ("do_rm_call_async_script_mode")])
def test_blpop_on_async_rm_call_using_cmd(r: ValkeyTestClient, cmd) -> None:
    """
    test "Blpop on async RM_Call using $cmd" {
        set rd [valkey_deferring_client]

        $rd $cmd blpop l 0
        wait_for_blocked_clients_count 1
        r lpush l a
        assert_equal [$rd read] {l a}
        wait_for_blocked_clients_count 0
        $rd close
    }
    """
    rd = ValkeyTestClient.create_from(r)
    # TODO: $rd cmd blpop l 0
    wait_for_blocked_clients_count(1)
    r.run("lpush", "l", "a")
    assert rd.run("read") == "l a"
    wait_for_blocked_clients_count(0)
    rd.run("close")


@pytest.mark.xfail(reason="not implemented")
@pytest.mark.parametrize(["cmd"], [("do_rm_call_async"), ("do_rm_call_async_script_mode")])
def test_brpop_on_async_rm_call_using_cmd(r: ValkeyTestClient, cmd) -> None:
    """
    test "Brpop on async RM_Call using $cmd" {
        set rd [valkey_deferring_client]

        $rd $cmd brpop l 0
        wait_for_blocked_clients_count 1
        r lpush l a
        assert_equal [$rd read] {l a}
        wait_for_blocked_clients_count 0
        $rd close
    }
    """
    rd = ValkeyTestClient.create_from(r)
    # TODO: $rd cmd brpop l 0
    wait_for_blocked_clients_count(1)
    r.run("lpush", "l", "a")
    assert rd.run("read") == "l a"
    wait_for_blocked_clients_count(0)
    rd.run("close")


@pytest.mark.xfail(reason="not implemented")
@pytest.mark.parametrize(["cmd"], [("do_rm_call_async"), ("do_rm_call_async_script_mode")])
def test_brpoplpush_on_async_rm_call_using_cmd(r: ValkeyTestClient, cmd) -> None:
    """
    test "Brpoplpush on async RM_Call using $cmd" {
        set rd [valkey_deferring_client]

        $rd $cmd brpoplpush l1 l2 0
        wait_for_blocked_clients_count 1
        r lpush l1 a
        assert_equal [$rd read] {a}
        wait_for_blocked_clients_count 0
        $rd close
        r lpop l2
    } {a}
    """
    rd = ValkeyTestClient.create_from(r)
    # TODO: $rd cmd brpoplpush l1 l2 0
    wait_for_blocked_clients_count(1)
    r.run("lpush", "l1", "a")
    assert rd.run("read") == "a"
    wait_for_blocked_clients_count(0)
    rd.run("close")
    assert r.run("lpop", "l2") == "a"


@pytest.mark.xfail(reason="not implemented")
@pytest.mark.parametrize(["cmd"], [("do_rm_call_async"), ("do_rm_call_async_script_mode")])
def test_blmove_on_async_rm_call_using_cmd(r: ValkeyTestClient, cmd) -> None:
    """
    test "Blmove on async RM_Call using $cmd" {
        set rd [valkey_deferring_client]

        $rd $cmd blmove l1 l2 LEFT LEFT 0
        wait_for_blocked_clients_count 1
        r lpush l1 a
        assert_equal [$rd read] {a}
        wait_for_blocked_clients_count 0
        $rd close
        r lpop l2
    } {a}
    """
    rd = ValkeyTestClient.create_from(r)
    # TODO: $rd cmd blmove l1 l2 LEFT LEFT 0
    wait_for_blocked_clients_count(1)
    r.run("lpush", "l1", "a")
    assert rd.run("read") == "a"
    wait_for_blocked_clients_count(0)
    rd.run("close")
    assert r.run("lpop", "l2") == "a"


@pytest.mark.xfail(reason="not implemented")
@pytest.mark.parametrize(["cmd"], [("do_rm_call_async"), ("do_rm_call_async_script_mode")])
def test_bzpopmin_on_async_rm_call_using_cmd(r: ValkeyTestClient, cmd) -> None:
    """
    test "Bzpopmin on async RM_Call using $cmd" {
        set rd [valkey_deferring_client]

        $rd $cmd bzpopmin s 0
        wait_for_blocked_clients_count 1
        r zadd s 10 foo
        assert_equal [$rd read] {s foo 10}
        wait_for_blocked_clients_count 0
        $rd close
    }
    """
    rd = ValkeyTestClient.create_from(r)
    # TODO: $rd cmd bzpopmin s 0
    wait_for_blocked_clients_count(1)
    r.run("zadd", "s", 10, "foo")
    assert rd.run("read") == "s foo 10"
    wait_for_blocked_clients_count(0)
    rd.run("close")


@pytest.mark.xfail(reason="not implemented")
@pytest.mark.parametrize(["cmd"], [("do_rm_call_async"), ("do_rm_call_async_script_mode")])
def test_bzpopmax_on_async_rm_call_using_cmd(r: ValkeyTestClient, cmd) -> None:
    """
    test "Bzpopmax on async RM_Call using $cmd" {
        set rd [valkey_deferring_client]

        $rd $cmd bzpopmax s 0
        wait_for_blocked_clients_count 1
        r zadd s 10 foo
        assert_equal [$rd read] {s foo 10}
        wait_for_blocked_clients_count 0
        $rd close
    }
    """
    rd = ValkeyTestClient.create_from(r)
    # TODO: $rd cmd bzpopmax s 0
    wait_for_blocked_clients_count(1)
    r.run("zadd", "s", 10, "foo")
    assert rd.run("read") == "s foo 10"
    wait_for_blocked_clients_count(0)
    rd.run("close")


def test_nested_async_rm_call(r: ValkeyTestClient) -> None:
    """
    test {Nested async RM_Call} {
        set rd [valkey_deferring_client]

        $rd do_rm_call_async do_rm_call_async do_rm_call_async do_rm_call_async blpop l 0
        wait_for_blocked_clients_count 1
        r lpush l a
        assert_equal [$rd read] {l a}
        wait_for_blocked_clients_count 0
        $rd close
    }
    """
    rd = ValkeyTestClient.create_from(r)
    rd.run("do_rm_call_async", "do_rm_call_async", "do_rm_call_async", "do_rm_call_async", "blpop", "l", 0)
    wait_for_blocked_clients_count(1)
    r.run("lpush", "l", "a")
    assert rd.run("read") == "l a"
    wait_for_blocked_clients_count(0)
    rd.run("close")


def test_test_multiple_async_rm_call_waiting_on_the_same_event(r: ValkeyTestClient) -> None:
    """
    test {Test multiple async RM_Call waiting on the same event} {
        set rd1 [valkey_deferring_client]
        set rd2 [valkey_deferring_client]

        $rd1 do_rm_call_async do_rm_call_async do_rm_call_async do_rm_call_async blpop l 0
        $rd2 do_rm_call_async do_rm_call_async do_rm_call_async do_rm_call_async blpop l 0
        wait_for_blocked_clients_count 2
        r lpush l element element
        assert_equal [$rd1 read] {l element}
        assert_equal [$rd2 read] {l element}
        wait_for_blocked_clients_count 0
        $rd1 close
        $rd2 close
    }
    """
    rd1 = ValkeyTestClient.create_from(r)
    rd2 = ValkeyTestClient.create_from(r)
    rd1.run("do_rm_call_async", "do_rm_call_async", "do_rm_call_async", "do_rm_call_async", "blpop", "l", 0)
    rd2.run("do_rm_call_async", "do_rm_call_async", "do_rm_call_async", "do_rm_call_async", "blpop", "l", 0)
    wait_for_blocked_clients_count(2)
    r.run("lpush", "l", "element", "element")
    assert rd1.run("read") == "l element"
    assert rd2.run("read") == "l element"
    wait_for_blocked_clients_count(0)
    rd1.run("close")
    rd2.run("close")


def test_async_rm_call_calls_rm_call(r: ValkeyTestClient) -> None:
    """
    test {async RM_Call calls RM_Call} {
        assert_equal {PONG} [r do_rm_call_async do_rm_call ping]
    }
    """
    assert "PONG" == r.run("do_rm_call_async", "do_rm_call", "ping")


def test_async_rm_call_calls_background_rm_call_calls_rm_call(r: ValkeyTestClient) -> None:
    """
    test {async RM_Call calls background RM_Call calls RM_Call} {
        assert_equal {PONG} [r do_rm_call_async do_bg_rm_call do_rm_call ping]
    }
    """
    assert "PONG" == r.run("do_rm_call_async", "do_bg_rm_call", "do_rm_call", "ping")


def test_async_rm_call_calls_background_rm_call_calls_rm_call_calls_async_rm_call(r: ValkeyTestClient) -> None:
    """
    test {async RM_Call calls background RM_Call calls RM_Call calls async RM_Call} {
        assert_equal {PONG} [r do_rm_call_async do_bg_rm_call do_rm_call do_rm_call_async ping]
    }
    """
    assert "PONG" == r.run("do_rm_call_async", "do_bg_rm_call", "do_rm_call", "do_rm_call_async", "ping")


def test_async_rm_call_inside_async_rm_call_callback(r: ValkeyTestClient) -> None:
    """
    test {async RM_Call inside async RM_Call callback} {
        set rd [valkey_deferring_client]
        $rd wait_and_do_rm_call blpop l 0
        wait_for_blocked_clients_count 1

        start_server {} {
            test "Connect a replica to the master instance" {
                r slaveof [srv -1 host] [srv -1 port]
                wait_for_condition 50 100 {
                    [s role] eq {slave} &&
                    [string match {*master_link_status:up*} [r info replication]]
                } else {
                    fail "Can't turn the instance into a replica"
                }
            }

            assert_equal {1} [r -1 lpush l a]
            assert_equal [$rd read] {l a}
        }

        wait_for_blocked_clients_count 0
        $rd close
    }
    """
    rd = ValkeyTestClient.create_from(r)
    rd.run("wait_and_do_rm_call", "blpop", "l", 0)
    wait_for_blocked_clients_count(1)
    start_server(
        "",
        '            test "Connect a replica to the master instance" {\n                r slaveof [srv -1 host] [srv -1 port]\n                wait_for_condition 50 100 {\n                    [s role] eq {slave} &&\n                    [string match {*master_link_status:up*} [r info replication]]\n                } else {\n                    fail "Can\'t turn the instance into a replica"\n                }\n            }\n\n            assert_equal {1} [r -1 lpush l a]\n            assert_equal [$rd read] {l a}\n        ',
    )
    wait_for_blocked_clients_count(0)
    rd.run("close")


@pytest.mark.xfail(reason="not implemented")
def test_become_replica_while_having_async_rm_call_running(r: ValkeyTestClient) -> None:
    """
    test {Become replica while having async RM_Call running} {
        r flushall
        set rd [valkey_deferring_client]
        $rd do_rm_call_async blpop l 0
        wait_for_blocked_clients_count 1

        #become a replica of a not existing server
        r replicaof localhost 30000

        catch {[$rd read]} e
        assert_match {UNBLOCKED force unblock from blocking operation*} $e
        wait_for_blocked_clients_count 0

        r replicaof no one

        r lpush l 1
        # make sure the async rm_call was aborted
        assert_equal [r llen l] {1}
        $rd close
    }
    """
    r.run("flushall")
    rd = ValkeyTestClient.create_from(r)
    rd.run("do_rm_call_async", "blpop", "l", 0)
    wait_for_blocked_clients_count(1)
    r.run("replicaof", "localhost", 30000)
    catch("[$rd read]", "e")
    # TODO: assert_match {UNBLOCKED force unblock from blocking operation*} e
    wait_for_blocked_clients_count(0)
    r.run("replicaof", "no", "one")
    r.run("lpush", "l", 1)
    assert r.run("llen", "l") == "1"
    rd.run("close")


def test_pipeline_with_blocking_rm_call(r: ValkeyTestClient) -> None:
    """
    test {Pipeline with blocking RM_Call} {
        r flushall
        set rd [valkey_deferring_client]
        set buf ""
        append buf "do_rm_call_async blpop l 0\r\n"
        append buf "ping\r\n"
        $rd write $buf
        $rd flush
        wait_for_blocked_clients_count 1

        # release the blocked client
        r lpush l 1

        assert_equal [$rd read] {l 1}
        assert_equal [$rd read] {PONG}

        wait_for_blocked_clients_count 0
        $rd close
    }
    """
    r.run("flushall")
    rd = ValkeyTestClient.create_from(r)
    buf = ""
    append("buf", "do_rm_call_async blpop l 0\r\n")
    append("buf", "ping\r\n")
    rd.run("write", buf)
    rd.run("flush")
    wait_for_blocked_clients_count(1)
    r.run("lpush", "l", 1)
    assert rd.run("read") == "l 1"
    assert rd.run("read") == "PONG"
    wait_for_blocked_clients_count(0)
    rd.run("close")


def test_blocking_rm_call_abort(r: ValkeyTestClient) -> None:
    """
    test {blocking RM_Call abort} {
        r flushall
        set rd [valkey_deferring_client]

        $rd client id
        set client_id [$rd read]

        $rd do_rm_call_async blpop l 0
        wait_for_blocked_clients_count 1

        r client kill ID $client_id
        assert_error {*error reading reply*} {$rd read}

        wait_for_blocked_clients_count 0

        r lpush l 1
        # make sure the async rm_call was aborted
        assert_equal [r llen l] {1}
        $rd close
    }
    """
    r.run("flushall")
    rd = ValkeyTestClient.create_from(r)
    rd.run("client", "id")
    client_id = rd.run("read")
    rd.run("do_rm_call_async", "blpop", "l", 0)
    wait_for_blocked_clients_count(1)
    r.run("client", "kill", "ID", client_id)
    assert_error("*error reading reply*", "$rd read")
    wait_for_blocked_clients_count(0)
    r.run("lpush", "l", 1)
    assert r.run("llen", "l") == "1"
    rd.run("close")


pytestmark = [pytest.mark.modules]


"""
r module load testmodule
"""


def test_test_basic_replication_stream_on_unblock_handler(r: ValkeyTestClient) -> None:
    """
    test {Test basic replication stream on unblock handler} {
        r flushall
        set repl [attach_to_replication_stream]

        set rd [valkey_deferring_client]

        $rd do_rm_call_async blpop l 0
        wait_for_blocked_clients_count 1
        r lpush l a
        assert_equal [$rd read] {l a}

        assert_replication_stream $repl {
            {select *}
            {lpush l a}
            {lpop l}
        }
        close_replication_stream $repl

        wait_for_blocked_clients_count 0
        $rd close
    }
    """
    r.run("flushall")
    repl = attach_to_replication_stream()
    rd = ValkeyTestClient.create_from(r)
    rd.run("do_rm_call_async", "blpop", "l", 0)
    wait_for_blocked_clients_count(1)
    r.run("lpush", "l", "a")
    assert rd.run("read") == "l a"
    assert_replication_stream(repl, "            {select *}\n            {lpush l a}\n            {lpop l}\n        ")
    close_replication_stream(repl)
    wait_for_blocked_clients_count(0)
    rd.run("close")


def test_test_unblock_handler_are_executed_as_a_unit(r: ValkeyTestClient) -> None:
    """
    test {Test unblock handler are executed as a unit} {
        r flushall
        set repl [attach_to_replication_stream]

        set rd [valkey_deferring_client]

        $rd blpop_and_set_multiple_keys l x 1 y 2
        wait_for_blocked_clients_count 1
        r lpush l a
        assert_equal [$rd read] {OK}

        assert_replication_stream $repl {
            {select *}
            {lpush l a}
            {multi}
            {lpop l}
            {set x 1}
            {set y 2}
            {exec}
        }
        close_replication_stream $repl

        wait_for_blocked_clients_count 0
        $rd close
    }
    """
    r.run("flushall")
    repl = attach_to_replication_stream()
    rd = ValkeyTestClient.create_from(r)
    rd.run("blpop_and_set_multiple_keys", "l", "x", 1, "y", 2)
    wait_for_blocked_clients_count(1)
    r.run("lpush", "l", "a")
    assert rd.run("read") == "OK"
    assert_replication_stream(
        repl,
        "            {select *}\n            {lpush l a}\n            {multi}\n            {lpop l}\n            {set x 1}\n            {set y 2}\n            {exec}\n        ",
    )
    close_replication_stream(repl)
    wait_for_blocked_clients_count(0)
    rd.run("close")


def test_test_no_propagation_of_blocking_command(r: ValkeyTestClient) -> None:
    """
    test {Test no propagation of blocking command} {
        r flushall
        set repl [attach_to_replication_stream]

        set rd [valkey_deferring_client]

        $rd do_rm_call_async_no_replicate blpop l 0
        wait_for_blocked_clients_count 1
        r lpush l a
        assert_equal [$rd read] {l a}

        # make sure the lpop are not replicated
        r set x 1

        assert_replication_stream $repl {
            {select *}
            {lpush l a}
            {set x 1}
        }
        close_replication_stream $repl

        wait_for_blocked_clients_count 0
        $rd close
    }
    """
    r.run("flushall")
    repl = attach_to_replication_stream()
    rd = ValkeyTestClient.create_from(r)
    rd.run("do_rm_call_async_no_replicate", "blpop", "l", 0)
    wait_for_blocked_clients_count(1)
    r.run("lpush", "l", "a")
    assert rd.run("read") == "l a"
    r.run("set", "x", 1)
    assert_replication_stream(repl, "            {select *}\n            {lpush l a}\n            {set x 1}\n        ")
    close_replication_stream(repl)
    wait_for_blocked_clients_count(0)
    rd.run("close")


pytestmark = [pytest.mark.modules]


"""
r module load testmodule
"""


"""
r module load testmodule2
"""


def test_test_unblock_handler_are_executed_as_a_unit_with_key_space_notifications(r: ValkeyTestClient) -> None:
    """
    test {Test unblock handler are executed as a unit with key space notifications} {
        r flushall
        set repl [attach_to_replication_stream]

        set rd [valkey_deferring_client]

        $rd blpop_and_set_multiple_keys l string_foo 1 string_bar 2
        wait_for_blocked_clients_count 1
        r lpush l a
        assert_equal [$rd read] {OK}

        # Explanation of the first multi exec block:
        # {lpop l} - pop the value by our blocking command 'blpop_and_set_multiple_keys'
        # {set string_foo 1} - the action of our blocking command 'blpop_and_set_multiple_keys'
        # {set string_bar 2} - the action of our blocking command 'blpop_and_set_multiple_keys'
        # {incr string_changed{string_foo}} - post notification job that was registered when 'string_foo' changed
        # {incr string_changed{string_bar}} - post notification job that was registered when 'string_bar' changed
        # {incr string_total} - post notification job that was registered when string_changed{string_foo} changed
        # {incr string_total} - post notification job that was registered when string_changed{string_bar} changed
        assert_replication_stream $repl {
            {select *}
            {lpush l a}
            {multi}
            {lpop l}
            {set string_foo 1}
            {set string_bar 2}
            {incr string_changed{string_foo}}
            {incr string_changed{string_bar}}
            {incr string_total}
            {incr string_total}
            {exec}
        }
        close_replication_stream $repl

        wait_for_blocked_clients_count 0
        $rd close
    }
    """
    r.run("flushall")
    repl = attach_to_replication_stream()
    rd = ValkeyTestClient.create_from(r)
    rd.run("blpop_and_set_multiple_keys", "l", "string_foo", 1, "string_bar", 2)
    wait_for_blocked_clients_count(1)
    r.run("lpush", "l", "a")
    assert rd.run("read") == "OK"
    assert_replication_stream(
        repl,
        "            {select *}\n            {lpush l a}\n            {multi}\n            {lpop l}\n            {set string_foo 1}\n            {set string_bar 2}\n            {incr string_changed{string_foo}}\n            {incr string_changed{string_bar}}\n            {incr string_total}\n            {incr string_total}\n            {exec}\n        ",
    )
    close_replication_stream(repl)
    wait_for_blocked_clients_count(0)
    rd.run("close")


def test_test_unblock_handler_are_executed_as_a_unit_with_lazy_expire(r: ValkeyTestClient) -> None:
    """
    test {Test unblock handler are executed as a unit with lazy expire} {
        r flushall
        r DEBUG SET-ACTIVE-EXPIRE 0
        set repl [attach_to_replication_stream]

        set rd [valkey_deferring_client]

        $rd blpop_and_set_multiple_keys l string_foo 1 string_bar 2
        wait_for_blocked_clients_count 1
        r lpush l a
        assert_equal [$rd read] {OK}

        # set expiration on string_foo
        r pexpire string_foo 1
        after 10

        # now the key should have been expired
        $rd blpop_and_set_multiple_keys l string_foo 1 string_bar 2
        wait_for_blocked_clients_count 1
        r lpush l a
        assert_equal [$rd read] {OK}

        # Explanation of the first multi exec block:
        # {lpop l} - pop the value by our blocking command 'blpop_and_set_multiple_keys'
        # {set string_foo 1} - the action of our blocking command 'blpop_and_set_multiple_keys'
        # {set string_bar 2} - the action of our blocking command 'blpop_and_set_multiple_keys'
        # {incr string_changed{string_foo}} - post notification job that was registered when 'string_foo' changed
        # {incr string_changed{string_bar}} - post notification job that was registered when 'string_bar' changed
        # {incr string_total} - post notification job that was registered when string_changed{string_foo} changed
        # {incr string_total} - post notification job that was registered when string_changed{string_bar} changed
        #
        # Explanation of the second multi exec block:
        # {lpop l} - pop the value by our blocking command 'blpop_and_set_multiple_keys'
        # {unlink string_foo} - lazy expiration of string_foo when 'blpop_and_set_multiple_keys' tries to write to it.
        # {set string_foo 1} - the action of our blocking command 'blpop_and_set_multiple_keys'
        # {set string_bar 2} - the action of our blocking command 'blpop_and_set_multiple_keys'
        # {incr expired} - the post notification job, registered after string_foo got expired
        # {incr string_changed{string_foo}} - post notification job triggered when we set string_foo
        # {incr string_changed{string_bar}} - post notification job triggered when we set string_bar
        # {incr string_total} - post notification job triggered when we incr 'string_changed{string_foo}'
        # {incr string_total} - post notification job triggered when we incr 'string_changed{string_bar}'
        assert_replication_stream $repl {
            {select *}
            {lpush l a}
            {multi}
            {lpop l}
            {set string_foo 1}
            {set string_bar 2}
            {incr string_changed{string_foo}}
            {incr string_changed{string_bar}}
            {incr string_total}
            {incr string_total}
            {exec}
            {pexpireat string_foo *}
            {lpush l a}
            {multi}
            {lpop l}
            {unlink string_foo}
            {set string_foo 1}
            {set string_bar 2}
            {incr expired}
            {incr string_changed{string_foo}}
            {incr string_changed{string_bar}}
            {incr string_total}
            {incr string_total}
            {exec}
        }
        close_replication_stream $repl
        r DEBUG SET-ACTIVE-EXPIRE 1

        wait_for_blocked_clients_count 0
        $rd close
    }
    """
    r.run("flushall")
    r.run("DEBUG", "SET-ACTIVE-EXPIRE", 0)
    repl = attach_to_replication_stream()
    rd = ValkeyTestClient.create_from(r)
    rd.run("blpop_and_set_multiple_keys", "l", "string_foo", 1, "string_bar", 2)
    wait_for_blocked_clients_count(1)
    r.run("lpush", "l", "a")
    assert rd.run("read") == "OK"
    r.run("pexpire", "string_foo", 1)
    time.sleep(10 / 1000)
    rd.run("blpop_and_set_multiple_keys", "l", "string_foo", 1, "string_bar", 2)
    wait_for_blocked_clients_count(1)
    r.run("lpush", "l", "a")
    assert rd.run("read") == "OK"
    assert_replication_stream(
        repl,
        "            {select *}\n            {lpush l a}\n            {multi}\n            {lpop l}\n            {set string_foo 1}\n            {set string_bar 2}\n            {incr string_changed{string_foo}}\n            {incr string_changed{string_bar}}\n            {incr string_total}\n            {incr string_total}\n            {exec}\n            {pexpireat string_foo *}\n            {lpush l a}\n            {multi}\n            {lpop l}\n            {unlink string_foo}\n            {set string_foo 1}\n            {set string_bar 2}\n            {incr expired}\n            {incr string_changed{string_foo}}\n            {incr string_changed{string_bar}}\n            {incr string_total}\n            {incr string_total}\n            {exec}\n        ",
    )
    close_replication_stream(repl)
    r.run("DEBUG", "SET-ACTIVE-EXPIRE", 1)
    wait_for_blocked_clients_count(0)
    rd.run("close")


pytestmark = [pytest.mark.modules]


"""
r module load testmodule
"""


"""
r module load testmodule3
"""


def test_test_unblock_handler_on_module_blocked_on_keys(r: ValkeyTestClient) -> None:
    """
    test {Test unblock handler on module blocked on keys} {
        set rd [valkey_deferring_client]

        r fsl.push l 1
        $rd do_rm_call_async FSL.BPOPGT l 3 0
        wait_for_blocked_clients_count 1
        r fsl.push l 2
        r fsl.push l 3
        r fsl.push l 4
        assert_equal [$rd read] {4}

        wait_for_blocked_clients_count 0
        $rd close
    }
    """
    rd = ValkeyTestClient.create_from(r)
    r.run("fsl.push", "l", 1)
    rd.run("do_rm_call_async", "FSL.BPOPGT", "l", 3, 0)
    wait_for_blocked_clients_count(1)
    r.run("fsl.push", "l", 2)
    r.run("fsl.push", "l", 3)
    r.run("fsl.push", "l", 4)
    assert rd.run("read") == "4"
    wait_for_blocked_clients_count(0)
    rd.run("close")


# --- stubs for unimplemented TCL helpers ---


def append(*args):
    raise NotImplementedError("append")


def assert_error(*args):
    raise NotImplementedError("assert_error")


def assert_replication_stream(*args):
    raise NotImplementedError("assert_replication_stream")


def attach_to_replication_stream(*args):
    raise NotImplementedError("attach_to_replication_stream")


def catch(*args):
    raise NotImplementedError("catch")


def close_replication_stream(*args):
    raise NotImplementedError("close_replication_stream")


def start_server(*args):
    raise NotImplementedError("start_server")


def wait_for_blocked_clients_count(*args):
    raise NotImplementedError("wait_for_blocked_clients_count")
