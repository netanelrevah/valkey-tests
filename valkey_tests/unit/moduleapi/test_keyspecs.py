# ruff: noqa: PLR2004, ANN001, ANN002, ANN201

from fnmatch import fnmatch

import pytest

from tests.valkey_test_client import ValkeyTestClient

"""
set testmodule file normalize tests/modules/keyspecs.so
"""

pytestmark = [pytest.mark.modules]


"""
r module load testmodule
"""


def test_module_key_specs_no_spec_only_legacy_triple(r: ValkeyTestClient) -> None:
    """
    test "Module key specs: No spec, only legacy triple" {
        set reply [lindex [r command info kspec.none] 0]
        # Verify (first, last, step) and not movablekeys
        assert_equal [lindex $reply 2] {module}
        assert_equal [lindex $reply 3] 1
        assert_equal [lindex $reply 4] -1
        assert_equal [lindex $reply 5] 2
        # Verify key-spec auto-generated from the legacy triple
        set keyspecs [lindex $reply 8]
        assert_equal [llength $keyspecs] 1
        assert_equal [lindex $keyspecs 0] {flags {RW access update} begin_search {type index spec {index 1}} find_keys {type range spec {lastkey -1 keystep 2 limit 0}}}
        assert_equal [r command getkeys kspec.none key1 val1 key2 val2] {key1 key2}
    }
    """
    reply = r.run("command", "info", "kspec.none")[0]
    assert reply[2] == "module"
    assert reply[3] == 1
    assert reply[4] == -1
    assert reply[5] == 2
    keyspecs = reply[8]
    assert len(keyspecs) == 1
    assert (
        keyspecs[0]
        == "flags {RW access update} begin_search {type index spec {index 1}} find_keys {type range spec {lastkey -1 keystep 2 limit 0}}"
    )
    assert r.run("command", "getkeys", "kspec.none", "key1", "val1", "key2", "val2") == "key1 key2"


def test_module_key_specs_no_spec_only_legacy_triple_with_getkeys_api(r: ValkeyTestClient) -> None:
    """
    test "Module key specs: No spec, only legacy triple with getkeys-api" {
        set reply [lindex [r command info kspec.nonewithgetkeys] 0]
        # Verify (first, last, step) and movablekeys
        assert_equal [lindex $reply 2] {module movablekeys}
        assert_equal [lindex $reply 3] 1
        assert_equal [lindex $reply 4] -1
        assert_equal [lindex $reply 5] 2
        # Verify key-spec auto-generated from the legacy triple
        set keyspecs [lindex $reply 8]
        assert_equal [llength $keyspecs] 1
        assert_equal [lindex $keyspecs 0] {flags {RW access update variable_flags} begin_search {type index spec {index 1}} find_keys {type range spec {lastkey -1 keystep 2 limit 0}}}
        assert_equal [r command getkeys kspec.nonewithgetkeys key1 val1 key2 val2] {key1 key2}
    }
    """
    reply = r.run("command", "info", "kspec.nonewithgetkeys")[0]
    assert reply[2] == "module movablekeys"
    assert reply[3] == 1
    assert reply[4] == -1
    assert reply[5] == 2
    keyspecs = reply[8]
    assert len(keyspecs) == 1
    assert (
        keyspecs[0]
        == "flags {RW access update variable_flags} begin_search {type index spec {index 1}} find_keys {type range spec {lastkey -1 keystep 2 limit 0}}"
    )
    assert r.run("command", "getkeys", "kspec.nonewithgetkeys", "key1", "val1", "key2", "val2") == "key1 key2"


