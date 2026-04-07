# ruff: noqa: PLR2004, F841, RUF043, ANN002, ANN201
import time
from fnmatch import fnmatch

import pytest

from tests.valkey_test_client import ValkeyTestClient

"""
proc streamCompareID {a b} {
    if {$a eq $b} {return 0}
    lassign [split $a -] a_ms a_seq
    lassign [split $b -] b_ms b_seq
    if {$a_ms > $b_ms} {return 1}
    if {$a_ms < $b_ms} {return -1}
    # Same ms case, compare seq.
    if {$a_seq > $b_seq} {return 1}
    if {$a_seq < $b_seq} {return -1}
}
"""


"""
proc streamNextID {id} {
    lassign [split $id -] ms seq
    incr seq
    join [list $ms $seq] -
}
"""


"""
proc streamRandomID {min_id max_id} {
    lassign [split $min_id -] min_ms min_seq
    lassign [split $max_id -] max_ms max_seq
    set delta [expr {$max_ms-$min_ms+1}]
    set ms [expr {$min_ms+[randomInt $delta]}]
    set seq [randomInt 1000]
    return $ms-$seq
}
"""


"""
proc streamSimulateXRANGE {items start end} {
    set res {}
    foreach i $items  {
        set this_id [lindex $i 0]
        if {[streamCompareID $this_id $start] >= 0} {
            if {[streamCompareID $this_id $end] <= 0} {
                lappend res $i
            }
        }
    }
    return $res
}
"""


"""
set content {}
"""

pytestmark = [pytest.mark.stream]


def test_xadd_wrong_number_of_args(r: ValkeyTestClient) -> None:
    """
    test "XADD wrong number of args" {
        assert_error {*wrong number of arguments for 'xadd' command} {r XADD mystream}
        assert_error {*wrong number of arguments for 'xadd' command} {r XADD mystream *}
        assert_error {*wrong number of arguments for 'xadd' command} {r XADD mystream * field}
    }
    """
    with pytest.raises(Exception, match=".*wrong\\ number\\ of\\ arguments\\ for\\ 'xadd'\\ command"):
        r.run("XADD", "mystream")
    with pytest.raises(Exception, match=".*wrong\\ number\\ of\\ arguments\\ for\\ 'xadd'\\ command"):
        r.run("XADD", "mystream", "*")
    with pytest.raises(Exception, match=".*wrong\\ number\\ of\\ arguments\\ for\\ 'xadd'\\ command"):
        r.run("XADD", "mystream", "*", "field")


def test_xadd_can_add_entries_into_a_stream_that_xrange_can_fetch(r: ValkeyTestClient) -> None:
    """
    test {XADD can add entries into a stream that XRANGE can fetch} {
        r XADD mystream * item 1 value a
        r XADD mystream * item 2 value b
        assert_equal 2 [r XLEN mystream]
        set items [r XRANGE mystream - +]
        assert_equal [lindex $items 0 1] {item 1 value a}
        assert_equal [lindex $items 1 1] {item 2 value b}
    }
    """
    r.run("XADD", "mystream", "*", "item", 1, "value", "a")
    r.run("XADD", "mystream", "*", "item", 2, "value", "b")
    assert 2 == r.run("XLEN", "mystream")
    items = r.run("XRANGE", "mystream", "-", "+")
    assert lindex(items, 0, 1) == "item 1 value a"
    assert lindex(items, 1, 1) == "item 2 value b"


def test_xadd_ids_are_incremental(r: ValkeyTestClient) -> None:
    """
    test {XADD IDs are incremental} {
        set id1 [r XADD mystream * item 1 value a]
        set id2 [r XADD mystream * item 2 value b]
        set id3 [r XADD mystream * item 3 value c]
        assert {[streamCompareID $id1 $id2] == -1}
        assert {[streamCompareID $id2 $id3] == -1}
    }
    """
    id1 = r.run("XADD", "mystream", "*", "item", 1, "value", "a")
    id2 = r.run("XADD", "mystream", "*", "item", 2, "value", "b")
    id3 = r.run("XADD", "mystream", "*", "item", 3, "value", "c")
    assert stream_compare_id(id1, id2) == -1
    assert stream_compare_id(id2, id3) == -1


def test_xadd_ids_are_incremental_when_ms_is_the_same_as_well(r: ValkeyTestClient) -> None:
    """
    test {XADD IDs are incremental when ms is the same as well} {
        r multi
        r XADD mystream * item 1 value a
        r XADD mystream * item 2 value b
        r XADD mystream * item 3 value c
        lassign [r exec] id1 id2 id3
        assert {[streamCompareID $id1 $id2] == -1}
        assert {[streamCompareID $id2 $id3] == -1}
    }
    """
    r.run("multi")
    r.run("XADD", "mystream", "*", "item", 1, "value", "a")
    r.run("XADD", "mystream", "*", "item", 2, "value", "b")
    r.run("XADD", "mystream", "*", "item", 3, "value", "c")
    lassign(r.run("exec"), "id1", "id2", "id3")
    assert_("[streamCompareID $id1 $id2] == -1")
    assert_("[streamCompareID $id2 $id3] == -1")


def test_xadd_ids_correctly_report_an_error_when_overflowing(r: ValkeyTestClient) -> None:
    """
    test {XADD IDs correctly report an error when overflowing} {
        r DEL mystream
        r xadd mystream 18446744073709551615-18446744073709551615 a b
        assert_error ERR* {r xadd mystream * c d}
    }
    """
    r.run("DEL", "mystream")
    r.run("xadd", "mystream", "18446744073709551615-18446744073709551615", "a", "b")
    with pytest.raises(Exception, match="ERR.*"):
        r.run("xadd", "mystream", "*", "c", "d")


def test_xadd_auto_generated_sequence_is_incremented_for_last_id(r: ValkeyTestClient) -> None:
    """
    test {XADD auto-generated sequence is incremented for last ID} {
        r DEL mystream
        set id1 [r XADD mystream 123-456 item 1 value a]
        set id2 [r XADD mystream 123-* item 2 value b]
        lassign [split $id2 -] _ seq
        assert {$seq == 457}
        assert {[streamCompareID $id1 $id2] == -1}
    }
    """
    r.run("DEL", "mystream")
    id1 = r.run("XADD", "mystream", "123-456", "item", 1, "value", "a")
    id2 = r.run("XADD", "mystream", "123-*", "item", 2, "value", "b")
    lassign(split(id2, "-"), "_", "seq")
    assert_("$seq == 457")
    assert stream_compare_id(id1, id2) == -1


def test_xadd_auto_generated_sequence_is_zero_for_future_timestamp_id(r: ValkeyTestClient) -> None:
    """
    test {XADD auto-generated sequence is zero for future timestamp ID} {
        r DEL mystream
        set id1 [r XADD mystream 123-456 item 1 value a]
        set id2 [r XADD mystream 789-* item 2 value b]
        lassign [split $id2 -] _ seq
        assert {$seq == 0}
        assert {[streamCompareID $id1 $id2] == -1}
    }
    """
    r.run("DEL", "mystream")
    id1 = r.run("XADD", "mystream", "123-456", "item", 1, "value", "a")
    id2 = r.run("XADD", "mystream", "789-*", "item", 2, "value", "b")
    lassign(split(id2, "-"), "_", "seq")
    assert_("$seq == 0")
    assert stream_compare_id(id1, id2) == -1


def test_xadd_auto_generated_sequence_can_t_be_smaller_than_last_id(r: ValkeyTestClient) -> None:
    """
    test {XADD auto-generated sequence can't be smaller than last ID} {
        r DEL mystream
        r XADD mystream 123-456 item 1 value a
        assert_error ERR* {r XADD mystream 42-* item 2 value b}
    }
    """
    r.run("DEL", "mystream")
    r.run("XADD", "mystream", "123-456", "item", 1, "value", "a")
    with pytest.raises(Exception, match="ERR.*"):
        r.run("XADD", "mystream", "42-*", "item", 2, "value", "b")


def test_xadd_auto_generated_sequence_can_t_overflow(r: ValkeyTestClient) -> None:
    """
    test {XADD auto-generated sequence can't overflow} {
        r DEL mystream
        r xadd mystream 1-18446744073709551615 a b
        assert_error ERR* {r xadd mystream 1-* c d}
    }
    """
    r.run("DEL", "mystream")
    r.run("xadd", "mystream", "1-18446744073709551615", "a", "b")
    with pytest.raises(Exception, match="ERR.*"):
        r.run("xadd", "mystream", "1-*", "c", "d")


def test_xadd_0_should_succeed(r: ValkeyTestClient) -> None:
    """
    test {XADD 0-* should succeed} {
        r DEL mystream
        set id [r xadd mystream 0-* a b]
        lassign [split $id -] _ seq
        assert {$seq == 1}
    }
    """
    r.run("DEL", "mystream")
    id = r.run("xadd", "mystream", "0-*", "a", "b")
    lassign(split(id, "-"), "_", "seq")
    assert_("$seq == 1")


def test_xadd_with_maxlen_option(r: ValkeyTestClient) -> None:
    """
    test {XADD with MAXLEN option} {
        r DEL mystream
        for {set j 0} {$j < 1000} {incr j} {
            if {rand() < 0.9} {
                r XADD mystream MAXLEN 5 * xitem $j
            } else {
                r XADD mystream MAXLEN 5 * yitem $j
            }
        }
        assert {[r xlen mystream] == 5}
        set res [r xrange mystream - +]
        set expected 995
        foreach r $res {
            assert {[lindex $r 1 1] == $expected}
            incr expected
        }
    }
    """
    r.run("DEL", "mystream")
    j = 0
    while j < 1000:
        if_(
            "rand() < 0.9",
            "                r XADD mystream MAXLEN 5 * xitem $j\n            ",
            "else",
            "                r XADD mystream MAXLEN 5 * yitem $j\n            ",
        )
        j += 1
    assert r.run("xlen", "mystream") == 5
    res = r.run("xrange", "mystream", "-", "+")
    expected = 995
    foreach("r", res, "            assert {[lindex $r 1 1] == $expected}\n            incr expected\n        ")


def test_xadd_with_maxlen_option_and_the_argument(r: ValkeyTestClient) -> None:
    """
    test {XADD with MAXLEN option and the '=' argument} {
        r DEL mystream
        for {set j 0} {$j < 1000} {incr j} {
            if {rand() < 0.9} {
                r XADD mystream MAXLEN = 5 * xitem $j
            } else {
                r XADD mystream MAXLEN = 5 * yitem $j
            }
        }
        assert {[r XLEN mystream] == 5}
    }
    """
    r.run("DEL", "mystream")
    j = 0
    while j < 1000:
        if_(
            "rand() < 0.9",
            "                r XADD mystream MAXLEN = 5 * xitem $j\n            ",
            "else",
            "                r XADD mystream MAXLEN = 5 * yitem $j\n            ",
        )
        j += 1
    assert r.run("XLEN", "mystream") == 5


