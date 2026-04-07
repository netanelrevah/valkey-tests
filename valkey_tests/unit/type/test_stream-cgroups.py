# ruff: noqa: PLR2004, F841, RUF043, ANN002, ANN201
import time
from fnmatch import fnmatch

import pytest

from tests.valkey_test_client import ValkeyTestClient

pytestmark = [pytest.mark.stream]


@pytest.mark.xfail(reason="not implemented")
def test_xgroup_create_creation_and_duplicate_group_name_detection(r: ValkeyTestClient) -> None:
    """
    test {XGROUP CREATE: creation and duplicate group name detection} {
        r DEL mystream
        r XADD mystream * foo bar
        r XGROUP CREATE mystream mygroup $
        catch {r XGROUP CREATE mystream mygroup $} err
        set err
    } {BUSYGROUP*}
    """
    r.run("DEL", "mystream")
    r.run("XADD", "mystream", "*", "foo", "bar")
    # TODO: r XGROUP CREATE mystream mygroup
    catch("r XGROUP CREATE mystream mygroup $", "err")
    # TODO: set err
    assert False


@pytest.mark.xfail(reason="not implemented")
def test_xgroup_create_with_entriesread_parameter(r: ValkeyTestClient) -> None:
    """
    test {XGROUP CREATE: with ENTRIESREAD parameter} {
        r DEL mystream
        r XADD mystream 1-1 a 1
        r XADD mystream 1-2 b 2
        r XADD mystream 1-3 c 3
        r XADD mystream 1-4 d 4
        assert_error "*value for ENTRIESREAD must be positive or -1*" {r XGROUP CREATE mystream mygroup $ ENTRIESREAD -3}

        r XGROUP CREATE mystream mygroup1 $ ENTRIESREAD 0
        r XGROUP CREATE mystream mygroup2 $ ENTRIESREAD 3

        set reply [r xinfo groups mystream]
        foreach group_info $reply {
            set group_name [dict get $group_info name]
            set entries_read [dict get $group_info entries-read]
            if {$group_name == "mygroup1"} {
                assert_equal $entries_read 0
            } else {
                assert_equal $entries_read 3
            }
        }
    }
    """
    r.run("DEL", "mystream")
    r.run("XADD", "mystream", "1-1", "a", 1)
    r.run("XADD", "mystream", "1-2", "b", 2)
    r.run("XADD", "mystream", "1-3", "c", 3)
    r.run("XADD", "mystream", "1-4", "d", 4)
    assert_error("*value for ENTRIESREAD must be positive or -1*", "r XGROUP CREATE mystream mygroup $ ENTRIESREAD -3")
    # TODO: r XGROUP CREATE mystream mygroup1  ENTRIESREAD 0
    # TODO: r XGROUP CREATE mystream mygroup2  ENTRIESREAD 3
    reply = r.run("xinfo", "groups", "mystream")
    foreach(
        "group_info",
        reply,
        '            set group_name [dict get $group_info name]\n            set entries_read [dict get $group_info entries-read]\n            if {$group_name == "mygroup1"} {\n                assert_equal $entries_read 0\n            } else {\n                assert_equal $entries_read 3\n            }\n        ',
    )


@pytest.mark.xfail(reason="not implemented")
def test_xgroup_create_automatic_stream_creation_fails_without_mkstream(r: ValkeyTestClient) -> None:
    """
    test {XGROUP CREATE: automatic stream creation fails without MKSTREAM} {
        r DEL mystream
        catch {r XGROUP CREATE mystream mygroup $} err
        set err
    } {ERR*}
    """
    r.run("DEL", "mystream")
    catch("r XGROUP CREATE mystream mygroup $", "err")
    # TODO: set err
    assert False


@pytest.mark.xfail(reason="not implemented")
def test_xgroup_create_automatic_stream_creation_works_with_mkstream(r: ValkeyTestClient) -> None:
    """
    test {XGROUP CREATE: automatic stream creation works with MKSTREAM} {
        r DEL mystream
        r XGROUP CREATE mystream mygroup $ MKSTREAM
    } {OK}
    """
    r.run("DEL", "mystream")
    # TODO: r XGROUP CREATE mystream mygroup  MKSTREAM
    assert False


@pytest.mark.xfail(reason="not implemented")
def test_xreadgroup_will_return_only_new_elements(r: ValkeyTestClient) -> None:
    """
    test {XREADGROUP will return only new elements} {
        r XADD mystream * a 1
        r XADD mystream * b 2
        # XREADGROUP should return only the new elements "a 1" "b 1"
        # and not the element "foo bar" which was pre existing in the
        # stream (see previous test)
        set reply [
            r XREADGROUP GROUP mygroup consumer-1 STREAMS mystream ">"
        ]
        assert {[llength [lindex $reply 0 1]] == 2}
        lindex $reply 0 1 0 1
    } {a 1}
    """
    r.run("XADD", "mystream", "*", "a", 1)
    r.run("XADD", "mystream", "*", "b", 2)
    reply = r.run("XREADGROUP", "GROUP", "mygroup", "consumer-1", "STREAMS", "mystream", ">")
    assert len(lindex(reply, 0, 1)) == 2
    # TODO: lindex reply 0 1 0 1
    assert False


def test_xreadgroup_can_read_the_history_of_the_elements_we_own(r: ValkeyTestClient) -> None:
    """
    test {XREADGROUP can read the history of the elements we own} {
        # Add a few more elements
        r XADD mystream * c 3
        r XADD mystream * d 4
        # Read a few elements using a different consumer name
        set reply [
            r XREADGROUP GROUP mygroup consumer-2 STREAMS mystream ">"
        ]
        assert {[llength [lindex $reply 0 1]] == 2}
        assert {[lindex $reply 0 1 0 1] eq {c 3}}

        set r1 [r XREADGROUP GROUP mygroup consumer-1 COUNT 10 STREAMS mystream 0]
        set r2 [r XREADGROUP GROUP mygroup consumer-2 COUNT 10 STREAMS mystream 0]
        assert {[lindex $r1 0 1 0 1] eq {a 1}}
        assert {[lindex $r2 0 1 0 1] eq {c 3}}
    }
    """
    r.run("XADD", "mystream", "*", "c", 3)
    r.run("XADD", "mystream", "*", "d", 4)
    reply = r.run("XREADGROUP", "GROUP", "mygroup", "consumer-2", "STREAMS", "mystream", ">")
    assert len(lindex(reply, 0, 1)) == 2
    assert lindex(reply, 0, 1, 0, 1) == "c 3"
    r1 = r.run("XREADGROUP", "GROUP", "mygroup", "consumer-1", "COUNT", 10, "STREAMS", "mystream", 0)
    r2 = r.run("XREADGROUP", "GROUP", "mygroup", "consumer-2", "COUNT", 10, "STREAMS", "mystream", 0)
    assert lindex(r1, 0, 1, 0, 1) == "a 1"
    assert lindex(r2, 0, 1, 0, 1) == "c 3"


def test_xpending_is_able_to_return_pending_items(r: ValkeyTestClient) -> None:
    """
    test {XPENDING is able to return pending items} {
        set pending [r XPENDING mystream mygroup - + 10]
        assert {[llength $pending] == 4}
        for {set j 0} {$j < 4} {incr j} {
            set item [lindex $pending $j]
            if {$j < 2} {
                set owner consumer-1
            } else {
                set owner consumer-2
            }
            assert {[lindex $item 1] eq $owner}
            assert {[lindex $item 1] eq $owner}
        }
    }
    """
    pending = r.run("XPENDING", "mystream", "mygroup", "-", "+", 10)
    assert len(pending) == 4
    j = 0
    while j < 4:
        item = pending[j]
        if j < 2:
            owner = "consumer-1"
        else:
            owner = "consumer-2"
        assert item[1] == owner
        assert item[1] == owner
        j += 1


def test_xpending_can_return_single_consumer_items(r: ValkeyTestClient) -> None:
    """
    test {XPENDING can return single consumer items} {
        set pending [r XPENDING mystream mygroup - + 10 consumer-1]
        assert {[llength $pending] == 2}
    }
    """
    pending = r.run("XPENDING", "mystream", "mygroup", "-", "+", 10, "consumer-1")
    assert len(pending) == 2


def test_xpending_only_group(r: ValkeyTestClient) -> None:
    """
    test {XPENDING only group} {
        set pending [r XPENDING mystream mygroup]
        assert {[llength $pending] == 4}
    }
    """
    pending = r.run("XPENDING", "mystream", "mygroup")
    assert len(pending) == 4


def test_xpending_with_idle(r: ValkeyTestClient) -> None:
    """
    test {XPENDING with IDLE} {
        after 20
        set pending [r XPENDING mystream mygroup IDLE 99999999 - + 10 consumer-1]
        assert {[llength $pending] == 0}
        set pending [r XPENDING mystream mygroup IDLE 1 - + 10 consumer-1]
        assert {[llength $pending] == 2}
        set pending [r XPENDING mystream mygroup IDLE 99999999 - + 10]
        assert {[llength $pending] == 0}
        set pending [r XPENDING mystream mygroup IDLE 1 - + 10]
        assert {[llength $pending] == 4}
    }
    """
    time.sleep(20 / 1000)
    pending = r.run("XPENDING", "mystream", "mygroup", "IDLE", 99999999, "-", "+", 10, "consumer-1")
    assert len(pending) == 0
    pending = r.run("XPENDING", "mystream", "mygroup", "IDLE", 1, "-", "+", 10, "consumer-1")
    assert len(pending) == 2
    pending = r.run("XPENDING", "mystream", "mygroup", "IDLE", 99999999, "-", "+", 10)
    assert len(pending) == 0
    pending = r.run("XPENDING", "mystream", "mygroup", "IDLE", 1, "-", "+", 10)
    assert len(pending) == 4


def test_xpending_with_exclusive_range_intervals_works_as_expected(r: ValkeyTestClient) -> None:
    """
    test {XPENDING with exclusive range intervals works as expected} {
        set pending [r XPENDING mystream mygroup - + 10]
        assert {[llength $pending] == 4}
        set startid [lindex [lindex $pending 0] 0]
        set endid [lindex [lindex $pending 3] 0]
        set expending [r XPENDING mystream mygroup ($startid ($endid 10]
        assert {[llength $expending] == 2}
        for {set j 0} {$j < 2} {incr j} {
            set itemid [lindex [lindex $expending $j] 0]
            assert {$itemid ne $startid}
            assert {$itemid ne $endid}
        }
    }
    """
    pending = r.run("XPENDING", "mystream", "mygroup", "-", "+", 10)
    assert len(pending) == 4
    startid = pending[0][0]
    endid = pending[3][0]
    expending = r.run("XPENDING", "mystream", "mygroup", "($startid", "($endid", 10)
    assert len(expending) == 2
    j = 0
    while j < 2:
        itemid = expending[j][0]
        assert itemid != startid
        assert itemid != endid
        j += 1


def test_xack_is_able_to_remove_items_from_the_consumer_or_group_pel(r: ValkeyTestClient) -> None:
    """
    test {XACK is able to remove items from the consumer/group PEL} {
        set pending [r XPENDING mystream mygroup - + 10 consumer-1]
        set id1 [lindex $pending 0 0]
        set id2 [lindex $pending 1 0]
        assert {[r XACK mystream mygroup $id1] eq 1}
        set pending [r XPENDING mystream mygroup - + 10 consumer-1]
        assert {[llength $pending] == 1}
        set id [lindex $pending 0 0]
        assert {$id eq $id2}
        set global_pel [r XPENDING mystream mygroup - + 10]
        assert {[llength $global_pel] == 3}
    }
    """
    pending = r.run("XPENDING", "mystream", "mygroup", "-", "+", 10, "consumer-1")
    id1 = lindex(pending, 0, 0)
    id2 = lindex(pending, 1, 0)
    assert r.run("XACK", "mystream", "mygroup", id1) == 1
    pending = r.run("XPENDING", "mystream", "mygroup", "-", "+", 10, "consumer-1")
    assert len(pending) == 1
    id = lindex(pending, 0, 0)
    assert id == id2
    global_pel = r.run("XPENDING", "mystream", "mygroup", "-", "+", 10)
    assert len(global_pel) == 3


def test_xack_can_t_remove_the_same_item_multiple_times(r: ValkeyTestClient) -> None:
    """
    test {XACK can't remove the same item multiple times} {
        assert {[r XACK mystream mygroup $id1] eq 0}
    }
    """
    assert_("[r XACK mystream mygroup $id1] eq 0")


def test_xack_is_able_to_accept_multiple_arguments(r: ValkeyTestClient) -> None:
    """
    test {XACK is able to accept multiple arguments} {
        # One of the IDs was already removed, so it should ack
        # just ID2.
        assert {[r XACK mystream mygroup $id1 $id2] eq 1}
    }
    """
    assert_("[r XACK mystream mygroup $id1 $id2] eq 1")


@pytest.mark.xfail(reason="not implemented")
def test_xack_should_fail_if_got_at_least_one_invalid_id(r: ValkeyTestClient) -> None:
    """
    test {XACK should fail if got at least one invalid ID} {
        r del mystream
        r xgroup create s g $ MKSTREAM
        r xadd s * f1 v1
        set c [llength [lindex [r xreadgroup group g c streams s >] 0 1]]
        assert {$c == 1}
        set pending [r xpending s g - + 10 c]
        set id1 [lindex $pending 0 0]
        assert_error "*Invalid stream ID specified*" {r xack s g $id1 invalid-id}
        assert {[r xack s g $id1] eq 1}
    }
    """
    r.run("del", "mystream")
    # TODO: r xgroup create s g  MKSTREAM
    r.run("xadd", "s", "*", "f1", "v1")
    c = len(lindex(r.run("xreadgroup", "group", "g", "c", "streams", "s", ">"), 0, 1))
    assert c == 1
    pending = r.run("xpending", "s", "g", "-", "+", 10, "c")
    id1 = lindex(pending, 0, 0)
    with pytest.raises(Exception, match=".*Invalid\\ stream\\ ID\\ specified.*"):
        r.run("xack", "s", "g", id1, "invalid-id")
    assert r.run("xack", "s", "g", id1) == 1


@pytest.mark.xfail(reason="not implemented")
def test_pel_nack_reassignment_after_xgroup_setid_event(r: ValkeyTestClient) -> None:
    """
    test {PEL NACK reassignment after XGROUP SETID event} {
        r del events
        r xadd events * f1 v1
        r xadd events * f1 v1
        r xadd events * f1 v1
        r xadd events * f1 v1
        r xgroup create events g1 $
        r xadd events * f1 v1
        set c [llength [lindex [r xreadgroup group g1 c1 streams events >] 0 1]]
        assert {$c == 1}
        r xgroup setid events g1 -
        set c [llength [lindex [r xreadgroup group g1 c2 streams events >] 0 1]]
        assert {$c == 5}
    }
    """
    r.run("del", "events")
    r.run("xadd", "events", "*", "f1", "v1")
    r.run("xadd", "events", "*", "f1", "v1")
    r.run("xadd", "events", "*", "f1", "v1")
    r.run("xadd", "events", "*", "f1", "v1")
    # TODO: r xgroup create events g1
    r.run("xadd", "events", "*", "f1", "v1")
    c = len(lindex(r.run("xreadgroup", "group", "g1", "c1", "streams", "events", ">"), 0, 1))
    assert c == 1
    r.run("xgroup", "setid", "events", "g1", "-")
    c = len(lindex(r.run("xreadgroup", "group", "g1", "c2", "streams", "events", ">"), 0, 1))
    assert c == 5


