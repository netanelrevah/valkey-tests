from fnmatch import fnmatch

import pytest

from tests.valkey_test_client import ValkeyTestClient

testmodule = "tests/modules/getkeys.so"

pytestmark = [pytest.mark.modules]


def test_command_info_correctly_reports_a_movable_keys_module_command(r: ValkeyTestClient) -> None:
    """
    test {COMMAND INFO correctly reports a movable keys module command} {
        set info [lindex [r command info getkeys.command] 0]

        assert_equal {module movablekeys} [lindex $info 2]
        assert_equal {0} [lindex $info 3]
        assert_equal {0} [lindex $info 4]
        assert_equal {0} [lindex $info 5]
    }
    """
    r.run("module", "load", testmodule)
    info = r.run("command", "info", "getkeys.command")[0]
    assert "module movablekeys" == info[2]
    assert "0" == info[3]
    assert "0" == info[4]
    assert "0" == info[5]


def test_command_getkeys_correctly_reports_a_movable_keys_module_command(r: ValkeyTestClient) -> None:
    """
    test {COMMAND GETKEYS correctly reports a movable keys module command} {
        r command getkeys getkeys.command arg1 arg2 key key1 arg3 key key2 key key3
    } {key1 key2 key3}
    """
    r.run("module", "load", testmodule)
    assert (
        r.run(
            "command", "getkeys", "getkeys.command", "arg1", "arg2", "key", "key1", "arg3", "key", "key2", "key", "key3"
        )
        == "key1 key2 key3"
    )


def test_command_getkeys_correctly_reports_a_movable_keys_module_command_using_flags(r: ValkeyTestClient) -> None:
    """
    test {COMMAND GETKEYS correctly reports a movable keys module command using flags} {
        r command getkeys getkeys.command_with_flags arg1 arg2 key key1 arg3 key key2 key key3
    } {key1 key2 key3}
    """
    r.run("module", "load", testmodule)
    assert (
        r.run(
            "command",
            "getkeys",
            "getkeys.command_with_flags",
            "arg1",
            "arg2",
            "key",
            "key1",
            "arg3",
            "key",
            "key2",
            "key",
            "key3",
        )
        == "key1 key2 key3"
    )


def test_command_getkeysandflags_correctly_reports_a_movable_keys_module_command_not_using_flags(
    r: ValkeyTestClient,
) -> None:
    """
    test {COMMAND GETKEYSANDFLAGS correctly reports a movable keys module command not using flags} {
        r command getkeysandflags getkeys.command arg1 arg2 key key1 arg3 key key2
    } {{key1 {RW access update}} {key2 {RW access update}}}
    """
    r.run("module", "load", testmodule)
    assert (
        r.run("command", "getkeysandflags", "getkeys.command", "arg1", "arg2", "key", "key1", "arg3", "key", "key2")
        == "{key1 {RW access update}} {key2 {RW access update}}"
    )


def test_command_getkeysandflags_correctly_reports_a_movable_keys_module_command_using_flags(
    r: ValkeyTestClient,
) -> None:
    """
    test {COMMAND GETKEYSANDFLAGS correctly reports a movable keys module command using flags} {
        r command getkeysandflags getkeys.command_with_flags arg1 arg2 key key1 arg3 key key2 key key3
    } {{key1 {RO access}} {key2 {RO access}} {key3 {RO access}}}
    """
    r.run("module", "load", testmodule)
    assert (
        r.run(
            "command",
            "getkeysandflags",
            "getkeys.command_with_flags",
            "arg1",
            "arg2",
            "key",
            "key1",
            "arg3",
            "key",
            "key2",
            "key",
            "key3",
        )
        == "{key1 {RO access}} {key2 {RO access}} {key3 {RO access}}"
    )


def test_rm_getcommandkeys_on_non_existing_command(r: ValkeyTestClient) -> None:
    """
    test {RM_GetCommandKeys on non-existing command} {
        catch {r getkeys.introspect 0 non-command key1 key2} e
        set _ $e
    } {*ENOENT*}
    """
    r.run("module", "load", testmodule)
    try:
        e = r.run("getkeys.introspect", 0, "non-command", "key1", "key2")
    except Exception as _catch_err:
        e = str(_catch_err)
    assert fnmatch(str(e), "*ENOENT*")


def test_rm_getcommandkeys_on_built_in_fixed_keys_command(r: ValkeyTestClient) -> None:
    """
    test {RM_GetCommandKeys on built-in fixed keys command} {
        r getkeys.introspect 0 set key1 value1
    } {key1}
    """
    r.run("module", "load", testmodule)
    assert r.run("getkeys.introspect", 0, "set", "key1", "value1") == "key1"


def test_rm_getcommandkeys_on_built_in_fixed_keys_command_with_flags(r: ValkeyTestClient) -> None:
    """
    test {RM_GetCommandKeys on built-in fixed keys command with flags} {
        r getkeys.introspect 1 set key1 value1
    } {{key1 OW}}
    """
    r.run("module", "load", testmodule)
    assert r.run("getkeys.introspect", 1, "set", "key1", "value1") == "{key1 OW}"


