# ruff: noqa: PLR2004, F841, RUF043, ANN002, ANN201
import time

import pytest

from tests.valkey_test_client import ValkeyTestClient

pytestmark = [pytest.mark.string]


def test_set_and_get_an_item(r: ValkeyTestClient) -> None:
    """
    test {SET and GET an item} {
        r set x foobar
        r get x
    } {foobar}
    """
    r.run("set", "x", "foobar")
    assert r.run("get", "x") == "foobar"


def test_set_and_get_an_empty_item(r: ValkeyTestClient) -> None:
    """
    test {SET and GET an empty item} {
        r set x {}
        r get x
    } {}
    """
    r.run("set", "x", "")
    r.run("get", "x")


def test_very_big_payload_in_get_or_set(r: ValkeyTestClient) -> None:
    """
    test {Very big payload in GET/SET} {
        set buf [string repeat "abcd" 1000000]
        r set foo $buf
        r get foo
    } string repeat "abcd" 1000000
    """
    buf = string("repeat", "abcd", 1000000)
    r.run("set", "foo", buf)
    r.run("get", "foo")


def test_memoryusage_of_string(r: ValkeyTestClient) -> None:
    """
    test {memoryusage of string} {
        # Simple test
        set key "key"
        set value "value"
        r set $key $value
        assert_lessthan_equal [expr [string length $key] + [string length $value]] [r memory usage key]

        # Big value
        set key "key"
        set value [string repeat A 100000]
        r set $key $value
        assert_lessthan_equal [expr [string length $key] + [string length $value]] [r memory usage key]

        # Big key
        set key [string repeat A 100000]
        set value "value"
        r set $key $value
        assert_lessthan_equal [expr [string length $key] + [string length $value]] [r memory usage key]

        # Big key for int
        set key [string repeat B 100000]
        r incr $key
        assert_lessthan_equal [string length $key] [r memory usage $key]
    }
    """
    key = "key"
    value = "value"
    r.run("set", key, value)
    assert_lessthan_equal(expr(len(key), "+", len(value)), r.run("memory", "usage", "key"))
    key = "key"
    value = string("repeat", "A", 100000)
    r.run("set", key, value)
    assert_lessthan_equal(expr(len(key), "+", len(value)), r.run("memory", "usage", "key"))
    key = string("repeat", "A", 100000)
    value = "value"
    r.run("set", key, value)
    assert_lessthan_equal(expr(len(key), "+", len(value)), r.run("memory", "usage", "key"))
    key = string("repeat", "B", 100000)
    r.run("incr", key)
    assert_lessthan_equal(len(key), r.run("memory", "usage", key))


def test_setnx_target_key_missing(r: ValkeyTestClient) -> None:
    """
    test "SETNX target key missing" {
        r del novar
        assert_equal 1 [r setnx novar foobared]
        assert_equal "foobared" [r get novar]
    }
    """
    r.run("del", "novar")
    assert 1 == r.run("setnx", "novar", "foobared")
    assert "foobared" == r.run("get", "novar")


def test_setnx_target_key_exists(r: ValkeyTestClient) -> None:
    """
    test "SETNX target key exists" {
        r set novar foobared
        assert_equal 0 [r setnx novar blabla]
        assert_equal "foobared" [r get novar]
    }
    """
    r.run("set", "novar", "foobared")
    assert 0 == r.run("setnx", "novar", "blabla")
    assert "foobared" == r.run("get", "novar")


def test_setnx_against_not_expired_volatile_key(r: ValkeyTestClient) -> None:
    """
    test "SETNX against not-expired volatile key" {
        r set x 10
        r expire x 10000
        assert_equal 0 [r setnx x 20]
        assert_equal 10 [r get x]
    }
    """
    r.run("set", "x", 10)
    r.run("expire", "x", 10000)
    assert 0 == r.run("setnx", "x", 20)
    assert 10 == r.run("get", "x")


def test_setnx_against_expired_volatile_key(r: ValkeyTestClient) -> None:
    """
    test "SETNX against expired volatile key" {
        # Make it very unlikely for the key this test uses to be expired by the
        # active expiry cycle. This is tightly coupled to the implementation of
        # active expiry and dbAdd() but currently the only way to test that
        # SETNX expires a key when it should have been.
        for {set x 0} {$x < 9999} {incr x} {
            r setex key-$x 3600 value
        }

        # This will be one of 10000 expiring keys. A cycle is executed every
        # 100ms, sampling 10 keys for being expired or not.  This key will be
        # expired for at most 1s when we wait 2s, resulting in a total sample
        # of 100 keys. The probability of the success of this test being a
        # false positive is therefore approx. 1%.
        r set x 10
        r expire x 1

        # Wait for the key to expire
        after 2000

        assert_equal 1 [r setnx x 20]
        assert_equal 20 [r get x]
    }
    """
    x = 0
    while x < 9999:
        r.run("setex", "key-$x", 3600, "value")
        x += 1
    r.run("set", "x", 10)
    r.run("expire", "x", 1)
    time.sleep(2000 / 1000)
    assert 1 == r.run("setnx", "x", 20)
    assert 20 == r.run("get", "x")


def test_getex_ex_option(r: ValkeyTestClient) -> None:
    """
    test "GETEX EX option" {
        r del foo
        r set foo bar
        r getex foo ex 10
        assert_range [r ttl foo] 5 10
    }
    """
    r.run("del", "foo")
    r.run("set", "foo", "bar")
    r.run("getex", "foo", "ex", 10)
    assert_range(r.run("ttl", "foo"), 5, 10)


def test_getex_px_option(r: ValkeyTestClient) -> None:
    """
    test "GETEX PX option" {
        r del foo
        r set foo bar
        r getex foo px 10000
        assert_range [r pttl foo] 5000 10000
    }
    """
    r.run("del", "foo")
    r.run("set", "foo", "bar")
    r.run("getex", "foo", "px", 10000)
    assert_range(r.run("pttl", "foo"), 5000, 10000)


def test_getex_exat_option(r: ValkeyTestClient) -> None:
    """
    test "GETEX EXAT option" {
        r del foo
        r set foo bar
        r getex foo exat [expr [clock seconds] + 10]
        assert_range [r ttl foo] 5 10
    }
    """
    r.run("del", "foo")
    r.run("set", "foo", "bar")
    r.run("getex", "foo", "exat", expr(clock("seconds"), "+", 10))
    assert_range(r.run("ttl", "foo"), 5, 10)


def test_getex_pxat_option(r: ValkeyTestClient) -> None:
    """
    test "GETEX PXAT option" {
        r del foo
        r set foo bar
        r getex foo pxat [expr [clock milliseconds] + 10000]
        assert_range [r pttl foo] 5000 10000
    }
    """
    r.run("del", "foo")
    r.run("set", "foo", "bar")
    r.run("getex", "foo", "pxat", expr(clock("milliseconds"), "+", 10000))
    assert_range(r.run("pttl", "foo"), 5000, 10000)


def test_getex_persist_option(r: ValkeyTestClient) -> None:
    """
    test "GETEX PERSIST option" {
        r del foo
        r set foo bar ex 10
        assert_range [r ttl foo] 5 10
        r getex foo persist
        assert_equal -1 [r ttl foo]
    }
    """
    r.run("del", "foo")
    r.run("set", "foo", "bar", "ex", 10)
    assert_range(r.run("ttl", "foo"), 5, 10)
    r.run("getex", "foo", "persist")
    assert -1 == r.run("ttl", "foo")


def test_getex_no_option(r: ValkeyTestClient) -> None:
    """
    test "GETEX no option" {
        r del foo
        r set foo bar
        r getex foo
        assert_equal bar [r getex foo]
    }
    """
    r.run("del", "foo")
    r.run("set", "foo", "bar")
    r.run("getex", "foo")
    assert "bar" == r.run("getex", "foo")


def test_getex_syntax_errors(r: ValkeyTestClient) -> None:
    """
    test "GETEX syntax errors" {
        set ex {}
        catch {r getex foo non-existent-option} ex
        set ex
    } {*syntax*}
    """
    ex = ""
    try:
        ex = r.run("getex", "foo", "non-existent-option")
    except Exception as _catch_err:
        ex = str(_catch_err)
    assert ex == "*syntax*"


