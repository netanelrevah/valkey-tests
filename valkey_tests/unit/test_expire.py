# ruff: noqa: PLR2004, ANN002, ANN201
import time
from fnmatch import fnmatch

import pytest

from tests.valkey_test_client import ValkeyTestClient

pytestmark = [pytest.mark.expire]


def test_expire_set_timeouts_multiple_times(r: ValkeyTestClient) -> None:
    """
    test {EXPIRE - set timeouts multiple times} {
        r set x foobar
        set v1 [r expire x 5]
        set v2 [r ttl x]
        set v3 [r expire x 10]
        set v4 [r ttl x]
        r expire x 2
        list $v1 $v2 $v3 $v4
    } {1 [45] 1 10}
    """
    r.run("set", "x", "foobar")
    v1 = r.run("expire", "x", 5)
    v2 = r.run("ttl", "x")
    v3 = r.run("expire", "x", 10)
    v4 = r.run("ttl", "x")
    r.run("expire", "x", 2)
    assert fnmatch(str([v1, v2, v3, v4]), "1 [45] 1 10")


def test_expire_it_should_be_still_possible_to_read_x(r: ValkeyTestClient) -> None:
    """
    test {EXPIRE - It should be still possible to read 'x'} {
        r get x
    } {foobar}
    """
    assert r.run("get", "x") == "foobar"


def test_expire_write_on_expire_should_work(r: ValkeyTestClient) -> None:
    """
    test {EXPIRE - write on expire should work} {
        r del x
        r lpush x foo
        r expire x 1000
        r lpush x bar
        r lrange x 0 -1
    } {bar foo}
    """
    r.run("del", "x")
    r.run("lpush", "x", "foo")
    r.run("expire", "x", 1000)
    r.run("lpush", "x", "bar")
    assert r.run("lrange", "x", 0, -1) == "bar foo"


def test_expireat_check_for_expire_alike_behavior(r: ValkeyTestClient) -> None:
    """
    test {EXPIREAT - Check for EXPIRE alike behavior} {
        r del x
        r set x foo
        r expireat x [expr [clock seconds]+15]
        r ttl x
    } {1[345]}
    """
    r.run("del", "x")
    r.run("set", "x", "foo")
    r.run("expireat", "x", expr(clock("seconds"), 15))
    assert fnmatch(str(r.run("ttl", "x")), "1[345]")


def test_setex_set_expire_combo_operation_check_for_ttl(r: ValkeyTestClient) -> None:
    """
    test {SETEX - Set + Expire combo operation. Check for TTL} {
        r setex x 12 test
        r ttl x
    } {1[012]}
    """
    r.run("setex", "x", 12, "test")
    assert fnmatch(str(r.run("ttl", "x")), "1[012]")


def test_setex_check_value(r: ValkeyTestClient) -> None:
    """
    test {SETEX - Check value} {
        r get x
    } {test}
    """
    assert r.run("get", "x") == "test"


def test_setex_overwrite_old_key(r: ValkeyTestClient) -> None:
    """
    test {SETEX - Overwrite old key} {
        r setex y 1 foo
        r get y
    } {foo}
    """
    r.run("setex", "y", 1, "foo")
    assert r.run("get", "y") == "foo"


def test_setex_wrong_time_parameter(r: ValkeyTestClient) -> None:
    """
    test {SETEX - Wrong time parameter} {
        catch {r setex z -10 foo} e
        set _ $e
    } {*invalid expire*}
    """
    try:
        e = r.run("setex", "z", -10, "foo")
    except Exception as _catch_err:
        e = str(_catch_err)
    assert fnmatch(str(e), "*invalid expire*")


def test_persist_can_undo_an_expire(r: ValkeyTestClient) -> None:
    """
    test {PERSIST can undo an EXPIRE} {
        r set x foo
        r expire x 50
        list [r ttl x] [r persist x] [r ttl x] [r get x]
    } {50 1 -1 foo}
    """
    r.run("set", "x", "foo")
    r.run("expire", "x", 50)
    assert [r.run("ttl", "x"), r.run("persist", "x"), r.run("ttl", "x"), r.run("get", "x")] == "50 1 -1 foo"


def test_persist_returns_0_against_non_existing_or_non_volatile_keys(r: ValkeyTestClient) -> None:
    """
    test {PERSIST returns 0 against non existing or non volatile keys} {
        r set x foo
        list [r persist foo] [r persist nokeyatall]
    } {0 0}
    """
    r.run("set", "x", "foo")
    assert [r.run("persist", "foo"), r.run("persist", "nokeyatall")] == "0 0"


@pytest.mark.xfail(reason="not implemented")
def test_expire_precision_is_now_the_millisecond(r: ValkeyTestClient) -> None:
    """
    test {EXPIRE precision is now the millisecond} {
        # This test is very likely to do a false positive if the
        # server is under pressure, so if it does not work give it a few more
        # chances.
        for {set j 0} {$j < 30} {incr j} {
            r del x
            r setex x 1 somevalue
            after 800
            set a [r get x]
            if {$a ne {somevalue}} continue
            after 300
            set b [r get x]
            if {$b eq {}} break
        }
        if {$::verbose} {
            puts "millisecond expire test attempts: $j"
        }
        assert_equal $a {somevalue}
        assert_equal $b {}
    }
    """
    j = 0
    while j < 30:
        r.run("del", "x")
        r.run("setex", "x", 1, "somevalue")
        time.sleep(800 / 1000)
        a = r.run("get", "x")
        if a != "somevalue":
            continue_()
        time.sleep(300 / 1000)
        b = r.run("get", "x")
        if b == "":
            break_()
        j += 1
    if_("$::verbose", '            puts "millisecond expire test attempts: $j"\n        ')
    # TODO: assert_equal a {somevalue}
    # TODO: assert_equal b {}


@pytest.mark.xfail(reason="not implemented")
def test_psetex_can_set_sub_second_expires(r: ValkeyTestClient) -> None:
    """
    test "PSETEX can set sub-second expires" {
        # This test is very likely to do a false positive if the server is
        # under pressure, so if it does not work give it a few more chances.
        for {set j 0} {$j < 50} {incr j} {
            r del x
            r psetex x 100 somevalue
            set a [r get x]
            after 101
            set b [r get x]

            if {$a eq {somevalue} && $b eq {}} break
        }
        if {$::verbose} { puts "PSETEX sub-second expire test attempts: $j" }
        list $a $b
    } {somevalue {}}
    """
    j = 0
    while j < 50:
        r.run("del", "x")
        r.run("psetex", "x", 100, "somevalue")
        a = r.run("get", "x")
        time.sleep(101 / 1000)
        b = r.run("get", "x")
        if (a == "somevalue") and (b == ""):
            break_()
        j += 1
    if_("$::verbose", ' puts "PSETEX sub-second expire test attempts: $j" ')
    # TODO: list a b
    assert False


@pytest.mark.xfail(reason="not implemented")
def test_pexpire_can_set_sub_second_expires(r: ValkeyTestClient) -> None:
    """
    test "PEXPIRE can set sub-second expires" {
        # This test is very likely to do a false positive if the server is
        # under pressure, so if it does not work give it a few more chances.
        for {set j 0} {$j < 50} {incr j} {
            r set x somevalue
            r pexpire x 100
            set c [r get x]
            after 101
            set d [r get x]

            if {$c eq {somevalue} && $d eq {}} break
        }
        if {$::verbose} { puts "PEXPIRE sub-second expire test attempts: $j" }
        list $c $d
    } {somevalue {}}
    """
    j = 0
    while j < 50:
        r.run("set", "x", "somevalue")
        r.run("pexpire", "x", 100)
        c = r.run("get", "x")
        time.sleep(101 / 1000)
        d = r.run("get", "x")
        if (c == "somevalue") and (d == ""):
            break_()
        j += 1
    if_("$::verbose", ' puts "PEXPIRE sub-second expire test attempts: $j" ')
    # TODO: list c d
    assert False


@pytest.mark.xfail(reason="not implemented")
def test_pexpireat_can_set_sub_second_expires(r: ValkeyTestClient) -> None:
    """
    test "PEXPIREAT can set sub-second expires" {
        # This test is very likely to do a false positive if the server is
        # under pressure, so if it does not work give it a few more chances.
        for {set j 0} {$j < 50} {incr j} {
            r set x somevalue
            set now [r time]
            r pexpireat x [expr ([lindex $now 0]*1000)+([lindex $now 1]/1000)+200]
            set e [r get x]
            after 201
            set f [r get x]

            if {$e eq {somevalue} && $f eq {}} break
        }
        if {$::verbose} { puts "PEXPIREAT sub-second expire test attempts: $j" }
        list $e $f
    } {somevalue {}}
    """
    j = 0
    while j < 50:
        r.run("set", "x", "somevalue")
        now = r.run("time")
        r.run("pexpireat", "x", expr("([lindex", now, "0]*1000)+([lindex", now, "1]/1000)+200"))
        e = r.run("get", "x")
        time.sleep(201 / 1000)
        f = r.run("get", "x")
        if (e == "somevalue") and (f == ""):
            break_()
        j += 1
    if_("$::verbose", ' puts "PEXPIREAT sub-second expire test attempts: $j" ')
    # TODO: list e f
    assert False


