# ruff: noqa: PLR2004, ANN001, ANN002, ANN201

from fnmatch import fnmatch

import pytest

from tests.valkey_test_client import ValkeyTestClient

pytestmark = [pytest.mark.slowlog]


def test_slowlog_check_that_it_starts_with_an_empty_log(r: ValkeyTestClient) -> None:
    """
    test {SLOWLOG - check that it starts with an empty log} {
        if {$::external} {
            r slowlog reset
        }
        r slowlog len
    } {0}
    """
    if_("$::external", "            r slowlog reset\n        ")
    assert r.run("slowlog", "len") == "0"


def test_slowlog_only_logs_commands_taking_more_time_than_specified(r: ValkeyTestClient) -> None:
    """
    test {SLOWLOG - only logs commands taking more time than specified} {
        r config set slowlog-log-slower-than 100000
        r ping
        assert_equal [r slowlog len] 0
        r debug sleep 0.2
        assert_equal [r slowlog len] 1
    } {} {needs:debug}
    """
    r.run("config", "set", "slowlog-log-slower-than", 100000)
    r.run("ping")
    assert r.run("slowlog", "len") == 0
    r.run("debug", "sleep", 0.2)
    assert r.run("slowlog", "len") == 1


def test_slowlog_zero_max_length_is_correctly_handled(r: ValkeyTestClient) -> None:
    """
    test {SLOWLOG - zero max length is correctly handled} {
        r SLOWLOG reset
        r config set slowlog-max-len 0
        r config set slowlog-log-slower-than 0
        for {set i 0} {$i < 100} {incr i} {
            r ping
        }
        r slowlog len
    } {0}
    """
    r.run("SLOWLOG", "reset")
    r.run("config", "set", "slowlog-max-len", 0)
    r.run("config", "set", "slowlog-log-slower-than", 0)
    i = 0
    while i < 100:
        r.run("ping")
        i += 1
    assert r.run("slowlog", "len") == "0"


def test_slowlog_max_entries_is_correctly_handled(r: ValkeyTestClient) -> None:
    """
    test {SLOWLOG - max entries is correctly handled} {
        r config set slowlog-log-slower-than 0
        r config set slowlog-max-len 10
        for {set i 0} {$i < 100} {incr i} {
            r ping
        }
        r slowlog len
    } {10}
    """
    r.run("config", "set", "slowlog-log-slower-than", 0)
    r.run("config", "set", "slowlog-max-len", 10)
    i = 0
    while i < 100:
        r.run("ping")
        i += 1
    assert r.run("slowlog", "len") == "10"


def test_slowlog_get_optional_argument_to_limit_output_len_works(r: ValkeyTestClient) -> None:
    """
    test {SLOWLOG - GET optional argument to limit output len works} {
        assert_equal 5  [llength [r slowlog get 5]]
        assert_equal 10 [llength [r slowlog get -1]]
        assert_equal 10 [llength [r slowlog get 20]]
    }
    """
    assert 5 == len(r.run("slowlog", "get", 5))
    assert 10 == len(r.run("slowlog", "get", -1))
    assert 10 == len(r.run("slowlog", "get", 20))


def test_slowlog_reset_subcommand_works(r: ValkeyTestClient) -> None:
    """
    test {SLOWLOG - RESET subcommand works} {
        r config set slowlog-log-slower-than 100000
        r slowlog reset
        r slowlog len
    } {0}
    """
    r.run("config", "set", "slowlog-log-slower-than", 100000)
    r.run("slowlog", "reset")
    assert r.run("slowlog", "len") == "0"


def test_slowlog_logged_entry_sanity_check(r: ValkeyTestClient) -> None:
    """
    test {SLOWLOG - logged entry sanity check} {
        r client setname foobar
        r debug sleep 0.2
        set e [lindex [r slowlog get] 0]
        assert_equal [llength $e] 6
        if {!$::external} {
            assert_equal [lindex $e 0] 106
        }
        assert_equal [expr {[lindex $e 2] > 100000}] 1
        assert_equal [lindex $e 3] {debug sleep 0.2}
        assert_equal {foobar} [lindex $e 5]
    } {} {needs:debug}
    """
    r.run("client", "setname", "foobar")
    r.run("debug", "sleep", 0.2)
    e = r.run("slowlog", "get")[0]
    assert len(e) == 6
    if_("!$::external", "            assert_equal [lindex $e 0] 106\n        ")
    assert expr("[lindex $e 2] > 100000") == 1
    assert e[3] == "debug sleep 0.2"
    assert "foobar" == e[5]


