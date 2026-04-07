# ruff: noqa: PLR2004, F841, ANN002, ANN201
from fnmatch import fnmatch

import pytest

from tests.valkey_test_client import ValkeyTestClient

pytestmark = [pytest.mark.bitops]


def test_bitfield_signed_set_and_get_basics(r: ValkeyTestClient) -> None:
    """
    test {BITFIELD signed SET and GET basics} {
        r del bits
        set results {}
        lappend results [r bitfield bits set i8 0 -100]
        lappend results [r bitfield bits set i8 0 101]
        lappend results [r bitfield bits get i8 0]
        set results
    } {0 -100 101}
    """
    r.run("del", "bits")
    results = []
    results.append(r.run("bitfield", "bits", "set", "i8", 0, -100))
    results.append(r.run("bitfield", "bits", "set", "i8", 0, 101))
    results.append(r.run("bitfield", "bits", "get", "i8", 0))
    assert results == "0 -100 101"


def test_bitfield_unsigned_set_and_get_basics(r: ValkeyTestClient) -> None:
    """
    test {BITFIELD unsigned SET and GET basics} {
        r del bits
        set results {}
        lappend results [r bitfield bits set u8 0 255]
        lappend results [r bitfield bits set u8 0 100]
        lappend results [r bitfield bits get u8 0]
        set results
    } {0 255 100}
    """
    r.run("del", "bits")
    results = []
    results.append(r.run("bitfield", "bits", "set", "u8", 0, 255))
    results.append(r.run("bitfield", "bits", "set", "u8", 0, 100))
    results.append(r.run("bitfield", "bits", "get", "u8", 0))
    assert results == "0 255 100"


def test_bitfield_signed_set_and_get_together(r: ValkeyTestClient) -> None:
    """
    test {BITFIELD signed SET and GET together} {
        r del bits
        set results [r bitfield bits set i8 0 255 set i8 0 100 get i8 0]
    } {0 -1 100}
    """
    r.run("del", "bits")
    assert r.run("bitfield", "bits", "set", "i8", 0, 255, "set", "i8", 0, 100, "get", "i8", 0) == "0 -1 100"


def test_bitfield_unsigned_with_set_get_and_incrby_arguments(r: ValkeyTestClient) -> None:
    """
    test {BITFIELD unsigned with SET, GET and INCRBY arguments} {
        r del bits
        set results [r bitfield bits set u8 0 255 incrby u8 0 100 get u8 0]
    } {0 99 99}
    """
    r.run("del", "bits")
    assert r.run("bitfield", "bits", "set", "u8", 0, 255, "incrby", "u8", 0, 100, "get", "u8", 0) == "0 99 99"


def test_bitfield_with_only_key_as_argument(r: ValkeyTestClient) -> None:
    """
    test {BITFIELD with only key as argument} {
        r del bits
        set result [r bitfield bits]
        assert {$result eq {}}
    }
    """
    r.run("del", "bits")
    result = r.run("bitfield", "bits")
    assert result == ""


def test_bitfield_idx_form(r: ValkeyTestClient) -> None:
    """
    test {BITFIELD #<idx> form} {
        r del bits
        set results {}
        r bitfield bits set u8 #0 65
        r bitfield bits set u8 #1 66
        r bitfield bits set u8 #2 67
        r get bits
    } {ABC}
    """
    r.run("del", "bits")
    results = ""
    r.run("bitfield", "bits", "set", "u8", "#0", 65)
    r.run("bitfield", "bits", "set", "u8", "#1", 66)
    r.run("bitfield", "bits", "set", "u8", "#2", 67)
    assert r.run("get", "bits") == "ABC"


def test_bitfield_basic_incrby_form(r: ValkeyTestClient) -> None:
    """
    test {BITFIELD basic INCRBY form} {
        r del bits
        set results {}
        r bitfield bits set u8 #0 10
        lappend results [r bitfield bits incrby u8 #0 100]
        lappend results [r bitfield bits incrby u8 #0 100]
        set results
    } {110 210}
    """
    r.run("del", "bits")
    results = []
    r.run("bitfield", "bits", "set", "u8", "#0", 10)
    results.append(r.run("bitfield", "bits", "incrby", "u8", "#0", 100))
    results.append(r.run("bitfield", "bits", "incrby", "u8", "#0", 100))
    assert results == "110 210"


