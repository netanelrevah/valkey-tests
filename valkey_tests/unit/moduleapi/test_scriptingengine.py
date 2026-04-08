# ruff: noqa: PLR2004, RUF043, ANN002, ANN201
import time
from fnmatch import fnmatch

import pytest

from tests.valkey_test_client import ValkeyTestClient

"""
set testmodule file normalize tests/modules/helloscripting.so
"""


"""
set HELLO_PROGRAM "#!hello name=mylib\nRFUNCTION foo\nARGS 0\nRETURN\nFUNCTION bar\nCONSTI 432\nRETURN"
"""

pytestmark = [pytest.mark.modules]


"""
r module load testmodule
"""


"""
r function load HELLO_PROGRAM
"""


def test_load_script_with_invalid_library_name(r: ValkeyTestClient) -> None:
    """
    test {Load script with invalid library name} {
        assert_error {ERR Library names can only contain letters, numbers, or underscores(_) and must be at least one character long} {r function load "#!hello name=my-lib\nFUNCTION foo\nARGS 0\nRETURN"}
    }
    """
    with pytest.raises(
        Exception,
        match="ERR\\ Library\\ names\\ can\\ only\\ contain\\ letters,\\ numbers,\\ or\\ underscores\\(_\\)\\ and\\ must\\ be\\ at\\ least\\ one\\ character\\ long",
    ):
        r.run("function", "load", "#!hello name=my-lib\nFUNCTION foo\nARGS 0\nRETURN")


def test_load_script_with_existing_library(r: ValkeyTestClient) -> None:
    """
    test {Load script with existing library} {
        assert_error {ERR Library 'mylib' already exists} {r function load $HELLO_PROGRAM}
    }
    """
    assert_error("ERR Library 'mylib' already exists", "r function load $HELLO_PROGRAM")


def test_load_script_with_invalid_engine(r: ValkeyTestClient) -> None:
    """
    test {Load script with invalid engine} {
        assert_error {ERR Engine 'wasm' not found} {r function load "#!wasm name=mylib2\nFUNCTION foo\nARGS 0\nRETURN"}
    }
    """
    with pytest.raises(Exception, match="ERR\\ Engine\\ 'wasm'\\ not\\ found"):
        r.run("function", "load", "#!wasm name=mylib2\nFUNCTION foo\nARGS 0\nRETURN")


def test_load_script_with_no_functions(r: ValkeyTestClient) -> None:
    """
    test {Load script with no functions} {
        assert_error {ERR No functions registered} {r function load "#!hello name=mylib2\n"}
    }
    """
    with pytest.raises(Exception, match="ERR\\ No\\ functions\\ registered"):
        r.run("function", "load", "#!hello name=mylib2\n")


def test_load_script_with_duplicate_function(r: ValkeyTestClient) -> None:
    """
    test {Load script with duplicate function} {
        assert_error {ERR Function foo already exists} {r function load "#!hello name=mylib2\nFUNCTION foo\nARGS 0\nRETURN"}
    }
    """
    with pytest.raises(Exception, match="ERR\\ Function\\ foo\\ already\\ exists"):
        r.run("function", "load", "#!hello name=mylib2\nFUNCTION foo\nARGS 0\nRETURN")


def test_load_script_with_no_metadata_header(r: ValkeyTestClient) -> None:
    """
    test {Load script with no metadata header} {
        assert_error {ERR Missing library metadata} {r function load "FUNCTION foo\nARGS 0\nRETURN"}
    }
    """
    with pytest.raises(Exception, match="ERR\\ Missing\\ library\\ metadata"):
        r.run("function", "load", "FUNCTION foo\nARGS 0\nRETURN")


def test_load_script_with_header_without_lib_name(r: ValkeyTestClient) -> None:
    """
    test {Load script with header without lib name} {
        assert_error {ERR Library name was not given} {r function load "#!hello \n"}
    }
    """
    with pytest.raises(Exception, match="ERR\\ Library\\ name\\ was\\ not\\ given"):
        r.run("function", "load", "#!hello \n")


def test_load_script_with_header_with_unknown_param(r: ValkeyTestClient) -> None:
    """
    test {Load script with header with unknown param} {
        assert_error {ERR Invalid metadata value given: nme=mylib} {r function load "#!hello nme=mylib\n"}
    }
    """
    with pytest.raises(Exception, match="ERR\\ Invalid\\ metadata\\ value\\ given:\\ nme=mylib"):
        r.run("function", "load", "#!hello nme=mylib\n")


