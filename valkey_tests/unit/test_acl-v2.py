# ruff: noqa: PLR2004, ANN001, ANN002, ANN201
from fnmatch import fnmatch

import pytest

from tests.valkey_test_client import ValkeyTestClient

pytestmark = [pytest.mark.acl_external_skip]


"""
set r2 valkey_client
"""


def test_test_basic_multiple_selectors(r: ValkeyTestClient, r2) -> None:
    """
    test {Test basic multiple selectors} {
        r ACL SETUSER selector-1 on -@all resetkeys nopass
        $r2 auth selector-1 password
        catch {$r2 ping} err
        assert_match "*NOPERM*command*" $err
        catch {$r2 set write::foo bar} err
        assert_match "*NOPERM*command*" $err
        catch {$r2 get read::foo} err
        assert_match "*NOPERM*command*" $err

        r ACL SETUSER selector-1 (+@write ~write::*) (+@read ~read::*)
        catch {$r2 ping} err
        assert_equal "OK" [$r2 set write::foo bar]
        assert_equal "" [$r2 get read::foo]
        catch {$r2 get write::foo} err
        assert_match "*NOPERM*key*" $err
        catch {$r2 set read::foo bar} err
        assert_match "*NOPERM*key*" $err
    }
    """
    r.run("ACL", "SETUSER", "selector-1", "on", "-@all", "resetkeys", "nopass")
    r2.run("auth", "selector-1", "password")
    err = None
    try:
        err = r2.run("ping")
    except Exception as _catch_err:
        err = str(_catch_err)
    assert fnmatch(str(err), "*NOPERM*command*")
    err = None
    try:
        err = r2.run("set", "write::foo", "bar")
    except Exception as _catch_err:
        err = str(_catch_err)
    assert fnmatch(str(err), "*NOPERM*command*")
    err = None
    try:
        err = r2.run("get", "read::foo")
    except Exception as _catch_err:
        err = str(_catch_err)
    assert fnmatch(str(err), "*NOPERM*command*")
    r.run("ACL", "SETUSER", "selector-1", "(+@write", "~write::*)", "(+@read", "~read::*)")
    err = None
    try:
        err = r2.run("ping")
    except Exception as _catch_err:
        err = str(_catch_err)
    assert "OK" == r2.run("set", "write::foo", "bar")
    assert "" == r2.run("get", "read::foo")
    err = None
    try:
        err = r2.run("get", "write::foo")
    except Exception as _catch_err:
        err = str(_catch_err)
    assert fnmatch(str(err), "*NOPERM*key*")
    err = None
    try:
        err = r2.run("set", "read::foo", "bar")
    except Exception as _catch_err:
        err = str(_catch_err)
    assert fnmatch(str(err), "*NOPERM*key*")


def test_test_acl_selectors_by_default_have_no_permissions(r: ValkeyTestClient) -> None:
    """
    test {Test ACL selectors by default have no permissions} {
        r ACL SETUSER selector-default reset ()
        set user [r ACL GETUSER "selector-default"]
        assert_equal 1 [llength [dict get $user selectors]]
        assert_equal "" [dict get [lindex [dict get $user selectors] 0] keys]
        assert_equal "" [dict get [lindex [dict get $user selectors] 0] channels]
        assert_equal "-@all" [dict get [lindex [dict get $user selectors] 0] commands]
    }
    """
    r.run("ACL", "SETUSER", "selector-default", "reset", "()")
    user = r.run("ACL", "GETUSER", "selector-default")
    assert 1 == len(user["selectors"])
    assert "" == user["selectors"][0]["keys"]
    assert "" == user["selectors"][0]["channels"]
    assert "-@all" == user["selectors"][0]["commands"]


def test_test_deleting_selectors(r: ValkeyTestClient) -> None:
    """
    test {Test deleting selectors} {
        r ACL SETUSER selector-del on "(~added-selector)"
        set user [r ACL GETUSER "selector-del"]
        assert_equal "~added-selector" [dict get [lindex [dict get $user selectors] 0] keys]
        assert_equal [llength [dict get $user selectors]] 1

        r ACL SETUSER selector-del clearselectors
        set user [r ACL GETUSER "selector-del"]
        assert_equal [llength [dict get $user selectors]] 0
    }
    """
    r.run("ACL", "SETUSER", "selector-del", "on", "(~added-selector)")
    user = r.run("ACL", "GETUSER", "selector-del")
    assert "~added-selector" == user["selectors"][0]["keys"]
    assert len(user["selectors"]) == 1
    r.run("ACL", "SETUSER", "selector-del", "clearselectors")
    user = r.run("ACL", "GETUSER", "selector-del")
    assert len(user["selectors"]) == 0


def test_test_selector_syntax_error_reports_the_error_in_the_selector_context(r: ValkeyTestClient) -> None:
    """
    test {Test selector syntax error reports the error in the selector context} {
        catch {r ACL SETUSER selector-syntax on (this-is-invalid)} e
        assert_match "ERR Error in ACL SETUSER modifier '(*)*Syntax*" $e

        catch {r ACL SETUSER selector-syntax on (&* &fail)} e
        assert_match "ERR Error in ACL SETUSER modifier '(*)*Adding a pattern after the*" $e

        catch {r ACL SETUSER selector-syntax on (+PING (+SELECT (+DEL} e
        assert_match "ERR Unmatched parenthesis in acl selector*" $e

        catch {r ACL SETUSER selector-syntax on (+PING (+SELECT (+DEL ) ) ) } e
        assert_match "ERR Error in ACL SETUSER modifier*" $e

        catch {r ACL SETUSER selector-syntax on (+PING (+SELECT (+DEL ) } e
        assert_match "ERR Error in ACL SETUSER modifier*" $e

        assert_equal "" [r ACL GETUSER selector-syntax]
    }
    """
    e = None
    try:
        e = r.run("ACL", "SETUSER", "selector-syntax", "on", "(this-is-invalid)")
    except Exception as _catch_err:
        e = str(_catch_err)
    assert fnmatch(str(e), "ERR Error in ACL SETUSER modifier '(*)*Syntax*")
    e = None
    try:
        e = r.run("ACL", "SETUSER", "selector-syntax", "on", "(&*", "&fail)")
    except Exception as _catch_err:
        e = str(_catch_err)
    assert fnmatch(str(e), "ERR Error in ACL SETUSER modifier '(*)*Adding a pattern after the*")
    e = None
    try:
        e = r.run("ACL", "SETUSER", "selector-syntax", "on", "(+PING", "(+SELECT", "(+DEL")
    except Exception as _catch_err:
        e = str(_catch_err)
    assert fnmatch(str(e), "ERR Unmatched parenthesis in acl selector*")
    e = None
    try:
        e = r.run("ACL", "SETUSER", "selector-syntax", "on", "(+PING", "(+SELECT", "(+DEL", ")", ")", ")")
    except Exception as _catch_err:
        e = str(_catch_err)
    assert fnmatch(str(e), "ERR Error in ACL SETUSER modifier*")
    e = None
    try:
        e = r.run("ACL", "SETUSER", "selector-syntax", "on", "(+PING", "(+SELECT", "(+DEL", ")")
    except Exception as _catch_err:
        e = str(_catch_err)
    assert fnmatch(str(e), "ERR Error in ACL SETUSER modifier*")
    assert "" == r.run("ACL", "GETUSER", "selector-syntax")


def test_test_flexible_selector_definition(r: ValkeyTestClient) -> None:
    """
    test {Test flexible selector definition} {
        # Test valid selectors
        r ACL SETUSER selector-2 "(~key1 +get )" "( ~key2 +get )" "( ~key3 +get)" "(~key4 +get)"
        r ACL SETUSER selector-2 (~key5 +get ) ( ~key6 +get ) ( ~key7 +get) (~key8 +get)
        set user [r ACL GETUSER "selector-2"]
        assert_equal "~key1" [dict get [lindex [dict get $user selectors] 0] keys]
        assert_equal "~key2" [dict get [lindex [dict get $user selectors] 1] keys]
        assert_equal "~key3" [dict get [lindex [dict get $user selectors] 2] keys]
        assert_equal "~key4" [dict get [lindex [dict get $user selectors] 3] keys]
        assert_equal "~key5" [dict get [lindex [dict get $user selectors] 4] keys]
        assert_equal "~key6" [dict get [lindex [dict get $user selectors] 5] keys]
        assert_equal "~key7" [dict get [lindex [dict get $user selectors] 6] keys]
        assert_equal "~key8" [dict get [lindex [dict get $user selectors] 7] keys]

        # Test invalid selector syntax
        catch {r ACL SETUSER invalid-selector " () "} err
        assert_match "ERR*Syntax error*" $err
        catch {r ACL SETUSER invalid-selector (} err
        assert_match "ERR*Unmatched parenthesis*" $err
        catch {r ACL SETUSER invalid-selector )} err
        assert_match "ERR*Syntax error*" $err
    }
    """
    r.run("ACL", "SETUSER", "selector-2", "(~key1 +get )", "( ~key2 +get )", "( ~key3 +get)", "(~key4 +get)")
    r.run(
        "ACL",
        "SETUSER",
        "selector-2",
        "(~key5",
        "+get",
        ")",
        "(",
        "~key6",
        "+get",
        ")",
        "(",
        "~key7",
        "+get)",
        "(~key8",
        "+get)",
    )
    user = r.run("ACL", "GETUSER", "selector-2")
    assert "~key1" == user["selectors"][0]["keys"]
    assert "~key2" == user["selectors"][1]["keys"]
    assert "~key3" == user["selectors"][2]["keys"]
    assert "~key4" == user["selectors"][3]["keys"]
    assert "~key5" == user["selectors"][4]["keys"]
    assert "~key6" == user["selectors"][5]["keys"]
    assert "~key7" == user["selectors"][6]["keys"]
    assert "~key8" == user["selectors"][7]["keys"]
    err = None
    try:
        err = r.run("ACL", "SETUSER", "invalid-selector", " () ")
    except Exception as _catch_err:
        err = str(_catch_err)
    assert fnmatch(str(err), "ERR*Syntax error*")
    err = None
    try:
        err = r.run("ACL", "SETUSER", "invalid-selector", "(")
    except Exception as _catch_err:
        err = str(_catch_err)
    assert fnmatch(str(err), "ERR*Unmatched parenthesis*")
    err = None
    try:
        err = r.run("ACL", "SETUSER", "invalid-selector", ")")
    except Exception as _catch_err:
        err = str(_catch_err)
    assert fnmatch(str(err), "ERR*Syntax error*")


def test_test_separate_read_permission(r: ValkeyTestClient, r2) -> None:
    """
    test {Test separate read permission} {
        r ACL SETUSER key-permission-R on nopass %R~read* +@all
        $r2 auth key-permission-R password
        assert_equal PONG [$r2 PING]
        r set readstr bar
        assert_equal bar [$r2 get readstr]
        catch {$r2 set readstr bar} err
        assert_match "*NOPERM*key*" $err
        catch {$r2 get notread} err
        assert_match "*NOPERM*key*" $err
    }
    """
    r.run("ACL", "SETUSER", "key-permission-R", "on", "nopass", "%R~read*", "+@all")
    r2.run("auth", "key-permission-R", "password")
    assert "PONG" == r2.run("PING")
    r.run("set", "readstr", "bar")
    assert "bar" == r2.run("get", "readstr")
    err = None
    try:
        err = r2.run("set", "readstr", "bar")
    except Exception as _catch_err:
        err = str(_catch_err)
    assert fnmatch(str(err), "*NOPERM*key*")
    err = None
    try:
        err = r2.run("get", "notread")
    except Exception as _catch_err:
        err = str(_catch_err)
    assert fnmatch(str(err), "*NOPERM*key*")


def test_test_separate_write_permission(r: ValkeyTestClient, r2) -> None:
    """
    test {Test separate write permission} {
        r ACL SETUSER key-permission-W on nopass %W~write* +@all
        $r2 auth key-permission-W password
        assert_equal PONG [$r2 PING]
        # Note, SET is a RW command, so it's not used for testing
        $r2 LPUSH writelist 10
        catch {$r2 GET writestr} err
        assert_match "*NOPERM*key*" $err
        catch {$r2 LPUSH notwrite 10} err
        assert_match "*NOPERM*key*" $err
    }
    """
    r.run("ACL", "SETUSER", "key-permission-W", "on", "nopass", "%W~write*", "+@all")
    r2.run("auth", "key-permission-W", "password")
    assert "PONG" == r2.run("PING")
    r2.run("LPUSH", "writelist", 10)
    err = None
    try:
        err = r2.run("GET", "writestr")
    except Exception as _catch_err:
        err = str(_catch_err)
    assert fnmatch(str(err), "*NOPERM*key*")
    err = None
    try:
        err = r2.run("LPUSH", "notwrite", 10)
    except Exception as _catch_err:
        err = str(_catch_err)
    assert fnmatch(str(err), "*NOPERM*key*")


def test_test_separate_read_and_write_permissions(r: ValkeyTestClient, r2) -> None:
    """
    test {Test separate read and write permissions} {
        r ACL SETUSER key-permission-RW on nopass %R~read* %W~write* +@all
        $r2 auth key-permission-RW password
        assert_equal PONG [$r2 PING]
        r set read bar
        $r2 copy read write
        catch {$r2 copy write read} err
        assert_match "*NOPERM*key*" $err
    }
    """
    r.run("ACL", "SETUSER", "key-permission-RW", "on", "nopass", "%R~read*", "%W~write*", "+@all")
    r2.run("auth", "key-permission-RW", "password")
    assert "PONG" == r2.run("PING")
    r.run("set", "read", "bar")
    r2.run("copy", "read", "write")
    err = None
    try:
        err = r2.run("copy", "write", "read")
    except Exception as _catch_err:
        err = str(_catch_err)
    assert fnmatch(str(err), "*NOPERM*key*")


def test_validate_read_and_write_permissions_format(r: ValkeyTestClient) -> None:
    """
    test {Validate read and write permissions format} {
        # Regression tests for CVE-2024-51741
        assert_error "ERR Error in ACL SETUSER modifier '%~': Syntax error" {r ACL SETUSER invalid %~}
        assert_error "ERR Error in ACL SETUSER modifier '%': Syntax error" {r ACL SETUSER invalid %}
    }
    """
    with pytest.raises(Exception, match="ERR\\ Error\\ in\\ ACL\\ SETUSER\\ modifier\\ '%\\~':\\ Syntax\\ error"):
        r.run("ACL", "SETUSER", "invalid", "%~")
    with pytest.raises(Exception, match="ERR\\ Error\\ in\\ ACL\\ SETUSER\\ modifier\\ '%':\\ Syntax\\ error"):
        r.run("ACL", "SETUSER", "invalid", "%")


def test_validate_key_permissions_format_empty_and_omitted_pattern(r: ValkeyTestClient) -> None:
    """
    test {Validate key permissions format - empty and omitted pattern} {
        # Empty pattern results with access to only the empty key
        r ACL SETUSER key-permission-no-key on nopass %RW~ +@all
        assert_equal "User key-permission-no-key has no permissions to access the 'x' key" [r ACL DRYRUN key-permission-no-key GET x]
        assert_equal "OK" [r ACL DRYRUN key-permission-no-key GET ""]

        # This is incorrect syntax, it should have `~`, but we'll allow it for compatibility since it does something
        r ACL SETUSER key-permission-omit on nopass %RW +@all
        assert_equal "User key-permission-omit has no permissions to access the 'x' key" [r ACL DRYRUN key-permission-omit GET x]
        assert_equal "OK" [r ACL DRYRUN key-permission-omit GET ""]

        # Assert these two are equivalent
        assert_equal [r ACL GETUSER key-permission-omit] [r ACL GETUSER key-permission-no-key]
    }
    """
    r.run("ACL", "SETUSER", "key-permission-no-key", "on", "nopass", "%RW~", "+@all")
    assert "User key-permission-no-key has no permissions to access the 'x' key" == r.run(
        "ACL", "DRYRUN", "key-permission-no-key", "GET", "x"
    )
    assert "OK" == r.run("ACL", "DRYRUN", "key-permission-no-key", "GET", "")
    r.run("ACL", "SETUSER", "key-permission-omit", "on", "nopass", "%RW", "+@all")
    assert "User key-permission-omit has no permissions to access the 'x' key" == r.run(
        "ACL", "DRYRUN", "key-permission-omit", "GET", "x"
    )
    assert "OK" == r.run("ACL", "DRYRUN", "key-permission-omit", "GET", "")
    assert r.run("ACL", "GETUSER", "key-permission-omit") == r.run("ACL", "GETUSER", "key-permission-no-key")


