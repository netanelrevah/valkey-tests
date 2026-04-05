# ruff: noqa: F841, RUF043
import time
from fnmatch import fnmatch

import pytest

from tests.valkey_test_client import ValkeyTestClient

pytestmark = [pytest.mark.keyspace]


@pytest.mark.xfail(reason="not implemented")
def test_del_against_a_single_item(r: ValkeyTestClient) -> None:
    """
    test {DEL against a single item} {
        r set x foo
        assert {[r get x] eq "foo"}
        r del x
        r get x
    } {}
    """
    r.run("set", "x", "foo")
    # TODO: assert {[r get x] eq "foo"}
    r.run("del", "x")
    assert r.run("get", "x") == ""


@pytest.mark.xfail(reason="not implemented")
def test_vararg_del(r: ValkeyTestClient) -> None:
    """
    test {Vararg DEL} {
        r set foo1{t} a
        r set foo2{t} b
        r set foo3{t} c
        list [r del foo1{t} foo2{t} foo3{t} foo4{t}] [r mget foo1{t} foo2{t} foo3{t}]
    } {3 {{} {} {}}}
    """
    r.run("set", "foo1{t}", "a")
    r.run("set", "foo2{t}", "b")
    r.run("set", "foo3{t}", "c")
    # TODO: list r del foo1{t} foo2{t} foo3{t} foo4{t} r mget foo1{t} foo2{t} foo3{t}
    assert False


def test_untagged_multi_key_commands(r: ValkeyTestClient) -> None:
    """
    test {Untagged multi-key commands} {
        r mset foo1 a foo2 b foo3 c
        assert_equal {a b c {}} [r mget foo1 foo2 foo3 foo4]
        r del foo1 foo2 foo3 foo4
    } {3} {cluster:skip}
    """
    r.run("mset", "foo1", "a", "foo2", "b", "foo3", "c")
    assert "a b c {}" == r.run("mget", "foo1", "foo2", "foo3", "foo4")
    assert r.run("del", "foo1", "foo2", "foo3", "foo4") == "3"


@pytest.mark.xfail(reason="not implemented")
def test_keys_with_pattern(r: ValkeyTestClient) -> None:
    """
    test {KEYS with pattern} {
        foreach key {key_x key_y key_z foo_a foo_b foo_c} {
            r set $key hello
        }
        lsort [r keys foo*]
    } {foo_a foo_b foo_c}
    """
    # TODO: foreach key {key_x key_y key_z foo_a foo_b foo_c} {
    #       r set $key hello
    #   }
    # TODO: lsort r keys foo*
    assert False


@pytest.mark.xfail(reason="not implemented")
def test_keys_to_get_all_keys(r: ValkeyTestClient) -> None:
    """
    test {KEYS to get all keys} {
        lsort [r keys *]
    } {foo_a foo_b foo_c key_x key_y key_z}
    """
    # TODO: lsort r keys *
    assert False


def test_dbsize(r: ValkeyTestClient) -> None:
    """
    test {DBSIZE} {
        r dbsize
    } {6}
    """
    assert r.run("dbsize") == "6"


@pytest.mark.xfail(reason="not implemented")
def test_keys_with_hashtag(r: ValkeyTestClient) -> None:
    """
    test {KEYS with hashtag} {
        foreach key {"{a}x" "{a}y" "{a}z" "{b}a" "{b}b" "{b}c"} {
            r set $key hello
        }
        assert_equal [lsort [r keys "{a}*"]] [list "{a}x" "{a}y" "{a}z"]
        assert_equal [lsort [r keys "*{b}*"]] [list "{b}a" "{b}b" "{b}c"]
    }
    """
    # TODO: foreach key {"{a}x" "{a}y" "{a}z" "{b}a" "{b}b" "{b}c"} {
    #       r set $key hello
    #   }
    # TODO: assert_equal lsort [r keys "{a}*"] list "{a}x" "{a}y" "{a}z"
    # TODO: assert_equal lsort [r keys "*{b}*"] list "{b}a" "{b}b" "{b}c"


@pytest.mark.xfail(reason="not implemented")
def test_del_all_keys(r: ValkeyTestClient) -> None:
    """
    test {DEL all keys} {
        foreach key [r keys *] {r del $key}
        r dbsize
    } {0}
    """
    # TODO: foreach key r keys * {r del $key}
    assert r.run("dbsize") == "0"


def test_keys_with_empty_db(r: ValkeyTestClient) -> None:
    """
    test {KEYS with empty DB} {
        assert_equal {} [r keys *]
    }
    """
    assert "" == r.run("keys", "*")


def test_del_against_expired_key(r: ValkeyTestClient) -> None:
    """
    test "DEL against expired key" {
        r debug set-active-expire 0
        r setex keyExpire 1 valExpire
        after 1100
        assert_equal 0 [r del keyExpire]
        r debug set-active-expire 1
    } {OK} {needs:debug}
    """
    r.run("debug", "set-active-expire", 0)
    r.run("setex", "keyExpire", 1, "valExpire")
    time.sleep(1100 / 1000)
    assert 0 == r.run("del", "keyExpire")
    assert r.run("debug", "set-active-expire", 1) == "OK"


@pytest.mark.xfail(reason="not implemented")
def test_exists(r: ValkeyTestClient) -> None:
    """
    test {EXISTS} {
        set res {}
        r set newkey test
        append res [r exists newkey]
        r del newkey
        append res [r exists newkey]
    } {10}
    """
    res = ""
    r.run("set", "newkey", "test")
    # TODO: append res r exists newkey
    r.run("del", "newkey")
    # TODO: append res r exists newkey
    assert False