def test_load_script_with_header_with_lib_name_passed_twice(r: ValkeyTestClient) -> None:
    """
    test {Load script with header with lib name passed twice} {
        assert_error {ERR Invalid metadata value, name argument was given multiple times} {r function load "#!hello name=mylib2 name=mylib3\n"}
    }
    """
    with pytest.raises(
        Exception, match="ERR\\ Invalid\\ metadata\\ value,\\ name\\ argument\\ was\\ given\\ multiple\\ times"
    ):
        r.run("function", "load", "#!hello name=mylib2 name=mylib3\n")


def test_load_script_with_invalid_function_name(r: ValkeyTestClient) -> None:
    """
    test {Load script with invalid function name} {
        assert_error {ERR Function names can only contain letters, numbers, or underscores(_) and must be at least one character long} {r function load "#!hello name=mylib2\nFUNCTION foo-bar\nARGS 0\nRETURN"}
    }
    """
    with pytest.raises(
        Exception,
        match="ERR\\ Function\\ names\\ can\\ only\\ contain\\ letters,\\ numbers,\\ or\\ underscores\\(_\\)\\ and\\ must\\ be\\ at\\ least\\ one\\ character\\ long",
    ):
        r.run("function", "load", "#!hello name=mylib2\nFUNCTION foo-bar\nARGS 0\nRETURN")


def test_load_script_with_duplicate_function_1(r: ValkeyTestClient) -> None:
    """
    test {Load script with duplicate function} {
        assert_error {ERR Function already exists in the library} {r function load "#!hello name=mylib2\nFUNCTION foo\nARGS 0\nRETURN\nFUNCTION foo\nARGS 0\nRETURN"}
    }
    """
    with pytest.raises(Exception, match="ERR\\ Function\\ already\\ exists\\ in\\ the\\ library"):
        r.run("function", "load", "#!hello name=mylib2\nFUNCTION foo\nARGS 0\nRETURN\nFUNCTION foo\nARGS 0\nRETURN")


def test_load_script_with_syntax_error(r: ValkeyTestClient) -> None:
    """
    test {Load script with syntax error} {
        assert_error {ERR Failed to parse instruction: 'SEND'} {r function load replace "#!hello name=mylib3\nFUNCTION foo\nARGS 0\nSEND"}
    }
    """
    with pytest.raises(Exception, match="ERR\\ Failed\\ to\\ parse\\ instruction:\\ 'SEND'"):
        r.run("function", "load", "replace", "#!hello name=mylib3\nFUNCTION foo\nARGS 0\nSEND")


def test_call_scripting_engine_function_calling_foo_works(r: ValkeyTestClient) -> None:
    """
    test {Call scripting engine function: calling foo works} {
        r fcall foo 0 134
    } {134}
    """
    assert r.run("fcall", "foo", 0, 134) == "134"


def test_call_scripting_engine_function_calling_bar_works(r: ValkeyTestClient) -> None:
    """
    test {Call scripting engine function: calling bar works} {
        r fcall bar 0
    } {432}
    """
    assert r.run("fcall", "bar", 0) == "432"


def test_call_server_command_from_script(r: ValkeyTestClient) -> None:
    """
    test {Call server command from script} {
        set result [r eval {#!hello
            FUNCTION callcmd
            CONSTS x
            ARGS 0
            CONSTI 2
            CALL SET
            RETURN
        } 0 43]
        assert_equal $result "OK"
        assert_equal [r GET x] 43

        set result [r eval {#!hello
            FUNCTION callcmd
            CONSTS hello
            CONSTI 1
            CALL PING
            RETURN
        } 0]
        assert_equal $result "hello"

        set result [r eval {#!hello
            FUNCTION callcmd
            CONSTI 0
            CALL PING
            RETURN
        } 0]
        assert_equal $result "PONG"
    }
    """
    result = r.run(
        "eval",
        "#!hello            FUNCTION callcmd            CONSTS x            ARGS 0            CONSTI 2            CALL SET            RETURN        ",
        0,
        43,
    )
    assert result == "OK"
    assert r.run("GET", "x") == 43
    result = r.run(
        "eval",
        "#!hello            FUNCTION callcmd            CONSTS hello            CONSTI 1            CALL PING            RETURN        ",
        0,
    )
    assert result == "hello"
    result = r.run(
        "eval",
        "#!hello            FUNCTION callcmd            CONSTI 0            CALL PING            RETURN        ",
        0,
    )
    assert result == "PONG"


