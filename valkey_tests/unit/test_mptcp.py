import pytest

from tests.valkey_test_client import ValkeyTestClient

pytestmark = [pytest.mark.mptcp, pytest.mark.external_skip]


def test_mptcp_server_starts_with_mptcp_yes_and_responds_to_commands(r: ValkeyTestClient) -> None:
    """
    test "MPTCP - Server starts with mptcp yes and responds to commands" {
        assert_equal "PONG" [r ping]
        assert_equal {mptcp yes} [r config get mptcp]
        r set test_key "test_value"
        assert_equal "test_value" [r get test_key]
        r del test_key
        assert_equal 0 [r exists test_key]
    }
    """
    assert "PONG" == r.run("ping")
    assert "mptcp yes" == r.run("config", "get", "mptcp")
    r.run("set", "test_key", "test_value")
    assert "test_value" == r.run("get", "test_key")
    r.run("del", "test_key")
    assert 0 == r.run("exists", "test_key")
