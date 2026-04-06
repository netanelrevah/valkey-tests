# ruff: noqa: F841, RUF043, ANN002, ANN201

from fnmatch import fnmatch

import pytest

from tests.valkey_test_client import ValkeyTestClient

"""
set testmodule file normalize tests/modules/auth.so
"""


"""
set testmoduletwo file normalize tests/modules/moduleauthtwo.so
"""


"""
set miscmodule file normalize tests/modules/misc.so
"""


"""
proc cmdstat {cmd} {
    return [cmdrstat $cmd r]
}
"""

pytestmark = [pytest.mark.modules]


"""
r module load testmodule
"""


"""
r module load testmoduletwo
"""


"""
set hello2_response r HELLO 2
"""


"""
set hello3_response r HELLO 3
"""


def test_test_registering_module_auth_callbacks(r: ValkeyTestClient) -> None:
    """
    test {test registering module auth callbacks} {
        assert_equal {OK} [r testmoduleone.rm_register_blocking_auth_cb]
        assert_equal {OK} [r testmoduletwo.rm_register_auth_cb]
        assert_equal {OK} [r testmoduleone.rm_register_auth_cb]
    }
    """
    assert "OK" == r.run("testmoduleone.rm_register_blocking_auth_cb")
    assert "OK" == r.run("testmoduletwo.rm_register_auth_cb")
    assert "OK" == r.run("testmoduleone.rm_register_auth_cb")


def test_test_module_auth_for_non_existing_or_disabled_users(r: ValkeyTestClient) -> None:
    """
    test {test module AUTH for non existing / disabled users} {
        r config resetstat
        # Validate that an error is thrown for non existing users.
        assert_error {*WRONGPASS*} {r AUTH foo pwd}
        assert_match {*calls=1,*,rejected_calls=0,failed_calls=1} [cmdstat auth]
        # Validate that an error is thrown for disabled users.
        r acl setuser foo >pwd off ~* &* +@all
        assert_error {*WRONGPASS*} {r AUTH foo pwd}
        assert_match {*calls=2,*,rejected_calls=0,failed_calls=2} [cmdstat auth]
    }
    """
    r.run("config", "resetstat")
    with pytest.raises(Exception, match=".*WRONGPASS.*"):
        r.run("AUTH", "foo", "pwd")
    assert fnmatch(str(cmdstat("auth")), "*calls=1,*,rejected_calls=0,failed_calls=1")
    r.run("acl", "setuser", "foo", ">pwd", "off", "~*", "&*", "+@all")
    with pytest.raises(Exception, match=".*WRONGPASS.*"):
        r.run("AUTH", "foo", "pwd")
    assert fnmatch(str(cmdstat("auth")), "*calls=2,*,rejected_calls=0,failed_calls=2")


def test_test_non_blocking_module_auth(r: ValkeyTestClient) -> None:
    """
    test {test non blocking module AUTH} {
        r config resetstat
        # Test for a fixed password user
        r acl setuser foo >pwd on ~* &* +@all
        assert_equal {OK} [r AUTH foo allow]
        assert_error {*Auth denied by Misc Module*} {r AUTH foo deny}
        assert_match {*calls=2,*,rejected_calls=0,failed_calls=1} [cmdstat auth]
        assert_error {*WRONGPASS*} {r AUTH foo nomatch}
        assert_match {*calls=3,*,rejected_calls=0,failed_calls=2} [cmdstat auth]
        assert_equal {OK} [r AUTH foo pwd]
        # Test for No Pass user
        r acl setuser foo on ~* &* +@all nopass
        assert_equal {OK} [r AUTH foo allow]
        assert_error {*Auth denied by Misc Module*} {r AUTH foo deny}
        assert_match {*calls=6,*,rejected_calls=0,failed_calls=3} [cmdstat auth]
        assert_equal {OK} [r AUTH foo nomatch]

        # Validate that the Module added an ACL Log entry.
        set entry [lindex [r ACL LOG] 0]
        assert {[dict get $entry username] eq {foo}}
        assert {[dict get $entry context] eq {module}}
        assert {[dict get $entry reason] eq {auth}}
        assert {[dict get $entry object] eq {Module Auth}}
        assert_match {*cmd=auth*} [dict get $entry client-info]
        r ACL LOG RESET
    }
    """
    r.run("config", "resetstat")
    r.run("acl", "setuser", "foo", ">pwd", "on", "~*", "&*", "+@all")
    assert "OK" == r.run("AUTH", "foo", "allow")
    with pytest.raises(Exception, match=".*Auth\\ denied\\ by\\ Misc\\ Module.*"):
        r.run("AUTH", "foo", "deny")
    assert fnmatch(str(cmdstat("auth")), "*calls=2,*,rejected_calls=0,failed_calls=1")
    with pytest.raises(Exception, match=".*WRONGPASS.*"):
        r.run("AUTH", "foo", "nomatch")
    assert fnmatch(str(cmdstat("auth")), "*calls=3,*,rejected_calls=0,failed_calls=2")
    assert "OK" == r.run("AUTH", "foo", "pwd")
    r.run("acl", "setuser", "foo", "on", "~*", "&*", "+@all", "nopass")
    assert "OK" == r.run("AUTH", "foo", "allow")
    with pytest.raises(Exception, match=".*Auth\\ denied\\ by\\ Misc\\ Module.*"):
        r.run("AUTH", "foo", "deny")
    assert fnmatch(str(cmdstat("auth")), "*calls=6,*,rejected_calls=0,failed_calls=3")
    assert "OK" == r.run("AUTH", "foo", "nomatch")
    entry = r.run("ACL", "LOG")[0]
    assert entry["username"] == "foo"
    assert entry["context"] == "module"
    assert entry["reason"] == "auth"
    assert entry["object"] == "Module Auth"
    assert fnmatch(str(entry["client-info"]), "*cmd=auth*")
    r.run("ACL", "LOG", "RESET")


