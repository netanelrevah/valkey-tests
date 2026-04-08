# ruff: noqa: PLR2004, N806, RUF043, ANN001, ANN002, ANN201

from fnmatch import fnmatch

import pytest

from tests.valkey_test_client import ValkeyTestClient

"""
proc count_bits s {
    binary scan $s b* bits
    string length [regsub -all {0} $bits {}]
}
"""


"""
proc count_bits_start_end {s start end} {
    binary scan $s B* bits
    string length [regsub -all {0} [string range $bits $start $end] {}]
}
"""


"""
proc simulate_bit_op {op args} {
    set maxlen 0
    set j 0
    set count [llength $args]
    foreach a $args {
        binary scan $a b* bits
        set b($j) $bits
        if {[string length $bits] > $maxlen} {
            set maxlen [string length $bits]
        }
        incr j
    }
    for {set j 0} {$j < $count} {incr j} {
        if {[string length $b($j)] < $maxlen} {
            append b($j) [string repeat 0 [expr $maxlen-[string length $b($j)]]]
        }
    }
    set out {}
    for {set x 0} {$x < $maxlen} {incr x} {
        set bit [string range $b(0) $x $x]
        if {$op eq {not}} {set bit [expr {!$bit}]}
        for {set j 1} {$j < $count} {incr j} {
            set bit2 [string range $b($j) $x $x]
            switch $op {
                and {set bit [expr {$bit & $bit2}]}
                or  {set bit [expr {$bit | $bit2}]}
                xor {set bit [expr {$bit ^ $bit2}]}
            }
        }
        append out $bit
    }
    binary format b* $out
}
"""

pytestmark = [pytest.mark.bitops]


def test_bitcount_against_wrong_type(r: ValkeyTestClient) -> None:
    """
    test {BITCOUNT against wrong type} {
        r del mylist
        r lpush mylist a b c
        assert_error "*WRONGTYPE*" {r bitcount mylist}
        assert_error "*WRONGTYPE*" {r bitcount mylist 0 100}

        # with negative indexes where start > end
        assert_error "*WRONGTYPE*" {r bitcount mylist -6 -7}
        assert_error "*WRONGTYPE*" {r bitcount mylist -6 -15 bit}
    }
    """
    r.run("del", "mylist")
    r.run("lpush", "mylist", "a", "b", "c")
    with pytest.raises(Exception, match=".*WRONGTYPE.*"):
        r.run("bitcount", "mylist")
    with pytest.raises(Exception, match=".*WRONGTYPE.*"):
        r.run("bitcount", "mylist", 0, 100)
    with pytest.raises(Exception, match=".*WRONGTYPE.*"):
        r.run("bitcount", "mylist", -6, -7)
    with pytest.raises(Exception, match=".*WRONGTYPE.*"):
        r.run("bitcount", "mylist", -6, -15, "bit")


def test_bitcount_returns_0_against_non_existing_key(r: ValkeyTestClient) -> None:
    """
    test {BITCOUNT returns 0 against non existing key} {
        r del no-key
        assert {[r bitcount no-key] == 0}
        assert {[r bitcount no-key 0 1000 bit] == 0}
    }
    """
    r.run("del", "no-key")
    assert r.run("bitcount", "no-key") == 0
    assert r.run("bitcount", "no-key", 0, 1000, "bit") == 0


def test_bitcount_returns_0_with_out_of_range_indexes(r: ValkeyTestClient) -> None:
    """
    test {BITCOUNT returns 0 with out of range indexes} {
        r set str "xxxx"
        assert {[r bitcount str 4 10] == 0}
        assert {[r bitcount str 32 87 bit] == 0}
    }
    """
    r.run("set", "str", "xxxx")
    assert r.run("bitcount", "str", 4, 10) == 0
    assert r.run("bitcount", "str", 32, 87, "bit") == 0


def test_bitcount_returns_0_with_negative_indexes_where_start_end(r: ValkeyTestClient) -> None:
    """
    test {BITCOUNT returns 0 with negative indexes where start > end} {
        r set str "xxxx"
        assert {[r bitcount str -6 -7] == 0}
        assert {[r bitcount str -6 -15 bit] == 0}

        # against non existing key
        r del str
        assert {[r bitcount str -6 -7] == 0}
        assert {[r bitcount str -6 -15 bit] == 0}
    }
    """
    r.run("set", "str", "xxxx")
    assert r.run("bitcount", "str", -6, -7) == 0
    assert r.run("bitcount", "str", -6, -15, "bit") == 0
    r.run("del", "str")
    assert r.run("bitcount", "str", -6, -7) == 0
    assert r.run("bitcount", "str", -6, -15, "bit") == 0


"""
catch {unset num}
"""


"""
foreach vec list "" "\xaa" "\x00\x00\xff" "foobar" "123" {
    incr num
    test "BITCOUNT against test vector #$num" {
        r set str $vec
        set count [count_bits $vec]
        assert {[r bitcount str] == $count}
        assert {[r bitcount str 0 -1 bit] == $count}
    }
}
"""


def test_bitcount_fuzzing_without_start_or_end(r: ValkeyTestClient) -> None:
    """
    test {BITCOUNT fuzzing without start/end} {
        for {set j 0} {$j < 100} {incr j} {
            set str [randstring 0 3000]
            r set str $str
            set count [count_bits $str]
            assert {[r bitcount str] == $count}
            assert {[r bitcount str 0 -1 bit] == $count}
        }
    }
    """
    j = 0
    while j < 100:
        str = randstring(0, 3000)
        r.run("set", "str", str)
        count = count_bits(str)
        assert r.run("bitcount", "str") == count
        assert r.run("bitcount", "str", 0, -1, "bit") == count
        j += 1


def test_bitcount_fuzzing_with_start_or_end(r: ValkeyTestClient) -> None:
    """
    test {BITCOUNT fuzzing with start/end} {
        for {set j 0} {$j < 100} {incr j} {
            set str [randstring 0 3000]
            r set str $str
            set l [string length $str]
            set start [randomInt $l]
            set end [randomInt $l]
            if {$start > $end} {
                # Swap start and end
                lassign [list $end $start] start end
            }
            assert {[r bitcount str $start $end] == [count_bits [string range $str $start $end]]}
        }

        for {set j 0} {$j < 100} {incr j} {
            set str [randstring 0 3000]
            r set str $str
            set l [expr [string length $str] * 8]
            set start [randomInt $l]
            set end [randomInt $l]
            if {$start > $end} {
                # Swap start and end
                lassign [list $end $start] start end
            }
            assert {[r bitcount str $start $end bit] == [count_bits_start_end $str $start $end]}
        }
    }
    """
    j = 0
    while j < 100:
        str = randstring(0, 3000)
        r.run("set", "str", str)
        L = len(str)
        start = random_int(L)
        end = random_int(L)
        if_(
            "$start > $end",
            "                # Swap start and end\n                lassign [list $end $start] start end\n            ",
        )
        assert r.run("bitcount", "str", start, end) == count_bits(string("range", str, start, end))
        j += 1
    j = 0
    while j < 100:
        str = randstring(0, 3000)
        r.run("set", "str", str)
        L = expr(len(str), "*", 8)
        start = random_int(L)
        end = random_int(L)
        if_(
            "$start > $end",
            "                # Swap start and end\n                lassign [list $end $start] start end\n            ",
        )
        assert r.run("bitcount", "str", start, end, "bit") == count_bits_start_end(str, start, end)
        j += 1


