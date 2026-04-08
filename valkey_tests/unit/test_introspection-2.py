# ruff: noqa: PLR2004, RUF043, ANN001, ANN002, ANN201
import time
from fnmatch import fnmatch

import pytest

from tests.valkey_test_client import ValkeyTestClient

"""
proc cmdstat {cmd} {
    return [cmdrstat $cmd r]
}
"""


"""
proc getlru {key} {
    set objinfo [r debug object $key]
    foreach info $objinfo {
        set kvinfo [split $info ":"]
        if {[string compare [lindex $kvinfo 0] "lru"] == 0} {
            return [lindex $kvinfo 1]
        }
    }
    fail "Can't get LRU info with DEBUG OBJECT"
}
"""

pytestmark = [pytest.mark.introspection]


def test_the_microsecond_part_of_the_time_command_will_not_overflow(r: ValkeyTestClient) -> None:
    """
    test {The microsecond part of the TIME command will not overflow} {
        set now [r time]
        set microseconds [lindex $now 1]
        assert_morethan_equal $microseconds 0
        assert_lessthan $microseconds 1000000
    }
    """
    now = r.run("time")
    microseconds = now[1]
    assert microseconds >= 0
    assert microseconds < 1000000


def test_ttl_type_and_exists_do_not_alter_the_last_access_time_of_a_key(r: ValkeyTestClient) -> None:
    """
    test {TTL, TYPE and EXISTS do not alter the last access time of a key} {
        r set foo bar
        after 3000
        r ttl foo
        r type foo
        r exists foo
        assert {[r object idletime foo] >= 2}
    }
    """
    r.run("set", "foo", "bar")
    time.sleep(3000 / 1000)
    r.run("ttl", "foo")
    r.run("type", "foo")
    r.run("exists", "foo")
    assert r.run("object", "idletime", "foo") >= 2


"""
proc test_touch_alters_access_time {} {
    r set foo bar
    r set script_foo bar
    after 3000
    r touch foo
    r eval {redis.call('touch', KEYS[1])} 1 script_foo
    assert {[r object idletime foo] < 2}
    assert {[r object idletime script_foo] < 2}
}
"""


def test_touch_alters_the_last_access_time_of_a_key(r: ValkeyTestClient) -> None:
    """
    test {TOUCH alters the last access time of a key} {
        test_touch_alters_access_time
    }
    """
    test_touch_alters_access_time()


def test_touch_alters_the_last_access_time_of_a_key_in_no_touch_mode(r: ValkeyTestClient) -> None:
    """
    test {TOUCH alters the last access time of a key in no-touch mode} {
        r client no-touch on
        test_touch_alters_access_time
        r client no-touch off
    }
    """
    r.run("client", "no-touch", "on")
    test_touch_alters_access_time()
    r.run("client", "no-touch", "off")


def test_operations_in_no_touch_mode_do_not_alter_the_last_access_time_of_a_key(r: ValkeyTestClient) -> None:
    """
    test {Operations in no-touch mode do not alter the last access time of a key} {
        r set foo bar
        r client no-touch on
        set oldlru [getlru foo]
        after 1100
        r get foo
        set newlru [getlru foo]
        assert_equal $newlru $oldlru
        r client no-touch off
        r get foo
        set newlru [getlru foo]
        assert_morethan $newlru $oldlru
    } {} {needs:debug}
    """
    r.run("set", "foo", "bar")
    r.run("client", "no-touch", "on")
    oldlru = getlru("foo")
    time.sleep(1100 / 1000)
    r.run("get", "foo")
    newlru = getlru("foo")
    assert newlru == oldlru
    r.run("client", "no-touch", "off")
    r.run("get", "foo")
    newlru = getlru("foo")
    assert newlru > oldlru


def test_touch_returns_the_number_of_existing_keys_specified(r: ValkeyTestClient) -> None:
    """
    test {TOUCH returns the number of existing keys specified} {
        r flushdb
        r set key1{t} 1
        r set key2{t} 2
        r touch key0{t} key1{t} key2{t} key3{t}
    } 2
    """
    r.run("flushdb")
    r.run("set", "key1{t}", 1)
    r.run("set", "key2{t}", 2)
    r.run("touch", "key0{t}", "key1{t}", "key2{t}", "key3{t}")


