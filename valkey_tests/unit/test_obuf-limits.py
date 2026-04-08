# ruff: noqa: PLR2004, F841, ANN001, ANN002, ANN201
import time
from fnmatch import fnmatch

import pytest

from tests.valkey_test_client import ValkeyTestClient

pytestmark = [pytest.mark.obuf_limits_external_skip_logreqres_skip]


"""
r config set min-io-threads-avoid-copy-reply 0
"""


def test_config_set_client_output_buffer_limit(r: ValkeyTestClient) -> None:
    """
    test {CONFIG SET client-output-buffer-limit} {
        set oldval [lindex [r config get client-output-buffer-limit] 1]

        catch {r config set client-output-buffer-limit "wrong number"} e
        assert_match {*Wrong*arguments*} $e

        catch {r config set client-output-buffer-limit "invalid_class 10mb 10mb 60"} e
        assert_match {*Invalid*client*class*} $e
        catch {r config set client-output-buffer-limit "master 10mb 10mb 60"} e
        assert_match {*Invalid*client*class*} $e

        catch {r config set client-output-buffer-limit "normal 10mbs 10mb 60"} e
        assert_match {*Error*hard*} $e

        catch {r config set client-output-buffer-limit "replica 10mb 10mbs 60"} e
        assert_match {*Error*soft*} $e

        catch {r config set client-output-buffer-limit "pubsub 10mb 10mb 60s"} e
        assert_match {*Error*soft_seconds*} $e

        r config set client-output-buffer-limit "normal 1mb 2mb 60 replica 3mb 4mb 70 pubsub 5mb 6mb 80"
        set res [lindex [r config get client-output-buffer-limit] 1]
        assert_equal $res "normal 1048576 2097152 60 slave 3145728 4194304 70 pubsub 5242880 6291456 80"

        # Set back to the original value.
        r config set client-output-buffer-limit $oldval
    }
    """
    oldval = r.run("config", "get", "client-output-buffer-limit")[1]
    try:
        e = r.run("config", "set", "client-output-buffer-limit", "wrong number")
    except Exception as _catch_err:
        e = str(_catch_err)
    assert fnmatch(str(e), "*Wrong*arguments*")
    try:
        e = r.run("config", "set", "client-output-buffer-limit", "invalid_class 10mb 10mb 60")
    except Exception as _catch_err:
        e = str(_catch_err)
    assert fnmatch(str(e), "*Invalid*client*class*")
    try:
        e = r.run("config", "set", "client-output-buffer-limit", "master 10mb 10mb 60")
    except Exception as _catch_err:
        e = str(_catch_err)
    assert fnmatch(str(e), "*Invalid*client*class*")
    try:
        e = r.run("config", "set", "client-output-buffer-limit", "normal 10mbs 10mb 60")
    except Exception as _catch_err:
        e = str(_catch_err)
    assert fnmatch(str(e), "*Error*hard*")
    try:
        e = r.run("config", "set", "client-output-buffer-limit", "replica 10mb 10mbs 60")
    except Exception as _catch_err:
        e = str(_catch_err)
    assert fnmatch(str(e), "*Error*soft*")
    try:
        e = r.run("config", "set", "client-output-buffer-limit", "pubsub 10mb 10mb 60s")
    except Exception as _catch_err:
        e = str(_catch_err)
    assert fnmatch(str(e), "*Error*soft_seconds*")
    r.run("config", "set", "client-output-buffer-limit", "normal 1mb 2mb 60 replica 3mb 4mb 70 pubsub 5mb 6mb 80")
    res = r.run("config", "get", "client-output-buffer-limit")[1]
    assert res == "normal 1048576 2097152 60 slave 3145728 4194304 70 pubsub 5242880 6291456 80"
    r.run("config", "set", "client-output-buffer-limit", oldval)


def test_client_output_buffer_hard_limit_is_enforced(r: ValkeyTestClient) -> None:
    """
    test {Client output buffer hard limit is enforced} {
        r config set client-output-buffer-limit {pubsub 100000 0 0}
        set rd1 [valkey_deferring_client]

        $rd1 subscribe foo
        set reply [$rd1 read]
        assert {$reply eq "subscribe foo 1"}

        set omem 0
        while 1 {
            # The larger content size ensures that client.buf gets filled more quickly,
            # allowing us to correctly observe the gradual increase of `omem`
            r publish foo [string repeat bar 50]
            set clients [split [r client list] "\r\n"]
            set c [split [lindex $clients 1] " "]
            if {![regexp {omem=([0-9]+)} $c - omem]} break
            if {$omem > 200000} break
        }
        assert {$omem >= 70000 && $omem < 200000}
        $rd1 close
    }
    """
    r.run("config", "set", "client-output-buffer-limit", "pubsub 100000 0 0")
    rd1 = ValkeyTestClient.create_from(r)
    rd1.run("subscribe", "foo")
    reply = rd1.run("read")
    assert reply == "subscribe foo 1"
    omem = 0
    while_(
        1,
        '            # The larger content size ensures that client.buf gets filled more quickly,\n            # allowing us to correctly observe the gradual increase of `omem`\n            r publish foo [string repeat bar 50]\n            set clients [split [r client list] "\\r\\n"]\n            set c [split [lindex $clients 1] " "]\n            if {![regexp {omem=([0-9]+)} $c - omem]} break\n            if {$omem > 200000} break\n        ',
    )
    assert (omem >= 70000) and (omem < 200000)
    rd1.run("close")