def test_expire_or_expireat_or_pexpire_or_pexpireat_expiration_time_is_already_expired(r: ValkeyTestClient) -> None:
    """
    test {EXPIRE / EXPIREAT / PEXPIRE / PEXPIREAT Expiration time is already expired} {
        r flushall
        r config resetstat

        r set x somevalue
        r expire x -1
        assert_equal {0} [r exists x]
        assert_equal {1} [s expired_keys]

        r set x somevalue
        r expireat x [expr [clock seconds] - 1]
        assert_equal {0} [r exists x]
        assert_equal {2}  [s expired_keys]

        r set x somevalue
        r pexpire x -1000
        assert_equal {0} [r exists x]
        assert_equal {3} [s expired_keys]

        r set x somevalue
        r pexpireat x [expr [clock milliseconds] - 1000]
        assert_equal {0} [r exists x]
        assert_equal {4} [s expired_keys]
    }
    """
    r.run("flushall")
    r.run("config", "resetstat")
    r.run("set", "x", "somevalue")
    r.run("expire", "x", -1)
    assert "0" == r.run("exists", "x")
    assert "1" == s("expired_keys")
    r.run("set", "x", "somevalue")
    r.run("expireat", "x", expr(clock("seconds"), "-", 1))
    assert "0" == r.run("exists", "x")
    assert "2" == s("expired_keys")
    r.run("set", "x", "somevalue")
    r.run("pexpire", "x", -1000)
    assert "0" == r.run("exists", "x")
    assert "3" == s("expired_keys")
    r.run("set", "x", "somevalue")
    r.run("pexpireat", "x", expr(clock("milliseconds"), "-", 1000))
    assert "0" == r.run("exists", "x")
    assert "4" == s("expired_keys")


def test_ttl_returns_time_to_live_in_seconds(r: ValkeyTestClient) -> None:
    """
    test {TTL returns time to live in seconds} {
        r del x
        r setex x 10 somevalue
        set ttl [r ttl x]
        assert {$ttl > 8 && $ttl <= 10}
    }
    """
    r.run("del", "x")
    r.run("setex", "x", 10, "somevalue")
    ttl = r.run("ttl", "x")
    assert (ttl > 8) and (ttl <= 10)


def test_pttl_returns_time_to_live_in_milliseconds(r: ValkeyTestClient) -> None:
    """
    test {PTTL returns time to live in milliseconds} {
        r del x
        r setex x 1 somevalue
        set ttl [r pttl x]
        assert {$ttl > 500 && $ttl <= 1000}
    }
    """
    r.run("del", "x")
    r.run("setex", "x", 1, "somevalue")
    ttl = r.run("pttl", "x")
    assert (ttl > 500) and (ttl <= 1000)


def test_ttl_or_pttl_or_expiretime_or_pexpiretime_return_1_if_key_has_no_expire(r: ValkeyTestClient) -> None:
    """
    test {TTL / PTTL / EXPIRETIME / PEXPIRETIME return -1 if key has no expire} {
        r del x
        r set x hello
        list [r ttl x] [r pttl x] [r expiretime x] [r pexpiretime x]
    } {-1 -1 -1 -1}
    """
    r.run("del", "x")
    r.run("set", "x", "hello")
    assert [r.run("ttl", "x"), r.run("pttl", "x"), r.run("expiretime", "x"), r.run("pexpiretime", "x")] == "-1 -1 -1 -1"


def test_ttl_or_pttl_or_expiretime_or_pexpiretime_return_2_if_key_does_not_exit(r: ValkeyTestClient) -> None:
    """
    test {TTL / PTTL / EXPIRETIME / PEXPIRETIME return -2 if key does not exit} {
        r del x
        list [r ttl x] [r pttl x] [r expiretime x] [r pexpiretime x]
    } {-2 -2 -2 -2}
    """
    r.run("del", "x")
    assert [r.run("ttl", "x"), r.run("pttl", "x"), r.run("expiretime", "x"), r.run("pexpiretime", "x")] == "-2 -2 -2 -2"


def test_expiretime_returns_absolute_expiration_time_in_seconds(r: ValkeyTestClient) -> None:
    """
    test {EXPIRETIME returns absolute expiration time in seconds} {
        r del x
        set abs_expire [expr [clock seconds] + 100]
        r set x somevalue exat $abs_expire
        assert_equal [r expiretime x] $abs_expire
    }
    """
    r.run("del", "x")
    abs_expire = expr(clock("seconds"), "+", 100)
    r.run("set", "x", "somevalue", "exat", abs_expire)
    assert r.run("expiretime", "x") == abs_expire


def test_pexpiretime_returns_absolute_expiration_time_in_milliseconds(r: ValkeyTestClient) -> None:
    """
    test {PEXPIRETIME returns absolute expiration time in milliseconds} {
        r del x
        set abs_expire [expr [clock milliseconds] + 100000]
        r set x somevalue pxat $abs_expire
        assert_equal [r pexpiretime x] $abs_expire
    }
    """
    r.run("del", "x")
    abs_expire = expr(clock("milliseconds"), "+", 100000)
    r.run("set", "x", "somevalue", "pxat", abs_expire)
    assert r.run("pexpiretime", "x") == abs_expire


def test_server_should_actively_expire_keys_incrementally(r: ValkeyTestClient) -> None:
    """
    test {Server should actively expire keys incrementally} {
        r flushdb
        r psetex key1 500 a
        r psetex key2 500 a
        r psetex key3 500 a
        assert_equal 3 [r dbsize]
        # The server expires random keys ten times every second so we are
        # fairly sure that all the three keys should be evicted after
        # two seconds.
        wait_for_condition 20 100 {
            [r dbsize] eq 0
        } else {
            fail "Keys did not actively expire."
        }
    }
    """
    r.run("flushdb")
    r.run("psetex", "key1", 500, "a")
    r.run("psetex", "key2", 500, "a")
    r.run("psetex", "key3", 500, "a")
    assert 3 == r.run("dbsize")
    wait_for_condition(20, 100, lambda: r.run("dbsize") == 0, lambda: fail("Keys did not actively expire."))


def test_server_should_lazy_expire_keys(r: ValkeyTestClient) -> None:
    """
    test {Server should lazy expire keys} {
        r flushdb
        r debug set-active-expire 0
        r psetex key1{t} 500 a
        r psetex key2{t} 500 a
        r psetex key3{t} 500 a
        set size1 [r dbsize]
        # The server expires random keys ten times every second so we are
        # fairly sure that all the three keys should be evicted after
        # one second.
        after 1000
        set size2 [r dbsize]
        r mget key1{t} key2{t} key3{t}
        set size3 [r dbsize]
        r debug set-active-expire 1
        list $size1 $size2 $size3
    } {3 3 0} {needs:debug}
    """
    r.run("flushdb")
    r.run("debug", "set-active-expire", 0)
    r.run("psetex", "key1{t}", 500, "a")
    r.run("psetex", "key2{t}", 500, "a")
    r.run("psetex", "key3{t}", 500, "a")
    size1 = r.run("dbsize")
    time.sleep(1000 / 1000)
    size2 = r.run("dbsize")
    r.run("mget", "key1{t}", "key2{t}", "key3{t}")
    size3 = r.run("dbsize")
    r.run("debug", "set-active-expire", 1)
    assert [size1, size2, size3] == "3 3 0"


def test_expire_should_not_resurrect_keys_issue_1026(r: ValkeyTestClient) -> None:
    """
    test {EXPIRE should not resurrect keys (issue #1026)} {
        r debug set-active-expire 0
        r set foo bar
        r pexpire foo 500
        after 1000
        r expire foo 10
        r debug set-active-expire 1
        r exists foo
    } {0} {needs:debug}
    """
    r.run("debug", "set-active-expire", 0)
    r.run("set", "foo", "bar")
    r.run("pexpire", "foo", 500)
    time.sleep(1000 / 1000)
    r.run("expire", "foo", 10)
    r.run("debug", "set-active-expire", 1)
    assert r.run("exists", "foo") == "0"


def test_5_keys_in_5_keys_out(r: ValkeyTestClient) -> None:
    """
    test {5 keys in, 5 keys out} {
        r flushdb
        r set a c
        r expire a 5
        r set t c
        r set e c
        r set s c
        r set foo b
        assert_equal [lsort [r keys *]] {a e foo s t}
        r del a ; # Do not leak volatile keys to other tests
    }
    """
    r.run("flushdb")
    r.run("set", "a", "c")
    r.run("expire", "a", 5)
    r.run("set", "t", "c")
    r.run("set", "e", "c")
    r.run("set", "s", "c")
    r.run("set", "foo", "b")
    assert sorted(r.run("keys", "*")) == "a e foo s t"
    r.run("del", "a")


def test_expire_with_empty_string_as_ttl_should_report_an_error(r: ValkeyTestClient) -> None:
    """
    test {EXPIRE with empty string as TTL should report an error} {
        r set foo bar
        catch {r expire foo ""} e
        set e
    } {*not an integer*}
    """
    r.run("set", "foo", "bar")
    try:
        e = r.run("expire", "foo", "")
    except Exception as _catch_err:
        e = str(_catch_err)
    assert fnmatch(str(e), "*not an integer*")


