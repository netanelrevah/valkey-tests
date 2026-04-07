# ruff: noqa: PLR2004, F841, RUF043, ANN002, ANN201
import time
from fnmatch import fnmatch

import pytest

from tests.valkey_test_client import ValkeyTestClient

pytestmark = [pytest.mark.other]


@pytest.mark.skipif("", reason="{$::force_failure}")
def test_failing_test(r: ValkeyTestClient) -> None:
    """
    test {Failing test} {
        format err
    } {ok}
    """
    format_("err")


def test_coverage_help_commands(r: ValkeyTestClient) -> None:
    """
    test {Coverage: HELP commands} {
        assert_match "*OBJECT <subcommand> *" [r OBJECT HELP]
        assert_match "*MEMORY <subcommand> *" [r MEMORY HELP]
        assert_match "*PUBSUB <subcommand> *" [r PUBSUB HELP]
        assert_match "*SLOWLOG <subcommand> *" [r SLOWLOG HELP]
        assert_match "*COMMANDLOG <subcommand> *" [r COMMANDLOG HELP]
        assert_match "*CLIENT <subcommand> *" [r CLIENT HELP]
        assert_match "*COMMAND <subcommand> *" [r COMMAND HELP]
        assert_match "*CONFIG <subcommand> *" [r CONFIG HELP]
        assert_match "*FUNCTION <subcommand> *" [r FUNCTION HELP]
        assert_match "*MODULE <subcommand> *" [r MODULE HELP]
    }
    """
    assert fnmatch(str(r.run("OBJECT", "HELP")), "*OBJECT <subcommand> *")
    assert fnmatch(str(r.run("MEMORY", "HELP")), "*MEMORY <subcommand> *")
    assert fnmatch(str(r.run("PUBSUB", "HELP")), "*PUBSUB <subcommand> *")
    assert fnmatch(str(r.run("SLOWLOG", "HELP")), "*SLOWLOG <subcommand> *")
    assert fnmatch(str(r.run("COMMANDLOG", "HELP")), "*COMMANDLOG <subcommand> *")
    assert fnmatch(str(r.run("CLIENT", "HELP")), "*CLIENT <subcommand> *")
    assert fnmatch(str(r.run("COMMAND", "HELP")), "*COMMAND <subcommand> *")
    assert fnmatch(str(r.run("CONFIG", "HELP")), "*CONFIG <subcommand> *")
    assert fnmatch(str(r.run("FUNCTION", "HELP")), "*FUNCTION <subcommand> *")
    assert fnmatch(str(r.run("MODULE", "HELP")), "*MODULE <subcommand> *")


def test_coverage_memory_malloc_stats(r: ValkeyTestClient) -> None:
    """
    test {Coverage: MEMORY MALLOC-STATS} {
        if {[string match {*jemalloc*} [s mem_allocator]]} {
            assert_match "*jemalloc*" [r memory malloc-stats]
        }
    }
    """
    if string("match", "*jemalloc*", s("mem_allocator")):
        assert fnmatch(str(r.run("memory", "malloc-stats")), "*jemalloc*")


def test_coverage_memory_purge(r: ValkeyTestClient) -> None:
    """
    test {Coverage: MEMORY PURGE} {
        if {[string match {*jemalloc*} [s mem_allocator]]} {
            assert_equal {OK} [r memory purge]
        }
    }
    """
    if string("match", "*jemalloc*", s("mem_allocator")):
        assert "OK" == r.run("memory", "purge")


def test_coverage_echo(r: ValkeyTestClient) -> None:
    """
    test {Coverage: ECHO} {
        assert_equal bang [r ECHO bang]
    }
    """
    assert "bang" == r.run("ECHO", "bang")


def test_save_make_sure_there_are_all_the_types_as_values(r: ValkeyTestClient) -> None:
    """
    test {SAVE - make sure there are all the types as values} {
        # Wait for a background saving in progress to terminate
        waitForBgsave r
        r lpush mysavelist hello
        r lpush mysavelist world
        r set myemptykey {}
        r set mynormalkey {blablablba}
        r zadd mytestzset 10 a
        r zadd mytestzset 20 b
        r zadd mytestzset 30 c
        r save
    } {OK} {needs:save}
    """
    wait_for_bgsave("r")
    r.run("lpush", "mysavelist", "hello")
    r.run("lpush", "mysavelist", "world")
    r.run("set", "myemptykey", "")
    r.run("set", "mynormalkey", "blablablba")
    r.run("zadd", "mytestzset", 10, "a")
    r.run("zadd", "mytestzset", 20, "b")
    r.run("zadd", "mytestzset", 30, "c")
    assert r.run("save") == "OK"


