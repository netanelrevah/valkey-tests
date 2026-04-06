# ruff: noqa: PLR2004, F841, ANN002, ANN201

from fnmatch import fnmatch

import pytest

from tests.valkey_test_client import ValkeyTestClient

"""
set testmodule file normalize tests/modules/infotest.so
"""


"""
proc field {info property} {
    if {[regexp "\r\n$property:(.*?)\r\n" $info _ value]} {
        set _ $value
    }
}
"""

pytestmark = [pytest.mark.modules]


"""
r module load testmodule log-key 0
"""


@pytest.mark.xfail(reason="not implemented")
def test_module_reading_info(r: ValkeyTestClient) -> None:
    """
    test {module reading info} {
        # check string, integer and float fields
        assert_equal [r info.gets replication role] "master"
        assert_equal [r info.getc replication role] "master"
        assert_equal [r info.geti stats expired_keys] 0
        assert_equal [r info.getd stats expired_stale_perc] 0

        # check signed and unsigned
        assert_equal [r info.geti infotest infotest_global] -2
        assert_equal [r info.getu infotest infotest_uglobal] -2

        # the above are always 0, try module info that is non-zero
        assert_equal [r info.geti infotest_italian infotest_due] 2
        set tre [r info.getd infotest_italian infotest_tre]
        assert {$tre > 3.2 && $tre < 3.4 }

        # search using the wrong section
        catch { [r info.gets badname redis_version] } e
        assert_match {*not found*} $e

        # check that section filter works
        assert { [string match "*usec_per_call*" [r info.gets all cmdstat_info.gets] ] }
        catch { [r info.gets default cmdstat_info.gets] ] } e
        assert_match {*not found*} $e
    }
    """
    assert r.run("info.gets", "replication", "role") == "master"
    assert r.run("info.getc", "replication", "role") == "master"
    assert r.run("info.geti", "stats", "expired_keys") == 0
    assert r.run("info.getd", "stats", "expired_stale_perc") == 0
    assert r.run("info.geti", "infotest", "infotest_global") == -2
    assert r.run("info.getu", "infotest", "infotest_uglobal") == -2
    assert r.run("info.geti", "infotest_italian", "infotest_due") == 2
    tre = r.run("info.getd", "infotest_italian", "infotest_tre")
    assert (tre > 3.2) and (tre < 3.4)
    catch(" [r info.gets badname redis_version] ", "e")
    # TODO: assert_match {*not found*} e
    assert string("match", "*usec_per_call*", r.run("info.gets", "all", "cmdstat_info.gets"))
    catch(" [r info.gets default cmdstat_info.gets] ] ", "e")
    # TODO: assert_match {*not found*} e


def test_module_info_all(r: ValkeyTestClient) -> None:
    """
    test {module info all} {
        set info [r info all]
        # info all does not contain modules
        assert { ![string match "*Spanish*" $info] }
        assert { ![string match "*infotest_*" $info] }
        assert { [string match "*used_memory*" $info] }
    }
    """
    info = r.run("info", "all")
    assert_(' ![string match "*Spanish*" $info] ')
    assert_(' ![string match "*infotest_*" $info] ')
    assert string("match", "*used_memory*", info)


def test_module_info_all_infotest(r: ValkeyTestClient) -> None:
    """
    test {module info all infotest} {
        set info [r info all infotest]
        # info all infotest should contain both ALL and the module information
        assert { [string match "*Spanish*" $info] }
        assert { [string match "*infotest_*" $info] }
        assert { [string match "*used_memory*" $info] }
    }
    """
    info = r.run("info", "all", "infotest")
    assert string("match", "*Spanish*", info)
    assert string("match", "*infotest_*", info)
    assert string("match", "*used_memory*", info)


@pytest.mark.xfail(reason="not implemented")
def test_module_info_everything(r: ValkeyTestClient) -> None:
    """
    test {module info everything} {
        set info [r info everything]
        # info everything contains all default sections, but not ones for crash report
        assert { [string match "*infotest_global*" $info] }
        assert { [string match "*Spanish*" $info] }
        assert { [string match "*Italian*" $info] }
        assert { [string match "*used_memory*" $info] }
        assert { ![string match "*Klingon*" $info] }
        field $info infotest_dos
    } {2}
    """
    info = r.run("info", "everything")
    assert string("match", "*infotest_global*", info)
    assert string("match", "*Spanish*", info)
    assert string("match", "*Italian*", info)
    assert string("match", "*used_memory*", info)
    assert_(' ![string match "*Klingon*" $info] ')
    # TODO: field info infotest_dos
    assert False


def test_module_info_modules(r: ValkeyTestClient) -> None:
    """
    test {module info modules} {
        set info [r info modules]
        # info all does not contain modules
        assert { [string match "*Spanish*" $info] }
        assert { [string match "*infotest_global*" $info] }
        assert { ![string match "*used_memory*" $info] }
    }
    """
    info = r.run("info", "modules")
    assert string("match", "*Spanish*", info)
    assert string("match", "*infotest_global*", info)
    assert_(' ![string match "*used_memory*" $info] ')