def test_bitcount_with_just_start(r: ValkeyTestClient) -> None:
    """
    test {BITCOUNT with just start} {
        set s "foobar"
        r set s $s
        assert_equal [r bitcount s 0] [count_bits "foobar"]
        assert_equal [r bitcount s 1] [count_bits "oobar"]
        assert_equal [r bitcount s 1000] 0
        assert_equal [r bitcount s -1] [count_bits "r"]
        assert_equal [r bitcount s -2] [count_bits "ar"]
        assert_equal [r bitcount s -1000] [count_bits "foobar"]
    }
    """
    s = "foobar"
    r.run("set", "s", s)
    assert r.run("bitcount", "s", 0) == count_bits("foobar")
    assert r.run("bitcount", "s", 1) == count_bits("oobar")
    assert r.run("bitcount", "s", 1000) == 0
    assert r.run("bitcount", "s", -1) == count_bits("r")
    assert r.run("bitcount", "s", -2) == count_bits("ar")
    assert r.run("bitcount", "s", -1000) == count_bits("foobar")


def test_bitcount_with_start_end(r: ValkeyTestClient) -> None:
    """
    test {BITCOUNT with start, end} {
        set s "foobar"
        r set s $s
        assert_equal [r bitcount s 0 -1] [count_bits "foobar"]
        assert_equal [r bitcount s 1 -2] [count_bits "ooba"]
        assert_equal [r bitcount s -2 1] 0
        assert_equal [r bitcount s -1000 0] [count_bits "f"]
        assert_equal [r bitcount s 0 1000] [count_bits "foobar"]
        assert_equal [r bitcount s -1000 1000] [count_bits "foobar"]

        assert_equal [r bitcount s 0 -1 bit] [count_bits $s]
        assert_equal [r bitcount s 10 14 bit] [count_bits_start_end $s 10 14]
        assert_equal [r bitcount s 3 14 bit] [count_bits_start_end $s 3 14]
        assert_equal [r bitcount s 3 29 bit] [count_bits_start_end $s 3 29]
        assert_equal [r bitcount s 10 -34 bit] [count_bits_start_end $s 10 14]
        assert_equal [r bitcount s 3 -34 bit] [count_bits_start_end $s 3 14]
        assert_equal [r bitcount s 3 -19 bit] [count_bits_start_end $s 3 29]
        assert_equal [r bitcount s -2 1 bit] 0
        assert_equal [r bitcount s -1000 14 bit] [count_bits_start_end $s 0 14]
        assert_equal [r bitcount s 0 1000 bit] [count_bits $s]
        assert_equal [r bitcount s -1000 1000 bit] [count_bits $s]
    }
    """
    s = "foobar"
    r.run("set", "s", s)
    assert r.run("bitcount", "s", 0, -1) == count_bits("foobar")
    assert r.run("bitcount", "s", 1, -2) == count_bits("ooba")
    assert r.run("bitcount", "s", -2, 1) == 0
    assert r.run("bitcount", "s", -1000, 0) == count_bits("f")
    assert r.run("bitcount", "s", 0, 1000) == count_bits("foobar")
    assert r.run("bitcount", "s", -1000, 1000) == count_bits("foobar")
    assert r.run("bitcount", "s", 0, -1, "bit") == count_bits(s)
    assert r.run("bitcount", "s", 10, 14, "bit") == count_bits_start_end(s, 10, 14)
    assert r.run("bitcount", "s", 3, 14, "bit") == count_bits_start_end(s, 3, 14)
    assert r.run("bitcount", "s", 3, 29, "bit") == count_bits_start_end(s, 3, 29)
    assert r.run("bitcount", "s", 10, -34, "bit") == count_bits_start_end(s, 10, 14)
    assert r.run("bitcount", "s", 3, -34, "bit") == count_bits_start_end(s, 3, 14)
    assert r.run("bitcount", "s", 3, -19, "bit") == count_bits_start_end(s, 3, 29)
    assert r.run("bitcount", "s", -2, 1, "bit") == 0
    assert r.run("bitcount", "s", -1000, 14, "bit") == count_bits_start_end(s, 0, 14)
    assert r.run("bitcount", "s", 0, 1000, "bit") == count_bits(s)
    assert r.run("bitcount", "s", -1000, 1000, "bit") == count_bits(s)


def test_bitcount_with_illegal_arguments(r: ValkeyTestClient) -> None:
    """
    test {BITCOUNT with illegal arguments} {
        # Used to return 0 for non-existing key instead of errors
        r del s
        assert_error {ERR *syntax*} {r bitcount s 0 1 hello}
        assert_error {ERR *syntax*} {r bitcount s 0 1 hello hello2}

        r set s 1
        assert_error {ERR *syntax*} {r bitcount s 0 1 hello}
        assert_error {ERR *syntax*} {r bitcount s 0 1 hello hello2}
    }
    """
    r.run("del", "s")
    with pytest.raises(Exception, match="ERR\\ .*syntax.*"):
        r.run("bitcount", "s", 0, 1, "hello")
    with pytest.raises(Exception, match="ERR\\ .*syntax.*"):
        r.run("bitcount", "s", 0, 1, "hello", "hello2")
    r.run("set", "s", 1)
    with pytest.raises(Exception, match="ERR\\ .*syntax.*"):
        r.run("bitcount", "s", 0, 1, "hello")
    with pytest.raises(Exception, match="ERR\\ .*syntax.*"):
        r.run("bitcount", "s", 0, 1, "hello", "hello2")


def test_bitcount_against_non_integer_value(r: ValkeyTestClient) -> None:
    """
    test {BITCOUNT against non-integer value} {
        # against existing key
        r set s 1
        assert_error {ERR *not an integer*} {r bitcount s a b}

        # against non existing key
        r del s
        assert_error {ERR *not an integer*} {r bitcount s a b}

        # against wrong type
        r lpush s a b c
        assert_error {ERR *not an integer*} {r bitcount s a b}
    }
    """
    r.run("set", "s", 1)
    with pytest.raises(Exception, match="ERR\\ .*not\\ an\\ integer.*"):
        r.run("bitcount", "s", "a", "b")
    r.run("del", "s")
    with pytest.raises(Exception, match="ERR\\ .*not\\ an\\ integer.*"):
        r.run("bitcount", "s", "a", "b")
    r.run("lpush", "s", "a", "b", "c")
    with pytest.raises(Exception, match="ERR\\ .*not\\ an\\ integer.*"):
        r.run("bitcount", "s", "a", "b")