def test_call_server_noscript_command(r: ValkeyTestClient) -> None:
    """
    test {Call server NOSCRIPT command} {
        assert_error {ERR command 'acl|cat' is not allowed on script mode} {
            r eval {#!hello
                FUNCTION callcmd
                CONSTS CAT
                CONSTI 1
                CALL ACL
                RETURN
            } 0
        }

        assert_error {ERR This Valkey command is not allowed from script*} {
            r eval {#!lua
                return server.call('ACL', 'CAT')
            } 0
        }

        r debug set-disable-deny-scripts 1

        set result [r eval {#!hello
            FUNCTION callcmd
            CONSTS CAT
            CONSTI 1
            CALL ACL
            RETURN
        } 0]
        assert_equal $result "OK"

        r eval {#!lua
            return server.call('ACL', 'CAT')
        } 0

        r debug set-disable-deny-scripts 0
    }
    """
    with pytest.raises(Exception, match="ERR\\ command\\ 'acl\\|cat'\\ is\\ not\\ allowed\\ on\\ script\\ mode"):
        r.run(
            "eval",
            "#!hello\n                FUNCTION callcmd\n                CONSTS CAT\n                CONSTI 1\n                CALL ACL\n                RETURN\n            ",
            0,
        )
    with pytest.raises(Exception, match="ERR\\ This\\ Valkey\\ command\\ is\\ not\\ allowed\\ from\\ script.*"):
        r.run("eval", "#!lua\n                return server.call('ACL', 'CAT')\n            ", 0)
    r.run("debug", "set-disable-deny-scripts", 1)
    result = r.run(
        "eval",
        "#!hello            FUNCTION callcmd            CONSTS CAT            CONSTI 1            CALL ACL            RETURN        ",
        0,
    )
    assert result == "OK"
    r.run("eval", "#!lua\n            return server.call('ACL', 'CAT')\n        ", 0)
    r.run("debug", "set-disable-deny-scripts", 0)


def test_call_server_command_without_permission(r: ValkeyTestClient) -> None:
    """
    test {Call server command without permission} {
        r acl setuser default -set

        r ACL LOG RESET

        assert_error {NOPERM User default has no permissions *} {r set x 5}

        assert_error {NOPERM User default has no permissions *} {
            r eval {#!hello
                FUNCTION callcmd
                CONSTS x
                ARGS 0
                CONSTI 2
                CALL SET
                RETURN
            } 0 43
        }

        assert_error {ERR ACL failure in script*} {
            r eval {#!lua
                return server.call('SET', 'x', 5)
            } 0
        }

        # verify ACL LOG entries
        set entries [r ACL LOG]
        assert_equal [llength $entries] 3

        set entry [lindex $entries 0]
        assert_equal [dict get $entry username] {default}
        assert_equal [dict get $entry context] {lua}
        assert_equal [dict get $entry object] {set}
        assert_equal [dict get $entry reason] {command}
        assert_match {*cmd=eval*} [dict get $entry client-info]

        set entry [lindex $entries 1]
        assert_equal [dict get $entry username] {default}
        assert_equal [dict get $entry context] {script}
        assert_equal [dict get $entry object] {set}
        assert_equal [dict get $entry reason] {command}
        assert_match {*cmd=eval*} [dict get $entry client-info]

        set entry [lindex $entries 2]
        assert_equal [dict get $entry username] {default}
        assert_equal [dict get $entry context] {toplevel}
        assert_equal [dict get $entry object] {set}
        assert_equal [dict get $entry reason] {command}
        assert_match {*cmd=set*} [dict get $entry client-info]

        r acl setuser default +set
    }
    """
    r.run("acl", "setuser", "default", "-set")
    r.run("ACL", "LOG", "RESET")
    with pytest.raises(Exception, match="NOPERM\\ User\\ default\\ has\\ no\\ permissions\\ .*"):
        r.run("set", "x", 5)
    with pytest.raises(Exception, match="NOPERM\\ User\\ default\\ has\\ no\\ permissions\\ .*"):
        r.run(
            "eval",
            "#!hello\n                FUNCTION callcmd\n                CONSTS x\n                ARGS 0\n                CONSTI 2\n                CALL SET\n                RETURN\n            ",
            0,
            43,
        )
    with pytest.raises(Exception, match="ERR\\ ACL\\ failure\\ in\\ script.*"):
        r.run("eval", "#!lua\n                return server.call('SET', 'x', 5)\n            ", 0)
    entries = r.run("ACL", "LOG")
    assert len(entries) == 3
    entry = entries[0]
    assert entry["username"] == "default"
    assert entry["context"] == "lua"
    assert entry["object"] == "set"
    assert entry["reason"] == "command"
    assert fnmatch(str(entry["client-info"]), "*cmd=eval*")
    entry = entries[1]
    assert entry["username"] == "default"
    assert entry["context"] == "script"
    assert entry["object"] == "set"
    assert entry["reason"] == "command"
    assert fnmatch(str(entry["client-info"]), "*cmd=eval*")
    entry = entries[2]
    assert entry["username"] == "default"
    assert entry["context"] == "toplevel"
    assert entry["object"] == "set"
    assert entry["reason"] == "command"
    assert fnmatch(str(entry["client-info"]), "*cmd=set*")
    r.run("acl", "setuser", "default", "+set")