def test_set_with_ex_with_big_integer_should_report_an_error(r: ValkeyTestClient) -> None:
    """
    test {SET with EX with big integer should report an error} {
        catch {r set foo bar EX 10000000000000000} e
        set e
    } {ERR invalid expire time in 'set' command}
    """
    try:
        e = r.run("set", "foo", "bar", "EX", 10000000000000000)
    except Exception as _catch_err:
        e = str(_catch_err)
    assert e == "ERR invalid expire time in 'set' command"


def test_set_with_ex_with_smallest_integer_should_report_an_error(r: ValkeyTestClient) -> None:
    """
    test {SET with EX with smallest integer should report an error} {
        catch {r SET foo bar EX -9999999999999999} e
        set e
    } {ERR invalid expire time in 'set' command}
    """
    try:
        e = r.run("SET", "foo", "bar", "EX", -9999999999999999)
    except Exception as _catch_err:
        e = str(_catch_err)
    assert e == "ERR invalid expire time in 'set' command"


def test_getex_with_big_integer_should_report_an_error(r: ValkeyTestClient) -> None:
    """
    test {GETEX with big integer should report an error} {
        r set foo bar
        catch {r GETEX foo EX 10000000000000000} e
        set e
    } {ERR invalid expire time in 'getex' command}
    """
    r.run("set", "foo", "bar")
    try:
        e = r.run("GETEX", "foo", "EX", 10000000000000000)
    except Exception as _catch_err:
        e = str(_catch_err)
    assert e == "ERR invalid expire time in 'getex' command"


def test_getex_with_smallest_integer_should_report_an_error(r: ValkeyTestClient) -> None:
    """
    test {GETEX with smallest integer should report an error} {
        r set foo bar
        catch {r GETEX foo EX -9999999999999999} e
        set e
    } {ERR invalid expire time in 'getex' command}
    """
    r.run("set", "foo", "bar")
    try:
        e = r.run("GETEX", "foo", "EX", -9999999999999999)
    except Exception as _catch_err:
        e = str(_catch_err)
    assert e == "ERR invalid expire time in 'getex' command"


def test_getex_with_error_expiration_time(r: ValkeyTestClient) -> None:
    """
    test {GETEX with error expiration time} {
        r del foo
        assert_error {ERR value is not an integer or out of range} {r getex foo ex abcd}
        r set foo bar
        assert_error {ERR value is not an integer or out of range} {r getex foo px -abcd}
        r del foo
        r hset foo f v
        assert_error {ERR value is not an integer or out of range} {r getex foo exat -abcd}
        r del foo
    }
    """
    r.run("del", "foo")
    with pytest.raises(Exception, match="ERR\\ value\\ is\\ not\\ an\\ integer\\ or\\ out\\ of\\ range"):
        r.run("getex", "foo", "ex", "abcd")
    r.run("set", "foo", "bar")
    with pytest.raises(Exception, match="ERR\\ value\\ is\\ not\\ an\\ integer\\ or\\ out\\ of\\ range"):
        r.run("getex", "foo", "px", "-abcd")
    r.run("del", "foo")
    r.run("hset", "foo", "f", "v")
    with pytest.raises(Exception, match="ERR\\ value\\ is\\ not\\ an\\ integer\\ or\\ out\\ of\\ range"):
        r.run("getex", "foo", "exat", "-abcd")
    r.run("del", "foo")


def test_expire_with_big_integer_overflows_when_converted_to_milliseconds(r: ValkeyTestClient) -> None:
    """
    test {EXPIRE with big integer overflows when converted to milliseconds} {
        r set foo bar

        # Hit `when > LLONG_MAX - basetime`
        assert_error "ERR invalid expire time in 'expire' command" {r EXPIRE foo 9223370399119966}

        # Hit `when > LLONG_MAX / 1000`
        assert_error "ERR invalid expire time in 'expire' command" {r EXPIRE foo 9223372036854776}
        assert_error "ERR invalid expire time in 'expire' command" {r EXPIRE foo 10000000000000000}
        assert_error "ERR invalid expire time in 'expire' command" {r EXPIRE foo 18446744073709561}

        assert_equal {-1} [r ttl foo]
    }
    """
    r.run("set", "foo", "bar")
    with pytest.raises(Exception, match="ERR\\ invalid\\ expire\\ time\\ in\\ 'expire'\\ command"):
        r.run("EXPIRE", "foo", 9223370399119966)
    with pytest.raises(Exception, match="ERR\\ invalid\\ expire\\ time\\ in\\ 'expire'\\ command"):
        r.run("EXPIRE", "foo", 9223372036854776)
    with pytest.raises(Exception, match="ERR\\ invalid\\ expire\\ time\\ in\\ 'expire'\\ command"):
        r.run("EXPIRE", "foo", 10000000000000000)
    with pytest.raises(Exception, match="ERR\\ invalid\\ expire\\ time\\ in\\ 'expire'\\ command"):
        r.run("EXPIRE", "foo", 18446744073709561)
    assert "-1" == r.run("ttl", "foo")


def test_pexpire_with_big_integer_overflow_when_basetime_is_added(r: ValkeyTestClient) -> None:
    """
    test {PEXPIRE with big integer overflow when basetime is added} {
        r set foo bar
        catch {r PEXPIRE foo 9223372036854770000} e
        set e
    } {ERR invalid expire time in 'pexpire' command}
    """
    r.run("set", "foo", "bar")
    try:
        e = r.run("PEXPIRE", "foo", 9223372036854770000)
    except Exception as _catch_err:
        e = str(_catch_err)
    assert e == "ERR invalid expire time in 'pexpire' command"


def test_expire_with_big_negative_integer(r: ValkeyTestClient) -> None:
    """
    test {EXPIRE with big negative integer} {
        r set foo bar

        # Hit `when < LLONG_MIN / 1000`
        assert_error "ERR invalid expire time in 'expire' command" {r EXPIRE foo -9223372036854776}
        assert_error "ERR invalid expire time in 'expire' command" {r EXPIRE foo -9999999999999999}

        r ttl foo
    } {-1}
    """
    r.run("set", "foo", "bar")
    with pytest.raises(Exception, match="ERR\\ invalid\\ expire\\ time\\ in\\ 'expire'\\ command"):
        r.run("EXPIRE", "foo", -9223372036854776)
    with pytest.raises(Exception, match="ERR\\ invalid\\ expire\\ time\\ in\\ 'expire'\\ command"):
        r.run("EXPIRE", "foo", -9999999999999999)
    assert r.run("ttl", "foo") == "-1"


def test_pexpireat_with_big_integer_works(r: ValkeyTestClient) -> None:
    """
    test {PEXPIREAT with big integer works} {
        r set foo bar
        r PEXPIREAT foo 9223372036854770000
    } {1}
    """
    r.run("set", "foo", "bar")
    assert r.run("PEXPIREAT", "foo", 9223372036854770000) == "1"


def test_pexpireat_with_big_negative_integer_works(r: ValkeyTestClient) -> None:
    """
    test {PEXPIREAT with big negative integer works} {
        r set foo bar
        r PEXPIREAT foo -9223372036854770000
        r ttl foo
    } {-2}
    """
    r.run("set", "foo", "bar")
    r.run("PEXPIREAT", "foo", -9223372036854770000)
    assert r.run("ttl", "foo") == "-2"


