# ruff: noqa: PLR2004, F841, RUF043, ANN002, ANN201
import time
from fnmatch import fnmatch

import pytest

from tests.valkey_test_client import ValkeyTestClient

"""
set testmodule file normalize tests/modules/misc.so
"""

pytestmark = [pytest.mark.modules]


"""
r module load testmodule
"""


def test_test_rm_call(r: ValkeyTestClient) -> None:
    """
    test {test RM_Call} {
        set info [r test.call_info commandstats]
        # cmdstat is not in a default section, so we also test an argument was passed
        assert { [string match "*cmdstat_module*" $info] }
    }
    """
    info = r.run("test.call_info", "commandstats")
    assert string("match", "*cmdstat_module*", info)


def test_test_rm_call_args_array(r: ValkeyTestClient) -> None:
    """
    test {test RM_Call args array} {
        set info [r test.call_generic info commandstats]
        # cmdstat is not in a default section, so we also test an argument was passed
        assert { [string match "*cmdstat_module*" $info] }
    }
    """
    info = r.run("test.call_generic", "info", "commandstats")
    assert string("match", "*cmdstat_module*", info)


def test_test_rm_call_recursive(r: ValkeyTestClient) -> None:
    """
    test {test RM_Call recursive} {
        set info [r test.call_generic test.call_generic info commandstats]
        assert { [string match "*cmdstat_module*" $info] }
    }
    """
    info = r.run("test.call_generic", "test.call_generic", "info", "commandstats")
    assert string("match", "*cmdstat_module*", info)


def test_test_valkey_version(r: ValkeyTestClient) -> None:
    """
    test {test valkey version} {
        assert_equal [s valkey_version] [r test.serverversion]
    }
    """
    assert s("valkey_version") == r.run("test.serverversion")


def test_test_long_double_conversions(r: ValkeyTestClient) -> None:
    """
    test {test long double conversions} {
        set ld [r test.ld_conversion]
        assert {[string match $ld "0.00000000000000001"]}
    }
    """
    ld = r.run("test.ld_conversion")
    assert string("match", ld, "0.00000000000000001")


def test_test_unsigned_long_long_conversions(r: ValkeyTestClient) -> None:
    """
    test {test unsigned long long conversions} {
        set ret [r test.ull_conversion]
        assert {[string match $ret "ok"]}
    }
    """
    ret = r.run("test.ull_conversion")
    assert string("match", ret, "ok")


def test_test_module_db_commands(r: ValkeyTestClient) -> None:
    """
    test {test module db commands} {
        r set x foo
        set key [r test.randomkey]
        assert_equal $key "x"
        assert_equal [r test.dbsize] 1
        r test.flushall
        assert_equal [r test.dbsize] 0
    }
    """
    r.run("set", "x", "foo")
    key = r.run("test.randomkey")
    assert key == "x"
    assert r.run("test.dbsize") == 1
    r.run("test.flushall")
    assert r.run("test.dbsize") == 0


def test_test_redismodule_resetdataset_do_not_reset_functions(r: ValkeyTestClient) -> None:
    """
    test {test RedisModule_ResetDataset do not reset functions} {
        r function load {#!lua name=lib
            server.register_function('test', function() return 1 end)
        }
        assert_equal [r function list] {{library_name lib engine LUA functions {{name test description {} flags {}}}}}
        r test.flushall
        assert_equal [r function list] {{library_name lib engine LUA functions {{name test description {} flags {}}}}}
        r function flush
    }
    """
    r.run(
        "function",
        "load",
        "#!lua name=lib\n            server.register_function('test', function() return 1 end)\n        ",
    )
    assert r.run("function", "list") == "{library_name lib engine LUA functions {{name test description {} flags {}}}}"
    r.run("test.flushall")
    assert r.run("function", "list") == "{library_name lib engine LUA functions {{name test description {} flags {}}}}"
    r.run("function", "flush")


def test_test_module_keyexists(r: ValkeyTestClient) -> None:
    """
    test {test module keyexists} {
        r set x foo
        assert_equal 1 [r test.keyexists x]
        r del x
        assert_equal 0 [r test.keyexists x]
    }
    """
    r.run("set", "x", "foo")
    assert 1 == r.run("test.keyexists", "x")
    r.run("del", "x")
    assert 0 == r.run("test.keyexists", "x")


def test_test_module_lru_api(r: ValkeyTestClient) -> None:
    """
    test {test module lru api} {
        r config set maxmemory-policy allkeys-lru
        r set x foo
        set lru [r test.getlru x]
        assert { $lru <= 1000 }
        set was_set [r test.setlru x 100000]
        assert { $was_set == 1 }
        set idle [r object idletime x]
        assert { $idle >= 100 }
        set lru [r test.getlru x]
        assert { $lru >= 100000 }
        r config set maxmemory-policy allkeys-lfu
        set lru [r test.getlru x]
        assert { $lru == -1 }
        set was_set [r test.setlru x 100000]
        assert { $was_set == 0 }
    }
    """
    r.run("config", "set", "maxmemory-policy", "allkeys-lru")
    r.run("set", "x", "foo")
    lru = r.run("test.getlru", "x")
    assert lru <= 1000
    was_set = r.run("test.setlru", "x", 100000)
    assert was_set == 1
    idle = r.run("object", "idletime", "x")
    assert idle >= 100
    lru = r.run("test.getlru", "x")
    assert lru >= 100000
    r.run("config", "set", "maxmemory-policy", "allkeys-lfu")
    lru = r.run("test.getlru", "x")
    assert lru == -1
    was_set = r.run("test.setlru", "x", 100000)
    assert was_set == 0


