# ruff: noqa: PLR2004, RUF043

from fnmatch import fnmatch

import pytest

from tests.valkey_test_client import ValkeyTestClient

"""
set testmodule file normalize tests/modules/aclcheck.so
"""

pytestmark = [pytest.mark.modules_acl]


"""
r module load testmodule
"""


def test_test_module_check_acl_for_command_perm(r: ValkeyTestClient) -> None:
    """
    test {test module check acl for command perm} {
        # by default all commands allowed
        assert_equal [r aclcheck.rm_call.check.cmd set x 5] OK
        # block SET command for user
        r acl setuser default -set
        catch {r aclcheck.rm_call.check.cmd set x 5} e
        assert_match {*DENIED CMD*} $e

        # verify that new log entry added
        set entry [lindex [r ACL LOG] 0]
        assert {[dict get $entry username] eq {default}}
        assert {[dict get $entry context] eq {module}}
        assert {[dict get $entry object] eq {set}}
        assert {[dict get $entry reason] eq {command}}
    }
    """
    assert r.run("aclcheck.rm_call.check.cmd", "set", "x", 5) == "OK"
    r.run("acl", "setuser", "default", "-set")
    try:
        e = r.run("aclcheck.rm_call.check.cmd", "set", "x", 5)
    except Exception as _catch_err:
        e = str(_catch_err)
    assert fnmatch(str(e), "*DENIED CMD*")
    entry = r.run("ACL", "LOG")[0]
    assert entry["username"] == "default"
    assert entry["context"] == "module"
    assert entry["object"] == "set"
    assert entry["reason"] == "command"


def test_test_module_check_acl_for_key_perm(r: ValkeyTestClient) -> None:
    """
    test {test module check acl for key perm} {
        # give permission for SET and block all keys but x(READ+WRITE), y(WRITE), z(READ)
        r acl setuser default +set resetkeys ~x %W~y %R~z

        assert_equal [r aclcheck.set.check.key "*" x 5] OK
        catch {r aclcheck.set.check.key "*" v 5} e
        assert_match "*DENIED KEY*" $e

        assert_equal [r aclcheck.set.check.key "~" x 5] OK
        assert_equal [r aclcheck.set.check.key "~" y 5] OK
        assert_equal [r aclcheck.set.check.key "~" z 5] OK
        catch {r aclcheck.set.check.key "~" v 5} e
        assert_match "*DENIED KEY*" $e

        assert_equal [r aclcheck.set.check.key "W" y 5] OK
        catch {r aclcheck.set.check.key "W" v 5} e
        assert_match "*DENIED KEY*" $e

        assert_equal [r aclcheck.set.check.key "R" z 5] OK
        catch {r aclcheck.set.check.key "R" v 5} e
        assert_match "*DENIED KEY*" $e
    }
    """
    r.run("acl", "setuser", "default", "+set", "resetkeys", "~x", "%W~y", "%R~z")
    assert r.run("aclcheck.set.check.key", "*", "x", 5) == "OK"
    try:
        e = r.run("aclcheck.set.check.key", "*", "v", 5)
    except Exception as _catch_err:
        e = str(_catch_err)
    assert fnmatch(str(e), "*DENIED KEY*")
    assert r.run("aclcheck.set.check.key", "~", "x", 5) == "OK"
    assert r.run("aclcheck.set.check.key", "~", "y", 5) == "OK"
    assert r.run("aclcheck.set.check.key", "~", "z", 5) == "OK"
    try:
        e = r.run("aclcheck.set.check.key", "~", "v", 5)
    except Exception as _catch_err:
        e = str(_catch_err)
    assert fnmatch(str(e), "*DENIED KEY*")
    assert r.run("aclcheck.set.check.key", "W", "y", 5) == "OK"
    try:
        e = r.run("aclcheck.set.check.key", "W", "v", 5)
    except Exception as _catch_err:
        e = str(_catch_err)
    assert fnmatch(str(e), "*DENIED KEY*")
    assert r.run("aclcheck.set.check.key", "R", "z", 5) == "OK"
    try:
        e = r.run("aclcheck.set.check.key", "R", "v", 5)
    except Exception as _catch_err:
        e = str(_catch_err)
    assert fnmatch(str(e), "*DENIED KEY*")


