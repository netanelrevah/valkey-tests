# ruff: noqa: PLR2004

import pytest

from tests.valkey_test_client import ValkeyTestClient

"""
set testmodule file normalize tests/modules/mallocsize.so
"""

pytestmark = [pytest.mark.modules]


"""
r module load testmodule
"""


def test_mallocsize_of_raw_bytes(r: ValkeyTestClient) -> None:
    """
    test {MallocSize of raw bytes} {
        assert_equal [r mallocsize.setraw key 40] {OK}
        assert_morethan [r memory usage key] 40
    }
    """
    assert r.run("mallocsize.setraw", "key", 40) == "OK"
    assert r.run("memory", "usage", "key") > 40


def test_mallocsize_of_string(r: ValkeyTestClient) -> None:
    """
    test {MallocSize of string} {
        assert_equal [r mallocsize.setstr key abcdefg] {OK}
        assert_morethan [r memory usage key] 7 ;# Length of "abcdefg"
    }
    """
    assert r.run("mallocsize.setstr", "key", "abcdefg") == "OK"
    assert r.run("memory", "usage", "key") > 7


def test_mallocsize_of_dict(r: ValkeyTestClient) -> None:
    """
    test {MallocSize of dict} {
        assert_equal [r mallocsize.setdict key f1 v1 f2 v2] {OK}
        assert_morethan [r memory usage key] 8 ;# Length of "f1v1f2v2"
    }
    """
    assert r.run("mallocsize.setdict", "key", "f1", "v1", "f2", "v2") == "OK"
    assert r.run("memory", "usage", "key") > 8
