# ruff: noqa: PLR2004, ANN002, ANN201

from fnmatch import fnmatch

import pytest

from tests.valkey_test_client import ValkeyTestClient

pytestmark = [pytest.mark.sort]


"""
proc create_random_dataset {num cmd} {
    set tosort {}
    set result {}
    array set seenrand {}
    r del tosort
    for {set i 0} {$i < $num} {incr i} {
        # Make sure all the weights are different because
        # the server does not use a stable sort but Tcl does.
        while 1 {
            randpath {
                set rint [expr int(rand()*1000000)]
            } {
                set rint [expr rand()]
            }
            if {![info exists seenrand($rint)]} break
        }
        set seenrand($rint) x
        r $cmd tosort $i
        r set weight_$i $rint
        r hset wobj_$i weight $rint
        lappend tosort [list $i $rint]
    }
    set sorted [lsort -index 1 -real $tosort]
    for {set i 0} {$i < $num} {incr i} {
        lappend result [lindex $sorted $i 0]
    }
    set _ $result
}
"""


"""
proc check_sort_store_encoding {key} {
    set listpack_max_size [lindex [r config get list-max-ziplist-size] 1]

    # When the length or size of quicklist is less than the limit,
    # it will be converted to listpack.
    if {[r llen $key] <= $listpack_max_size} {
        assert_encoding listpack $key
    } else {
        assert_encoding quicklist $key
    }
}
"""


@pytest.mark.parametrize(
    ["num", "cmd", "enc", "title"],
    [
        (16, "lpush", "listpack", "Listpack"),
        (1000, "lpush", "quicklist", "Quicklist"),
        (10000, "lpush", "quicklist", "Big Quicklist"),
        (16, "sadd", "intset", "Intset"),
        (1000, "sadd", "hashtable", "Hash table"),
        (10000, "sadd", "hashtable", "Big Hash table"),
    ],
)
def test_title_sort_by_key(r: ValkeyTestClient, num: int, cmd: str, enc: str, title: str) -> None:
    """
    test "$title: SORT BY key" {
        assert_equal $result [r sort tosort BY weight_*]
    } {} {cluster:skip}
    """
    result = create_random_dataset(num, cmd)
    assert_encoding(enc, "tosort")
    assert result == r.run("sort", "tosort", "BY", "weight_*")


@pytest.mark.parametrize(
    ["num", "cmd", "enc", "title"],
    [
        (16, "lpush", "listpack", "Listpack"),
        (1000, "lpush", "quicklist", "Quicklist"),
        (10000, "lpush", "quicklist", "Big Quicklist"),
        (16, "sadd", "intset", "Intset"),
        (1000, "sadd", "hashtable", "Hash table"),
        (10000, "sadd", "hashtable", "Big Hash table"),
    ],
)
def test_title_sort_by_key_with_limit(r: ValkeyTestClient, num: int, cmd: str, enc: str, title: str) -> None:
    """
    test "$title: SORT BY key with limit" {
        assert_equal [lrange $result 5 9] [r sort tosort BY weight_* LIMIT 5 5]
    } {} {cluster:skip}
    """
    result = create_random_dataset(num, cmd)
    assert_encoding(enc, "tosort")
    assert lrange(result, 5, 9) == r.run("sort", "tosort", "BY", "weight_*", "LIMIT", 5, 5)


@pytest.mark.parametrize(
    ["num", "cmd", "enc", "title"],
    [
        (16, "lpush", "listpack", "Listpack"),
        (1000, "lpush", "quicklist", "Quicklist"),
        (10000, "lpush", "quicklist", "Big Quicklist"),
        (16, "sadd", "intset", "Intset"),
        (1000, "sadd", "hashtable", "Hash table"),
        (10000, "sadd", "hashtable", "Big Hash table"),
    ],
)
def test_title_sort_by_hash_field(r: ValkeyTestClient, num: int, cmd: str, enc: str, title: str) -> None:
    """
    test "$title: SORT BY hash field" {
        assert_equal $result [r sort tosort BY wobj_*->weight]
    } {} {cluster:skip}
    """
    result = create_random_dataset(num, cmd)
    assert_encoding(enc, "tosort")
    assert result == r.run("sort", "tosort", "BY", "wobj_*->weight")


