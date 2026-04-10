# ruff: noqa: PLR2004, ANN002, ANN201

import pytest

from tests.valkey_test_client import ValkeyTestClient

testmodule = "tests/modules/test_lazyfree.so"

pytestmark = [pytest.mark.modules]


def test_modules_allocated_memory_can_be_reclaimed_in_the_background(r: ValkeyTestClient) -> None:
    """
    test "modules allocated memory can be reclaimed in the background" {
        set orig_mem [s used_memory]
        set rd [valkey_deferring_client]

        # LAZYFREE_THRESHOLD is 64
        for {set i 0} {$i < 10000} {incr i} {
            $rd lazyfreelink.insert lazykey $i
        }

        for {set j 0} {$j < 10000} {incr j} {
            $rd read
        }

        assert {[r lazyfreelink.len lazykey] == 10000}

        set peak_mem [s used_memory]
        assert {[r unlink lazykey] == 1}
        assert {$peak_mem > $orig_mem+10000}
        wait_for_condition 50 100 {
            [s used_memory] < $peak_mem &&
            [s used_memory] < $orig_mem*2 &&
            [string match {*lazyfreed_objects:1*} [r info Memory]]
        } else {
            fail "Module memory is not reclaimed by UNLINK"
        }
    }
    """
    r.run("module", "load", testmodule)
    orig_mem = s("used_memory")
    rd = ValkeyTestClient.create_from(r)
    i = 0
    while i < 10000:
        rd.run("lazyfreelink.insert", "lazykey", i)
        i += 1
    j = 0
    while j < 10000:
        rd.run("read")
        j += 1
    assert r.run("lazyfreelink.len", "lazykey") == 10000
    peak_mem = s("used_memory")
    assert r.run("unlink", "lazykey") == 1
    assert_("$peak_mem > $orig_mem+10000")
    wait_for_condition(
        50,
        100,
        lambda: (
            ((s("used_memory") < peak_mem) and (s("used_memory") < (orig_mem * 2)))
            and string("match", "*lazyfreed_objects:1*", r.run("info", "Memory"))
        ),
        lambda: fail("Module memory is not reclaimed by UNLINK"),
    )


# --- stubs for unimplemented TCL helpers ---


def assert_(*args):
    raise NotImplementedError("assert_")


def fail(*args):
    raise NotImplementedError("fail")


def s(*args):
    raise NotImplementedError("s")


def string(*args):
    raise NotImplementedError("string")


def wait_for_condition(*args):
    raise NotImplementedError("wait_for_condition")