"""
start_server {overrides {save ""} tags {external:skip}} {
    test {FLUSHALL should not reset the dirty counter if we disable save} {
        r set key value
        r flushall
        assert_morethan [s rdb_changes_since_last_save] 0
    }

    test {FLUSHALL should reset the dirty counter to 0 if we enable save} {
        r config set save "3600 1 300 100 60 10000"
        r set key value
        r flushall
        assert_equal [s rdb_changes_since_last_save] 0
    }
}
"""


def test_bgsave(r: ValkeyTestClient) -> None:
    """
    test {BGSAVE} {
        # Use FLUSHALL instead of FLUSHDB, FLUSHALL do a foreground save
        # and reset the dirty counter to 0, so we won't trigger an unexpected bgsave.
        r flushall
        r save
        r set x 10
        r bgsave
        waitForBgsave r
        r debug reload
        r get x
    } {10} {needs:debug needs:save}
    """
    r.run("flushall")
    r.run("save")
    r.run("set", "x", 10)
    r.run("bgsave")
    wait_for_bgsave("r")
    r.run("debug", "reload")
    assert r.run("get", "x") == "10"


def test_select_an_out_of_range_db(r: ValkeyTestClient) -> None:
    """
    test {SELECT an out of range DB} {
        catch {r select 1000000} err
        set _ $err
    } {*index is out of range*} {cluster:skip}
    """
    try:
        r.run("select", 1000000)
    except Exception as _catch_err:
        err = str(_catch_err)
    assert fnmatch(str(err), "*index is out of range*")


def test_expires_after_a_reload_snapshot_append_only_file_rewrite(r: ValkeyTestClient) -> None:
    """
    test {EXPIRES after a reload (snapshot + append only file rewrite)} {
        r flushdb
        r set x 10
        r expire x 1000
        r save
        r debug reload
        set ttl [r ttl x]
        set e1 [expr {$ttl > 900 && $ttl <= 1000}]
        r bgrewriteaof
        waitForBgrewriteaof r
        r debug loadaof
        set ttl [r ttl x]
        set e2 [expr {$ttl > 900 && $ttl <= 1000}]
        list $e1 $e2
    } {1 1} {needs:debug needs:save}
    """
    r.run("flushdb")
    r.run("set", "x", 10)
    r.run("expire", "x", 1000)
    r.run("save")
    r.run("debug", "reload")
    ttl = r.run("ttl", "x")
    e1 = expr("$ttl > 900 && $ttl <= 1000")
    r.run("bgrewriteaof")
    wait_for_bgrewriteaof("r")
    r.run("debug", "loadaof")
    ttl = r.run("ttl", "x")
    e2 = expr("$ttl > 900 && $ttl <= 1000")
    assert [e1, e2] == "1 1"


