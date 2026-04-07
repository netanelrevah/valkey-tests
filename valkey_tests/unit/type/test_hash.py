# ruff: noqa: PLR2004, F841, RUF043, ANN001, ANN002, ANN201

from fnmatch import fnmatch

import pytest

from tests.valkey_test_client import ValkeyTestClient

pytestmark = [pytest.mark.hash]


def test_hset_or_hlen_small_hash_creation(r: ValkeyTestClient) -> None:
    """
    test {HSET/HLEN - Small hash creation} {
        array set smallhash {}
        for {set i 0} {$i < 8} {incr i} {
            set key __avoid_collisions__[randstring 0 8 alpha]
            set val __avoid_collisions__[randstring 0 8 alpha]
            if {[info exists smallhash($key)]} {
                incr i -1
                continue
            }
            r hset smallhash $key $val
            set smallhash($key) $val
        }
        list [r hlen smallhash]
    } {8}
    """
    array("set", "smallhash", "")
    i = 0
    while i < 8:
        key = "__avoid_collisions__[randstring"
        val = "__avoid_collisions__[randstring"
        if_("[info exists smallhash($key)]", "                incr i -1\n                continue\n            ")
        r.run("hset", "smallhash", key, val)
        set_("smallhash($key)", val)
        i += 1
    assert [r.run("hlen", "smallhash")] == "8"


def test_is_the_small_hash_encoded_with_a_listpack(r: ValkeyTestClient) -> None:
    """
    test {Is the small hash encoded with a listpack?} {
        assert_encoding listpack smallhash
    }
    """
    assert_encoding("listpack", "smallhash")


"""
proc create_hash {key entries} {
    r del $key
    foreach entry $entries {
        r hset $key [lindex $entry 0] [lindex $entry 1]
    }
}
"""


"""
proc get_keys {l} {
    set res {}
    foreach entry $l {
        set key [lindex $entry 0]
        lappend res $key
    }
    return $res
}
"""


"""
set original_max_value lindex [r config get hash-max-ziplist-value] 1
"""


"""
r config set hash-max-ziplist-value 10
"""


"""
create_hash myhash contents
"""


"""
assert_encoding type myhash
"""


"""
assert_morethan memory_usage myhash 0
"""


@pytest.mark.parametrize(
    ["type", "contents"], [("listpack", "{a 1} {b 2} {c 3}"), ("hashtable", "{a 1} {b 2} {[randstring 70 90 alpha] 3}")]
)
def test_hrandfield_type(r: ValkeyTestClient, type, contents) -> None:
    """
    test "HRANDFIELD - $type" {
        unset -nocomplain myhash
        array set myhash {}
        for {set i 0} {$i < 100} {incr i} {
            set key [r hrandfield myhash]
            set myhash($key) 1
        }
        assert_equal [lsort [get_keys $contents]] [lsort [array names myhash]]
    }
    """
    unset("-nocomplain", "myhash")
    array("set", "myhash", "")
    i = 0
    while i < 100:
        key = r.run("hrandfield", "myhash")
        set_("myhash($key)", 1)
        i += 1
    assert sorted(get_keys(contents)) == sorted(array("names", "myhash"))


"""
r config set hash-max-ziplist-value original_max_value
"""


def test_hrandfield_with_resp3(r: ValkeyTestClient) -> None:
    """
    test "HRANDFIELD with RESP3" {
        r hello 3
        set res [r hrandfield myhash 3 withvalues]
        assert_equal [llength $res] 3
        assert_equal [llength [lindex $res 1]] 2

        set res [r hrandfield myhash 3]
        assert_equal [llength $res] 3
        assert_equal [llength [lindex $res 1]] 1
        r hello 2
    }
    """
    r.run("hello", 3)
    res = r.run("hrandfield", "myhash", 3, "withvalues")
    assert len(res) == 3
    assert len(res[1]) == 2
    res = r.run("hrandfield", "myhash", 3)
    assert len(res) == 3
    assert len(res[1]) == 1
    r.run("hello", 2)


def test_hrandfield_count_of_0_is_handled_correctly(r: ValkeyTestClient) -> None:
    """
    test "HRANDFIELD count of 0 is handled correctly" {
        r hrandfield myhash 0
    } {}
    """
    r.run("hrandfield", "myhash", 0)


def test_hrandfield_count_overflow(r: ValkeyTestClient) -> None:
    """
    test "HRANDFIELD count overflow" {
        r hmset myhash a 1
        assert_error {*value is out of range*} {r hrandfield myhash -9223372036854770000 withvalues}
        assert_error {*value is out of range*} {r hrandfield myhash -9223372036854775808 withvalues}
        assert_error {*value is out of range*} {r hrandfield myhash -9223372036854775808}
    } {}
    """
    r.run("hmset", "myhash", "a", 1)
    with pytest.raises(Exception, match=".*value\\ is\\ out\\ of\\ range.*"):
        r.run("hrandfield", "myhash", -9223372036854770000, "withvalues")
    with pytest.raises(Exception, match=".*value\\ is\\ out\\ of\\ range.*"):
        r.run("hrandfield", "myhash", -9223372036854775808, "withvalues")
    with pytest.raises(Exception, match=".*value\\ is\\ out\\ of\\ range.*"):
        r.run("hrandfield", "myhash", -9223372036854775808)


def test_hrandfield_with_count_against_non_existing_key(r: ValkeyTestClient) -> None:
    """
    test "HRANDFIELD with <count> against non existing key" {
        r hrandfield nonexisting_key 100
    } {}
    """
    r.run("hrandfield", "nonexisting_key", 100)


"""
r readraw 1
"""


def test_hrandfield_count_of_0_is_handled_correctly_emptyarray(r: ValkeyTestClient) -> None:
    """
    test "HRANDFIELD count of 0 is handled correctly - emptyarray" {
        r hrandfield myhash 0
    } {*0}
    """
    assert fnmatch(str(r.run("hrandfield", "myhash", 0)), "*0")


def test_hrandfield_with_count_against_non_existing_key_emptyarray(r: ValkeyTestClient) -> None:
    """
    test "HRANDFIELD with <count> against non existing key - emptyarray" {
        r hrandfield nonexisting_key 100
    } {*0}
    """
    assert fnmatch(str(r.run("hrandfield", "nonexisting_key", 100)), "*0")


"""
r readraw 0
"""


