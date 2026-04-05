# ruff: noqa: F841, RUF043

import pytest

from tests.valkey_test_client import ValkeyTestClient

"""
set testmodule file normalize tests/modules/datatype.so
"""

pytestmark = [pytest.mark.modules]


"""
r module load testmodule
"""


@pytest.mark.xfail(reason="not implemented")
def test_datatype_test_module_is_sane_get_or_set_work(r: ValkeyTestClient) -> None:
    """
    test {DataType: Test module is sane, GET/SET work.} {
        r datatype.set dtkey 100 stringval
        assert {[r datatype.get dtkey] eq {100 stringval}}
    }
    """
    r.run("datatype.set", "dtkey", 100, "stringval")
    # TODO: assert {[r datatype.get dtkey] eq {100 stringval}}


def test_test_blocking_of_datatype_creation_outside_of_onload(r: ValkeyTestClient) -> None:
    """
    test {test blocking of datatype creation outside of OnLoad} {
        assert_equal [r block.create.datatype.outside.onload] OK
    }
    """
    assert r.run("block.create.datatype.outside.onload") == "OK"


@pytest.mark.xfail(reason="not implemented")
def test_datatype_rm_savedatatypetostring_rm_loaddatatypefromstringencver_work(r: ValkeyTestClient) -> None:
    """
    test {DataType: RM_SaveDataTypeToString(), RM_LoadDataTypeFromStringEncver() work} {
        r datatype.set dtkey -1111 MyString
        set encoded [r datatype.dump dtkey]

        assert {[r datatype.restore dtkeycopy $encoded 4] eq {4}}
        assert {[r datatype.get dtkeycopy] eq {-1111 MyString}}
    }
    """
    r.run("datatype.set", "dtkey", -1111, "MyString")
    encoded = r.run("datatype.dump", "dtkey")
    # TODO: assert {[r datatype.restore dtkeycopy $encoded 4] eq {4}}
    # TODO: assert {[r datatype.get dtkeycopy] eq {-1111 MyString}}


@pytest.mark.xfail(reason="not implemented")
def test_datatype_handle_truncated_rm_loaddatatypefromstringencver(r: ValkeyTestClient) -> None:
    """
    test {DataType: Handle truncated RM_LoadDataTypeFromStringEncver()} {
        r datatype.set dtkey -1111 MyString
        set encoded [r datatype.dump dtkey]
        set truncated [string range $encoded 0 end-1]

        catch {r datatype.restore dtkeycopy $truncated 4} e
        set e
    } {*Invalid*}
    """
    r.run("datatype.set", "dtkey", -1111, "MyString")
    encoded = r.run("datatype.dump", "dtkey")
    # TODO: set truncated string range $encoded 0 end-1
    # TODO: catch {r datatype.restore dtkeycopy $truncated 4} e
    # TODO: set e
    assert False


@pytest.mark.xfail(reason="not implemented")
def test_datatype_moduletypereplacevalue_happy_path_works(r: ValkeyTestClient) -> None:
    """
    test {DataType: ModuleTypeReplaceValue() happy path works} {
        r datatype.set key-a 1 AAA
        r datatype.set key-b 2 BBB

        assert {[r datatype.swap key-a key-b] eq {OK}}
        assert {[r datatype.get key-a] eq {2 BBB}}
        assert {[r datatype.get key-b] eq {1 AAA}}
    }
    """
    r.run("datatype.set", "key-a", 1, "AAA")
    r.run("datatype.set", "key-b", 2, "BBB")
    # TODO: assert {[r datatype.swap key-a key-b] eq {OK}}
    # TODO: assert {[r datatype.get key-a] eq {2 BBB}}
    # TODO: assert {[r datatype.get key-b] eq {1 AAA}}


@pytest.mark.xfail(reason="not implemented")
def test_datatype_moduletypereplacevalue_fails_on_non_module_keys(r: ValkeyTestClient) -> None:
    """
    test {DataType: ModuleTypeReplaceValue() fails on non-module keys} {
        r datatype.set key-a 1 AAA
        r set key-b RedisString

        catch {r datatype.swap key-a key-b} e
        set e
    } {*ERR*}
    """
    r.run("datatype.set", "key-a", 1, "AAA")
    r.run("set", "key-b", "RedisString")
    # TODO: catch {r datatype.swap key-a key-b} e
    # TODO: set e
    assert False


@pytest.mark.xfail(reason="not implemented")
def test_datatype_copy_command_works_for_modules(r: ValkeyTestClient) -> None:
    """
    test {DataType: Copy command works for modules} {
        # Test failed copies
        r datatype.set answer-to-universe 42 AAA
        catch {r copy answer-to-universe answer2} e
        assert_match {*module key failed to copy*} $e

        # Our module's data type copy function copies the int value as-is
        # but appends /<from-key>/<to-key> to the string value so we can
        # track passed arguments.
        r datatype.set sourcekey 1234 AAA
        r copy sourcekey targetkey
        r datatype.get targetkey
    } {1234 AAA/sourcekey/targetkey}
    """
    r.run("datatype.set", "answer-to-universe", 42, "AAA")
    # TODO: catch {r copy answer-to-universe answer2} e
    # TODO: assert_match {*module key failed to copy*} e
    r.run("datatype.set", "sourcekey", 1234, "AAA")
    r.run("copy", "sourcekey", "targetkey")
    assert r.run("datatype.get", "targetkey") == "1234 AAA/sourcekey/targetkey"


