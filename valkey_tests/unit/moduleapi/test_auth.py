# ruff: noqa: PLR2004

from fnmatch import fnmatch

import pytest

from tests.valkey_test_client import ValkeyTestClient

"""
set testmodule file normalize tests/modules/auth.so
"""

pytestmark = [pytest.mark.modules]


def test_modules_can_create_a_user_that_can_be_authenticated(r: ValkeyTestClient) -> None:
    """
    test {Modules can create a user that can be authenticated} {
        # Make sure we start authenticated with default user
        r auth default ""
        assert_equal [r acl whoami] "default"
        r auth.createmoduleuser

        set id [r auth.authmoduleuser]
        assert_equal [r client id] $id

        # Verify returned id is the same as our current id and
        # we are authenticated with the specified user
        assert_equal [r acl whoami] "global"
    }
    """
    r.run("auth", "default", "")
    assert r.run("acl", "whoami") == "default"
    r.run("auth.createmoduleuser")
    id = r.run("auth.authmoduleuser")
    assert r.run("client", "id") == id
    assert r.run("acl", "whoami") == "global"


def test_de_authenticating_clients_is_tracked_and_kills_clients(r: ValkeyTestClient) -> None:
    """
    test {De-authenticating clients is tracked and kills clients} {
        assert_equal [r auth.changecount] 0
        r auth.createmoduleuser

        # Catch the I/O exception that was thrown when the server
        # disconnected with us.
        catch { [r ping] } e
        assert_match {*I/O*} $e

        # Check that a user change was registered
        assert_equal [r auth.changecount] 1
    }
    """
    assert r.run("auth.changecount") == 0
    r.run("auth.createmoduleuser")
    try:
        e = r.run("ping")
    except Exception as _catch_err:
        e = str(_catch_err)
    assert fnmatch(str(e), "*I/O*")
    assert r.run("auth.changecount") == 1


def test_modules_can_t_authenticate_with_acls_users_that_dont_exist(r: ValkeyTestClient) -> None:
    """
    test {Modules can't authenticate with ACLs users that dont exist} {
        catch { [r auth.authrealuser auth-module-test-fake] } e
        assert_match {*Invalid user*} $e
    }
    """
    try:
        e = r.run("auth.authrealuser", "auth-module-test-fake")
    except Exception as _catch_err:
        e = str(_catch_err)
    assert fnmatch(str(e), "*Invalid user*")


def test_modules_can_authenticate_with_acl_users(r: ValkeyTestClient) -> None:
    """
    test {Modules can authenticate with ACL users} {
        assert_equal [r acl whoami] "default"

        # Create user to auth into
        r acl setuser auth-module-test on allkeys allcommands

        set id [r auth.authrealuser auth-module-test]

        # Verify returned id is the same as our current id and
        # we are authenticated with the specified user
        assert_equal [r client id] $id
        assert_equal [r acl whoami] "auth-module-test"
    }
    """
    assert r.run("acl", "whoami") == "default"
    r.run("acl", "setuser", "auth-module-test", "on", "allkeys", "allcommands")
    id = r.run("auth.authrealuser", "auth-module-test")
    assert r.run("client", "id") == id
    assert r.run("acl", "whoami") == "auth-module-test"


def test_client_callback_is_called_on_user_switch(r: ValkeyTestClient) -> None:
    """
    test {Client callback is called on user switch} {
        assert_equal [r auth.changecount] 0

        # Auth again and validate change count
        r auth.authrealuser auth-module-test
        assert_equal [r auth.changecount] 1

        # Re-auth with the default user
        r auth default ""
        assert_equal [r auth.changecount] 1
        assert_equal [r acl whoami] "default"

        # Re-auth with the default user again, to
        # verify the callback isn't fired again
        r auth default ""
        assert_equal [r auth.changecount] 0
        assert_equal [r acl whoami] "default"
    }
    """
    assert r.run("auth.changecount") == 0
    r.run("auth.authrealuser", "auth-module-test")
    assert r.run("auth.changecount") == 1
    r.run("auth", "default", "")
    assert r.run("auth.changecount") == 1
    assert r.run("acl", "whoami") == "default"
    r.run("auth", "default", "")
    assert r.run("auth.changecount") == 0
    assert r.run("acl", "whoami") == "default"


def test_modules_can_redact_arguments(r: ValkeyTestClient) -> None:
    """
    test {modules can redact arguments} {
        r config set slowlog-log-slower-than 0
        r slowlog reset
        r auth.redact 1 2 3 4
        r auth.redact 1 2 3
        r config set slowlog-log-slower-than -1
        set slowlog_resp [r slowlog get]

        # There will be 3 records, slowlog reset and the
        # two auth redact calls.
        assert_equal 3 [llength $slowlog_resp]
        assert_equal {slowlog reset} [lindex [lindex $slowlog_resp 2] 3]
        assert_equal {auth.redact 1 (redacted) 3 (redacted)} [lindex [lindex $slowlog_resp 1] 3]
        assert_equal {auth.redact (redacted) 2 (redacted)} [lindex [lindex $slowlog_resp 0] 3]
    }
    """
    r.run("config", "set", "slowlog-log-slower-than", 0)
    r.run("slowlog", "reset")
    r.run("auth.redact", 1, 2, 3, 4)
    r.run("auth.redact", 1, 2, 3)
    r.run("config", "set", "slowlog-log-slower-than", -1)
    slowlog_resp = r.run("slowlog", "get")
    assert 3 == len(slowlog_resp)
    assert "slowlog reset" == slowlog_resp[2][3]
    assert "auth.redact 1 (redacted) 3 (redacted)" == slowlog_resp[1][3]
    assert "auth.redact (redacted) 2 (redacted)" == slowlog_resp[0][3]


def test_unload_the_module_testacl(r: ValkeyTestClient) -> None:
    """
    test "Unload the module - testacl" {
        assert_equal {OK} [r module unload testacl]
    }
    """
    assert "OK" == r.run("module", "unload", "testacl")