@pytest.mark.parametrize(
    ["type", "contents"],
    [
        ("hashtable", "{a 1} {b 2} {c 3} {d 4} {e 5} {6 f} {7 g} {8 h} {9 i} {[randstring 70 90 alpha] 10}"),
        ("listpack", "{a 1} {b 2} {c 3} {d 4} {e 5} {6 f} {7 g} {8 h} {9 i} {10 j}"),
    ],
)
def test_hrandfield_with_count_type(r: ValkeyTestClient, type, contents) -> None:
    """
    test "HRANDFIELD with <count> - $type" {
        set original_max_value [lindex [r config get hash-max-ziplist-value] 1]
        r config set hash-max-ziplist-value 10
        create_hash myhash $contents
        assert_encoding $type myhash

        # create a dict for easy lookup
        set mydict [dict create {*}[r hgetall myhash]]

        # We'll stress different parts of the code, see the implementation
        # of HRANDFIELD for more information, but basically there are
        # four different code paths.

        # PATH 1: Use negative count.

        # 1) Check that it returns repeated elements with and without values.
        set res [r hrandfield myhash -20]
        assert_equal [llength $res] 20
        set res [r hrandfield myhash -1001]
        assert_equal [llength $res] 1001
        # again with WITHVALUES
        set res [r hrandfield myhash -20 withvalues]
        assert_equal [llength $res] 40
        set res [r hrandfield myhash -1001 withvalues]
        assert_equal [llength $res] 2002

        # Test random uniform distribution
        # df = 9, 40 means 0.00001 probability
        set res [r hrandfield myhash -1000]
        assert_lessthan [chi_square_value $res] 40

        # 2) Check that all the elements actually belong to the original hash.
        foreach {key val} $res {
            assert {[dict exists $mydict $key]}
        }

        # 3) Check that eventually all the elements are returned.
        #    Use both WITHVALUES and without
        unset -nocomplain auxset
        set iterations 1000
        while {$iterations != 0} {
            incr iterations -1
            if {[expr {$iterations % 2}] == 0} {
                set res [r hrandfield myhash -3 withvalues]
                foreach {key val} $res {
                    dict append auxset $key $val
                }
            } else {
                set res [r hrandfield myhash -3]
                foreach key $res {
                    dict append auxset $key $val
                }
            }
            if {[lsort [dict keys $mydict]] eq
                [lsort [dict keys $auxset]]} {
                break;
            }
        }
        assert {$iterations != 0}

        # PATH 2: positive count (unique behavior) with requested size
        # equal or greater than set size.
        foreach size {10 20} {
            set res [r hrandfield myhash $size]
            assert_equal [llength $res] 10
            assert_equal [lsort $res] [lsort [dict keys $mydict]]

            # again with WITHVALUES
            set res [r hrandfield myhash $size withvalues]
            assert_equal [llength $res] 20
            assert_equal [lsort $res] [lsort $mydict]
        }

        # PATH 3: Ask almost as elements as there are in the set.
        # In this case the implementation will duplicate the original
        # set and will remove random elements up to the requested size.
        #
        # PATH 4: Ask a number of elements definitely smaller than
        # the set size.
        #
        # We can test both the code paths just changing the size but
        # using the same code.
        foreach size {8 2} {
            set res [r hrandfield myhash $size]
            assert_equal [llength $res] $size
            # again with WITHVALUES
            set res [r hrandfield myhash $size withvalues]
            assert_equal [llength $res] [expr {$size * 2}]

            # 1) Check that all the elements actually belong to the
            # original set.
            foreach ele [dict keys $res] {
                assert {[dict exists $mydict $ele]}
            }

            # 2) Check that eventually all the elements are returned.
            #    Use both WITHVALUES and without
            unset -nocomplain auxset
            unset -nocomplain allkey
            set iterations [expr {1000 / $size}]
            set all_ele_return false
            while {$iterations != 0} {
                incr iterations -1
                if {[expr {$iterations % 2}] == 0} {
                    set res [r hrandfield myhash $size withvalues]
                    foreach {key value} $res {
                        dict append auxset $key $value
                        lappend allkey $key
                    }
                } else {
                    set res [r hrandfield myhash $size]
                    foreach key $res {
                        dict append auxset $key
                        lappend allkey $key
                    }
                }
                if {[lsort [dict keys $mydict]] eq
                    [lsort [dict keys $auxset]]} {
                    set all_ele_return true
                }
            }
            assert_equal $all_ele_return true
            # df = 9, 40 means 0.00001 probability
            assert_lessthan [chi_square_value $allkey] 40
        }
    }
    """
    original_max_value = r.run("config", "get", "hash-max-ziplist-value")[1]
    r.run("config", "set", "hash-max-ziplist-value", 10)
    create_hash("myhash", contents)
    assert_encoding(type, "myhash")
    mydict = dict_("create", "*", r.run("hgetall", "myhash"))
    res = r.run("hrandfield", "myhash", -20)
    assert len(res) == 20
    res = r.run("hrandfield", "myhash", -1001)
    assert len(res) == 1001
    res = r.run("hrandfield", "myhash", -20, "withvalues")
    assert len(res) == 40
    res = r.run("hrandfield", "myhash", -1001, "withvalues")
    assert len(res) == 2002
    res = r.run("hrandfield", "myhash", -1000)
    assert_lessthan(chi_square_value(res), 40)
    foreach("key val", res, "                assert {[dict exists $mydict $key]}\n            ")
    unset("-nocomplain", "auxset")
    iterations = 1000
    while_(
        "$iterations != 0",
        "                incr iterations -1\n                if {[expr {$iterations % 2}] == 0} {\n                    set res [r hrandfield myhash -3 withvalues]\n                    foreach {key val} $res {\n                        dict append auxset $key $val\n                    }\n                } else {\n                    set res [r hrandfield myhash -3]\n                    foreach key $res {\n                        dict append auxset $key $val\n                    }\n                }\n                if {[lsort [dict keys $mydict]] eq\n                    [lsort [dict keys $auxset]]} {\n                    break;\n                }\n            ",
    )
    assert iterations != 0
    foreach(
        "size",
        "10 20",
        "                set res [r hrandfield myhash $size]\n                assert_equal [llength $res] 10\n                assert_equal [lsort $res] [lsort [dict keys $mydict]]\n\n                # again with WITHVALUES\n                set res [r hrandfield myhash $size withvalues]\n                assert_equal [llength $res] 20\n                assert_equal [lsort $res] [lsort $mydict]\n            ",
    )
    foreach(
        "size",
        "8 2",
        "                set res [r hrandfield myhash $size]\n                assert_equal [llength $res] $size\n                # again with WITHVALUES\n                set res [r hrandfield myhash $size withvalues]\n                assert_equal [llength $res] [expr {$size * 2}]\n\n                # 1) Check that all the elements actually belong to the\n                # original set.\n                foreach ele [dict keys $res] {\n                    assert {[dict exists $mydict $ele]}\n                }\n\n                # 2) Check that eventually all the elements are returned.\n                #    Use both WITHVALUES and without\n                unset -nocomplain auxset\n                unset -nocomplain allkey\n                set iterations [expr {1000 / $size}]\n                set all_ele_return false\n                while {$iterations != 0} {\n                    incr iterations -1\n                    if {[expr {$iterations % 2}] == 0} {\n                        set res [r hrandfield myhash $size withvalues]\n                        foreach {key value} $res {\n                            dict append auxset $key $value\n                            lappend allkey $key\n                        }\n                    } else {\n                        set res [r hrandfield myhash $size]\n                        foreach key $res {\n                            dict append auxset $key\n                            lappend allkey $key\n                        }\n                    }\n                    if {[lsort [dict keys $mydict]] eq\n                        [lsort [dict keys $auxset]]} {\n                        set all_ele_return true\n                    }\n                }\n                assert_equal $all_ele_return true\n                # df = 9, 40 means 0.00001 probability\n                assert_lessthan [chi_square_value $allkey] 40\n            ",
    )


"""
r config set hash-max-ziplist-value original_max_value
"""


def test_hset_or_hlen_big_hash_creation(r: ValkeyTestClient) -> None:
    """
    test {HSET/HLEN - Big hash creation} {
        array set bighash {}
        for {set i 0} {$i < 1024} {incr i} {
            set key __avoid_collisions__[randstring 0 8 alpha]
            set val __avoid_collisions__[randstring 0 8 alpha]
            if {[info exists bighash($key)]} {
                incr i -1
                continue
            }
            r hset bighash $key $val
            set bighash($key) $val
        }
        list [r hlen bighash]
    } {1024}
    """
    array("set", "bighash", "")
    i = 0
    while i < 1024:
        key = "__avoid_collisions__[randstring"
        val = "__avoid_collisions__[randstring"
        if_("[info exists bighash($key)]", "                incr i -1\n                continue\n            ")
        r.run("hset", "bighash", key, val)
        set_("bighash($key)", val)
        i += 1
    assert [r.run("hlen", "bighash")] == "1024"


def test_is_the_big_hash_encoded_with_an_hash_table(r: ValkeyTestClient) -> None:
    """
    test {Is the big hash encoded with an hash table?} {
        assert_encoding hashtable bighash
    }
    """
    assert_encoding("hashtable", "bighash")


def test_hget_against_the_small_hash(r: ValkeyTestClient) -> None:
    """
    test {HGET against the small hash} {
        set err {}
        foreach k [array names smallhash *] {
            if {$smallhash($k) ne [r hget smallhash $k]} {
                set err "$smallhash($k) != [r hget smallhash $k]"
                break
            }
        }
        set _ $err
    } {}
    """
    err = ""
    foreach(
        "k",
        array("names", "smallhash", "*"),
        '            if {$smallhash($k) ne [r hget smallhash $k]} {\n                set err "$smallhash($k) != [r hget smallhash $k]"\n                break\n            }\n        ',
    )
    _ = err


def test_hget_against_the_big_hash(r: ValkeyTestClient) -> None:
    """
    test {HGET against the big hash} {
        set err {}
        foreach k [array names bighash *] {
            if {$bighash($k) ne [r hget bighash $k]} {
                set err "$bighash($k) != [r hget bighash $k]"
                break
            }
        }
        set _ $err
    } {}
    """
    err = ""
    foreach(
        "k",
        array("names", "bighash", "*"),
        '            if {$bighash($k) ne [r hget bighash $k]} {\n                set err "$bighash($k) != [r hget bighash $k]"\n                break\n            }\n        ',
    )
    _ = err


def test_hget_against_non_existing_key(r: ValkeyTestClient) -> None:
    """
    test {HGET against non existing key} {
        set rv {}
        lappend rv [r hget smallhash __123123123__]
        lappend rv [r hget bighash __123123123__]
        set _ $rv
    } {{} {}}
    """
    rv = []
    rv.append(r.run("hget", "smallhash", "__123123123__"))
    rv.append(r.run("hget", "bighash", "__123123123__"))
    assert rv == "{} {}"


def test_hset_in_update_and_insert_mode(r: ValkeyTestClient) -> None:
    """
    test {HSET in update and insert mode} {
        set rv {}
        set k [lindex [array names smallhash *] 0]
        lappend rv [r hset smallhash $k newval1]
        set smallhash($k) newval1
        lappend rv [r hget smallhash $k]
        lappend rv [r hset smallhash __foobar123__ newval]
        set k [lindex [array names bighash *] 0]
        lappend rv [r hset bighash $k newval2]
        set bighash($k) newval2
        lappend rv [r hget bighash $k]
        lappend rv [r hset bighash __foobar123__ newval]
        lappend rv [r hdel smallhash __foobar123__]
        lappend rv [r hdel bighash __foobar123__]
        set _ $rv
    } {0 newval1 1 0 newval2 1 1 1}
    """
    rv = []
    k = array("names", "smallhash", "*")[0]
    rv.append(r.run("hset", "smallhash", k, "newval1"))
    set_("smallhash($k)", "newval1")
    rv.append(r.run("hget", "smallhash", k))
    rv.append(r.run("hset", "smallhash", "__foobar123__", "newval"))
    k = array("names", "bighash", "*")[0]
    rv.append(r.run("hset", "bighash", k, "newval2"))
    set_("bighash($k)", "newval2")
    rv.append(r.run("hget", "bighash", k))
    rv.append(r.run("hset", "bighash", "__foobar123__", "newval"))
    rv.append(r.run("hdel", "smallhash", "__foobar123__"))
    rv.append(r.run("hdel", "bighash", "__foobar123__"))
    assert rv == "0 newval1 1 0 newval2 1 1 1"


def test_hsetnx_target_key_missing_small_hash(r: ValkeyTestClient) -> None:
    """
    test {HSETNX target key missing - small hash} {
        r hsetnx smallhash __123123123__ foo
        r hget smallhash __123123123__
    } {foo}
    """
    r.run("hsetnx", "smallhash", "__123123123__", "foo")
    assert r.run("hget", "smallhash", "__123123123__") == "foo"


