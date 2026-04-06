# ruff: noqa: PLR2004

import pytest

from tests.valkey_test_client import ValkeyTestClient

pytestmark = [pytest.mark.limits_network_external_skip]


"""
if {$::tls} {
    set expected_code "*I/O error*"
} else {
    set expected_code "*ERR max*reached*"
}
"""


@pytest.mark.xfail(reason="not implemented")
def test_check_if_maxclients_works_refusing_connections(r: ValkeyTestClient) -> None:
    """
    test {Check if maxclients works refusing connections} {
        set c 0
        catch {
            while {$c < 50} {
                incr c
                set rd [valkey_deferring_client]
                $rd ping
                $rd read
                after 100
            }
        } e
        assert {$c > 8 && $c <= 10}
        set e
    } expected _code
    """
    c = 0
    # TODO: catch {
    #       while {$c < 50} {
    #           incr c
    #           set rd [valkey_deferring_client]
    #           $rd ping
    #           $rd read
    #           after 100
    #       }
    #   } e
    assert (c > 8) and (c <= 10)
    # TODO: set e