@pytest.mark.xfail(reason="not implemented")
def test_zero_length_value_in_key_set_or_get_or_exists(r: ValkeyTestClient) -> None:
    """
    test {Zero length value in key. SET/GET/EXISTS} {
        r set emptykey {}
        set res [r get emptykey]
        append res [r exists emptykey]
        r del emptykey
        append res [r exists emptykey]
    } {10}
    """
    r.run("set", "emptykey", "")
    res = r.run("get", "emptykey")
    # TODO: append res r exists emptykey
    r.run("del", "emptykey")
    # TODO: append res r exists emptykey
    assert False


@pytest.mark.xfail(reason="not implemented")
def test_commands_pipelining(r: ValkeyTestClient) -> None:
    """
    test {Commands pipelining} {
        set fd [r channel]
        puts -nonewline $fd "SET k1 xyzk\r\nGET k1\r\nPING\r\n"
        flush $fd
        set res {}
        append res [string match OK* [r read]]
        append res [r read]
        append res [string match PONG* [r read]]
        format $res
    } {1xyzk1}
    """
    fd = r.run("channel")
    # TODO: flush fd
    res = ""
    # TODO: append res string match OK* [r read]
    # TODO: append res r read
    # TODO: append res string match PONG* [r read]
    # TODO: format res
    assert False


@pytest.mark.xfail(reason="not implemented")
def test_non_existing_command(r: ValkeyTestClient) -> None:
    """
    test {Non existing command} {
        catch {r foobaredcommand} err
        string match ERR* $err
    } {1}
    """
    # TODO: catch {r foobaredcommand} err
    # TODO: string match ERR* err
    assert False


def test_rename_basic_usage(r: ValkeyTestClient) -> None:
    """
    test {RENAME basic usage} {
        r set mykey{t} hello
        r rename mykey{t} mykey1{t}
        r rename mykey1{t} mykey2{t}
        r get mykey2{t}
    } {hello}
    """
    r.run("set", "mykey{t}", "hello")
    r.run("rename", "mykey{t}", "mykey1{t}")
    r.run("rename", "mykey1{t}", "mykey2{t}")
    assert r.run("get", "mykey2{t}") == "hello"


def test_rename_source_key_should_no_longer_exist(r: ValkeyTestClient) -> None:
    """
    test {RENAME source key should no longer exist} {
        r exists mykey
    } {0}
    """
    assert r.run("exists", "mykey") == "0"


@pytest.mark.xfail(reason="not implemented")
def test_rename_against_already_existing_key(r: ValkeyTestClient) -> None:
    """
    test {RENAME against already existing key} {
        r set mykey{t} a
        r set mykey2{t} b
        r rename mykey2{t} mykey{t}
        set res [r get mykey{t}]
        append res [r exists mykey2{t}]
    } {b0}
    """
    r.run("set", "mykey{t}", "a")
    r.run("set", "mykey2{t}", "b")
    r.run("rename", "mykey2{t}", "mykey{t}")
    res = r.run("get", "mykey{t}")
    # TODO: append res r exists mykey2{t}
    assert False


@pytest.mark.xfail(reason="not implemented")
def test_renamenx_basic_usage(r: ValkeyTestClient) -> None:
    """
    test {RENAMENX basic usage} {
        r del mykey{t}
        r del mykey2{t}
        r set mykey{t} foobar
        r renamenx mykey{t} mykey2{t}
        set res [r get mykey2{t}]
        append res [r exists mykey{t}]
    } {foobar0}
    """
    r.run("del", "mykey{t}")
    r.run("del", "mykey2{t}")
    r.run("set", "mykey{t}", "foobar")
    r.run("renamenx", "mykey{t}", "mykey2{t}")
    res = r.run("get", "mykey2{t}")
    # TODO: append res r exists mykey{t}
    assert False


def test_renamenx_against_already_existing_key(r: ValkeyTestClient) -> None:
    """
    test {RENAMENX against already existing key} {
        r set mykey{t} foo
        r set mykey2{t} bar
        r renamenx mykey{t} mykey2{t}
    } {0}
    """
    r.run("set", "mykey{t}", "foo")
    r.run("set", "mykey2{t}", "bar")
    assert r.run("renamenx", "mykey{t}", "mykey2{t}") == "0"


@pytest.mark.xfail(reason="not implemented")
def test_renamenx_against_already_existing_key_2(r: ValkeyTestClient) -> None:
    """
    test {RENAMENX against already existing key (2)} {
        set res [r get mykey{t}]
        append res [r get mykey2{t}]
    } {foobar}
    """
    res = r.run("get", "mykey{t}")
    # TODO: append res r get mykey2{t}
    assert False


@pytest.mark.xfail(reason="not implemented")
def test_rename_against_non_existing_source_key(r: ValkeyTestClient) -> None:
    """
    test {RENAME against non existing source key} {
        catch {r rename nokey{t} foobar{t}} err
        format $err
    } {ERR*}
    """
    # TODO: catch {r rename nokey{t} foobar{t}} err
    # TODO: format err
    assert False


def test_rename_where_source_and_dest_key_are_the_same_existing(r: ValkeyTestClient) -> None:
    """
    test {RENAME where source and dest key are the same (existing)} {
        r set mykey foo
        r rename mykey mykey
    } {OK}
    """
    r.run("set", "mykey", "foo")
    assert r.run("rename", "mykey", "mykey") == "OK"


def test_renamenx_where_source_and_dest_key_are_the_same_existing(r: ValkeyTestClient) -> None:
    """
    test {RENAMENX where source and dest key are the same (existing)} {
        r set mykey foo
        r renamenx mykey mykey
    } {0}
    """
    r.run("set", "mykey", "foo")
    assert r.run("renamenx", "mykey", "mykey") == "0"


@pytest.mark.xfail(reason="not implemented")
def test_rename_where_source_and_dest_key_are_the_same_non_existing(r: ValkeyTestClient) -> None:
    """
    test {RENAME where source and dest key are the same (non existing)} {
        r del mykey
        catch {r rename mykey mykey} err
        format $err
    } {ERR*}
    """
    r.run("del", "mykey")
    # TODO: catch {r rename mykey mykey} err
    # TODO: format err
    assert False