def test_hsetnx_target_key_exists_small_hash(r: ValkeyTestClient) -> None:
    """
    test {HSETNX target key exists - small hash} {
        r hsetnx smallhash __123123123__ bar
        set result [r hget smallhash __123123123__]
        r hdel smallhash __123123123__
        set _ $result
    } {foo}
    """
    r.run("hsetnx", "smallhash", "__123123123__", "bar")
    result = r.run("hget", "smallhash", "__123123123__")
    r.run("hdel", "smallhash", "__123123123__")
    assert result == "foo"


def test_hsetnx_target_key_missing_big_hash(r: ValkeyTestClient) -> None:
    """
    test {HSETNX target key missing - big hash} {
        r hsetnx bighash __123123123__ foo
        r hget bighash __123123123__
    } {foo}
    """
    r.run("hsetnx", "bighash", "__123123123__", "foo")
    assert r.run("hget", "bighash", "__123123123__") == "foo"


def test_hsetnx_target_key_exists_big_hash(r: ValkeyTestClient) -> None:
    """
    test {HSETNX target key exists - big hash} {
        r hsetnx bighash __123123123__ bar
        set result [r hget bighash __123123123__]
        r hdel bighash __123123123__
        set _ $result
    } {foo}
    """
    r.run("hsetnx", "bighash", "__123123123__", "bar")
    result = r.run("hget", "bighash", "__123123123__")
    r.run("hdel", "bighash", "__123123123__")
    assert result == "foo"


def test_hset_or_hmset_wrong_number_of_args(r: ValkeyTestClient) -> None:
    """
    test {HSET/HMSET wrong number of args} {
        assert_error {*wrong number of arguments for 'hset' command} {r hset smallhash key1 val1 key2}
        assert_error {*wrong number of arguments for 'hmset' command} {r hmset smallhash key1 val1 key2}
    }
    """
    with pytest.raises(Exception, match=".*wrong\\ number\\ of\\ arguments\\ for\\ 'hset'\\ command"):
        r.run("hset", "smallhash", "key1", "val1", "key2")
    with pytest.raises(Exception, match=".*wrong\\ number\\ of\\ arguments\\ for\\ 'hmset'\\ command"):
        r.run("hmset", "smallhash", "key1", "val1", "key2")


def test_hmset_small_hash(r: ValkeyTestClient) -> None:
    """
    test {HMSET - small hash} {
        set args {}
        foreach {k v} [array get smallhash] {
            set newval [randstring 0 8 alpha]
            set smallhash($k) $newval
            lappend args $k $newval
        }
        r hmset smallhash {*}$args
    } {OK}
    """
    args = []
    foreach(
        "k v",
        array("get", "smallhash"),
        "            set newval [randstring 0 8 alpha]\n            set smallhash($k) $newval\n            lappend args $k $newval\n        ",
    )
    assert r.run("hmset", "smallhash", "*", args) == "OK"


def test_hmset_big_hash(r: ValkeyTestClient) -> None:
    """
    test {HMSET - big hash} {
        set args {}
        foreach {k v} [array get bighash] {
            set newval [randstring 0 8 alpha]
            set bighash($k) $newval
            lappend args $k $newval
        }
        r hmset bighash {*}$args
    } {OK}
    """
    args = []
    foreach(
        "k v",
        array("get", "bighash"),
        "            set newval [randstring 0 8 alpha]\n            set bighash($k) $newval\n            lappend args $k $newval\n        ",
    )
    assert r.run("hmset", "bighash", "*", args) == "OK"


def test_hmget_against_non_existing_key_and_fields(r: ValkeyTestClient) -> None:
    """
    test {HMGET against non existing key and fields} {
        set rv {}
        lappend rv [r hmget doesntexist __123123123__ __456456456__]
        lappend rv [r hmget smallhash __123123123__ __456456456__]
        lappend rv [r hmget bighash __123123123__ __456456456__]
        set _ $rv
    } {{{} {}} {{} {}} {{} {}}}
    """
    rv = []
    rv.append(r.run("hmget", "doesntexist", "__123123123__", "__456456456__"))
    rv.append(r.run("hmget", "smallhash", "__123123123__", "__456456456__"))
    rv.append(r.run("hmget", "bighash", "__123123123__", "__456456456__"))
    assert rv == "{{} {}} {{} {}} {{} {}}"


def test_hash_commands_against_wrong_type(r: ValkeyTestClient) -> None:
    """
    test {Hash commands against wrong type} {
        r set wrongtype somevalue
        assert_error "WRONGTYPE Operation against a key*" {r hmget wrongtype field1 field2}
        assert_error "WRONGTYPE Operation against a key*" {r hrandfield wrongtype}
        assert_error "WRONGTYPE Operation against a key*" {r hget wrongtype field1}
        assert_error "WRONGTYPE Operation against a key*" {r hgetall wrongtype}
        assert_error "WRONGTYPE Operation against a key*" {r hdel wrongtype field1}
        assert_error "WRONGTYPE Operation against a key*" {r hincrby wrongtype field1 2}
        assert_error "WRONGTYPE Operation against a key*" {r hincrbyfloat wrongtype field1 2.5}
        assert_error "WRONGTYPE Operation against a key*" {r hstrlen wrongtype field1}
        assert_error "WRONGTYPE Operation against a key*" {r hvals wrongtype}
        assert_error "WRONGTYPE Operation against a key*" {r hkeys wrongtype}
        assert_error "WRONGTYPE Operation against a key*" {r hexists wrongtype field1}
        assert_error "WRONGTYPE Operation against a key*" {r hset wrongtype field1 val1}
        assert_error "WRONGTYPE Operation against a key*" {r hmset wrongtype field1 val1 field2 val2}
        assert_error "WRONGTYPE Operation against a key*" {r hsetnx wrongtype field1 val1}
        assert_error "WRONGTYPE Operation against a key*" {r hlen wrongtype}
        assert_error "WRONGTYPE Operation against a key*" {r hscan wrongtype 0}
    }
    """
    r.run("set", "wrongtype", "somevalue")
    with pytest.raises(Exception, match="WRONGTYPE\\ Operation\\ against\\ a\\ key.*"):
        r.run("hmget", "wrongtype", "field1", "field2")
    with pytest.raises(Exception, match="WRONGTYPE\\ Operation\\ against\\ a\\ key.*"):
        r.run("hrandfield", "wrongtype")
    with pytest.raises(Exception, match="WRONGTYPE\\ Operation\\ against\\ a\\ key.*"):
        r.run("hget", "wrongtype", "field1")
    with pytest.raises(Exception, match="WRONGTYPE\\ Operation\\ against\\ a\\ key.*"):
        r.run("hgetall", "wrongtype")
    with pytest.raises(Exception, match="WRONGTYPE\\ Operation\\ against\\ a\\ key.*"):
        r.run("hdel", "wrongtype", "field1")
    with pytest.raises(Exception, match="WRONGTYPE\\ Operation\\ against\\ a\\ key.*"):
        r.run("hincrby", "wrongtype", "field1", 2)
    with pytest.raises(Exception, match="WRONGTYPE\\ Operation\\ against\\ a\\ key.*"):
        r.run("hincrbyfloat", "wrongtype", "field1", 2.5)
    with pytest.raises(Exception, match="WRONGTYPE\\ Operation\\ against\\ a\\ key.*"):
        r.run("hstrlen", "wrongtype", "field1")
    with pytest.raises(Exception, match="WRONGTYPE\\ Operation\\ against\\ a\\ key.*"):
        r.run("hvals", "wrongtype")
    with pytest.raises(Exception, match="WRONGTYPE\\ Operation\\ against\\ a\\ key.*"):
        r.run("hkeys", "wrongtype")
    with pytest.raises(Exception, match="WRONGTYPE\\ Operation\\ against\\ a\\ key.*"):
        r.run("hexists", "wrongtype", "field1")
    with pytest.raises(Exception, match="WRONGTYPE\\ Operation\\ against\\ a\\ key.*"):
        r.run("hset", "wrongtype", "field1", "val1")
    with pytest.raises(Exception, match="WRONGTYPE\\ Operation\\ against\\ a\\ key.*"):
        r.run("hmset", "wrongtype", "field1", "val1", "field2", "val2")
    with pytest.raises(Exception, match="WRONGTYPE\\ Operation\\ against\\ a\\ key.*"):
        r.run("hsetnx", "wrongtype", "field1", "val1")
    with pytest.raises(Exception, match="WRONGTYPE\\ Operation\\ against\\ a\\ key.*"):
        r.run("hlen", "wrongtype")
    with pytest.raises(Exception, match="WRONGTYPE\\ Operation\\ against\\ a\\ key.*"):
        r.run("hscan", "wrongtype", 0)


def test_hmget_small_hash(r: ValkeyTestClient) -> None:
    """
    test {HMGET - small hash} {
        set keys {}
        set vals {}
        foreach {k v} [array get smallhash] {
            lappend keys $k
            lappend vals $v
        }
        set err {}
        set result [r hmget smallhash {*}$keys]
        if {$vals ne $result} {
            set err "$vals != $result"
            break
        }
        set _ $err
    } {}
    """
    keys = []
    vals = []
    foreach("k v", array("get", "smallhash"), "            lappend keys $k\n            lappend vals $v\n        ")
    err = ""
    result = r.run("hmget", "smallhash", "*", keys)
    if_("$vals ne $result", '            set err "$vals != $result"\n            break\n        ')
    _ = err


