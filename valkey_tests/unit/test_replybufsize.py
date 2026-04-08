# ruff: noqa: PLR2004, ANN002, ANN201

import pytest

from tests.valkey_test_client import ValkeyTestClient

"""
proc get_reply_buffer_size {cname} {
    set clients [split [string trim [r client list]] "\r\n"]
    set c [lsearch -inline $clients *name=$cname*]
    if {![regexp rbs=(\[a-zA-Z0-9-\]+) $c - rbufsize]} {
        error "field rbs not found in $c"
    }
    return $rbufsize
}
"""

pytestmark = [pytest.mark.replybufsize]


def test_verify_reply_buffer_limits(r: ValkeyTestClient) -> None:
    """
    test {verify reply buffer limits} {
        # In order to reduce test time we can set the peak reset time very low
        r debug replybuffer peak-reset-time 100

        # Create a simple idle test client
        variable tc [valkey_client]
        $tc client setname test_client

        # make sure the client is idle for 1 seconds to make it shrink the reply buffer
        wait_for_condition 10 100 {
            [get_reply_buffer_size test_client] >= 1024 && [get_reply_buffer_size test_client] < 2046
        } else {
            set rbs [get_reply_buffer_size test_client]
            fail "reply buffer of idle client is $rbs after 1 seconds"
        }

        r set bigval [string repeat x 32768]

        # In order to reduce test time we can set the peak reset time very low
        r debug replybuffer peak-reset-time never

        wait_for_condition 10 100 {
            [$tc get bigval ; get_reply_buffer_size test_client] >= 16384 && [get_reply_buffer_size test_client] < 32768
        } else {
            set rbs [get_reply_buffer_size test_client]
            fail "reply buffer of busy client is $rbs after 1 seconds"
        }

        # Restore the peak reset time to default
        r debug replybuffer peak-reset-time reset

        $tc close
    } {0} {needs:debug}
    """
    r.run("config", "set", "min-io-threads-avoid-copy-reply", 0)
    r.run("config", "set", "min-string-size-avoid-copy-reply", 0)
    r.run("config", "set", "min-string-size-avoid-copy-reply-threaded", 0)
    r.run("debug", "replybuffer", "peak-reset-time", 100)
    tc = ValkeyTestClient.create_from(r)
    tc.run("client", "setname", "test_client")
    wait_for_condition(
        10,
        100,
        lambda: (get_reply_buffer_size("test_client") >= 1024) and (get_reply_buffer_size("test_client") < 2046),
    )
    r.run("set", "bigval", string("repeat", "x", 32768))
    r.run("debug", "replybuffer", "peak-reset-time", "never")
    wait_for_condition(
        10,
        100,
        "            [$tc get bigval ; get_reply_buffer_size test_client] >= 16384 && [get_reply_buffer_size test_client] < 32768\n        ",
        "else",
        '            set rbs [get_reply_buffer_size test_client]\n            fail "reply buffer of busy client is $rbs after 1 seconds"\n        ',
    )
    r.run("debug", "replybuffer", "peak-reset-time", "reset")
    tc.run("close")


# --- stubs for unimplemented TCL helpers ---


def fail(*args):
    raise NotImplementedError("fail")


def get_reply_buffer_size(*args):
    raise NotImplementedError("get_reply_buffer_size")


def string(*args):
    raise NotImplementedError("string")


def wait_for_condition(*args):
    raise NotImplementedError("wait_for_condition")
