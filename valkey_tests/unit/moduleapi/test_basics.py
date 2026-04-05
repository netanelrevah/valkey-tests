from fnmatch import fnmatch

import pytest

from tests.valkey_test_client import ValkeyTestClient

"""
set testmodule file normalize tests/modules/basics.so
"""

pytestmark = [pytest.mark.modules]


"""
r module load testmodule
"""


def test_test_module_api_basics(r: ValkeyTestClient) -> None:
    """
    test {test module api basics} {
        r test.basics
    } {ALL TESTS PASSED}
    """
    assert r.run("test.basics") == "ALL TESTS PASSED"


def test_test_rm_call_auto_mode(r: ValkeyTestClient) -> None:
    """
    test {test rm_call auto mode} {
        r hello 2
        set reply [r test.rmcallautomode]
        assert_equal [lindex $reply 0] f1
        assert_equal [lindex $reply 1] v1
        assert_equal [lindex $reply 2] f2
        assert_equal [lindex $reply 3] v2
        r hello 3
        set reply [r test.rmcallautomode]
        assert_equal [dict get $reply f1] v1
        assert_equal [dict get $reply f2] v2
    }
    """
    r.run("hello", 2)
    reply = r.run("test.rmcallautomode")
    assert reply[0] == "f1"
    assert reply[1] == "v1"
    assert reply[2] == "f2"
    assert reply[3] == "v2"
    r.run("hello", 3)
    reply = r.run("test.rmcallautomode")
    assert reply["f1"] == "v1"
    assert reply["f2"] == "v2"


@pytest.mark.xfail(reason="not implemented")
def test_test_get_resp(r: ValkeyTestClient) -> None:
    """
    test {test get resp} {
        foreach resp {3 2} {
            if {[lsearch $::denytags "resp3"] >= 0} {
                if {$resp == 3} {continue}
            } elseif {$::force_resp3} {
                if {$resp == 2} {continue}
            }
            r hello $resp
            set reply [r test.getresp]
            assert_equal $reply $resp
            r hello 2
        }
    }
    """
    # TODO: foreach resp {3 2} {
    #       if {[lsearch $::denytags "resp3"] >= 0} {
    #           if {$resp == 3} {continue}
    #       } elseif {$::force_resp3} {
    #           if {$resp == 2} {continue}
    #       }
    #       r hello $resp
    #       set reply [r test.getresp]
    #       assert_equal $reply $resp
    #       r hello 2
    #   }


@pytest.mark.xfail(reason="not implemented")
def test_busy_module_name(r: ValkeyTestClient) -> None:
    """
    test "Busy module name" {
        assert_error {ERR Error loading the extension. Please check the server logs.} {r module load $testmodule}
        verify_log_message 0 "*Module name is busy*" 0
    }
    """
    # TODO: assert_error {ERR Error loading the extension. Please check the server logs.} {r module load $testmodule}
    # TODO: verify_log_message 0 "*Module name is busy*" 0


def test_test_latency(r: ValkeyTestClient) -> None:
    """
    test "test latency" {
        r config set latency-monitor-threshold 0
        r latency reset
        r test.latency 0
        r test.latency 1
        assert_equal {} [r latency latest]
        assert_equal {} [r latency history test]

        r config set latency-monitor-threshold 1
        r test.latency 0
        assert_equal 0 [llength [r latency history test]]
        r test.latency 1
        assert_match {*test * 1 1*} [r latency latest]
        r test.latency 2
        assert_match {*test * 2 2*} [r latency latest]
    }
    """
    r.run("config", "set", "latency-monitor-threshold", 0)
    r.run("latency", "reset")
    r.run("test.latency", 0)
    r.run("test.latency", 1)
    assert "" == r.run("latency", "latest")
    assert "" == r.run("latency", "history", "test")
    r.run("config", "set", "latency-monitor-threshold", 1)
    r.run("test.latency", 0)
    assert 0 == len(r.run("latency", "history", "test"))
    r.run("test.latency", 1)
    assert fnmatch(str(r.run("latency", "latest")), "*test * 1 1*")
    r.run("test.latency", 2)
    assert fnmatch(str(r.run("latency", "latest")), "*test * 2 2*")


def test_unload_the_module_basics(r: ValkeyTestClient) -> None:
    """
    test "Unload the module - basics" {
        assert_equal {OK} [r module unload test]
    }
    """
    assert "OK" == r.run("module", "unload", "test")


pytestmark = [pytest.mark.modules_external_skip]


@pytest.mark.xfail(reason="not implemented")
def test_module_command_disabled(r: ValkeyTestClient) -> None:
    """
    test {module command disabled} {
        assert_error "NOAUTH *" {r module load $testmodule}

        r auth mypass
        assert_error "ERR *MODULE command not allowed*" {r module load $testmodule}
    }
    """
    # TODO: assert_error "NOAUTH *" {r module load $testmodule}
    r.run("auth", "mypass")
    # TODO: assert_error "ERR *MODULE command not allowed*" {r module load $testmodule}