def test_test_module_check_acl_for_module_user(r: ValkeyTestClient) -> None:
    """
    test {test module check acl for module user} {
        # the module user has access to all keys
        assert_equal [r aclcheck.rm_call.check.cmd.module.user set y 5] OK
    }
    """
    assert r.run("aclcheck.rm_call.check.cmd.module.user", "set", "y", 5) == "OK"


def test_test_module_check_acl_for_channel_perm(r: ValkeyTestClient) -> None:
    """
    test {test module check acl for channel perm} {
        # block all channels but ch1
        r acl setuser default resetchannels &ch1
        assert_equal [r aclcheck.publish.check.channel ch1 msg] 0
        catch {r aclcheck.publish.check.channel ch2 msg} e
        set e
    } {*DENIED CHANNEL*}
    """
    r.run("acl", "setuser", "default", "resetchannels", "&ch1")
    assert r.run("aclcheck.publish.check.channel", "ch1", "msg") == 0
    try:
        e = r.run("aclcheck.publish.check.channel", "ch2", "msg")
    except Exception as _catch_err:
        e = str(_catch_err)
    assert e == "*DENIED CHANNEL*"


def test_test_module_check_acl_in_rm_call(r: ValkeyTestClient) -> None:
    """
    test {test module check acl in rm_call} {
        # rm call check for key permission (x: READ + WRITE)
        assert_equal [r aclcheck.rm_call set x 5] OK
        assert_equal [r aclcheck.rm_call set x 6 get] 5

        # rm call check for key permission (y: only WRITE)
        assert_equal [r aclcheck.rm_call set y 5] OK
        assert_error {*NOPERM*} {r aclcheck.rm_call set y 5 get}
        assert_error {*NOPERM*No permissions to access a key*} {r aclcheck.rm_call_with_errors set y 5 get}

        # rm call check for key permission (z: only READ)
        assert_error {*NOPERM*} {r aclcheck.rm_call set z 5}
        catch {r aclcheck.rm_call_with_errors set z 5} e
        assert_match {*NOPERM*No permissions to access a key*} $e
        assert_error {*NOPERM*} {r aclcheck.rm_call set z 6 get}
        assert_error {*NOPERM*No permissions to access a key*} {r aclcheck.rm_call_with_errors set z 6 get}

        # verify that new log entry added
        set entry [lindex [r ACL LOG] 0]
        assert {[dict get $entry username] eq {default}}
        assert {[dict get $entry context] eq {module}}
        assert {[dict get $entry object] eq {z}}
        assert {[dict get $entry reason] eq {key}}

        # rm call check for command permission
        r acl setuser default -set
        assert_error {*NOPERM*} {r aclcheck.rm_call set x 5}
        assert_error {*NOPERM*has no permissions to run the 'set' command*} {r aclcheck.rm_call_with_errors set x 5}

        # verify that new log entry added
        set entry [lindex [r ACL LOG] 0]
        assert {[dict get $entry username] eq {default}}
        assert {[dict get $entry context] eq {module}}
        assert {[dict get $entry object] eq {set}}
        assert {[dict get $entry reason] eq {command}}
    }
    """
    assert r.run("aclcheck.rm_call", "set", "x", 5) == "OK"
    assert r.run("aclcheck.rm_call", "set", "x", 6, "get") == 5
    assert r.run("aclcheck.rm_call", "set", "y", 5) == "OK"
    with pytest.raises(Exception, match=".*NOPERM.*"):
        r.run("aclcheck.rm_call", "set", "y", 5, "get")
    with pytest.raises(Exception, match=".*NOPERM.*No\\ permissions\\ to\\ access\\ a\\ key.*"):
        r.run("aclcheck.rm_call_with_errors", "set", "y", 5, "get")
    with pytest.raises(Exception, match=".*NOPERM.*"):
        r.run("aclcheck.rm_call", "set", "z", 5)
    try:
        e = r.run("aclcheck.rm_call_with_errors", "set", "z", 5)
    except Exception as _catch_err:
        e = str(_catch_err)
    assert fnmatch(str(e), "*NOPERM*No permissions to access a key*")
    with pytest.raises(Exception, match=".*NOPERM.*"):
        r.run("aclcheck.rm_call", "set", "z", 6, "get")
    with pytest.raises(Exception, match=".*NOPERM.*No\\ permissions\\ to\\ access\\ a\\ key.*"):
        r.run("aclcheck.rm_call_with_errors", "set", "z", 6, "get")
    entry = r.run("ACL", "LOG")[0]
    assert entry["username"] == "default"
    assert entry["context"] == "module"
    assert entry["object"] == "z"
    assert entry["reason"] == "key"
    r.run("acl", "setuser", "default", "-set")
    with pytest.raises(Exception, match=".*NOPERM.*"):
        r.run("aclcheck.rm_call", "set", "x", 5)
    with pytest.raises(Exception, match=".*NOPERM.*has\\ no\\ permissions\\ to\\ run\\ the\\ 'set'\\ command.*"):
        r.run("aclcheck.rm_call_with_errors", "set", "x", 5)
    entry = r.run("ACL", "LOG")[0]
    assert entry["username"] == "default"
    assert entry["context"] == "module"
    assert entry["object"] == "set"
    assert entry["reason"] == "command"