def test_hmget_big_hash(r: ValkeyTestClient) -> None:
    """
    test {HMGET - big hash} {
        set keys {}
        set vals {}
        foreach {k v} [array get bighash] {
            lappend keys $k
            lappend vals $v
        }
        set err {}
        set result [r hmget bighash {*}$keys]
        if {$vals ne $result} {
            set err "$vals != $result"
            break
        }
        set _ $err
    } {}
    """
    keys = []
    vals = []
    foreach("k v", array("get", "bighash"), "            lappend keys $k\n            lappend vals $v\n        ")
    err = ""
    result = r.run("hmget", "bighash", "*", keys)
    if_("$vals ne $result", '            set err "$vals != $result"\n            break\n        ')
    _ = err


def test_hkeys_small_hash(r: ValkeyTestClient) -> None:
    """
    test {HKEYS - small hash} {
        lsort [r hkeys smallhash]
    } lsort [array names smallhash *]
    """
    lsort(r.run("hkeys", "smallhash"))


def test_hkeys_big_hash(r: ValkeyTestClient) -> None:
    """
    test {HKEYS - big hash} {
        lsort [r hkeys bighash]
    } lsort [array names bighash *]
    """
    lsort(r.run("hkeys", "bighash"))


def test_hvals_small_hash(r: ValkeyTestClient) -> None:
    """
    test {HVALS - small hash} {
        set vals {}
        foreach {k v} [array get smallhash] {
            lappend vals $v
        }
        set _ [lsort $vals]
    } lsort [r hvals smallhash]
    """
    vals = []
    foreach("k v", array("get", "smallhash"), "            lappend vals $v\n        ")
    _ = sorted(vals)


def test_hvals_big_hash(r: ValkeyTestClient) -> None:
    """
    test {HVALS - big hash} {
        set vals {}
        foreach {k v} [array get bighash] {
            lappend vals $v
        }
        set _ [lsort $vals]
    } lsort [r hvals bighash]
    """
    vals = []
    foreach("k v", array("get", "bighash"), "            lappend vals $v\n        ")
    _ = sorted(vals)


def test_hgetall_small_hash(r: ValkeyTestClient) -> None:
    """
    test {HGETALL - small hash} {
        lsort [r hgetall smallhash]
    } lsort [array get smallhash]
    """
    lsort(r.run("hgetall", "smallhash"))


def test_hgetall_big_hash(r: ValkeyTestClient) -> None:
    """
    test {HGETALL - big hash} {
        lsort [r hgetall bighash]
    } lsort [array get bighash]
    """
    lsort(r.run("hgetall", "bighash"))


def test_hgetall_against_non_existing_key(r: ValkeyTestClient) -> None:
    """
    test {HGETALL against non-existing key} {
        r del htest
        r hgetall htest
    } {}
    """
    r.run("del", "htest")
    r.run("hgetall", "htest")


def test_hgetdel_single_field(r: ValkeyTestClient) -> None:
    """
    test {HGETDEL - single field} {
        r del myhash
        r hset myhash field1 value1
        set rv {}
        lappend rv [r hgetdel myhash FIELDS 1 field1]
        lappend rv [r hexists myhash field1]
        lappend rv [r exists myhash]
        set _ $rv
    } {value1 0 0}
    """
    r.run("del", "myhash")
    r.run("hset", "myhash", "field1", "value1")
    rv = []
    rv.append(r.run("hgetdel", "myhash", "FIELDS", 1, "field1"))
    rv.append(r.run("hexists", "myhash", "field1"))
    rv.append(r.run("exists", "myhash"))
    assert rv == "value1 0 0"


def test_hgetdel_multiple_fields(r: ValkeyTestClient) -> None:
    """
    test {HGETDEL - multiple fields} {
        r del myhash
        r hmset myhash field1 value1 field2 value2 field3 value3
        set rv {}
        lappend rv [r hgetdel myhash FIELDS 2 field1 field3]
        lappend rv [r hexists myhash field1]
        lappend rv [r hexists myhash field2]
        lappend rv [r hexists myhash field3]
        lappend rv [r hget myhash field2]
        set _ $rv
    } {{value1 value3} 0 1 0 value2}
    """
    r.run("del", "myhash")
    r.run("hmset", "myhash", "field1", "value1", "field2", "value2", "field3", "value3")
    rv = []
    rv.append(r.run("hgetdel", "myhash", "FIELDS", 2, "field1", "field3"))
    rv.append(r.run("hexists", "myhash", "field1"))
    rv.append(r.run("hexists", "myhash", "field2"))
    rv.append(r.run("hexists", "myhash", "field3"))
    rv.append(r.run("hget", "myhash", "field2"))
    assert rv == "{value1 value3} 0 1 0 value2"


def test_hgetdel_non_existing_field(r: ValkeyTestClient) -> None:
    """
    test {HGETDEL - non-existing field} {
        r del myhash
        r hset myhash field1 value1
        set rv {}
        lappend rv [r hgetdel myhash FIELDS 1 nonexisting]
        lappend rv [r hexists myhash field1]
        set _ $rv
    } {{{}} 1}
    """
    r.run("del", "myhash")
    r.run("hset", "myhash", "field1", "value1")
    rv = []
    rv.append(r.run("hgetdel", "myhash", "FIELDS", 1, "nonexisting"))
    rv.append(r.run("hexists", "myhash", "field1"))
    assert rv == "{{}} 1"


def test_hgetdel_non_existing_key_and_hash_after_the_key_is_deleted(r: ValkeyTestClient) -> None:
    """
    test {HGETDEL - non-existing key and hash after the key is deleted } {
        r del myhash
        r hset myhash field1 value1
        assert_equal {value1 {}} [r hgetdel myhash FIELDS 2 field1 field2]
    }
    """
    r.run("del", "myhash")
    r.run("hset", "myhash", "field1", "value1")
    assert "value1 {}" == r.run("hgetdel", "myhash", "FIELDS", 2, "field1", "field2")


def test_hgetdel_non_existing_key(r: ValkeyTestClient) -> None:
    """
    test {HGETDEL - non-existing key} {
        r del myhash
        assert_equal {{}} [r hgetdel myhash FIELDS 1 field1]
    }
    """
    r.run("del", "myhash")
    assert "{}" == r.run("hgetdel", "myhash", "FIELDS", 1, "field1")


def test_hgetdel_mix_of_existing_and_non_existing_fields(r: ValkeyTestClient) -> None:
    """
    test {HGETDEL - mix of existing and non-existing fields} {
        r del myhash
        r hmset myhash a 1 b 2 c 3
        set rv {}
        lappend rv [r hgetdel myhash FIELDS 3 a nonexist b]
        lappend rv [r hexists myhash a]
        lappend rv [r hexists myhash b]
        lappend rv [r hexists myhash c]
        set _ $rv
    } {{1 {} 2} 0 0 1}
    """
    r.run("del", "myhash")
    r.run("hmset", "myhash", "a", 1, "b", 2, "c", 3)
    rv = []
    rv.append(r.run("hgetdel", "myhash", "FIELDS", 3, "a", "nonexist", "b"))
    rv.append(r.run("hexists", "myhash", "a"))
    rv.append(r.run("hexists", "myhash", "b"))
    rv.append(r.run("hexists", "myhash", "c"))
    assert rv == "{1 {} 2} 0 0 1"


def test_hgetdel_hash_becomes_empty_after_deletion(r: ValkeyTestClient) -> None:
    """
    test {HGETDEL - hash becomes empty after deletion} {
        r del myhash
        r hmset myhash a 1 b 2
        set rv {}
        lappend rv [r hgetdel myhash FIELDS 2 a b]
        lappend rv [r exists myhash]
        set _ $rv
    } {{1 2} 0}
    """
    r.run("del", "myhash")
    r.run("hmset", "myhash", "a", 1, "b", 2)
    rv = []
    rv.append(r.run("hgetdel", "myhash", "FIELDS", 2, "a", "b"))
    rv.append(r.run("exists", "myhash"))
    assert rv == "{1 2} 0"


def test_hgetdel_wrong_type(r: ValkeyTestClient) -> None:
    """
    test {HGETDEL - wrong type} {
        r del wrongtype
        r set wrongtype somevalue
        assert_error "*WRONGTYPE*" {r hgetdel wrongtype FIELDS 1 field1}
    }
    """
    r.run("del", "wrongtype")
    r.run("set", "wrongtype", "somevalue")
    with pytest.raises(Exception, match=".*WRONGTYPE.*"):
        r.run("hgetdel", "wrongtype", "FIELDS", 1, "field1")


def test_hgetdel_wrong_number_of_arguments(r: ValkeyTestClient) -> None:
    """
    test {HGETDEL - wrong number of arguments} {
        assert_error "*wrong number of arguments*" {r hgetdel myhash}
    }
    """
    with pytest.raises(Exception, match=".*wrong\\ number\\ of\\ arguments.*"):
        r.run("hgetdel", "myhash")