def test_xreadgroup_will_not_report_data_on_empty_history_bug_5577(r: ValkeyTestClient) -> None:
    """
    test {XREADGROUP will not report data on empty history. Bug #5577} {
        r del events
        r xadd events * a 1
        r xadd events * b 2
        r xadd events * c 3
        r xgroup create events mygroup 0

        # Current local PEL should be empty
        set res [r xpending events mygroup - + 10]
        assert {[llength $res] == 0}

        # So XREADGROUP should read an empty history as well
        set res [r xreadgroup group mygroup myconsumer count 3 streams events 0]
        assert {[llength [lindex $res 0 1]] == 0}

        # We should fetch all the elements in the stream asking for >
        set res [r xreadgroup group mygroup myconsumer count 3 streams events >]
        assert {[llength [lindex $res 0 1]] == 3}

        # Now the history is populated with three not acked entries
        set res [r xreadgroup group mygroup myconsumer count 3 streams events 0]
        assert {[llength [lindex $res 0 1]] == 3}
    }
    """
    r.run("del", "events")
    r.run("xadd", "events", "*", "a", 1)
    r.run("xadd", "events", "*", "b", 2)
    r.run("xadd", "events", "*", "c", 3)
    r.run("xgroup", "create", "events", "mygroup", 0)
    res = r.run("xpending", "events", "mygroup", "-", "+", 10)
    assert len(res) == 0
    res = r.run("xreadgroup", "group", "mygroup", "myconsumer", "count", 3, "streams", "events", 0)
    assert len(lindex(res, 0, 1)) == 0
    res = r.run("xreadgroup", "group", "mygroup", "myconsumer", "count", 3, "streams", "events", ">")
    assert len(lindex(res, 0, 1)) == 3
    res = r.run("xreadgroup", "group", "mygroup", "myconsumer", "count", 3, "streams", "events", 0)
    assert len(lindex(res, 0, 1)) == 3


@pytest.mark.xfail(reason="not implemented")
def test_xreadgroup_history_reporting_of_deleted_entries_bug_5570(r: ValkeyTestClient) -> None:
    """
    test {XREADGROUP history reporting of deleted entries. Bug #5570} {
        r del mystream
        r XGROUP CREATE mystream mygroup $ MKSTREAM
        r XADD mystream 1 field1 A
        r XREADGROUP GROUP mygroup myconsumer STREAMS mystream >
        r XADD mystream MAXLEN 1 2 field1 B
        r XREADGROUP GROUP mygroup myconsumer STREAMS mystream >

        # Now we have two pending entries, however one should be deleted
        # and one should be ok (we should only see "B")
        set res [r XREADGROUP GROUP mygroup myconsumer STREAMS mystream 0-1]
        assert {[lindex $res 0 1 0] == {1-0 {}}}
        assert {[lindex $res 0 1 1] == {2-0 {field1 B}}}
    }
    """
    r.run("del", "mystream")
    # TODO: r XGROUP CREATE mystream mygroup  MKSTREAM
    r.run("XADD", "mystream", 1, "field1", "A")
    r.run("XREADGROUP", "GROUP", "mygroup", "myconsumer", "STREAMS", "mystream", ">")
    r.run("XADD", "mystream", "MAXLEN", 1, 2, "field1", "B")
    r.run("XREADGROUP", "GROUP", "mygroup", "myconsumer", "STREAMS", "mystream", ">")
    res = r.run("XREADGROUP", "GROUP", "mygroup", "myconsumer", "STREAMS", "mystream", "0-1")
    assert lindex(res, 0, 1, 0) == "1-0 {}"
    assert lindex(res, 0, 1, 1) == "2-0 {field1 B}"


@pytest.mark.xfail(reason="not implemented")
def test_blocking_xreadgroup_will_not_reply_with_an_empty_array(r: ValkeyTestClient) -> None:
    """
    test {Blocking XREADGROUP will not reply with an empty array} {
        r del mystream
        r XGROUP CREATE mystream mygroup $ MKSTREAM
        r XADD mystream 666 f v
        set res [r XREADGROUP GROUP mygroup Alice BLOCK 10 STREAMS mystream ">"]
        assert {[lindex $res 0 1 0] == {666-0 {f v}}}
        r XADD mystream 667 f2 v2
        r XDEL mystream 667
        set rd [valkey_deferring_client]
        $rd XREADGROUP GROUP mygroup Alice BLOCK 10 STREAMS mystream ">"
        wait_for_blocked_clients_count 0
        assert {[$rd read] == {}} ;# before the fix, client didn't even block, but was served synchronously with {mystream {}}
        $rd close
    }
    """
    r.run("del", "mystream")
    # TODO: r XGROUP CREATE mystream mygroup  MKSTREAM
    r.run("XADD", "mystream", 666, "f", "v")
    res = r.run("XREADGROUP", "GROUP", "mygroup", "Alice", "BLOCK", 10, "STREAMS", "mystream", ">")
    assert lindex(res, 0, 1, 0) == "666-0 {f v}"
    r.run("XADD", "mystream", 667, "f2", "v2")
    r.run("XDEL", "mystream", 667)
    rd = ValkeyTestClient.create_from(r)
    rd.run("XREADGROUP", "GROUP", "mygroup", "Alice", "BLOCK", 10, "STREAMS", "mystream", ">")
    wait_for_blocked_clients_count(0)
    assert rd.run("read") == ""
    rd.run("close")


@pytest.mark.xfail(reason="not implemented")
def test_blocking_xreadgroup_key_deleted(r: ValkeyTestClient) -> None:
    """
    test {Blocking XREADGROUP: key deleted} {
        r DEL mystream
        r XADD mystream 666 f v
        r XGROUP CREATE mystream mygroup $
        set rd [valkey_deferring_client]
        $rd XREADGROUP GROUP mygroup Alice BLOCK 0 STREAMS mystream ">"
        wait_for_blocked_clients_count 1
        r DEL mystream
        assert_error "NOGROUP*" {$rd read}
        $rd close
    }
    """
    r.run("DEL", "mystream")
    r.run("XADD", "mystream", 666, "f", "v")
    # TODO: r XGROUP CREATE mystream mygroup
    rd = ValkeyTestClient.create_from(r)
    rd.run("XREADGROUP", "GROUP", "mygroup", "Alice", "BLOCK", 0, "STREAMS", "mystream", ">")
    wait_for_blocked_clients_count(1)
    r.run("DEL", "mystream")
    assert_error("NOGROUP*", "$rd read")
    rd.run("close")


@pytest.mark.xfail(reason="not implemented")
def test_blocking_xreadgroup_key_type_changed_with_set(r: ValkeyTestClient) -> None:
    """
    test {Blocking XREADGROUP: key type changed with SET} {
        r DEL mystream
        r XADD mystream 666 f v
        r XGROUP CREATE mystream mygroup $
        set rd [valkey_deferring_client]
        $rd XREADGROUP GROUP mygroup Alice BLOCK 0 STREAMS mystream ">"
        wait_for_blocked_clients_count 1
        r SET mystream val1
        assert_error "*WRONGTYPE*" {$rd read}
        $rd close
    }
    """
    r.run("DEL", "mystream")
    r.run("XADD", "mystream", 666, "f", "v")
    # TODO: r XGROUP CREATE mystream mygroup
    rd = ValkeyTestClient.create_from(r)
    rd.run("XREADGROUP", "GROUP", "mygroup", "Alice", "BLOCK", 0, "STREAMS", "mystream", ">")
    wait_for_blocked_clients_count(1)
    r.run("SET", "mystream", "val1")
    assert_error("*WRONGTYPE*", "$rd read")
    rd.run("close")


@pytest.mark.xfail(reason="not implemented")
def test_blocking_xreadgroup_key_type_changed_with_transaction(r: ValkeyTestClient) -> None:
    """
    test {Blocking XREADGROUP: key type changed with transaction} {
        r DEL mystream
        r XADD mystream 666 f v
        r XGROUP CREATE mystream mygroup $
        set rd [valkey_deferring_client]
        $rd XREADGROUP GROUP mygroup Alice BLOCK 0 STREAMS mystream ">"
        wait_for_blocked_clients_count 1
        r MULTI
        r DEL mystream
        r SADD mystream e1
        r EXEC
        assert_error "*WRONGTYPE*" {$rd read}
        $rd close
    }
    """
    r.run("DEL", "mystream")
    r.run("XADD", "mystream", 666, "f", "v")
    # TODO: r XGROUP CREATE mystream mygroup
    rd = ValkeyTestClient.create_from(r)
    rd.run("XREADGROUP", "GROUP", "mygroup", "Alice", "BLOCK", 0, "STREAMS", "mystream", ">")
    wait_for_blocked_clients_count(1)
    r.run("MULTI")
    r.run("DEL", "mystream")
    r.run("SADD", "mystream", "e1")
    r.run("EXEC")
    assert_error("*WRONGTYPE*", "$rd read")
    rd.run("close")


@pytest.mark.xfail(reason="not implemented")
def test_blocking_xreadgroup_flushed_db(r: ValkeyTestClient) -> None:
    """
    test {Blocking XREADGROUP: flushed DB} {
        r DEL mystream
        r XADD mystream 666 f v
        r XGROUP CREATE mystream mygroup $
        set rd [valkey_deferring_client]
        $rd XREADGROUP GROUP mygroup Alice BLOCK 0 STREAMS mystream ">"
        wait_for_blocked_clients_count 1
        r FLUSHALL
        assert_error "*NOGROUP*" {$rd read}
        $rd close
    }
    """
    r.run("DEL", "mystream")
    r.run("XADD", "mystream", 666, "f", "v")
    # TODO: r XGROUP CREATE mystream mygroup
    rd = ValkeyTestClient.create_from(r)
    rd.run("XREADGROUP", "GROUP", "mygroup", "Alice", "BLOCK", 0, "STREAMS", "mystream", ">")
    wait_for_blocked_clients_count(1)
    r.run("FLUSHALL")
    assert_error("*NOGROUP*", "$rd read")
    rd.run("close")


@pytest.mark.xfail(reason="not implemented")
def test_blocking_xreadgroup_swapped_db_key_doesn_t_exist(r: ValkeyTestClient) -> None:
    """
    test {Blocking XREADGROUP: swapped DB, key doesn't exist} {
        r SELECT 4
        r FLUSHDB
        r SELECT 9
        r DEL mystream
        r XADD mystream 666 f v
        r XGROUP CREATE mystream mygroup $
        set rd [valkey_deferring_client]
        $rd SELECT 9
        $rd read
        $rd XREADGROUP GROUP mygroup Alice BLOCK 0 STREAMS mystream ">"
        wait_for_blocked_clients_count 1
        r SWAPDB 4 9
        assert_error "*NOGROUP*" {$rd read}
        $rd close
    } {0} {singledb:skip cluster:skip}
    """
    r.run("SELECT", 4)
    r.run("FLUSHDB")
    r.run("SELECT", 9)
    r.run("DEL", "mystream")
    r.run("XADD", "mystream", 666, "f", "v")
    # TODO: r XGROUP CREATE mystream mygroup
    rd = ValkeyTestClient.create_from(r)
    rd.run("SELECT", 9)
    rd.run("read")
    rd.run("XREADGROUP", "GROUP", "mygroup", "Alice", "BLOCK", 0, "STREAMS", "mystream", ">")
    wait_for_blocked_clients_count(1)
    r.run("SWAPDB", 4, 9)
    assert_error("*NOGROUP*", "$rd read")
    # TODO: $rd close
    assert False


@pytest.mark.xfail(reason="not implemented")
def test_blocking_xreadgroup_swapped_db_key_is_not_a_stream(r: ValkeyTestClient) -> None:
    """
    test {Blocking XREADGROUP: swapped DB, key is not a stream} {
        r SELECT 4
        r FLUSHDB
        r LPUSH mystream e1
        r SELECT 9
        r DEL mystream
        r XADD mystream 666 f v
        r XGROUP CREATE mystream mygroup $
        set rd [valkey_deferring_client]
        $rd SELECT 9
        $rd read
        $rd XREADGROUP GROUP mygroup Alice BLOCK 0 STREAMS mystream ">"
        wait_for_blocked_clients_count 1
        r SWAPDB 4 9
        assert_error "*WRONGTYPE*" {$rd read}
        $rd close
    } {0} {singledb:skip cluster:skip}
    """
    r.run("SELECT", 4)
    r.run("FLUSHDB")
    r.run("LPUSH", "mystream", "e1")
    r.run("SELECT", 9)
    r.run("DEL", "mystream")
    r.run("XADD", "mystream", 666, "f", "v")
    # TODO: r XGROUP CREATE mystream mygroup
    rd = ValkeyTestClient.create_from(r)
    rd.run("SELECT", 9)
    rd.run("read")
    rd.run("XREADGROUP", "GROUP", "mygroup", "Alice", "BLOCK", 0, "STREAMS", "mystream", ">")
    wait_for_blocked_clients_count(1)
    r.run("SWAPDB", 4, 9)
    assert_error("*WRONGTYPE*", "$rd read")
    # TODO: $rd close
    assert False


@pytest.mark.xfail(reason="not implemented")
def test_xread_and_xreadgroup_against_wrong_parameter(r: ValkeyTestClient) -> None:
    """
    test {XREAD and XREADGROUP against wrong parameter} {
        r DEL mystream
        r XADD mystream 666 f v
        r XGROUP CREATE mystream mygroup $
        assert_error "ERR Unbalanced 'xreadgroup' list of streams: for each stream key an ID or '>' must be specified." {r XREADGROUP GROUP mygroup Alice COUNT 1 STREAMS mystream }
        assert_error "ERR Unbalanced 'xread' list of streams: for each stream key an ID or '$' must be specified." {r XREAD COUNT 1 STREAMS mystream }
    }
    """
    r.run("DEL", "mystream")
    r.run("XADD", "mystream", 666, "f", "v")
    # TODO: r XGROUP CREATE mystream mygroup
    with pytest.raises(
        Exception,
        match="ERR\\ Unbalanced\\ 'xreadgroup'\\ list\\ of\\ streams:\\ for\\ each\\ stream\\ key\\ an\\ ID\\ or\\ '>'\\ must\\ be\\ specified\\.",
    ):
        r.run("XREADGROUP", "GROUP", "mygroup", "Alice", "COUNT", 1, "STREAMS", "mystream")
    with pytest.raises(
        Exception,
        match="ERR\\ Unbalanced\\ 'xread'\\ list\\ of\\ streams:\\ for\\ each\\ stream\\ key\\ an\\ ID\\ or\\ '\\$'\\ must\\ be\\ specified\\.",
    ):
        r.run("XREAD", "COUNT", 1, "STREAMS", "mystream")


def test_blocking_xread_key_deleted(r: ValkeyTestClient) -> None:
    """
    test {Blocking XREAD: key deleted} {
        r DEL mystream
        r XADD mystream 666 f v
        set rd [valkey_deferring_client]
        $rd XREAD BLOCK 0 STREAMS mystream "$"
        wait_for_blocked_clients_count 1
        r DEL mystream

        r XADD mystream 667 f v
        set res [$rd read]
        assert_equal [lindex $res 0 1 0] {667-0 {f v}}
        $rd close
    }
    """
    r.run("DEL", "mystream")
    r.run("XADD", "mystream", 666, "f", "v")
    rd = ValkeyTestClient.create_from(r)
    rd.run("XREAD", "BLOCK", 0, "STREAMS", "mystream", "$")
    wait_for_blocked_clients_count(1)
    r.run("DEL", "mystream")
    r.run("XADD", "mystream", 667, "f", "v")
    res = rd.run("read")
    assert lindex(res, 0, 1, 0) == "667-0 {f v}"
    rd.run("close")


def test_blocking_xread_key_type_changed_with_set(r: ValkeyTestClient) -> None:
    """
    test {Blocking XREAD: key type changed with SET} {
        r DEL mystream
        r XADD mystream 666 f v
        set rd [valkey_deferring_client]
        $rd XREAD BLOCK 0 STREAMS mystream "$"
        wait_for_blocked_clients_count 1
        r SET mystream val1

        r DEL mystream
        r XADD mystream 667 f v
        set res [$rd read]
        assert_equal [lindex $res 0 1 0] {667-0 {f v}}
        $rd close
    }
    """
    r.run("DEL", "mystream")
    r.run("XADD", "mystream", 666, "f", "v")
    rd = ValkeyTestClient.create_from(r)
    rd.run("XREAD", "BLOCK", 0, "STREAMS", "mystream", "$")
    wait_for_blocked_clients_count(1)
    r.run("SET", "mystream", "val1")
    r.run("DEL", "mystream")
    r.run("XADD", "mystream", 667, "f", "v")
    res = rd.run("read")
    assert lindex(res, 0, 1, 0) == "667-0 {f v}"
    rd.run("close")


