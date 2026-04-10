# ruff: noqa: F841, RUF043, ANN002, ANN201
from fnmatch import fnmatch

import pytest

from tests.valkey_test_client import ValkeyTestClient

pytestmark = [pytest.mark.incr]


def test_incr_against_non_existing_key(r: ValkeyTestClient) -> None:
    """
    test {INCR against non existing key} {
        set res {}
        append res [r incr novar]
        append res [r get novar]
    } {11}
    """
    res = []
    append("res", r.run("incr", "novar"))
    append("res", r.run("get", "novar"))


def test_incr_against_key_created_by_incr_itself(r: ValkeyTestClient) -> None:
    """
    test {INCR against key created by incr itself} {
        r incr novar
    } {2}
    """
    assert r.run("incr", "novar") == "2"


def test_decr_against_key_created_by_incr(r: ValkeyTestClient) -> None:
    """
    test {DECR against key created by incr} {
        r decr novar
    } {1}
    """
    assert r.run("decr", "novar") == "1"


def test_decr_against_key_is_not_exist_and_incr(r: ValkeyTestClient) -> None:
    """
    test {DECR against key is not exist and incr} {
        r del novar_not_exist
        assert_equal {-1} [r decr novar_not_exist]
        assert_equal {0} [r incr novar_not_exist]
    }
    """
    r.run("del", "novar_not_exist")
    assert "-1" == r.run("decr", "novar_not_exist")
    assert "0" == r.run("incr", "novar_not_exist")


def test_incr_against_key_originally_set_with_set(r: ValkeyTestClient) -> None:
    """
    test {INCR against key originally set with SET} {
        r set novar 100
        r incr novar
    } {101}
    """
    r.run("set", "novar", 100)
    assert r.run("incr", "novar") == "101"


def test_incr_over_32bit_value(r: ValkeyTestClient) -> None:
    """
    test {INCR over 32bit value} {
        r set novar 17179869184
        r incr novar
    } {17179869185}
    """
    r.run("set", "novar", 17179869184)
    assert r.run("incr", "novar") == "17179869185"


def test_incrby_over_32bit_value_with_over_32bit_increment(r: ValkeyTestClient) -> None:
    """
    test {INCRBY over 32bit value with over 32bit increment} {
        r set novar 17179869184
        r incrby novar 17179869184
    } {34359738368}
    """
    r.run("set", "novar", 17179869184)
    assert r.run("incrby", "novar", 17179869184) == "34359738368"


def test_incr_fails_against_key_with_spaces_left(r: ValkeyTestClient) -> None:
    """
    test {INCR fails against key with spaces (left)} {
        r set novar "    11"
        catch {r incr novar} err
        format $err
    } {ERR*}
    """
    r.run("set", "novar", "    11")
    try:
        err = r.run("incr", "novar")
    except Exception as _catch_err:
        err = str(_catch_err)
    format_(err)


def test_incr_fails_against_key_with_spaces_right(r: ValkeyTestClient) -> None:
    """
    test {INCR fails against key with spaces (right)} {
        r set novar "11    "
        catch {r incr novar} err
        format $err
    } {ERR*}
    """
    r.run("set", "novar", "11    ")
    try:
        err = r.run("incr", "novar")
    except Exception as _catch_err:
        err = str(_catch_err)
    format_(err)


def test_incr_fails_against_key_with_spaces_both(r: ValkeyTestClient) -> None:
    """
    test {INCR fails against key with spaces (both)} {
        r set novar "    11    "
        catch {r incr novar} err
        format $err
    } {ERR*}
    """
    r.run("set", "novar", "    11    ")
    try:
        err = r.run("incr", "novar")
    except Exception as _catch_err:
        err = str(_catch_err)
    format_(err)


def test_decrby_negation_overflow(r: ValkeyTestClient) -> None:
    """
    test {DECRBY negation overflow} {
        r set x 0
        catch {r decrby x -9223372036854775808} err
        format $err
    } {ERR*}
    """
    r.run("set", "x", 0)
    try:
        err = r.run("decrby", "x", -9223372036854775808)
    except Exception as _catch_err:
        err = str(_catch_err)
    format_(err)