def test_hgetdel_check_for_syntax_and_type_errors(r: ValkeyTestClient) -> None:
    """
    test {HGETDEL - check for syntax and type errors} {
        assert_error "*value is not an integer or out of range" {r hgetdel myhash a b c}
        assert_error "*value is not an integer or out of range" {r hgetdel myhash FIELDS a b c}
        assert_error "*numfields should be greater than 0 and match the provided number of fields" {r hgetdel myhash FIELDS 2 a b c}
        assert_error "*numfields should be greater than 0 and match the provided number of fields" {r hgetdel myhash FIELDS 4 a b c}
    }
    """
    with pytest.raises(Exception, match=".*value\\ is\\ not\\ an\\ integer\\ or\\ out\\ of\\ range"):
        r.run("hgetdel", "myhash", "a", "b", "c")
    with pytest.raises(Exception, match=".*value\\ is\\ not\\ an\\ integer\\ or\\ out\\ of\\ range"):
        r.run("hgetdel", "myhash", "FIELDS", "a", "b", "c")
    with pytest.raises(
        Exception,
        match=".*numfields\\ should\\ be\\ greater\\ than\\ 0\\ and\\ match\\ the\\ provided\\ number\\ of\\ fields",
    ):
        r.run("hgetdel", "myhash", "FIELDS", 2, "a", "b", "c")
    with pytest.raises(
        Exception,
        match=".*numfields\\ should\\ be\\ greater\\ than\\ 0\\ and\\ match\\ the\\ provided\\ number\\ of\\ fields",
    ):
        r.run("hgetdel", "myhash", "FIELDS", 4, "a", "b", "c")


def test_hdel_and_return_value(r: ValkeyTestClient) -> None:
    """
    test {HDEL and return value} {
        set rv {}
        lappend rv [r hdel smallhash nokey]
        lappend rv [r hdel bighash nokey]
        set k [lindex [array names smallhash *] 0]
        lappend rv [r hdel smallhash $k]
        lappend rv [r hdel smallhash $k]
        lappend rv [r hget smallhash $k]
        unset smallhash($k)
        set k [lindex [array names bighash *] 0]
        lappend rv [r hdel bighash $k]
        lappend rv [r hdel bighash $k]
        lappend rv [r hget bighash $k]
        unset bighash($k)
        set _ $rv
    } {0 0 1 0 {} 1 0 {}}
    """
    rv = []
    rv.append(r.run("hdel", "smallhash", "nokey"))
    rv.append(r.run("hdel", "bighash", "nokey"))
    k = array("names", "smallhash", "*")[0]
    rv.append(r.run("hdel", "smallhash", k))
    rv.append(r.run("hdel", "smallhash", k))
    rv.append(r.run("hget", "smallhash", k))
    unset("smallhash($k)")
    k = array("names", "bighash", "*")[0]
    rv.append(r.run("hdel", "bighash", k))
    rv.append(r.run("hdel", "bighash", k))
    rv.append(r.run("hget", "bighash", k))
    unset("bighash($k)")
    assert rv == "0 0 1 0 {} 1 0 {}"


def test_hdel_more_than_a_single_value(r: ValkeyTestClient) -> None:
    """
    test {HDEL - more than a single value} {
        set rv {}
        r del myhash
        r hmset myhash a 1 b 2 c 3
        assert_equal 0 [r hdel myhash x y]
        assert_equal 2 [r hdel myhash a c f]
        r hgetall myhash
    } {b 2}
    """
    rv = ""
    r.run("del", "myhash")
    r.run("hmset", "myhash", "a", 1, "b", 2, "c", 3)
    assert 0 == r.run("hdel", "myhash", "x", "y")
    assert 2 == r.run("hdel", "myhash", "a", "c", "f")
    assert r.run("hgetall", "myhash") == "b 2"


def test_hdel_hash_becomes_empty_before_deleting_all_specified_fields(r: ValkeyTestClient) -> None:
    """
    test {HDEL - hash becomes empty before deleting all specified fields} {
        r del myhash
        r hmset myhash a 1 b 2 c 3
        assert_equal 3 [r hdel myhash a b c d e]
        assert_equal 0 [r exists myhash]
    }
    """
    r.run("del", "myhash")
    r.run("hmset", "myhash", "a", 1, "b", 2, "c", 3)
    assert 3 == r.run("hdel", "myhash", "a", "b", "c", "d", "e")
    assert 0 == r.run("exists", "myhash")


def test_hexists(r: ValkeyTestClient) -> None:
    """
    test {HEXISTS} {
        set rv {}
        set k [lindex [array names smallhash *] 0]
        lappend rv [r hexists smallhash $k]
        lappend rv [r hexists smallhash nokey]
        set k [lindex [array names bighash *] 0]
        lappend rv [r hexists bighash $k]
        lappend rv [r hexists bighash nokey]
    } {1 0 1 0}
    """
    rv = []
    k = array("names", "smallhash", "*")[0]
    rv.append(r.run("hexists", "smallhash", k))
    rv.append(r.run("hexists", "smallhash", "nokey"))
    k = array("names", "bighash", "*")[0]
    rv.append(r.run("hexists", "bighash", k))
    rv.append(r.run("hexists", "bighash", "nokey"))


def test_is_a_ziplist_encoded_hash_promoted_on_big_payload(r: ValkeyTestClient) -> None:
    """
    test {Is a ziplist encoded Hash promoted on big payload?} {
        r config set hash-max-listpack-value 64
        r hset smallhash foo [string repeat a 1024]
        r debug object smallhash
    } {*hashtable*} {needs:debug}
    """
    r.run("config", "set", "hash-max-listpack-value", 64)
    r.run("hset", "smallhash", "foo", string("repeat", "a", 1024))
    assert fnmatch(str(r.run("debug", "object", "smallhash")), "*hashtable*")


def test_hincrby_against_non_existing_database_key(r: ValkeyTestClient) -> None:
    """
    test {HINCRBY against non existing database key} {
        r del htest
        list [r hincrby htest foo 2]
    } {2}
    """
    r.run("del", "htest")
    assert [r.run("hincrby", "htest", "foo", 2)] == "2"


def test_hincrby_hincrbyfloat_against_non_integer_increment_value(r: ValkeyTestClient) -> None:
    """
    test {HINCRBY HINCRBYFLOAT against non-integer increment value} {
        r del incrhash
        r hset incrhash field 5
        assert_error "*value is not an integer*" {r hincrby incrhash field v}
        assert_error "*value is not a*" {r hincrbyfloat incrhash field v}
    }
    """
    r.run("del", "incrhash")
    r.run("hset", "incrhash", "field", 5)
    with pytest.raises(Exception, match=".*value\\ is\\ not\\ an\\ integer.*"):
        r.run("hincrby", "incrhash", "field", "v")
    with pytest.raises(Exception, match=".*value\\ is\\ not\\ a.*"):
        r.run("hincrbyfloat", "incrhash", "field", "v")


def test_hincrby_against_non_existing_hash_key(r: ValkeyTestClient) -> None:
    """
    test {HINCRBY against non existing hash key} {
        set rv {}
        r hdel smallhash tmp
        r hdel bighash tmp
        lappend rv [r hincrby smallhash tmp 2]
        lappend rv [r hget smallhash tmp]
        lappend rv [r hincrby bighash tmp 2]
        lappend rv [r hget bighash tmp]
    } {2 2 2 2}
    """
    rv = []
    r.run("hdel", "smallhash", "tmp")
    r.run("hdel", "bighash", "tmp")
    rv.append(r.run("hincrby", "smallhash", "tmp", 2))
    rv.append(r.run("hget", "smallhash", "tmp"))
    rv.append(r.run("hincrby", "bighash", "tmp", 2))
    rv.append(r.run("hget", "bighash", "tmp"))


def test_hincrby_against_hash_key_created_by_hincrby_itself(r: ValkeyTestClient) -> None:
    """
    test {HINCRBY against hash key created by hincrby itself} {
        set rv {}
        lappend rv [r hincrby smallhash tmp 3]
        lappend rv [r hget smallhash tmp]
        lappend rv [r hincrby bighash tmp 3]
        lappend rv [r hget bighash tmp]
    } {5 5 5 5}
    """
    rv = []
    rv.append(r.run("hincrby", "smallhash", "tmp", 3))
    rv.append(r.run("hget", "smallhash", "tmp"))
    rv.append(r.run("hincrby", "bighash", "tmp", 3))
    rv.append(r.run("hget", "bighash", "tmp"))


def test_hincrby_against_hash_key_originally_set_with_hset(r: ValkeyTestClient) -> None:
    """
    test {HINCRBY against hash key originally set with HSET} {
        r hset smallhash tmp 100
        r hset bighash tmp 100
        list [r hincrby smallhash tmp 2] [r hincrby bighash tmp 2]
    } {102 102}
    """
    r.run("hset", "smallhash", "tmp", 100)
    r.run("hset", "bighash", "tmp", 100)
    assert [r.run("hincrby", "smallhash", "tmp", 2), r.run("hincrby", "bighash", "tmp", 2)] == "102 102"


def test_hincrby_over_32bit_value(r: ValkeyTestClient) -> None:
    """
    test {HINCRBY over 32bit value} {
        r hset smallhash tmp 17179869184
        r hset bighash tmp 17179869184
        list [r hincrby smallhash tmp 1] [r hincrby bighash tmp 1]
    } {17179869185 17179869185}
    """
    r.run("hset", "smallhash", "tmp", 17179869184)
    r.run("hset", "bighash", "tmp", 17179869184)
    assert [r.run("hincrby", "smallhash", "tmp", 1), r.run("hincrby", "bighash", "tmp", 1)] == "17179869185 17179869185"


def test_hincrby_over_32bit_value_with_over_32bit_increment(r: ValkeyTestClient) -> None:
    """
    test {HINCRBY over 32bit value with over 32bit increment} {
        r hset smallhash tmp 17179869184
        r hset bighash tmp 17179869184
        list [r hincrby smallhash tmp 17179869184] [r hincrby bighash tmp 17179869184]
    } {34359738368 34359738368}
    """
    r.run("hset", "smallhash", "tmp", 17179869184)
    r.run("hset", "bighash", "tmp", 17179869184)
    assert [
        r.run("hincrby", "smallhash", "tmp", 17179869184),
        r.run("hincrby", "bighash", "tmp", 17179869184),
    ] == "34359738368 34359738368"