def test_expires_after_aof_reload_without_rewrite(r: ValkeyTestClient) -> None:
    """
    test {EXPIRES after AOF reload (without rewrite)} {
        r flushdb
        r config set appendonly yes
        r config set aof-use-rdb-preamble no
        r set x somevalue
        r expire x 1000
        r setex y 2000 somevalue
        r set z somevalue
        r expireat z [expr {[clock seconds]+3000}]

        # Milliseconds variants
        r set px somevalue
        r pexpire px 1000000
        r psetex py 2000000 somevalue
        r set pz somevalue
        r pexpireat pz [expr {([clock seconds]+3000)*1000}]

        # Reload and check
        waitForBgrewriteaof r
        # We need to wait two seconds to avoid false positives here, otherwise
        # the DEBUG LOADAOF command may read a partial file.
        # Another solution would be to set the fsync policy to no, since this
        # prevents write() to be delayed by the completion of fsync().
        after 2000
        r debug loadaof
        set ttl [r ttl x]
        assert {$ttl > 900 && $ttl <= 1000}
        set ttl [r ttl y]
        assert {$ttl > 1900 && $ttl <= 2000}
        set ttl [r ttl z]
        assert {$ttl > 2900 && $ttl <= 3000}
        set ttl [r ttl px]
        assert {$ttl > 900 && $ttl <= 1000}
        set ttl [r ttl py]
        assert {$ttl > 1900 && $ttl <= 2000}
        set ttl [r ttl pz]
        assert {$ttl > 2900 && $ttl <= 3000}
        r config set appendonly no
    } {OK} {needs:debug}
    """
    r.run("flushdb")
    r.run("config", "set", "appendonly", "yes")
    r.run("config", "set", "aof-use-rdb-preamble", "no")
    r.run("set", "x", "somevalue")
    r.run("expire", "x", 1000)
    r.run("setex", "y", 2000, "somevalue")
    r.run("set", "z", "somevalue")
    r.run("expireat", "z", expr("[clock seconds]+3000"))
    r.run("set", "px", "somevalue")
    r.run("pexpire", "px", 1000000)
    r.run("psetex", "py", 2000000, "somevalue")
    r.run("set", "pz", "somevalue")
    r.run("pexpireat", "pz", expr("([clock seconds]+3000)*1000"))
    wait_for_bgrewriteaof("r")
    time.sleep(2000 / 1000)
    r.run("debug", "loadaof")
    ttl = r.run("ttl", "x")
    assert (ttl > 900) and (ttl <= 1000)
    ttl = r.run("ttl", "y")
    assert (ttl > 1900) and (ttl <= 2000)
    ttl = r.run("ttl", "z")
    assert (ttl > 2900) and (ttl <= 3000)
    ttl = r.run("ttl", "px")
    assert (ttl > 900) and (ttl <= 1000)
    ttl = r.run("ttl", "py")
    assert (ttl > 1900) and (ttl <= 2000)
    ttl = r.run("ttl", "pz")
    assert (ttl > 2900) and (ttl <= 3000)
    assert r.run("config", "set", "appendonly", "no") == "OK"


def test_append_basics(r: ValkeyTestClient) -> None:
    """
    test {APPEND basics} {
        r del foo
        list [r append foo bar] [r get foo] \
             [r append foo 100] [r get foo]
    } {3 bar 6 bar100}
    """
    r.run("del", "foo")
    assert [
        r.run("append", "foo", "bar"),
        r.run("get", "foo"),
        r.run("append", "foo", 100),
        r.run("get", "foo"),
    ] == "3 bar 6 bar100"


def test_append_basics_integer_encoded_values(r: ValkeyTestClient) -> None:
    """
    test {APPEND basics, integer encoded values} {
        set res {}
        r del foo
        r append foo 1
        r append foo 2
        lappend res [r get foo]
        r set foo 1
        r append foo 2
        lappend res [r get foo]
    } {12 12}
    """
    res = []
    r.run("del", "foo")
    r.run("append", "foo", 1)
    r.run("append", "foo", 2)
    res.append(r.run("get", "foo"))
    r.run("set", "foo", 1)
    r.run("append", "foo", 2)
    res.append(r.run("get", "foo"))


def test_append_fuzzing(r: ValkeyTestClient) -> None:
    """
    test {APPEND fuzzing} {
        set err {}
        foreach type {binary alpha compr} {
            set buf {}
            r del x
            for {set i 0} {$i < 1000} {incr i} {
                set bin [randstring 0 10 $type]
                append buf $bin
                r append x $bin
            }
            if {$buf != [r get x]} {
                set err "Expected '$buf' found '[r get x]'"
                break
            }
        }
        set _ $err
    } {}
    """
    err = ""
    foreach(
        "type",
        "binary alpha compr",
        "            set buf {}\n            r del x\n            for {set i 0} {$i < 1000} {incr i} {\n                set bin [randstring 0 10 $type]\n                append buf $bin\n                r append x $bin\n            }\n            if {$buf != [r get x]} {\n                set err \"Expected '$buf' found '[r get x]'\"\n                break\n            }\n        ",
    )
    _ = err