def test_bitcount_regression_test_for_github_issue_582(r: ValkeyTestClient) -> None:
    """
    test {BITCOUNT regression test for github issue #582} {
        r del foo
        r setbit foo 0 1
        if {[catch {r bitcount foo 0 4294967296} e]} {
            assert_match {*ERR*out of range*} $e
            set _ 1
        } else {
            set e
        }
    } {1}
    """
    r.run("del", "foo")
    r.run("setbit", "foo", 0, 1)
    if_(
        "[catch {r bitcount foo 0 4294967296} e]",
        "            assert_match {*ERR*out of range*} $e\n            set _ 1\n        ",
        "else",
        "            set e\n        ",
    )


def test_bitcount_misaligned_prefix(r: ValkeyTestClient) -> None:
    """
    test {BITCOUNT misaligned prefix} {
        r del str
        r set str ab
        r bitcount str 1 -1
    } {3}
    """
    r.run("del", "str")
    r.run("set", "str", "ab")
    assert r.run("bitcount", "str", 1, -1) == "3"


def test_bitcount_misaligned_prefix_full_words_remainder(r: ValkeyTestClient) -> None:
    """
    test {BITCOUNT misaligned prefix + full words + remainder} {
        r del str
        r set str __PPxxxxxxxxxxxxxxxxRR__
        r bitcount str 2 -3
    } {74}
    """
    r.run("del", "str")
    r.run("set", "str", "__PPxxxxxxxxxxxxxxxxRR__")
    assert r.run("bitcount", "str", 2, -3) == "74"


def test_bitop_not_empty_string(r: ValkeyTestClient) -> None:
    """
    test {BITOP NOT (empty string)} {
        r set s{t} ""
        r bitop not dest{t} s{t}
        r get dest{t}
    } {}
    """
    r.run("set", "s{t}", "")
    r.run("bitop", "not", "dest{t}", "s{t}")
    r.run("get", "dest{t}")


def test_bitop_not_known_string(r: ValkeyTestClient) -> None:
    """
    test {BITOP NOT (known string)} {
        r set s{t} "\xaa\x00\xff\x55"
        r bitop not dest{t} s{t}
        r get dest{t}
    } "\x55\xff\x00\xaa"
    """
    r.run("set", "s{t}", "\xaa\x00\xff\x55")
    r.run("bitop", "not", "dest{t}", "s{t}")
    r.run("get", "dest{t}")


def test_bitop_where_dest_and_target_are_the_same_key(r: ValkeyTestClient) -> None:
    """
    test {BITOP where dest and target are the same key} {
        r set s "\xaa\x00\xff\x55"
        r bitop not s s
        r get s
    } "\x55\xff\x00\xaa"
    """
    r.run("set", "s", "\xaa\x00\xff\x55")
    r.run("bitop", "not", "s", "s")
    r.run("get", "s")


def test_bitop_and_or_xor_don_t_change_the_string_with_single_input_key(r: ValkeyTestClient) -> None:
    """
    test {BITOP AND|OR|XOR don't change the string with single input key} {
        r set a{t} "\x01\x02\xff"
        r bitop and res1{t} a{t}
        r bitop or  res2{t} a{t}
        r bitop xor res3{t} a{t}
        list [r get res1{t}] [r get res2{t}] [r get res3{t}]
    } list "\x01\x02\xff" "\x01\x02\xff" "\x01\x02\xff"
    """
    r.run("set", "a{t}", "\x01\x02\xff")
    r.run("bitop", "and", "res1{t}", "a{t}")
    r.run("bitop", "or", "res2{t}", "a{t}")
    r.run("bitop", "xor", "res3{t}", "a{t}")
    list_(r.run("get", "res1{t}"), r.run("get", "res2{t}"), r.run("get", "res3{t}"))


def test_bitop_missing_key_is_considered_a_stream_of_zero(r: ValkeyTestClient) -> None:
    """
    test {BITOP missing key is considered a stream of zero} {
        r set a{t} "\x01\x02\xff"
        r bitop and res1{t} no-suck-key{t} a{t}
        r bitop or  res2{t} no-suck-key{t} a{t} no-such-key{t}
        r bitop xor res3{t} no-such-key{t} a{t}
        list [r get res1{t}] [r get res2{t}] [r get res3{t}]
    } list "\x00\x00\x00" "\x01\x02\xff" "\x01\x02\xff"
    """
    r.run("set", "a{t}", "\x01\x02\xff")
    r.run("bitop", "and", "res1{t}", "no-suck-key{t}", "a{t}")
    r.run("bitop", "or", "res2{t}", "no-suck-key{t}", "a{t}", "no-such-key{t}")
    r.run("bitop", "xor", "res3{t}", "no-such-key{t}", "a{t}")
    list_(r.run("get", "res1{t}"), r.run("get", "res2{t}"), r.run("get", "res3{t}"))


def test_bitop_shorter_keys_are_zero_padded_to_the_key_with_max_length(r: ValkeyTestClient) -> None:
    """
    test {BITOP shorter keys are zero-padded to the key with max length} {
        r set a{t} "\x01\x02\xff\xff"
        r set b{t} "\x01\x02\xff"
        r bitop and res1{t} a{t} b{t}
        r bitop or  res2{t} a{t} b{t}
        r bitop xor res3{t} a{t} b{t}
        list [r get res1{t}] [r get res2{t}] [r get res3{t}]
    } list "\x01\x02\xff\x00" "\x01\x02\xff\xff" "\x00\x00\x00\xff"
    """
    r.run("set", "a{t}", "\x01\x02\xff\xff")
    r.run("set", "b{t}", "\x01\x02\xff")
    r.run("bitop", "and", "res1{t}", "a{t}", "b{t}")
    r.run("bitop", "or", "res2{t}", "a{t}", "b{t}")
    r.run("bitop", "xor", "res3{t}", "a{t}", "b{t}")
    list_(r.run("get", "res1{t}"), r.run("get", "res2{t}"), r.run("get", "res3{t}"))


@pytest.mark.parametrize(["op"], [("and"), ("or"), ("xor")])
def test_bitop_op_fuzzing(r: ValkeyTestClient, op) -> None:
    """
    test "BITOP $op fuzzing" {
        for {set i 0} {$i < 10} {incr i} {
            r flushall
            set vec {}
            set veckeys {}
            set numvec [expr {[randomInt 10]+1}]
            for {set j 0} {$j < $numvec} {incr j} {
                set str [randstring 0 1000]
                lappend vec $str
                lappend veckeys vector_$j{t}
                r set vector_$j{t} $str
            }
            r bitop $op target{t} {*}$veckeys
            assert_equal [r get target{t}] [simulate_bit_op $op {*}$vec]
        }
    }
    """
    i = 0
    while i < 10:
        r.run("flushall")
        vec = []
        veckeys = []
        numvec = expr("[randomInt 10]+1")
        j = 0
        while j < numvec:
            str = randstring(0, 1000)
            vec.append(str)
            veckeys.append("vector_$j{t}")
            r.run("set", "vector_$j{t}", str)
            j += 1
        r.run("bitop", op, "target{t}", "*", veckeys)
        assert r.run("get", "target{t}") == simulate_bit_op(op, "*", vec)
        i += 1