@pytest.mark.xfail(reason="not implemented")
def test_test_non_blocking_module_hello_auth(r: ValkeyTestClient) -> None:
    """
    test {test non blocking module HELLO AUTH} {
        r config resetstat
        r acl setuser foo >pwd on ~* &* +@all
        # Validate proto 2 and 3 in case of success
        assert_equal $hello2_response [r HELLO 2 AUTH foo pwd]
        assert_equal $hello2_response [r HELLO 2 AUTH foo allow]
        assert_equal $hello3_response [r HELLO 3 AUTH foo pwd]
        assert_equal $hello3_response [r HELLO 3 AUTH foo allow]
        # Validate denying AUTH for the HELLO cmd
        assert_error {*Auth denied by Misc Module*} {r HELLO 2 AUTH foo deny}
        assert_match {*calls=5,*,rejected_calls=0,failed_calls=1} [cmdstat hello]
        assert_error {*WRONGPASS*} {r HELLO 2 AUTH foo nomatch}
        assert_match {*calls=6,*,rejected_calls=0,failed_calls=2} [cmdstat hello]
        assert_error {*Auth denied by Misc Module*} {r HELLO 3 AUTH foo deny}
        assert_match {*calls=7,*,rejected_calls=0,failed_calls=3} [cmdstat hello]
        assert_error {*WRONGPASS*} {r HELLO 3 AUTH foo nomatch}
        assert_match {*calls=8,*,rejected_calls=0,failed_calls=4} [cmdstat hello]

        # Validate that the Module added an ACL Log entry.
        set entry [lindex [r ACL LOG] 1]
        assert {[dict get $entry username] eq {foo}}
        assert {[dict get $entry context] eq {module}}
        assert {[dict get $entry reason] eq {auth}}
        assert {[dict get $entry object] eq {Module Auth}}
        assert_match {*cmd=hello*} [dict get $entry client-info]
        r ACL LOG RESET
    }
    """
    r.run("config", "resetstat")
    r.run("acl", "setuser", "foo", ">pwd", "on", "~*", "&*", "+@all")
    # TODO: assert_equal hello2_response r HELLO 2 AUTH foo pwd
    # TODO: assert_equal hello2_response r HELLO 2 AUTH foo allow
    # TODO: assert_equal hello3_response r HELLO 3 AUTH foo pwd
    # TODO: assert_equal hello3_response r HELLO 3 AUTH foo allow
    with pytest.raises(Exception, match=".*Auth\\ denied\\ by\\ Misc\\ Module.*"):
        r.run("HELLO", 2, "AUTH", "foo", "deny")
    assert fnmatch(str(cmdstat("hello")), "*calls=5,*,rejected_calls=0,failed_calls=1")
    with pytest.raises(Exception, match=".*WRONGPASS.*"):
        r.run("HELLO", 2, "AUTH", "foo", "nomatch")
    assert fnmatch(str(cmdstat("hello")), "*calls=6,*,rejected_calls=0,failed_calls=2")
    with pytest.raises(Exception, match=".*Auth\\ denied\\ by\\ Misc\\ Module.*"):
        r.run("HELLO", 3, "AUTH", "foo", "deny")
    assert fnmatch(str(cmdstat("hello")), "*calls=7,*,rejected_calls=0,failed_calls=3")
    with pytest.raises(Exception, match=".*WRONGPASS.*"):
        r.run("HELLO", 3, "AUTH", "foo", "nomatch")
    assert fnmatch(str(cmdstat("hello")), "*calls=8,*,rejected_calls=0,failed_calls=4")
    entry = r.run("ACL", "LOG")[1]
    assert entry["username"] == "foo"
    assert entry["context"] == "module"
    assert entry["reason"] == "auth"
    assert entry["object"] == "Module Auth"
    assert fnmatch(str(entry["client-info"]), "*cmd=hello*")
    r.run("ACL", "LOG", "RESET")


