# ruff: noqa: PLR2004, F841, ANN002, ANN201
import time
from fnmatch import fnmatch

import pytest

from tests.valkey_test_client import ValkeyTestClient

pytestmark = [pytest.mark.dump]


"""
set db expr {$::singledb ? 0 : 9}
"""


def test_dump_or_restore_are_able_to_serialize_or_unserialize_a_simple_key(r: ValkeyTestClient) -> None:
    """
    test {DUMP / RESTORE are able to serialize / unserialize a simple key} {
        r set foo bar
        set encoded [r dump foo]
        r del foo
        list [r exists foo] [r restore foo 0 $encoded] [r ttl foo] [r get foo]
    } {0 OK -1 bar}
    """
    r.run("set", "foo", "bar")
    encoded = r.run("dump", "foo")
    r.run("del", "foo")
    assert [
        r.run("exists", "foo"),
        r.run("restore", "foo", 0, encoded),
        r.run("ttl", "foo"),
        r.run("get", "foo"),
    ] == "0 OK -1 bar"


def test_restore_can_set_an_arbitrary_expire_to_the_materialized_key(r: ValkeyTestClient) -> None:
    """
    test {RESTORE can set an arbitrary expire to the materialized key} {
        r set foo bar
        set encoded [r dump foo]
        r del foo
        r restore foo 5000 $encoded
        set ttl [r pttl foo]
        assert_range $ttl 3000 5000
        r get foo
    } {bar}
    """
    r.run("set", "foo", "bar")
    encoded = r.run("dump", "foo")
    r.run("del", "foo")
    r.run("restore", "foo", 5000, encoded)
    ttl = r.run("pttl", "foo")
    assert_range(ttl, 3000, 5000)
    assert r.run("get", "foo") == "bar"


def test_restore_can_set_an_expire_that_overflows_a_32_bit_integer(r: ValkeyTestClient) -> None:
    """
    test {RESTORE can set an expire that overflows a 32 bit integer} {
        r set foo bar
        set encoded [r dump foo]
        r del foo
        r restore foo 2569591501 $encoded
        set ttl [r pttl foo]
        assert_range $ttl (2569591501-3000) 2569591501
        r get foo
    } {bar}
    """
    r.run("set", "foo", "bar")
    encoded = r.run("dump", "foo")
    r.run("del", "foo")
    r.run("restore", "foo", 2569591501, encoded)
    ttl = r.run("pttl", "foo")
    assert_range(ttl, "(2569591501-3000)", 2569591501)
    assert r.run("get", "foo") == "bar"


def test_restore_can_set_an_absolute_expire(r: ValkeyTestClient) -> None:
    """
    test {RESTORE can set an absolute expire} {
        r set foo bar
        set encoded [r dump foo]
        r del foo
        set now [clock milliseconds]
        r restore foo [expr $now+3000] $encoded absttl
        set ttl [r pttl foo]
        assert_range $ttl 2000 3100
        r get foo
    } {bar}
    """
    r.run("set", "foo", "bar")
    encoded = r.run("dump", "foo")
    r.run("del", "foo")
    now = clock("milliseconds")
    r.run("restore", "foo", expr(now, 3000), encoded, "absttl")
    ttl = r.run("pttl", "foo")
    assert_range(ttl, 2000, 3100)
    assert r.run("get", "foo") == "bar"


def test_restore_with_absttl_in_the_past(r: ValkeyTestClient) -> None:
    """
    test {RESTORE with ABSTTL in the past} {
        r set foo bar
        set encoded [r dump foo]
        set now [clock milliseconds]
        r debug set-active-expire 0
        r restore foo [expr $now-3000] $encoded absttl REPLACE
        catch {r debug object foo} e
        r debug set-active-expire 1
        set e
    } {ERR no such key} {needs:debug}
    """
    r.run("set", "foo", "bar")
    encoded = r.run("dump", "foo")
    now = clock("milliseconds")
    r.run("debug", "set-active-expire", 0)
    r.run("restore", "foo", expr(now, -3000), encoded, "absttl", "REPLACE")
    try:
        e = r.run("debug", "object", "foo")
    except Exception as _catch_err:
        e = str(_catch_err)
    r.run("debug", "set-active-expire", 1)
    assert e == "ERR no such key"


