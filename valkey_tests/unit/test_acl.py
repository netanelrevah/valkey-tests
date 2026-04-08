# ruff: noqa: PLR2004, F841, RUF043, ANN002, ANN201
import time
from fnmatch import fnmatch

import pytest

from tests.valkey_test_client import ValkeyTestClient

pytestmark = [pytest.mark.acl_external_skip]


def test_connections_start_with_the_default_user(r: ValkeyTestClient) -> None:
    """
    test {Connections start with the default user} {
        r ACL WHOAMI
    } {default}
    """
    assert r.run("ACL", "WHOAMI") == "default"


def test_it_is_possible_to_create_new_users(r: ValkeyTestClient) -> None:
    """
    test {It is possible to create new users} {
        r ACL setuser newuser
    }
    """
    r.run("ACL", "setuser", "newuser")


def test_coverage_acl_users(r: ValkeyTestClient) -> None:
    """
    test {Coverage: ACL USERS} {
        r ACL USERS
    } {default newuser}
    """
    assert r.run("ACL", "USERS") == "default newuser"


def test_usernames_can_not_contain_spaces_or_null_characters(r: ValkeyTestClient) -> None:
    """
    test {Usernames can not contain spaces or null characters} {
        catch {r ACL setuser "a a"} err
        set err
    } {*Usernames can't contain spaces or null characters*}
    """
    try:
        err = r.run("ACL", "setuser", "a a")
    except Exception as _catch_err:
        err = str(_catch_err)
    assert fnmatch(str(err), "*Usernames can't contain spaces or null characters*")


def test_new_users_start_disabled(r: ValkeyTestClient) -> None:
    """
    test {New users start disabled} {
        r ACL setuser newuser >passwd1
        catch {r AUTH newuser passwd1} err
        set err
    } {*WRONGPASS*}
    """
    r.run("ACL", "setuser", "newuser", ">passwd1")
    try:
        err = r.run("AUTH", "newuser", "passwd1")
    except Exception as _catch_err:
        err = str(_catch_err)
    assert fnmatch(str(err), "*WRONGPASS*")


def test_enabling_the_user_allows_the_login(r: ValkeyTestClient) -> None:
    """
    test {Enabling the user allows the login} {
        r ACL setuser newuser on +acl
        r AUTH newuser passwd1
        r ACL WHOAMI
    } {newuser}
    """
    r.run("ACL", "setuser", "newuser", "on", "+acl")
    r.run("AUTH", "newuser", "passwd1")
    assert r.run("ACL", "WHOAMI") == "newuser"


def test_only_the_set_of_correct_passwords_work(r: ValkeyTestClient) -> None:
    """
    test {Only the set of correct passwords work} {
        r ACL setuser newuser >passwd2
        catch {r AUTH newuser passwd1} e
        assert {$e eq "OK"}
        catch {r AUTH newuser passwd2} e
        assert {$e eq "OK"}
        catch {r AUTH newuser passwd3} e
        set e
    } {*WRONGPASS*}
    """
    r.run("ACL", "setuser", "newuser", ">passwd2")
    try:
        e = r.run("AUTH", "newuser", "passwd1")
    except Exception as _catch_err:
        e = str(_catch_err)
    assert e == "OK"
    try:
        e = r.run("AUTH", "newuser", "passwd2")
    except Exception as _catch_err:
        e = str(_catch_err)
    assert e == "OK"
    try:
        e = r.run("AUTH", "newuser", "passwd3")
    except Exception as _catch_err:
        e = str(_catch_err)
    assert fnmatch(str(e), "*WRONGPASS*")


def test_it_is_possible_to_remove_passwords_from_the_set_of_valid_ones(r: ValkeyTestClient) -> None:
    """
    test {It is possible to remove passwords from the set of valid ones} {
        r ACL setuser newuser <passwd1
        catch {r AUTH newuser passwd1} e
        set e
    } {*WRONGPASS*}
    """
    r.run("ACL", "setuser", "newuser", "<passwd1")
    try:
        e = r.run("AUTH", "newuser", "passwd1")
    except Exception as _catch_err:
        e = str(_catch_err)
    assert fnmatch(str(e), "*WRONGPASS*")


def test_test_password_hashes_can_be_added(r: ValkeyTestClient) -> None:
    """
    test {Test password hashes can be added} {
        r ACL setuser newuser #34344e4d60c2b6d639b7bd22e18f2b0b91bc34bf0ac5f9952744435093cfb4e6
        catch {r AUTH newuser passwd4} e
        assert {$e eq "OK"}
    }
    """
    r.run("ACL", "setuser", "newuser", "#34344e4d60c2b6d639b7bd22e18f2b0b91bc34bf0ac5f9952744435093cfb4e6")
    try:
        e = r.run("AUTH", "newuser", "passwd4")
    except Exception as _catch_err:
        e = str(_catch_err)
    assert e == "OK"


def test_test_password_hashes_validate_input(r: ValkeyTestClient) -> None:
    """
    test {Test password hashes validate input} {
        # Validate Length
        catch {r ACL setuser newuser #34344e4d60c2b6d639b7bd22e18f2b0b91bc34bf0ac5f9952744435093cfb4e} e
        # Validate character outside set
        catch {r ACL setuser newuser #34344e4d60c2b6d639b7bd22e18f2b0b91bc34bf0ac5f9952744435093cfb4eq} e
        set e
    } {*Error in ACL SETUSER modifier*}
    """
    try:
        e = r.run("ACL", "setuser", "newuser", "#34344e4d60c2b6d639b7bd22e18f2b0b91bc34bf0ac5f9952744435093cfb4e")
    except Exception as _catch_err:
        e = str(_catch_err)
    try:
        e = r.run("ACL", "setuser", "newuser", "#34344e4d60c2b6d639b7bd22e18f2b0b91bc34bf0ac5f9952744435093cfb4eq")
    except Exception as _catch_err:
        e = str(_catch_err)
    assert fnmatch(str(e), "*Error in ACL SETUSER modifier*")


def test_acl_getuser_returns_the_password_hash_instead_of_the_actual_password(r: ValkeyTestClient) -> None:
    """
    test {ACL GETUSER returns the password hash instead of the actual password} {
        set passstr [dict get [r ACL getuser newuser] passwords]
        assert_match {*34344e4d60c2b6d639b7bd22e18f2b0b91bc34bf0ac5f9952744435093cfb4e6*} $passstr
        assert_no_match {*passwd4*} $passstr
    }
    """
    passstr = r.run("ACL", "getuser", "newuser")["passwords"]
    assert fnmatch(str(passstr), "*34344e4d60c2b6d639b7bd22e18f2b0b91bc34bf0ac5f9952744435093cfb4e6*")
    assert_no_match("*passwd4*", passstr)


def test_test_hashed_passwords_removal(r: ValkeyTestClient) -> None:
    """
    test {Test hashed passwords removal} {
        r ACL setuser newuser !34344e4d60c2b6d639b7bd22e18f2b0b91bc34bf0ac5f9952744435093cfb4e6
        set passstr [dict get [r ACL getuser newuser] passwords]
        assert_no_match {*34344e4d60c2b6d639b7bd22e18f2b0b91bc34bf0ac5f9952744435093cfb4e6*} $passstr
    }
    """
    r.run("ACL", "setuser", "newuser", "!34344e4d60c2b6d639b7bd22e18f2b0b91bc34bf0ac5f9952744435093cfb4e6")
    passstr = r.run("ACL", "getuser", "newuser")["passwords"]
    assert_no_match("*34344e4d60c2b6d639b7bd22e18f2b0b91bc34bf0ac5f9952744435093cfb4e6*", passstr)


def test_by_default_users_are_not_able_to_access_any_command(r: ValkeyTestClient) -> None:
    """
    test {By default users are not able to access any command} {
        catch {r SET foo bar} e
        set e
    } {*NOPERM*set*}
    """
    try:
        e = r.run("SET", "foo", "bar")
    except Exception as _catch_err:
        e = str(_catch_err)
    assert fnmatch(str(e), "*NOPERM*set*")


def test_by_default_users_are_not_able_to_access_any_key(r: ValkeyTestClient) -> None:
    """
    test {By default users are not able to access any key} {
        r ACL setuser newuser +set
        catch {r SET foo bar} e
        set e
    } {*NOPERM*key*}
    """
    r.run("ACL", "setuser", "newuser", "+set")
    try:
        e = r.run("SET", "foo", "bar")
    except Exception as _catch_err:
        e = str(_catch_err)
    assert fnmatch(str(e), "*NOPERM*key*")


def test_it_s_possible_to_allow_the_access_of_a_subset_of_keys(r: ValkeyTestClient) -> None:
    """
    test {It's possible to allow the access of a subset of keys} {
        r ACL setuser newuser allcommands ~foo:* ~bar:*
        r SET foo:1 a
        r SET bar:2 b
        catch {r SET zap:3 c} e
        r ACL setuser newuser allkeys; # Undo keys ACL
        set e
    } {*NOPERM*key*}
    """
    r.run("ACL", "setuser", "newuser", "allcommands", "~foo:*", "~bar:*")
    r.run("SET", "foo:1", "a")
    r.run("SET", "bar:2", "b")
    try:
        e = r.run("SET", "zap:3", "c")
    except Exception as _catch_err:
        e = str(_catch_err)
    r.run("ACL", "setuser", "newuser", "allkeys")
    assert fnmatch(str(e), "*NOPERM*key*")


def test_by_default_only_default_user_is_able_to_publish_to_any_channel(r: ValkeyTestClient) -> None:
    """
    test {By default, only default user is able to publish to any channel} {
        r AUTH default pwd
        r PUBLISH foo bar
        r ACL setuser psuser on >pspass +acl +client +@pubsub
        r AUTH psuser pspass
        catch {r PUBLISH foo bar} e
        set e
    } {*NOPERM*channel*}
    """
    r.run("AUTH", "default", "pwd")
    r.run("PUBLISH", "foo", "bar")
    r.run("ACL", "setuser", "psuser", "on", ">pspass", "+acl", "+client", "+@pubsub")
    r.run("AUTH", "psuser", "pspass")
    try:
        e = r.run("PUBLISH", "foo", "bar")
    except Exception as _catch_err:
        e = str(_catch_err)
    assert fnmatch(str(e), "*NOPERM*channel*")


def test_by_default_only_default_user_is_not_able_to_publish_to_any_shard_channel(r: ValkeyTestClient) -> None:
    """
    test {By default, only default user is not able to publish to any shard channel} {
        r AUTH default pwd
        r SPUBLISH foo bar
        r AUTH psuser pspass
        catch {r SPUBLISH foo bar} e
        set e
    } {*NOPERM*channel*}
    """
    r.run("AUTH", "default", "pwd")
    r.run("SPUBLISH", "foo", "bar")
    r.run("AUTH", "psuser", "pspass")
    try:
        e = r.run("SPUBLISH", "foo", "bar")
    except Exception as _catch_err:
        e = str(_catch_err)
    assert fnmatch(str(e), "*NOPERM*channel*")


def test_by_default_only_default_user_is_able_to_subscribe_to_any_channel(r: ValkeyTestClient) -> None:
    """
    test {By default, only default user is able to subscribe to any channel} {
        set rd [valkey_deferring_client]
        $rd AUTH default pwd
        $rd read
        $rd SUBSCRIBE foo
        assert_match {subscribe foo 1} [$rd read]
        $rd UNSUBSCRIBE
        $rd read
        $rd AUTH psuser pspass
        $rd read
        $rd SUBSCRIBE foo
        catch {$rd read} e
        $rd close
        set e
    } {*NOPERM*channel*}
    """
    rd = ValkeyTestClient.create_from(r)
    rd.run("AUTH", "default", "pwd")
    rd.run("read")
    rd.run("SUBSCRIBE", "foo")
    assert fnmatch(str(rd.run("read")), "subscribe foo 1")
    rd.run("UNSUBSCRIBE")
    rd.run("read")
    rd.run("AUTH", "psuser", "pspass")
    rd.run("read")
    rd.run("SUBSCRIBE", "foo")
    try:
        e = rd.run("read")
    except Exception as _catch_err:
        e = str(_catch_err)
    rd.run("close")
    assert fnmatch(str(e), "*NOPERM*channel*")


def test_by_default_only_default_user_is_able_to_subscribe_to_any_shard_channel(r: ValkeyTestClient) -> None:
    """
    test {By default, only default user is able to subscribe to any shard channel} {
        set rd [valkey_deferring_client]
        $rd AUTH default pwd
        $rd read
        $rd SSUBSCRIBE foo
        assert_match {ssubscribe foo 1} [$rd read]
        $rd SUNSUBSCRIBE
        $rd read
        $rd AUTH psuser pspass
        $rd read
        $rd SSUBSCRIBE foo
        catch {$rd read} e
        $rd close
        set e
    } {*NOPERM*channel*}
    """
    rd = ValkeyTestClient.create_from(r)
    rd.run("AUTH", "default", "pwd")
    rd.run("read")
    rd.run("SSUBSCRIBE", "foo")
    assert fnmatch(str(rd.run("read")), "ssubscribe foo 1")
    rd.run("SUNSUBSCRIBE")
    rd.run("read")
    rd.run("AUTH", "psuser", "pspass")
    rd.run("read")
    rd.run("SSUBSCRIBE", "foo")
    try:
        e = rd.run("read")
    except Exception as _catch_err:
        e = str(_catch_err)
    rd.run("close")
    assert fnmatch(str(e), "*NOPERM*channel*")


def test_by_default_only_default_user_is_able_to_subscribe_to_any_pattern(r: ValkeyTestClient) -> None:
    """
    test {By default, only default user is able to subscribe to any pattern} {
        set rd [valkey_deferring_client]
        $rd AUTH default pwd
        $rd read
        $rd PSUBSCRIBE bar*
        assert_match {psubscribe bar\* 1} [$rd read]
        $rd PUNSUBSCRIBE
        $rd read
        $rd AUTH psuser pspass
        $rd read
        $rd PSUBSCRIBE bar*
        catch {$rd read} e
        $rd close
        set e
    } {*NOPERM*channel*}
    """
    rd = ValkeyTestClient.create_from(r)
    rd.run("AUTH", "default", "pwd")
    rd.run("read")
    rd.run("PSUBSCRIBE", "bar*")
    assert fnmatch(str(rd.run("read")), "psubscribe bar\\* 1")
    rd.run("PUNSUBSCRIBE")
    rd.run("read")
    rd.run("AUTH", "psuser", "pspass")
    rd.run("read")
    rd.run("PSUBSCRIBE", "bar*")
    try:
        e = rd.run("read")
    except Exception as _catch_err:
        e = str(_catch_err)
    rd.run("close")
    assert fnmatch(str(e), "*NOPERM*channel*")


