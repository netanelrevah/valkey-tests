# ruff: noqa: PLR2004, F841, RUF043, ANN002, ANN201

import pytest

from tests.valkey_test_client import ValkeyTestClient

pytestmark = [pytest.mark.protocol_network]


def test_handle_an_empty_query(r: ValkeyTestClient) -> None:
    """
    test "Handle an empty query" {
        reconnect
        r write "\r\n"
        r flush
        assert_equal "PONG" [r ping]
    }
    """
    reconnect()
    r.run("write", "\r\n")
    r.run("flush")
    assert "PONG" == r.run("ping")


def test_handle_an_empty_query_in_pipeline(r: ValkeyTestClient) -> None:
    """
    test "Handle an empty query in pipeline" {
        reconnect
        r write "\r\n*1\r\n\$4\r\nping\r\n"
        r flush
        assert_equal PONG [r read]
    }
    """
    reconnect()
    r.run("write", "\r\n*1\r\n$4\r\nping\r\n")
    r.run("flush")
    assert "PONG" == r.run("read")


def test_negative_multibulk_length(r: ValkeyTestClient) -> None:
    """
    test "Negative multibulk length" {
        reconnect
        r write "*-10\r\n"
        r flush
        assert_equal PONG [r ping]
    }
    """
    reconnect()
    r.run("write", "*-10\r\n")
    r.run("flush")
    assert "PONG" == r.run("ping")


def test_negative_multibulk_length_in_pipeline(r: ValkeyTestClient) -> None:
    """
    test "Negative multibulk length in pipeline" {
        reconnect
        r write "*-10\r\n*1\r\n\$4\r\nping\r\n"
        r flush
        assert_equal PONG [r read]
    }
    """
    reconnect()
    r.run("write", "*-10\r\n*1\r\n$4\r\nping\r\n")
    r.run("flush")
    assert "PONG" == r.run("read")


def test_out_of_range_multibulk_length(r: ValkeyTestClient) -> None:
    """
    test "Out of range multibulk length" {
        reconnect
        r write "*3000000000\r\n"
        r flush
        assert_error "*invalid multibulk length*" {r read}
    }
    """
    reconnect()
    r.run("write", "*3000000000\r\n")
    r.run("flush")
    with pytest.raises(Exception, match=".*invalid\\ multibulk\\ length.*"):
        r.run("read")


def test_wrong_multibulk_payload_header(r: ValkeyTestClient) -> None:
    """
    test "Wrong multibulk payload header" {
        reconnect
        r write "*3\r\n\$3\r\nSET\r\n\$1\r\nx\r\nfooz\r\n"
        r flush
        assert_error "*expected '$', got 'f'*" {r read}
    }
    """
    reconnect()
    r.run("write", "*3\r\n$3\r\nSET\r\n$1\r\nx\r\nfooz\r\n")
    r.run("flush")
    with pytest.raises(Exception, match=".*expected\\ '\\$',\\ got\\ 'f'.*"):
        r.run("read")


def test_negative_multibulk_payload_length(r: ValkeyTestClient) -> None:
    """
    test "Negative multibulk payload length" {
        reconnect
        r write "*3\r\n\$3\r\nSET\r\n\$1\r\nx\r\n\$-10\r\n"
        r flush
        assert_error "*invalid bulk length*" {r read}
    }
    """
    reconnect()
    r.run("write", "*3\r\n$3\r\nSET\r\n$1\r\nx\r\n$-10\r\n")
    r.run("flush")
    with pytest.raises(Exception, match=".*invalid\\ bulk\\ length.*"):
        r.run("read")


def test_out_of_range_multibulk_payload_length(r: ValkeyTestClient) -> None:
    """
    test "Out of range multibulk payload length" {
        reconnect
        r write "*3\r\n\$3\r\nSET\r\n\$1\r\nx\r\n\$2000000000\r\n"
        r flush
        assert_error "*invalid bulk length*" {r read}
    }
    """
    reconnect()
    r.run("write", "*3\r\n$3\r\nSET\r\n$1\r\nx\r\n$2000000000\r\n")
    r.run("flush")
    with pytest.raises(Exception, match=".*invalid\\ bulk\\ length.*"):
        r.run("read")