def test_test_separate_read_and_write_permissions_on_different_selectors_are_not_additive(
    r: ValkeyTestClient, r2
) -> None:
    """
    test {Test separate read and write permissions on different selectors are not additive} {
        r ACL SETUSER key-permission-RW-selector on nopass "(%R~read* +@all)" "(%W~write* +@all)"
        $r2 auth key-permission-RW-selector password
        assert_equal PONG [$r2 PING]

        # Verify write selector
        $r2 LPUSH writelist 10
        catch {$r2 GET writestr} err
        assert_match "*NOPERM*key*" $err
        catch {$r2 LPUSH notwrite 10} err
        assert_match "*NOPERM*key*" $err

        # Verify read selector
        r set readstr bar
        assert_equal bar [$r2 get readstr]
        catch {$r2 set readstr bar} err
        assert_match "*NOPERM*key*" $err
        catch {$r2 get notread} err
        assert_match "*NOPERM*key*" $err

        # Verify they don't combine
        catch {$r2 copy read write} err
        assert_match "*NOPERM*key*" $err
        catch {$r2 copy write read} err
        assert_match "*NOPERM*key*" $err
    }
    """
    r.run("ACL", "SETUSER", "key-permission-RW-selector", "on", "nopass", "(%R~read* +@all)", "(%W~write* +@all)")
    r2.run("auth", "key-permission-RW-selector", "password")
    assert "PONG" == r2.run("PING")
    r2.run("LPUSH", "writelist", 10)
    err = None
    try:
        err = r2.run("GET", "writestr")
    except Exception as _catch_err:
        err = str(_catch_err)
    assert fnmatch(str(err), "*NOPERM*key*")
    err = None
    try:
        err = r2.run("LPUSH", "notwrite", 10)
    except Exception as _catch_err:
        err = str(_catch_err)
    assert fnmatch(str(err), "*NOPERM*key*")
    r.run("set", "readstr", "bar")
    assert "bar" == r2.run("get", "readstr")
    err = None
    try:
        err = r2.run("set", "readstr", "bar")
    except Exception as _catch_err:
        err = str(_catch_err)
    assert fnmatch(str(err), "*NOPERM*key*")
    err = None
    try:
        err = r2.run("get", "notread")
    except Exception as _catch_err:
        err = str(_catch_err)
    assert fnmatch(str(err), "*NOPERM*key*")
    err = None
    try:
        err = r2.run("copy", "read", "write")
    except Exception as _catch_err:
        err = str(_catch_err)
    assert fnmatch(str(err), "*NOPERM*key*")
    err = None
    try:
        err = r2.run("copy", "write", "read")
    except Exception as _catch_err:
        err = str(_catch_err)
    assert fnmatch(str(err), "*NOPERM*key*")


def test_test_set_with_separate_read_permission(r: ValkeyTestClient, r2) -> None:
    """
    test {Test SET with separate read permission} {
        r del readstr
        r ACL SETUSER set-key-permission-R on nopass %R~read* +@all
        $r2 auth set-key-permission-R password
        assert_equal PONG [$r2 PING]
        assert_equal {} [$r2 get readstr]

        # We don't have the permission to WRITE key.
        assert_error {*NOPERM*key*} {$r2 set readstr bar}
        assert_error {*NOPERM*key*} {$r2 set readstr bar get}
        assert_error {*NOPERM*key*} {$r2 set readstr bar ex 100}
        assert_error {*NOPERM*key*} {$r2 set readstr bar keepttl nx}
    }
    """
    r.run("del", "readstr")
    r.run("ACL", "SETUSER", "set-key-permission-R", "on", "nopass", "%R~read*", "+@all")
    r2.run("auth", "set-key-permission-R", "password")
    assert "PONG" == r2.run("PING")
    assert "" == r2.run("get", "readstr")
    assert_error("*NOPERM*key*", "$r2 set readstr bar")
    assert_error("*NOPERM*key*", "$r2 set readstr bar get")
    assert_error("*NOPERM*key*", "$r2 set readstr bar ex 100")
    assert_error("*NOPERM*key*", "$r2 set readstr bar keepttl nx")


def test_test_set_with_separate_write_permission(r: ValkeyTestClient, r2) -> None:
    """
    test {Test SET with separate write permission} {
        r del writestr
        r ACL SETUSER set-key-permission-W on nopass %W~write* +@all
        $r2 auth set-key-permission-W password
        assert_equal PONG [$r2 PING]
        assert_equal {OK} [$r2 set writestr bar]
        assert_equal {OK} [$r2 set writestr get]

        # We don't have the permission to READ key.
        assert_error {*NOPERM*key*} {$r2 set get writestr}
        assert_error {*NOPERM*key*} {$r2 set writestr bar get}
        assert_error {*NOPERM*key*} {$r2 set writestr bar get ex 100}
        assert_error {*NOPERM*key*} {$r2 set writestr bar get keepttl nx}

        # this probably should be `ERR value is not an integer or out of range`
        assert_error {*NOPERM*key*} {$r2 set writestr bar ex get}
    }
    """
    r.run("del", "writestr")
    r.run("ACL", "SETUSER", "set-key-permission-W", "on", "nopass", "%W~write*", "+@all")
    r2.run("auth", "set-key-permission-W", "password")
    assert "PONG" == r2.run("PING")
    assert "OK" == r2.run("set", "writestr", "bar")
    assert "OK" == r2.run("set", "writestr", "get")
    assert_error("*NOPERM*key*", "$r2 set get writestr")
    assert_error("*NOPERM*key*", "$r2 set writestr bar get")
    assert_error("*NOPERM*key*", "$r2 set writestr bar get ex 100")
    assert_error("*NOPERM*key*", "$r2 set writestr bar get keepttl nx")
    assert_error("*NOPERM*key*", "$r2 set writestr bar ex get")


def test_test_set_with_read_and_write_permissions(r: ValkeyTestClient, r2) -> None:
    """
    test {Test SET with read and write permissions} {
        r del readwrite_str
        r ACL SETUSER set-key-permission-RW-selector on nopass %RW~readwrite* +@all
        $r2 auth set-key-permission-RW-selector password
        assert_equal PONG [$r2 PING]

        assert_equal {} [$r2 get readwrite_str]
        assert_error {ERR * not an integer *} {$r2 set readwrite_str bar ex get}

        assert_equal {OK} [$r2 set readwrite_str bar]
        assert_equal {bar} [$r2 get readwrite_str]

        assert_equal {bar} [$r2 set readwrite_str bar2 get]
        assert_equal {bar2} [$r2 get readwrite_str]

        assert_equal {bar2} [$r2 set readwrite_str bar3 get ex 10]
        assert_equal {bar3} [$r2 get readwrite_str]
        assert_range [$r2 ttl readwrite_str] 5 10
    }
    """
    r.run("del", "readwrite_str")
    r.run("ACL", "SETUSER", "set-key-permission-RW-selector", "on", "nopass", "%RW~readwrite*", "+@all")
    r2.run("auth", "set-key-permission-RW-selector", "password")
    assert "PONG" == r2.run("PING")
    assert "" == r2.run("get", "readwrite_str")
    assert_error("ERR * not an integer *", "$r2 set readwrite_str bar ex get")
    assert "OK" == r2.run("set", "readwrite_str", "bar")
    assert "bar" == r2.run("get", "readwrite_str")
    assert "bar" == r2.run("set", "readwrite_str", "bar2", "get")
    assert "bar2" == r2.run("get", "readwrite_str")
    assert "bar2" == r2.run("set", "readwrite_str", "bar3", "get", "ex", 10)
    assert "bar3" == r2.run("get", "readwrite_str")
    assert_range(r2.run("ttl", "readwrite_str"), 5, 10)


def test_test_bitfield_with_separate_read_permission(r: ValkeyTestClient, r2) -> None:
    """
    test {Test BITFIELD with separate read permission} {
        r del readstr
        r ACL SETUSER bitfield-key-permission-R on nopass %R~read* +@all
        $r2 auth bitfield-key-permission-R password
        assert_equal PONG [$r2 PING]
        assert_equal {0} [$r2 bitfield readstr get u4 0]

        # We don't have the permission to WRITE key.
        assert_error {*NOPERM*key*} {$r2 bitfield readstr set u4 0 1}
        assert_error {*NOPERM*key*} {$r2 bitfield readstr get u4 0 set u4 0 1}
        assert_error {*NOPERM*key*} {$r2 bitfield readstr incrby u4 0 1}
    }
    """
    r.run("del", "readstr")
    r.run("ACL", "SETUSER", "bitfield-key-permission-R", "on", "nopass", "%R~read*", "+@all")
    r2.run("auth", "bitfield-key-permission-R", "password")
    assert "PONG" == r2.run("PING")
    assert "0" == r2.run("bitfield", "readstr", "get", "u4", 0)
    assert_error("*NOPERM*key*", "$r2 bitfield readstr set u4 0 1")
    assert_error("*NOPERM*key*", "$r2 bitfield readstr get u4 0 set u4 0 1")
    assert_error("*NOPERM*key*", "$r2 bitfield readstr incrby u4 0 1")


def test_test_bitfield_with_separate_write_permission(r: ValkeyTestClient, r2) -> None:
    """
    test {Test BITFIELD with separate write permission} {
        r del writestr
        r ACL SETUSER bitfield-key-permission-W on nopass %W~write* +@all
        $r2 auth bitfield-key-permission-W password
        assert_equal PONG [$r2 PING]

        # We don't have the permission to READ key.
        assert_error {*NOPERM*key*} {$r2 bitfield writestr get u4 0}
        assert_error {*NOPERM*key*} {$r2 bitfield writestr set u4 0 1}
        assert_error {*NOPERM*key*} {$r2 bitfield writestr incrby u4 0 1}
    }
    """
    r.run("del", "writestr")
    r.run("ACL", "SETUSER", "bitfield-key-permission-W", "on", "nopass", "%W~write*", "+@all")
    r2.run("auth", "bitfield-key-permission-W", "password")
    assert "PONG" == r2.run("PING")
    assert_error("*NOPERM*key*", "$r2 bitfield writestr get u4 0")
    assert_error("*NOPERM*key*", "$r2 bitfield writestr set u4 0 1")
    assert_error("*NOPERM*key*", "$r2 bitfield writestr incrby u4 0 1")


def test_test_bitfield_with_read_and_write_permissions(r: ValkeyTestClient, r2) -> None:
    """
    test {Test BITFIELD with read and write permissions} {
        r del readwrite_str
        r ACL SETUSER bitfield-key-permission-RW-selector on nopass %RW~readwrite* +@all
        $r2 auth bitfield-key-permission-RW-selector password
        assert_equal PONG [$r2 PING]

        assert_equal {0} [$r2 bitfield readwrite_str get u4 0]
        assert_equal {0} [$r2 bitfield readwrite_str set u4 0 1]
        assert_equal {2} [$r2 bitfield readwrite_str incrby u4 0 1]
        assert_equal {2} [$r2 bitfield readwrite_str get u4 0]
    }
    """
    r.run("del", "readwrite_str")
    r.run("ACL", "SETUSER", "bitfield-key-permission-RW-selector", "on", "nopass", "%RW~readwrite*", "+@all")
    r2.run("auth", "bitfield-key-permission-RW-selector", "password")
    assert "PONG" == r2.run("PING")
    assert "0" == r2.run("bitfield", "readwrite_str", "get", "u4", 0)
    assert "0" == r2.run("bitfield", "readwrite_str", "set", "u4", 0, 1)
    assert "2" == r2.run("bitfield", "readwrite_str", "incrby", "u4", 0, 1)
    assert "2" == r2.run("bitfield", "readwrite_str", "get", "u4", 0)


def test_test_acl_log_correctly_identifies_the_relevant_item_when_selectors_are_used(r: ValkeyTestClient, r2) -> None:
    """
    test {Test ACL log correctly identifies the relevant item when selectors are used} {
        r ACL SETUSER acl-log-test-selector on nopass
        r ACL SETUSER acl-log-test-selector +mget ~key (+mget ~key ~otherkey)
        $r2 auth acl-log-test-selector password

        # Test that command is shown only if none of the selectors match
        r ACL LOG RESET
        catch {$r2 GET key} err
        assert_match "*NOPERM*command*" $err
        set entry [lindex [r ACL LOG] 0]
        assert_equal [dict get $entry username] "acl-log-test-selector"
        assert_equal [dict get $entry context] "toplevel"
        assert_equal [dict get $entry reason] "command"
        assert_equal [dict get $entry object] "get"

        # Test two cases where the first selector matches less than the
        # second selector. We should still show the logically first unmatched key.
        r ACL LOG RESET
        catch {$r2 MGET otherkey someotherkey} err
        assert_match "*NOPERM*key*" $err
        set entry [lindex [r ACL LOG] 0]
        assert_equal [dict get $entry username] "acl-log-test-selector"
        assert_equal [dict get $entry context] "toplevel"
        assert_equal [dict get $entry reason] "key"
        assert_equal [dict get $entry object] "someotherkey"

        r ACL LOG RESET
        catch {$r2 MGET key otherkey someotherkey} err
        assert_match "*NOPERM*key*" $err
        set entry [lindex [r ACL LOG] 0]
        assert_equal [dict get $entry username] "acl-log-test-selector"
        assert_equal [dict get $entry context] "toplevel"
        assert_equal [dict get $entry reason] "key"
        assert_equal [dict get $entry object] "someotherkey"
    }
    """
    r.run("ACL", "SETUSER", "acl-log-test-selector", "on", "nopass")
    r.run("ACL", "SETUSER", "acl-log-test-selector", "+mget", "~key", "(+mget", "~key", "~otherkey)")
    r2.run("auth", "acl-log-test-selector", "password")
    r.run("ACL", "LOG", "RESET")
    err = None
    try:
        err = r2.run("GET", "key")
    except Exception as _catch_err:
        err = str(_catch_err)
    assert fnmatch(str(err), "*NOPERM*command*")
    entry = r.run("ACL", "LOG")[0]
    assert entry["username"] == "acl-log-test-selector"
    assert entry["context"] == "toplevel"
    assert entry["reason"] == "command"
    assert entry["object"] == "get"
    r.run("ACL", "LOG", "RESET")
    err = None
    try:
        err = r2.run("MGET", "otherkey", "someotherkey")
    except Exception as _catch_err:
        err = str(_catch_err)
    assert fnmatch(str(err), "*NOPERM*key*")
    entry = r.run("ACL", "LOG")[0]
    assert entry["username"] == "acl-log-test-selector"
    assert entry["context"] == "toplevel"
    assert entry["reason"] == "key"
    assert entry["object"] == "someotherkey"
    r.run("ACL", "LOG", "RESET")
    err = None
    try:
        err = r2.run("MGET", "key", "otherkey", "someotherkey")
    except Exception as _catch_err:
        err = str(_catch_err)
    assert fnmatch(str(err), "*NOPERM*key*")
    entry = r.run("ACL", "LOG")[0]
    assert entry["username"] == "acl-log-test-selector"
    assert entry["context"] == "toplevel"
    assert entry["reason"] == "key"
    assert entry["object"] == "someotherkey"


def test_test_acl_getuser_response_information(r: ValkeyTestClient) -> None:
    """
    test {Test ACL GETUSER response information} {
        r ACL setuser selector-info -@all +get resetchannels &channel1 %R~foo1 %W~bar1 ~baz1
        r ACL setuser selector-info (-@all +set resetchannels &channel2 %R~foo2 %W~bar2 ~baz2)
        set user [r ACL GETUSER "selector-info"]

        # Root selector
        assert_equal "%R~foo1 %W~bar1 ~baz1" [dict get $user keys]
        assert_equal "&channel1" [dict get $user channels]
        assert_equal "-@all +get" [dict get $user commands]

        # Added selector
        set secondary_selector [lindex [dict get $user selectors] 0]
        assert_equal "%R~foo2 %W~bar2 ~baz2" [dict get $secondary_selector keys]
        assert_equal "&channel2" [dict get $secondary_selector channels]
        assert_equal "-@all +set" [dict get $secondary_selector commands]
    }
    """
    r.run(
        "ACL", "setuser", "selector-info", "-@all", "+get", "resetchannels", "&channel1", "%R~foo1", "%W~bar1", "~baz1"
    )
    r.run(
        "ACL",
        "setuser",
        "selector-info",
        "(-@all",
        "+set",
        "resetchannels",
        "&channel2",
        "%R~foo2",
        "%W~bar2",
        "~baz2)",
    )
    user = r.run("ACL", "GETUSER", "selector-info")
    assert "%R~foo1 %W~bar1 ~baz1" == user["keys"]
    assert "&channel1" == user["channels"]
    assert "-@all +get" == user["commands"]
    secondary_selector = user["selectors"][0]
    assert "%R~foo2 %W~bar2 ~baz2" == secondary_selector["keys"]
    assert "&channel2" == secondary_selector["channels"]
    assert "-@all +set" == secondary_selector["commands"]