def test_test_module_comprehensive_acl_check(r: ValkeyTestClient) -> None:
    """
    test {test module comprehensive ACL check} {
        r acl setuser testuser on >testpass ~* &* +@all alldbs
        assert_equal [r auth testuser testpass] OK

        # Valid command with valid database
        assert_equal [r aclcheck.check.permissions 0 set x 5] OK
        assert_equal [r get x] 5

        # Denied command
        r acl setuser testuser -set
        catch {r aclcheck.check.permissions 0 set y 10} e
        assert_match {*NOPERM*} $e

        # Check ACL log entry
        set entry [lindex [r ACL LOG] 0]
        assert {[dict get $entry username] eq {testuser}}
        assert {[dict get $entry context] eq {module}}
        assert {[dict get $entry object] eq {set}}
        assert {[dict get $entry reason] eq {command}}
        r ACL LOG RESET

        # Denied key
        r acl setuser testuser +set resetkeys ~allowed_*
        assert_equal [r aclcheck.check.permissions 0 set allowed_key value] OK
        catch {r aclcheck.check.permissions 0 set denied_key value} e
        assert_match {*NOPERM*} $e

        set entry [lindex [r ACL LOG] 0]
        assert {[dict get $entry username] eq {testuser}}
        assert {[dict get $entry context] eq {module}}
        assert {[dict get $entry reason] eq {key}}
        r ACL LOG RESET

        # Denied channel
        r acl setuser testuser resetchannels &ch1
        assert_equal [r aclcheck.check.permissions 0 publish ch1 msg] 0
        catch {r aclcheck.check.permissions 0 publish ch2 msg} e
        assert_match {*NOPERM*} $e

        set entry [lindex [r ACL LOG] 0]
        assert {[dict get $entry username] eq {testuser}}
        assert {[dict get $entry context] eq {module}}
        assert {[dict get $entry reason] eq {channel}}
        r ACL LOG RESET

        # Denied db
        r acl setuser testuser allkeys resetdbs db=0,1,2
        assert_equal [r aclcheck.check.permissions 0 set testkey val] OK
        assert_equal [r aclcheck.check.permissions 1 set testkey val] OK
        catch {r aclcheck.check.permissions 3 set testkey val} e
        assert_match {*NOPERM*} $e

        set entry [lindex [r ACL LOG] 0]
        assert {[dict get $entry username] eq {testuser}}
        assert {[dict get $entry context] eq {module}}
        assert {[dict get $entry reason] eq {database}}
        r ACL LOG RESET

        # Invalid dbid
        catch {r aclcheck.check.permissions -1 set x 5} e
        assert_match {*invalid arguments*} $e

        catch {r aclcheck.check.permissions 999 set x 5} e
        assert_match {*invalid arguments*} $e

        # Invalid command
        catch {r aclcheck.check.permissions 0 nonexistentcmd arg1 arg2} e
        assert_match {*invalid arguments*} $e

        assert_equal [r auth default ""] OK
        r acl deluser testuser
        # Reset default user ACL to ensure clean state for next tests
        r acl setuser default on nopass ~* &* +@all alldbs
    }
    """
    r.run("acl", "setuser", "testuser", "on", ">testpass", "~*", "&*", "+@all", "alldbs")
    assert r.run("auth", "testuser", "testpass") == "OK"
    assert r.run("aclcheck.check.permissions", 0, "set", "x", 5) == "OK"
    assert r.run("get", "x") == 5
    r.run("acl", "setuser", "testuser", "-set")
    try:
        e = r.run("aclcheck.check.permissions", 0, "set", "y", 10)
    except Exception as _catch_err:
        e = str(_catch_err)
    assert fnmatch(str(e), "*NOPERM*")
    entry = r.run("ACL", "LOG")[0]
    assert entry["username"] == "testuser"
    assert entry["context"] == "module"
    assert entry["object"] == "set"
    assert entry["reason"] == "command"
    r.run("ACL", "LOG", "RESET")
    r.run("acl", "setuser", "testuser", "+set", "resetkeys", "~allowed_*")
    assert r.run("aclcheck.check.permissions", 0, "set", "allowed_key", "value") == "OK"
    try:
        e = r.run("aclcheck.check.permissions", 0, "set", "denied_key", "value")
    except Exception as _catch_err:
        e = str(_catch_err)
    assert fnmatch(str(e), "*NOPERM*")
    entry = r.run("ACL", "LOG")[0]
    assert entry["username"] == "testuser"
    assert entry["context"] == "module"
    assert entry["reason"] == "key"
    r.run("ACL", "LOG", "RESET")
    r.run("acl", "setuser", "testuser", "resetchannels", "&ch1")
    assert r.run("aclcheck.check.permissions", 0, "publish", "ch1", "msg") == 0
    try:
        e = r.run("aclcheck.check.permissions", 0, "publish", "ch2", "msg")
    except Exception as _catch_err:
        e = str(_catch_err)
    assert fnmatch(str(e), "*NOPERM*")
    entry = r.run("ACL", "LOG")[0]
    assert entry["username"] == "testuser"
    assert entry["context"] == "module"
    assert entry["reason"] == "channel"
    r.run("ACL", "LOG", "RESET")
    r.run("acl", "setuser", "testuser", "allkeys", "resetdbs", "db=0,1,2")
    assert r.run("aclcheck.check.permissions", 0, "set", "testkey", "val") == "OK"
    assert r.run("aclcheck.check.permissions", 1, "set", "testkey", "val") == "OK"
    try:
        e = r.run("aclcheck.check.permissions", 3, "set", "testkey", "val")
    except Exception as _catch_err:
        e = str(_catch_err)
    assert fnmatch(str(e), "*NOPERM*")
    entry = r.run("ACL", "LOG")[0]
    assert entry["username"] == "testuser"
    assert entry["context"] == "module"
    assert entry["reason"] == "database"
    r.run("ACL", "LOG", "RESET")
    try:
        e = r.run("aclcheck.check.permissions", -1, "set", "x", 5)
    except Exception as _catch_err:
        e = str(_catch_err)
    assert fnmatch(str(e), "*invalid arguments*")
    try:
        e = r.run("aclcheck.check.permissions", 999, "set", "x", 5)
    except Exception as _catch_err:
        e = str(_catch_err)
    assert fnmatch(str(e), "*invalid arguments*")
    try:
        e = r.run("aclcheck.check.permissions", 0, "nonexistentcmd", "arg1", "arg2")
    except Exception as _catch_err:
        e = str(_catch_err)
    assert fnmatch(str(e), "*invalid arguments*")
    assert r.run("auth", "default", "") == "OK"
    r.run("acl", "deluser", "testuser")
    r.run("acl", "setuser", "default", "on", "nopass", "~*", "&*", "+@all", "alldbs")