def test_bitop_not_fuzzing(r: ValkeyTestClient) -> None:
    """
    test {BITOP NOT fuzzing} {
        for {set i 0} {$i < 10} {incr i} {
            r flushall
            set str [randstring 0 1000]
            r set str{t} $str
            r bitop not target{t} str{t}
            assert_equal [r get target{t}] [simulate_bit_op not $str]
        }
    }
    """
    i = 0
    while i < 10:
        r.run("flushall")
        str = randstring(0, 1000)
        r.run("set", "str{t}", str)
        r.run("bitop", "not", "target{t}", "str{t}")
        assert r.run("get", "target{t}") == simulate_bit_op("not", str)
        i += 1


def test_bitop_with_integer_encoded_source_objects(r: ValkeyTestClient) -> None:
    """
    test {BITOP with integer encoded source objects} {
        r set a{t} 1
        r set b{t} 2
        r bitop xor dest{t} a{t} b{t} a{t}
        r get dest{t}
    } {2}
    """
    r.run("set", "a{t}", 1)
    r.run("set", "b{t}", 2)
    r.run("bitop", "xor", "dest{t}", "a{t}", "b{t}", "a{t}")
    assert r.run("get", "dest{t}") == "2"


def test_bitop_with_non_string_source_key(r: ValkeyTestClient) -> None:
    """
    test {BITOP with non string source key} {
        r del c{t}
        r set a{t} 1
        r set b{t} 2
        r lpush c{t} foo
        catch {r bitop xor dest{t} a{t} b{t} c{t} d{t}} e
        set e
    } {WRONGTYPE*}
    """
    r.run("del", "c{t}")
    r.run("set", "a{t}", 1)
    r.run("set", "b{t}", 2)
    r.run("lpush", "c{t}", "foo")
    try:
        e = r.run("bitop", "xor", "dest{t}", "a{t}", "b{t}", "c{t}", "d{t}")
    except Exception as _catch_err:
        e = str(_catch_err)
    assert fnmatch(str(e), "WRONGTYPE*")


def test_bitop_with_empty_string_after_non_empty_string_issue_529(r: ValkeyTestClient) -> None:
    """
    test {BITOP with empty string after non empty string (issue #529)} {
        r flushdb
        r set a{t} "\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
        r bitop or x{t} a{t} b{t}
    } {32}
    """
    r.run("flushdb")
    r.run(
        "set",
        "a{t}",
        "\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00",
    )
    assert r.run("bitop", "or", "x{t}", "a{t}", "b{t}") == "32"


def test_bitpos_against_wrong_type(r: ValkeyTestClient) -> None:
    """
    test {BITPOS against wrong type} {
        r del mylist
        r lpush mylist a b c
        assert_error "*WRONGTYPE*" {r bitpos mylist 0}
        assert_error "*WRONGTYPE*" {r bitpos mylist 1 10 100}
    }
    """
    r.run("del", "mylist")
    r.run("lpush", "mylist", "a", "b", "c")
    with pytest.raises(Exception, match=".*WRONGTYPE.*"):
        r.run("bitpos", "mylist", 0)
    with pytest.raises(Exception, match=".*WRONGTYPE.*"):
        r.run("bitpos", "mylist", 1, 10, 100)


def test_bitpos_will_illegal_arguments(r: ValkeyTestClient) -> None:
    """
    test {BITPOS will illegal arguments} {
        # Used to return 0 for non-existing key instead of errors
        r del s
        assert_error {ERR *syntax*} {r bitpos s 0 1 hello hello2}
        assert_error {ERR *syntax*} {r bitpos s 0 0 1 hello}

        r set s 1
        assert_error {ERR *syntax*} {r bitpos s 0 1 hello hello2}
        assert_error {ERR *syntax*} {r bitpos s 0 0 1 hello}
    }
    """
    r.run("del", "s")
    with pytest.raises(Exception, match="ERR\\ .*syntax.*"):
        r.run("bitpos", "s", 0, 1, "hello", "hello2")
    with pytest.raises(Exception, match="ERR\\ .*syntax.*"):
        r.run("bitpos", "s", 0, 0, 1, "hello")
    r.run("set", "s", 1)
    with pytest.raises(Exception, match="ERR\\ .*syntax.*"):
        r.run("bitpos", "s", 0, 1, "hello", "hello2")
    with pytest.raises(Exception, match="ERR\\ .*syntax.*"):
        r.run("bitpos", "s", 0, 0, 1, "hello")


def test_bitpos_against_non_integer_value(r: ValkeyTestClient) -> None:
    """
    test {BITPOS against non-integer value} {
        # against existing key
        r set s 1
        assert_error {ERR *not an integer*} {r bitpos s a}
        assert_error {ERR *not an integer*} {r bitpos s 0 a b}

        # against non existing key
        r del s
        assert_error {ERR *not an integer*} {r bitpos s b}
        assert_error {ERR *not an integer*} {r bitpos s 0 a b}

        # against wrong type
        r lpush s a b c
        assert_error {ERR *not an integer*} {r bitpos s a}
        assert_error {ERR *not an integer*} {r bitpos s 1 a b}
    }
    """
    r.run("set", "s", 1)
    with pytest.raises(Exception, match="ERR\\ .*not\\ an\\ integer.*"):
        r.run("bitpos", "s", "a")
    with pytest.raises(Exception, match="ERR\\ .*not\\ an\\ integer.*"):
        r.run("bitpos", "s", 0, "a", "b")
    r.run("del", "s")
    with pytest.raises(Exception, match="ERR\\ .*not\\ an\\ integer.*"):
        r.run("bitpos", "s", "b")
    with pytest.raises(Exception, match="ERR\\ .*not\\ an\\ integer.*"):
        r.run("bitpos", "s", 0, "a", "b")
    r.run("lpush", "s", "a", "b", "c")
    with pytest.raises(Exception, match="ERR\\ .*not\\ an\\ integer.*"):
        r.run("bitpos", "s", "a")
    with pytest.raises(Exception, match="ERR\\ .*not\\ an\\ integer.*"):
        r.run("bitpos", "s", 1, "a", "b")


def test_bitpos_bit_0_with_empty_key_returns_0(r: ValkeyTestClient) -> None:
    """
    test {BITPOS bit=0 with empty key returns 0} {
        r del str
        assert {[r bitpos str 0] == 0}
        assert {[r bitpos str 0 0 -1 bit] == 0}
    }
    """
    r.run("del", "str")
    assert r.run("bitpos", "str", 0) == 0
    assert r.run("bitpos", "str", 0, 0, -1, "bit") == 0


def test_bitpos_bit_1_with_empty_key_returns_1(r: ValkeyTestClient) -> None:
    """
    test {BITPOS bit=1 with empty key returns -1} {
        r del str
        assert {[r bitpos str 1] == -1}
        assert {[r bitpos str 1 0 -1] == -1}
    }
    """
    r.run("del", "str")
    assert r.run("bitpos", "str", 1) == -1
    assert r.run("bitpos", "str", 1, 0, -1) == -1


def test_bitpos_bit_0_with_string_less_than_1_word_works(r: ValkeyTestClient) -> None:
    """
    test {BITPOS bit=0 with string less than 1 word works} {
        r set str "\xff\xf0\x00"
        assert {[r bitpos str 0] == 12}
        assert {[r bitpos str 0 0 -1 bit] == 12}
    }
    """
    r.run("set", "str", "\xff\xf0\x00")
    assert r.run("bitpos", "str", 0) == 12
    assert r.run("bitpos", "str", 0, 0, -1, "bit") == 12