@pytest.mark.xfail(reason="not implemented")
def test_rename_with_volatile_key_should_move_the_ttl_as_well(r: ValkeyTestClient) -> None:
    """
    test {RENAME with volatile key, should move the TTL as well} {
        r del mykey{t} mykey2{t}
        r set mykey{t} foo
        r expire mykey{t} 100
        assert {[r ttl mykey{t}] > 95 && [r ttl mykey{t}] <= 100}
        r rename mykey{t} mykey2{t}
        assert {[r ttl mykey2{t}] > 95 && [r ttl mykey2{t}] <= 100}
    }
    """
    r.run("del", "mykey{t}", "mykey2{t}")
    r.run("set", "mykey{t}", "foo")
    r.run("expire", "mykey{t}", 100)
    # TODO: assert {[r ttl mykey{t}] > 95 && [r ttl mykey{t}] <= 100}
    r.run("rename", "mykey{t}", "mykey2{t}")
    # TODO: assert {[r ttl mykey2{t}] > 95 && [r ttl mykey2{t}] <= 100}


@pytest.mark.xfail(reason="not implemented")
def test_rename_with_volatile_key_should_not_inherit_ttl_of_target_key(r: ValkeyTestClient) -> None:
    """
    test {RENAME with volatile key, should not inherit TTL of target key} {
        r del mykey{t} mykey2{t}
        r set mykey{t} foo
        r set mykey2{t} bar
        r expire mykey2{t} 100
        assert {[r ttl mykey{t}] == -1 && [r ttl mykey2{t}] > 0}
        r rename mykey{t} mykey2{t}
        r ttl mykey2{t}
    } {-1}
    """
    r.run("del", "mykey{t}", "mykey2{t}")
    r.run("set", "mykey{t}", "foo")
    r.run("set", "mykey2{t}", "bar")
    r.run("expire", "mykey2{t}", 100)
    # TODO: assert {[r ttl mykey{t}] == -1 && [r ttl mykey2{t}] > 0}
    r.run("rename", "mykey{t}", "mykey2{t}")
    assert r.run("ttl", "mykey2{t}") == "-1"


@pytest.mark.xfail(reason="not implemented")
def test_del_all_keys_again_db_0(r: ValkeyTestClient) -> None:
    """
    test {DEL all keys again (DB 0)} {
        foreach key [r keys *] {
            r del $key
        }
        r dbsize
    } {0}
    """
    # TODO: foreach key r keys * {
    #       r del $key
    #   }
    assert r.run("dbsize") == "0"


@pytest.mark.xfail(reason="not implemented")
def test_del_all_keys_again_db_1(r: ValkeyTestClient) -> None:
    """
    test {DEL all keys again (DB 1)} {
        r select 10
        foreach key [r keys *] {
            r del $key
        }
        set res [r dbsize]
        r select 9
        format $res
    } {0} {singledb:skip}
    """
    r.run("select", 10)
    # TODO: foreach key r keys * {
    #       r del $key
    #   }
    res = r.run("dbsize")
    r.run("select", 9)
    # TODO: format res
    assert False


@pytest.mark.xfail(reason="not implemented")
def test_copy_basic_usage_for_string(r: ValkeyTestClient) -> None:
    """
    test {COPY basic usage for string} {
        r set mykey{t} foobar
        set res {}
        r copy mykey{t} mynewkey{t}
        lappend res [r get mynewkey{t}]
        lappend res [r dbsize]
        if {$::singledb} {
            assert_equal [list foobar 2] [format $res]
        } else {
            r copy mykey{t} mynewkey{t} DB 10
            r select 10
            lappend res [r get mynewkey{t}]
            lappend res [r dbsize]
            r select 9
            assert_equal [list foobar 2 foobar 1] [format $res]
        }
    }
    """
    r.run("set", "mykey{t}", "foobar")
    res = ""
    r.run("copy", "mykey{t}", "mynewkey{t}")
    # TODO: lappend res r get mynewkey{t}
    # TODO: lappend res r dbsize
    # TODO: if {$::singledb} {
    #       assert_equal [list foobar 2] [format $res]
    #   } else {
    #       r copy mykey{t} mynewkey{t} DB 10
    #       r select 10
    #       lappend res [r get mynewkey{t}]
    #       lappend res [r dbsize]
    #       r select 9
    #       assert_equal [list foobar 2 foobar 1] [format $res]
    #   }


@pytest.mark.xfail(reason="not implemented")
def test_copy_for_string_does_not_replace_an_existing_key_without_replace_option(r: ValkeyTestClient) -> None:
    """
    test {COPY for string does not replace an existing key without REPLACE option} {
        r set mykey2{t} hello
        catch {r copy mykey2{t} mynewkey{t} DB 10} e
        set e
    } {0} {singledb:skip}
    """
    r.run("set", "mykey2{t}", "hello")
    # TODO: catch {r copy mykey2{t} mynewkey{t} DB 10} e
    # TODO: set e
    assert False


def test_copy_for_string_can_replace_an_existing_key_with_replace_option(r: ValkeyTestClient) -> None:
    """
    test {COPY for string can replace an existing key with REPLACE option} {
        r copy mykey2{t} mynewkey{t} DB 10 REPLACE
        r select 10
        r get mynewkey{t}
    } {hello} {singledb:skip}
    """
    r.run("copy", "mykey2{t}", "mynewkey{t}", "DB", 10, "REPLACE")
    r.run("select", 10)
    assert r.run("get", "mynewkey{t}") == "hello"