"""
start_server {overrides {appendonly {yes} appendfsync always} tags {external:skip}} {
    test {All time-to-live(TTL) in commands are propagated as absolute timestamp in milliseconds in AOF} {
        # This test makes sure that expire times are propagated as absolute
        # times to the AOF file and not as relative time, so that when the AOF
        # is reloaded the TTLs are not being shifted forward to the future.
        # We want the time to logically pass when the server is restarted!

        set aof [get_last_incr_aof_path r]

        # Apply each TTL-related command to a unique key
        # SET commands
        r set foo1 bar ex 100
        r set foo2 bar px 100000
        r set foo3 bar exat [expr [clock seconds]+100]
        r set foo4 bar PXAT [expr [clock milliseconds]+100000]
        r setex foo5 100 bar
        r psetex foo6 100000 bar
        # EXPIRE-family commands
        r set foo7 bar
        r expire foo7 100
        r set foo8 bar
        r pexpire foo8 100000
        r set foo9 bar
        r expireat foo9 [expr [clock seconds]+100]
        r set foo10 bar
        r pexpireat foo10 [expr [clock seconds]*1000+100000]
        r set foo11 bar
        r expireat foo11 [expr [clock seconds]-100]
        # GETEX commands
        r set foo12 bar
        r getex foo12 ex 100
        r set foo13 bar
        r getex foo13 px 100000
        r set foo14 bar
        r getex foo14 exat [expr [clock seconds]+100]
        r set foo15 bar
        r getex foo15 pxat [expr [clock milliseconds]+100000]
        # RESTORE commands
        r set foo16 bar
        set encoded [r dump foo16]
        r restore foo17 100000 $encoded
        r restore foo18 [expr [clock milliseconds]+100000] $encoded absttl

        # Assert that each TTL-related command are persisted with absolute timestamps in AOF
        assert_aof_content $aof {
            {select *}
            {set foo1 bar PXAT *}
            {set foo2 bar PXAT *}
            {set foo3 bar PXAT *}
            {set foo4 bar PXAT *}
            {set foo5 bar PXAT *}
            {set foo6 bar PXAT *}
            {set foo7 bar}
            {pexpireat foo7 *}
            {set foo8 bar}
            {pexpireat foo8 *}
            {set foo9 bar}
            {pexpireat foo9 *}
            {set foo10 bar}
            {pexpireat foo10 *}
            {set foo11 bar}
            {unlink foo11}
            {set foo12 bar}
            {pexpireat foo12 *}
            {set foo13 bar}
            {pexpireat foo13 *}
            {set foo14 bar}
            {pexpireat foo14 *}
            {set foo15 bar}
            {pexpireat foo15 *}
            {set foo16 bar}
            {restore foo17 * * ABSTTL}
            {restore foo18 * * absttl}
        }

        # Remember the absolute TTLs of all the keys
        set ttl1 [r pexpiretime foo1]
        set ttl2 [r pexpiretime foo2]
        set ttl3 [r pexpiretime foo3]
        set ttl4 [r pexpiretime foo4]
        set ttl5 [r pexpiretime foo5]
        set ttl6 [r pexpiretime foo6]
        set ttl7 [r pexpiretime foo7]
        set ttl8 [r pexpiretime foo8]
        set ttl9 [r pexpiretime foo9]
        set ttl10 [r pexpiretime foo10]
        assert_equal "-2" [r pexpiretime foo11] ; # foo11 is gone
        set ttl12 [r pexpiretime foo12]
        set ttl13 [r pexpiretime foo13]
        set ttl14 [r pexpiretime foo14]
        set ttl15 [r pexpiretime foo15]
        assert_equal "-1" [r pexpiretime foo16] ; # foo16 has no TTL
        set ttl17 [r pexpiretime foo17]
        set ttl18 [r pexpiretime foo18]

        # Let some time pass and reload data from AOF
        after 2000
        r debug loadaof

        # Assert that relative TTLs are roughly the same
        assert_range [r ttl foo1] 90 98
        assert_range [r ttl foo2] 90 98
        assert_range [r ttl foo3] 90 98
        assert_range [r ttl foo4] 90 98
        assert_range [r ttl foo5] 90 98
        assert_range [r ttl foo6] 90 98
        assert_range [r ttl foo7] 90 98
        assert_range [r ttl foo8] 90 98
        assert_range [r ttl foo9] 90 98
        assert_range [r ttl foo10] 90 98
        assert_equal [r ttl foo11] "-2" ; # foo11 is gone
        assert_range [r ttl foo12] 90 98
        assert_range [r ttl foo13] 90 98
        assert_range [r ttl foo14] 90 98
        assert_range [r ttl foo15] 90 98
        assert_equal [r ttl foo16] "-1" ; # foo16 has no TTL
        assert_range [r ttl foo17] 90 98
        assert_range [r ttl foo18] 90 98

        # Assert that all keys have restored the same absolute TTLs from AOF
        assert_equal [r pexpiretime foo1] $ttl1
        assert_equal [r pexpiretime foo2] $ttl2
        assert_equal [r pexpiretime foo3] $ttl3
        assert_equal [r pexpiretime foo4] $ttl4
        assert_equal [r pexpiretime foo5] $ttl5
        assert_equal [r pexpiretime foo6] $ttl6
        assert_equal [r pexpiretime foo7] $ttl7
        assert_equal [r pexpiretime foo8] $ttl8
        assert_equal [r pexpiretime foo9] $ttl9
        assert_equal [r pexpiretime foo10] $ttl10
        assert_equal [r pexpiretime foo11] "-2" ; # foo11 is gone
        assert_equal [r pexpiretime foo12] $ttl12
        assert_equal [r pexpiretime foo13] $ttl13
        assert_equal [r pexpiretime foo14] $ttl14
        assert_equal [r pexpiretime foo15] $ttl15
        assert_equal [r pexpiretime foo16] "-1" ; # foo16 has no TTL
        assert_equal [r pexpiretime foo17] $ttl17
        assert_equal [r pexpiretime foo18] $ttl18
    } {} {needs:debug}
}
"""


def test_all_ttl_in_commands_are_propagated_as_absolute_timestamp_in_replication_stream(r: ValkeyTestClient) -> None:
    """
    test {All TTL in commands are propagated as absolute timestamp in replication stream} {
        # Make sure that both relative and absolute expire commands are propagated
        # as absolute to replicas for two reasons:
        # 1) We want to avoid replicas retaining data much longer than primary due
        #    to replication lag.
        # 2) We want to unify the way TTLs are replicated in both RDB and replication
        #    stream, which is as absolute timestamps.
        # See Redis OSS issue: https://github.com/redis/redis/issues/8433

        r flushall ; # Clean up keyspace to avoid interference by keys from other tests
        set repl [attach_to_replication_stream]
        # SET commands
        r set foo1 bar ex 200
        r set foo1 bar px 100000
        r set foo1 bar exat [expr [clock seconds]+100]
        r set foo1 bar pxat [expr [clock milliseconds]+100000]
        r setex foo1 100 bar
        r psetex foo1 100000 bar
        r set foo2 bar
        # EXPIRE-family commands
        r expire foo2 100
        r pexpire foo2 100000
        r set foo3 bar
        r expireat foo3 [expr [clock seconds]+100]
        r pexpireat foo3 [expr [clock seconds]*1000+100000]
        r expireat foo3 [expr [clock seconds]-100]
        # GETEX-family commands
        r set foo4 bar
        r getex foo4 ex 200
        r getex foo4 px 200000
        r getex foo4 exat [expr [clock seconds]+100]
        r getex foo4 pxat [expr [clock milliseconds]+100000]
        # RESTORE commands
        r set foo5 bar
        set encoded [r dump foo5]
        r restore foo6 100000 $encoded
        r restore foo7 [expr [clock milliseconds]+100000] $encoded absttl

        assert_replication_stream $repl {
            {select *}
            {set foo1 bar PXAT *}
            {set foo1 bar PXAT *}
            {set foo1 bar PXAT *}
            {set foo1 bar pxat *}
            {set foo1 bar PXAT *}
            {set foo1 bar PXAT *}
            {set foo2 bar}
            {pexpireat foo2 *}
            {pexpireat foo2 *}
            {set foo3 bar}
            {pexpireat foo3 *}
            {pexpireat foo3 *}
            {unlink foo3}
            {set foo4 bar}
            {pexpireat foo4 *}
            {pexpireat foo4 *}
            {pexpireat foo4 *}
            {pexpireat foo4 *}
            {set foo5 bar}
            {restore foo6 * * ABSTTL}
            {restore foo7 * * absttl}
        }
        close_replication_stream $repl
    } {} {needs:repl}
    """
    r.run("flushall")
    repl = attach_to_replication_stream()
    r.run("set", "foo1", "bar", "ex", 200)
    r.run("set", "foo1", "bar", "px", 100000)
    r.run("set", "foo1", "bar", "exat", expr(clock("seconds"), 100))
    r.run("set", "foo1", "bar", "pxat", expr(clock("milliseconds"), 100000))
    r.run("setex", "foo1", 100, "bar")
    r.run("psetex", "foo1", 100000, "bar")
    r.run("set", "foo2", "bar")
    r.run("expire", "foo2", 100)
    r.run("pexpire", "foo2", 100000)
    r.run("set", "foo3", "bar")
    r.run("expireat", "foo3", expr(clock("seconds"), 100))
    r.run("pexpireat", "foo3", expr(clock("seconds"), "*1000+100000"))
    r.run("expireat", "foo3", expr(clock("seconds"), -100))
    r.run("set", "foo4", "bar")
    r.run("getex", "foo4", "ex", 200)
    r.run("getex", "foo4", "px", 200000)
    r.run("getex", "foo4", "exat", expr(clock("seconds"), 100))
    r.run("getex", "foo4", "pxat", expr(clock("milliseconds"), 100000))
    r.run("set", "foo5", "bar")
    encoded = r.run("dump", "foo5")
    r.run("restore", "foo6", 100000, encoded)
    r.run("restore", "foo7", expr(clock("milliseconds"), 100000), encoded, "absttl")
    assert_replication_stream(
        repl,
        "            {select *}\n            {set foo1 bar PXAT *}\n            {set foo1 bar PXAT *}\n            {set foo1 bar PXAT *}\n            {set foo1 bar pxat *}\n            {set foo1 bar PXAT *}\n            {set foo1 bar PXAT *}\n            {set foo2 bar}\n            {pexpireat foo2 *}\n            {pexpireat foo2 *}\n            {set foo3 bar}\n            {pexpireat foo3 *}\n            {pexpireat foo3 *}\n            {unlink foo3}\n            {set foo4 bar}\n            {pexpireat foo4 *}\n            {pexpireat foo4 *}\n            {pexpireat foo4 *}\n            {pexpireat foo4 *}\n            {set foo5 bar}\n            {restore foo6 * * ABSTTL}\n            {restore foo7 * * absttl}\n        ",
    )
    close_replication_stream(repl)