def test_test_acl_getuser_response_with_database_permissions(r: ValkeyTestClient) -> None:
    """
    test {Test ACL GETUSER response with database permissions} {
        r ACL setuser db-getuser-test on nopass -@all +get ~* db=0,1,2
        set user [r ACL GETUSER "db-getuser-test"]

        assert_equal "db=0,1,2" [dict get $user databases]
        assert_equal "-@all +get" [dict get $user commands]

        r ACL setuser db-getuser-alldbs on nopass -@all +get ~* alldbs
        set user [r ACL GETUSER "db-getuser-alldbs"]
        assert_equal "alldbs" [dict get $user databases]

        r ACL setuser db-getuser-resetdbs on nopass -@all +get ~* resetdbs
        set user [r ACL GETUSER "db-getuser-resetdbs"]
        assert_equal "" [dict get $user databases]

        r ACL setuser db-getuser-selector on nopass db=0,1 -@all +get ~* (db=2,3 -@all +set ~*)
        set user [r ACL GETUSER "db-getuser-selector"]

        assert_equal "db=0,1" [dict get $user databases]

        set secondary_selector [lindex [dict get $user selectors] 0]
        assert_equal "db=2,3" [dict get $secondary_selector databases]
        assert_equal "-@all +set" [dict get $secondary_selector commands]

        r ACL setuser db-getuser-selector-alldbs on nopass db=0 -@all +get ~* (alldbs -@all +set ~*)
        set user [r ACL GETUSER "db-getuser-selector-alldbs"]

        assert_equal "db=0" [dict get $user databases]

        set secondary_selector [lindex [dict get $user selectors] 0]
        assert_equal "alldbs" [dict get $secondary_selector databases]

        r ACL setuser db-getuser-selector-reset on nopass db=0,1 -@all +get ~* (resetdbs -@all +set ~*)
        set user [r ACL GETUSER "db-getuser-selector-reset"]

        assert_equal "db=0,1" [dict get $user databases]

        set secondary_selector [lindex [dict get $user selectors] 0]
        assert_equal "" [dict get $secondary_selector databases]
    }
    """
    r.run("ACL", "setuser", "db-getuser-test", "on", "nopass", "-@all", "+get", "~*", "db=0,1,2")
    user = r.run("ACL", "GETUSER", "db-getuser-test")
    assert "db=0,1,2" == user["databases"]
    assert "-@all +get" == user["commands"]
    r.run("ACL", "setuser", "db-getuser-alldbs", "on", "nopass", "-@all", "+get", "~*", "alldbs")
    user = r.run("ACL", "GETUSER", "db-getuser-alldbs")
    assert "alldbs" == user["databases"]
    r.run("ACL", "setuser", "db-getuser-resetdbs", "on", "nopass", "-@all", "+get", "~*", "resetdbs")
    user = r.run("ACL", "GETUSER", "db-getuser-resetdbs")
    assert "" == user["databases"]
    r.run(
        "ACL",
        "setuser",
        "db-getuser-selector",
        "on",
        "nopass",
        "db=0,1",
        "-@all",
        "+get",
        "~*",
        "(db=2,3",
        "-@all",
        "+set",
        "~*)",
    )
    user = r.run("ACL", "GETUSER", "db-getuser-selector")
    assert "db=0,1" == user["databases"]
    secondary_selector = user["selectors"][0]
    assert "db=2,3" == secondary_selector["databases"]
    assert "-@all +set" == secondary_selector["commands"]
    r.run(
        "ACL",
        "setuser",
        "db-getuser-selector-alldbs",
        "on",
        "nopass",
        "db=0",
        "-@all",
        "+get",
        "~*",
        "(alldbs",
        "-@all",
        "+set",
        "~*)",
    )
    user = r.run("ACL", "GETUSER", "db-getuser-selector-alldbs")
    assert "db=0" == user["databases"]
    secondary_selector = user["selectors"][0]
    assert "alldbs" == secondary_selector["databases"]
    r.run(
        "ACL",
        "setuser",
        "db-getuser-selector-reset",
        "on",
        "nopass",
        "db=0,1",
        "-@all",
        "+get",
        "~*",
        "(resetdbs",
        "-@all",
        "+set",
        "~*)",
    )
    user = r.run("ACL", "GETUSER", "db-getuser-selector-reset")
    assert "db=0,1" == user["databases"]
    secondary_selector = user["selectors"][0]
    assert "" == secondary_selector["databases"]


def test_test_acl_list_idempotency(r: ValkeyTestClient) -> None:
    """
    test {Test ACL list idempotency} {
        r ACL SETUSER user-idempotency off -@all +get resetchannels &channel1 %R~foo1 %W~bar1 ~baz1 (-@all +set resetchannels &channel2 %R~foo2 %W~bar2 ~baz2)
        set response [lindex [r ACL LIST] [lsearch [r ACL LIST] "user user-idempotency*"]]

        assert_match "*-@all*+get*(*)*" $response
        assert_match "*resetchannels*&channel1*(*)*" $response
        assert_match "*%R~foo1*%W~bar1*~baz1*(*)*" $response

        assert_match "*(*-@all*+set*)*" $response
        assert_match "*(*resetchannels*&channel2*)*" $response
        assert_match "*(*%R~foo2*%W~bar2*~baz2*)*" $response
    }
    """
    r.run(
        "ACL",
        "SETUSER",
        "user-idempotency",
        "off",
        "-@all",
        "+get",
        "resetchannels",
        "&channel1",
        "%R~foo1",
        "%W~bar1",
        "~baz1",
        "(-@all",
        "+set",
        "resetchannels",
        "&channel2",
        "%R~foo2",
        "%W~bar2",
        "~baz2)",
    )
    response = r.run("ACL", "LIST")[lsearch(r.run("ACL", "LIST"), "user user-idempotency*")]
    assert fnmatch(str(response), "*-@all*+get*(*)*")
    assert fnmatch(str(response), "*resetchannels*&channel1*(*)*")
    assert fnmatch(str(response), "*%R~foo1*%W~bar1*~baz1*(*)*")
    assert fnmatch(str(response), "*(*-@all*+set*)*")
    assert fnmatch(str(response), "*(*resetchannels*&channel2*)*")
    assert fnmatch(str(response), "*(*%R~foo2*%W~bar2*~baz2*)*")


def test_test_r_w_is_the_same_as_all_permissions(r: ValkeyTestClient) -> None:
    """
    test {Test R+W is the same as all permissions} {
        r ACL setuser selector-rw-info %R~foo %W~foo %RW~bar
        set user [r ACL GETUSER selector-rw-info]
        assert_equal "~foo ~bar" [dict get $user keys]
    }
    """
    r.run("ACL", "setuser", "selector-rw-info", "%R~foo", "%W~foo", "%RW~bar")
    user = r.run("ACL", "GETUSER", "selector-rw-info")
    assert "~foo ~bar" == user["keys"]


def test_test_basic_dry_run_functionality(r: ValkeyTestClient) -> None:
    """
    test {Test basic dry run functionality} {
        r ACL setuser command-test +@all %R~read* %W~write* %RW~rw*
        assert_equal "OK" [r ACL DRYRUN command-test GET read]

        catch {r ACL DRYRUN not-a-user GET read} e
        assert_equal "ERR User 'not-a-user' not found" $e

        catch {r ACL DRYRUN command-test not-a-command read} e
        assert_equal "ERR Command 'not-a-command' not found" $e
    }
    """
    r.run("ACL", "setuser", "command-test", "+@all", "%R~read*", "%W~write*", "%RW~rw*")
    assert "OK" == r.run("ACL", "DRYRUN", "command-test", "GET", "read")
    e = None
    try:
        e = r.run("ACL", "DRYRUN", "not-a-user", "GET", "read")
    except Exception as _catch_err:
        e = str(_catch_err)
    assert "ERR User 'not-a-user' not found" == e
    e = None
    try:
        e = r.run("ACL", "DRYRUN", "command-test", "not-a-command", "read")
    except Exception as _catch_err:
        e = str(_catch_err)
    assert "ERR Command 'not-a-command' not found" == e


def test_test_various_commands_for_command_permissions(r: ValkeyTestClient) -> None:
    """
    test {Test various commands for command permissions} {
        r ACL setuser command-test -@all
        assert_match {*has no permissions to run the 'set' command*} [r ACL DRYRUN command-test set somekey somevalue]
        assert_match {*has no permissions to run the 'get' command*} [r ACL DRYRUN command-test get somekey]
    }
    """
    r.run("ACL", "setuser", "command-test", "-@all")
    assert fnmatch(
        str(r.run("ACL", "DRYRUN", "command-test", "set", "somekey", "somevalue")),
        "*has no permissions to run the 'set' command*",
    )
    assert fnmatch(
        str(r.run("ACL", "DRYRUN", "command-test", "get", "somekey")), "*has no permissions to run the 'get' command*"
    )


def test_test_various_odd_commands_for_key_permissions(r: ValkeyTestClient) -> None:
    """
    test {Test various odd commands for key permissions} {
        r ACL setuser command-test +@all %R~read* %W~write* %RW~rw*

        # Test migrate, which is marked with incomplete keys
        assert_equal "OK" [r ACL DRYRUN command-test MIGRATE whatever whatever rw 0 500]
        assert_match {*has no permissions to access the 'read' key*} [r ACL DRYRUN command-test MIGRATE whatever whatever read 0 500]
        assert_match {*has no permissions to access the 'write' key*} [r ACL DRYRUN command-test MIGRATE whatever whatever write 0 500]
        assert_equal "OK" [r ACL DRYRUN command-test MIGRATE whatever whatever "" 0 5000 KEYS rw]
        assert_match "*has no permissions to access the 'read' key" [r ACL DRYRUN command-test MIGRATE whatever whatever "" 0 5000 KEYS read]
        assert_match "*has no permissions to access the 'write' key" [r ACL DRYRUN command-test MIGRATE whatever whatever "" 0 5000 KEYS write]
        assert_equal "OK" [r ACL DRYRUN command-test MIGRATE whatever whatever "" 0 5000 AUTH KEYS KEYS rw]
        assert_match "*has no permissions to access the 'read' key" [r ACL DRYRUN command-test MIGRATE whatever whatever "" 0 5000 AUTH KEYS KEYS read]
        assert_match "*has no permissions to access the 'write' key" [r ACL DRYRUN command-test MIGRATE whatever whatever "" 0 5000 AUTH KEYS KEYS write]
        assert_equal "OK" [r ACL DRYRUN command-test MIGRATE whatever whatever "" 0 5000 AUTH2 KEYS 123 KEYS rw]
        assert_match "*has no permissions to access the 'read' key" [r ACL DRYRUN command-test MIGRATE whatever whatever "" 0 5000 AUTH2 KEYS 123 KEYS read]
        assert_match "*has no permissions to access the 'write' key" [r ACL DRYRUN command-test MIGRATE whatever whatever "" 0 5000 AUTH2 KEYS 123 KEYS write]
        assert_equal "OK" [r ACL DRYRUN command-test MIGRATE whatever whatever "" 0 5000 AUTH2 USER KEYS KEYS rw]
        assert_match "*has no permissions to access the 'read' key" [r ACL DRYRUN command-test MIGRATE whatever whatever "" 0 5000 AUTH2 USER KEYS KEYS read]
        assert_match "*has no permissions to access the 'write' key" [r ACL DRYRUN command-test MIGRATE whatever whatever "" 0 5000 AUTH2 USER KEYS KEYS write]

        # Test SORT, which is marked with incomplete keys
        assert_equal "OK" [r ACL DRYRUN command-test SORT read STORE write]
        assert_match {*has no permissions to access the 'read' key*}  [r ACL DRYRUN command-test SORT read STORE read]
        assert_match {*has no permissions to access the 'write' key*}  [r ACL DRYRUN command-test SORT write STORE write]

        # Test EVAL, which uses the numkey keyspec (Also test EVAL_RO)
        assert_equal "OK" [r ACL DRYRUN command-test EVAL "" 1 rw1]
        assert_match {*has no permissions to access the 'read' key*} [r ACL DRYRUN command-test EVAL "" 1 read]
        assert_equal "OK" [r ACL DRYRUN command-test EVAL_RO "" 1 rw1]
        assert_equal "OK" [r ACL DRYRUN command-test EVAL_RO "" 1 read]

        # Read is an optional argument and not a key here, make sure we don't treat it as a key
        assert_equal "OK" [r ACL DRYRUN command-test EVAL "" 0 read]

        # These are syntax errors, but it's 'OK' from an ACL perspective
        assert_equal "OK" [r ACL DRYRUN command-test EVAL "" -1 read]
        assert_equal "OK" [r ACL DRYRUN command-test EVAL "" 3 rw rw]
        assert_equal "OK" [r ACL DRYRUN command-test EVAL "" 3 rw read]

        # Test GEORADIUS which uses the last type of keyspec, keyword
        assert_equal "OK" [r ACL DRYRUN command-test GEORADIUS read longitude latitude radius M STOREDIST write]
        assert_equal "OK" [r ACL DRYRUN command-test GEORADIUS read longitude latitude radius M]
        assert_match {*has no permissions to access the 'read2' key*} [r ACL DRYRUN command-test GEORADIUS read1 longitude latitude radius M STOREDIST read2]
        assert_match {*has no permissions to access the 'write1' key*} [r ACL DRYRUN command-test GEORADIUS write1 longitude latitude radius M STOREDIST write2]
        assert_equal "OK" [r ACL DRYRUN command-test GEORADIUS read longitude latitude radius M STORE write]
        assert_equal "OK" [r ACL DRYRUN command-test GEORADIUS read longitude latitude radius M]
        assert_match {*has no permissions to access the 'read2' key*} [r ACL DRYRUN command-test GEORADIUS read1 longitude latitude radius M STORE read2]
        assert_match {*has no permissions to access the 'write1' key*} [r ACL DRYRUN command-test GEORADIUS write1 longitude latitude radius M STORE write2]
    }
    """
    r.run("ACL", "setuser", "command-test", "+@all", "%R~read*", "%W~write*", "%RW~rw*")
    assert "OK" == r.run("ACL", "DRYRUN", "command-test", "MIGRATE", "whatever", "whatever", "rw", 0, 500)
    assert fnmatch(
        str(r.run("ACL", "DRYRUN", "command-test", "MIGRATE", "whatever", "whatever", "read", 0, 500)),
        "*has no permissions to access the 'read' key*",
    )
    assert fnmatch(
        str(r.run("ACL", "DRYRUN", "command-test", "MIGRATE", "whatever", "whatever", "write", 0, 500)),
        "*has no permissions to access the 'write' key*",
    )
    assert "OK" == r.run("ACL", "DRYRUN", "command-test", "MIGRATE", "whatever", "whatever", "", 0, 5000, "KEYS", "rw")
    assert fnmatch(
        str(r.run("ACL", "DRYRUN", "command-test", "MIGRATE", "whatever", "whatever", "", 0, 5000, "KEYS", "read")),
        "*has no permissions to access the 'read' key",
    )
    assert fnmatch(
        str(r.run("ACL", "DRYRUN", "command-test", "MIGRATE", "whatever", "whatever", "", 0, 5000, "KEYS", "write")),
        "*has no permissions to access the 'write' key",
    )
    assert "OK" == r.run(
        "ACL", "DRYRUN", "command-test", "MIGRATE", "whatever", "whatever", "", 0, 5000, "AUTH", "KEYS", "KEYS", "rw"
    )
    assert fnmatch(
        str(
            r.run(
                "ACL",
                "DRYRUN",
                "command-test",
                "MIGRATE",
                "whatever",
                "whatever",
                "",
                0,
                5000,
                "AUTH",
                "KEYS",
                "KEYS",
                "read",
            )
        ),
        "*has no permissions to access the 'read' key",
    )
    assert fnmatch(
        str(
            r.run(
                "ACL",
                "DRYRUN",
                "command-test",
                "MIGRATE",
                "whatever",
                "whatever",
                "",
                0,
                5000,
                "AUTH",
                "KEYS",
                "KEYS",
                "write",
            )
        ),
        "*has no permissions to access the 'write' key",
    )
    assert "OK" == r.run(
        "ACL",
        "DRYRUN",
        "command-test",
        "MIGRATE",
        "whatever",
        "whatever",
        "",
        0,
        5000,
        "AUTH2",
        "KEYS",
        123,
        "KEYS",
        "rw",
    )
    assert fnmatch(
        str(
            r.run(
                "ACL",
                "DRYRUN",
                "command-test",
                "MIGRATE",
                "whatever",
                "whatever",
                "",
                0,
                5000,
                "AUTH2",
                "KEYS",
                123,
                "KEYS",
                "read",
            )
        ),
        "*has no permissions to access the 'read' key",
    )
    assert fnmatch(
        str(
            r.run(
                "ACL",
                "DRYRUN",
                "command-test",
                "MIGRATE",
                "whatever",
                "whatever",
                "",
                0,
                5000,
                "AUTH2",
                "KEYS",
                123,
                "KEYS",
                "write",
            )
        ),
        "*has no permissions to access the 'write' key",
    )
    assert "OK" == r.run(
        "ACL",
        "DRYRUN",
        "command-test",
        "MIGRATE",
        "whatever",
        "whatever",
        "",
        0,
        5000,
        "AUTH2",
        "USER",
        "KEYS",
        "KEYS",
        "rw",
    )
    assert fnmatch(
        str(
            r.run(
                "ACL",
                "DRYRUN",
                "command-test",
                "MIGRATE",
                "whatever",
                "whatever",
                "",
                0,
                5000,
                "AUTH2",
                "USER",
                "KEYS",
                "KEYS",
                "read",
            )
        ),
        "*has no permissions to access the 'read' key",
    )
    assert fnmatch(
        str(
            r.run(
                "ACL",
                "DRYRUN",
                "command-test",
                "MIGRATE",
                "whatever",
                "whatever",
                "",
                0,
                5000,
                "AUTH2",
                "USER",
                "KEYS",
                "KEYS",
                "write",
            )
        ),
        "*has no permissions to access the 'write' key",
    )
    assert "OK" == r.run("ACL", "DRYRUN", "command-test", "SORT", "read", "STORE", "write")
    assert fnmatch(
        str(r.run("ACL", "DRYRUN", "command-test", "SORT", "read", "STORE", "read")),
        "*has no permissions to access the 'read' key*",
    )
    assert fnmatch(
        str(r.run("ACL", "DRYRUN", "command-test", "SORT", "write", "STORE", "write")),
        "*has no permissions to access the 'write' key*",
    )
    assert "OK" == r.run("ACL", "DRYRUN", "command-test", "EVAL", "", 1, "rw1")
    assert fnmatch(
        str(r.run("ACL", "DRYRUN", "command-test", "EVAL", "", 1, "read")),
        "*has no permissions to access the 'read' key*",
    )
    assert "OK" == r.run("ACL", "DRYRUN", "command-test", "EVAL_RO", "", 1, "rw1")
    assert "OK" == r.run("ACL", "DRYRUN", "command-test", "EVAL_RO", "", 1, "read")
    assert "OK" == r.run("ACL", "DRYRUN", "command-test", "EVAL", "", 0, "read")
    assert "OK" == r.run("ACL", "DRYRUN", "command-test", "EVAL", "", -1, "read")
    assert "OK" == r.run("ACL", "DRYRUN", "command-test", "EVAL", "", 3, "rw", "rw")
    assert "OK" == r.run("ACL", "DRYRUN", "command-test", "EVAL", "", 3, "rw", "read")
    assert "OK" == r.run(
        "ACL",
        "DRYRUN",
        "command-test",
        "GEORADIUS",
        "read",
        "longitude",
        "latitude",
        "radius",
        "M",
        "STOREDIST",
        "write",
    )
    assert "OK" == r.run("ACL", "DRYRUN", "command-test", "GEORADIUS", "read", "longitude", "latitude", "radius", "M")
    assert fnmatch(
        str(
            r.run(
                "ACL",
                "DRYRUN",
                "command-test",
                "GEORADIUS",
                "read1",
                "longitude",
                "latitude",
                "radius",
                "M",
                "STOREDIST",
                "read2",
            )
        ),
        "*has no permissions to access the 'read2' key*",
    )
    assert fnmatch(
        str(
            r.run(
                "ACL",
                "DRYRUN",
                "command-test",
                "GEORADIUS",
                "write1",
                "longitude",
                "latitude",
                "radius",
                "M",
                "STOREDIST",
                "write2",
            )
        ),
        "*has no permissions to access the 'write1' key*",
    )
    assert "OK" == r.run(
        "ACL", "DRYRUN", "command-test", "GEORADIUS", "read", "longitude", "latitude", "radius", "M", "STORE", "write"
    )
    assert "OK" == r.run("ACL", "DRYRUN", "command-test", "GEORADIUS", "read", "longitude", "latitude", "radius", "M")
    assert fnmatch(
        str(
            r.run(
                "ACL",
                "DRYRUN",
                "command-test",
                "GEORADIUS",
                "read1",
                "longitude",
                "latitude",
                "radius",
                "M",
                "STORE",
                "read2",
            )
        ),
        "*has no permissions to access the 'read2' key*",
    )
    assert fnmatch(
        str(
            r.run(
                "ACL",
                "DRYRUN",
                "command-test",
                "GEORADIUS",
                "write1",
                "longitude",
                "latitude",
                "radius",
                "M",
                "STORE",
                "write2",
            )
        ),
        "*has no permissions to access the 'write1' key*",
    )


