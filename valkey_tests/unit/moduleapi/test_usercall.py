# ruff: noqa: PLR2004, RUF043

from fnmatch import fnmatch

import pytest

from tests.valkey_test_client import ValkeyTestClient

testmodule = "tests/modules/usercall.so"

test_script_set = "#!lua\nredis.call('set','x',1)\nreturn 1"

test_script_get = "#!lua\nredis.call('get','x')\nreturn 1"

pytestmark = [pytest.mark.modules_usercall_network]


def test_test_module_check_regular_valkey_command_without_user_or_acl(r: ValkeyTestClient) -> None:
    """
    test {test module check regular valkey command without user/acl} {
        assert_equal [r usercall.reset_user] OK
        assert_equal [r usercall.add_to_acl "~* &* +@all -set"] OK
        assert_equal [r usercall.call_without_user set x 5] OK
        assert_equal [r usercall.reset_user] OK
    }
    """
    r.run("module", "load", testmodule)
    assert r.run("usercall.reset_user") == "OK"
    assert r.run("usercall.add_to_acl", "~* &* +@all -set") == "OK"
    assert r.run("usercall.call_without_user", "set", "x", 5) == "OK"
    assert r.run("usercall.reset_user") == "OK"


def test_test_module_check_regular_valkey_command_with_user(r: ValkeyTestClient) -> None:
    """
    test {test module check regular valkey command with user} {
        assert_equal [r set x 5] OK

        assert_equal [r usercall.reset_user] OK
        assert_equal [r usercall.add_to_acl "~* &* +@all -set"] OK
        # off and sanitize-payload because module user / default value
        assert_equal [r usercall.get_acl] "off sanitize-payload ~* &* alldbs +@all -set"

        # doesn't fail for regular commands as just testing acl here
        assert_equal [r usercall.call_with_user_flag {} set x 10] OK

        assert_equal [r get x] 10
        assert_equal [r usercall.reset_user] OK
    }
    """
    r.run("module", "load", testmodule)
    assert r.run("set", "x", 5) == "OK"
    assert r.run("usercall.reset_user") == "OK"
    assert r.run("usercall.add_to_acl", "~* &* +@all -set") == "OK"
    assert r.run("usercall.get_acl") == "off sanitize-payload ~* &* alldbs +@all -set"
    assert r.run("usercall.call_with_user_flag", "", "set", "x", 10) == "OK"
    assert r.run("get", "x") == 10
    assert r.run("usercall.reset_user") == "OK"


def test_test_module_check_regular_valkey_command_with_user_and_acl(r: ValkeyTestClient) -> None:
    """
    test {test module check regular valkey command with user and acl} {
        assert_equal [r set x 5] OK

        r ACL LOG RESET
        assert_equal [r usercall.reset_user] OK
        assert_equal [r usercall.add_to_acl "~* &* +@all -set"] OK
        # off and sanitize-payload because module user / default value
        assert_equal [r usercall.get_acl] "off sanitize-payload ~* &* alldbs +@all -set"

        # fails here as testing acl in rm call
        assert_error {*NOPERM User module_user has no permissions*} {r usercall.call_with_user_flag C set x 10}

        assert_equal [r usercall.call_with_user_flag C get x] 5

        # verify that new log entry added
        set entry [lindex [r ACL LOG] 0]
        assert_equal [dict get $entry username] {module_user}
        assert_equal [dict get $entry context] {module}
        assert_equal [dict get $entry object] {set}
        assert_equal [dict get $entry reason] {command}
        assert_match {*cmd=usercall.call_with_user_flag*} [dict get $entry client-info]

        assert_equal [r usercall.reset_user] OK
    }
    """
    r.run("module", "load", testmodule)
    assert r.run("set", "x", 5) == "OK"
    r.run("ACL", "LOG", "RESET")
    assert r.run("usercall.reset_user") == "OK"
    assert r.run("usercall.add_to_acl", "~* &* +@all -set") == "OK"
    assert r.run("usercall.get_acl") == "off sanitize-payload ~* &* alldbs +@all -set"
    with pytest.raises(Exception, match=".*NOPERM\\ User\\ module_user\\ has\\ no\\ permissions.*"):
        r.run("usercall.call_with_user_flag", "C", "set", "x", 10)
    assert r.run("usercall.call_with_user_flag", "C", "get", "x") == 5
    entry = r.run("ACL", "LOG")[0]
    assert entry["username"] == "module_user"
    assert entry["context"] == "module"
    assert entry["object"] == "set"
    assert entry["reason"] == "command"
    assert fnmatch(str(entry["client-info"]), "*cmd=usercall.call_with_user_flag*")
    assert r.run("usercall.reset_user") == "OK"