def test_getex_and_get_expired_key_or_not_exist(r: ValkeyTestClient) -> None:
    """
    test "GETEX and GET expired key or not exist" {
        r del foo
        r set foo bar px 1
        after 2
        assert_equal {} [r getex foo]
        assert_equal {} [r get foo]
    }
    """
    r.run("del", "foo")
    r.run("set", "foo", "bar", "px", 1)
    time.sleep(2 / 1000)
    assert "" == r.run("getex", "foo")
    assert "" == r.run("get", "foo")


def test_getex_no_arguments(r: ValkeyTestClient) -> None:
    """
    test "GETEX no arguments" {
        set ex {}
        catch {r getex} ex
        set ex
    } {*wrong number of arguments for 'getex' command}
    """
    ex = ""
    try:
        ex = r.run("getex")
    except Exception as _catch_err:
        ex = str(_catch_err)
    assert ex == "*wrong number of arguments for 'getex' command"


def test_getdel_command(r: ValkeyTestClient) -> None:
    """
    test "GETDEL command" {
        r del foo
        r set foo bar
        assert_equal bar [r getdel foo ]
        assert_equal {} [r getdel foo ]
    }
    """
    r.run("del", "foo")
    r.run("set", "foo", "bar")
    assert "bar" == r.run("getdel", "foo")
    assert "" == r.run("getdel", "foo")


def test_getdel_propagate_as_del_command_to_replica(r: ValkeyTestClient) -> None:
    """
    test {GETDEL propagate as DEL command to replica} {
        set repl [attach_to_replication_stream]
        r set foo bar
        r getdel foo
        assert_replication_stream $repl {
            {select *}
            {set foo bar}
            {del foo}
        }
        close_replication_stream $repl
    } {} {needs:repl}
    """
    repl = attach_to_replication_stream()
    r.run("set", "foo", "bar")
    r.run("getdel", "foo")
    assert_replication_stream(
        repl, "            {select *}\n            {set foo bar}\n            {del foo}\n        "
    )
    close_replication_stream(repl)


def test_getex_without_argument_does_not_propagate_to_replica(r: ValkeyTestClient) -> None:
    """
    test {GETEX without argument does not propagate to replica} {
        set repl [attach_to_replication_stream]
        r set foo bar
        r getex foo
        r del foo
        assert_replication_stream $repl {
            {select *}
            {set foo bar}
            {del foo}
        }
        close_replication_stream $repl
    } {} {needs:repl}
    """
    repl = attach_to_replication_stream()
    r.run("set", "foo", "bar")
    r.run("getex", "foo")
    r.run("del", "foo")
    assert_replication_stream(
        repl, "            {select *}\n            {set foo bar}\n            {del foo}\n        "
    )
    close_replication_stream(repl)


def test_mget(r: ValkeyTestClient) -> None:
    """
    test {MGET} {
        r flushdb
        r set foo{t} BAR
        r set bar{t} FOO
        r mget foo{t} bar{t}
    } {BAR FOO}
    """
    r.run("flushdb")
    r.run("set", "foo{t}", "BAR")
    r.run("set", "bar{t}", "FOO")
    assert r.run("mget", "foo{t}", "bar{t}") == "BAR FOO"


def test_mget_against_non_existing_key(r: ValkeyTestClient) -> None:
    """
    test {MGET against non existing key} {
        r mget foo{t} baazz{t} bar{t}
    } {BAR {} FOO}
    """
    assert r.run("mget", "foo{t}", "baazz{t}", "bar{t}") == "BAR {} FOO"


def test_mget_against_non_string_key(r: ValkeyTestClient) -> None:
    """
    test {MGET against non-string key} {
        r sadd myset{t} ciao
        r sadd myset{t} bau
        r mget foo{t} baazz{t} bar{t} myset{t}
    } {BAR {} FOO {}}
    """
    r.run("sadd", "myset{t}", "ciao")
    r.run("sadd", "myset{t}", "bau")
    assert r.run("mget", "foo{t}", "baazz{t}", "bar{t}", "myset{t}") == "BAR {} FOO {}"


@pytest.mark.xfail(reason="not implemented")
def test_getset_set_new_value(r: ValkeyTestClient) -> None:
    """
    test {GETSET (set new value)} {
        r del foo
        list [r getset foo xyz] [r get foo]
    } {{} xyz}
    """
    r.run("del", "foo")
    # TODO: list r getset foo xyz r get foo
    assert False


@pytest.mark.xfail(reason="not implemented")
def test_getset_replace_old_value(r: ValkeyTestClient) -> None:
    """
    test {GETSET (replace old value)} {
        r set foo bar
        list [r getset foo xyz] [r get foo]
    } {bar xyz}
    """
    r.run("set", "foo", "bar")
    # TODO: list r getset foo xyz r get foo
    assert False


@pytest.mark.xfail(reason="not implemented")
def test_mset_base_case(r: ValkeyTestClient) -> None:
    """
    test {MSET base case} {
        r mset x{t} 10 y{t} "foo bar" z{t} "x x x x x x x\n\n\r\n"
        r mget x{t} y{t} z{t}
    } list 10 {foo bar} "x x x x x x x\n\n\r\n"
    """
    # TODO: r mset x{t} 10 y{t} "foo bar" z{t} "x x x x x x x\n\n\r\n"
    r.run("mget", "x{t}", "y{t}", "z{t}")


def test_mset_or_msetnx_wrong_number_of_args(r: ValkeyTestClient) -> None:
    """
    test {MSET/MSETNX wrong number of args} {
        assert_error {*wrong number of arguments for 'mset' command} {r mset x{t} 10 y{t} "foo bar" z{t}}
        assert_error {*wrong number of arguments for 'msetnx' command} {r msetnx x{t} 20 y{t} "foo bar" z{t}}
    }
    """
    with pytest.raises(Exception, match=".*wrong\\ number\\ of\\ arguments\\ for\\ 'mset'\\ command"):
        r.run("mset", "x{t}", 10, "y{t}", "foo bar", "z{t}")
    with pytest.raises(Exception, match=".*wrong\\ number\\ of\\ arguments\\ for\\ 'msetnx'\\ command"):
        r.run("msetnx", "x{t}", 20, "y{t}", "foo bar", "z{t}")


@pytest.mark.xfail(reason="not implemented")
def test_mset_with_already_existing_same_key_twice(r: ValkeyTestClient) -> None:
    """
    test {MSET with already existing - same key twice} {
        r set x{t} x
        list [r mset x{t} xxx x{t} yyy] [r get x{t}]
    } {OK yyy}
    """
    r.run("set", "x{t}", "x")
    # TODO: list r mset x{t} xxx x{t} yyy r get x{t}
    assert False


@pytest.mark.xfail(reason="not implemented")
def test_msetnx_with_already_existent_key(r: ValkeyTestClient) -> None:
    """
    test {MSETNX with already existent key} {
        list [r msetnx x1{t} xxx y2{t} yyy x{t} 20] [r exists x1{t}] [r exists y2{t}]
    } {0 0 0}
    """
    # TODO: list r msetnx x1{t} xxx y2{t} yyy x{t} 20 r exists x1{t} r exists y2{t}
    assert False


@pytest.mark.xfail(reason="not implemented")
def test_msetnx_with_not_existing_keys(r: ValkeyTestClient) -> None:
    """
    test {MSETNX with not existing keys} {
        list [r msetnx x1{t} xxx y2{t} yyy] [r get x1{t}] [r get y2{t}]
    } {1 xxx yyy}
    """
    # TODO: list r msetnx x1{t} xxx y2{t} yyy r get x1{t} r get y2{t}
    assert False


@pytest.mark.xfail(reason="not implemented")
def test_msetnx_with_not_existing_keys_same_key_twice(r: ValkeyTestClient) -> None:
    """
    test {MSETNX with not existing keys - same key twice} {
        r del x1{t}
        list [r msetnx x1{t} xxx x1{t} yyy] [r get x1{t}]
    } {1 yyy}
    """
    r.run("del", "x1{t}")
    # TODO: list r msetnx x1{t} xxx x1{t} yyy r get x1{t}
    assert False