def test_existence_test_commands_are_not_marked_as_access(r: ValkeyTestClient) -> None:
    """
    test {Existence test commands are not marked as access} {
        assert_equal "OK" [r ACL DRYRUN command-test HEXISTS read foo]
        assert_equal "OK" [r ACL DRYRUN command-test HEXISTS write foo]
        assert_match {*has no permissions to access the 'nothing' key*} [r ACL DRYRUN command-test HEXISTS nothing foo]

        assert_equal "OK" [r ACL DRYRUN command-test HSTRLEN read foo]
        assert_equal "OK" [r ACL DRYRUN command-test HSTRLEN write foo]
        assert_match {*has no permissions to access the 'nothing' key*} [r ACL DRYRUN command-test HSTRLEN nothing foo]

        assert_equal "OK" [r ACL DRYRUN command-test SISMEMBER read foo]
        assert_equal "OK" [r ACL DRYRUN command-test SISMEMBER write foo]
        assert_match {*has no permissions to access the 'nothing' key*} [r ACL DRYRUN command-test SISMEMBER nothing foo]
    }
    """
    assert "OK" == r.run("ACL", "DRYRUN", "command-test", "HEXISTS", "read", "foo")
    assert "OK" == r.run("ACL", "DRYRUN", "command-test", "HEXISTS", "write", "foo")
    assert fnmatch(
        str(r.run("ACL", "DRYRUN", "command-test", "HEXISTS", "nothing", "foo")),
        "*has no permissions to access the 'nothing' key*",
    )
    assert "OK" == r.run("ACL", "DRYRUN", "command-test", "HSTRLEN", "read", "foo")
    assert "OK" == r.run("ACL", "DRYRUN", "command-test", "HSTRLEN", "write", "foo")
    assert fnmatch(
        str(r.run("ACL", "DRYRUN", "command-test", "HSTRLEN", "nothing", "foo")),
        "*has no permissions to access the 'nothing' key*",
    )
    assert "OK" == r.run("ACL", "DRYRUN", "command-test", "SISMEMBER", "read", "foo")
    assert "OK" == r.run("ACL", "DRYRUN", "command-test", "SISMEMBER", "write", "foo")
    assert fnmatch(
        str(r.run("ACL", "DRYRUN", "command-test", "SISMEMBER", "nothing", "foo")),
        "*has no permissions to access the 'nothing' key*",
    )


def test_intersection_cardinaltiy_commands_are_access_commands(r: ValkeyTestClient) -> None:
    """
    test {Intersection cardinaltiy commands are access commands} {
        assert_equal "OK" [r ACL DRYRUN command-test SINTERCARD 2 read read]
        assert_match {*has no permissions to access the 'write' key*} [r ACL DRYRUN command-test SINTERCARD 2 write read]
        assert_match {*has no permissions to access the 'nothing' key*} [r ACL DRYRUN command-test SINTERCARD 2 nothing read]

        assert_equal "OK" [r ACL DRYRUN command-test ZCOUNT read 0 1]
        assert_match {*has no permissions to access the 'write' key*} [r ACL DRYRUN command-test ZCOUNT write 0 1]
        assert_match {*has no permissions to access the 'nothing' key*} [r ACL DRYRUN command-test ZCOUNT nothing 0 1]

        assert_equal "OK" [r ACL DRYRUN command-test PFCOUNT read read]
        assert_match {*has no permissions to access the 'write' key*} [r ACL DRYRUN command-test PFCOUNT write read]
        assert_match {*has no permissions to access the 'nothing' key*} [r ACL DRYRUN command-test PFCOUNT nothing read]

        assert_equal "OK" [r ACL DRYRUN command-test ZINTERCARD 2 read read]
        assert_match {*has no permissions to access the 'write' key*} [r ACL DRYRUN command-test ZINTERCARD 2 write read]
        assert_match {*has no permissions to access the 'nothing' key*} [r ACL DRYRUN command-test ZINTERCARD 2 nothing read]
    }
    """
    assert "OK" == r.run("ACL", "DRYRUN", "command-test", "SINTERCARD", 2, "read", "read")
    assert fnmatch(
        str(r.run("ACL", "DRYRUN", "command-test", "SINTERCARD", 2, "write", "read")),
        "*has no permissions to access the 'write' key*",
    )
    assert fnmatch(
        str(r.run("ACL", "DRYRUN", "command-test", "SINTERCARD", 2, "nothing", "read")),
        "*has no permissions to access the 'nothing' key*",
    )
    assert "OK" == r.run("ACL", "DRYRUN", "command-test", "ZCOUNT", "read", 0, 1)
    assert fnmatch(
        str(r.run("ACL", "DRYRUN", "command-test", "ZCOUNT", "write", 0, 1)),
        "*has no permissions to access the 'write' key*",
    )
    assert fnmatch(
        str(r.run("ACL", "DRYRUN", "command-test", "ZCOUNT", "nothing", 0, 1)),
        "*has no permissions to access the 'nothing' key*",
    )
    assert "OK" == r.run("ACL", "DRYRUN", "command-test", "PFCOUNT", "read", "read")
    assert fnmatch(
        str(r.run("ACL", "DRYRUN", "command-test", "PFCOUNT", "write", "read")),
        "*has no permissions to access the 'write' key*",
    )
    assert fnmatch(
        str(r.run("ACL", "DRYRUN", "command-test", "PFCOUNT", "nothing", "read")),
        "*has no permissions to access the 'nothing' key*",
    )
    assert "OK" == r.run("ACL", "DRYRUN", "command-test", "ZINTERCARD", 2, "read", "read")
    assert fnmatch(
        str(r.run("ACL", "DRYRUN", "command-test", "ZINTERCARD", 2, "write", "read")),
        "*has no permissions to access the 'write' key*",
    )
    assert fnmatch(
        str(r.run("ACL", "DRYRUN", "command-test", "ZINTERCARD", 2, "nothing", "read")),
        "*has no permissions to access the 'nothing' key*",
    )


def test_test_general_keyspace_commands_require_some_type_of_permission_to_execute(r: ValkeyTestClient) -> None:
    """
    test {Test general keyspace commands require some type of permission to execute} {
        assert_equal "OK" [r ACL DRYRUN command-test touch read]
        assert_equal "OK" [r ACL DRYRUN command-test touch write]
        assert_equal "OK" [r ACL DRYRUN command-test touch rw]
        assert_match {*has no permissions to access the 'nothing' key*} [r ACL DRYRUN command-test touch nothing]

        assert_equal "OK" [r ACL DRYRUN command-test exists read]
        assert_equal "OK" [r ACL DRYRUN command-test exists write]
        assert_equal "OK" [r ACL DRYRUN command-test exists rw]
        assert_match {*has no permissions to access the 'nothing' key*} [r ACL DRYRUN command-test exists nothing]

        assert_equal "OK" [r ACL DRYRUN command-test MEMORY USAGE read]
        assert_equal "OK" [r ACL DRYRUN command-test MEMORY USAGE write]
        assert_equal "OK" [r ACL DRYRUN command-test MEMORY USAGE rw]
        assert_match {*has no permissions to access the 'nothing' key*} [r ACL DRYRUN command-test MEMORY USAGE nothing]

        assert_equal "OK" [r ACL DRYRUN command-test TYPE read]
        assert_equal "OK" [r ACL DRYRUN command-test TYPE write]
        assert_equal "OK" [r ACL DRYRUN command-test TYPE rw]
        assert_match {*has no permissions to access the 'nothing' key*} [r ACL DRYRUN command-test TYPE nothing]
    }
    """
    assert "OK" == r.run("ACL", "DRYRUN", "command-test", "touch", "read")
    assert "OK" == r.run("ACL", "DRYRUN", "command-test", "touch", "write")
    assert "OK" == r.run("ACL", "DRYRUN", "command-test", "touch", "rw")
    assert fnmatch(
        str(r.run("ACL", "DRYRUN", "command-test", "touch", "nothing")),
        "*has no permissions to access the 'nothing' key*",
    )
    assert "OK" == r.run("ACL", "DRYRUN", "command-test", "exists", "read")
    assert "OK" == r.run("ACL", "DRYRUN", "command-test", "exists", "write")
    assert "OK" == r.run("ACL", "DRYRUN", "command-test", "exists", "rw")
    assert fnmatch(
        str(r.run("ACL", "DRYRUN", "command-test", "exists", "nothing")),
        "*has no permissions to access the 'nothing' key*",
    )
    assert "OK" == r.run("ACL", "DRYRUN", "command-test", "MEMORY", "USAGE", "read")
    assert "OK" == r.run("ACL", "DRYRUN", "command-test", "MEMORY", "USAGE", "write")
    assert "OK" == r.run("ACL", "DRYRUN", "command-test", "MEMORY", "USAGE", "rw")
    assert fnmatch(
        str(r.run("ACL", "DRYRUN", "command-test", "MEMORY", "USAGE", "nothing")),
        "*has no permissions to access the 'nothing' key*",
    )
    assert "OK" == r.run("ACL", "DRYRUN", "command-test", "TYPE", "read")
    assert "OK" == r.run("ACL", "DRYRUN", "command-test", "TYPE", "write")
    assert "OK" == r.run("ACL", "DRYRUN", "command-test", "TYPE", "rw")
    assert fnmatch(
        str(r.run("ACL", "DRYRUN", "command-test", "TYPE", "nothing")),
        "*has no permissions to access the 'nothing' key*",
    )


def test_cardinality_commands_require_some_type_of_permission_to_execute(r: ValkeyTestClient) -> None:
    """
    test {Cardinality commands require some type of permission to execute} {
        set commands {STRLEN HLEN LLEN SCARD ZCARD XLEN}
        foreach command $commands {
            assert_equal "OK" [r ACL DRYRUN command-test $command read]
            assert_equal "OK" [r ACL DRYRUN command-test $command write]
            assert_equal "OK" [r ACL DRYRUN command-test $command rw]
            assert_match {*has no permissions to access the 'nothing' key*} [r ACL DRYRUN command-test $command nothing]
        }
    }
    """
    commands = "STRLEN HLEN LLEN SCARD ZCARD XLEN"
    foreach(
        "command",
        commands,
        '            assert_equal "OK" [r ACL DRYRUN command-test $command read]\n            assert_equal "OK" [r ACL DRYRUN command-test $command write]\n            assert_equal "OK" [r ACL DRYRUN command-test $command rw]\n            assert_match {*has no permissions to access the \'nothing\' key*} [r ACL DRYRUN command-test $command nothing]\n        ',
    )


def test_test_sharded_channel_permissions(r: ValkeyTestClient) -> None:
    """
    test {Test sharded channel permissions} {
        r ACL setuser test-channels +@all resetchannels &channel
        assert_equal "OK" [r ACL DRYRUN test-channels spublish channel foo]
        assert_equal "OK" [r ACL DRYRUN test-channels ssubscribe channel]
        assert_equal "OK" [r ACL DRYRUN test-channels sunsubscribe]
        assert_equal "OK" [r ACL DRYRUN test-channels sunsubscribe channel]
        assert_equal "OK" [r ACL DRYRUN test-channels sunsubscribe otherchannel]

        assert_match {*has no permissions to access the 'otherchannel' channel*} [r ACL DRYRUN test-channels spublish otherchannel foo]
        assert_match {*has no permissions to access the 'otherchannel' channel*} [r ACL DRYRUN test-channels ssubscribe otherchannel foo]
    }
    """
    r.run("ACL", "setuser", "test-channels", "+@all", "resetchannels", "&channel")
    assert "OK" == r.run("ACL", "DRYRUN", "test-channels", "spublish", "channel", "foo")
    assert "OK" == r.run("ACL", "DRYRUN", "test-channels", "ssubscribe", "channel")
    assert "OK" == r.run("ACL", "DRYRUN", "test-channels", "sunsubscribe")
    assert "OK" == r.run("ACL", "DRYRUN", "test-channels", "sunsubscribe", "channel")
    assert "OK" == r.run("ACL", "DRYRUN", "test-channels", "sunsubscribe", "otherchannel")
    assert fnmatch(
        str(r.run("ACL", "DRYRUN", "test-channels", "spublish", "otherchannel", "foo")),
        "*has no permissions to access the 'otherchannel' channel*",
    )
    assert fnmatch(
        str(r.run("ACL", "DRYRUN", "test-channels", "ssubscribe", "otherchannel", "foo")),
        "*has no permissions to access the 'otherchannel' channel*",
    )


def test_test_sort_with_acl_permissions(r: ValkeyTestClient, r2) -> None:
    """
    test {Test sort with ACL permissions} {
        r set v1 1
        r lpush mylist 1

        r ACL setuser test-sort-acl on nopass (+sort ~mylist)
        $r2 auth test-sort-acl nopass

        catch {$r2 sort mylist by v*} e
        assert_equal "ERR BY option of SORT denied due to insufficient ACL permissions." $e
        catch {$r2 sort mylist get v*} e
        assert_equal "ERR GET option of SORT denied due to insufficient ACL permissions." $e

        r ACL setuser test-sort-acl (+sort ~mylist ~v*)
        catch {$r2 sort mylist by v*} e
        assert_equal "ERR BY option of SORT denied due to insufficient ACL permissions." $e
        catch {$r2 sort mylist get v*} e
        assert_equal "ERR GET option of SORT denied due to insufficient ACL permissions." $e

        r ACL setuser test-sort-acl (+sort ~mylist %W~*)
        catch {$r2 sort mylist by v*} e
        assert_equal "ERR BY option of SORT denied due to insufficient ACL permissions." $e
        catch {$r2 sort mylist get v*} e
        assert_equal "ERR GET option of SORT denied due to insufficient ACL permissions." $e

        r ACL setuser test-sort-acl (+sort ~mylist %R~*)
        assert_equal "1" [$r2 sort mylist by v*]

        # cleanup
        r ACL deluser test-sort-acl
        r del v1 mylist
    }
    """
    r.run("set", "v1", 1)
    r.run("lpush", "mylist", 1)
    r.run("ACL", "setuser", "test-sort-acl", "on", "nopass", "(+sort", "~mylist)")
    r2.run("auth", "test-sort-acl", "nopass")
    e = None
    try:
        e = r2.run("sort", "mylist", "by", "v*")
    except Exception as _catch_err:
        e = str(_catch_err)
    assert "ERR BY option of SORT denied due to insufficient ACL permissions." == e
    e = None
    try:
        e = r2.run("sort", "mylist", "get", "v*")
    except Exception as _catch_err:
        e = str(_catch_err)
    assert "ERR GET option of SORT denied due to insufficient ACL permissions." == e
    r.run("ACL", "setuser", "test-sort-acl", "(+sort", "~mylist", "~v*)")
    e = None
    try:
        e = r2.run("sort", "mylist", "by", "v*")
    except Exception as _catch_err:
        e = str(_catch_err)
    assert "ERR BY option of SORT denied due to insufficient ACL permissions." == e
    e = None
    try:
        e = r2.run("sort", "mylist", "get", "v*")
    except Exception as _catch_err:
        e = str(_catch_err)
    assert "ERR GET option of SORT denied due to insufficient ACL permissions." == e
    r.run("ACL", "setuser", "test-sort-acl", "(+sort", "~mylist", "%W~*)")
    e = None
    try:
        e = r2.run("sort", "mylist", "by", "v*")
    except Exception as _catch_err:
        e = str(_catch_err)
    assert "ERR BY option of SORT denied due to insufficient ACL permissions." == e
    e = None
    try:
        e = r2.run("sort", "mylist", "get", "v*")
    except Exception as _catch_err:
        e = str(_catch_err)
    assert "ERR GET option of SORT denied due to insufficient ACL permissions." == e
    r.run("ACL", "setuser", "test-sort-acl", "(+sort", "~mylist", "%R~*)")
    assert "1" == r2.run("sort", "mylist", "by", "v*")
    r.run("ACL", "deluser", "test-sort-acl")
    r.run("del", "v1", "mylist")


