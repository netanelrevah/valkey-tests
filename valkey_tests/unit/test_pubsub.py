# ruff: noqa: PLR2004, F841, ANN001, ANN002, ANN201

import pytest

from tests.valkey_test_client import ValkeyTestClient

pytestmark = [pytest.mark.pubsub_network]


"""
if {$::singledb} {
    set db 0
} else {
    set db 9
}
"""


"""
set rd1 valkey_deferring_client
"""


"""
if {[lsearch $::denytags "resp3"] >= 0} {
    if {$resp == 3} {continue}
} elseif {$::force_resp3} {
    if {$resp == 2} {continue}
}
"""


"""
$rd1 hello resp
"""


"""
$rd1 read
"""


@pytest.mark.xfail(reason="not implemented")
@pytest.mark.parametrize(["resp"], [(2), (3)])
def test_pub_or_sub_ping_on_resp_resp(r: ValkeyTestClient, resp) -> None:
    """
    test "Pub/Sub PING on RESP$resp" {
        subscribe $rd1 somechannel
        # While subscribed to non-zero channels PING works in Pub/Sub mode.
        $rd1 ping
        $rd1 ping "foo"
        # In RESP3, the SUBSCRIBEd client can issue any command and get a reply, so the PINGs are standard
        # In RESP2, only a handful of commands are allowed after a client is SUBSCRIBED (PING is one of them).
        # For some reason, the reply in that case is an array with two elements: "pong"  and argv[1] or an empty string
        # God knows why. Done in commit 2264b981
        if {$resp == 3} {
            assert_equal {PONG} [$rd1 read]
            assert_equal {foo} [$rd1 read]
        } else {
            assert_equal {pong {}} [$rd1 read]
            assert_equal {pong foo} [$rd1 read]
        }
        unsubscribe $rd1 somechannel
        # Now we are unsubscribed, PING should just return PONG.
        $rd1 ping
        assert_equal {PONG} [$rd1 read]
    }
    """
    # TODO: subscribe rd1 somechannel
    # TODO: $rd1 ping
    # TODO: $rd1 ping "foo"
    if_(
        "$resp == 3",
        "                assert_equal {PONG} [$rd1 read]\n                assert_equal {foo} [$rd1 read]\n            ",
        "else",
        "                assert_equal {pong {}} [$rd1 read]\n                assert_equal {pong foo} [$rd1 read]\n            ",
    )
    # TODO: unsubscribe rd1 somechannel
    # TODO: $rd1 ping
    # TODO: assert_equal {PONG} $rd1 read


"""
$rd1 close
"""


def test_publish_or_subscribe_basics(r: ValkeyTestClient) -> None:
    """
    test "PUBLISH/SUBSCRIBE basics" {
        set rd1 [valkey_deferring_client]

        # subscribe to two channels
        assert_equal {1 2} [subscribe $rd1 {chan1 chan2}]
        assert_equal 1 [r publish chan1 hello]
        assert_equal 1 [r publish chan2 world]
        assert_equal {message chan1 hello} [$rd1 read]
        assert_equal {message chan2 world} [$rd1 read]

        # unsubscribe from one of the channels
        unsubscribe $rd1 {chan1}
        assert_equal 0 [r publish chan1 hello]
        assert_equal 1 [r publish chan2 world]
        assert_equal {message chan2 world} [$rd1 read]

        # unsubscribe from the remaining channel
        unsubscribe $rd1 {chan2}
        assert_equal 0 [r publish chan1 hello]
        assert_equal 0 [r publish chan2 world]

        # clean up clients
        $rd1 close
    }
    """
    rd1 = valkey_deferring_client()
    assert "1 2" == subscribe(rd1, "chan1 chan2")
    assert 1 == r.run("publish", "chan1", "hello")
    assert 1 == r.run("publish", "chan2", "world")
    assert "message chan1 hello" == rd1.run("read")
    assert "message chan2 world" == rd1.run("read")
    unsubscribe(rd1, "chan1")
    assert 0 == r.run("publish", "chan1", "hello")
    assert 1 == r.run("publish", "chan2", "world")
    assert "message chan2 world" == rd1.run("read")
    unsubscribe(rd1, "chan2")
    assert 0 == r.run("publish", "chan1", "hello")
    assert 0 == r.run("publish", "chan2", "world")
    rd1.run("close")


def test_publish_or_subscribe_with_two_clients(r: ValkeyTestClient) -> None:
    """
    test "PUBLISH/SUBSCRIBE with two clients" {
        set rd1 [valkey_deferring_client]
        set rd2 [valkey_deferring_client]

        assert_equal {1} [subscribe $rd1 {chan1}]
        assert_equal {1} [subscribe $rd2 {chan1}]
        assert_equal 2 [r publish chan1 hello]
        assert_equal {message chan1 hello} [$rd1 read]
        assert_equal {message chan1 hello} [$rd2 read]

        # clean up clients
        $rd1 close
        $rd2 close
    }
    """
    rd1 = valkey_deferring_client()
    rd2 = valkey_deferring_client()
    assert "1" == subscribe(rd1, "chan1")
    assert "1" == subscribe(rd2, "chan1")
    assert 2 == r.run("publish", "chan1", "hello")
    assert "message chan1 hello" == rd1.run("read")
    assert "message chan1 hello" == rd2.run("read")
    rd1.run("close")
    rd2.run("close")