def test_restore_can_set_lru(r: ValkeyTestClient) -> None:
    """
    test {RESTORE can set LRU} {
        r set foo bar
        set encoded [r dump foo]
        r del foo
        r config set maxmemory-policy allkeys-lru
        r restore foo 0 $encoded idletime 1000
        set idle [r object idletime foo]
        assert {$idle >= 1000 && $idle <= 1010}
        assert_equal [r get foo] {bar}
        r config set maxmemory-policy noeviction
    } {OK} {needs:config-maxmemory}
    """
    r.run("set", "foo", "bar")
    encoded = r.run("dump", "foo")
    r.run("del", "foo")
    r.run("config", "set", "maxmemory-policy", "allkeys-lru")
    r.run("restore", "foo", 0, encoded, "idletime", 1000)
    idle = r.run("object", "idletime", "foo")
    assert (idle >= 1000) and (idle <= 1010)
    assert r.run("get", "foo") == "bar"
    assert r.run("config", "set", "maxmemory-policy", "noeviction") == "OK"


def test_restore_can_set_lfu(r: ValkeyTestClient) -> None:
    """
    test {RESTORE can set LFU} {
        r set foo bar
        set encoded [r dump foo]
        r del foo
        r config set maxmemory-policy allkeys-lfu
        r restore foo 0 $encoded freq 100
        set freq [r object freq foo]
        assert {$freq == 100}
        r get foo
        assert_equal [r get foo] {bar}
        r config set maxmemory-policy noeviction
    } {OK} {needs:config-maxmemory}
    """
    r.run("set", "foo", "bar")
    encoded = r.run("dump", "foo")
    r.run("del", "foo")
    r.run("config", "set", "maxmemory-policy", "allkeys-lfu")
    r.run("restore", "foo", 0, encoded, "freq", 100)
    freq = r.run("object", "freq", "foo")
    assert freq == 100
    r.run("get", "foo")
    assert r.run("get", "foo") == "bar"
    assert r.run("config", "set", "maxmemory-policy", "noeviction") == "OK"


def test_restore_returns_an_error_of_the_key_already_exists(r: ValkeyTestClient) -> None:
    """
    test {RESTORE returns an error of the key already exists} {
        r set foo bar
        set e {}
        catch {r restore foo 0 "..."} e
        set e
    } {*BUSYKEY*}
    """
    r.run("set", "foo", "bar")
    e = ""
    try:
        e = r.run("restore", "foo", 0, "...")
    except Exception as _catch_err:
        e = str(_catch_err)
    assert fnmatch(str(e), "*BUSYKEY*")


def test_restore_can_overwrite_an_existing_key_with_replace(r: ValkeyTestClient) -> None:
    """
    test {RESTORE can overwrite an existing key with REPLACE} {
        r set foo bar1
        set encoded1 [r dump foo]
        r set foo bar2
        set encoded2 [r dump foo]
        r del foo
        r restore foo 0 $encoded1
        r restore foo 0 $encoded2 replace
        r get foo
    } {bar2}
    """
    r.run("set", "foo", "bar1")
    encoded1 = r.run("dump", "foo")
    r.run("set", "foo", "bar2")
    encoded2 = r.run("dump", "foo")
    r.run("del", "foo")
    r.run("restore", "foo", 0, encoded1)
    r.run("restore", "foo", 0, encoded2, "replace")
    assert r.run("get", "foo") == "bar2"


def test_restore_can_detect_a_syntax_error_for_unrecognized_options(r: ValkeyTestClient) -> None:
    """
    test {RESTORE can detect a syntax error for unrecognized options} {
        catch {r restore foo 0 "..." invalid-option} e
        set e
    } {*syntax*}
    """
    try:
        e = r.run("restore", "foo", 0, "...", "invalid-option")
    except Exception as _catch_err:
        e = str(_catch_err)
    assert fnmatch(str(e), "*syntax*")