def test_flushdb(r: ValkeyTestClient) -> None:
    """
    test {FLUSHDB} {
        set aux {}
        if {$::singledb} {
            r flushdb
            lappend aux 0 [r dbsize]
        } else {
            r select 9
            r flushdb
            lappend aux [r dbsize]
            r select 10
            r flushdb
            lappend aux [r dbsize]
        }
    } {0 0}
    """
    aux = []
    if_(
        "$::singledb",
        "            r flushdb\n            lappend aux 0 [r dbsize]\n        ",
        "else",
        "            r select 9\n            r flushdb\n            lappend aux [r dbsize]\n            r select 10\n            r flushdb\n            lappend aux [r dbsize]\n        ",
    )


def test_perform_a_final_save_to_leave_a_clean_db_on_disk(r: ValkeyTestClient) -> None:
    """
    test {Perform a final SAVE to leave a clean DB on disk} {
        waitForBgsave r
        r save
    } {OK} {needs:save}
    """
    wait_for_bgsave("r")
    assert r.run("save") == "OK"


def test_reset_clears_client_state(r: ValkeyTestClient) -> None:
    """
    test {RESET clears client state} {
        r client setname test-client
        r client tracking on

        assert_equal [r reset] "RESET"
        set client [r client list]
        assert_match {*name= *} $client
        assert_match {*flags=N *} $client
    } {} {needs:reset}
    """
    r.run("client", "setname", "test-client")
    r.run("client", "tracking", "on")
    assert r.run("reset") == "RESET"
    client = r.run("client", "list")
    assert fnmatch(str(client), "*name= *")
    assert fnmatch(str(client), "*flags=N *")


def test_reset_clears_monitor_state(r: ValkeyTestClient) -> None:
    """
    test {RESET clears MONITOR state} {
        set rd [valkey_deferring_client]
        $rd monitor
        assert_equal [$rd read] "OK"

        $rd reset
        assert_equal [$rd read] "RESET"
        $rd close

        assert_no_match {*flags=O*} [r client list]
    } {} {needs:reset}
    """
    rd = ValkeyTestClient.create_from(r)
    rd.run("monitor")
    assert rd.run("read") == "OK"
    rd.run("reset")
    assert rd.run("read") == "RESET"
    rd.run("close")
    assert_no_match("*flags=O*", r.run("client", "list"))


def test_reset_clears_and_discards_multi_state(r: ValkeyTestClient) -> None:
    """
    test {RESET clears and discards MULTI state} {
        r multi
        r set key-a a

        r reset
        catch {r exec} err
        assert_match {*EXEC without MULTI*} $err
    } {} {needs:reset}
    """
    r.run("multi")
    r.run("set", "key-a", "a")
    r.run("reset")
    try:
        r.run("exec")
    except Exception as _catch_err:
        err = str(_catch_err)
    assert fnmatch(str(err), "*EXEC without MULTI*")


def test_reset_clears_pub_or_sub_state(r: ValkeyTestClient) -> None:
    """
    test {RESET clears Pub/Sub state} {
        r subscribe channel-1
        r reset

        # confirm we're not subscribed by executing another command
        r set key val
    } {OK} {needs:reset}
    """
    r.run("subscribe", "channel-1")
    r.run("reset")
    assert r.run("set", "key", "val") == "OK"


def test_reset_clears_authenticated_state(r: ValkeyTestClient) -> None:
    """
    test {RESET clears authenticated state} {
        r acl setuser user1 on >secret +@all
        r auth user1 secret
        assert_equal [r acl whoami] user1

        r reset

        assert_equal [r acl whoami] default
    } {} {needs:reset}
    """
    r.run("acl", "setuser", "user1", "on", ">secret", "+@all")
    r.run("auth", "user1", "secret")
    assert r.run("acl", "whoami") == "user1"
    r.run("reset")
    assert r.run("acl", "whoami") == "default"


def test_subcommand_syntax_error_crash_issue_10070(r: ValkeyTestClient) -> None:
    """
    test "Subcommand syntax error crash (issue #10070)" {
        assert_error {*unknown command*} {r GET|}
        assert_error {*unknown command*} {r GET|SET}
        assert_error {*unknown command*} {r GET|SET|OTHER}
        assert_error {*unknown command*} {r CONFIG|GET GET_XX}
        assert_error {*unknown subcommand*} {r CONFIG GET_XX}
    }
    """
    with pytest.raises(Exception, match=".*unknown\\ command.*"):
        r.run("GET|")
    with pytest.raises(Exception, match=".*unknown\\ command.*"):
        r.run("GET|SET")
    with pytest.raises(Exception, match=".*unknown\\ command.*"):
        r.run("GET|SET|OTHER")
    with pytest.raises(Exception, match=".*unknown\\ command.*"):
        r.run("CONFIG|GET", "GET_XX")
    with pytest.raises(Exception, match=".*unknown\\ subcommand.*"):
        r.run("CONFIG", "GET_XX")