def test_command_stats_for_geoadd(r: ValkeyTestClient) -> None:
    """
    test {command stats for GEOADD} {
        r config resetstat
        r GEOADD foo 0 0 bar
        assert_match {*calls=1,*} [cmdstat geoadd]
        assert_match {} [cmdstat zadd]
    } {} {needs:config-resetstat}
    """
    r.run("config", "resetstat")
    r.run("GEOADD", "foo", 0, 0, "bar")
    assert fnmatch(str(cmdstat("geoadd")), "*calls=1,*")
    assert fnmatch(str(cmdstat("zadd")), "")


def test_errors_stats_for_geoadd(r: ValkeyTestClient) -> None:
    """
    test {errors stats for GEOADD} {
        r config resetstat
        # make sure geo command will failed
        r set foo 1
        assert_error {WRONGTYPE Operation against a key holding the wrong kind of value*} {r GEOADD foo 0 0 bar}
        assert_match {*calls=1*,rejected_calls=0,failed_calls=1*} [cmdstat geoadd]
        assert_match {} [cmdstat zadd]
    } {} {needs:config-resetstat}
    """
    r.run("config", "resetstat")
    r.run("set", "foo", 1)
    with pytest.raises(
        Exception, match="WRONGTYPE\\ Operation\\ against\\ a\\ key\\ holding\\ the\\ wrong\\ kind\\ of\\ value.*"
    ):
        r.run("GEOADD", "foo", 0, 0, "bar")
    assert fnmatch(str(cmdstat("geoadd")), "*calls=1*,rejected_calls=0,failed_calls=1*")
    assert fnmatch(str(cmdstat("zadd")), "")


def test_command_stats_for_expire(r: ValkeyTestClient) -> None:
    """
    test {command stats for EXPIRE} {
        r config resetstat
        r SET foo bar
        r EXPIRE foo 0
        assert_match {*calls=1,*} [cmdstat expire]
        assert_match {} [cmdstat del]
    } {} {needs:config-resetstat}
    """
    r.run("config", "resetstat")
    r.run("SET", "foo", "bar")
    r.run("EXPIRE", "foo", 0)
    assert fnmatch(str(cmdstat("expire")), "*calls=1,*")
    assert fnmatch(str(cmdstat("del")), "")


def test_command_stats_for_brpop(r: ValkeyTestClient) -> None:
    """
    test {command stats for BRPOP} {
        r config resetstat
        r LPUSH list foo
        r BRPOP list 0
        assert_match {*calls=1,*} [cmdstat brpop]
        assert_match {} [cmdstat rpop]
    } {} {needs:config-resetstat}
    """
    r.run("config", "resetstat")
    r.run("LPUSH", "list", "foo")
    r.run("BRPOP", "list", 0)
    assert fnmatch(str(cmdstat("brpop")), "*calls=1,*")
    assert fnmatch(str(cmdstat("rpop")), "")


def test_command_stats_for_multi(r: ValkeyTestClient) -> None:
    """
    test {command stats for MULTI} {
        r config resetstat
        r MULTI
        r set foo{t} bar
        r GEOADD foo2{t} 0 0 bar
        r EXPIRE foo2{t} 0
        r EXEC
        assert_match {*calls=1,*} [cmdstat multi]
        assert_match {*calls=1,*} [cmdstat exec]
        assert_match {*calls=1,*} [cmdstat set]
        assert_match {*calls=1,*} [cmdstat expire]
        assert_match {*calls=1,*} [cmdstat geoadd]
    } {} {needs:config-resetstat}
    """
    r.run("config", "resetstat")
    r.run("MULTI")
    r.run("set", "foo{t}", "bar")
    r.run("GEOADD", "foo2{t}", 0, 0, "bar")
    r.run("EXPIRE", "foo2{t}", 0)
    r.run("EXEC")
    assert fnmatch(str(cmdstat("multi")), "*calls=1,*")
    assert fnmatch(str(cmdstat("exec")), "*calls=1,*")
    assert fnmatch(str(cmdstat("set")), "*calls=1,*")
    assert fnmatch(str(cmdstat("expire")), "*calls=1,*")
    assert fnmatch(str(cmdstat("geoadd")), "*calls=1,*")