def test_hincrby_fails_against_hash_value_with_spaces_left(r: ValkeyTestClient) -> None:
    """
    test {HINCRBY fails against hash value with spaces (left)} {
        r hset smallhash str " 11"
        r hset bighash str " 11"
        catch {r hincrby smallhash str 1} smallerr
        catch {r hincrby bighash str 1} bigerr
        set rv {}
        lappend rv [string match "ERR *not an integer*" $smallerr]
        lappend rv [string match "ERR *not an integer*" $bigerr]
    } {1 1}
    """
    r.run("hset", "smallhash", "str", " 11")
    r.run("hset", "bighash", "str", " 11")
    try:
        smallerr = r.run("hincrby", "smallhash", "str", 1)
    except Exception as _catch_err:
        smallerr = str(_catch_err)
    try:
        bigerr = r.run("hincrby", "bighash", "str", 1)
    except Exception as _catch_err:
        bigerr = str(_catch_err)
    rv = []
    rv.append(string("match", "ERR *not an integer*", smallerr))
    rv.append(string("match", "ERR *not an integer*", bigerr))


def test_hincrby_fails_against_hash_value_with_spaces_right(r: ValkeyTestClient) -> None:
    """
    test {HINCRBY fails against hash value with spaces (right)} {
        r hset smallhash str "11 "
        r hset bighash str "11 "
        catch {r hincrby smallhash str 1} smallerr
        catch {r hincrby bighash str 1} bigerr
        set rv {}
        lappend rv [string match "ERR *not an integer*" $smallerr]
        lappend rv [string match "ERR *not an integer*" $bigerr]
    } {1 1}
    """
    r.run("hset", "smallhash", "str", "11 ")
    r.run("hset", "bighash", "str", "11 ")
    try:
        smallerr = r.run("hincrby", "smallhash", "str", 1)
    except Exception as _catch_err:
        smallerr = str(_catch_err)
    try:
        bigerr = r.run("hincrby", "bighash", "str", 1)
    except Exception as _catch_err:
        bigerr = str(_catch_err)
    rv = []
    rv.append(string("match", "ERR *not an integer*", smallerr))
    rv.append(string("match", "ERR *not an integer*", bigerr))


def test_hincrby_can_detect_overflows(r: ValkeyTestClient) -> None:
    """
    test {HINCRBY can detect overflows} {
        set e {}
        r hset hash n -9223372036854775484
        assert {[r hincrby hash n -1] == -9223372036854775485}
        catch {r hincrby hash n -10000} e
        set e
    } {*overflow*}
    """
    e = ""
    r.run("hset", "hash", "n", -9223372036854775484)
    assert r.run("hincrby", "hash", "n", -1) == -9223372036854775485
    try:
        e = r.run("hincrby", "hash", "n", -10000)
    except Exception as _catch_err:
        e = str(_catch_err)
    assert fnmatch(str(e), "*overflow*")


def test_hincrbyfloat_against_non_existing_database_key(r: ValkeyTestClient) -> None:
    """
    test {HINCRBYFLOAT against non existing database key} {
        r del htest
        list [r hincrbyfloat htest foo 2.5]
    } {2.5}
    """
    r.run("del", "htest")
    assert [r.run("hincrbyfloat", "htest", "foo", 2.5)] == "2.5"


def test_hincrbyfloat_against_non_existing_hash_key(r: ValkeyTestClient) -> None:
    """
    test {HINCRBYFLOAT against non existing hash key} {
        set rv {}
        r hdel smallhash tmp
        r hdel bighash tmp
        lappend rv [roundFloat [r hincrbyfloat smallhash tmp 2.5]]
        lappend rv [roundFloat [r hget smallhash tmp]]
        lappend rv [roundFloat [r hincrbyfloat bighash tmp 2.5]]
        lappend rv [roundFloat [r hget bighash tmp]]
    } {2.5 2.5 2.5 2.5}
    """
    rv = []
    r.run("hdel", "smallhash", "tmp")
    r.run("hdel", "bighash", "tmp")
    rv.append(round_float(r.run("hincrbyfloat", "smallhash", "tmp", 2.5)))
    rv.append(round_float(r.run("hget", "smallhash", "tmp")))
    rv.append(round_float(r.run("hincrbyfloat", "bighash", "tmp", 2.5)))
    rv.append(round_float(r.run("hget", "bighash", "tmp")))


def test_hincrbyfloat_against_hash_key_created_by_hincrby_itself(r: ValkeyTestClient) -> None:
    """
    test {HINCRBYFLOAT against hash key created by hincrby itself} {
        set rv {}
        lappend rv [roundFloat [r hincrbyfloat smallhash tmp 3.5]]
        lappend rv [roundFloat [r hget smallhash tmp]]
        lappend rv [roundFloat [r hincrbyfloat bighash tmp 3.5]]
        lappend rv [roundFloat [r hget bighash tmp]]
    } {6 6 6 6}
    """
    rv = []
    rv.append(round_float(r.run("hincrbyfloat", "smallhash", "tmp", 3.5)))
    rv.append(round_float(r.run("hget", "smallhash", "tmp")))
    rv.append(round_float(r.run("hincrbyfloat", "bighash", "tmp", 3.5)))
    rv.append(round_float(r.run("hget", "bighash", "tmp")))


def test_hincrbyfloat_against_hash_key_originally_set_with_hset(r: ValkeyTestClient) -> None:
    """
    test {HINCRBYFLOAT against hash key originally set with HSET} {
        r hset smallhash tmp 100
        r hset bighash tmp 100
        list [roundFloat [r hincrbyfloat smallhash tmp 2.5]] \
             [roundFloat [r hincrbyfloat bighash tmp 2.5]]
    } {102.5 102.5}
    """
    r.run("hset", "smallhash", "tmp", 100)
    r.run("hset", "bighash", "tmp", 100)
    assert [
        round_float(r.run("hincrbyfloat", "smallhash", "tmp", 2.5)),
        round_float(r.run("hincrbyfloat", "bighash", "tmp", 2.5)),
    ] == "102.5 102.5"


def test_hincrbyfloat_over_32bit_value(r: ValkeyTestClient) -> None:
    """
    test {HINCRBYFLOAT over 32bit value} {
        r hset smallhash tmp 17179869184
        r hset bighash tmp 17179869184
        list [r hincrbyfloat smallhash tmp 1] \
             [r hincrbyfloat bighash tmp 1]
    } {17179869185 17179869185}
    """
    r.run("hset", "smallhash", "tmp", 17179869184)
    r.run("hset", "bighash", "tmp", 17179869184)
    assert [
        r.run("hincrbyfloat", "smallhash", "tmp", 1),
        r.run("hincrbyfloat", "bighash", "tmp", 1),
    ] == "17179869185 17179869185"


def test_hincrbyfloat_over_32bit_value_with_over_32bit_increment(r: ValkeyTestClient) -> None:
    """
    test {HINCRBYFLOAT over 32bit value with over 32bit increment} {
        r hset smallhash tmp 17179869184
        r hset bighash tmp 17179869184
        list [r hincrbyfloat smallhash tmp 17179869184] \
             [r hincrbyfloat bighash tmp 17179869184]
    } {34359738368 34359738368}
    """
    r.run("hset", "smallhash", "tmp", 17179869184)
    r.run("hset", "bighash", "tmp", 17179869184)
    assert [
        r.run("hincrbyfloat", "smallhash", "tmp", 17179869184),
        r.run("hincrbyfloat", "bighash", "tmp", 17179869184),
    ] == "34359738368 34359738368"


def test_hincrbyfloat_fails_against_hash_value_with_spaces_left(r: ValkeyTestClient) -> None:
    """
    test {HINCRBYFLOAT fails against hash value with spaces (left)} {
        r hset smallhash str " 11"
        r hset bighash str " 11"
        catch {r hincrbyfloat smallhash str 1} smallerr
        catch {r hincrbyfloat bighash str 1} bigerr
        set rv {}
        lappend rv [string match "ERR *not*float*" $smallerr]
        lappend rv [string match "ERR *not*float*" $bigerr]
    } {1 1}
    """
    r.run("hset", "smallhash", "str", " 11")
    r.run("hset", "bighash", "str", " 11")
    try:
        smallerr = r.run("hincrbyfloat", "smallhash", "str", 1)
    except Exception as _catch_err:
        smallerr = str(_catch_err)
    try:
        bigerr = r.run("hincrbyfloat", "bighash", "str", 1)
    except Exception as _catch_err:
        bigerr = str(_catch_err)
    rv = []
    rv.append(string("match", "ERR *not*float*", smallerr))
    rv.append(string("match", "ERR *not*float*", bigerr))


def test_hincrbyfloat_fails_against_hash_value_with_spaces_right(r: ValkeyTestClient) -> None:
    """
    test {HINCRBYFLOAT fails against hash value with spaces (right)} {
        r hset smallhash str "11 "
        r hset bighash str "11 "
        catch {r hincrbyfloat smallhash str 1} smallerr
        catch {r hincrbyfloat bighash str 1} bigerr
        set rv {}
        lappend rv [string match "ERR *not*float*" $smallerr]
        lappend rv [string match "ERR *not*float*" $bigerr]
    } {1 1}
    """
    r.run("hset", "smallhash", "str", "11 ")
    r.run("hset", "bighash", "str", "11 ")
    try:
        smallerr = r.run("hincrbyfloat", "smallhash", "str", 1)
    except Exception as _catch_err:
        smallerr = str(_catch_err)
    try:
        bigerr = r.run("hincrbyfloat", "bighash", "str", 1)
    except Exception as _catch_err:
        bigerr = str(_catch_err)
    rv = []
    rv.append(string("match", "ERR *not*float*", smallerr))
    rv.append(string("match", "ERR *not*float*", bigerr))