def test_it_s_possible_to_allow_publishing_to_a_subset_of_channels(r: ValkeyTestClient) -> None:
    """
    test {It's possible to allow publishing to a subset of channels} {
        r ACL setuser psuser resetchannels &foo:1 &bar:*
        assert_equal {0} [r PUBLISH foo:1 somemessage]
        assert_equal {0} [r PUBLISH bar:2 anothermessage]
        catch {r PUBLISH zap:3 nosuchmessage} e
        set e
    } {*NOPERM*channel*}
    """
    r.run("ACL", "setuser", "psuser", "resetchannels", "&foo:1", "&bar:*")
    assert "0" == r.run("PUBLISH", "foo:1", "somemessage")
    assert "0" == r.run("PUBLISH", "bar:2", "anothermessage")
    try:
        e = r.run("PUBLISH", "zap:3", "nosuchmessage")
    except Exception as _catch_err:
        e = str(_catch_err)
    assert fnmatch(str(e), "*NOPERM*channel*")


def test_it_s_possible_to_allow_publishing_to_a_subset_of_shard_channels(r: ValkeyTestClient) -> None:
    """
    test {It's possible to allow publishing to a subset of shard channels} {
        r ACL setuser psuser resetchannels &foo:1 &bar:*
        assert_equal {0} [r SPUBLISH foo:1 somemessage]
        assert_equal {0} [r SPUBLISH bar:2 anothermessage]
        catch {r SPUBLISH zap:3 nosuchmessage} e
        set e
    } {*NOPERM*channel*}
    """
    r.run("ACL", "setuser", "psuser", "resetchannels", "&foo:1", "&bar:*")
    assert "0" == r.run("SPUBLISH", "foo:1", "somemessage")
    assert "0" == r.run("SPUBLISH", "bar:2", "anothermessage")
    try:
        e = r.run("SPUBLISH", "zap:3", "nosuchmessage")
    except Exception as _catch_err:
        e = str(_catch_err)
    assert fnmatch(str(e), "*NOPERM*channel*")


def test_validate_subset_of_channels_is_prefixed_with_resetchannels_flag(r: ValkeyTestClient) -> None:
    """
    test {Validate subset of channels is prefixed with resetchannels flag} {
        r ACL setuser hpuser on nopass resetchannels &foo +@all

        # Verify resetchannels flag is prefixed before the channel name(s)
        set users [r ACL LIST]
        set curruser "hpuser"
        foreach user [lshuffle $users] {
            if {[string first $curruser $user] != -1} {
                assert_equal {user hpuser on nopass sanitize-payload resetchannels &foo alldbs +@all} $user
            }
        }

        # authenticate as hpuser
        r AUTH hpuser pass

        assert_equal {0} [r PUBLISH foo bar]
        catch {r PUBLISH bar game} e

        # Falling back to psuser for the below tests
        r AUTH psuser pspass
        r ACL deluser hpuser
        set e
    } {*NOPERM*channel*}
    """
    r.run("ACL", "setuser", "hpuser", "on", "nopass", "resetchannels", "&foo", "+@all")
    users = r.run("ACL", "LIST")
    curruser = "hpuser"
    foreach(
        "user",
        lshuffle(users),
        "            if {[string first $curruser $user] != -1} {\n                assert_equal {user hpuser on nopass sanitize-payload resetchannels &foo alldbs +@all} $user\n            }\n        ",
    )
    r.run("AUTH", "hpuser", "pass")
    assert "0" == r.run("PUBLISH", "foo", "bar")
    try:
        e = r.run("PUBLISH", "bar", "game")
    except Exception as _catch_err:
        e = str(_catch_err)
    r.run("AUTH", "psuser", "pspass")
    r.run("ACL", "deluser", "hpuser")
    assert fnmatch(str(e), "*NOPERM*channel*")


def test_in_transaction_queue_publish_or_subscribe_or_psubscribe_to_unauthorized_channel_will_fail(
    r: ValkeyTestClient,
) -> None:
    """
    test {In transaction queue publish/subscribe/psubscribe to unauthorized channel will fail} {
        r ACL setuser psuser +multi +discard
        r MULTI
        assert_error {*NOPERM*channel*} {r PUBLISH notexits helloworld}
        r DISCARD
        r MULTI
        assert_error {*NOPERM*channel*} {r SUBSCRIBE notexits foo:1}
        r DISCARD
        r MULTI
        assert_error {*NOPERM*channel*} {r PSUBSCRIBE notexits:* bar:*}
        r DISCARD
    }
    """
    r.run("ACL", "setuser", "psuser", "+multi", "+discard")
    r.run("MULTI")
    with pytest.raises(Exception, match=".*NOPERM.*channel.*"):
        r.run("PUBLISH", "notexits", "helloworld")
    r.run("DISCARD")
    r.run("MULTI")
    with pytest.raises(Exception, match=".*NOPERM.*channel.*"):
        r.run("SUBSCRIBE", "notexits", "foo:1")
    r.run("DISCARD")
    r.run("MULTI")
    with pytest.raises(Exception, match=".*NOPERM.*channel.*"):
        r.run("PSUBSCRIBE", "notexits:*", "bar:*")
    r.run("DISCARD")


def test_it_s_possible_to_allow_subscribing_to_a_subset_of_channels(r: ValkeyTestClient) -> None:
    """
    test {It's possible to allow subscribing to a subset of channels} {
        set rd [valkey_deferring_client]
        $rd AUTH psuser pspass
        $rd read
        $rd SUBSCRIBE foo:1
        assert_match {subscribe foo:1 1} [$rd read]
        $rd SUBSCRIBE bar:2
        assert_match {subscribe bar:2 2} [$rd read]
        $rd SUBSCRIBE zap:3
        catch {$rd read} e
        set e
    } {*NOPERM*channel*}
    """
    rd = ValkeyTestClient.create_from(r)
    rd.run("AUTH", "psuser", "pspass")
    rd.run("read")
    rd.run("SUBSCRIBE", "foo:1")
    assert fnmatch(str(rd.run("read")), "subscribe foo:1 1")
    rd.run("SUBSCRIBE", "bar:2")
    assert fnmatch(str(rd.run("read")), "subscribe bar:2 2")
    rd.run("SUBSCRIBE", "zap:3")
    try:
        e = rd.run("read")
    except Exception as _catch_err:
        e = str(_catch_err)
    assert fnmatch(str(e), "*NOPERM*channel*")


def test_it_s_possible_to_allow_subscribing_to_a_subset_of_shard_channels(r: ValkeyTestClient) -> None:
    """
    test {It's possible to allow subscribing to a subset of shard channels} {
        set rd [valkey_deferring_client]
        $rd AUTH psuser pspass
        $rd read
        $rd SSUBSCRIBE foo:1
        assert_match {ssubscribe foo:1 1} [$rd read]
        $rd SSUBSCRIBE bar:2
        assert_match {ssubscribe bar:2 2} [$rd read]
        $rd SSUBSCRIBE zap:3
        catch {$rd read} e
        set e
    } {*NOPERM*channel*}
    """
    rd = ValkeyTestClient.create_from(r)
    rd.run("AUTH", "psuser", "pspass")
    rd.run("read")
    rd.run("SSUBSCRIBE", "foo:1")
    assert fnmatch(str(rd.run("read")), "ssubscribe foo:1 1")
    rd.run("SSUBSCRIBE", "bar:2")
    assert fnmatch(str(rd.run("read")), "ssubscribe bar:2 2")
    rd.run("SSUBSCRIBE", "zap:3")
    try:
        e = rd.run("read")
    except Exception as _catch_err:
        e = str(_catch_err)
    assert fnmatch(str(e), "*NOPERM*channel*")


def test_it_s_possible_to_allow_subscribing_to_a_subset_of_channel_patterns(r: ValkeyTestClient) -> None:
    """
    test {It's possible to allow subscribing to a subset of channel patterns} {
        set rd [valkey_deferring_client]
        $rd AUTH psuser pspass
        $rd read
        $rd PSUBSCRIBE foo:1
        assert_match {psubscribe foo:1 1} [$rd read]
        $rd PSUBSCRIBE bar:*
        assert_match {psubscribe bar:\* 2} [$rd read]
        $rd PSUBSCRIBE bar:baz
        catch {$rd read} e
        set e
    } {*NOPERM*channel*}
    """
    rd = ValkeyTestClient.create_from(r)
    rd.run("AUTH", "psuser", "pspass")
    rd.run("read")
    rd.run("PSUBSCRIBE", "foo:1")
    assert fnmatch(str(rd.run("read")), "psubscribe foo:1 1")
    rd.run("PSUBSCRIBE", "bar:*")
    assert fnmatch(str(rd.run("read")), "psubscribe bar:\\* 2")
    rd.run("PSUBSCRIBE", "bar:baz")
    try:
        e = rd.run("read")
    except Exception as _catch_err:
        e = str(_catch_err)
    assert fnmatch(str(e), "*NOPERM*channel*")


def test_subscribers_are_killed_when_revoked_of_channel_permission(r: ValkeyTestClient) -> None:
    """
    test {Subscribers are killed when revoked of channel permission} {
        set rd [valkey_deferring_client]
        r ACL setuser psuser resetchannels &foo:1
        $rd AUTH psuser pspass
        $rd read
        $rd CLIENT SETNAME deathrow
        $rd read
        $rd SUBSCRIBE foo:1
        $rd read
        r ACL setuser psuser resetchannels
        assert_no_match {*deathrow*} [r CLIENT LIST]
        $rd close
    } {0}
    """
    rd = ValkeyTestClient.create_from(r)
    r.run("ACL", "setuser", "psuser", "resetchannels", "&foo:1")
    rd.run("AUTH", "psuser", "pspass")
    rd.run("read")
    rd.run("CLIENT", "SETNAME", "deathrow")
    rd.run("read")
    rd.run("SUBSCRIBE", "foo:1")
    rd.run("read")
    r.run("ACL", "setuser", "psuser", "resetchannels")
    assert_no_match("*deathrow*", r.run("CLIENT", "LIST"))
    rd.run("close")


def test_subscribers_are_killed_when_revoked_of_channel_permission_1(r: ValkeyTestClient) -> None:
    """
    test {Subscribers are killed when revoked of channel permission} {
        set rd [valkey_deferring_client]
        r ACL setuser psuser resetchannels &foo:1
        $rd AUTH psuser pspass
        $rd read
        $rd CLIENT SETNAME deathrow
        $rd read
        $rd SSUBSCRIBE foo:1
        $rd read
        r ACL setuser psuser resetchannels
        assert_no_match {*deathrow*} [r CLIENT LIST]
        $rd close
    } {0}
    """
    rd = ValkeyTestClient.create_from(r)
    r.run("ACL", "setuser", "psuser", "resetchannels", "&foo:1")
    rd.run("AUTH", "psuser", "pspass")
    rd.run("read")
    rd.run("CLIENT", "SETNAME", "deathrow")
    rd.run("read")
    rd.run("SSUBSCRIBE", "foo:1")
    rd.run("read")
    r.run("ACL", "setuser", "psuser", "resetchannels")
    assert_no_match("*deathrow*", r.run("CLIENT", "LIST"))
    rd.run("close")


def test_subscribers_are_killed_when_revoked_of_pattern_permission(r: ValkeyTestClient) -> None:
    """
    test {Subscribers are killed when revoked of pattern permission} {
        set rd [valkey_deferring_client]
        r ACL setuser psuser resetchannels &bar:*
        $rd AUTH psuser pspass
        $rd read
        $rd CLIENT SETNAME deathrow
        $rd read
        $rd PSUBSCRIBE bar:*
        $rd read
        r ACL setuser psuser resetchannels
        assert_no_match {*deathrow*} [r CLIENT LIST]
        $rd close
    } {0}
    """
    rd = ValkeyTestClient.create_from(r)
    r.run("ACL", "setuser", "psuser", "resetchannels", "&bar:*")
    rd.run("AUTH", "psuser", "pspass")
    rd.run("read")
    rd.run("CLIENT", "SETNAME", "deathrow")
    rd.run("read")
    rd.run("PSUBSCRIBE", "bar:*")
    rd.run("read")
    r.run("ACL", "setuser", "psuser", "resetchannels")
    assert_no_match("*deathrow*", r.run("CLIENT", "LIST"))
    rd.run("close")


def test_subscribers_are_killed_when_revoked_of_allchannels_permission(r: ValkeyTestClient) -> None:
    """
    test {Subscribers are killed when revoked of allchannels permission} {
        set rd [valkey_deferring_client]
        r ACL setuser psuser allchannels
        $rd AUTH psuser pspass
        $rd read
        $rd CLIENT SETNAME deathrow
        $rd read
        $rd PSUBSCRIBE foo
        $rd read
        r ACL setuser psuser resetchannels
        assert_no_match {*deathrow*} [r CLIENT LIST]
        $rd close
    } {0}
    """
    rd = ValkeyTestClient.create_from(r)
    r.run("ACL", "setuser", "psuser", "allchannels")
    rd.run("AUTH", "psuser", "pspass")
    rd.run("read")
    rd.run("CLIENT", "SETNAME", "deathrow")
    rd.run("read")
    rd.run("PSUBSCRIBE", "foo")
    rd.run("read")
    r.run("ACL", "setuser", "psuser", "resetchannels")
    assert_no_match("*deathrow*", r.run("CLIENT", "LIST"))
    rd.run("close")


def test_subscribers_are_pardoned_if_literal_permissions_are_retained_and_or_or_gaining_allchannels(
    r: ValkeyTestClient,
) -> None:
    """
    test {Subscribers are pardoned if literal permissions are retained and/or gaining allchannels} {
        set rd [valkey_deferring_client]
        r ACL setuser psuser resetchannels &foo:1 &bar:* &orders
        $rd AUTH psuser pspass
        $rd read
        $rd CLIENT SETNAME pardoned
        $rd read
        $rd SUBSCRIBE foo:1
        $rd read
        $rd SSUBSCRIBE orders
        $rd read
        $rd PSUBSCRIBE bar:*
        $rd read
        r ACL setuser psuser resetchannels &foo:1 &bar:* &orders &baz:qaz &zoo:*
        assert_match {*pardoned*} [r CLIENT LIST]
        r ACL setuser psuser allchannels
        assert_match {*pardoned*} [r CLIENT LIST]
        $rd close
    } {0}
    """
    rd = ValkeyTestClient.create_from(r)
    r.run("ACL", "setuser", "psuser", "resetchannels", "&foo:1", "&bar:*", "&orders")
    rd.run("AUTH", "psuser", "pspass")
    rd.run("read")
    rd.run("CLIENT", "SETNAME", "pardoned")
    rd.run("read")
    rd.run("SUBSCRIBE", "foo:1")
    rd.run("read")
    rd.run("SSUBSCRIBE", "orders")
    rd.run("read")
    rd.run("PSUBSCRIBE", "bar:*")
    rd.run("read")
    r.run("ACL", "setuser", "psuser", "resetchannels", "&foo:1", "&bar:*", "&orders", "&baz:qaz", "&zoo:*")
    assert fnmatch(str(r.run("CLIENT", "LIST")), "*pardoned*")
    r.run("ACL", "setuser", "psuser", "allchannels")
    assert fnmatch(str(r.run("CLIENT", "LIST")), "*pardoned*")
    rd.run("close")