def test_command_stats_for_scripts(r: ValkeyTestClient) -> None:
    """
    test {command stats for scripts} {
        r config resetstat
        r set mykey myval
        r eval {
            redis.call('set', KEYS[1], 0)
            redis.call('expire', KEYS[1], 0)
            redis.call('geoadd', KEYS[1], 0, 0, "bar")
        } 1 mykey
        assert_match {*calls=1,*} [cmdstat eval]
        assert_match {*calls=2,*} [cmdstat set]
        assert_match {*calls=1,*} [cmdstat expire]
        assert_match {*calls=1,*} [cmdstat geoadd]
    } {} {needs:config-resetstat}
    """
    r.run("config", "resetstat")
    r.run("set", "mykey", "myval")
    r.run(
        "eval",
        "            redis.call('set', KEYS[1], 0)\n            redis.call('expire', KEYS[1], 0)\n            redis.call('geoadd', KEYS[1], 0, 0, \"bar\")\n        ",
        1,
        "mykey",
    )
    assert fnmatch(str(cmdstat("eval")), "*calls=1,*")
    assert fnmatch(str(cmdstat("set")), "*calls=2,*")
    assert fnmatch(str(cmdstat("expire")), "*calls=1,*")
    assert fnmatch(str(cmdstat("geoadd")), "*calls=1,*")


def test_command_count_get_total_number_of_commands(r: ValkeyTestClient) -> None:
    """
    test {COMMAND COUNT get total number of commands} {
        assert_morethan [r command count] 0
    }
    """
    assert r.run("command", "count") > 0


def test_command_getkeys_get(r: ValkeyTestClient) -> None:
    """
    test {COMMAND GETKEYS GET} {
        assert_equal {key} [r command getkeys get key]
    }
    """
    assert "key" == r.run("command", "getkeys", "get", "key")


def test_command_getkeysandflags(r: ValkeyTestClient) -> None:
    """
    test {COMMAND GETKEYSANDFLAGS} {
        assert_equal {{k1 {OW update}}} [r command getkeysandflags set k1 v1]
        assert_equal {{k1 {OW update}} {k2 {OW update}}} [r command getkeysandflags mset k1 v1 k2 v2]
        assert_equal {{k1 {RW access delete}} {k2 {RW insert}}} [r command getkeysandflags LMOVE k1 k2 left right]
        assert_equal {{k1 {RO access}} {k2 {OW update}}} [r command getkeysandflags sort k1 store k2]
    }
    """
    assert "{k1 {OW update}}" == r.run("command", "getkeysandflags", "set", "k1", "v1")
    assert "{k1 {OW update}} {k2 {OW update}}" == r.run("command", "getkeysandflags", "mset", "k1", "v1", "k2", "v2")
    assert "{k1 {RW access delete}} {k2 {RW insert}}" == r.run(
        "command", "getkeysandflags", "LMOVE", "k1", "k2", "left", "right"
    )
    assert "{k1 {RO access}} {k2 {OW update}}" == r.run("command", "getkeysandflags", "sort", "k1", "store", "k2")


def test_command_getkeys_memory_usage(r: ValkeyTestClient) -> None:
    """
    test {COMMAND GETKEYS MEMORY USAGE} {
        assert_equal {key} [r command getkeys memory usage key]
    }
    """
    assert "key" == r.run("command", "getkeys", "memory", "usage", "key")


def test_command_getkeys_xgroup(r: ValkeyTestClient) -> None:
    """
    test {COMMAND GETKEYS XGROUP} {
        assert_equal {key} [r command getkeys xgroup create key groupname $]
    }
    """
    assert "key" == r.run("command", "getkeys", "xgroup", "create", "key", "groupname", "$")


def test_command_getkeys_eval_with_keys(r: ValkeyTestClient) -> None:
    """
    test {COMMAND GETKEYS EVAL with keys} {
        assert_equal {key} [r command getkeys eval "return 1" 1 key]
    }
    """
    assert "key" == r.run("command", "getkeys", "eval", "return 1", 1, "key")