"""
r config set maxmemory-policy allkeys-lru
"""


def test_test_module_lfu_api(r: ValkeyTestClient) -> None:
    """
    test {test module lfu api} {
        r config set maxmemory-policy allkeys-lfu
        r set x foo
        set lfu [r test.getlfu x]
        assert { $lfu >= 1 }
        set was_set [r test.setlfu x 100]
        assert { $was_set == 1 }
        set freq [r object freq x]
        assert { $freq <= 100 }
        set lfu [r test.getlfu x]
        assert { $lfu <= 100 }
        r config set maxmemory-policy allkeys-lru
        set lfu [r test.getlfu x]
        assert { $lfu == -1 }
        set was_set [r test.setlfu x 100]
        assert { $was_set == 0 }
    }
    """
    r.run("config", "set", "maxmemory-policy", "allkeys-lfu")
    r.run("set", "x", "foo")
    lfu = r.run("test.getlfu", "x")
    assert lfu >= 1
    was_set = r.run("test.setlfu", "x", 100)
    assert was_set == 1
    freq = r.run("object", "freq", "x")
    assert freq <= 100
    lfu = r.run("test.getlfu", "x")
    assert lfu <= 100
    r.run("config", "set", "maxmemory-policy", "allkeys-lru")
    lfu = r.run("test.getlfu", "x")
    assert lfu == -1
    was_set = r.run("test.setlfu", "x", 100)
    assert was_set == 0


"""
proc parse_client_flags {flags} {
    set flag_list [split $flags ":"]
    set parsed_flags {}

    # Just collect all non-empty flags
    foreach flag $flag_list {
        if {$flag ne ""} {
            lappend parsed_flags $flag
        }
    }

    return $parsed_flags
}
"""


def test_test_module_clientinfo_api(r: ValkeyTestClient) -> None:
    """
    test {test module clientinfo api} {
        # Test basic sanity and SSL flag
        set info [r test.clientinfo]
        assert { [dict get $info db] == 9 }

        set flags [parse_client_flags [dict get $info flags]]

        # Check initial state - should have auth flags, maybe SSL
        if {$::tls} {
            assert { "ssl" in $flags }
        }
        assert { "authenticated" in $flags }
        assert { "ever_authenticated" in $flags }
        assert { "multi" ni $flags }
        assert { "tracking" ni $flags }
        assert { "readonly" ni $flags }

        # Test MULTI flag
        r multi
        r test.clientinfo
        set info [lindex [r exec] 0]
        set flags [parse_client_flags [dict get $info flags]]
        assert { "multi" in $flags }
        assert { "authenticated" in $flags }
        assert { "ever_authenticated" in $flags }

        # Test TRACKING flag
        r client tracking on
        set info [r test.clientinfo]
        set flags [parse_client_flags [dict get $info flags]]
        assert { "tracking" in $flags }
        assert { "multi" ni $flags }
        assert { "authenticated" in $flags }
        assert { "ever_authenticated" in $flags }
        r CLIENT TRACKING off

        # Test READONLY flag
        r readonly
        set info [r test.clientinfo]
        set flags [parse_client_flags [dict get $info flags]]
        assert { "readonly" in $flags }
        assert { "tracking" ni $flags }
        assert { "multi" ni $flags }
        assert { "authenticated" in $flags }
        assert { "ever_authenticated" in $flags }

        r readwrite
        set info [r test.clientinfo]
        set flags [parse_client_flags [dict get $info flags]]
        assert { "readonly" ni $flags }
        assert { "authenticated" in $flags }
        assert { "ever_authenticated" in $flags }
    }
    """
    info = r.run("test.clientinfo")
    assert info["db"] == 9
    flags = parse_client_flags(info["flags"])
    if_("$::tls", '            assert { "ssl" in $flags }\n        ')
    assert_(' "authenticated" in $flags ')
    assert_(' "ever_authenticated" in $flags ')
    assert_(' "multi" ni $flags ')
    assert_(' "tracking" ni $flags ')
    assert_(' "readonly" ni $flags ')
    r.run("multi")
    r.run("test.clientinfo")
    info = r.run("exec")[0]
    flags = parse_client_flags(info["flags"])
    assert_(' "multi" in $flags ')
    assert_(' "authenticated" in $flags ')
    assert_(' "ever_authenticated" in $flags ')
    r.run("client", "tracking", "on")
    info = r.run("test.clientinfo")
    flags = parse_client_flags(info["flags"])
    assert_(' "tracking" in $flags ')
    assert_(' "multi" ni $flags ')
    assert_(' "authenticated" in $flags ')
    assert_(' "ever_authenticated" in $flags ')
    r.run("CLIENT", "TRACKING", "off")
    r.run("readonly")
    info = r.run("test.clientinfo")
    flags = parse_client_flags(info["flags"])
    assert_(' "readonly" in $flags ')
    assert_(' "tracking" ni $flags ')
    assert_(' "multi" ni $flags ')
    assert_(' "authenticated" in $flags ')
    assert_(' "ever_authenticated" in $flags ')
    r.run("readwrite")
    info = r.run("test.clientinfo")
    flags = parse_client_flags(info["flags"])
    assert_(' "readonly" ni $flags ')
    assert_(' "authenticated" in $flags ')
    assert_(' "ever_authenticated" in $flags ')