def test_restore_should_not_store_key_that_are_already_expired_with_replace_will_propagate_it_as_del_or_unlink(
    r: ValkeyTestClient,
) -> None:
    """
    test {RESTORE should not store key that are already expired, with REPLACE will propagate it as DEL or UNLINK} {
        r del key1{t} key2{t}
        r set key1{t} value2
        r lpush key2{t} 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30 31 32 33 34 35 36 37 38 39 40 41 42 43 44 45 46 47 48 49 50 51 52 53 54 55 56 57 58 59 60 61 62 63 64 65

        r set key{t} value
        set encoded [r dump key{t}]
        set now [clock milliseconds]

        set repl [attach_to_replication_stream]

        # Keys that have expired will not be stored.
        r config set lazyfree-lazy-server-del no
        assert_equal {OK} [r restore key1{t} [expr $now-5000] $encoded replace absttl]
        r config set lazyfree-lazy-server-del yes
        assert_equal {OK} [r restore key2{t} [expr $now-5000] $encoded replace absttl]
        assert_equal {0} [r exists key1{t} key2{t}]

        # Verify the propagate of DEL and UNLINK.
        assert_replication_stream $repl {
            {select *}
            {del key1{t}}
            {unlink key2{t}}
        }

        close_replication_stream $repl
    } {} {needs:repl}
    """
    r.run("del", "key1{t}", "key2{t}")
    r.run("set", "key1{t}", "value2")
    r.run(
        "lpush",
        "key2{t}",
        1,
        2,
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
        34,
        35,
        36,
        37,
        38,
        39,
        40,
        41,
        42,
        43,
        44,
        45,
        46,
        47,
        48,
        49,
        50,
        51,
        52,
        53,
        54,
        55,
        56,
        57,
        58,
        59,
        60,
        61,
        62,
        63,
        64,
        65,
    )
    r.run("set", "key{t}", "value")
    encoded = r.run("dump", "key{t}")
    now = clock("milliseconds")
    repl = attach_to_replication_stream()
    r.run("config", "set", "lazyfree-lazy-server-del", "no")
    assert "OK" == r.run("restore", "key1{t}", expr(now, -5000), encoded, "replace", "absttl")
    r.run("config", "set", "lazyfree-lazy-server-del", "yes")
    assert "OK" == r.run("restore", "key2{t}", expr(now, -5000), encoded, "replace", "absttl")
    assert "0" == r.run("exists", "key1{t}", "key2{t}")
    assert_replication_stream(
        repl, "            {select *}\n            {del key1{t}}\n            {unlink key2{t}}\n        "
    )
    close_replication_stream(repl)


def test_restore_key_with_future_rdb_version_strict_version_check(r: ValkeyTestClient) -> None:
    """
    test {RESTORE key with future RDB version, strict version check} {
        #              str len  "bar"      RDB 222 CRC64 checksum
        #               |   |     |         |       |
        set bar_dump "\x00\x03\x62\x61\x72\xde\x00\x0fYUza\xd3\xec\xe0"
        assert_error {ERR DUMP payload version or checksum are wrong} {r restore foo 0 $bar_dump replace}
    }
    """
    bar_dump = "\x00\x03\x62\x61\x72\xde\x00\x0fYUza\xd3\xec\xe0"
    with pytest.raises(Exception, match="ERR\\ DUMP\\ payload\\ version\\ or\\ checksum\\ are\\ wrong"):
        r.run("restore", "foo", 0, bar_dump, "replace")


def test_restore_key_with_future_rdb_version_relaxed_version_check(r: ValkeyTestClient) -> None:
    """
    test {RESTORE key with future RDB version, relaxed version check} {
        r config set rdb-version-check relaxed
        #               |type|len|           |  RDB  |      CRC64        |
        #               |str | 3 |   "bar"   |  222  |     checksum      |
        r restore foo 0 "\x00\x03\x62\x61\x72\xde\x00\x0fYUza\xd3\xec\xe0" replace
        r config set rdb-version-check strict
        assert_equal {bar} [r get foo]
    }
    """
    r.run("config", "set", "rdb-version-check", "relaxed")
    r.run("restore", "foo", 0, "\x00\x03\x62\x61\x72\xde\x00\x0fYUza\xd3\xec\xe0", "replace")
    r.run("config", "set", "rdb-version-check", "strict")
    assert "bar" == r.run("get", "foo")


def test_dump_of_non_existing_key_returns_nil(r: ValkeyTestClient) -> None:
    """
    test {DUMP of non existing key returns nil} {
        r dump nonexisting_key
    } {}
    """
    r.run("dump", "nonexisting_key")


def test_migrate_is_caching_connections(r: ValkeyTestClient) -> None:
    """
    test {MIGRATE is caching connections} {
        # Note, we run this as first test so that the connection cache
        # is empty.
        set first [srv 0 client]
        r set key "Some Value"
        start_server {tags {"repl"}} {
            set second [srv 0 client]
            set second_host [srv 0 host]
            set second_port [srv 0 port]

            assert_match {*migrate_cached_sockets:0*} [r -1 info]
            r -1 migrate $second_host $second_port key $db 1000
            assert_match {*migrate_cached_sockets:1*} [r -1 info]
        }
    } {} {external:skip}
    """
    first = srv(0, "client")
    r.run("set", "key", "Some Value")
    start_server(
        'tags {"repl"}',
        "            set second [srv 0 client]\n            set second_host [srv 0 host]\n            set second_port [srv 0 port]\n\n            assert_match {*migrate_cached_sockets:0*} [r -1 info]\n            r -1 migrate $second_host $second_port key $db 1000\n            assert_match {*migrate_cached_sockets:1*} [r -1 info]\n        ",
    )