"""
start_server {tags {needs:repl external:skip}} {
    # Set the outer layer server as primary
    set primary [srv -1 client]
    set primary_host [srv -1 host]
    set primary_port [srv -1 port]
    # Set this inner layer server as replica
    set replica [srv 0 client]

    test {First server should have role slave after REPLICAOF} {
        $replica replicaof $primary_host $primary_port
        wait_for_condition 50 100 {
            [s 0 role] eq {slave}
        } else {
            fail "Replication not started."
        }
    }

    test {For all replicated TTL-related commands, absolute expire times are identical on primary and replica} {
        # Apply each TTL-related command to a unique key on primary
        # SET commands
        $primary set foo1 bar ex 100
        $primary set foo2 bar px 100000
        $primary set foo3 bar exat [expr [clock seconds]+100]
        $primary set foo4 bar pxat [expr [clock milliseconds]+100000]
        $primary setex foo5 100 bar
        $primary psetex foo6 100000 bar
        # EXPIRE-family commands
        $primary set foo7 bar
        $primary expire foo7 100
        $primary set foo8 bar
        $primary pexpire foo8 100000
        $primary set foo9 bar
        $primary expireat foo9 [expr [clock seconds]+100]
        $primary set foo10 bar
        $primary pexpireat foo10 [expr [clock milliseconds]+100000]
        # GETEX commands
        $primary set foo11 bar
        $primary getex foo11 ex 100
        $primary set foo12 bar
        $primary getex foo12 px 100000
        $primary set foo13 bar
        $primary getex foo13 exat [expr [clock seconds]+100]
        $primary set foo14 bar
        $primary getex foo14 pxat [expr [clock milliseconds]+100000]
        # RESTORE commands
        $primary set foo15 bar
        set encoded [$primary dump foo15]
        $primary restore foo16 100000 $encoded
        $primary restore foo17 [expr [clock milliseconds]+100000] $encoded absttl

        # Wait for replica to get the keys and TTLs
        assert {[$primary wait 1 0] == 1}

        # Verify absolute TTLs are identical on primary and replica for all keys
        # This is because TTLs are always replicated as absolute values
        foreach key [$primary keys *] {
            assert_equal [$primary pexpiretime $key] [$replica pexpiretime $key]
        }
    }

    test {expired key which is created in writeable replicas should be deleted by active expiry} {
        $primary flushall
        $replica config set replica-read-only no
        foreach {yes_or_no} {yes no} {
            $replica config set appendonly $yes_or_no
            waitForBgrewriteaof $replica
            set prev_expired [s expired_keys]
            $replica set foo bar PX 1
            wait_for_condition 100 10 {
                [s expired_keys] eq $prev_expired + 1
            } else {
                fail "key not expired"
            }
            assert_equal {} [$replica get foo]
        }
    }
}
"""


def test_set_command_will_remove_expire(r: ValkeyTestClient) -> None:
    """
    test {SET command will remove expire} {
        r set foo bar EX 100
        r set foo bar
        r ttl foo
    } {-1}
    """
    r.run("set", "foo", "bar", "EX", 100)
    r.run("set", "foo", "bar")
    assert r.run("ttl", "foo") == "-1"


def test_set_use_keepttl_option_ttl_should_not_be_removed(r: ValkeyTestClient) -> None:
    """
    test {SET - use KEEPTTL option, TTL should not be removed} {
        r set foo bar EX 100
        r set foo bar KEEPTTL
        set ttl [r ttl foo]
        assert {$ttl <= 100 && $ttl > 90}
    }
    """
    r.run("set", "foo", "bar", "EX", 100)
    r.run("set", "foo", "bar", "KEEPTTL")
    ttl = r.run("ttl", "foo")
    assert (ttl <= 100) and (ttl > 90)


def test_set_use_keepttl_option_ttl_should_not_be_removed_after_loadaof(r: ValkeyTestClient) -> None:
    """
    test {SET - use KEEPTTL option, TTL should not be removed after loadaof} {
        r config set appendonly yes
        r set foo bar EX 100
        r set foo bar2 KEEPTTL
        after 2000
        r debug loadaof
        set ttl [r ttl foo]
        assert {$ttl <= 98 && $ttl > 90}
    } {} {needs:debug}
    """
    r.run("config", "set", "appendonly", "yes")
    r.run("set", "foo", "bar", "EX", 100)
    r.run("set", "foo", "bar2", "KEEPTTL")
    time.sleep(2000 / 1000)
    r.run("debug", "loadaof")
    ttl = r.run("ttl", "foo")
    assert (ttl <= 98) and (ttl > 90)


def test_getex_use_of_persist_option_should_remove_ttl(r: ValkeyTestClient) -> None:
    """
    test {GETEX use of PERSIST option should remove TTL} {
        r set foo bar EX 100
        r getex foo PERSIST
        r ttl foo
    } {-1}
    """
    r.run("set", "foo", "bar", "EX", 100)
    r.run("getex", "foo", "PERSIST")
    assert r.run("ttl", "foo") == "-1"


def test_getex_use_of_persist_option_should_remove_ttl_after_loadaof(r: ValkeyTestClient) -> None:
    """
    test {GETEX use of PERSIST option should remove TTL after loadaof} {
        r config set appendonly yes
        r set foo bar EX 100
        r getex foo PERSIST
        r debug loadaof
        r ttl foo
    } {-1} {needs:debug}
    """
    r.run("config", "set", "appendonly", "yes")
    r.run("set", "foo", "bar", "EX", 100)
    r.run("getex", "foo", "PERSIST")
    r.run("debug", "loadaof")
    assert r.run("ttl", "foo") == "-1"


def test_getex_propagate_as_to_replica_as_persist_unlink_or_nothing(r: ValkeyTestClient) -> None:
    """
    test {GETEX propagate as to replica as PERSIST, UNLINK, or nothing} {
        # In the above tests, many keys with random expiration times are set, flush
         # the DBs to avoid active expiry kicking in and messing the replication streams.
         r flushall
        set repl [attach_to_replication_stream]
        r set foo bar EX 100
        r getex foo PERSIST
        r getex foo
        r getex foo exat [expr [clock seconds]-100]
        assert_replication_stream $repl {
            {select *}
            {set foo bar PXAT *}
            {persist foo}
            {unlink foo}
         }
         close_replication_stream $repl
    } {} {needs:repl}
    """
    r.run("flushall")
    repl = attach_to_replication_stream()
    r.run("set", "foo", "bar", "EX", 100)
    r.run("getex", "foo", "PERSIST")
    r.run("getex", "foo")
    r.run("getex", "foo", "exat", expr(clock("seconds"), -100))
    assert_replication_stream(
        repl,
        "           {select *}\n           {set foo bar PXAT *}\n           {persist foo}\n           {unlink foo}\n        ",
    )
    close_replication_stream(repl)


def test_expire_with_nx_option_on_a_key_with_ttl(r: ValkeyTestClient) -> None:
    """
    test {EXPIRE with NX option on a key with ttl} {
        r SET foo bar EX 100
        assert_equal [r EXPIRE foo 200 NX] 0
        assert_range [r TTL foo] 50 100
    } {}
    """
    r.run("SET", "foo", "bar", "EX", 100)
    assert r.run("EXPIRE", "foo", 200, "NX") == 0
    assert_range(r.run("TTL", "foo"), 50, 100)


def test_expire_with_nx_option_on_a_key_without_ttl(r: ValkeyTestClient) -> None:
    """
    test {EXPIRE with NX option on a key without ttl} {
        r SET foo bar
        assert_equal [r EXPIRE foo 200 NX] 1
        assert_range [r TTL foo] 100 200
    } {}
    """
    r.run("SET", "foo", "bar")
    assert r.run("EXPIRE", "foo", 200, "NX") == 1
    assert_range(r.run("TTL", "foo"), 100, 200)


def test_expire_with_xx_option_on_a_key_with_ttl(r: ValkeyTestClient) -> None:
    """
    test {EXPIRE with XX option on a key with ttl} {
        r SET foo bar EX 100
        assert_equal [r EXPIRE foo 200 XX] 1
        assert_range [r TTL foo] 100 200
    } {}
    """
    r.run("SET", "foo", "bar", "EX", 100)
    assert r.run("EXPIRE", "foo", 200, "XX") == 1
    assert_range(r.run("TTL", "foo"), 100, 200)


def test_expire_with_xx_option_on_a_key_without_ttl(r: ValkeyTestClient) -> None:
    """
    test {EXPIRE with XX option on a key without ttl} {
        r SET foo bar
        assert_equal [r EXPIRE foo 200 XX] 0
        assert_equal [r TTL foo] -1
    } {}
    """
    r.run("SET", "foo", "bar")
    assert r.run("EXPIRE", "foo", 200, "XX") == 0
    assert r.run("TTL", "foo") == -1


def test_expire_with_gt_option_on_a_key_with_lower_ttl(r: ValkeyTestClient) -> None:
    """
    test {EXPIRE with GT option on a key with lower ttl} {
        r SET foo bar EX 100
        assert_equal [r EXPIRE foo 200 GT] 1
        assert_range [r TTL foo] 100 200
    } {}
    """
    r.run("SET", "foo", "bar", "EX", 100)
    assert r.run("EXPIRE", "foo", 200, "GT") == 1
    assert_range(r.run("TTL", "foo"), 100, 200)


def test_expire_with_gt_option_on_a_key_with_higher_ttl(r: ValkeyTestClient) -> None:
    """
    test {EXPIRE with GT option on a key with higher ttl} {
        r SET foo bar EX 200
        assert_equal [r EXPIRE foo 100 GT] 0
        assert_range [r TTL foo] 100 200
    } {}
    """
    r.run("SET", "foo", "bar", "EX", 200)
    assert r.run("EXPIRE", "foo", 100, "GT") == 0
    assert_range(r.run("TTL", "foo"), 100, 200)