def test_call_server_write_command_in_ro_script(r: ValkeyTestClient) -> None:
    """
    test {Call server write command in RO script} {
        assert_error {ERR Write commands are not allowed*} {
            r eval {#!lua flags=no-writes
                return server.call('SET', 'x', 5)
            } 0
        }

        assert_error {ERR Write commands are not allowed*} {
            r eval {#!hello flags=no-writes
                FUNCTION callcmd
                CONSTS x
                CONSTI 43
                CONSTI 2
                CALL SET
                RETURN
            } 0
        }

        r function load {#!hello name=errlib
                RFUNCTION callcmd
                CONSTS x
                CONSTI 43
                CONSTI 2
                CALL SET
                RETURN
            }
        assert_error {ERR Write commands are not allowed*} {r fcall callcmd 0}
    }
    """
    with pytest.raises(Exception, match="ERR\\ Write\\ commands\\ are\\ not\\ allowed.*"):
        r.run("eval", "#!lua flags=no-writes\n                return server.call('SET', 'x', 5)\n            ", 0)
    with pytest.raises(Exception, match="ERR\\ Write\\ commands\\ are\\ not\\ allowed.*"):
        r.run(
            "eval",
            "#!hello flags=no-writes\n                FUNCTION callcmd\n                CONSTS x\n                CONSTI 43\n                CONSTI 2\n                CALL SET\n                RETURN\n            ",
            0,
        )
    r.run(
        "function",
        "load",
        "#!hello name=errlib\n                RFUNCTION callcmd\n                CONSTS x\n                CONSTI 43\n                CONSTI 2\n                CALL SET\n                RETURN\n            ",
    )
    with pytest.raises(Exception, match="ERR\\ Write\\ commands\\ are\\ not\\ allowed.*"):
        r.run("fcall", "callcmd", 0)


def test_call_server_command_when_oom(r: ValkeyTestClient) -> None:
    """
    test {Call server command when OOM} {
        r config set maxmemory 1

        assert_error {*command not allowed when used memory*} {
            r eval {#!lua
                return server.call('set', 'x', 1)
            } 0
        }

        set res [r eval {#!lua flags=allow-oom
                return server.call('set', 'x', 1)
            } 0]
        assert_equal $res "OK"

        assert_error {*command not allowed when used memory*} {
            r eval {#!hello
                FUNCTION callcmd
                CONSTS x
                CONSTI 43
                CONSTI 2
                CALL SET
                RETURN
            } 0
        }

        set res [r eval {#!hello flags=allow-oom
                FUNCTION callcmd
                CONSTS x
                CONSTI 43
                CONSTI 2
                CALL SET
                RETURN
            } 0]
        assert_equal $res "OK"

        r config set maxmemory 0
    }
    """
    r.run("config", "set", "maxmemory", 1)
    with pytest.raises(Exception, match=".*command\\ not\\ allowed\\ when\\ used\\ memory.*"):
        r.run("eval", "#!lua\n                return server.call('set', 'x', 1)\n            ", 0)
    res = r.run("eval", "#!lua flags=allow-oom                return server.call('set', 'x', 1)            ", 0)
    assert res == "OK"
    with pytest.raises(Exception, match=".*command\\ not\\ allowed\\ when\\ used\\ memory.*"):
        r.run(
            "eval",
            "#!hello\n                FUNCTION callcmd\n                CONSTS x\n                CONSTI 43\n                CONSTI 2\n                CALL SET\n                RETURN\n            ",
            0,
        )
    res = r.run(
        "eval",
        "#!hello flags=allow-oom                FUNCTION callcmd                CONSTS x                CONSTI 43                CONSTI 2                CALL SET                RETURN            ",
        0,
    )
    assert res == "OK"
    r.run("config", "set", "maxmemory", 0)