def test_module_key_specs_two_ranges(r: ValkeyTestClient) -> None:
    """
    test "Module key specs: Two ranges" {
        set reply [lindex [r command info kspec.tworanges] 0]
        # Verify (first, last, step) and not movablekeys
        assert_equal [lindex $reply 2] {module}
        assert_equal [lindex $reply 3] 1
        assert_equal [lindex $reply 4] 2
        assert_equal [lindex $reply 5] 1
        # Verify key-specs
        set keyspecs [lindex $reply 8]
        assert_equal [lindex $keyspecs 0] {flags {RO access} begin_search {type index spec {index 1}} find_keys {type range spec {lastkey 0 keystep 1 limit 0}}}
        assert_equal [lindex $keyspecs 1] {flags {RW update} begin_search {type index spec {index 2}} find_keys {type range spec {lastkey 0 keystep 1 limit 0}}}
        assert_equal [r command getkeys kspec.tworanges foo bar baz quux] {foo bar}
    }
    """
    reply = r.run("command", "info", "kspec.tworanges")[0]
    assert reply[2] == "module"
    assert reply[3] == 1
    assert reply[4] == 2
    assert reply[5] == 1
    keyspecs = reply[8]
    assert (
        keyspecs[0]
        == "flags {RO access} begin_search {type index spec {index 1}} find_keys {type range spec {lastkey 0 keystep 1 limit 0}}"
    )
    assert (
        keyspecs[1]
        == "flags {RW update} begin_search {type index spec {index 2}} find_keys {type range spec {lastkey 0 keystep 1 limit 0}}"
    )
    assert r.run("command", "getkeys", "kspec.tworanges", "foo", "bar", "baz", "quux") == "foo bar"


def test_module_key_specs_two_ranges_with_gap(r: ValkeyTestClient) -> None:
    """
    test "Module key specs: Two ranges with gap" {
        set reply [lindex [r command info kspec.tworangeswithgap] 0]
        # Verify (first, last, step) and movablekeys
        assert_equal [lindex $reply 2] {module movablekeys}
        assert_equal [lindex $reply 3] 1
        assert_equal [lindex $reply 4] 1
        assert_equal [lindex $reply 5] 1
        # Verify key-specs
        set keyspecs [lindex $reply 8]
        assert_equal [lindex $keyspecs 0] {flags {RO access} begin_search {type index spec {index 1}} find_keys {type range spec {lastkey 0 keystep 1 limit 0}}}
        assert_equal [lindex $keyspecs 1] {flags {RW update} begin_search {type index spec {index 3}} find_keys {type range spec {lastkey 0 keystep 1 limit 0}}}
        assert_equal [r command getkeys kspec.tworangeswithgap foo bar baz quux] {foo baz}
    }
    """
    reply = r.run("command", "info", "kspec.tworangeswithgap")[0]
    assert reply[2] == "module movablekeys"
    assert reply[3] == 1
    assert reply[4] == 1
    assert reply[5] == 1
    keyspecs = reply[8]
    assert (
        keyspecs[0]
        == "flags {RO access} begin_search {type index spec {index 1}} find_keys {type range spec {lastkey 0 keystep 1 limit 0}}"
    )
    assert (
        keyspecs[1]
        == "flags {RW update} begin_search {type index spec {index 3}} find_keys {type range spec {lastkey 0 keystep 1 limit 0}}"
    )
    assert r.run("command", "getkeys", "kspec.tworangeswithgap", "foo", "bar", "baz", "quux") == "foo baz"


def test_module_key_specs_keyword_only_spec_clears_the_legacy_triple(r: ValkeyTestClient) -> None:
    """
    test "Module key specs: Keyword-only spec clears the legacy triple" {
        set reply [lindex [r command info kspec.keyword] 0]
        # Verify (first, last, step) and movablekeys
        assert_equal [lindex $reply 2] {module movablekeys}
        assert_equal [lindex $reply 3] 0
        assert_equal [lindex $reply 4] 0
        assert_equal [lindex $reply 5] 0
        # Verify key-specs
        set keyspecs [lindex $reply 8]
        assert_equal [lindex $keyspecs 0] {flags {RO access} begin_search {type keyword spec {keyword KEYS startfrom 1}} find_keys {type range spec {lastkey -1 keystep 1 limit 0}}}
        assert_equal [r command getkeys kspec.keyword foo KEYS bar baz] {bar baz}
    }
    """
    reply = r.run("command", "info", "kspec.keyword")[0]
    assert reply[2] == "module movablekeys"
    assert reply[3] == 0
    assert reply[4] == 0
    assert reply[5] == 0
    keyspecs = reply[8]
    assert (
        keyspecs[0]
        == "flags {RO access} begin_search {type keyword spec {keyword KEYS startfrom 1}} find_keys {type range spec {lastkey -1 keystep 1 limit 0}}"
    )
    assert r.run("command", "getkeys", "kspec.keyword", "foo", "KEYS", "bar", "baz") == "bar baz"