def test_bitpos_bit_1_with_string_less_than_1_word_works(r: ValkeyTestClient) -> None:
    """
    test {BITPOS bit=1 with string less than 1 word works} {
        r set str "\x00\x0f\x00"
        assert {[r bitpos str 1] == 12}
        assert {[r bitpos str 1 0 -1 bit] == 12}
    }
    """
    r.run("set", "str", "\x00\x0f\x00")
    assert r.run("bitpos", "str", 1) == 12
    assert r.run("bitpos", "str", 1, 0, -1, "bit") == 12


def test_bitpos_bit_0_starting_at_unaligned_address(r: ValkeyTestClient) -> None:
    """
    test {BITPOS bit=0 starting at unaligned address} {
        r set str "\xff\xf0\x00"
        assert {[r bitpos str 0 1] == 12}
        assert {[r bitpos str 0 1 -1 bit] == 12}
    }
    """
    r.run("set", "str", "\xff\xf0\x00")
    assert r.run("bitpos", "str", 0, 1) == 12
    assert r.run("bitpos", "str", 0, 1, -1, "bit") == 12


def test_bitpos_bit_1_starting_at_unaligned_address(r: ValkeyTestClient) -> None:
    """
    test {BITPOS bit=1 starting at unaligned address} {
        r set str "\x00\x0f\xff"
        assert {[r bitpos str 1 1] == 12}
        assert {[r bitpos str 1 1 -1 bit] == 12}
    }
    """
    r.run("set", "str", "\x00\x0f\xff")
    assert r.run("bitpos", "str", 1, 1) == 12
    assert r.run("bitpos", "str", 1, 1, -1, "bit") == 12


def test_bitpos_bit_0_unaligned_full_word_reminder(r: ValkeyTestClient) -> None:
    """
    test {BITPOS bit=0 unaligned+full word+reminder} {
        r del str
        r set str "\xff\xff\xff" ; # Prefix
        # Followed by two (or four in 32 bit systems) full words
        r append str "\xff\xff\xff\xff\xff\xff\xff\xff"
        r append str "\xff\xff\xff\xff\xff\xff\xff\xff"
        r append str "\xff\xff\xff\xff\xff\xff\xff\xff"
        # First zero bit.
        r append str "\x0f"
        assert {[r bitpos str 0] == 216}
        assert {[r bitpos str 0 1] == 216}
        assert {[r bitpos str 0 2] == 216}
        assert {[r bitpos str 0 3] == 216}
        assert {[r bitpos str 0 4] == 216}
        assert {[r bitpos str 0 5] == 216}
        assert {[r bitpos str 0 6] == 216}
        assert {[r bitpos str 0 7] == 216}
        assert {[r bitpos str 0 8] == 216}

        assert {[r bitpos str 0 1 -1 bit] == 216}
        assert {[r bitpos str 0 9 -1 bit] == 216}
        assert {[r bitpos str 0 17 -1 bit] == 216}
        assert {[r bitpos str 0 25 -1 bit] == 216}
        assert {[r bitpos str 0 33 -1 bit] == 216}
        assert {[r bitpos str 0 41 -1 bit] == 216}
        assert {[r bitpos str 0 49 -1 bit] == 216}
        assert {[r bitpos str 0 57 -1 bit] == 216}
        assert {[r bitpos str 0 65 -1 bit] == 216}
    }
    """
    r.run("del", "str")
    r.run("set", "str", "\xff\xff\xff")
    r.run("append", "str", "\xff\xff\xff\xff\xff\xff\xff\xff")
    r.run("append", "str", "\xff\xff\xff\xff\xff\xff\xff\xff")
    r.run("append", "str", "\xff\xff\xff\xff\xff\xff\xff\xff")
    r.run("append", "str", "\x0f")
    assert r.run("bitpos", "str", 0) == 216
    assert r.run("bitpos", "str", 0, 1) == 216
    assert r.run("bitpos", "str", 0, 2) == 216
    assert r.run("bitpos", "str", 0, 3) == 216
    assert r.run("bitpos", "str", 0, 4) == 216
    assert r.run("bitpos", "str", 0, 5) == 216
    assert r.run("bitpos", "str", 0, 6) == 216
    assert r.run("bitpos", "str", 0, 7) == 216
    assert r.run("bitpos", "str", 0, 8) == 216
    assert r.run("bitpos", "str", 0, 1, -1, "bit") == 216
    assert r.run("bitpos", "str", 0, 9, -1, "bit") == 216
    assert r.run("bitpos", "str", 0, 17, -1, "bit") == 216
    assert r.run("bitpos", "str", 0, 25, -1, "bit") == 216
    assert r.run("bitpos", "str", 0, 33, -1, "bit") == 216
    assert r.run("bitpos", "str", 0, 41, -1, "bit") == 216
    assert r.run("bitpos", "str", 0, 49, -1, "bit") == 216
    assert r.run("bitpos", "str", 0, 57, -1, "bit") == 216
    assert r.run("bitpos", "str", 0, 65, -1, "bit") == 216


def test_bitpos_bit_1_unaligned_full_word_reminder(r: ValkeyTestClient) -> None:
    """
    test {BITPOS bit=1 unaligned+full word+reminder} {
        r del str
        r set str "\x00\x00\x00" ; # Prefix
        # Followed by two (or four in 32 bit systems) full words
        r append str "\x00\x00\x00\x00\x00\x00\x00\x00"
        r append str "\x00\x00\x00\x00\x00\x00\x00\x00"
        r append str "\x00\x00\x00\x00\x00\x00\x00\x00"
        # First zero bit.
        r append str "\xf0"
        assert {[r bitpos str 1] == 216}
        assert {[r bitpos str 1 1] == 216}
        assert {[r bitpos str 1 2] == 216}
        assert {[r bitpos str 1 3] == 216}
        assert {[r bitpos str 1 4] == 216}
        assert {[r bitpos str 1 5] == 216}
        assert {[r bitpos str 1 6] == 216}
        assert {[r bitpos str 1 7] == 216}
        assert {[r bitpos str 1 8] == 216}

        assert {[r bitpos str 1 1 -1 bit] == 216}
        assert {[r bitpos str 1 9 -1 bit] == 216}
        assert {[r bitpos str 1 17 -1 bit] == 216}
        assert {[r bitpos str 1 25 -1 bit] == 216}
        assert {[r bitpos str 1 33 -1 bit] == 216}
        assert {[r bitpos str 1 41 -1 bit] == 216}
        assert {[r bitpos str 1 49 -1 bit] == 216}
        assert {[r bitpos str 1 57 -1 bit] == 216}
        assert {[r bitpos str 1 65 -1 bit] == 216}
    }
    """
    r.run("del", "str")
    r.run("set", "str", "\x00\x00\x00")
    r.run("append", "str", "\x00\x00\x00\x00\x00\x00\x00\x00")
    r.run("append", "str", "\x00\x00\x00\x00\x00\x00\x00\x00")
    r.run("append", "str", "\x00\x00\x00\x00\x00\x00\x00\x00")
    r.run("append", "str", "\xf0")
    assert r.run("bitpos", "str", 1) == 216
    assert r.run("bitpos", "str", 1, 1) == 216
    assert r.run("bitpos", "str", 1, 2) == 216
    assert r.run("bitpos", "str", 1, 3) == 216
    assert r.run("bitpos", "str", 1, 4) == 216
    assert r.run("bitpos", "str", 1, 5) == 216
    assert r.run("bitpos", "str", 1, 6) == 216
    assert r.run("bitpos", "str", 1, 7) == 216
    assert r.run("bitpos", "str", 1, 8) == 216
    assert r.run("bitpos", "str", 1, 1, -1, "bit") == 216
    assert r.run("bitpos", "str", 1, 9, -1, "bit") == 216
    assert r.run("bitpos", "str", 1, 17, -1, "bit") == 216
    assert r.run("bitpos", "str", 1, 25, -1, "bit") == 216
    assert r.run("bitpos", "str", 1, 33, -1, "bit") == 216
    assert r.run("bitpos", "str", 1, 41, -1, "bit") == 216
    assert r.run("bitpos", "str", 1, 49, -1, "bit") == 216
    assert r.run("bitpos", "str", 1, 57, -1, "bit") == 216
    assert r.run("bitpos", "str", 1, 65, -1, "bit") == 216