"""
if wait_for_timeout {
    set test_name "Client output buffer soft limit is enforced if time is overreached"
} else {
    set test_name "Client output buffer soft limit is not enforced too early and is enforced when no traffic"
}
"""


@pytest.mark.parametrize(["soft_limit_time", "wait_for_timeout"], [(3, "yes"), (4, "no")])
def test_test_name(r: ValkeyTestClient, soft_limit_time, wait_for_timeout) -> None:
    """
    test test_name {
        r config set client-output-buffer-limit "pubsub 0 100000 $soft_limit_time"
        set soft_limit_time [expr $soft_limit_time*1000]
        set rd1 [valkey_deferring_client]

        $rd1 client setname test_client
        set reply [$rd1 read]
        assert {$reply eq "OK"}

        $rd1 subscribe foo
        set reply [$rd1 read]
        assert {$reply eq "subscribe foo 1"}

        set omem 0
        set start_time 0
        set time_elapsed 0
        set last_under_limit_time [clock milliseconds]
        while 1 {
            r publish foo [string repeat "x" 1000]
            set clients [split [r client list] "\r\n"]
            set c [lsearch -inline $clients *name=test_client*]
            if {$start_time != 0} {
                set time_elapsed [expr {[clock milliseconds]-$start_time}]
                # Make sure test isn't taking too long
                assert {$time_elapsed <= [expr $soft_limit_time+3000]}
            }
            if {$wait_for_timeout && $c == ""} {
                # Make sure we're disconnected when we reach the soft limit
                assert {$omem >= 100000 && $time_elapsed >= $soft_limit_time}
                break
            } else {
                assert {[regexp {omem=([0-9]+)} $c - omem]}
            }
            if {$omem > 100000} {
                if {$start_time == 0} {set start_time $last_under_limit_time}
                if {!$wait_for_timeout && $time_elapsed >= [expr $soft_limit_time-1000]} break
                # Slow down loop when omem has reached the limit.
                after 10
            } else {
                # if the OS socket buffers swallowed what we previously filled, reset the start timer.
                set start_time 0
                set last_under_limit_time [clock milliseconds]
            }
        }

        if {!$wait_for_timeout} {
            # After we completely stopped the traffic, wait for soft limit to time out
            set timeout [expr {$soft_limit_time+1500 - ([clock milliseconds]-$start_time)}]
            wait_for_condition [expr $timeout/10] 10 {
                [lsearch [split [r client list] "\r\n"] *name=test_client*] == -1
            } else {
                fail "Soft limit timed out but client still connected"
            }
        }

        $rd1 close
    }
    """
    r.run("config", "set", "client-output-buffer-limit", f"pubsub 0 100000 {soft_limit_time}")
    soft_limit_time = expr(soft_limit_time, "*1000")
    rd1 = ValkeyTestClient.create_from(r)
    rd1.run("client", "setname", "test_client")
    reply = rd1.run("read")
    assert reply == "OK"
    rd1.run("subscribe", "foo")
    reply = rd1.run("read")
    assert reply == "subscribe foo 1"
    omem = 0
    start_time = 0
    time_elapsed = 0
    last_under_limit_time = clock("milliseconds")
    while_(
        1,
        '                r publish foo [string repeat "x" 1000]\n                set clients [split [r client list] "\\r\\n"]\n                set c [lsearch -inline $clients *name=test_client*]\n                if {$start_time != 0} {\n                    set time_elapsed [expr {[clock milliseconds]-$start_time}]\n                    # Make sure test isn\'t taking too long\n                    assert {$time_elapsed <= [expr $soft_limit_time+3000]}\n                }\n                if {$wait_for_timeout && $c == ""} {\n                    # Make sure we\'re disconnected when we reach the soft limit\n                    assert {$omem >= 100000 && $time_elapsed >= $soft_limit_time}\n                    break\n                } else {\n                    assert {[regexp {omem=([0-9]+)} $c - omem]}\n                }\n                if {$omem > 100000} {\n                    if {$start_time == 0} {set start_time $last_under_limit_time}\n                    if {!$wait_for_timeout && $time_elapsed >= [expr $soft_limit_time-1000]} break\n                    # Slow down loop when omem has reached the limit.\n                    after 10\n                } else {\n                    # if the OS socket buffers swallowed what we previously filled, reset the start timer.\n                    set start_time 0\n                    set last_under_limit_time [clock milliseconds]\n                }\n            ',
    )
    if_(
        "!$wait_for_timeout",
        '                # After we completely stopped the traffic, wait for soft limit to time out\n                set timeout [expr {$soft_limit_time+1500 - ([clock milliseconds]-$start_time)}]\n                wait_for_condition [expr $timeout/10] 10 {\n                    [lsearch [split [r client list] "\\r\\n"] *name=test_client*] == -1\n                } else {\n                    fail "Soft limit timed out but client still connected"\n                }\n            ',
    )
    rd1.run("close")


