# ruff: noqa: F841

import pytest

from tests.valkey_test_client import ValkeyTestClient

"""
set testmodule file normalize tests/modules/defragtest.so
"""

pytestmark = [pytest.mark.modules]


"""
r module load testmodule 10000
"""


"""
r config set active-defrag-ignore-bytes 1
"""


"""
r config set active-defrag-threshold-lower 0
"""


"""
r config set active-defrag-cycle-min 99
"""


"""
catch {r config set activedefrag yes} e
"""


@pytest.mark.xfail(reason="not implemented")
@pytest.mark.skipif("", reason='{[r config get activedefrag] eq "activedefrag yes"}')
def test_module_defrag_simple_key_defrag_works(r: ValkeyTestClient) -> None:
    """
    test {Module defrag: simple key defrag works} {
        r frag.create key1 1 1000 0

        after 2000
        set info [r info defragtest_stats]
        assert {[getInfoProperty $info defragtest_datatype_attempts] > 0}
        assert_equal 0 [getInfoProperty $info defragtest_datatype_resumes]
    }
    """
    r.run("frag.create", "key1", 1, 1000, 0)
    # TODO: after 2000
    info = r.run("info", "defragtest_stats")
    # TODO: assert {[getInfoProperty $info defragtest_datatype_attempts] > 0}
    # TODO: assert_equal 0 getInfoProperty $info defragtest_datatype_resumes


@pytest.mark.xfail(reason="not implemented")
@pytest.mark.skipif("", reason='{[r config get activedefrag] eq "activedefrag yes"}')
def test_module_defrag_late_defrag_with_cursor_works(r: ValkeyTestClient) -> None:
    """
    test {Module defrag: late defrag with cursor works} {
        r flushdb
        r frag.resetstats

        # key can only be defragged in no less than 10 iterations
        # due to maxstep
        r frag.create key2 10000 100 1000

        after 2000
        set info [r info defragtest_stats]
        assert {[getInfoProperty $info defragtest_datatype_resumes] > 10}
        assert_equal 0 [getInfoProperty $info defragtest_datatype_wrong_cursor]
    }
    """
    r.run("flushdb")
    r.run("frag.resetstats")
    r.run("frag.create", "key2", 10000, 100, 1000)
    # TODO: after 2000
    info = r.run("info", "defragtest_stats")
    # TODO: assert {[getInfoProperty $info defragtest_datatype_resumes] > 10}
    # TODO: assert_equal 0 getInfoProperty $info defragtest_datatype_wrong_cursor


@pytest.mark.xfail(reason="not implemented")
@pytest.mark.skipif("", reason='{[r config get activedefrag] eq "activedefrag yes"}')
def test_module_defrag_global_defrag_works(r: ValkeyTestClient) -> None:
    """
    test {Module defrag: global defrag works} {
        r flushdb
        r frag.resetstats

        after 2000
        set info [r info defragtest_stats]
        assert {[getInfoProperty $info defragtest_global_attempts] > 0}
    }
    """
    r.run("flushdb")
    r.run("frag.resetstats")
    # TODO: after 2000
    info = r.run("info", "defragtest_stats")
    # TODO: assert {[getInfoProperty $info defragtest_global_attempts] > 0}