def test_non_number_multibulk_payload_length(r: ValkeyTestClient) -> None:
    """
    test "Non-number multibulk payload length" {
        reconnect
        r write "*3\r\n\$3\r\nSET\r\n\$1\r\nx\r\n\$blabla\r\n"
        r flush
        assert_error "*invalid bulk length*" {r read}
    }
    """
    reconnect()
    r.run("write", "*3\r\n$3\r\nSET\r\n$1\r\nx\r\n$blabla\r\n")
    r.run("flush")
    with pytest.raises(Exception, match=".*invalid\\ bulk\\ length.*"):
        r.run("read")


def test_multi_bulk_request_not_followed_by_bulk_arguments(r: ValkeyTestClient) -> None:
    """
    test "Multi bulk request not followed by bulk arguments" {
        reconnect
        r write "*1\r\nfoo\r\n"
        r flush
        assert_error "*expected '$', got 'f'*" {r read}
    }
    """
    reconnect()
    r.run("write", "*1\r\nfoo\r\n")
    r.run("flush")
    with pytest.raises(Exception, match=".*expected\\ '\\$',\\ got\\ 'f'.*"):
        r.run("read")


def test_generic_wrong_number_of_args(r: ValkeyTestClient) -> None:
    """
    test "Generic wrong number of args" {
        reconnect
        assert_error "*wrong*arguments*ping*" {r ping x y z}
    }
    """
    reconnect()
    with pytest.raises(Exception, match=".*wrong.*arguments.*ping.*"):
        r.run("ping", "x", "y", "z")


def test_mixing_quoted_and_unquoted_strings(r: ValkeyTestClient) -> None:
    """
    test "Mixing quoted and unquoted strings" {
        reconnect
        r write "set \"\"\"tes\"t-'k'e\"y\" \"test\"'-'value\r\n"
        r write "get test'-'key\r\n"
        r flush
        assert_equal "OK" [r read]
        assert_equal "test-value" [r read]
    }
    """
    reconnect()
    r.run("write", 'set """tes"t-\'k\'e"y" "test"\'-\'value\r\n')
    r.run("write", "get test'-'key\r\n")
    r.run("flush")
    assert "OK" == r.run("read")
    assert "test-value" == r.run("read")


def test_unbalanced_single_quotes(r: ValkeyTestClient) -> None:
    """
    test "Unbalanced single quotes" {
        reconnect
        r write "set foo 'b'a'r\r\n"
        r write "ping\r\n"
        r flush
        assert_error "*unbalanced*" {r read}
    }
    """
    reconnect()
    r.run("write", "set foo 'b'a'r\r\n")
    r.run("write", "ping\r\n")
    r.run("flush")
    with pytest.raises(Exception, match=".*unbalanced.*"):
        r.run("read")


def test_unbalanced_double_quotes(r: ValkeyTestClient) -> None:
    """
    test "Unbalanced double quotes" {
        reconnect
        r write "set foo \"b\"a\"r\r\n"
        r write "ping\r\n"
        r flush
        assert_error "*unbalanced*" {r read}
    }
    """
    reconnect()
    r.run("write", 'set foo "b"a"r\r\n')
    r.run("write", "ping\r\n")
    r.run("flush")
    with pytest.raises(Exception, match=".*unbalanced.*"):
        r.run("read")