def test_blocked_command_gets_rejected_when_reprocessed_after_permission_change(r: ValkeyTestClient) -> None:
    """
    test {blocked command gets rejected when reprocessed after permission change} {
        r auth default ""
        r config resetstat
        set rd [valkey_deferring_client]
        r ACL setuser psuser reset on nopass +@all allkeys
        $rd AUTH psuser pspass
        $rd read
        $rd BLPOP list1 0
        wait_for_blocked_client
        r ACL setuser psuser resetkeys
        r LPUSH list1 foo
        assert_error {*NOPERM No permissions to access a key*} {$rd read}
        $rd ping
        $rd close
        assert_match {*calls=0,usec=0,*,rejected_calls=1,failed_calls=0} [cmdrstat blpop r]
    }
    """
    r.run("auth", "default", "")
    r.run("config", "resetstat")
    rd = ValkeyTestClient.create_from(r)
    r.run("ACL", "setuser", "psuser", "reset", "on", "nopass", "+@all", "allkeys")
    rd.run("AUTH", "psuser", "pspass")
    rd.run("read")
    rd.run("BLPOP", "list1", 0)
    wait_for_blocked_client()
    r.run("ACL", "setuser", "psuser", "resetkeys")
    r.run("LPUSH", "list1", "foo")
    assert_error("*NOPERM No permissions to access a key*", "$rd read")
    rd.run("ping")
    rd.run("close")
    assert fnmatch(str(cmdrstat("blpop", "r")), "*calls=0,usec=0,*,rejected_calls=1,failed_calls=0")


def test_users_can_be_configured_to_authenticate_with_any_password(r: ValkeyTestClient) -> None:
    """
    test {Users can be configured to authenticate with any password} {
        r ACL setuser newuser nopass
        r AUTH newuser zipzapblabla
    } {OK}
    """
    r.run("ACL", "setuser", "newuser", "nopass")
    assert r.run("AUTH", "newuser", "zipzapblabla") == "OK"


def test_acls_can_exclude_single_commands(r: ValkeyTestClient) -> None:
    """
    test {ACLs can exclude single commands} {
        r ACL setuser newuser -ping
        r INCR mycounter ; # Should not raise an error
        catch {r PING} e
        set e
    } {*NOPERM*ping*}
    """
    r.run("ACL", "setuser", "newuser", "-ping")
    r.run("INCR", "mycounter")
    try:
        e = r.run("PING")
    except Exception as _catch_err:
        e = str(_catch_err)
    assert fnmatch(str(e), "*NOPERM*ping*")


def test_acls_can_include_or_exclude_whole_classes_of_commands(r: ValkeyTestClient) -> None:
    """
    test {ACLs can include or exclude whole classes of commands} {
        r ACL setuser newuser -@all +@set +acl
        r SADD myset a b c; # Should not raise an error
        r ACL setuser newuser +@all -@string
        r SADD myset a b c; # Again should not raise an error
        # String commands instead should raise an error
        catch {r SET foo bar} e
        r ACL setuser newuser allcommands; # Undo commands ACL
        set e
    } {*NOPERM*set*}
    """
    r.run("ACL", "setuser", "newuser", "-@all", "+@set", "+acl")
    r.run("SADD", "myset", "a", "b", "c")
    r.run("ACL", "setuser", "newuser", "+@all", "-@string")
    r.run("SADD", "myset", "a", "b", "c")
    try:
        e = r.run("SET", "foo", "bar")
    except Exception as _catch_err:
        e = str(_catch_err)
    r.run("ACL", "setuser", "newuser", "allcommands")
    assert fnmatch(str(e), "*NOPERM*set*")


def test_acls_can_include_single_subcommands(r: ValkeyTestClient) -> None:
    """
    test {ACLs can include single subcommands} {
        r ACL setuser newuser +@all -client
        r ACL setuser newuser +client|id +client|setname
        set cmdstr [dict get [r ACL getuser newuser] commands]
        assert_match {+@all*-client*+client|id*} $cmdstr
        assert_match {+@all*-client*+client|setname*} $cmdstr
        r CLIENT ID; # Should not fail
        r CLIENT SETNAME foo ; # Should not fail
        catch {r CLIENT KILL type master} e
        set e
    } {*NOPERM*client|kill*}
    """
    r.run("ACL", "setuser", "newuser", "+@all", "-client")
    r.run("ACL", "setuser", "newuser", "+client|id", "+client|setname")
    cmdstr = r.run("ACL", "getuser", "newuser")["commands"]
    assert fnmatch(str(cmdstr), "+@all*-client*+client|id*")
    assert fnmatch(str(cmdstr), "+@all*-client*+client|setname*")
    r.run("CLIENT", "ID")
    r.run("CLIENT", "SETNAME", "foo")
    try:
        e = r.run("CLIENT", "KILL", "type", "master")
    except Exception as _catch_err:
        e = str(_catch_err)
    assert fnmatch(str(e), "*NOPERM*client|kill*")


def test_acls_can_exclude_single_subcommands_case_1(r: ValkeyTestClient) -> None:
    """
    test {ACLs can exclude single subcommands, case 1} {
        r ACL setuser newuser +@all -client|kill
        set cmdstr [dict get [r ACL getuser newuser] commands]
        assert_equal {+@all -client|kill} $cmdstr
        r CLIENT ID; # Should not fail
        r CLIENT SETNAME foo ; # Should not fail
        catch {r CLIENT KILL type master} e
        set e
    } {*NOPERM*client|kill*}
    """
    r.run("ACL", "setuser", "newuser", "+@all", "-client|kill")
    cmdstr = r.run("ACL", "getuser", "newuser")["commands"]
    assert "+@all -client|kill" == cmdstr
    r.run("CLIENT", "ID")
    r.run("CLIENT", "SETNAME", "foo")
    try:
        e = r.run("CLIENT", "KILL", "type", "master")
    except Exception as _catch_err:
        e = str(_catch_err)
    assert fnmatch(str(e), "*NOPERM*client|kill*")


def test_acls_can_exclude_single_subcommands_case_2(r: ValkeyTestClient) -> None:
    """
    test {ACLs can exclude single subcommands, case 2} {
        r ACL setuser newuser -@all +acl +config -config|set
        set cmdstr [dict get [r ACL getuser newuser] commands]
        assert_match {*+config*} $cmdstr
        assert_match {*-config|set*} $cmdstr
        r CONFIG GET loglevel; # Should not fail
        catch {r CONFIG SET loglevel debug} e
        set e
    } {*NOPERM*config|set*}
    """
    r.run("ACL", "setuser", "newuser", "-@all", "+acl", "+config", "-config|set")
    cmdstr = r.run("ACL", "getuser", "newuser")["commands"]
    assert fnmatch(str(cmdstr), "*+config*")
    assert fnmatch(str(cmdstr), "*-config|set*")
    r.run("CONFIG", "GET", "loglevel")
    try:
        e = r.run("CONFIG", "SET", "loglevel", "debug")
    except Exception as _catch_err:
        e = str(_catch_err)
    assert fnmatch(str(e), "*NOPERM*config|set*")


def test_acls_cannot_include_a_subcommand_with_a_specific_arg(r: ValkeyTestClient) -> None:
    """
    test {ACLs cannot include a subcommand with a specific arg} {
        r ACL setuser newuser +@all -config|get
        catch { r ACL setuser newuser +config|get|appendonly} e
        set e
    } {*Allowing first-arg of a subcommand is not supported*}
    """
    r.run("ACL", "setuser", "newuser", "+@all", "-config|get")
    try:
        e = r.run("ACL", "setuser", "newuser", "+config|get|appendonly")
    except Exception as _catch_err:
        e = str(_catch_err)
    assert fnmatch(str(e), "*Allowing first-arg of a subcommand is not supported*")


def test_acls_cannot_exclude_or_include_a_container_commands_with_a_specific_arg(r: ValkeyTestClient) -> None:
    """
    test {ACLs cannot exclude or include a container commands with a specific arg} {
        r ACL setuser newuser +@all +config|get
        catch { r ACL setuser newuser +@all +config|asdf} e
        assert_match "*Unknown command or category name in ACL*" $e
        catch { r ACL setuser newuser +@all -config|asdf} e
        assert_match "*Unknown command or category name in ACL*" $e
    } {}
    """
    r.run("ACL", "setuser", "newuser", "+@all", "+config|get")
    try:
        e = r.run("ACL", "setuser", "newuser", "+@all", "+config|asdf")
    except Exception as _catch_err:
        e = str(_catch_err)
    assert fnmatch(str(e), "*Unknown command or category name in ACL*")
    try:
        e = r.run("ACL", "setuser", "newuser", "+@all", "-config|asdf")
    except Exception as _catch_err:
        e = str(_catch_err)
    assert fnmatch(str(e), "*Unknown command or category name in ACL*")


def test_acls_cannot_exclude_or_include_a_container_command_with_two_args(r: ValkeyTestClient) -> None:
    """
    test {ACLs cannot exclude or include a container command with two args} {
        r ACL setuser newuser +@all +config|get
        catch { r ACL setuser newuser +@all +get|key1|key2} e
        assert_match "*Unknown command or category name in ACL*" $e
        catch { r ACL setuser newuser +@all -get|key1|key2} e
        assert_match "*Unknown command or category name in ACL*" $e
    } {}
    """
    r.run("ACL", "setuser", "newuser", "+@all", "+config|get")
    try:
        e = r.run("ACL", "setuser", "newuser", "+@all", "+get|key1|key2")
    except Exception as _catch_err:
        e = str(_catch_err)
    assert fnmatch(str(e), "*Unknown command or category name in ACL*")
    try:
        e = r.run("ACL", "setuser", "newuser", "+@all", "-get|key1|key2")
    except Exception as _catch_err:
        e = str(_catch_err)
    assert fnmatch(str(e), "*Unknown command or category name in ACL*")


def test_acls_including_of_a_type_includes_also_subcommands(r: ValkeyTestClient) -> None:
    """
    test {ACLs including of a type includes also subcommands} {
        r ACL setuser newuser -@all +del +acl +@stream
        r DEL key
        r XADD key * field value
        r XINFO STREAM key
    }
    """
    r.run("ACL", "setuser", "newuser", "-@all", "+del", "+acl", "+@stream")
    r.run("DEL", "key")
    r.run("XADD", "key", "*", "field", "value")
    r.run("XINFO", "STREAM", "key")


def test_acls_can_block_select_of_all_but_a_specific_db(r: ValkeyTestClient) -> None:
    """
    test {ACLs can block SELECT of all but a specific DB} {
        r ACL setuser newuser -@all +acl +select|0
        set cmdstr [dict get [r ACL getuser newuser] commands]
        assert_match {*+select|0*} $cmdstr
        r SELECT 0
        catch {r SELECT 1} e
        set e
    } {*NOPERM*select*} {singledb:skip}
    """
    r.run("ACL", "setuser", "newuser", "-@all", "+acl", "+select|0")
    cmdstr = r.run("ACL", "getuser", "newuser")["commands"]
    assert fnmatch(str(cmdstr), "*+select|0*")
    r.run("SELECT", 0)
    try:
        e = r.run("SELECT", 1)
    except Exception as _catch_err:
        e = str(_catch_err)
    assert fnmatch(str(e), "*NOPERM*select*")


def test_acls_can_block_all_debug_subcommands_except_one(r: ValkeyTestClient) -> None:
    """
    test {ACLs can block all DEBUG subcommands except one} {
        r ACL setuser newuser -@all +acl +del +incr +debug|object
        r DEL key
        set cmdstr [dict get [r ACL getuser newuser] commands]
        assert_match {*+debug|object*} $cmdstr
        r INCR key
        r DEBUG OBJECT key
        catch {r DEBUG SEGFAULT} e
        set e
    } {*NOPERM*debug*}
    """
    r.run("ACL", "setuser", "newuser", "-@all", "+acl", "+del", "+incr", "+debug|object")
    r.run("DEL", "key")
    cmdstr = r.run("ACL", "getuser", "newuser")["commands"]
    assert fnmatch(str(cmdstr), "*+debug|object*")
    r.run("INCR", "key")
    r.run("DEBUG", "OBJECT", "key")
    try:
        e = r.run("DEBUG", "SEGFAULT")
    except Exception as _catch_err:
        e = str(_catch_err)
    assert fnmatch(str(e), "*NOPERM*debug*")


def test_acls_set_can_include_subcommands_if_already_full_command_exists(r: ValkeyTestClient) -> None:
    """
    test {ACLs set can include subcommands, if already full command exists} {
        r ACL setuser bob +memory|doctor
        set cmdstr [dict get [r ACL getuser bob] commands]
        assert_equal {-@all +memory|doctor} $cmdstr

        # Validate the commands have got engulfed to +memory.
        r ACL setuser bob +memory
        set cmdstr [dict get [r ACL getuser bob] commands]
        assert_equal {-@all +memory} $cmdstr

        # Appending to the existing access string of bob.
        r ACL setuser bob +@all +client|id
        # Although this does nothing, we retain it anyways so we can reproduce
        # the original ACL.
        set cmdstr [dict get [r ACL getuser bob] commands]
        assert_equal {+@all +client|id} $cmdstr

        r ACL setuser bob >passwd1 on
        r AUTH bob passwd1
        r CLIENT ID; # Should not fail
        r MEMORY DOCTOR; # Should not fail
    }
    """
    r.run("ACL", "setuser", "bob", "+memory|doctor")
    cmdstr = r.run("ACL", "getuser", "bob")["commands"]
    assert "-@all +memory|doctor" == cmdstr
    r.run("ACL", "setuser", "bob", "+memory")
    cmdstr = r.run("ACL", "getuser", "bob")["commands"]
    assert "-@all +memory" == cmdstr
    r.run("ACL", "setuser", "bob", "+@all", "+client|id")
    cmdstr = r.run("ACL", "getuser", "bob")["commands"]
    assert "+@all +client|id" == cmdstr
    r.run("ACL", "setuser", "bob", ">passwd1", "on")
    r.run("AUTH", "bob", "passwd1")
    r.run("CLIENT", "ID")
    r.run("MEMORY", "DOCTOR")