def test_xadd_with_maxlen_option_and_the_argument_1(r: ValkeyTestClient) -> None:
    """
    test {XADD with MAXLEN option and the '~' argument} {
        r DEL mystream
        r config set stream-node-max-entries 100
        for {set j 0} {$j < 1000} {incr j} {
            if {rand() < 0.9} {
                r XADD mystream MAXLEN ~ 555 * xitem $j
            } else {
                r XADD mystream MAXLEN ~ 555 * yitem $j
            }
        }
        assert {[r XLEN mystream] == 600}
    }
    """
    r.run("DEL", "mystream")
    r.run("config", "set", "stream-node-max-entries", 100)
    j = 0
    while j < 1000:
        if_(
            "rand() < 0.9",
            "                r XADD mystream MAXLEN ~ 555 * xitem $j\n            ",
            "else",
            "                r XADD mystream MAXLEN ~ 555 * yitem $j\n            ",
        )
        j += 1
    assert r.run("XLEN", "mystream") == 600


def test_xadd_with_nomkstream_option(r: ValkeyTestClient) -> None:
    """
    test {XADD with NOMKSTREAM option} {
        r DEL mystream
        assert_equal "" [r XADD mystream NOMKSTREAM * item 1 value a]
        assert_equal 0 [r EXISTS mystream]
        r XADD mystream * item 1 value a
        r XADD mystream NOMKSTREAM * item 2 value b
        assert_equal 2 [r XLEN mystream]
        set items [r XRANGE mystream - +]
        assert_equal [lindex $items 0 1] {item 1 value a}
        assert_equal [lindex $items 1 1] {item 2 value b}
    }
    """
    r.run("DEL", "mystream")
    assert "" == r.run("XADD", "mystream", "NOMKSTREAM", "*", "item", 1, "value", "a")
    assert 0 == r.run("EXISTS", "mystream")
    r.run("XADD", "mystream", "*", "item", 1, "value", "a")
    r.run("XADD", "mystream", "NOMKSTREAM", "*", "item", 2, "value", "b")
    assert 2 == r.run("XLEN", "mystream")
    items = r.run("XRANGE", "mystream", "-", "+")
    assert lindex(items, 0, 1) == "item 1 value a"
    assert lindex(items, 1, 1) == "item 2 value b"


def test_xadd_with_minid_option(r: ValkeyTestClient) -> None:
    """
    test {XADD with MINID option} {
        r DEL mystream
        for {set j 1} {$j < 1001} {incr j} {
            set minid 1000
            if {$j >= 5} {
                set minid [expr {$j-5}]
            }
            if {rand() < 0.9} {
                r XADD mystream MINID $minid $j xitem $j
            } else {
                r XADD mystream MINID $minid $j yitem $j
            }
        }
        assert {[r xlen mystream] == 6}
        set res [r xrange mystream - +]
        set expected 995
        foreach r $res {
            assert {[lindex $r 1 1] == $expected}
            incr expected
        }
    }
    """
    r.run("DEL", "mystream")
    j = 1
    while j < 1001:
        minid = 1000
        if j >= 5:
            minid = expr("$j-5")
        if_(
            "rand() < 0.9",
            "                r XADD mystream MINID $minid $j xitem $j\n            ",
            "else",
            "                r XADD mystream MINID $minid $j yitem $j\n            ",
        )
        j += 1
    assert r.run("xlen", "mystream") == 6
    res = r.run("xrange", "mystream", "-", "+")
    expected = 995
    foreach("r", res, "            assert {[lindex $r 1 1] == $expected}\n            incr expected\n        ")


def test_xtrim_with_minid_option(r: ValkeyTestClient) -> None:
    """
    test {XTRIM with MINID option} {
        r DEL mystream
        r XADD mystream 1-0 f v
        r XADD mystream 2-0 f v
        r XADD mystream 3-0 f v
        r XADD mystream 4-0 f v
        r XADD mystream 5-0 f v
        r XTRIM mystream MINID = 3-0
        assert_equal [r XRANGE mystream - +] {{3-0 {f v}} {4-0 {f v}} {5-0 {f v}}}
    }
    """
    r.run("DEL", "mystream")
    r.run("XADD", "mystream", "1-0", "f", "v")
    r.run("XADD", "mystream", "2-0", "f", "v")
    r.run("XADD", "mystream", "3-0", "f", "v")
    r.run("XADD", "mystream", "4-0", "f", "v")
    r.run("XADD", "mystream", "5-0", "f", "v")
    r.run("XTRIM", "mystream", "MINID", "=", "3-0")
    assert r.run("XRANGE", "mystream", "-", "+") == "{3-0 {f v}} {4-0 {f v}} {5-0 {f v}}"


def test_xtrim_with_minid_option_big_delta_from_master_record(r: ValkeyTestClient) -> None:
    """
    test {XTRIM with MINID option, big delta from master record} {
        r DEL mystream
        r XADD mystream 1-0 f v
        r XADD mystream 1641544570597-0 f v
        r XADD mystream 1641544570597-1 f v
        r XTRIM mystream MINID 1641544570597-0
        assert_equal [r XRANGE mystream - +] {{1641544570597-0 {f v}} {1641544570597-1 {f v}}}
    }
    """
    r.run("DEL", "mystream")
    r.run("XADD", "mystream", "1-0", "f", "v")
    r.run("XADD", "mystream", "1641544570597-0", "f", "v")
    r.run("XADD", "mystream", "1641544570597-1", "f", "v")
    r.run("XTRIM", "mystream", "MINID", "1641544570597-0")
    assert r.run("XRANGE", "mystream", "-", "+") == "{1641544570597-0 {f v}} {1641544570597-1 {f v}}"


"""
proc insert_into_stream_key {key {count 10000}} {
    r multi
    for {set j 0} {$j < $count} {incr j} {
        # From time to time insert a field with a different set
        # of fields in order to stress the stream compression code.
        if {rand() < 0.9} {
            r XADD $key * item $j
        } else {
            r XADD $key * item $j otherfield foo
        }
    }
    r exec
}
"""


def test_xadd_mass_insertion_and_xlen(r: ValkeyTestClient) -> None:
    """
    test {XADD mass insertion and XLEN} {
        r DEL mystream
        insert_into_stream_key mystream

        set items [r XRANGE mystream - +]
        for {set j 0} {$j < 10000} {incr j} {
            assert {[lrange [lindex $items $j 1] 0 1] eq [list item $j]}
        }
        assert {[r xlen mystream] == $j}
    }
    """
    r.run("DEL", "mystream")
    insert_into_stream_key("mystream")
    items = r.run("XRANGE", "mystream", "-", "+")
    j = 0
    while j < 10000:
        assert lrange(lindex(items, j, 1), 0, 1) == ["item", j]
        j += 1
    assert_("[r xlen mystream] == $j")


def test_xadd_with_id_0_0(r: ValkeyTestClient) -> None:
    """
    test {XADD with ID 0-0} {
        r DEL otherstream
        catch {r XADD otherstream 0-0 k v} err
        assert {[r EXISTS otherstream] == 0}
    }
    """
    r.run("DEL", "otherstream")
    err = None
    try:
        err = r.run("XADD", "otherstream", "0-0", "k", "v")
    except Exception as _catch_err:
        err = str(_catch_err)
    assert r.run("EXISTS", "otherstream") == 0


def test_xadd_with_limit_delete_entries_no_more_than_limit(r: ValkeyTestClient) -> None:
    """
    test {XADD with LIMIT delete entries no more than limit} {
        r del yourstream
        for {set j 0} {$j < 3} {incr j} {
            r XADD yourstream * xitem v
        }
        r XADD yourstream MAXLEN ~ 0 limit 1 * xitem v
        assert {[r XLEN yourstream] == 4}
    }
    """
    r.run("del", "yourstream")
    j = 0
    while j < 3:
        r.run("XADD", "yourstream", "*", "xitem", "v")
        j += 1
    r.run("XADD", "yourstream", "MAXLEN", "~", 0, "limit", 1, "*", "xitem", "v")
    assert r.run("XLEN", "yourstream") == 4


def test_xrange_count_works_as_expected(r: ValkeyTestClient) -> None:
    """
    test {XRANGE COUNT works as expected} {
        assert {[llength [r xrange mystream - + COUNT 10]] == 10}
    }
    """
    assert len(r.run("xrange", "mystream", "-", "+", "COUNT", 10)) == 10


def test_xrevrange_count_works_as_expected(r: ValkeyTestClient) -> None:
    """
    test {XREVRANGE COUNT works as expected} {
        assert {[llength [r xrevrange mystream + - COUNT 10]] == 10}
    }
    """
    assert len(r.run("xrevrange", "mystream", "+", "-", "COUNT", 10)) == 10


def test_xrange_can_be_used_to_iterate_the_whole_stream(r: ValkeyTestClient) -> None:
    """
    test {XRANGE can be used to iterate the whole stream} {
        set last_id "-"
        set j 0
        while 1 {
            set elements [r xrange mystream $last_id + COUNT 100]
            if {[llength $elements] == 0} break
            foreach e $elements {
                assert {[lrange [lindex $e 1] 0 1] eq [list item $j]}
                incr j;
            }
            set last_id [streamNextID [lindex $elements end 0]]
        }
        assert {$j == 10000}
    }
    """
    last_id = "-"
    j = 0
    while_(
        1,
        "            set elements [r xrange mystream $last_id + COUNT 100]\n            if {[llength $elements] == 0} break\n            foreach e $elements {\n                assert {[lrange [lindex $e 1] 0 1] eq [list item $j]}\n                incr j;\n            }\n            set last_id [streamNextID [lindex $elements end 0]]\n        ",
    )
    assert j == 10000


def test_xrevrange_returns_the_reverse_of_xrange(r: ValkeyTestClient) -> None:
    """
    test {XREVRANGE returns the reverse of XRANGE} {
        assert {[r xrange mystream - +] == [lreverse [r xrevrange mystream + -]]}
    }
    """
    assert r.run("xrange", "mystream", "-", "+") == lreverse(r.run("xrevrange", "mystream", "+", "-"))


