# ruff: noqa: PLR2004, F841, RUF043

import pytest

from tests.valkey_test_client import ValkeyTestClient

"""
set testmodule file normalize tests/modules/stream.so
"""

pytestmark = [pytest.mark.modules]


"""
r module load testmodule
"""


@pytest.mark.xfail(reason="not implemented")
def test_module_stream_add_and_delete(r: ValkeyTestClient) -> None:
    """
    test {Module stream add and delete} {
        r del mystream
        # add to empty key
        set streamid1 [r stream.add mystream item 1 value a]
        # add to existing stream
        set streamid2 [r stream.add mystream item 2 value b]
        # check result
        assert { [string match "*-*" $streamid1] }
        set items [r XRANGE mystream - +]
        assert_equal $items \
            "{$streamid1 {item 1 value a}} {$streamid2 {item 2 value b}}"
        # delete one of them and try deleting non-existing ID
        assert_equal OK [r stream.delete mystream $streamid1]
        assert_error "ERR StreamDelete*" {r stream.delete mystream 123-456}
        assert_error "Invalid stream ID*" {r stream.delete mystream foo}
        assert_equal "{$streamid2 {item 2 value b}}" [r XRANGE mystream - +]
        # check error condition: wrong type
        r del mystream
        r set mystream mystring
        assert_error "ERR StreamAdd*" {r stream.add mystream item 1 value a}
        assert_error "ERR StreamDelete*" {r stream.delete mystream 123-456}
    }
    """
    r.run("del", "mystream")
    streamid1 = r.run("stream.add", "mystream", "item", 1, "value", "a")
    streamid2 = r.run("stream.add", "mystream", "item", 2, "value", "b")
    # TODO: assert { [string match "*-*" $streamid1] }
    items = r.run("XRANGE", "mystream", "-", "+")
    # TODO: assert_equal items "{$streamid1 {item 1 value a}} {$streamid2 {item 2 value b}}"
    assert "OK" == r.run("stream.delete", "mystream", streamid1)
    with pytest.raises(Exception, match="ERR\\ StreamDelete.*"):
        r.run("stream.delete", "mystream", "123-456")
    with pytest.raises(Exception, match="Invalid\\ stream\\ ID.*"):
        r.run("stream.delete", "mystream", "foo")
    # TODO: assert_equal "{$streamid2 {item 2 value b}}" r XRANGE mystream - +
    r.run("del", "mystream")
    r.run("set", "mystream", "mystring")
    with pytest.raises(Exception, match="ERR\\ StreamAdd.*"):
        r.run("stream.add", "mystream", "item", 1, "value", "a")
    with pytest.raises(Exception, match="ERR\\ StreamDelete.*"):
        r.run("stream.delete", "mystream", "123-456")


@pytest.mark.xfail(reason="not implemented")
def test_module_stream_add_unblocks_blocking_xread(r: ValkeyTestClient) -> None:
    """
    test {Module stream add unblocks blocking xread} {
        r del mystream

        # Blocking XREAD on an empty key
        set rd1 [valkey_deferring_client]
        $rd1 XREAD BLOCK 3000 STREAMS mystream $
        # wait until client is actually blocked
        wait_for_condition 50 100 {
            [s 0 blocked_clients] eq {1}
        } else {
            fail "Client is not blocked"
        }
        set id [r stream.add mystream field 1 value a]
        assert_equal "{mystream {{$id {field 1 value a}}}}" [$rd1 read]

        # Blocking XREAD on an existing stream
        set rd2 [valkey_deferring_client]
        $rd2 XREAD BLOCK 3000 STREAMS mystream $
        # wait until client is actually blocked
        wait_for_condition 50 100 {
            [s 0 blocked_clients] eq {1}
        } else {
            fail "Client is not blocked"
        }
        set id [r stream.add mystream field 2 value b]
        assert_equal "{mystream {{$id {field 2 value b}}}}" [$rd2 read]
    }
    """
    r.run("del", "mystream")
    # TODO: set rd1 valkey_deferring_client
    # TODO: $rd1 XREAD BLOCK 3000 STREAMS mystream
    # TODO: wait_for_condition 50 100 {
    #       [s 0 blocked_clients] eq {1}
    #   } else {
    #       fail "Client is not blocked"
    #   }
    id = r.run("stream.add", "mystream", "field", 1, "value", "a")
    # TODO: assert_equal "{mystream {{$id {field 1 value a}}}}" $rd1 read
    # TODO: set rd2 valkey_deferring_client
    # TODO: $rd2 XREAD BLOCK 3000 STREAMS mystream
    # TODO: wait_for_condition 50 100 {
    #       [s 0 blocked_clients] eq {1}
    #   } else {
    #       fail "Client is not blocked"
    #   }
    id = r.run("stream.add", "mystream", "field", 2, "value", "b")
    # TODO: assert_equal "{mystream {{$id {field 2 value b}}}}" $rd2 read