@pytest.mark.xfail(reason="not implemented")
def test_msetnx_with_already_existing_keys_same_key_twice(r: ValkeyTestClient) -> None:
    """
    test {MSETNX with already existing keys - same key twice} {
        list [r msetnx x1{t} xxx x1{t} zzz] [r get x1{t}]
    } {0 yyy}
    """
    # TODO: list r msetnx x1{t} xxx x1{t} zzz r get x1{t}
    assert False


def test_strlen_against_non_existing_key(r: ValkeyTestClient) -> None:
    """
    test "STRLEN against non-existing key" {
        assert_equal 0 [r strlen notakey]
    }
    """
    assert 0 == r.run("strlen", "notakey")


def test_strlen_against_integer_encoded_value(r: ValkeyTestClient) -> None:
    """
    test "STRLEN against integer-encoded value" {
        r set myinteger -555
        assert_equal 4 [r strlen myinteger]
    }
    """
    r.run("set", "myinteger", -555)
    assert 4 == r.run("strlen", "myinteger")


def test_strlen_against_plain_string(r: ValkeyTestClient) -> None:
    """
    test "STRLEN against plain string" {
        r set mystring "foozzz0123456789 baz"
        assert_equal 20 [r strlen mystring]
    }
    """
    r.run("set", "mystring", "foozzz0123456789 baz")
    assert 20 == r.run("strlen", "mystring")


def test_setbit_against_non_existing_key(r: ValkeyTestClient) -> None:
    """
    test "SETBIT against non-existing key" {
        r del mykey
        assert_equal 0 [r setbit mykey 1 1]
        assert_equal [binary format B* 01000000] [r get mykey]
    }
    """
    r.run("del", "mykey")
    assert 0 == r.run("setbit", "mykey", 1, 1)
    assert binary("format", "B*", 1000000) == r.run("get", "mykey")


def test_setbit_against_string_encoded_key(r: ValkeyTestClient) -> None:
    """
    test "SETBIT against string-encoded key" {
        # Ascii "@" is integer 64 = 01 00 00 00
        r set mykey "@"

        assert_equal 0 [r setbit mykey 2 1]
        assert_equal [binary format B* 01100000] [r get mykey]
        assert_equal 1 [r setbit mykey 1 0]
        assert_equal [binary format B* 00100000] [r get mykey]
    }
    """
    r.run("set", "mykey", "@")
    assert 0 == r.run("setbit", "mykey", 2, 1)
    assert binary("format", "B*", 1100000) == r.run("get", "mykey")
    assert 1 == r.run("setbit", "mykey", 1, 0)
    assert binary("format", "B*", 100000) == r.run("get", "mykey")


def test_setbit_against_integer_encoded_key(r: ValkeyTestClient) -> None:
    """
    test "SETBIT against integer-encoded key" {
        # Ascii "1" is integer 49 = 00 11 00 01
        r set mykey 1
        assert_encoding int mykey

        assert_equal 0 [r setbit mykey 6 1]
        assert_equal [binary format B* 00110011] [r get mykey]
        assert_equal 1 [r setbit mykey 2 0]
        assert_equal [binary format B* 00010011] [r get mykey]
    }
    """
    r.run("set", "mykey", 1)
    assert_encoding("int", "mykey")
    assert 0 == r.run("setbit", "mykey", 6, 1)
    assert binary("format", "B*", 110011) == r.run("get", "mykey")
    assert 1 == r.run("setbit", "mykey", 2, 0)
    assert binary("format", "B*", 10011) == r.run("get", "mykey")


def test_setbit_against_key_with_wrong_type(r: ValkeyTestClient) -> None:
    """
    test "SETBIT against key with wrong type" {
        r del mykey
        r lpush mykey "foo"
        assert_error "WRONGTYPE*" {r setbit mykey 0 1}
    }
    """
    r.run("del", "mykey")
    r.run("lpush", "mykey", "foo")
    with pytest.raises(Exception, match="WRONGTYPE.*"):
        r.run("setbit", "mykey", 0, 1)


def test_setbit_with_out_of_range_bit_offset(r: ValkeyTestClient) -> None:
    """
    test "SETBIT with out of range bit offset" {
        r del mykey
        assert_error "*out of range*" {r setbit mykey [expr 4*1024*1024*1024] 1}
        assert_error "*out of range*" {r setbit mykey -1 1}
    }
    """
    r.run("del", "mykey")
    with pytest.raises(Exception, match=".*out\\ of\\ range.*"):
        r.run("setbit", "mykey", expr("4*1024*1024*1024"), 1)
    with pytest.raises(Exception, match=".*out\\ of\\ range.*"):
        r.run("setbit", "mykey", -1, 1)


def test_setbit_with_non_bit_argument(r: ValkeyTestClient) -> None:
    """
    test "SETBIT with non-bit argument" {
        r del mykey
        assert_error "*out of range*" {r setbit mykey 0 -1}
        assert_error "*out of range*" {r setbit mykey 0  2}
        assert_error "*out of range*" {r setbit mykey 0 10}
        assert_error "*out of range*" {r setbit mykey 0 20}
    }
    """
    r.run("del", "mykey")
    with pytest.raises(Exception, match=".*out\\ of\\ range.*"):
        r.run("setbit", "mykey", 0, -1)
    with pytest.raises(Exception, match=".*out\\ of\\ range.*"):
        r.run("setbit", "mykey", 0, 2)
    with pytest.raises(Exception, match=".*out\\ of\\ range.*"):
        r.run("setbit", "mykey", 0, 10)
    with pytest.raises(Exception, match=".*out\\ of\\ range.*"):
        r.run("setbit", "mykey", 0, 20)


def test_setbit_fuzzing(r: ValkeyTestClient) -> None:
    """
    test "SETBIT fuzzing" {
        set str ""
        set len [expr 256*8]
        r del mykey

        for {set i 0} {$i < 2000} {incr i} {
            set bitnum [randomInt $len]
            set bitval [randomInt 2]
            set fmt [format "%%-%ds%%d%%-s" $bitnum]
            set head [string range $str 0 $bitnum-1]
            set tail [string range $str $bitnum+1 end]
            set str [string map {" " 0} [format $fmt $head $bitval $tail]]

            r setbit mykey $bitnum $bitval
            assert_equal [binary format B* $str] [r get mykey]
        }
    }
    """
    str = ""
    len = expr("256*8")
    r.run("del", "mykey")
    i = 0
    while i < 2000:
        bitnum = random_int(len)
        bitval = random_int(2)
        fmt = format_("%%-%ds%%d%%-s", bitnum)
        head = string("range", str, 0, bitnum, -1)
        tail = string("range", str, bitnum, 1, "end")
        str = string("map", '" " 0', format_(fmt, head, bitval, tail))
        r.run("setbit", "mykey", bitnum, bitval)
        assert binary("format", "B*", str) == r.run("get", "mykey")
        i += 1


def test_getbit_against_non_existing_key(r: ValkeyTestClient) -> None:
    """
    test "GETBIT against non-existing key" {
        r del mykey
        assert_equal 0 [r getbit mykey 0]
    }
    """
    r.run("del", "mykey")
    assert 0 == r.run("getbit", "mykey", 0)


def test_getbit_against_string_encoded_key(r: ValkeyTestClient) -> None:
    """
    test "GETBIT against string-encoded key" {
        # Single byte with 2nd and 3rd bit set
        r set mykey "`"

        # In-range
        assert_equal 0 [r getbit mykey 0]
        assert_equal 1 [r getbit mykey 1]
        assert_equal 1 [r getbit mykey 2]
        assert_equal 0 [r getbit mykey 3]

        # Out-range
        assert_equal 0 [r getbit mykey 8]
        assert_equal 0 [r getbit mykey 100]
        assert_equal 0 [r getbit mykey 10000]
    }
    """
    r.run("set", "mykey", "`")
    assert 0 == r.run("getbit", "mykey", 0)
    assert 1 == r.run("getbit", "mykey", 1)
    assert 1 == r.run("getbit", "mykey", 2)
    assert 0 == r.run("getbit", "mykey", 3)
    assert 0 == r.run("getbit", "mykey", 8)
    assert 0 == r.run("getbit", "mykey", 100)
    assert 0 == r.run("getbit", "mykey", 10000)