def test_tracking_with_rm_call_sanity(r: ValkeyTestClient) -> None:
    """
    test {tracking with rm_call sanity} {
        set rd_trk [valkey_client]
        $rd_trk HELLO 3
        $rd_trk CLIENT TRACKING on
        r MSET key1{t} 1 key2{t} 1

        # GET triggers tracking, SET does not
        $rd_trk test.rm_call GET key1{t}
        $rd_trk test.rm_call SET key2{t} 2
        r MSET key1{t} 2 key2{t} 2
        assert_equal {invalidate key1{t}} [$rd_trk read]
        assert_equal "PONG" [$rd_trk ping]
        $rd_trk close
    }
    """
    rd_trk = valkey_client()
    rd_trk.run("HELLO", 3)
    rd_trk.run("CLIENT", "TRACKING", "on")
    r.run("MSET", "key1{t}", 1, "key2{t}", 1)
    rd_trk.run("test.rm_call", "GET", "key1{t}")
    rd_trk.run("test.rm_call", "SET", "key2{t}", 2)
    r.run("MSET", "key1{t}", 2, "key2{t}", 2)
    assert "invalidate key1{t}" == rd_trk.run("read")
    assert "PONG" == rd_trk.run("ping")
    rd_trk.run("close")


def test_tracking_with_rm_call_with_script(r: ValkeyTestClient) -> None:
    """
    test {tracking with rm_call with script} {
        set rd_trk [valkey_client]
        $rd_trk HELLO 3
        $rd_trk CLIENT TRACKING on
        r MSET key1{t} 1 key2{t} 1

        # GET triggers tracking, SET does not
        $rd_trk test.rm_call EVAL "redis.call('get', 'key1{t}')" 2 key1{t} key2{t}
        r MSET key1{t} 2 key2{t} 2
        assert_equal {invalidate key1{t}} [$rd_trk read]
        assert_equal "PONG" [$rd_trk ping]
        $rd_trk close
    }
    """
    rd_trk = valkey_client()
    rd_trk.run("HELLO", 3)
    rd_trk.run("CLIENT", "TRACKING", "on")
    r.run("MSET", "key1{t}", 1, "key2{t}", 1)
    rd_trk.run("test.rm_call", "EVAL", "redis.call('get', 'key1{t}')", 2, "key1{t}", "key2{t}")
    r.run("MSET", "key1{t}", 2, "key2{t}", 2)
    assert "invalidate key1{t}" == rd_trk.run("read")
    assert "PONG" == rd_trk.run("ping")
    rd_trk.run("close")


def test_publish_to_self_inside_rm_call(r: ValkeyTestClient) -> None:
    """
    test {publish to self inside rm_call} {
        r hello 3
        r subscribe foo

        # published message comes after the response of the command that issued it.
        assert_equal [r test.rm_call publish foo bar] {1}
        assert_equal [r read] {message foo bar}

        r unsubscribe foo
        r hello 2
        set _ ""
    } {} {resp3}
    """
    r.run("hello", 3)
    r.run("subscribe", "foo")
    assert r.run("test.rm_call", "publish", "foo", "bar") == "1"
    assert r.run("read") == "message foo bar"
    r.run("unsubscribe", "foo")
    r.run("hello", 2)
    _ = ""


def test_test_module_get_or_set_client_name_by_id_api(r: ValkeyTestClient) -> None:
    """
    test {test module get/set client name by id api} {
        catch { r test.getname } e
        assert_equal "-ERR No name" $e
        r client setname nobody
        catch { r test.setname "name with spaces" } e
        assert_match "*Invalid argument*" $e
        assert_equal nobody [r client getname]
        assert_equal nobody [r test.getname]
        r test.setname somebody
        assert_equal somebody [r client getname]
    }
    """
    try:
        e = r.run("test.getname")
    except Exception as _catch_err:
        e = str(_catch_err)
    assert "-ERR No name" == e
    r.run("client", "setname", "nobody")
    try:
        e = r.run("test.setname", "name with spaces")
    except Exception as _catch_err:
        e = str(_catch_err)
    assert fnmatch(str(e), "*Invalid argument*")
    assert "nobody" == r.run("client", "getname")
    assert "nobody" == r.run("test.getname")
    r.run("test.setname", "somebody")
    assert "somebody" == r.run("client", "getname")