def test_publish_or_subscribe_after_unsubscribe_without_arguments(r: ValkeyTestClient) -> None:
    """
    test "PUBLISH/SUBSCRIBE after UNSUBSCRIBE without arguments" {
        set rd1 [valkey_deferring_client]
        assert_equal {1 2 3} [subscribe $rd1 {chan1 chan2 chan3}]
        unsubscribe $rd1
        # wait for the unsubscribe to take effect
        wait_for_condition 50 100 {
            [r publish chan1 hello] eq 0
        } else {
            fail "unsubscribe did not take effect"
        }
        assert_equal 0 [r publish chan1 hello]
        assert_equal 0 [r publish chan2 hello]
        assert_equal 0 [r publish chan3 hello]

        # clean up clients
        $rd1 close
    }
    """
    rd1 = valkey_deferring_client()
    assert "1 2 3" == subscribe(rd1, "chan1 chan2 chan3")
    unsubscribe(rd1)
    wait_for_condition(
        50,
        100,
        "            [r publish chan1 hello] eq 0\n        ",
        "else",
        '            fail "unsubscribe did not take effect"\n        ',
    )
    assert 0 == r.run("publish", "chan1", "hello")
    assert 0 == r.run("publish", "chan2", "hello")
    assert 0 == r.run("publish", "chan3", "hello")
    rd1.run("close")


def test_subscribe_to_one_channel_more_than_once(r: ValkeyTestClient) -> None:
    """
    test "SUBSCRIBE to one channel more than once" {
        set rd1 [valkey_deferring_client]
        assert_equal {1 1 1} [subscribe $rd1 {chan1 chan1 chan1}]
        assert_equal 1 [r publish chan1 hello]
        assert_equal {message chan1 hello} [$rd1 read]

        # clean up clients
        $rd1 close
    }
    """
    rd1 = valkey_deferring_client()
    assert "1 1 1" == subscribe(rd1, "chan1 chan1 chan1")
    assert 1 == r.run("publish", "chan1", "hello")
    assert "message chan1 hello" == rd1.run("read")
    rd1.run("close")


def test_unsubscribe_from_non_subscribed_channels(r: ValkeyTestClient) -> None:
    """
    test "UNSUBSCRIBE from non-subscribed channels" {
        set rd1 [valkey_deferring_client]
        assert_equal {0 0 0} [unsubscribe $rd1 {foo bar quux}]
        # clean up clients
        $rd1 close
    }
    """
    rd1 = valkey_deferring_client()
    assert "0 0 0" == unsubscribe(rd1, "foo bar quux")
    rd1.run("close")


def test_publish_or_psubscribe_basics(r: ValkeyTestClient) -> None:
    """
    test "PUBLISH/PSUBSCRIBE basics" {
        set rd1 [valkey_deferring_client]

        # subscribe to two patterns
        assert_equal {1 2} [psubscribe $rd1 {foo.* bar.*}]
        assert_equal 1 [r publish foo.1 hello]
        assert_equal 1 [r publish bar.1 hello]
        assert_equal 0 [r publish foo1 hello]
        assert_equal 0 [r publish barfoo.1 hello]
        assert_equal 0 [r publish qux.1 hello]
        assert_equal {pmessage foo.* foo.1 hello} [$rd1 read]
        assert_equal {pmessage bar.* bar.1 hello} [$rd1 read]

        # unsubscribe from one of the patterns
        assert_equal {1} [punsubscribe $rd1 {foo.*}]
        assert_equal 0 [r publish foo.1 hello]
        assert_equal 1 [r publish bar.1 hello]
        assert_equal {pmessage bar.* bar.1 hello} [$rd1 read]

        # unsubscribe from the remaining pattern
        assert_equal {0} [punsubscribe $rd1 {bar.*}]
        assert_equal 0 [r publish foo.1 hello]
        assert_equal 0 [r publish bar.1 hello]

        # clean up clients
        $rd1 close
    }
    """
    rd1 = valkey_deferring_client()
    assert "1 2" == psubscribe(rd1, "foo.* bar.*")
    assert 1 == r.run("publish", "foo.1", "hello")
    assert 1 == r.run("publish", "bar.1", "hello")
    assert 0 == r.run("publish", "foo1", "hello")
    assert 0 == r.run("publish", "barfoo.1", "hello")
    assert 0 == r.run("publish", "qux.1", "hello")
    assert "pmessage foo.* foo.1 hello" == rd1.run("read")
    assert "pmessage bar.* bar.1 hello" == rd1.run("read")
    assert "1" == punsubscribe(rd1, "foo.*")
    assert 0 == r.run("publish", "foo.1", "hello")
    assert 1 == r.run("publish", "bar.1", "hello")
    assert "pmessage bar.* bar.1 hello" == rd1.run("read")
    assert "0" == punsubscribe(rd1, "bar.*")
    assert 0 == r.run("publish", "foo.1", "hello")
    assert 0 == r.run("publish", "bar.1", "hello")
    rd1.run("close")


def test_publish_or_psubscribe_with_two_clients(r: ValkeyTestClient) -> None:
    """
    test "PUBLISH/PSUBSCRIBE with two clients" {
        set rd1 [valkey_deferring_client]
        set rd2 [valkey_deferring_client]

        assert_equal {1} [psubscribe $rd1 {chan.*}]
        assert_equal {1} [psubscribe $rd2 {chan.*}]
        assert_equal 2 [r publish chan.foo hello]
        assert_equal {pmessage chan.* chan.foo hello} [$rd1 read]
        assert_equal {pmessage chan.* chan.foo hello} [$rd2 read]

        # clean up clients
        $rd1 close
        $rd2 close
    }
    """
    rd1 = valkey_deferring_client()
    rd2 = valkey_deferring_client()
    assert "1" == psubscribe(rd1, "chan.*")
    assert "1" == psubscribe(rd2, "chan.*")
    assert 2 == r.run("publish", "chan.foo", "hello")
    assert "pmessage chan.* chan.foo hello" == rd1.run("read")
    assert "pmessage chan.* chan.foo hello" == rd2.run("read")
    rd1.run("close")
    rd2.run("close")