def test_acls_set_can_exclude_subcommands_if_already_full_command_exists(r: ValkeyTestClient) -> None:
    """
    test {ACLs set can exclude subcommands, if already full command exists} {
        r ACL setuser alice +@all -memory|doctor
        set cmdstr [dict get [r ACL getuser alice] commands]
        assert_equal {+@all -memory|doctor} $cmdstr

        r ACL setuser alice >passwd1 on
        r AUTH alice passwd1

        assert_error {*NOPERM*memory|doctor*} {r MEMORY DOCTOR}
        r MEMORY STATS ;# should work

        # Validate the commands have got engulfed to -memory.
        r ACL setuser alice +@all -memory
        set cmdstr [dict get [r ACL getuser alice] commands]
        assert_equal {+@all -memory} $cmdstr

        assert_error {*NOPERM*memory|doctor*} {r MEMORY DOCTOR}
        assert_error {*NOPERM*memory|stats*} {r MEMORY STATS}

        # Appending to the existing access string of alice.
        r ACL setuser alice -@all

        # Now, alice can't do anything, we need to auth newuser to execute ACL GETUSER
        r AUTH newuser passwd1

        # Validate the new commands has got engulfed to -@all.
        set cmdstr [dict get [r ACL getuser alice] commands]
        assert_equal {-@all} $cmdstr

        r AUTH alice passwd1

        assert_error {*NOPERM*get*} {r GET key}
        assert_error {*NOPERM*memory|stats*} {r MEMORY STATS}

        # Auth newuser before the next test
        r AUTH newuser passwd1
    }
    """
    r.run("ACL", "setuser", "alice", "+@all", "-memory|doctor")
    cmdstr = r.run("ACL", "getuser", "alice")["commands"]
    assert "+@all -memory|doctor" == cmdstr
    r.run("ACL", "setuser", "alice", ">passwd1", "on")
    r.run("AUTH", "alice", "passwd1")
    with pytest.raises(Exception, match=".*NOPERM.*memory\\|doctor.*"):
        r.run("MEMORY", "DOCTOR")
    r.run("MEMORY", "STATS")
    r.run("ACL", "setuser", "alice", "+@all", "-memory")
    cmdstr = r.run("ACL", "getuser", "alice")["commands"]
    assert "+@all -memory" == cmdstr
    with pytest.raises(Exception, match=".*NOPERM.*memory\\|doctor.*"):
        r.run("MEMORY", "DOCTOR")
    with pytest.raises(Exception, match=".*NOPERM.*memory\\|stats.*"):
        r.run("MEMORY", "STATS")
    r.run("ACL", "setuser", "alice", "-@all")
    r.run("AUTH", "newuser", "passwd1")
    cmdstr = r.run("ACL", "getuser", "alice")["commands"]
    assert "-@all" == cmdstr
    r.run("AUTH", "alice", "passwd1")
    with pytest.raises(Exception, match=".*NOPERM.*get.*"):
        r.run("GET", "key")
    with pytest.raises(Exception, match=".*NOPERM.*memory\\|stats.*"):
        r.run("MEMORY", "STATS")
    r.run("AUTH", "newuser", "passwd1")


def test_acl_setuser_reset_reverting_to_default_newly_created_user(r: ValkeyTestClient) -> None:
    """
    test {ACL SETUSER RESET reverting to default newly created user} {
        set current_user "example"
        r ACL DELUSER $current_user
        r ACL SETUSER $current_user

        set users [r ACL LIST]
        foreach user [lshuffle $users] {
            if {[string first $current_user $user] != -1} {
                set current_user_output $user
            }
        }

        r ACL SETUSER $current_user reset
        set users [r ACL LIST]
        foreach user [lshuffle $users] {
            if {[string first $current_user $user] != -1} {
                assert_equal $current_user_output $user
            }
        }
    }
    """
    current_user = "example"
    r.run("ACL", "DELUSER", current_user)
    r.run("ACL", "SETUSER", current_user)
    users = r.run("ACL", "LIST")
    foreach(
        "user",
        lshuffle(users),
        "            if {[string first $current_user $user] != -1} {\n                set current_user_output $user\n            }\n        ",
    )
    r.run("ACL", "SETUSER", current_user, "reset")
    users = r.run("ACL", "LIST")
    foreach(
        "user",
        lshuffle(users),
        "            if {[string first $current_user $user] != -1} {\n                assert_equal $current_user_output $user\n            }\n        ",
    )


def test_acl_getuser_is_able_to_translate_back_command_permissions(r: ValkeyTestClient) -> None:
    """
    test {ACL GETUSER is able to translate back command permissions} {
        # Subtractive
        r ACL setuser newuser reset +@all ~* -@string +incr -debug +debug|digest
        set cmdstr [dict get [r ACL getuser newuser] commands]
        assert_match {*+@all*} $cmdstr
        assert_match {*-@string*} $cmdstr
        assert_match {*+incr*} $cmdstr
        assert_match {*-debug +debug|digest**} $cmdstr

        # Additive
        r ACL setuser newuser reset +@string -incr +acl +debug|digest +debug|segfault
        set cmdstr [dict get [r ACL getuser newuser] commands]
        assert_match {*-@all*} $cmdstr
        assert_match {*+@string*} $cmdstr
        assert_match {*-incr*} $cmdstr
        assert_match {*+debug|digest*} $cmdstr
        assert_match {*+debug|segfault*} $cmdstr
        assert_match {*+acl*} $cmdstr
    }
    """
    r.run("ACL", "setuser", "newuser", "reset", "+@all", "~*", "-@string", "+incr", "-debug", "+debug|digest")
    cmdstr = r.run("ACL", "getuser", "newuser")["commands"]
    assert fnmatch(str(cmdstr), "*+@all*")
    assert fnmatch(str(cmdstr), "*-@string*")
    assert fnmatch(str(cmdstr), "*+incr*")
    assert fnmatch(str(cmdstr), "*-debug +debug|digest**")
    r.run("ACL", "setuser", "newuser", "reset", "+@string", "-incr", "+acl", "+debug|digest", "+debug|segfault")
    cmdstr = r.run("ACL", "getuser", "newuser")["commands"]
    assert fnmatch(str(cmdstr), "*-@all*")
    assert fnmatch(str(cmdstr), "*+@string*")
    assert fnmatch(str(cmdstr), "*-incr*")
    assert fnmatch(str(cmdstr), "*+debug|digest*")
    assert fnmatch(str(cmdstr), "*+debug|segfault*")
    assert fnmatch(str(cmdstr), "*+acl*")


def test_acl_getuser_provides_reasonable_results(r: ValkeyTestClient) -> None:
    """
    test {ACL GETUSER provides reasonable results} {
        set categories [r ACL CAT]

        # Test that adding each single category will
        # result in just that category with both +@all and -@all
        foreach category $categories {
            # Test for future commands where allowed
            r ACL setuser additive reset +@all "-@$category"
            set cmdstr [dict get [r ACL getuser additive] commands]
            assert_equal "+@all -@$category" $cmdstr

            # Test for future commands where disallowed
            r ACL setuser restrictive reset -@all "+@$category"
            set cmdstr [dict get [r ACL getuser restrictive] commands]
            assert_equal "-@all +@$category" $cmdstr
        }
    }
    """
    categories = r.run("ACL", "CAT")
    foreach(
        "category",
        categories,
        '            # Test for future commands where allowed\n            r ACL setuser additive reset +@all "-@$category"\n            set cmdstr [dict get [r ACL getuser additive] commands]\n            assert_equal "+@all -@$category" $cmdstr\n\n            # Test for future commands where disallowed\n            r ACL setuser restrictive reset -@all "+@$category"\n            set cmdstr [dict get [r ACL getuser restrictive] commands]\n            assert_equal "-@all +@$category" $cmdstr\n        ',
    )


def test_acl_getuser_provides_correct_results(r: ValkeyTestClient) -> None:
    """
    test {ACL GETUSER provides correct results} {
        r ACL SETUSER adv-test
        r ACL SETUSER adv-test +@all -@hash -@slow +hget
        assert_equal "+@all -@hash -@slow +hget" [dict get [r ACL getuser adv-test] commands]

        # Categories are re-ordered if re-added
        r ACL SETUSER adv-test -@hash
        assert_equal "+@all -@slow +hget -@hash" [dict get [r ACL getuser adv-test] commands]

        # Inverting categories removes existing categories
        r ACL SETUSER adv-test +@hash
        assert_equal "+@all -@slow +hget +@hash" [dict get [r ACL getuser adv-test] commands]

        # Inverting the all category compacts everything
        r ACL SETUSER adv-test -@all
        assert_equal "-@all" [dict get [r ACL getuser adv-test] commands]
        r ACL SETUSER adv-test -@string -@slow +@all
        assert_equal "+@all" [dict get [r ACL getuser adv-test] commands]

        # Make sure categories are case insensitive
        r ACL SETUSER adv-test -@all +@HASH +@hash +@HaSh
        assert_equal "-@all +@hash" [dict get [r ACL getuser adv-test] commands]

        # Make sure commands are case insensitive
        r ACL SETUSER adv-test -@all +HGET +hget +hGeT
        assert_equal "-@all +hget" [dict get [r ACL getuser adv-test] commands]

        # Arbitrary category additions and removals are handled
        r ACL SETUSER adv-test -@all +@hash +@slow +@set +@set +@slow +@hash
        assert_equal "-@all +@set +@slow +@hash" [dict get [r ACL getuser adv-test] commands]

        # Arbitrary command additions and removals are handled
        r ACL SETUSER adv-test -@all +hget -hset +hset -hget
        assert_equal "-@all +hset -hget" [dict get [r ACL getuser adv-test] commands]

        # Arbitrary subcommands are compacted
        r ACL SETUSER adv-test -@all +client|list +client|list +config|get +config +acl|list -acl
        assert_equal "-@all +client|list +config -acl" [dict get [r ACL getuser adv-test] commands]

        # Deprecated subcommand usage is handled
        r ACL SETUSER adv-test -@all +select|0 +select|0 +debug|segfault +debug
        assert_equal "-@all +select|0 +debug" [dict get [r ACL getuser adv-test] commands]

        # Unnecessary categories are retained for potential future compatibility
        r ACL SETUSER adv-test -@all -@dangerous
        assert_equal "-@all -@dangerous" [dict get [r ACL getuser adv-test] commands]

        # Duplicate categories are compressed, regression test for #12470
        r ACL SETUSER adv-test -@all +config +config|get -config|set +config
        assert_equal "-@all +config" [dict get [r ACL getuser adv-test] commands]
    }
    """
    r.run("ACL", "SETUSER", "adv-test")
    r.run("ACL", "SETUSER", "adv-test", "+@all", "-@hash", "-@slow", "+hget")
    assert "+@all -@hash -@slow +hget" == r.run("ACL", "getuser", "adv-test")["commands"]
    r.run("ACL", "SETUSER", "adv-test", "-@hash")
    assert "+@all -@slow +hget -@hash" == r.run("ACL", "getuser", "adv-test")["commands"]
    r.run("ACL", "SETUSER", "adv-test", "+@hash")
    assert "+@all -@slow +hget +@hash" == r.run("ACL", "getuser", "adv-test")["commands"]
    r.run("ACL", "SETUSER", "adv-test", "-@all")
    assert "-@all" == r.run("ACL", "getuser", "adv-test")["commands"]
    r.run("ACL", "SETUSER", "adv-test", "-@string", "-@slow", "+@all")
    assert "+@all" == r.run("ACL", "getuser", "adv-test")["commands"]
    r.run("ACL", "SETUSER", "adv-test", "-@all", "+@HASH", "+@hash", "+@HaSh")
    assert "-@all +@hash" == r.run("ACL", "getuser", "adv-test")["commands"]
    r.run("ACL", "SETUSER", "adv-test", "-@all", "+HGET", "+hget", "+hGeT")
    assert "-@all +hget" == r.run("ACL", "getuser", "adv-test")["commands"]
    r.run("ACL", "SETUSER", "adv-test", "-@all", "+@hash", "+@slow", "+@set", "+@set", "+@slow", "+@hash")
    assert "-@all +@set +@slow +@hash" == r.run("ACL", "getuser", "adv-test")["commands"]
    r.run("ACL", "SETUSER", "adv-test", "-@all", "+hget", "-hset", "+hset", "-hget")
    assert "-@all +hset -hget" == r.run("ACL", "getuser", "adv-test")["commands"]
    r.run(
        "ACL",
        "SETUSER",
        "adv-test",
        "-@all",
        "+client|list",
        "+client|list",
        "+config|get",
        "+config",
        "+acl|list",
        "-acl",
    )
    assert "-@all +client|list +config -acl" == r.run("ACL", "getuser", "adv-test")["commands"]
    r.run("ACL", "SETUSER", "adv-test", "-@all", "+select|0", "+select|0", "+debug|segfault", "+debug")
    assert "-@all +select|0 +debug" == r.run("ACL", "getuser", "adv-test")["commands"]
    r.run("ACL", "SETUSER", "adv-test", "-@all", "-@dangerous")
    assert "-@all -@dangerous" == r.run("ACL", "getuser", "adv-test")["commands"]
    r.run("ACL", "SETUSER", "adv-test", "-@all", "+config", "+config|get", "-config|set", "+config")
    assert "-@all +config" == r.run("ACL", "getuser", "adv-test")["commands"]


def test_acl_cat_with_illegal_arguments(r: ValkeyTestClient) -> None:
    """
    test "ACL CAT with illegal arguments" {
        assert_error {*Unknown category 'NON_EXISTS'} {r ACL CAT NON_EXISTS}
        assert_error {*unknown subcommand or wrong number of arguments for 'CAT'*} {r ACL CAT NON_EXISTS NON_EXISTS2}
    }
    """
    with pytest.raises(Exception, match=".*Unknown\\ category\\ 'NON_EXISTS'"):
        r.run("ACL", "CAT", "NON_EXISTS")
    with pytest.raises(
        Exception, match=".*unknown\\ subcommand\\ or\\ wrong\\ number\\ of\\ arguments\\ for\\ 'CAT'.*"
    ):
        r.run("ACL", "CAT", "NON_EXISTS", "NON_EXISTS2")


def test_acl_cat_without_category_list_all_categories(r: ValkeyTestClient) -> None:
    """
    test "ACL CAT without category - list all categories" {
        set categories [r acl cat]
        assert_not_equal [lsearch $categories "keyspace"] -1
        assert_not_equal [lsearch $categories "connection"] -1
    }
    """
    categories = r.run("acl", "cat")
    assert_not_equal(lsearch(categories, "keyspace"), -1)
    assert_not_equal(lsearch(categories, "connection"), -1)


def test_acl_cat_category_list_all_commands_or_subcommands_that_belong_to_category(r: ValkeyTestClient) -> None:
    """
    test "ACL CAT category - list all commands/subcommands that belong to category" {
        assert_not_equal [lsearch [r acl cat transaction] "multi"] -1
        assert_not_equal [lsearch [r acl cat scripting] "function|list"] -1

        # Negative check to make sure it doesn't actually return all commands.
        assert_equal [lsearch [r acl cat keyspace] "set"] -1
        assert_equal [lsearch [r acl cat stream] "get"] -1
    }
    """
    assert_not_equal(lsearch(r.run("acl", "cat", "transaction"), "multi"), -1)
    assert_not_equal(lsearch(r.run("acl", "cat", "scripting"), "function|list"), -1)
    assert lsearch(r.run("acl", "cat", "keyspace"), "set") == -1
    assert lsearch(r.run("acl", "cat", "stream"), "get") == -1