def test_extended_redis_compatibility_config(r: ValkeyTestClient) -> None:
    """
    test "Extended Redis Compatibility config" {
        # This config is added in Valkey 8.0, shall be deprecated and have no
        # effect in 9.x and be deleted in 10.0.
        set hello [r hello 3]
        set version [dict get $hello version]
        if {[string match "11.*" $version]} {
            # Check that the config doesn't exist anymore.
            assert_error "ERR Unknown*" {r config set extended-redis-compatibility yes}
            error "We shall also delete this test case"
        } elseif {[string match "10.*" $version]} {
            # This config is scheduled for removal. In 10.x it should still
            # exists but have no effect.
            r config set extended-redis-compatibility yes
            set hello [r hello 3]
            assert_equal valkey [dict get $hello server]
            assert_equal $version [dict get $hello version]
            r config set extended-redis-compatibility no
        } elseif {[string match "8.*" $version] || [string match "9.*" $version] || ($version eq "255.255.255")} {
            # In 8.x, the config shall work and affect HELLO server and version.
            r config set extended-redis-compatibility yes
            set hello [r hello 3]
            assert_equal "redis" [dict get $hello server]
            assert_match "7.2.*" [dict get $hello version]
            set info [r info server]
            assert_match "*redis_mode:*" $info
            assert_no_match "*server_mode:*" $info
            set lolwut_output [r lolwut version 5]
            assert_match {*Redis ver.*} $lolwut_output
            set lolwut_output [r lolwut version 6]
            assert_match {*Redis ver.*} $lolwut_output
            set lolwut_output [r lolwut version 9]
            assert_match {*Redis ver.*} $lolwut_output
            set lolwut_output [r lolwut]
            assert_match {*Redis ver.*} $lolwut_output
            r config set extended-redis-compatibility no
            set hello [r hello 3]
            assert_equal "valkey" [dict get $hello server]
            assert_equal $version [dict get $hello version]
            set info [r info server]
            assert_no_match "*redis_mode:*" $info
            assert_match "*server_mode:*" $info
            set lolwut_output [r lolwut]
            assert_match {*Valkey ver.*} $lolwut_output
            set lolwut_output [r lolwut version 5]
            assert_match {*Valkey ver.*} $lolwut_output
            set lolwut_output [r lolwut version 6]
            assert_match {*Valkey ver.*} $lolwut_output
            set lolwut_output [r lolwut version 9]
            assert_match {*Valkey ver.*} $lolwut_output
        }
    }
    """
    hello = r.run("hello", 3)
    version = hello["version"]
    if_(
        '[string match "11.*" $version]',
        '            # Check that the config doesn\'t exist anymore.\n            assert_error "ERR Unknown*" {r config set extended-redis-compatibility yes}\n            error "We shall also delete this test case"\n        ',
        "elseif",
        '[string match "10.*" $version]',
        "            # This config is scheduled for removal. In 10.x it should still\n            # exists but have no effect.\n            r config set extended-redis-compatibility yes\n            set hello [r hello 3]\n            assert_equal valkey [dict get $hello server]\n            assert_equal $version [dict get $hello version]\n            r config set extended-redis-compatibility no\n        ",
        "elseif",
        '[string match "8.*" $version] || [string match "9.*" $version] || ($version eq "255.255.255")',
        '            # In 8.x, the config shall work and affect HELLO server and version.\n            r config set extended-redis-compatibility yes\n            set hello [r hello 3]\n            assert_equal "redis" [dict get $hello server]\n            assert_match "7.2.*" [dict get $hello version]\n            set info [r info server]\n            assert_match "*redis_mode:*" $info\n            assert_no_match "*server_mode:*" $info\n            set lolwut_output [r lolwut version 5]\n            assert_match {*Redis ver.*} $lolwut_output\n            set lolwut_output [r lolwut version 6]\n            assert_match {*Redis ver.*} $lolwut_output\n            set lolwut_output [r lolwut version 9]\n            assert_match {*Redis ver.*} $lolwut_output\n            set lolwut_output [r lolwut]\n            assert_match {*Redis ver.*} $lolwut_output\n            r config set extended-redis-compatibility no\n            set hello [r hello 3]\n            assert_equal "valkey" [dict get $hello server]\n            assert_equal $version [dict get $hello version]\n            set info [r info server]\n            assert_no_match "*redis_mode:*" $info\n            assert_match "*server_mode:*" $info\n            set lolwut_output [r lolwut]\n            assert_match {*Valkey ver.*} $lolwut_output\n            set lolwut_output [r lolwut version 5]\n            assert_match {*Valkey ver.*} $lolwut_output\n            set lolwut_output [r lolwut version 6]\n            assert_match {*Valkey ver.*} $lolwut_output\n            set lolwut_output [r lolwut version 9]\n            assert_match {*Valkey ver.*} $lolwut_output\n        ',
    )