@pytest.mark.xfail(reason="not implemented")
def test_blocking_xreadgroup_for_stream_that_ran_dry_issue_5299(r: ValkeyTestClient) -> None:
    """
    test {Blocking XREADGROUP for stream that ran dry (issue #5299)} {
        set rd [valkey_deferring_client]

        # Add a entry then delete it, now stream's last_id is 666.
        r DEL mystream
        r XGROUP CREATE mystream mygroup $ MKSTREAM
        r XADD mystream 666 key value
        r XDEL mystream 666

        # Pass a special `>` ID but without new entry, released on timeout.
        $rd XREADGROUP GROUP mygroup myconsumer BLOCK 10 STREAMS mystream >
        assert_equal [$rd read] {}

        # Throw an error if the ID equal or smaller than the last_id.
        assert_error ERR*equal*smaller* {r XADD mystream 665 key value}
        assert_error ERR*equal*smaller* {r XADD mystream 666 key value}

        # Entered blocking state and then release because of the new entry.
        $rd XREADGROUP GROUP mygroup myconsumer BLOCK 0 STREAMS mystream >
        wait_for_blocked_clients_count 1
        r XADD mystream 667 key value
        assert_equal [$rd read] {{mystream {{667-0 {key value}}}}}

        $rd close
    }
    """
    rd = ValkeyTestClient.create_from(r)
    r.run("DEL", "mystream")
    # TODO: r XGROUP CREATE mystream mygroup  MKSTREAM
    r.run("XADD", "mystream", 666, "key", "value")
    r.run("XDEL", "mystream", 666)
    rd.run("XREADGROUP", "GROUP", "mygroup", "myconsumer", "BLOCK", 10, "STREAMS", "mystream", ">")
    assert rd.run("read") == ""
    with pytest.raises(Exception, match="ERR.*equal.*smaller.*"):
        r.run("XADD", "mystream", 665, "key", "value")
    with pytest.raises(Exception, match="ERR.*equal.*smaller.*"):
        r.run("XADD", "mystream", 666, "key", "value")
    rd.run("XREADGROUP", "GROUP", "mygroup", "myconsumer", "BLOCK", 0, "STREAMS", "mystream", ">")
    wait_for_blocked_clients_count(1)
    r.run("XADD", "mystream", 667, "key", "value")
    assert rd.run("read") == "{mystream {{667-0 {key value}}}}"
    rd.run("close")


@pytest.mark.xfail(reason="not implemented")
def test_blocking_xreadgroup_will_ignore_block_if_id_is_not(r: ValkeyTestClient) -> None:
    """
    test "Blocking XREADGROUP will ignore BLOCK if ID is not >" {
        set rd [valkey_deferring_client]

        # Add a entry then delete it, now stream's last_id is 666.
        r DEL mystream
        r XGROUP CREATE mystream mygroup $ MKSTREAM
        r XADD mystream 666 key value
        r XDEL mystream 666

        # Return right away instead of blocking, return the stream with an
        # empty list instead of NIL if the ID specified is not the special `>` ID.
        foreach id {0 600 666 700} {
            $rd XREADGROUP GROUP mygroup myconsumer BLOCK 0 STREAMS mystream $id
            assert_equal [$rd read] {{mystream {}}}
        }

        # After adding a new entry, `XREADGROUP BLOCK` still return the stream
        # with an empty list because the pending list is empty.
        r XADD mystream 667 key value
        foreach id {0 600 666 667 700} {
            $rd XREADGROUP GROUP mygroup myconsumer BLOCK 0 STREAMS mystream $id
            assert_equal [$rd read] {{mystream {}}}
        }

        # After we read it once, the pending list is not empty at this time,
        # pass any ID smaller than 667 will return one of the pending entry.
        set res [r XREADGROUP GROUP mygroup myconsumer BLOCK 0 STREAMS mystream >]
        assert_equal $res {{mystream {{667-0 {key value}}}}}
        foreach id {0 600 666} {
            $rd XREADGROUP GROUP mygroup myconsumer BLOCK 0 STREAMS mystream $id
            assert_equal [$rd read] {{mystream {{667-0 {key value}}}}}
        }

        # Pass ID equal or greater than 667 will return the stream with an empty list.
        foreach id {667 700} {
            $rd XREADGROUP GROUP mygroup myconsumer BLOCK 0 STREAMS mystream $id
            assert_equal [$rd read] {{mystream {}}}
        }

        # After we ACK the pending entry, return the stream with an empty list.
        r XACK mystream mygroup 667
        foreach id {0 600 666 667 700} {
            $rd XREADGROUP GROUP mygroup myconsumer BLOCK 0 STREAMS mystream $id
            assert_equal [$rd read] {{mystream {}}}
        }

        $rd close
    }
    """
    rd = ValkeyTestClient.create_from(r)
    r.run("DEL", "mystream")
    # TODO: r XGROUP CREATE mystream mygroup  MKSTREAM
    r.run("XADD", "mystream", 666, "key", "value")
    r.run("XDEL", "mystream", 666)
    foreach(
        "id",
        "0 600 666 700",
        "            $rd XREADGROUP GROUP mygroup myconsumer BLOCK 0 STREAMS mystream $id\n            assert_equal [$rd read] {{mystream {}}}\n        ",
    )
    r.run("XADD", "mystream", 667, "key", "value")
    foreach(
        "id",
        "0 600 666 667 700",
        "            $rd XREADGROUP GROUP mygroup myconsumer BLOCK 0 STREAMS mystream $id\n            assert_equal [$rd read] {{mystream {}}}\n        ",
    )
    res = r.run("XREADGROUP", "GROUP", "mygroup", "myconsumer", "BLOCK", 0, "STREAMS", "mystream", ">")
    assert res == "{mystream {{667-0 {key value}}}}"
    foreach(
        "id",
        "0 600 666",
        "            $rd XREADGROUP GROUP mygroup myconsumer BLOCK 0 STREAMS mystream $id\n            assert_equal [$rd read] {{mystream {{667-0 {key value}}}}}\n        ",
    )
    foreach(
        "id",
        "667 700",
        "            $rd XREADGROUP GROUP mygroup myconsumer BLOCK 0 STREAMS mystream $id\n            assert_equal [$rd read] {{mystream {}}}\n        ",
    )
    r.run("XACK", "mystream", "mygroup", 667)
    foreach(
        "id",
        "0 600 666 667 700",
        "            $rd XREADGROUP GROUP mygroup myconsumer BLOCK 0 STREAMS mystream $id\n            assert_equal [$rd read] {{mystream {}}}\n        ",
    )
    rd.run("close")


@pytest.mark.xfail(reason="not implemented")
def test_blocking_xreadgroup_for_stream_key_that_has_clients_blocked_on_list(r: ValkeyTestClient) -> None:
    """
    test {Blocking XREADGROUP for stream key that has clients blocked on list} {
        set rd [valkey_deferring_client]
        set rd2 [valkey_deferring_client]

        # First delete the stream
        r DEL mystream

        # now place a client blocked on non-existing key as list
        $rd2 BLPOP mystream 0

        # wait until we verify the client is blocked
        wait_for_blocked_clients_count 1

        # verify we only have 1 regular blocking key
        assert_equal 1 [getInfoProperty [r info clients] total_blocking_keys]
        assert_equal 0 [getInfoProperty [r info clients] total_blocking_keys_on_nokey]

        # now write mystream as stream
        r XADD mystream 666 key value
        r XGROUP CREATE mystream mygroup $ MKSTREAM

        # block another client on xreadgroup
        $rd XREADGROUP GROUP mygroup myconsumer BLOCK 0 STREAMS mystream ">"

        # wait until we verify we have 2 blocked clients (one for the list and one for the stream)
        wait_for_blocked_clients_count 2

        # verify we have 1 blocking key which also have clients blocked on nokey condition
        assert_equal 1 [getInfoProperty [r info clients] total_blocking_keys]
        assert_equal 1 [getInfoProperty [r info clients] total_blocking_keys_on_nokey]

        # now delete the key and verify we have no clients blocked on nokey condition
        r DEL mystream
        assert_error "NOGROUP*" {$rd read}
        assert_equal 1 [getInfoProperty [r info clients] total_blocking_keys]
        assert_equal 0 [getInfoProperty [r info clients] total_blocking_keys_on_nokey]

        # close the only left client and make sure we have no more blocking keys
        $rd2 close

        # wait until we verify we have no more blocked clients
        wait_for_blocked_clients_count 0

        assert_equal 0 [getInfoProperty [r info clients] total_blocking_keys]
        assert_equal 0 [getInfoProperty [r info clients] total_blocking_keys_on_nokey]

        $rd close
    }
    """
    rd = ValkeyTestClient.create_from(r)
    rd2 = ValkeyTestClient.create_from(r)
    r.run("DEL", "mystream")
    rd2.run("BLPOP", "mystream", 0)
    wait_for_blocked_clients_count(1)
    assert 1 == get_info_property(r.run("info", "clients"), "total_blocking_keys")
    assert 0 == get_info_property(r.run("info", "clients"), "total_blocking_keys_on_nokey")
    r.run("XADD", "mystream", 666, "key", "value")
    # TODO: r XGROUP CREATE mystream mygroup  MKSTREAM
    rd.run("XREADGROUP", "GROUP", "mygroup", "myconsumer", "BLOCK", 0, "STREAMS", "mystream", ">")
    wait_for_blocked_clients_count(2)
    assert 1 == get_info_property(r.run("info", "clients"), "total_blocking_keys")
    assert 1 == get_info_property(r.run("info", "clients"), "total_blocking_keys_on_nokey")
    r.run("DEL", "mystream")
    assert_error("NOGROUP*", "$rd read")
    assert 1 == get_info_property(r.run("info", "clients"), "total_blocking_keys")
    assert 0 == get_info_property(r.run("info", "clients"), "total_blocking_keys_on_nokey")
    rd2.run("close")
    wait_for_blocked_clients_count(0)
    assert 0 == get_info_property(r.run("info", "clients"), "total_blocking_keys")
    assert 0 == get_info_property(r.run("info", "clients"), "total_blocking_keys_on_nokey")
    rd.run("close")


@pytest.mark.xfail(reason="not implemented")
def test_blocking_xreadgroup_for_stream_key_that_has_clients_blocked_on_stream_avoid_endless_loop(
    r: ValkeyTestClient,
) -> None:
    """
    test {Blocking XREADGROUP for stream key that has clients blocked on stream - avoid endless loop} {
        r DEL mystream
        r XGROUP CREATE mystream mygroup $ MKSTREAM

        set rd1 [valkey_deferring_client]
        set rd2 [valkey_deferring_client]
        set rd3 [valkey_deferring_client]

        $rd1 xreadgroup GROUP mygroup myuser COUNT 10 BLOCK 10000 STREAMS mystream >
        $rd2 xreadgroup GROUP mygroup myuser COUNT 10 BLOCK 10000 STREAMS mystream >
        $rd3 xreadgroup GROUP mygroup myuser COUNT 10 BLOCK 10000 STREAMS mystream >

        wait_for_blocked_clients_count 3

        r xadd mystream MAXLEN 5000 * field1 value1 field2 value2 field3 value3

        $rd1 close
        $rd2 close
        $rd3 close

        assert_equal [r ping] {PONG}
    }
    """
    r.run("DEL", "mystream")
    # TODO: r XGROUP CREATE mystream mygroup  MKSTREAM
    rd1 = ValkeyTestClient.create_from(r)
    rd2 = ValkeyTestClient.create_from(r)
    rd3 = ValkeyTestClient.create_from(r)
    rd1.run("xreadgroup", "GROUP", "mygroup", "myuser", "COUNT", 10, "BLOCK", 10000, "STREAMS", "mystream", ">")
    rd2.run("xreadgroup", "GROUP", "mygroup", "myuser", "COUNT", 10, "BLOCK", 10000, "STREAMS", "mystream", ">")
    rd3.run("xreadgroup", "GROUP", "mygroup", "myuser", "COUNT", 10, "BLOCK", 10000, "STREAMS", "mystream", ">")
    wait_for_blocked_clients_count(3)
    r.run("xadd", "mystream", "MAXLEN", 5000, "*", "field1", "value1", "field2", "value2", "field3", "value3")
    rd1.run("close")
    rd2.run("close")
    rd3.run("close")
    assert r.run("ping") == "PONG"


@pytest.mark.xfail(reason="not implemented")
def test_blocking_xreadgroup_for_stream_key_that_has_clients_blocked_on_stream_reprocessing_command(
    r: ValkeyTestClient,
) -> None:
    """
    test {Blocking XREADGROUP for stream key that has clients blocked on stream - reprocessing command} {
        r DEL mystream
        r XGROUP CREATE mystream mygroup $ MKSTREAM

        set rd1 [valkey_deferring_client]
        set rd2 [valkey_deferring_client]

        $rd1 xreadgroup GROUP mygroup myuser BLOCK 0 STREAMS mystream >
        wait_for_blocked_clients_count 1

        set start [clock milliseconds]
        $rd2 xreadgroup GROUP mygroup myuser BLOCK 1000 STREAMS mystream >
        wait_for_blocked_clients_count 2

        # After a while call xadd and let rd2 re-process the command.
        after 200
        r xadd mystream * field value
        assert_equal {} [$rd2 read]
        set end [clock milliseconds]

        # Before the fix in #13004, this time would have been 1200+ (i.e. more than 1200ms),
        # now it should be 1000, but in order to avoid timing issues, we increase the range a bit.
        assert_range [expr $end-$start] 1000 1199

        $rd1 close
        $rd2 close
    }
    """
    r.run("DEL", "mystream")
    # TODO: r XGROUP CREATE mystream mygroup  MKSTREAM
    rd1 = ValkeyTestClient.create_from(r)
    rd2 = ValkeyTestClient.create_from(r)
    rd1.run("xreadgroup", "GROUP", "mygroup", "myuser", "BLOCK", 0, "STREAMS", "mystream", ">")
    wait_for_blocked_clients_count(1)
    start = clock("milliseconds")
    rd2.run("xreadgroup", "GROUP", "mygroup", "myuser", "BLOCK", 1000, "STREAMS", "mystream", ">")
    wait_for_blocked_clients_count(2)
    time.sleep(200 / 1000)
    r.run("xadd", "mystream", "*", "field", "value")
    assert "" == rd2.run("read")
    end = clock("milliseconds")
    assert_range(expr(end, "-$start"), 1000, 1199)
    rd1.run("close")
    rd2.run("close")


@pytest.mark.xfail(reason="not implemented")
def test_xgroup_destroy_should_unblock_xreadgroup_with_nogroup(r: ValkeyTestClient) -> None:
    """
    test {XGROUP DESTROY should unblock XREADGROUP with -NOGROUP} {
        r config resetstat
        r del mystream
        r XGROUP CREATE mystream mygroup $ MKSTREAM
        set rd [valkey_deferring_client]
        $rd XREADGROUP GROUP mygroup Alice BLOCK 0 STREAMS mystream ">"
        wait_for_blocked_clients_count 1
        r XGROUP DESTROY mystream mygroup
        assert_error "NOGROUP*" {$rd read}
        $rd close

        # verify command stats, error stats and error counter work on failed blocked command
        assert_match {*count=1*} [errorrstat NOGROUP r]
        assert_match {*calls=1,*,rejected_calls=0,failed_calls=1} [cmdrstat xreadgroup r]
        assert_equal [s total_error_replies] 1
    }
    """
    r.run("config", "resetstat")
    r.run("del", "mystream")
    # TODO: r XGROUP CREATE mystream mygroup  MKSTREAM
    rd = ValkeyTestClient.create_from(r)
    rd.run("XREADGROUP", "GROUP", "mygroup", "Alice", "BLOCK", 0, "STREAMS", "mystream", ">")
    wait_for_blocked_clients_count(1)
    r.run("XGROUP", "DESTROY", "mystream", "mygroup")
    assert_error("NOGROUP*", "$rd read")
    rd.run("close")
    assert fnmatch(str(errorrstat("NOGROUP", "r")), "*count=1*")
    assert fnmatch(str(cmdrstat("xreadgroup", "r")), "*calls=1,*,rejected_calls=0,failed_calls=1")
    assert s("total_error_replies") == 1