@pytest.mark.xfail(reason="not implemented")
def test_test_non_blocking_module_hello_auth_setname(r: ValkeyTestClient) -> None:
    """
    test {test non blocking module HELLO AUTH SETNAME} {
        r config resetstat
        r acl setuser foo >pwd on ~* &* +@all
        # Validate clientname is set on success
        assert_equal $hello2_response [r HELLO 2 AUTH foo pwd setname client1]
        assert {[r client getname] eq {client1}}
        assert_equal $hello2_response [r HELLO 2 AUTH foo allow setname client2]
        assert {[r client getname] eq {client2}}
        # Validate clientname is not updated on failure
        r client setname client0
        assert_error {*Auth denied by Misc Module*} {r HELLO 2 AUTH foo deny setname client1}
        assert {[r client getname] eq {client0}}
        assert_match {*calls=3,*,rejected_calls=0,failed_calls=1} [cmdstat hello]
        assert_error {*WRONGPASS*} {r HELLO 2 AUTH foo nomatch setname client2}
        assert {[r client getname] eq {client0}}
        assert_match {*calls=4,*,rejected_calls=0,failed_calls=2} [cmdstat hello]
    }
    """
    r.run("config", "resetstat")
    r.run("acl", "setuser", "foo", ">pwd", "on", "~*", "&*", "+@all")
    # TODO: assert_equal hello2_response r HELLO 2 AUTH foo pwd setname client1
    assert r.run("client", "getname") == "client1"
    # TODO: assert_equal hello2_response r HELLO 2 AUTH foo allow setname client2
    assert r.run("client", "getname") == "client2"
    r.run("client", "setname", "client0")
    with pytest.raises(Exception, match=".*Auth\\ denied\\ by\\ Misc\\ Module.*"):
        r.run("HELLO", 2, "AUTH", "foo", "deny", "setname", "client1")
    assert r.run("client", "getname") == "client0"
    assert fnmatch(str(cmdstat("hello")), "*calls=3,*,rejected_calls=0,failed_calls=1")
    with pytest.raises(Exception, match=".*WRONGPASS.*"):
        r.run("HELLO", 2, "AUTH", "foo", "nomatch", "setname", "client2")
    assert r.run("client", "getname") == "client0"
    assert fnmatch(str(cmdstat("hello")), "*calls=4,*,rejected_calls=0,failed_calls=2")


@pytest.mark.xfail(reason="not implemented")
def test_test_blocking_module_auth(r: ValkeyTestClient) -> None:
    """
    test {test blocking module AUTH} {
        r config resetstat
        # Test for a fixed password user
        r acl setuser foo >pwd on ~* &* +@all
        assert_equal {OK} [r AUTH foo block_allow]
        assert_error {*Auth denied by Misc Module*} {r AUTH foo block_deny}
        assert_match {*calls=2,*,rejected_calls=0,failed_calls=1} [cmdstat auth]
        assert_error {*WRONGPASS*} {r AUTH foo nomatch}
        assert_match {*calls=3,*,rejected_calls=0,failed_calls=2} [cmdstat auth]
        assert_equal {OK} [r AUTH foo pwd]
        # Test for No Pass user
        r acl setuser foo on ~* &* +@all nopass
        assert_equal {OK} [r AUTH foo block_allow]
        assert_error {*Auth denied by Misc Module*} {r AUTH foo block_deny}
        assert_match {*calls=6,*,rejected_calls=0,failed_calls=3} [cmdstat auth]
        assert_equal {OK} [r AUTH foo nomatch]
        # Validate that every Blocking AUTH command took at least 500000 usec.
        set stats [cmdstat auth]
        regexp "usec_per_call=(\[0-9]{1,})\.*," $stats all usec_per_call
        assert {$usec_per_call >= 500000}

        # Validate that the Module added an ACL Log entry.
        set entry [lindex [r ACL LOG] 0]
        assert {[dict get $entry username] eq {foo}}
        assert {[dict get $entry context] eq {module}}
        assert {[dict get $entry reason] eq {auth}}
        assert {[dict get $entry object] eq {Module Auth}}
        assert_match {*cmd=auth*} [dict get $entry client-info]
        r ACL LOG RESET
    }
    """
    r.run("config", "resetstat")
    r.run("acl", "setuser", "foo", ">pwd", "on", "~*", "&*", "+@all")
    assert "OK" == r.run("AUTH", "foo", "block_allow")
    with pytest.raises(Exception, match=".*Auth\\ denied\\ by\\ Misc\\ Module.*"):
        r.run("AUTH", "foo", "block_deny")
    assert fnmatch(str(cmdstat("auth")), "*calls=2,*,rejected_calls=0,failed_calls=1")
    with pytest.raises(Exception, match=".*WRONGPASS.*"):
        r.run("AUTH", "foo", "nomatch")
    assert fnmatch(str(cmdstat("auth")), "*calls=3,*,rejected_calls=0,failed_calls=2")
    assert "OK" == r.run("AUTH", "foo", "pwd")
    r.run("acl", "setuser", "foo", "on", "~*", "&*", "+@all", "nopass")
    assert "OK" == r.run("AUTH", "foo", "block_allow")
    with pytest.raises(Exception, match=".*Auth\\ denied\\ by\\ Misc\\ Module.*"):
        r.run("AUTH", "foo", "block_deny")
    assert fnmatch(str(cmdstat("auth")), "*calls=6,*,rejected_calls=0,failed_calls=3")
    assert "OK" == r.run("AUTH", "foo", "nomatch")
    stats = cmdstat("auth")
    # TODO: regexp "usec_per_call=(\[0-9]{1,})\.*," stats all usec_per_call
    assert_("$usec_per_call >= 500000")
    entry = r.run("ACL", "LOG")[0]
    assert entry["username"] == "foo"
    assert entry["context"] == "module"
    assert entry["reason"] == "auth"
    assert entry["object"] == "Module Auth"
    assert fnmatch(str(entry["client-info"]), "*cmd=auth*")
    r.run("ACL", "LOG", "RESET")