def test_publish_or_psubscribe_after_punsubscribe_without_arguments(r: ValkeyTestClient) -> None:
    """
    test "PUBLISH/PSUBSCRIBE after PUNSUBSCRIBE without arguments" {
        set rd1 [valkey_deferring_client]
        assert_equal {1 2 3} [psubscribe $rd1 {chan1.* chan2.* chan3.*}]
        punsubscribe $rd1
        # wait for the unsubscribe to take effect
        wait_for_condition 50 100 {
            [r publish chan1.hi hello] eq 0
        } else {
            fail "unsubscribe did not take effect"
        }
        assert_equal 0 [r publish chan1.hi hello]
        assert_equal 0 [r publish chan2.hi hello]
        assert_equal 0 [r publish chan3.hi hello]

        # clean up clients
        $rd1 close
    }
    """
    rd1 = valkey_deferring_client()
    assert "1 2 3" == psubscribe(rd1, "chan1.* chan2.* chan3.*")
    punsubscribe(rd1)
    wait_for_condition(
        50,
        100,
        "            [r publish chan1.hi hello] eq 0\n        ",
        "else",
        '            fail "unsubscribe did not take effect"\n        ',
    )
    assert 0 == r.run("publish", "chan1.hi", "hello")
    assert 0 == r.run("publish", "chan2.hi", "hello")
    assert 0 == r.run("publish", "chan3.hi", "hello")
    rd1.run("close")


@pytest.mark.xfail(reason="not implemented")
def test_pubsub_messages_with_client_reply_off(r: ValkeyTestClient) -> None:
    """
    test "PubSub messages with CLIENT REPLY OFF" {
        set rd [valkey_deferring_client]
        $rd hello 3
        $rd read ;# Discard the hello reply

        # Test that the subscribe/psubscribe notification is ok
        $rd client reply off
        assert_equal {1} [subscribe $rd channel]
        assert_equal {2} [psubscribe $rd ch*]

        # Test that the publish notification is ok
        $rd client reply off
        assert_equal 2 [r publish channel hello]
        assert_equal {message channel hello} [$rd read]
        assert_equal {pmessage ch* channel hello} [$rd read]

        # Test that the unsubscribe/punsubscribe notification is ok
        $rd client reply off
        assert_equal {1} [unsubscribe $rd channel]
        assert_equal {0} [punsubscribe $rd ch*]

        $rd close
    } {0} {resp3}
    """
    rd = valkey_deferring_client()
    rd.run("hello", 3)
    rd.run("read")
    rd.run("client", "reply", "off")
    assert "1" == subscribe(rd, "channel")
    assert "2" == psubscribe(rd, "ch*")
    rd.run("client", "reply", "off")
    assert 2 == r.run("publish", "channel", "hello")
    assert "message channel hello" == rd.run("read")
    assert "pmessage ch* channel hello" == rd.run("read")
    rd.run("client", "reply", "off")
    assert "1" == unsubscribe(rd, "channel")
    assert "0" == punsubscribe(rd, "ch*")
    # TODO: $rd close
    assert False


def test_punsubscribe_from_non_subscribed_channels(r: ValkeyTestClient) -> None:
    """
    test "PUNSUBSCRIBE from non-subscribed channels" {
        set rd1 [valkey_deferring_client]
        assert_equal {0 0 0} [punsubscribe $rd1 {foo.* bar.* quux.*}]

        # clean up clients
        $rd1 close
    }
    """
    rd1 = valkey_deferring_client()
    assert "0 0 0" == punsubscribe(rd1, "foo.* bar.* quux.*")
    rd1.run("close")


def test_numsub_returns_numbers_not_strings_1561(r: ValkeyTestClient) -> None:
    """
    test "NUMSUB returns numbers, not strings (#1561)" {
        r pubsub numsub abc def
    } {abc 0 def 0}
    """
    assert r.run("pubsub", "numsub", "abc", "def") == "abc 0 def 0"


def test_numpats_returns_the_number_of_unique_patterns(r: ValkeyTestClient) -> None:
    """
    test "NUMPATs returns the number of unique patterns" {
        set rd1 [valkey_deferring_client]
        set rd2 [valkey_deferring_client]

        # Three unique patterns and one that overlaps
        psubscribe $rd1 "foo*"
        psubscribe $rd2 "foo*"
        psubscribe $rd1 "bar*"
        psubscribe $rd2 "baz*"

        set patterns [r pubsub numpat]

        # clean up clients
        punsubscribe $rd1
        punsubscribe $rd2
        assert_equal 3 $patterns
        $rd1 close
        $rd2 close
    }
    """
    rd1 = valkey_deferring_client()
    rd2 = valkey_deferring_client()
    psubscribe(rd1, "foo*")
    psubscribe(rd2, "foo*")
    psubscribe(rd1, "bar*")
    psubscribe(rd2, "baz*")
    patterns = r.run("pubsub", "numpat")
    punsubscribe(rd1)
    punsubscribe(rd2)
    assert 3 == patterns
    rd1.run("close")
    rd2.run("close")