@pytest.mark.xfail(reason="not implemented")
def test_rename_can_unblock_xreadgroup_with_data(r: ValkeyTestClient) -> None:
    """
    test {RENAME can unblock XREADGROUP with data} {
        r del mystream{t}
        r XGROUP CREATE mystream{t} mygroup $ MKSTREAM
        set rd [valkey_deferring_client]
        $rd XREADGROUP GROUP mygroup Alice BLOCK 0 STREAMS mystream{t} ">"
        wait_for_blocked_clients_count 1
        r XGROUP CREATE mystream2{t} mygroup $ MKSTREAM
        r XADD mystream2{t} 100 f1 v1
        r RENAME mystream2{t} mystream{t}
        assert_equal "{mystream{t} {{100-0 {f1 v1}}}}" [$rd read] ;# mystream2{t} had mygroup before RENAME
        $rd close
    }
    """
    r.run("del", "mystream{t}")
    # TODO: r XGROUP CREATE mystream{t} mygroup  MKSTREAM
    rd = ValkeyTestClient.create_from(r)
    rd.run("XREADGROUP", "GROUP", "mygroup", "Alice", "BLOCK", 0, "STREAMS", "mystream{t}", ">")
    wait_for_blocked_clients_count(1)
    # TODO: r XGROUP CREATE mystream2{t} mygroup  MKSTREAM
    r.run("XADD", "mystream2{t}", 100, "f1", "v1")
    r.run("RENAME", "mystream2{t}", "mystream{t}")
    assert "{mystream{t} {{100-0 {f1 v1}}}}" == rd.run("read")
    rd.run("close")


@pytest.mark.xfail(reason="not implemented")
def test_rename_can_unblock_xreadgroup_with_nogroup(r: ValkeyTestClient) -> None:
    """
    test {RENAME can unblock XREADGROUP with -NOGROUP} {
        r del mystream{t}
        r XGROUP CREATE mystream{t} mygroup $ MKSTREAM
        set rd [valkey_deferring_client]
        $rd XREADGROUP GROUP mygroup Alice BLOCK 0 STREAMS mystream{t} ">"
        wait_for_blocked_clients_count 1
        r XADD mystream2{t} 100 f1 v1
        r RENAME mystream2{t} mystream{t}
        assert_error "*NOGROUP*" {$rd read} ;# mystream2{t} didn't have mygroup before RENAME
        $rd close
    }
    """
    r.run("del", "mystream{t}")
    # TODO: r XGROUP CREATE mystream{t} mygroup  MKSTREAM
    rd = ValkeyTestClient.create_from(r)
    rd.run("XREADGROUP", "GROUP", "mygroup", "Alice", "BLOCK", 0, "STREAMS", "mystream{t}", ">")
    wait_for_blocked_clients_count(1)
    r.run("XADD", "mystream2{t}", 100, "f1", "v1")
    r.run("RENAME", "mystream2{t}", "mystream{t}")
    assert_error("*NOGROUP*", "$rd read")
    rd.run("close")


def test_xclaim_can_claim_pel_items_from_another_consumer(r: ValkeyTestClient) -> None:
    """
    test {XCLAIM can claim PEL items from another consumer} {
        # Add 3 items into the stream, and create a consumer group
        r del mystream
        set id1 [r XADD mystream * a 1]
        set id2 [r XADD mystream * b 2]
        set id3 [r XADD mystream * c 3]
        r XGROUP CREATE mystream mygroup 0

        # Consumer 1 reads item 1 from the stream without acknowledgements.
        # Consumer 2 then claims pending item 1 from the PEL of consumer 1
        set reply [
            r XREADGROUP GROUP mygroup consumer1 count 1 STREAMS mystream >
        ]
        assert {[llength [lindex $reply 0 1 0 1]] == 2}
        assert {[lindex $reply 0 1 0 1] eq {a 1}}

        # make sure the entry is present in both the group, and the right consumer
        assert {[llength [r XPENDING mystream mygroup - + 10]] == 1}
        assert {[llength [r XPENDING mystream mygroup - + 10 consumer1]] == 1}
        assert {[llength [r XPENDING mystream mygroup - + 10 consumer2]] == 0}

        after 200
        set reply [
            r XCLAIM mystream mygroup consumer2 10 $id1
        ]
        assert {[llength [lindex $reply 0 1]] == 2}
        assert {[lindex $reply 0 1] eq {a 1}}

        # make sure the entry is present in both the group, and the right consumer
        assert {[llength [r XPENDING mystream mygroup - + 10]] == 1}
        assert {[llength [r XPENDING mystream mygroup - + 10 consumer1]] == 0}
        assert {[llength [r XPENDING mystream mygroup - + 10 consumer2]] == 1}

        # Consumer 1 reads another 2 items from stream
        r XREADGROUP GROUP mygroup consumer1 count 2 STREAMS mystream >
        after 200

        # Delete item 2 from the stream. Now consumer 1 has PEL that contains
        # only item 3. Try to use consumer 2 to claim the deleted item 2
        # from the PEL of consumer 1, this should be NOP
        r XDEL mystream $id2
        set reply [
            r XCLAIM mystream mygroup consumer2 10 $id2
        ]
        assert {[llength $reply] == 0}

        # Delete item 3 from the stream. Now consumer 1 has PEL that is empty.
        # Try to use consumer 2 to claim the deleted item 3 from the PEL
        # of consumer 1, this should be NOP
        after 200
        r XDEL mystream $id3
        set reply [
            r XCLAIM mystream mygroup consumer2 10 $id3
        ]
        assert {[llength $reply] == 0}
    }
    """
    r.run("del", "mystream")
    id1 = r.run("XADD", "mystream", "*", "a", 1)
    id2 = r.run("XADD", "mystream", "*", "b", 2)
    id3 = r.run("XADD", "mystream", "*", "c", 3)
    r.run("XGROUP", "CREATE", "mystream", "mygroup", 0)
    reply = r.run("XREADGROUP", "GROUP", "mygroup", "consumer1", "count", 1, "STREAMS", "mystream", ">")
    assert len(lindex(reply, 0, 1, 0, 1)) == 2
    assert lindex(reply, 0, 1, 0, 1) == "a 1"
    assert len(r.run("XPENDING", "mystream", "mygroup", "-", "+", 10)) == 1
    assert len(r.run("XPENDING", "mystream", "mygroup", "-", "+", 10, "consumer1")) == 1
    assert len(r.run("XPENDING", "mystream", "mygroup", "-", "+", 10, "consumer2")) == 0
    time.sleep(200 / 1000)
    reply = r.run("XCLAIM", "mystream", "mygroup", "consumer2", 10, id1)
    assert len(lindex(reply, 0, 1)) == 2
    assert lindex(reply, 0, 1) == "a 1"
    assert len(r.run("XPENDING", "mystream", "mygroup", "-", "+", 10)) == 1
    assert len(r.run("XPENDING", "mystream", "mygroup", "-", "+", 10, "consumer1")) == 0
    assert len(r.run("XPENDING", "mystream", "mygroup", "-", "+", 10, "consumer2")) == 1
    r.run("XREADGROUP", "GROUP", "mygroup", "consumer1", "count", 2, "STREAMS", "mystream", ">")
    time.sleep(200 / 1000)
    r.run("XDEL", "mystream", id2)
    reply = r.run("XCLAIM", "mystream", "mygroup", "consumer2", 10, id2)
    assert len(reply) == 0
    time.sleep(200 / 1000)
    r.run("XDEL", "mystream", id3)
    reply = r.run("XCLAIM", "mystream", "mygroup", "consumer2", 10, id3)
    assert len(reply) == 0


def test_xclaim_without_justid_increments_delivery_count(r: ValkeyTestClient) -> None:
    """
    test {XCLAIM without JUSTID increments delivery count} {
        # Add 3 items into the stream, and create a consumer group
        r del mystream
        set id1 [r XADD mystream * a 1]
        set id2 [r XADD mystream * b 2]
        set id3 [r XADD mystream * c 3]
        r XGROUP CREATE mystream mygroup 0

        # Consumer 1 reads item 1 from the stream without acknowledgements.
        # Consumer 2 then claims pending item 1 from the PEL of consumer 1
        set reply [
            r XREADGROUP GROUP mygroup consumer1 count 1 STREAMS mystream >
        ]
        assert {[llength [lindex $reply 0 1 0 1]] == 2}
        assert {[lindex $reply 0 1 0 1] eq {a 1}}
        after 200
        set reply [
            r XCLAIM mystream mygroup consumer2 10 $id1
        ]
        assert {[llength [lindex $reply 0 1]] == 2}
        assert {[lindex $reply 0 1] eq {a 1}}

        set reply [
            r XPENDING mystream mygroup - + 10
        ]
        assert {[llength [lindex $reply 0]] == 4}
        assert {[lindex $reply 0 3] == 2}

        # Consumer 3 then claims pending item 1 from the PEL of consumer 2 using JUSTID
        after 200
        set reply [
            r XCLAIM mystream mygroup consumer3 10 $id1 JUSTID
        ]
        assert {[llength $reply] == 1}
        assert {[lindex $reply 0] eq $id1}

        set reply [
            r XPENDING mystream mygroup - + 10
        ]
        assert {[llength [lindex $reply 0]] == 4}
        assert {[lindex $reply 0 3] == 2}
    }
    """
    r.run("del", "mystream")
    id1 = r.run("XADD", "mystream", "*", "a", 1)
    id2 = r.run("XADD", "mystream", "*", "b", 2)
    id3 = r.run("XADD", "mystream", "*", "c", 3)
    r.run("XGROUP", "CREATE", "mystream", "mygroup", 0)
    reply = r.run("XREADGROUP", "GROUP", "mygroup", "consumer1", "count", 1, "STREAMS", "mystream", ">")
    assert len(lindex(reply, 0, 1, 0, 1)) == 2
    assert lindex(reply, 0, 1, 0, 1) == "a 1"
    time.sleep(200 / 1000)
    reply = r.run("XCLAIM", "mystream", "mygroup", "consumer2", 10, id1)
    assert len(lindex(reply, 0, 1)) == 2
    assert lindex(reply, 0, 1) == "a 1"
    reply = r.run("XPENDING", "mystream", "mygroup", "-", "+", 10)
    assert len(reply[0]) == 4
    assert lindex(reply, 0, 3) == 2
    time.sleep(200 / 1000)
    reply = r.run("XCLAIM", "mystream", "mygroup", "consumer3", 10, id1, "JUSTID")
    assert len(reply) == 1
    assert reply[0] == id1
    reply = r.run("XPENDING", "mystream", "mygroup", "-", "+", 10)
    assert len(reply[0]) == 4
    assert lindex(reply, 0, 3) == 2


def test_xclaim_same_consumer(r: ValkeyTestClient) -> None:
    """
    test {XCLAIM same consumer} {
        # Add 3 items into the stream, and create a consumer group
        r del mystream
        set id1 [r XADD mystream * a 1]
        set id2 [r XADD mystream * b 2]
        set id3 [r XADD mystream * c 3]
        r XGROUP CREATE mystream mygroup 0

        set reply [r XREADGROUP GROUP mygroup consumer1 count 1 STREAMS mystream >]
        assert {[llength [lindex $reply 0 1 0 1]] == 2}
        assert {[lindex $reply 0 1 0 1] eq {a 1}}
        after 200
        # re-claim with the same consumer that already has it
        assert {[llength [r XCLAIM mystream mygroup consumer1 10 $id1]] == 1}

        # make sure the entry is still in the PEL
        set reply [r XPENDING mystream mygroup - + 10]
        assert {[llength $reply] == 1}
        assert {[lindex $reply 0 1] eq {consumer1}}
    }
    """
    r.run("del", "mystream")
    id1 = r.run("XADD", "mystream", "*", "a", 1)
    id2 = r.run("XADD", "mystream", "*", "b", 2)
    id3 = r.run("XADD", "mystream", "*", "c", 3)
    r.run("XGROUP", "CREATE", "mystream", "mygroup", 0)
    reply = r.run("XREADGROUP", "GROUP", "mygroup", "consumer1", "count", 1, "STREAMS", "mystream", ">")
    assert len(lindex(reply, 0, 1, 0, 1)) == 2
    assert lindex(reply, 0, 1, 0, 1) == "a 1"
    time.sleep(200 / 1000)
    assert len(r.run("XCLAIM", "mystream", "mygroup", "consumer1", 10, id1)) == 1
    reply = r.run("XPENDING", "mystream", "mygroup", "-", "+", 10)
    assert len(reply) == 1
    assert lindex(reply, 0, 1) == "consumer1"


def test_xautoclaim_can_claim_pel_items_from_another_consumer(r: ValkeyTestClient) -> None:
    """
    test {XAUTOCLAIM can claim PEL items from another consumer} {
        # Add 3 items into the stream, and create a consumer group
        r del mystream
        set id1 [r XADD mystream * a 1]
        set id2 [r XADD mystream * b 2]
        set id3 [r XADD mystream * c 3]
        set id4 [r XADD mystream * d 4]
        r XGROUP CREATE mystream mygroup 0

        # Consumer 1 reads item 1 from the stream without acknowledgements.
        # Consumer 2 then claims pending item 1 from the PEL of consumer 1
        set reply [r XREADGROUP GROUP mygroup consumer1 count 1 STREAMS mystream >]
        assert_equal [llength [lindex $reply 0 1 0 1]] 2
        assert_equal [lindex $reply 0 1 0 1] {a 1}
        after 200
        set reply [r XAUTOCLAIM mystream mygroup consumer2 10 - COUNT 1]
        assert_equal [llength $reply] 3
        assert_equal [lindex $reply 0] "0-0"
        assert_equal [llength [lindex $reply 1]] 1
        assert_equal [llength [lindex $reply 1 0]] 2
        assert_equal [llength [lindex $reply 1 0 1]] 2
        assert_equal [lindex $reply 1 0 1] {a 1}

        # Consumer 1 reads another 2 items from stream
        r XREADGROUP GROUP mygroup consumer1 count 3 STREAMS mystream >

        # For min-idle-time
        after 200

        # Delete item 2 from the stream. Now consumer 1 has PEL that contains
        # only item 3. Try to use consumer 2 to claim the deleted item 2
        # from the PEL of consumer 1, this should return nil
        r XDEL mystream $id2

        # id1 and id3 are self-claimed here but not id2 ('count' was set to 3)
        # we make sure id2 is indeed skipped (the cursor points to id4)
        set reply [r XAUTOCLAIM mystream mygroup consumer2 10 - COUNT 3]

        assert_equal [llength $reply] 3
        assert_equal [lindex $reply 0] $id4
        assert_equal [llength [lindex $reply 1]] 2
        assert_equal [llength [lindex $reply 1 0]] 2
        assert_equal [llength [lindex $reply 1 0 1]] 2
        assert_equal [lindex $reply 1 0 1] {a 1}
        assert_equal [lindex $reply 1 1 1] {c 3}
        assert_equal [llength [lindex $reply 2]] 1
        assert_equal [llength [lindex $reply 2 0]] 1

        # Delete item 3 from the stream. Now consumer 1 has PEL that is empty.
        # Try to use consumer 2 to claim the deleted item 3 from the PEL
        # of consumer 1, this should return nil
        after 200

        r XDEL mystream $id4

        # id1 and id3 are self-claimed here but not id2 and id4 ('count' is default 100)
        set reply [r XAUTOCLAIM mystream mygroup consumer2 10 - JUSTID]

        # we also test the JUSTID modifier here. note that, when using JUSTID,
        # deleted entries are returned in reply (consistent with XCLAIM).

        assert_equal [llength $reply] 3
        assert_equal [lindex $reply 0] {0-0}
        assert_equal [llength [lindex $reply 1]] 2
        assert_equal [lindex $reply 1 0] $id1
        assert_equal [lindex $reply 1 1] $id3
    }
    """
    r.run("del", "mystream")
    id1 = r.run("XADD", "mystream", "*", "a", 1)
    id2 = r.run("XADD", "mystream", "*", "b", 2)
    id3 = r.run("XADD", "mystream", "*", "c", 3)
    id4 = r.run("XADD", "mystream", "*", "d", 4)
    r.run("XGROUP", "CREATE", "mystream", "mygroup", 0)
    reply = r.run("XREADGROUP", "GROUP", "mygroup", "consumer1", "count", 1, "STREAMS", "mystream", ">")
    assert len(lindex(reply, 0, 1, 0, 1)) == 2
    assert lindex(reply, 0, 1, 0, 1) == "a 1"
    time.sleep(200 / 1000)
    reply = r.run("XAUTOCLAIM", "mystream", "mygroup", "consumer2", 10, "-", "COUNT", 1)
    assert len(reply) == 3
    assert reply[0] == "0-0"
    assert len(reply[1]) == 1
    assert len(lindex(reply, 1, 0)) == 2
    assert len(lindex(reply, 1, 0, 1)) == 2
    assert lindex(reply, 1, 0, 1) == "a 1"
    r.run("XREADGROUP", "GROUP", "mygroup", "consumer1", "count", 3, "STREAMS", "mystream", ">")
    time.sleep(200 / 1000)
    r.run("XDEL", "mystream", id2)
    reply = r.run("XAUTOCLAIM", "mystream", "mygroup", "consumer2", 10, "-", "COUNT", 3)
    assert len(reply) == 3
    assert reply[0] == id4
    assert len(reply[1]) == 2
    assert len(lindex(reply, 1, 0)) == 2
    assert len(lindex(reply, 1, 0, 1)) == 2
    assert lindex(reply, 1, 0, 1) == "a 1"
    assert lindex(reply, 1, 1, 1) == "c 3"
    assert len(reply[2]) == 1
    assert len(lindex(reply, 2, 0)) == 1
    time.sleep(200 / 1000)
    r.run("XDEL", "mystream", id4)
    reply = r.run("XAUTOCLAIM", "mystream", "mygroup", "consumer2", 10, "-", "JUSTID")
    assert len(reply) == 3
    assert reply[0] == "0-0"
    assert len(reply[1]) == 2
    assert lindex(reply, 1, 0) == id1
    assert lindex(reply, 1, 1) == id3