def test_getbit_against_integer_encoded_key(r: ValkeyTestClient) -> None:
    """
    test "GETBIT against integer-encoded key" {
        r set mykey 1
        assert_encoding int mykey

        # Ascii "1" is integer 49 = 00 11 00 01
        assert_equal 0 [r getbit mykey 0]
        assert_equal 0 [r getbit mykey 1]
        assert_equal 1 [r getbit mykey 2]
        assert_equal 1 [r getbit mykey 3]

        # Out-range
        assert_equal 0 [r getbit mykey 8]
        assert_equal 0 [r getbit mykey 100]
        assert_equal 0 [r getbit mykey 10000]
    }
    """
    r.run("set", "mykey", 1)
    assert_encoding("int", "mykey")
    assert 0 == r.run("getbit", "mykey", 0)
    assert 0 == r.run("getbit", "mykey", 1)
    assert 1 == r.run("getbit", "mykey", 2)
    assert 1 == r.run("getbit", "mykey", 3)
    assert 0 == r.run("getbit", "mykey", 8)
    assert 0 == r.run("getbit", "mykey", 100)
    assert 0 == r.run("getbit", "mykey", 10000)


@pytest.mark.xfail(reason="not implemented")
def test_setrange_against_non_existing_key(r: ValkeyTestClient) -> None:
    """
    test "SETRANGE against non-existing key" {
        r del mykey
        assert_equal 3 [r setrange mykey 0 foo]
        assert_equal "foo" [r get mykey]

        r del mykey
        assert_equal 0 [r setrange mykey 0 ""]
        assert_equal 0 [r exists mykey]

        r del mykey
        assert_equal 4 [r setrange mykey 1 foo]
        assert_equal "\000foo" [r get mykey]
    }
    """
    r.run("del", "mykey")
    assert 3 == r.run("setrange", "mykey", 0, "foo")
    assert "foo" == r.run("get", "mykey")
    r.run("del", "mykey")
    assert 0 == r.run("setrange", "mykey", 0, "")
    assert 0 == r.run("exists", "mykey")
    r.run("del", "mykey")
    assert 4 == r.run("setrange", "mykey", 1, "foo")
    # TODO: assert_equal "\000foo" r get mykey


@pytest.mark.xfail(reason="not implemented")
def test_setrange_against_string_encoded_key(r: ValkeyTestClient) -> None:
    """
    test "SETRANGE against string-encoded key" {
        r set mykey "foo"
        assert_equal 3 [r setrange mykey 0 b]
        assert_equal "boo" [r get mykey]

        r set mykey "foo"
        assert_equal 3 [r setrange mykey 0 ""]
        assert_equal "foo" [r get mykey]

        r set mykey "foo"
        assert_equal 3 [r setrange mykey 1 b]
        assert_equal "fbo" [r get mykey]

        r set mykey "foo"
        assert_equal 7 [r setrange mykey 4 bar]
        assert_equal "foo\000bar" [r get mykey]
    }
    """
    r.run("set", "mykey", "foo")
    assert 3 == r.run("setrange", "mykey", 0, "b")
    assert "boo" == r.run("get", "mykey")
    r.run("set", "mykey", "foo")
    assert 3 == r.run("setrange", "mykey", 0, "")
    assert "foo" == r.run("get", "mykey")
    r.run("set", "mykey", "foo")
    assert 3 == r.run("setrange", "mykey", 1, "b")
    assert "fbo" == r.run("get", "mykey")
    r.run("set", "mykey", "foo")
    assert 7 == r.run("setrange", "mykey", 4, "bar")
    # TODO: assert_equal "foo\000bar" r get mykey


@pytest.mark.xfail(reason="not implemented")
def test_setrange_against_integer_encoded_key(r: ValkeyTestClient) -> None:
    """
    test "SETRANGE against integer-encoded key" {
        r set mykey 1234
        assert_encoding int mykey
        assert_equal 4 [r setrange mykey 0 2]
        assert_encoding raw mykey
        assert_equal 2234 [r get mykey]

        # Shouldn't change encoding when nothing is set
        r set mykey 1234
        assert_encoding int mykey
        assert_equal 4 [r setrange mykey 0 ""]
        assert_encoding int mykey
        assert_equal 1234 [r get mykey]

        r set mykey 1234
        assert_encoding int mykey
        assert_equal 4 [r setrange mykey 1 3]
        assert_encoding raw mykey
        assert_equal 1334 [r get mykey]

        r set mykey 1234
        assert_encoding int mykey
        assert_equal 6 [r setrange mykey 5 2]
        assert_encoding raw mykey
        assert_equal "1234\0002" [r get mykey]
    }
    """
    r.run("set", "mykey", 1234)
    assert_encoding("int", "mykey")
    assert 4 == r.run("setrange", "mykey", 0, 2)
    assert_encoding("raw", "mykey")
    assert 2234 == r.run("get", "mykey")
    r.run("set", "mykey", 1234)
    assert_encoding("int", "mykey")
    assert 4 == r.run("setrange", "mykey", 0, "")
    assert_encoding("int", "mykey")
    assert 1234 == r.run("get", "mykey")
    r.run("set", "mykey", 1234)
    assert_encoding("int", "mykey")
    assert 4 == r.run("setrange", "mykey", 1, 3)
    assert_encoding("raw", "mykey")
    assert 1334 == r.run("get", "mykey")
    r.run("set", "mykey", 1234)
    assert_encoding("int", "mykey")
    assert 6 == r.run("setrange", "mykey", 5, 2)
    assert_encoding("raw", "mykey")
    # TODO: assert_equal "1234\0002" r get mykey


def test_setrange_against_key_with_wrong_type(r: ValkeyTestClient) -> None:
    """
    test "SETRANGE against key with wrong type" {
        r del mykey
        r lpush mykey "foo"
        assert_error "WRONGTYPE*" {r setrange mykey 0 bar}
    }
    """
    r.run("del", "mykey")
    r.run("lpush", "mykey", "foo")
    with pytest.raises(Exception, match="WRONGTYPE.*"):
        r.run("setrange", "mykey", 0, "bar")


def test_setrange_with_out_of_range_offset(r: ValkeyTestClient) -> None:
    """
    test "SETRANGE with out of range offset" {
        r del mykey
        assert_error "*maximum allowed size*" {r setrange mykey [expr 512*1024*1024-4] world}

        r set mykey "hello"
        assert_error "*out of range*" {r setrange mykey -1 world}
        assert_error "*maximum allowed size*" {r setrange mykey [expr 512*1024*1024-4] world}
    }
    """
    r.run("del", "mykey")
    with pytest.raises(Exception, match=".*maximum\\ allowed\\ size.*"):
        r.run("setrange", "mykey", expr("512*1024*1024-4"), "world")
    r.run("set", "mykey", "hello")
    with pytest.raises(Exception, match=".*out\\ of\\ range.*"):
        r.run("setrange", "mykey", -1, "world")
    with pytest.raises(Exception, match=".*maximum\\ allowed\\ size.*"):
        r.run("setrange", "mykey", expr("512*1024*1024-4"), "world")


def test_getrange_against_non_existing_key(r: ValkeyTestClient) -> None:
    """
    test "GETRANGE against non-existing key" {
        r del mykey
        assert_equal "" [r getrange mykey 0 -1]
    }
    """
    r.run("del", "mykey")
    assert "" == r.run("getrange", "mykey", 0, -1)


def test_getrange_against_wrong_key_type(r: ValkeyTestClient) -> None:
    """
    test "GETRANGE against wrong key type" {
        r lpush lkey1 "list"
        assert_error {WRONGTYPE Operation against a key holding the wrong kind of value*} {r getrange lkey1 0 -1}
    }
    """
    r.run("lpush", "lkey1", "list")
    with pytest.raises(
        Exception, match="WRONGTYPE\\ Operation\\ against\\ a\\ key\\ holding\\ the\\ wrong\\ kind\\ of\\ value.*"
    ):
        r.run("getrange", "lkey1", 0, -1)