def test_test_blocking_of_commands_outside_of_onload(r: ValkeyTestClient) -> None:
    """
    test {test blocking of Commands outside of OnLoad} {
        assert_equal [r block.commands.outside.onload] OK
    }
    """
    assert r.run("block.commands.outside.onload") == "OK"


def test_test_users_to_have_access_to_module_commands_having_acl_categories(r: ValkeyTestClient) -> None:
    """
    test {test users to have access to module commands having acl categories} {
        r acl SETUSER j1 on >password -@all +@WRITE
        r acl SETUSER j2 on >password -@all +@READ
        assert_equal [r acl DRYRUN j1 aclcheck.module.command.aclcategories.write] OK
        assert_equal [r acl DRYRUN j2 aclcheck.module.command.aclcategories.write.function.read.category] OK
        assert_equal [r acl DRYRUN j2 aclcheck.module.command.aclcategories.read.only.category] OK
    }
    """
    r.run("acl", "SETUSER", "j1", "on", ">password", "-@all", "+@WRITE")
    r.run("acl", "SETUSER", "j2", "on", ">password", "-@all", "+@READ")
    assert r.run("acl", "DRYRUN", "j1", "aclcheck.module.command.aclcategories.write") == "OK"
    assert r.run("acl", "DRYRUN", "j2", "aclcheck.module.command.aclcategories.write.function.read.category") == "OK"
    assert r.run("acl", "DRYRUN", "j2", "aclcheck.module.command.aclcategories.read.only.category") == "OK"


