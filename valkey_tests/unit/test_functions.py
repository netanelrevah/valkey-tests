# ruff: noqa: PLR2004, F841, ANN002, ANN201
import time
from fnmatch import fnmatch

import pytest

from tests.valkey_test_client import ValkeyTestClient

"""
proc get_function_code {args} {
    return [format "#!%s name=%s\nserver.register_function('%s', function(KEYS, ARGV)\n %s \nend)" [lindex $args 0] [lindex $args 1] [lindex $args 2] [lindex $args 3]]
}
"""


"""
proc get_no_writes_function_code {args} {
    return [format "#!%s name=%s\nserver.register_function{function_name='%s', callback=function(KEYS, ARGV)\n %s \nend, flags={'no-writes'}}" [lindex $args 0] [lindex $args 1] [lindex $args 2] [lindex $args 3]]
}
"""

pytestmark = [pytest.mark.scripting]


def test_function_basic_usage(r: ValkeyTestClient) -> None:
    """
    test {FUNCTION - Basic usage} {
        r function load [get_function_code LUA test test {return 'hello'}]
        r fcall test 0
    } {hello}
    """
    r.run("function", "load", get_function_code("LUA", "test", "test", "return 'hello'"))
    assert r.run("fcall", "test", 0) == "hello"


@pytest.mark.xfail(reason="not implemented")
def test_function_load_with_unknown_argument(r: ValkeyTestClient) -> None:
    """
    test {FUNCTION - Load with unknown argument} {
        catch {
            r function load foo bar [get_function_code LUA test test {return 'hello'}]
        } e
        set _ $e
    } {*Unknown option given*}
    """
    try:
        e = r.run("function", "load", "foo", "bar", get_function_code("LUA", "test", "test", "return 'hello'"))
    except Exception as _catch_err:
        e = str(_catch_err)
    # TODO: set _ e
    assert False


@pytest.mark.xfail(reason="not implemented")
def test_function_create_an_already_exiting_library_raise_error(r: ValkeyTestClient) -> None:
    """
    test {FUNCTION - Create an already exiting library raise error} {
        catch {
            r function load [get_function_code LUA test test {return 'hello1'}]
        } e
        set _ $e
    } {*already exists*}
    """
    try:
        e = r.run("function", "load", get_function_code("LUA", "test", "test", "return 'hello1'"))
    except Exception as _catch_err:
        e = str(_catch_err)
    # TODO: set _ e
    assert False


@pytest.mark.xfail(reason="not implemented")
def test_function_create_an_already_exiting_library_raise_error_case_insensitive(r: ValkeyTestClient) -> None:
    """
    test {FUNCTION - Create an already exiting library raise error (case insensitive)} {
        catch {
            r function load [get_function_code LUA test test {return 'hello1'}]
        } e
        set _ $e
    } {*already exists*}
    """
    try:
        e = r.run("function", "load", get_function_code("LUA", "test", "test", "return 'hello1'"))
    except Exception as _catch_err:
        e = str(_catch_err)
    # TODO: set _ e
    assert False


@pytest.mark.xfail(reason="not implemented")
def test_function_create_a_library_with_wrong_name_format(r: ValkeyTestClient) -> None:
    """
    test {FUNCTION - Create a library with wrong name format} {
        catch {
            r function load [get_function_code LUA {bad\0foramat} test {return 'hello1'}]
        } e
        set _ $e
    } {*Library names can only contain letters, numbers, or underscores(_)*}
    """
    try:
        e = r.run("function", "load", get_function_code("LUA", "bad\\0foramat", "test", "return 'hello1'"))
    except Exception as _catch_err:
        e = str(_catch_err)
    # TODO: set _ e
    assert False


@pytest.mark.xfail(reason="not implemented")
def test_function_create_library_with_unexisting_engine(r: ValkeyTestClient) -> None:
    """
    test {FUNCTION - Create library with unexisting engine} {
        catch {
            r function load [get_function_code bad_engine test test {return 'hello1'}]
        } e
        set _ $e
    } {*Engine 'bad_engine' not found*}
    """
    try:
        e = r.run("function", "load", get_function_code("bad_engine", "test", "test", "return 'hello1'"))
    except Exception as _catch_err:
        e = str(_catch_err)
    # TODO: set _ e
    assert False


@pytest.mark.xfail(reason="not implemented")
def test_function_test_uncompiled_script(r: ValkeyTestClient) -> None:
    """
    test {FUNCTION - Test uncompiled script} {
        catch {
            r function load replace [get_function_code LUA test test {bad script}]
        } e
        set _ $e
    } {*Error compiling function*}
    """
    try:
        e = r.run("function", "load", "replace", get_function_code("LUA", "test", "test", "bad script"))
    except Exception as _catch_err:
        e = str(_catch_err)
    # TODO: set _ e
    assert False


def test_function_test_replace_argument(r: ValkeyTestClient) -> None:
    """
    test {FUNCTION - test replace argument} {
        r function load REPLACE [get_function_code LUA test test {return 'hello1'}]
        r fcall test 0
    } {hello1}
    """
    r.run("function", "load", "REPLACE", get_function_code("LUA", "test", "test", "return 'hello1'"))
    assert r.run("fcall", "test", 0) == "hello1"


def test_function_test_function_case_insensitive(r: ValkeyTestClient) -> None:
    """
    test {FUNCTION - test function case insensitive} {
        r fcall TEST 0
    } {hello1}
    """
    assert r.run("fcall", "TEST", 0) == "hello1"


def test_function_test_replace_argument_with_failure_keeps_old_libraries(r: ValkeyTestClient) -> None:
    """
    test {FUNCTION - test replace argument with failure keeps old libraries} {
        catch {r function load REPLACE [get_function_code LUA test test {error}]} e
        assert_match {ERR Error compiling function*} $e
        r fcall test 0
    } {hello1}
    """
    try:
        e = r.run("function", "load", "REPLACE", get_function_code("LUA", "test", "test", "error"))
    except Exception as _catch_err:
        e = str(_catch_err)
    assert fnmatch(str(e), "ERR Error compiling function*")
    assert r.run("fcall", "test", 0) == "hello1"


@pytest.mark.xfail(reason="not implemented")
def test_function_test_function_delete(r: ValkeyTestClient) -> None:
    """
    test {FUNCTION - test function delete} {
        r function delete test
        catch {
            r fcall test 0
        } e
        set _ $e
    } {*Function not found*}
    """
    r.run("function", "delete", "test")
    try:
        e = r.run("fcall", "test", 0)
    except Exception as _catch_err:
        e = str(_catch_err)
    # TODO: set _ e
    assert False


@pytest.mark.xfail(reason="not implemented")
def test_function_test_fcall_bad_arguments(r: ValkeyTestClient) -> None:
    """
    test {FUNCTION - test fcall bad arguments} {
        r function load [get_function_code LUA test test {return 'hello'}]
        catch {
            r fcall test bad_arg
        } e
        set _ $e
    } {*Bad number of keys provided*}
    """
    r.run("function", "load", get_function_code("LUA", "test", "test", "return 'hello'"))
    try:
        e = r.run("fcall", "test", "bad_arg")
    except Exception as _catch_err:
        e = str(_catch_err)
    # TODO: set _ e
    assert False


@pytest.mark.xfail(reason="not implemented")
def test_function_test_fcall_bad_number_of_keys_arguments(r: ValkeyTestClient) -> None:
    """
    test {FUNCTION - test fcall bad number of keys arguments} {
        catch {
            r fcall test 10 key1
        } e
        set _ $e
    } {*Number of keys can't be greater than number of args*}
    """
    try:
        e = r.run("fcall", "test", 10, "key1")
    except Exception as _catch_err:
        e = str(_catch_err)
    # TODO: set _ e
    assert False


@pytest.mark.xfail(reason="not implemented")
def test_function_test_fcall_negative_number_of_keys(r: ValkeyTestClient) -> None:
    """
    test {FUNCTION - test fcall negative number of keys} {
        catch {
            r fcall test -1 key1
        } e
        set _ $e
    } {*Number of keys can't be negative*}
    """
    try:
        e = r.run("fcall", "test", -1, "key1")
    except Exception as _catch_err:
        e = str(_catch_err)
    # TODO: set _ e
    assert False


@pytest.mark.xfail(reason="not implemented")
def test_function_test_delete_on_not_exiting_library(r: ValkeyTestClient) -> None:
    """
    test {FUNCTION - test delete on not exiting library} {
        catch {
            r function delete test1
        } e
        set _ $e
    } {*Library not found*}
    """
    try:
        e = r.run("function", "delete", "test1")
    except Exception as _catch_err:
        e = str(_catch_err)
    # TODO: set _ e
    assert False


@pytest.mark.xfail(reason="not implemented")
def test_function_test_function_kill_when_function_is_not_running(r: ValkeyTestClient) -> None:
    """
    test {FUNCTION - test function kill when function is not running} {
        catch {
            r function kill
        } e
        set _ $e
    } {*No scripts in execution*}
    """
    try:
        e = r.run("function", "kill")
    except Exception as _catch_err:
        e = str(_catch_err)
    # TODO: set _ e
    assert False


@pytest.mark.xfail(reason="not implemented")
def test_function_test_wrong_subcommand(r: ValkeyTestClient) -> None:
    """
    test {FUNCTION - test wrong subcommand} {
        catch {
            r function bad_subcommand
        } e
        set _ $e
    } {*unknown subcommand*}
    """
    try:
        e = r.run("function", "bad_subcommand")
    except Exception as _catch_err:
        e = str(_catch_err)
    # TODO: set _ e
    assert False


def test_function_test_loading_from_rdb(r: ValkeyTestClient) -> None:
    """
    test {FUNCTION - test loading from rdb} {
        r debug reload
        r fcall test 0
    } {hello} {needs:debug}
    """
    r.run("debug", "reload")
    assert r.run("fcall", "test", 0) == "hello"


def test_function_test_debug_reload_different_options(r: ValkeyTestClient) -> None:
    """
    test {FUNCTION - test debug reload different options} {
        catch {r debug reload noflush} e
        assert_match "*Error trying to load the RDB*" $e
        r debug reload noflush merge
        r function list
    } {{library_name test engine LUA functions {{name test description {} flags {}}}}} {needs:debug}
    """
    try:
        e = r.run("debug", "reload", "noflush")
    except Exception as _catch_err:
        e = str(_catch_err)
    assert fnmatch(str(e), "*Error trying to load the RDB*")
    r.run("debug", "reload", "noflush", "merge")
    assert r.run("function", "list") == "{library_name test engine LUA functions {{name test description {} flags {}}}}"


