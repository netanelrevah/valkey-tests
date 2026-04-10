import pytest

from tests.valkey_test_client import ValkeyTestClient

testmodule = "tests/modules/getchannels.so"

pytestmark = [pytest.mark.modules]


def test_module_getchannels_api_with_literals_acl(r: ValkeyTestClient) -> None:
    """
    test "module getchannels-api with literals - ACL" {
        assert_equal "OK" [r ACL DRYRUN testuser getchannels.command subscribe literal channel subscribe literal pattern1]
        assert_equal "OK" [r ACL DRYRUN testuser getchannels.command publish literal channel publish literal pattern1]
        assert_equal "OK" [r ACL DRYRUN testuser getchannels.command unsubscribe literal channel unsubscribe literal pattern1]

        assert_equal "User testuser has no permissions to access the 'nopattern1' channel" [r ACL DRYRUN testuser getchannels.command subscribe literal channel subscribe literal nopattern1]
        assert_equal "User testuser has no permissions to access the 'nopattern1' channel" [r ACL DRYRUN testuser getchannels.command publish literal channel subscribe literal nopattern1]
        assert_equal "OK" [r ACL DRYRUN testuser getchannels.command unsubscribe literal channel unsubscribe literal nopattern1]

        assert_equal "User testuser has no permissions to access the 'otherchannel' channel" [r ACL DRYRUN testuser getchannels.command subscribe literal otherchannel subscribe literal pattern1]
        assert_equal "User testuser has no permissions to access the 'otherchannel' channel" [r ACL DRYRUN testuser getchannels.command publish literal otherchannel subscribe literal pattern1]
        assert_equal "OK" [r ACL DRYRUN testuser getchannels.command unsubscribe literal otherchannel unsubscribe literal pattern1]
    }
    """
    r.run("module", "load", testmodule)
    r.run("ACL", "setuser", "testuser", "+@all", "resetchannels", "&channel", "&pattern*")
    assert "OK" == r.run(
        "ACL",
        "DRYRUN",
        "testuser",
        "getchannels.command",
        "subscribe",
        "literal",
        "channel",
        "subscribe",
        "literal",
        "pattern1",
    )
    assert "OK" == r.run(
        "ACL",
        "DRYRUN",
        "testuser",
        "getchannels.command",
        "publish",
        "literal",
        "channel",
        "publish",
        "literal",
        "pattern1",
    )
    assert "OK" == r.run(
        "ACL",
        "DRYRUN",
        "testuser",
        "getchannels.command",
        "unsubscribe",
        "literal",
        "channel",
        "unsubscribe",
        "literal",
        "pattern1",
    )
    assert "User testuser has no permissions to access the 'nopattern1' channel" == r.run(
        "ACL",
        "DRYRUN",
        "testuser",
        "getchannels.command",
        "subscribe",
        "literal",
        "channel",
        "subscribe",
        "literal",
        "nopattern1",
    )
    assert "User testuser has no permissions to access the 'nopattern1' channel" == r.run(
        "ACL",
        "DRYRUN",
        "testuser",
        "getchannels.command",
        "publish",
        "literal",
        "channel",
        "subscribe",
        "literal",
        "nopattern1",
    )
    assert "OK" == r.run(
        "ACL",
        "DRYRUN",
        "testuser",
        "getchannels.command",
        "unsubscribe",
        "literal",
        "channel",
        "unsubscribe",
        "literal",
        "nopattern1",
    )
    assert "User testuser has no permissions to access the 'otherchannel' channel" == r.run(
        "ACL",
        "DRYRUN",
        "testuser",
        "getchannels.command",
        "subscribe",
        "literal",
        "otherchannel",
        "subscribe",
        "literal",
        "pattern1",
    )
    assert "User testuser has no permissions to access the 'otherchannel' channel" == r.run(
        "ACL",
        "DRYRUN",
        "testuser",
        "getchannels.command",
        "publish",
        "literal",
        "otherchannel",
        "subscribe",
        "literal",
        "pattern1",
    )
    assert "OK" == r.run(
        "ACL",
        "DRYRUN",
        "testuser",
        "getchannels.command",
        "unsubscribe",
        "literal",
        "otherchannel",
        "unsubscribe",
        "literal",
        "pattern1",
    )