@pytest.mark.xfail(reason="not implemented")
def test_check_crlf_when_parsing_the_querybuf(r: ValkeyTestClient) -> None:
    """
    test "Check CRLF when parsing the querybuf" {
        # Command) SET key value
        # RESP) *3\r\n$3\r\nSET\r\n$3\r\nkey\r\n$5\r\nvalue\r\n
        # We need to strictly check these \r\n characters.
        set proto "*3\r\n\$3\r\nSET\r\n\$3\r\nkey\r\n\$5\r\nvalue\r\n"
        reconnect; r write $proto; r flush; assert_equal "OK" [r read]

        # Check if multibulklen `*3\r\n` is followed by `\r\n`
        set proto1 "*3x\n\$3\r\nSET\r\n\$3\r\nkey\r\n\$5\r\nvalue\r\n"
        set proto2 "*3\rx\$3\r\nSET\r\n\$3\r\nkey\r\n\$5\r\nvalue\r\n"
        set proto3 "*3xx\$3\r\nSET\r\n\$3\r\nkey\r\n\$5\r\nvalue\r\n"
        r write $proto1; r flush; assert_error "*invalid multibulk length*" {r read}; reconnect
        r write $proto2; r flush; assert_error "*invalid CRLF in request*" {r read}; reconnect
        r write $proto3; r flush; assert_error "*invalid multibulk length*" {r read}; reconnect

        # Check if bulklen `$3\r\n` is followed by `\r\n`
        set proto1 "*3\r\n\$3x\nSET\r\n\$3\r\nkey\r\n\$5\r\nvalue\r\n"
        set proto2 "*3\r\n\$3\rxSET\r\n\$3\r\nkey\r\n\$5\r\nvalue\r\n"
        set proto3 "*3\r\n\$3xxSET\r\n\$3\r\nkey\r\n\$5\r\nvalue\r\n"
        r write $proto1; r flush; assert_error "*invalid bulk length*" {r read}; reconnect
        r write $proto2; r flush; assert_error "*invalid CRLF in request*" {r read}; reconnect
        r write $proto3; r flush; assert_error "*invalid bulk length*" {r read}; reconnect

        # Check if `SET\r\n` is followed by `\r\n`
        set proto1 "*3\r\n\$3\r\nSET\rx\$3\r\nkey\r\n\$5\r\nvalue\r\n"
        set proto2 "*3\r\n\$3\r\nSETx\n\$3\r\nkey\r\n\$5\r\nvalue\r\n"
        set proto3 "*3\r\n\$3\r\nSETxx\$3\r\nkey\r\n\$5\r\nvalue\r\n"
        r write $proto1; r flush; assert_error "*invalid CRLF in request*" {r read}; reconnect
        r write $proto2; r flush; assert_error "*invalid CRLF in request*" {r read}; reconnect
        r write $proto3; r flush; assert_error "*invalid CRLF in request*" {r read}; reconnect

        # Check if `key\r\n` is followed by `\r\n`
        set proto1 "*3\r\n\$3\r\nSET\r\n\$3\r\nkeyx\n\$5\r\nvalue\r\n"
        set proto2 "*3\r\n\$3\r\nSET\r\n\$3\r\nkey\rx\$5\r\nvalue\r\n"
        set proto3 "*3\r\n\$3\r\nSET\r\n\$3\r\nkeyxx\$5\r\nvalue\r\n"
        r write $proto1; r flush; assert_error "*invalid CRLF in request*" {r read}; reconnect
        r write $proto2; r flush; assert_error "*invalid CRLF in request*" {r read}; reconnect
        r write $proto3; r flush; assert_error "*invalid CRLF in request*" {r read}; reconnect

        # Check if bulklen `$5\r\n` is followed by `\r\n`
        set proto1 "*3\r\n\$3\r\nSET\r\n\$3\r\nkey\r\n\$5x\nvalue\r\n"
        set proto2 "*3\r\n\$3\r\nSET\r\n\$3\r\nkey\r\n\$5\rxvalue\r\n"
        set proto3 "*3\r\n\$3\r\nSET\r\n\$3\r\nkey\r\n\$5xxvalue\r\n"
        r write $proto1; r flush; assert_error "*invalid bulk length*" {r read}; reconnect
        r write $proto2; r flush; assert_error "*invalid CRLF in request*" {r read}; reconnect
        r write $proto3; r flush; assert_error "*invalid bulk length*" {r read}; reconnect

        # Check if `value\r\n` is followed by `\r\n`
        set proto1 "*3\r\n\$3\r\nSET\r\n\$3\r\nkey\r\n\$5\r\nvaluex\n"
        set proto2 "*3\r\n\$3\r\nSET\r\n\$3\r\nkey\r\n\$5\r\nvalue\rx"
        set proto3 "*3\r\n\$3\r\nSET\r\n\$3\r\nkey\r\n\$5\r\nvaluexx"
        r write $proto1; r flush; assert_error "*invalid CRLF in request*" {r read}; reconnect
        r write $proto2; r flush; assert_error "*invalid CRLF in request*" {r read}; reconnect
        r write $proto3; r flush; assert_error "*invalid CRLF in request*" {r read}; reconnect
    }
    """
    proto = "*3\r\n$3\r\nSET\r\n$3\r\nkey\r\n$5\r\nvalue\r\n"
    # TODO: reconnect; r write proto
    r.run("flush")
    assert "OK" == r.run("read")
    proto1 = "*3x\n$3\r\nSET\r\n$3\r\nkey\r\n$5\r\nvalue\r\n"
    proto2 = "*3\rx$3\r\nSET\r\n$3\r\nkey\r\n$5\r\nvalue\r\n"
    proto3 = "*3xx$3\r\nSET\r\n$3\r\nkey\r\n$5\r\nvalue\r\n"
    r.run("write", proto1)
    r.run("flush")
    with pytest.raises(Exception, match=".*invalid\\ multibulk\\ length.*"):
        r.run("read")
    reconnect()
    r.run("write", proto2)
    r.run("flush")
    with pytest.raises(Exception, match=".*invalid\\ CRLF\\ in\\ request.*"):
        r.run("read")
    reconnect()
    r.run("write", proto3)
    r.run("flush")
    with pytest.raises(Exception, match=".*invalid\\ multibulk\\ length.*"):
        r.run("read")
    reconnect()
    proto1 = "*3\r\n$3x\nSET\r\n$3\r\nkey\r\n$5\r\nvalue\r\n"
    proto2 = "*3\r\n$3\rxSET\r\n$3\r\nkey\r\n$5\r\nvalue\r\n"
    proto3 = "*3\r\n$3xxSET\r\n$3\r\nkey\r\n$5\r\nvalue\r\n"
    r.run("write", proto1)
    r.run("flush")
    with pytest.raises(Exception, match=".*invalid\\ bulk\\ length.*"):
        r.run("read")
    reconnect()
    r.run("write", proto2)
    r.run("flush")
    with pytest.raises(Exception, match=".*invalid\\ CRLF\\ in\\ request.*"):
        r.run("read")
    reconnect()
    r.run("write", proto3)
    r.run("flush")
    with pytest.raises(Exception, match=".*invalid\\ bulk\\ length.*"):
        r.run("read")
    reconnect()
    proto1 = "*3\r\n$3\r\nSET\rx$3\r\nkey\r\n$5\r\nvalue\r\n"
    proto2 = "*3\r\n$3\r\nSETx\n$3\r\nkey\r\n$5\r\nvalue\r\n"
    proto3 = "*3\r\n$3\r\nSETxx$3\r\nkey\r\n$5\r\nvalue\r\n"
    r.run("write", proto1)
    r.run("flush")
    with pytest.raises(Exception, match=".*invalid\\ CRLF\\ in\\ request.*"):
        r.run("read")
    reconnect()
    r.run("write", proto2)
    r.run("flush")
    with pytest.raises(Exception, match=".*invalid\\ CRLF\\ in\\ request.*"):
        r.run("read")
    reconnect()
    r.run("write", proto3)
    r.run("flush")
    with pytest.raises(Exception, match=".*invalid\\ CRLF\\ in\\ request.*"):
        r.run("read")
    reconnect()
    proto1 = "*3\r\n$3\r\nSET\r\n$3\r\nkeyx\n$5\r\nvalue\r\n"
    proto2 = "*3\r\n$3\r\nSET\r\n$3\r\nkey\rx$5\r\nvalue\r\n"
    proto3 = "*3\r\n$3\r\nSET\r\n$3\r\nkeyxx$5\r\nvalue\r\n"
    r.run("write", proto1)
    r.run("flush")
    with pytest.raises(Exception, match=".*invalid\\ CRLF\\ in\\ request.*"):
        r.run("read")
    reconnect()
    r.run("write", proto2)
    r.run("flush")
    with pytest.raises(Exception, match=".*invalid\\ CRLF\\ in\\ request.*"):
        r.run("read")
    reconnect()
    r.run("write", proto3)
    r.run("flush")
    with pytest.raises(Exception, match=".*invalid\\ CRLF\\ in\\ request.*"):
        r.run("read")
    reconnect()
    proto1 = "*3\r\n$3\r\nSET\r\n$3\r\nkey\r\n$5x\nvalue\r\n"
    proto2 = "*3\r\n$3\r\nSET\r\n$3\r\nkey\r\n$5\rxvalue\r\n"
    proto3 = "*3\r\n$3\r\nSET\r\n$3\r\nkey\r\n$5xxvalue\r\n"
    r.run("write", proto1)
    r.run("flush")
    with pytest.raises(Exception, match=".*invalid\\ bulk\\ length.*"):
        r.run("read")
    reconnect()
    r.run("write", proto2)
    r.run("flush")
    with pytest.raises(Exception, match=".*invalid\\ CRLF\\ in\\ request.*"):
        r.run("read")
    reconnect()
    r.run("write", proto3)
    r.run("flush")
    with pytest.raises(Exception, match=".*invalid\\ bulk\\ length.*"):
        r.run("read")
    reconnect()
    proto1 = "*3\r\n$3\r\nSET\r\n$3\r\nkey\r\n$5\r\nvaluex\n"
    proto2 = "*3\r\n$3\r\nSET\r\n$3\r\nkey\r\n$5\r\nvalue\rx"
    proto3 = "*3\r\n$3\r\nSET\r\n$3\r\nkey\r\n$5\r\nvaluexx"
    r.run("write", proto1)
    r.run("flush")
    with pytest.raises(Exception, match=".*invalid\\ CRLF\\ in\\ request.*"):
        r.run("read")
    reconnect()
    r.run("write", proto2)
    r.run("flush")
    with pytest.raises(Exception, match=".*invalid\\ CRLF\\ in\\ request.*"):
        r.run("read")
    reconnect()
    r.run("write", proto3)
    r.run("flush")
    with pytest.raises(Exception, match=".*invalid\\ CRLF\\ in\\ request.*"):
        r.run("read")
    reconnect()