def test_command_getkeys_eval_without_keys(r: ValkeyTestClient) -> None:
    """
    test {COMMAND GETKEYS EVAL without keys} {
        assert_equal {} [r command getkeys eval "return 1" 0]
    }
    """
    assert "" == r.run("command", "getkeys", "eval", "return 1", 0)


def test_command_getkeys_lcs(r: ValkeyTestClient) -> None:
    """
    test {COMMAND GETKEYS LCS} {
        assert_equal {key1 key2} [r command getkeys lcs key1 key2]
    }
    """
    assert "key1 key2" == r.run("command", "getkeys", "lcs", "key1", "key2")


def test_command_getkeys_more_than_256_keys(r: ValkeyTestClient) -> None:
    """
    test {COMMAND GETKEYS MORE THAN 256 KEYS} {
        set all_keys [list]
        set numkeys 260
        for {set i 1} {$i <= $numkeys} {incr i} {
            lappend all_keys "key$i"
        }
        set all_keys_with_target [linsert $all_keys 0 target]
        # we are using ZUNIONSTORE command since in order to reproduce allocation of a new buffer in getKeysPrepareResult
        # when numkeys in result > 0
        # we need a command that the final number of keys is not known in the first call to getKeysPrepareResult
        # before the fix in that case data of old buffer was not copied to the new result buffer
        # causing all previous keys (numkeys) data to be uninitialize
        assert_equal $all_keys_with_target [r command getkeys ZUNIONSTORE target $numkeys {*}$all_keys]
    }
    """
    all_keys = []
    numkeys = 260
    i = 1
    while i <= numkeys:
        all_keys.append(f"key{i}")
        i += 1
    all_keys_with_target = linsert(all_keys, 0, "target")
    assert all_keys_with_target == r.run("command", "getkeys", "ZUNIONSTORE", "target", numkeys, "*", all_keys)


def test_command_list_syntax_error(r: ValkeyTestClient) -> None:
    """
    test "COMMAND LIST syntax error" {
        assert_error "ERR syntax error*" {r command list bad_arg}
        assert_error "ERR syntax error*" {r command list filterby bad_arg}
        assert_error "ERR syntax error*" {r command list filterby bad_arg bad_arg2}
    }
    """
    with pytest.raises(Exception, match="ERR\\ syntax\\ error.*"):
        r.run("command", "list", "bad_arg")
    with pytest.raises(Exception, match="ERR\\ syntax\\ error.*"):
        r.run("command", "list", "filterby", "bad_arg")
    with pytest.raises(Exception, match="ERR\\ syntax\\ error.*"):
        r.run("command", "list", "filterby", "bad_arg", "bad_arg2")


def test_command_list_without_filterby(r: ValkeyTestClient) -> None:
    """
    test "COMMAND LIST WITHOUT FILTERBY" {
        set commands [r command list]
        assert_not_equal [lsearch $commands "set"] -1
        assert_not_equal [lsearch $commands "client|list"] -1
    }
    """
    commands = r.run("command", "list")
    assert_not_equal(lsearch(commands, "set"), -1)
    assert_not_equal(lsearch(commands, "client|list"), -1)


def test_command_list_filterby_aclcat_against_non_existing_category(r: ValkeyTestClient) -> None:
    """
    test "COMMAND LIST FILTERBY ACLCAT against non existing category" {
        assert_equal {} [r command list filterby aclcat non_existing_category]
    }
    """
    assert "" == r.run("command", "list", "filterby", "aclcat", "non_existing_category")


def test_command_list_filterby_aclcat_list_all_commands_or_subcommands(r: ValkeyTestClient) -> None:
    """
    test "COMMAND LIST FILTERBY ACLCAT - list all commands/subcommands" {
        set commands [r command list filterby aclcat scripting]
        assert_not_equal [lsearch $commands "eval"] -1
        assert_not_equal [lsearch $commands "script|kill"] -1

        # Negative check, a command that should not be here
        assert_equal [lsearch $commands "set"] -1
    }
    """
    commands = r.run("command", "list", "filterby", "aclcat", "scripting")
    assert_not_equal(lsearch(commands, "eval"), -1)
    assert_not_equal(lsearch(commands, "script|kill"), -1)
    assert lsearch(commands, "set") == -1


