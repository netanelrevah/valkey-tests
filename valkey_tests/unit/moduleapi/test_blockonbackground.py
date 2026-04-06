import pytest

from tests.valkey_test_client import ValkeyTestClient

"""
set testmodule file normalize tests/modules/blockonbackground.so
"""


"""
source tests/support/util.tcl
"""


"""
proc latency_percentiles_usec {cmd} {
    return [latencyrstat_percentiles $cmd r]
}
"""

pytestmark = [pytest.mark.modules]


"""
r module load testmodule
"""


@pytest.mark.xfail(reason="not implemented")
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
    r.run("slowlog", "reset")
    r.run("config", "set", "slowlog-log-slower-than", 200000)
    if "!$::no_latency":
        assert r.run("slowlog", "len") == 0
    r.run("block.debug", 0, 10000)
    if "!$::no_latency":
        assert r.run("slowlog", "len") == 0
    r.run("config", "resetstat")
    r.run("config", "set", "latency-tracking", "yes")
    r.run("config", "set", "latency-tracking-info-percentiles", "50.0")
    r.run("block.debug", 200, 10000)
    if "!$::no_latency":
        assert r.run("slowlog", "len") == 1
    # TODO: set cmdstatline cmdrstat block.debug r
    # TODO: set latencystatline_debug latency_percentiles_usec block.debug
    # TODO: regexp "calls=1,usec=(.*?),usec_per_call=(.*?),rejected_calls=0,failed_calls=0" cmdstatline -> usec usec_per_call
    # TODO: regexp "p50=(.+\..+)" latencystatline _debug -> p50
    # TODO: assert {$usec >= 100000}
    # TODO: assert {$usec_per_call >= 100000}
    # TODO: assert {$p50 >= 100000}


@pytest.mark.xfail(reason="not implemented")
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
    r.run("slowlog", "reset")
    r.run("config", "set", "slowlog-log-slower-than", 200000)
    if "!$::no_latency":
        assert r.run("slowlog", "len") == 0
    r.run("block.debug", 0, 20000)
    if "!$::no_latency":
        assert r.run("slowlog", "len") == 0
    r.run("config", "resetstat")
    r.run("block.debug", 20000, 500)
    if "!$::no_latency":
        assert r.run("slowlog", "len") == 1
    # TODO: set cmdstatline cmdrstat block.debug r
    # TODO: regexp "calls=1,usec=(.*?),usec_per_call=(.*?),rejected_calls=0,failed_calls=0" cmdstatline usec usec_per_call
    # TODO: assert {$usec >= 250000}
    # TODO: assert {$usec_per_call >= 250000}


@pytest.mark.xfail(reason="not implemented")
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
    r.run("slowlog", "reset")
    r.run("config", "set", "slowlog-log-slower-than", 200000)
    if "!$::no_latency":
        assert r.run("slowlog", "len") == 0
    r.run("block.double_debug", 0)
    if "!$::no_latency":
        assert r.run("slowlog", "len") == 0
    r.run("config", "resetstat")
    r.run("block.double_debug", 100)
    if "!$::no_latency":
        assert r.run("slowlog", "len") == 1
    # TODO: set cmdstatline cmdrstat block.double_debug r
    # TODO: regexp "calls=1,usec=(.*?),usec_per_call=(.*?),rejected_calls=0,failed_calls=0" cmdstatline usec usec_per_call
    # TODO: assert {$usec >= 60000}
    # TODO: assert {$usec_per_call >= 60000}


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
    r.run("slowlog", "reset")
    r.run("config", "set", "slowlog-log-slower-than", 200000)
    if "!$::no_latency":
        assert r.run("slowlog", "len") == 0
    r.run("block.debug_no_track", 200, 1000)
    if "!$::no_latency":
        assert r.run("slowlog", "len") == 0


@pytest.mark.xfail(reason="not implemented")
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
    # TODO: set rd valkey_deferring_client
    # TODO: $rd client id
    # TODO: set id $rd read
    # TODO: $rd block.block 20000
    # TODO: wait_for_condition 50 100 {
    #       [r block.is_blocked] == 1
    #   } else {
    #       fail "Module did not block"
    #   }
    # TODO: assert_equal 1 r client unblock $id
    # TODO: assert_match {*Timed out*} $rd read
    # TODO: $rd block.block 0
    # TODO: wait_for_condition 50 100 {
    #       [r block.is_blocked] == 1
    #   } else {
    #       fail "Module did not block"
    #   }
    # TODO: assert_equal 0 r client unblock $id
    assert "OK" == r.run("block.release", "foobar")
    # TODO: assert_equal "foobar" $rd read