@pytest.mark.xfail(reason="not implemented")
def test_copy_for_string_ensures_that_copied_data_is_independent_of_copying_data(r: ValkeyTestClient) -> None:
    """
    test {COPY for string ensures that copied data is independent of copying data} {
        r flushdb
        r select 9
        r set mykey{t} foobar
        set res {}
        r copy mykey{t} mynewkey{t} DB 10
        r select 10
        lappend res [r get mynewkey{t}]
        r set mynewkey{t} hoge
        lappend res [r get mynewkey{t}]
        r select 9
        lappend res [r get mykey{t}]
        r select 10
        r flushdb
        r select 9
        format $res
    } list foobar hoge foobar {singledb:skip}
    """
    r.run("flushdb")
    r.run("select", 9)
    r.run("set", "mykey{t}", "foobar")
    res = ""
    r.run("copy", "mykey{t}", "mynewkey{t}", "DB", 10)
    r.run("select", 10)
    # TODO: lappend res r get mynewkey{t}
    r.run("set", "mynewkey{t}", "hoge")
    # TODO: lappend res r get mynewkey{t}
    r.run("select", 9)
    # TODO: lappend res r get mykey{t}
    r.run("select", 10)
    r.run("flushdb")
    r.run("select", 9)
    # TODO: format res


@pytest.mark.xfail(reason="not implemented")
def test_copy_for_string_does_not_copy_data_to_no_integer_db(r: ValkeyTestClient) -> None:
    """
    test {COPY for string does not copy data to no-integer DB} {
        r set mykey{t} foobar
        catch {r copy mykey{t} mynewkey{t} DB notanumber} e
        set e
    } {ERR value is not an integer or out of range}
    """
    r.run("set", "mykey{t}", "foobar")
    # TODO: catch {r copy mykey{t} mynewkey{t} DB notanumber} e
    # TODO: set e
    assert False


@pytest.mark.xfail(reason="not implemented")
def test_copy_can_copy_key_expire_metadata_as_well(r: ValkeyTestClient) -> None:
    """
    test {COPY can copy key expire metadata as well} {
        r set mykey{t} foobar ex 100
        r copy mykey{t} mynewkey{t} REPLACE
        assert {[r ttl mynewkey{t}] > 0 && [r ttl mynewkey{t}] <= 100}
        assert {[r get mynewkey{t}] eq "foobar"}
    }
    """
    r.run("set", "mykey{t}", "foobar", "ex", 100)
    r.run("copy", "mykey{t}", "mynewkey{t}", "REPLACE")
    # TODO: assert {[r ttl mynewkey{t}] > 0 && [r ttl mynewkey{t}] <= 100}
    # TODO: assert {[r get mynewkey{t}] eq "foobar"}


@pytest.mark.xfail(reason="not implemented")
def test_copy_does_not_create_an_expire_if_it_does_not_exist(r: ValkeyTestClient) -> None:
    """
    test {COPY does not create an expire if it does not exist} {
        r set mykey{t} foobar
        assert {[r ttl mykey{t}] == -1}
        r copy mykey{t} mynewkey{t} REPLACE
        assert {[r ttl mynewkey{t}] == -1}
        assert {[r get mynewkey{t}] eq "foobar"}
    }
    """
    r.run("set", "mykey{t}", "foobar")
    # TODO: assert {[r ttl mykey{t}] == -1}
    r.run("copy", "mykey{t}", "mynewkey{t}", "REPLACE")
    # TODO: assert {[r ttl mynewkey{t}] == -1}
    # TODO: assert {[r get mynewkey{t}] eq "foobar"}


"""
array set largevalue generate_largevalue_test_array
"""


"""
foreach {type large} array get largevalue {
    set origin_config [config_get_set list-max-listpack-size -1]
    test "COPY basic usage for list - $type" {
        r del mylist{t} mynewlist{t}
        r lpush mylist{t} a b $large c d
        assert_encoding $type mylist{t}
        r copy mylist{t} mynewlist{t}
        assert_encoding $type mynewlist{t}
        set digest [debug_digest_value mylist{t}]
        assert_equal $digest [debug_digest_value mynewlist{t}]
        assert_refcount 1 mylist{t}
        assert_refcount 1 mynewlist{t}
        r del mylist{t}
        assert_equal $digest [debug_digest_value mynewlist{t}]
    }
    config_set list-max-listpack-size $origin_config
}
"""


@pytest.mark.xfail(reason="not implemented")
@pytest.mark.parametrize(["type"], [("intset"), ("listpack"), ("hashtable")])
def test_copy_basic_usage_for_type_set(r: ValkeyTestClient) -> None:
    """
    test {COPY basic usage for $type set} {
        r del set1{t} newset1{t}
        r sadd set1{t} 1 2 3
        if {$type ne "intset"} {
            r sadd set1{t} a
        }
        if {$type eq "hashtable"} {
            for {set i 4} {$i < 200} {incr i} {
                r sadd set1{t} $i
            }
        }
        assert_encoding $type set1{t}
        r copy set1{t} newset1{t}
        set digest [debug_digest_value set1{t}]
        assert_equal $digest [debug_digest_value newset1{t}]
        assert_refcount 1 set1{t}
        assert_refcount 1 newset1{t}
        r del set1{t}
        assert_equal $digest [debug_digest_value newset1{t}]
    }
    """
    r.run("del", "set1{t}", "newset1{t}")
    r.run("sadd", "set1{t}", 1, 2, 3)
    # TODO: if {$type ne "intset"} {
    #       r sadd set1{t} a
    #   }
    # TODO: if {$type eq "hashtable"} {
    #       for {set i 4} {$i < 200} {incr i} {
    #           r sadd set1{t} $i
    #       }
    #   }
    # TODO: assert_encoding type set1{t}
    r.run("copy", "set1{t}", "newset1{t}")
    # TODO: set digest debug_digest_value set1{t}
    # TODO: assert_equal digest debug_digest_value newset1{t}
    # TODO: assert_refcount 1 set1{t}
    # TODO: assert_refcount 1 newset1{t}
    r.run("del", "set1{t}")
    # TODO: assert_equal digest debug_digest_value newset1{t}