"""
set c 0
"""


"""
foreach seq list "\x00" "*\x00" "$\x00" "*1\r\n$\x00" {
    incr c
    test "Protocol desync regression test #$c" {
        if {$::tls} {
            set s [::tls::socket [srv 0 host] [srv 0 port]]
        } else {
            set s [socket [srv 0 host] [srv 0 port]]
        }
        fconfigure $s -translation binary
        puts -nonewline $s $seq
        # PROTO_INLINE_MAX_SIZE is hardcoded in Valkey code to 64K. doing the same here 
        # since we would like to validate it is enforced. 
        set PROTO_INLINE_MAX_SIZE [expr 1024 * 64]
        set payload [string repeat A 1024]
        set payload_size 0
        while {$payload_size <= $PROTO_INLINE_MAX_SIZE} {
            if {[catch {
                incr payload_size [string length $payload]
                puts -nonewline $s $payload
                flush $s
            }]} {
                assert_morethan $payload_size $PROTO_INLINE_MAX_SIZE
                break
            }
        }
        assert_match {*Protocol error*} [gets $s]]
        close $s
    }
}
"""


"""
unset c
"""


"""
reconnect
"""


"""
r ping
"""


"""
r readraw 1
"""


"""
set nullres {*-1}
"""


"""
if {$::force_resp3} {
    set nullres {_}
}
"""