@pytest.mark.xfail(reason="not implemented")
def test_test_blocking_module_hello_auth(r: ValkeyTestClient) -> None:
    """
    test {test blocking module HELLO AUTH} {
        r config resetstat
        r acl setuser foo >pwd on ~* &* +@all
        # validate proto 2 and 3 in case of success
        assert_equal $hello2_response [r HELLO 2 AUTH foo pwd]
        assert_equal $hello2_response [r HELLO 2 AUTH foo block_allow]
        assert_equal $hello3_response [r HELLO 3 AUTH foo pwd]
        assert_equal $hello3_response [r HELLO 3 AUTH foo block_allow]
        # validate denying AUTH for the HELLO cmd
        assert_error {*Auth denied by Misc Module*} {r HELLO 2 AUTH foo block_deny}
        assert_match {*calls=5,*,rejected_calls=0,failed_calls=1} [cmdstat hello]
        assert_error {*WRONGPASS*} {r HELLO 2 AUTH foo nomatch}
        assert_match {*calls=6,*,rejected_calls=0,failed_calls=2} [cmdstat hello]
        assert_error {*Auth denied by Misc Module*} {r HELLO 3 AUTH foo block_deny}
        assert_match {*calls=7,*,rejected_calls=0,failed_calls=3} [cmdstat hello]
        assert_error {*WRONGPASS*} {r HELLO 3 AUTH foo nomatch}
        assert_match {*calls=8,*,rejected_calls=0,failed_calls=4} [cmdstat hello]
        # Validate that every HELLO AUTH command took at least 500000 usec.
        set stats [cmdstat hello]
        regexp "usec_per_call=(\[0-9]{1,})\.*," $stats all usec_per_call
        assert {$usec_per_call >= 500000}

        # Validate that the Module added an ACL Log entry.
        set entry [lindex [r ACL LOG] 1]
        assert {[dict get $entry username] eq {foo}}
        assert {[dict get $entry context] eq {module}}
        assert {[dict get $entry reason] eq {auth}}
        assert {[dict get $entry object] eq {Module Auth}}
        assert_match {*cmd=hello*} [dict get $entry client-info]
        r ACL LOG RESET
    }
    """
    r.run("config", "resetstat")
    r.run("acl", "setuser", "foo", ">pwd", "on", "~*", "&*", "+@all")
    # TODO: assert_equal hello2_response r HELLO 2 AUTH foo pwd
    # TODO: assert_equal hello2_response r HELLO 2 AUTH foo block_allow
    # TODO: assert_equal hello3_response r HELLO 3 AUTH foo pwd
    # TODO: assert_equal hello3_response r HELLO 3 AUTH foo block_allow
    with pytest.raises(Exception, match=".*Auth\\ denied\\ by\\ Misc\\ Module.*"):
        r.run("HELLO", 2, "AUTH", "foo", "block_deny")
    assert fnmatch(str(cmdstat("hello")), "*calls=5,*,rejected_calls=0,failed_calls=1")
    with pytest.raises(Exception, match=".*WRONGPASS.*"):
        r.run("HELLO", 2, "AUTH", "foo", "nomatch")
    assert fnmatch(str(cmdstat("hello")), "*calls=6,*,rejected_calls=0,failed_calls=2")
    with pytest.raises(Exception, match=".*Auth\\ denied\\ by\\ Misc\\ Module.*"):
        r.run("HELLO", 3, "AUTH", "foo", "block_deny")
    assert fnmatch(str(cmdstat("hello")), "*calls=7,*,rejected_calls=0,failed_calls=3")
    with pytest.raises(Exception, match=".*WRONGPASS.*"):
        r.run("HELLO", 3, "AUTH", "foo", "nomatch")
    assert fnmatch(str(cmdstat("hello")), "*calls=8,*,rejected_calls=0,failed_calls=4")
    stats = cmdstat("hello")
    # TODO: regexp "usec_per_call=(\[0-9]{1,})\.*," stats all usec_per_call
    assert_("$usec_per_call >= 500000")
    entry = r.run("ACL", "LOG")[1]
    assert entry["username"] == "foo"
    assert entry["context"] == "module"
    assert entry["reason"] == "auth"
    assert entry["object"] == "Module Auth"
    assert fnmatch(str(entry["client-info"]), "*cmd=hello*")
    r.run("ACL", "LOG", "RESET")