def test_test_module_check_regular_valkey_command_with_user_and_acl_from_blocked_background_thread(
    r: ValkeyTestClient,
) -> None:
    """
    test {test module check regular valkey command with user and acl from blocked background thread} {
        assert_equal [r set x 5] OK

        r ACL LOG RESET
        assert_equal [r usercall.reset_user] OK
        assert_equal [r usercall.add_to_acl "~* &* +@all -set"] OK

        # fails here as testing acl in rm call from a background thread
        assert_error {*NOPERM User module_user has no permissions*} {r usercall.call_with_user_bg C set x 10}

        assert_equal [r usercall.call_with_user_bg C get x] 5

        # verify that new log entry added
        set entry [lindex [r ACL LOG] 0]
        assert_equal [dict get $entry username] {module_user}
        assert_equal [dict get $entry context] {module}
        assert_equal [dict get $entry object] {set}
        assert_equal [dict get $entry reason] {command}
        assert_match {*cmd=NULL*} [dict get $entry client-info]

        assert_equal [r usercall.reset_user] OK
    }
    """
    r.run("module", "load", testmodule)
    assert r.run("set", "x", 5) == "OK"
    r.run("ACL", "LOG", "RESET")
    assert r.run("usercall.reset_user") == "OK"
    assert r.run("usercall.add_to_acl", "~* &* +@all -set") == "OK"
    with pytest.raises(Exception, match=".*NOPERM\\ User\\ module_user\\ has\\ no\\ permissions.*"):
        r.run("usercall.call_with_user_bg", "C", "set", "x", 10)
    assert r.run("usercall.call_with_user_bg", "C", "get", "x") == 5
    entry = r.run("ACL", "LOG")[0]
    assert entry["username"] == "module_user"
    assert entry["context"] == "module"
    assert entry["object"] == "set"
    assert entry["reason"] == "command"
    assert fnmatch(str(entry["client-info"]), "*cmd=NULL*")
    assert r.run("usercall.reset_user") == "OK"


def test_test_module_check_eval_script_without_user(r: ValkeyTestClient) -> None:
    """
    test {test module check eval script without user} {
        set sha_set [r script load $test_script_set]
        set sha_get [r script load $test_script_get]

        assert_equal [r usercall.call_without_user evalsha $sha_set 0] 1
        assert_equal [r usercall.call_without_user evalsha $sha_get 0] 1
    }
    """
    r.run("module", "load", testmodule)
    sha_set = r.run("script", "load", test_script_set)
    sha_get = r.run("script", "load", test_script_get)
    assert r.run("usercall.call_without_user", "evalsha", sha_set, 0) == 1
    assert r.run("usercall.call_without_user", "evalsha", sha_get, 0) == 1