def test_migrate_cached_connections_are_released_after_some_time(r: ValkeyTestClient) -> None:
    """
    test {MIGRATE cached connections are released after some time} {
        after 15000
        assert_match {*migrate_cached_sockets:0*} [r info]
    }
    """
    time.sleep(15000 / 1000)
    assert fnmatch(str(r.run("info")), "*migrate_cached_sockets:0*")


def test_migrate_is_able_to_migrate_a_key_between_two_instances(r: ValkeyTestClient) -> None:
    """
    test {MIGRATE is able to migrate a key between two instances} {
        set first [srv 0 client]
        r set key "Some Value"
        start_server {tags {"repl"}} {
            set second [srv 0 client]
            set second_host [srv 0 host]
            set second_port [srv 0 port]

            assert {[$first exists key] == 1}
            assert {[$second exists key] == 0}
            set ret [r -1 migrate $second_host $second_port key $db 5000]
            assert {$ret eq {OK}}
            assert {[$first exists key] == 0}
            assert {[$second exists key] == 1}
            assert {[$second get key] eq {Some Value}}
            assert {[$second ttl key] == -1}
        }
    } {} {external:skip}
    """
    first = srv(0, "client")
    r.run("set", "key", "Some Value")
    start_server(
        'tags {"repl"}',
        "            set second [srv 0 client]\n            set second_host [srv 0 host]\n            set second_port [srv 0 port]\n\n            assert {[$first exists key] == 1}\n            assert {[$second exists key] == 0}\n            set ret [r -1 migrate $second_host $second_port key $db 5000]\n            assert {$ret eq {OK}}\n            assert {[$first exists key] == 0}\n            assert {[$second exists key] == 1}\n            assert {[$second get key] eq {Some Value}}\n            assert {[$second ttl key] == -1}\n        ",
    )


def test_migrate_is_able_to_copy_a_key_between_two_instances(r: ValkeyTestClient) -> None:
    """
    test {MIGRATE is able to copy a key between two instances} {
        set first [srv 0 client]
        r del list
        r lpush list a b c d
        start_server {tags {"repl"}} {
            set second [srv 0 client]
            set second_host [srv 0 host]
            set second_port [srv 0 port]

            assert {[$first exists list] == 1}
            assert {[$second exists list] == 0}
            set ret [r -1 migrate $second_host $second_port list $db 5000 copy]
            assert {$ret eq {OK}}
            assert {[$first exists list] == 1}
            assert {[$second exists list] == 1}
            assert {[$first lrange list 0 -1] eq [$second lrange list 0 -1]}
        }
    } {} {external:skip}
    """
    first = srv(0, "client")
    r.run("del", "list")
    r.run("lpush", "list", "a", "b", "c", "d")
    start_server(
        'tags {"repl"}',
        "            set second [srv 0 client]\n            set second_host [srv 0 host]\n            set second_port [srv 0 port]\n\n            assert {[$first exists list] == 1}\n            assert {[$second exists list] == 0}\n            set ret [r -1 migrate $second_host $second_port list $db 5000 copy]\n            assert {$ret eq {OK}}\n            assert {[$first exists list] == 1}\n            assert {[$second exists list] == 1}\n            assert {[$first lrange list 0 -1] eq [$second lrange list 0 -1]}\n        ",
    )


def test_migrate_will_not_overwrite_existing_keys_unless_replace_is_used(r: ValkeyTestClient) -> None:
    """
    test {MIGRATE will not overwrite existing keys, unless REPLACE is used} {
        set first [srv 0 client]
        r del list
        r lpush list a b c d
        start_server {tags {"repl"}} {
            set second [srv 0 client]
            set second_host [srv 0 host]
            set second_port [srv 0 port]

            assert {[$first exists list] == 1}
            assert {[$second exists list] == 0}
            $second set list somevalue
            catch {r -1 migrate $second_host $second_port list $db 5000 copy} e
            assert_match {ERR*} $e
            set ret [r -1 migrate $second_host $second_port list $db 5000 copy replace]
            assert {$ret eq {OK}}
            assert {[$first exists list] == 1}
            assert {[$second exists list] == 1}
            assert {[$first lrange list 0 -1] eq [$second lrange list 0 -1]}
        }
    } {} {external:skip}
    """
    first = srv(0, "client")
    r.run("del", "list")
    r.run("lpush", "list", "a", "b", "c", "d")
    start_server(
        'tags {"repl"}',
        "            set second [srv 0 client]\n            set second_host [srv 0 host]\n            set second_port [srv 0 port]\n\n            assert {[$first exists list] == 1}\n            assert {[$second exists list] == 0}\n            $second set list somevalue\n            catch {r -1 migrate $second_host $second_port list $db 5000 copy} e\n            assert_match {ERR*} $e\n            set ret [r -1 migrate $second_host $second_port list $db 5000 copy replace]\n            assert {$ret eq {OK}}\n            assert {[$first exists list] == 1}\n            assert {[$second exists list] == 1}\n            assert {[$first lrange list 0 -1] eq [$second lrange list 0 -1]}\n        ",
    )