def test_acl_requires_explicit_permission_for_scripting_for_eval_ro_evalsha_ro_and_fcall_ro(
    r: ValkeyTestClient,
) -> None:
    """
    test "ACL requires explicit permission for scripting for EVAL_RO, EVALSHA_RO and FCALL_RO" {
        r ACL SETUSER scripter on nopass +readonly
        assert_match {*has no permissions to run the 'eval_ro' command*} [r ACL DRYRUN scripter EVAL_RO "" 0]
        assert_match {*has no permissions to run the 'evalsha_ro' command*} [r ACL DRYRUN scripter EVALSHA_RO "" 0]
        assert_match {*has no permissions to run the 'fcall_ro' command*} [r ACL DRYRUN scripter FCALL_RO "" 0]
    }
    """
    r.run("ACL", "SETUSER", "scripter", "on", "nopass", "+readonly")
    assert fnmatch(
        str(r.run("ACL", "DRYRUN", "scripter", "EVAL_RO", "", 0)), "*has no permissions to run the 'eval_ro' command*"
    )
    assert fnmatch(
        str(r.run("ACL", "DRYRUN", "scripter", "EVALSHA_RO", "", 0)),
        "*has no permissions to run the 'evalsha_ro' command*",
    )
    assert fnmatch(
        str(r.run("ACL", "DRYRUN", "scripter", "FCALL_RO", "", 0)), "*has no permissions to run the 'fcall_ro' command*"
    )


def test_acl_5998_regression_memory_leaks_adding_or_removing_subcommands(r: ValkeyTestClient) -> None:
    """
    test {ACL #5998 regression: memory leaks adding / removing subcommands} {
        r AUTH default ""
        r ACL setuser newuser reset -debug +debug|a +debug|b +debug|c
        r ACL setuser newuser -debug
        # The test framework will detect a leak if any.
    }
    """
    r.run("AUTH", "default", "")
    r.run("ACL", "setuser", "newuser", "reset", "-debug", "+debug|a", "+debug|b", "+debug|c")
    r.run("ACL", "setuser", "newuser", "-debug")


def test_acl_log_aggregates_similar_errors_together_and_assigns_unique_entry_id_to_new_errors(
    r: ValkeyTestClient,
) -> None:
    """
    test {ACL LOG aggregates similar errors together and assigns unique entry-id to new errors} {
        r ACL LOG RESET
        r ACL setuser user1 >foo
        assert_error "*WRONGPASS*" {r AUTH user1 doo}
        set entry_id_initial_error [dict get [lindex [r ACL LOG] 0] entry-id]
        set timestamp_created_original [dict get [lindex [r ACL LOG] 0] timestamp-created]
        set timestamp_last_update_original [dict get [lindex [r ACL LOG] 0] timestamp-last-updated]
        after 1
        for {set j 0} {$j < 10} {incr j} {
            assert_error "*WRONGPASS*" {r AUTH user1 doo}
        }
        set entry_id_latest_error [dict get [lindex [r ACL LOG] 0] entry-id]
        set timestamp_created_updated [dict get [lindex [r ACL LOG] 0] timestamp-created]
        set timestamp_last_updated_after_update [dict get [lindex [r ACL LOG] 0] timestamp-last-updated]
        assert {$entry_id_latest_error eq $entry_id_initial_error}
        assert {$timestamp_last_update_original < $timestamp_last_updated_after_update}
        assert {$timestamp_created_original eq $timestamp_created_updated}
        r ACL setuser user2 >doo
        assert_error "*WRONGPASS*" {r AUTH user2 foo}
        set new_error_entry_id [dict get [lindex [r ACL LOG] 0] entry-id]
        assert {$new_error_entry_id eq $entry_id_latest_error + 1 }
    }
    """
    r.run("ACL", "LOG", "RESET")
    r.run("ACL", "setuser", "user1", ">foo")
    with pytest.raises(Exception, match=".*WRONGPASS.*"):
        r.run("AUTH", "user1", "doo")
    entry_id_initial_error = r.run("ACL", "LOG")[0]["entry-id"]
    timestamp_created_original = r.run("ACL", "LOG")[0]["timestamp-created"]
    timestamp_last_update_original = r.run("ACL", "LOG")[0]["timestamp-last-updated"]
    time.sleep(1 / 1000)
    j = 0
    while j < 10:
        with pytest.raises(Exception, match=".*WRONGPASS.*"):
            r.run("AUTH", "user1", "doo")
        j += 1
    entry_id_latest_error = r.run("ACL", "LOG")[0]["entry-id"]
    timestamp_created_updated = r.run("ACL", "LOG")[0]["timestamp-created"]
    timestamp_last_updated_after_update = r.run("ACL", "LOG")[0]["timestamp-last-updated"]
    assert entry_id_latest_error == entry_id_initial_error
    assert timestamp_last_update_original < timestamp_last_updated_after_update
    assert timestamp_created_original == timestamp_created_updated
    r.run("ACL", "setuser", "user2", ">doo")
    with pytest.raises(Exception, match=".*WRONGPASS.*"):
        r.run("AUTH", "user2", "foo")
    new_error_entry_id = r.run("ACL", "LOG")[0]["entry-id"]
    assert new_error_entry_id == (entry_id_latest_error + 1)


def test_acl_log_shows_failed_command_executions_at_toplevel(r: ValkeyTestClient) -> None:
    """
    test {ACL LOG shows failed command executions at toplevel} {
        r ACL LOG RESET
        r ACL setuser antirez >foo on +set ~object:1234
        r ACL setuser antirez +eval +multi +exec
        r ACL setuser antirez resetchannels +publish
        r AUTH antirez foo
        assert_error "*NOPERM*get*" {r GET foo}
        r AUTH default ""
        set entry [lindex [r ACL LOG] 0]
        assert {[dict get $entry username] eq {antirez}}
        assert {[dict get $entry context] eq {toplevel}}
        assert {[dict get $entry reason] eq {command}}
        assert {[dict get $entry object] eq {get}}
        assert_match {*cmd=get*} [dict get $entry client-info]
    }
    """
    r.run("ACL", "LOG", "RESET")
    r.run("ACL", "setuser", "antirez", ">foo", "on", "+set", "~object:1234")
    r.run("ACL", "setuser", "antirez", "+eval", "+multi", "+exec")
    r.run("ACL", "setuser", "antirez", "resetchannels", "+publish")
    r.run("AUTH", "antirez", "foo")
    with pytest.raises(Exception, match=".*NOPERM.*get.*"):
        r.run("GET", "foo")
    r.run("AUTH", "default", "")
    entry = r.run("ACL", "LOG")[0]
    assert entry["username"] == "antirez"
    assert entry["context"] == "toplevel"
    assert entry["reason"] == "command"
    assert entry["object"] == "get"
    assert fnmatch(str(entry["client-info"]), "*cmd=get*")


def test_acl_log_shows_failed_subcommand_executions_at_toplevel(r: ValkeyTestClient) -> None:
    """
    test "ACL LOG shows failed subcommand executions at toplevel" {
        r ACL LOG RESET
        r ACL DELUSER demo
        r ACL SETUSER demo on nopass
        r AUTH demo ""
        assert_error "*NOPERM*script|help*" {r SCRIPT HELP}
        r AUTH default ""
        set entry [lindex [r ACL LOG] 0]
        assert_equal [dict get $entry username] {demo}
        assert_equal [dict get $entry context] {toplevel}
        assert_equal [dict get $entry reason] {command}
        assert_equal [dict get $entry object] {script|help}
    }
    """
    r.run("ACL", "LOG", "RESET")
    r.run("ACL", "DELUSER", "demo")
    r.run("ACL", "SETUSER", "demo", "on", "nopass")
    r.run("AUTH", "demo", "")
    with pytest.raises(Exception, match=".*NOPERM.*script\\|help.*"):
        r.run("SCRIPT", "HELP")
    r.run("AUTH", "default", "")
    entry = r.run("ACL", "LOG")[0]
    assert entry["username"] == "demo"
    assert entry["context"] == "toplevel"
    assert entry["reason"] == "command"
    assert entry["object"] == "script|help"


def test_acl_log_is_able_to_test_similar_events(r: ValkeyTestClient) -> None:
    """
    test {ACL LOG is able to test similar events} {
        r ACL LOG RESET
        r AUTH antirez foo
        catch {r GET foo}
        catch {r GET foo}
        catch {r GET foo}
        r AUTH default ""
        set entry [lindex [r ACL LOG] 0]
        assert {[dict get $entry count] == 3}
    }
    """
    r.run("ACL", "LOG", "RESET")
    r.run("AUTH", "antirez", "foo")
    try:
        r.run("GET", "foo")
    except Exception:
        pass
    try:
        r.run("GET", "foo")
    except Exception:
        pass
    try:
        r.run("GET", "foo")
    except Exception:
        pass
    r.run("AUTH", "default", "")
    entry = r.run("ACL", "LOG")[0]
    assert entry["count"] == 3


def test_acl_log_is_able_to_log_keys_access_violations_and_key_name(r: ValkeyTestClient) -> None:
    """
    test {ACL LOG is able to log keys access violations and key name} {
        r AUTH antirez foo
        catch {r SET somekeynotallowed 1234}
        r AUTH default ""
        set entry [lindex [r ACL LOG] 0]
        assert {[dict get $entry reason] eq {key}}
        assert {[dict get $entry object] eq {somekeynotallowed}}
    }
    """
    r.run("AUTH", "antirez", "foo")
    try:
        r.run("SET", "somekeynotallowed", 1234)
    except Exception:
        pass
    r.run("AUTH", "default", "")
    entry = r.run("ACL", "LOG")[0]
    assert entry["reason"] == "key"
    assert entry["object"] == "somekeynotallowed"


def test_acl_log_is_able_to_log_channel_access_violations_and_channel_name(r: ValkeyTestClient) -> None:
    """
    test {ACL LOG is able to log channel access violations and channel name} {
        r AUTH antirez foo
        catch {r PUBLISH somechannelnotallowed nullmsg}
        r AUTH default ""
        set entry [lindex [r ACL LOG] 0]
        assert {[dict get $entry reason] eq {channel}}
        assert {[dict get $entry object] eq {somechannelnotallowed}}
    }
    """
    r.run("AUTH", "antirez", "foo")
    try:
        r.run("PUBLISH", "somechannelnotallowed", "nullmsg")
    except Exception:
        pass
    r.run("AUTH", "default", "")
    entry = r.run("ACL", "LOG")[0]
    assert entry["reason"] == "channel"
    assert entry["object"] == "somechannelnotallowed"


def test_acl_log_is_able_to_log_database_access_violations(r: ValkeyTestClient) -> None:
    """
    test {ACL LOG is able to log database access violations} {
        r ACL LOG RESET
        r ACL SETUSER dbuser on nopass db=0 +@all ~*
        r AUTH dbuser password

        catch {r SELECT 1}
        catch {r SWAPDB 0 2}
        catch {r FLUSHALL}

        set log [r ACL LOG]
        set entry [lindex $log 0]
        assert {[dict get $entry reason] eq {database}}
        assert {[dict get $entry object] eq {flushall}}
        set entry [lindex $log 1]
        assert {[dict get $entry reason] eq {database}}
        assert {[dict get $entry object] eq {2}}
        set entry [lindex $log 2]
        assert {[dict get $entry reason] eq {database}}
        assert {[dict get $entry object] eq {1}}
    }
    """
    r.run("ACL", "LOG", "RESET")
    r.run("ACL", "SETUSER", "dbuser", "on", "nopass", "db=0", "+@all", "~*")
    r.run("AUTH", "dbuser", "password")
    try:
        r.run("SELECT", 1)
    except Exception:
        pass
    try:
        r.run("SWAPDB", 0, 2)
    except Exception:
        pass
    try:
        r.run("FLUSHALL")
    except Exception:
        pass
    log = r.run("ACL", "LOG")
    entry = log[0]
    assert entry["reason"] == "database"
    assert entry["object"] == "flushall"
    entry = log[1]
    assert entry["reason"] == "database"
    assert entry["object"] == "2"
    entry = log[2]
    assert entry["reason"] == "database"
    assert entry["object"] == "1"


def test_acl_log_reset_is_able_to_flush_the_entries_in_the_log(r: ValkeyTestClient) -> None:
    """
    test {ACL LOG RESET is able to flush the entries in the log} {
        r ACL LOG RESET
        assert {[llength [r ACL LOG]] == 0}
    }
    """
    r.run("ACL", "LOG", "RESET")
    assert len(r.run("ACL", "LOG")) == 0


def test_acl_log_can_distinguish_the_transaction_context_1(r: ValkeyTestClient) -> None:
    """
    test {ACL LOG can distinguish the transaction context (1)} {
        r AUTH antirez foo
        r MULTI
        catch {r INCR foo}
        catch {r EXEC}
        r AUTH default ""
        set entry [lindex [r ACL LOG] 0]
        assert {[dict get $entry context] eq {multi}}
        assert {[dict get $entry object] eq {incr}}
    }
    """
    r.run("AUTH", "antirez", "foo")
    r.run("MULTI")
    try:
        r.run("INCR", "foo")
    except Exception:
        pass
    try:
        r.run("EXEC")
    except Exception:
        pass
    r.run("AUTH", "default", "")
    entry = r.run("ACL", "LOG")[0]
    assert entry["context"] == "multi"
    assert entry["object"] == "incr"


def test_acl_log_can_distinguish_the_transaction_context_2(r: ValkeyTestClient) -> None:
    """
    test {ACL LOG can distinguish the transaction context (2)} {
        set rd1 [valkey_deferring_client]
        r ACL SETUSER antirez +incr

        r AUTH antirez foo
        r MULTI
        r INCR object:1234
        $rd1 ACL SETUSER antirez -incr
        $rd1 read
        catch {r EXEC}
        $rd1 close
        r AUTH default ""
        set entry [lindex [r ACL LOG] 0]
        assert {[dict get $entry context] eq {multi}}
        assert {[dict get $entry object] eq {incr}}
        assert_match {*cmd=exec*} [dict get $entry client-info]
        r ACL SETUSER antirez -incr
    }
    """
    rd1 = ValkeyTestClient.create_from(r)
    r.run("ACL", "SETUSER", "antirez", "+incr")
    r.run("AUTH", "antirez", "foo")
    r.run("MULTI")
    r.run("INCR", "object:1234")
    rd1.run("ACL", "SETUSER", "antirez", "-incr")
    rd1.run("read")
    try:
        r.run("EXEC")
    except Exception:
        pass
    rd1.run("close")
    r.run("AUTH", "default", "")
    entry = r.run("ACL", "LOG")[0]
    assert entry["context"] == "multi"
    assert entry["object"] == "incr"
    assert fnmatch(str(entry["client-info"]), "*cmd=exec*")
    r.run("ACL", "SETUSER", "antirez", "-incr")


def test_acl_can_log_errors_in_the_context_of_lua_scripting(r: ValkeyTestClient) -> None:
    """
    test {ACL can log errors in the context of Lua scripting} {
        r AUTH antirez foo
        catch {r EVAL {redis.call('incr','foo')} 0}
        r AUTH default ""
        set entry [lindex [r ACL LOG] 0]
        assert {[dict get $entry context] eq {lua}}
        assert {[dict get $entry object] eq {incr}}
        assert_match {*cmd=eval*} [dict get $entry client-info]
    }
    """
    r.run("AUTH", "antirez", "foo")
    try:
        r.run("EVAL", "redis.call('incr','foo')", 0)
    except Exception:
        pass
    r.run("AUTH", "default", "")
    entry = r.run("ACL", "LOG")[0]
    assert entry["context"] == "lua"
    assert entry["object"] == "incr"
    assert fnmatch(str(entry["client-info"]), "*cmd=eval*")


