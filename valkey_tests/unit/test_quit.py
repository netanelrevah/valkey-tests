# ruff: noqa: RUF043, ANN002, ANN201

import pytest

from tests.valkey_test_client import ValkeyTestClient

pytestmark = [pytest.mark.quit]


def test_quit_returns_ok(r: ValkeyTestClient) -> None:
    """
    test "QUIT returns OK" {
        reconnect
        assert_equal OK [r quit]
        assert_error * {r ping}
    }
    """
    reconnect()
    assert "OK" == r.run("quit")
    with pytest.raises(Exception, match=".*"):
        r.run("ping")


def test_pipelined_commands_after_quit_must_not_be_executed(r: ValkeyTestClient) -> None:
    """
    test "Pipelined commands after QUIT must not be executed" {
        reconnect
        r write [format_command quit]
        r write [format_command set foo bar]
        r flush
        assert_equal OK [r read]
        assert_error * {r read}

        reconnect
        assert_equal {} [r get foo]
    }
    """
    reconnect()
    r.run("write", format_command("quit"))
    r.run("write", format_command("set", "foo", "bar"))
    r.run("flush")
    assert "OK" == r.run("read")
    with pytest.raises(Exception, match=".*"):
        r.run("read")
    reconnect()
    assert "" == r.run("get", "foo")


def test_pipelined_commands_after_quit_that_exceed_read_buffer_size(r: ValkeyTestClient) -> None:
    """
    test "Pipelined commands after QUIT that exceed read buffer size" {
        reconnect
        r write [format_command quit]
        r write [format_command set foo [string repeat "x" 1024]]
        r flush
        assert_equal OK [r read]
        assert_error * {r read}

        reconnect
        assert_equal {} [r get foo]
    }
    """
    reconnect()
    r.run("write", format_command("quit"))
    r.run("write", format_command("set", "foo", string("repeat", "x", 1024)))
    r.run("flush")
    assert "OK" == r.run("read")
    with pytest.raises(Exception, match=".*"):
        r.run("read")
    reconnect()
    assert "" == r.run("get", "foo")


# --- stubs for unimplemented TCL helpers ---


def format_command(*args):
    raise NotImplementedError("format_command")


def reconnect(*args):
    raise NotImplementedError("reconnect")


def string(*args):
    raise NotImplementedError("string")