def test_slowlog_certain_commands_are_omitted_that_contain_sensitive_information(r: ValkeyTestClient) -> None:
    """
    test {SLOWLOG - Certain commands are omitted that contain sensitive information} {
        r config set slowlog-max-len 100
        r config set slowlog-log-slower-than 0
        r slowlog reset
        catch {r acl setuser "slowlog test user" +get +set} _
        r config set primaryuser ""
        r config set primaryauth ""
        r config set requirepass ""
        r config set tls-key-file-pass ""
        r config set tls-client-key-file-pass ""
        r acl setuser slowlog-test-user +get +set
        r acl getuser slowlog-test-user
        r acl deluser slowlog-test-user non-existing-user
        r config set slowlog-log-slower-than 0
        r config set slowlog-log-slower-than -1
        set slowlog_resp [r slowlog get -1]

        # Make sure normal configs work, but the two sensitive
        # commands are omitted or redacted
        assert_equal 11 [llength $slowlog_resp]
        assert_equal {slowlog reset} [lindex [lindex $slowlog_resp 10] 3]
        assert_equal {acl setuser (redacted) (redacted) (redacted)} [lindex [lindex $slowlog_resp 9] 3]
        assert_equal {config set primaryuser (redacted)} [lindex [lindex $slowlog_resp 8] 3]
        assert_equal {config set primaryauth (redacted)} [lindex [lindex $slowlog_resp 7] 3]
        assert_equal {config set requirepass (redacted)} [lindex [lindex $slowlog_resp 6] 3]
        assert_equal {config set tls-key-file-pass (redacted)} [lindex [lindex $slowlog_resp 5] 3]
        assert_equal {config set tls-client-key-file-pass (redacted)} [lindex [lindex $slowlog_resp 4] 3]
        assert_equal {acl setuser (redacted) (redacted) (redacted)} [lindex [lindex $slowlog_resp 3] 3]
        assert_equal {acl getuser (redacted)} [lindex [lindex $slowlog_resp 2] 3]
        assert_equal {acl deluser (redacted) (redacted)} [lindex [lindex $slowlog_resp 1] 3]
        assert_equal {config set slowlog-log-slower-than 0} [lindex [lindex $slowlog_resp 0] 3]
    } {} {needs:repl}
    """
    r.run("config", "set", "slowlog-max-len", 100)
    r.run("config", "set", "slowlog-log-slower-than", 0)
    r.run("slowlog", "reset")
    try:
        _ = r.run("acl", "setuser", "slowlog test user", "+get", "+set")
    except Exception as _catch_err:
        _ = str(_catch_err)
    r.run("config", "set", "primaryuser", "")
    r.run("config", "set", "primaryauth", "")
    r.run("config", "set", "requirepass", "")
    r.run("config", "set", "tls-key-file-pass", "")
    r.run("config", "set", "tls-client-key-file-pass", "")
    r.run("acl", "setuser", "slowlog-test-user", "+get", "+set")
    r.run("acl", "getuser", "slowlog-test-user")
    r.run("acl", "deluser", "slowlog-test-user", "non-existing-user")
    r.run("config", "set", "slowlog-log-slower-than", 0)
    r.run("config", "set", "slowlog-log-slower-than", -1)
    slowlog_resp = r.run("slowlog", "get", -1)
    assert 11 == len(slowlog_resp)
    assert "slowlog reset" == slowlog_resp[10][3]
    assert "acl setuser (redacted) (redacted) (redacted)" == slowlog_resp[9][3]
    assert "config set primaryuser (redacted)" == slowlog_resp[8][3]
    assert "config set primaryauth (redacted)" == slowlog_resp[7][3]
    assert "config set requirepass (redacted)" == slowlog_resp[6][3]
    assert "config set tls-key-file-pass (redacted)" == slowlog_resp[5][3]
    assert "config set tls-client-key-file-pass (redacted)" == slowlog_resp[4][3]
    assert "acl setuser (redacted) (redacted) (redacted)" == slowlog_resp[3][3]
    assert "acl getuser (redacted)" == slowlog_resp[2][3]
    assert "acl deluser (redacted) (redacted)" == slowlog_resp[1][3]
    assert "config set slowlog-log-slower-than 0" == slowlog_resp[0][3]