@pytest.mark.xfail(reason="not implemented")
def test_copy_basic_usage_for_listpack_sorted_set(r: ValkeyTestClient) -> None:
    """
    test {COPY basic usage for listpack sorted set} {
        r del zset1{t} newzset1{t}
        r zadd zset1{t} 123 foobar
        assert_encoding listpack zset1{t}
        r copy zset1{t} newzset1{t}
        set digest [debug_digest_value zset1{t}]
        assert_equal $digest [debug_digest_value newzset1{t}]
        assert_refcount 1 zset1{t}
        assert_refcount 1 newzset1{t}
        r del zset1{t}
        assert_equal $digest [debug_digest_value newzset1{t}]
    }
    """
    r.run("del", "zset1{t}", "newzset1{t}")
    r.run("zadd", "zset1{t}", 123, "foobar")
    # TODO: assert_encoding listpack zset1{t}
    r.run("copy", "zset1{t}", "newzset1{t}")
    # TODO: set digest debug_digest_value zset1{t}
    # TODO: assert_equal digest debug_digest_value newzset1{t}
    # TODO: assert_refcount 1 zset1{t}
    # TODO: assert_refcount 1 newzset1{t}
    r.run("del", "zset1{t}")
    # TODO: assert_equal digest debug_digest_value newzset1{t}


@pytest.mark.xfail(reason="not implemented")
def test_copy_basic_usage_for_skiplist_sorted_set(r: ValkeyTestClient) -> None:
    """
    test {COPY basic usage for skiplist sorted set} {
        r del zset2{t} newzset2{t}
        set original_max [lindex [r config get zset-max-ziplist-entries] 1]
        r config set zset-max-ziplist-entries 0
        for {set j 0} {$j < 130} {incr j} {
            r zadd zset2{t} [randomInt 50] ele-[randomInt 10]
        }
        assert_encoding skiplist zset2{t}
        r copy zset2{t} newzset2{t}
        set digest [debug_digest_value zset2{t}]
        assert_equal $digest [debug_digest_value newzset2{t}]
        assert_refcount 1 zset2{t}
        assert_refcount 1 newzset2{t}
        r del zset2{t}
        assert_equal $digest [debug_digest_value newzset2{t}]
        r config set zset-max-ziplist-entries $original_max
    }
    """
    r.run("del", "zset2{t}", "newzset2{t}")
    # TODO: set original_max lindex [r config get zset-max-ziplist-entries] 1
    r.run("config", "set", "zset-max-ziplist-entries", 0)
    # TODO: for {set j 0} {$j < 130} {incr j} {
    #       r zadd zset2{t} [randomInt 50] ele-[randomInt 10]
    #   }
    # TODO: assert_encoding skiplist zset2{t}
    r.run("copy", "zset2{t}", "newzset2{t}")
    # TODO: set digest debug_digest_value zset2{t}
    # TODO: assert_equal digest debug_digest_value newzset2{t}
    # TODO: assert_refcount 1 zset2{t}
    # TODO: assert_refcount 1 newzset2{t}
    r.run("del", "zset2{t}")
    # TODO: assert_equal digest debug_digest_value newzset2{t}
    # TODO: r config set zset-max-ziplist-entries original _max


@pytest.mark.xfail(reason="not implemented")
def test_copy_basic_usage_for_listpack_hash(r: ValkeyTestClient) -> None:
    """
    test {COPY basic usage for listpack hash} {
        r del hash1{t} newhash1{t}
        r hset hash1{t} tmp 17179869184
        assert_encoding listpack hash1{t}
        r copy hash1{t} newhash1{t}
        set digest [debug_digest_value hash1{t}]
        assert_equal $digest [debug_digest_value newhash1{t}]
        assert_refcount 1 hash1{t}
        assert_refcount 1 newhash1{t}
        r del hash1{t}
        assert_equal $digest [debug_digest_value newhash1{t}]
    }
    """
    r.run("del", "hash1{t}", "newhash1{t}")
    r.run("hset", "hash1{t}", "tmp", 17179869184)
    # TODO: assert_encoding listpack hash1{t}
    r.run("copy", "hash1{t}", "newhash1{t}")
    # TODO: set digest debug_digest_value hash1{t}
    # TODO: assert_equal digest debug_digest_value newhash1{t}
    # TODO: assert_refcount 1 hash1{t}
    # TODO: assert_refcount 1 newhash1{t}
    r.run("del", "hash1{t}")
    # TODO: assert_equal digest debug_digest_value newhash1{t}


@pytest.mark.xfail(reason="not implemented")
def test_copy_basic_usage_for_hashtable_hash(r: ValkeyTestClient) -> None:
    """
    test {COPY basic usage for hashtable hash} {
        r del hash2{t} newhash2{t}
        set original_max [lindex [r config get hash-max-ziplist-entries] 1]
        r config set hash-max-ziplist-entries 0
        for {set i 0} {$i < 64} {incr i} {
            r hset hash2{t} [randomValue] [randomValue]
        }
        assert_encoding hashtable hash2{t}
        r copy hash2{t} newhash2{t}
        set digest [debug_digest_value hash2{t}]
        assert_equal $digest [debug_digest_value newhash2{t}]
        assert_refcount 1 hash2{t}
        assert_refcount 1 newhash2{t}
        r del hash2{t}
        assert_equal $digest [debug_digest_value newhash2{t}]
        r config set hash-max-ziplist-entries $original_max
    }
    """
    r.run("del", "hash2{t}", "newhash2{t}")
    # TODO: set original_max lindex [r config get hash-max-ziplist-entries] 1
    r.run("config", "set", "hash-max-ziplist-entries", 0)
    # TODO: for {set i 0} {$i < 64} {incr i} {
    #       r hset hash2{t} [randomValue] [randomValue]
    #   }
    # TODO: assert_encoding hashtable hash2{t}
    r.run("copy", "hash2{t}", "newhash2{t}")
    # TODO: set digest debug_digest_value hash2{t}
    # TODO: assert_equal digest debug_digest_value newhash2{t}
    # TODO: assert_refcount 1 hash2{t}
    # TODO: assert_refcount 1 newhash2{t}
    r.run("del", "hash2{t}")
    # TODO: assert_equal digest debug_digest_value newhash2{t}
    # TODO: r config set hash-max-ziplist-entries original _max


