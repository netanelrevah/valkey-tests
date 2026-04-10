from fnmatch import fnmatch

import pytest

from tests.valkey_test_client import ValkeyTestClient

testmodule = "tests/modules/eventloop.so"

pytestmark = [pytest.mark.modules]


def test_module_eventloop_sendbytes(r: ValkeyTestClient) -> None:
    """
    test "Module eventloop sendbytes" {
        assert_match "OK" [r test.sendbytes 5000000]
        assert_match "OK" [r test.sendbytes 2000000]
    }
    """
    r.run("module", "load", testmodule)
    assert fnmatch(str(r.run("test.sendbytes", 5000000)), "OK")
    assert fnmatch(str(r.run("test.sendbytes", 2000000)), "OK")


def test_module_eventloop_iteration(r: ValkeyTestClient) -> None:
    """
    test "Module eventloop iteration" {
        set iteration [r test.iteration]
        set next_iteration [r test.iteration]
        assert {$next_iteration > $iteration}
    }
    """
    r.run("module", "load", testmodule)
    iteration = r.run("test.iteration")
    next_iteration = r.run("test.iteration")
    assert next_iteration > iteration


def test_module_eventloop_sanity(r: ValkeyTestClient) -> None:
    """
    test "Module eventloop sanity" {
        r test.sanity
    }
    """
    r.run("module", "load", testmodule)
    r.run("test.sanity")


def test_module_eventloop_oneshot(r: ValkeyTestClient) -> None:
    """
    test "Module eventloop oneshot" {
        r test.oneshot
    }
    """
    r.run("module", "load", testmodule)
    r.run("test.oneshot")


def test_unload_the_module_eventloop(r: ValkeyTestClient) -> None:
    """
    test "Unload the module - eventloop" {
        assert_equal {OK} [r module unload eventloop]
    }
    """
    r.run("module", "load", testmodule)
    assert "OK" == r.run("module", "unload", "eventloop")