def test_function_test_debug_reload_with_nosave_and_noflush(r: ValkeyTestClient) -> None:
    """
    test {FUNCTION - test debug reload with nosave and noflush} {
        r function delete test
        r set x 1
        r function load [get_function_code LUA test1 test1 {return 'hello'}]
        r debug reload
        r function load [get_function_code LUA test2 test2 {return 'hello'}]
        r debug reload nosave noflush merge
        assert_equal [r fcall test1 0] {hello}
        assert_equal [r fcall test2 0] {hello}
    } {} {needs:debug}
    """
    r.run("function", "delete", "test")
    r.run("set", "x", 1)
    r.run("function", "load", get_function_code("LUA", "test1", "test1", "return 'hello'"))
    r.run("debug", "reload")
    r.run("function", "load", get_function_code("LUA", "test2", "test2", "return 'hello'"))
    r.run("debug", "reload", "nosave", "noflush", "merge")
    assert r.run("fcall", "test1", 0) == "hello"
    assert r.run("fcall", "test2", 0) == "hello"


def test_function_test_flushall_and_flushdb_do_not_clean_functions(r: ValkeyTestClient) -> None:
    """
    test {FUNCTION - test flushall and flushdb do not clean functions} {
        r function flush
        r function load REPLACE [get_function_code lua test test {return redis.call('set', 'x', '1')}]
        r flushall
        r flushdb
        r function list
    } {{library_name test engine LUA functions {{name test description {} flags {}}}}}
    """
    r.run("function", "flush")
    r.run("function", "load", "REPLACE", get_function_code("lua", "test", "test", "return redis.call('set', 'x', '1')"))
    r.run("flushall")
    r.run("flushdb")
    assert r.run("function", "list") == "{library_name test engine LUA functions {{name test description {} flags {}}}}"


def test_function_test_function_dump_and_restore(r: ValkeyTestClient) -> None:
    """
    test {FUNCTION - test function dump and restore} {
        r function flush
        r function load [get_function_code lua test test {return 'hello'}]
        set e [r function dump]
        r function delete test
        assert_match {} [r function list]
        r function restore $e
        r function list
    } {{library_name test engine LUA functions {{name test description {} flags {}}}}}
    """
    r.run("function", "flush")
    r.run("function", "load", get_function_code("lua", "test", "test", "return 'hello'"))
    e = r.run("function", "dump")
    r.run("function", "delete", "test")
    assert fnmatch(str(r.run("function", "list")), "")
    r.run("function", "restore", e)
    assert r.run("function", "list") == "{library_name test engine LUA functions {{name test description {} flags {}}}}"


def test_function_test_function_dump_and_restore_with_flush_argument(r: ValkeyTestClient) -> None:
    """
    test {FUNCTION - test function dump and restore with flush argument} {
        set e [r function dump]
        r function flush
        assert_match {} [r function list]
        r function restore $e FLUSH
        r function list
    } {{library_name test engine LUA functions {{name test description {} flags {}}}}}
    """
    e = r.run("function", "dump")
    r.run("function", "flush")
    assert fnmatch(str(r.run("function", "list")), "")
    r.run("function", "restore", e, "FLUSH")
    assert r.run("function", "list") == "{library_name test engine LUA functions {{name test description {} flags {}}}}"


def test_function_test_function_dump_and_restore_with_append_argument(r: ValkeyTestClient) -> None:
    """
    test {FUNCTION - test function dump and restore with append argument} {
        set e [r function dump]
        r function flush
        assert_match {} [r function list]
        r function load [get_function_code lua test test {return 'hello1'}]
        catch {r function restore $e APPEND} err
        assert_match {*already exists*} $err
        r function flush
        r function load [get_function_code lua test1 test1 {return 'hello1'}]
        r function restore $e APPEND
        assert_match {hello} [r fcall test 0]
        assert_match {hello1} [r fcall test1 0]
    }
    """
    e = r.run("function", "dump")
    r.run("function", "flush")
    assert fnmatch(str(r.run("function", "list")), "")
    r.run("function", "load", get_function_code("lua", "test", "test", "return 'hello1'"))
    try:
        err = r.run("function", "restore", e, "APPEND")
    except Exception as _catch_err:
        err = str(_catch_err)
    assert fnmatch(str(err), "*already exists*")
    r.run("function", "flush")
    r.run("function", "load", get_function_code("lua", "test1", "test1", "return 'hello1'"))
    r.run("function", "restore", e, "APPEND")
    assert fnmatch(str(r.run("fcall", "test", 0)), "hello")
    assert fnmatch(str(r.run("fcall", "test1", 0)), "hello1")


def test_function_test_function_dump_and_restore_with_replace_argument(r: ValkeyTestClient) -> None:
    """
    test {FUNCTION - test function dump and restore with replace argument} {
        r function flush
        r function load [get_function_code LUA test test {return 'hello'}]
        set e [r function dump]
        r function flush
        assert_match {} [r function list]
        r function load [get_function_code lua test test {return 'hello1'}]
        assert_match {hello1} [r fcall test 0]
        r function restore $e REPLACE
        assert_match {hello} [r fcall test 0]
    }
    """
    r.run("function", "flush")
    r.run("function", "load", get_function_code("LUA", "test", "test", "return 'hello'"))
    e = r.run("function", "dump")
    r.run("function", "flush")
    assert fnmatch(str(r.run("function", "list")), "")
    r.run("function", "load", get_function_code("lua", "test", "test", "return 'hello1'"))
    assert fnmatch(str(r.run("fcall", "test", 0)), "hello1")
    r.run("function", "restore", e, "REPLACE")
    assert fnmatch(str(r.run("fcall", "test", 0)), "hello")


def test_function_test_function_restore_with_bad_payload_do_not_drop_existing_functions(r: ValkeyTestClient) -> None:
    """
    test {FUNCTION - test function restore with bad payload do not drop existing functions} {
        r function flush
        r function load [get_function_code LUA test test {return 'hello'}]
        catch {r function restore bad_payload} e
        assert_match {*payload version or checksum are wrong*} $e
        r function list
    } {{library_name test engine LUA functions {{name test description {} flags {}}}}}
    """
    r.run("function", "flush")
    r.run("function", "load", get_function_code("LUA", "test", "test", "return 'hello'"))
    try:
        e = r.run("function", "restore", "bad_payload")
    except Exception as _catch_err:
        e = str(_catch_err)
    assert fnmatch(str(e), "*payload version or checksum are wrong*")
    assert r.run("function", "list") == "{library_name test engine LUA functions {{name test description {} flags {}}}}"


@pytest.mark.xfail(reason="not implemented")
def test_function_test_function_restore_with_wrong_number_of_arguments(r: ValkeyTestClient) -> None:
    """
    test {FUNCTION - test function restore with wrong number of arguments} {
        catch {r function restore arg1 args2 arg3} e
        set _ $e
    } {*unknown subcommand or wrong number of arguments for 'restore'. Try FUNCTION HELP.}
    """
    try:
        e = r.run("function", "restore", "arg1", "args2", "arg3")
    except Exception as _catch_err:
        e = str(_catch_err)
    # TODO: set _ e
    assert False


@pytest.mark.xfail(reason="not implemented")
def test_function_test_fcall_ro_with_write_command(r: ValkeyTestClient) -> None:
    """
    test {FUNCTION - test fcall_ro with write command} {
        r function load REPLACE [get_no_writes_function_code lua test test {return redis.call('set', 'x', '1')}]
        catch { r fcall_ro test 1 x } e
        set _ $e
    } {*Write commands are not allowed from read-only scripts*}
    """
    r.run(
        "function",
        "load",
        "REPLACE",
        get_no_writes_function_code("lua", "test", "test", "return redis.call('set', 'x', '1')"),
    )
    try:
        e = r.run("fcall_ro", "test", 1, "x")
    except Exception as _catch_err:
        e = str(_catch_err)
    # TODO: set _ e
    assert False


def test_function_test_fcall_ro_with_read_only_commands(r: ValkeyTestClient) -> None:
    """
    test {FUNCTION - test fcall_ro with read only commands} {
        r function load REPLACE [get_no_writes_function_code lua test test {return redis.call('get', 'x')}]
        r set x 1
        r fcall_ro test 1 x
    } {1}
    """
    r.run(
        "function",
        "load",
        "REPLACE",
        get_no_writes_function_code("lua", "test", "test", "return redis.call('get', 'x')"),
    )
    r.run("set", "x", 1)
    assert r.run("fcall_ro", "test", 1, "x") == "1"


def test_function_test_keys_and_argv(r: ValkeyTestClient) -> None:
    """
    test {FUNCTION - test keys and argv} {
        r function load REPLACE [get_function_code lua test test {return redis.call('set', KEYS[1], ARGV[1])}]
        r fcall test 1 x foo
        r get x
    } {foo}
    """
    r.run(
        "function",
        "load",
        "REPLACE",
        get_function_code("lua", "test", "test", "return redis.call('set', KEYS[1], ARGV[1])"),
    )
    r.run("fcall", "test", 1, "x", "foo")
    assert r.run("get", "x") == "foo"


def test_function_test_command_get_keys_on_fcall(r: ValkeyTestClient) -> None:
    """
    test {FUNCTION - test command get keys on fcall} {
        r COMMAND GETKEYS fcall test 1 x foo
    } {x}
    """
    assert r.run("COMMAND", "GETKEYS", "fcall", "test", 1, "x", "foo") == "x"


def test_function_test_command_get_keys_on_fcall_ro(r: ValkeyTestClient) -> None:
    """
    test {FUNCTION - test command get keys on fcall_ro} {
        r COMMAND GETKEYS fcall_ro test 1 x foo
    } {x}
    """
    assert r.run("COMMAND", "GETKEYS", "fcall_ro", "test", 1, "x", "foo") == "x"


@pytest.mark.xfail(reason="not implemented")
def test_function_test_function_kill(r: ValkeyTestClient) -> None:
    """
    test {FUNCTION - test function kill} {
        set rd [valkey_deferring_client]
        r config set busy-reply-threshold 10
        r function load REPLACE [get_function_code lua test test {local a = 1 while true do a = a + 1 end}]
        $rd fcall test 0
        after 200
        catch {r ping} e
        assert_match {BUSY*} $e
        assert_match {running_script {name test command {fcall test 0} duration_ms *} engines {*}} [r FUNCTION STATS]
        r function kill
        after 200 ; # Give some time to Lua to call the hook again...
        assert_equal [r ping] "PONG"
        assert_error {ERR Script killed by user with FUNCTION KILL*} {$rd read}
        $rd close
    }
    """
    rd = valkey_deferring_client()
    r.run("config", "set", "busy-reply-threshold", 10)
    r.run(
        "function",
        "load",
        "REPLACE",
        get_function_code("lua", "test", "test", "local a = 1 while true do a = a + 1 end"),
    )
    # TODO: $rd fcall test 0
    time.sleep(200 / 1000)
    try:
        e = r.run("ping")
    except Exception as _catch_err:
        e = str(_catch_err)
    assert fnmatch(str(e), "BUSY*")
    assert fnmatch(
        str(r.run("FUNCTION", "STATS")), "running_script {name test command {fcall test 0} duration_ms *} engines {*}"
    )
    r.run("function", "kill")
    time.sleep(200 / 1000)
    assert r.run("ping") == "PONG"
    assert_error("ERR Script killed by user with FUNCTION KILL*", "$rd read")
    # TODO: $rd close