@pytest.mark.xfail(reason="not implemented")
def test_copy_basic_usage_for_stream(r: ValkeyTestClient) -> None:
    """
    test {COPY basic usage for stream} {
        r del mystream{t} mynewstream{t}
        for {set i 0} {$i < 1000} {incr i} {
            r XADD mystream{t} * item 2 value b
        }
        r copy mystream{t} mynewstream{t}
        set digest [debug_digest_value mystream{t}]
        assert_equal $digest [debug_digest_value mynewstream{t}]
        assert_refcount 1 mystream{t}
        assert_refcount 1 mynewstream{t}
        r del mystream{t}
        assert_equal $digest [debug_digest_value mynewstream{t}]
    }
    """
    r.run("del", "mystream{t}", "mynewstream{t}")
    # TODO: for {set i 0} {$i < 1000} {incr i} {
    #       r XADD mystream{t} * item 2 value b
    #   }
    r.run("copy", "mystream{t}", "mynewstream{t}")
    # TODO: set digest debug_digest_value mystream{t}
    # TODO: assert_equal digest debug_digest_value mynewstream{t}
    # TODO: assert_refcount 1 mystream{t}
    # TODO: assert_refcount 1 mynewstream{t}
    r.run("del", "mystream{t}")
    # TODO: assert_equal digest debug_digest_value mynewstream{t}


@pytest.mark.xfail(reason="not implemented")
def test_copy_basic_usage_for_stream_cgroups(r: ValkeyTestClient) -> None:
    """
    test {COPY basic usage for stream-cgroups} {
        r del x{t}
        r XADD x{t} 100 a 1
        set id [r XADD x{t} 101 b 1]
        r XADD x{t} 102 c 1
        r XADD x{t} 103 e 1
        r XADD x{t} 104 f 1
        r XADD x{t} 105 g 1
        r XGROUP CREATE x{t} g1 0
        r XGROUP CREATE x{t} g2 0
        r XREADGROUP GROUP g1 Alice COUNT 1 STREAMS x{t} >
        r XREADGROUP GROUP g1 Bob COUNT 1 STREAMS x{t} >
        r XREADGROUP GROUP g1 Bob NOACK COUNT 1 STREAMS x{t} >
        r XREADGROUP GROUP g2 Charlie COUNT 4 STREAMS x{t} >
        r XGROUP SETID x{t} g1 $id
        r XREADGROUP GROUP g1 Dave COUNT 3 STREAMS x{t} >
        r XDEL x{t} 103

        r copy x{t} newx{t}
        set info [r xinfo stream x{t} full]
        assert_equal $info [r xinfo stream newx{t} full]
        assert_refcount 1 x{t}
        assert_refcount 1 newx{t}
        r del x{t}
        assert_equal $info [r xinfo stream newx{t} full]
        r flushdb
    }
    """
    r.run("del", "x{t}")
    r.run("XADD", "x{t}", 100, "a", 1)
    id = r.run("XADD", "x{t}", 101, "b", 1)
    r.run("XADD", "x{t}", 102, "c", 1)
    r.run("XADD", "x{t}", 103, "e", 1)
    r.run("XADD", "x{t}", 104, "f", 1)
    r.run("XADD", "x{t}", 105, "g", 1)
    r.run("XGROUP", "CREATE", "x{t}", "g1", 0)
    r.run("XGROUP", "CREATE", "x{t}", "g2", 0)
    r.run("XREADGROUP", "GROUP", "g1", "Alice", "COUNT", 1, "STREAMS", "x{t}", ">")
    r.run("XREADGROUP", "GROUP", "g1", "Bob", "COUNT", 1, "STREAMS", "x{t}", ">")
    r.run("XREADGROUP", "GROUP", "g1", "Bob", "NOACK", "COUNT", 1, "STREAMS", "x{t}", ">")
    r.run("XREADGROUP", "GROUP", "g2", "Charlie", "COUNT", 4, "STREAMS", "x{t}", ">")
    r.run("XGROUP", "SETID", "x{t}", "g1", id)
    r.run("XREADGROUP", "GROUP", "g1", "Dave", "COUNT", 3, "STREAMS", "x{t}", ">")
    r.run("XDEL", "x{t}", 103)
    r.run("copy", "x{t}", "newx{t}")
    info = r.run("xinfo", "stream", "x{t}", "full")
    assert info == r.run("xinfo", "stream", "newx{t}", "full")
    # TODO: assert_refcount 1 x{t}
    # TODO: assert_refcount 1 newx{t}
    r.run("del", "x{t}")
    assert info == r.run("xinfo", "stream", "newx{t}", "full")
    r.run("flushdb")


@pytest.mark.xfail(reason="not implemented")
def test_move_basic_usage(r: ValkeyTestClient) -> None:
    """
    test {MOVE basic usage} {
        r set mykey foobar
        r move mykey 10
        set res {}
        lappend res [r exists mykey]
        lappend res [r dbsize]
        r select 10
        lappend res [r get mykey]
        lappend res [r dbsize]
        r select 9
        format $res
    } list 0 0 foobar 1 {singledb:skip}
    """
    r.run("set", "mykey", "foobar")
    r.run("move", "mykey", 10)
    res = ""
    # TODO: lappend res r exists mykey
    # TODO: lappend res r dbsize
    r.run("select", 10)
    # TODO: lappend res r get mykey
    # TODO: lappend res r dbsize
    r.run("select", 9)
    # TODO: format res