def test_getrange_against_string_value(r: ValkeyTestClient) -> None:
    """
    test "GETRANGE against string value" {
        r set mykey "Hello World"
        assert_equal "Hell" [r getrange mykey 0 3]
        assert_equal "Hello World" [r getrange mykey 0 -1]
        assert_equal "orld" [r getrange mykey -4 -1]
        assert_equal "" [r getrange mykey 5 3]
        assert_equal " World" [r getrange mykey 5 5000]
        assert_equal "Hello World" [r getrange mykey -5000 10000]
    }
    """
    r.run("set", "mykey", "Hello World")
    assert "Hell" == r.run("getrange", "mykey", 0, 3)
    assert "Hello World" == r.run("getrange", "mykey", 0, -1)
    assert "orld" == r.run("getrange", "mykey", -4, -1)
    assert "" == r.run("getrange", "mykey", 5, 3)
    assert " World" == r.run("getrange", "mykey", 5, 5000)
    assert "Hello World" == r.run("getrange", "mykey", -5000, 10000)


def test_getrange_against_integer_encoded_value(r: ValkeyTestClient) -> None:
    """
    test "GETRANGE against integer-encoded value" {
        r set mykey 1234
        assert_equal "123" [r getrange mykey 0 2]
        assert_equal "1234" [r getrange mykey 0 -1]
        assert_equal "234" [r getrange mykey -3 -1]
        assert_equal "" [r getrange mykey 5 3]
        assert_equal "4" [r getrange mykey 3 5000]
        assert_equal "1234" [r getrange mykey -5000 10000]
    }
    """
    r.run("set", "mykey", 1234)
    assert "123" == r.run("getrange", "mykey", 0, 2)
    assert "1234" == r.run("getrange", "mykey", 0, -1)
    assert "234" == r.run("getrange", "mykey", -3, -1)
    assert "" == r.run("getrange", "mykey", 5, 3)
    assert "4" == r.run("getrange", "mykey", 3, 5000)
    assert "1234" == r.run("getrange", "mykey", -5000, 10000)


def test_getrange_fuzzing(r: ValkeyTestClient) -> None:
    """
    test "GETRANGE fuzzing" {
        for {set i 0} {$i < 1000} {incr i} {
            r set bin [set bin [randstring 0 1024 binary]]
            set _start [set start [randomInt 1500]]
            set _end [set end [randomInt 1500]]
            if {$_start < 0} {set _start "end-[abs($_start)-1]"}
            if {$_end < 0} {set _end "end-[abs($_end)-1]"}
            assert_equal [string range $bin $_start $_end] [r getrange bin $start $end]
        }
    }
    """
    for_(
        "set i 0",
        "$i < 1000",
        "incr i",
        '            r set bin [set bin [randstring 0 1024 binary]]\n            set _start [set start [randomInt 1500]]\n            set _end [set end [randomInt 1500]]\n            if {$_start < 0} {set _start "end-[abs($_start)-1]"}\n            if {$_end < 0} {set _end "end-[abs($_end)-1]"}\n            assert_equal [string range $bin $_start $_end] [r getrange bin $start $end]\n        ',
    )


def test_coverage_substr(r: ValkeyTestClient) -> None:
    """
    test "Coverage: SUBSTR" {
        r set key abcde
        assert_equal "a" [r substr key 0 0]
        assert_equal "abcd" [r substr key 0 3]
        assert_equal "bcde" [r substr key -4 -1]
        assert_equal "" [r substr key -1 -3]
        assert_equal "" [r substr key 7 8]
        assert_equal "" [r substr nokey 0 1]
    }
    """
    r.run("set", "key", "abcde")
    assert "a" == r.run("substr", "key", 0, 0)
    assert "abcd" == r.run("substr", "key", 0, 3)
    assert "bcde" == r.run("substr", "key", -4, -1)
    assert "" == r.run("substr", "key", -1, -3)
    assert "" == r.run("substr", "key", 7, 8)
    assert "" == r.run("substr", "nokey", 0, 1)


@pytest.mark.skipif("", reason="{[string match {*jemalloc*} [s mem_allocator]]}")
def test_trim_on_set_with_big_value(r: ValkeyTestClient) -> None:
    """
    test {trim on SET with big value} {
        # set a big value to trigger increasing the query buf
        r set key [string repeat A 100000]
        # set a smaller value but > PROTO_MBULK_BIG_ARG (32*1024) the server will try to save the query buf itself on the DB.
        r set key [string repeat A 33000]
        # asset the value was trimmed
        assert {[r memory usage key] < 42000}; # 42K to count for Jemalloc's additional memory overhead.
    }
    """
    r.run("set", "key", string("repeat", "A", 100000))
    r.run("set", "key", string("repeat", "A", 33000))
    assert r.run("memory", "usage", "key") < 42000


def test_extended_set_can_detect_syntax_errors(r: ValkeyTestClient) -> None:
    """
    test {Extended SET can detect syntax errors} {
        set e {}
        catch {r set foo bar non-existing-option} e
        set e
    } {*syntax*}
    """
    e = ""
    try:
        e = r.run("set", "foo", "bar", "non-existing-option")
    except Exception as _catch_err:
        e = str(_catch_err)
    assert e == "*syntax*"


@pytest.mark.xfail(reason="not implemented")
def test_extended_set_nx_option(r: ValkeyTestClient) -> None:
    """
    test {Extended SET NX option} {
        r del foo
        set v1 [r set foo 1 nx]
        set v2 [r set foo 2 nx]
        list $v1 $v2 [r get foo]
    } {OK {} 1}
    """
    r.run("del", "foo")
    v1 = r.run("set", "foo", 1, "nx")
    v2 = r.run("set", "foo", 2, "nx")
    # TODO: list v1 v2 r get foo
    assert False


@pytest.mark.xfail(reason="not implemented")
def test_extended_set_xx_option(r: ValkeyTestClient) -> None:
    """
    test {Extended SET XX option} {
        r del foo
        set v1 [r set foo 1 xx]
        r set foo bar
        set v2 [r set foo 2 xx]
        list $v1 $v2 [r get foo]
    } {{} OK 2}
    """
    r.run("del", "foo")
    v1 = r.run("set", "foo", 1, "xx")
    r.run("set", "foo", "bar")
    v2 = r.run("set", "foo", 2, "xx")
    # TODO: list v1 v2 r get foo
    assert False


@pytest.mark.xfail(reason="not implemented")
def test_extended_set_get_option(r: ValkeyTestClient) -> None:
    """
    test {Extended SET GET option} {
        r del foo
        r set foo bar
        set old_value [r set foo bar2 GET]
        set new_value [r get foo]
        list $old_value $new_value
    } {bar bar2}
    """
    r.run("del", "foo")
    r.run("set", "foo", "bar")
    old_value = r.run("set", "foo", "bar2", "GET")
    new_value = r.run("get", "foo")
    # TODO: list old_value new_value
    assert False


@pytest.mark.xfail(reason="not implemented")
def test_extended_set_get_option_with_no_previous_value(r: ValkeyTestClient) -> None:
    """
    test {Extended SET GET option with no previous value} {
        r del foo
        set old_value [r set foo bar GET]
        set new_value [r get foo]
        list $old_value $new_value
    } {{} bar}
    """
    r.run("del", "foo")
    old_value = r.run("set", "foo", "bar", "GET")
    new_value = r.run("get", "foo")
    # TODO: list old_value new_value
    assert False


@pytest.mark.xfail(reason="not implemented")
def test_extended_set_get_option_with_xx(r: ValkeyTestClient) -> None:
    """
    test {Extended SET GET option with XX} {
        r del foo
        r set foo bar
        set old_value [r set foo baz GET XX]
        set new_value [r get foo]
        list $old_value $new_value
    } {bar baz}
    """
    r.run("del", "foo")
    r.run("set", "foo", "bar")
    old_value = r.run("set", "foo", "baz", "GET", "XX")
    new_value = r.run("get", "foo")
    # TODO: list old_value new_value
    assert False