def test_test_module_getclientcert_api(r: ValkeyTestClient) -> None:
    """
    test {test module getclientcert api} {
        set cert [r test.getclientcert]

        if {$::tls} {
            assert {$cert != ""}
        } else {
            assert {$cert == ""}
        }
    }
    """
    cert = r.run("test.getclientcert")
    if_("$::tls", '            assert {$cert != ""}\n        ', "else", '            assert {$cert == ""}\n        ')


def test_test_detached_thread_safe_cnotext(r: ValkeyTestClient) -> None:
    """
    test {test detached thread safe cnotext} {
        r test.log_tsctx "info" "Test message"
        verify_log_message 0 "*<misc> Test message*" 0
    }
    """
    r.run("test.log_tsctx", "info", "Test message")
    verify_log_message(0, "*<misc> Test message*", 0)


def test_test_rm_call_client_info(r: ValkeyTestClient) -> None:
    """
    test {test RM_Call CLIENT INFO} {
        assert_match "*fd=-1*" [r test.call_generic client info]
    }
    """
    assert fnmatch(str(r.run("test.call_generic", "client", "info")), "*fd=-1*")


def test_unsafe_command_names_are_sanitized_in_info_output(r: ValkeyTestClient) -> None:
    """
    test {Unsafe command names are sanitized in INFO output} {
        r test.weird:cmd
        set info [r info commandstats]
        assert_match {*cmdstat_test.weird_cmd:calls=1*} $info
    }
    """
    r.run("test.weird:cmd")
    info = r.run("info", "commandstats")
    assert fnmatch(str(info), "*cmdstat_test.weird_cmd:calls=1*")


def test_test_monotonic_time(r: ValkeyTestClient) -> None:
    """
    test {test monotonic time} {
        set x [r test.monotonic_time]
        assert { [r test.monotonic_time] >= $x }
    }
    """
    x = r.run("test.monotonic_time")
    assert r.run("test.monotonic_time") >= x


def test_rm_call_oom(r: ValkeyTestClient) -> None:
    """
    test {rm_call OOM} {
        r config set maxmemory 1
        r config set maxmemory-policy volatile-lru

        # sanity test plain call
        assert_equal {OK} [
            r test.rm_call set x 1
        ]

        # add the M flag
        assert_error {OOM *} {
            r test.rm_call_flags M set x 1

        }

        # test a non deny-oom command
        assert_equal {1} [
            r test.rm_call_flags M get x
        ]

        r config set maxmemory 0
    } {OK} {needs:config-maxmemory}
    """
    r.run("config", "set", "maxmemory", 1)
    r.run("config", "set", "maxmemory-policy", "volatile-lru")
    assert "OK" == r.run("test.rm_call", "set", "x", 1)
    with pytest.raises(Exception, match="OOM\\ .*"):
        r.run("test.rm_call_flags", "M", "set", "x", 1)
    assert "1" == r.run("test.rm_call_flags", "M", "get", "x")
    assert r.run("config", "set", "maxmemory", 0) == "OK"


def test_rm_call_clear_oom(r: ValkeyTestClient) -> None:
    """
    test {rm_call clear OOM} {
        r config set maxmemory 1

        # verify rm_call fails with OOM
        assert_error {OOM *} {
            r test.rm_call_flags M set x 1
        }

        # clear OOM state
        r config set maxmemory 0

        # test set command is allowed
        r test.rm_call_flags M set x 1
    } {OK} {needs:config-maxmemory}
    """
    r.run("config", "set", "maxmemory", 1)
    with pytest.raises(Exception, match="OOM\\ .*"):
        r.run("test.rm_call_flags", "M", "set", "x", 1)
    r.run("config", "set", "maxmemory", 0)
    assert r.run("test.rm_call_flags", "M", "set", "x", 1) == "OK"


def test_rm_call_oom_eval(r: ValkeyTestClient) -> None:
    """
    test {rm_call OOM Eval} {
        r config set maxmemory 1
        r config set maxmemory-policy volatile-lru

        # use the M flag without allow-oom shebang flag
        assert_error {OOM *} {
            r test.rm_call_flags M eval {#!lua
                redis.call('set','x',1)
                return 1
            } 1 x
        }

        # add the M flag with allow-oom shebang flag
        assert_equal {1} [
            r test.rm_call_flags M eval {#!lua flags=allow-oom
                redis.call('set','x',1)
                return 1
            } 1 x
        ]

        r config set maxmemory 0
    } {OK} {needs:config-maxmemory}
    """
    r.run("config", "set", "maxmemory", 1)
    r.run("config", "set", "maxmemory-policy", "volatile-lru")
    with pytest.raises(Exception, match="OOM\\ .*"):
        r.run(
            "test.rm_call_flags",
            "M",
            "eval",
            "#!lua\n                redis.call('set','x',1)\n                return 1\n            ",
            1,
            "x",
        )
    assert "1" == r.run(
        "test.rm_call_flags",
        "M",
        "eval",
        "#!lua flags=allow-oom                redis.call('set','x',1)                return 1            ",
        1,
        "x",
    )
    assert r.run("config", "set", "maxmemory", 0) == "OK"