def test_mix_subscribe_and_psubscribe(r: ValkeyTestClient) -> None:
    """
    test "Mix SUBSCRIBE and PSUBSCRIBE" {
        set rd1 [valkey_deferring_client]
        assert_equal {1} [subscribe $rd1 {foo.bar}]
        assert_equal {2} [psubscribe $rd1 {foo.*}]

        assert_equal 2 [r publish foo.bar hello]
        assert_equal {message foo.bar hello} [$rd1 read]
        assert_equal {pmessage foo.* foo.bar hello} [$rd1 read]

        # clean up clients
        $rd1 close
    }
    """
    rd1 = valkey_deferring_client()
    assert "1" == subscribe(rd1, "foo.bar")
    assert "2" == psubscribe(rd1, "foo.*")
    assert 2 == r.run("publish", "foo.bar", "hello")
    assert "message foo.bar hello" == rd1.run("read")
    assert "pmessage foo.* foo.bar hello" == rd1.run("read")
    rd1.run("close")


@pytest.mark.xfail(reason="not implemented")
def test_punsubscribe_and_unsubscribe_should_always_reply(r: ValkeyTestClient) -> None:
    """
    test "PUNSUBSCRIBE and UNSUBSCRIBE should always reply" {
        # Make sure we are not subscribed to any channel at all.
        r punsubscribe
        r unsubscribe
        # Now check if the commands still reply correctly.
        set reply1 [r punsubscribe]
        set reply2 [r unsubscribe]
        concat $reply1 $reply2
    } {punsubscribe {} 0 unsubscribe {} 0}
    """
    r.run("punsubscribe")
    r.run("unsubscribe")
    reply1 = r.run("punsubscribe")
    reply2 = r.run("unsubscribe")
    # TODO: concat reply1 reply2
    assert False


@pytest.mark.xfail(reason="not implemented")
def test_keyspace_notifications_we_receive_keyspace_notifications(r: ValkeyTestClient) -> None:
    """
    test "Keyspace notifications: we receive keyspace notifications" {
        r config set notify-keyspace-events KA
        set rd1 [valkey_deferring_client]
        $rd1 CLIENT REPLY OFF ;# Make sure it works even if replies are silenced
        assert_equal {1} [psubscribe $rd1 *]
        r set foo bar
        assert_equal "pmessage * __keyspace@${db}__:foo set" [$rd1 read]
        $rd1 close
    }
    """
    r.run("config", "set", "notify-keyspace-events", "KA")
    rd1 = valkey_deferring_client()
    rd1.run("CLIENT", "REPLY", "OFF")
    assert "1" == psubscribe(rd1, "*")
    r.run("set", "foo", "bar")
    # TODO: assert_equal "pmessage * __keyspace@${db}__:foo set" $rd1 read
    rd1.run("close")


@pytest.mark.xfail(reason="not implemented")
def test_keyspace_notifications_we_receive_keyevent_notifications(r: ValkeyTestClient) -> None:
    """
    test "Keyspace notifications: we receive keyevent notifications" {
        r config set notify-keyspace-events EA
        set rd1 [valkey_deferring_client]
        $rd1 CLIENT REPLY SKIP ;# Make sure it works even if replies are silenced
        assert_equal {1} [psubscribe $rd1 *]
        r set foo bar
        assert_equal "pmessage * __keyevent@${db}__:set foo" [$rd1 read]
        $rd1 close
    }
    """
    r.run("config", "set", "notify-keyspace-events", "EA")
    rd1 = valkey_deferring_client()
    rd1.run("CLIENT", "REPLY", "SKIP")
    assert "1" == psubscribe(rd1, "*")
    r.run("set", "foo", "bar")
    # TODO: assert_equal "pmessage * __keyevent@${db}__:set foo" $rd1 read
    rd1.run("close")


@pytest.mark.xfail(reason="not implemented")
def test_keyspace_notifications_we_can_receive_both_kind_of_events(r: ValkeyTestClient) -> None:
    """
    test "Keyspace notifications: we can receive both kind of events" {
        r config set notify-keyspace-events KEA
        set rd1 [valkey_deferring_client]
        $rd1 CLIENT REPLY ON ;# Just coverage
        assert_equal {OK} [$rd1 read]
        assert_equal {1} [psubscribe $rd1 *]
        r set foo bar
        assert_equal "pmessage * __keyspace@${db}__:foo set" [$rd1 read]
        assert_equal "pmessage * __keyevent@${db}__:set foo" [$rd1 read]
        $rd1 close
    }
    """
    r.run("config", "set", "notify-keyspace-events", "KEA")
    rd1 = valkey_deferring_client()
    rd1.run("CLIENT", "REPLY", "ON")
    assert "OK" == rd1.run("read")
    assert "1" == psubscribe(rd1, "*")
    r.run("set", "foo", "bar")
    # TODO: assert_equal "pmessage * __keyspace@${db}__:foo set" $rd1 read
    # TODO: assert_equal "pmessage * __keyevent@${db}__:set foo" $rd1 read
    rd1.run("close")


@pytest.mark.xfail(reason="not implemented")
def test_keyspace_notifications_we_are_able_to_mask_events(r: ValkeyTestClient) -> None:
    """
    test "Keyspace notifications: we are able to mask events" {
        r config set notify-keyspace-events KEl
        r del mylist
        set rd1 [valkey_deferring_client]
        assert_equal {1} [psubscribe $rd1 *]
        r set foo bar
        r lpush mylist a
        # No notification for set, because only list commands are enabled.
        assert_equal "pmessage * __keyspace@${db}__:mylist lpush" [$rd1 read]
        assert_equal "pmessage * __keyevent@${db}__:lpush mylist" [$rd1 read]
        $rd1 close
    }
    """
    r.run("config", "set", "notify-keyspace-events", "KEl")
    r.run("del", "mylist")
    rd1 = valkey_deferring_client()
    assert "1" == psubscribe(rd1, "*")
    r.run("set", "foo", "bar")
    r.run("lpush", "mylist", "a")
    # TODO: assert_equal "pmessage * __keyspace@${db}__:mylist lpush" $rd1 read
    # TODO: assert_equal "pmessage * __keyevent@${db}__:lpush mylist" $rd1 read
    rd1.run("close")