def test_module_stream_add_benchmark_1m_stream_add(r: ValkeyTestClient) -> None:
    """
    test {Module stream add benchmark (1M stream add)} {
        set n 1000000
        r del mystream
        set result [r stream.addn mystream $n field value]
        assert_equal $result $n
    }
    """
    n = 1000000
    r.run("del", "mystream")
    result = r.run("stream.addn", "mystream", n, "field", "value")
    assert result == n


@pytest.mark.xfail(reason="not implemented")
def test_module_stream_iterator(r: ValkeyTestClient) -> None:
    """
    test {Module stream iterator} {
        r del mystream
        set streamid1 [r xadd mystream * item 1 value a]
        set streamid2 [r xadd mystream * item 2 value b]
        # range result
        set result1 [r stream.range mystream "-" "+"]
        set expect1 [r xrange mystream "-" "+"]
        assert_equal $result1 $expect1
        # reverse range
        set result_rev [r stream.range mystream "+" "-"]
        set expect_rev [r xrevrange mystream "+" "-"]
        assert_equal $result_rev $expect_rev

        # only one item: range with startid = endid
        set result2 [r stream.range mystream "-" $streamid1]
        assert_equal $result2 "{$streamid1 {item 1 value a}}"
        assert_equal $result2 [list [list $streamid1 {item 1 value a}]]
        # only one item: range with startid = endid
        set result3 [r stream.range mystream $streamid2 $streamid2]
        assert_equal $result3 "{$streamid2 {item 2 value b}}"
        assert_equal $result3 [list [list $streamid2 {item 2 value b}]]
    }
    """
    r.run("del", "mystream")
    streamid1 = r.run("xadd", "mystream", "*", "item", 1, "value", "a")
    streamid2 = r.run("xadd", "mystream", "*", "item", 2, "value", "b")
    result1 = r.run("stream.range", "mystream", "-", "+")
    expect1 = r.run("xrange", "mystream", "-", "+")
    assert result1 == expect1
    result_rev = r.run("stream.range", "mystream", "+", "-")
    expect_rev = r.run("xrevrange", "mystream", "+", "-")
    # TODO: assert_equal result _rev expect _rev
    result2 = r.run("stream.range", "mystream", "-", streamid1)
    # TODO: assert_equal result2 "{$streamid1 {item 1 value a}}"
    # TODO: assert_equal result2 list [list $streamid1 {item 1 value a}]
    result3 = r.run("stream.range", "mystream", streamid2, streamid2)
    # TODO: assert_equal result3 "{$streamid2 {item 2 value b}}"
    # TODO: assert_equal result3 list [list $streamid2 {item 2 value b}]