def test_hincrbyfloat_fails_against_hash_value_that_contains_a_null_terminator_in_the_middle(
    r: ValkeyTestClient,
) -> None:
    """
    test {HINCRBYFLOAT fails against hash value that contains a null-terminator in the middle} {
        r hset h f "1\x002"
        catch {r hincrbyfloat h f 1} err
        set rv {}
        lappend rv [string match "ERR *not*float*" $err]
    } {1}
    """
    r.run("hset", "h", "f", "1\x002")
    try:
        err = r.run("hincrbyfloat", "h", "f", 1)
    except Exception as _catch_err:
        err = str(_catch_err)
    rv = []
    rv.append(string("match", "ERR *not*float*", err))


def test_hstrlen_against_the_small_hash(r: ValkeyTestClient) -> None:
    """
    test {HSTRLEN against the small hash} {
        set err {}
        foreach k [array names smallhash *] {
            if {[string length $smallhash($k)] ne [r hstrlen smallhash $k]} {
                set err "[string length $smallhash($k)] != [r hstrlen smallhash $k]"
                break
            }
        }
        set _ $err
    } {}
    """
    err = ""
    foreach(
        "k",
        array("names", "smallhash", "*"),
        '            if {[string length $smallhash($k)] ne [r hstrlen smallhash $k]} {\n                set err "[string length $smallhash($k)] != [r hstrlen smallhash $k]"\n                break\n            }\n        ',
    )
    _ = err


def test_hstrlen_against_the_big_hash(r: ValkeyTestClient) -> None:
    """
    test {HSTRLEN against the big hash} {
        set err {}
        foreach k [array names bighash *] {
            if {[string length $bighash($k)] ne [r hstrlen bighash $k]} {
                set err "[string length $bighash($k)] != [r hstrlen bighash $k]"
                puts "HSTRLEN and logical length mismatch:"
                puts "key: $k"
                puts "Logical content: $bighash($k)"
                puts "Server  content: [r hget bighash $k]"
            }
        }
        set _ $err
    } {}
    """
    err = ""
    foreach(
        "k",
        array("names", "bighash", "*"),
        '            if {[string length $bighash($k)] ne [r hstrlen bighash $k]} {\n                set err "[string length $bighash($k)] != [r hstrlen bighash $k]"\n                puts "HSTRLEN and logical length mismatch:"\n                puts "key: $k"\n                puts "Logical content: $bighash($k)"\n                puts "Server  content: [r hget bighash $k]"\n            }\n        ',
    )
    _ = err


def test_hstrlen_against_non_existing_field(r: ValkeyTestClient) -> None:
    """
    test {HSTRLEN against non existing field} {
        set rv {}
        lappend rv [r hstrlen smallhash __123123123__]
        lappend rv [r hstrlen bighash __123123123__]
        set _ $rv
    } {0 0}
    """
    rv = []
    rv.append(r.run("hstrlen", "smallhash", "__123123123__"))
    rv.append(r.run("hstrlen", "bighash", "__123123123__"))
    assert rv == "0 0"


def test_hstrlen_corner_cases(r: ValkeyTestClient) -> None:
    """
    test {HSTRLEN corner cases} {
        set vals {
            -9223372036854775808 9223372036854775807 9223372036854775808
            {} 0 -1 x
        }
        foreach v $vals {
            r hmset smallhash field $v
            r hmset bighash field $v
            set len1 [string length $v]
            set len2 [r hstrlen smallhash field]
            set len3 [r hstrlen bighash field]
            assert {$len1 == $len2}
            assert {$len2 == $len3}
        }
    }
    """
    vals = "            -9223372036854775808 9223372036854775807 9223372036854775808\n            {} 0 -1 x\n        "
    foreach(
        "v",
        vals,
        "            r hmset smallhash field $v\n            r hmset bighash field $v\n            set len1 [string length $v]\n            set len2 [r hstrlen smallhash field]\n            set len3 [r hstrlen bighash field]\n            assert {$len1 == $len2}\n            assert {$len2 == $len3}\n        ",
    )


def test_hincrbyfloat_over_hash_max_listpack_value_encoded_with_a_listpack(r: ValkeyTestClient) -> None:
    """
    test {HINCRBYFLOAT over hash-max-listpack-value encoded with a listpack} {
        set original_max_value [lindex [r config get hash-max-ziplist-value] 1]
        r config set hash-max-listpack-value 8

        # hash's value exceeds hash-max-listpack-value
        r del smallhash
        r del bighash
        r hset smallhash tmp 0
        r hset bighash tmp 0
        r hincrbyfloat smallhash tmp 0.000005
        r hincrbyfloat bighash tmp 0.0000005
        assert_encoding listpack smallhash
        assert_encoding hashtable bighash

        # hash's field exceeds hash-max-listpack-value
        r del smallhash
        r del bighash
        r hincrbyfloat smallhash abcdefgh 1
        r hincrbyfloat bighash abcdefghi 1
        assert_encoding listpack smallhash
        assert_encoding hashtable bighash

        r config set hash-max-listpack-value $original_max_value
    }
    """
    original_max_value = r.run("config", "get", "hash-max-ziplist-value")[1]
    r.run("config", "set", "hash-max-listpack-value", 8)
    r.run("del", "smallhash")
    r.run("del", "bighash")
    r.run("hset", "smallhash", "tmp", 0)
    r.run("hset", "bighash", "tmp", 0)
    r.run("hincrbyfloat", "smallhash", "tmp", 0.000005)
    r.run("hincrbyfloat", "bighash", "tmp", 0.0000005)
    assert_encoding("listpack", "smallhash")
    assert_encoding("hashtable", "bighash")
    r.run("del", "smallhash")
    r.run("del", "bighash")
    r.run("hincrbyfloat", "smallhash", "abcdefgh", 1)
    r.run("hincrbyfloat", "bighash", "abcdefghi", 1)
    assert_encoding("listpack", "smallhash")
    assert_encoding("hashtable", "bighash")
    r.run("config", "set", "hash-max-listpack-value", original_max_value)


def test_hash_ziplist_regression_test_for_large_keys(r: ValkeyTestClient) -> None:
    """
    test {Hash ziplist regression test for large keys} {
        r hset hash kkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkk a
        r hset hash kkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkk b
        r hget hash kkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkk
    } {b}
    """
    r.run(
        "hset",
        "hash",
        "kkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkk",
        "a",
    )
    r.run(
        "hset",
        "hash",
        "kkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkk",
        "b",
    )
    assert (
        r.run(
            "hget",
            "hash",
            "kkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkk",
        )
        == "b"
    )


@pytest.mark.parametrize(["size"], [(10), (512)])
def test_hash_fuzzing_1_size_fields(r: ValkeyTestClient, size) -> None:
    """
    test "Hash fuzzing #1 - $size fields" {
        for {set times 0} {$times < 10} {incr times} {
            catch {unset hash}
            array set hash {}
            r del hash

            # Create
            for {set j 0} {$j < $size} {incr j} {
                set field [randomValue]
                set value [randomValue]
                r hset hash $field $value
                set hash($field) $value
            }

            # Verify
            foreach {k v} [array get hash] {
                assert_equal $v [r hget hash $k]
            }
            assert_equal [array size hash] [r hlen hash]
        }
    }
    """
    times = 0
    while times < 10:
        catch("unset hash")
        array("set", "hash", "")
        r.run("del", "hash")
        j = 0
        while j < size:
            field = random_value()
            value = random_value()
            r.run("hset", "hash", field, value)
            set_("hash($field)", value)
            j += 1
        foreach("k v", array("get", "hash"), "                    assert_equal $v [r hget hash $k]\n                ")
        assert array("size", "hash") == r.run("hlen", "hash")
        times += 1


@pytest.mark.parametrize(["size"], [(10), (512)])
def test_hash_fuzzing_2_size_fields(r: ValkeyTestClient, size) -> None:
    """
    test "Hash fuzzing #2 - $size fields" {
        for {set times 0} {$times < 10} {incr times} {
            catch {unset hash}
            array set hash {}
            r del hash

            # Create
            for {set j 0} {$j < $size} {incr j} {
                randpath {
                    set field [randomValue]
                    set value [randomValue]
                    r hset hash $field $value
                    set hash($field) $value
                } {
                    set field [randomSignedInt 512]
                    set value [randomSignedInt 512]
                    r hset hash $field $value
                    set hash($field) $value
                } {
                    randpath {
                        set field [randomValue]
                    } {
                        set field [randomSignedInt 512]
                    }
                    r hdel hash $field
                    unset -nocomplain hash($field)
                }
            }

            # Verify
            foreach {k v} [array get hash] {
                assert_equal $v [r hget hash $k]
            }
            assert_equal [array size hash] [r hlen hash]
        }
    }
    """
    times = 0
    while times < 10:
        catch("unset hash")
        array("set", "hash", "")
        r.run("del", "hash")
        j = 0
        while j < size:
            randpath(
                "                        set field [randomValue]\n                        set value [randomValue]\n                        r hset hash $field $value\n                        set hash($field) $value\n                    ",
                "                        set field [randomSignedInt 512]\n                        set value [randomSignedInt 512]\n                        r hset hash $field $value\n                        set hash($field) $value\n                    ",
                "                        randpath {\n                            set field [randomValue]\n                        } {\n                            set field [randomSignedInt 512]\n                        }\n                        r hdel hash $field\n                        unset -nocomplain hash($field)\n                    ",
            )
            j += 1
        foreach("k v", array("get", "hash"), "                    assert_equal $v [r hget hash $k]\n                ")
        assert array("size", "hash") == r.run("hlen", "hash")
        times += 1