@pytest.mark.xfail(reason="not implemented")
def test_test_blocking_module_hello_auth_setname(r: ValkeyTestClient) -> None:
    """
    test {test blocking module HELLO AUTH SETNAME} {
        r config resetstat
        r acl setuser foo >pwd on ~* &* +@all
        # Validate clientname is set on success
        assert_equal $hello2_response [r HELLO 2 AUTH foo pwd setname client1]
        assert {[r client getname] eq {client1}}
        assert_equal $hello2_response [r HELLO 2 AUTH foo block_allow setname client2]
        assert {[r client getname] eq {client2}}
        # Validate clientname is not updated on failure
        r client setname client0
        assert_error {*Auth denied by Misc Module*} {r HELLO 2 AUTH foo block_deny setname client1}
        assert {[r client getname] eq {client0}}
        assert_match {*calls=3,*,rejected_calls=0,failed_calls=1} [cmdstat hello]
        assert_error {*WRONGPASS*} {r HELLO 2 AUTH foo nomatch setname client2}
        assert {[r client getname] eq {client0}}
        assert_match {*calls=4,*,rejected_calls=0,failed_calls=2} [cmdstat hello]
        # Validate that every HELLO AUTH SETNAME command took at least 500000 usec.
        set stats [cmdstat hello]
        regexp "usec_per_call=(\[0-9]{1,})\.*," $stats all usec_per_call
        assert {$usec_per_call >= 500000}
    }
    """
    r.run("config", "resetstat")
    r.run("acl", "setuser", "foo", ">pwd", "on", "~*", "&*", "+@all")
    # TODO: assert_equal hello2_response r HELLO 2 AUTH foo pwd setname client1
    assert r.run("client", "getname") == "client1"
    # TODO: assert_equal hello2_response r HELLO 2 AUTH foo block_allow setname client2
    assert r.run("client", "getname") == "client2"
    r.run("client", "setname", "client0")
    with pytest.raises(Exception, match=".*Auth\\ denied\\ by\\ Misc\\ Module.*"):
        r.run("HELLO", 2, "AUTH", "foo", "block_deny", "setname", "client1")
    assert r.run("client", "getname") == "client0"
    assert fnmatch(str(cmdstat("hello")), "*calls=3,*,rejected_calls=0,failed_calls=1")
    with pytest.raises(Exception, match=".*WRONGPASS.*"):
        r.run("HELLO", 2, "AUTH", "foo", "nomatch", "setname", "client2")
    assert r.run("client", "getname") == "client0"
    assert fnmatch(str(cmdstat("hello")), "*calls=4,*,rejected_calls=0,failed_calls=2")
    stats = cmdstat("hello")
    # TODO: regexp "usec_per_call=(\[0-9]{1,})\.*," stats all usec_per_call
    assert_("$usec_per_call >= 500000")


@pytest.mark.xfail(reason="not implemented")
def test_test_auth_after_registering_multiple_module_auth_callbacks(r: ValkeyTestClient) -> None:
    """
    test {test AUTH after registering multiple module auth callbacks} {
        r config resetstat

        # Register two more callbacks from the same module.
        assert_equal {OK} [r testmoduleone.rm_register_blocking_auth_cb]
        assert_equal {OK} [r testmoduleone.rm_register_auth_cb]

        # Register another module auth callback from the second module.
        assert_equal {OK} [r testmoduletwo.rm_register_auth_cb]

        r acl setuser foo >pwd on ~* &* +@all

        # Case 1 - Non Blocking Success
        assert_equal {OK} [r AUTH foo allow]

        # Case 2 - Non Blocking Deny
        assert_error {*Auth denied by Misc Module*} {r AUTH foo deny}
        assert_match {*calls=2,*,rejected_calls=0,failed_calls=1} [cmdstat auth]

        r config resetstat

        # Case 3 - Blocking Success
        assert_equal {OK} [r AUTH foo block_allow]

        # Case 4 - Blocking Deny
        assert_error {*Auth denied by Misc Module*} {r AUTH foo block_deny}
        assert_match {*calls=2,*,rejected_calls=0,failed_calls=1} [cmdstat auth]

        # Validate that every Blocking AUTH command took at least 500000 usec.
        set stats [cmdstat auth]
        regexp "usec_per_call=(\[0-9]{1,})\.*," $stats all usec_per_call
        assert {$usec_per_call >= 500000}

        r config resetstat

        # Case 5 - Non Blocking Success via the second module.
        assert_equal {OK} [r AUTH foo allow_two]

        # Case 6 - Non Blocking Deny via the second module.
        assert_error {*Auth denied by Misc Module*} {r AUTH foo deny_two}
        assert_match {*calls=2,*,rejected_calls=0,failed_calls=1} [cmdstat auth]

        r config resetstat

        # Case 7 - All four auth callbacks "Skip" by not explicitly allowing or denying.
        assert_error {*WRONGPASS*} {r AUTH foo nomatch}
        assert_match {*calls=1,*,rejected_calls=0,failed_calls=1} [cmdstat auth]
        assert_equal {OK} [r AUTH foo pwd]

        # Because we had to attempt all 4 callbacks, validate that the AUTH command took at least
        # 1000000 usec (each blocking callback takes 500000 usec).
        set stats [cmdstat auth]
        regexp "usec_per_call=(\[0-9]{1,})\.*," $stats all usec_per_call
        assert {$usec_per_call >= 1000000}
    }
    """
    r.run("config", "resetstat")
    assert "OK" == r.run("testmoduleone.rm_register_blocking_auth_cb")
    assert "OK" == r.run("testmoduleone.rm_register_auth_cb")
    assert "OK" == r.run("testmoduletwo.rm_register_auth_cb")
    r.run("acl", "setuser", "foo", ">pwd", "on", "~*", "&*", "+@all")
    assert "OK" == r.run("AUTH", "foo", "allow")
    with pytest.raises(Exception, match=".*Auth\\ denied\\ by\\ Misc\\ Module.*"):
        r.run("AUTH", "foo", "deny")
    assert fnmatch(str(cmdstat("auth")), "*calls=2,*,rejected_calls=0,failed_calls=1")
    r.run("config", "resetstat")
    assert "OK" == r.run("AUTH", "foo", "block_allow")
    with pytest.raises(Exception, match=".*Auth\\ denied\\ by\\ Misc\\ Module.*"):
        r.run("AUTH", "foo", "block_deny")
    assert fnmatch(str(cmdstat("auth")), "*calls=2,*,rejected_calls=0,failed_calls=1")
    stats = cmdstat("auth")
    # TODO: regexp "usec_per_call=(\[0-9]{1,})\.*," stats all usec_per_call
    assert_("$usec_per_call >= 500000")
    r.run("config", "resetstat")
    assert "OK" == r.run("AUTH", "foo", "allow_two")
    with pytest.raises(Exception, match=".*Auth\\ denied\\ by\\ Misc\\ Module.*"):
        r.run("AUTH", "foo", "deny_two")
    assert fnmatch(str(cmdstat("auth")), "*calls=2,*,rejected_calls=0,failed_calls=1")
    r.run("config", "resetstat")
    with pytest.raises(Exception, match=".*WRONGPASS.*"):
        r.run("AUTH", "foo", "nomatch")
    assert fnmatch(str(cmdstat("auth")), "*calls=1,*,rejected_calls=0,failed_calls=1")
    assert "OK" == r.run("AUTH", "foo", "pwd")
    stats = cmdstat("auth")
    # TODO: regexp "usec_per_call=(\[0-9]{1,})\.*," stats all usec_per_call
    assert_("$usec_per_call >= 1000000")