@pytest.mark.xfail(reason="not implemented")
def test_extended_set_get_option_with_xx_and_no_previous_value(r: ValkeyTestClient) -> None:
    """
    test {Extended SET GET option with XX and no previous value} {
        r del foo
        set old_value [r set foo bar GET XX]
        set new_value [r get foo]
        list $old_value $new_value
    } {{} {}}
    """
    r.run("del", "foo")
    old_value = r.run("set", "foo", "bar", "GET", "XX")
    new_value = r.run("get", "foo")
    # TODO: list old_value new_value
    assert False


@pytest.mark.xfail(reason="not implemented")
def test_extended_set_get_option_with_nx(r: ValkeyTestClient) -> None:
    """
    test {Extended SET GET option with NX} {
        r del foo
        set old_value [r set foo bar GET NX]
        set new_value [r get foo]
        list $old_value $new_value
    } {{} bar}
    """
    r.run("del", "foo")
    old_value = r.run("set", "foo", "bar", "GET", "NX")
    new_value = r.run("get", "foo")
    # TODO: list old_value new_value
    assert False


@pytest.mark.xfail(reason="not implemented")
def test_extended_set_get_option_with_nx_and_previous_value(r: ValkeyTestClient) -> None:
    """
    test {Extended SET GET option with NX and previous value} {
        r del foo
        r set foo bar
        set old_value [r set foo baz GET NX]
        set new_value [r get foo]
        list $old_value $new_value
    } {bar bar}
    """
    r.run("del", "foo")
    r.run("set", "foo", "bar")
    old_value = r.run("set", "foo", "baz", "GET", "NX")
    new_value = r.run("get", "foo")
    # TODO: list old_value new_value
    assert False


def test_extended_set_get_with_incorrect_type_should_result_in_wrong_type_error(r: ValkeyTestClient) -> None:
    """
    test {Extended SET GET with incorrect type should result in wrong type error} {
        r del foo
        r rpush foo waffle
        catch {r set foo bar GET} err1
        assert_equal "waffle" [r rpop foo]
        set err1
    } {*WRONGTYPE*}
    """
    r.run("del", "foo")
    r.run("rpush", "foo", "waffle")
    try:
        err1 = r.run("set", "foo", "bar", "GET")
    except Exception as _catch_err:
        err1 = str(_catch_err)
    assert "waffle" == r.run("rpop", "foo")
    assert err1 == "*WRONGTYPE*"


def test_set_with_ifeq_conditional(r: ValkeyTestClient) -> None:
    """
    test "SET with IFEQ conditional" {
        r del foo

        r set foo "initial_value"

        assert_equal {OK} [r set foo "new_value" ifeq "initial_value"]
        assert_equal "new_value" [r get foo]

        assert_equal {} [r set foo "should_not_set" ifeq "wrong_value"]
        assert_equal "new_value" [r get foo]
    }
    """
    r.run("del", "foo")
    r.run("set", "foo", "initial_value")
    assert "OK" == r.run("set", "foo", "new_value", "ifeq", "initial_value")
    assert "new_value" == r.run("get", "foo")
    assert "" == r.run("set", "foo", "should_not_set", "ifeq", "wrong_value")
    assert "new_value" == r.run("get", "foo")


def test_set_with_ifeq_conditional_non_string_current_value(r: ValkeyTestClient) -> None:
    """
    test "SET with IFEQ conditional - non-string current value" {
        r del foo

        r sadd foo "some_set_value"
        assert_error {WRONGTYPE Operation against a key holding the wrong kind of value} {r set foo "new_value" ifeq "some_set_value"}
    }
    """
    r.run("del", "foo")
    r.run("sadd", "foo", "some_set_value")
    with pytest.raises(
        Exception, match="WRONGTYPE\\ Operation\\ against\\ a\\ key\\ holding\\ the\\ wrong\\ kind\\ of\\ value"
    ):
        r.run("set", "foo", "new_value", "ifeq", "some_set_value")


def test_set_with_ifeq_conditional_with_get(r: ValkeyTestClient) -> None:
    """
    test "SET with IFEQ conditional - with get" {
        r del foo

        assert_equal {} [r set foo "new_value" ifeq "initial_value" get]
        assert_equal {} [r get foo]

        r set foo "initial_value"

        assert_equal "initial_value" [r set foo "new_value" ifeq "initial_value" get]
        assert_equal "new_value" [r get foo]
    }
    """
    r.run("del", "foo")
    assert "" == r.run("set", "foo", "new_value", "ifeq", "initial_value", "get")
    assert "" == r.run("get", "foo")
    r.run("set", "foo", "initial_value")
    assert "initial_value" == r.run("set", "foo", "new_value", "ifeq", "initial_value", "get")
    assert "new_value" == r.run("get", "foo")


def test_set_with_ifeq_conditional_non_string_current_value_with_get(r: ValkeyTestClient) -> None:
    """
    test "SET with IFEQ conditional - non string current value with get" {
        r del foo

        r sadd foo "some_set_value"

        assert_error {WRONGTYPE Operation against a key holding the wrong kind of value} {r set foo "new_value" ifeq "initial_value" get}
    }
    """
    r.run("del", "foo")
    r.run("sadd", "foo", "some_set_value")
    with pytest.raises(
        Exception, match="WRONGTYPE\\ Operation\\ against\\ a\\ key\\ holding\\ the\\ wrong\\ kind\\ of\\ value"
    ):
        r.run("set", "foo", "new_value", "ifeq", "initial_value", "get")


def test_set_with_ifeq_conditional_with_xx(r: ValkeyTestClient) -> None:
    """
    test "SET with IFEQ conditional - with xx" {
        r del foo
        assert_error {ERR syntax error} {r set foo "new_value" ifeq "initial_value" xx}
    }
    """
    r.run("del", "foo")
    with pytest.raises(Exception, match="ERR\\ syntax\\ error"):
        r.run("set", "foo", "new_value", "ifeq", "initial_value", "xx")


def test_set_with_ifeq_conditional_with_nx(r: ValkeyTestClient) -> None:
    """
    test "SET with IFEQ conditional - with nx" {
        r del foo
        assert_error {ERR syntax error} {r set foo "new_value" ifeq "initial_value" nx}
    }
    """
    r.run("del", "foo")
    with pytest.raises(Exception, match="ERR\\ syntax\\ error"):
        r.run("set", "foo", "new_value", "ifeq", "initial_value", "nx")


def test_extended_set_ex_option(r: ValkeyTestClient) -> None:
    """
    test {Extended SET EX option} {
        r del foo
        r set foo bar ex 10
        set ttl [r ttl foo]
        assert {$ttl <= 10 && $ttl > 5}
    }
    """
    r.run("del", "foo")
    r.run("set", "foo", "bar", "ex", 10)
    ttl = r.run("ttl", "foo")
    assert (ttl <= 10) and (ttl > 5)


def test_extended_set_px_option(r: ValkeyTestClient) -> None:
    """
    test {Extended SET PX option} {
        r del foo
        r set foo bar px 10000
        set ttl [r ttl foo]
        assert {$ttl <= 10 && $ttl > 5}
    }
    """
    r.run("del", "foo")
    r.run("set", "foo", "bar", "px", 10000)
    ttl = r.run("ttl", "foo")
    assert (ttl <= 10) and (ttl > 5)


def test_extended_set_exat_option(r: ValkeyTestClient) -> None:
    """
    test "Extended SET EXAT option" {
        r del foo
        r set foo bar exat [expr [clock seconds] + 10]
        assert_range [r ttl foo] 5 10
    }
    """
    r.run("del", "foo")
    r.run("set", "foo", "bar", "exat", expr(clock("seconds"), "+", 10))
    assert_range(r.run("ttl", "foo"), 5, 10)


def test_extended_set_pxat_option(r: ValkeyTestClient) -> None:
    """
    test "Extended SET PXAT option" {
        r del foo
        r set foo bar pxat [expr [clock milliseconds] + 10000]
        assert_range [r ttl foo] 5 10
    }
    """
    r.run("del", "foo")
    r.run("set", "foo", "bar", "pxat", expr(clock("milliseconds"), "+", 10000))
    assert_range(r.run("ttl", "foo"), 5, 10)