@pytest.mark.xfail(reason="not implemented")
def test_ensure_errors_from_commands_called_from_script_is_counted_only_once(r: ValkeyTestClient) -> None:
    """
    test {Ensure errors from commands called from script is counted only once} {
        r lpush l 1
        assert_error {WRONGTYPE Operation against a key holding the wrong kind of value*} {
            r eval {#!hello
                FUNCTION callcmd
                CONSTS l
                CONSTI 1
                CALL GET
                RETURN
            } 0
        }

        set errorstats [r info Errorstats]
        regexp {errorstat_WRONGTYPE:count=([0-9]+)} $errorstats -> wrongtype_errors
        assert_equal $wrongtype_errors 1
    }
    """
    r.run("lpush", "l", 1)
    with pytest.raises(
        Exception, match="WRONGTYPE\\ Operation\\ against\\ a\\ key\\ holding\\ the\\ wrong\\ kind\\ of\\ value.*"
    ):
        r.run(
            "eval",
            "#!hello\n                FUNCTION callcmd\n                CONSTS l\n                CONSTI 1\n                CALL GET\n                RETURN\n            ",
            0,
        )
    errorstats = r.run("info", "Errorstats")
    regexp("errorstat_WRONGTYPE:count=([0-9]+)", errorstats, "->", "wrongtype_errors")
    # TODO: assert_equal wrongtype_errors 1


def test_call_server_command_that_returns_null_values(r: ValkeyTestClient) -> None:
    """
    test {Call server command that returns NULL values} {
        r lpush s a

        set result [r eval {#!hello
            FUNCTION callcmd
            CONSTS s
            CONSTI 1
            CONSTI 2
            CALL BLPOP
            RETURN
        } 0]
        assert_equal $result "OK"

        set result [r eval {#!hello
            FUNCTION callcmd
            CONSTS s
            CONSTI 2
            CONSTI 2
            CALL BLPOP
            RETURN
        } 0]
        assert_equal $result "(null array)"

        set result [r eval {#!hello
            FUNCTION callcmd
            CONSTS f
            CONSTI 1
            CALL GET
            RETURN
        } 0]
        assert_equal $result "(null string)"
    }
    """
    r.run("lpush", "s", "a")
    result = r.run(
        "eval",
        "#!hello            FUNCTION callcmd            CONSTS s            CONSTI 1            CONSTI 2            CALL BLPOP            RETURN        ",
        0,
    )
    assert result == "OK"
    result = r.run(
        "eval",
        "#!hello            FUNCTION callcmd            CONSTS s            CONSTI 2            CONSTI 2            CALL BLPOP            RETURN        ",
        0,
    )
    assert result == "(null array)"
    result = r.run(
        "eval",
        "#!hello            FUNCTION callcmd            CONSTS f            CONSTI 1            CALL GET            RETURN        ",
        0,
    )
    assert result == "(null string)"


def test_replace_function_library_and_call_functions(r: ValkeyTestClient) -> None:
    """
    test {Replace function library and call functions} {
        set result [r function load replace "#!hello name=mylib\nFUNCTION foo\nARGS 0\nRETURN\nFUNCTION bar\nCONSTI 500\nRETURN"]
        assert_equal $result "mylib"

        set result [r fcall foo 0 132]
        assert_equal $result 132

        set result [r fcall bar 0]
        assert_equal $result 500
    }
    """
    result = r.run(
        "function",
        "load",
        "replace",
        "#!hello name=mylib\nFUNCTION foo\nARGS 0\nRETURN\nFUNCTION bar\nCONSTI 500\nRETURN",
    )
    assert result == "mylib"
    result = r.run("fcall", "foo", 0, 132)
    assert result == 132
    result = r.run("fcall", "bar", 0)
    assert result == 500


def test_list_scripting_engine_functions(r: ValkeyTestClient) -> None:
    """
    test {List scripting engine functions} {
        r function flush sync
        r function load replace "#!hello name=mylib\nFUNCTION foobar\nARGS 0\nRETURN"
        r function list
    } {{library_name mylib engine HELLO functions {{name foobar description {} flags {}}}}}
    """
    r.run("function", "flush", "sync")
    r.run("function", "load", "replace", "#!hello name=mylib\nFUNCTION foobar\nARGS 0\nRETURN")
    assert (
        r.run("function", "list")
        == "{library_name mylib engine HELLO functions {{name foobar description {} flags {}}}}"
    )


def test_load_a_second_library_and_call_a_function(r: ValkeyTestClient) -> None:
    """
    test {Load a second library and call a function} {
        r function load "#!hello name=mylib2\nFUNCTION getarg\nARGS 0\nRETURN"
        set result [r fcall getarg 0 456]
        assert_equal $result 456
    }
    """
    r.run("function", "load", "#!hello name=mylib2\nFUNCTION getarg\nARGS 0\nRETURN")
    result = r.run("fcall", "getarg", 0, 456)
    assert result == 456