def test_rm_call_write_flag(r: ValkeyTestClient) -> None:
    """
    test {rm_call write flag} {
        # add the W flag
        assert_error {ERR Write command 'set' was called while write is not allowed.} {
            r test.rm_call_flags W set x 1
        }

        # test a non deny-oom command
        r test.rm_call_flags W get x
    } {1}
    """
    with pytest.raises(
        Exception, match="ERR\\ Write\\ command\\ 'set'\\ was\\ called\\ while\\ write\\ is\\ not\\ allowed\\."
    ):
        r.run("test.rm_call_flags", "W", "set", "x", 1)
    assert r.run("test.rm_call_flags", "W", "get", "x") == "1"


def test_rm_call_eval(r: ValkeyTestClient) -> None:
    """
    test {rm_call EVAL} {
        r test.rm_call eval {
            redis.call('set','x',1)
            return 1
        } 1 x

        assert_error {ERR Write commands are not allowed from read-only scripts.*} {
            r test.rm_call eval {#!lua flags=no-writes
                redis.call('set','x',1)
                return 1
            } 1 x
        }
    }
    """
    r.run("test.rm_call", "eval", "            redis.call('set','x',1)\n            return 1\n        ", 1, "x")
    with pytest.raises(
        Exception, match="ERR\\ Write\\ commands\\ are\\ not\\ allowed\\ from\\ read\\-only\\ scripts\\..*"
    ):
        r.run(
            "test.rm_call",
            "eval",
            "#!lua flags=no-writes\n                redis.call('set','x',1)\n                return 1\n            ",
            1,
            "x",
        )


def test_rm_call_eval_oom_with_m_flag(r: ValkeyTestClient) -> None:
    """
    test {rm_call EVAL - OOM - with M flag} {
        r config set maxmemory 1

        # script without shebang, but uses SET, so fails
        assert_error {*OOM command not allowed when used memory > 'maxmemory'*} {
            r test.rm_call_flags M eval {
                redis.call('set','x',1)
                return 1
            } 1 x
        }

        # script with an allow-oom flag, succeeds despite using SET
        r test.rm_call_flags M eval {#!lua flags=allow-oom
            redis.call('set','x', 1)
            return 2
        } 1 x

        # script with no-writes flag, implies allow-oom, succeeds
        r test.rm_call_flags M eval {#!lua flags=no-writes
            redis.call('get','x')
            return 2
        } 1 x

        # script with shebang using default flags, so fails regardless of using only GET
        assert_error {*OOM command not allowed when used memory > 'maxmemory'*} {
            r test.rm_call_flags M eval {#!lua
                redis.call('get','x')
                return 3
            } 1 x
        }

        # script without shebang, but uses GET, so succeeds
        r test.rm_call_flags M eval {
            redis.call('get','x')
            return 4
        } 1 x

        r config set maxmemory 0
    } {OK} {needs:config-maxmemory}
    """
    r.run("config", "set", "maxmemory", 1)
    with pytest.raises(Exception, match=".*OOM\\ command\\ not\\ allowed\\ when\\ used\\ memory\\ >\\ 'maxmemory'.*"):
        r.run(
            "test.rm_call_flags",
            "M",
            "eval",
            "                redis.call('set','x',1)\n                return 1\n            ",
            1,
            "x",
        )
    r.run(
        "test.rm_call_flags",
        "M",
        "eval",
        "#!lua flags=allow-oom\n            redis.call('set','x', 1)\n            return 2\n        ",
        1,
        "x",
    )
    r.run(
        "test.rm_call_flags",
        "M",
        "eval",
        "#!lua flags=no-writes\n            redis.call('get','x')\n            return 2\n        ",
        1,
        "x",
    )
    with pytest.raises(Exception, match=".*OOM\\ command\\ not\\ allowed\\ when\\ used\\ memory\\ >\\ 'maxmemory'.*"):
        r.run(
            "test.rm_call_flags",
            "M",
            "eval",
            "#!lua\n                redis.call('get','x')\n                return 3\n            ",
            1,
            "x",
        )
    r.run(
        "test.rm_call_flags", "M", "eval", "            redis.call('get','x')\n            return 4\n        ", 1, "x"
    )
    assert r.run("config", "set", "maxmemory", 0) == "OK"