def test_xrange_exclusive_ranges(r: ValkeyTestClient) -> None:
    """
    test {XRANGE exclusive ranges} {
        set ids {0-1 0-18446744073709551615 1-0 42-0 42-42
                 18446744073709551615-18446744073709551614
                 18446744073709551615-18446744073709551615}
        set total [llength $ids]
        r multi
        r DEL vipstream
        foreach id $ids {
            r XADD vipstream $id foo bar
        }
        r exec
        assert {[llength [r xrange vipstream - +]] == $total}
        assert {[llength [r xrange vipstream ([lindex $ids 0] +]] == $total-1}
        assert {[llength [r xrange vipstream - ([lindex $ids $total-1]]] == $total-1}
        assert {[llength [r xrange vipstream (0-1 (1-0]] == 1}
        assert {[llength [r xrange vipstream (1-0 (42-42]] == 1}
        catch {r xrange vipstream (- +} e
        assert_match {ERR*} $e
        catch {r xrange vipstream - (+} e
        assert_match {ERR*} $e
        catch {r xrange vipstream (18446744073709551615-18446744073709551615 +} e
        assert_match {ERR*} $e
        catch {r xrange vipstream - (0-0} e
        assert_match {ERR*} $e
    }
    """
    ids = "0-1 0-18446744073709551615 1-0 42-0 42-42\n                 18446744073709551615-18446744073709551614\n                 18446744073709551615-18446744073709551615"
    total = len(ids)
    r.run("multi")
    r.run("DEL", "vipstream")
    foreach("id", ids, "            r XADD vipstream $id foo bar\n        ")
    r.run("exec")
    assert len(r.run("xrange", "vipstream", "-", "+")) == total
    assert_("[llength [r xrange vipstream ([lindex $ids 0] +]] == $total-1")
    assert_("[llength [r xrange vipstream - ([lindex $ids $total-1]]] == $total-1")
    assert len(r.run("xrange", "vipstream", "(0-1", "(1-0")) == 1
    assert len(r.run("xrange", "vipstream", "(1-0", "(42-42")) == 1
    e = None
    try:
        e = r.run("xrange", "vipstream", "(-", "+")
    except Exception as _catch_err:
        e = str(_catch_err)
    assert fnmatch(str(e), "ERR*")
    e = None
    try:
        e = r.run("xrange", "vipstream", "-", "(+")
    except Exception as _catch_err:
        e = str(_catch_err)
    assert fnmatch(str(e), "ERR*")
    e = None
    try:
        e = r.run("xrange", "vipstream", "(18446744073709551615-18446744073709551615", "+")
    except Exception as _catch_err:
        e = str(_catch_err)
    assert fnmatch(str(e), "ERR*")
    e = None
    try:
        e = r.run("xrange", "vipstream", "-", "(0-0")
    except Exception as _catch_err:
        e = str(_catch_err)
    assert fnmatch(str(e), "ERR*")


def test_xread_with_non_empty_stream(r: ValkeyTestClient) -> None:
    """
    test {XREAD with non empty stream} {
        set res [r XREAD COUNT 1 STREAMS mystream 0-0]
        assert {[lrange [lindex $res 0 1 0 1] 0 1] eq {item 0}}
    }
    """
    res = r.run("XREAD", "COUNT", 1, "STREAMS", "mystream", "0-0")
    assert lrange(lindex(res, 0, 1, 0, 1), 0, 1) == "item 0"


def test_non_blocking_xread_with_empty_streams(r: ValkeyTestClient) -> None:
    """
    test {Non blocking XREAD with empty streams} {
        set res [r XREAD STREAMS s1{t} s2{t} 0-0 0-0]
        assert {$res eq {}}
    }
    """
    res = r.run("XREAD", "STREAMS", "s1{t}", "s2{t}", "0-0", "0-0")
    assert res == ""


def test_xread_with_non_empty_second_stream(r: ValkeyTestClient) -> None:
    """
    test {XREAD with non empty second stream} {
        insert_into_stream_key mystream{t}
        set res [r XREAD COUNT 1 STREAMS nostream{t} mystream{t} 0-0 0-0]
        assert {[lindex $res 0 0] eq {mystream{t}}}
        assert {[lrange [lindex $res 0 1 0 1] 0 1] eq {item 0}}
    }
    """
    insert_into_stream_key("mystream{t}")
    res = r.run("XREAD", "COUNT", 1, "STREAMS", "nostream{t}", "mystream{t}", "0-0", "0-0")
    assert lindex(res, 0, 0) == "mystream{t}"
    assert lrange(lindex(res, 0, 1, 0, 1), 0, 1) == "item 0"


def test_blocking_xread_waiting_new_data(r: ValkeyTestClient) -> None:
    """
    test {Blocking XREAD waiting new data} {
        r XADD s2{t} * old abcd1234
        set rd [valkey_deferring_client]
        $rd XREAD BLOCK 20000 STREAMS s1{t} s2{t} s3{t} $ $ $
        wait_for_blocked_client
        r XADD s2{t} * new abcd1234
        set res [$rd read]
        assert {[lindex $res 0 0] eq {s2{t}}}
        assert {[lindex $res 0 1 0 1] eq {new abcd1234}}
        $rd close
    }
    """
    r.run("XADD", "s2{t}", "*", "old", "abcd1234")
    rd = ValkeyTestClient.create_from(r)
    rd.run("XREAD", "BLOCK", 20000, "STREAMS", "s1{t}", "s2{t}", "s3{t}", "$", "$", "$")
    wait_for_blocked_client()
    r.run("XADD", "s2{t}", "*", "new", "abcd1234")
    res = rd.run("read")
    assert lindex(res, 0, 0) == "s2{t}"
    assert lindex(res, 0, 1, 0, 1) == "new abcd1234"
    rd.run("close")


def test_blocking_xread_waiting_old_data(r: ValkeyTestClient) -> None:
    """
    test {Blocking XREAD waiting old data} {
        set rd [valkey_deferring_client]
        $rd XREAD BLOCK 20000 STREAMS s1{t} s2{t} s3{t} $ 0-0 $
        r XADD s2{t} * foo abcd1234
        set res [$rd read]
        assert {[lindex $res 0 0] eq {s2{t}}}
        assert {[lindex $res 0 1 0 1] eq {old abcd1234}}
        $rd close
    }
    """
    rd = ValkeyTestClient.create_from(r)
    rd.run("XREAD", "BLOCK", 20000, "STREAMS", "s1{t}", "s2{t}", "s3{t}", "$", "0-0", "$")
    r.run("XADD", "s2{t}", "*", "foo", "abcd1234")
    res = rd.run("read")
    assert lindex(res, 0, 0) == "s2{t}"
    assert lindex(res, 0, 1, 0, 1) == "old abcd1234"
    rd.run("close")


def test_blocking_xread_will_not_reply_with_an_empty_array(r: ValkeyTestClient) -> None:
    """
    test {Blocking XREAD will not reply with an empty array} {
        r del s1
        r XADD s1 666 f v
        r XADD s1 667 f2 v2
        r XDEL s1 667
        set rd [valkey_deferring_client]
        $rd XREAD BLOCK 10 STREAMS s1 666
        after 20
        assert {[$rd read] == {}} ;# before the fix, client didn't even block, but was served synchronously with {s1 {}}
        $rd close
    }
    """
    r.run("del", "s1")
    r.run("XADD", "s1", 666, "f", "v")
    r.run("XADD", "s1", 667, "f2", "v2")
    r.run("XDEL", "s1", 667)
    rd = ValkeyTestClient.create_from(r)
    rd.run("XREAD", "BLOCK", 10, "STREAMS", "s1", 666)
    time.sleep(20 / 1000)
    assert rd.run("read") == ""
    rd.run("close")


def test_blocking_xread_for_stream_that_ran_dry_issue_5299(r: ValkeyTestClient) -> None:
    """
    test "Blocking XREAD for stream that ran dry (issue #5299)" {
        set rd [valkey_deferring_client]

        # Add a entry then delete it, now stream's last_id is 666.
        r DEL mystream
        r XADD mystream 666 key value
        r XDEL mystream 666

        # Pass a ID smaller than stream's last_id, released on timeout.
        $rd XREAD BLOCK 10 STREAMS mystream 665
        assert_equal [$rd read] {}

        # Throw an error if the ID equal or smaller than the last_id.
        assert_error ERR*equal*smaller* {r XADD mystream 665 key value}
        assert_error ERR*equal*smaller* {r XADD mystream 666 key value}

        # Entered blocking state and then release because of the new entry.
        $rd XREAD BLOCK 0 STREAMS mystream 665
        wait_for_blocked_clients_count 1
        r XADD mystream 667 key value
        assert_equal [$rd read] {{mystream {{667-0 {key value}}}}}

        $rd close
    }
    """
    rd = ValkeyTestClient.create_from(r)
    r.run("DEL", "mystream")
    r.run("XADD", "mystream", 666, "key", "value")
    r.run("XDEL", "mystream", 666)
    rd.run("XREAD", "BLOCK", 10, "STREAMS", "mystream", 665)
    assert rd.run("read") == ""
    with pytest.raises(Exception, match="ERR.*equal.*smaller.*"):
        r.run("XADD", "mystream", 665, "key", "value")
    with pytest.raises(Exception, match="ERR.*equal.*smaller.*"):
        r.run("XADD", "mystream", 666, "key", "value")
    rd.run("XREAD", "BLOCK", 0, "STREAMS", "mystream", 665)
    wait_for_blocked_clients_count(1)
    r.run("XADD", "mystream", 667, "key", "value")
    assert rd.run("read") == "{mystream {{667-0 {key value}}}}"
    rd.run("close")


def test_xread_last_element_from_non_empty_stream(r: ValkeyTestClient) -> None:
    """
    test {XREAD last element from non-empty stream} {
        # should return last entry

        # add 3 entries to a stream
        r DEL lestream
        r XADD lestream 1-0 k1 v1
        r XADD lestream 2-0 k2 v2
        r XADD lestream 3-0 k3 v3

        # read the last entry
        set res [r XREAD STREAMS lestream +]

        # verify it's the last entry
        assert_equal $res {{lestream {{3-0 {k3 v3}}}}}

        # two more entries, with MAX_UINT64 for sequence number for the last one
        r XADD lestream 3-18446744073709551614 k4 v4
        r XADD lestream 3-18446744073709551615 k5 v5

        # read the new last entry
        set res [r XREAD STREAMS lestream +]

        # verify it's the last entry
        assert_equal $res {{lestream {{3-18446744073709551615 {k5 v5}}}}}
    }
    """
    r.run("DEL", "lestream")
    r.run("XADD", "lestream", "1-0", "k1", "v1")
    r.run("XADD", "lestream", "2-0", "k2", "v2")
    r.run("XADD", "lestream", "3-0", "k3", "v3")
    res = r.run("XREAD", "STREAMS", "lestream", "+")
    assert res == "{lestream {{3-0 {k3 v3}}}}"
    r.run("XADD", "lestream", "3-18446744073709551614", "k4", "v4")
    r.run("XADD", "lestream", "3-18446744073709551615", "k5", "v5")
    res = r.run("XREAD", "STREAMS", "lestream", "+")
    assert res == "{lestream {{3-18446744073709551615 {k5 v5}}}}"