def test_test_dryrun_with_wrong_number_of_arguments(r: ValkeyTestClient) -> None:
    """
    test {Test DRYRUN with wrong number of arguments} {
        r ACL setuser test-dry-run +@all ~v*

        assert_equal "OK" [r ACL DRYRUN test-dry-run SET v v]

        catch {r ACL DRYRUN test-dry-run SET v} e
        assert_equal "ERR wrong number of arguments for 'set' command" $e

        catch {r ACL DRYRUN test-dry-run SET} e
        assert_equal "ERR wrong number of arguments for 'set' command" $e
    }
    """
    r.run("ACL", "setuser", "test-dry-run", "+@all", "~v*")
    assert "OK" == r.run("ACL", "DRYRUN", "test-dry-run", "SET", "v", "v")
    e = None
    try:
        e = r.run("ACL", "DRYRUN", "test-dry-run", "SET", "v")
    except Exception as _catch_err:
        e = str(_catch_err)
    assert "ERR wrong number of arguments for 'set' command" == e
    e = None
    try:
        e = r.run("ACL", "DRYRUN", "test-dry-run", "SET")
    except Exception as _catch_err:
        e = str(_catch_err)
    assert "ERR wrong number of arguments for 'set' command" == e


"""
$r2 close
"""


"""
set server_path tmpdir "selectors.acl"
"""


"""
exec cp -f tests/assets/userwithselectors.acl server_path
"""


"""
exec cp -f tests/assets/default.conf server_path
"""


def test_test_behavior_of_loading_acls(r: ValkeyTestClient) -> None:
    """
    test {Test behavior of loading ACLs} {
        set selectors [dict get [r ACL getuser alice] selectors]
        assert_equal [llength $selectors] 1
        set test_selector [lindex $selectors 0]
        assert_equal "-@all +get" [dict get $test_selector "commands"]
        assert_equal "~rw*" [dict get $test_selector "keys"]

        set selectors [dict get [r ACL getuser bob] selectors]
        assert_equal [llength $selectors] 2
        set test_selector [lindex $selectors 0]
        assert_equal "-@all +set" [dict get $test_selector "commands"]
        assert_equal "%W~w*" [dict get $test_selector "keys"]

        set test_selector [lindex $selectors 1]
        assert_equal "-@all +get" [dict get $test_selector "commands"]
        assert_equal "%R~r*" [dict get $test_selector "keys"]
    }
    """
    selectors = r.run("ACL", "getuser", "alice")["selectors"]
    assert len(selectors) == 1
    test_selector = selectors[0]
    assert "-@all +get" == test_selector["commands"]
    assert "~rw*" == test_selector["keys"]
    selectors = r.run("ACL", "getuser", "bob")["selectors"]
    assert len(selectors) == 2
    test_selector = selectors[0]
    assert "-@all +set" == test_selector["commands"]
    assert "%W~w*" == test_selector["keys"]
    test_selector = selectors[1]
    assert "-@all +get" == test_selector["commands"]
    assert "%R~r*" == test_selector["keys"]


pytestmark = [pytest.mark.acl_external_skip]


"""
set r2 valkey_client
"""


def test_test_basic_database_level_acl_functionality(r: ValkeyTestClient, r2) -> None:
    """
    test {Test basic database-level ACL functionality} {
        r ACL SETUSER db-user on +@all nopass ~* db=0,1
        $r2 auth db-user password

        assert_equal "OK" [$r2 select 0]
        assert_equal "OK" [$r2 set key1 value1]

        assert_equal "OK" [$r2 select 1]
        assert_equal "OK" [$r2 set key2 value2]

        catch {$r2 select 2} err
        assert_match "*NOPERM*database*" $err
    }
    """
    r.run("ACL", "SETUSER", "db-user", "on", "+@all", "nopass", "~*", "db=0,1")
    r2.run("auth", "db-user", "password")
    assert "OK" == r2.run("select", 0)
    assert "OK" == r2.run("set", "key1", "value1")
    assert "OK" == r2.run("select", 1)
    assert "OK" == r2.run("set", "key2", "value2")
    err = None
    try:
        err = r2.run("select", 2)
    except Exception as _catch_err:
        err = str(_catch_err)
    assert fnmatch(str(err), "*NOPERM*database*")


def test_test_database_permissions_with_selectors(r: ValkeyTestClient, r2) -> None:
    """
    test {Test database permissions with selectors} {
        r ACL SETUSER db-selector on nopass (db=0,1 +@all -@read ~write*) (db=2,3 +@all -@write ~read*)
        $r2 auth db-selector password

        assert_equal "OK" [$r2 select 0]
        assert_equal "OK" [$r2 set writekey value]
        catch {$r2 get writekey} err
        assert_match "*NOPERM*command*" $err

        assert_equal "OK" [$r2 select 1]
        assert_equal "OK" [$r2 set writekey value]

        assert_equal "OK" [$r2 select 2]
        catch {$r2 set write:key value} err
        assert_match "*NOPERM*command*" $err
        r select 2
        r set readstr bar
        assert_equal [$r2 get readstr] bar

        assert_equal "OK" [$r2 select 3]
        r select 3
        r set readstr bar
        assert_equal [$r2 get readstr] bar

        catch {$r2 select 4} err
        assert_match "*NOPERM*command*" $err
    }
    """
    r.run(
        "ACL",
        "SETUSER",
        "db-selector",
        "on",
        "nopass",
        "(db=0,1",
        "+@all",
        "-@read",
        "~write*)",
        "(db=2,3",
        "+@all",
        "-@write",
        "~read*)",
    )
    r2.run("auth", "db-selector", "password")
    assert "OK" == r2.run("select", 0)
    assert "OK" == r2.run("set", "writekey", "value")
    err = None
    try:
        err = r2.run("get", "writekey")
    except Exception as _catch_err:
        err = str(_catch_err)
    assert fnmatch(str(err), "*NOPERM*command*")
    assert "OK" == r2.run("select", 1)
    assert "OK" == r2.run("set", "writekey", "value")
    assert "OK" == r2.run("select", 2)
    err = None
    try:
        err = r2.run("set", "write:key", "value")
    except Exception as _catch_err:
        err = str(_catch_err)
    assert fnmatch(str(err), "*NOPERM*command*")
    r.run("select", 2)
    r.run("set", "readstr", "bar")
    assert r2.run("get", "readstr") == "bar"
    assert "OK" == r2.run("select", 3)
    r.run("select", 3)
    r.run("set", "readstr", "bar")
    assert r2.run("get", "readstr") == "bar"
    err = None
    try:
        err = r2.run("select", 4)
    except Exception as _catch_err:
        err = str(_catch_err)
    assert fnmatch(str(err), "*NOPERM*command*")


def test_test_alldbs_and_resetdbs_commands(r: ValkeyTestClient, r2) -> None:
    """
    test {Test alldbs and resetdbs commands} {
        r ACL SETUSER db-reset-user on +@all ~* nopass db=0
        $r2 auth db-reset-user password

        assert_equal "OK" [$r2 select 0]
        catch {$r2 select 1} err
        assert_match "*NOPERM*database*" $err

        r ACL SETUSER db-reset-user resetdbs

        catch {$r2 select 0} err
        assert_match "*NOPERM*database*" $err
        catch {$r2 select 1} err
        assert_match "*NOPERM*database*" $err
        catch {$r2 select 2} err
        assert_match "*NOPERM*database*" $err

        r ACL SETUSER db-reset-user alldbs

        assert_equal "OK" [$r2 select 0]
        assert_equal "OK" [$r2 select 1]
    }
    """
    r.run("ACL", "SETUSER", "db-reset-user", "on", "+@all", "~*", "nopass", "db=0")
    r2.run("auth", "db-reset-user", "password")
    assert "OK" == r2.run("select", 0)
    err = None
    try:
        err = r2.run("select", 1)
    except Exception as _catch_err:
        err = str(_catch_err)
    assert fnmatch(str(err), "*NOPERM*database*")
    r.run("ACL", "SETUSER", "db-reset-user", "resetdbs")
    err = None
    try:
        err = r2.run("select", 0)
    except Exception as _catch_err:
        err = str(_catch_err)
    assert fnmatch(str(err), "*NOPERM*database*")
    err = None
    try:
        err = r2.run("select", 1)
    except Exception as _catch_err:
        err = str(_catch_err)
    assert fnmatch(str(err), "*NOPERM*database*")
    err = None
    try:
        err = r2.run("select", 2)
    except Exception as _catch_err:
        err = str(_catch_err)
    assert fnmatch(str(err), "*NOPERM*database*")
    r.run("ACL", "SETUSER", "db-reset-user", "alldbs")
    assert "OK" == r2.run("select", 0)
    assert "OK" == r2.run("select", 1)


def test_test_transaction_with_database_switching(r: ValkeyTestClient, r2) -> None:
    """
    test {Test transaction with database switching} {
        r ACL SETUSER db-tx-user on nopass (db=0,1 +@all -@read ~*) (db=2,3 +@all -@write ~*)
        $r2 auth db-tx-user password

        assert_equal "OK" [$r2 select 0]
        assert_equal "OK" [$r2 multi]
        assert_equal "QUEUED" [$r2 set key1 value1]
        assert_equal "QUEUED" [$r2 select 2]
        assert_equal "QUEUED" [$r2 get key2]
        assert_equal "QUEUED" [$r2 select 0]
        assert_equal "QUEUED" [$r2 set key3 value3]

        set result [$r2 exec]
        assert_equal 5 [llength $result]

        assert_equal "OK" [$r2 select 0]
        assert_equal "OK" [$r2 multi]
        assert_equal "QUEUED" [$r2 set key1 value1]
        catch {$r2 select 4} err
        assert_match "*NOPERM*command*" $err

        catch {$r2 exec} err
        assert_match "*EXECABORT*" $err
    }
    """
    r.run(
        "ACL",
        "SETUSER",
        "db-tx-user",
        "on",
        "nopass",
        "(db=0,1",
        "+@all",
        "-@read",
        "~*)",
        "(db=2,3",
        "+@all",
        "-@write",
        "~*)",
    )
    r2.run("auth", "db-tx-user", "password")
    assert "OK" == r2.run("select", 0)
    assert "OK" == r2.run("multi")
    assert "QUEUED" == r2.run("set", "key1", "value1")
    assert "QUEUED" == r2.run("select", 2)
    assert "QUEUED" == r2.run("get", "key2")
    assert "QUEUED" == r2.run("select", 0)
    assert "QUEUED" == r2.run("set", "key3", "value3")
    result = r2.run("exec")
    assert 5 == len(result)
    assert "OK" == r2.run("select", 0)
    assert "OK" == r2.run("multi")
    assert "QUEUED" == r2.run("set", "key1", "value1")
    err = None
    try:
        err = r2.run("select", 4)
    except Exception as _catch_err:
        err = str(_catch_err)
    assert fnmatch(str(err), "*NOPERM*command*")
    err = None
    try:
        err = r2.run("exec")
    except Exception as _catch_err:
        err = str(_catch_err)
    assert fnmatch(str(err), "*EXECABORT*")


def test_test_transaction_with_command_permissions_in_different_dbs(r: ValkeyTestClient, r2) -> None:
    """
    test {Test transaction with command permissions in different DBs} {
        r ACL SETUSER db-cmd-user on nopass (db=0,1 +@all -@read ~*) (db=2,3 +@all -@write ~*)
        $r2 auth db-cmd-user password

        assert_equal "OK" [$r2 select 0]
        catch {$r2 get key} err
        assert_match "*NOPERM*command*" $err

        assert_equal "OK" [$r2 select 2]
        catch {$r2 set key value} err
        assert_match "*NOPERM*command*" $err

        assert_equal "OK" [$r2 select 0]
        assert_equal "OK" [$r2 multi]
        assert_equal "QUEUED" [$r2 set key1 value1]
        assert_equal "QUEUED" [$r2 select 2]
        assert_equal "QUEUED" [$r2 get key2]


        set result [$r2 exec]
        assert_equal 3 [llength $result]
    }
    """
    r.run(
        "ACL",
        "SETUSER",
        "db-cmd-user",
        "on",
        "nopass",
        "(db=0,1",
        "+@all",
        "-@read",
        "~*)",
        "(db=2,3",
        "+@all",
        "-@write",
        "~*)",
    )
    r2.run("auth", "db-cmd-user", "password")
    assert "OK" == r2.run("select", 0)
    err = None
    try:
        err = r2.run("get", "key")
    except Exception as _catch_err:
        err = str(_catch_err)
    assert fnmatch(str(err), "*NOPERM*command*")
    assert "OK" == r2.run("select", 2)
    err = None
    try:
        err = r2.run("set", "key", "value")
    except Exception as _catch_err:
        err = str(_catch_err)
    assert fnmatch(str(err), "*NOPERM*command*")
    assert "OK" == r2.run("select", 0)
    assert "OK" == r2.run("multi")
    assert "QUEUED" == r2.run("set", "key1", "value1")
    assert "QUEUED" == r2.run("select", 2)
    assert "QUEUED" == r2.run("get", "key2")
    result = r2.run("exec")
    assert 3 == len(result)


def test_test_database_acl_with_string_representation(r: ValkeyTestClient) -> None:
    """
    test {Test database ACL with string representation} {
        r ACL SETUSER db-string-user on +@all nopass ~* db=0,1

        set acl_str [r ACL LIST]
        set user_line [lsearch -inline $acl_str "user db-string-user*"]

        assert_match "*db=0,1*" $user_line
    }
    """
    r.run("ACL", "SETUSER", "db-string-user", "on", "+@all", "nopass", "~*", "db=0,1")
    acl_str = r.run("ACL", "LIST")
    user_line = lsearch("-inline", acl_str, "user db-string-user*")
    assert fnmatch(str(user_line), "*db=0,1*")


def test_test_edge_cases_with_database_ids_check_new_errmsg(r: ValkeyTestClient) -> None:
    """
    test {Test edge cases with database IDs, check new errmsg} {
        catch {r ACL SETUSER db-edge-user db=-1} err
        assert_match "*Error in ACL SETUSER modifier 'db=-1': The provided database ID is out of range*" $err

        catch {r ACL SETUSER db-edge-user db=abc} err
        assert_match "*Error in ACL SETUSER modifier 'db=abc': Syntax error*" $err

        catch {r ACL SETUSER db-edge-user db=12345678987654321} err
        assert_match "*Error in ACL SETUSER modifier 'db=12345678987654321': The provided database ID is out of range*" $err

        catch {r ACL SETUSER db-edge-user db=non-numeric1,non-numeric2} err
        assert_match "*Error in ACL SETUSER modifier 'db=non-numeric1,non-numeric2': Syntax error*" $err

        set acl_list [r ACL LIST]
        set user_line [lsearch -inline $acl_list "user db-edge-user*"]
        assert_equal "" $user_line
    }
    """
    err = None
    try:
        err = r.run("ACL", "SETUSER", "db-edge-user", "db=-1")
    except Exception as _catch_err:
        err = str(_catch_err)
    assert fnmatch(str(err), "*Error in ACL SETUSER modifier 'db=-1': The provided database ID is out of range*")
    err = None
    try:
        err = r.run("ACL", "SETUSER", "db-edge-user", "db=abc")
    except Exception as _catch_err:
        err = str(_catch_err)
    assert fnmatch(str(err), "*Error in ACL SETUSER modifier 'db=abc': Syntax error*")
    err = None
    try:
        err = r.run("ACL", "SETUSER", "db-edge-user", "db=12345678987654321")
    except Exception as _catch_err:
        err = str(_catch_err)
    assert fnmatch(
        str(err), "*Error in ACL SETUSER modifier 'db=12345678987654321': The provided database ID is out of range*"
    )
    err = None
    try:
        err = r.run("ACL", "SETUSER", "db-edge-user", "db=non-numeric1,non-numeric2")
    except Exception as _catch_err:
        err = str(_catch_err)
    assert fnmatch(str(err), "*Error in ACL SETUSER modifier 'db=non-numeric1,non-numeric2': Syntax error*")
    acl_list = r.run("ACL", "LIST")
    user_line = lsearch("-inline", acl_list, "user db-edge-user*")
    assert "" == user_line


def test_test_default_behavior_without_db_restrictions(r: ValkeyTestClient, r2) -> None:
    """
    test {Test default behavior without db restrictions} {
        r ACL SETUSER db-compat-user on >password +@all
        $r2 auth db-compat-user password

        assert_equal "OK" [$r2 select 0]
        assert_equal "OK" [$r2 select 1]
        assert_equal "OK" [$r2 select 2]
        assert_equal "OK" [$r2 select 3]

        r ACL SETUSER db-compat-user2 on >password +@all db=0
        r ACL SETUSER db-compat-user2 reset
        r ACL SETUSER db-compat-user2 on >password +@all
        $r2 auth db-compat-user2 password

        assert_equal "OK" [$r2 select 0]
        assert_equal "OK" [$r2 select 1]
        assert_equal "OK" [$r2 select 2]
        assert_equal "OK" [$r2 select 3]
    }
    """
    r.run("ACL", "SETUSER", "db-compat-user", "on", ">password", "+@all")
    r2.run("auth", "db-compat-user", "password")
    assert "OK" == r2.run("select", 0)
    assert "OK" == r2.run("select", 1)
    assert "OK" == r2.run("select", 2)
    assert "OK" == r2.run("select", 3)
    r.run("ACL", "SETUSER", "db-compat-user2", "on", ">password", "+@all", "db=0")
    r.run("ACL", "SETUSER", "db-compat-user2", "reset")
    r.run("ACL", "SETUSER", "db-compat-user2", "on", ">password", "+@all")
    r2.run("auth", "db-compat-user2", "password")
    assert "OK" == r2.run("select", 0)
    assert "OK" == r2.run("select", 1)
    assert "OK" == r2.run("select", 2)
    assert "OK" == r2.run("select", 3)