def test_test_module_check_eval_script_with_user_being_set_but_not_acl_testing(r: ValkeyTestClient) -> None:
    """
    test {test module check eval script with user being set, but not acl testing} {
        set sha_set [r script load $test_script_set]
        set sha_get [r script load $test_script_get]

        assert_equal [r usercall.reset_user] OK
        assert_equal [r usercall.add_to_acl "~* &* +@all -set"] OK
        # off and sanitize-payload because module user / default value
        assert_equal [r usercall.get_acl] "off sanitize-payload ~* &* alldbs +@all -set"

        # passes as not checking ACL
        assert_equal [r usercall.call_with_user_flag {} evalsha $sha_set 0] 1
        assert_equal [r usercall.call_with_user_flag {} evalsha $sha_get 0] 1
    }
    """
    r.run("module", "load", testmodule)
    sha_set = r.run("script", "load", test_script_set)
    sha_get = r.run("script", "load", test_script_get)
    assert r.run("usercall.reset_user") == "OK"
    assert r.run("usercall.add_to_acl", "~* &* +@all -set") == "OK"
    assert r.run("usercall.get_acl") == "off sanitize-payload ~* &* alldbs +@all -set"
    assert r.run("usercall.call_with_user_flag", "", "evalsha", sha_set, 0) == 1
    assert r.run("usercall.call_with_user_flag", "", "evalsha", sha_get, 0) == 1


def test_test_module_check_eval_script_with_user_and_acl(r: ValkeyTestClient) -> None:
    """
    test {test module check eval script with user and acl} {
        set sha_set [r script load $test_script_set]
        set sha_get [r script load $test_script_get]

        r ACL LOG RESET
        assert_equal [r usercall.reset_user] OK
        assert_equal [r usercall.add_to_acl "~* &* +@all -set"] OK

        # fails here in script, as rm_call will permit the eval call
        catch {r usercall.call_with_user_flag C evalsha $sha_set 0} e
        assert_match {*ERR ACL failure in script*} $e

        assert_equal [r usercall.call_with_user_flag C evalsha $sha_get 0] 1

        # verify that new log entry added
        set entry [lindex [r ACL LOG] 0]
        assert_equal [dict get $entry username] {module_user}
        assert_equal [dict get $entry context] {lua}
        assert_equal [dict get $entry object] {set}
        assert_equal [dict get $entry reason] {command}
        assert_match {*cmd=usercall.call_with_user_flag*} [dict get $entry client-info]
    }
    """
    r.run("module", "load", testmodule)
    sha_set = r.run("script", "load", test_script_set)
    sha_get = r.run("script", "load", test_script_get)
    r.run("ACL", "LOG", "RESET")
    assert r.run("usercall.reset_user") == "OK"
    assert r.run("usercall.add_to_acl", "~* &* +@all -set") == "OK"
    try:
        e = r.run("usercall.call_with_user_flag", "C", "evalsha", sha_set, 0)
    except Exception as _catch_err:
        e = str(_catch_err)
    assert fnmatch(str(e), "*ERR ACL failure in script*")
    assert r.run("usercall.call_with_user_flag", "C", "evalsha", sha_get, 0) == 1
    entry = r.run("ACL", "LOG")[0]
    assert entry["username"] == "module_user"
    assert entry["context"] == "lua"
    assert entry["object"] == "set"
    assert entry["reason"] == "command"
    assert fnmatch(str(entry["client-info"]), "*cmd=usercall.call_with_user_flag*")


"""
start_server {tags {"wait aof external:skip"}} {
    set slave [srv 0 client]
    set slave_host [srv 0 host]
    set slave_port [srv 0 port]
    set slave_pid [srv 0 pid]
    set master [srv -1 client]
    set master_host [srv -1 host]
    set master_port [srv -1 port]

    $master config set appendonly yes
    $master config set appendfsync everysec
    $slave config set appendonly yes
    $slave config set appendfsync everysec

    test {Setup slave} {
        $slave slaveof $master_host $master_port
        wait_for_condition 50 100 {
            [s 0 master_link_status] eq {up}
        } else {
            fail "Replication not started."
        }
    }

    test {test module replicate only to replicas and WAITAOF} {
        $master set x 1
        assert_equal [$master waitaof 1 1 10000] {1 1}
        $master usercall.call_with_user_flag A! config set loglevel notice
        # Make sure WAITAOF doesn't hang
        assert_equal [$master waitaof 1 1 10000] {1 1}
    }
}
"""
