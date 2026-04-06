# ruff: noqa: PLR2004, F841, ANN002, ANN201

import pytest

from tests.valkey_test_client import ValkeyTestClient

"""
set testmodule file normalize tests/modules/test_lazyfree.so
"""

pytestmark = [pytest.mark.modules]


"""
r module load testmodule
"""


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
    orig_mem = s("used_memory")
    rd = valkey_deferring_client()
    for_("set i 0", "$i < 10000", "incr i", "            $rd lazyfreelink.insert lazykey $i\n        ")
    for_("set j 0", "$j < 10000", "incr j", "            $rd read \n        ")
    assert r.run("lazyfreelink.len", "lazykey") == 10000
    peak_mem = s("used_memory")
    assert r.run("unlink", "lazykey") == 1
    assert_("$peak_mem > $orig_mem+10000")
    wait_for_condition(
        50,
        100,
        "            [s used_memory] < $peak_mem &&\n            [s used_memory] < $orig_mem*2 &&\n            [string match {*lazyfreed_objects:1*} [r info Memory]]\n        ",
        "else",
        '            fail "Module memory is not reclaimed by UNLINK"\n        ',
    )


# --- stubs for unimplemented TCL helpers ---


def assert_(*args):
    raise NotImplementedError("assert_")


def for_(*args):
    raise NotImplementedError("for_")


def s(*args):
    raise NotImplementedError("s")


def valkey_deferring_client(*args):
    raise NotImplementedError("valkey_deferring_client")


def wait_for_condition(*args):
    raise NotImplementedError("wait_for_condition")