def test_set_exat_or_pxat_expiration_time_is_expired(r: ValkeyTestClient) -> None:
    """
    test "SET EXAT / PXAT Expiration time is expired" {
        r debug set-active-expire 0
        set repl [attach_to_replication_stream]

        # Key exists.
        r set foo bar
        r set foo bar exat [expr [clock seconds] - 100]
        assert_error {ERR no such key} {r debug object foo}
        r set foo bar
        r set foo bar pxat [expr [clock milliseconds] - 10000]
        assert_error {ERR no such key} {r debug object foo}

        # Key does not exist.
        r del foo
        r set foo bar exat [expr [clock seconds] - 100]
        assert_error {ERR no such key} {r debug object foo}
        r set foo bar pxat [expr [clock milliseconds] - 10000]
        assert_error {ERR no such key} {r debug object foo}

        r incr foo
        assert_replication_stream $repl {
           {select *}
           {set foo bar}
           {unlink foo}
           {set foo bar}
           {unlink foo}
           {incr foo}
        }

        r debug set-active-expire 1
        close_replication_stream $repl
    } {} {needs:debug needs:repl}
    """
    r.run("debug", "set-active-expire", 0)
    repl = attach_to_replication_stream()
    r.run("set", "foo", "bar")
    r.run("set", "foo", "bar", "exat", expr(clock("seconds"), "-", 100))
    with pytest.raises(Exception, match="ERR\\ no\\ such\\ key"):
        r.run("debug", "object", "foo")
    r.run("set", "foo", "bar")
    r.run("set", "foo", "bar", "pxat", expr(clock("milliseconds"), "-", 10000))
    with pytest.raises(Exception, match="ERR\\ no\\ such\\ key"):
        r.run("debug", "object", "foo")
    r.run("del", "foo")
    r.run("set", "foo", "bar", "exat", expr(clock("seconds"), "-", 100))
    with pytest.raises(Exception, match="ERR\\ no\\ such\\ key"):
        r.run("debug", "object", "foo")
    r.run("set", "foo", "bar", "pxat", expr(clock("milliseconds"), "-", 10000))
    with pytest.raises(Exception, match="ERR\\ no\\ such\\ key"):
        r.run("debug", "object", "foo")
    r.run("incr", "foo")
    assert_replication_stream(
        repl,
        "           {select *}\n           {set foo bar}\n           {unlink foo}\n           {set foo bar}\n           {unlink foo}\n           {incr foo}\n        ",
    )
    r.run("debug", "set-active-expire", 1)
    close_replication_stream(repl)


def test_extended_set_using_multiple_options_at_once(r: ValkeyTestClient) -> None:
    """
    test {Extended SET using multiple options at once} {
        r set foo val
        assert {[r set foo bar xx px 10000] eq {OK}}
        set ttl [r ttl foo]
        assert {$ttl <= 10 && $ttl > 5}
    }
    """
    r.run("set", "foo", "val")
    assert r.run("set", "foo", "bar", "xx", "px", 10000) == "OK"
    ttl = r.run("ttl", "foo")
    assert (ttl <= 10) and (ttl > 5)


def test_getrange_with_huge_ranges_github_issue_1844(r: ValkeyTestClient) -> None:
    """
    test {GETRANGE with huge ranges, Github issue #1844} {
        r set foo bar
        r getrange foo 0 4294967297
    } {bar}
    """
    r.run("set", "foo", "bar")
    assert r.run("getrange", "foo", 0, 4294967297) == "bar"


"""
set rna1 {CACCTTCCCAGGTAACAAACCAACCAACTTTCGATCTCTTGTAGATCTGTTCTCTAAACGAACTTTAAAATCTGTGTGGCTGTCACTCGGCTGCATGCTTAGTGCACTCACGCAGTATAATTAATAACTAATTACTGTCGTTGACAGGACACGAGTAACTCGTCTATCTTCTGCAGGCTGCTTACGGTTTCGTCCGTGTTGCAGCCGATCATCAGCACATCTAGGTTTCGTCCGGGTGTG}
"""


"""
set rna2 {ATTAAAGGTTTATACCTTCCCAGGTAACAAACCAACCAACTTTCGATCTCTTGTAGATCTGTTCTCTAAACGAACTTTAAAATCTGTGTGGCTGTCACTCGGCTGCATGCTTAGTGCACTCACGCAGTATAATTAATAACTAATTACTGTCGTTGACAGGACACGAGTAACTCGTCTATCTTCTGCAGGCTGCTTACGGTTTCGTCCGTGTTGCAGCCGATCATCAGCACATCTAGGTTT}
"""


"""
set rnalcs {ACCTTCCCAGGTAACAAACCAACCAACTTTCGATCTCTTGTAGATCTGTTCTCTAAACGAACTTTAAAATCTGTGTGGCTGTCACTCGGCTGCATGCTTAGTGCACTCACGCAGTATAATTAATAACTAATTACTGTCGTTGACAGGACACGAGTAACTCGTCTATCTTCTGCAGGCTGCTTACGGTTTCGTCCGTGTTGCAGCCGATCATCAGCACATCTAGGTTT}
"""


@pytest.mark.xfail(reason="not implemented")
def test_lcs_basic(r: ValkeyTestClient) -> None:
    """
    test {LCS basic} {
        r set virus1{t} $rna1
        r set virus2{t} $rna2
        r LCS virus1{t} virus2{t}
    } rnalcs
    """
    # TODO: r set virus1{t} rna1
    # TODO: r set virus2{t} rna2
    r.run("LCS", "virus1{t}", "virus2{t}")


@pytest.mark.xfail(reason="not implemented")
def test_lcs_len(r: ValkeyTestClient) -> None:
    """
    test {LCS len} {
        r set virus1{t} $rna1
        r set virus2{t} $rna2
        r LCS virus1{t} virus2{t} LEN
    } string length $rnalcs
    """
    # TODO: r set virus1{t} rna1
    # TODO: r set virus2{t} rna2
    r.run("LCS", "virus1{t}", "virus2{t}", "LEN")


def test_lcs_indexes(r: ValkeyTestClient) -> None:
    """
    test {LCS indexes} {
        dict get [r LCS virus1{t} virus2{t} IDX] matches
    } {{{238 238} {239 239}} {{236 236} {238 238}} {{229 230} {236 237}} {{224 224} {235 235}} {{1 222} {13 234}}}
    """
    assert (
        r.run("LCS", "virus1{t}", "virus2{t}", "IDX")["matches"]
        == "{{238 238} {239 239}} {{236 236} {238 238}} {{229 230} {236 237}} {{224 224} {235 235}} {{1 222} {13 234}}"
    )


def test_lcs_indexes_with_match_len(r: ValkeyTestClient) -> None:
    """
    test {LCS indexes with match len} {
        dict get [r LCS virus1{t} virus2{t} IDX WITHMATCHLEN] matches
    } {{{238 238} {239 239} 1} {{236 236} {238 238} 1} {{229 230} {236 237} 2} {{224 224} {235 235} 1} {{1 222} {13 234} 222}}
    """
    assert (
        r.run("LCS", "virus1{t}", "virus2{t}", "IDX", "WITHMATCHLEN")["matches"]
        == "{{238 238} {239 239} 1} {{236 236} {238 238} 1} {{229 230} {236 237} 2} {{224 224} {235 235} 1} {{1 222} {13 234} 222}"
    )


def test_lcs_indexes_with_match_len_and_minimum_match_len(r: ValkeyTestClient) -> None:
    """
    test {LCS indexes with match len and minimum match len} {
        dict get [r LCS virus1{t} virus2{t} IDX WITHMATCHLEN MINMATCHLEN 5] matches
    } {{{1 222} {13 234} 222}}
    """
    assert (
        r.run("LCS", "virus1{t}", "virus2{t}", "IDX", "WITHMATCHLEN", "MINMATCHLEN", 5)["matches"]
        == "{{1 222} {13 234} 222}"
    )