def test_incr_fails_against_a_key_holding_a_list(r: ValkeyTestClient) -> None:
    """
    test {INCR fails against a key holding a list} {
        r rpush mylist 1
        catch {r incr mylist} err
        r rpop mylist
        format $err
    } {WRONGTYPE*}
    """
    r.run("rpush", "mylist", 1)
    try:
        err = r.run("incr", "mylist")
    except Exception as _catch_err:
        err = str(_catch_err)
    r.run("rpop", "mylist")
    format_(err)


def test_decrby_over_32bit_value_with_over_32bit_increment_negative_res(r: ValkeyTestClient) -> None:
    """
    test {DECRBY over 32bit value with over 32bit increment, negative res} {
        r set novar 17179869184
        r decrby novar 17179869185
    } {-1}
    """
    r.run("set", "novar", 17179869184)
    assert r.run("decrby", "novar", 17179869185) == "-1"


def test_decrby_against_key_is_not_exist(r: ValkeyTestClient) -> None:
    """
    test {DECRBY against key is not exist} {
        r del key_not_exist
        assert_equal {-1} [r decrby key_not_exist 1]
    }
    """
    r.run("del", "key_not_exist")
    assert "-1" == r.run("decrby", "key_not_exist", 1)


def test_incr_can_modify_objects_in_place(r: ValkeyTestClient) -> None:
    """
    test {INCR can modify objects in-place} {
        r set foo 20000
        r incr foo
        assert_refcount 1 foo
        set old [lindex [split [r debug object foo]] 1]
        r incr foo
        set new [lindex [split [r debug object foo]] 1]
        assert {[string range $old 0 2] eq "at:"}
        assert {[string range $new 0 2] eq "at:"}
        assert {$old eq $new}
    } {} {needs:debug}
    """
    r.run("set", "foo", 20000)
    r.run("incr", "foo")
    assert_refcount(1, "foo")
    old = split(r.run("debug", "object", "foo"))[1]
    r.run("incr", "foo")
    new = split(r.run("debug", "object", "foo"))[1]
    assert string("range", old, 0, 2) == "at:"
    assert string("range", new, 0, 2) == "at:"
    assert old == new


def test_incrbyfloat_against_non_existing_key(r: ValkeyTestClient) -> None:
    """
    test {INCRBYFLOAT against non existing key} {
        r del novar
        list    [roundFloat [r incrbyfloat novar 1]] \
                [roundFloat [r get novar]] \
                [roundFloat [r incrbyfloat novar 0.25]] \
                [roundFloat [r get novar]]
    } {1 1 1.25 1.25}
    """
    r.run("del", "novar")
    assert [
        round_float(r.run("incrbyfloat", "novar", 1)),
        round_float(r.run("get", "novar")),
        round_float(r.run("incrbyfloat", "novar", 0.25)),
        round_float(r.run("get", "novar")),
    ] == "1 1 1.25 1.25"


def test_incrbyfloat_against_key_originally_set_with_set(r: ValkeyTestClient) -> None:
    """
    test {INCRBYFLOAT against key originally set with SET} {
        r set novar 1.5
        roundFloat [r incrbyfloat novar 1.5]
    } {3}
    """
    r.run("set", "novar", 1.5)
    round_float(r.run("incrbyfloat", "novar", 1.5))


def test_incrbyfloat_over_32bit_value(r: ValkeyTestClient) -> None:
    """
    test {INCRBYFLOAT over 32bit value} {
        r set novar 17179869184
        r incrbyfloat novar 1.5
    } {17179869185.5}
    """
    r.run("set", "novar", 17179869184)
    assert r.run("incrbyfloat", "novar", 1.5) == "17179869185.5"


def test_incrbyfloat_over_32bit_value_with_over_32bit_increment(r: ValkeyTestClient) -> None:
    """
    test {INCRBYFLOAT over 32bit value with over 32bit increment} {
        r set novar 17179869184
        r incrbyfloat novar 17179869184
    } {34359738368}
    """
    r.run("set", "novar", 17179869184)
    assert r.run("incrbyfloat", "novar", 17179869184) == "34359738368"