@pytest.mark.xfail(reason="not implemented")
def test_function_test_script_kill_not_working_on_function(r: ValkeyTestClient) -> None:
    """
    test {FUNCTION - test script kill not working on function} {
        set rd [valkey_deferring_client]
        r config set busy-reply-threshold 10
        r function load REPLACE [get_function_code lua test test {local a = 1 while true do a = a + 1 end}]
        $rd fcall test 0
        after 200
        catch {r ping} e
        assert_match {BUSY*} $e
        catch {r script kill} e
        assert_match {BUSY*} $e
        r function kill
        after 200 ; # Give some time to Lua to call the hook again...
        assert_equal [r ping] "PONG"
        assert_error {ERR Script killed by user with FUNCTION KILL*} {$rd read}
        $rd close
    }
    """
    rd = valkey_deferring_client()
    r.run("config", "set", "busy-reply-threshold", 10)
    r.run(
        "function",
        "load",
        "REPLACE",
        get_function_code("lua", "test", "test", "local a = 1 while true do a = a + 1 end"),
    )
    # TODO: $rd fcall test 0
    time.sleep(200 / 1000)
    try:
        e = r.run("ping")
    except Exception as _catch_err:
        e = str(_catch_err)
    assert fnmatch(str(e), "BUSY*")
    try:
        e = r.run("script", "kill")
    except Exception as _catch_err:
        e = str(_catch_err)
    assert fnmatch(str(e), "BUSY*")
    r.run("function", "kill")
    time.sleep(200 / 1000)
    assert r.run("ping") == "PONG"
    assert_error("ERR Script killed by user with FUNCTION KILL*", "$rd read")
    # TODO: $rd close


@pytest.mark.xfail(reason="not implemented")
def test_function_test_function_kill_not_working_on_eval(r: ValkeyTestClient) -> None:
    """
    test {FUNCTION - test function kill not working on eval} {
        set rd [valkey_deferring_client]
        r config set busy-reply-threshold 10
        $rd eval {local a = 1 while true do a = a + 1 end} 0
        after 200
        catch {r ping} e
        assert_match {BUSY*} $e
        catch {r function kill} e
        assert_match {BUSY*} $e
        r script kill
        after 200 ; # Give some time to Lua to call the hook again...
        assert_equal [r ping] "PONG"
        assert_error {ERR Script killed by user with SCRIPT KILL*} {$rd read}
        $rd close
    }
    """
    rd = valkey_deferring_client()
    r.run("config", "set", "busy-reply-threshold", 10)
    # TODO: $rd eval {local a = 1 while true do a = a + 1 end} 0
    time.sleep(200 / 1000)
    try:
        e = r.run("ping")
    except Exception as _catch_err:
        e = str(_catch_err)
    assert fnmatch(str(e), "BUSY*")
    try:
        e = r.run("function", "kill")
    except Exception as _catch_err:
        e = str(_catch_err)
    assert fnmatch(str(e), "BUSY*")
    r.run("script", "kill")
    time.sleep(200 / 1000)
    assert r.run("ping") == "PONG"
    assert_error("ERR Script killed by user with SCRIPT KILL*", "$rd read")
    # TODO: $rd close


def test_function_test_function_flush(r: ValkeyTestClient) -> None:
    """
    test {FUNCTION - test function flush} {
        r function load REPLACE [get_function_code lua test test {local a = 1 while true do a = a + 1 end}]
        assert_match {{library_name test engine LUA functions {{name test description {} flags {}}}}} [r function list]
        r function flush
        assert_match {} [r function list]

        r function load REPLACE [get_function_code lua test test {local a = 1 while true do a = a + 1 end}]
        assert_match {{library_name test engine LUA functions {{name test description {} flags {}}}}} [r function list]
        r function flush async
        assert_match {} [r function list]

        r function load REPLACE [get_function_code lua test test {local a = 1 while true do a = a + 1 end}]
        assert_match {{library_name test engine LUA functions {{name test description {} flags {}}}}} [r function list]
        r function flush sync
        assert_match {} [r function list]
    }
    """
    r.run(
        "function",
        "load",
        "REPLACE",
        get_function_code("lua", "test", "test", "local a = 1 while true do a = a + 1 end"),
    )
    assert fnmatch(
        str(r.run("function", "list")), "{library_name test engine LUA functions {{name test description {} flags {}}}}"
    )
    r.run("function", "flush")
    assert fnmatch(str(r.run("function", "list")), "")
    r.run(
        "function",
        "load",
        "REPLACE",
        get_function_code("lua", "test", "test", "local a = 1 while true do a = a + 1 end"),
    )
    assert fnmatch(
        str(r.run("function", "list")), "{library_name test engine LUA functions {{name test description {} flags {}}}}"
    )
    r.run("function", "flush", "async")
    assert fnmatch(str(r.run("function", "list")), "")
    r.run(
        "function",
        "load",
        "REPLACE",
        get_function_code("lua", "test", "test", "local a = 1 while true do a = a + 1 end"),
    )
    assert fnmatch(
        str(r.run("function", "list")), "{library_name test engine LUA functions {{name test description {} flags {}}}}"
    )
    r.run("function", "flush", "sync")
    assert fnmatch(str(r.run("function", "list")), "")


def test_function_test_function_flush_will_re_create_the_lua_engine(r: ValkeyTestClient) -> None:
    """
    test {FUNCTION - test function flush will re-create the lua engine} {
        for {set i 0} {$i < 60} {incr i} {
            r function load [get_function_code lua test_$i test_$i {local a = 1 while true do a = a + 1 end}]
        }
        set before_flush_memory [s used_memory_vm_functions]
        r function flush sync
        set after_flush_memory [s used_memory_vm_functions]
        assert_lessthan $after_flush_memory $before_flush_memory

        for {set i 0} {$i < 100} {incr i} {
            r function load [get_function_code lua test_$i test_$i {local a = 1 while true do a = a + 1 end}]
        }
        set before_flush_memory [s used_memory_vm_functions]
        r function flush async
        set after_flush_memory [s used_memory_vm_functions]
        assert_lessthan $after_flush_memory $before_flush_memory
    }
    """
    i = 0
    while i < 60:
        r.run(
            "function",
            "load",
            get_function_code("lua", "test_$i", "test_$i", "local a = 1 while true do a = a + 1 end"),
        )
        i += 1
    before_flush_memory = s("used_memory_vm_functions")
    r.run("function", "flush", "sync")
    after_flush_memory = s("used_memory_vm_functions")
    assert_lessthan(after_flush_memory, before_flush_memory)
    i = 0
    while i < 100:
        r.run(
            "function",
            "load",
            get_function_code("lua", "test_$i", "test_$i", "local a = 1 while true do a = a + 1 end"),
        )
        i += 1
    before_flush_memory = s("used_memory_vm_functions")
    r.run("function", "flush", "async")
    after_flush_memory = s("used_memory_vm_functions")
    assert_lessthan(after_flush_memory, before_flush_memory)


def test_function_test_loading_function_during_the_flush_async(r: ValkeyTestClient) -> None:
    """
    test {FUNCTION - test loading function during the flush async} {
        for {set i 0} {$i < 10000} {incr i} {
            r function load [get_function_code LUA test_$i test_$i {return 'hello'}]
        }
        r function flush sync

        for {set i 0} {$i < 10000} {incr i} {
            r function load [get_function_code LUA test_$i test_$i {return 'hello'}]
        }
        r function flush async

        for {set i 0} {$i < 10000} {incr i} {
            r function load [get_function_code LUA test_$i test_$i {return 'hello'}]
        }
        r function flush
    }
    """
    i = 0
    while i < 10000:
        r.run("function", "load", get_function_code("LUA", "test_$i", "test_$i", "return 'hello'"))
        i += 1
    r.run("function", "flush", "sync")
    i = 0
    while i < 10000:
        r.run("function", "load", get_function_code("LUA", "test_$i", "test_$i", "return 'hello'"))
        i += 1
    r.run("function", "flush", "async")
    i = 0
    while i < 10000:
        r.run("function", "load", get_function_code("LUA", "test_$i", "test_$i", "return 'hello'"))
        i += 1
    r.run("function", "flush")


def test_function_test_function_wrong_argument(r: ValkeyTestClient) -> None:
    """
    test {FUNCTION - test function wrong argument} {
        catch {r function flush bad_arg} e
        assert_match {*only supports SYNC|ASYNC*} $e

        catch {r function flush sync extra_arg} e
        assert_match {*unknown subcommand or wrong number of arguments for 'flush'. Try FUNCTION HELP.} $e
    }
    """
    try:
        e = r.run("function", "flush", "bad_arg")
    except Exception as _catch_err:
        e = str(_catch_err)
    assert fnmatch(str(e), "*only supports SYNC|ASYNC*")
    try:
        e = r.run("function", "flush", "sync", "extra_arg")
    except Exception as _catch_err:
        e = str(_catch_err)
    assert fnmatch(str(e), "*unknown subcommand or wrong number of arguments for 'flush'. Try FUNCTION HELP.")


pytestmark = [pytest.mark.scripting_repl_external_skip]


"""
start_server {} {
    test "Connect a replica to the master instance" {
        r -1 slaveof [srv 0 host] [srv 0 port]
        wait_for_condition 150 100 {
            [s -1 role] eq {slave} &&
            [string match {*master_link_status:up*} [r -1 info replication]]
        } else {
            fail "Can't turn the instance into a replica"
        }
    }

    test {FUNCTION - creation is replicated to replica} {
        r function load [get_no_writes_function_code LUA test test {return 'hello'}]
        wait_for_condition 150 100 {
            [r -1 function list] eq {{library_name test engine LUA functions {{name test description {} flags no-writes}}}}
        } else {
            fail "Failed waiting for function to replicate to replica"
        }
    }

    test {FUNCTION - call on replica} {
        r -1 fcall test 0
    } {hello}

    test {FUNCTION - restore is replicated to replica} {
        set e [r function dump]

        r function delete test
        wait_for_condition 150 100 {
            [r -1 function list] eq {}
        } else {
            fail "Failed waiting for function to replicate to replica"
        }

        assert_equal [r function restore $e] {OK}

        wait_for_condition 150 100 {
            [r -1 function list] eq {{library_name test engine LUA functions {{name test description {} flags no-writes}}}}
        } else {
            fail "Failed waiting for function to replicate to replica"
        }
    }

    test {FUNCTION - delete is replicated to replica} {
        r function delete test
        wait_for_condition 150 100 {
            [r -1 function list] eq {}
        } else {
            fail "Failed waiting for function to replicate to replica"
        }
    }

    test {FUNCTION - flush is replicated to replica} {
        r function load [get_function_code LUA test test {return 'hello'}]
        wait_for_condition 150 100 {
            [r -1 function list] eq {{library_name test engine LUA functions {{name test description {} flags {}}}}}
        } else {
            fail "Failed waiting for function to replicate to replica"
        }
        r function flush
        wait_for_condition 150 100 {
            [r -1 function list] eq {}
        } else {
            fail "Failed waiting for function to replicate to replica"
        }
    }

    test "Disconnecting the replica from master instance" {
        r -1 slaveof no one
        # creating a function after disconnect to make sure function
        # is replicated on rdb phase
        r function load [get_no_writes_function_code LUA test test {return 'hello'}]

        # reconnect the replica
        r -1 slaveof [srv 0 host] [srv 0 port]
        wait_for_condition 150 100 {
            [s -1 role] eq {slave} &&
            [string match {*master_link_status:up*} [r -1 info replication]]
        } else {
            fail "Can't turn the instance into a replica"
        }
    }

    test "FUNCTION - test replication to replica on rdb phase" {
        r -1 fcall test 0
    } {hello}

    test "FUNCTION - test replication to replica on rdb phase info command" {
        r -1 function list
    } {{library_name test engine LUA functions {{name test description {} flags no-writes}}}}

    test "FUNCTION - create on read only replica" {
        catch {
            r -1 function load [get_function_code LUA test test {return 'hello'}]
        } e
        set _ $e
    } {*can't write against a read only replica*}

    test "FUNCTION - delete on read only replica" {
        catch {
            r -1 function delete test
        } e
        set _ $e
    } {*can't write against a read only replica*}

    test "FUNCTION - function effect is replicated to replica" {
        r function load REPLACE [get_function_code LUA test test {return redis.call('set', 'x', '1')}]
        r fcall test 1 x
        assert {[r get x] eq {1}}
        wait_for_condition 150 100 {
            [r -1 get x] eq {1}
        } else {
            fail "Failed waiting function effect to be replicated to replica"
        }
    }

    test "FUNCTION - modify key space of read only replica" {
        catch {
            r -1 fcall test 1 x
        } e
        set _ $e
    } {READONLY You can't write against a read only replica.}
}
"""


