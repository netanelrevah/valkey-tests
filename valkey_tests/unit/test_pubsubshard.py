# ruff: noqa: PLR2004, ANN002, ANN201

import pytest

from tests.valkey_test_client import ValkeyTestClient

pytestmark = [pytest.mark.pubsubshard_external_skip]


def test_spublish_or_ssubscribe_basics(r: ValkeyTestClient) -> None:
    """
    test "SPUBLISH/SSUBSCRIBE basics" {
        set rd1 [valkey_deferring_client]

        # subscribe to two channels
        assert_equal {1} [ssubscribe $rd1 {chan1}]
        assert_equal {2} [ssubscribe $rd1 {chan2}]
        assert_equal 1 [r SPUBLISH chan1 hello]
        assert_equal 1 [r SPUBLISH chan2 world]
        assert_equal {smessage chan1 hello} [$rd1 read]
        assert_equal {smessage chan2 world} [$rd1 read]

        # unsubscribe from one of the channels
        sunsubscribe $rd1 {chan1}
        assert_equal 0 [r SPUBLISH chan1 hello]
        assert_equal 1 [r SPUBLISH chan2 world]
        assert_equal {smessage chan2 world} [$rd1 read]

        # unsubscribe from the remaining channel
        sunsubscribe $rd1 {chan2}
        assert_equal 0 [r SPUBLISH chan1 hello]
        assert_equal 0 [r SPUBLISH chan2 world]

        # clean up clients
        $rd1 close
    }
    """
    rd1 = ValkeyTestClient.create_from(r)
    assert "1" == ssubscribe(rd1, "chan1")
    assert "2" == ssubscribe(rd1, "chan2")
    assert 1 == r.run("SPUBLISH", "chan1", "hello")
    assert 1 == r.run("SPUBLISH", "chan2", "world")
    assert "smessage chan1 hello" == rd1.run("read")
    assert "smessage chan2 world" == rd1.run("read")
    sunsubscribe(rd1, "chan1")
    assert 0 == r.run("SPUBLISH", "chan1", "hello")
    assert 1 == r.run("SPUBLISH", "chan2", "world")
    assert "smessage chan2 world" == rd1.run("read")
    sunsubscribe(rd1, "chan2")
    assert 0 == r.run("SPUBLISH", "chan1", "hello")
    assert 0 == r.run("SPUBLISH", "chan2", "world")
    rd1.run("close")


def test_spublish_or_ssubscribe_with_two_clients(r: ValkeyTestClient) -> None:
    """
    test "SPUBLISH/SSUBSCRIBE with two clients" {
        set rd1 [valkey_deferring_client]
        set rd2 [valkey_deferring_client]

        assert_equal {1} [ssubscribe $rd1 {chan1}]
        assert_equal {1} [ssubscribe $rd2 {chan1}]
        assert_equal 2 [r SPUBLISH chan1 hello]
        assert_equal {smessage chan1 hello} [$rd1 read]
        assert_equal {smessage chan1 hello} [$rd2 read]

        # clean up clients
        $rd1 close
        $rd2 close
    }
    """
    rd1 = ValkeyTestClient.create_from(r)
    rd2 = ValkeyTestClient.create_from(r)
    assert "1" == ssubscribe(rd1, "chan1")
    assert "1" == ssubscribe(rd2, "chan1")
    assert 2 == r.run("SPUBLISH", "chan1", "hello")
    assert "smessage chan1 hello" == rd1.run("read")
    assert "smessage chan1 hello" == rd2.run("read")
    rd1.run("close")
    rd2.run("close")