def test_bitpos_bit_1_returns_1_if_string_is_all_0_bits(r: ValkeyTestClient) -> None:
    """
    test {BITPOS bit=1 returns -1 if string is all 0 bits} {
        r set str ""
        for {set j 0} {$j < 20} {incr j} {
            assert {[r bitpos str 1] == -1}
            assert {[r bitpos str 1 0 -1 bit] == -1}
            r append str "\x00"
        }
    }
    """
    r.run("set", "str", "")
    j = 0
    while j < 20:
        assert r.run("bitpos", "str", 1) == -1
        assert r.run("bitpos", "str", 1, 0, -1, "bit") == -1
        r.run("append", "str", "\x00")
        j += 1


def test_bitpos_bit_0_works_with_intervals(r: ValkeyTestClient) -> None:
    """
    test {BITPOS bit=0 works with intervals} {
        r set str "\x00\xff\x00"
        assert {[r bitpos str 0 0 -1] == 0}
        assert {[r bitpos str 0 1 -1] == 16}
        assert {[r bitpos str 0 2 -1] == 16}
        assert {[r bitpos str 0 2 200] == 16}
        assert {[r bitpos str 0 1 1] == -1}

        assert {[r bitpos str 0 0 -1 bit] == 0}
        assert {[r bitpos str 0 8 -1 bit] == 16}
        assert {[r bitpos str 0 16 -1 bit] == 16}
        assert {[r bitpos str 0 16 200 bit] == 16}
        assert {[r bitpos str 0 8 8 bit] == -1}
    }
    """
    r.run("set", "str", "\x00\xff\x00")
    assert r.run("bitpos", "str", 0, 0, -1) == 0
    assert r.run("bitpos", "str", 0, 1, -1) == 16
    assert r.run("bitpos", "str", 0, 2, -1) == 16
    assert r.run("bitpos", "str", 0, 2, 200) == 16
    assert r.run("bitpos", "str", 0, 1, 1) == -1
    assert r.run("bitpos", "str", 0, 0, -1, "bit") == 0
    assert r.run("bitpos", "str", 0, 8, -1, "bit") == 16
    assert r.run("bitpos", "str", 0, 16, -1, "bit") == 16
    assert r.run("bitpos", "str", 0, 16, 200, "bit") == 16
    assert r.run("bitpos", "str", 0, 8, 8, "bit") == -1


def test_bitpos_bit_1_works_with_intervals(r: ValkeyTestClient) -> None:
    """
    test {BITPOS bit=1 works with intervals} {
        r set str "\x00\xff\x00"
        assert {[r bitpos str 1 0 -1] == 8}
        assert {[r bitpos str 1 1 -1] == 8}
        assert {[r bitpos str 1 2 -1] == -1}
        assert {[r bitpos str 1 2 200] == -1}
        assert {[r bitpos str 1 1 1] == 8}

        assert {[r bitpos str 1 0 -1 bit] == 8}
        assert {[r bitpos str 1 8 -1 bit] == 8}
        assert {[r bitpos str 1 16 -1 bit] == -1}
        assert {[r bitpos str 1 16 200 bit] == -1}
        assert {[r bitpos str 1 8 8 bit] == 8}
    }
    """
    r.run("set", "str", "\x00\xff\x00")
    assert r.run("bitpos", "str", 1, 0, -1) == 8
    assert r.run("bitpos", "str", 1, 1, -1) == 8
    assert r.run("bitpos", "str", 1, 2, -1) == -1
    assert r.run("bitpos", "str", 1, 2, 200) == -1
    assert r.run("bitpos", "str", 1, 1, 1) == 8
    assert r.run("bitpos", "str", 1, 0, -1, "bit") == 8
    assert r.run("bitpos", "str", 1, 8, -1, "bit") == 8
    assert r.run("bitpos", "str", 1, 16, -1, "bit") == -1
    assert r.run("bitpos", "str", 1, 16, 200, "bit") == -1
    assert r.run("bitpos", "str", 1, 8, 8, "bit") == 8


def test_bitpos_bit_0_changes_behavior_if_end_is_given(r: ValkeyTestClient) -> None:
    """
    test {BITPOS bit=0 changes behavior if end is given} {
        r set str "\xff\xff\xff"
        assert {[r bitpos str 0] == 24}
        assert {[r bitpos str 0 0] == 24}
        assert {[r bitpos str 0 0 -1] == -1}
        assert {[r bitpos str 0 0 -1 bit] == -1}
    }
    """
    r.run("set", "str", "\xff\xff\xff")
    assert r.run("bitpos", "str", 0) == 24
    assert r.run("bitpos", "str", 0, 0) == 24
    assert r.run("bitpos", "str", 0, 0, -1) == -1
    assert r.run("bitpos", "str", 0, 0, -1, "bit") == -1