def test_sort_get(r: ValkeyTestClient) -> None:
    """
    test "SORT GET #" {
        assert_equal [lsort -integer $result] [r sort tosort GET #]
    } {} {cluster:skip}
    """
    result = create_random_dataset(16, "lpush")
    assert sorted(result) == r.run("sort", "tosort", "GET", "#")


@pytest.mark.parametrize(["command"], [("SORT"), ("SORT_RO")])
def test_command_get_const(r: ValkeyTestClient, command: str) -> None:
    """
    test "$command GET <const>" {
        r del foo
        set res [r $command tosort GET foo]
        assert_equal 16 [llength $res]
        foreach item $res { assert_equal {} $item }
    } {} {cluster:skip}
    """
    r.run("del", "foo")
    res = r.run(command, "tosort", "GET", "foo")
    assert 16 == len(res)
    foreach("item", res, " assert_equal {} $item ")


def test_sort_get_key_and_hash_with_sanity_check(r: ValkeyTestClient) -> None:
    """
    test "SORT GET (key and hash) with sanity check" {
        set l1 [r sort tosort GET # GET weight_*]
        set l2 [r sort tosort GET # GET wobj_*->weight]
        foreach {id1 w1} $l1 {id2 w2} $l2 {
            assert_equal $id1 $id2
            assert_equal $w1 [r get weight_$id1]
            assert_equal $w2 [r get weight_$id1]
        }
    } {} {cluster:skip}
    """
    l1 = r.run("sort", "tosort", "GET", "#", "GET", "weight_*")
    l2 = r.run("sort", "tosort", "GET", "#", "GET", "wobj_*->weight")
    foreach(
        "id1 w1",
        l1,
        "id2 w2",
        l2,
        "            assert_equal $id1 $id2\n            assert_equal $w1 [r get weight_$id1]\n            assert_equal $w2 [r get weight_$id1]\n        ",
    )


@pytest.mark.xfail(reason="not implemented")
def test_sort_by_key_store(r: ValkeyTestClient) -> None:
    """
    test "SORT BY key STORE" {
        r sort tosort BY weight_* store sort-res
        assert_equal $result [r lrange sort-res 0 -1]
        assert_equal 16 [r llen sort-res]
        check_sort_store_encoding sort-res
    } {} {cluster:skip}
    """
    r.run("sort", "tosort", "BY", "weight_*", "store", "sort-res")
    # TODO: assert_equal result r lrange sort-res 0 -1
    assert 16 == r.run("llen", "sort-res")
    check_sort_store_encoding("sort-res")


@pytest.mark.xfail(reason="not implemented")
def test_sort_by_hash_field_store(r: ValkeyTestClient) -> None:
    """
    test "SORT BY hash field STORE" {
        r sort tosort BY wobj_*->weight store sort-res
        assert_equal $result [r lrange sort-res 0 -1]
        assert_equal 16 [r llen sort-res]
        check_sort_store_encoding sort-res
    } {} {cluster:skip}
    """
    r.run("sort", "tosort", "BY", "wobj_*->weight", "store", "sort-res")
    # TODO: assert_equal result r lrange sort-res 0 -1
    assert 16 == r.run("llen", "sort-res")
    check_sort_store_encoding("sort-res")


def test_sort_extracts_store_correctly(r: ValkeyTestClient) -> None:
    """
    test "SORT extracts STORE correctly" {
        r command getkeys sort abc store def
    } {abc def}
    """
    assert r.run("command", "getkeys", "sort", "abc", "store", "def") == "abc def"


def test_sort_ro_get_keys(r: ValkeyTestClient) -> None:
    """
    test "SORT_RO get keys" {
        r command getkeys sort_ro abc
    } {abc}
    """
    assert r.run("command", "getkeys", "sort_ro", "abc") == "abc"


def test_sort_extracts_multiple_store_correctly(r: ValkeyTestClient) -> None:
    """
    test "SORT extracts multiple STORE correctly" {
        r command getkeys sort abc store invalid store stillbad store def
    } {abc def}
    """
    assert (
        r.run("command", "getkeys", "sort", "abc", "store", "invalid", "store", "stillbad", "store", "def") == "abc def"
    )