def test_acl_log_can_accept_a_numerical_argument_to_show_less_entries(r: ValkeyTestClient) -> None:
    """
    test {ACL LOG can accept a numerical argument to show less entries} {
        r AUTH antirez foo
        catch {r INCR foo}
        catch {r INCR foo}
        catch {r INCR foo}
        catch {r INCR foo}
        r AUTH default ""
        assert {[llength [r ACL LOG]] > 1}
        assert {[llength [r ACL LOG 2]] == 2}
    }
    """
    r.run("AUTH", "antirez", "foo")
    try:
        r.run("INCR", "foo")
    except Exception:
        pass
    try:
        r.run("INCR", "foo")
    except Exception:
        pass
    try:
        r.run("INCR", "foo")
    except Exception:
        pass
    try:
        r.run("INCR", "foo")
    except Exception:
        pass
    r.run("AUTH", "default", "")
    assert len(r.run("ACL", "LOG")) > 1
    assert len(r.run("ACL", "LOG", 2)) == 2


def test_acl_log_can_log_failed_auth_attempts(r: ValkeyTestClient) -> None:
    """
    test {ACL LOG can log failed auth attempts} {
        catch {r AUTH antirez wrong-password}
        set entry [lindex [r ACL LOG] 0]
        assert {[dict get $entry context] eq {toplevel}}
        assert {[dict get $entry reason] eq {auth}}
        assert {[dict get $entry object] eq {AUTH}}
        assert {[dict get $entry username] eq {antirez}}
    }
    """
    try:
        r.run("AUTH", "antirez", "wrong-password")
    except Exception:
        pass
    entry = r.run("ACL", "LOG")[0]
    assert entry["context"] == "toplevel"
    assert entry["reason"] == "auth"
    assert entry["object"] == "AUTH"
    assert entry["username"] == "antirez"


def test_acllog_zero_max_length_is_correctly_handled(r: ValkeyTestClient) -> None:
    """
    test {ACLLOG - zero max length is correctly handled} {
        r ACL LOG RESET
        r CONFIG SET acllog-max-len 0
        for {set j 0} {$j < 10} {incr j} {
            catch {r SET obj:$j 123}
        }
        r AUTH default ""
        assert {[llength [r ACL LOG]] == 0}
    }
    """
    r.run("ACL", "LOG", "RESET")
    r.run("CONFIG", "SET", "acllog-max-len", 0)
    j = 0
    while j < 10:
        try:
            r.run("SET", "obj:$j", 123)
        except Exception:
            pass
        j += 1
    r.run("AUTH", "default", "")
    assert len(r.run("ACL", "LOG")) == 0


def test_acl_log_entries_are_limited_to_a_maximum_amount(r: ValkeyTestClient) -> None:
    """
    test {ACL LOG entries are limited to a maximum amount} {
        r ACL LOG RESET
        r CONFIG SET acllog-max-len 5
        r AUTH antirez foo
        for {set j 0} {$j < 10} {incr j} {
            catch {r SET obj:$j 123}
        }
        r AUTH default ""
        assert {[llength [r ACL LOG]] == 5}
    }
    """
    r.run("ACL", "LOG", "RESET")
    r.run("CONFIG", "SET", "acllog-max-len", 5)
    r.run("AUTH", "antirez", "foo")
    j = 0
    while j < 10:
        try:
            r.run("SET", "obj:$j", 123)
        except Exception:
            pass
        j += 1
    r.run("AUTH", "default", "")
    assert len(r.run("ACL", "LOG")) == 5


def test_acl_log_entries_are_still_present_on_update_of_max_len_config(r: ValkeyTestClient) -> None:
    """
    test {ACL LOG entries are still present on update of max len config} {
        r CONFIG SET acllog-max-len 0
        assert {[llength [r ACL LOG]] == 5}
    }
    """
    r.run("CONFIG", "SET", "acllog-max-len", 0)
    assert len(r.run("ACL", "LOG")) == 5


def test_when_default_user_is_off_new_connections_are_not_authenticated(r: ValkeyTestClient) -> None:
    """
    test {When default user is off, new connections are not authenticated} {
        r ACL setuser default off
        catch {set rd1 [valkey_deferring_client]} e
        r ACL setuser default on
        set e
    } {*NOAUTH*}
    """
    r.run("ACL", "setuser", "default", "off")
    try:
        e = rd1 = ValkeyTestClient.create_from(r)
    except Exception as _catch_err:
        e = str(_catch_err)
    r.run("ACL", "setuser", "default", "on")
    assert fnmatch(str(e), "*NOAUTH*")


def test_when_default_user_has_no_command_permission_hello_command_still_works_for_other_users(
    r: ValkeyTestClient,
) -> None:
    """
    test {When default user has no command permission, hello command still works for other users} {
        r ACL setuser secure-user >supass on +@all
        r ACL setuser default -@all
        r HELLO 2 AUTH secure-user supass
        r ACL setuser default nopass +@all
        r AUTH default ""
    }
    """
    r.run("ACL", "setuser", "secure-user", ">supass", "on", "+@all")
    r.run("ACL", "setuser", "default", "-@all")
    r.run("HELLO", 2, "AUTH", "secure-user", "supass")
    r.run("ACL", "setuser", "default", "nopass", "+@all")
    r.run("AUTH", "default", "")


def test_when_an_authentication_chain_is_used_in_the_hello_cmd_the_last_auth_cmd_has_precedence(
    r: ValkeyTestClient,
) -> None:
    """
    test {When an authentication chain is used in the HELLO cmd, the last auth cmd has precedence} {
        r ACL setuser secure-user1 >supass on +@all
        r ACL setuser secure-user2 >supass on +@all
        r HELLO 2 AUTH secure-user pass AUTH secure-user2 supass AUTH secure-user1 supass
        assert {[r ACL whoami] eq {secure-user1}}
        catch {r HELLO 2 AUTH secure-user supass AUTH secure-user2 supass AUTH secure-user pass} e
        assert_match "WRONGPASS invalid username-password pair or user is disabled." $e
        assert {[r ACL whoami] eq {secure-user1}}
    }
    """
    r.run("ACL", "setuser", "secure-user1", ">supass", "on", "+@all")
    r.run("ACL", "setuser", "secure-user2", ">supass", "on", "+@all")
    r.run("HELLO", 2, "AUTH", "secure-user", "pass", "AUTH", "secure-user2", "supass", "AUTH", "secure-user1", "supass")
    assert r.run("ACL", "whoami") == "secure-user1"
    try:
        e = r.run(
            "HELLO", 2, "AUTH", "secure-user", "supass", "AUTH", "secure-user2", "supass", "AUTH", "secure-user", "pass"
        )
    except Exception as _catch_err:
        e = str(_catch_err)
    assert fnmatch(str(e), "WRONGPASS invalid username-password pair or user is disabled.")
    assert r.run("ACL", "whoami") == "secure-user1"


def test_when_a_setname_chain_is_used_in_the_hello_cmd_the_last_setname_cmd_has_precedence(r: ValkeyTestClient) -> None:
    """
    test {When a setname chain is used in the HELLO cmd, the last setname cmd has precedence} {
        r HELLO 2 setname client1 setname client2 setname client3 setname client4
        assert {[r client getname] eq {client4}}
        catch {r HELLO 2 setname client5 setname client6 setname "client name"} e
        assert_match "ERR Client names cannot contain spaces, newlines or special characters." $e
        assert {[r client getname] eq {client4}}
    }
    """
    r.run("HELLO", 2, "setname", "client1", "setname", "client2", "setname", "client3", "setname", "client4")
    assert r.run("client", "getname") == "client4"
    try:
        e = r.run("HELLO", 2, "setname", "client5", "setname", "client6", "setname", "client name")
    except Exception as _catch_err:
        e = str(_catch_err)
    assert fnmatch(str(e), "ERR Client names cannot contain spaces, newlines or special characters.")
    assert r.run("client", "getname") == "client4"


def test_when_authentication_fails_in_the_hello_cmd_the_client_setname_should_not_be_applied(
    r: ValkeyTestClient,
) -> None:
    """
    test {When authentication fails in the HELLO cmd, the client setname should not be applied} {
        r client setname client0
        catch {r HELLO 2 AUTH user pass setname client1} e
        assert_match "WRONGPASS invalid username-password pair or user is disabled." $e
        assert {[r client getname] eq {client0}}
    }
    """
    r.run("client", "setname", "client0")
    try:
        e = r.run("HELLO", 2, "AUTH", "user", "pass", "setname", "client1")
    except Exception as _catch_err:
        e = str(_catch_err)
    assert fnmatch(str(e), "WRONGPASS invalid username-password pair or user is disabled.")
    assert r.run("client", "getname") == "client0"


def test_acl_help_should_not_have_unexpected_options(r: ValkeyTestClient) -> None:
    """
    test {ACL HELP should not have unexpected options} {
        catch {r ACL help xxx} e
        assert_match "*wrong number of arguments for 'acl|help' command" $e
    }
    """
    try:
        e = r.run("ACL", "help", "xxx")
    except Exception as _catch_err:
        e = str(_catch_err)
    assert fnmatch(str(e), "*wrong number of arguments for 'acl|help' command")


def test_delete_a_user_that_the_client_doesn_t_use(r: ValkeyTestClient) -> None:
    """
    test {Delete a user that the client doesn't use} {
        r ACL setuser not_used on >passwd
        assert {[r ACL deluser not_used] == 1}
        # The client is not closed
        assert {[r ping] eq {PONG}}
    }
    """
    r.run("ACL", "setuser", "not_used", "on", ">passwd")
    assert r.run("ACL", "deluser", "not_used") == 1
    assert r.run("ping") == "PONG"


def test_delete_a_user_that_the_client_is_using(r: ValkeyTestClient) -> None:
    """
    test {Delete a user that the client is using} {
        r ACL setuser using on +acl >passwd
        r AUTH using passwd
        # The client will receive reply normally
        assert {[r ACL deluser using] == 1}
        # The client is closed
        catch {[r ping]} e
        assert_match "*I/O error*" $e
    }
    """
    r.run("ACL", "setuser", "using", "on", "+acl", ">passwd")
    r.run("AUTH", "using", "passwd")
    assert r.run("ACL", "deluser", "using") == 1
    try:
        e = r.run("ping")
    except Exception as _catch_err:
        e = str(_catch_err)
    assert fnmatch(str(e), "*I/O error*")


def test_acl_genpass_command_failed_test(r: ValkeyTestClient) -> None:
    """
    test {ACL GENPASS command failed test} {
        catch {r ACL genpass -236} err1
        catch {r ACL genpass 5000} err2
        assert_match "*ACL GENPASS argument must be the number*" $err1
        assert_match "*ACL GENPASS argument must be the number*" $err2
    }
    """
    try:
        err1 = r.run("ACL", "genpass", -236)
    except Exception as _catch_err:
        err1 = str(_catch_err)
    try:
        err2 = r.run("ACL", "genpass", 5000)
    except Exception as _catch_err:
        err2 = str(_catch_err)
    assert fnmatch(str(err1), "*ACL GENPASS argument must be the number*")
    assert fnmatch(str(err2), "*ACL GENPASS argument must be the number*")


def test_default_user_can_not_be_removed(r: ValkeyTestClient) -> None:
    """
    test {Default user can not be removed} {
        catch {r ACL deluser default} err
        set err
    } {ERR The 'default' user cannot be removed}
    """
    try:
        err = r.run("ACL", "deluser", "default")
    except Exception as _catch_err:
        err = str(_catch_err)
    assert err == "ERR The 'default' user cannot be removed"


def test_acl_load_non_existing_configured_acl_file(r: ValkeyTestClient) -> None:
    """
    test {ACL load non-existing configured ACL file} {
        catch {r ACL load} err
        set err
    } {*instance is not configured to use an ACL file*}
    """
    try:
        err = r.run("ACL", "load")
    except Exception as _catch_err:
        err = str(_catch_err)
    assert fnmatch(str(err), "*instance is not configured to use an ACL file*")


def test_acl_metrics_user_auth_failure(r: ValkeyTestClient) -> None:
    """
    test {ACL-Metrics user AUTH failure} {
        set current_auth_failures [s acl_access_denied_auth]
        set current_invalid_cmd_accesses [s acl_access_denied_cmd]
        set current_invalid_key_accesses [s acl_access_denied_key]
        set current_invalid_channel_accesses [s acl_access_denied_channel]
        assert_error "*WRONGPASS*" {r AUTH notrealuser 1233456}
        assert {[s acl_access_denied_auth] eq [expr $current_auth_failures + 1]}
        assert_error "*WRONGPASS*" {r HELLO 3 AUTH notrealuser 1233456}
        assert {[s acl_access_denied_auth] eq [expr $current_auth_failures + 2]}
        assert_error "*WRONGPASS*" {r HELLO 2 AUTH notrealuser 1233456}
        assert {[s acl_access_denied_auth] eq [expr $current_auth_failures + 3]}
        assert {[s acl_access_denied_cmd] eq $current_invalid_cmd_accesses}
        assert {[s acl_access_denied_key] eq $current_invalid_key_accesses}
        assert {[s acl_access_denied_channel] eq $current_invalid_channel_accesses}
    }
    """
    current_auth_failures = s("acl_access_denied_auth")
    current_invalid_cmd_accesses = s("acl_access_denied_cmd")
    current_invalid_key_accesses = s("acl_access_denied_key")
    current_invalid_channel_accesses = s("acl_access_denied_channel")
    with pytest.raises(Exception, match=".*WRONGPASS.*"):
        r.run("AUTH", "notrealuser", 1233456)
    assert s("acl_access_denied_auth") == expr(current_auth_failures, "+", 1)
    with pytest.raises(Exception, match=".*WRONGPASS.*"):
        r.run("HELLO", 3, "AUTH", "notrealuser", 1233456)
    assert s("acl_access_denied_auth") == expr(current_auth_failures, "+", 2)
    with pytest.raises(Exception, match=".*WRONGPASS.*"):
        r.run("HELLO", 2, "AUTH", "notrealuser", 1233456)
    assert s("acl_access_denied_auth") == expr(current_auth_failures, "+", 3)
    assert s("acl_access_denied_cmd") == current_invalid_cmd_accesses
    assert s("acl_access_denied_key") == current_invalid_key_accesses
    assert s("acl_access_denied_channel") == current_invalid_channel_accesses


