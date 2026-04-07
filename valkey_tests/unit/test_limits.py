# ruff: noqa: PLR2004, F841, ANN002, ANN201

import pytest

from tests.valkey_test_client import ValkeyTestClient

pytestmark = [pytest.mark.limits_network_external_skip]


"""
if {$::tls} {
    set expected_code "*I/O error*"
} else {
    set expected_code "*ERR max*reached*"
}
"""


def test_check_if_maxclients_works_refusing_connections(r: ValkeyTestClient) -> None:
    """
    test {Check if maxclients works refusing connections} {
        set c 0
        catch {
            while {$c < 50} {
                incr c
                set rd [valkey_deferring_client]
                $rd ping
                $rd read
                after 100
            }
        } e
        assert {$c > 8 && $c <= 10}
        set e
    } expected_code
    """
    c = 0
    try:
        while_(
            "$c < 50",
            "                incr c\n                set rd [valkey_deferring_client]\n                $rd ping\n                $rd read\n                after 100\n            ",
        )
    except Exception as _catch_err:
        e = str(_catch_err)
    assert (c > 8) and (c <= 10)
    set_("e")


# --- stubs for unimplemented TCL helpers ---


def set_(*args):
    raise NotImplementedError("set_")


def while_(*args):
    raise NotImplementedError("while_")