@pytest.mark.xfail(reason="not implemented")
def test_sort_desc(r: ValkeyTestClient) -> None:
    """
    test "SORT DESC" {
        assert_equal [lsort -decreasing -integer $result] [r sort tosort DESC]
    }
    """
    # TODO: assert_equal lsort -decreasing -integer $result r sort tosort DESC


def test_sort_alpha_against_integer_encoded_strings(r: ValkeyTestClient) -> None:
    """
    test "SORT ALPHA against integer encoded strings" {
        r del mylist
        r lpush mylist 2
        r lpush mylist 1
        r lpush mylist 3
        r lpush mylist 10
        r sort mylist alpha
    } {1 10 2 3}
    """
    r.run("del", "mylist")
    r.run("lpush", "mylist", 2)
    r.run("lpush", "mylist", 1)
    r.run("lpush", "mylist", 3)
    r.run("lpush", "mylist", 10)
    assert r.run("sort", "mylist", "alpha") == "1 10 2 3"


def test_sort_sorted_set(r: ValkeyTestClient) -> None:
    """
    test "SORT sorted set" {
        r del zset
        r zadd zset 1 a
        r zadd zset 5 b
        r zadd zset 2 c
        r zadd zset 10 d
        r zadd zset 3 e
        r sort zset alpha desc
    } {e d c b a}
    """
    r.run("del", "zset")
    r.run("zadd", "zset", 1, "a")
    r.run("zadd", "zset", 5, "b")
    r.run("zadd", "zset", 2, "c")
    r.run("zadd", "zset", 10, "d")
    r.run("zadd", "zset", 3, "e")
    assert r.run("sort", "zset", "alpha", "desc") == "e d c b a"


def test_sort_sorted_set_by_nosort_should_retain_ordering(r: ValkeyTestClient) -> None:
    """
    test "SORT sorted set BY nosort should retain ordering" {
        r del zset
        r zadd zset 1 a
        r zadd zset 5 b
        r zadd zset 2 c
        r zadd zset 10 d
        r zadd zset 3 e
        r multi
        r sort zset by nosort asc
        r sort zset by nosort desc
        r exec
    } {{a c e b d} {d b e c a}}
    """
    r.run("del", "zset")
    r.run("zadd", "zset", 1, "a")
    r.run("zadd", "zset", 5, "b")
    r.run("zadd", "zset", 2, "c")
    r.run("zadd", "zset", 10, "d")
    r.run("zadd", "zset", 3, "e")
    r.run("multi")
    r.run("sort", "zset", "by", "nosort", "asc")
    r.run("sort", "zset", "by", "nosort", "desc")
    assert r.run("exec") == "{a c e b d} {d b e c a}"


def test_sort_sorted_set_by_nosort_limit(r: ValkeyTestClient) -> None:
    """
    test "SORT sorted set BY nosort + LIMIT" {
        r del zset
        r zadd zset 1 a
        r zadd zset 5 b
        r zadd zset 2 c
        r zadd zset 10 d
        r zadd zset 3 e
        assert_equal [r sort zset by nosort asc limit 0 1] {a}
        assert_equal [r sort zset by nosort desc limit 0 1] {d}
        assert_equal [r sort zset by nosort asc limit 0 2] {a c}
        assert_equal [r sort zset by nosort desc limit 0 2] {d b}
        assert_equal [r sort zset by nosort limit 5 10] {}
        assert_equal [r sort zset by nosort limit -10 100] {a c e b d}
    }
    """
    r.run("del", "zset")
    r.run("zadd", "zset", 1, "a")
    r.run("zadd", "zset", 5, "b")
    r.run("zadd", "zset", 2, "c")
    r.run("zadd", "zset", 10, "d")
    r.run("zadd", "zset", 3, "e")
    assert r.run("sort", "zset", "by", "nosort", "asc", "limit", 0, 1) == "a"
    assert r.run("sort", "zset", "by", "nosort", "desc", "limit", 0, 1) == "d"
    assert r.run("sort", "zset", "by", "nosort", "asc", "limit", 0, 2) == "a c"
    assert r.run("sort", "zset", "by", "nosort", "desc", "limit", 0, 2) == "d b"
    assert r.run("sort", "zset", "by", "nosort", "limit", 5, 10) == ""
    assert r.run("sort", "zset", "by", "nosort", "limit", -10, 100) == "a c e b d"