def test_xread_last_element_from_empty_stream(r: ValkeyTestClient) -> None:
    """
    test {XREAD last element from empty stream} {
        # should return nil

        # make sure the stream is empty
        r DEL lestream

        # read last entry and verify nil is received
        assert_equal [r XREAD STREAMS lestream +] {}

        # add an element to the stream, than delete it
        r XADD lestream 1-0 k1 v1
        r XDEL lestream 1-0

        # verify nil is still received when reading last entry
        assert_equal [r XREAD STREAMS lestream +] {}
    }
    """
    r.run("DEL", "lestream")
    assert r.run("XREAD", "STREAMS", "lestream", "+") == ""
    r.run("XADD", "lestream", "1-0", "k1", "v1")
    r.run("XDEL", "lestream", "1-0")
    assert r.run("XREAD", "STREAMS", "lestream", "+") == ""


def test_xread_last_element_blocking_from_empty_stream(r: ValkeyTestClient) -> None:
    """
    test {XREAD last element blocking from empty stream} {
        # should block until a new entry is available

        # make sure there is no stream
        r DEL lestream

        # read last entry from stream, blocking
        set rd [valkey_deferring_client]
        $rd XREAD BLOCK 20000 STREAMS lestream +
        wait_for_blocked_client

        # add an entry to the stream
        r XADD lestream 1-0 k1 v1

        # read and verify result
        set res [$rd read]
        assert_equal $res {{lestream {{1-0 {k1 v1}}}}}
        $rd close
    }
    """
    r.run("DEL", "lestream")
    rd = ValkeyTestClient.create_from(r)
    rd.run("XREAD", "BLOCK", 20000, "STREAMS", "lestream", "+")
    wait_for_blocked_client()
    r.run("XADD", "lestream", "1-0", "k1", "v1")
    res = rd.run("read")
    assert res == "{lestream {{1-0 {k1 v1}}}}"
    rd.run("close")


def test_xread_last_element_blocking_from_non_empty_stream(r: ValkeyTestClient) -> None:
    """
    test {XREAD last element blocking from non-empty stream} {
        # should return last element immediately, w/o blocking

        # add 3 entries to a stream
        r DEL lestream
        r XADD lestream 1-0 k1 v1
        r XADD lestream 2-0 k2 v2
        r XADD lestream 3-0 k3 v3

        # read the last entry
        set res [r XREAD BLOCK 1000000 STREAMS lestream +]

        # verify it's the last entry
        assert_equal $res {{lestream {{3-0 {k3 v3}}}}}
    }
    """
    r.run("DEL", "lestream")
    r.run("XADD", "lestream", "1-0", "k1", "v1")
    r.run("XADD", "lestream", "2-0", "k2", "v2")
    r.run("XADD", "lestream", "3-0", "k3", "v3")
    res = r.run("XREAD", "BLOCK", 1000000, "STREAMS", "lestream", "+")
    assert res == "{lestream {{3-0 {k3 v3}}}}"


def test_xread_last_element_from_multiple_streams(r: ValkeyTestClient) -> None:
    """
    test {XREAD last element from multiple streams} {
        # should return last element only from non-empty streams

        # add 3 entries to one stream
        r DEL "\{lestream\}1"
        r XADD "\{lestream\}1" 1-0 k1 v1
        r XADD "\{lestream\}1" 2-0 k2 v2
        r XADD "\{lestream\}1" 3-0 k3 v3

        # add 3 entries to another stream
        r DEL "\{lestream\}2"
        r XADD "\{lestream\}2" 1-0 k1 v4
        r XADD "\{lestream\}2" 2-0 k2 v5
        r XADD "\{lestream\}2" 3-0 k3 v6

        # read last element from 3 streams (2 with enetries, 1 non-existent)
        # verify the last element from the two existing streams were returned
        set res [r XREAD STREAMS "\{lestream\}1" "\{lestream\}2" "\{lestream\}3" + + +]
        assert_equal $res {{{{lestream}1} {{3-0 {k3 v3}}}} {{{lestream}2} {{3-0 {k3 v6}}}}}
    }
    """
    r.run("DEL", "{lestream}1")
    r.run("XADD", "{lestream}1", "1-0", "k1", "v1")
    r.run("XADD", "{lestream}1", "2-0", "k2", "v2")
    r.run("XADD", "{lestream}1", "3-0", "k3", "v3")
    r.run("DEL", "{lestream}2")
    r.run("XADD", "{lestream}2", "1-0", "k1", "v4")
    r.run("XADD", "{lestream}2", "2-0", "k2", "v5")
    r.run("XADD", "{lestream}2", "3-0", "k3", "v6")
    res = r.run("XREAD", "STREAMS", "{lestream}1", "{lestream}2", "{lestream}3", "+", "+", "+")
    assert res == "{{{lestream}1} {{3-0 {k3 v3}}}} {{{lestream}2} {{3-0 {k3 v6}}}}"


def test_xread_last_element_with_count_1(r: ValkeyTestClient) -> None:
    """
    test {XREAD last element with count > 1} {
        # Should return only the last element - count has no affect here

        # add 3 entries to a stream
        r DEL lestream
        r XADD lestream 1-0 k1 v1
        r XADD lestream 2-0 k2 v2
        r XADD lestream 3-0 k3 v3

        # read the last entry
        set res [r XREAD COUNT 3 STREAMS lestream +]

        # verify only last entry was read, even though COUNT > 1
        assert_equal $res {{lestream {{3-0 {k3 v3}}}}}
    }
    """
    r.run("DEL", "lestream")
    r.run("XADD", "lestream", "1-0", "k1", "v1")
    r.run("XADD", "lestream", "2-0", "k2", "v2")
    r.run("XADD", "lestream", "3-0", "k3", "v3")
    res = r.run("XREAD", "COUNT", 3, "STREAMS", "lestream", "+")
    assert res == "{lestream {{3-0 {k3 v3}}}}"


def test_xread_xadd_del_should_not_awake_client(r: ValkeyTestClient) -> None:
    """
    test "XREAD: XADD + DEL should not awake client" {
        set rd [valkey_deferring_client]
        r del s1
        $rd XREAD BLOCK 20000 STREAMS s1 $
        wait_for_blocked_clients_count 1
        r multi
        r XADD s1 * old abcd1234
        r DEL s1
        r exec
        r XADD s1 * new abcd1234
        set res [$rd read]
        assert {[lindex $res 0 0] eq {s1}}
        assert {[lindex $res 0 1 0 1] eq {new abcd1234}}
        $rd close
    }
    """
    rd = ValkeyTestClient.create_from(r)
    r.run("del", "s1")
    rd.run("XREAD", "BLOCK", 20000, "STREAMS", "s1", "$")
    wait_for_blocked_clients_count(1)
    r.run("multi")
    r.run("XADD", "s1", "*", "old", "abcd1234")
    r.run("DEL", "s1")
    r.run("exec")
    r.run("XADD", "s1", "*", "new", "abcd1234")
    res = rd.run("read")
    assert lindex(res, 0, 0) == "s1"
    assert lindex(res, 0, 1, 0, 1) == "new abcd1234"
    rd.run("close")


def test_xread_xadd_del_lpush_should_not_awake_client(r: ValkeyTestClient) -> None:
    """
    test "XREAD: XADD + DEL + LPUSH should not awake client" {
        set rd [valkey_deferring_client]
        r del s1
        $rd XREAD BLOCK 20000 STREAMS s1 $
        wait_for_blocked_clients_count 1
        r multi
        r XADD s1 * old abcd1234
        r DEL s1
        r LPUSH s1 foo bar
        r exec
        r DEL s1
        r XADD s1 * new abcd1234
        set res [$rd read]
        assert {[lindex $res 0 0] eq {s1}}
        assert {[lindex $res 0 1 0 1] eq {new abcd1234}}
        $rd close
    }
    """
    rd = ValkeyTestClient.create_from(r)
    r.run("del", "s1")
    rd.run("XREAD", "BLOCK", 20000, "STREAMS", "s1", "$")
    wait_for_blocked_clients_count(1)
    r.run("multi")
    r.run("XADD", "s1", "*", "old", "abcd1234")
    r.run("DEL", "s1")
    r.run("LPUSH", "s1", "foo", "bar")
    r.run("exec")
    r.run("DEL", "s1")
    r.run("XADD", "s1", "*", "new", "abcd1234")
    res = rd.run("read")
    assert lindex(res, 0, 0) == "s1"
    assert lindex(res, 0, 1, 0, 1) == "new abcd1234"
    rd.run("close")


def test_xread_with_same_stream_name_multiple_times_should_work(r: ValkeyTestClient) -> None:
    """
    test {XREAD with same stream name multiple times should work} {
        r XADD s2 * old abcd1234
        set rd [valkey_deferring_client]
        $rd XREAD BLOCK 20000 STREAMS s2 s2 s2 $ $ $
        wait_for_blocked_clients_count 1
        r XADD s2 * new abcd1234
        set res [$rd read]
        assert {[lindex $res 0 0] eq {s2}}
        assert {[lindex $res 0 1 0 1] eq {new abcd1234}}
        $rd close
    }
    """
    r.run("XADD", "s2", "*", "old", "abcd1234")
    rd = ValkeyTestClient.create_from(r)
    rd.run("XREAD", "BLOCK", 20000, "STREAMS", "s2", "s2", "s2", "$", "$", "$")
    wait_for_blocked_clients_count(1)
    r.run("XADD", "s2", "*", "new", "abcd1234")
    res = rd.run("read")
    assert lindex(res, 0, 0) == "s2"
    assert lindex(res, 0, 1, 0, 1) == "new abcd1234"
    rd.run("close")


