# ruff: noqa: PLR2004, ANN002, ANN201
import time
from fnmatch import fnmatch

import pytest

from tests.valkey_test_client import ValkeyTestClient

testmodule = "tests/modules/timer.so"

pytestmark = [pytest.mark.modules]


def test_rm_createtimer_a_sequence_of_timers_work(r: ValkeyTestClient) -> None:
    """
    test {RM_CreateTimer: a sequence of timers work} {
        # We can't guarantee same-ms but we try using MULTI/EXEC
        r multi
        for {set i 0} {$i < 20} {incr i} {
            r test.createtimer 10 timer-incr-key
        }
        r exec

        after 500
        assert_equal 20 [r get timer-incr-key]
    }
    """
    r.run("module", "load", testmodule)
    r.run("multi")
    i = 0
    while i < 20:
        r.run("test.createtimer", 10, "timer-incr-key")
        i += 1
    r.run("exec")
    time.sleep(500 / 1000)
    assert 20 == r.run("get", "timer-incr-key")


def test_rm_gettimer_basic_sanity(r: ValkeyTestClient) -> None:
    """
    test {RM_GetTimer: basic sanity} {
        # Getting non-existing timer
        assert_equal {} [r test.gettimer 0]

        # Getting a real timer
        set id [r test.createtimer 10000 timer-incr-key]
        set info [r test.gettimer $id]

        assert_equal "timer-incr-key" [lindex $info 0]
        set remaining [lindex $info 1]
        assert {$remaining < 10000 && $remaining > 1}
        # Stop the timer after get timer test
        assert_equal 1 [r test.stoptimer $id]
    }
    """
    r.run("module", "load", testmodule)
    assert "" == r.run("test.gettimer", 0)
    id = r.run("test.createtimer", 10000, "timer-incr-key")
    info = r.run("test.gettimer", id)
    assert "timer-incr-key" == info[0]
    remaining = info[1]
    assert (remaining < 10000) and (remaining > 1)
    assert 1 == r.run("test.stoptimer", id)


def test_rm_stoptimer_basic_sanity(r: ValkeyTestClient) -> None:
    """
    test {RM_StopTimer: basic sanity} {
        r set "timer-incr-key" 0
        set id [r test.createtimer 1000 timer-incr-key]

        assert_equal 1 [r test.stoptimer $id]

        # Wait to be sure timer doesn't execute
        after 2000
        assert_equal 0 [r get timer-incr-key]

        # Stop non-existing timer
        assert_equal 0 [r test.stoptimer $id]
    }
    """
    r.run("module", "load", testmodule)
    r.run("set", "timer-incr-key", 0)
    id = r.run("test.createtimer", 1000, "timer-incr-key")
    assert 1 == r.run("test.stoptimer", id)
    time.sleep(2000 / 1000)
    assert 0 == r.run("get", "timer-incr-key")
    assert 0 == r.run("test.stoptimer", id)


def test_timer_appears_non_existing_after_it_fires(r: ValkeyTestClient) -> None:
    """
    test {Timer appears non-existing after it fires} {
        r set "timer-incr-key" 0
        set id [r test.createtimer 10 timer-incr-key]

        # verify timer fired
        after 500
        assert_equal 1 [r get timer-incr-key]

        # verify id does not exist
        assert_equal {} [r test.gettimer $id]
    }
    """
    r.run("module", "load", testmodule)
    r.run("set", "timer-incr-key", 0)
    id = r.run("test.createtimer", 10, "timer-incr-key")
    time.sleep(500 / 1000)
    assert 1 == r.run("get", "timer-incr-key")
    assert "" == r.run("test.gettimer", id)


def test_module_can_be_unloaded_when_timer_was_finished(r: ValkeyTestClient) -> None:
    """
    test "Module can be unloaded when timer was finished" {
        r set "timer-incr-key" 0
        r test.createtimer 500 timer-incr-key

        # Make sure the Timer has not been fired
        assert_equal 0 [r get timer-incr-key]
        # Module can not be unloaded since the timer was ongoing
        catch {r module unload timer} err
        assert_match {*the module holds timer that is not fired*} $err

        # Wait to be sure timer has been finished
        wait_for_condition 10 500 {
            [r get timer-incr-key] == 1
        } else {
            fail "Timer not fired"
        }

        # Timer fired, can be unloaded now.
        assert_equal {OK} [r module unload timer]
    }
    """
    r.run("module", "load", testmodule)
    r.run("set", "timer-incr-key", 0)
    r.run("test.createtimer", 500, "timer-incr-key")
    assert 0 == r.run("get", "timer-incr-key")
    try:
        err = r.run("module", "unload", "timer")
    except Exception as _catch_err:
        err = str(_catch_err)
    assert fnmatch(str(err), "*the module holds timer that is not fired*")
    wait_for_condition(10, 500, lambda: r.run("get", "timer-incr-key") == 1, lambda: fail("Timer not fired"))
    assert "OK" == r.run("module", "unload", "timer")


def test_module_can_be_unloaded_when_timer_was_stopped(r: ValkeyTestClient) -> None:
    """
    test "Module can be unloaded when timer was stopped" {
        r module load $testmodule
        r set "timer-incr-key" 0
        set id [r test.createtimer 5000 timer-incr-key]

        # Module can not be unloaded since the timer was ongoing
        catch {r module unload timer} err
        assert_match {*the module holds timer that is not fired*} $err

        # Stop the timer
        assert_equal 1 [r test.stoptimer $id]

        # Make sure the Timer has not been fired
        assert_equal 0 [r get timer-incr-key]

        # Timer has stopped, can be unloaded now.
        assert_equal {OK} [r module unload timer]
    }
    """
    r.run("module", "load", testmodule)
    r.run("module", "load", testmodule)
    r.run("set", "timer-incr-key", 0)
    id = r.run("test.createtimer", 5000, "timer-incr-key")
    try:
        err = r.run("module", "unload", "timer")
    except Exception as _catch_err:
        err = str(_catch_err)
    assert fnmatch(str(err), "*the module holds timer that is not fired*")
    assert 1 == r.run("test.stoptimer", id)
    assert 0 == r.run("get", "timer-incr-key")
    assert "OK" == r.run("module", "unload", "timer")


# --- stubs for unimplemented TCL helpers ---


def fail(*args):
    raise NotImplementedError("fail")


def wait_for_condition(*args):
    raise NotImplementedError("wait_for_condition")