def test_rm_getcommandkeys_on_eval(r: ValkeyTestClient) -> None:
    """
    test {RM_GetCommandKeys on EVAL} {
        r getkeys.introspect 0 eval "" 4 key1 key2 key3 key4 arg1 arg2
    } {key1 key2 key3 key4}
    """
    r.run("module", "load", testmodule)
    assert (
        r.run("getkeys.introspect", 0, "eval", "", 4, "key1", "key2", "key3", "key4", "arg1", "arg2")
        == "key1 key2 key3 key4"
    )


def test_rm_getcommandkeys_on_a_movable_keys_module_command(r: ValkeyTestClient) -> None:
    """
    test {RM_GetCommandKeys on a movable keys module command} {
        r getkeys.introspect 0 getkeys.command arg1 arg2 key key1 arg3 key key2 key key3
    } {key1 key2 key3}
    """
    r.run("module", "load", testmodule)
    assert (
        r.run(
            "getkeys.introspect",
            0,
            "getkeys.command",
            "arg1",
            "arg2",
            "key",
            "key1",
            "arg3",
            "key",
            "key2",
            "key",
            "key3",
        )
        == "key1 key2 key3"
    )


def test_rm_getcommandkeys_on_a_non_movable_module_command(r: ValkeyTestClient) -> None:
    """
    test {RM_GetCommandKeys on a non-movable module command} {
        r getkeys.introspect 0 getkeys.fixed arg1 key1 key2 key3 arg2
    } {key1 key2 key3}
    """
    r.run("module", "load", testmodule)
    assert r.run("getkeys.introspect", 0, "getkeys.fixed", "arg1", "key1", "key2", "key3", "arg2") == "key1 key2 key3"


def test_rm_getcommandkeys_with_bad_arity(r: ValkeyTestClient) -> None:
    """
    test {RM_GetCommandKeys with bad arity} {
        catch {r getkeys.introspect 0 set key} e
        set _ $e
    } {*EINVAL*}
    """
    r.run("module", "load", testmodule)
    try:
        e = r.run("getkeys.introspect", 0, "set", "key")
    except Exception as _catch_err:
        e = str(_catch_err)
    assert fnmatch(str(e), "*EINVAL*")


def test_module_getkeys_api_acl(r: ValkeyTestClient) -> None:
    """
    test "module getkeys-api - ACL" {
        # legacy triple didn't provide flags, so they require both read and write
        assert_equal "OK" [r ACL DRYRUN testuser getkeys.command key rw]
        assert_match {*has no permissions to access the 'read' key*} [r ACL DRYRUN testuser getkeys.command key read]
        assert_match {*has no permissions to access the 'write' key*} [r ACL DRYRUN testuser getkeys.command key write]
    }
    """
    r.run("ACL", "setuser", "testuser", "+@all", "%R~read*", "%W~write*", "%RW~rw*")
    assert "OK" == r.run("ACL", "DRYRUN", "testuser", "getkeys.command", "key", "rw")
    assert fnmatch(
        str(r.run("ACL", "DRYRUN", "testuser", "getkeys.command", "key", "read")),
        "*has no permissions to access the 'read' key*",
    )
    assert fnmatch(
        str(r.run("ACL", "DRYRUN", "testuser", "getkeys.command", "key", "write")),
        "*has no permissions to access the 'write' key*",
    )


def test_module_getkeys_api_with_flags_acl(r: ValkeyTestClient) -> None:
    """
    test "module getkeys-api with flags - ACL" {
        assert_equal "OK" [r ACL DRYRUN testuser getkeys.command_with_flags key rw]
        assert_equal "OK" [r ACL DRYRUN testuser getkeys.command_with_flags key read]
        assert_match {*has no permissions to access the 'write' key*} [r ACL DRYRUN testuser getkeys.command_with_flags key write]
    }
    """
    r.run("ACL", "setuser", "testuser", "+@all", "%R~read*", "%W~write*", "%RW~rw*")
    assert "OK" == r.run("ACL", "DRYRUN", "testuser", "getkeys.command_with_flags", "key", "rw")
    assert "OK" == r.run("ACL", "DRYRUN", "testuser", "getkeys.command_with_flags", "key", "read")
    assert fnmatch(
        str(r.run("ACL", "DRYRUN", "testuser", "getkeys.command_with_flags", "key", "write")),
        "*has no permissions to access the 'write' key*",
    )


def test_unload_the_module_getkeys(r: ValkeyTestClient) -> None:
    """
    test "Unload the module - getkeys" {
        assert_equal {OK} [r module unload getkeys]
    }
    """
    r.run("ACL", "setuser", "testuser", "+@all", "%R~read*", "%W~write*", "%RW~rw*")
    assert "OK" == r.run("module", "unload", "getkeys")
