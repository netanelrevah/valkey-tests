# ruff: noqa: ANN002, ANN201

import pytest

from tests.valkey_test_client import ValkeyTestClient

"""
set testmodule file normalize tests/modules/commandfilter.so
"""

pytestmark = [pytest.mark.modules]


def test_retain_a_command_filter_argument(r: ValkeyTestClient) -> None:
    """
    test {Retain a command filter argument} {
        # Retain an argument now. Later we'll try to re-read it and make sure
        # it is not corrupt and that valgrind does not complain.
        r rpush some-list @retain my-retained-string
        r commandfilter.retained
    } {my-retained-string}
    """
    r.run("rpush", "some-list", "@retain", "my-retained-string")
    assert r.run("commandfilter.retained") == "my-retained-string"


def test_command_filter_handles_redirected_commands(r: ValkeyTestClient) -> None:
    """
    test {Command Filter handles redirected commands} {
        r set mykey @log
        r lrange log-key 0 -1
    } "{set mykey @log}"
    """
    r.run("set", "mykey", "@log")
    r.run("lrange", "log-key", 0, -1)


def test_command_filter_can_call_redismodule_commandfilterargdelete(r: ValkeyTestClient) -> None:
    """
    test {Command Filter can call RedisModule_CommandFilterArgDelete} {
        r rpush mylist elem1 @delme elem2
        r lrange mylist 0 -1
    } {elem1 elem2}
    """
    r.run("rpush", "mylist", "elem1", "@delme", "elem2")
    assert r.run("lrange", "mylist", 0, -1) == "elem1 elem2"


def test_command_filter_can_call_redismodule_commandfilterarginsert(r: ValkeyTestClient) -> None:
    """
    test {Command Filter can call RedisModule_CommandFilterArgInsert} {
        r del mylist
        r rpush mylist elem1 @insertbefore elem2 @insertafter elem3
        r lrange mylist 0 -1
    } {elem1 --inserted-before-- @insertbefore elem2 @insertafter --inserted-after-- elem3}
    """
    r.run("del", "mylist")
    r.run("rpush", "mylist", "elem1", "@insertbefore", "elem2", "@insertafter", "elem3")
    assert (
        r.run("lrange", "mylist", 0, -1)
        == "elem1 --inserted-before-- @insertbefore elem2 @insertafter --inserted-after-- elem3"
    )


def test_command_filter_can_call_redismodule_commandfilterargreplace(r: ValkeyTestClient) -> None:
    """
    test {Command Filter can call RedisModule_CommandFilterArgReplace} {
        r del mylist
        r rpush mylist elem1 @replaceme elem2
        r lrange mylist 0 -1
    } {elem1 --replaced-- elem2}
    """
    r.run("del", "mylist")
    r.run("rpush", "mylist", "elem1", "@replaceme", "elem2")
    assert r.run("lrange", "mylist", 0, -1) == "elem1 --replaced-- elem2"


def test_command_filter_applies_on_rm_call_commands(r: ValkeyTestClient) -> None:
    """
    test {Command Filter applies on RM_Call() commands} {
        r del log-key
        r commandfilter.ping
        r lrange log-key 0 -1
    } "{ping @log}"
    """
    r.run("del", "log-key")
    r.run("commandfilter.ping")
    r.run("lrange", "log-key", 0, -1)


def test_command_filter_applies_on_lua_redis_call(r: ValkeyTestClient) -> None:
    """
    test {Command Filter applies on Lua redis.call()} {
        r del log-key
        r eval "redis.call('ping', '@log')" 0
        r lrange log-key 0 -1
    } "{ping @log}"
    """
    r.run("del", "log-key")
    r.run("eval", "redis.call('ping', '@log')", 0)
    r.run("lrange", "log-key", 0, -1)


def test_command_filter_applies_on_lua_redis_call_that_calls_a_module(r: ValkeyTestClient) -> None:
    """
    test {Command Filter applies on Lua redis.call() that calls a module} {
        r del log-key
        r eval "redis.call('commandfilter.ping')" 0
        r lrange log-key 0 -1
    } "{ping @log}"
    """
    r.run("del", "log-key")
    r.run("eval", "redis.call('commandfilter.ping')", 0)
    r.run("lrange", "log-key", 0, -1)


def test_command_filter_strings_can_be_retained(r: ValkeyTestClient) -> None:
    """
    test {Command Filter strings can be retained} {
        r commandfilter.retained
    } {my-retained-string}
    """
    assert r.run("commandfilter.retained") == "my-retained-string"


def test_command_filter_is_unregistered_implicitly_on_module_unload(r: ValkeyTestClient) -> None:
    """
    test {Command Filter is unregistered implicitly on module unload} {
        r del log-key
        r module unload commandfilter
        r set mykey @log
        r lrange log-key 0 -1
    } {}
    """
    r.run("del", "log-key")
    r.run("module", "unload", "commandfilter")
    r.run("set", "mykey", "@log")
    r.run("lrange", "log-key", 0, -1)