def test_bitfield_chaining_of_multiple_commands(r: ValkeyTestClient) -> None:
    """
    test {BITFIELD chaining of multiple commands} {
        r del bits
        set results {}
        r bitfield bits set u8 #0 10
        lappend results [r bitfield bits incrby u8 #0 100 incrby u8 #0 100]
        set results
    } {{110 210}}
    """
    r.run("del", "bits")
    results = []
    r.run("bitfield", "bits", "set", "u8", "#0", 10)
    results.append(r.run("bitfield", "bits", "incrby", "u8", "#0", 100, "incrby", "u8", "#0", 100))
    assert results == "{110 210}"


@pytest.mark.xfail(reason="not implemented")
def test_bitfield_unsigned_overflow_wrap(r: ValkeyTestClient) -> None:
    """
    test {BITFIELD unsigned overflow wrap} {
        r del bits
        set results {}
        r bitfield bits set u8 #0 100
        lappend results [r bitfield bits overflow wrap incrby u8 #0 257]
        lappend results [r bitfield bits get u8 #0]
        lappend results [r bitfield bits overflow wrap incrby u8 #0 255]
        lappend results [r bitfield bits get u8 #0]
    } {101 101 100 100}
    """
    r.run("del", "bits")
    results = []
    r.run("bitfield", "bits", "set", "u8", "#0", 100)
    results.append(r.run("bitfield", "bits", "overflow", "wrap", "incrby", "u8", "#0", 257))
    results.append(r.run("bitfield", "bits", "get", "u8", "#0"))
    results.append(r.run("bitfield", "bits", "overflow", "wrap", "incrby", "u8", "#0", 255))
    # TODO: lappend results r bitfield bits get u8 #0
    assert False


@pytest.mark.xfail(reason="not implemented")
def test_bitfield_unsigned_overflow_sat(r: ValkeyTestClient) -> None:
    """
    test {BITFIELD unsigned overflow sat} {
        r del bits
        set results {}
        r bitfield bits set u8 #0 100
        lappend results [r bitfield bits overflow sat incrby u8 #0 257]
        lappend results [r bitfield bits get u8 #0]
        lappend results [r bitfield bits overflow sat incrby u8 #0 -255]
        lappend results [r bitfield bits get u8 #0]
    } {255 255 0 0}
    """
    r.run("del", "bits")
    results = []
    r.run("bitfield", "bits", "set", "u8", "#0", 100)
    results.append(r.run("bitfield", "bits", "overflow", "sat", "incrby", "u8", "#0", 257))
    results.append(r.run("bitfield", "bits", "get", "u8", "#0"))
    results.append(r.run("bitfield", "bits", "overflow", "sat", "incrby", "u8", "#0", -255))
    # TODO: lappend results r bitfield bits get u8 #0
    assert False


@pytest.mark.xfail(reason="not implemented")
def test_bitfield_signed_overflow_wrap(r: ValkeyTestClient) -> None:
    """
    test {BITFIELD signed overflow wrap} {
        r del bits
        set results {}
        r bitfield bits set i8 #0 100
        lappend results [r bitfield bits overflow wrap incrby i8 #0 257]
        lappend results [r bitfield bits get i8 #0]
        lappend results [r bitfield bits overflow wrap incrby i8 #0 255]
        lappend results [r bitfield bits get i8 #0]
    } {101 101 100 100}
    """
    r.run("del", "bits")
    results = []
    r.run("bitfield", "bits", "set", "i8", "#0", 100)
    results.append(r.run("bitfield", "bits", "overflow", "wrap", "incrby", "i8", "#0", 257))
    results.append(r.run("bitfield", "bits", "get", "i8", "#0"))
    results.append(r.run("bitfield", "bits", "overflow", "wrap", "incrby", "i8", "#0", 255))
    # TODO: lappend results r bitfield bits get i8 #0
    assert False