def test_setrange_with_huge_offset(r: ValkeyTestClient) -> None:
    """
    test {SETRANGE with huge offset} {
        foreach value {9223372036854775807 2147483647} {
            catch {[r setrange K $value A]} res
            # expecting a different error on 32 and 64 bit systems
            if {![string match "*string exceeds maximum allowed size*" $res] && ![string match "*out of range*" $res]} {
                assert_equal $res "expecting an error"
           }
        }
    }
    """
    foreach(
        "value",
        "9223372036854775807 2147483647",
        '            catch {[r setrange K $value A]} res\n            # expecting a different error on 32 and 64 bit systems\n            if {![string match "*string exceeds maximum allowed size*" $res] && ![string match "*out of range*" $res]} {\n                assert_equal $res "expecting an error"\n           }\n        ',
    )


@pytest.mark.xfail(reason="not implemented")
def test_append_modifies_the_encoding_from_int_to_raw(r: ValkeyTestClient) -> None:
    """
    test {APPEND modifies the encoding from int to raw} {
        r del foo
        r set foo 1
        assert_encoding "int" foo
        r append foo 2

        set res {}
        lappend res [r get foo]
        assert_encoding "raw" foo

        r set bar 12
        assert_encoding "int" bar
        lappend res [r get bar]
    } {12 12}
    """
    r.run("del", "foo")
    r.run("set", "foo", 1)
    assert_encoding("int", "foo")
    r.run("append", "foo", 2)
    res = ""
    lappend("res", r.run("get", "foo"))
    assert_encoding("raw", "foo")
    r.run("set", "bar", 12)
    assert_encoding("int", "bar")
    # TODO: lappend res r get bar
    assert False


def test_delifeq_non_existing_key(r: ValkeyTestClient) -> None:
    """
    test {DELIFEQ non-existing key} {
        r del foo
        assert_equal 0 [r delifeq foo "test"]
    }
    """
    r.run("del", "foo")
    assert 0 == r.run("delifeq", "foo", "test")


def test_delifeq_existing_key_matching_value(r: ValkeyTestClient) -> None:
    """
    test {DELIFEQ existing key, matching value} {
        r set foo "test"
        assert_equal 1 [r delifeq foo "test"]
    }
    """
    r.run("set", "foo", "test")
    assert 1 == r.run("delifeq", "foo", "test")


def test_delifeq_existing_key_non_matching_value(r: ValkeyTestClient) -> None:
    """
    test {DELIFEQ existing key, non-matching value} {
        r set foo "nope"
        assert_equal 0 [r delifeq foo "test"]
    }
    """
    r.run("set", "foo", "nope")
    assert 0 == r.run("delifeq", "foo", "test")


def test_delifeq_existing_key_non_string_value(r: ValkeyTestClient) -> None:
    """
    test {DELIFEQ existing key, non-string value} {
        r del foo
        r sadd foo "test"
        assert_error "WRONGTYPE*" {r delifeq foo "test"}
    }
    """
    r.run("del", "foo")
    r.run("sadd", "foo", "test")
    with pytest.raises(Exception, match="WRONGTYPE.*"):
        r.run("delifeq", "foo", "test")


def test_delifeq_propagate_as_del_command_to_replica(r: ValkeyTestClient) -> None:
    """
    test {DELIFEQ propagate as DEL command to replica} {
        set repl [attach_to_replication_stream]
        r set foo bar
        r delifeq foo bar
        assert_replication_stream $repl {
            {select *}
            {set foo bar}
            {del foo}
        }
        close_replication_stream $repl
    } {} {needs:repl}
    """
    repl = attach_to_replication_stream()
    r.run("set", "foo", "bar")
    r.run("delifeq", "foo", "bar")
    assert_replication_stream(
        repl, "            {select *}\n            {set foo bar}\n            {del foo}\n        "
    )
    close_replication_stream(repl)


@pytest.mark.skipif("", reason="{[string match {*jemalloc*} [s mem_allocator]]}")
def test_memory_usage_of_embedded_string_value(r: ValkeyTestClient) -> None:
    """
    test {Memory usage of embedded string value} {
        # Check that we can fit 9 bytes of key + value into a 24 byte
        # allocation, including the serverObject itself.
        r set quux xyzzy
        assert_lessthan_equal [r memory usage quux] 24

        # Check that the SDS overhead of the embedded key and value is 6 bytes
        # (sds5 + sds8). This is the memory layout:
        #
        # +-------------------+----------+---------------+----------------+
        # | robj header       | key sds  | sds5 key      | sds8 value     |
        # | excluding val_ptr | hdr size | hdr "quux" \0 | hdr "xyzzy" \0 |
        # | 8 bytes           | 1        | 1  + 4    + 1 | 3  + 5     + 1 |
        # +-------------------+----------+---------------+----------------+
        #
        # The test must work when the server is compiled for 32 bit and TCL is
        # compiled and run on a 64 bit system or vice versa. The size of a
        # pointer in the server is what matters.
        set info_server [r info server]
        regexp {arch_bits:(\d+)} $info_server _ arch_bits
        set pointer_size [expr {$arch_bits / 8}]

        set content_size [expr {[string length quux] + [string length xyzzy]}]
        regexp {robj:(\d+)} [r debug structsize] _ obj_header_size
        # remove the size of the void *ptr (which is reused when value is embedded)
        set obj_header_size [expr {$obj_header_size - $pointer_size}]
        set debug_sdslen [r debug sdslen quux]
        regexp {key_sds_len:4 key_sds_avail:0 obj_alloc:(\d+)} $debug_sdslen _ obj_alloc
        regexp {val_sds_len:5 val_sds_avail:(\d+) val_alloc:(\d+)} $debug_sdslen _ avail val_alloc
        set sds_overhead [expr {$obj_alloc + $val_alloc - $obj_header_size - 1 - $content_size - $avail}]
        assert_equal 6 $sds_overhead
    } {} {needs:debug}
    """
    r.run("set", "quux", "xyzzy")
    assert_lessthan_equal(r.run("memory", "usage", "quux"), 24)
    info_server = r.run("info", "server")
    regexp("arch_bits:(\\d+)", info_server, "_", "arch_bits")
    pointer_size = expr("$arch_bits / 8")
    content_size = expr("[string length quux] + [string length xyzzy]")
    regexp("robj:(\\d+)", r.run("debug", "structsize"), "_", "obj_header_size")
    obj_header_size = expr("$obj_header_size - $pointer_size")
    debug_sdslen = r.run("debug", "sdslen", "quux")
    regexp("key_sds_len:4 key_sds_avail:0 obj_alloc:(\\d+)", debug_sdslen, "_", "obj_alloc")
    regexp("val_sds_len:5 val_sds_avail:(\\d+) val_alloc:(\\d+)", debug_sdslen, "_", "avail", "val_alloc")
    sds_overhead = expr("$obj_alloc + $val_alloc - $obj_header_size - 1 - $content_size - $avail")
    assert 6 == sds_overhead


# --- stubs for unimplemented TCL helpers ---


def assert_encoding(*args):
    raise NotImplementedError("assert_encoding")


def assert_lessthan_equal(*args):
    raise NotImplementedError("assert_lessthan_equal")


def assert_range(*args):
    raise NotImplementedError("assert_range")


def assert_replication_stream(*args):
    raise NotImplementedError("assert_replication_stream")


def attach_to_replication_stream(*args):
    raise NotImplementedError("attach_to_replication_stream")


def binary(*args):
    raise NotImplementedError("binary")


def clock(*args):
    raise NotImplementedError("clock")


def close_replication_stream(*args):
    raise NotImplementedError("close_replication_stream")


def expr(*args):
    raise NotImplementedError("expr")


def for_(*args):
    raise NotImplementedError("for_")


def foreach(*args):
    raise NotImplementedError("foreach")


def format_(*args):
    raise NotImplementedError("format_")


def if_(*args):
    raise NotImplementedError("if_")


def lappend(*args):
    raise NotImplementedError("lappend")


def random_int(*args):
    raise NotImplementedError("random_int")


def randstring(*args):
    raise NotImplementedError("randstring")


def regexp(*args):
    raise NotImplementedError("regexp")


def set_(*args):
    raise NotImplementedError("set_")


def string(*args):
    raise NotImplementedError("string")