def test_rm_call_eval_oom_without_m_flag(r: ValkeyTestClient) -> None:
    """
    test {rm_call EVAL - OOM - without M flag} {
        r config set maxmemory 1

        # no shebang at all
        r test.rm_call eval {
            redis.call('set','x',1)
            return 6
        } 1 x

        # Shebang without flags
        r test.rm_call eval {#!lua
            redis.call('set','x', 1)
            return 7
        } 1 x

        # with allow-oom flag
        r test.rm_call eval {#!lua flags=allow-oom
            redis.call('set','x', 1)
            return 8
        } 1 x

        r config set maxmemory 0
    } {OK} {needs:config-maxmemory}
    """
    r.run("config", "set", "maxmemory", 1)
    r.run("test.rm_call", "eval", "            redis.call('set','x',1)\n            return 6\n        ", 1, "x")
    r.run("test.rm_call", "eval", "#!lua\n            redis.call('set','x', 1)\n            return 7\n        ", 1, "x")
    r.run(
        "test.rm_call",
        "eval",
        "#!lua flags=allow-oom\n            redis.call('set','x', 1)\n            return 8\n        ",
        1,
        "x",
    )
    assert r.run("config", "set", "maxmemory", 0) == "OK"


def test_not_enough_good_replicas(r: ValkeyTestClient) -> None:
    """
    test "not enough good replicas" {
        r set x "some value"
        r config set min-replicas-to-write 1

        # rm_call in script mode
        assert_error {NOREPLICAS *} {r test.rm_call_flags S set x s}

        assert_equal [
            r test.rm_call eval {#!lua flags=no-writes
                return redis.call('get','x')
            } 1 x
        ] "some value"

        assert_equal [
            r test.rm_call eval {
                return redis.call('get','x')
            } 1 x
        ] "some value"

        assert_error {NOREPLICAS *} {
            r test.rm_call eval {#!lua
                return redis.call('get','x')
            } 1 x
        }

        assert_error {NOREPLICAS *} {
            r test.rm_call eval {
                return redis.call('set','x', 1)
            } 1 x
        }

        r config set min-replicas-to-write 0
    }
    """
    r.run("set", "x", "some value")
    r.run("config", "set", "min-replicas-to-write", 1)
    with pytest.raises(Exception, match="NOREPLICAS\\ .*"):
        r.run("test.rm_call_flags", "S", "set", "x", "s")
    assert (
        r.run(
            "test.rm_call",
            "eval",
            "#!lua flags=no-writes                return redis.call('get','x')            ",
            1,
            "x",
        )
        == "some value"
    )
    assert (
        r.run("test.rm_call", "eval", "                return redis.call('get','x')            ", 1, "x")
        == "some value"
    )
    with pytest.raises(Exception, match="NOREPLICAS\\ .*"):
        r.run("test.rm_call", "eval", "#!lua\n                return redis.call('get','x')\n            ", 1, "x")
    with pytest.raises(Exception, match="NOREPLICAS\\ .*"):
        r.run("test.rm_call", "eval", "                return redis.call('set','x', 1)\n            ", 1, "x")
    r.run("config", "set", "min-replicas-to-write", 0)


def test_rm_call_eval_read_only_replica(r: ValkeyTestClient) -> None:
    """
    test {rm_call EVAL - read-only replica} {
        r replicaof 127.0.0.1 1

        # rm_call in script mode
        assert_error {READONLY *} {r test.rm_call_flags S set x 1}

        assert_error {READONLY You can't write against a read only replica. script*} {
            r test.rm_call eval {
                redis.call('set','x',1)
                return 1
            } 1 x
        }

        r test.rm_call eval {#!lua flags=no-writes
            redis.call('get','x')
            return 2
        } 1 x

        assert_error {READONLY Can not run script with write flag on readonly replica*} {
            r test.rm_call eval {#!lua
                redis.call('get','x')
                return 3
            } 1 x
        }

        r test.rm_call eval {
            redis.call('get','x')
            return 4
        } 1 x

        r replicaof no one
    } {OK} {needs:config-maxmemory}
    """
    r.run("replicaof", "127.0.0.1", 1)
    with pytest.raises(Exception, match="READONLY\\ .*"):
        r.run("test.rm_call_flags", "S", "set", "x", 1)
    with pytest.raises(
        Exception, match="READONLY\\ You\\ can't\\ write\\ against\\ a\\ read\\ only\\ replica\\.\\ script.*"
    ):
        r.run(
            "test.rm_call",
            "eval",
            "                redis.call('set','x',1)\n                return 1\n            ",
            1,
            "x",
        )
    r.run(
        "test.rm_call",
        "eval",
        "#!lua flags=no-writes\n            redis.call('get','x')\n            return 2\n        ",
        1,
        "x",
    )
    with pytest.raises(
        Exception, match="READONLY\\ Can\\ not\\ run\\ script\\ with\\ write\\ flag\\ on\\ readonly\\ replica.*"
    ):
        r.run(
            "test.rm_call",
            "eval",
            "#!lua\n                redis.call('get','x')\n                return 3\n            ",
            1,
            "x",
        )
    r.run("test.rm_call", "eval", "            redis.call('get','x')\n            return 4\n        ", 1, "x")
    assert r.run("replicaof", "no", "one") == "OK"