def test_acl_metrics_invalid_command_accesses(r: ValkeyTestClient) -> None:
    """
    test {ACL-Metrics invalid command accesses} {
        set current_auth_failures [s acl_access_denied_auth]
        set current_invalid_cmd_accesses [s acl_access_denied_cmd]
        set current_invalid_key_accesses [s acl_access_denied_key]
        set current_invalid_channel_accesses [s acl_access_denied_channel]
        r ACL setuser invalidcmduser on >passwd nocommands
        r AUTH invalidcmduser passwd
        assert_error "*no permissions to run the * command*" {r acl list}
        r AUTH default ""
        assert {[s acl_access_denied_auth] eq $current_auth_failures}
        assert {[s acl_access_denied_cmd] eq [expr $current_invalid_cmd_accesses + 1]}
        assert {[s acl_access_denied_key] eq $current_invalid_key_accesses}
        assert {[s acl_access_denied_channel] eq $current_invalid_channel_accesses}
    }
    """
    current_auth_failures = s("acl_access_denied_auth")
    current_invalid_cmd_accesses = s("acl_access_denied_cmd")
    current_invalid_key_accesses = s("acl_access_denied_key")
    current_invalid_channel_accesses = s("acl_access_denied_channel")
    r.run("ACL", "setuser", "invalidcmduser", "on", ">passwd", "nocommands")
    r.run("AUTH", "invalidcmduser", "passwd")
    with pytest.raises(Exception, match=".*no\\ permissions\\ to\\ run\\ the\\ .*\\ command.*"):
        r.run("acl", "list")
    r.run("AUTH", "default", "")
    assert s("acl_access_denied_auth") == current_auth_failures
    assert s("acl_access_denied_cmd") == expr(current_invalid_cmd_accesses, "+", 1)
    assert s("acl_access_denied_key") == current_invalid_key_accesses
    assert s("acl_access_denied_channel") == current_invalid_channel_accesses


def test_acl_metrics_invalid_key_accesses(r: ValkeyTestClient) -> None:
    """
    test {ACL-Metrics invalid key accesses} {
        set current_auth_failures [s acl_access_denied_auth]
        set current_invalid_cmd_accesses [s acl_access_denied_cmd]
        set current_invalid_key_accesses [s acl_access_denied_key]
        set current_invalid_channel_accesses [s acl_access_denied_channel]
        r ACL setuser invalidkeyuser on >passwd resetkeys allcommands
        r AUTH invalidkeyuser passwd
        assert_error "*NOPERM*key*" {r get x}
        r AUTH default ""
        assert {[s acl_access_denied_auth] eq $current_auth_failures}
        assert {[s acl_access_denied_cmd] eq $current_invalid_cmd_accesses}
        assert {[s acl_access_denied_key] eq [expr $current_invalid_key_accesses + 1]}
        assert {[s acl_access_denied_channel] eq $current_invalid_channel_accesses}
    }
    """
    current_auth_failures = s("acl_access_denied_auth")
    current_invalid_cmd_accesses = s("acl_access_denied_cmd")
    current_invalid_key_accesses = s("acl_access_denied_key")
    current_invalid_channel_accesses = s("acl_access_denied_channel")
    r.run("ACL", "setuser", "invalidkeyuser", "on", ">passwd", "resetkeys", "allcommands")
    r.run("AUTH", "invalidkeyuser", "passwd")
    with pytest.raises(Exception, match=".*NOPERM.*key.*"):
        r.run("get", "x")
    r.run("AUTH", "default", "")
    assert s("acl_access_denied_auth") == current_auth_failures
    assert s("acl_access_denied_cmd") == current_invalid_cmd_accesses
    assert s("acl_access_denied_key") == expr(current_invalid_key_accesses, "+", 1)
    assert s("acl_access_denied_channel") == current_invalid_channel_accesses


def test_acl_metrics_invalid_channels_accesses(r: ValkeyTestClient) -> None:
    """
    test {ACL-Metrics invalid channels accesses} {
        set current_auth_failures [s acl_access_denied_auth]
        set current_invalid_cmd_accesses [s acl_access_denied_cmd]
        set current_invalid_key_accesses [s acl_access_denied_key]
        set current_invalid_channel_accesses [s acl_access_denied_channel]
        r ACL setuser invalidchanneluser on >passwd resetchannels allcommands
        r AUTH invalidkeyuser passwd
        assert_error "*NOPERM*channel*" {r subscribe x}
        r AUTH default ""
        assert {[s acl_access_denied_auth] eq $current_auth_failures}
        assert {[s acl_access_denied_cmd] eq $current_invalid_cmd_accesses}
        assert {[s acl_access_denied_key] eq $current_invalid_key_accesses}
        assert {[s acl_access_denied_channel] eq [expr $current_invalid_channel_accesses + 1]}
    }
    """
    current_auth_failures = s("acl_access_denied_auth")
    current_invalid_cmd_accesses = s("acl_access_denied_cmd")
    current_invalid_key_accesses = s("acl_access_denied_key")
    current_invalid_channel_accesses = s("acl_access_denied_channel")
    r.run("ACL", "setuser", "invalidchanneluser", "on", ">passwd", "resetchannels", "allcommands")
    r.run("AUTH", "invalidkeyuser", "passwd")
    with pytest.raises(Exception, match=".*NOPERM.*channel.*"):
        r.run("subscribe", "x")
    r.run("AUTH", "default", "")
    assert s("acl_access_denied_auth") == current_auth_failures
    assert s("acl_access_denied_cmd") == current_invalid_cmd_accesses
    assert s("acl_access_denied_key") == current_invalid_key_accesses
    assert s("acl_access_denied_channel") == expr(current_invalid_channel_accesses, "+", 1)


"""
set server_path tmpdir "server.acl"
"""


"""
exec cp -f tests/assets/user.acl server_path
"""


def test_default_load_from_include_file_can_access_any_channels(r: ValkeyTestClient) -> None:
    """
    test {default: load from include file, can access any channels} {
        r SUBSCRIBE foo
        r PSUBSCRIBE bar*
        r UNSUBSCRIBE
        r PUNSUBSCRIBE
        r PUBLISH hello world
    }
    """
    r.run("SUBSCRIBE", "foo")
    r.run("PSUBSCRIBE", "bar*")
    r.run("UNSUBSCRIBE")
    r.run("PUNSUBSCRIBE")
    r.run("PUBLISH", "hello", "world")


def test_default_with_config_acl_pubsub_default_allchannels_after_reset_can_access_any_channels(
    r: ValkeyTestClient,
) -> None:
    """
    test {default: with config acl-pubsub-default allchannels after reset, can access any channels} {
        r ACL setuser default reset on nopass ~* +@all
        r SUBSCRIBE foo
        r PSUBSCRIBE bar*
        r UNSUBSCRIBE
        r PUNSUBSCRIBE
        r PUBLISH hello world
    }
    """
    r.run("ACL", "setuser", "default", "reset", "on", "nopass", "~*", "+@all")
    r.run("SUBSCRIBE", "foo")
    r.run("PSUBSCRIBE", "bar*")
    r.run("UNSUBSCRIBE")
    r.run("PUNSUBSCRIBE")
    r.run("PUBLISH", "hello", "world")


def test_default_with_config_acl_pubsub_default_resetchannels_after_reset_can_not_access_any_channels(
    r: ValkeyTestClient,
) -> None:
    """
    test {default: with config acl-pubsub-default resetchannels after reset, can not access any channels} {
        r CONFIG SET acl-pubsub-default resetchannels
        r ACL setuser default reset on nopass ~* +@all
        assert_error {*NOPERM*channel*} {r SUBSCRIBE foo}
        assert_error {*NOPERM*channel*} {r PSUBSCRIBE bar*}
        assert_error {*NOPERM*channel*} {r PUBLISH hello world}
        r CONFIG SET acl-pubsub-default resetchannels
    }
    """
    r.run("CONFIG", "SET", "acl-pubsub-default", "resetchannels")
    r.run("ACL", "setuser", "default", "reset", "on", "nopass", "~*", "+@all")
    with pytest.raises(Exception, match=".*NOPERM.*channel.*"):
        r.run("SUBSCRIBE", "foo")
    with pytest.raises(Exception, match=".*NOPERM.*channel.*"):
        r.run("PSUBSCRIBE", "bar*")
    with pytest.raises(Exception, match=".*NOPERM.*channel.*"):
        r.run("PUBLISH", "hello", "world")
    r.run("CONFIG", "SET", "acl-pubsub-default", "resetchannels")


def test_alice_can_execute_all_command(r: ValkeyTestClient) -> None:
    """
    test {Alice: can execute all command} {
        r AUTH alice alice
        assert_equal "alice" [r acl whoami]
        r SET key value
    }
    """
    r.run("AUTH", "alice", "alice")
    assert "alice" == r.run("acl", "whoami")
    r.run("SET", "key", "value")


def test_bob_just_execute_set_and_acl_command(r: ValkeyTestClient) -> None:
    """
    test {Bob: just execute @set and acl command} {
        r AUTH bob bob
        assert_equal "bob" [r acl whoami]
        assert_equal "3" [r sadd set 1 2 3]
        catch {r SET key value} e
        set e
    } {*NOPERM*set*}
    """
    r.run("AUTH", "bob", "bob")
    assert "bob" == r.run("acl", "whoami")
    assert "3" == r.run("sadd", "set", 1, 2, 3)
    try:
        e = r.run("SET", "key", "value")
    except Exception as _catch_err:
        e = str(_catch_err)
    assert fnmatch(str(e), "*NOPERM*set*")


def test_acl_load_only_disconnects_affected_clients(r: ValkeyTestClient) -> None:
    """
    test {ACL LOAD only disconnects affected clients} {
        reconnect
        r ACL SETUSER doug on nopass resetchannels &test* +@all ~*

        set rd1 [valkey_deferring_client]
        set rd2 [valkey_deferring_client]

        $rd1 AUTH alice alice
        $rd1 read
        $rd1 SUBSCRIBE test1
        $rd1 read

        $rd2 AUTH doug doug
        $rd2 read
        $rd2 SUBSCRIBE test1
        $rd2 read

        r ACL LOAD
        r PUBLISH test1 test-message

        # Permissions for 'alice' haven't changed, so they should still be connected
        assert_match {*test-message*} [$rd1 read]

        # 'doug' no longer has access to "test1" channel, so they should get disconnected
        catch {$rd2 read} e
        assert_match {*I/O error*} $e

        $rd1 close
        $rd2 close
    }
    """
    reconnect()
    r.run("ACL", "SETUSER", "doug", "on", "nopass", "resetchannels", "&test*", "+@all", "~*")
    rd1 = ValkeyTestClient.create_from(r)
    rd2 = ValkeyTestClient.create_from(r)
    rd1.run("AUTH", "alice", "alice")
    rd1.run("read")
    rd1.run("SUBSCRIBE", "test1")
    rd1.run("read")
    rd2.run("AUTH", "doug", "doug")
    rd2.run("read")
    rd2.run("SUBSCRIBE", "test1")
    rd2.run("read")
    r.run("ACL", "LOAD")
    r.run("PUBLISH", "test1", "test-message")
    assert fnmatch(str(rd1.run("read")), "*test-message*")
    try:
        e = rd2.run("read")
    except Exception as _catch_err:
        e = str(_catch_err)
    assert fnmatch(str(e), "*I/O error*")
    rd1.run("close")
    rd2.run("close")


def test_acl_load_disconnects_clients_of_deleted_users(r: ValkeyTestClient) -> None:
    """
    test {ACL LOAD disconnects clients of deleted users} {
        reconnect
        r ACL SETUSER mortimer on >mortimer ~* &* +@all

        set rd1 [valkey_deferring_client]
        set rd2 [valkey_deferring_client]

        $rd1 AUTH alice alice
        $rd1 read
        $rd1 SUBSCRIBE test
        $rd1 read

        $rd2 AUTH mortimer mortimer
        $rd2 read
        $rd2 SUBSCRIBE test
        $rd2 read

        r ACL LOAD
        r PUBLISH test test-message

        # Permissions for 'alice' haven't changed, so they should still be connected
        assert_match {*test-message*} [$rd1 read]

        # 'mortimer' has been deleted, so their client should get disconnected
        catch {$rd2 read} e
        assert_match {*I/O error*} $e

        $rd1 close
        $rd2 close
    }
    """
    reconnect()
    r.run("ACL", "SETUSER", "mortimer", "on", ">mortimer", "~*", "&*", "+@all")
    rd1 = ValkeyTestClient.create_from(r)
    rd2 = ValkeyTestClient.create_from(r)
    rd1.run("AUTH", "alice", "alice")
    rd1.run("read")
    rd1.run("SUBSCRIBE", "test")
    rd1.run("read")
    rd2.run("AUTH", "mortimer", "mortimer")
    rd2.run("read")
    rd2.run("SUBSCRIBE", "test")
    rd2.run("read")
    r.run("ACL", "LOAD")
    r.run("PUBLISH", "test", "test-message")
    assert fnmatch(str(rd1.run("read")), "*test-message*")
    try:
        e = rd2.run("read")
    except Exception as _catch_err:
        e = str(_catch_err)
    assert fnmatch(str(e), "*I/O error*")
    rd1.run("close")
    rd2.run("close")


def test_acl_load_and_save(r: ValkeyTestClient) -> None:
    """
    test {ACL load and save} {
        r ACL setuser eve +get allkeys >eve on
        r ACL save

        r ACL load

        # Clients should not be disconnected since permissions haven't changed

        r AUTH alice alice
        r SET key value
        r AUTH eve eve
        r GET key
        catch {r SET key value} e
        set e
    } {*NOPERM*set*}
    """
    r.run("ACL", "setuser", "eve", "+get", "allkeys", ">eve", "on")
    r.run("ACL", "save")
    r.run("ACL", "load")
    r.run("AUTH", "alice", "alice")
    r.run("SET", "key", "value")
    r.run("AUTH", "eve", "eve")
    r.run("GET", "key")
    try:
        e = r.run("SET", "key", "value")
    except Exception as _catch_err:
        e = str(_catch_err)
    assert fnmatch(str(e), "*NOPERM*set*")


def test_acl_load_and_save_with_restricted_channels(r: ValkeyTestClient) -> None:
    """
    test {ACL load and save with restricted channels} {
        r AUTH alice alice
        r ACL setuser harry on nopass resetchannels &test +@all ~*
        r ACL save

        r ACL load

        # Clients should not be disconnected since permissions haven't changed

        r AUTH harry anything
        r publish test bar
        catch {r publish test1 bar} e
        r ACL deluser harry
        set e
    } {*NOPERM*channel*}
    """
    r.run("AUTH", "alice", "alice")
    r.run("ACL", "setuser", "harry", "on", "nopass", "resetchannels", "&test", "+@all", "~*")
    r.run("ACL", "save")
    r.run("ACL", "load")
    r.run("AUTH", "harry", "anything")
    r.run("publish", "test", "bar")
    try:
        e = r.run("publish", "test1", "bar")
    except Exception as _catch_err:
        e = str(_catch_err)
    r.run("ACL", "deluser", "harry")
    assert fnmatch(str(e), "*NOPERM*channel*")


"""
set server_path tmpdir "resetchannels.acl"
"""


"""
exec cp -f tests/assets/nodefaultuser.acl server_path
"""


"""
exec cp -f tests/assets/default.conf server_path
"""