"""
test {FUNCTION can processes create, delete and flush commands in AOF when doing "debug loadaof" in read-only slaves} {
    start_server {} {
        r config set appendonly yes
        waitForBgrewriteaof r
        r FUNCTION LOAD "#!lua name=test\nserver.register_function('test', function() return 'hello' end)"
        r config set slave-read-only yes
        r slaveof 127.0.0.1 0
        r debug loadaof
        r slaveof no one
        assert_equal [r function list] {{library_name test engine LUA functions {{name test description {} flags {}}}}}

        r FUNCTION DELETE test

        r slaveof 127.0.0.1 0
        r debug loadaof
        r slaveof no one
        assert_equal [r function list] {}

        r FUNCTION LOAD "#!lua name=test\nserver.register_function('test', function() return 'hello' end)"
        r FUNCTION FLUSH

        r slaveof 127.0.0.1 0
        r debug loadaof
        r slaveof no one
        assert_equal [r function list] {}
    }
} {} {needs:debug external:skip}
"""

pytestmark = [pytest.mark.scripting]


def test_libraries_test_shared_function_can_access_default_globals(r: ValkeyTestClient) -> None:
    """
    test {LIBRARIES - test shared function can access default globals} {
        r function load {#!lua name=lib1
            local function ping()
                return redis.call('ping')
            end
            server.register_function(
                'f1',
                function(keys, args)
                    return ping()
                end
            )
        }
        r fcall f1 0
    } {PONG}
    """
    r.run(
        "function",
        "load",
        "#!lua name=lib1\n            local function ping()\n                return redis.call('ping')\n            end\n            server.register_function(\n                'f1',\n                function(keys, args)\n                    return ping()\n                end\n            )\n        ",
    )
    assert r.run("fcall", "f1", 0) == "PONG"


def test_libraries_usage_and_code_sharing(r: ValkeyTestClient) -> None:
    """
    test {LIBRARIES - usage and code sharing} {
        r function load REPLACE {#!lua name=lib1
            local function add1(a)
                return a + 1
            end
            server.register_function(
                'f1',
                function(keys, args)
                    return add1(1)
                end
            )
            server.register_function(
                'f2',
                function(keys, args)
                    return add1(2)
                end
            )
        }
        assert_equal [r fcall f1 0] {2}
        assert_equal [r fcall f2 0] {3}
        r function list
    } {{library_name lib1 engine LUA functions {*}}}
    """
    r.run(
        "function",
        "load",
        "REPLACE",
        "#!lua name=lib1\n            local function add1(a)\n                return a + 1\n            end\n            server.register_function(\n                'f1',\n                function(keys, args)\n                    return add1(1)\n                end\n            )\n            server.register_function(\n                'f2',\n                function(keys, args)\n                    return add1(2)\n                end\n            )\n        ",
    )
    assert r.run("fcall", "f1", 0) == "2"
    assert r.run("fcall", "f2", 0) == "3"
    assert r.run("function", "list") == "{library_name lib1 engine LUA functions {*}}"


def test_libraries_test_registration_failure_revert_the_entire_load(r: ValkeyTestClient) -> None:
    """
    test {LIBRARIES - test registration failure revert the entire load} {
        catch {
            r function load replace {#!lua name=lib1
                local function add1(a)
                    return a + 2
                end
                server.register_function(
                    'f1',
                    function(keys, args)
                        return add1(1)
                    end
                )
                server.register_function(
                    'f2',
                    'not a function'
                )
            }
        } e
        assert_match {*second argument to server.register_function must be a function*} $e
        assert_equal [r fcall f1 0] {2}
        assert_equal [r fcall f2 0] {3}
    }
    """
    try:
        e = r.run(
            "function",
            "load",
            "replace",
            "#!lua name=lib1\n                local function add1(a)\n                    return a + 2\n                end\n                server.register_function(\n                    'f1',\n                    function(keys, args)\n                        return add1(1)\n                    end\n                )\n                server.register_function(\n                    'f2',\n                    'not a function'\n                )\n            ",
        )
    except Exception as _catch_err:
        e = str(_catch_err)
    assert fnmatch(str(e), "*second argument to server.register_function must be a function*")
    assert r.run("fcall", "f1", 0) == "2"
    assert r.run("fcall", "f2", 0) == "3"


def test_libraries_test_registration_function_name_collision(r: ValkeyTestClient) -> None:
    """
    test {LIBRARIES - test registration function name collision} {
        catch {
            r function load replace {#!lua name=lib2
                server.register_function(
                    'f1',
                    function(keys, args)
                        return 1
                    end
                )
            }
        } e
        assert_match {*Function f1 already exists*} $e
        assert_equal [r fcall f1 0] {2}
        assert_equal [r fcall f2 0] {3}
    }
    """
    try:
        e = r.run(
            "function",
            "load",
            "replace",
            "#!lua name=lib2\n                server.register_function(\n                    'f1',\n                    function(keys, args)\n                        return 1\n                    end\n                )\n            ",
        )
    except Exception as _catch_err:
        e = str(_catch_err)
    assert fnmatch(str(e), "*Function f1 already exists*")
    assert r.run("fcall", "f1", 0) == "2"
    assert r.run("fcall", "f2", 0) == "3"


@pytest.mark.xfail(reason="not implemented")
def test_libraries_test_registration_function_name_collision_on_same_library(r: ValkeyTestClient) -> None:
    """
    test {LIBRARIES - test registration function name collision on same library} {
        catch {
            r function load replace {#!lua name=lib2
                server.register_function(
                    'f1',
                    function(keys, args)
                        return 1
                    end
                )
                server.register_function(
                    'f1',
                    function(keys, args)
                        return 1
                    end
                )
            }
        } e
        set _ $e
    } {*Function already exists in the library*}
    """
    try:
        e = r.run(
            "function",
            "load",
            "replace",
            "#!lua name=lib2\n                server.register_function(\n                    'f1',\n                    function(keys, args)\n                        return 1\n                    end\n                )\n                server.register_function(\n                    'f1',\n                    function(keys, args)\n                        return 1\n                    end\n                )\n            ",
        )
    except Exception as _catch_err:
        e = str(_catch_err)
    # TODO: set _ e
    assert False


@pytest.mark.xfail(reason="not implemented")
def test_libraries_test_registration_with_no_argument(r: ValkeyTestClient) -> None:
    """
    test {LIBRARIES - test registration with no argument} {
        catch {
            r function load replace {#!lua name=lib2
                server.register_function()
            }
        } e
        set _ $e
    } {*wrong number of arguments to server.register_function*}
    """
    try:
        e = r.run(
            "function", "load", "replace", "#!lua name=lib2\n                server.register_function()\n            "
        )
    except Exception as _catch_err:
        e = str(_catch_err)
    # TODO: set _ e
    assert False


@pytest.mark.xfail(reason="not implemented")
def test_libraries_test_registration_with_only_name(r: ValkeyTestClient) -> None:
    """
    test {LIBRARIES - test registration with only name} {
        catch {
            r function load replace {#!lua name=lib2
                server.register_function('f1')
            }
        } e
        set _ $e
    } {*calling server.register_function with a single argument is only applicable to Lua table*}
    """
    try:
        e = r.run(
            "function",
            "load",
            "replace",
            "#!lua name=lib2\n                server.register_function('f1')\n            ",
        )
    except Exception as _catch_err:
        e = str(_catch_err)
    # TODO: set _ e
    assert False


@pytest.mark.xfail(reason="not implemented")
def test_libraries_test_registration_with_to_many_arguments(r: ValkeyTestClient) -> None:
    """
    test {LIBRARIES - test registration with to many arguments} {
        catch {
            r function load replace {#!lua name=lib2
                server.register_function('f1', function() return 1 end, {}, 'description', 'extra arg')
            }
        } e
        set _ $e
    } {*wrong number of arguments to server.register_function*}
    """
    try:
        e = r.run(
            "function",
            "load",
            "replace",
            "#!lua name=lib2\n                server.register_function('f1', function() return 1 end, {}, 'description', 'extra arg')\n            ",
        )
    except Exception as _catch_err:
        e = str(_catch_err)
    # TODO: set _ e
    assert False


@pytest.mark.xfail(reason="not implemented")
def test_libraries_test_registration_with_no_string_name(r: ValkeyTestClient) -> None:
    """
    test {LIBRARIES - test registration with no string name} {
        catch {
            r function load replace {#!lua name=lib2
                server.register_function(nil, function() return 1 end)
            }
        } e
        set _ $e
    } {*first argument to server.register_function must be a string*}
    """
    try:
        e = r.run(
            "function",
            "load",
            "replace",
            "#!lua name=lib2\n                server.register_function(nil, function() return 1 end)\n            ",
        )
    except Exception as _catch_err:
        e = str(_catch_err)
    # TODO: set _ e
    assert False


@pytest.mark.xfail(reason="not implemented")
def test_libraries_test_registration_with_wrong_name_format(r: ValkeyTestClient) -> None:
    """
    test {LIBRARIES - test registration with wrong name format} {
        catch {
            r function load replace {#!lua name=lib2
                server.register_function('test\0test', function() return 1 end)
            }
        } e
        set _ $e
    } {*Function names can only contain letters, numbers, or underscores(_) and must be at least one character long*}
    """
    try:
        e = r.run(
            "function",
            "load",
            "replace",
            "#!lua name=lib2\n                server.register_function('test\\0test', function() return 1 end)\n            ",
        )
    except Exception as _catch_err:
        e = str(_catch_err)
    # TODO: set _ e
    assert False