def test_expire_with_gt_option_on_a_key_without_ttl(r: ValkeyTestClient) -> None:
    """
    test {EXPIRE with GT option on a key without ttl} {
        r SET foo bar
        assert_equal [r EXPIRE foo 200 GT] 0
        assert_equal [r TTL foo] -1
    } {}
    """
    r.run("SET", "foo", "bar")
    assert r.run("EXPIRE", "foo", 200, "GT") == 0
    assert r.run("TTL", "foo") == -1


def test_expire_with_lt_option_on_a_key_with_higher_ttl(r: ValkeyTestClient) -> None:
    """
    test {EXPIRE with LT option on a key with higher ttl} {
        r SET foo bar EX 100
        assert_equal [r EXPIRE foo 200 LT] 0
        assert_range [r TTL foo] 50 100
    } {}
    """
    r.run("SET", "foo", "bar", "EX", 100)
    assert r.run("EXPIRE", "foo", 200, "LT") == 0
    assert_range(r.run("TTL", "foo"), 50, 100)


def test_expire_with_lt_option_on_a_key_with_lower_ttl(r: ValkeyTestClient) -> None:
    """
    test {EXPIRE with LT option on a key with lower ttl} {
        r SET foo bar EX 200
        assert_equal [r EXPIRE foo 100 LT] 1
        assert_range [r TTL foo] 50 100
    } {}
    """
    r.run("SET", "foo", "bar", "EX", 200)
    assert r.run("EXPIRE", "foo", 100, "LT") == 1
    assert_range(r.run("TTL", "foo"), 50, 100)


def test_expire_with_lt_option_on_a_key_without_ttl(r: ValkeyTestClient) -> None:
    """
    test {EXPIRE with LT option on a key without ttl} {
        r SET foo bar
        assert_equal [r EXPIRE foo 100 LT] 1
        assert_range [r TTL foo] 50 100
    } {}
    """
    r.run("SET", "foo", "bar")
    assert r.run("EXPIRE", "foo", 100, "LT") == 1
    assert_range(r.run("TTL", "foo"), 50, 100)


def test_expire_with_lt_and_xx_option_on_a_key_with_ttl(r: ValkeyTestClient) -> None:
    """
    test {EXPIRE with LT and XX option on a key with ttl} {
        r SET foo bar EX 200
        assert_equal [r EXPIRE foo 100 LT XX] 1
        assert_range [r TTL foo] 50 100
    } {}
    """
    r.run("SET", "foo", "bar", "EX", 200)
    assert r.run("EXPIRE", "foo", 100, "LT", "XX") == 1
    assert_range(r.run("TTL", "foo"), 50, 100)


def test_expire_with_lt_and_xx_option_on_a_key_without_ttl(r: ValkeyTestClient) -> None:
    """
    test {EXPIRE with LT and XX option on a key without ttl} {
        r SET foo bar
        assert_equal [r EXPIRE foo 200 LT XX] 0
        assert_equal [r TTL foo] -1
    } {}
    """
    r.run("SET", "foo", "bar")
    assert r.run("EXPIRE", "foo", 200, "LT", "XX") == 0
    assert r.run("TTL", "foo") == -1


def test_expire_with_conflicting_options_lt_gt(r: ValkeyTestClient) -> None:
    """
    test {EXPIRE with conflicting options: LT GT} {
        catch {r EXPIRE foo 200 LT GT} e
        set e
    } {ERR GT and LT options at the same time are not compatible}
    """
    try:
        e = r.run("EXPIRE", "foo", 200, "LT", "GT")
    except Exception as _catch_err:
        e = str(_catch_err)
    assert e == "ERR GT and LT options at the same time are not compatible"


def test_expire_with_conflicting_options_nx_gt(r: ValkeyTestClient) -> None:
    """
    test {EXPIRE with conflicting options: NX GT} {
        catch {r EXPIRE foo 200 NX GT} e
        set e
    } {ERR NX and XX, GT or LT options at the same time are not compatible}
    """
    try:
        e = r.run("EXPIRE", "foo", 200, "NX", "GT")
    except Exception as _catch_err:
        e = str(_catch_err)
    assert e == "ERR NX and XX, GT or LT options at the same time are not compatible"


def test_expire_with_conflicting_options_nx_lt(r: ValkeyTestClient) -> None:
    """
    test {EXPIRE with conflicting options: NX LT} {
        catch {r EXPIRE foo 200 NX LT} e
        set e
    } {ERR NX and XX, GT or LT options at the same time are not compatible}
    """
    try:
        e = r.run("EXPIRE", "foo", 200, "NX", "LT")
    except Exception as _catch_err:
        e = str(_catch_err)
    assert e == "ERR NX and XX, GT or LT options at the same time are not compatible"


def test_expire_with_conflicting_options_nx_xx(r: ValkeyTestClient) -> None:
    """
    test {EXPIRE with conflicting options: NX XX} {
        catch {r EXPIRE foo 200 NX XX} e
        set e
    } {ERR NX and XX, GT or LT options at the same time are not compatible}
    """
    try:
        e = r.run("EXPIRE", "foo", 200, "NX", "XX")
    except Exception as _catch_err:
        e = str(_catch_err)
    assert e == "ERR NX and XX, GT or LT options at the same time are not compatible"


def test_expire_with_unsupported_options(r: ValkeyTestClient) -> None:
    """
    test {EXPIRE with unsupported options} {
        catch {r EXPIRE foo 200 AB} e
        set e
    } {ERR Unsupported option AB}
    """
    try:
        e = r.run("EXPIRE", "foo", 200, "AB")
    except Exception as _catch_err:
        e = str(_catch_err)
    assert e == "ERR Unsupported option AB"


def test_expire_with_unsupported_options_1(r: ValkeyTestClient) -> None:
    """
    test {EXPIRE with unsupported options} {
        catch {r EXPIRE foo 200 XX AB} e
        set e
    } {ERR Unsupported option AB}
    """
    try:
        e = r.run("EXPIRE", "foo", 200, "XX", "AB")
    except Exception as _catch_err:
        e = str(_catch_err)
    assert e == "ERR Unsupported option AB"


def test_expire_with_negative_expiry(r: ValkeyTestClient) -> None:
    """
    test {EXPIRE with negative expiry} {
        r SET foo bar EX 100
        assert_equal [r EXPIRE foo -10 LT] 1
        assert_equal [r TTL foo] -2
    } {}
    """
    r.run("SET", "foo", "bar", "EX", 100)
    assert r.run("EXPIRE", "foo", -10, "LT") == 1
    assert r.run("TTL", "foo") == -2


def test_expire_with_negative_expiry_on_a_non_valitale_key(r: ValkeyTestClient) -> None:
    """
    test {EXPIRE with negative expiry on a non-valitale key} {
        r SET foo bar
        assert_equal [r EXPIRE foo -10 LT] 1
        assert_equal [r TTL foo] -2
    } {}
    """
    r.run("SET", "foo", "bar")
    assert r.run("EXPIRE", "foo", -10, "LT") == 1
    assert r.run("TTL", "foo") == -2


def test_expire_with_non_existed_key(r: ValkeyTestClient) -> None:
    """
    test {EXPIRE with non-existed key} {
        assert_equal [r EXPIRE none 100 NX] 0
        assert_equal [r EXPIRE none 100 XX] 0
        assert_equal [r EXPIRE none 100 GT] 0
        assert_equal [r EXPIRE none 100 LT] 0
    } {}
    """
    assert r.run("EXPIRE", "none", 100, "NX") == 0
    assert r.run("EXPIRE", "none", 100, "XX") == 0
    assert r.run("EXPIRE", "none", 100, "GT") == 0
    assert r.run("EXPIRE", "none", 100, "LT") == 0


def test_server_should_not_propagate_the_read_command_on_lazy_expire(r: ValkeyTestClient) -> None:
    """
    test {Server should not propagate the read command on lazy expire} {
        r debug set-active-expire 0
        r flushall ; # Clean up keyspace to avoid interference by keys from other tests
        r set foo bar PX 1
        set repl [attach_to_replication_stream]
        wait_for_condition 50 100 {
            [r get foo] eq {}
        } else {
            fail "Replication not started."
        }

        # dummy command to verify nothing else gets into the replication stream.
        r set x 1

        assert_replication_stream $repl {
            {select *}
            {unlink foo}
            {set x 1}
        }
        close_replication_stream $repl
        assert_equal [r debug set-active-expire 1] {OK}
    } {} {needs:debug}
    """
    r.run("debug", "set-active-expire", 0)
    r.run("flushall")
    r.run("set", "foo", "bar", "PX", 1)
    repl = attach_to_replication_stream()
    wait_for_condition(50, 100, lambda: r.run("get", "foo") == "", lambda: fail("Replication not started."))
    r.run("set", "x", 1)
    assert_replication_stream(repl, "            {select *}\n            {unlink foo}\n            {set x 1}\n        ")
    close_replication_stream(repl)
    assert r.run("debug", "set-active-expire", 1) == "OK"