def test_delete_all_libraries_and_functions(r: ValkeyTestClient) -> None:
    """
    test {Delete all libraries and functions} {
        set result [r function flush]
        assert_equal $result {OK}
        r function list
    } {}
    """
    result = r.run("function", "flush")
    assert result == "OK"
    r.run("function", "list")


@pytest.mark.xfail(reason="not implemented")
def test_test_the_deletion_of_a_single_library(r: ValkeyTestClient) -> None:
    """
    test {Test the deletion of a single library} {
        r function load $HELLO_PROGRAM
        r function load "#!hello name=mylib2\nFUNCTION getarg\nARGS 0\nRETURN"

        set result [r function delete mylib]
        assert_equal $result {OK}

        set result [r fcall getarg 0 446]
        assert_equal $result 446
    }
    """
    # TODO: r function load HELLO_PROGRAM
    r.run("function", "load", "#!hello name=mylib2\nFUNCTION getarg\nARGS 0\nRETURN")
    result = r.run("function", "delete", "mylib")
    assert result == "OK"
    result = r.run("fcall", "getarg", 0, 446)
    assert result == 446


@pytest.mark.xfail(reason="not implemented")
def test_test_dump_and_restore_function_library(r: ValkeyTestClient) -> None:
    """
    test {Test dump and restore function library} {
        r function load $HELLO_PROGRAM

        set result [r fcall bar 0]
        assert_equal $result 432

        set dump [r function dump]

        set result [r function flush]
        assert_equal $result {OK}

        set result [r function restore $dump]
        assert_equal $result {OK}

        set result [r fcall getarg 0 436]
        assert_equal $result 436

        set result [r fcall bar 0]
        assert_equal $result 432
    }
    """
    # TODO: r function load HELLO_PROGRAM
    result = r.run("fcall", "bar", 0)
    assert result == 432
    dump = r.run("function", "dump")
    result = r.run("function", "flush")
    assert result == "OK"
    result = r.run("function", "restore", dump)
    assert result == "OK"
    result = r.run("fcall", "getarg", 0, 436)
    assert result == 436
    result = r.run("fcall", "bar", 0)
    assert result == 432


def test_test_function_kill(r: ValkeyTestClient) -> None:
    """
    test {Test function kill} {
        set rd [valkey_deferring_client]
        r config set busy-reply-threshold 10
        r function load REPLACE "#!hello name=mylib\nFUNCTION wait\nARGS 0\nSLEEP\nARGS 0\nRETURN"
        $rd fcall wait 0 100
        after 1000
        catch {r ping} e
        assert_match {BUSY*} $e
        assert_match {running_script {name wait command {fcall wait 0 100} duration_ms *} engines {*}} [r FUNCTION STATS]
        r function kill
        after 1000 ;
        assert_equal [r ping] "PONG"
        assert_error {ERR Script killed by user with FUNCTION KILL*} {$rd read}
        $rd ping
        assert_equal [$rd read] "PONG"
        $rd close
    }
    """
    rd = ValkeyTestClient.create_from(r)
    r.run("config", "set", "busy-reply-threshold", 10)
    r.run("function", "load", "REPLACE", "#!hello name=mylib\nFUNCTION wait\nARGS 0\nSLEEP\nARGS 0\nRETURN")
    rd.run("fcall", "wait", 0, 100)
    time.sleep(1000 / 1000)
    try:
        e = r.run("ping")
    except Exception as _catch_err:
        e = str(_catch_err)
    assert fnmatch(str(e), "BUSY*")
    assert fnmatch(
        str(r.run("FUNCTION", "STATS")),
        "running_script {name wait command {fcall wait 0 100} duration_ms *} engines {*}",
    )
    r.run("function", "kill")
    time.sleep(1000 / 1000)
    assert r.run("ping") == "PONG"
    assert_error("ERR Script killed by user with FUNCTION KILL*", "$rd read")
    rd.run("ping")
    assert rd.run("read") == "PONG"
    rd.run("close")


def test_test_eval_execution(r: ValkeyTestClient) -> None:
    """
    test {Test eval execution} {
        set result [r eval "#!hello\nFUNCTION foo\nARGS 0\nRETURN" 0 145]
        assert_equal $result 145
    }
    """
    result = r.run("eval", "#!hello\nFUNCTION foo\nARGS 0\nRETURN", 0, 145)
    assert result == 145


def test_test_evalsha_execution(r: ValkeyTestClient) -> None:
    """
    test {Test evalsha execution} {
        set sha [r script load "#!hello\nFUNCTION foo\nARGS 0\nRETURN"]
        set result [r evalsha $sha 0 167]
        assert_equal $result 167
    }
    """
    sha = r.run("script", "load", "#!hello\nFUNCTION foo\nARGS 0\nRETURN")
    result = r.run("evalsha", sha, 0, 167)
    assert result == 167