def test_module_key_specs_complex_specs_case_1(r: ValkeyTestClient) -> None:
    """
    test "Module key specs: Complex specs, case 1" {
        set reply [lindex [r command info kspec.complex1] 0]
        # Verify (first, last, step) and movablekeys
        assert_equal [lindex $reply 2] {module movablekeys}
        assert_equal [lindex $reply 3] 1
        assert_equal [lindex $reply 4] 1
        assert_equal [lindex $reply 5] 1
        # Verify key-specs
        set keyspecs [lindex $reply 8]
        assert_equal [lindex $keyspecs 0] {flags RO begin_search {type index spec {index 1}} find_keys {type range spec {lastkey 0 keystep 1 limit 0}}}
        assert_equal [lindex $keyspecs 1] {flags {RW update} begin_search {type keyword spec {keyword STORE startfrom 2}} find_keys {type range spec {lastkey 0 keystep 1 limit 0}}}
        assert_equal [lindex $keyspecs 2] {flags {RO access} begin_search {type keyword spec {keyword KEYS startfrom 2}} find_keys {type keynum spec {keynumidx 0 firstkey 1 keystep 1}}}
        assert_equal [r command getkeys kspec.complex1 foo dummy KEYS 1 bar baz STORE quux] {foo quux bar}
    }
    """
    reply = r.run("command", "info", "kspec.complex1")[0]
    assert reply[2] == "module movablekeys"
    assert reply[3] == 1
    assert reply[4] == 1
    assert reply[5] == 1
    keyspecs = reply[8]
    assert (
        keyspecs[0]
        == "flags RO begin_search {type index spec {index 1}} find_keys {type range spec {lastkey 0 keystep 1 limit 0}}"
    )
    assert (
        keyspecs[1]
        == "flags {RW update} begin_search {type keyword spec {keyword STORE startfrom 2}} find_keys {type range spec {lastkey 0 keystep 1 limit 0}}"
    )
    assert (
        keyspecs[2]
        == "flags {RO access} begin_search {type keyword spec {keyword KEYS startfrom 2}} find_keys {type keynum spec {keynumidx 0 firstkey 1 keystep 1}}"
    )
    assert (
        r.run("command", "getkeys", "kspec.complex1", "foo", "dummy", "KEYS", 1, "bar", "baz", "STORE", "quux")
        == "foo quux bar"
    )


def test_module_key_specs_complex_specs_case_2(r: ValkeyTestClient) -> None:
    """
    test "Module key specs: Complex specs, case 2" {
        set reply [lindex [r command info kspec.complex2] 0]
        # Verify (first, last, step) and movablekeys
        assert_equal [lindex $reply 2] {module movablekeys}
        assert_equal [lindex $reply 3] 1
        assert_equal [lindex $reply 4] 2
        assert_equal [lindex $reply 5] 1
        # Verify key-specs
        set keyspecs [lindex $reply 8]
        assert_equal [lindex $keyspecs 0] {flags {RW update} begin_search {type keyword spec {keyword STORE startfrom 5}} find_keys {type range spec {lastkey 0 keystep 1 limit 0}}}
        assert_equal [lindex $keyspecs 1] {flags {RO access} begin_search {type index spec {index 1}} find_keys {type range spec {lastkey 0 keystep 1 limit 0}}}
        assert_equal [lindex $keyspecs 2] {flags {RO access} begin_search {type index spec {index 2}} find_keys {type range spec {lastkey 0 keystep 1 limit 0}}}
        assert_equal [lindex $keyspecs 3] {flags {RW update} begin_search {type index spec {index 3}} find_keys {type keynum spec {keynumidx 0 firstkey 1 keystep 1}}}
        assert_equal [lindex $keyspecs 4] {flags {RW update} begin_search {type keyword spec {keyword MOREKEYS startfrom 5}} find_keys {type range spec {lastkey -1 keystep 1 limit 0}}}
        assert_equal [r command getkeys kspec.complex2 foo bar 2 baz quux banana STORE dst dummy MOREKEYS hey ho] {dst foo bar baz quux hey ho}
    }
    """
    reply = r.run("command", "info", "kspec.complex2")[0]
    assert reply[2] == "module movablekeys"
    assert reply[3] == 1
    assert reply[4] == 2
    assert reply[5] == 1
    keyspecs = reply[8]
    assert (
        keyspecs[0]
        == "flags {RW update} begin_search {type keyword spec {keyword STORE startfrom 5}} find_keys {type range spec {lastkey 0 keystep 1 limit 0}}"
    )
    assert (
        keyspecs[1]
        == "flags {RO access} begin_search {type index spec {index 1}} find_keys {type range spec {lastkey 0 keystep 1 limit 0}}"
    )
    assert (
        keyspecs[2]
        == "flags {RO access} begin_search {type index spec {index 2}} find_keys {type range spec {lastkey 0 keystep 1 limit 0}}"
    )
    assert (
        keyspecs[3]
        == "flags {RW update} begin_search {type index spec {index 3}} find_keys {type keynum spec {keynumidx 0 firstkey 1 keystep 1}}"
    )
    assert (
        keyspecs[4]
        == "flags {RW update} begin_search {type keyword spec {keyword MOREKEYS startfrom 5}} find_keys {type range spec {lastkey -1 keystep 1 limit 0}}"
    )
    assert (
        r.run(
            "command",
            "getkeys",
            "kspec.complex2",
            "foo",
            "bar",
            2,
            "baz",
            "quux",
            "banana",
            "STORE",
            "dst",
            "dummy",
            "MOREKEYS",
            "hey",
            "ho",
        )
        == "dst foo bar baz quux hey ho"
    )