def test_scan_lazy_expire_should_not_be_wrapped_in_multi_or_exec(r: ValkeyTestClient) -> None:
    """
    test {SCAN: Lazy-expire should not be wrapped in MULTI/EXEC} {
        r debug set-active-expire 0
        r flushall

        r set foo1 bar PX 1
        r set foo2 bar PX 1
        after 2

        set repl [attach_to_replication_stream]

        r scan 0

        assert_replication_stream $repl {
            {select *}
            {unlink foo*}
            {unlink foo*}
        }
        close_replication_stream $repl
        assert_equal [r debug set-active-expire 1] {OK}
    } {} {needs:debug}
    """
    r.run("debug", "set-active-expire", 0)
    r.run("flushall")
    r.run("set", "foo1", "bar", "PX", 1)
    r.run("set", "foo2", "bar", "PX", 1)
    time.sleep(2 / 1000)
    repl = attach_to_replication_stream()
    r.run("scan", 0)
    assert_replication_stream(
        repl, "            {select *}\n            {unlink foo*}\n            {unlink foo*}\n        "
    )
    close_replication_stream(repl)
    assert r.run("debug", "set-active-expire", 1) == "OK"


def test_randomkey_lazy_expire_should_not_be_wrapped_in_multi_or_exec(r: ValkeyTestClient) -> None:
    """
    test {RANDOMKEY: Lazy-expire should not be wrapped in MULTI/EXEC} {
        r debug set-active-expire 0
        r flushall

        r set foo1 bar PX 1
        r set foo2 bar PX 1
        after 2

        set repl [attach_to_replication_stream]

        r randomkey

        assert_replication_stream $repl {
            {select *}
            {unlink foo*}
            {unlink foo*}
        }
        close_replication_stream $repl
        assert_equal [r debug set-active-expire 1] {OK}
    } {} {needs:debug}
    """
    r.run("debug", "set-active-expire", 0)
    r.run("flushall")
    r.run("set", "foo1", "bar", "PX", 1)
    r.run("set", "foo2", "bar", "PX", 1)
    time.sleep(2 / 1000)
    repl = attach_to_replication_stream()
    r.run("randomkey")
    assert_replication_stream(
        repl, "            {select *}\n            {unlink foo*}\n            {unlink foo*}\n        "
    )
    close_replication_stream(repl)
    assert r.run("debug", "set-active-expire", 1) == "OK"


def test_import_source_can_be_closed_when_import_mode_is_off(r: ValkeyTestClient) -> None:
    """
    test {import-source can be closed when import-mode is off} {
        r config set import-mode no
        assert_error "ERR Server is not in import mode" {r client import-source on}

        r config set import-mode yes
        assert_equal [r client import-source on] {OK}
        assert_match {*flags=I*} [r client list id [r client id]]

        r config set import-mode no
        assert_equal [r client import-source off] {OK}
        assert_match {*flags=N*} [r client list id [r client id]]
    }
    """
    r.run("config", "set", "import-mode", "no")
    with pytest.raises(Exception, match="ERR\\ Server\\ is\\ not\\ in\\ import\\ mode"):
        r.run("client", "import-source", "on")
    r.run("config", "set", "import-mode", "yes")
    assert r.run("client", "import-source", "on") == "OK"
    assert fnmatch(str(r.run("client", "list", "id", r.run("client", "id"))), "*flags=I*")
    r.run("config", "set", "import-mode", "no")
    assert r.run("client", "import-source", "off") == "OK"
    assert fnmatch(str(r.run("client", "list", "id", r.run("client", "id"))), "*flags=N*")


def test_import_mode_should_forbid_active_expiration(r: ValkeyTestClient) -> None:
    """
    test {Import mode should forbid active expiration} {
        r flushall

        r config set import-mode yes
        assert_equal [r client import-source on] {OK}

        r set foo1 bar PX 1
        r set foo2 bar PX 1
        after 10

        assert_equal [r dbsize] {2}

        assert_equal [r client import-source off] {OK}
        r config set import-mode no

        # Verify all keys have expired
        wait_for_condition 40 100 {
            [r dbsize] eq 0
        } else {
            fail "Keys did not actively expire."
        }
    }
    """
    r.run("flushall")
    r.run("config", "set", "import-mode", "yes")
    assert r.run("client", "import-source", "on") == "OK"
    r.run("set", "foo1", "bar", "PX", 1)
    r.run("set", "foo2", "bar", "PX", 1)
    time.sleep(10 / 1000)
    assert r.run("dbsize") == "2"
    assert r.run("client", "import-source", "off") == "OK"
    r.run("config", "set", "import-mode", "no")
    wait_for_condition(40, 100, lambda: r.run("dbsize") == 0, lambda: fail("Keys did not actively expire."))


def test_import_mode_should_forbid_lazy_expiration(r: ValkeyTestClient) -> None:
    """
    test {Import mode should forbid lazy expiration} {
        r flushall
        r debug set-active-expire 0

        r config set import-mode yes
        assert_equal [r client import-source on] {OK}

        r set foo1 1 PX 1
        after 10

        r get foo1
        assert_equal [r dbsize] {1}

        assert_equal [r client import-source off] {OK}
        r config set import-mode no

        r get foo1

        assert_equal [r dbsize] {0}

        assert_equal [r debug set-active-expire 1] {OK}
    } {} {needs:debug}
    """
    r.run("flushall")
    r.run("debug", "set-active-expire", 0)
    r.run("config", "set", "import-mode", "yes")
    assert r.run("client", "import-source", "on") == "OK"
    r.run("set", "foo1", 1, "PX", 1)
    time.sleep(10 / 1000)
    r.run("get", "foo1")
    assert r.run("dbsize") == "1"
    assert r.run("client", "import-source", "off") == "OK"
    r.run("config", "set", "import-mode", "no")
    r.run("get", "foo1")
    assert r.run("dbsize") == "0"
    assert r.run("debug", "set-active-expire", 1) == "OK"


def test_client_can_visit_expired_key_in_import_source_state(r: ValkeyTestClient) -> None:
    """
    test {Client can visit expired key in import-source state} {
        r flushall

        r config set import-mode yes

        r set foo1 1 PX 1
        after 10

        # Normal clients cannot visit expired key.
        assert_equal [r get foo1] {}
        assert_equal [r ttl foo1] {-2}
        assert_equal [r dbsize] 1

        # Client can visit expired key when in import-source state.
        assert_equal [r client import-source on] {OK}
        assert_equal [r ttl foo1] {0}
        assert_equal [r get foo1] {1}
        assert_equal [r incr foo1] {2}
        assert_equal [r randomkey] {foo1}
        assert_equal [r scan 0 match * count 10000] {0 foo1}
        assert_equal [r keys *] {foo1}

        assert_equal [r client import-source off] {OK}
        r config set import-mode no

        # Verify all keys have expired
        wait_for_condition 40 100 {
            [r dbsize] eq 0
        } else {
            fail "Keys did not actively expire."
        }
    }
    """
    r.run("flushall")
    r.run("config", "set", "import-mode", "yes")
    r.run("set", "foo1", 1, "PX", 1)
    time.sleep(10 / 1000)
    assert r.run("get", "foo1") == ""
    assert r.run("ttl", "foo1") == "-2"
    assert r.run("dbsize") == 1
    assert r.run("client", "import-source", "on") == "OK"
    assert r.run("ttl", "foo1") == "0"
    assert r.run("get", "foo1") == "1"
    assert r.run("incr", "foo1") == "2"
    assert r.run("randomkey") == "foo1"
    assert r.run("scan", 0, "match", "*", "count", 10000) == "0 foo1"
    assert r.run("keys", "*") == "foo1"
    assert r.run("client", "import-source", "off") == "OK"
    r.run("config", "set", "import-mode", "no")
    wait_for_condition(40, 100, lambda: r.run("dbsize") == 0, lambda: fail("Keys did not actively expire."))


def test_negative_ttl_will_not_cause_server_to_crash_when_import_mode_is_on(r: ValkeyTestClient) -> None:
    """
    test {Negative ttl will not cause server to crash when import mode is on} {
        r flushall
        r config set import-mode yes
        r set foo bar
        r expireat foo -1
        r set foo1 bar
        r expireat foo1 -10000
        assert_equal [r dbsize] 2
        r config set import-mode no
        wait_for_condition 30 100 {
            [r dbsize] == 0
        } else {
            fail "key wasn't expired"
        }
    }
    """
    r.run("flushall")
    r.run("config", "set", "import-mode", "yes")
    r.run("set", "foo", "bar")
    r.run("expireat", "foo", -1)
    r.run("set", "foo1", "bar")
    r.run("expireat", "foo1", -10000)
    assert r.run("dbsize") == 2
    r.run("config", "set", "import-mode", "no")
    wait_for_condition(30, 100, lambda: r.run("dbsize") == 0, lambda: fail("key wasn't expired"))