@pytest.mark.xfail(reason="not implemented")
def test_datatype_slow_loading(r: ValkeyTestClient) -> None:
    """
    test {DataType: Slow Loading} {
        r config set busy-reply-threshold 5000 ;# make sure we're using a high default
        # trigger slow loading
        r datatype.slow_loading 1
        set rd [valkey_deferring_client]
        set start [clock clicks -milliseconds]
        $rd debug reload

        # wait till we know we're blocked inside the module
        wait_for_condition 50 100 {
            [r datatype.is_in_slow_loading] eq 1
        } else {
            fail "Failed waiting for slow loading to start"
        }

        # make sure we get LOADING error, and that we didn't get here late (not waiting for busy-reply-threshold)
        assert_error {*LOADING*} {r ping}
        assert_lessthan [expr [clock clicks -milliseconds]-$start] 2000

        # abort the blocking operation
        r datatype.slow_loading 0
        wait_for_condition 50 100 {
            [s loading] eq {0}
        } else {
            fail "Failed waiting for loading to end"
        }
        $rd read
        $rd close
    }
    """
    r.run("config", "set", "busy-reply-threshold", 5000)
    r.run("datatype.slow_loading", 1)
    # TODO: set rd valkey_deferring_client
    # TODO: set start clock clicks -milliseconds
    # TODO: $rd debug reload
    # TODO: wait_for_condition 50 100 {
    #       [r datatype.is_in_slow_loading] eq 1
    #   } else {
    #       fail "Failed waiting for slow loading to start"
    #   }
    with pytest.raises(Exception, match=".*LOADING.*"):
        r.run("ping")
    # TODO: assert_lessthan expr [clock clicks -milliseconds]-$start 2000
    r.run("datatype.slow_loading", 0)
    # TODO: wait_for_condition 50 100 {
    #       [s loading] eq {0}
    #   } else {
    #       fail "Failed waiting for loading to end"
    #   }
    # TODO: $rd read
    # TODO: $rd close


@pytest.mark.xfail(reason="not implemented")
def test_datatype_check_the_type_name(r: ValkeyTestClient) -> None:
    """
    test {DataType: check the type name} {
        r flushdb
        r datatype.set foo 111 bar
        assert_type test___dt foo
    }
    """
    r.run("flushdb")
    r.run("datatype.set", "foo", 111, "bar")
    # TODO: assert_type test___dt foo


@pytest.mark.xfail(reason="not implemented")
def test_scan_module_datatype(r: ValkeyTestClient) -> None:
    """
    test {SCAN module datatype} {
        r flushdb
        populate 1000
        r datatype.set foo 111 bar
        set type [r type foo]
        set cur 0
        set keys {}
        while 1 {
            set res [r scan $cur type $type]
            set cur [lindex $res 0]
            set k [lindex $res 1]
            lappend keys {*}$k
            if {$cur == 0} break
        }

        assert_equal 1 [llength $keys]
    }
    """
    r.run("flushdb")
    # TODO: populate 1000
    r.run("datatype.set", "foo", 111, "bar")
    type = r.run("type", "foo")
    cur = 0
    keys = ""
    # TODO: while 1 {
    #       set res [r scan $cur type $type]
    #       set cur [lindex $res 0]
    #       set k [lindex $res 1]
    #       lappend keys {*}$k
    #       if {$cur == 0} break
    #   }
    assert 1 == len(keys)


@pytest.mark.xfail(reason="not implemented")
def test_scan_module_datatype_with_case_sensitive(r: ValkeyTestClient) -> None:
    """
    test {SCAN module datatype with case sensitive} {
        r flushdb
        populate 1000
        r datatype.set foo 111 bar
        set type "tEsT___dT"
        set cur 0
        set keys {}
        while 1 {
            set res [r scan $cur type $type]
            set cur [lindex $res 0]
            set k [lindex $res 1]
            lappend keys {*}$k
            if {$cur == 0} break
        }

        assert_equal 1 [llength $keys]
    }
    """
    r.run("flushdb")
    # TODO: populate 1000
    r.run("datatype.set", "foo", 111, "bar")
    type = "tEsT___dT"
    cur = 0
    keys = ""
    # TODO: while 1 {
    #       set res [r scan $cur type $type]
    #       set cur [lindex $res 0]
    #       set k [lindex $res 1]
    #       lappend keys {*}$k
    #       if {$cur == 0} break
    #   }
    assert 1 == len(keys)


@pytest.mark.xfail(reason="not implemented")
def test_datatype_check_memory_usage(r: ValkeyTestClient) -> None:
    """
    test {DataType: check memory usage} {
        r flushdb
        set large_key [string repeat A 100000]
        r datatype.set $large_key 111 bar
        assert_morethan [r memory usage $large_key] 100000
    }
    """
    r.run("flushdb")
    # TODO: set large_key string repeat A 100000
    # TODO: r datatype.set large _key 111 bar
    # TODO: assert_morethan r memory usage $large_key 100000
