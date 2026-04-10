# ruff: noqa: PLR2004, ANN002, ANN201

from fnmatch import fnmatch

import pytest

from tests.valkey_test_client import ValkeyTestClient

testmodule = "tests/modules/blockonbackground.so"


"""
source tests/support/util.tcl
"""


"""
proc latency_percentiles_usec {cmd} {
    return [latencyrstat_percentiles $cmd r]
}
"""

pytestmark = [pytest.mark.modules]


def test_blocked_clients_time_tracking_check_blocked_command_that_uses_redismodule_blockedclientmeasuretimestart_is_tracking_background_time(
    r: ValkeyTestClient,
) -> None:
    """
    test { blocked clients time tracking - check blocked command that uses RedisModule_BlockedClientMeasureTimeStart() is tracking background time} {
        r slowlog reset
        r config set slowlog-log-slower-than 200000
        if {!$::no_latency} {
            assert_equal [r slowlog len] 0
        }
        r block.debug 0 10000
        if {!$::no_latency} {
            assert_equal [r slowlog len] 0
        }
        r config resetstat
        r config set latency-tracking yes
        r config set latency-tracking-info-percentiles "50.0"
        r block.debug 200 10000
        if {!$::no_latency} {
            assert_equal [r slowlog len] 1
        }

        set cmdstatline [cmdrstat block.debug r]
        set latencystatline_debug [latency_percentiles_usec block.debug]

        regexp "calls=1,usec=(.*?),usec_per_call=(.*?),rejected_calls=0,failed_calls=0" $cmdstatline -> usec usec_per_call
        regexp "p50=(.+\..+)" $latencystatline_debug  -> p50
        assert {$usec >= 100000}
        assert {$usec_per_call >= 100000}
        assert {$p50 >= 100000}
    }
    """
    r.run("module", "load", testmodule)
    r.run("slowlog", "reset")
    r.run("config", "set", "slowlog-log-slower-than", 200000)
    if_("!$::no_latency", "            assert_equal [r slowlog len] 0\n        ")
    r.run("block.debug", 0, 10000)
    if_("!$::no_latency", "            assert_equal [r slowlog len] 0\n        ")
    r.run("config", "resetstat")
    r.run("config", "set", "latency-tracking", "yes")
    r.run("config", "set", "latency-tracking-info-percentiles", "50.0")
    r.run("block.debug", 200, 10000)
    if_("!$::no_latency", "            assert_equal [r slowlog len] 1\n        ")
    cmdstatline = cmdrstat("block.debug", "r")
    latencystatline_debug = latency_percentiles_usec("block.debug")
    regexp(
        "calls=1,usec=(.*?),usec_per_call=(.*?),rejected_calls=0,failed_calls=0",
        cmdstatline,
        "->",
        "usec",
        "usec_per_call",
    )
    regexp("p50=(.+..+)", latencystatline_debug, "->", "p50")
    assert usec >= 100000
    assert usec_per_call >= 100000
    assert p50 >= 100000


def test_blocked_clients_time_tracking_check_blocked_command_that_uses_redismodule_blockedclientmeasuretimestart_is_tracking_background_time_even_in_timeout(
    r: ValkeyTestClient,
) -> None:
    """
    test { blocked clients time tracking - check blocked command that uses RedisModule_BlockedClientMeasureTimeStart() is tracking background time even in timeout } {
        r slowlog reset
        r config set slowlog-log-slower-than 200000
        if {!$::no_latency} {
            assert_equal [r slowlog len] 0
        }
        r block.debug 0 20000
        if {!$::no_latency} {
            assert_equal [r slowlog len] 0
        }
        r config resetstat
        r block.debug 20000 500
        if {!$::no_latency} {
            assert_equal [r slowlog len] 1
        }

        set cmdstatline [cmdrstat block.debug r]

        regexp "calls=1,usec=(.*?),usec_per_call=(.*?),rejected_calls=0,failed_calls=0" $cmdstatline usec usec_per_call
        assert {$usec >= 250000}
        assert {$usec_per_call >= 250000}
    }
    """
    r.run("module", "load", testmodule)
    r.run("slowlog", "reset")
    r.run("config", "set", "slowlog-log-slower-than", 200000)
    if_("!$::no_latency", "            assert_equal [r slowlog len] 0\n        ")
    r.run("block.debug", 0, 20000)
    if_("!$::no_latency", "            assert_equal [r slowlog len] 0\n        ")
    r.run("config", "resetstat")
    r.run("block.debug", 20000, 500)
    if_("!$::no_latency", "            assert_equal [r slowlog len] 1\n        ")
    cmdstatline = cmdrstat("block.debug", "r")
    regexp(
        "calls=1,usec=(.*?),usec_per_call=(.*?),rejected_calls=0,failed_calls=0", cmdstatline, "usec", "usec_per_call"
    )
    assert usec >= 250000
    assert usec_per_call >= 250000