def test_migrate_propagates_ttl_correctly(r: ValkeyTestClient) -> None:
    """
    test {MIGRATE propagates TTL correctly} {
        set first [srv 0 client]
        r set key "Some Value"
        start_server {tags {"repl"}} {
            set second [srv 0 client]
            set second_host [srv 0 host]
            set second_port [srv 0 port]

            assert {[$first exists key] == 1}
            assert {[$second exists key] == 0}
            $first expire key 10
            set ret [r -1 migrate $second_host $second_port key $db 5000]
            assert {$ret eq {OK}}
            assert {[$first exists key] == 0}
            assert {[$second exists key] == 1}
            assert {[$second get key] eq {Some Value}}
            assert {[$second ttl key] >= 7 && [$second ttl key] <= 10}
        }
    } {} {external:skip}
    """
    first = srv(0, "client")
    r.run("set", "key", "Some Value")
    start_server(
        'tags {"repl"}',
        "            set second [srv 0 client]\n            set second_host [srv 0 host]\n            set second_port [srv 0 port]\n\n            assert {[$first exists key] == 1}\n            assert {[$second exists key] == 0}\n            $first expire key 10\n            set ret [r -1 migrate $second_host $second_port key $db 5000]\n            assert {$ret eq {OK}}\n            assert {[$first exists key] == 0}\n            assert {[$second exists key] == 1}\n            assert {[$second get key] eq {Some Value}}\n            assert {[$second ttl key] >= 7 && [$second ttl key] <= 10}\n        ",
    )


def test_migrate_can_correctly_transfer_large_values(r: ValkeyTestClient) -> None:
    """
    test {MIGRATE can correctly transfer large values} {
        set first [srv 0 client]
        r del key
        for {set j 0} {$j < 40000} {incr j} {
            r rpush key 1 2 3 4 5 6 7 8 9 10
            r rpush key "item 1" "item 2" "item 3" "item 4" "item 5" \
                        "item 6" "item 7" "item 8" "item 9" "item 10"
        }
        assert {[string length [r dump key]] > (1024*64)}
        start_server {tags {"repl"}} {
            set second [srv 0 client]
            set second_host [srv 0 host]
            set second_port [srv 0 port]

            assert {[$first exists key] == 1}
            assert {[$second exists key] == 0}
            set ret [r -1 migrate $second_host $second_port key $db 10000]
            assert {$ret eq {OK}}
            assert {[$first exists key] == 0}
            assert {[$second exists key] == 1}
            assert {[$second ttl key] == -1}
            assert {[$second llen key] == 40000*20}
        }
    } {} {external:skip}
    """
    first = srv(0, "client")
    r.run("del", "key")
    j = 0
    while j < 40000:
        r.run("rpush", "key", 1, 2, 3, 4, 5, 6, 7, 8, 9, 10)
        r.run(
            "rpush",
            "key",
            "item 1",
            "item 2",
            "item 3",
            "item 4",
            "item 5",
            "item 6",
            "item 7",
            "item 8",
            "item 9",
            "item 10",
        )
        j += 1
    assert_("[string length [r dump key]] > (1024*64)")
    start_server(
        'tags {"repl"}',
        "            set second [srv 0 client]\n            set second_host [srv 0 host]\n            set second_port [srv 0 port]\n\n            assert {[$first exists key] == 1}\n            assert {[$second exists key] == 0}\n            set ret [r -1 migrate $second_host $second_port key $db 10000]\n            assert {$ret eq {OK}}\n            assert {[$first exists key] == 0}\n            assert {[$second exists key] == 1}\n            assert {[$second ttl key] == -1}\n            assert {[$second llen key] == 40000*20}\n        ",
    )


