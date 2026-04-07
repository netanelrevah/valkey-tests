# ruff: noqa: PLR2004, F841, N806, ANN002, ANN201
import time

import pytest

from tests.valkey_test_client import ValkeyTestClient

"""
proc client_idle_sec {name} {
    set clients [split [r client list] "\r\n"]
    set c [lsearch -inline $clients *name=$name*]
    assert {[regexp {idle=([0-9]+)} $c - idle]}
    return $idle
}
"""


"""
proc client_query_buffer {name} {
    set clients [split [r client list] "\r\n"]
    set c [lsearch -inline $clients *name=$name*]
    if {[string length $c] > 0} {
        assert {[regexp {qbuf=([0-9]+)} $c - qbuf]}
        assert {[regexp {qbuf-free=([0-9]+)} $c - qbuf_free]}
        return [expr $qbuf + $qbuf_free]
    }
    return 0
}
"""

pytestmark = [pytest.mark.querybuf_slow]


"""
r config set hz 100
"""


def test_query_buffer_resized_correctly(r: ValkeyTestClient) -> None:
    """
    test "query buffer resized correctly" {
        set rd [valkey_deferring_client]

        $rd client setname test_client
        $rd read

        # Make sure query buff has size of 0 bytes at start as the client uses the shared qb.
        assert {[client_query_buffer test_client] == 0}

        # Pause cron to prevent premature shrinking (timing issue).
        r debug pause-cron 1

        # Send partial command to client to make sure it doesn't use the shared qb.
        $rd write "*3\r\n\$3\r\nset\r\n\$2\r\na"
        $rd flush
        # Wait for the client to start using a private query buffer.
        wait_for_condition 1000 10 {
            [client_query_buffer test_client] > 0
        } else {
            fail "client should start using a private query buffer"
        }

        # send the rest of the command
        $rd write "a\r\n\$1\r\nb\r\n"
        $rd flush
        assert_equal {OK} [$rd read]

        set orig_test_client_qbuf [client_query_buffer test_client]
        # Make sure query buff has less than the peak resize threshold (PROTO_RESIZE_THRESHOLD) 32k
        # but at least the basic IO reading buffer size (PROTO_IOBUF_LEN) 16k
        set MAX_QUERY_BUFFER_SIZE [expr 32768 + 2] ; # 32k + 2, allowing for potential greedy allocation of (16k + 1) * 2 bytes for the query buffer.
        assert {$orig_test_client_qbuf >= 16384 && $orig_test_client_qbuf <= $MAX_QUERY_BUFFER_SIZE}

        # Allow shrinking to occur
        r debug pause-cron 0

        # Check that the initial query buffer is resized after 2 sec
        wait_for_condition 1000 10 {
            [client_idle_sec test_client] >= 3 && [client_query_buffer test_client] < $orig_test_client_qbuf
        } else {
            fail "query buffer was not resized"
        }
        $rd close
    }
    """
    rd = ValkeyTestClient.create_from(r)
    rd.run("client", "setname", "test_client")
    rd.run("read")
    assert client_query_buffer("test_client") == 0
    r.run("debug", "pause-cron", 1)
    rd.run("write", "*3\r\n$3\r\nset\r\n$2\r\na")
    rd.run("flush")
    wait_for_condition(
        1000,
        10,
        lambda: client_query_buffer("test_client") > 0,
        lambda: fail("client should start using a private query buffer"),
    )
    rd.run("write", "a\r\n$1\r\nb\r\n")
    rd.run("flush")
    assert "OK" == rd.run("read")
    orig_test_client_qbuf = client_query_buffer("test_client")
    MAX_QUERY_BUFFER_SIZE = expr(32768, "+", 2)
    assert (orig_test_client_qbuf >= 16384) and (orig_test_client_qbuf <= MAX_QUERY_BUFFER_SIZE)
    r.run("debug", "pause-cron", 0)
    wait_for_condition(
        1000,
        10,
        lambda: (client_idle_sec("test_client") >= 3) and (client_query_buffer("test_client") < orig_test_client_qbuf),
        lambda: fail("query buffer was not resized"),
    )
    rd.run("close")