def test_module_command_list_filtering(r: ValkeyTestClient) -> None:
    """
    test "Module command list filtering" {
        ;# Note: we piggyback this tcl file to test the general functionality of command list filtering
        set reply [r command list filterby module keyspecs]
        assert_equal [lsort $reply] {kspec.complex1 kspec.complex2 kspec.keyword kspec.none kspec.nonewithgetkeys kspec.tworanges kspec.tworangeswithgap}
        assert_equal [r command getkeys kspec.complex2 foo bar 2 baz quux banana STORE dst dummy MOREKEYS hey ho] {dst foo bar baz quux hey ho}
    }
    """
    reply = r.run("command", "list", "filterby", "module", "keyspecs")
    assert (
        sorted(reply)
        == "kspec.complex1 kspec.complex2 kspec.keyword kspec.none kspec.nonewithgetkeys kspec.tworanges kspec.tworangeswithgap"
    )
    assert (
        r.run(
            "command",
            "getkeys",
            "kspec.complex2",
            "foo",
            "bar",
            2,
            "baz",
            "quux",
            "banana",
            "STORE",
            "dst",
            "dummy",
            "MOREKEYS",
            "hey",
            "ho",
        )
        == "dst foo bar baz quux hey ho"
    )


def test_command_getkeysandflags_correctly_reports_module_key_spec_without_flags(r: ValkeyTestClient) -> None:
    """
    test {COMMAND GETKEYSANDFLAGS correctly reports module key-spec without flags} {
        r command getkeysandflags kspec.none key1 val1 key2 val2
    } {{key1 {RW access update}} {key2 {RW access update}}}
    """
    assert (
        r.run("command", "getkeysandflags", "kspec.none", "key1", "val1", "key2", "val2")
        == "{key1 {RW access update}} {key2 {RW access update}}"
    )


def test_command_getkeysandflags_correctly_reports_module_key_spec_with_flags(r: ValkeyTestClient) -> None:
    """
    test {COMMAND GETKEYSANDFLAGS correctly reports module key-spec with flags} {
        r command getkeysandflags kspec.nonewithgetkeys key1 val1 key2 val2
    } {{key1 {RO access}} {key2 {RO access}}}
    """
    assert (
        r.run("command", "getkeysandflags", "kspec.nonewithgetkeys", "key1", "val1", "key2", "val2")
        == "{key1 {RO access}} {key2 {RO access}}"
    )