def test_test_flushall_with_database_permissions(r: ValkeyTestClient, r2) -> None:
    """
    test {Test FLUSHALL with database permissions} {
        r ACL SETUSER flushall-user on nopass +@all ~* db=0
        $r2 auth flushall-user password
        $r2 select 0
        $r2 set key value

        catch {$r2 flushall} e
        assert_match "*NOPERM*database*" $e

        assert_equal "OK" [$r2 flushdb]
    }
    """
    r.run("ACL", "SETUSER", "flushall-user", "on", "nopass", "+@all", "~*", "db=0")
    r2.run("auth", "flushall-user", "password")
    r2.run("select", 0)
    r2.run("set", "key", "value")
    e = None
    try:
        e = r2.run("flushall")
    except Exception as _catch_err:
        e = str(_catch_err)
    assert fnmatch(str(e), "*NOPERM*database*")
    assert "OK" == r2.run("flushdb")


def test_test_swapdb_with_database_permissions(r: ValkeyTestClient, r2) -> None:
    """
    test {Test SWAPDB with database permissions} {
        r ACL SETUSER swapdb-user on nopass +@all ~* db=0,1
        $r2 auth swapdb-user password

        assert_equal "OK" [$r2 swapdb 0 1]

        catch {$r2 swapdb 0 2} e
        assert_match "*NOPERM*database*" $e
    }
    """
    r.run("ACL", "SETUSER", "swapdb-user", "on", "nopass", "+@all", "~*", "db=0,1")
    r2.run("auth", "swapdb-user", "password")
    assert "OK" == r2.run("swapdb", 0, 1)
    e = None
    try:
        e = r2.run("swapdb", 0, 2)
    except Exception as _catch_err:
        e = str(_catch_err)
    assert fnmatch(str(e), "*NOPERM*database*")


def test_test_move_with_database_permissions(r: ValkeyTestClient, r2) -> None:
    """
    test {Test MOVE with database permissions} {
        r ACL SETUSER move-user on nopass +move +set ~* db=0,1
        $r2 auth move-user password
        $r2 set move-key value
        assert_equal "1" [$r2 move move-key 1]

        catch {$r2 move move-key 2} e
        assert_match "*NOPERM*database*" $e
    }
    """
    r.run("ACL", "SETUSER", "move-user", "on", "nopass", "+move", "+set", "~*", "db=0,1")
    r2.run("auth", "move-user", "password")
    r2.run("set", "move-key", "value")
    assert "1" == r2.run("move", "move-key", 1)
    e = None
    try:
        e = r2.run("move", "move-key", 2)
    except Exception as _catch_err:
        e = str(_catch_err)
    assert fnmatch(str(e), "*NOPERM*database*")


def test_test_copy_with_database_permissions(r: ValkeyTestClient, r2) -> None:
    """
    test {Test COPY with database permissions} {
        r ACL SETUSER copy-user on nopass +copy +set +get +select ~* db=0,1
        $r2 auth copy-user password

        $r2 select 0
        $r2 set copy-key value

        assert_equal "1" [$r2 copy copy-key copy-key-dest DB 1]

        $r2 select 1
        assert_equal "value" [$r2 get copy-key-dest]

        $r2 select 0
        catch {$r2 copy copy-key copy-key-dest2 DB 2} e
        assert_match "*NOPERM*database*" $e

        r select 2
        assert_equal {} [r get copy-key-dest2]

        # cleanup
        r select 0
    }
    """
    r.run("ACL", "SETUSER", "copy-user", "on", "nopass", "+copy", "+set", "+get", "+select", "~*", "db=0,1")
    r2.run("auth", "copy-user", "password")
    r2.run("select", 0)
    r2.run("set", "copy-key", "value")
    assert "1" == r2.run("copy", "copy-key", "copy-key-dest", "DB", 1)
    r2.run("select", 1)
    assert "value" == r2.run("get", "copy-key-dest")
    r2.run("select", 0)
    e = None
    try:
        e = r2.run("copy", "copy-key", "copy-key-dest2", "DB", 2)
    except Exception as _catch_err:
        e = str(_catch_err)
    assert fnmatch(str(e), "*NOPERM*database*")
    r.run("select", 2)
    assert "" == r.run("get", "copy-key-dest2")
    r.run("select", 0)


def test_test_duplicate_database_ids_in_db_are_handled_correctly(r: ValkeyTestClient, r2) -> None:
    """
    test {Test duplicate database IDs in db= are handled correctly} {
        r ACL SETUSER db-dup-user on nopass +@all ~* db=0,0,1,1,0
        $r2 auth db-dup-user password

        # Should work - duplicates should be silently ignored
        assert_equal "OK" [$r2 select 0]
        assert_equal "OK" [$r2 select 1]

        catch {$r2 select 2} err
        assert_match "*NOPERM*database*" $err

        # Verify ACL LIST shows deduplicated list
        set acl_str [r ACL LIST]
        set user_line [lsearch -inline $acl_str "user db-dup-user*"]
        assert_match "*db=0,1*" $user_line
    }
    """
    r.run("ACL", "SETUSER", "db-dup-user", "on", "nopass", "+@all", "~*", "db=0,0,1,1,0")
    r2.run("auth", "db-dup-user", "password")
    assert "OK" == r2.run("select", 0)
    assert "OK" == r2.run("select", 1)
    err = None
    try:
        err = r2.run("select", 2)
    except Exception as _catch_err:
        err = str(_catch_err)
    assert fnmatch(str(err), "*NOPERM*database*")
    acl_str = r.run("ACL", "LIST")
    user_line = lsearch("-inline", acl_str, "user db-dup-user*")
    assert fnmatch(str(user_line), "*db=0,1*")


def test_test_multiple_selectors_with_overlapping_database_permissions(r: ValkeyTestClient, r2) -> None:
    """
    test {Test multiple selectors with overlapping database permissions} {
        r ACL SETUSER db-overlap on nopass (db=0,1 +@write +select ~write*) (db=1,2 +@read +select ~read*)
        $r2 auth db-overlap password

        # DB 0: only write selector
        assert_equal "OK" [$r2 select 0]
        assert_equal "OK" [$r2 set writekey value]
        catch {$r2 get readkey} err
        assert_match "*NOPERM*command*" $err

        # DB 1: both selectors apply
        assert_equal "OK" [$r2 select 1]
        assert_equal "OK" [$r2 set writekey value]
        catch {$r2 set readkey bar} err
        assert_match "*NOPERM*key*" $err
        assert_equal {} [$r2 get readkey]

        # DB 2: only read selector
        assert_equal "OK" [$r2 select 2]
        catch {$r2 set writekey value} err
        assert_match "*NOPERM*command*" $err
        catch {$r2 set readkey bar} err
        assert_match "*NOPERM*command*" $err
        assert_equal {} [$r2 get readkey]

        # DB 3: no selector
        catch {$r2 select 3} err
        assert_match "*NOPERM*" $err
    }
    """
    r.run(
        "ACL",
        "SETUSER",
        "db-overlap",
        "on",
        "nopass",
        "(db=0,1",
        "+@write",
        "+select",
        "~write*)",
        "(db=1,2",
        "+@read",
        "+select",
        "~read*)",
    )
    r2.run("auth", "db-overlap", "password")
    assert "OK" == r2.run("select", 0)
    assert "OK" == r2.run("set", "writekey", "value")
    err = None
    try:
        err = r2.run("get", "readkey")
    except Exception as _catch_err:
        err = str(_catch_err)
    assert fnmatch(str(err), "*NOPERM*command*")
    assert "OK" == r2.run("select", 1)
    assert "OK" == r2.run("set", "writekey", "value")
    err = None
    try:
        err = r2.run("set", "readkey", "bar")
    except Exception as _catch_err:
        err = str(_catch_err)
    assert fnmatch(str(err), "*NOPERM*key*")
    assert "" == r2.run("get", "readkey")
    assert "OK" == r2.run("select", 2)
    err = None
    try:
        err = r2.run("set", "writekey", "value")
    except Exception as _catch_err:
        err = str(_catch_err)
    assert fnmatch(str(err), "*NOPERM*command*")
    err = None
    try:
        err = r2.run("set", "readkey", "bar")
    except Exception as _catch_err:
        err = str(_catch_err)
    assert fnmatch(str(err), "*NOPERM*command*")
    assert "" == r2.run("get", "readkey")
    err = None
    try:
        err = r2.run("select", 3)
    except Exception as _catch_err:
        err = str(_catch_err)
    assert fnmatch(str(err), "*NOPERM*")


def test_test_db_with_leading_or_trailing_commas(r: ValkeyTestClient) -> None:
    """
    test {Test db= with leading/trailing commas} {
        catch {r ACL SETUSER db-comma-start db=,0,1} err
        assert_match "*Error*" $err

        catch {r ACL SETUSER db-comma-end db=0,1,} err
        assert_match "*Error*" $err

        catch {r ACL SETUSER db-comma-double db=0,,1} err
        assert_match "*Error*" $err
    }
    """
    err = None
    try:
        err = r.run("ACL", "SETUSER", "db-comma-start", "db=,0,1")
    except Exception as _catch_err:
        err = str(_catch_err)
    assert fnmatch(str(err), "*Error*")
    err = None
    try:
        err = r.run("ACL", "SETUSER", "db-comma-end", "db=0,1,")
    except Exception as _catch_err:
        err = str(_catch_err)
    assert fnmatch(str(err), "*Error*")
    err = None
    try:
        err = r.run("ACL", "SETUSER", "db-comma-double", "db=0,,1")
    except Exception as _catch_err:
        err = str(_catch_err)
    assert fnmatch(str(err), "*Error*")


def test_test_resetdbs_clears_explicit_db_list(r: ValkeyTestClient, r2) -> None:
    """
    test {Test resetdbs clears explicit db list} {
        r ACL SETUSER db-reset-test on nopass +@all ~* db=0,1
        $r2 auth db-reset-test password

        assert_equal "OK" [$r2 select 0]
        assert_equal "OK" [$r2 select 1]

        r ACL SETUSER db-reset-test resetdbs

        catch {$r2 select 0} err
        assert_match "*NOPERM*database*" $err
        catch {$r2 select 1} err
        assert_match "*NOPERM*database*" $err

        r ACL SETUSER db-reset-test db=0
        $r2 select 0
    }
    """
    r.run("ACL", "SETUSER", "db-reset-test", "on", "nopass", "+@all", "~*", "db=0,1")
    r2.run("auth", "db-reset-test", "password")
    assert "OK" == r2.run("select", 0)
    assert "OK" == r2.run("select", 1)
    r.run("ACL", "SETUSER", "db-reset-test", "resetdbs")
    err = None
    try:
        err = r2.run("select", 0)
    except Exception as _catch_err:
        err = str(_catch_err)
    assert fnmatch(str(err), "*NOPERM*database*")
    err = None
    try:
        err = r2.run("select", 1)
    except Exception as _catch_err:
        err = str(_catch_err)
    assert fnmatch(str(err), "*NOPERM*database*")
    r.run("ACL", "SETUSER", "db-reset-test", "db=0")
    r2.run("select", 0)


def test_test_clearselectors_removes_db_restrictions_from_selectors_but_not_root(r: ValkeyTestClient, r2) -> None:
    """
    test {Test clearselectors removes db restrictions from selectors but not root} {
        r ACL SETUSER db-clear on nopass +select db=0,1 (db=2,3 +@all ~*)
        $r2 auth db-clear password

        r ACL SETUSER db-clear clearselectors

        # Root selector should still have db restrictions
        assert_equal "OK" [$r2 select 0]
        assert_equal "OK" [$r2 select 1]

        catch {$r2 select 2} err
        assert_match "*NOPERM*" $err
    }
    """
    r.run("ACL", "SETUSER", "db-clear", "on", "nopass", "+select", "db=0,1", "(db=2,3", "+@all", "~*)")
    r2.run("auth", "db-clear", "password")
    r.run("ACL", "SETUSER", "db-clear", "clearselectors")
    assert "OK" == r2.run("select", 0)
    assert "OK" == r2.run("select", 1)
    err = None
    try:
        err = r2.run("select", 2)
    except Exception as _catch_err:
        err = str(_catch_err)
    assert fnmatch(str(err), "*NOPERM*")


def test_test_acl_dryrun_with_database_permissions(r: ValkeyTestClient) -> None:
    """
    test {Test ACL DRYRUN with database permissions} {
        r ACL SETUSER db-dryrun on nopass +@all ~* db=0,1

        assert_equal "OK" [r ACL DRYRUN db-dryrun SELECT 0]
        assert_equal "OK" [r ACL DRYRUN db-dryrun SELECT 1]

        assert_match "*has no permissions to access database*" [r ACL DRYRUN db-dryrun SELECT 2]
        assert_match "*has no permissions to access database*" [r ACL DRYRUN db-dryrun MOVE key 2]
        assert_match "*has no permissions to access database*" [r ACL DRYRUN db-dryrun SWAPDB 0 2]
        assert_equal "OK" [r ACL DRYRUN db-dryrun COPY key1 key2 DB 1]
        assert_match "*has no permissions to access database*" [r ACL DRYRUN db-dryrun COPY key1 key2 DB 2]
    }
    """
    r.run("ACL", "SETUSER", "db-dryrun", "on", "nopass", "+@all", "~*", "db=0,1")
    assert "OK" == r.run("ACL", "DRYRUN", "db-dryrun", "SELECT", 0)
    assert "OK" == r.run("ACL", "DRYRUN", "db-dryrun", "SELECT", 1)
    assert fnmatch(str(r.run("ACL", "DRYRUN", "db-dryrun", "SELECT", 2)), "*has no permissions to access database*")
    assert fnmatch(
        str(r.run("ACL", "DRYRUN", "db-dryrun", "MOVE", "key", 2)), "*has no permissions to access database*"
    )
    assert fnmatch(str(r.run("ACL", "DRYRUN", "db-dryrun", "SWAPDB", 0, 2)), "*has no permissions to access database*")
    assert "OK" == r.run("ACL", "DRYRUN", "db-dryrun", "COPY", "key1", "key2", "DB", 1)
    assert fnmatch(
        str(r.run("ACL", "DRYRUN", "db-dryrun", "COPY", "key1", "key2", "DB", 2)),
        "*has no permissions to access database*",
    )


def test_test_db_with_maximum_database_id(r: ValkeyTestClient, r2) -> None:
    """
    test {Test db= with maximum database ID} {
        set max_db [expr {[lindex [r config get databases] 1] - 1}]
        r ACL SETUSER db-max on nopass +@all ~* db=$max_db
        $r2 auth db-max password

        assert_equal "OK" [$r2 select $max_db]

        # Try one beyond max
        catch {$r2 select [expr {$max_db + 1}]} err
        # Should fail with out of range, not permission error
        assert_match "*out of range*" $err
    }
    """
    max_db = expr("[lindex [r config get databases] 1] - 1")
    r.run("ACL", "SETUSER", "db-max", "on", "nopass", "+@all", "~*", "db=$max_db")
    r2.run("auth", "db-max", "password")
    assert "OK" == r2.run("select", max_db)
    err = None
    try:
        err = r2.run("select", expr("$max_db + 1"))
    except Exception as _catch_err:
        err = str(_catch_err)
    assert fnmatch(str(err), "*out of range*")


def test_test_consecutive_database_permissions_only_last_one_should_persist(r: ValkeyTestClient, r2) -> None:
    """
    test {Test consecutive database permissions - only last one should persist} {
        # User db-consec should only have db=2 permissions
        r ACL SETUSER db-consec on nopass +@all ~* db=0 db=1 db=2
        $r2 auth db-consec password

        catch {$r2 select 0} err
        assert_match "*NOPERM*database*" $err
        catch {$r2 select 1} err
        assert_match "*NOPERM*database*" $err
        assert_equal "OK" [$r2 select 2]
        catch {$r2 select 3} err
        assert_match "*NOPERM*database*" $err

        # User db-consec-2 should only have db=1 permissions
        r ACL SETUSER db-consec-2 on nopass +@all ~* db=0
        r ACL SETUSER db-consec-2 db=1
        $r2 auth db-consec-2 password

        catch {$r2 select 0} err
        assert_match "*NOPERM*database*" $err
        assert_equal "OK" [$r2 select 1]
        catch {$r2 select 2} err
        assert_match "*NOPERM*database*" $err

        # Cleanup
        $r2 auth default password
        $r2 select 0
    }
    """
    r.run("ACL", "SETUSER", "db-consec", "on", "nopass", "+@all", "~*", "db=0", "db=1", "db=2")
    r2.run("auth", "db-consec", "password")
    err = None
    try:
        err = r2.run("select", 0)
    except Exception as _catch_err:
        err = str(_catch_err)
    assert fnmatch(str(err), "*NOPERM*database*")
    err = None
    try:
        err = r2.run("select", 1)
    except Exception as _catch_err:
        err = str(_catch_err)
    assert fnmatch(str(err), "*NOPERM*database*")
    assert "OK" == r2.run("select", 2)
    err = None
    try:
        err = r2.run("select", 3)
    except Exception as _catch_err:
        err = str(_catch_err)
    assert fnmatch(str(err), "*NOPERM*database*")
    r.run("ACL", "SETUSER", "db-consec-2", "on", "nopass", "+@all", "~*", "db=0")
    r.run("ACL", "SETUSER", "db-consec-2", "db=1")
    r2.run("auth", "db-consec-2", "password")
    err = None
    try:
        err = r2.run("select", 0)
    except Exception as _catch_err:
        err = str(_catch_err)
    assert fnmatch(str(err), "*NOPERM*database*")
    assert "OK" == r2.run("select", 1)
    err = None
    try:
        err = r2.run("select", 2)
    except Exception as _catch_err:
        err = str(_catch_err)
    assert fnmatch(str(err), "*NOPERM*database*")
    r2.run("auth", "default", "password")
    r2.run("select", 0)