def test_stress_test_the_hash_ziplist_hashtable_encoding_conversion(r: ValkeyTestClient) -> None:
    """
    test {Stress test the hash ziplist -> hashtable encoding conversion} {
        r config set hash-max-ziplist-entries 32
        for {set j 0} {$j < 100} {incr j} {
            r del myhash
            for {set i 0} {$i < 64} {incr i} {
                r hset myhash [randomValue] [randomValue]
            }
            assert_encoding hashtable myhash
        }
    }
    """
    r.run("config", "set", "hash-max-ziplist-entries", 32)
    j = 0
    while j < 100:
        r.run("del", "myhash")
        i = 0
        while i < 64:
            r.run("hset", "myhash", random_value(), random_value())
            i += 1
        assert_encoding("hashtable", "myhash")
        j += 1


@pytest.mark.skipif("", reason="{[string match *x86_64* [exec uname -a]]}")
def test_test_hincrbyfloat_for_correct_float_representation_issue_2846(r: ValkeyTestClient) -> None:
    """
    test {Test HINCRBYFLOAT for correct float representation (issue #2846)} {
        r del myhash
        assert {[r hincrbyfloat myhash float 1.23] eq {1.23}}
        assert {[r hincrbyfloat myhash float 0.77] eq {2}}
        assert {[r hincrbyfloat myhash float -0.1] eq {1.9}}
    } {} {valgrind:skip}
    """
    r.run("del", "myhash")
    assert r.run("hincrbyfloat", "myhash", "float", 1.23) == "1.23"
    assert r.run("hincrbyfloat", "myhash", "float", 0.77) == "2"
    assert r.run("hincrbyfloat", "myhash", "float", -0.1) == "1.9"


def test_hash_ziplist_of_various_encodings(r: ValkeyTestClient) -> None:
    """
    test {Hash ziplist of various encodings} {
        r del k
        config_set hash-max-ziplist-entries 1000000000
        config_set hash-max-ziplist-value 1000000000
        r hset k ZIP_INT_8B 127
        r hset k ZIP_INT_16B 32767
        r hset k ZIP_INT_32B 2147483647
        r hset k ZIP_INT_64B 9223372036854775808
        r hset k ZIP_INT_IMM_MIN 0
        r hset k ZIP_INT_IMM_MAX 12
        r hset k ZIP_STR_06B [string repeat x 31]
        r hset k ZIP_STR_14B [string repeat x 8191]
        r hset k ZIP_STR_32B [string repeat x 65535]
        set k [r hgetall k]
        set dump [r dump k]

        # will be converted to dict at RESTORE
        config_set hash-max-ziplist-entries 2
        config_set sanitize-dump-payload no mayfail
        r restore kk 0 $dump
        set kk [r hgetall kk]

        # make sure the values are right
        assert_equal [lsort $k] [lsort $kk]
        assert_equal [dict get $k ZIP_STR_06B] [string repeat x 31]
        set k [dict remove $k ZIP_STR_06B]
        assert_equal [dict get $k ZIP_STR_14B] [string repeat x 8191]
        set k [dict remove $k ZIP_STR_14B]
        assert_equal [dict get $k ZIP_STR_32B] [string repeat x 65535]
        set k [dict remove $k ZIP_STR_32B]
        set _ $k
    } {ZIP_INT_8B 127 ZIP_INT_16B 32767 ZIP_INT_32B 2147483647 ZIP_INT_64B 9223372036854775808 ZIP_INT_IMM_MIN 0 ZIP_INT_IMM_MAX 12}
    """
    r.run("del", "k")
    config_set("hash-max-ziplist-entries", 1000000000)
    config_set("hash-max-ziplist-value", 1000000000)
    r.run("hset", "k", "ZIP_INT_8B", 127)
    r.run("hset", "k", "ZIP_INT_16B", 32767)
    r.run("hset", "k", "ZIP_INT_32B", 2147483647)
    r.run("hset", "k", "ZIP_INT_64B", 9223372036854775808)
    r.run("hset", "k", "ZIP_INT_IMM_MIN", 0)
    r.run("hset", "k", "ZIP_INT_IMM_MAX", 12)
    r.run("hset", "k", "ZIP_STR_06B", string("repeat", "x", 31))
    r.run("hset", "k", "ZIP_STR_14B", string("repeat", "x", 8191))
    r.run("hset", "k", "ZIP_STR_32B", string("repeat", "x", 65535))
    k = r.run("hgetall", "k")
    dump = r.run("dump", "k")
    config_set("hash-max-ziplist-entries", 2)
    config_set("sanitize-dump-payload", "no", "mayfail")
    r.run("restore", "kk", 0, dump)
    kk = r.run("hgetall", "kk")
    assert sorted(k) == sorted(kk)
    assert k["ZIP_STR_06B"] == string("repeat", "x", 31)
    k = dict_("remove", k, "ZIP_STR_06B")
    assert k["ZIP_STR_14B"] == string("repeat", "x", 8191)
    k = dict_("remove", k, "ZIP_STR_14B")
    assert k["ZIP_STR_32B"] == string("repeat", "x", 65535)
    k = dict_("remove", k, "ZIP_STR_32B")
    assert (
        k
        == "ZIP_INT_8B 127 ZIP_INT_16B 32767 ZIP_INT_32B 2147483647 ZIP_INT_64B 9223372036854775808 ZIP_INT_IMM_MIN 0 ZIP_INT_IMM_MAX 12"
    )


@pytest.mark.xfail(reason="not implemented")
def test_hash_ziplist_of_various_encodings_sanitize_dump(r: ValkeyTestClient) -> None:
    """
    test {Hash ziplist of various encodings - sanitize dump} {
        config_set sanitize-dump-payload yes mayfail
        r restore kk 0 $dump replace
        set k [r hgetall k]
        set kk [r hgetall kk]

        # make sure the values are right
        assert_equal [lsort $k] [lsort $kk]
        assert_equal [dict get $k ZIP_STR_06B] [string repeat x 31]
        set k [dict remove $k ZIP_STR_06B]
        assert_equal [dict get $k ZIP_STR_14B] [string repeat x 8191]
        set k [dict remove $k ZIP_STR_14B]
        assert_equal [dict get $k ZIP_STR_32B] [string repeat x 65535]
        set k [dict remove $k ZIP_STR_32B]
        set _ $k
    } {ZIP_INT_8B 127 ZIP_INT_16B 32767 ZIP_INT_32B 2147483647 ZIP_INT_64B 9223372036854775808 ZIP_INT_IMM_MIN 0 ZIP_INT_IMM_MAX 12}
    """
    config_set("sanitize-dump-payload", "yes", "mayfail")
    # TODO: r restore kk 0 dump replace
    k = r.run("hgetall", "k")
    kk = r.run("hgetall", "kk")
    assert sorted(k) == sorted(kk)
    assert k["ZIP_STR_06B"] == string("repeat", "x", 31)
    k = dict_("remove", k, "ZIP_STR_06B")
    assert k["ZIP_STR_14B"] == string("repeat", "x", 8191)
    k = dict_("remove", k, "ZIP_STR_14B")
    assert k["ZIP_STR_32B"] == string("repeat", "x", 65535)
    k = dict_("remove", k, "ZIP_STR_32B")
    assert (
        k
        == "ZIP_INT_8B 127 ZIP_INT_16B 32767 ZIP_INT_32B 2147483647 ZIP_INT_64B 9223372036854775808 ZIP_INT_IMM_MIN 0 ZIP_INT_IMM_MAX 12"
    )


def test_hincrbyfloat_does_not_allow_nan_or_infinity(r: ValkeyTestClient) -> None:
    """
    test {HINCRBYFLOAT does not allow NaN or Infinity} {
        assert_error "*value is NaN or Infinity*" {r hincrbyfloat hfoo field +inf}
        assert_equal 0 [r exists hfoo]
    } {} {valgrind:skip}
    """
    with pytest.raises(Exception, match=".*value\\ is\\ NaN\\ or\\ Infinity.*"):
        r.run("hincrbyfloat", "hfoo", "field", float("+inf"))
    assert 0 == r.run("exists", "hfoo")


# --- stubs for unimplemented TCL helpers ---


def array(*args):
    raise NotImplementedError("array")


def assert_encoding(*args):
    raise NotImplementedError("assert_encoding")


def assert_lessthan(*args):
    raise NotImplementedError("assert_lessthan")


def catch(*args):
    raise NotImplementedError("catch")


def chi_square_value(*args):
    raise NotImplementedError("chi_square_value")


def config_set(*args):
    raise NotImplementedError("config_set")


def create_hash(*args):
    raise NotImplementedError("create_hash")


def dict_(*args):
    raise NotImplementedError("dict_")


def foreach(*args):
    raise NotImplementedError("foreach")


def get_keys(*args):
    raise NotImplementedError("get_keys")


def if_(*args):
    raise NotImplementedError("if_")


def lsort(*args):
    raise NotImplementedError("lsort")


def random_value(*args):
    raise NotImplementedError("random_value")


def randpath(*args):
    raise NotImplementedError("randpath")


def round_float(*args):
    raise NotImplementedError("round_float")


def set_(*args):
    raise NotImplementedError("set_")


def string(*args):
    raise NotImplementedError("string")


def unset(*args):
    raise NotImplementedError("unset")


def while_(*args):
    raise NotImplementedError("while_")