def test_migrate_can_correctly_transfer_hashes(r: ValkeyTestClient) -> None:
    """
    test {MIGRATE can correctly transfer hashes} {
        set first [srv 0 client]
        r del key
        r hmset key field1 "item 1" field2 "item 2" field3 "item 3" \
                    field4 "item 4" field5 "item 5" field6 "item 6"
        start_server {tags {"repl"}} {
            set second [srv 0 client]
            set second_host [srv 0 host]
            set second_port [srv 0 port]

            assert {[$first exists key] == 1}
            assert {[$second exists key] == 0}
            set ret [r -1 migrate $second_host $second_port key $db 10000]
            assert {$ret eq {OK}}
            assert {[$first exists key] == 0}
            assert {[$second exists key] == 1}
            assert {[$second ttl key] == -1}
        }
    } {} {external:skip}
    """
    first = srv(0, "client")
    r.run("del", "key")
    r.run(
        "hmset",
        "key",
        "field1",
        "item 1",
        "field2",
        "item 2",
        "field3",
        "item 3",
        "field4",
        "item 4",
        "field5",
        "item 5",
        "field6",
        "item 6",
    )
    start_server(
        'tags {"repl"}',
        "            set second [srv 0 client]\n            set second_host [srv 0 host]\n            set second_port [srv 0 port]\n\n            assert {[$first exists key] == 1}\n            assert {[$second exists key] == 0}\n            set ret [r -1 migrate $second_host $second_port key $db 10000]\n            assert {$ret eq {OK}}\n            assert {[$first exists key] == 0}\n            assert {[$second exists key] == 1}\n            assert {[$second ttl key] == -1}\n        ",
    )


def test_migrate_timeout_actually_works(r: ValkeyTestClient) -> None:
    """
    test {MIGRATE timeout actually works} {
        set first [srv 0 client]
        r set key "Some Value"
        start_server {tags {"repl"}} {
            set second [srv 0 client]
            set second_host [srv 0 host]
            set second_port [srv 0 port]

            assert {[$first exists key] == 1}
            assert {[$second exists key] == 0}

            set rd [valkey_deferring_client]
            $rd debug sleep 1.0 ; # Make second server unable to reply.
            after 100; # wait to make sure DEBUG command was executed.
            set e {}
            catch {r -1 migrate $second_host $second_port key $db 500} e
            assert_match {IOERR*} $e
        }
    } {} {external:skip}
    """
    first = srv(0, "client")
    r.run("set", "key", "Some Value")
    start_server(
        'tags {"repl"}',
        "            set second [srv 0 client]\n            set second_host [srv 0 host]\n            set second_port [srv 0 port]\n\n            assert {[$first exists key] == 1}\n            assert {[$second exists key] == 0}\n\n            set rd [valkey_deferring_client]\n            $rd debug sleep 1.0 ; # Make second server unable to reply.\n            after 100; # wait to make sure DEBUG command was executed.\n            set e {}\n            catch {r -1 migrate $second_host $second_port key $db 500} e\n            assert_match {IOERR*} $e\n        ",
    )


def test_migrate_can_migrate_multiple_keys_at_once(r: ValkeyTestClient) -> None:
    """
    test {MIGRATE can migrate multiple keys at once} {
        set first [srv 0 client]
        r set key1 "v1"
        r set key2 "v2"
        r set key3 "v3"
        start_server {tags {"repl"}} {
            set second [srv 0 client]
            set second_host [srv 0 host]
            set second_port [srv 0 port]

            assert {[$first exists key1] == 1}
            assert {[$second exists key1] == 0}
            set ret [r -1 migrate $second_host $second_port "" $db 5000 keys key1 key2 key3]
            assert {$ret eq {OK}}
            assert {[$first exists key1] == 0}
            assert {[$first exists key2] == 0}
            assert {[$first exists key3] == 0}
            assert {[$second get key1] eq {v1}}
            assert {[$second get key2] eq {v2}}
            assert {[$second get key3] eq {v3}}
        }
    } {} {external:skip}
    """
    first = srv(0, "client")
    r.run("set", "key1", "v1")
    r.run("set", "key2", "v2")
    r.run("set", "key3", "v3")
    start_server(
        'tags {"repl"}',
        '            set second [srv 0 client]\n            set second_host [srv 0 host]\n            set second_port [srv 0 port]\n\n            assert {[$first exists key1] == 1}\n            assert {[$second exists key1] == 0}\n            set ret [r -1 migrate $second_host $second_port "" $db 5000 keys key1 key2 key3]\n            assert {$ret eq {OK}}\n            assert {[$first exists key1] == 0}\n            assert {[$first exists key2] == 0}\n            assert {[$first exists key3] == 0}\n            assert {[$second get key1] eq {v1}}\n            assert {[$second get key2] eq {v2}}\n            assert {[$second get key3] eq {v3}}\n        ',
    )