def test_test_commands_without_key_or_metadata_access_work_in_restricted_databases(r: ValkeyTestClient, r2) -> None:
    """
    test {Test commands without key/metadata access work in restricted databases} {
        r ACL SETUSER db-keyless-cmd on nopass db=15 +@all ~*
        $r2 auth db-keyless-cmd password

        # Commands that don't touch keys/metadata should work
        set ping_result [$r2 ping]
        assert {[string length $ping_result] > 0}

        set ping_msg_result [$r2 ping "hello"]
        assert {[string length $ping_msg_result] > 0}

        catch {$r2 acl getuser} err
        assert_match "*wrong number of arguments*" $err

        set user_info [$r2 acl getuser db-keyless-cmd]
        assert {[llength $user_info] > 0}

        set log_result [$r2 acl log 0]
        assert {[llength $log_result] >= 0}

        set info_result [$r2 info server]
        assert {[string length $info_result] > 0}

        # Commands that touch keys should fail with NOPERM database error
        catch {$r2 select 2} err
        assert_match "*NOPERM*database*" $err

        catch {$r2 get key} err
        assert_match "*NOPERM*database*" $err

        catch {$r2 getdel key} err
        assert_match "*NOPERM*database*" $err

        catch {$r2 set key value} err
        assert_match "*NOPERM*database*" $err

        catch {$r2 del key} err
        assert_match "*NOPERM*database*" $err

        catch {$r2 exists key} err
        assert_match "*NOPERM*database*" $err

        catch {$r2 flushdb} err
        assert_match "*NOPERM*database*" $err

        # But user can select to db=15 where they have permissions
        set select_result [$r2 select 15]
        assert {[string length $select_result] > 0}

        set set_result [$r2 set key value]
        assert {[string length $set_result] > 0}

        set get_result [$r2 get key]
        assert {[string length $get_result] > 0}

        catch {$r2 select 0} err
        assert_match "*NOPERM*database*" $err
    }
    """
    r.run("ACL", "SETUSER", "db-keyless-cmd", "on", "nopass", "db=15", "+@all", "~*")
    r2.run("auth", "db-keyless-cmd", "password")
    ping_result = r2.run("ping")
    assert len(ping_result) > 0
    ping_msg_result = r2.run("ping", "hello")
    assert len(ping_msg_result) > 0
    err = None
    try:
        err = r2.run("acl", "getuser")
    except Exception as _catch_err:
        err = str(_catch_err)
    assert fnmatch(str(err), "*wrong number of arguments*")
    user_info = r2.run("acl", "getuser", "db-keyless-cmd")
    assert len(user_info) > 0
    log_result = r2.run("acl", "log", 0)
    assert len(log_result) >= 0
    info_result = r2.run("info", "server")
    assert len(info_result) > 0
    err = None
    try:
        err = r2.run("select", 2)
    except Exception as _catch_err:
        err = str(_catch_err)
    assert fnmatch(str(err), "*NOPERM*database*")
    err = None
    try:
        err = r2.run("get", "key")
    except Exception as _catch_err:
        err = str(_catch_err)
    assert fnmatch(str(err), "*NOPERM*database*")
    err = None
    try:
        err = r2.run("getdel", "key")
    except Exception as _catch_err:
        err = str(_catch_err)
    assert fnmatch(str(err), "*NOPERM*database*")
    err = None
    try:
        err = r2.run("set", "key", "value")
    except Exception as _catch_err:
        err = str(_catch_err)
    assert fnmatch(str(err), "*NOPERM*database*")
    err = None
    try:
        err = r2.run("del", "key")
    except Exception as _catch_err:
        err = str(_catch_err)
    assert fnmatch(str(err), "*NOPERM*database*")
    err = None
    try:
        err = r2.run("exists", "key")
    except Exception as _catch_err:
        err = str(_catch_err)
    assert fnmatch(str(err), "*NOPERM*database*")
    err = None
    try:
        err = r2.run("flushdb")
    except Exception as _catch_err:
        err = str(_catch_err)
    assert fnmatch(str(err), "*NOPERM*database*")
    select_result = r2.run("select", 15)
    assert len(select_result) > 0
    set_result = r2.run("set", "key", "value")
    assert len(set_result) > 0
    get_result = r2.run("get", "key")
    assert len(get_result) > 0
    err = None
    try:
        err = r2.run("select", 0)
    except Exception as _catch_err:
        err = str(_catch_err)
    assert fnmatch(str(err), "*NOPERM*database*")


def test_test_watch_command_with_no_database_access(r: ValkeyTestClient, r2) -> None:
    """
    test {Test WATCH command with no database access} {
        r ACL SETUSER watch-nodb-user on nopass +@all ~* db=1
        $r2 auth watch-nodb-user password

        catch {$r2 watch somekey} err
        assert_match "*NOPERM*database*" $err

        assert_equal "OK" [$r2 select 1]
        assert_equal "OK" [$r2 watch somekey]

        # cleanup
        $r2 auth default password
        $r2 select 0
    }
    """
    r.run("ACL", "SETUSER", "watch-nodb-user", "on", "nopass", "+@all", "~*", "db=1")
    r2.run("auth", "watch-nodb-user", "password")
    err = None
    try:
        err = r2.run("watch", "somekey")
    except Exception as _catch_err:
        err = str(_catch_err)
    assert fnmatch(str(err), "*NOPERM*database*")
    assert "OK" == r2.run("select", 1)
    assert "OK" == r2.run("watch", "somekey")
    r2.run("auth", "default", "password")
    r2.run("select", 0)


def test_test_keyspace_command_with_no_database_access(r: ValkeyTestClient, r2) -> None:
    """
    test {Test keyspace command with no database access} {
        r ACL SETUSER exists-nodb-user on nopass +@all ~* db=1
        $r2 auth exists-nodb-user password

        catch {$r2 exists somekey} err
        assert_match "*NOPERM*database*" $err

        assert_equal "OK" [$r2 select 1]
        assert_equal "0" [$r2 exists somekey]

        # cleanup
        $r2 auth default password
        $r2 select 0
    }
    """
    r.run("ACL", "SETUSER", "exists-nodb-user", "on", "nopass", "+@all", "~*", "db=1")
    r2.run("auth", "exists-nodb-user", "password")
    err = None
    try:
        err = r2.run("exists", "somekey")
    except Exception as _catch_err:
        err = str(_catch_err)
    assert fnmatch(str(err), "*NOPERM*database*")
    assert "OK" == r2.run("select", 1)
    assert "0" == r2.run("exists", "somekey")
    r2.run("auth", "default", "password")
    r2.run("select", 0)


def test_test_multi_with_select_to_invalid_database(r: ValkeyTestClient, r2) -> None:
    """
    test {Test MULTI with SELECT to invalid database} {
        r ACL SETUSER db-invalid-select on nopass +@all ~* db=0,1
        $r2 auth db-invalid-select password

        assert_equal "OK" [$r2 select 0]
        assert_equal "OK" [$r2 multi]
        assert_equal "QUEUED" [$r2 set key1 value1]

        catch {$r2 select 2} err
        assert_match "*NOPERM*database*" $err

        catch {$r2 exec} err
        assert_match "*EXECABORT*" $err

        assert_equal {} [$r2 get key1]
    }
    """
    r.run("ACL", "SETUSER", "db-invalid-select", "on", "nopass", "+@all", "~*", "db=0,1")
    r2.run("auth", "db-invalid-select", "password")
    assert "OK" == r2.run("select", 0)
    assert "OK" == r2.run("multi")
    assert "QUEUED" == r2.run("set", "key1", "value1")
    err = None
    try:
        err = r2.run("select", 2)
    except Exception as _catch_err:
        err = str(_catch_err)
    assert fnmatch(str(err), "*NOPERM*database*")
    err = None
    try:
        err = r2.run("exec")
    except Exception as _catch_err:
        err = str(_catch_err)
    assert fnmatch(str(err), "*EXECABORT*")
    assert "" == r2.run("get", "key1")


def test_test_watch_with_multi_and_select_keys_modified(r: ValkeyTestClient, r2) -> None:
    """
    test {Test WATCH with MULTI and SELECT - keys modified} {
        r ACL SETUSER db-watch-select on nopass +@all ~* db=0,1
        $r2 auth db-watch-select password

        assert_equal "OK" [$r2 select 0]
        $r2 set watchkey original
        assert_equal "OK" [$r2 watch watchkey]

        assert_equal "OK" [$r2 multi]
        assert_equal "QUEUED" [$r2 select 1]
        assert_equal "QUEUED" [$r2 set key1 value1]

        r select 0
        r set watchkey modified

        set result [$r2 exec]
        assert_equal 0 [llength $result]

        assert_equal {} [$r2 get key1]
    }
    """
    r.run("ACL", "SETUSER", "db-watch-select", "on", "nopass", "+@all", "~*", "db=0,1")
    r2.run("auth", "db-watch-select", "password")
    assert "OK" == r2.run("select", 0)
    r2.run("set", "watchkey", "original")
    assert "OK" == r2.run("watch", "watchkey")
    assert "OK" == r2.run("multi")
    assert "QUEUED" == r2.run("select", 1)
    assert "QUEUED" == r2.run("set", "key1", "value1")
    r.run("select", 0)
    r.run("set", "watchkey", "modified")
    result = r2.run("exec")
    assert 0 == len(result)
    assert "" == r2.run("get", "key1")


def test_test_watch_with_multi_and_select_no_modification(r: ValkeyTestClient, r2) -> None:
    """
    test {Test WATCH with MULTI and SELECT - no modification} {
        r ACL SETUSER db-watch-nomod on nopass +@all ~* db=0,1
        $r2 auth db-watch-nomod password

        assert_equal "OK" [$r2 select 0]
        $r2 set watchkey original
        assert_equal "OK" [$r2 watch watchkey]

        assert_equal "OK" [$r2 multi]
        assert_equal "QUEUED" [$r2 select 1]
        assert_equal "QUEUED" [$r2 set key1 value1]

        # No modification of watched key

        set result [$r2 exec]
        assert_equal 2 [llength $result]

        assert_equal "value1" [$r2 get key1]
    }
    """
    r.run("ACL", "SETUSER", "db-watch-nomod", "on", "nopass", "+@all", "~*", "db=0,1")
    r2.run("auth", "db-watch-nomod", "password")
    assert "OK" == r2.run("select", 0)
    r2.run("set", "watchkey", "original")
    assert "OK" == r2.run("watch", "watchkey")
    assert "OK" == r2.run("multi")
    assert "QUEUED" == r2.run("select", 1)
    assert "QUEUED" == r2.run("set", "key1", "value1")
    result = r2.run("exec")
    assert 2 == len(result)
    assert "value1" == r2.run("get", "key1")


def test_test_sort_with_by_or_get_patterns_in_multi_after_select(r: ValkeyTestClient, r2) -> None:
    """
    test {Test SORT with BY/GET patterns in MULTI after SELECT} {
        r ACL SETUSER db-sort-multi on nopass +@all ~* db=0,1
        $r2 auth db-sort-multi password

        assert_equal "OK" [$r2 select 0]
        $r2 lpush mylist 1 2 3
        $r2 set weight_1 10
        $r2 set weight_2 20
        $r2 set weight_3 30

        assert_equal "OK" [$r2 multi]
        assert_equal "QUEUED" [$r2 select 1]

        assert_equal "QUEUED" [$r2 sort mylist by weight_*]

        set result [$r2 exec]
        assert_equal 2 [llength $result]

        # Cleanup
        $r2 select 0
        $r2 del mylist weight_1 weight_2 weight_3
    }
    """
    r.run("ACL", "SETUSER", "db-sort-multi", "on", "nopass", "+@all", "~*", "db=0,1")
    r2.run("auth", "db-sort-multi", "password")
    assert "OK" == r2.run("select", 0)
    r2.run("lpush", "mylist", 1, 2, 3)
    r2.run("set", "weight_1", 10)
    r2.run("set", "weight_2", 20)
    r2.run("set", "weight_3", 30)
    assert "OK" == r2.run("multi")
    assert "QUEUED" == r2.run("select", 1)
    assert "QUEUED" == r2.run("sort", "mylist", "by", "weight_*")
    result = r2.run("exec")
    assert 2 == len(result)
    r2.run("select", 0)
    r2.run("del", "mylist", "weight_1", "weight_2", "weight_3")


def test_test_discard_after_select_in_multi(r: ValkeyTestClient, r2) -> None:
    """
    test {Test DISCARD after SELECT in MULTI} {
        r ACL SETUSER db-discard on nopass +@all ~* db=0,1
        $r2 auth db-discard password

        assert_equal "OK" [$r2 select 0]
        assert_equal "OK" [$r2 multi]

        assert_equal "QUEUED" [$r2 set key1 value1]
        assert_equal "QUEUED" [$r2 select 1]
        assert_equal "QUEUED" [$r2 set key2 value2]

        assert_equal "OK" [$r2 discard]

        $r2 set testkey testvalue
        assert_equal "testvalue" [$r2 get testkey]

        assert_equal {} [$r2 get key1]
        $r2 select 1
        assert_equal {} [$r2 get key2]

        # Cleanup
        $r2 select 0
        $r2 del testkey
    }
    """
    r.run("ACL", "SETUSER", "db-discard", "on", "nopass", "+@all", "~*", "db=0,1")
    r2.run("auth", "db-discard", "password")
    assert "OK" == r2.run("select", 0)
    assert "OK" == r2.run("multi")
    assert "QUEUED" == r2.run("set", "key1", "value1")
    assert "QUEUED" == r2.run("select", 1)
    assert "QUEUED" == r2.run("set", "key2", "value2")
    assert "OK" == r2.run("discard")
    r2.run("set", "testkey", "testvalue")
    assert "testvalue" == r2.run("get", "testkey")
    assert "" == r2.run("get", "key1")
    r2.run("select", 1)
    assert "" == r2.run("get", "key2")
    r2.run("select", 0)
    r2.run("del", "testkey")


def test_test_multi_with_multiple_select_commands(r: ValkeyTestClient, r2) -> None:
    """
    test {Test MULTI with multiple SELECT commands} {
        r ACL SETUSER db-multi-select on nopass +@all ~* db=0,1,2
        $r2 auth db-multi-select password

        assert_equal "OK" [$r2 select 0]
        assert_equal "OK" [$r2 multi]

        assert_equal "QUEUED" [$r2 set key0 value0]
        assert_equal "QUEUED" [$r2 select 1]
        assert_equal "QUEUED" [$r2 set key1 value1]
        assert_equal "QUEUED" [$r2 select 2]
        assert_equal "QUEUED" [$r2 set key2 value2]
        assert_equal "QUEUED" [$r2 select 0]
        assert_equal "QUEUED" [$r2 get key0]

        set result [$r2 exec]
        assert_equal 7 [llength $result]

        assert_equal "value0" [$r2 get key0]
        $r2 select 1
        assert_equal "value1" [$r2 get key1]
        $r2 select 2
        assert_equal "value2" [$r2 get key2]

        # Cleanup
        $r2 select 0
        $r2 del key0 finalkey
        $r2 select 1
        $r2 del key1
        $r2 select 2
        $r2 del key2
        $r2 select 0
    }
    """
    r.run("ACL", "SETUSER", "db-multi-select", "on", "nopass", "+@all", "~*", "db=0,1,2")
    r2.run("auth", "db-multi-select", "password")
    assert "OK" == r2.run("select", 0)
    assert "OK" == r2.run("multi")
    assert "QUEUED" == r2.run("set", "key0", "value0")
    assert "QUEUED" == r2.run("select", 1)
    assert "QUEUED" == r2.run("set", "key1", "value1")
    assert "QUEUED" == r2.run("select", 2)
    assert "QUEUED" == r2.run("set", "key2", "value2")
    assert "QUEUED" == r2.run("select", 0)
    assert "QUEUED" == r2.run("get", "key0")
    result = r2.run("exec")
    assert 7 == len(result)
    assert "value0" == r2.run("get", "key0")
    r2.run("select", 1)
    assert "value1" == r2.run("get", "key1")
    r2.run("select", 2)
    assert "value2" == r2.run("get", "key2")
    r2.run("select", 0)
    r2.run("del", "key0", "finalkey")
    r2.run("select", 1)
    r2.run("del", "key1")
    r2.run("select", 2)
    r2.run("del", "key2")
    r2.run("select", 0)


def test_test_multi_with_select_and_acl_permission_changes_between_queue_and_exec(r: ValkeyTestClient, r2) -> None:
    """
    test {Test MULTI with SELECT and ACL permission changes between queue and exec} {
        r ACL SETUSER db-acl-change on nopass +@all ~* db=0,1
        $r2 auth db-acl-change password

        assert_equal "OK" [$r2 select 0]
        assert_equal "OK" [$r2 multi]
        assert_equal "QUEUED" [$r2 set key1 value1]
        assert_equal "QUEUED" [$r2 select 1]
        assert_equal "QUEUED" [$r2 set key2 value2]

        r ACL SETUSER db-acl-change db=0

        catch {$r2 exec} err
        assert_match "*NOPERM*" $err

        # Cleanup
        r ACL SETUSER db-acl-change db=0,1
    }
    """
    r.run("ACL", "SETUSER", "db-acl-change", "on", "nopass", "+@all", "~*", "db=0,1")
    r2.run("auth", "db-acl-change", "password")
    assert "OK" == r2.run("select", 0)
    assert "OK" == r2.run("multi")
    assert "QUEUED" == r2.run("set", "key1", "value1")
    assert "QUEUED" == r2.run("select", 1)
    assert "QUEUED" == r2.run("set", "key2", "value2")
    r.run("ACL", "SETUSER", "db-acl-change", "db=0")
    err = None
    try:
        err = r2.run("exec")
    except Exception as _catch_err:
        err = str(_catch_err)
    assert fnmatch(str(err), "*NOPERM*")
    r.run("ACL", "SETUSER", "db-acl-change", "db=0,1")