pytestmark = [pytest.mark.other_external_skip]


def test_don_t_rehash_if_server_has_child_process(r: ValkeyTestClient) -> None:
    """
    test {Don't rehash if server has child process} {
        r config set save ""
        r config set rdb-key-save-delay 1000000

        # Populate some, then check table size and populate more up to one less
        # than the soft maximum fill factor.
        populate 2000 a 1
        set table_size [main_hash_table_size]
        populate [main_hash_table_keys_before_rehashing_starts] b 1

        # Now we are close to resizing. Check that rehashing didn't start.
        assert_equal $table_size [main_hash_table_size]
        assert_no_match "*Hash table 1 stats*" [r debug htstats 9]

        r bgsave
        wait_for_condition 10 100 {
            [s rdb_bgsave_in_progress] eq 1
        } else {
            fail "bgsave did not start in time"
        }

        r mset k1 v1 k2 v2
        # Hash table should not rehash
        assert_equal $table_size [main_hash_table_size]
        assert_no_match "*Hash table 1 stats*" [r debug htstats 9]
        exec kill -9 [get_child_pid 0]
        waitForBgsave r

        # Hash table should rehash since there is no child process,
        # so the resize limit is restored.
        wait_for_condition 50 100 {
            [main_hash_table_size] > $table_size
        } else {
            fail "hash table did not rehash after child process killed"
        }
    } {} {needs:debug needs:local-process}
    """
    r.run("config", "set", "save", "")
    r.run("config", "set", "rdb-key-save-delay", 1000000)
    populate(2000, "a", 1)
    table_size = main_hash_table_size()
    populate(main_hash_table_keys_before_rehashing_starts(), "b", 1)
    assert table_size == main_hash_table_size()
    assert_no_match("*Hash table 1 stats*", r.run("debug", "htstats", 9))
    r.run("bgsave")
    wait_for_condition(10, 100, lambda: s("rdb_bgsave_in_progress") == 1, lambda: fail("bgsave did not start in time"))
    r.run("mset", "k1", "v1", "k2", "v2")
    assert table_size == main_hash_table_size()
    assert_no_match("*Hash table 1 stats*", r.run("debug", "htstats", 9))
    exec_("kill", -9, get_child_pid(0))
    wait_for_bgsave("r")
    wait_for_condition(
        50,
        100,
        lambda: main_hash_table_size() > table_size,
        lambda: fail("hash table did not rehash after child process killed"),
    )


"""
proc read_proc_title {pid} {
    set fd [open "/proc/$pid/cmdline" "r"]
    set cmdline [read $fd 1024]
    close $fd

    return $cmdline
}
"""

pytestmark = [pytest.mark.other_external_skip]