@pytest.mark.xfail(reason="not implemented")
def test_keyspace_notifications_general_events_test(r: ValkeyTestClient) -> None:
    """
    test "Keyspace notifications: general events test" {
        r config set notify-keyspace-events KEg
        set rd1 [valkey_deferring_client]
        assert_equal {1} [psubscribe $rd1 *]
        r set foo bar
        r expire foo 1
        r del foo
        assert_equal "pmessage * __keyspace@${db}__:foo expire" [$rd1 read]
        assert_equal "pmessage * __keyevent@${db}__:expire foo" [$rd1 read]
        assert_equal "pmessage * __keyspace@${db}__:foo del" [$rd1 read]
        assert_equal "pmessage * __keyevent@${db}__:del foo" [$rd1 read]
        $rd1 close
    }
    """
    r.run("config", "set", "notify-keyspace-events", "KEg")
    rd1 = valkey_deferring_client()
    assert "1" == psubscribe(rd1, "*")
    r.run("set", "foo", "bar")
    r.run("expire", "foo", 1)
    r.run("del", "foo")
    # TODO: assert_equal "pmessage * __keyspace@${db}__:foo expire" $rd1 read
    # TODO: assert_equal "pmessage * __keyevent@${db}__:expire foo" $rd1 read
    # TODO: assert_equal "pmessage * __keyspace@${db}__:foo del" $rd1 read
    # TODO: assert_equal "pmessage * __keyevent@${db}__:del foo" $rd1 read
    rd1.run("close")


@pytest.mark.xfail(reason="not implemented")
def test_keyspace_notifications_list_events_test(r: ValkeyTestClient) -> None:
    """
    test "Keyspace notifications: list events test" {
        r config set notify-keyspace-events KEl
        r del mylist
        set rd1 [valkey_deferring_client]
        assert_equal {1} [psubscribe $rd1 *]
        r lpush mylist a
        r rpush mylist a
        r rpop mylist
        assert_equal "pmessage * __keyspace@${db}__:mylist lpush" [$rd1 read]
        assert_equal "pmessage * __keyevent@${db}__:lpush mylist" [$rd1 read]
        assert_equal "pmessage * __keyspace@${db}__:mylist rpush" [$rd1 read]
        assert_equal "pmessage * __keyevent@${db}__:rpush mylist" [$rd1 read]
        assert_equal "pmessage * __keyspace@${db}__:mylist rpop" [$rd1 read]
        assert_equal "pmessage * __keyevent@${db}__:rpop mylist" [$rd1 read]
        $rd1 close
    }
    """
    r.run("config", "set", "notify-keyspace-events", "KEl")
    r.run("del", "mylist")
    rd1 = valkey_deferring_client()
    assert "1" == psubscribe(rd1, "*")
    r.run("lpush", "mylist", "a")
    r.run("rpush", "mylist", "a")
    r.run("rpop", "mylist")
    # TODO: assert_equal "pmessage * __keyspace@${db}__:mylist lpush" $rd1 read
    # TODO: assert_equal "pmessage * __keyevent@${db}__:lpush mylist" $rd1 read
    # TODO: assert_equal "pmessage * __keyspace@${db}__:mylist rpush" $rd1 read
    # TODO: assert_equal "pmessage * __keyevent@${db}__:rpush mylist" $rd1 read
    # TODO: assert_equal "pmessage * __keyspace@${db}__:mylist rpop" $rd1 read
    # TODO: assert_equal "pmessage * __keyevent@${db}__:rpop mylist" $rd1 read
    rd1.run("close")


@pytest.mark.xfail(reason="not implemented")
def test_keyspace_notifications_set_events_test(r: ValkeyTestClient) -> None:
    """
    test "Keyspace notifications: set events test" {
        r config set notify-keyspace-events Ks
        r del myset
        set rd1 [valkey_deferring_client]
        assert_equal {1} [psubscribe $rd1 *]
        r sadd myset a b c d
        r srem myset x
        r sadd myset x y z
        r srem myset x
        assert_equal "pmessage * __keyspace@${db}__:myset sadd" [$rd1 read]
        assert_equal "pmessage * __keyspace@${db}__:myset sadd" [$rd1 read]
        assert_equal "pmessage * __keyspace@${db}__:myset srem" [$rd1 read]
        $rd1 close
    }
    """
    r.run("config", "set", "notify-keyspace-events", "Ks")
    r.run("del", "myset")
    rd1 = valkey_deferring_client()
    assert "1" == psubscribe(rd1, "*")
    r.run("sadd", "myset", "a", "b", "c", "d")
    r.run("srem", "myset", "x")
    r.run("sadd", "myset", "x", "y", "z")
    r.run("srem", "myset", "x")
    # TODO: assert_equal "pmessage * __keyspace@${db}__:myset sadd" $rd1 read
    # TODO: assert_equal "pmessage * __keyspace@${db}__:myset sadd" $rd1 read
    # TODO: assert_equal "pmessage * __keyspace@${db}__:myset srem" $rd1 read
    rd1.run("close")