@pytest.mark.xfail(reason="not implemented")
def test_bitfield_signed_overflow_sat(r: ValkeyTestClient) -> None:
    """
    test {BITFIELD signed overflow sat} {
        r del bits
        set results {}
        r bitfield bits set u8 #0 100
        lappend results [r bitfield bits overflow sat incrby i8 #0 257]
        lappend results [r bitfield bits get i8 #0]
        lappend results [r bitfield bits overflow sat incrby i8 #0 -255]
        lappend results [r bitfield bits get i8 #0]
    } {127 127 -128 -128}
    """
    r.run("del", "bits")
    results = []
    r.run("bitfield", "bits", "set", "u8", "#0", 100)
    results.append(r.run("bitfield", "bits", "overflow", "sat", "incrby", "i8", "#0", 257))
    results.append(r.run("bitfield", "bits", "get", "i8", "#0"))
    results.append(r.run("bitfield", "bits", "overflow", "sat", "incrby", "i8", "#0", -255))
    # TODO: lappend results r bitfield bits get i8 #0
    assert False


def test_bitfield_overflow_detection_fuzzing(r: ValkeyTestClient) -> None:
    """
    test {BITFIELD overflow detection fuzzing} {
        for {set j 0} {$j < 1000} {incr j} {
            set bits [expr {[randomInt 64]+1}]
            set sign [randomInt 2]
            set range [expr {2**$bits}]
            if {$bits == 64} {set sign 1} ; # u64 is not supported by BITFIELD.
            if {$sign} {
                set min [expr {-($range/2)}]
                set type "i$bits"
            } else {
                set min 0
                set type "u$bits"
            }
            set max [expr {$min+$range-1}]

            # Compare Tcl vs the server
            set range2 [expr {$range*2}]
            set value [expr {($min*2)+[randomInt $range2]}]
            set increment [expr {($min*2)+[randomInt $range2]}]
            if {$value > 9223372036854775807} {
                set value 9223372036854775807
            }
            if {$value < -9223372036854775808} {
                set value -9223372036854775808
            }
            if {$increment > 9223372036854775807} {
                set increment 9223372036854775807
            }
            if {$increment < -9223372036854775808} {
                set increment -9223372036854775808
            }

            set overflow 0
            if {$value > $max || $value < $min} {set overflow 1}
            if {($value + $increment) > $max} {set overflow 1}
            if {($value + $increment) < $min} {set overflow 1}

            r del bits
            set res1 [r bitfield bits overflow fail set $type 0 $value]
            set res2 [r bitfield bits overflow fail incrby $type 0 $increment]

            if {$overflow && [lindex $res1 0] ne {} &&
                             [lindex $res2 0] ne {}} {
                fail "OW not detected where needed: $type $value+$increment"
            }
            if {!$overflow && ([lindex $res1 0] eq {} ||
                               [lindex $res2 0] eq {})} {
                fail "OW detected where NOT needed: $type $value+$increment"
            }
        }
    }
    """
    for_(
        "set j 0",
        "$j < 1000",
        "incr j",
        '            set bits [expr {[randomInt 64]+1}]\n            set sign [randomInt 2]\n            set range [expr {2**$bits}]\n            if {$bits == 64} {set sign 1} ; # u64 is not supported by BITFIELD.\n            if {$sign} {\n                set min [expr {-($range/2)}]\n                set type "i$bits"\n            } else {\n                set min 0\n                set type "u$bits"\n            }\n            set max [expr {$min+$range-1}]\n\n            # Compare Tcl vs the server\n            set range2 [expr {$range*2}]\n            set value [expr {($min*2)+[randomInt $range2]}]\n            set increment [expr {($min*2)+[randomInt $range2]}]\n            if {$value > 9223372036854775807} {\n                set value 9223372036854775807\n            }\n            if {$value < -9223372036854775808} {\n                set value -9223372036854775808\n            }\n            if {$increment > 9223372036854775807} {\n                set increment 9223372036854775807\n            }\n            if {$increment < -9223372036854775808} {\n                set increment -9223372036854775808\n            }\n\n            set overflow 0\n            if {$value > $max || $value < $min} {set overflow 1}\n            if {($value + $increment) > $max} {set overflow 1}\n            if {($value + $increment) < $min} {set overflow 1}\n\n            r del bits\n            set res1 [r bitfield bits overflow fail set $type 0 $value]\n            set res2 [r bitfield bits overflow fail incrby $type 0 $increment]\n\n            if {$overflow && [lindex $res1 0] ne {} &&\n                             [lindex $res2 0] ne {}} {\n                fail "OW not detected where needed: $type $value+$increment"\n            }\n            if {!$overflow && ([lindex $res1 0] eq {} ||\n                               [lindex $res2 0] eq {})} {\n                fail "OW detected where NOT needed: $type $value+$increment"\n            }\n        ',
    )