def test_move_against_key_existing_in_the_target_db(r: ValkeyTestClient) -> None:
    """
    test {MOVE against key existing in the target DB} {
        r set mykey hello
        r move mykey 10
    } {0} {singledb:skip}
    """
    r.run("set", "mykey", "hello")
    assert r.run("move", "mykey", 10) == "0"


@pytest.mark.xfail(reason="not implemented")
def test_move_against_non_integer_db_1428(r: ValkeyTestClient) -> None:
    """
    test {MOVE against non-integer DB (#1428)} {
        r set mykey hello
        catch {r move mykey notanumber} e
        set e
    } {ERR value is not an integer or out of range} {singledb:skip}
    """
    r.run("set", "mykey", "hello")
    # TODO: catch {r move mykey notanumber} e
    # TODO: set e
    assert False


@pytest.mark.xfail(reason="not implemented")
def test_move_can_move_key_expire_metadata_as_well(r: ValkeyTestClient) -> None:
    """
    test {MOVE can move key expire metadata as well} {
        r select 10
        r flushdb
        r select 9
        r set mykey foo ex 100
        r move mykey 10
        assert {[r ttl mykey] == -2}
        r select 10
        assert {[r ttl mykey] > 0 && [r ttl mykey] <= 100}
        assert {[r get mykey] eq "foo"}
        r select 9
    } {OK} {singledb:skip}
    """
    r.run("select", 10)
    r.run("flushdb")
    r.run("select", 9)
    r.run("set", "mykey", "foo", "ex", 100)
    r.run("move", "mykey", 10)
    # TODO: assert {[r ttl mykey] == -2}
    r.run("select", 10)
    # TODO: assert {[r ttl mykey] > 0 && [r ttl mykey] <= 100}
    # TODO: assert {[r get mykey] eq "foo"}
    assert r.run("select", 9) == "OK"


@pytest.mark.xfail(reason="not implemented")
def test_move_does_not_create_an_expire_if_it_does_not_exist(r: ValkeyTestClient) -> None:
    """
    test {MOVE does not create an expire if it does not exist} {
        r select 10
        r flushdb
        r select 9
        r set mykey foo
        r move mykey 10
        assert {[r ttl mykey] == -2}
        r select 10
        assert {[r ttl mykey] == -1}
        assert {[r get mykey] eq "foo"}
        r select 9
    } {OK} {singledb:skip}
    """
    r.run("select", 10)
    r.run("flushdb")
    r.run("select", 9)
    r.run("set", "mykey", "foo")
    r.run("move", "mykey", 10)
    # TODO: assert {[r ttl mykey] == -2}
    r.run("select", 10)
    # TODO: assert {[r ttl mykey] == -1}
    # TODO: assert {[r get mykey] eq "foo"}
    assert r.run("select", 9) == "OK"


@pytest.mark.xfail(reason="not implemented")
def test_set_or_get_keys_in_different_dbs(r: ValkeyTestClient) -> None:
    """
    test {SET/GET keys in different DBs} {
        r set a hello
        r set b world
        r select 10
        r set a foo
        r set b bared
        r select 9
        set res {}
        lappend res [r get a]
        lappend res [r get b]
        r select 10
        lappend res [r get a]
        lappend res [r get b]
        r select 9
        format $res
    } {hello world foo bared} {singledb:skip}
    """
    r.run("set", "a", "hello")
    r.run("set", "b", "world")
    r.run("select", 10)
    r.run("set", "a", "foo")
    r.run("set", "b", "bared")
    r.run("select", 9)
    res = ""
    # TODO: lappend res r get a
    # TODO: lappend res r get b
    r.run("select", 10)
    # TODO: lappend res r get a
    # TODO: lappend res r get b
    r.run("select", 9)
    # TODO: format res
    assert False


@pytest.mark.xfail(reason="not implemented")
def test_randomkey(r: ValkeyTestClient) -> None:
    """
    test {RANDOMKEY} {
        r flushdb
        r set foo x
        r set bar y
        set foo_seen 0
        set bar_seen 0
        for {set i 0} {$i < 100} {incr i} {
            set rkey [r randomkey]
            if {$rkey eq {foo}} {
                set foo_seen 1
            }
            if {$rkey eq {bar}} {
                set bar_seen 1
            }
        }
        list $foo_seen $bar_seen
    } {1 1}
    """
    r.run("flushdb")
    r.run("set", "foo", "x")
    r.run("set", "bar", "y")
    foo_seen = 0
    bar_seen = 0
    # TODO: for {set i 0} {$i < 100} {incr i} {
    #       set rkey [r randomkey]
    #       if {$rkey eq {foo}} {
    #           set foo_seen 1
    #       }
    #       if {$rkey eq {bar}} {
    #           set bar_seen 1
    #       }
    #   }
    # TODO: list foo _seen bar _seen
    assert False


def test_randomkey_against_empty_db(r: ValkeyTestClient) -> None:
    """
    test {RANDOMKEY against empty DB} {
        r flushdb
        r randomkey
    } {}
    """
    r.run("flushdb")
    assert r.run("randomkey") == ""


def test_randomkey_regression_1(r: ValkeyTestClient) -> None:
    """
    test {RANDOMKEY regression 1} {
        r flushdb
        r set x 10
        r del x
        r randomkey
    } {}
    """
    r.run("flushdb")
    r.run("set", "x", 10)
    r.run("del", "x")
    assert r.run("randomkey") == ""