def test_process_title_set_as_expected(r: ValkeyTestClient) -> None:
    """
    test {Process title set as expected} {
        # Test only on Linux where it's easy to get cmdline without relying on tools.
        # Skip valgrind as it messes up the arguments.
        set os [exec uname]
        if {$os == "Linux" && !$::valgrind} {
            # Set a custom template
            r config set "proc-title-template" "TEST {title} {listen-addr} {port} {tls-port} {unixsocket} {config-file}"
            set cmdline [read_proc_title [srv 0 pid]]

            assert_equal "TEST" [lindex $cmdline 0]
            assert_match "*/valkey-server" [lindex $cmdline 1]

            if {$::tls} {
                set expect_port [srv 0 pport]
                set expect_tls_port [srv 0 port]
                set port [srv 0 pport]
            } else {
                set expect_port [srv 0 port]
                set expect_tls_port 0
                set port [srv 0 port]
            }

            assert_equal "$::host:$port" [lindex $cmdline 2]
            assert_equal $expect_port [lindex $cmdline 3]
            assert_equal $expect_tls_port [lindex $cmdline 4]
            assert_match "*/tests/tmp/server.*/socket" [lindex $cmdline 5]
            assert_match "*/tests/tmp/valkey.conf.*" [lindex $cmdline 6]

            # Try setting a bad template
            catch {r config set "proc-title-template" "{invalid-var}"} err
            assert_match {*template format is invalid*} $err
        }
    }
    """
    os = exec_("uname")
    if_(
        '$os == "Linux" && !$::valgrind',
        '            # Set a custom template\n            r config set "proc-title-template" "TEST {title} {listen-addr} {port} {tls-port} {unixsocket} {config-file}"\n            set cmdline [read_proc_title [srv 0 pid]]\n\n            assert_equal "TEST" [lindex $cmdline 0]\n            assert_match "*/valkey-server" [lindex $cmdline 1]\n\n            if {$::tls} {\n                set expect_port [srv 0 pport]\n                set expect_tls_port [srv 0 port]\n                set port [srv 0 pport]\n            } else {\n                set expect_port [srv 0 port]\n                set expect_tls_port 0\n                set port [srv 0 port]\n            }\n\n            assert_equal "$::host:$port" [lindex $cmdline 2]\n            assert_equal $expect_port [lindex $cmdline 3]\n            assert_equal $expect_tls_port [lindex $cmdline 4]\n            assert_match "*/tests/tmp/server.*/socket" [lindex $cmdline 5]\n            assert_match "*/tests/tmp/valkey.conf.*" [lindex $cmdline 6]\n\n            # Try setting a bad template\n            catch {r config set "proc-title-template" "{invalid-var}"} err\n            assert_match {*template format is invalid*} $err\n        ',
    )


"""
start_cluster 1 0 {tags {"other external:skip cluster slow"}} {
    r config set hz 500
    test "Server can trigger resizing" {
        r flushall
        # hashslot(foo) is 12182
        for {set j 1} {$j <= 128} {incr j} {
            r set "{foo}$j" a
        }
        set table_size [main_hash_table_size]

        # disable resizing, the reason for not using slow bgsave is because
        # it will hit the dict_force_resize_ratio.
        r debug dict-resizing 0

        # delete data to have lot's (96%) of empty buckets
        for {set j 1} {$j <= 123} {incr j} {
            r del "{foo}$j"
        }
        assert_equal $table_size [main_hash_table_size]

        # enable resizing
        r debug dict-resizing 1

        # waiting for serverCron to resize the tables
        wait_for_condition 1000 10 {
            [main_hash_table_size] < $table_size
        } else {
            puts [r debug HTSTATS 0]
            fail "hash tables weren't resize."
        }
    } {} {needs:debug}

    test "Server can rewind and trigger smaller slot resizing" {
        # hashslot(foo) is 12182
        # hashslot(alice) is 749, smaller than hashslot(foo),
        # attempt to trigger a resize on it, see details in #12802.
        for {set j 1} {$j <= 128} {incr j} {
            r set "{alice}$j" a
        }
        set table_size [main_hash_table_size]

        # disable resizing, the reason for not using slow bgsave is because
        # it will hit the dict_force_resize_ratio.
        r debug dict-resizing 0

        for {set j 1} {$j <= 123} {incr j} {
            r del "{alice}$j"
        }

        # enable resizing
        r debug dict-resizing 1

        # waiting for serverCron to resize the tables
        wait_for_condition 1000 10 {
            [main_hash_table_size] < $table_size
        } else {
            puts [r debug HTSTATS 0]
            fail "hash tables weren't resize."
        }
    } {} {needs:debug}

    test "CLUSTER FORGET with invalid node ID" {
         catch {r cluster forget 1} err
         set _ $err
    } {*ERR Unknown node*}
}
"""

pytestmark = [pytest.mark.other_external_skip]