def test_setbit_or_bitfield_only_increase_dirty_when_the_value_changed(r: ValkeyTestClient) -> None:
    """
    test {SETBIT/BITFIELD only increase dirty when the value changed} {
        r del foo{t} foo2{t} foo3{t}
        set dirty [s rdb_changes_since_last_save]

        # Create a new key, always increase the dirty.
        r setbit foo{t} 0 0
        r bitfield foo2{t} set i5 0 0
        set dirty2 [s rdb_changes_since_last_save]
        assert {$dirty2 == $dirty + 2}

        # No change.
        r setbit foo{t} 0 0
        r bitfield foo2{t} set i5 0 0
        set dirty3 [s rdb_changes_since_last_save]
        assert {$dirty3 == $dirty2}

        # Do a change and a no change.
        r setbit foo{t} 0 1
        r setbit foo{t} 0 1
        r setbit foo{t} 0 0
        r setbit foo{t} 0 0
        r bitfield foo2{t} set i5 0 1
        r bitfield foo2{t} set i5 0 1
        r bitfield foo2{t} set i5 0 0
        r bitfield foo2{t} set i5 0 0
        set dirty4 [s rdb_changes_since_last_save]
        assert {$dirty4 == $dirty3 + 4}

        # BITFIELD INCRBY always increase dirty.
        r bitfield foo3{t} incrby i5 0 1
        r bitfield foo3{t} incrby i5 0 1
        set dirty5 [s rdb_changes_since_last_save]
        assert {$dirty5 == $dirty4 + 2}

        # Change length only
        r setbit foo{t} 90 0
        r bitfield foo2{t} set i5 90 0
        set dirty6 [s rdb_changes_since_last_save]
        assert {$dirty6 == $dirty5 + 2}
    }
    """
    r.run("del", "foo{t}", "foo2{t}", "foo3{t}")
    dirty = s("rdb_changes_since_last_save")
    r.run("setbit", "foo{t}", 0, 0)
    r.run("bitfield", "foo2{t}", "set", "i5", 0, 0)
    dirty2 = s("rdb_changes_since_last_save")
    assert dirty2 == (dirty + 2)
    r.run("setbit", "foo{t}", 0, 0)
    r.run("bitfield", "foo2{t}", "set", "i5", 0, 0)
    dirty3 = s("rdb_changes_since_last_save")
    assert dirty3 == dirty2
    r.run("setbit", "foo{t}", 0, 1)
    r.run("setbit", "foo{t}", 0, 1)
    r.run("setbit", "foo{t}", 0, 0)
    r.run("setbit", "foo{t}", 0, 0)
    r.run("bitfield", "foo2{t}", "set", "i5", 0, 1)
    r.run("bitfield", "foo2{t}", "set", "i5", 0, 1)
    r.run("bitfield", "foo2{t}", "set", "i5", 0, 0)
    r.run("bitfield", "foo2{t}", "set", "i5", 0, 0)
    dirty4 = s("rdb_changes_since_last_save")
    assert dirty4 == (dirty3 + 4)
    r.run("bitfield", "foo3{t}", "incrby", "i5", 0, 1)
    r.run("bitfield", "foo3{t}", "incrby", "i5", 0, 1)
    dirty5 = s("rdb_changes_since_last_save")
    assert dirty5 == (dirty4 + 2)
    r.run("setbit", "foo{t}", 90, 0)
    r.run("bitfield", "foo2{t}", "set", "i5", 90, 0)
    dirty6 = s("rdb_changes_since_last_save")
    assert dirty6 == (dirty5 + 2)


def test_bitpos_bit_1_fuzzy_testing_using_setbit(r: ValkeyTestClient) -> None:
    """
    test {BITPOS bit=1 fuzzy testing using SETBIT} {
        r del str
        set max 524288; # 64k
        set first_one_pos -1
        for {set j 0} {$j < 1000} {incr j} {
            assert {[r bitpos str 1] == $first_one_pos}
            assert {[r bitpos str 1 0 -1 bit] == $first_one_pos}
            set pos [randomInt $max]
            r setbit str $pos 1
            if {$first_one_pos == -1 || $first_one_pos > $pos} {
                # Update the position of the first 1 bit in the array
                # if the bit we set is on the left of the previous one.
                set first_one_pos $pos
            }
        }
    }
    """
    r.run("del", "str")
    max = 524288
    first_one_pos = -1
    j = 0
    while j < 1000:
        assert r.run("bitpos", "str", 1) == first_one_pos
        assert r.run("bitpos", "str", 1, 0, -1, "bit") == first_one_pos
        pos = random_int(max)
        r.run("setbit", "str", pos, 1)
        if_(
            "$first_one_pos == -1 || $first_one_pos > $pos",
            "                # Update the position of the first 1 bit in the array\n                # if the bit we set is on the left of the previous one.\n                set first_one_pos $pos\n            ",
        )
        j += 1


def test_bitpos_bit_0_fuzzy_testing_using_setbit(r: ValkeyTestClient) -> None:
    """
    test {BITPOS bit=0 fuzzy testing using SETBIT} {
        set max 524288; # 64k
        set first_zero_pos $max
        r set str [string repeat "\xff" [expr $max/8]]
        for {set j 0} {$j < 1000} {incr j} {
            assert {[r bitpos str 0] == $first_zero_pos}
            if {$first_zero_pos == $max} {
                assert {[r bitpos str 0 0 -1 bit] == -1}
            } else {
                assert {[r bitpos str 0 0 -1 bit] == $first_zero_pos}
            }
            set pos [randomInt $max]
            r setbit str $pos 0
            if {$first_zero_pos > $pos} {
                # Update the position of the first 0 bit in the array
                # if the bit we clear is on the left of the previous one.
                set first_zero_pos $pos
            }
        }
    }
    """
    max = 524288
    first_zero_pos = max
    r.run("set", "str", string("repeat", "\xff", expr(max, "/8")))
    j = 0
    while j < 1000:
        assert r.run("bitpos", "str", 0) == first_zero_pos
        if first_zero_pos == max:
            assert r.run("bitpos", "str", 0, 0, -1, "bit") == -1
        else:
            assert_("[r bitpos str 0 0 -1 bit] == $first_zero_pos")
        pos = random_int(max)
        r.run("setbit", "str", pos, 0)
        if_(
            "$first_zero_pos > $pos",
            "                # Update the position of the first 0 bit in the array\n                # if the bit we clear is on the left of the previous one.\n                set first_zero_pos $pos\n            ",
        )
        j += 1