@pytest.mark.xfail(reason="not implemented")
def test_module_stream_iterator_delete(r: ValkeyTestClient) -> None:
    """
    test {Module stream iterator delete} {
        r del mystream
        set id1 [r xadd mystream * normal item]
        set id2 [r xadd mystream * selfdestruct yes]
        set id3 [r xadd mystream * another item]
        # stream.range deletes the "selfdestruct" item after returning it
        assert_equal \
            "{$id1 {normal item}} {$id2 {selfdestruct yes}} {$id3 {another item}}" \
            [r stream.range mystream - +]
        # now, the "selfdestruct" item is gone
        assert_equal \
            "{$id1 {normal item}} {$id3 {another item}}" \
            [r stream.range mystream - +]
    }
    """
    r.run("del", "mystream")
    id1 = r.run("xadd", "mystream", "*", "normal", "item")
    id2 = r.run("xadd", "mystream", "*", "selfdestruct", "yes")
    id3 = r.run("xadd", "mystream", "*", "another", "item")
    # TODO: assert_equal "{$id1 {normal item}} {$id2 {selfdestruct yes}} {$id3 {another item}}" r stream.range mystream - +
    # TODO: assert_equal "{$id1 {normal item}} {$id3 {another item}}" r stream.range mystream - +


def test_module_stream_trim_by_length(r: ValkeyTestClient) -> None:
    """
    test {Module stream trim by length} {
        r del mystream
        # exact maxlen
        r xadd mystream * item 1 value a
        r xadd mystream * item 2 value b
        r xadd mystream * item 3 value c
        assert_equal 3 [r xlen mystream]
        assert_equal 0 [r stream.trim mystream maxlen = 5]
        assert_equal 3 [r xlen mystream]
        assert_equal 2 [r stream.trim mystream maxlen = 1]
        assert_equal 1 [r xlen mystream]
        assert_equal 1 [r stream.trim mystream maxlen = 0]
        # check that there is no limit for exact maxlen
        r stream.addn mystream 20000 item x value y
        assert_equal 20000 [r stream.trim mystream maxlen = 0]
        # approx maxlen (100 items per node implies default limit 10K items)
        r stream.addn mystream 20000 item x value y
        assert_equal 20000 [r xlen mystream]
        assert_equal 10000 [r stream.trim mystream maxlen ~ 2]
        assert_equal 9900  [r stream.trim mystream maxlen ~ 2]
        assert_equal 0     [r stream.trim mystream maxlen ~ 2]
        assert_equal 100   [r xlen mystream]
        assert_equal 100   [r stream.trim mystream maxlen ~ 0]
        assert_equal 0     [r xlen mystream]
    }
    """
    r.run("del", "mystream")
    r.run("xadd", "mystream", "*", "item", 1, "value", "a")
    r.run("xadd", "mystream", "*", "item", 2, "value", "b")
    r.run("xadd", "mystream", "*", "item", 3, "value", "c")
    assert 3 == r.run("xlen", "mystream")
    assert 0 == r.run("stream.trim", "mystream", "maxlen", "=", 5)
    assert 3 == r.run("xlen", "mystream")
    assert 2 == r.run("stream.trim", "mystream", "maxlen", "=", 1)
    assert 1 == r.run("xlen", "mystream")
    assert 1 == r.run("stream.trim", "mystream", "maxlen", "=", 0)
    r.run("stream.addn", "mystream", 20000, "item", "x", "value", "y")
    assert 20000 == r.run("stream.trim", "mystream", "maxlen", "=", 0)
    r.run("stream.addn", "mystream", 20000, "item", "x", "value", "y")
    assert 20000 == r.run("xlen", "mystream")
    assert 10000 == r.run("stream.trim", "mystream", "maxlen", "~", 2)
    assert 9900 == r.run("stream.trim", "mystream", "maxlen", "~", 2)
    assert 0 == r.run("stream.trim", "mystream", "maxlen", "~", 2)
    assert 100 == r.run("xlen", "mystream")
    assert 100 == r.run("stream.trim", "mystream", "maxlen", "~", 0)
    assert 0 == r.run("xlen", "mystream")