def test_command_filter_unregister_works_as_expected(r: ValkeyTestClient) -> None:
    """
    test {Command Filter unregister works as expected} {
        # Validate reloading succeeded
        r del log-key
        r set mykey @log
        assert_equal "{set mykey @log}" [r lrange log-key 0 -1]

        # Unregister
        r commandfilter.unregister
        r del log-key

        r set mykey @log
        r lrange log-key 0 -1
    } {}
    """
    r.run("del", "log-key")
    r.run("set", "mykey", "@log")
    assert "{set mykey @log}" == r.run("lrange", "log-key", 0, -1)
    r.run("commandfilter.unregister")
    r.run("del", "log-key")
    r.run("set", "mykey", "@log")
    r.run("lrange", "log-key", 0, -1)


def test_command_filter_redismodule_cmdfilter_noself_works_as_expected(r: ValkeyTestClient) -> None:
    """
    test {Command Filter REDISMODULE_CMDFILTER_NOSELF works as expected} {
        r set mykey @log
        assert_equal "{set mykey @log}" [r lrange log-key 0 -1]

        r del log-key
        r commandfilter.ping
        assert_equal {} [r lrange log-key 0 -1]

        r eval "redis.call('commandfilter.ping')" 0
        assert_equal {} [r lrange log-key 0 -1]
    }
    """
    r.run("set", "mykey", "@log")
    assert "{set mykey @log}" == r.run("lrange", "log-key", 0, -1)
    r.run("del", "log-key")
    r.run("commandfilter.ping")
    assert "" == r.run("lrange", "log-key", 0, -1)
    r.run("eval", "redis.call('commandfilter.ping')", 0)
    assert "" == r.run("lrange", "log-key", 0, -1)


def test_unload_the_module_commandfilter(r: ValkeyTestClient) -> None:
    """
    test "Unload the module - commandfilter" {
        assert_equal {OK} [r module unload commandfilter]
    }
    """
    assert "OK" == r.run("module", "unload", "commandfilter")


"""
test {RM_CommandFilterArgInsert and script argv caching} {
    # coverage for scripts calling commands that expand the argv array
    # an attempt to add coverage for a possible bug in luaArgsToRedisArgv
    # this test needs a fresh server so that lua_argv_size is 0.
    # glibc realloc can return the same pointer even when the size changes
    # still this test isn't able to trigger the issue, but we keep it anyway.
    start_server {tags {"modules"}} {
        r module load $testmodule log-key 0
        r del mylist
        # command with 6 args
        r eval {redis.call('rpush', KEYS[1], 'elem1', 'elem2', 'elem3', 'elem4')} 1 mylist
        # command with 3 args that is changed to 4
        r eval {redis.call('rpush', KEYS[1], '@insertafter')} 1 mylist
        # command with 6 args again
        r eval {redis.call('rpush', KEYS[1], 'elem1', 'elem2', 'elem3', 'elem4')} 1 mylist
        assert_equal [r lrange mylist 0 -1] {elem1 elem2 elem3 elem4 @insertafter --inserted-after-- elem1 elem2 elem3 elem4}
    }
}
"""


"""
test {Blocking Commands don't run through command filter when reprocessed} {
    start_server {tags {"modules"}} {
        r module load $testmodule log-key 0

        r del list1{t}
        r del list2{t}

        r lpush list2{t} a b c d e

        set rd [valkey_deferring_client]
        # we're asking to pop from the left, but the command filter swaps the two arguments,
        # if it didn't swap it, we would end up with e d c b a 5 (5 being the left most of the following lpush)
        # but since we swap the arguments, we end up with 1 e d c b a (1 being the right most of it).
        # if the command filter would run again on unblock, they would be swapped back.
        $rd blmove list1{t} list2{t} left right 0
        wait_for_blocked_client
        r lpush list1{t} 1 2 3 4 5
        # validate that we moved the correct element with the swapped args
        assert_equal [$rd read] 1
        # validate that we moved the correct elements to the correct side of the list
        assert_equal [r lpop list2{t}] 1

        $rd close
    }
}
"""


"""
test {Filtering based on client id} {
    start_server {tags {"modules"}} {
        r module load $testmodule log-key 0

        set rr [valkey_client]
        set cid [$rr client id]
        r unfilter_clientid $cid

        r rpush mylist elem1 @replaceme elem2
        assert_equal [r lrange mylist 0 -1] {elem1 --replaced-- elem2}

        r del mylist

        assert_equal [$rr rpush mylist elem1 @replaceme elem2] 3
        assert_equal [r lrange mylist 0 -1] {elem1 @replaceme elem2}

        $rr close
    }
}
"""


def test_onload_failure_will_handle_un_registration(r: ValkeyTestClient) -> None:
    """
    test {OnLoad failure will handle un-registration} {
        catch {r module load $testmodule log-key 0 noload}
        r set mykey @log
        assert_equal [r lrange log-key 0 -1] {}
        r rpush mylist elem1 @delme elem2
        assert_equal [r lrange mylist 0 -1] {elem1 @delme elem2}
    }
    """
    catch("r module load $testmodule log-key 0 noload")
    r.run("set", "mykey", "@log")
    assert r.run("lrange", "log-key", 0, -1) == ""
    r.run("rpush", "mylist", "elem1", "@delme", "elem2")
    assert r.run("lrange", "mylist", 0, -1) == "elem1 @delme elem2"


# --- stubs for unimplemented TCL helpers ---


def catch(*args):
    raise NotImplementedError("catch")