def test_sort_sorted_set_by_nosort_works_as_expected_from_scripts(r: ValkeyTestClient) -> None:
    """
    test "SORT sorted set BY nosort works as expected from scripts" {
        r del zset
        r zadd zset 1 a
        r zadd zset 5 b
        r zadd zset 2 c
        r zadd zset 10 d
        r zadd zset 3 e
        r eval {
            return {redis.call('sort',KEYS[1],'by','nosort','asc'),
                    redis.call('sort',KEYS[1],'by','nosort','desc')}
        } 1 zset
    } {{a c e b d} {d b e c a}}
    """
    r.run("del", "zset")
    r.run("zadd", "zset", 1, "a")
    r.run("zadd", "zset", 5, "b")
    r.run("zadd", "zset", 2, "c")
    r.run("zadd", "zset", 10, "d")
    r.run("zadd", "zset", 3, "e")
    assert (
        r.run(
            "eval",
            "            return {redis.call('sort',KEYS[1],'by','nosort','asc'),\n                    redis.call('sort',KEYS[1],'by','nosort','desc')}\n        ",
            1,
            "zset",
        )
        == "{a c e b d} {d b e c a}"
    )


def test_sort_sorted_set_inf_and_inf_handling(r: ValkeyTestClient) -> None:
    """
    test "SORT sorted set: +inf and -inf handling" {
        r del zset
        r zadd zset -100 a
        r zadd zset 200 b
        r zadd zset -300 c
        r zadd zset 1000000 d
        r zadd zset +inf max
        r zadd zset -inf min
        r zrange zset 0 -1
    } {min c a b d max}
    """
    r.run("del", "zset")
    r.run("zadd", "zset", -100, "a")
    r.run("zadd", "zset", 200, "b")
    r.run("zadd", "zset", -300, "c")
    r.run("zadd", "zset", 1000000, "d")
    r.run("zadd", "zset", float("+inf"), "max")
    r.run("zadd", "zset", float("-inf"), "min")
    assert r.run("zrange", "zset", 0, -1) == "min c a b d max"


def test_sort_regression_for_issue_19_sorting_floats(r: ValkeyTestClient) -> None:
    """
    test "SORT regression for issue #19, sorting floats" {
        r flushdb
        set floats {1.1 5.10 3.10 7.44 2.1 5.75 6.12 0.25 1.15}
        foreach x $floats {
            r lpush mylist $x
        }
        assert_equal [lsort -real $floats] [r sort mylist]
    }
    """
    r.run("flushdb")
    floats = "1.1 5.10 3.10 7.44 2.1 5.75 6.12 0.25 1.15"
    foreach("x", floats, "            r lpush mylist $x\n        ")
    assert sorted(floats) == r.run("sort", "mylist")


def test_sort_returns_an_empty_array_if_the_list_is_empty(r: ValkeyTestClient) -> None:
    """
    test "SORT returns an empty array if the list is empty" {
        r flushdb
        r sort mylist
    } {}
    """
    r.run("flushdb")
    r.run("sort", "mylist")


def test_sort_with_store_returns_zero_if_result_is_empty_github_issue_224(r: ValkeyTestClient) -> None:
    """
    test "SORT with STORE returns zero if result is empty (github issue 224)" {
        r flushdb
        r sort foo{t} store bar{t}
    } {0}
    """
    r.run("flushdb")
    assert r.run("sort", "foo{t}", "store", "bar{t}") == "0"


def test_sort_with_store_does_not_create_empty_lists_github_issue_224(r: ValkeyTestClient) -> None:
    """
    test "SORT with STORE does not create empty lists (github issue 224)" {
        r flushdb
        r lpush foo{t} bar
        r sort foo{t} alpha limit 10 10 store zap{t}
        r exists zap{t}
    } {0}
    """
    r.run("flushdb")
    r.run("lpush", "foo{t}", "bar")
    r.run("sort", "foo{t}", "alpha", "limit", 10, 10, "store", "zap{t}")
    assert r.run("exists", "zap{t}") == "0"