def test_unload_the_module_aclcheck(r: ValkeyTestClient) -> None:
    """
    test {Unload the module - aclcheck} {
        assert_equal {OK} [r module unload aclcheck]
    }
    """
    assert "OK" == r.run("module", "unload", "aclcheck")


pytestmark = [pytest.mark.modules_check_access_for_keys_with_prefix]


"""
r module load testmodule
"""


def test_test_module_check_acl_check_permissions_for_key_prefix(r: ValkeyTestClient) -> None:
    """
    test {test module check acl check permissions for key prefix} {
        # Create a testuser that can only write to keys starting with "write_" prefix and read
        # from keys starting with "read_"
        assert_equal [r ACL SETUSER testuser on >1234 %W~write_* %R~read_* +@all -@dangerous] OK
        assert_equal [r AUTH testuser 1234] OK
        # No access
        assert_equal [r acl.check_key_prefix wr* W] EACCESS
        # We have write permissions for keys starting with write_*
        assert_equal [r acl.check_key_prefix write_* W] OK
        # write_1 matches the pattern write_* -> OK
        assert_equal [r acl.check_key_prefix write_1 W] OK
        # We can not read from write_* keys
        assert_equal [r acl.check_key_prefix write_1 R] EACCESS
        # But we can read from read_1 keys
        assert_equal [r acl.check_key_prefix read_1 R] OK
        # Missing the _
        assert_equal [r acl.check_key_prefix read* R] EACCESS
        assert_equal [r acl.check_key_prefix read_* R] OK
    }
    """
    assert r.run("ACL", "SETUSER", "testuser", "on", ">1234", "%W~write_*", "%R~read_*", "+@all", "-@dangerous") == "OK"
    assert r.run("AUTH", "testuser", 1234) == "OK"
    assert r.run("acl.check_key_prefix", "wr*", "W") == "EACCESS"
    assert r.run("acl.check_key_prefix", "write_*", "W") == "OK"
    assert r.run("acl.check_key_prefix", "write_1", "W") == "OK"
    assert r.run("acl.check_key_prefix", "write_1", "R") == "EACCESS"
    assert r.run("acl.check_key_prefix", "read_1", "R") == "OK"
    assert r.run("acl.check_key_prefix", "read*", "R") == "EACCESS"
    assert r.run("acl.check_key_prefix", "read_*", "R") == "OK"


pytestmark = [pytest.mark.modules_check_access_for_keys_with_prefix]


"""
r module load testmodule
"""