def test_xread_multiple_xadd_inside_transaction(r: ValkeyTestClient) -> None:
    """
    test {XREAD + multiple XADD inside transaction} {
        r XADD s2 * old abcd1234
        set rd [valkey_deferring_client]
        $rd XREAD BLOCK 20000 STREAMS s2 s2 s2 $ $ $
        wait_for_blocked_clients_count 1
        r MULTI
        r XADD s2 * field one
        r XADD s2 * field two
        r XADD s2 * field three
        r EXEC
        set res [$rd read]
        assert {[lindex $res 0 0] eq {s2}}
        assert {[lindex $res 0 1 0 1] eq {field one}}
        assert {[lindex $res 0 1 1 1] eq {field two}}
        $rd close
    }
    """
    r.run("XADD", "s2", "*", "old", "abcd1234")
    rd = ValkeyTestClient.create_from(r)
    rd.run("XREAD", "BLOCK", 20000, "STREAMS", "s2", "s2", "s2", "$", "$", "$")
    wait_for_blocked_clients_count(1)
    r.run("MULTI")
    r.run("XADD", "s2", "*", "field", "one")
    r.run("XADD", "s2", "*", "field", "two")
    r.run("XADD", "s2", "*", "field", "three")
    r.run("EXEC")
    res = rd.run("read")
    assert lindex(res, 0, 0) == "s2"
    assert lindex(res, 0, 1, 0, 1) == "field one"
    assert lindex(res, 0, 1, 1, 1) == "field two"
    rd.run("close")


def test_xdel_basic_test(r: ValkeyTestClient) -> None:
    """
    test {XDEL basic test} {
        r del somestream
        r xadd somestream * foo value0
        set id [r xadd somestream * foo value1]
        r xadd somestream * foo value2
        r xdel somestream $id
        assert {[r xlen somestream] == 2}
        set result [r xrange somestream - +]
        assert {[lindex $result 0 1 1] eq {value0}}
        assert {[lindex $result 1 1 1] eq {value2}}
    }
    """
    r.run("del", "somestream")
    r.run("xadd", "somestream", "*", "foo", "value0")
    id = r.run("xadd", "somestream", "*", "foo", "value1")
    r.run("xadd", "somestream", "*", "foo", "value2")
    r.run("xdel", "somestream", id)
    assert r.run("xlen", "somestream") == 2
    result = r.run("xrange", "somestream", "-", "+")
    assert lindex(result, 0, 1, 1) == "value0"
    assert lindex(result, 1, 1, 1) == "value2"


def test_xdel_multiply_id_test(r: ValkeyTestClient) -> None:
    """
    test {XDEL multiply id test} {
        r del somestream
        r xadd somestream 1-1 a 1
        r xadd somestream 1-2 b 2
        r xadd somestream 1-3 c 3
        r xadd somestream 1-4 d 4
        r xadd somestream 1-5 e 5
        assert {[r xlen somestream] == 5}
        assert {[r xdel somestream 1-1 1-4 1-5 2-1] == 3}
        assert {[r xlen somestream] == 2}
        set result [r xrange somestream - +]
        assert {[dict get [lindex $result 0 1] b] eq {2}}
        assert {[dict get [lindex $result 1 1] c] eq {3}}
    }
    """
    r.run("del", "somestream")
    r.run("xadd", "somestream", "1-1", "a", 1)
    r.run("xadd", "somestream", "1-2", "b", 2)
    r.run("xadd", "somestream", "1-3", "c", 3)
    r.run("xadd", "somestream", "1-4", "d", 4)
    r.run("xadd", "somestream", "1-5", "e", 5)
    assert r.run("xlen", "somestream") == 5
    assert r.run("xdel", "somestream", "1-1", "1-4", "1-5", "2-1") == 3
    assert r.run("xlen", "somestream") == 2
    result = r.run("xrange", "somestream", "-", "+")
    assert lindex(result, 0, 1)["b"] == "2"
    assert lindex(result, 1, 1)["c"] == "3"


def test_xdel_fuzz_test(r: ValkeyTestClient) -> None:
    """
    test {XDEL fuzz test} {
        r del somestream
        set ids {}
        set x 0; # Length of the stream
        while 1 {
            lappend ids [r xadd somestream * item $x]
            incr x
            # Add enough elements to have a few radix tree nodes inside the stream.
            if {[dict get [r xinfo stream somestream] radix-tree-keys] > 20} break
        }

        # Now remove all the elements till we reach an empty stream
        # and after every deletion, check that the stream is sane enough
        # to report the right number of elements with XRANGE: this will also
        # force accessing the whole data structure to check sanity.
        assert {[r xlen somestream] == $x}

        # We want to remove elements in random order to really test the
        # implementation in a better way.
        set ids [lshuffle $ids]
        foreach id $ids {
            assert {[r xdel somestream $id] == 1}
            incr x -1
            assert {[r xlen somestream] == $x}
            # The test would be too slow calling XRANGE for every iteration.
            # Do it every 100 removal.
            if {$x % 100 == 0} {
                set res [r xrange somestream - +]
                assert {[llength $res] == $x}
            }
        }
    }
    """
    r.run("del", "somestream")
    ids = []
    x = 0
    while_(
        1,
        "            lappend ids [r xadd somestream * item $x]\n            incr x\n            # Add enough elements to have a few radix tree nodes inside the stream.\n            if {[dict get [r xinfo stream somestream] radix-tree-keys] > 20} break\n        ",
    )
    assert r.run("xlen", "somestream") == x
    ids = lshuffle(ids)
    foreach(
        "id",
        ids,
        "            assert {[r xdel somestream $id] == 1}\n            incr x -1\n            assert {[r xlen somestream] == $x}\n            # The test would be too slow calling XRANGE for every iteration.\n            # Do it every 100 removal.\n            if {$x % 100 == 0} {\n                set res [r xrange somestream - +]\n                assert {[llength $res] == $x}\n            }\n        ",
    )


def test_xrange_fuzzing(r: ValkeyTestClient) -> None:
    """
    test {XRANGE fuzzing} {
        set items [r XRANGE mystream{t} - +]
        set low_id [lindex $items 0 0]
        set high_id [lindex $items end 0]
        for {set j 0} {$j < 100} {incr j} {
            set start [streamRandomID $low_id $high_id]
            set end [streamRandomID $low_id $high_id]
            set range [r xrange mystream{t} $start $end]
            set tcl_range [streamSimulateXRANGE $items $start $end]
            if {$range ne $tcl_range} {
                puts "*** WARNING *** - XRANGE fuzzing mismatch: $start - $end"
                puts "---"
                puts "XRANGE: '$range'"
                puts "---"
                puts "TCL: '$tcl_range'"
                puts "---"
                fail "XRANGE fuzzing failed, check logs for details"
            }
        }
    }
    """
    items = r.run("XRANGE", "mystream{t}", "-", "+")
    low_id = lindex(items, 0, 0)
    high_id = lindex(items, "end", 0)
    j = 0
    while j < 100:
        start = stream_random_id(low_id, high_id)
        end = stream_random_id(low_id, high_id)
        range = r.run("xrange", "mystream{t}", start, end)
        tcl_range = stream_simulate_xrange(items, start, end)
        if range != tcl_range:
            fail("XRANGE fuzzing failed, check logs for details")
        j += 1


def test_xrevrange_regression_test_for_issue_5006(r: ValkeyTestClient) -> None:
    """
    test {XREVRANGE regression test for issue #5006} {
        # Add non compressed entries
        r xadd teststream 1234567891230 key1 value1
        r xadd teststream 1234567891240 key2 value2
        r xadd teststream 1234567891250 key3 value3

        # Add SAMEFIELD compressed entries
        r xadd teststream2 1234567891230 key1 value1
        r xadd teststream2 1234567891240 key1 value2
        r xadd teststream2 1234567891250 key1 value3

        assert_equal [r xrevrange teststream 1234567891245 -] {{1234567891240-0 {key2 value2}} {1234567891230-0 {key1 value1}}}

        assert_equal [r xrevrange teststream2 1234567891245 -] {{1234567891240-0 {key1 value2}} {1234567891230-0 {key1 value1}}}
    }
    """
    r.run("xadd", "teststream", 1234567891230, "key1", "value1")
    r.run("xadd", "teststream", 1234567891240, "key2", "value2")
    r.run("xadd", "teststream", 1234567891250, "key3", "value3")
    r.run("xadd", "teststream2", 1234567891230, "key1", "value1")
    r.run("xadd", "teststream2", 1234567891240, "key1", "value2")
    r.run("xadd", "teststream2", 1234567891250, "key1", "value3")
    assert (
        r.run("xrevrange", "teststream", 1234567891245, "-")
        == "{1234567891240-0 {key2 value2}} {1234567891230-0 {key1 value1}}"
    )
    assert (
        r.run("xrevrange", "teststream2", 1234567891245, "-")
        == "{1234567891240-0 {key1 value2}} {1234567891230-0 {key1 value1}}"
    )


def test_xread_streamid_edge_no_blocking(r: ValkeyTestClient) -> None:
    """
    test {XREAD streamID edge (no-blocking)} {
        r del x
        r XADD x 1-1 f v
        r XADD x 1-18446744073709551615 f v
        r XADD x 2-1 f v
        set res [r XREAD BLOCK 0 STREAMS x 1-18446744073709551615]
        assert {[lindex $res 0 1 0] == {2-1 {f v}}}
    }
    """
    r.run("del", "x")
    r.run("XADD", "x", "1-1", "f", "v")
    r.run("XADD", "x", "1-18446744073709551615", "f", "v")
    r.run("XADD", "x", "2-1", "f", "v")
    res = r.run("XREAD", "BLOCK", 0, "STREAMS", "x", "1-18446744073709551615")
    assert lindex(res, 0, 1, 0) == "2-1 {f v}"


def test_xread_streamid_edge_blocking(r: ValkeyTestClient) -> None:
    """
    test {XREAD streamID edge (blocking)} {
        r del x
        set rd [valkey_deferring_client]
        $rd XREAD BLOCK 0 STREAMS x 1-18446744073709551615
        wait_for_blocked_clients_count 1
        r XADD x 1-1 f v
        r XADD x 1-18446744073709551615 f v
        r XADD x 2-1 f v
        set res [$rd read]
        assert {[lindex $res 0 1 0] == {2-1 {f v}}}
        $rd close
    }
    """
    r.run("del", "x")
    rd = ValkeyTestClient.create_from(r)
    rd.run("XREAD", "BLOCK", 0, "STREAMS", "x", "1-18446744073709551615")
    wait_for_blocked_clients_count(1)
    r.run("XADD", "x", "1-1", "f", "v")
    r.run("XADD", "x", "1-18446744073709551615", "f", "v")
    r.run("XADD", "x", "2-1", "f", "v")
    res = rd.run("read")
    assert lindex(res, 0, 1, 0) == "2-1 {f v}"
    rd.run("close")


