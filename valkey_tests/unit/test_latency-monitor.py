# ruff: noqa: PLR2004, ANN002, ANN201
from fnmatch import fnmatch

import pytest

from tests.valkey_test_client import ValkeyTestClient

pytestmark = [pytest.mark.latency_monitor_needs_latency]


"""
r config set latency-monitor-threshold 200
"""


"""
r latency reset
"""


def test_latency_histogram_with_empty_histogram(r: ValkeyTestClient) -> None:
    """
    test {LATENCY HISTOGRAM with empty histogram} {
        r config resetstat
        set histo [dict create {*}[r latency histogram]]
        # Config resetstat is recorded
        assert_equal [dict size $histo] 1
        assert_match {*config|resetstat*} $histo
    }
    """
    r.run("config", "resetstat")
    histo = dict_("create", "*", r.run("latency", "histogram"))
    assert dict_("size", histo) == 1
    assert fnmatch(str(histo), "*config|resetstat*")


def test_latency_histogram_all_commands(r: ValkeyTestClient) -> None:
    """
    test {LATENCY HISTOGRAM all commands} {
        r config resetstat
        r set a b
        r set c d
        set histo [dict create {*}[r latency histogram]]
        assert_match {calls 2 histogram_usec *} [dict get $histo set]
        assert_match {calls 1 histogram_usec *} [dict get $histo "config|resetstat"]
    }
    """
    r.run("config", "resetstat")
    r.run("set", "a", "b")
    r.run("set", "c", "d")
    histo = dict_("create", "*", r.run("latency", "histogram"))
    assert fnmatch(str(histo["set"]), "calls 2 histogram_usec *")
    assert fnmatch(str(histo["config|resetstat"]), "calls 1 histogram_usec *")


def test_latency_histogram_sub_commands(r: ValkeyTestClient) -> None:
    """
    test {LATENCY HISTOGRAM sub commands} {
        r config resetstat
        r client id
        r client list
        # parent command reply with its sub commands
        set histo [dict create {*}[r latency histogram client]]
        assert {[dict size $histo] == 2}
        assert_match {calls 1 histogram_usec *} [dict get $histo "client|id"]
        assert_match {calls 1 histogram_usec *} [dict get $histo "client|list"]

        # explicitly ask for one sub-command
        set histo [dict create {*}[r latency histogram "client|id"]]
        assert {[dict size $histo] == 1}
        assert_match {calls 1 histogram_usec *} [dict get $histo "client|id"]
    }
    """
    r.run("config", "resetstat")
    r.run("client", "id")
    r.run("client", "list")
    histo = dict_("create", "*", r.run("latency", "histogram", "client"))
    assert dict_("size", histo) == 2
    assert fnmatch(str(histo["client|id"]), "calls 1 histogram_usec *")
    assert fnmatch(str(histo["client|list"]), "calls 1 histogram_usec *")
    histo = dict_("create", "*", r.run("latency", "histogram", "client|id"))
    assert dict_("size", histo) == 1
    assert fnmatch(str(histo["client|id"]), "calls 1 histogram_usec *")


def test_latency_histogram_with_a_subset_of_commands(r: ValkeyTestClient) -> None:
    """
    test {LATENCY HISTOGRAM with a subset of commands} {
        r config resetstat
        r set a b
        r set c d
        r get a
        r hset f k v
        r hgetall f
        set histo [dict create {*}[r latency histogram set hset]]
        assert_match {calls 2 histogram_usec *} [dict get $histo set]
        assert_match {calls 1 histogram_usec *} [dict get $histo hset]
        assert_equal [dict size $histo] 2
        set histo [dict create {*}[r latency histogram hgetall get zadd]]
        assert_match {calls 1 histogram_usec *} [dict get $histo hgetall]
        assert_match {calls 1 histogram_usec *} [dict get $histo get]
        assert_equal [dict size $histo] 2
    }
    """
    r.run("config", "resetstat")
    r.run("set", "a", "b")
    r.run("set", "c", "d")
    r.run("get", "a")
    r.run("hset", "f", "k", "v")
    r.run("hgetall", "f")
    histo = dict_("create", "*", r.run("latency", "histogram", "set", "hset"))
    assert fnmatch(str(histo["set"]), "calls 2 histogram_usec *")
    assert fnmatch(str(histo["hset"]), "calls 1 histogram_usec *")
    assert dict_("size", histo) == 2
    histo = dict_("create", "*", r.run("latency", "histogram", "hgetall", "get", "zadd"))
    assert fnmatch(str(histo["hgetall"]), "calls 1 histogram_usec *")
    assert fnmatch(str(histo["get"]), "calls 1 histogram_usec *")
    assert dict_("size", histo) == 2


def test_latency_histogram_command(r: ValkeyTestClient) -> None:
    """
    test {LATENCY HISTOGRAM command} {
        r config resetstat
        r set a b
        r get a
        assert {[llength [r latency histogram set get]] == 4}
    }
    """
    r.run("config", "resetstat")
    r.run("set", "a", "b")
    r.run("get", "a")
    assert len(r.run("latency", "histogram", "set", "get")) == 4