def test_sort_with_store_removes_key_if_result_is_empty_github_issue_227(r: ValkeyTestClient) -> None:
    """
    test "SORT with STORE removes key if result is empty (github issue 227)" {
        r flushdb
        r lpush foo{t} bar
        r sort emptylist{t} store foo{t}
        r exists foo{t}
    } {0}
    """
    r.run("flushdb")
    r.run("lpush", "foo{t}", "bar")
    r.run("sort", "emptylist{t}", "store", "foo{t}")
    assert r.run("exists", "foo{t}") == "0"


def test_sort_with_by_constant_and_store_should_still_order_output(r: ValkeyTestClient) -> None:
    """
    test "SORT with BY <constant> and STORE should still order output" {
        r del myset mylist
        r sadd myset a b c d e f g h i l m n o p q r s t u v z aa aaa azz
        r sort myset alpha by _ store mylist
        r lrange mylist 0 -1
    } {a aa aaa azz b c d e f g h i l m n o p q r s t u v z} {cluster:skip}
    """
    r.run("del", "myset", "mylist")
    r.run(
        "sadd",
        "myset",
        "a",
        "b",
        "c",
        "d",
        "e",
        "f",
        "g",
        "h",
        "i",
        "l",
        "m",
        "n",
        "o",
        "p",
        "q",
        "r",
        "s",
        "t",
        "u",
        "v",
        "z",
        "aa",
        "aaa",
        "azz",
    )
    r.run("sort", "myset", "alpha", "by", "_", "store", "mylist")
    assert r.run("lrange", "mylist", 0, -1) == "a aa aaa azz b c d e f g h i l m n o p q r s t u v z"


def test_sort_will_complain_with_numerical_sorting_and_bad_doubles_1(r: ValkeyTestClient) -> None:
    """
    test "SORT will complain with numerical sorting and bad doubles (1)" {
        r del myset
        r sadd myset 1 2 3 4 not-a-double
        set e {}
        catch {r sort myset} e
        set e
    } {*ERR*double*}
    """
    r.run("del", "myset")
    r.run("sadd", "myset", 1, 2, 3, 4, "not-a-double")
    e = []
    try:
        e = r.run("sort", "myset")
    except Exception as _catch_err:
        e = str(_catch_err)
    assert fnmatch(str(e), "*ERR*double*")


def test_sort_will_complain_with_numerical_sorting_and_bad_doubles_2(r: ValkeyTestClient) -> None:
    """
    test "SORT will complain with numerical sorting and bad doubles (2)" {
        r del myset
        r sadd myset 1 2 3 4
        r mset score:1 10 score:2 20 score:3 30 score:4 not-a-double
        set e {}
        catch {r sort myset by score:*} e
        set e
    } {*ERR*double*} {cluster:skip}
    """
    r.run("del", "myset")
    r.run("sadd", "myset", 1, 2, 3, 4)
    r.run("mset", "score:1", 10, "score:2", 20, "score:3", 30, "score:4", "not-a-double")
    e = []
    try:
        e = r.run("sort", "myset", "by", "score:*")
    except Exception as _catch_err:
        e = str(_catch_err)
    assert fnmatch(str(e), "*ERR*double*")


def test_sort_by_sub_sorts_lexicographically_if_score_is_the_same(r: ValkeyTestClient) -> None:
    """
    test "SORT BY sub-sorts lexicographically if score is the same" {
        r del myset
        r sadd myset a b c d e f g h i l m n o p q r s t u v z aa aaa azz
        foreach ele {a aa aaa azz b c d e f g h i l m n o p q r s t u v z} {
            set score:$ele 100
        }
        r sort myset by score:*
    } {a aa aaa azz b c d e f g h i l m n o p q r s t u v z} {cluster:skip}
    """
    r.run("del", "myset")
    r.run(
        "sadd",
        "myset",
        "a",
        "b",
        "c",
        "d",
        "e",
        "f",
        "g",
        "h",
        "i",
        "l",
        "m",
        "n",
        "o",
        "p",
        "q",
        "r",
        "s",
        "t",
        "u",
        "v",
        "z",
        "aa",
        "aaa",
        "azz",
    )
    foreach("ele", "a aa aaa azz b c d e f g h i l m n o p q r s t u v z", "            set score:$ele 100\n        ")
    assert r.run("sort", "myset", "by", "score:*") == "a aa aaa azz b c d e f g h i l m n o p q r s t u v z"