def test_xadd_streamid_edge(r: ValkeyTestClient) -> None:
    """
    test {XADD streamID edge} {
        r del x
        r XADD x 2577343934890-18446744073709551615 f v ;# we need the timestamp to be in the future
        r XADD x * f2 v2
        assert_equal [r XRANGE x - +] {{2577343934890-18446744073709551615 {f v}} {2577343934891-0 {f2 v2}}}
    }
    """
    r.run("del", "x")
    r.run("XADD", "x", "2577343934890-18446744073709551615", "f", "v")
    r.run("XADD", "x", "*", "f2", "v2")
    assert r.run("XRANGE", "x", "-", "+") == "{2577343934890-18446744073709551615 {f v}} {2577343934891-0 {f2 v2}}"


def test_xtrim_with_maxlen_option_basic_test(r: ValkeyTestClient) -> None:
    """
    test {XTRIM with MAXLEN option basic test} {
        r DEL mystream
        for {set j 0} {$j < 1000} {incr j} {
            if {rand() < 0.9} {
                r XADD mystream * xitem $j
            } else {
                r XADD mystream * yitem $j
            }
        }
        r XTRIM mystream MAXLEN 666
        assert {[r XLEN mystream] == 666}
        r XTRIM mystream MAXLEN = 555
        assert {[r XLEN mystream] == 555}
        r XTRIM mystream MAXLEN ~ 444
        assert {[r XLEN mystream] == 500}
        r XTRIM mystream MAXLEN ~ 400
        assert {[r XLEN mystream] == 400}
    }
    """
    r.run("DEL", "mystream")
    j = 0
    while j < 1000:
        if_(
            "rand() < 0.9",
            "                r XADD mystream * xitem $j\n            ",
            "else",
            "                r XADD mystream * yitem $j\n            ",
        )
        j += 1
    r.run("XTRIM", "mystream", "MAXLEN", 666)
    assert r.run("XLEN", "mystream") == 666
    r.run("XTRIM", "mystream", "MAXLEN", "=", 555)
    assert r.run("XLEN", "mystream") == 555
    r.run("XTRIM", "mystream", "MAXLEN", "~", 444)
    assert r.run("XLEN", "mystream") == 500
    r.run("XTRIM", "mystream", "MAXLEN", "~", 400)
    assert r.run("XLEN", "mystream") == 400


def test_xadd_with_limit_consecutive_calls(r: ValkeyTestClient) -> None:
    """
    test {XADD with LIMIT consecutive calls} {
        r del mystream
        r config set stream-node-max-entries 10
        for {set j 0} {$j < 100} {incr j} {
            r XADD mystream * xitem v
        }
        r XADD mystream MAXLEN ~ 55 LIMIT 30 * xitem v
        assert {[r xlen mystream] == 71}
        r XADD mystream MAXLEN ~ 55 LIMIT 30 * xitem v
        assert {[r xlen mystream] == 62}
        r config set stream-node-max-entries 100
    }
    """
    r.run("del", "mystream")
    r.run("config", "set", "stream-node-max-entries", 10)
    j = 0
    while j < 100:
        r.run("XADD", "mystream", "*", "xitem", "v")
        j += 1
    r.run("XADD", "mystream", "MAXLEN", "~", 55, "LIMIT", 30, "*", "xitem", "v")
    assert r.run("xlen", "mystream") == 71
    r.run("XADD", "mystream", "MAXLEN", "~", 55, "LIMIT", 30, "*", "xitem", "v")
    assert r.run("xlen", "mystream") == 62
    r.run("config", "set", "stream-node-max-entries", 100)


def test_xtrim_with_is_limited(r: ValkeyTestClient) -> None:
    """
    test {XTRIM with ~ is limited} {
        r del mystream
        r config set stream-node-max-entries 1
        for {set j 0} {$j < 102} {incr j} {
            r XADD mystream * xitem v
        }
        r XTRIM mystream MAXLEN ~ 1
        assert {[r xlen mystream] == 2}
        r config set stream-node-max-entries 100
    }
    """
    r.run("del", "mystream")
    r.run("config", "set", "stream-node-max-entries", 1)
    j = 0
    while j < 102:
        r.run("XADD", "mystream", "*", "xitem", "v")
        j += 1
    r.run("XTRIM", "mystream", "MAXLEN", "~", 1)
    assert r.run("xlen", "mystream") == 2
    r.run("config", "set", "stream-node-max-entries", 100)


def test_xtrim_without_is_not_limited(r: ValkeyTestClient) -> None:
    """
    test {XTRIM without ~ is not limited} {
        r del mystream
        r config set stream-node-max-entries 1
        for {set j 0} {$j < 102} {incr j} {
            r XADD mystream * xitem v
        }
        r XTRIM mystream MAXLEN 1
        assert {[r xlen mystream] == 1}
        r config set stream-node-max-entries 100
    }
    """
    r.run("del", "mystream")
    r.run("config", "set", "stream-node-max-entries", 1)
    j = 0
    while j < 102:
        r.run("XADD", "mystream", "*", "xitem", "v")
        j += 1
    r.run("XTRIM", "mystream", "MAXLEN", 1)
    assert r.run("xlen", "mystream") == 1
    r.run("config", "set", "stream-node-max-entries", 100)


def test_xtrim_without_and_with_limit(r: ValkeyTestClient) -> None:
    """
    test {XTRIM without ~ and with LIMIT} {
        r del mystream
        r config set stream-node-max-entries 1
        for {set j 0} {$j < 102} {incr j} {
            r XADD mystream * xitem v
        }
        assert_error ERR* {r XTRIM mystream MAXLEN 1 LIMIT 30}
    }
    """
    r.run("del", "mystream")
    r.run("config", "set", "stream-node-max-entries", 1)
    j = 0
    while j < 102:
        r.run("XADD", "mystream", "*", "xitem", "v")
        j += 1
    with pytest.raises(Exception, match="ERR.*"):
        r.run("XTRIM", "mystream", "MAXLEN", 1, "LIMIT", 30)


def test_xtrim_with_limit_delete_entries_no_more_than_limit(r: ValkeyTestClient) -> None:
    """
    test {XTRIM with LIMIT delete entries no more than limit} {
        r del mystream
        r config set stream-node-max-entries 2
        for {set j 0} {$j < 3} {incr j} {
            r XADD mystream * xitem v
        }
        assert {[r XTRIM mystream MAXLEN ~ 0 LIMIT 1] == 0}
        assert {[r XTRIM mystream MAXLEN ~ 0 LIMIT 2] == 2}
    }
    """
    r.run("del", "mystream")
    r.run("config", "set", "stream-node-max-entries", 2)
    j = 0
    while j < 3:
        r.run("XADD", "mystream", "*", "xitem", "v")
        j += 1
    assert r.run("XTRIM", "mystream", "MAXLEN", "~", 0, "LIMIT", 1) == 0
    assert r.run("XTRIM", "mystream", "MAXLEN", "~", 0, "LIMIT", 2) == 2


pytestmark = [pytest.mark.stream_needs_debug]


def test_xadd_with_maxlen_xlen_can_propagate_correctly(r: ValkeyTestClient) -> None:
    """
    test {XADD with MAXLEN > xlen can propagate correctly} {
        for {set j 0} {$j < 100} {incr j} {
            r XADD mystream * xitem v
        }
        r XADD mystream MAXLEN 200 * xitem v
        incr j
        assert {[r xlen mystream] == $j}
        r debug loadaof
        r XADD mystream * xitem v
        incr j
        assert {[r xlen mystream] == $j}
    }
    """
    j = 0
    while j < 100:
        r.run("XADD", "mystream", "*", "xitem", "v")
        j += 1
    r.run("XADD", "mystream", "MAXLEN", 200, "*", "xitem", "v")
    incr("j")
    assert_("[r xlen mystream] == $j")
    r.run("debug", "loadaof")
    r.run("XADD", "mystream", "*", "xitem", "v")
    incr("j")
    assert_("[r xlen mystream] == $j")


pytestmark = [pytest.mark.stream_needs_debug]


def test_xadd_with_minid_lastid_can_propagate_correctly(r: ValkeyTestClient) -> None:
    """
    test {XADD with MINID > lastid can propagate correctly} {
        for {set j 0} {$j < 100} {incr j} {
            set id [expr {$j+1}]
            r XADD mystream $id xitem v
        }
        r XADD mystream MINID 1 * xitem v
        incr j
        assert {[r xlen mystream] == $j}
        r debug loadaof
        r XADD mystream * xitem v
        incr j
        assert {[r xlen mystream] == $j}
    }
    """
    j = 0
    while j < 100:
        id = expr("$j+1")
        r.run("XADD", "mystream", id, "xitem", "v")
        j += 1
    r.run("XADD", "mystream", "MINID", 1, "*", "xitem", "v")
    incr("j")
    assert_("[r xlen mystream] == $j")
    r.run("debug", "loadaof")
    r.run("XADD", "mystream", "*", "xitem", "v")
    incr("j")
    assert_("[r xlen mystream] == $j")


pytestmark = [pytest.mark.stream_needs_debug]


@pytest.mark.xfail(reason="not implemented")
def test_xadd_with_maxlen_can_propagate_correctly(r: ValkeyTestClient) -> None:
    """
    test {XADD with ~ MAXLEN can propagate correctly} {
        for {set j 0} {$j < 100} {incr j} {
            r XADD mystream * xitem v
        }
        r XADD mystream MAXLEN ~ $j * xitem v
        incr j
        assert {[r xlen mystream] == $j}
        r config set stream-node-max-entries 1
        r debug loadaof
        r XADD mystream * xitem v
        incr j
        assert {[r xlen mystream] == $j}
    }
    """
    j = 0
    while j < 100:
        r.run("XADD", "mystream", "*", "xitem", "v")
        j += 1
    # TODO: r XADD mystream MAXLEN ~ j * xitem v
    incr("j")
    assert_("[r xlen mystream] == $j")
    r.run("config", "set", "stream-node-max-entries", 1)
    r.run("debug", "loadaof")
    r.run("XADD", "mystream", "*", "xitem", "v")
    incr("j")
    assert_("[r xlen mystream] == $j")


pytestmark = [pytest.mark.stream_needs_debug]