@pytest.mark.xfail(reason="not implemented")
def test_module_auth_during_blocking_module_auth(r: ValkeyTestClient) -> None:
    """
    test {module auth during blocking module auth} {
        r config resetstat
        r acl setuser foo >pwd on ~* &* +@all
        set rd [valkey_deferring_client]
        set rd_two [valkey_deferring_client]

        # Attempt blocking module auth. While this ongoing, attempt non blocking module auth from
        # moduleone/moduletwo and start another blocking module auth from another deferring client.
        $rd AUTH foo block_allow
        wait_for_blocked_clients_count 1
        assert_equal {OK} [r AUTH foo allow]
        assert_equal {OK} [r AUTH foo allow_two]
        # Validate that the non blocking module auth cmds finished before any blocking module auth.
        set info_clients [r info clients]
        assert_match "*blocked_clients:1*" $info_clients
        $rd_two AUTH foo block_allow

        # Validate that all of the AUTH commands succeeded.
        wait_for_blocked_clients_count 0 500 10
        $rd flush
        assert_equal [$rd read] "OK"
        $rd_two flush
        assert_equal [$rd_two read] "OK"
        assert_match {*calls=4,*,rejected_calls=0,failed_calls=0} [cmdstat auth]
    }
    """
    r.run("config", "resetstat")
    r.run("acl", "setuser", "foo", ">pwd", "on", "~*", "&*", "+@all")
    rd = valkey_deferring_client()
    rd_two = valkey_deferring_client()
    # TODO: $rd AUTH foo block_allow
    wait_for_blocked_clients_count(1)
    assert "OK" == r.run("AUTH", "foo", "allow")
    assert "OK" == r.run("AUTH", "foo", "allow_two")
    info_clients = r.run("info", "clients")
    assert fnmatch(str(info_clients), "*blocked_clients:1*")
    # TODO: $rd_two AUTH foo block_allow
    wait_for_blocked_clients_count(0, 500, 10)
    # TODO: $rd flush
    # TODO: assert_equal $rd read "OK"
    # TODO: $rd_two flush
    # TODO: assert_equal $rd_two read "OK"
    assert fnmatch(str(cmdstat("auth")), "*calls=4,*,rejected_calls=0,failed_calls=0")


def test_module_auth_inside_multi_exec(r: ValkeyTestClient) -> None:
    """
    test {module auth inside MULTI EXEC} {
        r config resetstat
        r acl setuser foo >pwd on ~* &* +@all

        # Validate that non blocking module auth inside MULTI succeeds.
        r multi
        r AUTH foo allow
        assert_equal {OK} [r exec]

        # Validate that blocking module auth inside MULTI throws an err.
        r multi
        r AUTH foo block_allow
        assert_error {*ERR Blocking module command called from transaction*} {r exec}
        assert_match {*calls=2,*,rejected_calls=0,failed_calls=1} [cmdstat auth]
    }
    """
    r.run("config", "resetstat")
    r.run("acl", "setuser", "foo", ">pwd", "on", "~*", "&*", "+@all")
    r.run("multi")
    r.run("AUTH", "foo", "allow")
    assert "OK" == r.run("exec")
    r.run("multi")
    r.run("AUTH", "foo", "block_allow")
    with pytest.raises(Exception, match=".*ERR\\ Blocking\\ module\\ command\\ called\\ from\\ transaction.*"):
        r.run("exec")
    assert fnmatch(str(cmdstat("auth")), "*calls=2,*,rejected_calls=0,failed_calls=1")