def test_incrbyfloat_fails_against_key_with_spaces_left(r: ValkeyTestClient) -> None:
    """
    test {INCRBYFLOAT fails against key with spaces (left)} {
        set err {}
        r set novar "    11"
        catch {r incrbyfloat novar 1.0} err
        format $err
    } {ERR *valid*}
    """
    err = []
    r.run("set", "novar", "    11")
    try:
        err = r.run("incrbyfloat", "novar", 1.0)
    except Exception as _catch_err:
        err = str(_catch_err)
    format_(err)


def test_incrbyfloat_fails_against_key_with_spaces_right(r: ValkeyTestClient) -> None:
    """
    test {INCRBYFLOAT fails against key with spaces (right)} {
        set err {}
        r set novar "11    "
        catch {r incrbyfloat novar 1.0} err
        format $err
    } {ERR *valid*}
    """
    err = []
    r.run("set", "novar", "11    ")
    try:
        err = r.run("incrbyfloat", "novar", 1.0)
    except Exception as _catch_err:
        err = str(_catch_err)
    format_(err)


def test_incrbyfloat_fails_against_key_with_spaces_both(r: ValkeyTestClient) -> None:
    """
    test {INCRBYFLOAT fails against key with spaces (both)} {
        set err {}
        r set novar " 11 "
        catch {r incrbyfloat novar 1.0} err
        format $err
    } {ERR *valid*}
    """
    err = []
    r.run("set", "novar", " 11 ")
    try:
        err = r.run("incrbyfloat", "novar", 1.0)
    except Exception as _catch_err:
        err = str(_catch_err)
    format_(err)


def test_incrbyfloat_fails_against_a_key_holding_a_list(r: ValkeyTestClient) -> None:
    """
    test {INCRBYFLOAT fails against a key holding a list} {
        r del mylist
        set err {}
        r rpush mylist 1
        catch {r incrbyfloat mylist 1.0} err
        r del mylist
        format $err
    } {WRONGTYPE*}
    """
    r.run("del", "mylist")
    err = []
    r.run("rpush", "mylist", 1)
    try:
        err = r.run("incrbyfloat", "mylist", 1.0)
    except Exception as _catch_err:
        err = str(_catch_err)
    r.run("del", "mylist")
    format_(err)


def test_incrbyfloat_does_not_allow_nan_or_infinity(r: ValkeyTestClient) -> None:
    """
    test {INCRBYFLOAT does not allow NaN or Infinity} {
        r set foo 0
        set err {}
        catch {r incrbyfloat foo +inf} err
        set err
        # p.s. no way I can force NaN to test it from the API because
        # there is no way to increment / decrement by infinity nor to
        # perform divisions.
    } {ERR *would produce*} {valgrind:skip}
    """
    r.run("set", "foo", 0)
    err = []
    try:
        err = r.run("incrbyfloat", "foo", float("+inf"))
    except Exception as _catch_err:
        err = str(_catch_err)
    assert fnmatch(str(err), "ERR *would produce*")


def test_incrbyfloat_decrement(r: ValkeyTestClient) -> None:
    """
    test {INCRBYFLOAT decrement} {
        r set foo 1
        roundFloat [r incrbyfloat foo -1.1]
    } {-0.1}
    """
    r.run("set", "foo", 1)
    round_float(r.run("incrbyfloat", "foo", -1.1))


def test_string_to_double_with_null_terminator(r: ValkeyTestClient) -> None:
    """
    test {string to double with null terminator} {
        r set foo 1
        r setrange foo 2 2
        catch {r incrbyfloat foo 1} err
        format $err
    } {ERR *valid*}
    """
    r.run("set", "foo", 1)
    r.run("setrange", "foo", 2, 2)
    try:
        err = r.run("incrbyfloat", "foo", 1)
    except Exception as _catch_err:
        err = str(_catch_err)
    format_(err)


def test_no_negative_zero(r: ValkeyTestClient) -> None:
    """
    test {No negative zero} {
        r del foo
        r incrbyfloat foo [expr double(1)/41]
        r incrbyfloat foo [expr double(-1)/41]
        r get foo
    } {0}
    """
    r.run("del", "foo")
    r.run("incrbyfloat", "foo", expr("double(1)/41"))
    r.run("incrbyfloat", "foo", expr("double(-1)/41"))
    assert r.run("get", "foo") == "0"