def test_rm_call_eval_stale_replica(r: ValkeyTestClient) -> None:
    """
    test {rm_call EVAL - stale replica} {
        r replicaof 127.0.0.1 1
        r config set replica-serve-stale-data no

        # rm_call in script mode
        assert_error {MASTERDOWN *} {
            r test.rm_call_flags S get x
        }

        assert_error {MASTERDOWN *} {
            r test.rm_call eval {#!lua flags=no-writes
                redis.call('get','x')
                return 2
            } 1 x
        }

        assert_error {MASTERDOWN *} {
            r test.rm_call eval {
                redis.call('get','x')
                return 4
            } 1 x
        }

        r replicaof no one
        r config set replica-serve-stale-data yes
    } {OK} {needs:config-maxmemory}
    """
    r.run("replicaof", "127.0.0.1", 1)
    r.run("config", "set", "replica-serve-stale-data", "no")
    with pytest.raises(Exception, match="MASTERDOWN\\ .*"):
        r.run("test.rm_call_flags", "S", "get", "x")
    with pytest.raises(Exception, match="MASTERDOWN\\ .*"):
        r.run(
            "test.rm_call",
            "eval",
            "#!lua flags=no-writes\n                redis.call('get','x')\n                return 2\n            ",
            1,
            "x",
        )
    with pytest.raises(Exception, match="MASTERDOWN\\ .*"):
        r.run(
            "test.rm_call",
            "eval",
            "                redis.call('get','x')\n                return 4\n            ",
            1,
            "x",
        )
    r.run("replicaof", "no", "one")
    assert r.run("config", "set", "replica-serve-stale-data", "yes") == "OK"


def test_rm_call_eval_failed_bgsave_prevents_writes(r: ValkeyTestClient) -> None:
    """
    test "rm_call EVAL - failed bgsave prevents writes" {
        r config set rdb-key-save-delay 10000000
        populate 1000
        r set x x
        r bgsave
        set pid1 [get_child_pid 0]
        catch {exec kill -9 $pid1}
        waitForBgsave r

        # make sure a read command succeeds
        assert_equal [r get x] x

        # make sure a write command fails
        assert_error {MISCONF *} {r set x y}

        # rm_call in script mode
        assert_error {MISCONF *} {r test.rm_call_flags S set x 1}

        # repeat with script
        assert_error {MISCONF *} {r test.rm_call eval {
            return redis.call('set','x',1)
            } 1 x
        }
        assert_equal {x} [r test.rm_call eval {
            return redis.call('get','x')
            } 1 x
        ]

        # again with script using shebang
        assert_error {MISCONF *} {r test.rm_call eval {#!lua
            return redis.call('set','x',1)
            } 1 x
        }
        assert_equal {x} [r test.rm_call eval {#!lua flags=no-writes
            return redis.call('get','x')
            } 1 x
        ]

        r config set rdb-key-save-delay 0
        r bgsave
        waitForBgsave r

        # server is writable again
        r set x y
    } {OK}
    """
    r.run("config", "set", "rdb-key-save-delay", 10000000)
    populate(1000)
    r.run("set", "x", "x")
    r.run("bgsave")
    pid1 = get_child_pid(0)
    catch("exec kill -9 $pid1")
    wait_for_bgsave("r")
    assert r.run("get", "x") == "x"
    with pytest.raises(Exception, match="MISCONF\\ .*"):
        r.run("set", "x", "y")
    with pytest.raises(Exception, match="MISCONF\\ .*"):
        r.run("test.rm_call_flags", "S", "set", "x", 1)
    with pytest.raises(Exception, match="MISCONF\\ .*"):
        r.run("test.rm_call", "eval", "            return redis.call('set','x',1)\n            ", 1, "x")
    assert "x" == r.run("test.rm_call", "eval", "            return redis.call('get','x')            ", 1, "x")
    with pytest.raises(Exception, match="MISCONF\\ .*"):
        r.run("test.rm_call", "eval", "#!lua\n            return redis.call('set','x',1)\n            ", 1, "x")
    assert "x" == r.run(
        "test.rm_call", "eval", "#!lua flags=no-writes            return redis.call('get','x')            ", 1, "x"
    )
    r.run("config", "set", "rdb-key-save-delay", 0)
    r.run("bgsave")
    wait_for_bgsave("r")
    assert r.run("set", "x", "y") == "OK"


def test_malloc_api(r: ValkeyTestClient) -> None:
    """
    test "malloc API" {
        assert_equal {OK} [r test.malloc_api 0]
    }
    """
    assert "OK" == r.run("test.malloc_api", 0)


def test_cluster_keyslot(r: ValkeyTestClient) -> None:
    """
    test "Cluster keyslot" {
        assert_equal 12182 [r test.keyslot foo]
    }
    """
    assert 12182 == r.run("test.keyslot", "foo")


pytestmark = [pytest.mark.modules]


"""
r module load testmodule
"""