def test_replicakeyswithexpire_memory_leak_verification_and_cleanup(r: ValkeyTestClient) -> None:
    """
    test {replicaKeysWithExpire memory leak verification and cleanup} {
        # This test verifies the memory leak issue and cleanup mechanism for replicaKeysWithExpire

        # Set up a primary-replica relationship
        start_server {tags {needs:repl external:skip}} {
            # Set the outer layer server as primary
            set primary [srv -1 client]
            set primary_host [srv -1 host]
            set primary_port [srv -1 port]
            # Set this inner layer server as replica
            set replica [srv 0 client]
            set replica_host [srv 0 host]
            set replica_port [srv 0 port]

            $replica replicaof $primary_host $primary_port

            # Wait for replication to sync
            wait_for_sync $replica

            # Enable writable replica mode
            $replica config set replica-read-only no

            # Disable the cleanup via debug command to simulate the memory leak scenario
            $replica debug set-active-expire 0

            # Write a batch of keys with expiration directly to the replica
            $replica flushall
            set key_count 10
            for {set i 0} {$i < $key_count} {incr i} {
                $replica set "expire_key_$i" "value_from_replica_$i"
                $replica expire "expire_key_$i" 1
            }

            # Check the initial replicaKeysWithExpire count via info command
            set replica_count_before [s 0 slave_expires_tracked_keys]
            assert {$replica_count_before > 0}

            # Now perform failover from primary to this replica
            $primary failover to $replica_host $replica_port

            # Verify the failover completed and this server is now primary
            wait_for_condition 50 100 {
                [s -1 master_failover_state] == "no-failover"
            } else {
                fail "Failover from primary to replica did not finish"
            }

            # Verify that the count is the same - this demonstrates the memory leak
            set primary_count_before_cleanup [s 0 slave_expires_tracked_keys]
            assert {$primary_count_before_cleanup == $replica_count_before}

            # Now enable the cleanup via debug command
            $replica debug set-active-expire 1

            # Check the replicaKeysWithExpire count after cleanup - should be 0
            wait_for_condition 50 100 {
                [s 0 slave_expires_tracked_keys] eq "0"
            } else {
                fail "Count should be 0 after cleanup"
            }

            # Clean up
            $replica flushall
            assert_equal [$replica dbsize] 0
        }
    }
    """
    start_server(
        "tags {needs:repl external:skip}",
        '            # Set the outer layer server as primary\n            set primary [srv -1 client]\n            set primary_host [srv -1 host]\n            set primary_port [srv -1 port]\n            # Set this inner layer server as replica\n            set replica [srv 0 client]\n            set replica_host [srv 0 host]\n            set replica_port [srv 0 port]\n            \n            $replica replicaof $primary_host $primary_port\n            \n            # Wait for replication to sync\n            wait_for_sync $replica\n            \n            # Enable writable replica mode\n            $replica config set replica-read-only no\n            \n            # Disable the cleanup via debug command to simulate the memory leak scenario\n            $replica debug set-active-expire 0\n            \n            # Write a batch of keys with expiration directly to the replica\n            $replica flushall\n            set key_count 10\n            for {set i 0} {$i < $key_count} {incr i} {\n                $replica set "expire_key_$i" "value_from_replica_$i"\n                $replica expire "expire_key_$i" 1\n            }\n            \n            # Check the initial replicaKeysWithExpire count via info command\n            set replica_count_before [s 0 slave_expires_tracked_keys]\n            assert {$replica_count_before > 0}\n            \n            # Now perform failover from primary to this replica\n            $primary failover to $replica_host $replica_port\n            \n            # Verify the failover completed and this server is now primary\n            wait_for_condition 50 100 {\n                [s -1 master_failover_state] == "no-failover"\n            } else {\n                fail "Failover from primary to replica did not finish"\n            }\n            \n            # Verify that the count is the same - this demonstrates the memory leak\n            set primary_count_before_cleanup [s 0 slave_expires_tracked_keys]\n            assert {$primary_count_before_cleanup == $replica_count_before} \n            \n            # Now enable the cleanup via debug command\n            $replica debug set-active-expire 1\n\n            # Check the replicaKeysWithExpire count after cleanup - should be 0\n            wait_for_condition 50 100 {\n                [s 0 slave_expires_tracked_keys] eq "0"\n            } else {\n                fail "Count should be 0 after cleanup"\n            }\n            \n            # Clean up\n            $replica flushall\n            assert_equal [$replica dbsize] 0\n        ',
    )


pytestmark = [pytest.mark.expire]


def test_active_expiration_triggers_hashtable_shrink(r: ValkeyTestClient) -> None:
    """
    test {Active expiration triggers hashtable shrink} {
        r debug SET-ACTIVE-EXPIRE 0
        set persistent_keys 5
        set volatile_keys 100
        set total_keys [expr $persistent_keys + $volatile_keys]

        for {set i 0} {$i < $persistent_keys} {incr i} {
            r set "key_$i" "value_$i"
        }
        for {set i 0} {$i < $volatile_keys} {incr i} {
            r psetex "expire_key_${i}" 100 "expire_value_${i}"
        }
        set table_size_before_expire [main_hash_table_size]

        # Verify keys are set
        assert_equal $total_keys [r dbsize]

        # Wait for active expiration
        r debug SET-ACTIVE-EXPIRE 1
        wait_for_condition 100 50 {
            [r dbsize] eq $persistent_keys
        } else {
            fail "Keys not expired"
        }

        # Wait for the table to shrink and active rehashing finish
        wait_for_condition 100 50 {
            [main_hash_table_size] < $table_size_before_expire
        } else {
            puts [r debug htstats 9]
            fail "Table didn't shrink"
        }

        # Verify server is still responsive
        assert_equal [r ping] {PONG}
    } {} {needs:debug}
    """
    r.run("debug", "SET-ACTIVE-EXPIRE", 0)
    persistent_keys = 5
    volatile_keys = 100
    total_keys = expr(persistent_keys, "+", volatile_keys)
    i = 0
    while i < persistent_keys:
        r.run("set", f"key_{i}", f"value_{i}")
        i += 1
    i = 0
    while i < volatile_keys:
        r.run("psetex", f"expire_key_{i}", 100, f"expire_value_{i}")
        i += 1
    table_size_before_expire = main_hash_table_size()
    assert total_keys == r.run("dbsize")
    r.run("debug", "SET-ACTIVE-EXPIRE", 1)
    wait_for_condition(100, 50, lambda: r.run("dbsize") == persistent_keys, lambda: fail("Keys not expired"))
    wait_for_condition(
        100, 50, lambda: main_hash_table_size() < table_size_before_expire, lambda: fail("Table didn't shrink")
    )
    assert r.run("ping") == "PONG"


"""
start_cluster 1 0 {tags {"expire external:skip cluster"}} {
    test "expire scan should skip dictionaries with lot's of empty buckets" {
        r debug set-active-expire 0

        # Collect two slots to help determine the expiry scan logic is able
        # to go past certain slots which aren't valid for scanning at the given point of time.
        # And the next non empty slot after that still gets scanned and expiration happens.

        # hashslot(alice) is 749
        r psetex alice 500 val

        # hashslot(foo) is 12182
        # fill data across different slots with expiration
        for {set j 1} {$j <= 1000} {incr j} {
            r psetex "{foo}$j" 500 a
        }
        # hashslot(key) is 12539
        r psetex key 500 val

        # disable resizing, the reason for not using slow bgsave is because
        # it will hit the dict_force_resize_ratio.
        r debug dict-resizing 0

        # delete data to have lot's (99%) of empty buckets (slot 12182 should be skipped)
        for {set j 1} {$j <= 999} {incr j} {
            r del "{foo}$j"
        }

        # Trigger a full traversal of all dictionaries.
        r keys *

        r debug set-active-expire 1

        # Verify {foo}100 still exists and remaining got cleaned up
        wait_for_condition 20 100 {
            [r dbsize] eq 1
        } else {
            if {[r dbsize] eq 0} {
                puts [r debug htstats 0]
                fail "scan didn't handle slot skipping logic."
            } else {
                puts [r debug htstats 0]
                fail "scan didn't process all valid slots."
            }
        }

        # Enable resizing
        r debug dict-resizing 1

        # Wait for ongoing rehashing to complete, if any
        wait_for_condition 100 50 {
            [dict get [r memory stats] db.dict.rehashing.count] == 0
        } else {
            fail "Active rehashing didn't finish"
        }

        # put some data into slot 12182 and trigger the resize
        # by deleting it to trigger shrink
        r psetex "{foo}0" 500 a
        r del "{foo}0"

        # Verify all keys have expired
        wait_for_condition 400 100 {
            [r dbsize] eq 0
        } else {
            puts [r dbsize]
            flush stdout
            fail "Keys did not actively expire."
        }

        # Make sure we don't have any timeouts.
        assert_equal 0 [s 0 expired_time_cap_reached_count]
    } {} {needs:debug}
}
"""


# --- stubs for unimplemented TCL helpers ---


def assert_range(*args):
    raise NotImplementedError("assert_range")


def assert_replication_stream(*args):
    raise NotImplementedError("assert_replication_stream")


def attach_to_replication_stream(*args):
    raise NotImplementedError("attach_to_replication_stream")


def break_(*args):
    raise NotImplementedError("break_")


def clock(*args):
    raise NotImplementedError("clock")


def close_replication_stream(*args):
    raise NotImplementedError("close_replication_stream")


def continue_(*args):
    raise NotImplementedError("continue_")


def expr(*args):
    raise NotImplementedError("expr")


def fail(*args):
    raise NotImplementedError("fail")


def if_(*args):
    raise NotImplementedError("if_")


def main_hash_table_size(*args):
    raise NotImplementedError("main_hash_table_size")


def s(*args):
    raise NotImplementedError("s")


def start_server(*args):
    raise NotImplementedError("start_server")


def wait_for_condition(*args):
    raise NotImplementedError("wait_for_condition")
