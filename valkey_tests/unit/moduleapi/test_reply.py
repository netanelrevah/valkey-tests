# ruff: noqa: ANN002, ANN201

import pytest

from tests.valkey_test_client import ValkeyTestClient

"""
set testmodule file normalize tests/modules/reply.so
"""

pytestmark = [pytest.mark.modules]


def test_unload_the_module_replywith(r: ValkeyTestClient) -> None:
    """
    test "Unload the module - replywith" {
        assert_equal {OK} [r module unload replywith]
    }
    """
    assert "OK" == r.run("module", "unload", "replywith")


# --- stubs for unimplemented TCL helpers ---


def for_(*args):
    raise NotImplementedError("for_")


def if_(*args):
    raise NotImplementedError("if_")
