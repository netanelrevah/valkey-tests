import pytest

from tests.valkey_test_client import ValkeyTestClient

"""
set testmodule file normalize tests/modules/publish.so
"""

pytestmark = [pytest.mark.modules]


"""
r module load testmodule
"""


@pytest.mark.xfail(reason="not implemented")
def test_publish_and_spublish_via_a_module(r: ValkeyTestClient) -> None:
    """
    test {PUBLISH and SPUBLISH via a module} {
        set rd1 [valkey_deferring_client]
        set rd2 [valkey_deferring_client]

        assert_equal {1} [ssubscribe $rd1 {chan1}]
        assert_equal {1} [subscribe $rd2 {chan1}]
        assert_equal 1 [r publish.shard chan1 hello]
        assert_equal 1 [r publish.classic chan1 world]
        assert_equal {smessage chan1 hello} [$rd1 read]
        assert_equal {message chan1 world} [$rd2 read]
        $rd1 close
        $rd2 close
    }
    """
    # TODO: set rd1 valkey_deferring_client
    # TODO: set rd2 valkey_deferring_client
    # TODO: assert_equal {1} ssubscribe $rd1 {chan1}
    # TODO: assert_equal {1} subscribe $rd2 {chan1}
    assert 1 == r.run("publish.shard", "chan1", "hello")
    assert 1 == r.run("publish.classic", "chan1", "world")
    # TODO: assert_equal {smessage chan1 hello} $rd1 read
    # TODO: assert_equal {message chan1 world} $rd2 read
    # TODO: $rd1 close
    # TODO: $rd2 close


@pytest.mark.xfail(reason="not implemented")
def test_module_publish_to_self_with_multi_message(r: ValkeyTestClient) -> None:
    """
    test {module publish to self with multi message} {
        r hello 3
        r subscribe foo

        # published message comes after the response of the command that issued it.
        assert_equal [r publish.classic_multi foo bar vaz] {1 1}
        assert_equal [r read] {message foo bar}
        assert_equal [r read] {message foo vaz}

        r unsubscribe foo
        r hello 2
        set _ ""
    } {} {resp3}
    """
    r.run("hello", 3)
    r.run("subscribe", "foo")
    assert r.run("publish.classic_multi", "foo", "bar", "vaz") == "1 1"
    assert r.run("read") == "message foo bar"
    assert r.run("read") == "message foo vaz"
    r.run("unsubscribe", "foo")
    r.run("hello", 2)
    # TODO: set _ ""
    assert False