def test_test_module_check_acl_check_permissions_for_key_prefix_read(r: ValkeyTestClient) -> None:
    """
    test {test module check acl check permissions for key prefix (read=*)} {
        # Create a testuser that can only write to keys starting with "write_" prefix and read
        # from keys starting with "read_"
        assert_equal [r ACL SETUSER testuser on >1234 %W~write_* %R~* +@all -@dangerous] OK
        assert_equal [r AUTH testuser 1234] OK
        # No access
        assert_equal [r acl.check_key_prefix wr* W] EACCESS
        # We have write permissions for keys starting with write_*
        assert_equal [r acl.check_key_prefix write_* W] OK
        # write_1 matches the pattern write_* -> OK
        assert_equal [r acl.check_key_prefix write_1 W] OK
        # We can read from all keys ("*")
        assert_equal [r acl.check_key_prefix read_1 R] OK
        assert_equal [r acl.check_key_prefix read* R] OK
        assert_equal [r acl.check_key_prefix read_* R] OK
        assert_equal [r acl.check_key_prefix write_1 R] OK
    }
    """
    assert r.run("ACL", "SETUSER", "testuser", "on", ">1234", "%W~write_*", "%R~*", "+@all", "-@dangerous") == "OK"
    assert r.run("AUTH", "testuser", 1234) == "OK"
    assert r.run("acl.check_key_prefix", "wr*", "W") == "EACCESS"
    assert r.run("acl.check_key_prefix", "write_*", "W") == "OK"
    assert r.run("acl.check_key_prefix", "write_1", "W") == "OK"
    assert r.run("acl.check_key_prefix", "read_1", "R") == "OK"
    assert r.run("acl.check_key_prefix", "read*", "R") == "OK"
    assert r.run("acl.check_key_prefix", "read_*", "R") == "OK"
    assert r.run("acl.check_key_prefix", "write_1", "R") == "OK"


pytestmark = [pytest.mark.modules_acl]


@pytest.mark.xfail(reason="not implemented")
def test_test_existing_users_to_have_access_to_module_commands_loaded_on_runtime(r: ValkeyTestClient) -> None:
    """
    test {test existing users to have access to module commands loaded on runtime} {
        r acl SETUSER j3 on >password -@all +@WRITE
        assert_equal [r module load $testmodule] OK
        assert_equal [r acl DRYRUN j3 aclcheck.module.command.aclcategories.write] OK
        assert_equal {OK} [r module unload aclcheck]
    }
    """
    r.run("acl", "SETUSER", "j3", "on", ">password", "-@all", "+@WRITE")
    # TODO: assert_equal r module load $testmodule OK
    assert r.run("acl", "DRYRUN", "j3", "aclcheck.module.command.aclcategories.write") == "OK"
    assert "OK" == r.run("module", "unload", "aclcheck")


pytestmark = [pytest.mark.modules_acl]


@pytest.mark.xfail(reason="not implemented")
def test_test_existing_users_without_permissions_do_not_have_access_to_module_commands_loaded_on_runtime(
    r: ValkeyTestClient,
) -> None:
    """
    test {test existing users without permissions, do not have access to module commands loaded on runtime.} {
        r acl SETUSER j4 on >password -@all +@READ
        r acl SETUSER j5 on >password -@all +@WRITE
        assert_equal [r module load $testmodule] OK
        catch {r acl DRYRUN j4 aclcheck.module.command.aclcategories.write} e
        assert_equal {User j4 has no permissions to run the 'aclcheck.module.command.aclcategories.write' command} $e
        catch {r acl DRYRUN j5 aclcheck.module.command.aclcategories.write.function.read.category} e
        assert_equal {User j5 has no permissions to run the 'aclcheck.module.command.aclcategories.write.function.read.category' command} $e
    }
    """
    r.run("acl", "SETUSER", "j4", "on", ">password", "-@all", "+@READ")
    r.run("acl", "SETUSER", "j5", "on", ">password", "-@all", "+@WRITE")
    # TODO: assert_equal r module load $testmodule OK
    try:
        e = r.run("acl", "DRYRUN", "j4", "aclcheck.module.command.aclcategories.write")
    except Exception as _catch_err:
        e = str(_catch_err)
    assert "User j4 has no permissions to run the 'aclcheck.module.command.aclcategories.write' command" == e
    try:
        e = r.run("acl", "DRYRUN", "j5", "aclcheck.module.command.aclcategories.write.function.read.category")
    except Exception as _catch_err:
        e = str(_catch_err)
    assert (
        "User j5 has no permissions to run the 'aclcheck.module.command.aclcategories.write.function.read.category' command"
        == e
    )