def test_default_user_has_access_to_all_channels_irrespective_of_flag(r: ValkeyTestClient) -> None:
    """
    test {Default user has access to all channels irrespective of flag} {
        set channelinfo [dict get [r ACL getuser default] channels]
        assert_equal "&*" $channelinfo
        set channelinfo [dict get [r ACL getuser alice] channels]
        assert_equal "" $channelinfo
    }
    """
    channelinfo = r.run("ACL", "getuser", "default")["channels"]
    assert "&*" == channelinfo
    channelinfo = r.run("ACL", "getuser", "alice")["channels"]
    assert "" == channelinfo


def test_update_acl_pubsub_default_existing_users_shouldn_t_get_affected(r: ValkeyTestClient) -> None:
    """
    test {Update acl-pubsub-default, existing users shouldn't get affected} {
        set channelinfo [dict get [r ACL getuser default] channels]
        assert_equal "&*" $channelinfo
        r CONFIG set acl-pubsub-default allchannels
        r ACL setuser mydefault
        set channelinfo [dict get [r ACL getuser mydefault] channels]
        assert_equal "&*" $channelinfo
        r CONFIG set acl-pubsub-default resetchannels
        set channelinfo [dict get [r ACL getuser mydefault] channels]
        assert_equal "&*" $channelinfo
    }
    """
    channelinfo = r.run("ACL", "getuser", "default")["channels"]
    assert "&*" == channelinfo
    r.run("CONFIG", "set", "acl-pubsub-default", "allchannels")
    r.run("ACL", "setuser", "mydefault")
    channelinfo = r.run("ACL", "getuser", "mydefault")["channels"]
    assert "&*" == channelinfo
    r.run("CONFIG", "set", "acl-pubsub-default", "resetchannels")
    channelinfo = r.run("ACL", "getuser", "mydefault")["channels"]
    assert "&*" == channelinfo


def test_single_channel_is_valid(r: ValkeyTestClient) -> None:
    """
    test {Single channel is valid} {
        r ACL setuser onechannel &test
        set channelinfo [dict get [r ACL getuser onechannel] channels]
        assert_equal "&test" $channelinfo
        r ACL deluser onechannel
    }
    """
    r.run("ACL", "setuser", "onechannel", "&test")
    channelinfo = r.run("ACL", "getuser", "onechannel")["channels"]
    assert "&test" == channelinfo
    r.run("ACL", "deluser", "onechannel")


def test_single_channel_is_not_valid_with_allchannels(r: ValkeyTestClient) -> None:
    """
    test {Single channel is not valid with allchannels} {
        r CONFIG set acl-pubsub-default allchannels
        catch {r ACL setuser onechannel &test} err
        r CONFIG set acl-pubsub-default resetchannels
        set err
    } {*start with an empty list of channels*}
    """
    r.run("CONFIG", "set", "acl-pubsub-default", "allchannels")
    try:
        err = r.run("ACL", "setuser", "onechannel", "&test")
    except Exception as _catch_err:
        err = str(_catch_err)
    r.run("CONFIG", "set", "acl-pubsub-default", "resetchannels")
    assert fnmatch(str(err), "*start with an empty list of channels*")


"""
set server_path tmpdir "resetchannels.acl"
"""


"""
exec cp -f tests/assets/nodefaultuser.acl server_path
"""


"""
exec cp -f tests/assets/default.conf server_path
"""


def test_only_default_user_has_access_to_all_channels_irrespective_of_flag(r: ValkeyTestClient) -> None:
    """
    test {Only default user has access to all channels irrespective of flag} {
        set channelinfo [dict get [r ACL getuser default] channels]
        assert_equal "&*" $channelinfo
        set channelinfo [dict get [r ACL getuser alice] channels]
        assert_equal "" $channelinfo
    }
    """
    channelinfo = r.run("ACL", "getuser", "default")["channels"]
    assert "&*" == channelinfo
    channelinfo = r.run("ACL", "getuser", "alice")["channels"]
    assert "" == channelinfo


pytestmark = [pytest.mark.external_skip]


def test_default_load_from_config_file_without_channel_permission_default_user_can_t_access_any_channels(
    r: ValkeyTestClient,
) -> None:
    """
    test {default: load from config file, without channel permission default user can't access any channels} {
        catch {r SUBSCRIBE foo} e
        set e
    } {*NOPERM*channel*}
    """
    try:
        e = r.run("SUBSCRIBE", "foo")
    except Exception as _catch_err:
        e = str(_catch_err)
    assert fnmatch(str(e), "*NOPERM*channel*")


pytestmark = [pytest.mark.external_skip]


def test_default_load_from_config_file_with_all_channels_permissions(r: ValkeyTestClient) -> None:
    """
    test {default: load from config file with all channels permissions} {
        r SUBSCRIBE foo
        r PSUBSCRIBE bar*
        r UNSUBSCRIBE
        r PUNSUBSCRIBE
        r PUBLISH hello world
    }
    """
    r.run("SUBSCRIBE", "foo")
    r.run("PSUBSCRIBE", "bar*")
    r.run("UNSUBSCRIBE")
    r.run("PUNSUBSCRIBE")
    r.run("PUBLISH", "hello", "world")


"""
set server_path tmpdir "duplicate.acl"
"""


"""
exec cp -f tests/assets/user.acl server_path
"""


"""
exec cp -f tests/assets/default.conf server_path
"""


@pytest.mark.xfail(reason="not implemented")
def test_test_loading_an_acl_file_with_duplicate_users(r: ValkeyTestClient) -> None:
    """
    test {Test loading an ACL file with duplicate users} {
        exec cp -f tests/assets/user.acl $server_path

        # Corrupt the ACL file
        set corruption "\nuser alice on nopass ~* -@all"
        exec echo $corruption >> $server_path/user.acl
        catch {r ACL LOAD} err
        assert_match {*Duplicate user 'alice' found*} $err

        # Verify the previous users still exist
        # NOTE: A missing user evaluates to an empty
        # string.
        assert {[r ACL GETUSER alice] != ""}
        assert_equal [dict get [r ACL GETUSER alice] commands] "+@all"
        assert {[r ACL GETUSER bob] != ""}
        assert {[r ACL GETUSER default] != ""}
    }
    """
    # TODO: exec cp -f tests/assets/user.acl server_path
    corruption = "\nuser alice on nopass ~* -@all"
    # TODO: exec echo corruption >> server_path /user.acl
    try:
        err = r.run("ACL", "LOAD")
    except Exception as _catch_err:
        err = str(_catch_err)
    assert fnmatch(str(err), "*Duplicate user 'alice' found*")
    assert r.run("ACL", "GETUSER", "alice") != ""
    assert r.run("ACL", "GETUSER", "alice")["commands"] == "+@all"
    assert r.run("ACL", "GETUSER", "bob") != ""
    assert r.run("ACL", "GETUSER", "default") != ""


@pytest.mark.xfail(reason="not implemented")
def test_test_loading_an_acl_file_with_duplicate_default_user(r: ValkeyTestClient) -> None:
    """
    test {Test loading an ACL file with duplicate default user} {
        exec cp -f tests/assets/user.acl $server_path

        # Corrupt the ACL file
        set corruption "\nuser default on nopass ~* -@all"
        exec echo $corruption >> $server_path/user.acl
        catch {r ACL LOAD} err
        assert_match {*Duplicate user 'default' found*} $err

        # Verify the previous users still exist
        # NOTE: A missing user evaluates to an empty
        # string.
        assert {[r ACL GETUSER alice] != ""}
        assert_equal [dict get [r ACL GETUSER alice] commands] "+@all"
        assert {[r ACL GETUSER bob] != ""}
        assert {[r ACL GETUSER default] != ""}
    }
    """
    # TODO: exec cp -f tests/assets/user.acl server_path
    corruption = "\nuser default on nopass ~* -@all"
    # TODO: exec echo corruption >> server_path /user.acl
    try:
        err = r.run("ACL", "LOAD")
    except Exception as _catch_err:
        err = str(_catch_err)
    assert fnmatch(str(err), "*Duplicate user 'default' found*")
    assert r.run("ACL", "GETUSER", "alice") != ""
    assert r.run("ACL", "GETUSER", "alice")["commands"] == "+@all"
    assert r.run("ACL", "GETUSER", "bob") != ""
    assert r.run("ACL", "GETUSER", "default") != ""


@pytest.mark.xfail(reason="not implemented")
def test_test_loading_duplicate_users_in_config_on_startup(r: ValkeyTestClient) -> None:
    """
    test {Test loading duplicate users in config on startup} {
        catch {exec $::VALKEY_SERVER_BIN --user foo --user foo} err
        assert_match {*Duplicate user*} $err

        catch {exec $::VALKEY_SERVER_BIN --user default --user default} err
        assert_match {*Duplicate user*} $err
    } {} {external:skip}
    """
    catch("exec $::VALKEY_SERVER_BIN --user foo --user foo", "err")
    # TODO: assert_match {*Duplicate user*} err
    catch("exec $::VALKEY_SERVER_BIN --user default --user default", "err")
    # TODO: assert_match {*Duplicate user*} err


pytestmark = [pytest.mark.acl, pytest.mark.external_skip]


def test_acl_from_config_file_and_config_rewrite(r: ValkeyTestClient) -> None:
    """
    test {ACL from config file and config rewrite} {
        assert_error {NOPERM *} {r flushdb}
        r config rewrite
        restart_server 0 true false
        assert_error {NOPERM *} {r flushdb}
    }
    """
    with pytest.raises(Exception, match="NOPERM\\ .*"):
        r.run("flushdb")
    r.run("config", "rewrite")
    restart_server(0, "true", "false")
    with pytest.raises(Exception, match="NOPERM\\ .*"):
        r.run("flushdb")


"""
tags {acl external:skip} {
    set renames [list rename-command "PING RainWasHere" \
                      rename-command "RainWasHere VPING" \
                      rename-command "INCR VINCR" \
                      rename-command "SET VSET" \
                      rename-command "SADD VSADD" \
                      rename-command "HGET VHGET" \
                      rename-command "HSET VHSET" \
                      rename-command "CONFIG VCONFIG" ]
    start_server [list config_lines $renames ] {
        test {ACL still denies individual renamed commands} {
            r ACL setuser newuser on nopass ~* +acl -ping +incr
            r AUTH newuser anypass
            r VINCR mycounter ; # Should not raise an error
            assert_error {*NOPERM*ping*} {r vping}
        }

        test {ACL command classes aren't affected by command renaming} {
            r ACL setuser newuser -@all +@set +acl
            r VSADD myset a b c; # Should not raise an error
            r ACL setuser newuser +@all -@string
            r VSADD myset a b c; # Again should not raise an error
            # String commands instead should raise an error
            assert_error {*NOPERM*set*} {r vset foo bar}
            r ACL setuser newuser allcommands; # Undo commands ACL
        }

        test {ACL GETUSER provides correct results when commands renamed} {
            r ACL SETUSER adv-test
            r ACL SETUSER adv-test +@all -@hash -@slow +hget
            assert_equal "+@all -@hash -@slow +hget" [dict get [r ACL getuser adv-test] commands]

            # Categories are re-ordered if re-added
            r ACL SETUSER adv-test -@hash
            assert_equal "+@all -@slow +hget -@hash" [dict get [r ACL getuser adv-test] commands]

            # Inverting categories removes existing categories
            r ACL SETUSER adv-test +@hash
            assert_equal "+@all -@slow +hget +@hash" [dict get [r ACL getuser adv-test] commands]

            # Make sure categories are case insensitive
            r ACL SETUSER adv-test -@all +@HASH +@hash +@HaSh
            assert_equal "-@all +@hash" [dict get [r ACL getuser adv-test] commands]

            # Make sure commands are case insensitive
            r ACL SETUSER adv-test -@all +HGET +hget +hGeT
            assert_equal "-@all +hget" [dict get [r ACL getuser adv-test] commands]

            # Arbitrary category additions and removals are handled
            r ACL SETUSER adv-test -@all +@hash +@slow +@set +@set +@slow +@hash
            assert_equal "-@all +@set +@slow +@hash" [dict get [r ACL getuser adv-test] commands]

            # Arbitrary command additions and removals are handled
            r ACL SETUSER adv-test -@all +hget -hset +hset -hget
            assert_equal "-@all +hset -hget" [dict get [r ACL getuser adv-test] commands]

            # Arbitrary subcommands are compacted
            r ACL SETUSER adv-test -@all +client|list +client|list +config|get +config +acl|list -acl
            assert_equal "-@all +client|list +config -acl" [dict get [r ACL getuser adv-test] commands]
        }
    }
}
"""


"""
set server_path tmpdir "server.acl"
"""


"""
exec cp -f tests/assets/user.acl server_path
"""


@pytest.mark.xfail(reason="not implemented")
def test_test_acl_load_works_on_primary(r: ValkeyTestClient) -> None:
    """
    test "Test ACL LOAD works on primary" {
        exec cp -f tests/assets/user.acl $server_path
        $primary ACL setuser harry on nopass resetchannels &test +@all ~*
        $primary ACL save
        $primary ACL load
        $primary AUTH harry anything
    }
    """
    primary = ValkeyTestClient.create_from(r)
    primary_host = r.host
    primary_port = r.port
    # TODO: exec cp -f tests/assets/user.acl server_path
    primary.run("ACL", "setuser", "harry", "on", "nopass", "resetchannels", "&test", "+@all", "~*")
    primary.run("ACL", "save")
    primary.run("ACL", "load")
    primary.run("AUTH", "harry", "anything")


"""
start_server list overrides [list "dir" $server_path "aclfile" "user.acl"] {
    set replica [srv 0 client]
    $replica replicaof $primary_host $primary_port

    test "Test ACL LOAD works on replica" {
        # wait for replication to be in sync
        wait_for_condition 50 100 {
            [lindex [$replica role] 0] eq {slave} &&
            [string match {*master_link_status:up*} [$replica info replication]]
        } else {
            fail "Can't turn the instance into a replica"
        }

        # Check ACL LOAD works as expected
        exec cp -f tests/assets/user.acl $server_path
        $replica ACL setuser joe on nopass resetchannels &test +@all ~*
        $replica ACL save
        $replica ACL load
        $replica AUTH joe anything
    }
}
"""


# --- stubs for unimplemented TCL helpers ---


def assert_error(*args):
    raise NotImplementedError("assert_error")


def assert_no_match(*args):
    raise NotImplementedError("assert_no_match")


def assert_not_equal(*args):
    raise NotImplementedError("assert_not_equal")


def catch(*args):
    raise NotImplementedError("catch")


def cmdrstat(*args):
    raise NotImplementedError("cmdrstat")


def expr(*args):
    raise NotImplementedError("expr")


def foreach(*args):
    raise NotImplementedError("foreach")


def lsearch(*args):
    raise NotImplementedError("lsearch")


def lshuffle(*args):
    raise NotImplementedError("lshuffle")


def reconnect(*args):
    raise NotImplementedError("reconnect")


def restart_server(*args):
    raise NotImplementedError("restart_server")


def s(*args):
    raise NotImplementedError("s")


def wait_for_blocked_client(*args):
    raise NotImplementedError("wait_for_blocked_client")