def test_blocked_clients_time_tracking_check_blocked_command_with_multiple_calls_redismodule_blockedclientmeasuretimestart_is_tracking_the_total_background_time(
    r: ValkeyTestClient,
) -> None:
    """
    test { blocked clients time tracking - check blocked command with multiple calls RedisModule_BlockedClientMeasureTimeStart()  is tracking the total background time } {
        r slowlog reset
        r config set slowlog-log-slower-than 200000
        if {!$::no_latency} {
            assert_equal [r slowlog len] 0
        }
        r block.double_debug 0
        if {!$::no_latency} {
            assert_equal [r slowlog len] 0
        }
        r config resetstat
        r block.double_debug 100
        if {!$::no_latency} {
            assert_equal [r slowlog len] 1
        }
        set cmdstatline [cmdrstat block.double_debug r]

        regexp "calls=1,usec=(.*?),usec_per_call=(.*?),rejected_calls=0,failed_calls=0" $cmdstatline usec usec_per_call
        assert {$usec >= 60000}
        assert {$usec_per_call >= 60000}
    }
    """
    r.run("module", "load", testmodule)
    r.run("slowlog", "reset")
    r.run("config", "set", "slowlog-log-slower-than", 200000)
    if_("!$::no_latency", "            assert_equal [r slowlog len] 0\n        ")
    r.run("block.double_debug", 0)
    if_("!$::no_latency", "            assert_equal [r slowlog len] 0\n        ")
    r.run("config", "resetstat")
    r.run("block.double_debug", 100)
    if_("!$::no_latency", "            assert_equal [r slowlog len] 1\n        ")
    cmdstatline = cmdrstat("block.double_debug", "r")
    regexp(
        "calls=1,usec=(.*?),usec_per_call=(.*?),rejected_calls=0,failed_calls=0", cmdstatline, "usec", "usec_per_call"
    )
    assert usec >= 60000
    assert usec_per_call >= 60000


def test_blocked_clients_time_tracking_check_blocked_command_without_calling_redismodule_blockedclientmeasuretimestart_is_not_reporting_background_time(
    r: ValkeyTestClient,
) -> None:
    """
    test { blocked clients time tracking - check blocked command without calling RedisModule_BlockedClientMeasureTimeStart() is not reporting background time } {
        r slowlog reset
        r config set slowlog-log-slower-than 200000
        if {!$::no_latency} {
            assert_equal [r slowlog len] 0
        }
        r block.debug_no_track 200 1000
        # ensure slowlog is still empty
        if {!$::no_latency} {
            assert_equal [r slowlog len] 0
        }
    }
    """
    r.run("module", "load", testmodule)
    r.run("slowlog", "reset")
    r.run("config", "set", "slowlog-log-slower-than", 200000)
    if_("!$::no_latency", "            assert_equal [r slowlog len] 0\n        ")
    r.run("block.debug_no_track", 200, 1000)
    if_("!$::no_latency", "            assert_equal [r slowlog len] 0\n        ")


def test_client_unblock_works_only_for_modules_with_timeout_support(r: ValkeyTestClient) -> None:
    """
    test "client unblock works only for modules with timeout support" {
        set rd [valkey_deferring_client]
        $rd client id
        set id [$rd read]

        # Block with a timeout function - may unblock
        $rd block.block 20000
        wait_for_condition 50 100 {
            [r block.is_blocked] == 1
        } else {
            fail "Module did not block"
        }

        assert_equal 1 [r client unblock $id]
        assert_match {*Timed out*} [$rd read]

        # Block without a timeout function - cannot unblock
        $rd block.block 0
        wait_for_condition 50 100 {
            [r block.is_blocked] == 1
        } else {
            fail "Module did not block"
        }

        assert_equal 0 [r client unblock $id]
        assert_equal "OK" [r block.release foobar]
        assert_equal "foobar" [$rd read]
    }
    """
    r.run("module", "load", testmodule)
    rd = ValkeyTestClient.create_from(r)
    rd.run("client", "id")
    id = rd.run("read")
    rd.run("block.block", 20000)
    wait_for_condition(50, 100, lambda: r.run("block.is_blocked") == 1, lambda: fail("Module did not block"))
    assert 1 == r.run("client", "unblock", id)
    assert fnmatch(str(rd.run("read")), "*Timed out*")
    rd.run("block.block", 0)
    wait_for_condition(50, 100, lambda: r.run("block.is_blocked") == 1, lambda: fail("Module did not block"))
    assert 0 == r.run("client", "unblock", id)
    assert "OK" == r.run("block.release", "foobar")
    assert "foobar" == rd.run("read")


# --- stubs for unimplemented TCL helpers ---


def cmdrstat(*args):
    raise NotImplementedError("cmdrstat")


def fail(*args):
    raise NotImplementedError("fail")


def if_(*args):
    raise NotImplementedError("if_")


def latency_percentiles_usec(*args):
    raise NotImplementedError("latency_percentiles_usec")


def regexp(*args):
    raise NotImplementedError("regexp")


def wait_for_condition(*args):
    raise NotImplementedError("wait_for_condition")