def test_no_response_for_single_command_if_client_output_buffer_hard_limit_is_enforced(r: ValkeyTestClient) -> None:
    """
    test {No response for single command if client output buffer hard limit is enforced} {
        r config set latency-tracking no
        r config set client-output-buffer-limit {normal 100000 0 0}
        # Total size of all items must be more than 100k
        set item [string repeat "x" 1000]
        for {set i 0} {$i < 150} {incr i} {
            r lpush mylist $item
        }
        set orig_mem [s used_memory]
        # Set client name and get all items
        set rd [valkey_deferring_client]
        $rd client setname mybiglist
        assert {[$rd read] eq "OK"}
        $rd lrange mylist 0 -1
        $rd flush
        after 100

        # Before we read reply, the server will close this client.
        set clients [r client list]
        assert_no_match "*name=mybiglist*" $clients
        set cur_mem [s used_memory]
        # 10k just is a deviation threshold
        assert {$cur_mem < 10000 + $orig_mem}

        # Read nothing
        set fd [$rd channel]
        assert_equal {} [$rd rawread]
    }
    """
    r.run("config", "set", "latency-tracking", "no")
    r.run("config", "set", "client-output-buffer-limit", "normal 100000 0 0")
    item = string("repeat", "x", 1000)
    i = 0
    while i < 150:
        r.run("lpush", "mylist", item)
        i += 1
    orig_mem = s("used_memory")
    rd = ValkeyTestClient.create_from(r)
    rd.run("client", "setname", "mybiglist")
    assert rd.run("read") == "OK"
    rd.run("lrange", "mylist", 0, -1)
    rd.run("flush")
    time.sleep(100 / 1000)
    clients = r.run("client", "list")
    assert_no_match("*name=mybiglist*", clients)
    cur_mem = s("used_memory")
    assert cur_mem < (10000 + orig_mem)
    fd = rd.run("channel")
    assert "" == rd.run("rawread")


def test_no_response_for_multi_commands_in_pipeline_if_client_output_buffer_limit_is_enforced(
    r: ValkeyTestClient,
) -> None:
    """
    test {No response for multi commands in pipeline if client output buffer limit is enforced} {
        r config set client-output-buffer-limit {normal 100000 0 0}
        set value [string repeat "x" 10000]
        r set bigkey $value
        set rd1 [valkey_deferring_client]
        set rd2 [valkey_deferring_client]
        $rd2 client setname multicommands
        assert_equal "OK" [$rd2 read]

        # Let the server sleep 1s firstly
        $rd1 debug sleep 1
        $rd1 flush
        after 100

        # Create a pipeline of commands that will be processed in one socket read.
        # It is important to use one write, in TLS mode independent writes seem
        # to wait for response from the server.
        # Total size should be less than OS socket buffer, the server can
        # execute all commands in this pipeline when it wakes up.
        set buf ""
        for {set i 0} {$i < 15} {incr i} {
            append buf "set $i $i\r\n"
            append buf "get $i\r\n"
            append buf "del $i\r\n"
            # One bigkey is 10k, total response size must be more than 100k
            append buf "get bigkey\r\n"
        }
        $rd2 write $buf
        $rd2 flush
        after 100

        # Reds must wake up if it can send reply
        assert_equal "PONG" [r ping]
        set clients [r client list]
        assert_no_match "*name=multicommands*" $clients
        assert_equal {} [$rd2 rawread]
    }
    """
    r.run("config", "set", "client-output-buffer-limit", "normal 100000 0 0")
    value = string("repeat", "x", 10000)
    r.run("set", "bigkey", value)
    rd1 = ValkeyTestClient.create_from(r)
    rd2 = ValkeyTestClient.create_from(r)
    rd2.run("client", "setname", "multicommands")
    assert "OK" == rd2.run("read")
    rd1.run("debug", "sleep", 1)
    rd1.run("flush")
    time.sleep(100 / 1000)
    buf = ""
    i = 0
    while i < 15:
        append("buf", f"set {i} {i}\r\n")
        append("buf", f"get {i}\r\n")
        append("buf", f"del {i}\r\n")
        append("buf", "get bigkey\r\n")
        i += 1
    rd2.run("write", buf)
    rd2.run("flush")
    time.sleep(100 / 1000)
    assert "PONG" == r.run("ping")
    clients = r.run("client", "list")
    assert_no_match("*name=multicommands*", clients)
    assert "" == rd2.run("rawread")