def test_spublish_or_ssubscribe_after_unsubscribe_without_arguments(r: ValkeyTestClient) -> None:
    """
    test "SPUBLISH/SSUBSCRIBE after UNSUBSCRIBE without arguments" {
        set rd1 [valkey_deferring_client]
        assert_equal {1} [ssubscribe $rd1 {chan1}]
        assert_equal {2} [ssubscribe $rd1 {chan2}]
        assert_equal {3} [ssubscribe $rd1 {chan3}]
        sunsubscribe $rd1

        # wait for the unsubscribe to take effect
        wait_for_condition 50 100 {
            [r spublish chan1 hello] eq 0
        } else {
            fail "unsubscribe did not take effect"
        }

        assert_equal 0 [r SPUBLISH chan1 hello]
        assert_equal 0 [r SPUBLISH chan2 hello]
        assert_equal 0 [r SPUBLISH chan3 hello]

        # clean up clients
        $rd1 close
    }
    """
    rd1 = ValkeyTestClient.create_from(r)
    assert "1" == ssubscribe(rd1, "chan1")
    assert "2" == ssubscribe(rd1, "chan2")
    assert "3" == ssubscribe(rd1, "chan3")
    sunsubscribe(rd1)
    wait_for_condition(
        50,
        100,
        "            [r spublish chan1 hello] eq 0\n        ",
        "else",
        '            fail "unsubscribe did not take effect"\n        ',
    )
    assert 0 == r.run("SPUBLISH", "chan1", "hello")
    assert 0 == r.run("SPUBLISH", "chan2", "hello")
    assert 0 == r.run("SPUBLISH", "chan3", "hello")
    rd1.run("close")


def test_ssubscribe_to_one_channel_more_than_once(r: ValkeyTestClient) -> None:
    """
    test "SSUBSCRIBE to one channel more than once" {
        set rd1 [valkey_deferring_client]
        assert_equal {1 1 1} [ssubscribe $rd1 {chan1 chan1 chan1}]
        assert_equal 1 [r SPUBLISH chan1 hello]
        assert_equal {smessage chan1 hello} [$rd1 read]

        # clean up clients
        $rd1 close
    }
    """
    rd1 = ValkeyTestClient.create_from(r)
    assert "1 1 1" == ssubscribe(rd1, "chan1 chan1 chan1")
    assert 1 == r.run("SPUBLISH", "chan1", "hello")
    assert "smessage chan1 hello" == rd1.run("read")
    rd1.run("close")


def test_sunsubscribe_from_non_subscribed_channels(r: ValkeyTestClient) -> None:
    """
    test "SUNSUBSCRIBE from non-subscribed channels" {
        set rd1 [valkey_deferring_client]
        assert_equal {0} [sunsubscribe $rd1 {foo}]
        assert_equal {0} [sunsubscribe $rd1 {bar}]
        assert_equal {0} [sunsubscribe $rd1 {quux}]

        # clean up clients
        $rd1 close
    }
    """
    rd1 = ValkeyTestClient.create_from(r)
    assert "0" == sunsubscribe(rd1, "foo")
    assert "0" == sunsubscribe(rd1, "bar")
    assert "0" == sunsubscribe(rd1, "quux")
    rd1.run("close")


def test_pubsub_command_basics(r: ValkeyTestClient) -> None:
    """
    test "PUBSUB command basics" {
        r pubsub shardnumsub abc def
    } {abc 0 def 0}
    """
    assert r.run("pubsub", "shardnumsub", "abc", "def") == "abc 0 def 0"


def test_spublish_or_ssubscribe_with_two_clients_1(r: ValkeyTestClient) -> None:
    """
    test "SPUBLISH/SSUBSCRIBE with two clients" {
        set rd1 [valkey_deferring_client]
        set rd2 [valkey_deferring_client]

        assert_equal {1} [ssubscribe $rd1 {chan1}]
        assert_equal {1} [ssubscribe $rd2 {chan1}]
        assert_equal 2 [r SPUBLISH chan1 hello]
        assert_equal "chan1 2" [r pubsub shardnumsub chan1]
        assert_equal "chan1" [r pubsub shardchannels]

        # clean up clients
        $rd1 close
        $rd2 close
    }
    """
    rd1 = ValkeyTestClient.create_from(r)
    rd2 = ValkeyTestClient.create_from(r)
    assert "1" == ssubscribe(rd1, "chan1")
    assert "1" == ssubscribe(rd2, "chan1")
    assert 2 == r.run("SPUBLISH", "chan1", "hello")
    assert "chan1 2" == r.run("pubsub", "shardnumsub", "chan1")
    assert "chan1" == r.run("pubsub", "shardchannels")
    rd1.run("close")
    rd2.run("close")