def test_test_script_exists(r: ValkeyTestClient) -> None:
    """
    test {Test script exists} {
        set sha [r script load "#!hello\nFUNCTION foo\nARGS 0\nRETURN"]
        set result [r script exists $sha]
        assert_equal $result 1
    }
    """
    sha = r.run("script", "load", "#!hello\nFUNCTION foo\nARGS 0\nRETURN")
    result = r.run("script", "exists", sha)
    assert result == 1


def test_test_script_flush_sync(r: ValkeyTestClient) -> None:
    """
    test {Test script flush sync} {
        set sha [r script load "#!hello\nFUNCTION foo\nARGS 0\nRETURN"]
        set result [r script exists $sha]
        assert_equal $result 1
        r script flush SYNC
        set result [r script exists $sha]
        assert_equal $result 0
    }
    """
    sha = r.run("script", "load", "#!hello\nFUNCTION foo\nARGS 0\nRETURN")
    result = r.run("script", "exists", sha)
    assert result == 1
    r.run("script", "flush", "SYNC")
    result = r.run("script", "exists", sha)
    assert result == 0


def test_test_script_flush_async(r: ValkeyTestClient) -> None:
    """
    test {Test script flush async} {
        set sha [r script load "#!hello\nFUNCTION foo\nARGS 0\nRETURN"]
        set result [r script exists $sha]
        assert_equal $result 1
        r script flush ASYNC
        set result [r script exists $sha]
        assert_equal $result 0
    }
    """
    sha = r.run("script", "load", "#!hello\nFUNCTION foo\nARGS 0\nRETURN")
    result = r.run("script", "exists", sha)
    assert result == 1
    r.run("script", "flush", "ASYNC")
    result = r.run("script", "exists", sha)
    assert result == 0


def test_test_hello_debugger(r: ValkeyTestClient) -> None:
    """
    test {Test HELLO debugger} {
        r script debug sync hello
        set ret [r eval "#!hello\nFUNCTION foo\nARGS 0\nRETURN" 0 167]
        assert_equal {{>>>   0: ARGS 0}} $ret
        set cmd "*1\r\n\$4\r\nstep\r\n"
        r write $cmd
        r flush
        set ret [r read]
        assert_equal {{>>>   1: RETURN}} $ret
        set cmd "*1\r\n\$5\r\nstack\r\n"
        r write $cmd
        r flush
        set ret [r read]
        assert_equal {{Stack contents:} {top -> [0] 167}} $ret
        set cmd "*1\r\n\$1\r\nc\r\n"
        r write $cmd
        r flush
        set ret [r read]
        assert_equal {<endsession>} $ret
        r script debug off
        reconnect
        assert_equal [r ping] {PONG}
    }
    """
    r.run("script", "debug", "sync", "hello")
    ret = r.run("eval", "#!hello\nFUNCTION foo\nARGS 0\nRETURN", 0, 167)
    assert "{>>>   0: ARGS 0}" == ret
    cmd = "*1\r\n$4\r\nstep\r\n"
    r.run("write", cmd)
    r.run("flush")
    ret = r.run("read")
    assert "{>>>   1: RETURN}" == ret
    cmd = "*1\r\n$5\r\nstack\r\n"
    r.run("write", cmd)
    r.run("flush")
    ret = r.run("read")
    assert "{Stack contents:} {top -> [0] 167}" == ret
    cmd = "*1\r\n$1\r\nc\r\n"
    r.run("write", cmd)
    r.run("flush")
    ret = r.run("read")
    assert "<endsession>" == ret
    r.run("script", "debug", "off")
    reconnect()
    assert r.run("ping") == "PONG"