def test_module_stream_trim_by_id(r: ValkeyTestClient) -> None:
    """
    test {Module stream trim by ID} {
        r del mystream
        # exact minid
        r xadd mystream * item 1 value a
        r xadd mystream * item 2 value b
        set minid [r xadd mystream * item 3 value c]
        assert_equal 3 [r xlen mystream]
        assert_equal 0 [r stream.trim mystream minid = -]
        assert_equal 3 [r xlen mystream]
        assert_equal 2 [r stream.trim mystream minid = $minid]
        assert_equal 1 [r xlen mystream]
        assert_equal 1 [r stream.trim mystream minid = +]
        # check that there is no limit for exact minid
        r stream.addn mystream 20000 item x value y
        assert_equal 20000 [r stream.trim mystream minid = +]
        # approx minid (100 items per node implies default limit 10K items)
        r stream.addn mystream 19980 item x value y
        set minid [r xadd mystream * item x value y]
        r stream.addn mystream 19 item x value y
        assert_equal 20000 [r xlen mystream]
        assert_equal 10000 [r stream.trim mystream minid ~ $minid]
        assert_equal 9900  [r stream.trim mystream minid ~ $minid]
        assert_equal 0     [r stream.trim mystream minid ~ $minid]
        assert_equal 100   [r xlen mystream]
        assert_equal 100   [r stream.trim mystream minid ~ +]
        assert_equal 0     [r xlen mystream]
    }
    """
    r.run("del", "mystream")
    r.run("xadd", "mystream", "*", "item", 1, "value", "a")
    r.run("xadd", "mystream", "*", "item", 2, "value", "b")
    minid = r.run("xadd", "mystream", "*", "item", 3, "value", "c")
    assert 3 == r.run("xlen", "mystream")
    assert 0 == r.run("stream.trim", "mystream", "minid", "=", "-")
    assert 3 == r.run("xlen", "mystream")
    assert 2 == r.run("stream.trim", "mystream", "minid", "=", minid)
    assert 1 == r.run("xlen", "mystream")
    assert 1 == r.run("stream.trim", "mystream", "minid", "=", "+")
    r.run("stream.addn", "mystream", 20000, "item", "x", "value", "y")
    assert 20000 == r.run("stream.trim", "mystream", "minid", "=", "+")
    r.run("stream.addn", "mystream", 19980, "item", "x", "value", "y")
    minid = r.run("xadd", "mystream", "*", "item", "x", "value", "y")
    r.run("stream.addn", "mystream", 19, "item", "x", "value", "y")
    assert 20000 == r.run("xlen", "mystream")
    assert 10000 == r.run("stream.trim", "mystream", "minid", "~", minid)
    assert 9900 == r.run("stream.trim", "mystream", "minid", "~", minid)
    assert 0 == r.run("stream.trim", "mystream", "minid", "~", minid)
    assert 100 == r.run("xlen", "mystream")
    assert 100 == r.run("stream.trim", "mystream", "minid", "~", "+")
    assert 0 == r.run("xlen", "mystream")


def test_unload_the_module_stream(r: ValkeyTestClient) -> None:
    """
    test "Unload the module - stream" {
        assert_equal {OK} [r module unload stream]
    }
    """
    assert "OK" == r.run("module", "unload", "stream")


"""
run_solo {stream-large-memory} {
    set testmodule [file normalize tests/modules/stream.so]
    start_server {tags {"modules large-memory"}} {
        r module load $testmodule

        test {Module stream XADD big fields doesn't create empty key} {
            set original_proto [config_get_set proto-max-bulk-len 2147483647] ;#2gb
            set original_query [config_get_set client-query-buffer-limit 2147483647] ;#2gb

            r del mystream
            r write "*4\r\n\$10\r\nstream.add\r\n\$8\r\nmystream\r\n\$5\r\nfield\r\n"
            catch {
                write_big_bulk 1073741824 ;#1gb
            } err
            assert {$err eq "ERR StreamAdd failed"}
            assert_equal 0 [r exists mystream]

            # restore defaults
            r config set proto-max-bulk-len $original_proto
            r config set client-query-buffer-limit $original_query
        } {OK}

        assert_equal {OK} [r module unload stream]
    }
}
"""