def test_bitfield_overflow_wrap_fuzzing(r: ValkeyTestClient) -> None:
    """
    test {BITFIELD overflow wrap fuzzing} {
        for {set j 0} {$j < 1000} {incr j} {
            set bits [expr {[randomInt 64]+1}]
            set sign [randomInt 2]
            set range [expr {2**$bits}]
            if {$bits == 64} {set sign 1} ; # u64 is not supported by BITFIELD.
            if {$sign} {
                set min [expr {-($range/2)}]
                set type "i$bits"
            } else {
                set min 0
                set type "u$bits"
            }
            set max [expr {$min+$range-1}]

            # Compare Tcl vs the server
            set range2 [expr {$range*2}]
            set value [expr {($min*2)+[randomInt $range2]}]
            set increment [expr {($min*2)+[randomInt $range2]}]
            if {$value > 9223372036854775807} {
                set value 9223372036854775807
            }
            if {$value < -9223372036854775808} {
                set value -9223372036854775808
            }
            if {$increment > 9223372036854775807} {
                set increment 9223372036854775807
            }
            if {$increment < -9223372036854775808} {
                set increment -9223372036854775808
            }

            r del bits
            r bitfield bits overflow wrap set $type 0 $value
            r bitfield bits overflow wrap incrby $type 0 $increment
            set res [lindex [r bitfield bits get $type 0] 0]

            set expected 0
            if {$sign} {incr expected [expr {$max+1}]}
            incr expected $value
            incr expected $increment
            set expected [expr {$expected % $range}]
            if {$sign} {incr expected $min}

            if {$res != $expected} {
                fail "WRAP error: $type $value+$increment = $res, should be $expected"
            }
        }
    }
    """
    for_(
        "set j 0",
        "$j < 1000",
        "incr j",
        '            set bits [expr {[randomInt 64]+1}]\n            set sign [randomInt 2]\n            set range [expr {2**$bits}]\n            if {$bits == 64} {set sign 1} ; # u64 is not supported by BITFIELD.\n            if {$sign} {\n                set min [expr {-($range/2)}]\n                set type "i$bits"\n            } else {\n                set min 0\n                set type "u$bits"\n            }\n            set max [expr {$min+$range-1}]\n\n            # Compare Tcl vs the server\n            set range2 [expr {$range*2}]\n            set value [expr {($min*2)+[randomInt $range2]}]\n            set increment [expr {($min*2)+[randomInt $range2]}]\n            if {$value > 9223372036854775807} {\n                set value 9223372036854775807\n            }\n            if {$value < -9223372036854775808} {\n                set value -9223372036854775808\n            }\n            if {$increment > 9223372036854775807} {\n                set increment 9223372036854775807\n            }\n            if {$increment < -9223372036854775808} {\n                set increment -9223372036854775808\n            }\n\n            r del bits\n            r bitfield bits overflow wrap set $type 0 $value\n            r bitfield bits overflow wrap incrby $type 0 $increment\n            set res [lindex [r bitfield bits get $type 0] 0]\n\n            set expected 0\n            if {$sign} {incr expected [expr {$max+1}]}\n            incr expected $value\n            incr expected $increment\n            set expected [expr {$expected % $range}]\n            if {$sign} {incr expected $min}\n\n            if {$res != $expected} {\n                fail "WRAP error: $type $value+$increment = $res, should be $expected"\n            }\n        ',
    )