@pytest.mark.xfail(reason="not implemented")
def test_module_info_one_module(r: ValkeyTestClient) -> None:
    """
    test {module info one module} {
        set info [r info INFOtest] ;# test case insensitive compare
        # info all does not contain modules
        assert { [string match "*Spanish*" $info] }
        assert { ![string match "*used_memory*" $info] }
        field $info infotest_global
    } {-2}
    """
    info = r.run("info", "INFOtest")
    assert string("match", "*Spanish*", info)
    assert_(' ![string match "*used_memory*" $info] ')
    # TODO: field info infotest_global
    assert False


@pytest.mark.xfail(reason="not implemented")
def test_module_info_one_section(r: ValkeyTestClient) -> None:
    """
    test {module info one section} {
        set info [r info INFOtest_SpanisH] ;# test case insensitive compare
        assert { ![string match "*used_memory*" $info] }
        assert { ![string match "*Italian*" $info] }
        assert { ![string match "*infotest_global*" $info] }
        field $info infotest_uno
    } {one}
    """
    info = r.run("info", "INFOtest_SpanisH")
    assert_(' ![string match "*used_memory*" $info] ')
    assert_(' ![string match "*Italian*" $info] ')
    assert_(' ![string match "*infotest_global*" $info] ')
    # TODO: field info infotest_uno
    assert False


@pytest.mark.xfail(reason="not implemented")
def test_module_info_dict(r: ValkeyTestClient) -> None:
    """
    test {module info dict} {
        set info [r info infotest_keyspace]
        set keyspace [field $info infotest_db0]
        set keys [scan [regexp -inline {keys\=([\d]*)} $keyspace] keys=%d]
    } {3}
    """
    info = r.run("info", "infotest_keyspace")
    keyspace = field(info, "infotest_db0")
    # TODO: set keys scan [regexp -inline {keys\=([\d]*)} $keyspace] keys=%d
    assert False


def test_module_info_unsafe_fields(r: ValkeyTestClient) -> None:
    """
    test {module info unsafe fields} {
        set info [r info infotest_unsafe]
        assert_match {*infotest_unsafe_field:value=1*} $info
    }
    """
    info = r.run("info", "infotest_unsafe")
    assert fnmatch(str(info), "*infotest_unsafe_field:value=1*")


def test_module_info_multiply_sections_without_all_everything_default_keywords(r: ValkeyTestClient) -> None:
    """
    test {module info multiply sections without all, everything, default keywords} {
        set info [r info replication INFOTEST]
        assert { [string match "*Spanish*" $info] }
        assert { ![string match "*used_memory*" $info] }
        assert { [string match "*repl_offset*" $info] }
    }
    """
    info = r.run("info", "replication", "INFOTEST")
    assert string("match", "*Spanish*", info)
    assert_(' ![string match "*used_memory*" $info] ')
    assert string("match", "*repl_offset*", info)


def test_module_info_multiply_sections_with_all_keyword_and_modules(r: ValkeyTestClient) -> None:
    """
    test {module info multiply sections with all keyword and modules} {
        set info [r info all modules]
        assert { [string match "*cluster*" $info] }
        assert { [string match "*cmdstat_info*" $info] }
        assert { [string match "*infotest_global*" $info] }
    }
    """
    info = r.run("info", "all", "modules")
    assert string("match", "*cluster*", info)
    assert string("match", "*cmdstat_info*", info)
    assert string("match", "*infotest_global*", info)


@pytest.mark.xfail(reason="not implemented")
def test_module_info_multiply_sections_with_everything_keyword(r: ValkeyTestClient) -> None:
    """
    test {module info multiply sections with everything keyword} {
        set info [r info replication everything cpu]
        assert { [string match "*client_recent*" $info] }
        assert { [string match "*cmdstat_info*" $info] }
        assert { [string match "*Italian*" $info] }
        # check that we didn't get the same info twice
        assert { ![string match "*used_cpu_user_children*used_cpu_user_children*" $info] }
        assert { ![string match "*Italian*Italian*" $info] }
        field $info infotest_dos
    } {2}
    """
    info = r.run("info", "replication", "everything", "cpu")
    assert string("match", "*client_recent*", info)
    assert string("match", "*cmdstat_info*", info)
    assert string("match", "*Italian*", info)
    assert_(' ![string match "*used_cpu_user_children*used_cpu_user_children*" $info] ')
    assert_(' ![string match "*Italian*Italian*" $info] ')
    # TODO: field info infotest_dos
    assert False


def test_unload_the_module_infotest(r: ValkeyTestClient) -> None:
    """
    test "Unload the module - infotest" {
        assert_equal {OK} [r module unload infotest]
    }
    """
    assert "OK" == r.run("module", "unload", "infotest")


# --- stubs for unimplemented TCL helpers ---


def assert_(*args):
    raise NotImplementedError("assert_")


def catch(*args):
    raise NotImplementedError("catch")


def field(*args):
    raise NotImplementedError("field")


def string(*args):
    raise NotImplementedError("string")