def test_bitpos_or_bitcount_fuzzy_testing_using_setbit(r: ValkeyTestClient) -> None:
    """
    test {BITPOS/BITCOUNT fuzzy testing using SETBIT} {
        # We have two start and end ranges, each range used to select a random
        # position, one for start position and one for end position.
        proc test_one {start1 end1 start2 end2 pos bit pos_type} {
            set start [randomRange $start1 $end1]
            set end [randomRange $start2 $end2]
            if {$start > $end} {
                # Swap start and end
                lassign [list $end $start] start end
            }
            set startbit $start
            set endbit $end
            # For byte index, we need to generate the real bit index
            if {[string equal $pos_type byte]} {
                set startbit [expr $start << 3]
                set endbit [expr ($end << 3) + 7]
            }
            # This means whether the test bit index is in the range.
            set inrange [expr ($pos >= $startbit && $pos <= $endbit) ? 1: 0]
            # For bitcount, there are four different results.
            # $inrange == 0 && $bit == 0, all bits in the range are set, so $endbit - $startbit + 1
            # $inrange == 0 && $bit == 1, all bits in the range are clear, so 0
            # $inrange == 1 && $bit == 0, all bits in the range are set but one, so $endbit - $startbit
            # $inrange == 1 && $bit == 1, all bits in the range are clear but one, so 1
            set res_count [expr ($endbit - $startbit + 1) * (1 - $bit) + $inrange * [expr $bit ? 1 : -1]]
            assert {[r bitpos str $bit $start $end $pos_type] == [expr $inrange ? $pos : -1]}
            assert {[r bitcount str $start $end $pos_type] == $res_count}
        }

        r del str
        set max 80;
        r setbit str [expr $max - 1] 0
        set bytes [expr $max >> 3]
        # First iteration sets all bits to 1, then set bit to 0 from 0 to max - 1
        # Second iteration sets all bits to 0, then set bit to 1 from 0 to max - 1
        for {set bit 0} {$bit < 2} {incr bit} {
            r bitop not str str
            for {set j 0} {$j < $max} {incr j} {
                r setbit str $j $bit

                # First iteration tests byte index and second iteration tests bit index.
                foreach {curr end pos_type} [list [expr $j >> 3] $bytes byte $j $max bit] {
                    # start==end set to bit position
                    test_one $curr $curr $curr $curr $j $bit $pos_type
                    # Both start and end are before bit position
                    if {$curr > 0} {
                        test_one 0 $curr 0 $curr $j $bit $pos_type
                    }
                    # Both start and end are after bit position
                    if {$curr < [expr $end - 1]} {
                        test_one [expr $curr + 1] $end [expr $curr + 1] $end $j $bit $pos_type
                    }
                    # start is before and end is after bit position
                    if {$curr > 0 && $curr < [expr $end - 1]} {
                        test_one 0 $curr [expr $curr +1] $end $j $bit $pos_type
                    }
                }

                # restore bit
                r setbit str $j [expr 1 - $bit]
            }
        }
    }
    """
    proc(
        "test_one",
        "start1 end1 start2 end2 pos bit pos_type",
        "            set start [randomRange $start1 $end1]\n            set end [randomRange $start2 $end2]\n            if {$start > $end} {\n                # Swap start and end\n                lassign [list $end $start] start end\n            }\n            set startbit $start\n            set endbit $end\n            # For byte index, we need to generate the real bit index\n            if {[string equal $pos_type byte]} {\n                set startbit [expr $start << 3]\n                set endbit [expr ($end << 3) + 7]\n            }\n            # This means whether the test bit index is in the range.\n            set inrange [expr ($pos >= $startbit && $pos <= $endbit) ? 1: 0]\n            # For bitcount, there are four different results.\n            # $inrange == 0 && $bit == 0, all bits in the range are set, so $endbit - $startbit + 1\n            # $inrange == 0 && $bit == 1, all bits in the range are clear, so 0\n            # $inrange == 1 && $bit == 0, all bits in the range are set but one, so $endbit - $startbit\n            # $inrange == 1 && $bit == 1, all bits in the range are clear but one, so 1\n            set res_count [expr ($endbit - $startbit + 1) * (1 - $bit) + $inrange * [expr $bit ? 1 : -1]]\n            assert {[r bitpos str $bit $start $end $pos_type] == [expr $inrange ? $pos : -1]}\n            assert {[r bitcount str $start $end $pos_type] == $res_count}\n        ",
    )
    r.run("del", "str")
    max = 80
    r.run("setbit", "str", expr(max, "-", 1), 0)
    bytes = expr(max, ">>", 3)
    bit = 0
    while bit < 2:
        r.run("bitop", "not", "str", "str")
        j = 0
        while j < max:
            r.run("setbit", "str", j, bit)
            foreach(
                "curr end pos_type",
                [expr(j, ">>", 3), bytes, "byte", j, max, "bit"],
                "                    # start==end set to bit position\n                    test_one $curr $curr $curr $curr $j $bit $pos_type\n                    # Both start and end are before bit position\n                    if {$curr > 0} {\n                        test_one 0 $curr 0 $curr $j $bit $pos_type\n                    }\n                    # Both start and end are after bit position\n                    if {$curr < [expr $end - 1]} {\n                        test_one [expr $curr + 1] $end [expr $curr + 1] $end $j $bit $pos_type\n                    }\n                    # start is before and end is after bit position\n                    if {$curr > 0 && $curr < [expr $end - 1]} {\n                        test_one 0 $curr [expr $curr +1] $end $j $bit $pos_type\n                    }\n                ",
            )
            r.run("setbit", "str", j, expr(1, "-", bit))
            j += 1
        bit += 1


"""
run_solo {bitops-large-memory} {
    start_server {tags {"bitops large-memory"}} {
        test "BIT pos larger than UINT_MAX" {
            set bytes [expr (1 << 29) + 1]
            set bitpos [expr (1 << 32)]
            set oldval [lindex [r config get proto-max-bulk-len] 1]
            r config set proto-max-bulk-len $bytes
            r setbit mykey $bitpos 1
            assert_equal $bytes [r strlen mykey]
            assert_equal 1 [r getbit mykey $bitpos]
            assert_equal [list 128 128 -1] [r bitfield mykey get u8 $bitpos set u8 $bitpos 255 get i8 $bitpos]
            assert_equal $bitpos [r bitpos mykey 1]
            assert_equal $bitpos [r bitpos mykey 1 [expr $bytes - 1]]
            if {$::accurate} {
                # set all bits to 1
                set mega [expr (1 << 23)]
                set part [string repeat "\xff" $mega]
                for {set i 0} {$i < 64} {incr i} {
                    r setrange mykey [expr $i * $mega] $part
                }
                r setrange mykey [expr $bytes - 1] "\xff"
                assert_equal [expr $bitpos + 8] [r bitcount mykey]
                assert_equal -1 [r bitpos mykey 0 0 [expr $bytes - 1]]
            }
            r config set proto-max-bulk-len $oldval
            r del mykey
        } {1}

        test "SETBIT values larger than UINT32_MAX and lzf_compress/lzf_decompress correctly" {
            set bytes [expr (1 << 32) + 1]
            set bitpos [expr (1 << 35)]
            set oldval [lindex [r config get proto-max-bulk-len] 1]
            r config set proto-max-bulk-len $bytes
            r setbit mykey $bitpos 1
            assert_equal $bytes [r strlen mykey]
            assert_equal 1 [r getbit mykey $bitpos]
            r debug reload ;# lzf_compress/lzf_decompress when RDB saving/loading.
            assert_equal 1 [r getbit mykey $bitpos]
            r config set proto-max-bulk-len $oldval
            r del mykey
        } {1} {needs:debug}
    }
}
"""


# --- stubs for unimplemented TCL helpers ---


def assert_(*args):
    raise NotImplementedError("assert_")


def catch(*args):
    raise NotImplementedError("catch")


def count_bits(*args):
    raise NotImplementedError("count_bits")


def count_bits_start_end(*args):
    raise NotImplementedError("count_bits_start_end")


def expr(*args):
    raise NotImplementedError("expr")


def foreach(*args):
    raise NotImplementedError("foreach")


def if_(*args):
    raise NotImplementedError("if_")


def list_(*args):
    raise NotImplementedError("list_")


def proc(*args):
    raise NotImplementedError("proc")


def random_int(*args):
    raise NotImplementedError("random_int")


def randstring(*args):
    raise NotImplementedError("randstring")


def s(*args):
    raise NotImplementedError("s")


def simulate_bit_op(*args):
    raise NotImplementedError("simulate_bit_op")


def string(*args):
    raise NotImplementedError("string")