def test_sort_get_with_pattern_ending_with_just_does_not_get_hash_field(r: ValkeyTestClient) -> None:
    """
    test "SORT GET with pattern ending with just -> does not get hash field" {
        r del mylist
        r lpush mylist a
        r set x:a-> 100
        r sort mylist by num get x:*->
    } {100} {cluster:skip}
    """
    r.run("del", "mylist")
    r.run("lpush", "mylist", "a")
    r.run("set", "x:a->", 100)
    assert r.run("sort", "mylist", "by", "num", "get", "x:*->") == "100"


def test_sort_by_nosort_retains_native_order_for_lists(r: ValkeyTestClient) -> None:
    """
    test "SORT by nosort retains native order for lists" {
        r del testa
        r lpush testa 2 1 4 3 5
        r sort testa by nosort
    } {5 3 4 1 2} {cluster:skip}
    """
    r.run("del", "testa")
    r.run("lpush", "testa", 2, 1, 4, 3, 5)
    assert r.run("sort", "testa", "by", "nosort") == "5 3 4 1 2"


def test_sort_by_nosort_plus_store_retains_native_order_for_lists(r: ValkeyTestClient) -> None:
    """
    test "SORT by nosort plus store retains native order for lists" {
        r del testa
        r lpush testa 2 1 4 3 5
        r sort testa by nosort store testb
        r lrange testb 0 -1
    } {5 3 4 1 2} {cluster:skip}
    """
    r.run("del", "testa")
    r.run("lpush", "testa", 2, 1, 4, 3, 5)
    r.run("sort", "testa", "by", "nosort", "store", "testb")
    assert r.run("lrange", "testb", 0, -1) == "5 3 4 1 2"


def test_sort_by_nosort_with_limit_returns_based_on_original_list_order(r: ValkeyTestClient) -> None:
    """
    test "SORT by nosort with limit returns based on original list order" {
        r sort testa by nosort limit 0 3 store testb
        r lrange testb 0 -1
    } {5 3 4} {cluster:skip}
    """
    r.run("sort", "testa", "by", "nosort", "limit", 0, 3, "store", "testb")
    assert r.run("lrange", "testb", 0, -1) == "5 3 4"


def test_sort_ro_successful_case(r: ValkeyTestClient) -> None:
    """
    test "SORT_RO - Successful case" {
        r del mylist
        r lpush mylist a
        r set x:a 100
        r sort_ro mylist by nosort get x:*->
    } {100} {cluster:skip}
    """
    r.run("del", "mylist")
    r.run("lpush", "mylist", "a")
    r.run("set", "x:a", 100)
    assert r.run("sort_ro", "mylist", "by", "nosort", "get", "x:*->") == "100"


def test_sort_ro_cannot_run_with_store_arg(r: ValkeyTestClient) -> None:
    """
    test "SORT_RO - Cannot run with STORE arg" {
        catch {r sort_ro foolist STORE bar} e
        set e
    } {ERR syntax error}
    """
    try:
        e = r.run("sort_ro", "foolist", "STORE", "bar")
    except Exception as _catch_err:
        e = str(_catch_err)
    assert e == "ERR syntax error"


def test_setrange_with_huge_offset(r: ValkeyTestClient) -> None:
    """
    test {SETRANGE with huge offset} {
        r lpush L 2 1 0
        # expecting a different outcome on 32 and 64 bit systems
        foreach value {9223372036854775807 2147483647} {
            catch {[r sort_ro L by a limit 2 $value]} res
            if {![string match "2" $res] && ![string match "*out of range*" $res]} {
                assert_not_equal $res "expecting an error or 2"
            }
        }
    }
    """
    r.run("lpush", "L", 2, 1, 0)
    foreach(
        "value",
        "9223372036854775807 2147483647",
        '            catch {[r sort_ro L by a limit 2 $value]} res\n            if {![string match "2" $res] && ![string match "*out of range*" $res]} {\n                assert_not_equal $res "expecting an error or 2"\n            }\n        ',
    )