def test_test_dry_run_ok_oom_or_acl(r: ValkeyTestClient) -> None:
    """
    test {test Dry Run - OK OOM/ACL} {
        set x 5
        r set x $x
        catch {r test.rm_call_flags DMC set x 10} e
        assert_match {*NULL reply returned*} $e
        assert_equal [r get x] 5
    }
    """
    x = 5
    r.run("set", "x", x)
    try:
        e = r.run("test.rm_call_flags", "DMC", "set", "x", 10)
    except Exception as _catch_err:
        e = str(_catch_err)
    assert fnmatch(str(e), "*NULL reply returned*")
    assert r.run("get", "x") == 5


def test_test_dry_run_fail_oom(r: ValkeyTestClient) -> None:
    """
    test {test Dry Run - Fail OOM} {
        set x 5
        r set x $x
        r config set maxmemory 1
        catch {r test.rm_call_flags DM set x 10} e
        assert_match {*OOM*} $e
        assert_equal [r get x] $x
        r config set maxmemory 0
    } {OK} {needs:config-maxmemory}
    """
    x = 5
    r.run("set", "x", x)
    r.run("config", "set", "maxmemory", 1)
    try:
        e = r.run("test.rm_call_flags", "DM", "set", "x", 10)
    except Exception as _catch_err:
        e = str(_catch_err)
    assert fnmatch(str(e), "*OOM*")
    assert r.run("get", "x") == x
    assert r.run("config", "set", "maxmemory", 0) == "OK"


def test_test_dry_run_fail_acl(r: ValkeyTestClient) -> None:
    """
    test {test Dry Run - Fail ACL} {
        set x 5
        r set x $x
        # deny all permissions besides the dryrun command
        r acl setuser default resetkeys

        catch {r test.rm_call_flags DC set x 10} e
        assert_match {*NOPERM No permissions to access a key*} $e
        r acl setuser default +@all ~*
        assert_equal [r get x] $x
    }
    """
    x = 5
    r.run("set", "x", x)
    r.run("acl", "setuser", "default", "resetkeys")
    try:
        e = r.run("test.rm_call_flags", "DC", "set", "x", 10)
    except Exception as _catch_err:
        e = str(_catch_err)
    assert fnmatch(str(e), "*NOPERM No permissions to access a key*")
    r.run("acl", "setuser", "default", "+@all", "~*")
    assert r.run("get", "x") == x


def test_test_silent_open_key(r: ValkeyTestClient) -> None:
    """
    test {test silent open key} {
        r debug set-active-expire 0
        r test.clear_n_events
        r set x 1 PX 10
        after 1000
        # now the key has been expired, open it silently and make sure not event were fired.
        assert_error {key not found} {r test.silent_open_key x}
        assert_equal {0} [r test.get_n_events]
    }
    """
    r.run("debug", "set-active-expire", 0)
    r.run("test.clear_n_events")
    r.run("set", "x", 1, "PX", 10)
    time.sleep(1000 / 1000)
    with pytest.raises(Exception, match="key\\ not\\ found"):
        r.run("test.silent_open_key", "x")
    assert "0" == r.run("test.get_n_events")


@pytest.mark.skipif("", reason="{[string match {*jemalloc*} [s mem_allocator]]}")
def test_test_rm_call_with_large_arg_for_set_command(r: ValkeyTestClient) -> None:
    """
    test {test RM_Call with large arg for SET command} {
        # set a big value to trigger increasing the query buf
        r set foo [string repeat A 100000]
        # set a smaller value but > PROTO_MBULK_BIG_ARG (32*1024) the server will try to save the query buf itself on the DB.
        r test.call_generic set bar [string repeat A 33000]
        # asset the value was trimmed
        assert {[r memory usage bar] < 42000}; # 42K to count for Jemalloc's additional memory overhead.
    }
    """
    r.run("set", "foo", string("repeat", "A", 100000))
    r.run("test.call_generic", "set", "bar", string("repeat", "A", 33000))
    assert r.run("memory", "usage", "bar") < 42000


def test_unload_the_module_misc(r: ValkeyTestClient) -> None:
    """
    test "Unload the module - misc" {
        assert_equal {OK} [r module unload misc]
    }
    """
    assert "OK" == r.run("module", "unload", "misc")


# --- stubs for unimplemented TCL helpers ---


def assert_(*args):
    raise NotImplementedError("assert_")


def catch(*args):
    raise NotImplementedError("catch")


def get_child_pid(*args):
    raise NotImplementedError("get_child_pid")


def if_(*args):
    raise NotImplementedError("if_")


def parse_client_flags(*args):
    raise NotImplementedError("parse_client_flags")


def populate(*args):
    raise NotImplementedError("populate")


def s(*args):
    raise NotImplementedError("s")


def string(*args):
    raise NotImplementedError("string")


def valkey_client(*args):
    raise NotImplementedError("valkey_client")


def verify_log_message(*args):
    raise NotImplementedError("verify_log_message")


def wait_for_bgsave(*args):
    raise NotImplementedError("wait_for_bgsave")