def test_test_users_without_permissions_do_not_have_access_to_module_commands(r: ValkeyTestClient) -> None:
    """
    test {test users without permissions, do not have access to module commands.} {
        r acl SETUSER j6 on >password -@all +@READ
        catch {r acl DRYRUN j6 aclcheck.module.command.aclcategories.write} e
        assert_equal {User j6 has no permissions to run the 'aclcheck.module.command.aclcategories.write' command} $e
        r acl SETUSER j7 on >password -@all +@WRITE
        catch {r acl DRYRUN j7 aclcheck.module.command.aclcategories.write.function.read.category} e
        assert_equal {User j7 has no permissions to run the 'aclcheck.module.command.aclcategories.write.function.read.category' command} $e
    }
    """
    r.run("acl", "SETUSER", "j6", "on", ">password", "-@all", "+@READ")
    try:
        e = r.run("acl", "DRYRUN", "j6", "aclcheck.module.command.aclcategories.write")
    except Exception as _catch_err:
        e = str(_catch_err)
    assert "User j6 has no permissions to run the 'aclcheck.module.command.aclcategories.write' command" == e
    r.run("acl", "SETUSER", "j7", "on", ">password", "-@all", "+@WRITE")
    try:
        e = r.run("acl", "DRYRUN", "j7", "aclcheck.module.command.aclcategories.write.function.read.category")
    except Exception as _catch_err:
        e = str(_catch_err)
    assert (
        "User j7 has no permissions to run the 'aclcheck.module.command.aclcategories.write.function.read.category' command"
        == e
    )


def test_test_if_foocategory_acl_categories_is_added(r: ValkeyTestClient) -> None:
    """
    test {test if foocategory acl categories is added} {
        r acl SETUSER j8 on >password -@all +@foocategory
        assert_equal [r acl DRYRUN j8 aclcheck.module.command.test.add.new.aclcategories] OK
    }
    """
    r.run("acl", "SETUSER", "j8", "on", ">password", "-@all", "+@foocategory")
    assert r.run("acl", "DRYRUN", "j8", "aclcheck.module.command.test.add.new.aclcategories") == "OK"


def test_test_if_acl_cat_output_for_the_new_category_is_correct(r: ValkeyTestClient) -> None:
    """
    test {test if ACL CAT output for the new category is correct} {
        assert_equal [r ACL CAT foocategory] aclcheck.module.command.test.add.new.aclcategories
    }
    """
    assert r.run("ACL", "CAT", "foocategory") == "aclcheck.module.command.test.add.new.aclcategories"


def test_test_permission_compaction_and_simplification_for_categories_added_by_a_module(r: ValkeyTestClient) -> None:
    """
    test {test permission compaction and simplification for categories added by a module} {
        r acl SETUSER j9 on >password -@all +@foocategory -@foocategory
        catch {r ACL GETUSER j9} res
        assert_equal {-@all -@foocategory} [lindex $res 5]
        assert_equal {OK} [r module unload aclcheck]
    }
    """
    r.run("acl", "SETUSER", "j9", "on", ">password", "-@all", "+@foocategory", "-@foocategory")
    try:
        res = r.run("ACL", "GETUSER", "j9")
    except Exception as _catch_err:
        res = str(_catch_err)
    assert "-@all -@foocategory" == res[5]
    assert "OK" == r.run("module", "unload", "aclcheck")


pytestmark = [pytest.mark.modules_acl]


@pytest.mark.xfail(reason="not implemented")
def test_test_module_load_fails_if_exceeds_the_maximum_number_of_adding_acl_categories(r: ValkeyTestClient) -> None:
    """
    test {test module load fails if exceeds the maximum number of adding acl categories} {
        assert_error {ERR Error loading the extension. Please check the server logs.} {r module load $testmodule 1}
    }
    """
    # TODO: assert_error {ERR Error loading the extension. Please check the server logs.} {r module load $testmodule 1}