@pytest.mark.xfail(reason="not implemented")
def test_disabling_valkey_user_during_blocking_module_auth(r: ValkeyTestClient) -> None:
    """
    test {Disabling Valkey User during blocking module auth} {
        r config resetstat
        r acl setuser foo >pwd on ~* &* +@all
        set rd [valkey_deferring_client]

        # Attempt blocking module auth and disable the user while module auth is in progress.
        $rd AUTH foo pwd
        wait_for_blocked_clients_count 1
        r acl setuser foo >pwd off ~* &* +@all

        # Validate that module auth failed.
        wait_for_blocked_clients_count 0 500 10
        $rd flush
        assert_error {*WRONGPASS*} { $rd read }
        assert_match {*calls=1,*,rejected_calls=0,failed_calls=1} [cmdstat auth]
    }
    """
    r.run("config", "resetstat")
    r.run("acl", "setuser", "foo", ">pwd", "on", "~*", "&*", "+@all")
    rd = valkey_deferring_client()
    # TODO: $rd AUTH foo pwd
    wait_for_blocked_clients_count(1)
    r.run("acl", "setuser", "foo", ">pwd", "off", "~*", "&*", "+@all")
    wait_for_blocked_clients_count(0, 500, 10)
    # TODO: $rd flush
    assert_error("*WRONGPASS*", " $rd read ")
    assert fnmatch(str(cmdstat("auth")), "*calls=1,*,rejected_calls=0,failed_calls=1")


@pytest.mark.xfail(reason="not implemented")
def test_killing_a_client_in_the_middle_of_blocking_module_auth(r: ValkeyTestClient) -> None:
    """
    test {Killing a client in the middle of blocking module auth} {
        r config resetstat
        r acl setuser foo >pwd on ~* &* +@all
        set rd [valkey_deferring_client]
        $rd client id
        set cid [$rd read]

        # Attempt blocking module auth command on client `cid` and kill the client while module auth
        # is in progress.
        $rd AUTH foo pwd
        wait_for_blocked_clients_count 1
        r client kill id $cid

        # Validate that the blocked client count goes to 0 and no AUTH command is tracked.
        wait_for_blocked_clients_count 0 500 10
        $rd flush
        assert_error {*I/O error reading reply*} { $rd read }
        assert_match {} [cmdstat auth]
    }
    """
    r.run("config", "resetstat")
    r.run("acl", "setuser", "foo", ">pwd", "on", "~*", "&*", "+@all")
    rd = valkey_deferring_client()
    # TODO: $rd client id
    # TODO: set cid $rd read
    # TODO: $rd AUTH foo pwd
    wait_for_blocked_clients_count(1)
    # TODO: r client kill id cid
    wait_for_blocked_clients_count(0, 500, 10)
    # TODO: $rd flush
    assert_error("*I/O error reading reply*", " $rd read ")
    assert fnmatch(str(cmdstat("auth")), "")


def test_test_rm_abortblock_module_api_during_blocking_module_auth(r: ValkeyTestClient) -> None:
    """
    test {test RM_AbortBlock Module API during blocking module auth} {
        r config resetstat
        r acl setuser foo >pwd on ~* &* +@all

        # Attempt module auth. With the "block_abort" as the password, the "testacl.so" module
        # blocks the client and uses the RM_AbortBlock API. This should result in module auth
        # failing and the client being unblocked with the default AUTH err message.
        assert_error {*WRONGPASS*} {r AUTH foo block_abort}
        assert_match {*calls=1,*,rejected_calls=0,failed_calls=1} [cmdstat auth]
    }
    """
    r.run("config", "resetstat")
    r.run("acl", "setuser", "foo", ">pwd", "on", "~*", "&*", "+@all")
    with pytest.raises(Exception, match=".*WRONGPASS.*"):
        r.run("AUTH", "foo", "block_abort")
    assert fnmatch(str(cmdstat("auth")), "*calls=1,*,rejected_calls=0,failed_calls=1")