def test_command_list_filterby_pattern_list_all_commands_or_subcommands(r: ValkeyTestClient) -> None:
    """
    test "COMMAND LIST FILTERBY PATTERN - list all commands/subcommands" {
        # Exact command match.
        assert_equal {set} [r command list filterby pattern set]
        assert_equal {get} [r command list filterby pattern get]

        # Return the parent command and all the subcommands below it.
        set commands [r command list filterby pattern config*]
        assert_not_equal [lsearch $commands "config"] -1
        assert_not_equal [lsearch $commands "config|get"] -1

        # We can filter subcommands under a parent command.
        set commands [r command list filterby pattern config|*re*]
        assert_not_equal [lsearch $commands "config|resetstat"] -1
        assert_not_equal [lsearch $commands "config|rewrite"] -1

        # We can filter subcommands across parent commands.
        set commands [r command list filterby pattern cl*help]
        assert_not_equal [lsearch $commands "client|help"] -1
        assert_not_equal [lsearch $commands "cluster|help"] -1

        # Negative check, command that doesn't exist.
        assert_equal {} [r command list filterby pattern non_exists]
        assert_equal {} [r command list filterby pattern non_exists*]
    }
    """
    assert "set" == r.run("command", "list", "filterby", "pattern", "set")
    assert "get" == r.run("command", "list", "filterby", "pattern", "get")
    commands = r.run("command", "list", "filterby", "pattern", "config*")
    assert_not_equal(lsearch(commands, "config"), -1)
    assert_not_equal(lsearch(commands, "config|get"), -1)
    commands = r.run("command", "list", "filterby", "pattern", "config|*re*")
    assert_not_equal(lsearch(commands, "config|resetstat"), -1)
    assert_not_equal(lsearch(commands, "config|rewrite"), -1)
    commands = r.run("command", "list", "filterby", "pattern", "cl*help")
    assert_not_equal(lsearch(commands, "client|help"), -1)
    assert_not_equal(lsearch(commands, "cluster|help"), -1)
    assert "" == r.run("command", "list", "filterby", "pattern", "non_exists")
    assert "" == r.run("command", "list", "filterby", "pattern", "non_exists*")


def test_command_list_filterby_module_against_non_existing_module(r: ValkeyTestClient) -> None:
    """
    test "COMMAND LIST FILTERBY MODULE against non existing module" {
        # This should be empty, the real one is in subcommands.tcl
        assert_equal {} [r command list filterby module non_existing_module]
    }
    """
    assert "" == r.run("command", "list", "filterby", "module", "non_existing_module")


def test_command_info_of_invalid_subcommands(r: ValkeyTestClient) -> None:
    """
    test {COMMAND INFO of invalid subcommands} {
        assert_equal {{}} [r command info get|key]
        assert_equal {{}} [r command info config|get|key]
    }
    """
    assert "{}" == r.run("command", "info", "get|key")
    assert "{}" == r.run("command", "info", "config|get|key")


@pytest.mark.parametrize(
    ["cmd"],
    [
        ("SET"),
        ("GET"),
        ("MSET"),
        ("BITFIELD"),
        ("LMOVE"),
        ("LPOP"),
        ("BLPOP"),
        ("PING"),
        ("MEMORY"),
        ("MEMORY|USAGE"),
        ("RENAME"),
        ("GEORADIUS_RO"),
    ],
)
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
    ["cmd"], [("ZUNIONSTORE"), ("XREAD"), ("EVAL"), ("SORT"), ("SORT_RO"), ("MIGRATE"), ("GEORADIUS")]
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


# --- stubs for unimplemented TCL helpers ---


def assert_no_match(*args):
    raise NotImplementedError("assert_no_match")


def assert_not_equal(*args):
    raise NotImplementedError("assert_not_equal")


def cmdstat(*args):
    raise NotImplementedError("cmdstat")


def getlru(*args):
    raise NotImplementedError("getlru")


def linsert(*args):
    raise NotImplementedError("linsert")


def lsearch(*args):
    raise NotImplementedError("lsearch")


def test_touch_alters_access_time(*args):
    raise NotImplementedError("test_touch_alters_access_time")