def test_xadd_with_maxlen_and_limit_can_propagate_correctly(r: ValkeyTestClient) -> None:
    """
    test {XADD with ~ MAXLEN and LIMIT can propagate correctly} {
        for {set j 0} {$j < 100} {incr j} {
            r XADD mystream * xitem v
        }
        r XADD mystream MAXLEN ~ 55 LIMIT 30 * xitem v
        assert {[r xlen mystream] == 71}
        r config set stream-node-max-entries 1
        r debug loadaof
        r XADD mystream * xitem v
        assert {[r xlen mystream] == 72}
    }
    """
    j = 0
    while j < 100:
        r.run("XADD", "mystream", "*", "xitem", "v")
        j += 1
    r.run("XADD", "mystream", "MAXLEN", "~", 55, "LIMIT", 30, "*", "xitem", "v")
    assert r.run("xlen", "mystream") == 71
    r.run("config", "set", "stream-node-max-entries", 1)
    r.run("debug", "loadaof")
    r.run("XADD", "mystream", "*", "xitem", "v")
    assert r.run("xlen", "mystream") == 72


pytestmark = [pytest.mark.stream_needs_debug]


@pytest.mark.xfail(reason="not implemented")
def test_xadd_with_minid_can_propagate_correctly(r: ValkeyTestClient) -> None:
    """
    test {XADD with ~ MINID can propagate correctly} {
        for {set j 0} {$j < 100} {incr j} {
            set id [expr {$j+1}]
            r XADD mystream $id xitem v
        }
        r XADD mystream MINID ~ $j * xitem v
        incr j
        assert {[r xlen mystream] == $j}
        r config set stream-node-max-entries 1
        r debug loadaof
        r XADD mystream * xitem v
        incr j
        assert {[r xlen mystream] == $j}
    }
    """
    j = 0
    while j < 100:
        id = expr("$j+1")
        r.run("XADD", "mystream", id, "xitem", "v")
        j += 1
    # TODO: r XADD mystream MINID ~ j * xitem v
    incr("j")
    assert_("[r xlen mystream] == $j")
    r.run("config", "set", "stream-node-max-entries", 1)
    r.run("debug", "loadaof")
    r.run("XADD", "mystream", "*", "xitem", "v")
    incr("j")
    assert_("[r xlen mystream] == $j")


pytestmark = [pytest.mark.stream_needs_debug]


def test_xadd_with_minid_and_limit_can_propagate_correctly(r: ValkeyTestClient) -> None:
    """
    test {XADD with ~ MINID and LIMIT can propagate correctly} {
        for {set j 0} {$j < 100} {incr j} {
            set id [expr {$j+1}]
            r XADD mystream $id xitem v
        }
        r XADD mystream MINID ~ 55 LIMIT 30 * xitem v
        assert {[r xlen mystream] == 71}
        r config set stream-node-max-entries 1
        r debug loadaof
        r XADD mystream * xitem v
        assert {[r xlen mystream] == 72}
    }
    """
    j = 0
    while j < 100:
        id = expr("$j+1")
        r.run("XADD", "mystream", id, "xitem", "v")
        j += 1
    r.run("XADD", "mystream", "MINID", "~", 55, "LIMIT", 30, "*", "xitem", "v")
    assert r.run("xlen", "mystream") == 71
    r.run("config", "set", "stream-node-max-entries", 1)
    r.run("debug", "loadaof")
    r.run("XADD", "mystream", "*", "xitem", "v")
    assert r.run("xlen", "mystream") == 72


pytestmark = [pytest.mark.stream_needs_debug]


def test_xtrim_with_maxlen_can_propagate_correctly(r: ValkeyTestClient) -> None:
    """
    test {XTRIM with ~ MAXLEN can propagate correctly} {
        for {set j 0} {$j < 100} {incr j} {
            r XADD mystream * xitem v
        }
        r XTRIM mystream MAXLEN ~ 85
        assert {[r xlen mystream] == 90}
        r config set stream-node-max-entries 1
        r debug loadaof
        r XADD mystream * xitem v
        incr j
        assert {[r xlen mystream] == 91}
    }
    """
    j = 0
    while j < 100:
        r.run("XADD", "mystream", "*", "xitem", "v")
        j += 1
    r.run("XTRIM", "mystream", "MAXLEN", "~", 85)
    assert r.run("xlen", "mystream") == 90
    r.run("config", "set", "stream-node-max-entries", 1)
    r.run("debug", "loadaof")
    r.run("XADD", "mystream", "*", "xitem", "v")
    incr("j")
    assert r.run("xlen", "mystream") == 91


pytestmark = [pytest.mark.stream]


def test_xadd_can_create_an_empty_stream(r: ValkeyTestClient) -> None:
    """
    test {XADD can CREATE an empty stream} {
        r XADD mystream MAXLEN 0 * a b
        assert {[dict get [r xinfo stream mystream] length] == 0}
    }
    """
    r.run("XADD", "mystream", "MAXLEN", 0, "*", "a", "b")
    assert r.run("xinfo", "stream", "mystream")["length"] == 0


def test_xsetid_can_set_a_specific_id(r: ValkeyTestClient) -> None:
    """
    test {XSETID can set a specific ID} {
        r XSETID mystream "200-0"
        set reply [r XINFO stream mystream]
        assert_equal [dict get $reply last-generated-id] "200-0"
        assert_equal [dict get $reply entries-added] 1
    }
    """
    r.run("XSETID", "mystream", "200-0")
    reply = r.run("XINFO", "stream", "mystream")
    assert reply["last-generated-id"] == "200-0"
    assert reply["entries-added"] == 1


def test_xsetid_cannot_setid_with_smaller_id(r: ValkeyTestClient) -> None:
    """
    test {XSETID cannot SETID with smaller ID} {
        r XADD mystream * a b
        catch {r XSETID mystream "1-1"} err
        r XADD mystream MAXLEN 0 * a b
        set err
    } {ERR *smaller*}
    """
    r.run("XADD", "mystream", "*", "a", "b")
    err = None
    try:
        err = r.run("XSETID", "mystream", "1-1")
    except Exception as _catch_err:
        err = str(_catch_err)
    r.run("XADD", "mystream", "MAXLEN", 0, "*", "a", "b")
    assert fnmatch(str(err), "ERR *smaller*")


def test_xsetid_cannot_setid_on_non_existent_key(r: ValkeyTestClient) -> None:
    """
    test {XSETID cannot SETID on non-existent key} {
        catch {r XSETID stream 1-1} err
        set _ $err
    } {ERR no such key}
    """
    err = None
    try:
        err = r.run("XSETID", "stream", "1-1")
    except Exception as _catch_err:
        err = str(_catch_err)
    assert err == "ERR no such key"


def test_xsetid_cannot_run_with_an_offset_but_without_a_maximal_tombstone(r: ValkeyTestClient) -> None:
    """
    test {XSETID cannot run with an offset but without a maximal tombstone} {
        catch {r XSETID stream 1-1 0} err
        set _ $err
    } {ERR syntax error}
    """
    err = None
    try:
        err = r.run("XSETID", "stream", "1-1", 0)
    except Exception as _catch_err:
        err = str(_catch_err)
    assert err == "ERR syntax error"


def test_xsetid_cannot_run_with_a_maximal_tombstone_but_without_an_offset(r: ValkeyTestClient) -> None:
    """
    test {XSETID cannot run with a maximal tombstone but without an offset} {
        catch {r XSETID stream 1-1 0-0} err
        set _ $err
    } {ERR syntax error}
    """
    err = None
    try:
        err = r.run("XSETID", "stream", "1-1", "0-0")
    except Exception as _catch_err:
        err = str(_catch_err)
    assert err == "ERR syntax error"


def test_xsetid_errors_on_negative_offset(r: ValkeyTestClient) -> None:
    """
    test {XSETID errors on negative offset} {
        catch {r XSETID stream 1-1 ENTRIESADDED -1 MAXDELETEDID 0-0} err
        set _ $err
    } {ERR *must be positive}
    """
    err = None
    try:
        err = r.run("XSETID", "stream", "1-1", "ENTRIESADDED", -1, "MAXDELETEDID", "0-0")
    except Exception as _catch_err:
        err = str(_catch_err)
    assert fnmatch(str(err), "ERR *must be positive")


def test_xsetid_cannot_set_the_maximal_tombstone_with_larger_id(r: ValkeyTestClient) -> None:
    """
    test {XSETID cannot set the maximal tombstone with larger ID} {
        r DEL x
        r XADD x 1-0 a b

        catch {r XSETID x "1-0" ENTRIESADDED 1 MAXDELETEDID "2-0" } err
        r XADD mystream MAXLEN 0 * a b
        set err
    } {ERR *smaller*}
    """
    r.run("DEL", "x")
    r.run("XADD", "x", "1-0", "a", "b")
    err = None
    try:
        err = r.run("XSETID", "x", "1-0", "ENTRIESADDED", 1, "MAXDELETEDID", "2-0")
    except Exception as _catch_err:
        err = str(_catch_err)
    r.run("XADD", "mystream", "MAXLEN", 0, "*", "a", "b")
    assert fnmatch(str(err), "ERR *smaller*")


def test_xsetid_cannot_set_the_offset_to_less_than_the_length(r: ValkeyTestClient) -> None:
    """
    test {XSETID cannot set the offset to less than the length} {
        r DEL x
        r XADD x 1-0 a b

        catch {r XSETID x "1-0" ENTRIESADDED 0 MAXDELETEDID "0-0" } err
        r XADD mystream MAXLEN 0 * a b
        set err
    } {ERR *smaller*}
    """
    r.run("DEL", "x")
    r.run("XADD", "x", "1-0", "a", "b")
    err = None
    try:
        err = r.run("XSETID", "x", "1-0", "ENTRIESADDED", 0, "MAXDELETEDID", "0-0")
    except Exception as _catch_err:
        err = str(_catch_err)
    r.run("XADD", "mystream", "MAXLEN", 0, "*", "a", "b")
    assert fnmatch(str(err), "ERR *smaller*")


def test_xsetid_cannot_set_smaller_id_than_current_maxdeletedid(r: ValkeyTestClient) -> None:
    """
    test {XSETID cannot set smaller ID than current MAXDELETEDID} {
        r DEL x
        r XADD x 1-1 a 1
        r XADD x 1-2 b 2
        r XADD x 1-3 c 3
        r XDEL x 1-2
        r XDEL x 1-3
        set reply [r XINFO stream x]
        assert_equal [dict get $reply max-deleted-entry-id] "1-3"
        catch {r XSETID x "1-2" } err
        set err
    } {ERR *smaller*}
    """
    r.run("DEL", "x")
    r.run("XADD", "x", "1-1", "a", 1)
    r.run("XADD", "x", "1-2", "b", 2)
    r.run("XADD", "x", "1-3", "c", 3)
    r.run("XDEL", "x", "1-2")
    r.run("XDEL", "x", "1-3")
    reply = r.run("XINFO", "stream", "x")
    assert reply["max-deleted-entry-id"] == "1-3"
    err = None
    try:
        err = r.run("XSETID", "x", "1-2")
    except Exception as _catch_err:
        err = str(_catch_err)
    assert fnmatch(str(err), "ERR *smaller*")