@pytest.mark.xfail(reason="not implemented")
def test_keyspace_notifications_zset_events_test(r: ValkeyTestClient) -> None:
    """
    test "Keyspace notifications: zset events test" {
        r config set notify-keyspace-events Kz
        r del myzset
        set rd1 [valkey_deferring_client]
        assert_equal {1} [psubscribe $rd1 *]
        r zadd myzset 1 a 2 b
        r zrem myzset x
        r zadd myzset 3 x 4 y 5 z
        r zrem myzset x
        assert_equal "pmessage * __keyspace@${db}__:myzset zadd" [$rd1 read]
        assert_equal "pmessage * __keyspace@${db}__:myzset zadd" [$rd1 read]
        assert_equal "pmessage * __keyspace@${db}__:myzset zrem" [$rd1 read]
        $rd1 close
    }
    """
    r.run("config", "set", "notify-keyspace-events", "Kz")
    r.run("del", "myzset")
    rd1 = valkey_deferring_client()
    assert "1" == psubscribe(rd1, "*")
    r.run("zadd", "myzset", 1, "a", 2, "b")
    r.run("zrem", "myzset", "x")
    r.run("zadd", "myzset", 3, "x", 4, "y", 5, "z")
    r.run("zrem", "myzset", "x")
    # TODO: assert_equal "pmessage * __keyspace@${db}__:myzset zadd" $rd1 read
    # TODO: assert_equal "pmessage * __keyspace@${db}__:myzset zadd" $rd1 read
    # TODO: assert_equal "pmessage * __keyspace@${db}__:myzset zrem" $rd1 read
    rd1.run("close")


@pytest.mark.xfail(reason="not implemented")
def test_keyspace_notifications_hash_events_test(r: ValkeyTestClient) -> None:
    """
    test "Keyspace notifications: hash events test" {
        r config set notify-keyspace-events Kh
        r del myhash
        set rd1 [valkey_deferring_client]
        assert_equal {1} [psubscribe $rd1 *]
        r hmset myhash yes 1 no 0
        r hincrby myhash yes 10
        assert_equal "pmessage * __keyspace@${db}__:myhash hset" [$rd1 read]
        assert_equal "pmessage * __keyspace@${db}__:myhash hincrby" [$rd1 read]
        $rd1 close
    }
    """
    r.run("config", "set", "notify-keyspace-events", "Kh")
    r.run("del", "myhash")
    rd1 = valkey_deferring_client()
    assert "1" == psubscribe(rd1, "*")
    r.run("hmset", "myhash", "yes", 1, "no", 0)
    r.run("hincrby", "myhash", "yes", 10)
    # TODO: assert_equal "pmessage * __keyspace@${db}__:myhash hset" $rd1 read
    # TODO: assert_equal "pmessage * __keyspace@${db}__:myhash hincrby" $rd1 read
    rd1.run("close")


@pytest.mark.xfail(reason="not implemented")
def test_keyspace_notifications_stream_events_test(r: ValkeyTestClient) -> None:
    """
    test "Keyspace notifications: stream events test" {
        r config set notify-keyspace-events Kt
        r del mystream
        set rd1 [valkey_deferring_client]
        assert_equal {1} [psubscribe $rd1 *]
        r xgroup create mystream mygroup $ mkstream
        r xgroup createconsumer mystream mygroup Bob
        set id [r xadd mystream 1 field1 A]
        r xreadgroup group mygroup Alice STREAMS mystream >
        r xclaim mystream mygroup Mike 0 $id force
        # Not notify because of "Lee" not exists.
        r xgroup delconsumer mystream mygroup Lee
        # Not notify because of "Bob" exists.
        r xautoclaim mystream mygroup Bob 0 $id
        r xgroup delconsumer mystream mygroup Bob
        assert_equal "pmessage * __keyspace@${db}__:mystream xgroup-create" [$rd1 read]
        assert_equal "pmessage * __keyspace@${db}__:mystream xgroup-createconsumer" [$rd1 read]
        assert_equal "pmessage * __keyspace@${db}__:mystream xadd" [$rd1 read]
        assert_equal "pmessage * __keyspace@${db}__:mystream xgroup-createconsumer" [$rd1 read]
        assert_equal "pmessage * __keyspace@${db}__:mystream xgroup-createconsumer" [$rd1 read]
        assert_equal "pmessage * __keyspace@${db}__:mystream xgroup-delconsumer" [$rd1 read]
        $rd1 close
    }
    """
    r.run("config", "set", "notify-keyspace-events", "Kt")
    r.run("del", "mystream")
    rd1 = valkey_deferring_client()
    assert "1" == psubscribe(rd1, "*")
    # TODO: r xgroup create mystream mygroup  mkstream
    r.run("xgroup", "createconsumer", "mystream", "mygroup", "Bob")
    id = r.run("xadd", "mystream", 1, "field1", "A")
    r.run("xreadgroup", "group", "mygroup", "Alice", "STREAMS", "mystream", ">")
    r.run("xclaim", "mystream", "mygroup", "Mike", 0, id, "force")
    r.run("xgroup", "delconsumer", "mystream", "mygroup", "Lee")
    r.run("xautoclaim", "mystream", "mygroup", "Bob", 0, id)
    r.run("xgroup", "delconsumer", "mystream", "mygroup", "Bob")
    # TODO: assert_equal "pmessage * __keyspace@${db}__:mystream xgroup-create" $rd1 read
    # TODO: assert_equal "pmessage * __keyspace@${db}__:mystream xgroup-createconsumer" $rd1 read
    # TODO: assert_equal "pmessage * __keyspace@${db}__:mystream xadd" $rd1 read
    # TODO: assert_equal "pmessage * __keyspace@${db}__:mystream xgroup-createconsumer" $rd1 read
    # TODO: assert_equal "pmessage * __keyspace@${db}__:mystream xgroup-createconsumer" $rd1 read
    # TODO: assert_equal "pmessage * __keyspace@${db}__:mystream xgroup-delconsumer" $rd1 read
    rd1.run("close")