def test_xautoclaim_as_an_iterator(r: ValkeyTestClient) -> None:
    """
    test {XAUTOCLAIM as an iterator} {
        # Add 5 items into the stream, and create a consumer group
        r del mystream
        set id1 [r XADD mystream * a 1]
        set id2 [r XADD mystream * b 2]
        set id3 [r XADD mystream * c 3]
        set id4 [r XADD mystream * d 4]
        set id5 [r XADD mystream * e 5]
        r XGROUP CREATE mystream mygroup 0

        # Read 5 messages into consumer1
        r XREADGROUP GROUP mygroup consumer1 count 90 STREAMS mystream >

        # For min-idle-time
        after 200

        # Claim 2 entries
        set reply [r XAUTOCLAIM mystream mygroup consumer2 10 - COUNT 2]
        assert_equal [llength $reply] 3
        set cursor [lindex $reply 0]
        assert_equal $cursor $id3
        assert_equal [llength [lindex $reply 1]] 2
        assert_equal [llength [lindex $reply 1 0 1]] 2
        assert_equal [lindex $reply 1 0 1] {a 1}

        # Claim 2 more entries
        set reply [r XAUTOCLAIM mystream mygroup consumer2 10 $cursor COUNT 2]
        assert_equal [llength $reply] 3
        set cursor [lindex $reply 0]
        assert_equal $cursor $id5
        assert_equal [llength [lindex $reply 1]] 2
        assert_equal [llength [lindex $reply 1 0 1]] 2
        assert_equal [lindex $reply 1 0 1] {c 3}

        # Claim last entry
        set reply [r XAUTOCLAIM mystream mygroup consumer2 10 $cursor COUNT 1]
        assert_equal [llength $reply] 3
        set cursor [lindex $reply 0]
        assert_equal $cursor {0-0}
        assert_equal [llength [lindex $reply 1]] 1
        assert_equal [llength [lindex $reply 1 0 1]] 2
        assert_equal [lindex $reply 1 0 1] {e 5}
    }
    """
    r.run("del", "mystream")
    id1 = r.run("XADD", "mystream", "*", "a", 1)
    id2 = r.run("XADD", "mystream", "*", "b", 2)
    id3 = r.run("XADD", "mystream", "*", "c", 3)
    id4 = r.run("XADD", "mystream", "*", "d", 4)
    id5 = r.run("XADD", "mystream", "*", "e", 5)
    r.run("XGROUP", "CREATE", "mystream", "mygroup", 0)
    r.run("XREADGROUP", "GROUP", "mygroup", "consumer1", "count", 90, "STREAMS", "mystream", ">")
    time.sleep(200 / 1000)
    reply = r.run("XAUTOCLAIM", "mystream", "mygroup", "consumer2", 10, "-", "COUNT", 2)
    assert len(reply) == 3
    cursor = reply[0]
    assert cursor == id3
    assert len(reply[1]) == 2
    assert len(lindex(reply, 1, 0, 1)) == 2
    assert lindex(reply, 1, 0, 1) == "a 1"
    reply = r.run("XAUTOCLAIM", "mystream", "mygroup", "consumer2", 10, cursor, "COUNT", 2)
    assert len(reply) == 3
    cursor = reply[0]
    assert cursor == id5
    assert len(reply[1]) == 2
    assert len(lindex(reply, 1, 0, 1)) == 2
    assert lindex(reply, 1, 0, 1) == "c 3"
    reply = r.run("XAUTOCLAIM", "mystream", "mygroup", "consumer2", 10, cursor, "COUNT", 1)
    assert len(reply) == 3
    cursor = reply[0]
    assert cursor == "0-0"
    assert len(reply[1]) == 1
    assert len(lindex(reply, 1, 0, 1)) == 2
    assert lindex(reply, 1, 0, 1) == "e 5"


def test_xautoclaim_count_must_be_0(r: ValkeyTestClient) -> None:
    """
    test {XAUTOCLAIM COUNT must be > 0} {
        assert_error "ERR COUNT must be > 0" {r XAUTOCLAIM key group consumer 1 1 COUNT 0}
    }
    """
    with pytest.raises(Exception, match="ERR\\ COUNT\\ must\\ be\\ >\\ 0"):
        r.run("XAUTOCLAIM", "key", "group", "consumer", 1, 1, "COUNT", 0)


def test_xclaim_with_xdel(r: ValkeyTestClient) -> None:
    """
    test {XCLAIM with XDEL} {
        r DEL x
        r XADD x 1-0 f v
        r XADD x 2-0 f v
        r XADD x 3-0 f v
        r XGROUP CREATE x grp 0
        assert_equal [r XREADGROUP GROUP grp Alice STREAMS x >] {{x {{1-0 {f v}} {2-0 {f v}} {3-0 {f v}}}}}
        r XDEL x 2-0
        assert_equal [r XCLAIM x grp Bob 0 1-0 2-0 3-0] {{1-0 {f v}} {3-0 {f v}}}
        assert_equal [r XPENDING x grp - + 10 Alice] {}
    }
    """
    r.run("DEL", "x")
    r.run("XADD", "x", "1-0", "f", "v")
    r.run("XADD", "x", "2-0", "f", "v")
    r.run("XADD", "x", "3-0", "f", "v")
    r.run("XGROUP", "CREATE", "x", "grp", 0)
    assert (
        r.run("XREADGROUP", "GROUP", "grp", "Alice", "STREAMS", "x", ">") == "{x {{1-0 {f v}} {2-0 {f v}} {3-0 {f v}}}}"
    )
    r.run("XDEL", "x", "2-0")
    assert r.run("XCLAIM", "x", "grp", "Bob", 0, "1-0", "2-0", "3-0") == "{1-0 {f v}} {3-0 {f v}}"
    assert r.run("XPENDING", "x", "grp", "-", "+", 10, "Alice") == ""


def test_xclaim_with_trimming(r: ValkeyTestClient) -> None:
    """
    test {XCLAIM with trimming} {
        r DEL x
        r config set stream-node-max-entries 2
        r XADD x 1-0 f v
        r XADD x 2-0 f v
        r XADD x 3-0 f v
        r XGROUP CREATE x grp 0
        assert_equal [r XREADGROUP GROUP grp Alice STREAMS x >] {{x {{1-0 {f v}} {2-0 {f v}} {3-0 {f v}}}}}
        r XTRIM x MAXLEN 1
        assert_equal [r XCLAIM x grp Bob 0 1-0 2-0 3-0] {{3-0 {f v}}}
        assert_equal [r XPENDING x grp - + 10 Alice] {}
    }
    """
    r.run("DEL", "x")
    r.run("config", "set", "stream-node-max-entries", 2)
    r.run("XADD", "x", "1-0", "f", "v")
    r.run("XADD", "x", "2-0", "f", "v")
    r.run("XADD", "x", "3-0", "f", "v")
    r.run("XGROUP", "CREATE", "x", "grp", 0)
    assert (
        r.run("XREADGROUP", "GROUP", "grp", "Alice", "STREAMS", "x", ">") == "{x {{1-0 {f v}} {2-0 {f v}} {3-0 {f v}}}}"
    )
    r.run("XTRIM", "x", "MAXLEN", 1)
    assert r.run("XCLAIM", "x", "grp", "Bob", 0, "1-0", "2-0", "3-0") == "{3-0 {f v}}"
    assert r.run("XPENDING", "x", "grp", "-", "+", 10, "Alice") == ""


def test_xautoclaim_with_xdel(r: ValkeyTestClient) -> None:
    """
    test {XAUTOCLAIM with XDEL} {
        r DEL x
        r XADD x 1-0 f v
        r XADD x 2-0 f v
        r XADD x 3-0 f v
        r XGROUP CREATE x grp 0
        assert_equal [r XREADGROUP GROUP grp Alice STREAMS x >] {{x {{1-0 {f v}} {2-0 {f v}} {3-0 {f v}}}}}
        r XDEL x 2-0
        assert_equal [r XAUTOCLAIM x grp Bob 0 0-0] {0-0 {{1-0 {f v}} {3-0 {f v}}} 2-0}
        assert_equal [r XPENDING x grp - + 10 Alice] {}
    }
    """
    r.run("DEL", "x")
    r.run("XADD", "x", "1-0", "f", "v")
    r.run("XADD", "x", "2-0", "f", "v")
    r.run("XADD", "x", "3-0", "f", "v")
    r.run("XGROUP", "CREATE", "x", "grp", 0)
    assert (
        r.run("XREADGROUP", "GROUP", "grp", "Alice", "STREAMS", "x", ">") == "{x {{1-0 {f v}} {2-0 {f v}} {3-0 {f v}}}}"
    )
    r.run("XDEL", "x", "2-0")
    assert r.run("XAUTOCLAIM", "x", "grp", "Bob", 0, "0-0") == "0-0 {{1-0 {f v}} {3-0 {f v}}} 2-0"
    assert r.run("XPENDING", "x", "grp", "-", "+", 10, "Alice") == ""


def test_xautoclaim_with_xdel_and_count(r: ValkeyTestClient) -> None:
    """
    test {XAUTOCLAIM with XDEL and count} {
        r DEL x
        r XADD x 1-0 f v
        r XADD x 2-0 f v
        r XADD x 3-0 f v
        r XGROUP CREATE x grp 0
        assert_equal [r XREADGROUP GROUP grp Alice STREAMS x >] {{x {{1-0 {f v}} {2-0 {f v}} {3-0 {f v}}}}}
        r XDEL x 1-0
        r XDEL x 2-0
        assert_equal [r XAUTOCLAIM x grp Bob 0 0-0 COUNT 1] {2-0 {} 1-0}
        assert_equal [r XAUTOCLAIM x grp Bob 0 2-0 COUNT 1] {3-0 {} 2-0}
        assert_equal [r XAUTOCLAIM x grp Bob 0 3-0 COUNT 1] {0-0 {{3-0 {f v}}} {}}
        assert_equal [r XPENDING x grp - + 10 Alice] {}
    }
    """
    r.run("DEL", "x")
    r.run("XADD", "x", "1-0", "f", "v")
    r.run("XADD", "x", "2-0", "f", "v")
    r.run("XADD", "x", "3-0", "f", "v")
    r.run("XGROUP", "CREATE", "x", "grp", 0)
    assert (
        r.run("XREADGROUP", "GROUP", "grp", "Alice", "STREAMS", "x", ">") == "{x {{1-0 {f v}} {2-0 {f v}} {3-0 {f v}}}}"
    )
    r.run("XDEL", "x", "1-0")
    r.run("XDEL", "x", "2-0")
    assert r.run("XAUTOCLAIM", "x", "grp", "Bob", 0, "0-0", "COUNT", 1) == "2-0 {} 1-0"
    assert r.run("XAUTOCLAIM", "x", "grp", "Bob", 0, "2-0", "COUNT", 1) == "3-0 {} 2-0"
    assert r.run("XAUTOCLAIM", "x", "grp", "Bob", 0, "3-0", "COUNT", 1) == "0-0 {{3-0 {f v}}} {}"
    assert r.run("XPENDING", "x", "grp", "-", "+", 10, "Alice") == ""


def test_xautoclaim_with_out_of_range_count(r: ValkeyTestClient) -> None:
    """
    test {XAUTOCLAIM with out of range count} {
        assert_error {ERR COUNT*} {r XAUTOCLAIM x grp Bob 0 3-0 COUNT 8070450532247928833}
    }
    """
    with pytest.raises(Exception, match="ERR\\ COUNT.*"):
        r.run("XAUTOCLAIM", "x", "grp", "Bob", 0, "3-0", "COUNT", 8070450532247928833)


def test_xclaim_with_trimming_1(r: ValkeyTestClient) -> None:
    """
    test {XCLAIM with trimming} {
        r DEL x
        r config set stream-node-max-entries 2
        r XADD x 1-0 f v
        r XADD x 2-0 f v
        r XADD x 3-0 f v
        r XGROUP CREATE x grp 0
        assert_equal [r XREADGROUP GROUP grp Alice STREAMS x >] {{x {{1-0 {f v}} {2-0 {f v}} {3-0 {f v}}}}}
        r XTRIM x MAXLEN 1
        assert_equal [r XAUTOCLAIM x grp Bob 0 0-0] {0-0 {{3-0 {f v}}} {1-0 2-0}}
        assert_equal [r XPENDING x grp - + 10 Alice] {}
    }
    """
    r.run("DEL", "x")
    r.run("config", "set", "stream-node-max-entries", 2)
    r.run("XADD", "x", "1-0", "f", "v")
    r.run("XADD", "x", "2-0", "f", "v")
    r.run("XADD", "x", "3-0", "f", "v")
    r.run("XGROUP", "CREATE", "x", "grp", 0)
    assert (
        r.run("XREADGROUP", "GROUP", "grp", "Alice", "STREAMS", "x", ">") == "{x {{1-0 {f v}} {2-0 {f v}} {3-0 {f v}}}}"
    )
    r.run("XTRIM", "x", "MAXLEN", 1)
    assert r.run("XAUTOCLAIM", "x", "grp", "Bob", 0, "0-0") == "0-0 {{3-0 {f v}}} {1-0 2-0}"
    assert r.run("XPENDING", "x", "grp", "-", "+", 10, "Alice") == ""