@pytest.mark.xfail(reason="not implemented")
def test_libraries_test_registration_with_empty_name(r: ValkeyTestClient) -> None:
    """
    test {LIBRARIES - test registration with empty name} {
        catch {
            r function load replace {#!lua name=lib2
                server.register_function('', function() return 1 end)
            }
        } e
        set _ $e
    } {*Function names can only contain letters, numbers, or underscores(_) and must be at least one character long*}
    """
    try:
        e = r.run(
            "function",
            "load",
            "replace",
            "#!lua name=lib2\n                server.register_function('', function() return 1 end)\n            ",
        )
    except Exception as _catch_err:
        e = str(_catch_err)
    # TODO: set _ e
    assert False


@pytest.mark.xfail(reason="not implemented")
def test_libraries_math_random_from_function_load(r: ValkeyTestClient) -> None:
    """
    test {LIBRARIES - math.random from function load} {
        catch {
            r function load replace {#!lua name=lib2
                return math.random()
            }
        } e
        set _ $e
    } {*attempted to access nonexistent global variable 'math'*}
    """
    try:
        e = r.run("function", "load", "replace", "#!lua name=lib2\n                return math.random()\n            ")
    except Exception as _catch_err:
        e = str(_catch_err)
    # TODO: set _ e
    assert False


@pytest.mark.xfail(reason="not implemented")
def test_libraries_redis_call_from_function_load(r: ValkeyTestClient) -> None:
    """
    test {LIBRARIES - redis.call from function load} {
        catch {
            r function load replace {#!lua name=lib2
                return redis.call('ping')
            }
        } e
        set _ $e
    } {*attempted to access nonexistent global variable 'call'*}
    """
    try:
        e = r.run(
            "function", "load", "replace", "#!lua name=lib2\n                return redis.call('ping')\n            "
        )
    except Exception as _catch_err:
        e = str(_catch_err)
    # TODO: set _ e
    assert False


@pytest.mark.xfail(reason="not implemented")
def test_libraries_redis_setresp_from_function_load(r: ValkeyTestClient) -> None:
    """
    test {LIBRARIES - redis.setresp from function load} {
        catch {
            r function load replace {#!lua name=lib2
                return redis.setresp(3)
            }
        } e
        set _ $e
    } {*attempted to access nonexistent global variable 'setresp'*}
    """
    try:
        e = r.run(
            "function", "load", "replace", "#!lua name=lib2\n                return redis.setresp(3)\n            "
        )
    except Exception as _catch_err:
        e = str(_catch_err)
    # TODO: set _ e
    assert False


@pytest.mark.xfail(reason="not implemented")
def test_libraries_redis_set_repl_from_function_load(r: ValkeyTestClient) -> None:
    """
    test {LIBRARIES - redis.set_repl from function load} {
        catch {
            r function load replace {#!lua name=lib2
                return redis.set_repl(redis.REPL_NONE)
            }
        } e
        set _ $e
    } {*attempted to access nonexistent global variable 'set_repl'*}
    """
    try:
        e = r.run(
            "function",
            "load",
            "replace",
            "#!lua name=lib2\n                return redis.set_repl(redis.REPL_NONE)\n            ",
        )
    except Exception as _catch_err:
        e = str(_catch_err)
    # TODO: set _ e
    assert False


@pytest.mark.xfail(reason="not implemented")
def test_libraries_redis_acl_check_cmd_from_function_load(r: ValkeyTestClient) -> None:
    """
    test {LIBRARIES - redis.acl_check_cmd from function load} {
        catch {
            r function load replace {#!lua name=lib2
                return redis.acl_check_cmd('set','xx',1)
            }
        } e
        set _ $e
    } {*attempted to access nonexistent global variable 'acl_check_cmd'*}
    """
    try:
        e = r.run(
            "function",
            "load",
            "replace",
            "#!lua name=lib2\n                return redis.acl_check_cmd('set','xx',1)\n            ",
        )
    except Exception as _catch_err:
        e = str(_catch_err)
    # TODO: set _ e
    assert False


@pytest.mark.xfail(reason="not implemented")
def test_libraries_malicious_access_test(r: ValkeyTestClient) -> None:
    """
    test {LIBRARIES - malicious access test} {
        # the 'library' API is not exposed inside a
        # function context and the 'redis' API is not
        # expose on the library registration context.
        # But a malicious user might find a way to hack it
        # (as demonstrated in this test). This is why we
        # have another level of protection on the C
        # code itself and we want to test it and verify
        # that it works properly.
        r function load replace {#!lua name=lib1
            local lib = redis
            lib.register_function('f1', function ()
                lib.redis = redis
                lib.math = math
                return {ok='OK'}
            end)

            lib.register_function('f2', function ()
                lib.register_function('f1', function ()
                    lib.redis = redis
                    lib.math = math
                    return {ok='OK'}
                end)
            end)
        }
        catch {[r fcall f1 0]} e
        assert_match {*Attempt to modify a readonly table*} $e

        catch {[r function load {#!lua name=lib2
            redis.math.random()
        }]} e
        assert_match {*Script attempted to access nonexistent global variable 'math'*} $e

        catch {[r function load {#!lua name=lib2
            redis.redis.call('ping')
        }]} e
        assert_match {*Script attempted to access nonexistent global variable 'redis'*} $e

        catch {[r fcall f2 0]} e
        assert_match {*can only be called on FUNCTION LOAD command*} $e
    }
    """
    r.run(
        "function",
        "load",
        "replace",
        "#!lua name=lib1\n            local lib = redis\n            lib.register_function('f1', function ()\n                lib.redis = redis\n                lib.math = math\n                return {ok='OK'}\n            end)\n\n            lib.register_function('f2', function ()\n                lib.register_function('f1', function ()\n                    lib.redis = redis\n                    lib.math = math\n                    return {ok='OK'}\n                end)\n            end)\n        ",
    )
    catch("[r fcall f1 0]", "e")
    # TODO: assert_match {*Attempt to modify a readonly table*} e
    catch("[r function load {#!lua name=lib2\n            redis.math.random()\n        }]", "e")
    # TODO: assert_match {*Script attempted to access nonexistent global variable 'math'*} e
    catch("[r function load {#!lua name=lib2\n            redis.redis.call('ping')\n        }]", "e")
    # TODO: assert_match {*Script attempted to access nonexistent global variable 'redis'*} e
    catch("[r fcall f2 0]", "e")
    # TODO: assert_match {*can only be called on FUNCTION LOAD command*} e


def test_libraries_delete_removed_all_functions_on_library(r: ValkeyTestClient) -> None:
    """
    test {LIBRARIES - delete removed all functions on library} {
        r function delete lib1
        r function list
    } {}
    """
    r.run("function", "delete", "lib1")
    r.run("function", "list")


@pytest.mark.xfail(reason="not implemented")
def test_libraries_register_function_inside_a_function(r: ValkeyTestClient) -> None:
    """
    test {LIBRARIES - register function inside a function} {
        r function load {#!lua name=lib
            server.register_function(
                'f1',
                function(keys, args)
                    server.register_function(
                        'f2',
                        function(key, args)
                            return 2
                        end
                    )
                    return 1
                end
            )
        }
        catch {r fcall f1 0} e
        set _ $e
    } {*attempt to call field 'register_function' (a nil value)*}
    """
    r.run(
        "function",
        "load",
        "#!lua name=lib\n            server.register_function(\n                'f1',\n                function(keys, args)\n                    server.register_function(\n                        'f2',\n                        function(key, args)\n                            return 2\n                        end\n                    )\n                    return 1\n                end\n            )\n        ",
    )
    try:
        e = r.run("fcall", "f1", 0)
    except Exception as _catch_err:
        e = str(_catch_err)
    # TODO: set _ e
    assert False


@pytest.mark.xfail(reason="not implemented")
def test_libraries_register_library_with_no_functions(r: ValkeyTestClient) -> None:
    """
    test {LIBRARIES - register library with no functions} {
        r function flush
        catch {
            r function load {#!lua name=lib
                return 1
            }
        } e
        set _ $e
    } {*No functions registered*}
    """
    r.run("function", "flush")
    try:
        e = r.run("function", "load", "#!lua name=lib\n                return 1\n            ")
    except Exception as _catch_err:
        e = str(_catch_err)
    # TODO: set _ e
    assert False


@pytest.mark.xfail(reason="not implemented")
def test_libraries_load_timeout(r: ValkeyTestClient) -> None:
    """
    test {LIBRARIES - load timeout} {
        catch {
            r function load {#!lua name=lib
                local a = 1
                while 1 do a = a + 1 end
            }
        } e
        set _ $e
    } {*FUNCTION LOAD timeout*}
    """
    try:
        e = r.run(
            "function",
            "load",
            "#!lua name=lib\n                local a = 1\n                while 1 do a = a + 1 end\n            ",
        )
    except Exception as _catch_err:
        e = str(_catch_err)
    # TODO: set _ e
    assert False


@pytest.mark.xfail(reason="not implemented")
def test_libraries_verify_global_protection_on_the_load_run(r: ValkeyTestClient) -> None:
    """
    test {LIBRARIES - verify global protection on the load run} {
        catch {
            r function load {#!lua name=lib
                a = 1
            }
        } e
        set _ $e
    } {*Attempt to modify a readonly table*}
    """
    try:
        e = r.run("function", "load", "#!lua name=lib\n                a = 1\n            ")
    except Exception as _catch_err:
        e = str(_catch_err)
    # TODO: set _ e
    assert False


def test_libraries_named_arguments(r: ValkeyTestClient) -> None:
    """
    test {LIBRARIES - named arguments} {
        r function load {#!lua name=lib
            server.register_function{
                function_name='f1',
                callback=function()
                    return 'hello'
                end,
                description='some desc'
            }
        }
        r function list
    } {{library_name lib engine LUA functions {{name f1 description {some desc} flags {}}}}}
    """
    r.run(
        "function",
        "load",
        "#!lua name=lib\n            server.register_function{\n                function_name='f1',\n                callback=function()\n                    return 'hello'\n                end,\n                description='some desc'\n            }\n        ",
    )
    assert (
        r.run("function", "list")
        == "{library_name lib engine LUA functions {{name f1 description {some desc} flags {}}}}"
    )


@pytest.mark.xfail(reason="not implemented")
def test_libraries_named_arguments_bad_function_name(r: ValkeyTestClient) -> None:
    """
    test {LIBRARIES - named arguments, bad function name} {
        catch {
            r function load replace {#!lua name=lib
                server.register_function{
                    function_name=function() return 1 end,
                    callback=function()
                        return 'hello'
                    end,
                    description='some desc'
                }
            }
        } e
        set _ $e
    } {*function_name argument given to server.register_function must be a string*}
    """
    try:
        e = r.run(
            "function",
            "load",
            "replace",
            "#!lua name=lib\n                server.register_function{\n                    function_name=function() return 1 end,\n                    callback=function()\n                        return 'hello'\n                    end,\n                    description='some desc'\n                }\n            ",
        )
    except Exception as _catch_err:
        e = str(_catch_err)
    # TODO: set _ e
    assert False