def test_slowlog_some_commands_can_redact_sensitive_fields(r: ValkeyTestClient) -> None:
    """
    test {SLOWLOG - Some commands can redact sensitive fields} {
        r config set slowlog-log-slower-than 0
        r slowlog reset
        r migrate [srv 0 host] [srv 0 port] key 9 5000
        r migrate [srv 0 host] [srv 0 port] key 9 5000 AUTH user
        r migrate [srv 0 host] [srv 0 port] key 9 5000 AUTH2 user password
        r config set slowlog-log-slower-than -1
        set slowlog_resp [r slowlog get]

        # Make sure all 3 commands were logged, but the sensitive fields are omitted
        assert_equal 4 [llength $slowlog_resp]
        assert_match {* key 9 5000} [lindex [lindex $slowlog_resp 2] 3]
        assert_match {* key 9 5000 AUTH (redacted)} [lindex [lindex $slowlog_resp 1] 3]
        assert_match {* key 9 5000 AUTH2 (redacted) (redacted)} [lindex [lindex $slowlog_resp 0] 3]
    } {} {needs:repl}
    """
    r.run("config", "set", "slowlog-log-slower-than", 0)
    r.run("slowlog", "reset")
    r.run("migrate", srv(0, "host"), srv(0, "port"), "key", 9, 5000)
    r.run("migrate", srv(0, "host"), srv(0, "port"), "key", 9, 5000, "AUTH", "user")
    r.run("migrate", srv(0, "host"), srv(0, "port"), "key", 9, 5000, "AUTH2", "user", "password")
    r.run("config", "set", "slowlog-log-slower-than", -1)
    slowlog_resp = r.run("slowlog", "get")
    assert 4 == len(slowlog_resp)
    assert fnmatch(str(slowlog_resp[2][3]), "* key 9 5000")
    assert fnmatch(str(slowlog_resp[1][3]), "* key 9 5000 AUTH (redacted)")
    assert fnmatch(str(slowlog_resp[0][3]), "* key 9 5000 AUTH2 (redacted) (redacted)")


def test_slowlog_rewritten_commands_are_logged_as_their_original_command(r: ValkeyTestClient) -> None:
    """
    test {SLOWLOG - Rewritten commands are logged as their original command} {
        r config set slowlog-log-slower-than 0

        # Test rewriting client arguments
        r sadd set a b c d e
        r slowlog reset

        # SPOP is rewritten as DEL when all keys are removed
        r spop set 10
        assert_equal {spop set 10} [lindex [lindex [r slowlog get] 0] 3]

        # Test replacing client arguments
        r slowlog reset

        # GEOADD is replicated as ZADD
        r geoadd cool-cities -122.33207 47.60621 Seattle
        assert_equal {geoadd cool-cities -122.33207 47.60621 Seattle} [lindex [lindex [r slowlog get] 0] 3]

        # Test replacing a single command argument
        r set A 5
        r slowlog reset

        # GETSET is replicated as SET
        r getset a 5
        assert_equal {getset a 5} [lindex [lindex [r slowlog get] 0] 3]

        # INCRBYFLOAT calls rewrite multiple times, so it's a special case
        r set A 0
        r slowlog reset

        # INCRBYFLOAT is replicated as SET
        r INCRBYFLOAT A 1.0
        assert_equal {INCRBYFLOAT A 1.0} [lindex [lindex [r slowlog get] 0] 3]

        # blocked BLPOP is replicated as LPOP
        set rd [valkey_deferring_client]
        $rd blpop l 0
        wait_for_blocked_clients_count 1 50 100
        r multi
        r lpush l foo
        r slowlog reset
        r exec
        $rd read
        $rd close
        assert_equal {blpop l 0} [lindex [lindex [r slowlog get] 0] 3]
    }
    """
    r.run("config", "set", "slowlog-log-slower-than", 0)
    r.run("sadd", "set", "a", "b", "c", "d", "e")
    r.run("slowlog", "reset")
    r.run("spop", "set", 10)
    assert "spop set 10" == r.run("slowlog", "get")[0][3]
    r.run("slowlog", "reset")
    r.run("geoadd", "cool-cities", -122.33207, 47.60621, "Seattle")
    assert "geoadd cool-cities -122.33207 47.60621 Seattle" == r.run("slowlog", "get")[0][3]
    r.run("set", "A", 5)
    r.run("slowlog", "reset")
    r.run("getset", "a", 5)
    assert "getset a 5" == r.run("slowlog", "get")[0][3]
    r.run("set", "A", 0)
    r.run("slowlog", "reset")
    r.run("INCRBYFLOAT", "A", 1.0)
    assert "INCRBYFLOAT A 1.0" == r.run("slowlog", "get")[0][3]
    rd = ValkeyTestClient.create_from(r)
    rd.run("blpop", "l", 0)
    wait_for_blocked_clients_count(1, 50, 100)
    r.run("multi")
    r.run("lpush", "l", "foo")
    r.run("slowlog", "reset")
    r.run("exec")
    rd.run("read")
    rd.run("close")
    assert "blpop l 0" == r.run("slowlog", "get")[0][3]