@pytest.mark.xfail(reason="not implemented")
def test_test_rm_registerauthcallback_module_api_during_blocking_module_auth(r: ValkeyTestClient) -> None:
    """
    test {test RM_RegisterAuthCallback Module API during blocking module auth} {
        r config resetstat
        r acl setuser foo >defaultpwd on ~* &* +@all
        set rd [valkey_deferring_client]

        # Start the module auth attempt with the standard auth password for the user. This
        # will result in all module auth cbs attempted and then standard auth will be tried.
        $rd AUTH foo defaultpwd
        wait_for_blocked_clients_count 1

        # Validate that we allow modules to register module auth cbs while module auth is already
        # in progress.
        assert_equal {OK} [r testmoduleone.rm_register_blocking_auth_cb]
        assert_equal {OK} [r testmoduletwo.rm_register_auth_cb]

        # Validate that blocking module auth succeeds.
        wait_for_blocked_clients_count 0 500 10
        $rd flush
        assert_equal [$rd read] "OK"
        set stats [cmdstat auth]
        assert_match {*calls=1,*,rejected_calls=0,failed_calls=0} $stats

        # Validate that even the new blocking module auth cb which was registered in the middle of
        # blocking module auth is attempted - making it take twice the duration (2x 500000 us).
        regexp "usec_per_call=(\[0-9]{1,})\.*," $stats all usec_per_call
        assert {$usec_per_call >= 1000000}
    }
    """
    r.run("config", "resetstat")
    r.run("acl", "setuser", "foo", ">defaultpwd", "on", "~*", "&*", "+@all")
    rd = valkey_deferring_client()
    # TODO: $rd AUTH foo defaultpwd
    wait_for_blocked_clients_count(1)
    assert "OK" == r.run("testmoduleone.rm_register_blocking_auth_cb")
    assert "OK" == r.run("testmoduletwo.rm_register_auth_cb")
    wait_for_blocked_clients_count(0, 500, 10)
    # TODO: $rd flush
    # TODO: assert_equal $rd read "OK"
    stats = cmdstat("auth")
    assert fnmatch(str(stats), "*calls=1,*,rejected_calls=0,failed_calls=0")
    # TODO: regexp "usec_per_call=(\[0-9]{1,})\.*," stats all usec_per_call
    assert_("$usec_per_call >= 1000000")


@pytest.mark.xfail(reason="not implemented")
def test_module_unload_during_blocking_module_auth(r: ValkeyTestClient) -> None:
    """
    test {Module unload during blocking module auth} {
        r config resetstat
        r module load $miscmodule
        set rd [valkey_deferring_client]
        r acl setuser foo >pwd on ~* &* +@all

        # Start a blocking module auth attempt.
        $rd AUTH foo block_allow
        wait_for_blocked_clients_count 1

        # moduleone and moduletwo have module auth cbs registered. Because blocking module auth is
        # ongoing, they cannot be unloaded.
        catch {r module unload testacl} e
        assert_match {*the module has blocked clients*} $e
        # The moduleauthtwo module can be unregistered because no client is blocked on it.
        assert_equal "OK" [r module unload moduleauthtwo]

        # The misc module does not have module auth cbs registered, so it can be unloaded even when
        # blocking module auth is ongoing.
        assert_equal "OK" [r module unload misc]

        # Validate that blocking module auth succeeds.
        wait_for_blocked_clients_count 0 500 10
        $rd flush
        assert_equal [$rd read] "OK"
        assert_match {*calls=1,*,rejected_calls=0,failed_calls=0} [cmdstat auth]

        # Validate that unloading the moduleauthtwo module does not unregister module auth cbs of
        # of the testacl module. Module based auth should succeed.
        assert_equal {OK} [r AUTH foo allow]

        # Validate that the testacl module can be unloaded since blocking module auth is done.
        r module unload testacl

        # Validate that since all module auth cbs are unregistered, module auth attempts fail.
        assert_error {*WRONGPASS*} {r AUTH foo block_allow}
        assert_error {*WRONGPASS*} {r AUTH foo allow_two}
        assert_error {*WRONGPASS*} {r AUTH foo allow}
        assert_match {*calls=5,*,rejected_calls=0,failed_calls=3} [cmdstat auth]
    }
    """
    r.run("config", "resetstat")
    # TODO: r module load miscmodule
    rd = valkey_deferring_client()
    r.run("acl", "setuser", "foo", ">pwd", "on", "~*", "&*", "+@all")
    # TODO: $rd AUTH foo block_allow
    wait_for_blocked_clients_count(1)
    try:
        e = r.run("module", "unload", "testacl")
    except Exception as _catch_err:
        e = str(_catch_err)
    assert fnmatch(str(e), "*the module has blocked clients*")
    assert "OK" == r.run("module", "unload", "moduleauthtwo")
    assert "OK" == r.run("module", "unload", "misc")
    wait_for_blocked_clients_count(0, 500, 10)
    # TODO: $rd flush
    # TODO: assert_equal $rd read "OK"
    assert fnmatch(str(cmdstat("auth")), "*calls=1,*,rejected_calls=0,failed_calls=0")
    assert "OK" == r.run("AUTH", "foo", "allow")
    r.run("module", "unload", "testacl")
    with pytest.raises(Exception, match=".*WRONGPASS.*"):
        r.run("AUTH", "foo", "block_allow")
    with pytest.raises(Exception, match=".*WRONGPASS.*"):
        r.run("AUTH", "foo", "allow_two")
    with pytest.raises(Exception, match=".*WRONGPASS.*"):
        r.run("AUTH", "foo", "allow")
    assert fnmatch(str(cmdstat("auth")), "*calls=5,*,rejected_calls=0,failed_calls=3")


# --- stubs for unimplemented TCL helpers ---


def assert_(*args):
    raise NotImplementedError("assert_")


def assert_error(*args):
    raise NotImplementedError("assert_error")


def cmdstat(*args):
    raise NotImplementedError("cmdstat")


def valkey_deferring_client(*args):
    raise NotImplementedError("valkey_deferring_client")


def wait_for_blocked_clients_count(*args):
    raise NotImplementedError("wait_for_blocked_clients_count")