@pytest.mark.xfail(reason="not implemented")
def test_libraries_named_arguments_bad_callback_type(r: ValkeyTestClient) -> None:
    """
    test {LIBRARIES - named arguments, bad callback type} {
        catch {
            r function load replace {#!lua name=lib
                server.register_function{
                    function_name='f1',
                    callback='bad',
                    description='some desc'
                }
            }
        } e
        set _ $e
    } {*callback argument given to server.register_function must be a function*}
    """
    try:
        e = r.run(
            "function",
            "load",
            "replace",
            "#!lua name=lib\n                server.register_function{\n                    function_name='f1',\n                    callback='bad',\n                    description='some desc'\n                }\n            ",
        )
    except Exception as _catch_err:
        e = str(_catch_err)
    # TODO: set _ e
    assert False


@pytest.mark.xfail(reason="not implemented")
def test_libraries_named_arguments_bad_description(r: ValkeyTestClient) -> None:
    """
    test {LIBRARIES - named arguments, bad description} {
        catch {
            r function load replace {#!lua name=lib
                server.register_function{
                    function_name='f1',
                    callback=function()
                        return 'hello'
                    end,
                    description=function() return 1 end
                }
            }
        } e
        set _ $e
    } {*description argument given to server.register_function must be a string*}
    """
    try:
        e = r.run(
            "function",
            "load",
            "replace",
            "#!lua name=lib\n                server.register_function{\n                    function_name='f1',\n                    callback=function()\n                        return 'hello'\n                    end,\n                    description=function() return 1 end\n                }\n            ",
        )
    except Exception as _catch_err:
        e = str(_catch_err)
    # TODO: set _ e
    assert False


@pytest.mark.xfail(reason="not implemented")
def test_libraries_named_arguments_unknown_argument(r: ValkeyTestClient) -> None:
    """
    test {LIBRARIES - named arguments, unknown argument} {
        catch {
            r function load replace {#!lua name=lib
                server.register_function{
                    function_name='f1',
                    callback=function()
                        return 'hello'
                    end,
                    description='desc',
                    some_unknown='unknown'
                }
            }
        } e
        set _ $e
    } {*unknown argument given to server.register_function*}
    """
    try:
        e = r.run(
            "function",
            "load",
            "replace",
            "#!lua name=lib\n                server.register_function{\n                    function_name='f1',\n                    callback=function()\n                        return 'hello'\n                    end,\n                    description='desc',\n                    some_unknown='unknown'\n                }\n            ",
        )
    except Exception as _catch_err:
        e = str(_catch_err)
    # TODO: set _ e
    assert False


@pytest.mark.xfail(reason="not implemented")
def test_libraries_named_arguments_missing_function_name(r: ValkeyTestClient) -> None:
    """
    test {LIBRARIES - named arguments, missing function name} {
        catch {
            r function load replace {#!lua name=lib
                server.register_function{
                    callback=function()
                        return 'hello'
                    end,
                    description='desc'
                }
            }
        } e
        set _ $e
    } {*server.register_function must get a function name argument*}
    """
    try:
        e = r.run(
            "function",
            "load",
            "replace",
            "#!lua name=lib\n                server.register_function{\n                    callback=function()\n                        return 'hello'\n                    end,\n                    description='desc'\n                }\n            ",
        )
    except Exception as _catch_err:
        e = str(_catch_err)
    # TODO: set _ e
    assert False


@pytest.mark.xfail(reason="not implemented")
def test_libraries_named_arguments_missing_callback(r: ValkeyTestClient) -> None:
    """
    test {LIBRARIES - named arguments, missing callback} {
        catch {
            r function load replace {#!lua name=lib
                server.register_function{
                    function_name='f1',
                    description='desc'
                }
            }
        } e
        set _ $e
    } {*server.register_function must get a callback argument*}
    """
    try:
        e = r.run(
            "function",
            "load",
            "replace",
            "#!lua name=lib\n                server.register_function{\n                    function_name='f1',\n                    description='desc'\n                }\n            ",
        )
    except Exception as _catch_err:
        e = str(_catch_err)
    # TODO: set _ e
    assert False


def test_function_test_function_restore_with_function_name_collision(r: ValkeyTestClient) -> None:
    """
    test {FUNCTION - test function restore with function name collision} {
        r function flush
        r function load {#!lua name=lib1
            local function add1(a)
                return a + 1
            end
            server.register_function(
                'f1',
                function(keys, args)
                    return add1(1)
                end
            )
            server.register_function(
                'f2',
                function(keys, args)
                    return add1(2)
                end
            )
            server.register_function(
                'f3',
                function(keys, args)
                    return add1(3)
                end
            )
        }
        set e [r function dump]
        r function flush

        # load a library with different name but with the same function name
        r function load {#!lua name=lib1
            server.register_function(
                'f6',
                function(keys, args)
                    return 7
                end
            )
        }
        r function load {#!lua name=lib2
            local function add1(a)
                return a + 1
            end
            server.register_function(
                'f4',
                function(keys, args)
                    return add1(4)
                end
            )
            server.register_function(
                'f5',
                function(keys, args)
                    return add1(5)
                end
            )
            server.register_function(
                'f3',
                function(keys, args)
                    return add1(3)
                end
            )
        }

        catch {r function restore $e} error
        assert_match {*Library lib1 already exists*} $error
        assert_equal [r fcall f3 0] {4}
        assert_equal [r fcall f4 0] {5}
        assert_equal [r fcall f5 0] {6}
        assert_equal [r fcall f6 0] {7}

        catch {r function restore $e replace} error
        assert_match {*Function f3 already exists*} $error
        assert_equal [r fcall f3 0] {4}
        assert_equal [r fcall f4 0] {5}
        assert_equal [r fcall f5 0] {6}
        assert_equal [r fcall f6 0] {7}
    }
    """
    r.run("function", "flush")
    r.run(
        "function",
        "load",
        "#!lua name=lib1\n            local function add1(a)\n                return a + 1\n            end\n            server.register_function(\n                'f1',\n                function(keys, args)\n                    return add1(1)\n                end\n            )\n            server.register_function(\n                'f2',\n                function(keys, args)\n                    return add1(2)\n                end\n            )\n            server.register_function(\n                'f3',\n                function(keys, args)\n                    return add1(3)\n                end\n            )\n        ",
    )
    e = r.run("function", "dump")
    r.run("function", "flush")
    r.run(
        "function",
        "load",
        "#!lua name=lib1\n            server.register_function(\n                'f6',\n                function(keys, args)\n                    return 7\n                end\n            )\n        ",
    )
    r.run(
        "function",
        "load",
        "#!lua name=lib2\n            local function add1(a)\n                return a + 1\n            end\n            server.register_function(\n                'f4',\n                function(keys, args)\n                    return add1(4)\n                end\n            )\n            server.register_function(\n                'f5',\n                function(keys, args)\n                    return add1(5)\n                end\n            )\n            server.register_function(\n                'f3',\n                function(keys, args)\n                    return add1(3)\n                end\n            )\n        ",
    )
    try:
        error = r.run("function", "restore", e)
    except Exception as _catch_err:
        error = str(_catch_err)
    assert fnmatch(str(error), "*Library lib1 already exists*")
    assert r.run("fcall", "f3", 0) == "4"
    assert r.run("fcall", "f4", 0) == "5"
    assert r.run("fcall", "f5", 0) == "6"
    assert r.run("fcall", "f6", 0) == "7"
    try:
        error = r.run("function", "restore", e, "replace")
    except Exception as _catch_err:
        error = str(_catch_err)
    assert fnmatch(str(error), "*Function f3 already exists*")
    assert r.run("fcall", "f3", 0) == "4"
    assert r.run("fcall", "f4", 0) == "5"
    assert r.run("fcall", "f5", 0) == "6"
    assert r.run("fcall", "f6", 0) == "7"


def test_function_test_function_list_with_code(r: ValkeyTestClient) -> None:
    """
    test {FUNCTION - test function list with code} {
        r function flush
        r function load {#!lua name=library1
            server.register_function('f6', function(keys, args) return 7 end)
        }
        r function list withcode
    } {{library_name library1 engine LUA functions {{name f6 description {} flags {}}} library_code {*server.register_function('f6', function(keys, args) return 7 end)*}}}
    """
    r.run("function", "flush")
    r.run(
        "function",
        "load",
        "#!lua name=library1\n            server.register_function('f6', function(keys, args) return 7 end)\n        ",
    )
    assert (
        r.run("function", "list", "withcode")
        == "{library_name library1 engine LUA functions {{name f6 description {} flags {}}} library_code {*server.register_function('f6', function(keys, args) return 7 end)*}}"
    )


def test_function_test_function_list_with_pattern(r: ValkeyTestClient) -> None:
    """
    test {FUNCTION - test function list with pattern} {
        r function load {#!lua name=lib1
            server.register_function('f7', function(keys, args) return 7 end)
        }
        r function list libraryname library*
    } {{library_name library1 engine LUA functions {{name f6 description {} flags {}}}}}
    """
    r.run(
        "function",
        "load",
        "#!lua name=lib1\n            server.register_function('f7', function(keys, args) return 7 end)\n        ",
    )
    assert (
        r.run("function", "list", "libraryname", "library*")
        == "{library_name library1 engine LUA functions {{name f6 description {} flags {}}}}"
    )


@pytest.mark.xfail(reason="not implemented")
def test_function_test_function_list_wrong_argument(r: ValkeyTestClient) -> None:
    """
    test {FUNCTION - test function list wrong argument} {
        catch {r function list bad_argument} e
        set _ $e
    } {*Unknown argument bad_argument*}
    """
    try:
        e = r.run("function", "list", "bad_argument")
    except Exception as _catch_err:
        e = str(_catch_err)
    # TODO: set _ e
    assert False


@pytest.mark.xfail(reason="not implemented")
def test_function_test_function_list_with_bad_argument_to_library_name(r: ValkeyTestClient) -> None:
    """
    test {FUNCTION - test function list with bad argument to library name} {
        catch {r function list libraryname} e
        set _ $e
    } {*library name argument was not given*}
    """
    try:
        e = r.run("function", "list", "libraryname")
    except Exception as _catch_err:
        e = str(_catch_err)
    # TODO: set _ e
    assert False


@pytest.mark.xfail(reason="not implemented")
def test_function_test_function_list_withcode_multiple_times(r: ValkeyTestClient) -> None:
    """
    test {FUNCTION - test function list withcode multiple times} {
        catch {r function list withcode withcode} e
        set _ $e
    } {*Unknown argument withcode*}
    """
    try:
        e = r.run("function", "list", "withcode", "withcode")
    except Exception as _catch_err:
        e = str(_catch_err)
    # TODO: set _ e
    assert False