def test_keys_two_times_with_long_key_github_issue_1208(r: ValkeyTestClient) -> None:
    """
    test {KEYS * two times with long key, Github issue #1208} {
        r flushdb
        r set dlskeriewrioeuwqoirueioqwrueoqwrueqw test
        r keys *
        r keys *
    } {dlskeriewrioeuwqoirueioqwrueoqwrueqw}
    """
    r.run("flushdb")
    r.run("set", "dlskeriewrioeuwqoirueioqwrueoqwrueqw", "test")
    r.run("keys", "*")
    assert r.run("keys", "*") == "dlskeriewrioeuwqoirueioqwrueoqwrueqw"


def test_regression_for_pattern_matching_long_nested_loops(r: ValkeyTestClient) -> None:
    """
    test {Regression for pattern matching long nested loops} {
        r flushdb
        r SET aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa 1
        r KEYS "a*a*a*a*a*a*a*a*a*a*a*a*a*a*a*a*a*a*a*a*b"
    } {}
    """
    r.run("flushdb")
    r.run("SET", "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa", 1)
    assert r.run("KEYS", "a*a*a*a*a*a*a*a*a*a*a*a*a*a*a*a*a*a*a*a*b") == ""


@pytest.mark.xfail(reason="not implemented")
def test_coverage_basic_swapdb_test_and_unhappy_path(r: ValkeyTestClient) -> None:
    """
    test {Coverage: basic SWAPDB test and unhappy path} {
        r flushall
        r select 0
        r set swapkey v1
        r select 1
        assert_match 0 [r dbsize] ;#verify DB[1] has 0 keys
        r swapdb 0 1
        assert_match 1 [r dbsize]
        r select 0
        assert_match 0 [r dbsize] ;#verify DB[0] has 0 keys
        r flushall
        assert_error "ERR DB index is out of range*" {r swapdb 44 55}
        assert_error "ERR invalid second DB index*" {r swapdb 44 a}
        assert_error "ERR invalid first DB index*" {r swapdb a 55}
        assert_error "ERR invalid first DB index*" {r swapdb a b}
        assert_match "OK" [r swapdb 0 0]
    } {} {singledb:skip cluster:skip}
    """
    r.run("flushall")
    r.run("select", 0)
    r.run("set", "swapkey", "v1")
    r.run("select", 1)
    assert fnmatch(str(r.run("dbsize")), str(0))
    r.run("swapdb", 0, 1)
    assert fnmatch(str(r.run("dbsize")), str(1))
    r.run("select", 0)
    assert fnmatch(str(r.run("dbsize")), str(0))
    r.run("flushall")
    with pytest.raises(Exception, match="ERR\\ DB\\ index\\ is\\ out\\ of\\ range.*"):
        r.run("swapdb", 44, 55)
    with pytest.raises(Exception, match="ERR\\ invalid\\ second\\ DB\\ index.*"):
        r.run("swapdb", 44, "a")
    with pytest.raises(Exception, match="ERR\\ invalid\\ first\\ DB\\ index.*"):
        r.run("swapdb", "a", 55)
    with pytest.raises(Exception, match="ERR\\ invalid\\ first\\ DB\\ index.*"):
        r.run("swapdb", "a", "b")
    # TODO: assert_match "OK" r swapdb 0 0
    assert False


@pytest.mark.xfail(reason="not implemented")
def test_coverage_swapdb_and_flushdb(r: ValkeyTestClient) -> None:
    """
    test {Coverage: SWAPDB and FLUSHDB} {
        # set a key in each db and swapdb one of 2 with different db
        # and flushdb on swapped db.
        r flushall
        r select 0
        r set swapkey v1
        r select 1
        r set swapkey1 v1
        assert_no_match "*db2:keys=*" [r info keyspace]
        r swapdb 0 2
        r select 0
        assert_match 0 [r dbsize]
        assert_no_match "*db0:keys=*" [r info keyspace]
        r select 2
        r flushdb
        assert_match 0 [r dbsize]
        assert_match "*db1:keys=*" [r info keyspace]
        assert_no_match "*db0:keys=*" [r info keyspace]
        assert_no_match "*db2:keys=*" [r info keyspace]
        r flushall
    } {OK} {singledb:skip cluster:skip}
    """
    r.run("flushall")
    r.run("select", 0)
    r.run("set", "swapkey", "v1")
    r.run("select", 1)
    r.run("set", "swapkey1", "v1")
    # TODO: assert_no_match "*db2:keys=*" r info keyspace
    r.run("swapdb", 0, 2)
    r.run("select", 0)
    assert fnmatch(str(r.run("dbsize")), str(0))
    # TODO: assert_no_match "*db0:keys=*" r info keyspace
    r.run("select", 2)
    r.run("flushdb")
    assert fnmatch(str(r.run("dbsize")), str(0))
    assert fnmatch(str(r.run("info", "keyspace")), "*db1:keys=*")
    # TODO: assert_no_match "*db0:keys=*" r info keyspace
    # TODO: assert_no_match "*db2:keys=*" r info keyspace
    assert r.run("flushall") == "OK"


@pytest.mark.xfail(reason="not implemented")
def test_regression_for_pattern_matching_very_long_nested_loops(r: ValkeyTestClient) -> None:
    """
    test {Regression for pattern matching very long nested loops} {
        r flushdb
        r SET [string repeat "a" 50000] 1
        r KEYS [string repeat "*?" 50000]
    } {}
    """
    r.run("flushdb")
    # TODO: r SET string repeat "a" 50000 1
    # TODO: r KEYS string repeat "*?" 50000
    assert False


"""
start_cluster 1 0 {tags {"keyspace external:skip cluster"}} {
    test {KEYS with empty DB in cluster mode} {
        assert_equal {} [r keys *]
        assert_equal {} [r keys foo*]
    }

    test {KEYS with empty slot in cluster mode} {
        assert_equal {} [r keys foo]
    }
}
"""