def test_server_can_resize_empty_dict(r: ValkeyTestClient) -> None:
    """
    test "Server can resize empty dict" {
        # Write and then delete 128 keys, creating an empty dict
        r flushall
        for {set j 1} {$j <= 128} {incr j} {
            r set $j{b} a
        }
        for {set j 1} {$j <= 128} {incr j} {
            r del $j{b}
        }
        # The dict containing 128 keys must have expanded,
        # its hash table itself takes a lot more than 400 bytes
        set dbnum [expr {$::singledb ? 0 : 9}]
        wait_for_condition 100 50 {
            [dict get [r memory stats] db.$dbnum overhead.hashtable.main] < 400
        } else {
            fail "dict did not resize in time"
        }
    }
    """
    r.run("flushall")
    j = 1
    while j <= 128:
        r.run("set", j, "b", "a")
        j += 1
    j = 1
    while j <= 128:
        r.run("del", j, "b")
        j += 1
    dbnum = expr("$::singledb ? 0 : 9")
    wait_for_condition(
        100,
        50,
        lambda: r.run("memory", "stats")["db.$dbnum"]["overhead.hashtable.main"] < 400,
        lambda: fail("dict did not resize in time"),
    )


pytestmark = [pytest.mark.other_external_skip]


def test_test_io_threads_are_runtime_modifiable(r: ValkeyTestClient) -> None:
    """
    test "test io-threads are runtime modifiable" {
        # Randomly set the number of threads between 1 and 5
        for {set i 0} {$i < 100} {incr i} {
            set random_num [expr {int(rand() * 5) + 1}]
            r config set io-threads $random_num
            set thread_num [lindex [r config get io-threads] 1]
            assert_equal $random_num $thread_num
        }
    }
    """
    i = 0
    while i < 100:
        random_num = expr("int(rand() * 5) + 1")
        r.run("config", "set", "io-threads", random_num)
        thread_num = r.run("config", "get", "io-threads")[1]
        assert random_num == thread_num
        i += 1


"""
set tempFileName file join [pwd] [pid]
"""


"""
if {$::verbose} {
    puts "Creating temp file $tempFileName"
}
"""


"""
set tempFileId open $tempFileName w
"""


"""
set group dict get [file attributes $tempFileName] -group
"""


"""
if {$group != ""} {
    set escaped_group "\"[string map {"\\" "\\\\"} $group]\""
    start_server [list tags {"repl external:skip"} overrides [list unixsocketgroup $escaped_group unixsocketperm 744]] {
        test {test unixsocket options are set correctly} {
            set socketpath [lindex [r config get unixsocket] 1]
            set attributes [file attributes $socketpath]
            set permissions [string range [dict get $attributes -permissions] end-2 end]
            assert_equal [dict get $attributes -group] $group
            assert_equal 744 $permissions
        }
    }
}
"""


"""
if {$::verbose} {
    puts "Deleting temp file: $tempFileName"
}
"""


"""
close tempFileId
"""


"""
file delete tempFileName
"""


# --- stubs for unimplemented TCL helpers ---


def assert_no_match(*args):
    raise NotImplementedError("assert_no_match")


def error(*args):
    raise NotImplementedError("error")


def exec_(*args):
    raise NotImplementedError("exec_")


def expr(*args):
    raise NotImplementedError("expr")


def fail(*args):
    raise NotImplementedError("fail")


def foreach(*args):
    raise NotImplementedError("foreach")


def format_(*args):
    raise NotImplementedError("format_")


def get_child_pid(*args):
    raise NotImplementedError("get_child_pid")


def if_(*args):
    raise NotImplementedError("if_")


def main_hash_table_keys_before_rehashing_starts(*args):
    raise NotImplementedError("main_hash_table_keys_before_rehashing_starts")


def main_hash_table_size(*args):
    raise NotImplementedError("main_hash_table_size")


def populate(*args):
    raise NotImplementedError("populate")


def s(*args):
    raise NotImplementedError("s")


def string(*args):
    raise NotImplementedError("string")


def wait_for_bgrewriteaof(*args):
    raise NotImplementedError("wait_for_bgrewriteaof")


def wait_for_bgsave(*args):
    raise NotImplementedError("wait_for_bgsave")


def wait_for_condition(*args):
    raise NotImplementedError("wait_for_condition")