def test_latency_histogram_with_wrong_command_name_skips_the_invalid_one(r: ValkeyTestClient) -> None:
    """
    test {LATENCY HISTOGRAM with wrong command name skips the invalid one} {
        r config resetstat
        assert {[llength [r latency histogram blabla]] == 0}
        assert {[llength [r latency histogram blabla blabla2 set get]] == 0}
        r set a b
        r get a
        assert_match {calls 1 histogram_usec *} [lindex [r latency histogram blabla blabla2 set get] 1]
        assert_match {calls 1 histogram_usec *} [lindex [r latency histogram blabla blabla2 set get] 3]
        assert {[string length [r latency histogram blabla set get]] > 0}
    }
    """
    r.run("config", "resetstat")
    assert len(r.run("latency", "histogram", "blabla")) == 0
    assert len(r.run("latency", "histogram", "blabla", "blabla2", "set", "get")) == 0
    r.run("set", "a", "b")
    r.run("get", "a")
    assert fnmatch(str(r.run("latency", "histogram", "blabla", "blabla2", "set", "get")[1]), "calls 1 histogram_usec *")
    assert fnmatch(str(r.run("latency", "histogram", "blabla", "blabla2", "set", "get")[3]), "calls 1 histogram_usec *")
    assert len(r.run("latency", "histogram", "blabla", "set", "get")) > 0


@pytest.mark.xfail(reason="not implemented")
def test_latency_of_expire_events_are_correctly_collected(r: ValkeyTestClient) -> None:
    """
    test {LATENCY of expire events are correctly collected} {
        r config set latency-monitor-threshold 1
        r config set lazyfree-lazy-expire no
        r flushdb
        if {$::valgrind} {set count 100000} else {set count 1000000}
        r eval {
            local i = 0
            while (i < tonumber(ARGV[1])) do
                redis.call('sadd',KEYS[1],i)
                i = i+1
             end
        } 1 mybigkey $count
        r pexpire mybigkey 50
        wait_for_condition 5 100 {
            [r dbsize] == 0
        } else {
            fail "key wasn't expired"
        }
        assert_match {*expire-cycle*} [r latency latest]

        test {LATENCY GRAPH can output the expire event graph} {
             assert_match {*expire-cycle*high*low*} [r latency graph expire-cycle]
        }

        r config set latency-monitor-threshold 200
        r config set lazyfree-lazy-expire yes
    }
    """
    r.run("config", "set", "latency-monitor-threshold", 1)
    r.run("config", "set", "lazyfree-lazy-expire", "no")
    r.run("flushdb")
    if_("$::valgrind", "set count 100000", "else", "set count 1000000")
    # TODO: r eval {
    #       local i = 0
    #       while (i < tonumber(ARGV[1])) do
    #           redis.call('sadd',KEYS[1],i)
    #           i = i+1
    #        end
    #   } 1 mybigkey count
    r.run("pexpire", "mybigkey", 50)
    wait_for_condition(
        5, 100, "            [r dbsize] == 0\n        ", "else", '            fail "key wasn\'t expired"\n        '
    )
    assert fnmatch(str(r.run("latency", "latest")), "*expire-cycle*")
    test(
        "LATENCY GRAPH can output the expire event graph",
        "             assert_match {*expire-cycle*high*low*} [r latency graph expire-cycle]\n        ",
    )
    r.run("config", "set", "latency-monitor-threshold", 200)
    r.run("config", "set", "lazyfree-lazy-expire", "yes")


def test_latency_history_or_reset_with_wrong_event_name_is_fine(r: ValkeyTestClient) -> None:
    """
    test {LATENCY HISTORY / RESET with wrong event name is fine} {
        assert {[llength [r latency history blabla]] == 0}
        assert {[r latency reset blabla] == 0}
    }
    """
    assert len(r.run("latency", "history", "blabla")) == 0
    assert r.run("latency", "reset", "blabla") == 0


def test_latency_doctor_produces_some_output(r: ValkeyTestClient) -> None:
    """
    test {LATENCY DOCTOR produces some output} {
        assert {[string length [r latency doctor]] > 0}
    }
    """
    assert len(r.run("latency", "doctor")) > 0


def test_latency_reset_is_able_to_reset_events(r: ValkeyTestClient) -> None:
    """
    test {LATENCY RESET is able to reset events} {
        assert {[r latency reset] > 0}
        assert {[r latency latest] eq {}}
    }
    """
    assert r.run("latency", "reset") > 0
    assert r.run("latency", "latest") == ""


def test_latency_help_should_not_have_unexpected_options(r: ValkeyTestClient) -> None:
    """
    test {LATENCY HELP should not have unexpected options} {
        catch {r LATENCY help xxx} e
        assert_match "*wrong number of arguments for 'latency|help' command" $e
    }
    """
    try:
        e = r.run("LATENCY", "help", "xxx")
    except Exception as _catch_err:
        e = str(_catch_err)
    assert fnmatch(str(e), "*wrong number of arguments for 'latency|help' command")


"""
start_cluster 1 1 {tags {"latency-monitor cluster external:skip needs:latency"} overrides {latency-monitor-threshold 1}} {
    test "Cluster config file latency" {
        # This test just a sanity test so that we can make sure the code path is cover.
        # We don't assert anything since we can't be sure whether it will be counted.
        R 0 cluster saveconfig
        R 1 cluster saveconfig
        R 1 cluster failover takeover
        R 0 latency latest
        R 1 latency latest
    }
}
"""


# --- stubs for unimplemented TCL helpers ---


def dict_(*args):
    raise NotImplementedError("dict_")


def if_(*args):
    raise NotImplementedError("if_")


def test(*args):
    raise NotImplementedError("test")


def wait_for_condition(*args):
    raise NotImplementedError("wait_for_condition")