def test_spublish_or_ssubscribe_with_publish_or_subscribe(r: ValkeyTestClient) -> None:
    """
    test "SPUBLISH/SSUBSCRIBE with PUBLISH/SUBSCRIBE" {
        set rd1 [valkey_deferring_client]
        set rd2 [valkey_deferring_client]

        assert_equal {1} [ssubscribe $rd1 {chan1}]
        assert_equal {1} [subscribe $rd2 {chan1}]
        assert_equal 1 [r SPUBLISH chan1 hello]
        assert_equal 1 [r publish chan1 hello]
        assert_equal "chan1 1" [r pubsub shardnumsub chan1]
        assert_equal "chan1 1" [r pubsub numsub chan1]
        assert_equal "chan1" [r pubsub shardchannels]
        assert_equal "chan1" [r pubsub channels]

        $rd1 close
        $rd2 close
    }
    """
    rd1 = ValkeyTestClient.create_from(r)
    rd2 = ValkeyTestClient.create_from(r)
    assert "1" == ssubscribe(rd1, "chan1")
    assert "1" == subscribe(rd2, "chan1")
    assert 1 == r.run("SPUBLISH", "chan1", "hello")
    assert 1 == r.run("publish", "chan1", "hello")
    assert "chan1 1" == r.run("pubsub", "shardnumsub", "chan1")
    assert "chan1 1" == r.run("pubsub", "numsub", "chan1")
    assert "chan1" == r.run("pubsub", "shardchannels")
    assert "chan1" == r.run("pubsub", "channels")
    rd1.run("close")
    rd2.run("close")


def test_pubsubshard_with_client_reply_off(r: ValkeyTestClient) -> None:
    """
    test "PubSubShard with CLIENT REPLY OFF" {
        set rd [valkey_deferring_client]
        $rd hello 3
        $rd read ;# Discard the hello reply

        # Test that the ssubscribe notification is ok
        $rd client reply off
        $rd ping
        assert_equal {1} [ssubscribe $rd channel]

        # Test that the spublish notification is ok
        $rd client reply off
        $rd ping
        assert_equal 1 [r spublish channel hello]
        assert_equal {smessage channel hello} [$rd read]

        # Test that sunsubscribe notification is ok
        $rd client reply off
        $rd ping
        assert_equal {0} [sunsubscribe $rd channel]

        $rd close
    }
    """
    rd = ValkeyTestClient.create_from(r)
    rd.run("hello", 3)
    rd.run("read")
    rd.run("client", "reply", "off")
    rd.run("ping")
    assert "1" == ssubscribe(rd, "channel")
    rd.run("client", "reply", "off")
    rd.run("ping")
    assert 1 == r.run("spublish", "channel", "hello")
    assert "smessage channel hello" == rd.run("read")
    rd.run("client", "reply", "off")
    rd.run("ping")
    assert "0" == sunsubscribe(rd, "channel")
    rd.run("close")


pytestmark = [pytest.mark.pubsubshard_external_skip]


"""
start_server {tags {"pubsubshard external:skip"}} {
    set node_0 [srv 0 client]
    set node_0_host [srv 0 host]
    set node_0_port [srv 0 port]

    set node_1 [srv -1 client]
    set node_1_host [srv -1 host]
    set node_1_port [srv -1 port]

    test {setup replication for following tests} {
        $node_1 replicaof $node_0_host $node_0_port
        wait_for_sync $node_1
    }

    test {publish message to master and receive on replica} {
        set rd0 [valkey_deferring_client node_0_host node_0_port]
        set rd1 [valkey_deferring_client node_1_host node_1_port]

        assert_equal {1} [ssubscribe $rd1 {chan1}]
        $rd0 SPUBLISH chan1 hello
        assert_equal {smessage chan1 hello} [$rd1 read]
        $rd0 SPUBLISH chan1 world
        assert_equal {smessage chan1 world} [$rd1 read]
    }
}
"""


# --- stubs for unimplemented TCL helpers ---


def ssubscribe(*args):
    raise NotImplementedError("ssubscribe")


def subscribe(*args):
    raise NotImplementedError("subscribe")


def sunsubscribe(*args):
    raise NotImplementedError("sunsubscribe")


def wait_for_condition(*args):
    raise NotImplementedError("wait_for_condition")