def test_sort_store_quicklist_with_the_right_options(r: ValkeyTestClient) -> None:
    """
    test {SORT STORE quicklist with the right options} {
        set origin_config [config_get_set list-max-listpack-size -1]
        r del lst{t} lst_dst{t}
        r config set list-max-listpack-size -1
        r config set list-compress-depth 12
        r lpush lst{t} {*}[split [string repeat "1" 6000] ""]
        r sort lst{t} store lst_dst{t}
        assert_encoding quicklist lst_dst{t}
        assert_match "*ql_listpack_max:-1 ql_compressed:1*" [r debug object lst_dst{t}]
        config_set list-max-listpack-size $origin_config
    } {} {needs:debug}
    """
    origin_config = config_get_set("list-max-listpack-size", -1)
    r.run("del", "lst{t}", "lst_dst{t}")
    r.run("config", "set", "list-max-listpack-size", -1)
    r.run("config", "set", "list-compress-depth", 12)
    r.run("lpush", "lst{t}", "*", split(string("repeat", "1", 6000), ""))
    r.run("sort", "lst{t}", "store", "lst_dst{t}")
    assert_encoding("quicklist", "lst_dst{t}")
    assert fnmatch(str(r.run("debug", "object", "lst_dst{t}")), "*ql_listpack_max:-1 ql_compressed:1*")
    config_set("list-max-listpack-size", origin_config)


"""
start_cluster 1 0 {tags {"external:skip cluster sort"}} {
    r flushall
    r lpush "{a}mylist" 1 2 3
    r set "{a}by1" 20
    r set "{a}by2" 30
    r set "{a}by3" 0
    r set "{a}get1" 200
    r set "{a}get2" 100
    r set "{a}get3" 30

    test "sort by in cluster mode" {
        catch {r sort "{a}mylist" by by*} e
        assert_match {ERR BY option of SORT denied in Cluster mode when *} $e
        assert_equal {3 1 2} [r sort "{a}mylist" by "{a}by*"]
        assert_equal {3 1 2} [r sort "{a}mylist" by "{a}by*" get #]
    }

    test "sort get in cluster mode" {
        catch {r sort "{a}mylist" by "{a}by*" get get*} e
        assert_match {ERR GET option of SORT denied in Cluster mode when *} $e
        assert_equal {30 200 100} [r sort "{a}mylist" by "{a}by*" get "{a}get*"]
        assert_equal {30 3 200 1 100 2} [r sort "{a}mylist" by "{a}by*" get "{a}get*" get #]
    }

    test "sort_ro by in cluster mode" {
        catch {r sort_ro "{a}mylist" by by*} e
        assert_match {ERR BY option of SORT denied in Cluster mode when *} $e
        assert_equal {3 1 2} [r sort_ro "{a}mylist" by "{a}by*"]
        assert_equal {3 1 2} [r sort_ro "{a}mylist" by "{a}by*" get #]
    }

    test "sort_ro get in cluster mode" {
        catch {r sort_ro "{a}mylist" by "{a}by*" get get*} e
        assert_match {ERR GET option of SORT denied in Cluster mode when *} $e
        assert_equal {30 200 100} [r sort_ro "{a}mylist" by "{a}by*" get "{a}get*"]
        assert_equal {30 3 200 1 100 2} [r sort_ro "{a}mylist" by "{a}by*" get "{a}get*" get #]
    }
}
"""


# --- stubs for unimplemented TCL helpers ---


def assert_encoding(*args):
    raise NotImplementedError("assert_encoding")


def check_sort_store_encoding(*args):
    raise NotImplementedError("check_sort_store_encoding")


def config_get_set(*args):
    raise NotImplementedError("config_get_set")


def config_set(*args):
    raise NotImplementedError("config_set")


def create_random_dataset(*args):
    raise NotImplementedError("create_random_dataset")


def foreach(*args):
    raise NotImplementedError("foreach")


def lrange(*args):
    raise NotImplementedError("lrange")


def split(*args):
    raise NotImplementedError("split")


def string(*args):
    raise NotImplementedError("string")