def test_slowlog_commands_with_too_many_arguments_are_trimmed(r: ValkeyTestClient) -> None:
    """
    test {SLOWLOG - commands with too many arguments are trimmed} {
        r config set slowlog-log-slower-than 0
        r slowlog reset
        r sadd set 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30 31 32 33
        set e [lindex [r slowlog get] end-1]
        lindex $e 3
    } {sadd set 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30 31 {... (2 more arguments)}}
    """
    r.run("config", "set", "slowlog-log-slower-than", 0)
    r.run("slowlog", "reset")
    r.run(
        "sadd",
        "set",
        3,
        4,
        5,
        6,
        7,
        8,
        9,
        10,
        11,
        12,
        13,
        14,
        15,
        16,
        17,
        18,
        19,
        20,
        21,
        22,
        23,
        24,
        25,
        26,
        27,
        28,
        29,
        30,
        31,
        32,
        33,
    )
    e = r.run("slowlog", "get")["end-1"]
    assert (
        e[3]
        == "sadd set 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30 31 {... (2 more arguments)}"
    )


def test_slowlog_too_long_arguments_are_trimmed(r: ValkeyTestClient) -> None:
    """
    test {SLOWLOG - too long arguments are trimmed} {
        r config set slowlog-log-slower-than 0
        r slowlog reset
        set arg [string repeat A 129]
        r sadd set foo $arg
        set e [lindex [r slowlog get] end-1]
        lindex $e 3
    } {sadd set foo {AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA... (1 more bytes)}}
    """
    r.run("config", "set", "slowlog-log-slower-than", 0)
    r.run("slowlog", "reset")
    arg = string("repeat", "A", 129)
    r.run("sadd", "set", "foo", arg)
    e = r.run("slowlog", "get")["end-1"]
    assert (
        e[3]
        == "sadd set foo {AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA... (1 more bytes)}"
    )


def test_slowlog_exec_is_not_logged_just_executed_commands(r: ValkeyTestClient) -> None:
    """
    test {SLOWLOG - EXEC is not logged, just executed commands} {
        r config set slowlog-log-slower-than 100000
        r slowlog reset
        assert_equal [r slowlog len] 0
        r multi
        r debug sleep 0.2
        r exec
        assert_equal [r slowlog len] 1
        set e [lindex [r slowlog get] 0]
        assert_equal [lindex $e 3] {debug sleep 0.2}
    } {} {needs:debug}
    """
    r.run("config", "set", "slowlog-log-slower-than", 100000)
    r.run("slowlog", "reset")
    assert r.run("slowlog", "len") == 0
    r.run("multi")
    r.run("debug", "sleep", 0.2)
    r.run("exec")
    assert r.run("slowlog", "len") == 1
    e = r.run("slowlog", "get")[0]
    assert e[3] == "debug sleep 0.2"