def test_module_getchannels_api_with_patterns_acl(r: ValkeyTestClient) -> None:
    """
    test "module getchannels-api with patterns - ACL" {
        assert_equal "OK" [r ACL DRYRUN testuser getchannels.command subscribe pattern pattern*]
        assert_equal "OK" [r ACL DRYRUN testuser getchannels.command publish pattern pattern*]
        assert_equal "OK" [r ACL DRYRUN testuser getchannels.command unsubscribe pattern pattern*]

        assert_equal "User testuser has no permissions to access the 'pattern1' channel" [r ACL DRYRUN testuser getchannels.command subscribe pattern pattern1 subscribe pattern pattern*]
        assert_equal "User testuser has no permissions to access the 'pattern1' channel" [r ACL DRYRUN testuser getchannels.command publish pattern pattern1 subscribe pattern pattern*]
        assert_equal "OK" [r ACL DRYRUN testuser getchannels.command unsubscribe pattern pattern1 unsubscribe pattern pattern*]

        assert_equal "User testuser has no permissions to access the 'otherpattern*' channel" [r ACL DRYRUN testuser getchannels.command subscribe pattern otherpattern* subscribe pattern pattern*]
        assert_equal "User testuser has no permissions to access the 'otherpattern*' channel" [r ACL DRYRUN testuser getchannels.command publish pattern otherpattern* subscribe pattern pattern*]
        assert_equal "OK" [r ACL DRYRUN testuser getchannels.command unsubscribe pattern otherpattern* unsubscribe pattern pattern*]
    }
    """
    r.run("module", "load", testmodule)
    r.run("ACL", "setuser", "testuser", "+@all", "resetchannels", "&channel", "&pattern*")
    assert "OK" == r.run("ACL", "DRYRUN", "testuser", "getchannels.command", "subscribe", "pattern", "pattern*")
    assert "OK" == r.run("ACL", "DRYRUN", "testuser", "getchannels.command", "publish", "pattern", "pattern*")
    assert "OK" == r.run("ACL", "DRYRUN", "testuser", "getchannels.command", "unsubscribe", "pattern", "pattern*")
    assert "User testuser has no permissions to access the 'pattern1' channel" == r.run(
        "ACL",
        "DRYRUN",
        "testuser",
        "getchannels.command",
        "subscribe",
        "pattern",
        "pattern1",
        "subscribe",
        "pattern",
        "pattern*",
    )
    assert "User testuser has no permissions to access the 'pattern1' channel" == r.run(
        "ACL",
        "DRYRUN",
        "testuser",
        "getchannels.command",
        "publish",
        "pattern",
        "pattern1",
        "subscribe",
        "pattern",
        "pattern*",
    )
    assert "OK" == r.run(
        "ACL",
        "DRYRUN",
        "testuser",
        "getchannels.command",
        "unsubscribe",
        "pattern",
        "pattern1",
        "unsubscribe",
        "pattern",
        "pattern*",
    )
    assert "User testuser has no permissions to access the 'otherpattern*' channel" == r.run(
        "ACL",
        "DRYRUN",
        "testuser",
        "getchannels.command",
        "subscribe",
        "pattern",
        "otherpattern*",
        "subscribe",
        "pattern",
        "pattern*",
    )
    assert "User testuser has no permissions to access the 'otherpattern*' channel" == r.run(
        "ACL",
        "DRYRUN",
        "testuser",
        "getchannels.command",
        "publish",
        "pattern",
        "otherpattern*",
        "subscribe",
        "pattern",
        "pattern*",
    )
    assert "OK" == r.run(
        "ACL",
        "DRYRUN",
        "testuser",
        "getchannels.command",
        "unsubscribe",
        "pattern",
        "otherpattern*",
        "unsubscribe",
        "pattern",
        "pattern*",
    )


def test_unload_the_module_getchannels(r: ValkeyTestClient) -> None:
    """
    test "Unload the module - getchannels" {
        assert_equal {OK} [r module unload getchannels]
    }
    """
    r.run("module", "load", testmodule)
    r.run("ACL", "setuser", "testuser", "+@all", "resetchannels", "&channel", "&pattern*")
    assert "OK" == r.run("module", "unload", "getchannels")