@pytest.mark.xfail(reason="not implemented")
def test_keyspace_notifications_expired_events_triggered_expire(r: ValkeyTestClient) -> None:
    """
    test "Keyspace notifications: expired events (triggered expire)" {
        r config set notify-keyspace-events Ex
        r del foo
        set rd1 [valkey_deferring_client]
        assert_equal {1} [psubscribe $rd1 *]
        r psetex foo 100 1
        wait_for_condition 50 100 {
            [r exists foo] == 0
        } else {
            fail "Key does not expire?!"
        }
        assert_equal "pmessage * __keyevent@${db}__:expired foo" [$rd1 read]
        $rd1 close
    }
    """
    r.run("config", "set", "notify-keyspace-events", "Ex")
    r.run("del", "foo")
    rd1 = valkey_deferring_client()
    assert "1" == psubscribe(rd1, "*")
    r.run("psetex", "foo", 100, 1)
    wait_for_condition(
        50,
        100,
        "            [r exists foo] == 0\n        ",
        "else",
        '            fail "Key does not expire?!"\n        ',
    )
    # TODO: assert_equal "pmessage * __keyevent@${db}__:expired foo" $rd1 read
    rd1.run("close")


@pytest.mark.xfail(reason="not implemented")
def test_keyspace_notifications_expired_events_background_expire(r: ValkeyTestClient) -> None:
    """
    test "Keyspace notifications: expired events (background expire)" {
        r config set notify-keyspace-events Ex
        r del foo
        set rd1 [valkey_deferring_client]
        assert_equal {1} [psubscribe $rd1 *]
        r psetex foo 100 1
        assert_equal "pmessage * __keyevent@${db}__:expired foo" [$rd1 read]
        $rd1 close
    }
    """
    r.run("config", "set", "notify-keyspace-events", "Ex")
    r.run("del", "foo")
    rd1 = valkey_deferring_client()
    assert "1" == psubscribe(rd1, "*")
    r.run("psetex", "foo", 100, 1)
    # TODO: assert_equal "pmessage * __keyevent@${db}__:expired foo" $rd1 read
    rd1.run("close")


@pytest.mark.xfail(reason="not implemented")
def test_keyspace_notification_expired_event_expiration_time_is_already_expired(r: ValkeyTestClient) -> None:
    """
    test "Keyspace notification: expired event (Expiration time is already expired)" {
        r config set notify-keyspace-events Ex
        r del foo
        set rd1 [valkey_deferring_client]
        assert_equal {1} [psubscribe $rd1 *]
        r set foo 1
        r expire foo -1
        assert_equal "pmessage * __keyevent@${db}__:expired foo" [$rd1 read]
        $rd1 close
    }
    """
    r.run("config", "set", "notify-keyspace-events", "Ex")
    r.run("del", "foo")
    rd1 = valkey_deferring_client()
    assert "1" == psubscribe(rd1, "*")
    r.run("set", "foo", 1)
    r.run("expire", "foo", -1)
    # TODO: assert_equal "pmessage * __keyevent@${db}__:expired foo" $rd1 read
    rd1.run("close")


@pytest.mark.xfail(reason="not implemented")
def test_keyspace_notifications_evicted_events(r: ValkeyTestClient) -> None:
    """
    test "Keyspace notifications: evicted events" {
        r config set notify-keyspace-events Ee
        r config set maxmemory-policy allkeys-lru
        r flushdb
        set rd1 [valkey_deferring_client]
        assert_equal {1} [psubscribe $rd1 *]
        r set foo bar
        r config set maxmemory 1
        assert_equal "pmessage * __keyevent@${db}__:evicted foo" [$rd1 read]
        r config set maxmemory 0
        $rd1 close
        r config set maxmemory-policy noeviction
    } {OK} {needs:config-maxmemory}
    """
    r.run("config", "set", "notify-keyspace-events", "Ee")
    r.run("config", "set", "maxmemory-policy", "allkeys-lru")
    r.run("flushdb")
    rd1 = valkey_deferring_client()
    assert "1" == psubscribe(rd1, "*")
    r.run("set", "foo", "bar")
    r.run("config", "set", "maxmemory", 1)
    # TODO: assert_equal "pmessage * __keyevent@${db}__:evicted foo" $rd1 read
    r.run("config", "set", "maxmemory", 0)
    rd1.run("close")
    assert r.run("config", "set", "maxmemory-policy", "noeviction") == "OK"


def test_keyspace_notifications_test_config_get_or_set_of_event_flags(r: ValkeyTestClient) -> None:
    """
    test "Keyspace notifications: test CONFIG GET/SET of event flags" {
        r config set notify-keyspace-events gKE
        assert_equal {gKE} [lindex [r config get notify-keyspace-events] 1]
        r config set notify-keyspace-events {$lshzxeKE}
        assert_equal {$lshzxeKE} [lindex [r config get notify-keyspace-events] 1]
        r config set notify-keyspace-events KA
        assert_equal {AK} [lindex [r config get notify-keyspace-events] 1]
        r config set notify-keyspace-events EA
        assert_equal {AE} [lindex [r config get notify-keyspace-events] 1]
    }
    """
    r.run("config", "set", "notify-keyspace-events", "gKE")
    assert "gKE" == r.run("config", "get", "notify-keyspace-events")[1]
    r.run("config", "set", "notify-keyspace-events", "$lshzxeKE")
    assert "$lshzxeKE" == r.run("config", "get", "notify-keyspace-events")[1]
    r.run("config", "set", "notify-keyspace-events", "KA")
    assert "AK" == r.run("config", "get", "notify-keyspace-events")[1]
    r.run("config", "set", "notify-keyspace-events", "EA")
    assert "AE" == r.run("config", "get", "notify-keyspace-events")[1]