def test_bitfield_regression_for_3221(r: ValkeyTestClient) -> None:
    """
    test {BITFIELD regression for #3221} {
        r set bits 1
        r bitfield bits get u1 0
    } {0}
    """
    r.run("set", "bits", 1)
    assert r.run("bitfield", "bits", "get", "u1", 0) == "0"


def test_bitfield_regression_for_3564(r: ValkeyTestClient) -> None:
    """
    test {BITFIELD regression for #3564} {
        for {set j 0} {$j < 10} {incr j} {
            r del mystring
            set res [r BITFIELD mystring SET i8 0 10 SET i8 64 10 INCRBY i8 10 99900]
            assert {$res eq {0 0 60}}
        }
        r del mystring
    }
    """
    j = 0
    while j < 10:
        r.run("del", "mystring")
        res = r.run("BITFIELD", "mystring", "SET", "i8", 0, 10, "SET", "i8", 64, 10, "INCRBY", "i8", 10, 99900)
        assert res == "0 0 60"
        j += 1
    r.run("del", "mystring")


def test_bitfield_ro_with_only_key_as_argument(r: ValkeyTestClient) -> None:
    """
    test {BITFIELD_RO with only key as argument} {
        set res [r bitfield_ro bits]
        assert {$res eq {}}
    }
    """
    res = r.run("bitfield_ro", "bits")
    assert res == ""


def test_bitfield_ro_fails_when_write_option_is_used(r: ValkeyTestClient) -> None:
    """
    test {BITFIELD_RO fails when write option is used} {
        catch {r bitfield_ro bits set u8 0 100 get u8 0} err
        assert_match {*ERR BITFIELD_RO only supports the GET subcommand*} $err
    }
    """
    try:
        err = r.run("bitfield_ro", "bits", "set", "u8", 0, 100, "get", "u8", 0)
    except Exception as _catch_err:
        err = str(_catch_err)
    assert fnmatch(str(err), "*ERR BITFIELD_RO only supports the GET subcommand*")


pytestmark = [pytest.mark.repl_external_skip]


"""
start_server {} {
    set master [srv -1 client]
    set master_host [srv -1 host]
    set master_port [srv -1 port]
    set slave [srv 0 client]

    test {BITFIELD: setup slave} {
        $slave slaveof $master_host $master_port
        wait_for_condition 50 100 {
            [s 0 master_link_status] eq {up}
        } else {
            fail "Replication not started."
        }
    }

    test {BITFIELD: write on master, read on slave} {
        $master del bits
        assert_equal 0 [$master bitfield bits set u8 0 255]
        assert_equal 255 [$master bitfield bits set u8 0 100]
        wait_for_ofs_sync $master $slave
        assert_equal 100 [$slave bitfield_ro bits get u8 0]
    }

    test {BITFIELD_RO with only key as argument on read-only replica} {
        set res [$slave bitfield_ro bits]
        assert {$res eq {}}
    }

    test {BITFIELD_RO fails when write option is used on read-only replica} {
        catch {$slave bitfield_ro bits set u8 0 100 get u8 0} err
        assert_match {*ERR BITFIELD_RO only supports the GET subcommand*} $err
    }
}
"""


# --- stubs for unimplemented TCL helpers ---


def expr(*args):
    raise NotImplementedError("expr")


def for_(*args):
    raise NotImplementedError("for_")


def if_(*args):
    raise NotImplementedError("if_")


def incr(*args):
    raise NotImplementedError("incr")


def random_int(*args):
    raise NotImplementedError("random_int")