pytestmark = [pytest.mark.stream]


def test_xadd_advances_the_entries_added_counter_and_sets_the_recorded_first_entry_id(r: ValkeyTestClient) -> None:
    """
    test {XADD advances the entries-added counter and sets the recorded-first-entry-id} {
        r DEL x
        r XADD x 1-0 data a

        set reply [r XINFO STREAM x FULL]
        assert_equal [dict get $reply entries-added] 1
        assert_equal [dict get $reply recorded-first-entry-id] "1-0"

        r XADD x 2-0 data a
        set reply [r XINFO STREAM x FULL]
        assert_equal [dict get $reply entries-added] 2
        assert_equal [dict get $reply recorded-first-entry-id] "1-0"
    }
    """
    r.run("DEL", "x")
    r.run("XADD", "x", "1-0", "data", "a")
    reply = r.run("XINFO", "STREAM", "x", "FULL")
    assert reply["entries-added"] == 1
    assert reply["recorded-first-entry-id"] == "1-0"
    r.run("XADD", "x", "2-0", "data", "a")
    reply = r.run("XINFO", "STREAM", "x", "FULL")
    assert reply["entries-added"] == 2
    assert reply["recorded-first-entry-id"] == "1-0"


def test_xdel_or_trim_are_reflected_by_recorded_first_entry(r: ValkeyTestClient) -> None:
    """
    test {XDEL/TRIM are reflected by recorded first entry} {
        r DEL x
        r XADD x 1-0 data a
        r XADD x 2-0 data a
        r XADD x 3-0 data a
        r XADD x 4-0 data a
        r XADD x 5-0 data a

        set reply [r XINFO STREAM x FULL]
        assert_equal [dict get $reply entries-added] 5
        assert_equal [dict get $reply recorded-first-entry-id] "1-0"

        r XDEL x 2-0
        set reply [r XINFO STREAM x FULL]
        assert_equal [dict get $reply recorded-first-entry-id] "1-0"

        r XDEL x 1-0
        set reply [r XINFO STREAM x FULL]
        assert_equal [dict get $reply recorded-first-entry-id] "3-0"

        r XTRIM x MAXLEN = 2
        set reply [r XINFO STREAM x FULL]
        assert_equal [dict get $reply recorded-first-entry-id] "4-0"
    }
    """
    r.run("DEL", "x")
    r.run("XADD", "x", "1-0", "data", "a")
    r.run("XADD", "x", "2-0", "data", "a")
    r.run("XADD", "x", "3-0", "data", "a")
    r.run("XADD", "x", "4-0", "data", "a")
    r.run("XADD", "x", "5-0", "data", "a")
    reply = r.run("XINFO", "STREAM", "x", "FULL")
    assert reply["entries-added"] == 5
    assert reply["recorded-first-entry-id"] == "1-0"
    r.run("XDEL", "x", "2-0")
    reply = r.run("XINFO", "STREAM", "x", "FULL")
    assert reply["recorded-first-entry-id"] == "1-0"
    r.run("XDEL", "x", "1-0")
    reply = r.run("XINFO", "STREAM", "x", "FULL")
    assert reply["recorded-first-entry-id"] == "3-0"
    r.run("XTRIM", "x", "MAXLEN", "=", 2)
    reply = r.run("XINFO", "STREAM", "x", "FULL")
    assert reply["recorded-first-entry-id"] == "4-0"


def test_maximum_xdel_id_behaves_correctly(r: ValkeyTestClient) -> None:
    """
    test {Maximum XDEL ID behaves correctly} {
        r DEL x
        r XADD x 1-0 data a
        r XADD x 2-0 data b
        r XADD x 3-0 data c

        set reply [r XINFO STREAM x FULL]
        assert_equal [dict get $reply max-deleted-entry-id] "0-0"

        r XDEL x 2-0
        set reply [r XINFO STREAM x FULL]
        assert_equal [dict get $reply max-deleted-entry-id] "2-0"

        r XDEL x 1-0
        set reply [r XINFO STREAM x FULL]
        assert_equal [dict get $reply max-deleted-entry-id] "2-0"
    }
    """
    r.run("DEL", "x")
    r.run("XADD", "x", "1-0", "data", "a")
    r.run("XADD", "x", "2-0", "data", "b")
    r.run("XADD", "x", "3-0", "data", "c")
    reply = r.run("XINFO", "STREAM", "x", "FULL")
    assert reply["max-deleted-entry-id"] == "0-0"
    r.run("XDEL", "x", "2-0")
    reply = r.run("XINFO", "STREAM", "x", "FULL")
    assert reply["max-deleted-entry-id"] == "2-0"
    r.run("XDEL", "x", "1-0")
    reply = r.run("XINFO", "STREAM", "x", "FULL")
    assert reply["max-deleted-entry-id"] == "2-0"


def test_xadd_with_artial_id_with_maximal_seq(r: ValkeyTestClient) -> None:
    """
    test {XADD with artial ID with maximal seq} {
        r DEL x
        r XADD x 1-18446744073709551615 f1 v1
        assert_error {*The ID specified in XADD is equal or smaller*} {r XADD x 1-* f2 v2}
    }
    """
    r.run("DEL", "x")
    r.run("XADD", "x", "1-18446744073709551615", "f1", "v1")
    with pytest.raises(Exception, match=".*The\\ ID\\ specified\\ in\\ XADD\\ is\\ equal\\ or\\ smaller.*"):
        r.run("XADD", "x", "1-*", "f2", "v2")


pytestmark = [pytest.mark.stream_needs_debug]


def test_empty_stream_can_be_rewrite_into_aof_correctly(r: ValkeyTestClient) -> None:
    """
    test {Empty stream can be rewrite into AOF correctly} {
        r XADD mystream MAXLEN 0 * a b
        assert {[dict get [r xinfo stream mystream] length] == 0}
        r bgrewriteaof
        waitForBgrewriteaof r
        r debug loadaof
        assert {[dict get [r xinfo stream mystream] length] == 0}
    }
    """
    r.run("XADD", "mystream", "MAXLEN", 0, "*", "a", "b")
    assert r.run("xinfo", "stream", "mystream")["length"] == 0
    r.run("bgrewriteaof")
    wait_for_bgrewriteaof("r")
    r.run("debug", "loadaof")
    assert r.run("xinfo", "stream", "mystream")["length"] == 0


def test_stream_can_be_rewrite_into_aof_correctly_after_xdel_lastid(r: ValkeyTestClient) -> None:
    """
    test {Stream can be rewrite into AOF correctly after XDEL lastid} {
        r XSETID mystream 0-0
        r XADD mystream 1-1 a b
        r XADD mystream 2-2 a b
        assert {[dict get [r xinfo stream mystream] length] == 2}
        r XDEL mystream 2-2
        r bgrewriteaof
        waitForBgrewriteaof r
        r debug loadaof
        assert {[dict get [r xinfo stream mystream] length] == 1}
        assert_equal [dict get [r xinfo stream mystream] last-generated-id] "2-2"
    }
    """
    r.run("XSETID", "mystream", "0-0")
    r.run("XADD", "mystream", "1-1", "a", "b")
    r.run("XADD", "mystream", "2-2", "a", "b")
    assert r.run("xinfo", "stream", "mystream")["length"] == 2
    r.run("XDEL", "mystream", "2-2")
    r.run("bgrewriteaof")
    wait_for_bgrewriteaof("r")
    r.run("debug", "loadaof")
    assert r.run("xinfo", "stream", "mystream")["length"] == 1
    assert r.run("xinfo", "stream", "mystream")["last-generated-id"] == "2-2"


pytestmark = [pytest.mark.stream]


def test_xgroup_help_should_not_have_unexpected_options(r: ValkeyTestClient) -> None:
    """
    test {XGROUP HELP should not have unexpected options} {
        catch {r XGROUP help xxx} e
        assert_match "*wrong number of arguments for 'xgroup|help' command" $e
    }
    """
    e = None
    try:
        e = r.run("XGROUP", "help", "xxx")
    except Exception as _catch_err:
        e = str(_catch_err)
    assert fnmatch(str(e), "*wrong number of arguments for 'xgroup|help' command")


def test_xinfo_help_should_not_have_unexpected_options(r: ValkeyTestClient) -> None:
    """
    test {XINFO HELP should not have unexpected options} {
        catch {r XINFO help xxx} e
        assert_match "*wrong number of arguments for 'xinfo|help' command" $e
    }
    """
    e = None
    try:
        e = r.run("XINFO", "help", "xxx")
    except Exception as _catch_err:
        e = str(_catch_err)
    assert fnmatch(str(e), "*wrong number of arguments for 'xinfo|help' command")


# --- stubs for unimplemented TCL helpers ---


def assert_(*args):
    raise NotImplementedError("assert_")


def expr(*args):
    raise NotImplementedError("expr")


def fail(*args):
    raise NotImplementedError("fail")


def foreach(*args):
    raise NotImplementedError("foreach")


def if_(*args):
    raise NotImplementedError("if_")


def incr(*args):
    raise NotImplementedError("incr")


def insert_into_stream_key(*args):
    raise NotImplementedError("insert_into_stream_key")


def lassign(*args):
    raise NotImplementedError("lassign")


def lindex(*args):
    raise NotImplementedError("lindex")


def lrange(*args):
    raise NotImplementedError("lrange")


def lreverse(*args):
    raise NotImplementedError("lreverse")


def lshuffle(*args):
    raise NotImplementedError("lshuffle")


def split(*args):
    raise NotImplementedError("split")


def stream_compare_id(*args):
    raise NotImplementedError("stream_compare_id")


def stream_random_id(*args):
    raise NotImplementedError("stream_random_id")


def stream_simulate_xrange(*args):
    raise NotImplementedError("stream_simulate_xrange")


def wait_for_bgrewriteaof(*args):
    raise NotImplementedError("wait_for_bgrewriteaof")


def wait_for_blocked_client(*args):
    raise NotImplementedError("wait_for_blocked_client")


def wait_for_blocked_clients_count(*args):
    raise NotImplementedError("wait_for_blocked_clients_count")


def while_(*args):
    raise NotImplementedError("while_")