@pytest.mark.xfail(reason="not implemented")
def test_migrate_with_multiple_keys_must_have_empty_key_arg(r: ValkeyTestClient) -> None:
    """
    test {MIGRATE with multiple keys must have empty key arg} {
        catch {r MIGRATE 127.0.0.1 6379 NotEmpty $db 5000 keys a b c} e
        set e
    } {*empty string*} {external:skip}
    """
    catch("r MIGRATE 127.0.0.1 6379 NotEmpty $db 5000 keys a b c", "e")
    # TODO: set e
    assert False


def test_migrate_with_multiple_keys_migrate_just_existing_ones(r: ValkeyTestClient) -> None:
    """
    test {MIGRATE with multiple keys migrate just existing ones} {
        set first [srv 0 client]
        r set key1 "v1"
        r set key2 "v2"
        r set key3 "v3"
        start_server {tags {"repl"}} {
            set second [srv 0 client]
            set second_host [srv 0 host]
            set second_port [srv 0 port]

            set ret [r -1 migrate $second_host $second_port "" $db 5000 keys nokey-1 nokey-2 nokey-2]
            assert {$ret eq {NOKEY}}

            assert {[$first exists key1] == 1}
            assert {[$second exists key1] == 0}
            set ret [r -1 migrate $second_host $second_port "" $db 5000 keys nokey-1 key1 nokey-2 key2 nokey-3 key3]
            assert {$ret eq {OK}}
            assert {[$first exists key1] == 0}
            assert {[$first exists key2] == 0}
            assert {[$first exists key3] == 0}
            assert {[$second get key1] eq {v1}}
            assert {[$second get key2] eq {v2}}
            assert {[$second get key3] eq {v3}}
        }
    } {} {external:skip}
    """
    first = srv(0, "client")
    r.run("set", "key1", "v1")
    r.run("set", "key2", "v2")
    r.run("set", "key3", "v3")
    start_server(
        'tags {"repl"}',
        '            set second [srv 0 client]\n            set second_host [srv 0 host]\n            set second_port [srv 0 port]\n\n            set ret [r -1 migrate $second_host $second_port "" $db 5000 keys nokey-1 nokey-2 nokey-2]\n            assert {$ret eq {NOKEY}}\n\n            assert {[$first exists key1] == 1}\n            assert {[$second exists key1] == 0}\n            set ret [r -1 migrate $second_host $second_port "" $db 5000 keys nokey-1 key1 nokey-2 key2 nokey-3 key3]\n            assert {$ret eq {OK}}\n            assert {[$first exists key1] == 0}\n            assert {[$first exists key2] == 0}\n            assert {[$first exists key3] == 0}\n            assert {[$second get key1] eq {v1}}\n            assert {[$second get key2] eq {v2}}\n            assert {[$second get key3] eq {v3}}\n        ',
    )


def test_migrate_with_multiple_keys_stress_command_rewriting(r: ValkeyTestClient) -> None:
    """
    test {MIGRATE with multiple keys: stress command rewriting} {
        set first [srv 0 client]
        r flushdb
        r mset a 1 b 2 c 3 d 4 c 5 e 6 f 7 g 8 h 9 i 10 l 11 m 12 n 13 o 14 p 15 q 16
        start_server {tags {"repl"}} {
            set second [srv 0 client]
            set second_host [srv 0 host]
            set second_port [srv 0 port]

            set ret [r -1 migrate $second_host $second_port "" $db 5000 keys a b c d e f g h i l m n o p q]

            assert {[$first dbsize] == 0}
            assert {[$second dbsize] == 15}
        }
    } {} {external:skip}
    """
    first = srv(0, "client")
    r.run("flushdb")
    r.run(
        "mset",
        "a",
        1,
        "b",
        2,
        "c",
        3,
        "d",
        4,
        "c",
        5,
        "e",
        6,
        "f",
        7,
        "g",
        8,
        "h",
        9,
        "i",
        10,
        "l",
        11,
        "m",
        12,
        "n",
        13,
        "o",
        14,
        "p",
        15,
        "q",
        16,
    )
    start_server(
        'tags {"repl"}',
        '            set second [srv 0 client]\n            set second_host [srv 0 host]\n            set second_port [srv 0 port]\n\n            set ret [r -1 migrate $second_host $second_port "" $db 5000 keys a b c d e f g h i l m n o p q]\n\n            assert {[$first dbsize] == 0}\n            assert {[$second dbsize] == 15}\n        ',
    )


