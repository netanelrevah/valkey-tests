# ruff: noqa: PLR2004, ANN002, ANN201

import pytest

from tests.valkey_test_client import ValkeyTestClient

"""
set testmodule file normalize tests/modules/fork.so
"""

pytestmark = [pytest.mark.modules]


def test_module_fork(r: ValkeyTestClient) -> None:
    """
    test {Module fork} {
        # the argument to fork.create is the exitcode on termination
        # the second argument to fork.create is passed to usleep
        r fork.create 3 100000 ;# 100ms
        wait_for_condition 20 100 {
            [r fork.exitcode] != -1
        } else {
            fail "fork didn't terminate"
        }
        r fork.exitcode
    } {3}
    """
    r.run("fork.create", 3, 100000)
    wait_for_condition(20, 100, lambda: r.run("fork.exitcode") != -1, lambda: fail("fork didn't terminate"))
    assert r.run("fork.exitcode") == "3"


def test_module_fork_kill(r: ValkeyTestClient) -> None:
    """
    test {Module fork kill} {
        # use a longer time to avoid the child exiting before being killed
        r fork.create 3 100000000 ;# 100s
        wait_for_condition 20 100 {
            [count_log_message 0 "fork child started"] == 2
        } else {
            fail "fork didn't start"
        }

        # module fork twice
        assert_error {Fork failed} {r fork.create 0 1}
        assert {[count_log_message 0 "Can't fork for module: Operation already in progress"] eq "1"}

        r fork.kill

        assert {[count_log_message 0 "Received SIGUSR1 in child"] eq "1"}
        # check that it wasn't printed again (the print belong to the previous test)
        assert {[count_log_message 0 "fork child exiting"] eq "1"}
    }
    """
    r.run("fork.create", 3, 100000000)
    wait_for_condition(
        20, 100, lambda: count_log_message(0, "fork child started") == 2, lambda: fail("fork didn't start")
    )
    with pytest.raises(Exception, match="Fork\\ failed"):
        r.run("fork.create", 0, 1)
    assert count_log_message(0, "Can't fork for module: Operation already in progress") == "1"
    r.run("fork.kill")
    assert count_log_message(0, "Received SIGUSR1 in child") == "1"
    assert count_log_message(0, "fork child exiting") == "1"


def test_unload_the_module_fork(r: ValkeyTestClient) -> None:
    """
    test "Unload the module - fork" {
        assert_equal {OK} [r module unload fork]
    }
    """
    assert "OK" == r.run("module", "unload", "fork")


# --- stubs for unimplemented TCL helpers ---


def count_log_message(*args):
    raise NotImplementedError("count_log_message")


def fail(*args):
    raise NotImplementedError("fail")


def wait_for_condition(*args):
    raise NotImplementedError("wait_for_condition")