def test_test_eval_with_database_permissions(r: ValkeyTestClient, r2) -> None:
    """
    test {Test EVAL with database permissions} {
        r ACL SETUSER eval-db-user on nopass +@all ~* db=0,1
        $r2 auth eval-db-user password

        assert_equal "OK" [$r2 select 0]
        assert_equal "OK" [$r2 select 1]

        catch {$r2 eval {server.call('SELECT', '2')} 0} err
        assert_match "*ACL failure in script*No permissions to access database*" $err

        $r2 select 0
        set result [$r2 eval {server.call('SELECT', '0'); return server.call('SET', 'key', 'value')} 0]
        assert_equal "OK" $result

        assert_equal "value" [$r2 get key]

        # Cleanup
        $r2 del key
    }
    """
    r.run("ACL", "SETUSER", "eval-db-user", "on", "nopass", "+@all", "~*", "db=0,1")
    r2.run("auth", "eval-db-user", "password")
    assert "OK" == r2.run("select", 0)
    assert "OK" == r2.run("select", 1)
    err = None
    try:
        err = r2.run("eval", "server.call('SELECT', '2')", 0)
    except Exception as _catch_err:
        err = str(_catch_err)
    assert fnmatch(str(err), "*ACL failure in script*No permissions to access database*")
    r2.run("select", 0)
    result = r2.run("eval", "server.call('SELECT', '0'); return server.call('SET', 'key', 'value')", 0)
    assert "OK" == result
    assert "value" == r2.run("get", "key")
    r2.run("del", "key")


def test_test_evalsha_with_database_permissions(r: ValkeyTestClient, r2) -> None:
    """
    test {Test EVALSHA with database permissions} {
        r ACL SETUSER evalsha-db-user on nopass +@all ~* db=0,1
        $r2 auth evalsha-db-user password

        assert_equal "OK" [$r2 select 0]

        set sha [r script load {server.call('SELECT', '2'); return 'OK'}]

        catch {$r2 evalsha $sha 0} err
        assert_match "*ACL failure in script*No permissions to access database*" $err

        set sha_ok [r script load {server.call('SELECT', '1'); return server.call('SET', 'key2', 'value2')}]

        set result [$r2 evalsha $sha_ok 0]
        assert_equal "OK" $result

        $r2 select 1
        assert_equal "value2" [$r2 get key2]

        # Cleanup
        $r2 del key2
        $r2 select 0
    }
    """
    r.run("ACL", "SETUSER", "evalsha-db-user", "on", "nopass", "+@all", "~*", "db=0,1")
    r2.run("auth", "evalsha-db-user", "password")
    assert "OK" == r2.run("select", 0)
    sha = r.run("script", "load", "server.call('SELECT', '2'); return 'OK'")
    err = None
    try:
        err = r2.run("evalsha", sha, 0)
    except Exception as _catch_err:
        err = str(_catch_err)
    assert fnmatch(str(err), "*ACL failure in script*No permissions to access database*")
    sha_ok = r.run("script", "load", "server.call('SELECT', '1'); return server.call('SET', 'key2', 'value2')")
    result = r2.run("evalsha", sha_ok, 0)
    assert "OK" == result
    r2.run("select", 1)
    assert "value2" == r2.run("get", "key2")
    r2.run("del", "key2")
    r2.run("select", 0)


def test_test_eval_ro_with_database_permissions(r: ValkeyTestClient, r2) -> None:
    """
    test {Test EVAL_RO with database permissions} {
        r ACL SETUSER eval-ro-db-user on nopass +@all ~* db=0,1
        $r2 auth eval-ro-db-user password

        assert_equal "OK" [$r2 select 0]
        r set testkey testvalue

        catch {$r2 eval_ro {server.call('SELECT', '2')} 0} err
        assert_match "*ACL failure in script*No permissions to access database*" $err

        set result [$r2 eval_ro {server.call('SELECT', '0'); return server.call('GET', 'testkey')} 0]
        assert_equal "testvalue" $result

        # Cleanup
        r del testkey
    }
    """
    r.run("ACL", "SETUSER", "eval-ro-db-user", "on", "nopass", "+@all", "~*", "db=0,1")
    r2.run("auth", "eval-ro-db-user", "password")
    assert "OK" == r2.run("select", 0)
    r.run("set", "testkey", "testvalue")
    err = None
    try:
        err = r2.run("eval_ro", "server.call('SELECT', '2')", 0)
    except Exception as _catch_err:
        err = str(_catch_err)
    assert fnmatch(str(err), "*ACL failure in script*No permissions to access database*")
    result = r2.run("eval_ro", "server.call('SELECT', '0'); return server.call('GET', 'testkey')", 0)
    assert "testvalue" == result
    r.run("del", "testkey")


def test_test_evalsha_ro_with_database_permissions(r: ValkeyTestClient, r2) -> None:
    """
    test {Test EVALSHA_RO with database permissions} {
        r ACL SETUSER evalsha-ro-db-user on nopass +@all ~* db=0,1
        $r2 auth evalsha-ro-db-user password

        assert_equal "OK" [$r2 select 0]
        r set rokey rovalue

        set sha [r script load {server.call('SELECT', '3'); return server.call('GET', 'rokey')}]

        catch {$r2 evalsha_ro $sha 0} err
        assert_match "*ACL failure in script*No permissions to access database*" $err

        set sha_ok [r script load {server.call('SELECT', '1'); return 'allowed'}]

        set result [$r2 evalsha_ro $sha_ok 0]
        assert_equal "allowed" $result

        # Cleanup
        r del rokey
    }
    """
    r.run("ACL", "SETUSER", "evalsha-ro-db-user", "on", "nopass", "+@all", "~*", "db=0,1")
    r2.run("auth", "evalsha-ro-db-user", "password")
    assert "OK" == r2.run("select", 0)
    r.run("set", "rokey", "rovalue")
    sha = r.run("script", "load", "server.call('SELECT', '3'); return server.call('GET', 'rokey')")
    err = None
    try:
        err = r2.run("evalsha_ro", sha, 0)
    except Exception as _catch_err:
        err = str(_catch_err)
    assert fnmatch(str(err), "*ACL failure in script*No permissions to access database*")
    sha_ok = r.run("script", "load", "server.call('SELECT', '1'); return 'allowed'")
    result = r2.run("evalsha_ro", sha_ok, 0)
    assert "allowed" == result
    r.run("del", "rokey")


def test_test_fcall_with_database_permissions(r: ValkeyTestClient, r2) -> None:
    """
    test {Test FCALL with database permissions} {
        r ACL SETUSER fcall-db-user on nopass +@all ~* db=0,1
        $r2 auth fcall-db-user password

        assert_equal "OK" [$r2 select 0]

        r function load {#!lua name=dbtest
            server.register_function('select_restricted', function(keys, args)
                server.call('SELECT', '2')
                return 'OK'
            end)
        }

        catch {$r2 fcall select_restricted 0} err
        assert_match "*ACL failure in script*No permissions to access database*" $err

        r function load replace {#!lua name=dbtest
            server.register_function('select_allowed', function(keys, args)
                server.call('SELECT', '1')
                return server.call('SET', 'fcallkey', 'fcallvalue')
            end)
        }

        set result [$r2 fcall select_allowed 0]
        assert_equal "OK" $result

        $r2 select 1
        assert_equal "fcallvalue" [$r2 get fcallkey]

        # Cleanup
        $r2 del fcallkey
        $r2 select 0
        r function delete dbtest
    }
    """
    r.run("ACL", "SETUSER", "fcall-db-user", "on", "nopass", "+@all", "~*", "db=0,1")
    r2.run("auth", "fcall-db-user", "password")
    assert "OK" == r2.run("select", 0)
    r.run(
        "function",
        "load",
        "#!lua name=dbtest\n            server.register_function('select_restricted', function(keys, args)\n                server.call('SELECT', '2')\n                return 'OK'\n            end)\n        ",
    )
    err = None
    try:
        err = r2.run("fcall", "select_restricted", 0)
    except Exception as _catch_err:
        err = str(_catch_err)
    assert fnmatch(str(err), "*ACL failure in script*No permissions to access database*")
    r.run(
        "function",
        "load",
        "replace",
        "#!lua name=dbtest\n            server.register_function('select_allowed', function(keys, args)\n                server.call('SELECT', '1')\n                return server.call('SET', 'fcallkey', 'fcallvalue')\n            end)\n        ",
    )
    result = r2.run("fcall", "select_allowed", 0)
    assert "OK" == result
    r2.run("select", 1)
    assert "fcallvalue" == r2.run("get", "fcallkey")
    r2.run("del", "fcallkey")
    r2.run("select", 0)
    r.run("function", "delete", "dbtest")


def test_test_fcall_ro_with_database_permissions(r: ValkeyTestClient, r2) -> None:
    """
    test {Test FCALL_RO with database permissions} {
        r ACL SETUSER fcall-ro-db-user on nopass +@all ~* db=0,1
        $r2 auth fcall-ro-db-user password

        assert_equal "OK" [$r2 select 0]
        r set fcallrokey fcallrovalue

        r function load {#!lua name=dbtestro
            server.register_function{
                function_name='read_restricted',
                callback=function(keys, args)
                    server.call('SELECT', '3')
                    return server.call('GET', 'fcallrokey')
                end,
                flags={'no-writes'}
            }
        }

        catch {$r2 fcall_ro read_restricted 0} err
        assert_match "*ACL failure in script*No permissions to access database*" $err

        r function load replace {#!lua name=dbtestro
            server.register_function{
                function_name='read_allowed',
                callback=function(keys, args)
                    server.call('SELECT', '0')
                    return server.call('GET', 'fcallrokey')
                end,
                flags={'no-writes'}
            }
        }

        set result [$r2 fcall_ro read_allowed 0]
        assert_equal "fcallrovalue" $result

        # Cleanup
        r del fcallrokey
        r function delete dbtestro
    }
    """
    r.run("ACL", "SETUSER", "fcall-ro-db-user", "on", "nopass", "+@all", "~*", "db=0,1")
    r2.run("auth", "fcall-ro-db-user", "password")
    assert "OK" == r2.run("select", 0)
    r.run("set", "fcallrokey", "fcallrovalue")
    r.run(
        "function",
        "load",
        "#!lua name=dbtestro\n            server.register_function{\n                function_name='read_restricted',\n                callback=function(keys, args)\n                    server.call('SELECT', '3')\n                    return server.call('GET', 'fcallrokey')\n                end,\n                flags={'no-writes'}\n            }\n        ",
    )
    err = None
    try:
        err = r2.run("fcall_ro", "read_restricted", 0)
    except Exception as _catch_err:
        err = str(_catch_err)
    assert fnmatch(str(err), "*ACL failure in script*No permissions to access database*")
    r.run(
        "function",
        "load",
        "replace",
        "#!lua name=dbtestro\n            server.register_function{\n                function_name='read_allowed',\n                callback=function(keys, args)\n                    server.call('SELECT', '0')\n                    return server.call('GET', 'fcallrokey')\n                end,\n                flags={'no-writes'}\n            }\n        ",
    )
    result = r2.run("fcall_ro", "read_allowed", 0)
    assert "fcallrovalue" == result
    r.run("del", "fcallrokey")
    r.run("function", "delete", "dbtestro")


def test_test_eval_with_multiple_database_switches_in_script(r: ValkeyTestClient, r2) -> None:
    """
    test {Test EVAL with multiple database switches in script} {
        r ACL SETUSER eval-multi-db on nopass +@all ~* db=0,1,2
        $r2 auth eval-multi-db password

        assert_equal "OK" [$r2 select 0]

        set result [$r2 eval {
            server.call('SELECT', '0')
            server.call('SET', 'key0', 'val0')
            server.call('SELECT', '1')
            server.call('SET', 'key1', 'val1')
            server.call('SELECT', '2')
            server.call('SET', 'key2', 'val2')
            return 'OK'
        } 0]
        assert_equal "OK" $result

        $r2 select 0
        assert_equal "val0" [$r2 get key0]
        $r2 select 1
        assert_equal "val1" [$r2 get key1]
        $r2 select 2
        assert_equal "val2" [$r2 get key2]

        $r2 select 0
        catch {$r2 eval {
            server.call('SELECT', '0')
            server.call('SET', 'key0', 'newval')
            server.call('SELECT', '3')
            server.call('SET', 'key3', 'val3')
            return 'OK'
        } 0} err
        assert_match "*ACL failure in script*No permissions to access database*" $err

        # Cleanup
        $r2 select 0
        $r2 del key0
        $r2 select 1
        $r2 del key1
        $r2 select 2
        $r2 del key2
        $r2 select 0
    }
    """
    r.run("ACL", "SETUSER", "eval-multi-db", "on", "nopass", "+@all", "~*", "db=0,1,2")
    r2.run("auth", "eval-multi-db", "password")
    assert "OK" == r2.run("select", 0)
    result = r2.run(
        "eval",
        "            server.call('SELECT', '0')            server.call('SET', 'key0', 'val0')            server.call('SELECT', '1')            server.call('SET', 'key1', 'val1')            server.call('SELECT', '2')            server.call('SET', 'key2', 'val2')            return 'OK'        ",
        0,
    )
    assert "OK" == result
    r2.run("select", 0)
    assert "val0" == r2.run("get", "key0")
    r2.run("select", 1)
    assert "val1" == r2.run("get", "key1")
    r2.run("select", 2)
    assert "val2" == r2.run("get", "key2")
    r2.run("select", 0)
    err = None
    try:
        err = r2.run(
            "eval",
            "            server.call('SELECT', '0')\n            server.call('SET', 'key0', 'newval')\n            server.call('SELECT', '3')\n            server.call('SET', 'key3', 'val3')\n            return 'OK'\n        ",
            0,
        )
    except Exception as _catch_err:
        err = str(_catch_err)
    assert fnmatch(str(err), "*ACL failure in script*No permissions to access database*")
    r2.run("select", 0)
    r2.run("del", "key0")
    r2.run("select", 1)
    r2.run("del", "key1")
    r2.run("select", 2)
    r2.run("del", "key2")
    r2.run("select", 0)


def test_acl_stats_for_invalid_database_accesses(r: ValkeyTestClient, r2) -> None:
    """
    test {ACL stats for invalid database accesses} {
        set current_auth_failures [s acl_access_denied_auth]
        set current_invalid_cmd_accesses [s acl_access_denied_cmd]
        set current_invalid_key_accesses [s acl_access_denied_key]
        set current_invalid_channel_accesses [s acl_access_denied_channel]
        set current_invalid_db_accesses [s acl_access_denied_db]

        r ACL SETUSER invaliddbuser on nopass +@all ~* db=0,1
        $r2 auth invaliddbuser password

        catch {$r2 select 2} err
        assert_match "*NOPERM*database*" $err

        catch {$r2 select 3} err
        assert_match "*NOPERM*database*" $err

        catch {$r2 select 4} err
        assert_match "*NOPERM*database*" $err

        r AUTH default ""

        # Verify the counter increased by 3
        assert {[s acl_access_denied_auth] eq $current_auth_failures}
        assert {[s acl_access_denied_cmd] eq $current_invalid_cmd_accesses}
        assert {[s acl_access_denied_key] eq $current_invalid_key_accesses}
        assert {[s acl_access_denied_channel] eq $current_invalid_channel_accesses}
        assert {[s acl_access_denied_db] eq [expr $current_invalid_db_accesses + 3]}

        # Cleanup
        r ACL deluser invaliddbuser
    }
    """
    current_auth_failures = s("acl_access_denied_auth")
    current_invalid_cmd_accesses = s("acl_access_denied_cmd")
    current_invalid_key_accesses = s("acl_access_denied_key")
    current_invalid_channel_accesses = s("acl_access_denied_channel")
    current_invalid_db_accesses = s("acl_access_denied_db")
    r.run("ACL", "SETUSER", "invaliddbuser", "on", "nopass", "+@all", "~*", "db=0,1")
    r2.run("auth", "invaliddbuser", "password")
    err = None
    try:
        err = r2.run("select", 2)
    except Exception as _catch_err:
        err = str(_catch_err)
    assert fnmatch(str(err), "*NOPERM*database*")
    err = None
    try:
        err = r2.run("select", 3)
    except Exception as _catch_err:
        err = str(_catch_err)
    assert fnmatch(str(err), "*NOPERM*database*")
    err = None
    try:
        err = r2.run("select", 4)
    except Exception as _catch_err:
        err = str(_catch_err)
    assert fnmatch(str(err), "*NOPERM*database*")
    r.run("AUTH", "default", "")
    assert s("acl_access_denied_auth") == current_auth_failures
    assert s("acl_access_denied_cmd") == current_invalid_cmd_accesses
    assert s("acl_access_denied_key") == current_invalid_key_accesses
    assert s("acl_access_denied_channel") == current_invalid_channel_accesses
    assert s("acl_access_denied_db") == expr(current_invalid_db_accesses, "+", 3)
    r.run("ACL", "deluser", "invaliddbuser")


"""
$r2 close
"""


# --- stubs for unimplemented TCL helpers ---


def assert_error(*args):
    raise NotImplementedError("assert_error")


def assert_range(*args):
    raise NotImplementedError("assert_range")


def expr(*args):
    raise NotImplementedError("expr")


def foreach(*args):
    raise NotImplementedError("foreach")


def lsearch(*args):
    raise NotImplementedError("lsearch")


def s(*args):
    raise NotImplementedError("s")