@pytest.mark.xfail(reason="not implemented")
def test_test_info_scriptingengines_section(r: ValkeyTestClient) -> None:
    """
    test {Test INFO scriptingengines section} {
        # Get the scripting engines info section
        set info [r info scriptingengines]

        # Verify the section header exists
        assert_match "*# Scripting Engines*" $info

        # Verify we have exactly 2 engines (LUA + HELLO)
        assert_match "*engines_count:*" $info
        regexp {engines_count:([0-9]+)} $info -> engines_count
        assert_equal $engines_count 2

        # Verify memory fields exist and are non-negative numbers
        assert_match "*engines_total_used_memory:*" $info
        assert_match "*engines_total_memory_overhead:*" $info
        regexp {engines_total_used_memory:([0-9]+)} $info -> total_memory
        regexp {engines_total_memory_overhead:([0-9]+)} $info -> total_overhead
        assert {$total_memory >= 0}
        assert {$total_overhead >= 0}

        # Verify individual engine information exists
        assert_match "*engine_0:*" $info
        assert_match "*engine_1:*" $info

        # Check that engines have proper format including abi_version
        assert_match "*engine_*:name=*,module=*,abi_version=*,used_memory=*,memory_overhead=*" $info

        # Verify both LUA and HELLO engines are present
        assert_match "*name=LUA*" $info
        assert_match "*name=HELLO*" $info

        # Verify LUA is built-in and HELLO is from module
        assert_match "*name=LUA,module=lua*" $info
        assert_match "*name=HELLO,module=helloengine*" $info
    }
    """
    info = r.run("info", "scriptingengines")
    assert fnmatch(str(info), "*# Scripting Engines*")
    assert fnmatch(str(info), "*engines_count:*")
    regexp("engines_count:([0-9]+)", info, "->", "engines_count")
    # TODO: assert_equal engines_count 2
    assert fnmatch(str(info), "*engines_total_used_memory:*")
    assert fnmatch(str(info), "*engines_total_memory_overhead:*")
    regexp("engines_total_used_memory:([0-9]+)", info, "->", "total_memory")
    regexp("engines_total_memory_overhead:([0-9]+)", info, "->", "total_overhead")
    assert_("$total_memory >= 0")
    assert_("$total_overhead >= 0")
    assert fnmatch(str(info), "*engine_0:*")
    assert fnmatch(str(info), "*engine_1:*")
    assert fnmatch(str(info), "*engine_*:name=*,module=*,abi_version=*,used_memory=*,memory_overhead=*")
    assert fnmatch(str(info), "*name=LUA*")
    assert fnmatch(str(info), "*name=HELLO*")
    assert fnmatch(str(info), "*name=LUA,module=lua*")
    assert fnmatch(str(info), "*name=HELLO,module=helloengine*")


def test_unload_scripting_engine_module(r: ValkeyTestClient) -> None:
    """
    test {Unload scripting engine module} {
        set result [r module unload helloengine]
        assert_equal $result "OK"
    }
    """
    result = r.run("module", "unload", "helloengine")
    assert result == "OK"


@pytest.mark.xfail(reason="not implemented")
def test_load_scripting_engine_in_version_before_function_env_reset(r: ValkeyTestClient) -> None:
    """
    test {Load scripting engine in version before function env reset} {
        r module load $testmodule 2
        r function load $HELLO_PROGRAM
        set result [r fcall foo 0 123]
        assert_equal $result 123
        set result [r function flush async]
        assert_equal $result {OK}
        assert_error {ERR Function not found} {r fcall foo 0 123}
        set result [r module unload helloengine]
        assert_equal $result "OK"
    }
    """
    # TODO: r module load testmodule 2
    # TODO: r function load HELLO_PROGRAM
    result = r.run("fcall", "foo", 0, 123)
    assert result == 123
    result = r.run("function", "flush", "async")
    assert result == "OK"
    with pytest.raises(Exception, match="ERR\\ Function\\ not\\ found"):
        r.run("fcall", "foo", 0, 123)
    result = r.run("module", "unload", "helloengine")
    assert result == "OK"


@pytest.mark.xfail(reason="not implemented")
def test_load_scripting_engine_in_version_before_debugger_support(r: ValkeyTestClient) -> None:
    """
    test {Load scripting engine in version before debugger support} {
        r module load $testmodule 3
        r function load $HELLO_PROGRAM
        set result [r fcall foo 0 123]
        assert_equal $result 123
        assert_error {ERR The scripting engine 'HELLO' does not support interactive script debugging} {r script debug sync hello}
        set result [r module unload helloengine]
        assert_equal $result "OK"
    }
    """
    # TODO: r module load testmodule 3
    # TODO: r function load HELLO_PROGRAM
    result = r.run("fcall", "foo", 0, 123)
    assert result == 123
    with pytest.raises(
        Exception,
        match="ERR\\ The\\ scripting\\ engine\\ 'HELLO'\\ does\\ not\\ support\\ interactive\\ script\\ debugging",
    ):
        r.run("script", "debug", "sync", "hello")
    result = r.run("module", "unload", "helloengine")
    assert result == "OK"


# --- stubs for unimplemented TCL helpers ---


def assert_(*args):
    raise NotImplementedError("assert_")


def assert_error(*args):
    raise NotImplementedError("assert_error")


def reconnect(*args):
    raise NotImplementedError("reconnect")


def regexp(*args):
    raise NotImplementedError("regexp")