def test_slowlog_can_clean_older_entries(r: ValkeyTestClient) -> None:
    """
    test {SLOWLOG - can clean older entries} {
        r client setname lastentry_client
        r config set slowlog-max-len 1
        r debug sleep 0.2
        assert {[llength [r slowlog get]] == 1}
        set e [lindex [r slowlog get] 0]
        assert_equal {lastentry_client} [lindex $e 5]
    } {} {needs:debug}
    """
    r.run("client", "setname", "lastentry_client")
    r.run("config", "set", "slowlog-max-len", 1)
    r.run("debug", "sleep", 0.2)
    assert len(r.run("slowlog", "get")) == 1
    e = r.run("slowlog", "get")[0]
    assert "lastentry_client" == e[5]


def test_slowlog_can_be_disabled(r: ValkeyTestClient) -> None:
    """
    test {SLOWLOG - can be disabled} {
        r config set slowlog-max-len 1
        r config set slowlog-log-slower-than 1
        r slowlog reset
        r debug sleep 0.2
        assert_equal [r slowlog len] 1
        r config set slowlog-log-slower-than -1
        r slowlog reset
        r debug sleep 0.2
        assert_equal [r slowlog len] 0
    } {} {needs:debug}
    """
    r.run("config", "set", "slowlog-max-len", 1)
    r.run("config", "set", "slowlog-log-slower-than", 1)
    r.run("slowlog", "reset")
    r.run("debug", "sleep", 0.2)
    assert r.run("slowlog", "len") == 1
    r.run("config", "set", "slowlog-log-slower-than", -1)
    r.run("slowlog", "reset")
    r.run("debug", "sleep", 0.2)
    assert r.run("slowlog", "len") == 0


def test_slowlog_count_must_be_1(r: ValkeyTestClient) -> None:
    """
    test {SLOWLOG - count must be >= -1} {
        assert_error "ERR count should be greater than or equal to -1" {r slowlog get -2}
        assert_error "ERR count should be greater than or equal to -1" {r slowlog get -222}
    }
    """
    with pytest.raises(Exception, match="ERR\\ count\\ should\\ be\\ greater\\ than\\ or\\ equal\\ to\\ \\-1"):
        r.run("slowlog", "get", -2)
    with pytest.raises(Exception, match="ERR\\ count\\ should\\ be\\ greater\\ than\\ or\\ equal\\ to\\ \\-1"):
        r.run("slowlog", "get", -222)


def test_slowlog_get_all_slow_logs(r: ValkeyTestClient) -> None:
    """
    test {SLOWLOG - get all slow logs} {
        r config set slowlog-log-slower-than 0
        r config set slowlog-max-len 3
        r slowlog reset

        r set key test
        r sadd set a b c
        r incr num
        r lpush list a

        assert_equal [r slowlog len] 3
        assert_equal 0 [llength [r slowlog get 0]]
        assert_equal 1 [llength [r slowlog get 1]]
        assert_equal 3 [llength [r slowlog get -1]]
        assert_equal 3 [llength [r slowlog get 3]]
    }
    """
    r.run("config", "set", "slowlog-log-slower-than", 0)
    r.run("config", "set", "slowlog-max-len", 3)
    r.run("slowlog", "reset")
    r.run("set", "key", "test")
    r.run("sadd", "set", "a", "b", "c")
    r.run("incr", "num")
    r.run("lpush", "list", "a")
    assert r.run("slowlog", "len") == 3
    assert 0 == len(r.run("slowlog", "get", 0))
    assert 1 == len(r.run("slowlog", "get", 1))
    assert 3 == len(r.run("slowlog", "get", -1))
    assert 3 == len(r.run("slowlog", "get", 3))