@pytest.mark.xfail(reason="not implemented")
def test_function_test_function_list_libraryname_multiple_times(r: ValkeyTestClient) -> None:
    """
    test {FUNCTION - test function list libraryname multiple times} {
        catch {r function list withcode libraryname foo libraryname foo} e
        set _ $e
    } {*Unknown argument libraryname*}
    """
    try:
        e = r.run("function", "list", "withcode", "libraryname", "foo", "libraryname", "foo")
    except Exception as _catch_err:
        e = str(_catch_err)
    # TODO: set _ e
    assert False


def test_function_verify_oom_on_function_load_and_function_restore(r: ValkeyTestClient) -> None:
    """
    test {FUNCTION - verify OOM on function load and function restore} {
        r function flush
        r function load replace {#!lua name=test
            server.register_function('f1', function() return 1 end)
        }
        set payload [r function dump]
        r config set maxmemory 1

        r function flush
        catch {r function load replace {#!lua name=test
            server.register_function('f1', function() return 1 end)
        }} e
        assert_match {*command not allowed when used memory*} $e

        r function flush
        catch {r function restore $payload} e
        assert_match {*command not allowed when used memory*} $e

        r config set maxmemory 0
    } {OK} {needs:config-maxmemory}
    """
    r.run("function", "flush")
    r.run(
        "function",
        "load",
        "replace",
        "#!lua name=test\n            server.register_function('f1', function() return 1 end)\n        ",
    )
    payload = r.run("function", "dump")
    r.run("config", "set", "maxmemory", 1)
    r.run("function", "flush")
    try:
        e = r.run(
            "function",
            "load",
            "replace",
            "#!lua name=test\n            server.register_function('f1', function() return 1 end)\n        ",
        )
    except Exception as _catch_err:
        e = str(_catch_err)
    assert fnmatch(str(e), "*command not allowed when used memory*")
    r.run("function", "flush")
    try:
        e = r.run("function", "restore", payload)
    except Exception as _catch_err:
        e = str(_catch_err)
    assert fnmatch(str(e), "*command not allowed when used memory*")
    assert r.run("config", "set", "maxmemory", 0) == "OK"


def test_function_verify_allow_omm_allows_running_any_command(r: ValkeyTestClient) -> None:
    """
    test {FUNCTION - verify allow-omm allows running any command} {
        r FUNCTION load replace {#!lua name=f1
            server.register_function{
                function_name='f1',
                callback=function() return redis.call('set', 'x', '1') end,
                flags={'allow-oom'}
            }
        }

        r config set maxmemory 1

        assert_match {OK} [r fcall f1 1 x]
        assert_match {1} [r get x]

        r config set maxmemory 0
    } {OK} {needs:config-maxmemory}
    """
    r.run(
        "FUNCTION",
        "load",
        "replace",
        "#!lua name=f1\n            server.register_function{\n                function_name='f1',\n                callback=function() return redis.call('set', 'x', '1') end,\n                flags={'allow-oom'}\n            }\n        ",
    )
    r.run("config", "set", "maxmemory", 1)
    assert fnmatch(str(r.run("fcall", "f1", 1, "x")), "OK")
    assert fnmatch(str(r.run("get", "x")), "1")
    assert r.run("config", "set", "maxmemory", 0) == "OK"


pytestmark = [pytest.mark.scripting]


@pytest.mark.xfail(reason="not implemented")
def test_function_wrong_flags_type_named_arguments(r: ValkeyTestClient) -> None:
    """
    test {FUNCTION - wrong flags type named arguments} {
        catch {r function load replace {#!lua name=test
            server.register_function{
                function_name = 'f1',
                callback = function() return 1 end,
                flags = 'bad flags type'
            }
        }} e
        set _ $e
    } {*flags argument to server.register_function must be a table representing function flags*}
    """
    try:
        e = r.run(
            "function",
            "load",
            "replace",
            "#!lua name=test\n            server.register_function{\n                function_name = 'f1',\n                callback = function() return 1 end,\n                flags = 'bad flags type'\n            }\n        ",
        )
    except Exception as _catch_err:
        e = str(_catch_err)
    # TODO: set _ e
    assert False


@pytest.mark.xfail(reason="not implemented")
def test_function_wrong_flag_type(r: ValkeyTestClient) -> None:
    """
    test {FUNCTION - wrong flag type} {
        catch {r function load replace {#!lua name=test
            server.register_function{
                function_name = 'f1',
                callback = function() return 1 end,
                flags = {function() return 1 end}
            }
        }} e
        set _ $e
    } {*unknown flag given*}
    """
    try:
        e = r.run(
            "function",
            "load",
            "replace",
            "#!lua name=test\n            server.register_function{\n                function_name = 'f1',\n                callback = function() return 1 end,\n                flags = {function() return 1 end}\n            }\n        ",
        )
    except Exception as _catch_err:
        e = str(_catch_err)
    # TODO: set _ e
    assert False


@pytest.mark.xfail(reason="not implemented")
def test_function_unknown_flag(r: ValkeyTestClient) -> None:
    """
    test {FUNCTION - unknown flag} {
        catch {r function load replace {#!lua name=test
            server.register_function{
                function_name = 'f1',
                callback = function() return 1 end,
                flags = {'unknown'}
            }
        }} e
        set _ $e
    } {*unknown flag given*}
    """
    try:
        e = r.run(
            "function",
            "load",
            "replace",
            "#!lua name=test\n            server.register_function{\n                function_name = 'f1',\n                callback = function() return 1 end,\n                flags = {'unknown'}\n            }\n        ",
        )
    except Exception as _catch_err:
        e = str(_catch_err)
    # TODO: set _ e
    assert False


@pytest.mark.xfail(reason="not implemented")
def test_function_write_script_on_fcall_ro(r: ValkeyTestClient) -> None:
    """
    test {FUNCTION - write script on fcall_ro} {
        r function load replace {#!lua name=test
            server.register_function{
                function_name = 'f1',
                callback = function() return redis.call('set', 'x', 1) end
            }
        }
        catch {r fcall_ro f1 1 x} e
        set _ $e
    } {*Can not execute a script with write flag using \*_ro command*}
    """
    r.run(
        "function",
        "load",
        "replace",
        "#!lua name=test\n            server.register_function{\n                function_name = 'f1',\n                callback = function() return redis.call('set', 'x', 1) end\n            }\n        ",
    )
    try:
        e = r.run("fcall_ro", "f1", 1, "x")
    except Exception as _catch_err:
        e = str(_catch_err)
    # TODO: set _ e
    assert False


@pytest.mark.xfail(reason="not implemented")
def test_function_write_script_with_no_writes_flag(r: ValkeyTestClient) -> None:
    """
    test {FUNCTION - write script with no-writes flag} {
        r function load replace {#!lua name=test
            server.register_function{
                function_name = 'f1',
                callback = function() return redis.call('set', 'x', 1) end,
                flags = {'no-writes'}
            }
        }
        catch {r fcall f1 1 x} e
        set _ $e
    } {*Write commands are not allowed from read-only scripts*}
    """
    r.run(
        "function",
        "load",
        "replace",
        "#!lua name=test\n            server.register_function{\n                function_name = 'f1',\n                callback = function() return redis.call('set', 'x', 1) end,\n                flags = {'no-writes'}\n            }\n        ",
    )
    try:
        e = r.run("fcall", "f1", 1, "x")
    except Exception as _catch_err:
        e = str(_catch_err)
    # TODO: set _ e
    assert False


@pytest.mark.xfail(reason="not implemented")
def test_function_deny_oom(r: ValkeyTestClient) -> None:
    """
    test {FUNCTION - deny oom} {
        r FUNCTION load replace {#!lua name=test
            server.register_function('f1', function() return redis.call('set', 'x', '1') end)
        }

        r config set maxmemory 1

        catch {[r fcall f1 1 x]} e
        assert_match {OOM *when used memory > 'maxmemory'*} $e

        r config set maxmemory 0
    } {OK} {needs:config-maxmemory}
    """
    r.run(
        "FUNCTION",
        "load",
        "replace",
        "#!lua name=test\n            server.register_function('f1', function() return redis.call('set', 'x', '1') end)\n        ",
    )
    r.run("config", "set", "maxmemory", 1)
    catch("[r fcall f1 1 x]", "e")
    # TODO: assert_match {OOM *when used memory > 'maxmemory'*} e
    assert r.run("config", "set", "maxmemory", 0) == "OK"


def test_function_deny_oom_on_no_writes_function(r: ValkeyTestClient) -> None:
    """
    test {FUNCTION - deny oom on no-writes function} {
        r FUNCTION load replace {#!lua name=test
            server.register_function{function_name='f1', callback=function() return 'hello' end, flags={'no-writes'}}
        }

        r config set maxmemory 1

        assert_equal [r fcall f1 1 k] hello
        assert_equal [r fcall_ro f1 1 k] hello

        r config set maxmemory 0
    } {OK} {needs:config-maxmemory}
    """
    r.run(
        "FUNCTION",
        "load",
        "replace",
        "#!lua name=test\n            server.register_function{function_name='f1', callback=function() return 'hello' end, flags={'no-writes'}}\n        ",
    )
    r.run("config", "set", "maxmemory", 1)
    assert r.run("fcall", "f1", 1, "k") == "hello"
    assert r.run("fcall_ro", "f1", 1, "k") == "hello"
    assert r.run("config", "set", "maxmemory", 0) == "OK"


@pytest.mark.xfail(reason="not implemented")
def test_function_allow_stale(r: ValkeyTestClient) -> None:
    """
    test {FUNCTION - allow stale} {
        r FUNCTION load replace {#!lua name=test
            server.register_function{function_name='f1', callback=function() return 'hello' end, flags={'no-writes'}}
            server.register_function{function_name='f2', callback=function() return 'hello' end, flags={'allow-stale', 'no-writes'}}
            server.register_function{function_name='f3', callback=function() return redis.call('get', 'x') end, flags={'allow-stale', 'no-writes'}}
            server.register_function{function_name='f4', callback=function() return redis.call('info', 'server') end, flags={'allow-stale', 'no-writes'}}
        }

        r config set replica-serve-stale-data no
        r replicaof 127.0.0.1 1

        catch {[r fcall f1 0]} e
        assert_match {MASTERDOWN *} $e

        assert_equal {hello} [r fcall f2 0]

        catch {[r fcall f3 1 x]} e
        assert_match {ERR *Can not execute the command on a stale replica*} $e

        assert_match {*redis_version*} [r fcall f4 0]

        r replicaof no one
        r config set replica-serve-stale-data yes
        set _ {}
    } {} {external:skip}
    """
    r.run(
        "FUNCTION",
        "load",
        "replace",
        "#!lua name=test\n            server.register_function{function_name='f1', callback=function() return 'hello' end, flags={'no-writes'}}\n            server.register_function{function_name='f2', callback=function() return 'hello' end, flags={'allow-stale', 'no-writes'}}\n            server.register_function{function_name='f3', callback=function() return redis.call('get', 'x') end, flags={'allow-stale', 'no-writes'}}\n            server.register_function{function_name='f4', callback=function() return redis.call('info', 'server') end, flags={'allow-stale', 'no-writes'}}\n        ",
    )
    r.run("config", "set", "replica-serve-stale-data", "no")
    r.run("replicaof", "127.0.0.1", 1)
    catch("[r fcall f1 0]", "e")
    # TODO: assert_match {MASTERDOWN *} e
    assert "hello" == r.run("fcall", "f2", 0)
    catch("[r fcall f3 1 x]", "e")
    # TODO: assert_match {ERR *Can not execute the command on a stale replica*} e
    assert fnmatch(str(r.run("fcall", "f4", 0)), "*redis_version*")
    r.run("replicaof", "no", "one")
    r.run("config", "set", "replica-serve-stale-data", "yes")
    _ = ""