@pytest.mark.xfail(reason="not implemented")
def test_query_buffer_resized_correctly_when_not_idle(r: ValkeyTestClient) -> None:
    """
    test "query buffer resized correctly when not idle" {
        # Pause cron to prevent premature shrinking (timing issue).
        r debug pause-cron 1

        # Memory will increase by more than 32k due to client query buffer.
        set rd [valkey_client]
        $rd client setname test_client

        # Create a large query buffer (more than PROTO_RESIZE_THRESHOLD - 32k)
        $rd set x [string repeat A 400000]

        # Make sure query buff is larger than the peak resize threshold (PROTO_RESIZE_THRESHOLD) 32k
        set orig_test_client_qbuf [client_query_buffer test_client]
        assert {$orig_test_client_qbuf > 32768}

        r debug pause-cron 0

        # Wait for qbuf to shrink due to lower peak
        set t [clock milliseconds]
        while true {
            # Write something smaller, so query buf peak can shrink
            $rd set x [string repeat A 100]
            set new_test_client_qbuf [client_query_buffer test_client]
            if {$new_test_client_qbuf < $orig_test_client_qbuf && $new_test_client_qbuf > 0} { break }
            if {[expr [clock milliseconds] - $t] > 1000} { break }
            after 10
        }
        # Validate qbuf shrunk but isn't 0 since we maintain room based on latest peak
        assert {[client_query_buffer test_client] > 0 && [client_query_buffer test_client] < $orig_test_client_qbuf}
        $rd close
    } {0} {needs:debug}
    """
    r.run("debug", "pause-cron", 1)
    rd = ValkeyTestClient.create_from(r)
    rd.run("client", "setname", "test_client")
    rd.run("set", "x", string("repeat", "A", 400000))
    orig_test_client_qbuf = client_query_buffer("test_client")
    assert orig_test_client_qbuf > 32768
    r.run("debug", "pause-cron", 0)
    t = clock("milliseconds")
    while_(
        "true",
        "            # Write something smaller, so query buf peak can shrink\n            $rd set x [string repeat A 100]\n            set new_test_client_qbuf [client_query_buffer test_client]\n            if {$new_test_client_qbuf < $orig_test_client_qbuf && $new_test_client_qbuf > 0} { break } \n            if {[expr [clock milliseconds] - $t] > 1000} { break }\n            after 10\n        ",
    )
    assert (client_query_buffer("test_client") > 0) and (client_query_buffer("test_client") < orig_test_client_qbuf)
    # TODO: $rd close
    assert False


def test_query_buffer_resized_correctly_with_fat_argv(r: ValkeyTestClient) -> None:
    """
    test "query buffer resized correctly with fat argv" {
        set rd [valkey_client]
        $rd client setname test_client
        $rd write "*3\r\n\$3\r\nset\r\n\$1\r\na\r\n\$1000000\r\n"
        $rd flush

        after 200
        # Send the start of the arg and make sure the client is not using shared qb for it rather a private buf of > 1000000 size.
        $rd write "a"
        $rd flush

        after 20
        if {[client_query_buffer test_client] < 1000000} {
            fail "query buffer should not be resized when client idle time smaller than 2s"
        }

        # Check that the query buffer is resized after 2 sec
        wait_for_condition 1000 10 {
            [client_idle_sec test_client] >= 3 && [client_query_buffer test_client] < 1000000
        } else {
            fail "query buffer should be resized when client idle time bigger than 2s"
        }

        $rd close
    }
    """
    rd = ValkeyTestClient.create_from(r)
    rd.run("client", "setname", "test_client")
    rd.run("write", "*3\r\n$3\r\nset\r\n$1\r\na\r\n$1000000\r\n")
    rd.run("flush")
    time.sleep(200 / 1000)
    rd.run("write", "a")
    rd.run("flush")
    time.sleep(20 / 1000)
    if client_query_buffer("test_client") < 1000000:
        fail("query buffer should not be resized when client idle time smaller than 2s")
    wait_for_condition(
        1000,
        10,
        lambda: (client_idle_sec("test_client") >= 3) and (client_query_buffer("test_client") < 1000000),
        lambda: fail("query buffer should be resized when client idle time bigger than 2s"),
    )
    rd.run("close")


# --- stubs for unimplemented TCL helpers ---


def client_idle_sec(*args):
    raise NotImplementedError("client_idle_sec")


def client_query_buffer(*args):
    raise NotImplementedError("client_query_buffer")


def clock(*args):
    raise NotImplementedError("clock")


def expr(*args):
    raise NotImplementedError("expr")


def fail(*args):
    raise NotImplementedError("fail")


def string(*args):
    raise NotImplementedError("string")


def wait_for_condition(*args):
    raise NotImplementedError("wait_for_condition")


def while_(*args):
    raise NotImplementedError("while_")