def test_raw_protocol_response(r: ValkeyTestClient) -> None:
    """
    test "raw protocol response" {
        r srandmember nonexisting_key
    } "$nullres"
    """
    r.run("srandmember", "nonexisting_key")


def test_raw_protocol_response_deferred(r: ValkeyTestClient) -> None:
    """
    test "raw protocol response - deferred" {
        r srandmember nonexisting_key
        r read
    } "$nullres"
    """
    r.run("deferred", 1)
    r.run("srandmember", "nonexisting_key")
    r.run("read")


def test_raw_protocol_response_multiline(r: ValkeyTestClient) -> None:
    """
    test "raw protocol response - multiline" {
        r sadd ss a
        assert_equal [r read] {:1}
        r srandmember ss 100
        assert_equal [r read] {*1}
        assert_equal [r read] {$1}
        assert_equal [r read] {a}
    }
    """
    r.run("deferred", 1)
    r.run("sadd", "ss", "a")
    assert r.run("read") == ":1"
    r.run("srandmember", "ss", 100)
    assert r.run("read") == "*1"
    assert r.run("read") == "$1"
    assert r.run("read") == "a"


def test_resp3_attributes(r: ValkeyTestClient) -> None:
    """
    test {RESP3 attributes} {
        r hello 3
        assert_equal {Some real reply following the attribute} [r debug protocol attrib]
        assert_equal {key-popularity {key:123 90}} [r attributes]

        # make sure attributes are not kept from previous command
        r ping
        assert_error {*attributes* no such element in array} {r attributes}

        # restore state
        r hello 2
        set _ ""
    } {} {needs:debug resp3}
    """
    r.run("readraw", 0)
    r.run("deferred", 0)
    assert r.run("ping") == "PONG"
    r.run("hello", 3)
    assert "Some real reply following the attribute" == r.run("debug", "protocol", "attrib")
    assert "key-popularity {key:123 90}" == r.run("attributes")
    r.run("ping")
    with pytest.raises(Exception, match=".*attributes.*\\ no\\ such\\ element\\ in\\ array"):
        r.run("attributes")
    r.run("hello", 2)
    _ = ""