def test_migrate_with_multiple_keys_delete_just_ack_keys(r: ValkeyTestClient) -> None:
    """
    test {MIGRATE with multiple keys: delete just ack keys} {
        set first [srv 0 client]
        r flushdb
        r mset a 1 b 2 c 3 d 4 c 5 e 6 f 7 g 8 h 9 i 10 l 11 m 12 n 13 o 14 p 15 q 16
        start_server {tags {"repl"}} {
            set second [srv 0 client]
            set second_host [srv 0 host]
            set second_port [srv 0 port]

            $second mset c _ d _; # Two busy keys and no REPLACE used

            catch {r -1 migrate $second_host $second_port "" $db 5000 keys a b c d e f g h i l m n o p q} e

            assert {[$first dbsize] == 2}
            assert {[$second dbsize] == 15}
            assert {[$first exists c] == 1}
            assert {[$first exists d] == 1}
        }
    } {} {external:skip}
    """
    first = srv(0, "client")
    r.run("flushdb")
    r.run(
        "mset",
        "a",
        1,
        "b",
        2,
        "c",
        3,
        "d",
        4,
        "c",
        5,
        "e",
        6,
        "f",
        7,
        "g",
        8,
        "h",
        9,
        "i",
        10,
        "l",
        11,
        "m",
        12,
        "n",
        13,
        "o",
        14,
        "p",
        15,
        "q",
        16,
    )
    start_server(
        'tags {"repl"}',
        '            set second [srv 0 client]\n            set second_host [srv 0 host]\n            set second_port [srv 0 port]\n\n            $second mset c _ d _; # Two busy keys and no REPLACE used\n\n            catch {r -1 migrate $second_host $second_port "" $db 5000 keys a b c d e f g h i l m n o p q} e\n\n            assert {[$first dbsize] == 2}\n            assert {[$second dbsize] == 15}\n            assert {[$first exists c] == 1}\n            assert {[$first exists d] == 1}\n        ',
    )


def test_migrate_auth_correct_and_wrong_password_cases(r: ValkeyTestClient) -> None:
    """
    test {MIGRATE AUTH: correct and wrong password cases} {
        set first [srv 0 client]
        r del list
        r lpush list a b c d
        start_server {tags {"repl"}} {
            set second [srv 0 client]
            set second_host [srv 0 host]
            set second_port [srv 0 port]
            $second config set requirepass foobar
            $second auth foobar

            assert {[$first exists list] == 1}
            assert {[$second exists list] == 0}
            set ret [r -1 migrate $second_host $second_port list $db 5000 AUTH foobar]
            assert {$ret eq {OK}}
            assert {[$second exists list] == 1}
            assert {[$second lrange list 0 -1] eq {d c b a}}

            r -1 lpush list a b c d
            $second config set requirepass foobar2
            catch {r -1 migrate $second_host $second_port list $db 5000 AUTH foobar} err
            assert_match {*WRONGPASS*} $err
        }
    } {} {external:skip}
    """
    first = srv(0, "client")
    r.run("del", "list")
    r.run("lpush", "list", "a", "b", "c", "d")
    start_server(
        'tags {"repl"}',
        "            set second [srv 0 client]\n            set second_host [srv 0 host]\n            set second_port [srv 0 port]\n            $second config set requirepass foobar\n            $second auth foobar\n\n            assert {[$first exists list] == 1}\n            assert {[$second exists list] == 0}\n            set ret [r -1 migrate $second_host $second_port list $db 5000 AUTH foobar]\n            assert {$ret eq {OK}}\n            assert {[$second exists list] == 1}\n            assert {[$second lrange list 0 -1] eq {d c b a}}\n\n            r -1 lpush list a b c d\n            $second config set requirepass foobar2\n            catch {r -1 migrate $second_host $second_port list $db 5000 AUTH foobar} err\n            assert_match {*WRONGPASS*} $err\n        ",
    )


# --- stubs for unimplemented TCL helpers ---


def assert_(*args):
    raise NotImplementedError("assert_")


def assert_range(*args):
    raise NotImplementedError("assert_range")


def assert_replication_stream(*args):
    raise NotImplementedError("assert_replication_stream")


def attach_to_replication_stream(*args):
    raise NotImplementedError("attach_to_replication_stream")


def catch(*args):
    raise NotImplementedError("catch")


def clock(*args):
    raise NotImplementedError("clock")


def close_replication_stream(*args):
    raise NotImplementedError("close_replication_stream")


def expr(*args):
    raise NotImplementedError("expr")


def srv(*args):
    raise NotImplementedError("srv")


def start_server(*args):
    raise NotImplementedError("start_server")