def test_slowlog_blocking_command_is_reported_only_after_unblocked(r: ValkeyTestClient) -> None:
    """
    test {SLOWLOG - blocking command is reported only after unblocked} {
        # Cleanup first
        r del mylist
        # create a test client
        set rd [valkey_deferring_client]

        # config the slowlog and reset
        r config set slowlog-log-slower-than 0
        r config set slowlog-max-len 110
        r slowlog reset

        $rd BLPOP mylist 0
        wait_for_blocked_clients_count 1 50 20
        assert_equal 0 [llength [regexp -all -inline (?=BLPOP) [r slowlog get]]]

        r LPUSH mylist 1
        wait_for_blocked_clients_count 0 50 20
        assert_equal 1 [llength [regexp -all -inline (?=BLPOP) [r slowlog get]]]

        $rd close
    }
    """
    r.run("del", "mylist")
    rd = ValkeyTestClient.create_from(r)
    r.run("config", "set", "slowlog-log-slower-than", 0)
    r.run("config", "set", "slowlog-max-len", 110)
    r.run("slowlog", "reset")
    rd.run("BLPOP", "mylist", 0)
    wait_for_blocked_clients_count(1, 50, 20)
    assert 0 == len(regexp("-all", "-inline", "(?=BLPOP)", r.run("slowlog", "get")))
    r.run("LPUSH", "mylist", 1)
    wait_for_blocked_clients_count(0, 50, 20)
    assert 1 == len(regexp("-all", "-inline", "(?=BLPOP)", r.run("slowlog", "get")))
    rd.run("close")


@pytest.mark.parametrize(["is_eval"], [(0), (1)])
def test_slowlog_the_commands_in_script_are_recorded_normally_is_eval_is_eval(r: ValkeyTestClient, is_eval) -> None:
    """
    test "SLOWLOG - the commands in script are recorded normally - is_eval: $is_eval" {
        if {$is_eval == 0} {
            r function load replace "#!lua name=mylib \n redis.register_function('myfunc', function(KEYS, ARGS) server.call('ping') end)"
        }

        r client setname test-client
        r config set slowlog-log-slower-than 0
        r slowlog reset

        if {$is_eval} {
            r eval "server.call('ping')" 0
        } else {
            r fcall myfunc 0
        }
        set slowlog_resp [r slowlog get 2]
        assert_equal 2 [llength $slowlog_resp]

        # The first one is the script command, and the second one is the ping command executed in the script
        # Each slowlog contains: id, timestamp, execution time, command array, ip:port, client name
        set script_cmd [lindex $slowlog_resp 0]
        set ping_cmd [lindex $slowlog_resp 1]

        # Make sure the command are logged.
        if {$is_eval} {
            assert_equal {eval server.call('ping') 0} [lindex $script_cmd 3]
        } else {
            assert_equal {fcall myfunc 0} [lindex $script_cmd 3]
        }
        assert_equal {ping} [lindex $ping_cmd 3]

        # Make sure the client info are the logged.
        assert_equal [lindex $script_cmd 4] [lindex $ping_cmd 4]
        assert_equal {test-client} [lindex $script_cmd 5]
        assert_equal {test-client} [lindex $ping_cmd 5]
    }
    """
    if is_eval == 0:
        r.run(
            "function",
            "load",
            "replace",
            "#!lua name=mylib \n redis.register_function('myfunc', function(KEYS, ARGS) server.call('ping') end)",
        )
    r.run("client", "setname", "test-client")
    r.run("config", "set", "slowlog-log-slower-than", 0)
    r.run("slowlog", "reset")
    if is_eval:
        r.run("eval", "server.call('ping')", 0)
    else:
        r.run("fcall", "myfunc", 0)
    slowlog_resp = r.run("slowlog", "get", 2)
    assert 2 == len(slowlog_resp)
    script_cmd = slowlog_resp[0]
    ping_cmd = slowlog_resp[1]
    if_(
        "$is_eval",
        "                assert_equal {eval server.call('ping') 0} [lindex $script_cmd 3]\n            ",
        "else",
        "                assert_equal {fcall myfunc 0} [lindex $script_cmd 3]\n            ",
    )
    assert "ping" == ping_cmd[3]
    assert script_cmd[4] == ping_cmd[4]
    assert "test-client" == script_cmd[5]
    assert "test-client" == ping_cmd[5]


# --- stubs for unimplemented TCL helpers ---


def expr(*args):
    raise NotImplementedError("expr")


def if_(*args):
    raise NotImplementedError("if_")


def regexp(*args):
    raise NotImplementedError("regexp")


def srv(*args):
    raise NotImplementedError("srv")


def string(*args):
    raise NotImplementedError("string")


def wait_for_blocked_clients_count(*args):
    raise NotImplementedError("wait_for_blocked_clients_count")