def test_command_getkeysandflags_correctly_reports_module_key_spec_flags(r: ValkeyTestClient) -> None:
    """
    test {COMMAND GETKEYSANDFLAGS correctly reports module key-spec flags} {
        r command getkeysandflags kspec.keyword keys key1 key2 key3
    } {{key1 {RO access}} {key2 {RO access}} {key3 {RO access}}}
    """
    assert (
        r.run("command", "getkeysandflags", "kspec.keyword", "keys", "key1", "key2", "key3")
        == "{key1 {RO access}} {key2 {RO access}} {key3 {RO access}}"
    )


"""
r ACL setuser testuser +@all %R~read* %W~write* %RW~rw*
"""


def test_module_key_specs_no_spec_only_legacy_triple_acl(r: ValkeyTestClient) -> None:
    """
    test "Module key specs: No spec, only legacy triple - ACL" {
        # legacy triple didn't provide flags, so they require both read and write
        assert_equal "OK" [r ACL DRYRUN testuser kspec.none rw val1]
        assert_match {*has no permissions to access the 'read' key*} [r ACL DRYRUN testuser kspec.none read val1]
        assert_match {*has no permissions to access the 'write' key*} [r ACL DRYRUN testuser kspec.none write val1]
    }
    """
    assert "OK" == r.run("ACL", "DRYRUN", "testuser", "kspec.none", "rw", "val1")
    assert fnmatch(
        str(r.run("ACL", "DRYRUN", "testuser", "kspec.none", "read", "val1")),
        "*has no permissions to access the 'read' key*",
    )
    assert fnmatch(
        str(r.run("ACL", "DRYRUN", "testuser", "kspec.none", "write", "val1")),
        "*has no permissions to access the 'write' key*",
    )


def test_module_key_specs_tworanges_acl(r: ValkeyTestClient) -> None:
    """
    test "Module key specs: tworanges - ACL" {
        assert_equal "OK" [r ACL DRYRUN testuser kspec.tworanges read write]
        assert_equal "OK" [r ACL DRYRUN testuser kspec.tworanges rw rw]
        assert_match {*has no permissions to access the 'read' key*} [r ACL DRYRUN testuser kspec.tworanges rw read]
        assert_match {*has no permissions to access the 'write' key*} [r ACL DRYRUN testuser kspec.tworanges write rw]
    }
    """
    assert "OK" == r.run("ACL", "DRYRUN", "testuser", "kspec.tworanges", "read", "write")
    assert "OK" == r.run("ACL", "DRYRUN", "testuser", "kspec.tworanges", "rw", "rw")
    assert fnmatch(
        str(r.run("ACL", "DRYRUN", "testuser", "kspec.tworanges", "rw", "read")),
        "*has no permissions to access the 'read' key*",
    )
    assert fnmatch(
        str(r.run("ACL", "DRYRUN", "testuser", "kspec.tworanges", "write", "rw")),
        "*has no permissions to access the 'write' key*",
    )


@pytest.mark.parametrize(["cmd"], [("kspec.none"), ("kspec.tworanges")])
def test_cmd_command_will_not_be_marked_with_movablekeys(r: ValkeyTestClient, cmd) -> None:
    """
    test "$cmd command will not be marked with movablekeys" {
        set info [lindex [r command info $cmd] 0]
        assert_no_match {*movablekeys*} [lindex $info 2]
    }
    """
    info = r.run("command", "info", cmd)[0]
    assert_no_match("*movablekeys*", info[2])


@pytest.mark.parametrize(
    ["cmd"], [("kspec.keyword"), ("kspec.complex1"), ("kspec.complex2"), ("kspec.nonewithgetkeys")]
)
def test_cmd_command_is_marked_with_movablekeys(r: ValkeyTestClient, cmd) -> None:
    """
    test "$cmd command is marked with movablekeys" {
        set info [lindex [r command info $cmd] 0]
        assert_match {*movablekeys*} [lindex $info 2]
    }
    """
    info = r.run("command", "info", cmd)[0]
    assert fnmatch(str(info[2]), "*movablekeys*")


def test_unload_the_module_keyspecs(r: ValkeyTestClient) -> None:
    """
    test "Unload the module - keyspecs" {
        assert_equal {OK} [r module unload keyspecs]
    }
    """
    assert "OK" == r.run("module", "unload", "keyspecs")


# --- stubs for unimplemented TCL helpers ---


def assert_no_match(*args):
    raise NotImplementedError("assert_no_match")