def test_resp3_attributes_readraw(r: ValkeyTestClient) -> None:
    """
    test {RESP3 attributes readraw} {
        r hello 3
        r readraw 1
        r deferred 1

        r debug protocol attrib
        assert_equal [r read] {|1}
        assert_equal [r read] {$14}
        assert_equal [r read] {key-popularity}
        assert_equal [r read] {*2}
        assert_equal [r read] {$7}
        assert_equal [r read] {key:123}
        assert_equal [r read] {:90}
        assert_equal [r read] {$39}
        assert_equal [r read] {Some real reply following the attribute}

        # restore state
        r readraw 0
        r deferred 0
        r hello 2
        set _ {}
    } {} {needs:debug resp3}
    """
    r.run("readraw", 0)
    r.run("deferred", 0)
    assert r.run("ping") == "PONG"
    r.run("hello", 3)
    r.run("readraw", 1)
    r.run("deferred", 1)
    r.run("debug", "protocol", "attrib")
    assert r.run("read") == "|1"
    assert r.run("read") == "$14"
    assert r.run("read") == "key-popularity"
    assert r.run("read") == "*2"
    assert r.run("read") == "$7"
    assert r.run("read") == "key:123"
    assert r.run("read") == ":90"
    assert r.run("read") == "$39"
    assert r.run("read") == "Some real reply following the attribute"
    r.run("readraw", 0)
    r.run("deferred", 0)
    r.run("hello", 2)
    _ = []


def test_resp3_attributes_on_resp2(r: ValkeyTestClient) -> None:
    """
    test {RESP3 attributes on RESP2} {
        r hello 2
        set res [r debug protocol attrib]
        set _ $res
    } {Some real reply following the attribute} {needs:debug}
    """
    r.run("readraw", 0)
    r.run("deferred", 0)
    assert r.run("ping") == "PONG"
    r.run("hello", 2)
    res = r.run("debug", "protocol", "attrib")
    assert res == "Some real reply following the attribute"


def test_test_big_number_parsing(r: ValkeyTestClient) -> None:
    """
    test "test big number parsing" {
        r hello 3
        r debug protocol bignum
    } {1234567999999999999999999999999999999} {needs:debug resp3}
    """
    r.run("readraw", 0)
    r.run("deferred", 0)
    assert r.run("ping") == "PONG"
    r.run("hello", 3)
    assert r.run("debug", "protocol", "bignum") == "1234567999999999999999999999999999999"


def test_test_bool_parsing(r: ValkeyTestClient) -> None:
    """
    test "test bool parsing" {
        r hello 3
        assert_equal [r debug protocol true] 1
        assert_equal [r debug protocol false] 0
        r hello 2
        assert_equal [r debug protocol true] 1
        assert_equal [r debug protocol false] 0
        set _ {}
    } {} {needs:debug resp3}
    """
    r.run("readraw", 0)
    r.run("deferred", 0)
    assert r.run("ping") == "PONG"
    r.run("hello", 3)
    assert r.run("debug", "protocol", "true") == 1
    assert r.run("debug", "protocol", "false") == 0
    r.run("hello", 2)
    assert r.run("debug", "protocol", "true") == 1
    assert r.run("debug", "protocol", "false") == 0
    _ = []


def test_test_verbatim_str_parsing(r: ValkeyTestClient) -> None:
    """
    test "test verbatim str parsing" {
        r hello 3
        r debug protocol verbatim
    } "This is a verbatim\nstring" {needs:debug resp3}
    """
    r.run("readraw", 0)
    r.run("deferred", 0)
    assert r.run("ping") == "PONG"
    r.run("hello", 3)
    r.run("debug", "protocol", "verbatim")


def test_test_large_number_of_args(r: ValkeyTestClient) -> None:
    """
    test "test large number of args" {
        r flushdb
        set args [split [string trim [string repeat "k v " 10000]]]
        lappend args "{k}2" v2
        r mset {*}$args
        assert_equal [r get "{k}2"] v2
    }
    """
    r.run("readraw", 0)
    r.run("deferred", 0)
    assert r.run("ping") == "PONG"
    r.run("flushdb")
    args = split(string("trim", string("repeat", "k v ", 10000)))
    args.append("{k}2")
    args.append("v2")
    r.run("mset", "*", args)
    assert r.run("get", "{k}2") == "v2"