def test_execute_transactions_completely_even_if_client_output_buffer_limit_is_enforced(r: ValkeyTestClient) -> None:
    """
    test {Execute transactions completely even if client output buffer limit is enforced} {
        r config set client-output-buffer-limit {normal 100000 0 0}
        # Total size of all items must be more than 100k
        set item [string repeat "x" 1000]
        for {set i 0} {$i < 150} {incr i} {
            r lpush mylist2 $item
        }

        # Output buffer limit is enforced during executing transaction
        r client setname transactionclient
        r set k1 v1
        r multi
        r set k2 v2
        r get k2
        r lrange mylist2 0 -1
        r set k3 v3
        r del k1
        catch {[r exec]} e
        assert_match "*I/O error*" $e
        reconnect
        set clients [r client list]
        assert_no_match "*name=transactionclient*" $clients

        # Transactions should be executed completely
        assert_equal {} [r get k1]
        assert_equal "v2" [r get k2]
        assert_equal "v3" [r get k3]
    }
    """
    r.run("config", "set", "client-output-buffer-limit", "normal 100000 0 0")
    item = string("repeat", "x", 1000)
    i = 0
    while i < 150:
        r.run("lpush", "mylist2", item)
        i += 1
    r.run("client", "setname", "transactionclient")
    r.run("set", "k1", "v1")
    r.run("multi")
    r.run("set", "k2", "v2")
    r.run("get", "k2")
    r.run("lrange", "mylist2", 0, -1)
    r.run("set", "k3", "v3")
    r.run("del", "k1")
    try:
        e = r.run("exec")
    except Exception as _catch_err:
        e = str(_catch_err)
    assert fnmatch(str(e), "*I/O error*")
    reconnect()
    clients = r.run("client", "list")
    assert_no_match("*name=transactionclient*", clients)
    assert "" == r.run("get", "k1")
    assert "v2" == r.run("get", "k2")
    assert "v3" == r.run("get", "k3")


def test_obuf_limit_hrandfield_with_huge_count_stopped_mid_run(r: ValkeyTestClient) -> None:
    """
    test "Obuf limit, HRANDFIELD with huge count stopped mid-run" {
        r config set client-output-buffer-limit {normal 1000000 0 0}
        r hset myhash a b
        catch {r hrandfield myhash -999999999} e
        assert_match "*I/O error*" $e
        reconnect
    }
    """
    r.run("config", "set", "client-output-buffer-limit", "normal 1000000 0 0")
    r.run("hset", "myhash", "a", "b")
    try:
        e = r.run("hrandfield", "myhash", -999999999)
    except Exception as _catch_err:
        e = str(_catch_err)
    assert fnmatch(str(e), "*I/O error*")
    reconnect()


def test_obuf_limit_keys_stopped_mid_run(r: ValkeyTestClient) -> None:
    """
    test "Obuf limit, KEYS stopped mid-run" {
        r config set client-output-buffer-limit {normal 100000 0 0}
        populate 1000 "long-key-name-prefix-of-100-chars-------------------------------------------------------------------"
        catch {r keys *} e
        assert_match "*I/O error*" $e
        reconnect
    }
    """
    r.run("config", "set", "client-output-buffer-limit", "normal 100000 0 0")
    populate(
        1000, "long-key-name-prefix-of-100-chars-------------------------------------------------------------------"
    )
    try:
        e = r.run("keys", "*")
    except Exception as _catch_err:
        e = str(_catch_err)
    assert fnmatch(str(e), "*I/O error*")
    reconnect()


# --- stubs for unimplemented TCL helpers ---


def append(*args):
    raise NotImplementedError("append")


def assert_no_match(*args):
    raise NotImplementedError("assert_no_match")


def clock(*args):
    raise NotImplementedError("clock")


def expr(*args):
    raise NotImplementedError("expr")


def if_(*args):
    raise NotImplementedError("if_")


def populate(*args):
    raise NotImplementedError("populate")


def reconnect(*args):
    raise NotImplementedError("reconnect")


def s(*args):
    raise NotImplementedError("s")


def string(*args):
    raise NotImplementedError("string")


def while_(*args):
    raise NotImplementedError("while_")