def test_xinfo_full_output(r: ValkeyTestClient) -> None:
    """
    test {XINFO FULL output} {
        r del x
        r XADD x 100 a 1
        r XADD x 101 b 1
        r XADD x 102 c 1
        r XADD x 103 e 1
        r XADD x 104 f 1
        r XGROUP CREATE x g1 0
        r XGROUP CREATE x g2 0
        r XREADGROUP GROUP g1 Alice COUNT 1 STREAMS x >
        r XREADGROUP GROUP g1 Bob COUNT 1 STREAMS x >
        r XREADGROUP GROUP g1 Bob NOACK COUNT 1 STREAMS x >
        r XREADGROUP GROUP g2 Charlie COUNT 4 STREAMS x >
        r XDEL x 103

        set reply [r XINFO STREAM x FULL]
        assert_equal [llength $reply] 18
        assert_equal [dict get $reply length] 4
        assert_equal [dict get $reply entries] "{100-0 {a 1}} {101-0 {b 1}} {102-0 {c 1}} {104-0 {f 1}}"

        # First consumer group
        set group [lindex [dict get $reply groups] 0]
        assert_equal [dict get $group name] "g1"
        assert_equal [lindex [dict get $group pending] 0 0] "100-0"
        set consumer [lindex [dict get $group consumers] 0]
        assert_equal [dict get $consumer name] "Alice"
        assert_equal [lindex [dict get $consumer pending] 0 0] "100-0" ;# first entry in first consumer's PEL

        # Second consumer group
        set group [lindex [dict get $reply groups] 1]
        assert_equal [dict get $group name] "g2"
        set consumer [lindex [dict get $group consumers] 0]
        assert_equal [dict get $consumer name] "Charlie"
        assert_equal [lindex [dict get $consumer pending] 0 0] "100-0" ;# first entry in first consumer's PEL
        assert_equal [lindex [dict get $consumer pending] 1 0] "101-0" ;# second entry in first consumer's PEL

        set reply [r XINFO STREAM x FULL COUNT 1]
        assert_equal [llength $reply] 18
        assert_equal [dict get $reply length] 4
        assert_equal [dict get $reply entries] "{100-0 {a 1}}"
    }
    """
    r.run("del", "x")
    r.run("XADD", "x", 100, "a", 1)
    r.run("XADD", "x", 101, "b", 1)
    r.run("XADD", "x", 102, "c", 1)
    r.run("XADD", "x", 103, "e", 1)
    r.run("XADD", "x", 104, "f", 1)
    r.run("XGROUP", "CREATE", "x", "g1", 0)
    r.run("XGROUP", "CREATE", "x", "g2", 0)
    r.run("XREADGROUP", "GROUP", "g1", "Alice", "COUNT", 1, "STREAMS", "x", ">")
    r.run("XREADGROUP", "GROUP", "g1", "Bob", "COUNT", 1, "STREAMS", "x", ">")
    r.run("XREADGROUP", "GROUP", "g1", "Bob", "NOACK", "COUNT", 1, "STREAMS", "x", ">")
    r.run("XREADGROUP", "GROUP", "g2", "Charlie", "COUNT", 4, "STREAMS", "x", ">")
    r.run("XDEL", "x", 103)
    reply = r.run("XINFO", "STREAM", "x", "FULL")
    assert len(reply) == 18
    assert reply["length"] == 4
    assert reply["entries"] == "{100-0 {a 1}} {101-0 {b 1}} {102-0 {c 1}} {104-0 {f 1}}"
    group = reply["groups"][0]
    assert group["name"] == "g1"
    assert lindex(group["pending"], 0, 0) == "100-0"
    consumer = group["consumers"][0]
    assert consumer["name"] == "Alice"
    assert lindex(consumer["pending"], 0, 0) == "100-0"
    group = reply["groups"][1]
    assert group["name"] == "g2"
    consumer = group["consumers"][0]
    assert consumer["name"] == "Charlie"
    assert lindex(consumer["pending"], 0, 0) == "100-0"
    assert lindex(consumer["pending"], 1, 0) == "101-0"
    reply = r.run("XINFO", "STREAM", "x", "FULL", "COUNT", 1)
    assert len(reply) == 18
    assert reply["length"] == 4
    assert reply["entries"] == "{100-0 {a 1}}"


@pytest.mark.xfail(reason="not implemented")
def test_consumer_seen_time_and_active_time(r: ValkeyTestClient) -> None:
    """
    test {Consumer seen-time and active-time} {
        r DEL mystream
        r XGROUP CREATE mystream mygroup $ MKSTREAM
        r XREADGROUP GROUP mygroup Alice COUNT 1 STREAMS mystream >
        after 100
        set reply [r xinfo consumers mystream mygroup]
        set consumer_info [lindex $reply 0]
        assert {[dict get $consumer_info idle] >= 100} ;# consumer idle (seen-time)
        assert_equal [dict get $consumer_info inactive] "-1" ;# consumer inactive (active-time)

        r XADD mystream * f v
        r XREADGROUP GROUP mygroup Alice COUNT 1 STREAMS mystream >
        set reply [r xinfo consumers mystream mygroup]
        set consumer_info [lindex $reply 0]
        assert_equal [lindex $consumer_info 1] "Alice" ;# consumer name
        assert {[dict get $consumer_info idle] < 300} ;# consumer idle (seen-time)
        assert {[dict get $consumer_info inactive] < 300} ;# consumer inactive (active-time)

        after 100
        r XREADGROUP GROUP mygroup Alice COUNT 1 STREAMS mystream >
        set reply [r xinfo consumers mystream mygroup]
        set consumer_info [lindex $reply 0]
        assert {[dict get $consumer_info idle] < 300} ;# consumer idle (seen-time)
        assert {[dict get $consumer_info inactive] >= 100} ;# consumer inactive (active-time)


        # Simulate loading from RDB

        set reply [r XINFO STREAM mystream FULL]
        set group [lindex [dict get $reply groups] 0]
        set consumer [lindex [dict get $group consumers] 0]
        set prev_seen [dict get $consumer seen-time]
        set prev_active [dict get $consumer active-time]

        set dump [r DUMP mystream]
        r DEL mystream
        r RESTORE mystream 0 $dump

        set reply [r XINFO STREAM mystream FULL]
        set group [lindex [dict get $reply groups] 0]
        set consumer [lindex [dict get $group consumers] 0]
        assert_equal $prev_seen [dict get $consumer seen-time]
        assert_equal $prev_active [dict get $consumer active-time]
    }
    """
    r.run("DEL", "mystream")
    # TODO: r XGROUP CREATE mystream mygroup  MKSTREAM
    r.run("XREADGROUP", "GROUP", "mygroup", "Alice", "COUNT", 1, "STREAMS", "mystream", ">")
    time.sleep(100 / 1000)
    reply = r.run("xinfo", "consumers", "mystream", "mygroup")
    consumer_info = reply[0]
    assert consumer_info["idle"] >= 100
    assert consumer_info["inactive"] == "-1"
    r.run("XADD", "mystream", "*", "f", "v")
    r.run("XREADGROUP", "GROUP", "mygroup", "Alice", "COUNT", 1, "STREAMS", "mystream", ">")
    reply = r.run("xinfo", "consumers", "mystream", "mygroup")
    consumer_info = reply[0]
    assert consumer_info[1] == "Alice"
    assert consumer_info["idle"] < 300
    assert consumer_info["inactive"] < 300
    time.sleep(100 / 1000)
    r.run("XREADGROUP", "GROUP", "mygroup", "Alice", "COUNT", 1, "STREAMS", "mystream", ">")
    reply = r.run("xinfo", "consumers", "mystream", "mygroup")
    consumer_info = reply[0]
    assert consumer_info["idle"] < 300
    assert consumer_info["inactive"] >= 100
    reply = r.run("XINFO", "STREAM", "mystream", "FULL")
    group = reply["groups"][0]
    consumer = group["consumers"][0]
    prev_seen = consumer["seen-time"]
    prev_active = consumer["active-time"]
    dump = r.run("DUMP", "mystream")
    r.run("DEL", "mystream")
    r.run("RESTORE", "mystream", 0, dump)
    reply = r.run("XINFO", "STREAM", "mystream", "FULL")
    group = reply["groups"][0]
    consumer = group["consumers"][0]
    assert prev_seen == consumer["seen-time"]
    assert prev_active == consumer["active-time"]


@pytest.mark.xfail(reason="not implemented")
def test_xgroup_createconsumer_create_consumer_if_does_not_exist(r: ValkeyTestClient) -> None:
    """
    test {XGROUP CREATECONSUMER: create consumer if does not exist} {
        r del mystream
        r XGROUP CREATE mystream mygroup $ MKSTREAM
        r XADD mystream * f v

        set reply [r xinfo groups mystream]
        set group_info [lindex $reply 0]
        set n_consumers [lindex $group_info 3]
        assert_equal $n_consumers 0 ;# consumers number in cg

        # create consumer using XREADGROUP
        r XREADGROUP GROUP mygroup Alice COUNT 1 STREAMS mystream >

        set reply [r xinfo groups mystream]
        set group_info [lindex $reply 0]
        set n_consumers [lindex $group_info 3]
        assert_equal $n_consumers 1 ;# consumers number in cg

        set reply [r xinfo consumers mystream mygroup]
        set consumer_info [lindex $reply 0]
        assert_equal [lindex $consumer_info 1] "Alice" ;# consumer name

        # create group using XGROUP CREATECONSUMER when Alice already exists
        set created [r XGROUP CREATECONSUMER mystream mygroup Alice]
        assert_equal $created 0

        # create group using XGROUP CREATECONSUMER when Bob does not exist
        set created [r XGROUP CREATECONSUMER mystream mygroup Bob]
        assert_equal $created 1

        set reply [r xinfo groups mystream]
        set group_info [lindex $reply 0]
        set n_consumers [lindex $group_info 3]
        assert_equal $n_consumers 2 ;# consumers number in cg

        set reply [r xinfo consumers mystream mygroup]
        set consumer_info [lindex $reply 0]
        assert_equal [lindex $consumer_info 1] "Alice" ;# consumer name
        set consumer_info [lindex $reply 1]
        assert_equal [lindex $consumer_info 1] "Bob" ;# consumer name
    }
    """
    r.run("del", "mystream")
    # TODO: r XGROUP CREATE mystream mygroup  MKSTREAM
    r.run("XADD", "mystream", "*", "f", "v")
    reply = r.run("xinfo", "groups", "mystream")
    group_info = reply[0]
    n_consumers = group_info[3]
    assert n_consumers == 0
    r.run("XREADGROUP", "GROUP", "mygroup", "Alice", "COUNT", 1, "STREAMS", "mystream", ">")
    reply = r.run("xinfo", "groups", "mystream")
    group_info = reply[0]
    n_consumers = group_info[3]
    assert n_consumers == 1
    reply = r.run("xinfo", "consumers", "mystream", "mygroup")
    consumer_info = reply[0]
    assert consumer_info[1] == "Alice"
    created = r.run("XGROUP", "CREATECONSUMER", "mystream", "mygroup", "Alice")
    assert created == 0
    created = r.run("XGROUP", "CREATECONSUMER", "mystream", "mygroup", "Bob")
    assert created == 1
    reply = r.run("xinfo", "groups", "mystream")
    group_info = reply[0]
    n_consumers = group_info[3]
    assert n_consumers == 2
    reply = r.run("xinfo", "consumers", "mystream", "mygroup")
    consumer_info = reply[0]
    assert consumer_info[1] == "Alice"
    consumer_info = reply[1]
    assert consumer_info[1] == "Bob"


def test_xgroup_createconsumer_group_must_exist(r: ValkeyTestClient) -> None:
    """
    test {XGROUP CREATECONSUMER: group must exist} {
        r del mystream
        r XADD mystream * f v
        assert_error "*NOGROUP*" {r XGROUP CREATECONSUMER mystream mygroup consumer}
    }
    """
    r.run("del", "mystream")
    r.run("XADD", "mystream", "*", "f", "v")
    with pytest.raises(Exception, match=".*NOGROUP.*"):
        r.run("XGROUP", "CREATECONSUMER", "mystream", "mygroup", "consumer")


"""
start_server {tags {"stream needs:debug"} overrides {appendonly yes aof-use-rdb-preamble no appendfsync always}} {
    test {XREADGROUP with NOACK creates consumer} {
        r del mystream
        r XGROUP CREATE mystream mygroup $ MKSTREAM
        r XADD mystream * f1 v1
        r XREADGROUP GROUP mygroup Alice NOACK STREAMS mystream ">"
        set rd [valkey_deferring_client]
        $rd XREADGROUP GROUP mygroup Bob BLOCK 0 NOACK STREAMS mystream ">"
        wait_for_blocked_clients_count 1
        r XADD mystream * f2 v2
        set grpinfo [r xinfo groups mystream]

        r debug loadaof
        assert_equal [r xinfo groups mystream] $grpinfo
        set reply [r xinfo consumers mystream mygroup]
        set consumer_info [lindex $reply 0]
        assert_equal [lindex $consumer_info 1] "Alice" ;# consumer name
        set consumer_info [lindex $reply 1]
        assert_equal [lindex $consumer_info 1] "Bob" ;# consumer name
        $rd close
    }

    test {Consumer without PEL is present in AOF after AOFRW} {
        r del mystream
        r XGROUP CREATE mystream mygroup $ MKSTREAM
        r XADD mystream * f v
        r XREADGROUP GROUP mygroup Alice NOACK STREAMS mystream ">"
        set rd [valkey_deferring_client]
        $rd XREADGROUP GROUP mygroup Bob BLOCK 0 NOACK STREAMS mystream ">"
        wait_for_blocked_clients_count 1
        r XGROUP CREATECONSUMER mystream mygroup Charlie
        set grpinfo [lindex [r xinfo groups mystream] 0]

        r bgrewriteaof
        waitForBgrewriteaof r
        r debug loadaof

        set curr_grpinfo [lindex [r xinfo groups mystream] 0]
        assert {$curr_grpinfo == $grpinfo}
        set n_consumers [lindex $grpinfo 3]

        # All consumers are created via XREADGROUP, regardless of whether they managed
        # to read any entries or not
        assert_equal $n_consumers 3
        $rd close
    }
}
"""


def test_consumer_group_read_counter_and_lag_in_empty_streams(r: ValkeyTestClient) -> None:
    """
    test {Consumer group read counter and lag in empty streams} {
        r DEL x
        r XGROUP CREATE x g1 0 MKSTREAM

        set reply [r XINFO STREAM x FULL]
        set group [lindex [dict get $reply groups] 0]
        assert_equal [dict get $reply max-deleted-entry-id] "0-0"
        assert_equal [dict get $reply entries-added] 0
        assert_equal [dict get $group entries-read] {}
        assert_equal [dict get $group lag] 0

        r XADD x 1-0 data a
        r XDEL x 1-0

        set reply [r XINFO STREAM x FULL]
        set group [lindex [dict get $reply groups] 0]
        assert_equal [dict get $reply max-deleted-entry-id] "1-0"
        assert_equal [dict get $reply entries-added] 1
        assert_equal [dict get $group entries-read] {}
        assert_equal [dict get $group lag] 0
    }
    """
    r.run("DEL", "x")
    r.run("XGROUP", "CREATE", "x", "g1", 0, "MKSTREAM")
    reply = r.run("XINFO", "STREAM", "x", "FULL")
    group = reply["groups"][0]
    assert reply["max-deleted-entry-id"] == "0-0"
    assert reply["entries-added"] == 0
    assert group["entries-read"] == ""
    assert group["lag"] == 0
    r.run("XADD", "x", "1-0", "data", "a")
    r.run("XDEL", "x", "1-0")
    reply = r.run("XINFO", "STREAM", "x", "FULL")
    group = reply["groups"][0]
    assert reply["max-deleted-entry-id"] == "1-0"
    assert reply["entries-added"] == 1
    assert group["entries-read"] == ""
    assert group["lag"] == 0