@pytest.mark.xfail(reason="not implemented")
def test_keyspace_notifications_new_key_test(r: ValkeyTestClient) -> None:
    """
    test "Keyspace notifications: new key test" {
        r config set notify-keyspace-events En
        set rd1 [valkey_deferring_client]
        assert_equal {1} [psubscribe $rd1 *]
        r set foo bar
        # second set of foo should not cause a 'new' event
        r set foo baz
        r set bar bar
        assert_equal "pmessage * __keyevent@${db}__:new foo" [$rd1 read]
        assert_equal "pmessage * __keyevent@${db}__:new bar" [$rd1 read]
        $rd1 close
    }
    """
    r.run("config", "set", "notify-keyspace-events", "En")
    rd1 = valkey_deferring_client()
    assert "1" == psubscribe(rd1, "*")
    r.run("set", "foo", "bar")
    r.run("set", "foo", "baz")
    r.run("set", "bar", "bar")
    # TODO: assert_equal "pmessage * __keyevent@${db}__:new foo" $rd1 read
    # TODO: assert_equal "pmessage * __keyevent@${db}__:new bar" $rd1 read
    rd1.run("close")


def test_publish_to_self_inside_multi(r: ValkeyTestClient) -> None:
    """
    test "publish to self inside multi" {
        r hello 3
        r subscribe foo
        r multi
        r ping abc
        r publish foo bar
        r publish foo vaz
        r ping def
        assert_equal [r exec] {abc 1 1 def}
        assert_equal [r read] {message foo bar}
        assert_equal [r read] {message foo vaz}
    } {} {resp3}
    """
    r.run("hello", 3)
    r.run("subscribe", "foo")
    r.run("multi")
    r.run("ping", "abc")
    r.run("publish", "foo", "bar")
    r.run("publish", "foo", "vaz")
    r.run("ping", "def")
    assert r.run("exec") == "abc 1 1 def"
    assert r.run("read") == "message foo bar"
    assert r.run("read") == "message foo vaz"


def test_publish_to_self_inside_script(r: ValkeyTestClient) -> None:
    """
    test "publish to self inside script" {
        r hello 3
        r subscribe foo
        set res [r eval {
                redis.call("ping","abc")
                redis.call("publish","foo","bar")
                redis.call("publish","foo","vaz")
                redis.call("ping","def")
                return "bla"} 0]
        assert_equal $res {bla}
        assert_equal [r read] {message foo bar}
        assert_equal [r read] {message foo vaz}
    } {} {resp3}
    """
    r.run("hello", 3)
    r.run("subscribe", "foo")
    res = r.run(
        "eval",
        '                redis.call("ping","abc")                redis.call("publish","foo","bar")                redis.call("publish","foo","vaz")                redis.call("ping","def")                return "bla"',
        0,
    )
    assert res == "bla"
    assert r.run("read") == "message foo bar"
    assert r.run("read") == "message foo vaz"


def test_unsubscribe_inside_multi_and_publish_to_self(r: ValkeyTestClient) -> None:
    """
    test "unsubscribe inside multi, and publish to self" {
        r hello 3

        # Note: SUBSCRIBE and UNSUBSCRIBE with multiple channels in the same command,
        # breaks the multi response, see Redis OSS issue: https://github.com/redis/redis/issues/12207
        # this is just a temporary sanity test to detect unintended breakage.

        # subscribe for 3 channels actually emits 3 "responses"
        assert_equal "subscribe foo 1" [r subscribe foo bar baz]
        assert_equal "subscribe bar 2" [r read]
        assert_equal "subscribe baz 3" [r read]

        r multi
        r ping abc
        r unsubscribe bar
        r unsubscribe baz
        r ping def
        assert_equal [r exec] {abc {unsubscribe bar 2} {unsubscribe baz 1} def}

        # published message comes after the publish command's response.
        assert_equal [r publish foo vaz] {1}
        assert_equal [r read] {message foo vaz}
    } {} {resp3}
    """
    r.run("hello", 3)
    assert "subscribe foo 1" == r.run("subscribe", "foo", "bar", "baz")
    assert "subscribe bar 2" == r.run("read")
    assert "subscribe baz 3" == r.run("read")
    r.run("multi")
    r.run("ping", "abc")
    r.run("unsubscribe", "bar")
    r.run("unsubscribe", "baz")
    r.run("ping", "def")
    assert r.run("exec") == "abc {unsubscribe bar 2} {unsubscribe baz 1} def"
    assert r.run("publish", "foo", "vaz") == "1"
    assert r.run("read") == "message foo vaz"


# --- stubs for unimplemented TCL helpers ---


def if_(*args):
    raise NotImplementedError("if_")


def psubscribe(*args):
    raise NotImplementedError("psubscribe")


def punsubscribe(*args):
    raise NotImplementedError("punsubscribe")


def subscribe(*args):
    raise NotImplementedError("subscribe")


def unsubscribe(*args):
    raise NotImplementedError("unsubscribe")


def valkey_deferring_client(*args):
    raise NotImplementedError("valkey_deferring_client")


def wait_for_condition(*args):
    raise NotImplementedError("wait_for_condition")