def test_incrby_incrbyfloat_decrby_against_unhappy_path(r: ValkeyTestClient) -> None:
    """
    test {INCRBY INCRBYFLOAT DECRBY against unhappy path} {
        r del mykeyincr
        assert_error "*ERR wrong number of arguments*" {r incr mykeyincr v}
        assert_error "*ERR wrong number of arguments*" {r decr mykeyincr v}
        assert_error "*value is not an integer or out of range*" {r incrby mykeyincr v}
        assert_error "*value is not an integer or out of range*" {r incrby mykeyincr 1.5}
        assert_error "*value is not an integer or out of range*" {r decrby mykeyincr v}
        assert_error "*value is not an integer or out of range*" {r decrby mykeyincr 1.5}
        assert_error "*value is not a valid float*" {r incrbyfloat mykeyincr v}
    }
    """
    r.run("del", "mykeyincr")
    with pytest.raises(Exception, match=".*ERR\\ wrong\\ number\\ of\\ arguments.*"):
        r.run("incr", "mykeyincr", "v")
    with pytest.raises(Exception, match=".*ERR\\ wrong\\ number\\ of\\ arguments.*"):
        r.run("decr", "mykeyincr", "v")
    with pytest.raises(Exception, match=".*value\\ is\\ not\\ an\\ integer\\ or\\ out\\ of\\ range.*"):
        r.run("incrby", "mykeyincr", "v")
    with pytest.raises(Exception, match=".*value\\ is\\ not\\ an\\ integer\\ or\\ out\\ of\\ range.*"):
        r.run("incrby", "mykeyincr", 1.5)
    with pytest.raises(Exception, match=".*value\\ is\\ not\\ an\\ integer\\ or\\ out\\ of\\ range.*"):
        r.run("decrby", "mykeyincr", "v")
    with pytest.raises(Exception, match=".*value\\ is\\ not\\ an\\ integer\\ or\\ out\\ of\\ range.*"):
        r.run("decrby", "mykeyincr", 1.5)
    with pytest.raises(Exception, match=".*value\\ is\\ not\\ a\\ valid\\ float.*"):
        r.run("incrbyfloat", "mykeyincr", "v")


@pytest.mark.parametrize(["cmd"], [("incr"), ("decr"), ("incrby"), ("decrby")])
def test_cmd_operation_should_update_encoding_from_raw_to_int(r: ValkeyTestClient, cmd: str) -> None:
    """
    test "$cmd operation should update encoding from raw to int" {
        set res {}
        set expected {1 12}
        if {[string match {*incr*} $cmd]} {
            lappend expected 13
        } else {
            lappend expected 11
        }

        r set foo 1
        assert_encoding "int" foo
        lappend res [r get foo]

        r append foo 2
        assert_encoding "raw" foo
        lappend res [r get foo]

        if {[string match {*by*} $cmd]} {
            r $cmd foo 1
        } else {
            r $cmd foo
        }
        assert_encoding "int" foo
        lappend res [r get foo]
        assert_equal $res $expected
    }
    """
    res = []
    expected = "1 12"
    if string("match", "*incr*", cmd):
        lappend("expected", 13)
    else:
        lappend("expected", 11)
    r.run("set", "foo", 1)
    assert_encoding("int", "foo")
    res.append(r.run("get", "foo"))
    r.run("append", "foo", 2)
    assert_encoding("raw", "foo")
    res.append(r.run("get", "foo"))
    if string("match", "*by*", cmd):
        r.run(cmd, "foo", 1)
    else:
        r.run(cmd, "foo")
    assert_encoding("int", "foo")
    res.append(r.run("get", "foo"))
    assert res == expected


# --- stubs for unimplemented TCL helpers ---


def append(*args):
    raise NotImplementedError("append")


def assert_encoding(*args):
    raise NotImplementedError("assert_encoding")


def assert_refcount(*args):
    raise NotImplementedError("assert_refcount")


def expr(*args):
    raise NotImplementedError("expr")


def format_(*args):
    raise NotImplementedError("format_")


def lappend(*args):
    raise NotImplementedError("lappend")


def round_float(*args):
    raise NotImplementedError("round_float")


def split(*args):
    raise NotImplementedError("split")


def string(*args):
    raise NotImplementedError("string")