def test_consumer_group_read_counter_and_lag_sanity(r: ValkeyTestClient) -> None:
    """
    test {Consumer group read counter and lag sanity} {
        r DEL x
        r XADD x 1-0 data a
        r XADD x 2-0 data b
        r XADD x 3-0 data c
        r XADD x 4-0 data d
        r XADD x 5-0 data e
        r XGROUP CREATE x g1 0

        set reply [r XINFO STREAM x FULL]
        set group [lindex [dict get $reply groups] 0]
        assert_equal [dict get $group entries-read] {}
        assert_equal [dict get $group lag] 5

        r XREADGROUP GROUP g1 c11 COUNT 1 STREAMS x >
        set reply [r XINFO STREAM x FULL]
        set group [lindex [dict get $reply groups] 0]
        assert_equal [dict get $group entries-read] 1
        assert_equal [dict get $group lag] 4

        r XREADGROUP GROUP g1 c12 COUNT 10 STREAMS x >
        set reply [r XINFO STREAM x FULL]
        set group [lindex [dict get $reply groups] 0]
        assert_equal [dict get $group entries-read] 5
        assert_equal [dict get $group lag] 0

        r XADD x 6-0 data f
        set reply [r XINFO STREAM x FULL]
        set group [lindex [dict get $reply groups] 0]
        assert_equal [dict get $group entries-read] 5
        assert_equal [dict get $group lag] 1

        r XADD x 7-0 data g
        r XADD x 8-0 data h
        r XADD x 9-0 data i
        r XADD x 10-0 data j
        r XREADGROUP GROUP g1 c11 COUNT 3 STREAMS x >
        r XDEL x 9-0
        # Now there is a tombstone in the stream after the consumer group last_id
        # so the lag can't be calculated
        set reply [r XINFO STREAM x FULL]
        set group [lindex [dict get $reply groups] 0]
        assert_equal [dict get $group entries-read] 8
        assert_equal [dict get $group lag] {}

        r XREADGROUP GROUP g1 c12 COUNT 1 STREAMS x >
        set reply [r XINFO STREAM x FULL]
        set group [lindex [dict get $reply groups] 0]
        assert_equal [dict get $group entries-read] 10
        assert_equal [dict get $group lag] 0
    }
    """
    r.run("DEL", "x")
    r.run("XADD", "x", "1-0", "data", "a")
    r.run("XADD", "x", "2-0", "data", "b")
    r.run("XADD", "x", "3-0", "data", "c")
    r.run("XADD", "x", "4-0", "data", "d")
    r.run("XADD", "x", "5-0", "data", "e")
    r.run("XGROUP", "CREATE", "x", "g1", 0)
    reply = r.run("XINFO", "STREAM", "x", "FULL")
    group = reply["groups"][0]
    assert group["entries-read"] == ""
    assert group["lag"] == 5
    r.run("XREADGROUP", "GROUP", "g1", "c11", "COUNT", 1, "STREAMS", "x", ">")
    reply = r.run("XINFO", "STREAM", "x", "FULL")
    group = reply["groups"][0]
    assert group["entries-read"] == 1
    assert group["lag"] == 4
    r.run("XREADGROUP", "GROUP", "g1", "c12", "COUNT", 10, "STREAMS", "x", ">")
    reply = r.run("XINFO", "STREAM", "x", "FULL")
    group = reply["groups"][0]
    assert group["entries-read"] == 5
    assert group["lag"] == 0
    r.run("XADD", "x", "6-0", "data", "f")
    reply = r.run("XINFO", "STREAM", "x", "FULL")
    group = reply["groups"][0]
    assert group["entries-read"] == 5
    assert group["lag"] == 1
    r.run("XADD", "x", "7-0", "data", "g")
    r.run("XADD", "x", "8-0", "data", "h")
    r.run("XADD", "x", "9-0", "data", "i")
    r.run("XADD", "x", "10-0", "data", "j")
    r.run("XREADGROUP", "GROUP", "g1", "c11", "COUNT", 3, "STREAMS", "x", ">")
    r.run("XDEL", "x", "9-0")
    reply = r.run("XINFO", "STREAM", "x", "FULL")
    group = reply["groups"][0]
    assert group["entries-read"] == 8
    assert group["lag"] == ""
    r.run("XREADGROUP", "GROUP", "g1", "c12", "COUNT", 1, "STREAMS", "x", ">")
    reply = r.run("XINFO", "STREAM", "x", "FULL")
    group = reply["groups"][0]
    assert group["entries-read"] == 10
    assert group["lag"] == 0


def test_consumer_group_lag_with_xdels(r: ValkeyTestClient) -> None:
    """
    test {Consumer group lag with XDELs} {
        r DEL x
        r XADD x 1-0 data a
        r XADD x 2-0 data b
        r XADD x 3-0 data c
        r XADD x 4-0 data d
        r XADD x 5-0 data e
        r XDEL x 3-0
        r XGROUP CREATE x g1 0
        r XGROUP CREATE x g2 0

        set reply [r XINFO STREAM x FULL]
        set group [lindex [dict get $reply groups] 0]
        assert_equal [dict get $group entries-read] {}
        assert_equal [dict get $group lag] {}

        r XREADGROUP GROUP g1 c11 COUNT 1 STREAMS x >
        set reply [r XINFO STREAM x FULL]
        set group [lindex [dict get $reply groups] 0]
        assert_equal [dict get $group entries-read] {}
        assert_equal [dict get $group lag] {}

        r XREADGROUP GROUP g1 c11 COUNT 1 STREAMS x >
        set reply [r XINFO STREAM x FULL]
        set group [lindex [dict get $reply groups] 0]
        assert_equal [dict get $group entries-read] {}
        assert_equal [dict get $group lag] {}

        r XREADGROUP GROUP g1 c11 COUNT 1 STREAMS x >
        set reply [r XINFO STREAM x FULL]
        set group [lindex [dict get $reply groups] 0]
        assert_equal [dict get $group entries-read] {}
        assert_equal [dict get $group lag] {}

        r XREADGROUP GROUP g1 c11 COUNT 1 STREAMS x >
        set reply [r XINFO STREAM x FULL]
        set group [lindex [dict get $reply groups] 0]
        assert_equal [dict get $group entries-read] 5
        assert_equal [dict get $group lag] 0

        r XADD x 6-0 data f
        set reply [r XINFO STREAM x FULL]
        set group [lindex [dict get $reply groups] 0]
        assert_equal [dict get $group entries-read] 5
        assert_equal [dict get $group lag] 1

        r XTRIM x MINID = 3-0
        set reply [r XINFO STREAM x FULL]
        set group [lindex [dict get $reply groups] 0]
        assert_equal [dict get $group entries-read] 5
        assert_equal [dict get $group lag] 1
        set group [lindex [dict get $reply groups] 1]
        assert_equal [dict get $group entries-read] {}
        assert_equal [dict get $group lag] 3

        r XTRIM x MINID = 5-0
        set reply [r XINFO STREAM x FULL]
        set group [lindex [dict get $reply groups] 0]
        assert_equal [dict get $group entries-read] 5
        assert_equal [dict get $group lag] 1
        set group [lindex [dict get $reply groups] 1]
        assert_equal [dict get $group entries-read] {}
        assert_equal [dict get $group lag] 2
    }
    """
    r.run("DEL", "x")
    r.run("XADD", "x", "1-0", "data", "a")
    r.run("XADD", "x", "2-0", "data", "b")
    r.run("XADD", "x", "3-0", "data", "c")
    r.run("XADD", "x", "4-0", "data", "d")
    r.run("XADD", "x", "5-0", "data", "e")
    r.run("XDEL", "x", "3-0")
    r.run("XGROUP", "CREATE", "x", "g1", 0)
    r.run("XGROUP", "CREATE", "x", "g2", 0)
    reply = r.run("XINFO", "STREAM", "x", "FULL")
    group = reply["groups"][0]
    assert group["entries-read"] == ""
    assert group["lag"] == ""
    r.run("XREADGROUP", "GROUP", "g1", "c11", "COUNT", 1, "STREAMS", "x", ">")
    reply = r.run("XINFO", "STREAM", "x", "FULL")
    group = reply["groups"][0]
    assert group["entries-read"] == ""
    assert group["lag"] == ""
    r.run("XREADGROUP", "GROUP", "g1", "c11", "COUNT", 1, "STREAMS", "x", ">")
    reply = r.run("XINFO", "STREAM", "x", "FULL")
    group = reply["groups"][0]
    assert group["entries-read"] == ""
    assert group["lag"] == ""
    r.run("XREADGROUP", "GROUP", "g1", "c11", "COUNT", 1, "STREAMS", "x", ">")
    reply = r.run("XINFO", "STREAM", "x", "FULL")
    group = reply["groups"][0]
    assert group["entries-read"] == ""
    assert group["lag"] == ""
    r.run("XREADGROUP", "GROUP", "g1", "c11", "COUNT", 1, "STREAMS", "x", ">")
    reply = r.run("XINFO", "STREAM", "x", "FULL")
    group = reply["groups"][0]
    assert group["entries-read"] == 5
    assert group["lag"] == 0
    r.run("XADD", "x", "6-0", "data", "f")
    reply = r.run("XINFO", "STREAM", "x", "FULL")
    group = reply["groups"][0]
    assert group["entries-read"] == 5
    assert group["lag"] == 1
    r.run("XTRIM", "x", "MINID", "=", "3-0")
    reply = r.run("XINFO", "STREAM", "x", "FULL")
    group = reply["groups"][0]
    assert group["entries-read"] == 5
    assert group["lag"] == 1
    group = reply["groups"][1]
    assert group["entries-read"] == ""
    assert group["lag"] == 3
    r.run("XTRIM", "x", "MINID", "=", "5-0")
    reply = r.run("XINFO", "STREAM", "x", "FULL")
    group = reply["groups"][0]
    assert group["entries-read"] == 5
    assert group["lag"] == 1
    group = reply["groups"][1]
    assert group["entries-read"] == ""
    assert group["lag"] == 2


def test_consumer_group_lag_with_xtrim(r: ValkeyTestClient) -> None:
    """
    test {Consumer group lag with XTRIM} {
        r DEL x
        r XADD x 1-0 data a
        r XADD x 2-0 data b
        r XADD x 3-0 data c
        r XADD x 4-0 data d
        r XADD x 5-0 data e
        r XDEL x 3-0
        r XGROUP CREATE x g1 0
        r XGROUP CREATE x g2 0

        set reply [r XINFO STREAM x FULL]
        set group [lindex [dict get $reply groups] 0]
        assert_equal [dict get $group entries-read] {}
        assert_equal [dict get $group lag] {}

        r XREADGROUP GROUP g1 c11 COUNT 1 STREAMS x >
        set reply [r XINFO STREAM x FULL]
        set group [lindex [dict get $reply groups] 0]
        assert_equal [dict get $group entries-read] {}
        assert_equal [dict get $group lag] {}

        r XREADGROUP GROUP g1 c11 COUNT 1 STREAMS x >
        set reply [r XINFO STREAM x FULL]
        set group [lindex [dict get $reply groups] 0]
        assert_equal [dict get $group entries-read] {}
        assert_equal [dict get $group lag] {}

        r XREADGROUP GROUP g1 c11 COUNT 1 STREAMS x >
        set reply [r XINFO STREAM x FULL]
        set group [lindex [dict get $reply groups] 0]
        assert_equal [dict get $group entries-read] {}
        assert_equal [dict get $group lag] {}

        r XREADGROUP GROUP g1 c11 COUNT 1 STREAMS x >
        set reply [r XINFO STREAM x FULL]
        set group [lindex [dict get $reply groups] 0]
        assert_equal [dict get $group entries-read] 5
        assert_equal [dict get $group lag] 0

        r XADD x 6-0 data f
        r XADD x 7-0 data g
        set reply [r XINFO STREAM x FULL]
        set group [lindex [dict get $reply groups] 0]
        assert_equal [dict get $group entries-read] 5
        assert_equal [dict get $group lag] 2

        r XTRIM x MINID = 7-0
        set reply [r XINFO STREAM x FULL]
        set group [lindex [dict get $reply groups] 0]
        assert_equal [dict get $group entries-read] 5
        assert_equal [dict get $group lag] 2
        set group [lindex [dict get $reply groups] 1]
        assert_equal [dict get $group entries-read] {}
        assert_equal [dict get $group lag] 1

        r XREADGROUP GROUP g1 c11 STREAMS x >
        set reply [r XINFO STREAM x FULL]
        set group [lindex [dict get $reply groups] 0]
        assert_equal [dict get $group entries-read] 7
        assert_equal [dict get $group lag] 0
    }
    """
    r.run("DEL", "x")
    r.run("XADD", "x", "1-0", "data", "a")
    r.run("XADD", "x", "2-0", "data", "b")
    r.run("XADD", "x", "3-0", "data", "c")
    r.run("XADD", "x", "4-0", "data", "d")
    r.run("XADD", "x", "5-0", "data", "e")
    r.run("XDEL", "x", "3-0")
    r.run("XGROUP", "CREATE", "x", "g1", 0)
    r.run("XGROUP", "CREATE", "x", "g2", 0)
    reply = r.run("XINFO", "STREAM", "x", "FULL")
    group = reply["groups"][0]
    assert group["entries-read"] == ""
    assert group["lag"] == ""
    r.run("XREADGROUP", "GROUP", "g1", "c11", "COUNT", 1, "STREAMS", "x", ">")
    reply = r.run("XINFO", "STREAM", "x", "FULL")
    group = reply["groups"][0]
    assert group["entries-read"] == ""
    assert group["lag"] == ""
    r.run("XREADGROUP", "GROUP", "g1", "c11", "COUNT", 1, "STREAMS", "x", ">")
    reply = r.run("XINFO", "STREAM", "x", "FULL")
    group = reply["groups"][0]
    assert group["entries-read"] == ""
    assert group["lag"] == ""
    r.run("XREADGROUP", "GROUP", "g1", "c11", "COUNT", 1, "STREAMS", "x", ">")
    reply = r.run("XINFO", "STREAM", "x", "FULL")
    group = reply["groups"][0]
    assert group["entries-read"] == ""
    assert group["lag"] == ""
    r.run("XREADGROUP", "GROUP", "g1", "c11", "COUNT", 1, "STREAMS", "x", ">")
    reply = r.run("XINFO", "STREAM", "x", "FULL")
    group = reply["groups"][0]
    assert group["entries-read"] == 5
    assert group["lag"] == 0
    r.run("XADD", "x", "6-0", "data", "f")
    r.run("XADD", "x", "7-0", "data", "g")
    reply = r.run("XINFO", "STREAM", "x", "FULL")
    group = reply["groups"][0]
    assert group["entries-read"] == 5
    assert group["lag"] == 2
    r.run("XTRIM", "x", "MINID", "=", "7-0")
    reply = r.run("XINFO", "STREAM", "x", "FULL")
    group = reply["groups"][0]
    assert group["entries-read"] == 5
    assert group["lag"] == 2
    group = reply["groups"][1]
    assert group["entries-read"] == ""
    assert group["lag"] == 1
    r.run("XREADGROUP", "GROUP", "g1", "c11", "STREAMS", "x", ">")
    reply = r.run("XINFO", "STREAM", "x", "FULL")
    group = reply["groups"][0]
    assert group["entries-read"] == 7
    assert group["lag"] == 0