def test_test_argument_rewriting_issue_9598(r: ValkeyTestClient) -> None:
    """
    test "test argument rewriting - issue 9598" {
        # INCRBYFLOAT uses argument rewriting for correct float value propagation.
        # We use it to make sure argument rewriting works properly. It's important
        # this test is run under valgrind to verify there are no memory leaks in
        # arg buffer handling.
        r flushdb

        # Test normal argument handling
        r set k 0
        assert_equal [r incrbyfloat k 1.0] 1

        # Test argument handing in multi-state buffers
        r multi
        r incrbyfloat k 1.0
        assert_equal [r exec] 2
    }
    """
    r.run("readraw", 0)
    r.run("deferred", 0)
    assert r.run("ping") == "PONG"
    r.run("flushdb")
    r.run("set", "k", 0)
    assert r.run("incrbyfloat", "k", 1.0) == 1
    r.run("multi")
    r.run("incrbyfloat", "k", 1.0)
    assert r.run("exec") == 2


pytestmark = [pytest.mark.protocol_hello_logreqres_skip]


def test_hello_without_protover(r: ValkeyTestClient) -> None:
    """
    test {HELLO without protover} {
        set reply [r HELLO 3]
        assert_equal [dict get $reply proto] 3

        set reply [r HELLO]
        assert_equal [dict get $reply proto] 3

        set reply [r HELLO 2]
        assert_equal [dict get $reply proto] 2

        set reply [r HELLO]
        assert_equal [dict get $reply proto] 2
    }
    """
    reply = r.run("HELLO", 3)
    assert reply["proto"] == 3
    reply = r.run("HELLO")
    assert reply["proto"] == 3
    reply = r.run("HELLO", 2)
    assert reply["proto"] == 2
    reply = r.run("HELLO")
    assert reply["proto"] == 2


def test_hello_and_availability_zone(r: ValkeyTestClient) -> None:
    """
    test {HELLO and availability-zone} {
        r CONFIG SET availability-zone myzone

        set reply [r HELLO 3]
        assert_equal [dict get $reply availability_zone] myzone

        set reply [r HELLO 2]
        assert_equal [dict get $reply availability_zone] myzone

        r CONFIG SET availability-zone ""

        set reply [r HELLO 3]
        assert_equal [dict exists $reply availability_zone] 0

        set reply [r HELLO 2]
        assert_equal [dict exists $reply availability_zone] 0
    }
    """
    r.run("CONFIG", "SET", "availability-zone", "myzone")
    reply = r.run("HELLO", 3)
    assert reply["availability_zone"] == "myzone"
    reply = r.run("HELLO", 2)
    assert reply["availability_zone"] == "myzone"
    r.run("CONFIG", "SET", "availability-zone", "")
    reply = r.run("HELLO", 3)
    assert dict_("exists", reply, "availability_zone") == 0
    reply = r.run("HELLO", 2)
    assert dict_("exists", reply, "availability_zone") == 0


pytestmark = [pytest.mark.regression]


def test_regression_for_a_crash_with_blocking_ops_and_pipelining(r: ValkeyTestClient) -> None:
    """
    test "Regression for a crash with blocking ops and pipelining" {
        set rd [valkey_deferring_client]
        set fd [r channel]
        set proto "*3\r\n\$5\r\nBLPOP\r\n\$6\r\nnolist\r\n\$1\r\n0\r\n"
        puts -nonewline $fd $proto$proto
        flush $fd
        set res {}

        $rd rpush nolist a
        $rd read
        $rd rpush nolist a
        $rd read
        $rd close
    }
    """
    rd = ValkeyTestClient.create_from(r)
    fd = r.run("channel")
    proto = "*3\r\n$5\r\nBLPOP\r\n$6\r\nnolist\r\n$1\r\n0\r\n"
    flush(fd)
    res = []
    rd.run("rpush", "nolist", "a")
    rd.run("read")
    rd.run("rpush", "nolist", "a")
    rd.run("read")
    rd.run("close")


# --- stubs for unimplemented TCL helpers ---


def dict_(*args):
    raise NotImplementedError("dict_")


def flush(*args):
    raise NotImplementedError("flush")


def reconnect(*args):
    raise NotImplementedError("reconnect")


def split(*args):
    raise NotImplementedError("split")


def string(*args):
    raise NotImplementedError("string")