def test_function_valkey_version_api(r: ValkeyTestClient) -> None:
    """
    test {FUNCTION - valkey version api} {
        r FUNCTION load replace {#!lua name=test
            local version = redis.REDIS_VERSION_NUM

            server.register_function{function_name='get_version_v1', callback=function()
              return string.format('%s.%s.%s',
                                    bit.band(bit.rshift(version, 16), 0x000000ff),
                                    bit.band(bit.rshift(version, 8), 0x000000ff),
                                    bit.band(version, 0x000000ff))
            end}
            server.register_function{function_name='get_version_v2', callback=function() return redis.REDIS_VERSION end}
        }

        catch {[r fcall f1 0]} e
        assert_equal  [r fcall get_version_v1 0] [r fcall get_version_v2 0]
    }
    """
    r.run(
        "FUNCTION",
        "load",
        "replace",
        "#!lua name=test\n            local version = redis.REDIS_VERSION_NUM\n\n            server.register_function{function_name='get_version_v1', callback=function()\n              return string.format('%s.%s.%s',\n                                    bit.band(bit.rshift(version, 16), 0x000000ff),\n                                    bit.band(bit.rshift(version, 8), 0x000000ff),\n                                    bit.band(version, 0x000000ff))\n            end}\n            server.register_function{function_name='get_version_v2', callback=function() return redis.REDIS_VERSION end}\n        ",
    )
    catch("[r fcall f1 0]", "e")
    assert r.run("fcall", "get_version_v1", 0) == r.run("fcall", "get_version_v2", 0)


def test_function_function_stats(r: ValkeyTestClient) -> None:
    """
    test {FUNCTION - function stats} {
        r FUNCTION FLUSH

        r FUNCTION load {#!lua name=test1
            server.register_function('f1', function() return 1 end)
            server.register_function('f2', function() return 1 end)
        }

        r FUNCTION load {#!lua name=test2
            server.register_function('f3', function() return 1 end)
        }

        r function stats
    } {running_script {} engines {LUA {libraries_count 2 functions_count 3}}}
    """
    r.run("FUNCTION", "FLUSH")
    r.run(
        "FUNCTION",
        "load",
        "#!lua name=test1\n            server.register_function('f1', function() return 1 end)\n            server.register_function('f2', function() return 1 end)\n        ",
    )
    r.run(
        "FUNCTION",
        "load",
        "#!lua name=test2\n            server.register_function('f3', function() return 1 end)\n        ",
    )
    assert r.run("function", "stats") == "running_script {} engines {LUA {libraries_count 2 functions_count 3}}"


def test_function_function_stats_reloaded_correctly_from_rdb(r: ValkeyTestClient) -> None:
    """
    test {FUNCTION - function stats reloaded correctly from rdb} {
        r debug reload
        r function stats
    } {running_script {} engines {LUA {libraries_count 2 functions_count 3}}} {needs:debug}
    """
    r.run("debug", "reload")
    assert r.run("function", "stats") == "running_script {} engines {LUA {libraries_count 2 functions_count 3}}"


def test_function_function_stats_delete_library(r: ValkeyTestClient) -> None:
    """
    test {FUNCTION - function stats delete library} {
        r function delete test1
        r function stats
    } {running_script {} engines {LUA {libraries_count 1 functions_count 1}}}
    """
    r.run("function", "delete", "test1")
    assert r.run("function", "stats") == "running_script {} engines {LUA {libraries_count 1 functions_count 1}}"


def test_function_test_function_stats_on_loading_failure(r: ValkeyTestClient) -> None:
    """
    test {FUNCTION - test function stats on loading failure} {
        r FUNCTION FLUSH

        r FUNCTION load {#!lua name=test1
            server.register_function('f1', function() return 1 end)
            server.register_function('f2', function() return 1 end)
        }

        catch {r FUNCTION load {#!lua name=test1
            server.register_function('f3', function() return 1 end)
        }} e
        assert_match "*Library 'test1' already exists*" $e


        r function stats
    } {running_script {} engines {LUA {libraries_count 1 functions_count 2}}}
    """
    r.run("FUNCTION", "FLUSH")
    r.run(
        "FUNCTION",
        "load",
        "#!lua name=test1\n            server.register_function('f1', function() return 1 end)\n            server.register_function('f2', function() return 1 end)\n        ",
    )
    try:
        e = r.run(
            "FUNCTION",
            "load",
            "#!lua name=test1\n            server.register_function('f3', function() return 1 end)\n        ",
        )
    except Exception as _catch_err:
        e = str(_catch_err)
    assert fnmatch(str(e), "*Library 'test1' already exists*")
    assert r.run("function", "stats") == "running_script {} engines {LUA {libraries_count 1 functions_count 2}}"


def test_function_function_stats_cleaned_after_flush(r: ValkeyTestClient) -> None:
    """
    test {FUNCTION - function stats cleaned after flush} {
        r function flush
        r function stats
    } {running_script {} engines {LUA {libraries_count 0 functions_count 0}}}
    """
    r.run("function", "flush")
    assert r.run("function", "stats") == "running_script {} engines {LUA {libraries_count 0 functions_count 0}}"


@pytest.mark.xfail(reason="not implemented")
def test_function_function_test_empty_engine(r: ValkeyTestClient) -> None:
    """
    test {FUNCTION - function test empty engine} {
        catch {r function load replace {#! name=test
            server.register_function('foo', function() return 1 end)
        }} e
        set _ $e
    } {ERR Engine '' not found}
    """
    try:
        e = r.run(
            "function",
            "load",
            "replace",
            "#! name=test\n            server.register_function('foo', function() return 1 end)\n        ",
        )
    except Exception as _catch_err:
        e = str(_catch_err)
    # TODO: set _ e
    assert False


@pytest.mark.xfail(reason="not implemented")
def test_function_function_test_unknown_metadata_value(r: ValkeyTestClient) -> None:
    """
    test {FUNCTION - function test unknown metadata value} {
        catch {r function load replace {#!lua name=test foo=bar
            server.register_function('foo', function() return 1 end)
        }} e
        set _ $e
    } {ERR Invalid metadata value given: foo=bar}
    """
    try:
        e = r.run(
            "function",
            "load",
            "replace",
            "#!lua name=test foo=bar\n            server.register_function('foo', function() return 1 end)\n        ",
        )
    except Exception as _catch_err:
        e = str(_catch_err)
    # TODO: set _ e
    assert False


@pytest.mark.xfail(reason="not implemented")
def test_function_function_test_no_name(r: ValkeyTestClient) -> None:
    """
    test {FUNCTION - function test no name} {
        catch {r function load replace {#!lua
            server.register_function('foo', function() return 1 end)
        }} e
        set _ $e
    } {ERR Library name was not given}
    """
    try:
        e = r.run(
            "function",
            "load",
            "replace",
            "#!lua\n            server.register_function('foo', function() return 1 end)\n        ",
        )
    except Exception as _catch_err:
        e = str(_catch_err)
    # TODO: set _ e
    assert False


@pytest.mark.xfail(reason="not implemented")
def test_function_function_test_multiple_names(r: ValkeyTestClient) -> None:
    """
    test {FUNCTION - function test multiple names} {
        catch {r function load replace {#!lua name=foo name=bar
            server.register_function('foo', function() return 1 end)
        }} e
        set _ $e
    } {ERR Invalid metadata value, name argument was given multiple times}
    """
    try:
        e = r.run(
            "function",
            "load",
            "replace",
            "#!lua name=foo name=bar\n            server.register_function('foo', function() return 1 end)\n        ",
        )
    except Exception as _catch_err:
        e = str(_catch_err)
    # TODO: set _ e
    assert False


def test_function_function_test_name_with_quotes(r: ValkeyTestClient) -> None:
    """
    test {FUNCTION - function test name with quotes} {
        r function load replace {#!lua name="foo"
            server.register_function('foo', function() return 1 end)
        }
    } {foo}
    """
    assert (
        r.run(
            "function",
            "load",
            "replace",
            "#!lua name=\"foo\"\n            server.register_function('foo', function() return 1 end)\n        ",
        )
        == "foo"
    )


@pytest.mark.xfail(reason="not implemented")
def test_function_trick_global_protection_1(r: ValkeyTestClient) -> None:
    """
    test {FUNCTION - trick global protection 1} {
        r FUNCTION FLUSH

        r FUNCTION load {#!lua name=test1
            server.register_function('f1', function()
                mt = getmetatable(_G)
                original_globals = mt.__index
                original_globals['redis'] = function() return 1 end
            end)
        }

        catch {[r fcall f1 0]} e
        set _ $e
    } {*Attempt to modify a readonly table*}
    """
    r.run("FUNCTION", "FLUSH")
    r.run(
        "FUNCTION",
        "load",
        "#!lua name=test1\n            server.register_function('f1', function()\n                mt = getmetatable(_G)\n                original_globals = mt.__index\n                original_globals['redis'] = function() return 1 end\n            end)\n        ",
    )
    catch("[r fcall f1 0]", "e")
    # TODO: set _ e
    assert False


@pytest.mark.xfail(reason="not implemented")
def test_function_test_getmetatable_on_script_load(r: ValkeyTestClient) -> None:
    """
    test {FUNCTION - test getmetatable on script load} {
        r FUNCTION FLUSH

        catch {
            r FUNCTION load {#!lua name=test1
                mt = getmetatable(_G)
            }
        } e

        set _ $e
    } {*Script attempted to access nonexistent global variable 'getmetatable'*}
    """
    r.run("FUNCTION", "FLUSH")
    try:
        e = r.run("FUNCTION", "load", "#!lua name=test1\n                mt = getmetatable(_G)\n            ")
    except Exception as _catch_err:
        e = str(_catch_err)
    # TODO: set _ e
    assert False


# --- stubs for unimplemented TCL helpers ---


def assert_error(*args):
    raise NotImplementedError("assert_error")


def assert_lessthan(*args):
    raise NotImplementedError("assert_lessthan")


def catch(*args):
    raise NotImplementedError("catch")


def get_function_code(*args):
    raise NotImplementedError("get_function_code")


def get_no_writes_function_code(*args):
    raise NotImplementedError("get_no_writes_function_code")


def s(*args):
    raise NotImplementedError("s")


def valkey_deferring_client(*args):
    raise NotImplementedError("valkey_deferring_client")