def test_consumer_group_lag_with_xadd_trimming(r: ValkeyTestClient) -> None:
    """
    test {Consumer group lag with XADD trimming} {
        r DEL x
        r XADD x 1-0 data a
        r XADD x 2-0 data b
        r XADD x 3-0 data c
        r XADD x 4-0 data d
        r XADD x 5-0 data e
        r XDEL x 3-0
        r XGROUP CREATE x g1 0
        r XGROUP CREATE x g2 0

        set reply [r XINFO STREAM x FULL]
        set group [lindex [dict get $reply groups] 0]
        assert_equal [dict get $group entries-read] {}
        assert_equal [dict get $group lag] {}

        r XREADGROUP GROUP g1 c11 COUNT 1 STREAMS x >
        set reply [r XINFO STREAM x FULL]
        set group [lindex [dict get $reply groups] 0]
        assert_equal [dict get $group entries-read] {}
        assert_equal [dict get $group lag] {}

        r XREADGROUP GROUP g1 c11 COUNT 1 STREAMS x >
        set reply [r XINFO STREAM x FULL]
        set group [lindex [dict get $reply groups] 0]
        assert_equal [dict get $group entries-read] {}
        assert_equal [dict get $group lag] {}

        r XREADGROUP GROUP g1 c11 COUNT 1 STREAMS x >
        set reply [r XINFO STREAM x FULL]
        set group [lindex [dict get $reply groups] 0]
        assert_equal [dict get $group entries-read] {}
        assert_equal [dict get $group lag] {}

        r XREADGROUP GROUP g1 c11 COUNT 1 STREAMS x >
        set reply [r XINFO STREAM x FULL]
        set group [lindex [dict get $reply groups] 0]
        assert_equal [dict get $group entries-read] 5
        assert_equal [dict get $group lag] 0

        r XADD x 6-0 data f
        r XADD x 7-0 data g
        set reply [r XINFO STREAM x FULL]
        set group [lindex [dict get $reply groups] 0]
        assert_equal [dict get $group entries-read] 5
        assert_equal [dict get $group lag] 2

        r XADD x MINID = 7-0 8-0 data h
        set reply [r XINFO STREAM x FULL]
        set group [lindex [dict get $reply groups] 0]
        assert_equal [dict get $group entries-read] 5
        assert_equal [dict get $group lag] 3
        set group [lindex [dict get $reply groups] 1]
        assert_equal [dict get $group entries-read] {}
        assert_equal [dict get $group lag] 2

        r XREADGROUP GROUP g1 c11 STREAMS x >
        set reply [r XINFO STREAM x FULL]
        set group [lindex [dict get $reply groups] 0]
        assert_equal [dict get $group entries-read] 8
        assert_equal [dict get $group lag] 0
    }
    """
    r.run("DEL", "x")
    r.run("XADD", "x", "1-0", "data", "a")
    r.run("XADD", "x", "2-0", "data", "b")
    r.run("XADD", "x", "3-0", "data", "c")
    r.run("XADD", "x", "4-0", "data", "d")
    r.run("XADD", "x", "5-0", "data", "e")
    r.run("XDEL", "x", "3-0")
    r.run("XGROUP", "CREATE", "x", "g1", 0)
    r.run("XGROUP", "CREATE", "x", "g2", 0)
    reply = r.run("XINFO", "STREAM", "x", "FULL")
    group = reply["groups"][0]
    assert group["entries-read"] == ""
    assert group["lag"] == ""
    r.run("XREADGROUP", "GROUP", "g1", "c11", "COUNT", 1, "STREAMS", "x", ">")
    reply = r.run("XINFO", "STREAM", "x", "FULL")
    group = reply["groups"][0]
    assert group["entries-read"] == ""
    assert group["lag"] == ""
    r.run("XREADGROUP", "GROUP", "g1", "c11", "COUNT", 1, "STREAMS", "x", ">")
    reply = r.run("XINFO", "STREAM", "x", "FULL")
    group = reply["groups"][0]
    assert group["entries-read"] == ""
    assert group["lag"] == ""
    r.run("XREADGROUP", "GROUP", "g1", "c11", "COUNT", 1, "STREAMS", "x", ">")
    reply = r.run("XINFO", "STREAM", "x", "FULL")
    group = reply["groups"][0]
    assert group["entries-read"] == ""
    assert group["lag"] == ""
    r.run("XREADGROUP", "GROUP", "g1", "c11", "COUNT", 1, "STREAMS", "x", ">")
    reply = r.run("XINFO", "STREAM", "x", "FULL")
    group = reply["groups"][0]
    assert group["entries-read"] == 5
    assert group["lag"] == 0
    r.run("XADD", "x", "6-0", "data", "f")
    r.run("XADD", "x", "7-0", "data", "g")
    reply = r.run("XINFO", "STREAM", "x", "FULL")
    group = reply["groups"][0]
    assert group["entries-read"] == 5
    assert group["lag"] == 2
    r.run("XADD", "x", "MINID", "=", "7-0", "8-0", "data", "h")
    reply = r.run("XINFO", "STREAM", "x", "FULL")
    group = reply["groups"][0]
    assert group["entries-read"] == 5
    assert group["lag"] == 3
    group = reply["groups"][1]
    assert group["entries-read"] == ""
    assert group["lag"] == 2
    r.run("XREADGROUP", "GROUP", "g1", "c11", "STREAMS", "x", ">")
    reply = r.run("XINFO", "STREAM", "x", "FULL")
    group = reply["groups"][0]
    assert group["entries-read"] == 8
    assert group["lag"] == 0


@pytest.mark.xfail(reason="not implemented")
def test_loading_from_legacy_redis_v6_2_x_rdb_ver_10_persistence(r: ValkeyTestClient) -> None:
    """
    test {Loading from legacy (Redis <= v6.2.x, rdb_ver < 10) persistence} {
        # The payload was DUMPed from a v5 instance after:
        # XADD x 1-0 data a
        # XADD x 2-0 data b
        # XADD x 3-0 data c
        # XADD x 4-0 data d
        # XADD x 5-0 data e
        # XADD x 6-0 data f
        # XDEL x 3-0
        # XGROUP CREATE x g1 0
        # XGROUP CREATE x g2 0
        # XREADGROUP GROUP g1 c11 COUNT 4 STREAMS x >
        # XTRIM x MAXLEN = 2

        r DEL x
        r RESTORE x 0 "\x0f\x01\x10\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\xc3\x40\x4a\x40\x57\x16\x57\x00\x00\x00\x23\x00\x02\x01\x04\x01\x01\x01\x84\x64\x61\x74\x61\x05\x00\x01\x03\x01\x00\x20\x01\x03\x81\x61\x02\x04\x20\x0a\x00\x01\x40\x0a\x00\x62\x60\x0a\x00\x02\x40\x0a\x00\x63\x60\x0a\x40\x22\x01\x81\x64\x20\x0a\x40\x39\x20\x0a\x00\x65\x60\x0a\x00\x05\x40\x0a\x00\x66\x20\x0a\x00\xff\x02\x06\x00\x02\x02\x67\x31\x05\x00\x04\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x3e\xf7\x83\x43\x7a\x01\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x02\x00\x00\x00\x00\x00\x00\x00\x00\x3e\xf7\x83\x43\x7a\x01\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x04\x00\x00\x00\x00\x00\x00\x00\x00\x3e\xf7\x83\x43\x7a\x01\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x05\x00\x00\x00\x00\x00\x00\x00\x00\x3e\xf7\x83\x43\x7a\x01\x00\x00\x01\x01\x03\x63\x31\x31\x3e\xf7\x83\x43\x7a\x01\x00\x00\x04\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x02\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x04\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x05\x00\x00\x00\x00\x00\x00\x00\x00\x02\x67\x32\x00\x00\x00\x00\x09\x00\x3d\x52\xef\x68\x67\x52\x1d\xfa"

        set reply [r XINFO STREAM x FULL]
        assert_equal [dict get $reply max-deleted-entry-id] "0-0"
        assert_equal [dict get $reply entries-added] 2
        set group [lindex [dict get $reply groups] 0]
        assert_equal [dict get $group entries-read] 1
        assert_equal [dict get $group lag] 1
        set group [lindex [dict get $reply groups] 1]
        assert_equal [dict get $group entries-read] 0
        assert_equal [dict get $group lag] 2
    }
    """
    r.run("DEL", "x")
    # TODO: r RESTORE x 0 "\x0F\x01\x10\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\xC3\x40\x4A\x40\x57\x16\x57\x00\x00\x00\x23\x00\x02\x01\x04\x01\x01\x01\x84\x64\x61\x74\x61\x05\x00\x01\x03\x01\x00\x20\x01\x03\x81\x61\x02\x04\x20\x0A\x00\x01\x40\x0A\x00\x62\x60\x0A\x00\x02\x40\x0A\x00\x63\x60\x0A\x40\x22\x01\x81\x64\x20\x0A\x40\x39\x20\x0A\x00\x65\x60\x0A\x00\x05\x40\x0A\x00\x66\x20\x0A\x00\xFF\x02\x06\x00\x02\x02\x67\x31\x05\x00\x04\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x3E\xF7\x83\x43\x7A\x01\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x02\x00\x00\x00\x00\x00\x00\x00\x00\x3E\xF7\x83\x43\x7A\x01\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x04\x00\x00\x00\x00\x00\x00\x00\x00\x3E\xF7\x83\x43\x7A\x01\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x05\x00\x00\x00\x00\x00\x00\x00\x00\x3E\xF7\x83\x43\x7A\x01\x00\x00\x01\x01\x03\x63\x31\x31\x3E\xF7\x83\x43\x7A\x01\x00\x00\x04\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x02\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x04\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x05\x00\x00\x00\x00\x00\x00\x00\x00\x02\x67\x32\x00\x00\x00\x00\x09\x00\x3D\x52\xEF\x68\x67\x52\x1D\xFA"
    reply = r.run("XINFO", "STREAM", "x", "FULL")
    assert reply["max-deleted-entry-id"] == "0-0"
    assert reply["entries-added"] == 2
    group = reply["groups"][0]
    assert group["entries-read"] == 1
    assert group["lag"] == 1
    group = reply["groups"][1]
    assert group["entries-read"] == 0
    assert group["lag"] == 2


@pytest.mark.xfail(reason="not implemented")
def test_loading_from_legacy_redis_v7_0_x_rdb_ver_11_persistence(r: ValkeyTestClient) -> None:
    """
    test {Loading from legacy (Redis <= v7.0.x, rdb_ver < 11) persistence} {
        # The payload was DUMPed from a v7 instance after:
        # XGROUP CREATE x g $ MKSTREAM
        # XADD x 1-1 f v
        # XREADGROUP GROUP g Alice STREAMS x >

        r DEL x
        r RESTORE x 0 "\x13\x01\x10\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x01\x1d\x1d\x00\x00\x00\x0a\x00\x01\x01\x00\x01\x01\x01\x81\x66\x02\x00\x01\x02\x01\x00\x01\x00\x01\x81\x76\x02\x04\x01\xff\x01\x01\x01\x01\x01\x00\x00\x01\x01\x01\x67\x01\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x01\xf5\x5a\x71\xc7\x84\x01\x00\x00\x01\x01\x05\x41\x6c\x69\x63\x65\xf5\x5a\x71\xc7\x84\x01\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x01\x0b\x00\xa7\xa9\x14\xa5\x27\xff\x9b\x9b"
        set reply [r XINFO STREAM x FULL]
        set group [lindex [dict get $reply groups] 0]
        set consumer [lindex [dict get $group consumers] 0]
        assert_equal [dict get $consumer seen-time] [dict get $consumer active-time]
    }
    """
    r.run("DEL", "x")
    # TODO: r RESTORE x 0 "\x13\x01\x10\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x01\x1D\x1D\x00\x00\x00\x0A\x00\x01\x01\x00\x01\x01\x01\x81\x66\x02\x00\x01\x02\x01\x00\x01\x00\x01\x81\x76\x02\x04\x01\xFF\x01\x01\x01\x01\x01\x00\x00\x01\x01\x01\x67\x01\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x01\xF5\x5A\x71\xC7\x84\x01\x00\x00\x01\x01\x05\x41\x6C\x69\x63\x65\xF5\x5A\x71\xC7\x84\x01\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x01\x0B\x00\xA7\xA9\x14\xA5\x27\xFF\x9B\x9B"
    reply = r.run("XINFO", "STREAM", "x", "FULL")
    group = reply["groups"][0]
    consumer = group["consumers"][0]
    assert consumer["seen-time"] == consumer["active-time"]


"""
start_server {tags {"external:skip"}} {
    set master [srv -1 client]
    set master_host [srv -1 host]
    set master_port [srv -1 port]
    set slave [srv 0 client]

    foreach noack {0 1} {
        test "Consumer group last ID propagation to slave (NOACK=$noack)" {
            $slave slaveof $master_host $master_port
            wait_for_condition 50 100 {
                [s 0 master_link_status] eq {up}
            } else {
                fail "Replication not started."
            }

            $master del stream
            $master xadd stream * a 1
            $master xadd stream * a 2
            $master xadd stream * a 3
            $master xgroup create stream mygroup 0

            # Consume the first two items on the master
            for {set j 0} {$j < 2} {incr j} {
                if {$noack} {
                    set item [$master xreadgroup group mygroup \
                              myconsumer COUNT 1 NOACK STREAMS stream >]
                } else {
                    set item [$master xreadgroup group mygroup \
                              myconsumer COUNT 1 STREAMS stream >]
                }
                set id [lindex $item 0 1 0 0]
                if {$noack == 0} {
                    assert {[$master xack stream mygroup $id] eq "1"}
                }
            }

            wait_for_ofs_sync $master $slave

            # Turn slave into master
            $slave slaveof no one

            set item [$slave xreadgroup group mygroup myconsumer \
                      COUNT 1 STREAMS stream >]

            # The consumed entry should be the third
            set myentry [lindex $item 0 1 0 1]
            assert {$myentry eq {a 3}}
        }
    }
}
"""


"""
start_server {tags {"external:skip"}} {
    set master [srv -1 client]
    set master_host [srv -1 host]
    set master_port [srv -1 port]
    set replica [srv 0 client]

    foreach autoclaim {0 1} {
        test "Replication tests of XCLAIM with deleted entries (autoclaim=$autoclaim)" {
            $replica replicaof $master_host $master_port
            wait_for_condition 50 100 {
                [s 0 master_link_status] eq {up}
            } else {
                fail "Replication not started."
            }

            $master DEL x
            $master XADD x 1-0 f v
            $master XADD x 2-0 f v
            $master XADD x 3-0 f v
            $master XADD x 4-0 f v
            $master XADD x 5-0 f v
            $master XGROUP CREATE x grp 0
            assert_equal [$master XREADGROUP GROUP grp Alice STREAMS x >] {{x {{1-0 {f v}} {2-0 {f v}} {3-0 {f v}} {4-0 {f v}} {5-0 {f v}}}}}
            wait_for_ofs_sync $master $replica
            assert_equal [llength [$replica XPENDING x grp - + 10 Alice]] 5
            $master XDEL x 2-0
            $master XDEL x 4-0
            if {$autoclaim} {
                assert_equal [$master XAUTOCLAIM x grp Bob 0 0-0] {0-0 {{1-0 {f v}} {3-0 {f v}} {5-0 {f v}}} {2-0 4-0}}
                wait_for_ofs_sync $master $replica
                assert_equal [llength [$replica XPENDING x grp - + 10 Alice]] 0
            } else {
                assert_equal [$master XCLAIM x grp Bob 0 1-0 2-0 3-0 4-0] {{1-0 {f v}} {3-0 {f v}}}
                wait_for_ofs_sync $master $replica
                assert_equal [llength [$replica XPENDING x grp - + 10 Alice]] 1
            }
        }
    }

    test {XREADGROUP ACK would propagate entries-read} {
        $master del mystream
        $master xadd mystream * a b c d e f
        $master xgroup create mystream mygroup $
        $master xreadgroup group mygroup ryan count 1 streams mystream >
        $master xadd mystream * a1 b1 a1 b2
        $master xadd mystream * name v1 name v1
        $master xreadgroup group mygroup ryan count 1 streams mystream >
        $master xreadgroup group mygroup ryan count 1 streams mystream >

        set reply [$master XINFO STREAM mystream FULL]
        set group [lindex [dict get $reply groups] 0]
        assert_equal [dict get $group entries-read] 3
        assert_equal [dict get $group lag] 0

        # wait for replica offset
        wait_for_ofs_sync $master $replica

        set reply [$replica XINFO STREAM mystream FULL]
        set group [lindex [dict get $reply groups] 0]
        assert_equal [dict get $group entries-read] 3
        assert_equal [dict get $group lag] 0
    }
}
"""


"""
start_server {tags {"stream needs:debug"} overrides {appendonly yes aof-use-rdb-preamble no}} {
    test {Empty stream with no lastid can be rewrite into AOF correctly} {
        r XGROUP CREATE mystream group-name $ MKSTREAM
        assert {[dict get [r xinfo stream mystream] length] == 0}
        set grpinfo [r xinfo groups mystream]
        r bgrewriteaof
        waitForBgrewriteaof r
        r debug loadaof
        assert {[dict get [r xinfo stream mystream] length] == 0}
        assert_equal [r xinfo groups mystream] $grpinfo
    }
}
"""


# --- stubs for unimplemented TCL helpers ---


def assert_(*args):
    raise NotImplementedError("assert_")


def assert_error(*args):
    raise NotImplementedError("assert_error")


def assert_range(*args):
    raise NotImplementedError("assert_range")


def catch(*args):
    raise NotImplementedError("catch")


def clock(*args):
    raise NotImplementedError("clock")


def cmdrstat(*args):
    raise NotImplementedError("cmdrstat")


def errorrstat(*args):
    raise NotImplementedError("errorrstat")


def expr(*args):
    raise NotImplementedError("expr")


def foreach(*args):
    raise NotImplementedError("foreach")


def get_info_property(*args):
    raise NotImplementedError("get_info_property")


def lindex(*args):
    raise NotImplementedError("lindex")


def s(*args):
    raise NotImplementedError("s")


def wait_for_blocked_clients_count(*args):
    raise NotImplementedError("wait_for_blocked_clients_count")
