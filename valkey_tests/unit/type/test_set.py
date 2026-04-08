# ruff: noqa: PLR2004, F841, RUF043, ANN002, ANN201
from fnmatch import fnmatch

import pytest

from tests.valkey_test_client import ValkeyTestClient

pytestmark = [pytest.mark.set]


"""
proc create_set {key entries} {
    r del $key
    foreach entry $entries { r sadd $key $entry }
}
"""


"""
array set initelems {listpack {foo} hashtable {foo}}
"""


"""
for {set i 0} {$i < 130} {incr i} {
    lappend initelems(hashtable) [format "i%03d" $i]
}
"""


@pytest.mark.xfail(reason="not implemented")
@pytest.mark.parametrize(["type"], [("listpack"), ("hashtable")])
def test_sadd_scard_sismember_smismember_smembers_basics_type(r: ValkeyTestClient, type: str) -> None:
    """
    test "SADD, SCARD, SISMEMBER, SMISMEMBER, SMEMBERS basics - $type" {
        create_set myset $initelems($type)
        assert_encoding $type myset
        assert_equal 1 [r sadd myset bar]
        assert_equal 0 [r sadd myset bar]
        assert_equal [expr [llength $initelems($type)] + 1] [r scard myset]
        assert_equal 1 [r sismember myset foo]
        assert_equal 1 [r sismember myset bar]
        assert_equal 0 [r sismember myset bla]
        assert_equal {1} [r smismember myset foo]
        assert_equal {1 1} [r smismember myset foo bar]
        assert_equal {1 0} [r smismember myset foo bla]
        assert_equal {0 1} [r smismember myset bla foo]
        assert_equal {0} [r smismember myset bla]
        assert_equal "bar $initelems($type)" [lsort [r smembers myset]]
        r memory usage myset
    }
    """
    # TODO: create_set myset initelems ($type)
    assert_encoding(type, "myset")
    assert 1 == r.run("sadd", "myset", "bar")
    assert 0 == r.run("sadd", "myset", "bar")
    # TODO: assert_equal expr [llength $initelems($type)] + 1 r scard myset
    assert 1 == r.run("sismember", "myset", "foo")
    assert 1 == r.run("sismember", "myset", "bar")
    assert 0 == r.run("sismember", "myset", "bla")
    assert "1" == r.run("smismember", "myset", "foo")
    assert "1 1" == r.run("smismember", "myset", "foo", "bar")
    assert "1 0" == r.run("smismember", "myset", "foo", "bla")
    assert "0 1" == r.run("smismember", "myset", "bla", "foo")
    assert "0" == r.run("smismember", "myset", "bla")
    # TODO: assert_equal "bar $initelems($type)" lsort [r smembers myset]
    r.run("memory", "usage", "myset")


def test_sadd_scard_sismember_smismember_smembers_basics_intset(r: ValkeyTestClient) -> None:
    """
    test {SADD, SCARD, SISMEMBER, SMISMEMBER, SMEMBERS basics - intset} {
        create_set myset {17}
        assert_encoding intset myset
        assert_equal 1 [r sadd myset 16]
        assert_equal 0 [r sadd myset 16]
        assert_equal 2 [r scard myset]
        assert_equal 1 [r sismember myset 16]
        assert_equal 1 [r sismember myset 17]
        assert_equal 0 [r sismember myset 18]
        assert_equal {1} [r smismember myset 16]
        assert_equal {1 1} [r smismember myset 16 17]
        assert_equal {1 0} [r smismember myset 16 18]
        assert_equal {0 1} [r smismember myset 18 16]
        assert_equal {0} [r smismember myset 18]
        assert_equal {16 17} [lsort [r smembers myset]]
        r memory usage myset
    }
    """
    create_set("myset", "17")
    assert_encoding("intset", "myset")
    assert 1 == r.run("sadd", "myset", 16)
    assert 0 == r.run("sadd", "myset", 16)
    assert 2 == r.run("scard", "myset")
    assert 1 == r.run("sismember", "myset", 16)
    assert 1 == r.run("sismember", "myset", 17)
    assert 0 == r.run("sismember", "myset", 18)
    assert "1" == r.run("smismember", "myset", 16)
    assert "1 1" == r.run("smismember", "myset", 16, 17)
    assert "1 0" == r.run("smismember", "myset", 16, 18)
    assert "0 1" == r.run("smismember", "myset", 18, 16)
    assert "0" == r.run("smismember", "myset", 18)
    assert "16 17" == sorted(r.run("smembers", "myset"))
    r.run("memory", "usage", "myset")


def test_smismember_smembers_scard_against_non_set(r: ValkeyTestClient) -> None:
    """
    test {SMISMEMBER SMEMBERS SCARD against non set} {
        r lpush mylist foo
        assert_error WRONGTYPE* {r smismember mylist bar}
        assert_error WRONGTYPE* {r smembers mylist}
        assert_error WRONGTYPE* {r scard mylist}
    }
    """
    r.run("lpush", "mylist", "foo")
    with pytest.raises(Exception, match="WRONGTYPE.*"):
        r.run("smismember", "mylist", "bar")
    with pytest.raises(Exception, match="WRONGTYPE.*"):
        r.run("smembers", "mylist")
    with pytest.raises(Exception, match="WRONGTYPE.*"):
        r.run("scard", "mylist")


def test_smismember_smembers_scard_against_non_existing_key(r: ValkeyTestClient) -> None:
    """
    test {SMISMEMBER SMEMBERS SCARD against non existing key} {
        assert_equal {0} [r smismember myset1 foo]
        assert_equal {0 0} [r smismember myset1 foo bar]
        assert_equal {} [r smembers myset1]
        assert_equal {0} [r scard myset1]
    }
    """
    assert "0" == r.run("smismember", "myset1", "foo")
    assert "0 0" == r.run("smismember", "myset1", "foo", "bar")
    assert "" == r.run("smembers", "myset1")
    assert "0" == r.run("scard", "myset1")


def test_smismember_requires_one_or_more_members(r: ValkeyTestClient) -> None:
    """
    test {SMISMEMBER requires one or more members} {
        r del zmscoretest
        r zadd zmscoretest 10 x
        r zadd zmscoretest 20 y

        catch {r smismember zmscoretest} e
        assert_match {*ERR*wrong*number*arg*} $e
    }
    """
    r.run("del", "zmscoretest")
    r.run("zadd", "zmscoretest", 10, "x")
    r.run("zadd", "zmscoretest", 20, "y")
    try:
        e = r.run("smismember", "zmscoretest")
    except Exception as _catch_err:
        e = str(_catch_err)
    assert fnmatch(str(e), "*ERR*wrong*number*arg*")


def test_sadd_against_non_set(r: ValkeyTestClient) -> None:
    """
    test {SADD against non set} {
        r lpush mylist foo
        assert_error WRONGTYPE* {r sadd mylist bar}
    }
    """
    r.run("lpush", "mylist", "foo")
    with pytest.raises(Exception, match="WRONGTYPE.*"):
        r.run("sadd", "mylist", "bar")


def test_sadd_a_non_integer_against_a_small_intset(r: ValkeyTestClient) -> None:
    """
    test "SADD a non-integer against a small intset" {
        create_set myset {1 2 3}
        assert_encoding intset myset
        assert_equal 1 [r sadd myset a]
        assert_encoding listpack myset
    }
    """
    create_set("myset", "1 2 3")
    assert_encoding("intset", "myset")
    assert 1 == r.run("sadd", "myset", "a")
    assert_encoding("listpack", "myset")


def test_sadd_a_non_integer_against_a_large_intset(r: ValkeyTestClient) -> None:
    """
    test "SADD a non-integer against a large intset" {
        create_set myset {0}
        for {set i 1} {$i < 130} {incr i} {r sadd myset $i}
        assert_encoding intset myset
        assert_equal 1 [r sadd myset a]
        assert_encoding hashtable myset
    }
    """
    create_set("myset", "0")
    i = 1
    while i < 130:
        r.run("sadd", "myset", i)
        i += 1
    assert_encoding("intset", "myset")
    assert 1 == r.run("sadd", "myset", "a")
    assert_encoding("hashtable", "myset")


def test_sadd_an_integer_larger_than_64_bits(r: ValkeyTestClient) -> None:
    """
    test "SADD an integer larger than 64 bits" {
        create_set myset {213244124402402314402033402}
        assert_encoding listpack myset
        assert_equal 1 [r sismember myset 213244124402402314402033402]
        assert_equal {1} [r smismember myset 213244124402402314402033402]
    }
    """
    create_set("myset", "213244124402402314402033402")
    assert_encoding("listpack", "myset")
    assert 1 == r.run("sismember", "myset", 213244124402402314402033402)
    assert "1" == r.run("smismember", "myset", 213244124402402314402033402)


def test_sadd_an_integer_larger_than_64_bits_to_a_large_intset(r: ValkeyTestClient) -> None:
    """
    test "SADD an integer larger than 64 bits to a large intset" {
        create_set myset {0}
        for {set i 1} {$i < 130} {incr i} {r sadd myset $i}
        assert_encoding intset myset
        r sadd myset 213244124402402314402033402
        assert_encoding hashtable myset
        assert_equal 1 [r sismember myset 213244124402402314402033402]
        assert_equal {1} [r smismember myset 213244124402402314402033402]
    }
    """
    create_set("myset", "0")
    i = 1
    while i < 130:
        r.run("sadd", "myset", i)
        i += 1
    assert_encoding("intset", "myset")
    r.run("sadd", "myset", 213244124402402314402033402)
    assert_encoding("hashtable", "myset")
    assert 1 == r.run("sismember", "myset", 213244124402402314402033402)
    assert "1" == r.run("smismember", "myset", 213244124402402314402033402)


@pytest.mark.parametrize(["type"], [("single"), ("multiple"), ("single_multiple")])
def test_sadd_overflows_the_maximum_allowed_integers_in_an_intset_type(r: ValkeyTestClient, type: str) -> None:
    """
    test "SADD overflows the maximum allowed integers in an intset - $type" {
        r del myset

        if {$type == "single"} {
            # All are single sadd commands.
            for {set i 0} {$i < 512} {incr i} { r sadd myset $i }
        } elseif {$type == "multiple"} {
            # One sadd command to add all elements.
            set args {}
            for {set i 0} {$i < 512} {incr i} { lappend args $i }
            r sadd myset {*}$args
        } elseif {$type == "single_multiple"} {
            # First one sadd adds an element (creates a key) and then one sadd adds all elements.
            r sadd myset 1
            set args {}
            for {set i 0} {$i < 512} {incr i} { lappend args $i }
            r sadd myset {*}$args
        }

        assert_encoding intset myset
        assert_equal 512 [r scard myset]
        assert_equal 1 [r sadd myset 512]
        assert_encoding hashtable myset
    }
    """
    r.run("del", "myset")
    if type == "single":
        i = 0
        while i < 512:
            r.run("sadd", "myset", i)
            i += 1
    elif type == "multiple":
        args = []
        i = 0
        while i < 512:
            args.append(i)
            i += 1
        r.run("sadd", "myset", "*", args)
    elif type == "single_multiple":
        r.run("sadd", "myset", 1)
        args = []
        i = 0
        while i < 512:
            args.append(i)
            i += 1
        r.run("sadd", "myset", "*", args)
    assert_encoding("intset", "myset")
    assert 512 == r.run("scard", "myset")
    assert 1 == r.run("sadd", "myset", 512)
    assert_encoding("hashtable", "myset")


@pytest.mark.parametrize(["type"], [("single"), ("multiple"), ("single_multiple")])
def test_sadd_overflows_the_maximum_allowed_elements_in_a_listpack_type(r: ValkeyTestClient, type: str) -> None:
    """
    test "SADD overflows the maximum allowed elements in a listpack - $type" {
        r del myset

        if {$type == "single"} {
            # All are single sadd commands.
            r sadd myset a
            for {set i 0} {$i < 127} {incr i} { r sadd myset $i }
        } elseif {$type == "multiple"} {
            # One sadd command to add all elements.
            set args {}
            lappend args a
            for {set i 0} {$i < 127} {incr i} { lappend args $i }
            r sadd myset {*}$args
        } elseif {$type == "single_multiple"} {
            # First one sadd adds an element (creates a key) and then one sadd adds all elements.
            r sadd myset a
            set args {}
            lappend args a
            for {set i 0} {$i < 127} {incr i} { lappend args $i }
            r sadd myset {*}$args
        }

        assert_encoding listpack myset
        assert_equal 128 [r scard myset]
        assert_equal 1 [r sadd myset b]
        assert_encoding hashtable myset
    }
    """
    r.run("del", "myset")
    if type == "single":
        r.run("sadd", "myset", "a")
        i = 0
        while i < 127:
            r.run("sadd", "myset", i)
            i += 1
    elif type == "multiple":
        args = []
        args.append("a")
        i = 0
        while i < 127:
            args.append(i)
            i += 1
        r.run("sadd", "myset", "*", args)
    elif type == "single_multiple":
        r.run("sadd", "myset", "a")
        args = []
        args.append("a")
        i = 0
        while i < 127:
            args.append(i)
            i += 1
        r.run("sadd", "myset", "*", args)
    assert_encoding("listpack", "myset")
    assert 128 == r.run("scard", "myset")
    assert 1 == r.run("sadd", "myset", "b")
    assert_encoding("hashtable", "myset")


def test_variadic_sadd(r: ValkeyTestClient) -> None:
    """
    test {Variadic SADD} {
        r del myset
        assert_equal 3 [r sadd myset a b c]
        assert_equal 2 [r sadd myset A a b c B]
        assert_equal [lsort {A a b c B}] [lsort [r smembers myset]]
    }
    """
    r.run("del", "myset")
    assert 3 == r.run("sadd", "myset", "a", "b", "c")
    assert 2 == r.run("sadd", "myset", "A", "a", "b", "c", "B")
    assert sorted("A a b c B") == sorted(r.run("smembers", "myset"))


def test_set_encoding_after_debug_reload(r: ValkeyTestClient) -> None:
    """
    test "Set encoding after DEBUG RELOAD" {
        r del myintset
        r del myhashset
        r del mylargeintset
        r del mysmallset
        for {set i 0} {$i <  100} {incr i} { r sadd myintset $i }
        for {set i 0} {$i < 1280} {incr i} { r sadd mylargeintset $i }
        for {set i 0} {$i <   50} {incr i} { r sadd mysmallset [format "i%03d" $i] }
        for {set i 0} {$i <  256} {incr i} { r sadd myhashset [format "i%03d" $i] }
        assert_encoding intset myintset
        assert_encoding hashtable mylargeintset
        assert_encoding listpack mysmallset
        assert_encoding hashtable myhashset

        r debug reload
        assert_encoding intset myintset
        assert_encoding hashtable mylargeintset
        assert_encoding listpack mysmallset
        assert_encoding hashtable myhashset
    } {} {needs:debug}
    """
    r.run("del", "myintset")
    r.run("del", "myhashset")
    r.run("del", "mylargeintset")
    r.run("del", "mysmallset")
    i = 0
    while i < 100:
        r.run("sadd", "myintset", i)
        i += 1
    i = 0
    while i < 1280:
        r.run("sadd", "mylargeintset", i)
        i += 1
    i = 0
    while i < 50:
        r.run("sadd", "mysmallset", format_("i%03d", i))
        i += 1
    i = 0
    while i < 256:
        r.run("sadd", "myhashset", format_("i%03d", i))
        i += 1
    assert_encoding("intset", "myintset")
    assert_encoding("hashtable", "mylargeintset")
    assert_encoding("listpack", "mysmallset")
    assert_encoding("hashtable", "myhashset")
    r.run("debug", "reload")
    assert_encoding("intset", "myintset")
    assert_encoding("hashtable", "mylargeintset")
    assert_encoding("listpack", "mysmallset")
    assert_encoding("hashtable", "myhashset")


@pytest.mark.xfail(reason="not implemented")
@pytest.mark.parametrize(["type"], [("listpack"), ("hashtable")])
def test_srem_basics_type(r: ValkeyTestClient, type: str) -> None:
    """
    test {SREM basics - $type} {
        create_set myset $initelems($type)
        r sadd myset ciao
        assert_encoding $type myset
        assert_equal 0 [r srem myset qux]
        assert_equal 1 [r srem myset ciao]
        assert_equal $initelems($type) [lsort [r smembers myset]]
    }
    """
    # TODO: create_set myset initelems ($type)
    r.run("sadd", "myset", "ciao")
    assert_encoding(type, "myset")
    assert 0 == r.run("srem", "myset", "qux")
    assert 1 == r.run("srem", "myset", "ciao")
    # TODO: assert_equal initelems ($type) lsort [r smembers myset]


def test_srem_basics_intset(r: ValkeyTestClient) -> None:
    """
    test {SREM basics - intset} {
        create_set myset {3 4 5}
        assert_encoding intset myset
        assert_equal 0 [r srem myset 6]
        assert_equal 1 [r srem myset 4]
        assert_equal {3 5} [lsort [r smembers myset]]
    }
    """
    create_set("myset", "3 4 5")
    assert_encoding("intset", "myset")
    assert 0 == r.run("srem", "myset", 6)
    assert 1 == r.run("srem", "myset", 4)
    assert "3 5" == sorted(r.run("smembers", "myset"))


def test_srem_with_multiple_arguments(r: ValkeyTestClient) -> None:
    """
    test {SREM with multiple arguments} {
        r del myset
        r sadd myset a b c d
        assert_equal 0 [r srem myset k k k]
        assert_equal 2 [r srem myset b d x y]
        lsort [r smembers myset]
    } {a c}
    """
    r.run("del", "myset")
    r.run("sadd", "myset", "a", "b", "c", "d")
    assert 0 == r.run("srem", "myset", "k", "k", "k")
    assert 2 == r.run("srem", "myset", "b", "d", "x", "y")
    assert sorted(r.run("smembers", "myset")) == "a c"


def test_srem_variadic_version_with_more_args_needed_to_destroy_the_key(r: ValkeyTestClient) -> None:
    """
    test {SREM variadic version with more args needed to destroy the key} {
        r del myset
        r sadd myset 1 2 3
        r srem myset 1 2 3 4 5 6 7 8
    } {3}
    """
    r.run("del", "myset")
    r.run("sadd", "myset", 1, 2, 3)
    assert r.run("srem", "myset", 1, 2, 3, 4, 5, 6, 7, 8) == "3"


def test_sintercard_with_illegal_arguments(r: ValkeyTestClient) -> None:
    """
    test "SINTERCARD with illegal arguments" {
        assert_error "ERR wrong number of arguments for 'sintercard' command" {r sintercard}
        assert_error "ERR wrong number of arguments for 'sintercard' command" {r sintercard 1}

        assert_error "ERR numkeys*" {r sintercard 0 myset{t}}
        assert_error "ERR numkeys*" {r sintercard a myset{t}}

        assert_error "ERR Number of keys*" {r sintercard 2 myset{t}}
        assert_error "ERR Number of keys*" {r sintercard 3 myset{t} myset2{t}}

        assert_error "ERR syntax error*" {r sintercard 1 myset{t} myset2{t}}
        assert_error "ERR syntax error*" {r sintercard 1 myset{t} bar_arg}
        assert_error "ERR syntax error*" {r sintercard 1 myset{t} LIMIT}

        assert_error "ERR LIMIT*" {r sintercard 1 myset{t} LIMIT -1}
        assert_error "ERR LIMIT*" {r sintercard 1 myset{t} LIMIT a}
    }
    """
    with pytest.raises(Exception, match="ERR\\ wrong\\ number\\ of\\ arguments\\ for\\ 'sintercard'\\ command"):
        r.run("sintercard")
    with pytest.raises(Exception, match="ERR\\ wrong\\ number\\ of\\ arguments\\ for\\ 'sintercard'\\ command"):
        r.run("sintercard", 1)
    with pytest.raises(Exception, match="ERR\\ numkeys.*"):
        r.run("sintercard", 0, "myset{t}")
    with pytest.raises(Exception, match="ERR\\ numkeys.*"):
        r.run("sintercard", "a", "myset{t}")
    with pytest.raises(Exception, match="ERR\\ Number\\ of\\ keys.*"):
        r.run("sintercard", 2, "myset{t}")
    with pytest.raises(Exception, match="ERR\\ Number\\ of\\ keys.*"):
        r.run("sintercard", 3, "myset{t}", "myset2{t}")
    with pytest.raises(Exception, match="ERR\\ syntax\\ error.*"):
        r.run("sintercard", 1, "myset{t}", "myset2{t}")
    with pytest.raises(Exception, match="ERR\\ syntax\\ error.*"):
        r.run("sintercard", 1, "myset{t}", "bar_arg")
    with pytest.raises(Exception, match="ERR\\ syntax\\ error.*"):
        r.run("sintercard", 1, "myset{t}", "LIMIT")
    with pytest.raises(Exception, match="ERR\\ LIMIT.*"):
        r.run("sintercard", 1, "myset{t}", "LIMIT", -1)
    with pytest.raises(Exception, match="ERR\\ LIMIT.*"):
        r.run("sintercard", 1, "myset{t}", "LIMIT", "a")


def test_sintercard_against_non_set_should_throw_error(r: ValkeyTestClient) -> None:
    """
    test "SINTERCARD against non-set should throw error" {
        r del set{t}
        r sadd set{t} a b c
        r set key1{t} x

        assert_error "WRONGTYPE*" {r sintercard 1 key1{t}}
        assert_error "WRONGTYPE*" {r sintercard 2 set{t} key1{t}}
        assert_error "WRONGTYPE*" {r sintercard 2 key1{t} noset{t}}
    }
    """
    r.run("del", "set{t}")
    r.run("sadd", "set{t}", "a", "b", "c")
    r.run("set", "key1{t}", "x")
    with pytest.raises(Exception, match="WRONGTYPE.*"):
        r.run("sintercard", 1, "key1{t}")
    with pytest.raises(Exception, match="WRONGTYPE.*"):
        r.run("sintercard", 2, "set{t}", "key1{t}")
    with pytest.raises(Exception, match="WRONGTYPE.*"):
        r.run("sintercard", 2, "key1{t}", "noset{t}")


def test_sintercard_against_non_existing_key(r: ValkeyTestClient) -> None:
    """
    test "SINTERCARD against non-existing key" {
        assert_equal 0 [r sintercard 1 non-existing-key]
        assert_equal 0 [r sintercard 1 non-existing-key limit 0]
        assert_equal 0 [r sintercard 1 non-existing-key limit 10]
    }
    """
    assert 0 == r.run("sintercard", 1, "non-existing-key")
    assert 0 == r.run("sintercard", 1, "non-existing-key", "limit", 0)
    assert 0 == r.run("sintercard", 1, "non-existing-key", "limit", 10)


@pytest.mark.parametrize(
    ["type", "smallenc", "bigenc"], [("regular", "listpack", "hashtable"), ("intset", "intset", "intset")]
)
def test_generated_sets_must_be_encoded_correctly_type(
    r: ValkeyTestClient, type: str, smallenc: str, bigenc: str
) -> None:
    """
    test "Generated sets must be encoded correctly - $type" {
        for {set i 1} {$i <= 5} {incr i} {
            assert_encoding $encoding($i) [format "set%d{t}" $i]
        }
    }
    """
    if type == "regular":
        smallenc = "listpack"
        bigenc = "hashtable"
    else:
        smallenc = "intset"
        bigenc = "intset"
    array("set", "encoding", f"1 {bigenc} 2 {bigenc} 3 {smallenc} 4 {bigenc} 5 {smallenc}")
    i = 1
    while i <= 5:
        r.run("del", format_("set%d{t}", i))
        i += 1
    i = 0
    while i < 200:
        r.run("sadd", "set1{t}", i)
        r.run("sadd", "set2{t}", expr(i, 195))
        i += 1
    foreach("i", "199 195 1000 2000", "            r sadd set3{t} $i\n        ")
    i = 5
    while i < 200:
        r.run("sadd", "set4{t}", i)
        i += 1
    r.run("sadd", "set5{t}", 0)
    large = 200
    if type == "regular":
        large = "foo"
    i = 1
    while i <= 5:
        r.run("sadd", format_("set%d{t}", i), large)
        i += 1
    for_(
        "set i 1",
        "$i <= 5",
        "incr i",
        '                assert_encoding $encoding($i) [format "set%d{t}" $i]\n            ',
    )


@pytest.mark.parametrize(
    ["type", "smallenc", "bigenc"], [("regular", "listpack", "hashtable"), ("intset", "intset", "intset")]
)
def test_sinter_with_two_sets_type(r: ValkeyTestClient, type: str, smallenc: str, bigenc: str) -> None:
    """
    test "SINTER with two sets - $type" {
        assert_equal [list 195 196 197 198 199 $large] [lsort [r sinter set1{t} set2{t}]]
    }
    """
    if type == "regular":
        smallenc = "listpack"
        bigenc = "hashtable"
    else:
        smallenc = "intset"
        bigenc = "intset"
    array("set", "encoding", f"1 {bigenc} 2 {bigenc} 3 {smallenc} 4 {bigenc} 5 {smallenc}")
    i = 1
    while i <= 5:
        r.run("del", format_("set%d{t}", i))
        i += 1
    i = 0
    while i < 200:
        r.run("sadd", "set1{t}", i)
        r.run("sadd", "set2{t}", expr(i, 195))
        i += 1
    foreach("i", "199 195 1000 2000", "            r sadd set3{t} $i\n        ")
    i = 5
    while i < 200:
        r.run("sadd", "set4{t}", i)
        i += 1
    r.run("sadd", "set5{t}", 0)
    large = 200
    if type == "regular":
        large = "foo"
    i = 1
    while i <= 5:
        r.run("sadd", format_("set%d{t}", i), large)
        i += 1
    assert [195, 196, 197, 198, 199, large] == sorted(r.run("sinter", "set1{t}", "set2{t}"))


@pytest.mark.parametrize(
    ["type", "smallenc", "bigenc"], [("regular", "listpack", "hashtable"), ("intset", "intset", "intset")]
)
def test_sintercard_with_two_sets_type(r: ValkeyTestClient, type: str, smallenc: str, bigenc: str) -> None:
    """
    test "SINTERCARD with two sets - $type" {
        assert_equal 6 [r sintercard 2 set1{t} set2{t}]
        assert_equal 6 [r sintercard 2 set1{t} set2{t} limit 0]
        assert_equal 3 [r sintercard 2 set1{t} set2{t} limit 3]
        assert_equal 6 [r sintercard 2 set1{t} set2{t} limit 10]
    }
    """
    if type == "regular":
        smallenc = "listpack"
        bigenc = "hashtable"
    else:
        smallenc = "intset"
        bigenc = "intset"
    array("set", "encoding", f"1 {bigenc} 2 {bigenc} 3 {smallenc} 4 {bigenc} 5 {smallenc}")
    i = 1
    while i <= 5:
        r.run("del", format_("set%d{t}", i))
        i += 1
    i = 0
    while i < 200:
        r.run("sadd", "set1{t}", i)
        r.run("sadd", "set2{t}", expr(i, 195))
        i += 1
    foreach("i", "199 195 1000 2000", "            r sadd set3{t} $i\n        ")
    i = 5
    while i < 200:
        r.run("sadd", "set4{t}", i)
        i += 1
    r.run("sadd", "set5{t}", 0)
    large = 200
    if type == "regular":
        large = "foo"
    i = 1
    while i <= 5:
        r.run("sadd", format_("set%d{t}", i), large)
        i += 1
    assert 6 == r.run("sintercard", 2, "set1{t}", "set2{t}")
    assert 6 == r.run("sintercard", 2, "set1{t}", "set2{t}", "limit", 0)
    assert 3 == r.run("sintercard", 2, "set1{t}", "set2{t}", "limit", 3)
    assert 6 == r.run("sintercard", 2, "set1{t}", "set2{t}", "limit", 10)


@pytest.mark.parametrize(
    ["type", "smallenc", "bigenc"], [("regular", "listpack", "hashtable"), ("intset", "intset", "intset")]
)
def test_sinterstore_with_two_sets_type(r: ValkeyTestClient, type: str, smallenc: str, bigenc: str) -> None:
    """
    test "SINTERSTORE with two sets - $type" {
        r sinterstore setres{t} set1{t} set2{t}
        assert_encoding $smallenc setres{t}
        assert_equal [list 195 196 197 198 199 $large] [lsort [r smembers setres{t}]]
    }
    """
    if type == "regular":
        smallenc = "listpack"
        bigenc = "hashtable"
    else:
        smallenc = "intset"
        bigenc = "intset"
    array("set", "encoding", f"1 {bigenc} 2 {bigenc} 3 {smallenc} 4 {bigenc} 5 {smallenc}")
    i = 1
    while i <= 5:
        r.run("del", format_("set%d{t}", i))
        i += 1
    i = 0
    while i < 200:
        r.run("sadd", "set1{t}", i)
        r.run("sadd", "set2{t}", expr(i, 195))
        i += 1
    foreach("i", "199 195 1000 2000", "            r sadd set3{t} $i\n        ")
    i = 5
    while i < 200:
        r.run("sadd", "set4{t}", i)
        i += 1
    r.run("sadd", "set5{t}", 0)
    large = 200
    if type == "regular":
        large = "foo"
    i = 1
    while i <= 5:
        r.run("sadd", format_("set%d{t}", i), large)
        i += 1
    r.run("sinterstore", "setres{t}", "set1{t}", "set2{t}")
    assert_encoding(smallenc, "setres{t}")
    assert [195, 196, 197, 198, 199, large] == sorted(r.run("smembers", "setres{t}"))


@pytest.mark.parametrize(
    ["type", "smallenc", "bigenc"], [("regular", "listpack", "hashtable"), ("intset", "intset", "intset")]
)
def test_sinterstore_with_two_sets_after_a_debug_reload_type(
    r: ValkeyTestClient, type: str, smallenc: str, bigenc: str
) -> None:
    """
    test "SINTERSTORE with two sets, after a DEBUG RELOAD - $type" {
        r debug reload
        r sinterstore setres{t} set1{t} set2{t}
        assert_encoding $smallenc setres{t}
        assert_equal [list 195 196 197 198 199 $large] [lsort [r smembers setres{t}]]
    } {} {needs:debug}
    """
    if type == "regular":
        smallenc = "listpack"
        bigenc = "hashtable"
    else:
        smallenc = "intset"
        bigenc = "intset"
    array("set", "encoding", f"1 {bigenc} 2 {bigenc} 3 {smallenc} 4 {bigenc} 5 {smallenc}")
    i = 1
    while i <= 5:
        r.run("del", format_("set%d{t}", i))
        i += 1
    i = 0
    while i < 200:
        r.run("sadd", "set1{t}", i)
        r.run("sadd", "set2{t}", expr(i, 195))
        i += 1
    foreach("i", "199 195 1000 2000", "            r sadd set3{t} $i\n        ")
    i = 5
    while i < 200:
        r.run("sadd", "set4{t}", i)
        i += 1
    r.run("sadd", "set5{t}", 0)
    large = 200
    if type == "regular":
        large = "foo"
    i = 1
    while i <= 5:
        r.run("sadd", format_("set%d{t}", i), large)
        i += 1
    r.run("debug", "reload")
    r.run("sinterstore", "setres{t}", "set1{t}", "set2{t}")
    assert_encoding(smallenc, "setres{t}")
    assert [195, 196, 197, 198, 199, large] == sorted(r.run("smembers", "setres{t}"))


@pytest.mark.parametrize(
    ["type", "smallenc", "bigenc"], [("regular", "listpack", "hashtable"), ("intset", "intset", "intset")]
)
def test_sunion_with_two_sets_type(r: ValkeyTestClient, type: str, smallenc: str, bigenc: str) -> None:
    """
    test "SUNION with two sets - $type" {
        set expected [lsort -uniq "[r smembers set1{t}] [r smembers set2{t}]"]
        assert_equal $expected [lsort [r sunion set1{t} set2{t}]]
    }
    """
    if type == "regular":
        smallenc = "listpack"
        bigenc = "hashtable"
    else:
        smallenc = "intset"
        bigenc = "intset"
    array("set", "encoding", f"1 {bigenc} 2 {bigenc} 3 {smallenc} 4 {bigenc} 5 {smallenc}")
    i = 1
    while i <= 5:
        r.run("del", format_("set%d{t}", i))
        i += 1
    i = 0
    while i < 200:
        r.run("sadd", "set1{t}", i)
        r.run("sadd", "set2{t}", expr(i, 195))
        i += 1
    foreach("i", "199 195 1000 2000", "            r sadd set3{t} $i\n        ")
    i = 5
    while i < 200:
        r.run("sadd", "set4{t}", i)
        i += 1
    r.run("sadd", "set5{t}", 0)
    large = 200
    if type == "regular":
        large = "foo"
    i = 1
    while i <= 5:
        r.run("sadd", format_("set%d{t}", i), large)
        i += 1
    expected = sorted("[r smembers set1{t}] [r smembers set2{t}]")
    assert expected == sorted(r.run("sunion", "set1{t}", "set2{t}"))


@pytest.mark.parametrize(
    ["type", "smallenc", "bigenc"], [("regular", "listpack", "hashtable"), ("intset", "intset", "intset")]
)
def test_sunionstore_with_two_sets_type(r: ValkeyTestClient, type: str, smallenc: str, bigenc: str) -> None:
    """
    test "SUNIONSTORE with two sets - $type" {
        r sunionstore setres{t} set1{t} set2{t}
        assert_encoding $bigenc setres{t}
        set expected [lsort -uniq "[r smembers set1{t}] [r smembers set2{t}]"]
        assert_equal $expected [lsort [r smembers setres{t}]]
    }
    """
    if type == "regular":
        smallenc = "listpack"
        bigenc = "hashtable"
    else:
        smallenc = "intset"
        bigenc = "intset"
    array("set", "encoding", f"1 {bigenc} 2 {bigenc} 3 {smallenc} 4 {bigenc} 5 {smallenc}")
    i = 1
    while i <= 5:
        r.run("del", format_("set%d{t}", i))
        i += 1
    i = 0
    while i < 200:
        r.run("sadd", "set1{t}", i)
        r.run("sadd", "set2{t}", expr(i, 195))
        i += 1
    foreach("i", "199 195 1000 2000", "            r sadd set3{t} $i\n        ")
    i = 5
    while i < 200:
        r.run("sadd", "set4{t}", i)
        i += 1
    r.run("sadd", "set5{t}", 0)
    large = 200
    if type == "regular":
        large = "foo"
    i = 1
    while i <= 5:
        r.run("sadd", format_("set%d{t}", i), large)
        i += 1
    r.run("sunionstore", "setres{t}", "set1{t}", "set2{t}")
    assert_encoding(bigenc, "setres{t}")
    expected = sorted("[r smembers set1{t}] [r smembers set2{t}]")
    assert expected == sorted(r.run("smembers", "setres{t}"))


@pytest.mark.parametrize(
    ["type", "smallenc", "bigenc"], [("regular", "listpack", "hashtable"), ("intset", "intset", "intset")]
)
def test_sinter_against_three_sets_type(r: ValkeyTestClient, type: str, smallenc: str, bigenc: str) -> None:
    """
    test "SINTER against three sets - $type" {
        assert_equal [list 195 199 $large] [lsort [r sinter set1{t} set2{t} set3{t}]]
    }
    """
    if type == "regular":
        smallenc = "listpack"
        bigenc = "hashtable"
    else:
        smallenc = "intset"
        bigenc = "intset"
    array("set", "encoding", f"1 {bigenc} 2 {bigenc} 3 {smallenc} 4 {bigenc} 5 {smallenc}")
    i = 1
    while i <= 5:
        r.run("del", format_("set%d{t}", i))
        i += 1
    i = 0
    while i < 200:
        r.run("sadd", "set1{t}", i)
        r.run("sadd", "set2{t}", expr(i, 195))
        i += 1
    foreach("i", "199 195 1000 2000", "            r sadd set3{t} $i\n        ")
    i = 5
    while i < 200:
        r.run("sadd", "set4{t}", i)
        i += 1
    r.run("sadd", "set5{t}", 0)
    large = 200
    if type == "regular":
        large = "foo"
    i = 1
    while i <= 5:
        r.run("sadd", format_("set%d{t}", i), large)
        i += 1
    assert [195, 199, large] == sorted(r.run("sinter", "set1{t}", "set2{t}", "set3{t}"))


@pytest.mark.parametrize(
    ["type", "smallenc", "bigenc"], [("regular", "listpack", "hashtable"), ("intset", "intset", "intset")]
)
def test_sintercard_against_three_sets_type(r: ValkeyTestClient, type: str, smallenc: str, bigenc: str) -> None:
    """
    test "SINTERCARD against three sets - $type" {
        assert_equal 3 [r sintercard 3 set1{t} set2{t} set3{t}]
        assert_equal 3 [r sintercard 3 set1{t} set2{t} set3{t} limit 0]
        assert_equal 2 [r sintercard 3 set1{t} set2{t} set3{t} limit 2]
        assert_equal 3 [r sintercard 3 set1{t} set2{t} set3{t} limit 10]
    }
    """
    if type == "regular":
        smallenc = "listpack"
        bigenc = "hashtable"
    else:
        smallenc = "intset"
        bigenc = "intset"
    array("set", "encoding", f"1 {bigenc} 2 {bigenc} 3 {smallenc} 4 {bigenc} 5 {smallenc}")
    i = 1
    while i <= 5:
        r.run("del", format_("set%d{t}", i))
        i += 1
    i = 0
    while i < 200:
        r.run("sadd", "set1{t}", i)
        r.run("sadd", "set2{t}", expr(i, 195))
        i += 1
    foreach("i", "199 195 1000 2000", "            r sadd set3{t} $i\n        ")
    i = 5
    while i < 200:
        r.run("sadd", "set4{t}", i)
        i += 1
    r.run("sadd", "set5{t}", 0)
    large = 200
    if type == "regular":
        large = "foo"
    i = 1
    while i <= 5:
        r.run("sadd", format_("set%d{t}", i), large)
        i += 1
    assert 3 == r.run("sintercard", 3, "set1{t}", "set2{t}", "set3{t}")
    assert 3 == r.run("sintercard", 3, "set1{t}", "set2{t}", "set3{t}", "limit", 0)
    assert 2 == r.run("sintercard", 3, "set1{t}", "set2{t}", "set3{t}", "limit", 2)
    assert 3 == r.run("sintercard", 3, "set1{t}", "set2{t}", "set3{t}", "limit", 10)


@pytest.mark.parametrize(
    ["type", "smallenc", "bigenc"], [("regular", "listpack", "hashtable"), ("intset", "intset", "intset")]
)
def test_sinterstore_with_three_sets_type(r: ValkeyTestClient, type: str, smallenc: str, bigenc: str) -> None:
    """
    test "SINTERSTORE with three sets - $type" {
        r sinterstore setres{t} set1{t} set2{t} set3{t}
        assert_equal [list 195 199 $large] [lsort [r smembers setres{t}]]
    }
    """
    if type == "regular":
        smallenc = "listpack"
        bigenc = "hashtable"
    else:
        smallenc = "intset"
        bigenc = "intset"
    array("set", "encoding", f"1 {bigenc} 2 {bigenc} 3 {smallenc} 4 {bigenc} 5 {smallenc}")
    i = 1
    while i <= 5:
        r.run("del", format_("set%d{t}", i))
        i += 1
    i = 0
    while i < 200:
        r.run("sadd", "set1{t}", i)
        r.run("sadd", "set2{t}", expr(i, 195))
        i += 1
    foreach("i", "199 195 1000 2000", "            r sadd set3{t} $i\n        ")
    i = 5
    while i < 200:
        r.run("sadd", "set4{t}", i)
        i += 1
    r.run("sadd", "set5{t}", 0)
    large = 200
    if type == "regular":
        large = "foo"
    i = 1
    while i <= 5:
        r.run("sadd", format_("set%d{t}", i), large)
        i += 1
    r.run("sinterstore", "setres{t}", "set1{t}", "set2{t}", "set3{t}")
    assert [195, 199, large] == sorted(r.run("smembers", "setres{t}"))


@pytest.mark.parametrize(
    ["type", "smallenc", "bigenc"], [("regular", "listpack", "hashtable"), ("intset", "intset", "intset")]
)
def test_sunion_with_non_existing_keys_type(r: ValkeyTestClient, type: str, smallenc: str, bigenc: str) -> None:
    """
    test "SUNION with non existing keys - $type" {
        set expected [lsort -uniq "[r smembers set1{t}] [r smembers set2{t}]"]
        assert_equal $expected [lsort [r sunion nokey1{t} set1{t} set2{t} nokey2{t}]]
    }
    """
    if type == "regular":
        smallenc = "listpack"
        bigenc = "hashtable"
    else:
        smallenc = "intset"
        bigenc = "intset"
    array("set", "encoding", f"1 {bigenc} 2 {bigenc} 3 {smallenc} 4 {bigenc} 5 {smallenc}")
    i = 1
    while i <= 5:
        r.run("del", format_("set%d{t}", i))
        i += 1
    i = 0
    while i < 200:
        r.run("sadd", "set1{t}", i)
        r.run("sadd", "set2{t}", expr(i, 195))
        i += 1
    foreach("i", "199 195 1000 2000", "            r sadd set3{t} $i\n        ")
    i = 5
    while i < 200:
        r.run("sadd", "set4{t}", i)
        i += 1
    r.run("sadd", "set5{t}", 0)
    large = 200
    if type == "regular":
        large = "foo"
    i = 1
    while i <= 5:
        r.run("sadd", format_("set%d{t}", i), large)
        i += 1
    expected = sorted("[r smembers set1{t}] [r smembers set2{t}]")
    assert expected == sorted(r.run("sunion", "nokey1{t}", "set1{t}", "set2{t}", "nokey2{t}"))


@pytest.mark.parametrize(
    ["type", "smallenc", "bigenc"], [("regular", "listpack", "hashtable"), ("intset", "intset", "intset")]
)
def test_sdiff_with_two_sets_type(r: ValkeyTestClient, type: str, smallenc: str, bigenc: str) -> None:
    """
    test "SDIFF with two sets - $type" {
        assert_equal {0 1 2 3 4} [lsort [r sdiff set1{t} set4{t}]]
    }
    """
    if type == "regular":
        smallenc = "listpack"
        bigenc = "hashtable"
    else:
        smallenc = "intset"
        bigenc = "intset"
    array("set", "encoding", f"1 {bigenc} 2 {bigenc} 3 {smallenc} 4 {bigenc} 5 {smallenc}")
    i = 1
    while i <= 5:
        r.run("del", format_("set%d{t}", i))
        i += 1
    i = 0
    while i < 200:
        r.run("sadd", "set1{t}", i)
        r.run("sadd", "set2{t}", expr(i, 195))
        i += 1
    foreach("i", "199 195 1000 2000", "            r sadd set3{t} $i\n        ")
    i = 5
    while i < 200:
        r.run("sadd", "set4{t}", i)
        i += 1
    r.run("sadd", "set5{t}", 0)
    large = 200
    if type == "regular":
        large = "foo"
    i = 1
    while i <= 5:
        r.run("sadd", format_("set%d{t}", i), large)
        i += 1
    assert "0 1 2 3 4" == sorted(r.run("sdiff", "set1{t}", "set4{t}"))


@pytest.mark.parametrize(
    ["type", "smallenc", "bigenc"], [("regular", "listpack", "hashtable"), ("intset", "intset", "intset")]
)
def test_sdiff_with_three_sets_type(r: ValkeyTestClient, type: str, smallenc: str, bigenc: str) -> None:
    """
    test "SDIFF with three sets - $type" {
        assert_equal {1 2 3 4} [lsort [r sdiff set1{t} set4{t} set5{t}]]
    }
    """
    if type == "regular":
        smallenc = "listpack"
        bigenc = "hashtable"
    else:
        smallenc = "intset"
        bigenc = "intset"
    array("set", "encoding", f"1 {bigenc} 2 {bigenc} 3 {smallenc} 4 {bigenc} 5 {smallenc}")
    i = 1
    while i <= 5:
        r.run("del", format_("set%d{t}", i))
        i += 1
    i = 0
    while i < 200:
        r.run("sadd", "set1{t}", i)
        r.run("sadd", "set2{t}", expr(i, 195))
        i += 1
    foreach("i", "199 195 1000 2000", "            r sadd set3{t} $i\n        ")
    i = 5
    while i < 200:
        r.run("sadd", "set4{t}", i)
        i += 1
    r.run("sadd", "set5{t}", 0)
    large = 200
    if type == "regular":
        large = "foo"
    i = 1
    while i <= 5:
        r.run("sadd", format_("set%d{t}", i), large)
        i += 1
    assert "1 2 3 4" == sorted(r.run("sdiff", "set1{t}", "set4{t}", "set5{t}"))


@pytest.mark.parametrize(
    ["type", "smallenc", "bigenc"], [("regular", "listpack", "hashtable"), ("intset", "intset", "intset")]
)
def test_sdiffstore_with_three_sets_type(r: ValkeyTestClient, type: str, smallenc: str, bigenc: str) -> None:
    """
    test "SDIFFSTORE with three sets - $type" {
        r sdiffstore setres{t} set1{t} set4{t} set5{t}
        # When we start with intsets, we should always end with intsets.
        if {$type eq {intset}} {
            assert_encoding intset setres{t}
        }
        assert_equal {1 2 3 4} [lsort [r smembers setres{t}]]
    }
    """
    if type == "regular":
        smallenc = "listpack"
        bigenc = "hashtable"
    else:
        smallenc = "intset"
        bigenc = "intset"
    array("set", "encoding", f"1 {bigenc} 2 {bigenc} 3 {smallenc} 4 {bigenc} 5 {smallenc}")
    i = 1
    while i <= 5:
        r.run("del", format_("set%d{t}", i))
        i += 1
    i = 0
    while i < 200:
        r.run("sadd", "set1{t}", i)
        r.run("sadd", "set2{t}", expr(i, 195))
        i += 1
    foreach("i", "199 195 1000 2000", "            r sadd set3{t} $i\n        ")
    i = 5
    while i < 200:
        r.run("sadd", "set4{t}", i)
        i += 1
    r.run("sadd", "set5{t}", 0)
    large = 200
    if type == "regular":
        large = "foo"
    i = 1
    while i <= 5:
        r.run("sadd", format_("set%d{t}", i), large)
        i += 1
    r.run("sdiffstore", "setres{t}", "set1{t}", "set4{t}", "set5{t}")
    if type == "intset":
        assert_encoding("intset", "setres{t}")
    assert "1 2 3 4" == sorted(r.run("smembers", "setres{t}"))


@pytest.mark.parametrize(
    ["type", "smallenc", "bigenc"], [("regular", "listpack", "hashtable"), ("intset", "intset", "intset")]
)
def test_sinter_or_sunion_or_sdiff_with_three_same_sets_type(
    r: ValkeyTestClient, type: str, smallenc: str, bigenc: str
) -> None:
    """
    test "SINTER/SUNION/SDIFF with three same sets - $type" {
        set expected [lsort "[r smembers set1{t}]"]
        assert_equal $expected [lsort [r sinter set1{t} set1{t} set1{t}]]
        assert_equal $expected [lsort [r sunion set1{t} set1{t} set1{t}]]
        assert_equal {} [lsort [r sdiff set1{t} set1{t} set1{t}]]
    }
    """
    if type == "regular":
        smallenc = "listpack"
        bigenc = "hashtable"
    else:
        smallenc = "intset"
        bigenc = "intset"
    array("set", "encoding", f"1 {bigenc} 2 {bigenc} 3 {smallenc} 4 {bigenc} 5 {smallenc}")
    i = 1
    while i <= 5:
        r.run("del", format_("set%d{t}", i))
        i += 1
    i = 0
    while i < 200:
        r.run("sadd", "set1{t}", i)
        r.run("sadd", "set2{t}", expr(i, 195))
        i += 1
    foreach("i", "199 195 1000 2000", "            r sadd set3{t} $i\n        ")
    i = 5
    while i < 200:
        r.run("sadd", "set4{t}", i)
        i += 1
    r.run("sadd", "set5{t}", 0)
    large = 200
    if type == "regular":
        large = "foo"
    i = 1
    while i <= 5:
        r.run("sadd", format_("set%d{t}", i), large)
        i += 1
    expected = sorted("[r smembers set1{t}]")
    assert expected == sorted(r.run("sinter", "set1{t}", "set1{t}", "set1{t}"))
    assert expected == sorted(r.run("sunion", "set1{t}", "set1{t}", "set1{t}"))
    assert "" == sorted(r.run("sdiff", "set1{t}", "set1{t}", "set1{t}"))


def test_sinterstore_with_two_listpack_sets_where_result_is_intset(r: ValkeyTestClient) -> None:
    """
    test "SINTERSTORE with two listpack sets where result is intset" {
        r del setres{t} set1{t} set2{t}
        r sadd set1{t} a b c 1 3 6 x y z
        r sadd set2{t} e f g 1 2 3 u v w
        assert_encoding listpack set1{t}
        assert_encoding listpack set2{t}
        r sinterstore setres{t} set1{t} set2{t}
        assert_equal [list 1 3] [lsort [r smembers setres{t}]]
        assert_encoding intset setres{t}
    }
    """
    r.run("del", "setres{t}", "set1{t}", "set2{t}")
    r.run("sadd", "set1{t}", "a", "b", "c", 1, 3, 6, "x", "y", "z")
    r.run("sadd", "set2{t}", "e", "f", "g", 1, 2, 3, "u", "v", "w")
    assert_encoding("listpack", "set1{t}")
    assert_encoding("listpack", "set2{t}")
    r.run("sinterstore", "setres{t}", "set1{t}", "set2{t}")
    assert [1, 3] == sorted(r.run("smembers", "setres{t}"))
    assert_encoding("intset", "setres{t}")


def test_sinterstore_with_two_hashtable_sets_where_result_is_intset(r: ValkeyTestClient) -> None:
    """
    test "SINTERSTORE with two hashtable sets where result is intset" {
        r del setres{t} set1{t} set2{t}
        r sadd set1{t} a b c 444 555 666
        r sadd set2{t} e f g 111 222 333
        set expected {}
        for {set i 1} {$i < 130} {incr i} {
            r sadd set1{t} $i
            r sadd set2{t} $i
            lappend expected $i
        }
        assert_encoding hashtable set1{t}
        assert_encoding hashtable set2{t}
        r sinterstore setres{t} set1{t} set2{t}
        assert_equal [lsort $expected] [lsort [r smembers setres{t}]]
        assert_encoding intset setres{t}
    }
    """
    r.run("del", "setres{t}", "set1{t}", "set2{t}")
    r.run("sadd", "set1{t}", "a", "b", "c", 444, 555, 666)
    r.run("sadd", "set2{t}", "e", "f", "g", 111, 222, 333)
    expected = []
    i = 1
    while i < 130:
        r.run("sadd", "set1{t}", i)
        r.run("sadd", "set2{t}", i)
        expected.append(i)
        i += 1
    assert_encoding("hashtable", "set1{t}")
    assert_encoding("hashtable", "set2{t}")
    r.run("sinterstore", "setres{t}", "set1{t}", "set2{t}")
    assert sorted(expected) == sorted(r.run("smembers", "setres{t}"))
    assert_encoding("intset", "setres{t}")


def test_sunion_hashtable_and_listpack(r: ValkeyTestClient) -> None:
    """
    test "SUNION hashtable and listpack" {
        # This adds code coverage for adding a non-sds string to a hashtable set
        # which already contains the string.
        r del set1{t} set2{t}
        set union {abcdefghijklmnopqrstuvwxyz1234567890 a b c 1 2 3}
        create_set set1{t} $union
        create_set set2{t} {a b c}
        assert_encoding hashtable set1{t}
        assert_encoding listpack set2{t}
        assert_equal [lsort $union] [lsort [r sunion set1{t} set2{t}]]
    }
    """
    r.run("del", "set1{t}", "set2{t}")
    union = "abcdefghijklmnopqrstuvwxyz1234567890 a b c 1 2 3"
    create_set("set1{t}", union)
    create_set("set2{t}", "a b c")
    assert_encoding("hashtable", "set1{t}")
    assert_encoding("listpack", "set2{t}")
    assert sorted(union) == sorted(r.run("sunion", "set1{t}", "set2{t}"))


def test_sdiff_with_first_set_empty(r: ValkeyTestClient) -> None:
    """
    test "SDIFF with first set empty" {
        r del set1{t} set2{t} set3{t}
        r sadd set2{t} 1 2 3 4
        r sadd set3{t} a b c d
        r sdiff set1{t} set2{t} set3{t}
    } {}
    """
    r.run("del", "set1{t}", "set2{t}", "set3{t}")
    r.run("sadd", "set2{t}", 1, 2, 3, 4)
    r.run("sadd", "set3{t}", "a", "b", "c", "d")
    r.run("sdiff", "set1{t}", "set2{t}", "set3{t}")


def test_sdiff_with_same_set_two_times(r: ValkeyTestClient) -> None:
    """
    test "SDIFF with same set two times" {
        r del set1
        r sadd set1 a b c 1 2 3 4 5 6
        r sdiff set1 set1
    } {}
    """
    r.run("del", "set1")
    r.run("sadd", "set1", "a", "b", "c", 1, 2, 3, 4, 5, 6)
    r.run("sdiff", "set1", "set1")


def test_sdiff_fuzzing(r: ValkeyTestClient) -> None:
    """
    test "SDIFF fuzzing" {
        for {set j 0} {$j < 100} {incr j} {
            unset -nocomplain s
            array set s {}
            set args {}
            set num_sets [expr {[randomInt 10]+1}]
            for {set i 0} {$i < $num_sets} {incr i} {
                set num_elements [randomInt 100]
                r del set_$i{t}
                lappend args set_$i{t}
                while {$num_elements} {
                    set ele [randomValue]
                    r sadd set_$i{t} $ele
                    if {$i == 0} {
                        set s($ele) x
                    } else {
                        unset -nocomplain s($ele)
                    }
                    incr num_elements -1
                }
            }
            set result [lsort [r sdiff {*}$args]]
            assert_equal $result [lsort [array names s]]
        }
    }
    """
    j = 0
    while j < 100:
        unset("-nocomplain", "s")
        array("set", "s", "")
        args = []
        num_sets = expr("[randomInt 10]+1")
        i = 0
        while i < num_sets:
            num_elements = random_int(100)
            r.run("del", "set_$i{t}")
            args.append("set_$i{t}")
            while_(
                "$num_elements",
                "                    set ele [randomValue]\n                    r sadd set_$i{t} $ele\n                    if {$i == 0} {\n                        set s($ele) x\n                    } else {\n                        unset -nocomplain s($ele)\n                    }\n                    incr num_elements -1\n                ",
            )
            i += 1
        result = sorted(r.run("sdiff", "*", args))
        assert result == sorted(array("names", "s"))
        j += 1


def test_sdiff_against_non_set_should_throw_error(r: ValkeyTestClient) -> None:
    """
    test "SDIFF against non-set should throw error" {
        # with an empty set
        r set key1{t} x
        assert_error "WRONGTYPE*" {r sdiff key1{t} noset{t}}
        # different order
        assert_error "WRONGTYPE*" {r sdiff noset{t} key1{t}}

        # with a legal set
        r del set1{t}
        r sadd set1{t} a b c
        assert_error "WRONGTYPE*" {r sdiff key1{t} set1{t}}
        # different order
        assert_error "WRONGTYPE*" {r sdiff set1{t} key1{t}}
    }
    """
    r.run("set", "key1{t}", "x")
    with pytest.raises(Exception, match="WRONGTYPE.*"):
        r.run("sdiff", "key1{t}", "noset{t}")
    with pytest.raises(Exception, match="WRONGTYPE.*"):
        r.run("sdiff", "noset{t}", "key1{t}")
    r.run("del", "set1{t}")
    r.run("sadd", "set1{t}", "a", "b", "c")
    with pytest.raises(Exception, match="WRONGTYPE.*"):
        r.run("sdiff", "key1{t}", "set1{t}")
    with pytest.raises(Exception, match="WRONGTYPE.*"):
        r.run("sdiff", "set1{t}", "key1{t}")


def test_sdiff_should_handle_non_existing_key_as_empty(r: ValkeyTestClient) -> None:
    """
    test "SDIFF should handle non existing key as empty" {
        r del set1{t} set2{t} set3{t}

        r sadd set1{t} a b c
        r sadd set2{t} b c d
        assert_equal {a} [lsort [r sdiff set1{t} set2{t} set3{t}]]
        assert_equal {} [lsort [r sdiff set3{t} set2{t} set1{t}]]
    }
    """
    r.run("del", "set1{t}", "set2{t}", "set3{t}")
    r.run("sadd", "set1{t}", "a", "b", "c")
    r.run("sadd", "set2{t}", "b", "c", "d")
    assert "a" == sorted(r.run("sdiff", "set1{t}", "set2{t}", "set3{t}"))
    assert "" == sorted(r.run("sdiff", "set3{t}", "set2{t}", "set1{t}"))


def test_sdiffstore_against_non_set_should_throw_error(r: ValkeyTestClient) -> None:
    """
    test "SDIFFSTORE against non-set should throw error" {
        r del set1{t} set2{t} set3{t} key1{t}
        r set key1{t} x

        # with en empty dstkey
        assert_error "WRONGTYPE*" {r SDIFFSTORE set3{t} key1{t} noset{t}}
        assert_equal 0 [r exists set3{t}]
        assert_error "WRONGTYPE*" {r SDIFFSTORE set3{t} noset{t} key1{t}}
        assert_equal 0 [r exists set3{t}]

        # with a legal dstkey
        r sadd set1{t} a b c
        r sadd set2{t} b c d
        r sadd set3{t} e
        assert_error "WRONGTYPE*" {r SDIFFSTORE set3{t} key1{t} set1{t} noset{t}}
        assert_equal 1 [r exists set3{t}]
        assert_equal {e} [lsort [r smembers set3{t}]]

        assert_error "WRONGTYPE*" {r SDIFFSTORE set3{t} set1{t} key1{t} set2{t}}
        assert_equal 1 [r exists set3{t}]
        assert_equal {e} [lsort [r smembers set3{t}]]
    }
    """
    r.run("del", "set1{t}", "set2{t}", "set3{t}", "key1{t}")
    r.run("set", "key1{t}", "x")
    with pytest.raises(Exception, match="WRONGTYPE.*"):
        r.run("SDIFFSTORE", "set3{t}", "key1{t}", "noset{t}")
    assert 0 == r.run("exists", "set3{t}")
    with pytest.raises(Exception, match="WRONGTYPE.*"):
        r.run("SDIFFSTORE", "set3{t}", "noset{t}", "key1{t}")
    assert 0 == r.run("exists", "set3{t}")
    r.run("sadd", "set1{t}", "a", "b", "c")
    r.run("sadd", "set2{t}", "b", "c", "d")
    r.run("sadd", "set3{t}", "e")
    with pytest.raises(Exception, match="WRONGTYPE.*"):
        r.run("SDIFFSTORE", "set3{t}", "key1{t}", "set1{t}", "noset{t}")
    assert 1 == r.run("exists", "set3{t}")
    assert "e" == sorted(r.run("smembers", "set3{t}"))
    with pytest.raises(Exception, match="WRONGTYPE.*"):
        r.run("SDIFFSTORE", "set3{t}", "set1{t}", "key1{t}", "set2{t}")
    assert 1 == r.run("exists", "set3{t}")
    assert "e" == sorted(r.run("smembers", "set3{t}"))


def test_sdiffstore_should_handle_non_existing_key_as_empty(r: ValkeyTestClient) -> None:
    """
    test "SDIFFSTORE should handle non existing key as empty" {
        r del set1{t} set2{t} set3{t}

        r set setres{t} xxx
        assert_equal 0 [r sdiffstore setres{t} foo111{t} bar222{t}]
        assert_equal 0 [r exists setres{t}]

        # with a legal dstkey, should delete dstkey
        r sadd set3{t} a b c
        assert_equal 0 [r sdiffstore set3{t} set1{t} set2{t}]
        assert_equal 0 [r exists set3{t}]

        r sadd set1{t} a b c
        assert_equal 3 [r sdiffstore set3{t} set1{t} set2{t}]
        assert_equal 1 [r exists set3{t}]
        assert_equal {a b c} [lsort [r smembers set3{t}]]

        # with a legal dstkey and empty set2, should delete the dstkey
        r sadd set3{t} a b c
        assert_equal 0 [r sdiffstore set3{t} set2{t} set1{t}]
        assert_equal 0 [r exists set3{t}]
    }
    """
    r.run("del", "set1{t}", "set2{t}", "set3{t}")
    r.run("set", "setres{t}", "xxx")
    assert 0 == r.run("sdiffstore", "setres{t}", "foo111{t}", "bar222{t}")
    assert 0 == r.run("exists", "setres{t}")
    r.run("sadd", "set3{t}", "a", "b", "c")
    assert 0 == r.run("sdiffstore", "set3{t}", "set1{t}", "set2{t}")
    assert 0 == r.run("exists", "set3{t}")
    r.run("sadd", "set1{t}", "a", "b", "c")
    assert 3 == r.run("sdiffstore", "set3{t}", "set1{t}", "set2{t}")
    assert 1 == r.run("exists", "set3{t}")
    assert "a b c" == sorted(r.run("smembers", "set3{t}"))
    r.run("sadd", "set3{t}", "a", "b", "c")
    assert 0 == r.run("sdiffstore", "set3{t}", "set2{t}", "set1{t}")
    assert 0 == r.run("exists", "set3{t}")


def test_sinter_against_non_set_should_throw_error(r: ValkeyTestClient) -> None:
    """
    test "SINTER against non-set should throw error" {
        r set key1{t} x
        assert_error "WRONGTYPE*" {r sinter key1{t} noset{t}}
        # different order
        assert_error "WRONGTYPE*" {r sinter noset{t} key1{t}}

        r sadd set1{t} a b c
        assert_error "WRONGTYPE*" {r sinter key1{t} set1{t}}
        # different order
        assert_error "WRONGTYPE*" {r sinter set1{t} key1{t}}
    }
    """
    r.run("set", "key1{t}", "x")
    with pytest.raises(Exception, match="WRONGTYPE.*"):
        r.run("sinter", "key1{t}", "noset{t}")
    with pytest.raises(Exception, match="WRONGTYPE.*"):
        r.run("sinter", "noset{t}", "key1{t}")
    r.run("sadd", "set1{t}", "a", "b", "c")
    with pytest.raises(Exception, match="WRONGTYPE.*"):
        r.run("sinter", "key1{t}", "set1{t}")
    with pytest.raises(Exception, match="WRONGTYPE.*"):
        r.run("sinter", "set1{t}", "key1{t}")


def test_sinter_should_handle_non_existing_key_as_empty(r: ValkeyTestClient) -> None:
    """
    test "SINTER should handle non existing key as empty" {
        r del set1{t} set2{t} set3{t}
        r sadd set1{t} a b c
        r sadd set2{t} b c d
        r sinter set1{t} set2{t} set3{t}
    } {}
    """
    r.run("del", "set1{t}", "set2{t}", "set3{t}")
    r.run("sadd", "set1{t}", "a", "b", "c")
    r.run("sadd", "set2{t}", "b", "c", "d")
    r.run("sinter", "set1{t}", "set2{t}", "set3{t}")


def test_sinter_with_same_integer_elements_but_different_encoding(r: ValkeyTestClient) -> None:
    """
    test "SINTER with same integer elements but different encoding" {
        r del set1{t} set2{t}
        r sadd set1{t} 1 2 3
        r sadd set2{t} 1 2 3 a
        r srem set2{t} a
        assert_encoding intset set1{t}
        assert_encoding listpack set2{t}
        lsort [r sinter set1{t} set2{t}]
    } {1 2 3}
    """
    r.run("del", "set1{t}", "set2{t}")
    r.run("sadd", "set1{t}", 1, 2, 3)
    r.run("sadd", "set2{t}", 1, 2, 3, "a")
    r.run("srem", "set2{t}", "a")
    assert_encoding("intset", "set1{t}")
    assert_encoding("listpack", "set2{t}")
    assert sorted(r.run("sinter", "set1{t}", "set2{t}")) == "1 2 3"


def test_sinterstore_against_non_set_should_throw_error(r: ValkeyTestClient) -> None:
    """
    test "SINTERSTORE against non-set should throw error" {
        r del set1{t} set2{t} set3{t} key1{t}
        r set key1{t} x

        # with en empty dstkey
        assert_error "WRONGTYPE*" {r sinterstore set3{t} key1{t} noset{t}}
        assert_equal 0 [r exists set3{t}]
        assert_error "WRONGTYPE*" {r sinterstore set3{t} noset{t} key1{t}}
        assert_equal 0 [r exists set3{t}]

        # with a legal dstkey
        r sadd set1{t} a b c
        r sadd set2{t} b c d
        r sadd set3{t} e
        assert_error "WRONGTYPE*" {r sinterstore set3{t} key1{t} set2{t} noset{t}}
        assert_equal 1 [r exists set3{t}]
        assert_equal {e} [lsort [r smembers set3{t}]]

        assert_error "WRONGTYPE*" {r sinterstore set3{t} noset{t} key1{t} set2{t}}
        assert_equal 1 [r exists set3{t}]
        assert_equal {e} [lsort [r smembers set3{t}]]
    }
    """
    r.run("del", "set1{t}", "set2{t}", "set3{t}", "key1{t}")
    r.run("set", "key1{t}", "x")
    with pytest.raises(Exception, match="WRONGTYPE.*"):
        r.run("sinterstore", "set3{t}", "key1{t}", "noset{t}")
    assert 0 == r.run("exists", "set3{t}")
    with pytest.raises(Exception, match="WRONGTYPE.*"):
        r.run("sinterstore", "set3{t}", "noset{t}", "key1{t}")
    assert 0 == r.run("exists", "set3{t}")
    r.run("sadd", "set1{t}", "a", "b", "c")
    r.run("sadd", "set2{t}", "b", "c", "d")
    r.run("sadd", "set3{t}", "e")
    with pytest.raises(Exception, match="WRONGTYPE.*"):
        r.run("sinterstore", "set3{t}", "key1{t}", "set2{t}", "noset{t}")
    assert 1 == r.run("exists", "set3{t}")
    assert "e" == sorted(r.run("smembers", "set3{t}"))
    with pytest.raises(Exception, match="WRONGTYPE.*"):
        r.run("sinterstore", "set3{t}", "noset{t}", "key1{t}", "set2{t}")
    assert 1 == r.run("exists", "set3{t}")
    assert "e" == sorted(r.run("smembers", "set3{t}"))


def test_sinterstore_against_non_existing_keys_should_delete_dstkey(r: ValkeyTestClient) -> None:
    """
    test "SINTERSTORE against non existing keys should delete dstkey" {
        r del set1{t} set2{t} set3{t}

        r set setres{t} xxx
        assert_equal 0 [r sinterstore setres{t} foo111{t} bar222{t}]
        assert_equal 0 [r exists setres{t}]

        # with a legal dstkey
        r sadd set3{t} a b c
        assert_equal 0 [r sinterstore set3{t} set1{t} set2{t}]
        assert_equal 0 [r exists set3{t}]

        r sadd set1{t} a b c
        assert_equal 0 [r sinterstore set3{t} set1{t} set2{t}]
        assert_equal 0 [r exists set3{t}]

        assert_equal 0 [r sinterstore set3{t} set2{t} set1{t}]
        assert_equal 0 [r exists set3{t}]
    }
    """
    r.run("del", "set1{t}", "set2{t}", "set3{t}")
    r.run("set", "setres{t}", "xxx")
    assert 0 == r.run("sinterstore", "setres{t}", "foo111{t}", "bar222{t}")
    assert 0 == r.run("exists", "setres{t}")
    r.run("sadd", "set3{t}", "a", "b", "c")
    assert 0 == r.run("sinterstore", "set3{t}", "set1{t}", "set2{t}")
    assert 0 == r.run("exists", "set3{t}")
    r.run("sadd", "set1{t}", "a", "b", "c")
    assert 0 == r.run("sinterstore", "set3{t}", "set1{t}", "set2{t}")
    assert 0 == r.run("exists", "set3{t}")
    assert 0 == r.run("sinterstore", "set3{t}", "set2{t}", "set1{t}")
    assert 0 == r.run("exists", "set3{t}")


def test_sunion_against_non_set_should_throw_error(r: ValkeyTestClient) -> None:
    """
    test "SUNION against non-set should throw error" {
        r set key1{t} x
        assert_error "WRONGTYPE*" {r sunion key1{t} noset{t}}
        # different order
        assert_error "WRONGTYPE*" {r sunion noset{t} key1{t}}

        r del set1{t}
        r sadd set1{t} a b c
        assert_error "WRONGTYPE*" {r sunion key1{t} set1{t}}
        # different order
        assert_error "WRONGTYPE*" {r sunion set1{t} key1{t}}
    }
    """
    r.run("set", "key1{t}", "x")
    with pytest.raises(Exception, match="WRONGTYPE.*"):
        r.run("sunion", "key1{t}", "noset{t}")
    with pytest.raises(Exception, match="WRONGTYPE.*"):
        r.run("sunion", "noset{t}", "key1{t}")
    r.run("del", "set1{t}")
    r.run("sadd", "set1{t}", "a", "b", "c")
    with pytest.raises(Exception, match="WRONGTYPE.*"):
        r.run("sunion", "key1{t}", "set1{t}")
    with pytest.raises(Exception, match="WRONGTYPE.*"):
        r.run("sunion", "set1{t}", "key1{t}")


def test_sunion_should_handle_non_existing_key_as_empty(r: ValkeyTestClient) -> None:
    """
    test "SUNION should handle non existing key as empty" {
        r del set1{t} set2{t} set3{t}

        r sadd set1{t} a b c
        r sadd set2{t} b c d
        assert_equal {a b c d} [lsort [r sunion set1{t} set2{t} set3{t}]]
    }
    """
    r.run("del", "set1{t}", "set2{t}", "set3{t}")
    r.run("sadd", "set1{t}", "a", "b", "c")
    r.run("sadd", "set2{t}", "b", "c", "d")
    assert "a b c d" == sorted(r.run("sunion", "set1{t}", "set2{t}", "set3{t}"))


def test_sunionstore_against_non_set_should_throw_error(r: ValkeyTestClient) -> None:
    """
    test "SUNIONSTORE against non-set should throw error" {
        r del set1{t} set2{t} set3{t} key1{t}
        r set key1{t} x

        # with en empty dstkey
        assert_error "WRONGTYPE*" {r sunionstore set3{t} key1{t} noset{t}}
        assert_equal 0 [r exists set3{t}]
        assert_error "WRONGTYPE*" {r sunionstore set3{t} noset{t} key1{t}}
        assert_equal 0 [r exists set3{t}]

        # with a legal dstkey
        r sadd set1{t} a b c
        r sadd set2{t} b c d
        r sadd set3{t} e
        assert_error "WRONGTYPE*" {r sunionstore set3{t} key1{t} key2{t} noset{t}}
        assert_equal 1 [r exists set3{t}]
        assert_equal {e} [lsort [r smembers set3{t}]]

        assert_error "WRONGTYPE*" {r sunionstore set3{t} noset{t} key1{t} key2{t}}
        assert_equal 1 [r exists set3{t}]
        assert_equal {e} [lsort [r smembers set3{t}]]
    }
    """
    r.run("del", "set1{t}", "set2{t}", "set3{t}", "key1{t}")
    r.run("set", "key1{t}", "x")
    with pytest.raises(Exception, match="WRONGTYPE.*"):
        r.run("sunionstore", "set3{t}", "key1{t}", "noset{t}")
    assert 0 == r.run("exists", "set3{t}")
    with pytest.raises(Exception, match="WRONGTYPE.*"):
        r.run("sunionstore", "set3{t}", "noset{t}", "key1{t}")
    assert 0 == r.run("exists", "set3{t}")
    r.run("sadd", "set1{t}", "a", "b", "c")
    r.run("sadd", "set2{t}", "b", "c", "d")
    r.run("sadd", "set3{t}", "e")
    with pytest.raises(Exception, match="WRONGTYPE.*"):
        r.run("sunionstore", "set3{t}", "key1{t}", "key2{t}", "noset{t}")
    assert 1 == r.run("exists", "set3{t}")
    assert "e" == sorted(r.run("smembers", "set3{t}"))
    with pytest.raises(Exception, match="WRONGTYPE.*"):
        r.run("sunionstore", "set3{t}", "noset{t}", "key1{t}", "key2{t}")
    assert 1 == r.run("exists", "set3{t}")
    assert "e" == sorted(r.run("smembers", "set3{t}"))


def test_sunionstore_should_handle_non_existing_key_as_empty(r: ValkeyTestClient) -> None:
    """
    test "SUNIONSTORE should handle non existing key as empty" {
        r del set1{t} set2{t} set3{t}

        r set setres{t} xxx
        assert_equal 0 [r sunionstore setres{t} foo111{t} bar222{t}]
        assert_equal 0 [r exists setres{t}]

        # set1 set2 both empty, should delete the dstkey
        r sadd set3{t} a b c
        assert_equal 0 [r sunionstore set3{t} set1{t} set2{t}]
        assert_equal 0 [r exists set3{t}]

        r sadd set1{t} a b c
        r sadd set3{t} e f
        assert_equal 3 [r sunionstore set3{t} set1{t} set2{t}]
        assert_equal 1 [r exists set3{t}]
        assert_equal {a b c} [lsort [r smembers set3{t}]]

        r sadd set3{t} d
        assert_equal 3 [r sunionstore set3{t} set2{t} set1{t}]
        assert_equal 1 [r exists set3{t}]
        assert_equal {a b c} [lsort [r smembers set3{t}]]
    }
    """
    r.run("del", "set1{t}", "set2{t}", "set3{t}")
    r.run("set", "setres{t}", "xxx")
    assert 0 == r.run("sunionstore", "setres{t}", "foo111{t}", "bar222{t}")
    assert 0 == r.run("exists", "setres{t}")
    r.run("sadd", "set3{t}", "a", "b", "c")
    assert 0 == r.run("sunionstore", "set3{t}", "set1{t}", "set2{t}")
    assert 0 == r.run("exists", "set3{t}")
    r.run("sadd", "set1{t}", "a", "b", "c")
    r.run("sadd", "set3{t}", "e", "f")
    assert 3 == r.run("sunionstore", "set3{t}", "set1{t}", "set2{t}")
    assert 1 == r.run("exists", "set3{t}")
    assert "a b c" == sorted(r.run("smembers", "set3{t}"))
    r.run("sadd", "set3{t}", "d")
    assert 3 == r.run("sunionstore", "set3{t}", "set2{t}", "set1{t}")
    assert 1 == r.run("exists", "set3{t}")
    assert "a b c" == sorted(r.run("smembers", "set3{t}"))


def test_sunionstore_against_non_existing_keys_should_delete_dstkey(r: ValkeyTestClient) -> None:
    """
    test "SUNIONSTORE against non existing keys should delete dstkey" {
        r set setres{t} xxx
        assert_equal 0 [r sunionstore setres{t} foo111{t} bar222{t}]
        assert_equal 0 [r exists setres{t}]
    }
    """
    r.run("set", "setres{t}", "xxx")
    assert 0 == r.run("sunionstore", "setres{t}", "foo111{t}", "bar222{t}")
    assert 0 == r.run("exists", "setres{t}")


@pytest.mark.parametrize(["type", "contents"], [("listpack", "a b c"), ("intset", "1 2 3")])
def test_spop_basics_type(r: ValkeyTestClient, type: str, contents: str) -> None:
    """
    test "SPOP basics - $type" {
        create_set myset $contents
        assert_encoding $type myset
        assert_equal $contents [lsort [list [r spop myset] [r spop myset] [r spop myset]]]
        assert_equal 0 [r scard myset]
    }
    """
    create_set("myset", contents)
    assert_encoding(type, "myset")
    assert contents == sorted([r.run("spop", "myset"), r.run("spop", "myset"), r.run("spop", "myset")])
    assert 0 == r.run("scard", "myset")


@pytest.mark.parametrize(["type", "contents"], [("listpack", "a b c"), ("intset", "1 2 3")])
def test_spop_with_count_1_type(r: ValkeyTestClient, type: str, contents: str) -> None:
    """
    test "SPOP with <count>=1 - $type" {
        create_set myset $contents
        assert_encoding $type myset
        assert_equal $contents [lsort [list [r spop myset 1] [r spop myset 1] [r spop myset 1]]]
        assert_equal 0 [r scard myset]
    }
    """
    create_set("myset", contents)
    assert_encoding(type, "myset")
    assert contents == sorted([r.run("spop", "myset", 1), r.run("spop", "myset", 1), r.run("spop", "myset", 1)])
    assert 0 == r.run("scard", "myset")


@pytest.mark.parametrize(["type", "contents"], [("listpack", "a b c"), ("intset", "1 2 3")])
def test_srandmember_type(r: ValkeyTestClient, type: str, contents: str) -> None:
    """
    test "SRANDMEMBER - $type" {
        create_set myset $contents
        unset -nocomplain myset
        array set myset {}
        for {set i 0} {$i < 100} {incr i} {
            set myset([r srandmember myset]) 1
        }
        assert_equal $contents [lsort [array names myset]]
    }
    """
    create_set("myset", contents)
    unset("-nocomplain", "myset")
    array("set", "myset", "")
    i = 0
    while i < 100:
        set_("myset([r", "srandmember", "myset])", 1)
        i += 1
    assert contents == sorted(array("names", "myset"))


def test_spop_integer_from_listpack_set(r: ValkeyTestClient) -> None:
    """
    test "SPOP integer from listpack set" {
        create_set myset {a 1 2 3 4 5 6 7}
        assert_encoding listpack myset
        set a [r spop myset]
        set b [r spop myset]
        assert {[string is digit $a] || [string is digit $b]}
    }
    """
    create_set("myset", "a 1 2 3 4 5 6 7")
    assert_encoding("listpack", "myset")
    a = r.run("spop", "myset")
    b = r.run("spop", "myset")
    assert string("is", "digit", a) or string("is", "digit", b)


@pytest.mark.parametrize(
    ["type", "contents"],
    [
        ("listpack", "a b c d e f g h i j k l m n o p q r s t u v w x y z"),
        ("intset", "1 10 11 12 13 14 15 16 17 18 19 2 20 21 22 23 24 25 26 3 4 5 6 7 8 9"),
        ("hashtable", "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 b c d e f g h i j k l m n o p q r s t u v w x y z"),
    ],
)
def test_spop_with_count_type(r: ValkeyTestClient, type: str, contents: str) -> None:
    """
    test "SPOP with <count> - $type" {
        create_set myset $contents
        assert_encoding $type myset
        assert_equal $contents [lsort [concat [r spop myset 11] [r spop myset 9] [r spop myset 0] [r spop myset 4] [r spop myset 1] [r spop myset 0] [r spop myset 1] [r spop myset 0]]]
        assert_equal 0 [r scard myset]
    }
    """
    create_set("myset", contents)
    assert_encoding(type, "myset")
    assert contents == sorted(
        concat(
            r.run("spop", "myset", 11),
            r.run("spop", "myset", 9),
            r.run("spop", "myset", 0),
            r.run("spop", "myset", 4),
            r.run("spop", "myset", 1),
            r.run("spop", "myset", 0),
            r.run("spop", "myset", 1),
            r.run("spop", "myset", 0),
        )
    )
    assert 0 == r.run("scard", "myset")


def test_spop_using_integers_testing_knuth_s_and_floyd_s_algorithm(r: ValkeyTestClient) -> None:
    """
    test "SPOP using integers, testing Knuth's and Floyd's algorithm" {
        create_set myset {1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20}
        assert_encoding intset myset
        assert_equal 20 [r scard myset]
        r spop myset 1
        assert_equal 19 [r scard myset]
        r spop myset 2
        assert_equal 17 [r scard myset]
        r spop myset 3
        assert_equal 14 [r scard myset]
        r spop myset 10
        assert_equal 4 [r scard myset]
        r spop myset 10
        assert_equal 0 [r scard myset]
        r spop myset 1
        assert_equal 0 [r scard myset]
    } {}
    """
    create_set("myset", "1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20")
    assert_encoding("intset", "myset")
    assert 20 == r.run("scard", "myset")
    r.run("spop", "myset", 1)
    assert 19 == r.run("scard", "myset")
    r.run("spop", "myset", 2)
    assert 17 == r.run("scard", "myset")
    r.run("spop", "myset", 3)
    assert 14 == r.run("scard", "myset")
    r.run("spop", "myset", 10)
    assert 4 == r.run("scard", "myset")
    r.run("spop", "myset", 10)
    assert 0 == r.run("scard", "myset")
    r.run("spop", "myset", 1)
    assert 0 == r.run("scard", "myset")


def test_spop_using_integers_with_knuth_s_algorithm(r: ValkeyTestClient) -> None:
    """
    test "SPOP using integers with Knuth's algorithm" {
        r spop nonexisting_key 100
    } {}
    """
    r.run("spop", "nonexisting_key", 100)


@pytest.mark.parametrize(
    ["type", "content"],
    [
        ("intset", "1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20"),
        ("listpack", "a 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20"),
    ],
)
def test_spop_new_implementation_code_path_1_type(r: ValkeyTestClient, type: str, content: str) -> None:
    """
    test "SPOP new implementation: code path #1 $type" {
        create_set myset $content
        assert_encoding $type myset
        set res [r spop myset 30]
        assert {[lsort $content] eq [lsort $res]}
        assert_equal {0} [r exists myset]
    }
    """
    create_set("myset", content)
    assert_encoding(type, "myset")
    res = r.run("spop", "myset", 30)
    assert sorted(content) == sorted(res)
    assert "0" == r.run("exists", "myset")


@pytest.mark.parametrize(
    ["type", "content"],
    [
        ("intset", "1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20"),
        ("listpack", "a 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20"),
    ],
)
def test_spop_new_implementation_code_path_2_type(r: ValkeyTestClient, type: str, content: str) -> None:
    """
    test "SPOP new implementation: code path #2 $type" {
        create_set myset $content
        assert_encoding $type myset
        set res [r spop myset 2]
        assert {[llength $res] == 2}
        assert {[r scard myset] == 18}
        set union [concat [r smembers myset] $res]
        assert {[lsort $union] eq [lsort $content]}
    }
    """
    create_set("myset", content)
    assert_encoding(type, "myset")
    res = r.run("spop", "myset", 2)
    assert len(res) == 2
    assert r.run("scard", "myset") == 18
    union = concat(r.run("smembers", "myset"), res)
    assert sorted(union) == sorted(content)


@pytest.mark.parametrize(
    ["type", "content"],
    [
        ("intset", "1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20"),
        ("listpack", "a 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20"),
    ],
)
def test_spop_new_implementation_code_path_3_type(r: ValkeyTestClient, type: str, content: str) -> None:
    """
    test "SPOP new implementation: code path #3 $type" {
        create_set myset $content
        assert_encoding $type myset
        set res [r spop myset 18]
        assert {[llength $res] == 18}
        assert {[r scard myset] == 2}
        set union [concat [r smembers myset] $res]
        assert {[lsort $union] eq [lsort $content]}
    }
    """
    create_set("myset", content)
    assert_encoding(type, "myset")
    res = r.run("spop", "myset", 18)
    assert len(res) == 18
    assert r.run("scard", "myset") == 2
    union = concat(r.run("smembers", "myset"), res)
    assert sorted(union) == sorted(content)


def test_spop_new_implementation_code_path_1_propagate_as_del_or_unlink(r: ValkeyTestClient) -> None:
    """
    test "SPOP new implementation: code path #1 propagate as DEL or UNLINK" {
        r del myset1{t} myset2{t}
        r sadd myset1{t} 1 2 3 4 5
        r sadd myset2{t} 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30 31 32 33 34 35 36 37 38 39 40 41 42 43 44 45 46 47 48 49 50 51 52 53 54 55 56 57 58 59 60 61 62 63 64 65

        set repl [attach_to_replication_stream]

        r config set lazyfree-lazy-server-del no
        r spop myset1{t} [r scard myset1{t}]
        r config set lazyfree-lazy-server-del yes
        r spop myset2{t} [r scard myset2{t}]
        assert_equal {0} [r exists myset1{t} myset2{t}]

        # Verify the propagate of DEL and UNLINK.
        assert_replication_stream $repl {
            {select *}
            {del myset1{t}}
            {unlink myset2{t}}
        }

        close_replication_stream $repl
    } {} {needs:repl}
    """
    r.run("del", "myset1{t}", "myset2{t}")
    r.run("sadd", "myset1{t}", 1, 2, 3, 4, 5)
    r.run(
        "sadd",
        "myset2{t}",
        1,
        2,
        3,
        4,
        5,
        6,
        7,
        8,
        9,
        10,
        11,
        12,
        13,
        14,
        15,
        16,
        17,
        18,
        19,
        20,
        21,
        22,
        23,
        24,
        25,
        26,
        27,
        28,
        29,
        30,
        31,
        32,
        33,
        34,
        35,
        36,
        37,
        38,
        39,
        40,
        41,
        42,
        43,
        44,
        45,
        46,
        47,
        48,
        49,
        50,
        51,
        52,
        53,
        54,
        55,
        56,
        57,
        58,
        59,
        60,
        61,
        62,
        63,
        64,
        65,
    )
    repl = attach_to_replication_stream()
    r.run("config", "set", "lazyfree-lazy-server-del", "no")
    r.run("spop", "myset1{t}", r.run("scard", "myset1{t}"))
    r.run("config", "set", "lazyfree-lazy-server-del", "yes")
    r.run("spop", "myset2{t}", r.run("scard", "myset2{t}"))
    assert "0" == r.run("exists", "myset1{t}", "myset2{t}")
    assert_replication_stream(
        repl, "            {select *}\n            {del myset1{t}}\n            {unlink myset2{t}}\n        "
    )
    close_replication_stream(repl)


def test_srandmember_count_of_0_is_handled_correctly(r: ValkeyTestClient) -> None:
    """
    test "SRANDMEMBER count of 0 is handled correctly" {
        r srandmember myset 0
    } {}
    """
    r.run("srandmember", "myset", 0)


def test_srandmember_with_count_against_non_existing_key(r: ValkeyTestClient) -> None:
    """
    test "SRANDMEMBER with <count> against non existing key" {
        r srandmember nonexisting_key 100
    } {}
    """
    r.run("srandmember", "nonexisting_key", 100)


def test_srandmember_count_overflow(r: ValkeyTestClient) -> None:
    """
    test "SRANDMEMBER count overflow" {
        r sadd myset a
        assert_error {*value is out of range*} {r srandmember myset -9223372036854775808}
    } {}
    """
    r.run("sadd", "myset", "a")
    with pytest.raises(Exception, match=".*value\\ is\\ out\\ of\\ range.*"):
        r.run("srandmember", "myset", -9223372036854775808)


def test_srandmember_count_of_0_is_handled_correctly_emptyarray(r: ValkeyTestClient) -> None:
    """
    test "SRANDMEMBER count of 0 is handled correctly - emptyarray" {
        r srandmember myset 0
    } {*0}
    """
    r.run("readraw", 1)
    assert fnmatch(str(r.run("srandmember", "myset", 0)), "*0")


def test_srandmember_with_count_against_non_existing_key_emptyarray(r: ValkeyTestClient) -> None:
    """
    test "SRANDMEMBER with <count> against non existing key - emptyarray" {
        r srandmember nonexisting_key 100
    } {*0}
    """
    r.run("readraw", 1)
    assert fnmatch(str(r.run("srandmember", "nonexisting_key", 100)), "*0")


"""
r readraw 0
"""


@pytest.mark.parametrize(
    ["type", "contents"],
    [
        (
            "listpack",
            """            1 5 10 50 125 50000 33959417 4775547 65434162
            12098459 427716 483706 2726473884 72615637475
            MARY PATRICIA LINDA BARBARA ELIZABETH JENNIFER MARIA
            SUSAN MARGARET DOROTHY LISA NANCY KAREN BETTY HELEN
            SANDRA DONNA CAROL RUTH SHARON MICHELLE LAURA SARAH
            KIMBERLY DEBORAH JESSICA SHIRLEY CYNTHIA ANGELA MELISSA
            BRENDA AMY ANNA REBECCA VIRGINIA KATHLEEN
        """,
        ),
        (
            "intset",
            """            0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19
            20 21 22 23 24 25 26 27 28 29
            30 31 32 33 34 35 36 37 38 39
            40 41 42 43 44 45 46 47 48 49
        """,
        ),
        (
            "hashtable",
            """            ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789
            1 5 10 50 125 50000 33959417 4775547 65434162
            12098459 427716 483706 2726473884 72615637475
            MARY PATRICIA LINDA BARBARA ELIZABETH JENNIFER MARIA
            SUSAN MARGARET DOROTHY LISA NANCY KAREN BETTY HELEN
            SANDRA DONNA CAROL RUTH SHARON MICHELLE LAURA SARAH
            KIMBERLY DEBORAH JESSICA SHIRLEY CYNTHIA ANGELA MELISSA
            BRENDA AMY ANNA REBECCA VIRGINIA
        """,
        ),
    ],
)
def test_srandmember_with_count_type(r: ValkeyTestClient, type: str, contents: str) -> None:
    """
    test "SRANDMEMBER with <count> - $type" {
        create_set myset $contents
        assert_encoding $type myset
        unset -nocomplain myset
        array set myset {}
        foreach ele [r smembers myset] {
            set myset($ele) 1
        }
        assert_equal [lsort $contents] [lsort [array names myset]]

        # Make sure that a count of 0 is handled correctly.
        assert_equal [r srandmember myset 0] {}

        # We'll stress different parts of the code, see the implementation
        # of SRANDMEMBER for more information, but basically there are
        # four different code paths.
        #
        # PATH 1: Use negative count.
        #
        # 1) Check that it returns repeated elements.
        set res [r srandmember myset -100]
        assert_equal [llength $res] 100

        # 2) Check that all the elements actually belong to the
        # original set.
        foreach ele $res {
            assert {[info exists myset($ele)]}
        }

        # 3) Check that eventually all the elements are returned.
        unset -nocomplain auxset
        set iterations 1000
        while {$iterations != 0} {
            incr iterations -1
            set res [r srandmember myset -10]
            foreach ele $res {
                set auxset($ele) 1
            }
            if {[lsort [array names myset]] eq
                [lsort [array names auxset]]} {
                break;
            }
        }
        assert {$iterations != 0}

        # PATH 2: positive count (unique behavior) with requested size
        # equal or greater than set size.
        foreach size {50 100} {
            set res [r srandmember myset $size]
            assert_equal [llength $res] 50
            assert_equal [lsort $res] [lsort [array names myset]]
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

        foreach size {45 5} {
            set res [r srandmember myset $size]
            assert_equal [llength $res] $size

            # 1) Check that all the elements actually belong to the
            # original set.
            foreach ele $res {
                assert {[info exists myset($ele)]}
            }

            # 2) Check that eventually all the elements are returned.
            unset -nocomplain auxset
            set iterations 1000
            while {$iterations != 0} {
                incr iterations -1
                set res [r srandmember myset $size]
                foreach ele $res {
                    set auxset($ele) 1
                }
                if {[lsort [array names myset]] eq
                    [lsort [array names auxset]]} {
                    break;
                }
            }
            assert {$iterations != 0}
        }
    }
    """
    create_set("myset", contents)
    assert_encoding(type, "myset")
    unset("-nocomplain", "myset")
    array("set", "myset", "")
    foreach("ele", r.run("smembers", "myset"), "                set myset($ele) 1\n            ")
    assert sorted(contents) == sorted(array("names", "myset"))
    assert r.run("srandmember", "myset", 0) == ""
    res = r.run("srandmember", "myset", -100)
    assert len(res) == 100
    foreach("ele", res, "                assert {[info exists myset($ele)]}\n            ")
    unset("-nocomplain", "auxset")
    iterations = 1000
    while_(
        "$iterations != 0",
        "                incr iterations -1\n                set res [r srandmember myset -10]\n                foreach ele $res {\n                    set auxset($ele) 1\n                }\n                if {[lsort [array names myset]] eq\n                    [lsort [array names auxset]]} {\n                    break;\n                }\n            ",
    )
    assert iterations != 0
    foreach(
        "size",
        "50 100",
        "                set res [r srandmember myset $size]\n                assert_equal [llength $res] 50\n                assert_equal [lsort $res] [lsort [array names myset]]\n            ",
    )
    foreach(
        "size",
        "45 5",
        "                set res [r srandmember myset $size]\n                assert_equal [llength $res] $size\n\n                # 1) Check that all the elements actually belong to the\n                # original set.\n                foreach ele $res {\n                    assert {[info exists myset($ele)]}\n                }\n\n                # 2) Check that eventually all the elements are returned.\n                unset -nocomplain auxset\n                set iterations 1000\n                while {$iterations != 0} {\n                    incr iterations -1\n                    set res [r srandmember myset $size]\n                    foreach ele $res {\n                        set auxset($ele) 1\n                    }\n                    if {[lsort [array names myset]] eq\n                        [lsort [array names auxset]]} {\n                        break;\n                    }\n                }\n                assert {$iterations != 0}\n            ",
    )


@pytest.mark.parametrize(
    ["type", "contents"],
    [
        (
            "listpack",
            """            1 5 10 50 125
            MARY PATRICIA LINDA BARBARA ELIZABETH
        """,
        ),
        (
            "intset",
            """            0 1 2 3 4 5 6 7 8 9
        """,
        ),
        (
            "hashtable",
            """            ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789
            1 5 10 50 125
            MARY PATRICIA LINDA BARBARA
        """,
        ),
    ],
)
def test_srandmember_histogram_distribution_type(r: ValkeyTestClient, type: str, contents: str) -> None:
    """
    test "SRANDMEMBER histogram distribution - $type" {
        create_set myset $contents
        assert_encoding $type myset
        unset -nocomplain myset
        array set myset {}
        foreach ele [r smembers myset] {
            set myset($ele) 1
        }

        # Use negative count (PATH 1).
        # df = 9, 40 means 0.00001 probability
        set res [r srandmember myset -1000]
        assert_lessthan [chi_square_value $res] 40

        # Use positive count (both PATH 3 and PATH 4).
        foreach size {8 2} {
            unset -nocomplain allkey
            set iterations [expr {1000 / $size}]
            while {$iterations != 0} {
                incr iterations -1
                set res [r srandmember myset $size]
                foreach ele $res {
                    lappend allkey $ele
                }
            }
            # df = 9, 40 means 0.00001 probability
            assert_lessthan [chi_square_value $allkey] 40
        }
    }
    """
    create_set("myset", contents)
    assert_encoding(type, "myset")
    unset("-nocomplain", "myset")
    array("set", "myset", "")
    foreach("ele", r.run("smembers", "myset"), "                set myset($ele) 1\n            ")
    res = r.run("srandmember", "myset", -1000)
    assert chi_square_value(res) < 40
    foreach(
        "size",
        "8 2",
        "                unset -nocomplain allkey\n                set iterations [expr {1000 / $size}]\n                while {$iterations != 0} {\n                    incr iterations -1\n                    set res [r srandmember myset $size]\n                    foreach ele $res {\n                        lappend allkey $ele\n                    }\n                }\n                # df = 9, 40 means 0.00001 probability\n                assert_lessthan [chi_square_value $allkey] 40\n            ",
    )


def test_smove_basics_from_regular_set_to_intset(r: ValkeyTestClient) -> None:
    """
    test "SMOVE basics - from regular set to intset" {
        # move a non-integer element to an intset should convert encoding
        setup_move
        assert_equal 1 [r smove myset1{t} myset2{t} a]
        assert_equal {1 b} [lsort [r smembers myset1{t}]]
        assert_equal {2 3 4 a} [lsort [r smembers myset2{t}]]
        assert_encoding listpack myset2{t}

        # move an integer element should not convert the encoding
        setup_move
        assert_equal 1 [r smove myset1{t} myset2{t} 1]
        assert_equal {a b} [lsort [r smembers myset1{t}]]
        assert_equal {1 2 3 4} [lsort [r smembers myset2{t}]]
        assert_encoding intset myset2{t}
    }
    """
    proc(
        "is_rehashing",
        "myset",
        "        set htstats [r debug HTSTATS-KEY $myset]\n        return [string match {*rehashing target*} $htstats]\n    ",
    )
    proc(
        "rem_hash_set_top_N",
        "myset n",
        "        set cursor 0\n        set members {}\n        set enough 0\n        while 1 {\n            set res [r sscan $myset $cursor]\n            set cursor [lindex $res 0]\n            set k [lindex $res 1]\n            foreach m $k {\n                lappend members $m\n                if {[llength $members] >= $n} {\n                    set enough 1\n                    break\n                }\n            }\n            if {$enough || $cursor == 0} {\n                break\n            }\n        }\n        r srem $myset {*}$members\n    ",
    )
    proc(
        "setup_move",
        "",
        "        r del myset3{t} myset4{t}\n        create_set myset1{t} {1 a b}\n        create_set myset2{t} {2 3 4}\n        assert_encoding listpack myset1{t}\n        assert_encoding intset myset2{t}\n    ",
    )
    setup_move()
    assert 1 == r.run("smove", "myset1{t}", "myset2{t}", "a")
    assert "1 b" == sorted(r.run("smembers", "myset1{t}"))
    assert "2 3 4 a" == sorted(r.run("smembers", "myset2{t}"))
    assert_encoding("listpack", "myset2{t}")
    setup_move()
    assert 1 == r.run("smove", "myset1{t}", "myset2{t}", 1)
    assert "a b" == sorted(r.run("smembers", "myset1{t}"))
    assert "1 2 3 4" == sorted(r.run("smembers", "myset2{t}"))
    assert_encoding("intset", "myset2{t}")


def test_smove_basics_from_intset_to_regular_set(r: ValkeyTestClient) -> None:
    """
    test "SMOVE basics - from intset to regular set" {
        setup_move
        assert_equal 1 [r smove myset2{t} myset1{t} 2]
        assert_equal {1 2 a b} [lsort [r smembers myset1{t}]]
        assert_equal {3 4} [lsort [r smembers myset2{t}]]
    }
    """
    proc(
        "is_rehashing",
        "myset",
        "        set htstats [r debug HTSTATS-KEY $myset]\n        return [string match {*rehashing target*} $htstats]\n    ",
    )
    proc(
        "rem_hash_set_top_N",
        "myset n",
        "        set cursor 0\n        set members {}\n        set enough 0\n        while 1 {\n            set res [r sscan $myset $cursor]\n            set cursor [lindex $res 0]\n            set k [lindex $res 1]\n            foreach m $k {\n                lappend members $m\n                if {[llength $members] >= $n} {\n                    set enough 1\n                    break\n                }\n            }\n            if {$enough || $cursor == 0} {\n                break\n            }\n        }\n        r srem $myset {*}$members\n    ",
    )
    proc(
        "setup_move",
        "",
        "        r del myset3{t} myset4{t}\n        create_set myset1{t} {1 a b}\n        create_set myset2{t} {2 3 4}\n        assert_encoding listpack myset1{t}\n        assert_encoding intset myset2{t}\n    ",
    )
    setup_move()
    assert 1 == r.run("smove", "myset2{t}", "myset1{t}", 2)
    assert "1 2 a b" == sorted(r.run("smembers", "myset1{t}"))
    assert "3 4" == sorted(r.run("smembers", "myset2{t}"))


def test_smove_non_existing_key(r: ValkeyTestClient) -> None:
    """
    test "SMOVE non existing key" {
        setup_move
        assert_equal 0 [r smove myset1{t} myset2{t} foo]
        assert_equal 0 [r smove myset1{t} myset1{t} foo]
        assert_equal {1 a b} [lsort [r smembers myset1{t}]]
        assert_equal {2 3 4} [lsort [r smembers myset2{t}]]
    }
    """
    proc(
        "is_rehashing",
        "myset",
        "        set htstats [r debug HTSTATS-KEY $myset]\n        return [string match {*rehashing target*} $htstats]\n    ",
    )
    proc(
        "rem_hash_set_top_N",
        "myset n",
        "        set cursor 0\n        set members {}\n        set enough 0\n        while 1 {\n            set res [r sscan $myset $cursor]\n            set cursor [lindex $res 0]\n            set k [lindex $res 1]\n            foreach m $k {\n                lappend members $m\n                if {[llength $members] >= $n} {\n                    set enough 1\n                    break\n                }\n            }\n            if {$enough || $cursor == 0} {\n                break\n            }\n        }\n        r srem $myset {*}$members\n    ",
    )
    proc(
        "setup_move",
        "",
        "        r del myset3{t} myset4{t}\n        create_set myset1{t} {1 a b}\n        create_set myset2{t} {2 3 4}\n        assert_encoding listpack myset1{t}\n        assert_encoding intset myset2{t}\n    ",
    )
    setup_move()
    assert 0 == r.run("smove", "myset1{t}", "myset2{t}", "foo")
    assert 0 == r.run("smove", "myset1{t}", "myset1{t}", "foo")
    assert "1 a b" == sorted(r.run("smembers", "myset1{t}"))
    assert "2 3 4" == sorted(r.run("smembers", "myset2{t}"))


def test_smove_non_existing_src_set(r: ValkeyTestClient) -> None:
    """
    test "SMOVE non existing src set" {
        setup_move
        assert_equal 0 [r smove noset{t} myset2{t} foo]
        assert_equal {2 3 4} [lsort [r smembers myset2{t}]]
    }
    """
    proc(
        "is_rehashing",
        "myset",
        "        set htstats [r debug HTSTATS-KEY $myset]\n        return [string match {*rehashing target*} $htstats]\n    ",
    )
    proc(
        "rem_hash_set_top_N",
        "myset n",
        "        set cursor 0\n        set members {}\n        set enough 0\n        while 1 {\n            set res [r sscan $myset $cursor]\n            set cursor [lindex $res 0]\n            set k [lindex $res 1]\n            foreach m $k {\n                lappend members $m\n                if {[llength $members] >= $n} {\n                    set enough 1\n                    break\n                }\n            }\n            if {$enough || $cursor == 0} {\n                break\n            }\n        }\n        r srem $myset {*}$members\n    ",
    )
    proc(
        "setup_move",
        "",
        "        r del myset3{t} myset4{t}\n        create_set myset1{t} {1 a b}\n        create_set myset2{t} {2 3 4}\n        assert_encoding listpack myset1{t}\n        assert_encoding intset myset2{t}\n    ",
    )
    setup_move()
    assert 0 == r.run("smove", "noset{t}", "myset2{t}", "foo")
    assert "2 3 4" == sorted(r.run("smembers", "myset2{t}"))


def test_smove_from_regular_set_to_non_existing_destination_set(r: ValkeyTestClient) -> None:
    """
    test "SMOVE from regular set to non existing destination set" {
        setup_move
        assert_equal 1 [r smove myset1{t} myset3{t} a]
        assert_equal {1 b} [lsort [r smembers myset1{t}]]
        assert_equal {a} [lsort [r smembers myset3{t}]]
        assert_encoding listpack myset3{t}
    }
    """
    proc(
        "is_rehashing",
        "myset",
        "        set htstats [r debug HTSTATS-KEY $myset]\n        return [string match {*rehashing target*} $htstats]\n    ",
    )
    proc(
        "rem_hash_set_top_N",
        "myset n",
        "        set cursor 0\n        set members {}\n        set enough 0\n        while 1 {\n            set res [r sscan $myset $cursor]\n            set cursor [lindex $res 0]\n            set k [lindex $res 1]\n            foreach m $k {\n                lappend members $m\n                if {[llength $members] >= $n} {\n                    set enough 1\n                    break\n                }\n            }\n            if {$enough || $cursor == 0} {\n                break\n            }\n        }\n        r srem $myset {*}$members\n    ",
    )
    proc(
        "setup_move",
        "",
        "        r del myset3{t} myset4{t}\n        create_set myset1{t} {1 a b}\n        create_set myset2{t} {2 3 4}\n        assert_encoding listpack myset1{t}\n        assert_encoding intset myset2{t}\n    ",
    )
    setup_move()
    assert 1 == r.run("smove", "myset1{t}", "myset3{t}", "a")
    assert "1 b" == sorted(r.run("smembers", "myset1{t}"))
    assert "a" == sorted(r.run("smembers", "myset3{t}"))
    assert_encoding("listpack", "myset3{t}")


def test_smove_from_intset_to_non_existing_destination_set(r: ValkeyTestClient) -> None:
    """
    test "SMOVE from intset to non existing destination set" {
        setup_move
        assert_equal 1 [r smove myset2{t} myset3{t} 2]
        assert_equal {3 4} [lsort [r smembers myset2{t}]]
        assert_equal {2} [lsort [r smembers myset3{t}]]
        assert_encoding intset myset3{t}
    }
    """
    proc(
        "is_rehashing",
        "myset",
        "        set htstats [r debug HTSTATS-KEY $myset]\n        return [string match {*rehashing target*} $htstats]\n    ",
    )
    proc(
        "rem_hash_set_top_N",
        "myset n",
        "        set cursor 0\n        set members {}\n        set enough 0\n        while 1 {\n            set res [r sscan $myset $cursor]\n            set cursor [lindex $res 0]\n            set k [lindex $res 1]\n            foreach m $k {\n                lappend members $m\n                if {[llength $members] >= $n} {\n                    set enough 1\n                    break\n                }\n            }\n            if {$enough || $cursor == 0} {\n                break\n            }\n        }\n        r srem $myset {*}$members\n    ",
    )
    proc(
        "setup_move",
        "",
        "        r del myset3{t} myset4{t}\n        create_set myset1{t} {1 a b}\n        create_set myset2{t} {2 3 4}\n        assert_encoding listpack myset1{t}\n        assert_encoding intset myset2{t}\n    ",
    )
    setup_move()
    assert 1 == r.run("smove", "myset2{t}", "myset3{t}", 2)
    assert "3 4" == sorted(r.run("smembers", "myset2{t}"))
    assert "2" == sorted(r.run("smembers", "myset3{t}"))
    assert_encoding("intset", "myset3{t}")


def test_smove_wrong_src_key_type(r: ValkeyTestClient) -> None:
    """
    test "SMOVE wrong src key type" {
        r set x{t} 10
        assert_error "WRONGTYPE*" {r smove x{t} myset2{t} foo}
    }
    """
    proc(
        "is_rehashing",
        "myset",
        "        set htstats [r debug HTSTATS-KEY $myset]\n        return [string match {*rehashing target*} $htstats]\n    ",
    )
    proc(
        "rem_hash_set_top_N",
        "myset n",
        "        set cursor 0\n        set members {}\n        set enough 0\n        while 1 {\n            set res [r sscan $myset $cursor]\n            set cursor [lindex $res 0]\n            set k [lindex $res 1]\n            foreach m $k {\n                lappend members $m\n                if {[llength $members] >= $n} {\n                    set enough 1\n                    break\n                }\n            }\n            if {$enough || $cursor == 0} {\n                break\n            }\n        }\n        r srem $myset {*}$members\n    ",
    )
    proc(
        "setup_move",
        "",
        "        r del myset3{t} myset4{t}\n        create_set myset1{t} {1 a b}\n        create_set myset2{t} {2 3 4}\n        assert_encoding listpack myset1{t}\n        assert_encoding intset myset2{t}\n    ",
    )
    r.run("set", "x{t}", 10)
    with pytest.raises(Exception, match="WRONGTYPE.*"):
        r.run("smove", "x{t}", "myset2{t}", "foo")


def test_smove_wrong_dst_key_type(r: ValkeyTestClient) -> None:
    """
    test "SMOVE wrong dst key type" {
        r set x{t} 10
        assert_error "WRONGTYPE*" {r smove myset2{t} x{t} foo}
    }
    """
    proc(
        "is_rehashing",
        "myset",
        "        set htstats [r debug HTSTATS-KEY $myset]\n        return [string match {*rehashing target*} $htstats]\n    ",
    )
    proc(
        "rem_hash_set_top_N",
        "myset n",
        "        set cursor 0\n        set members {}\n        set enough 0\n        while 1 {\n            set res [r sscan $myset $cursor]\n            set cursor [lindex $res 0]\n            set k [lindex $res 1]\n            foreach m $k {\n                lappend members $m\n                if {[llength $members] >= $n} {\n                    set enough 1\n                    break\n                }\n            }\n            if {$enough || $cursor == 0} {\n                break\n            }\n        }\n        r srem $myset {*}$members\n    ",
    )
    proc(
        "setup_move",
        "",
        "        r del myset3{t} myset4{t}\n        create_set myset1{t} {1 a b}\n        create_set myset2{t} {2 3 4}\n        assert_encoding listpack myset1{t}\n        assert_encoding intset myset2{t}\n    ",
    )
    r.run("set", "x{t}", 10)
    with pytest.raises(Exception, match="WRONGTYPE.*"):
        r.run("smove", "myset2{t}", "x{t}", "foo")


def test_smove_with_identical_source_and_destination(r: ValkeyTestClient) -> None:
    """
    test "SMOVE with identical source and destination" {
        r del set{t}
        r sadd set{t} a b c
        r smove set{t} set{t} b
        lsort [r smembers set{t}]
    } {a b c}
    """
    proc(
        "is_rehashing",
        "myset",
        "        set htstats [r debug HTSTATS-KEY $myset]\n        return [string match {*rehashing target*} $htstats]\n    ",
    )
    proc(
        "rem_hash_set_top_N",
        "myset n",
        "        set cursor 0\n        set members {}\n        set enough 0\n        while 1 {\n            set res [r sscan $myset $cursor]\n            set cursor [lindex $res 0]\n            set k [lindex $res 1]\n            foreach m $k {\n                lappend members $m\n                if {[llength $members] >= $n} {\n                    set enough 1\n                    break\n                }\n            }\n            if {$enough || $cursor == 0} {\n                break\n            }\n        }\n        r srem $myset {*}$members\n    ",
    )
    proc(
        "setup_move",
        "",
        "        r del myset3{t} myset4{t}\n        create_set myset1{t} {1 a b}\n        create_set myset2{t} {2 3 4}\n        assert_encoding listpack myset1{t}\n        assert_encoding intset myset2{t}\n    ",
    )
    r.run("del", "set{t}")
    r.run("sadd", "set{t}", "a", "b", "c")
    r.run("smove", "set{t}", "set{t}", "b")
    assert sorted(r.run("smembers", "set{t}")) == "a b c"


def test_smove_only_notify_dstset_when_the_addition_is_successful(r: ValkeyTestClient) -> None:
    """
    test "SMOVE only notify dstset when the addition is successful" {
        r del srcset{t}
        r del dstset{t}

        r sadd srcset{t} a b
        r sadd dstset{t} a

        r watch dstset{t}

        r multi
        r sadd dstset{t} c

        set r2 [valkey_client]
        $r2 smove srcset{t} dstset{t} a

        # The dstset is actually unchanged, multi should success
        r exec
        set res [r scard dstset{t}]
        assert_equal $res 2
        $r2 close
    }
    """
    proc(
        "is_rehashing",
        "myset",
        "        set htstats [r debug HTSTATS-KEY $myset]\n        return [string match {*rehashing target*} $htstats]\n    ",
    )
    proc(
        "rem_hash_set_top_N",
        "myset n",
        "        set cursor 0\n        set members {}\n        set enough 0\n        while 1 {\n            set res [r sscan $myset $cursor]\n            set cursor [lindex $res 0]\n            set k [lindex $res 1]\n            foreach m $k {\n                lappend members $m\n                if {[llength $members] >= $n} {\n                    set enough 1\n                    break\n                }\n            }\n            if {$enough || $cursor == 0} {\n                break\n            }\n        }\n        r srem $myset {*}$members\n    ",
    )
    proc(
        "setup_move",
        "",
        "        r del myset3{t} myset4{t}\n        create_set myset1{t} {1 a b}\n        create_set myset2{t} {2 3 4}\n        assert_encoding listpack myset1{t}\n        assert_encoding intset myset2{t}\n    ",
    )
    r.run("del", "srcset{t}")
    r.run("del", "dstset{t}")
    r.run("sadd", "srcset{t}", "a", "b")
    r.run("sadd", "dstset{t}", "a")
    r.run("watch", "dstset{t}")
    r.run("multi")
    r.run("sadd", "dstset{t}", "c")
    r2 = ValkeyTestClient.create_from(r)
    r2.run("smove", "srcset{t}", "dstset{t}", "a")
    r.run("exec")
    res = r.run("scard", "dstset{t}")
    assert res == 2
    r2.run("close")


"""
run_solo {set-large-memory} {
    start_server [list overrides [list save ""] tags {"large-memory"}] {

    # test if the server supports such large configs (avoid 32 bit builds)
    catch {
        r config set proto-max-bulk-len 10000000000 ;#10gb
        r config set client-query-buffer-limit 10000000000 ;#10gb
    }
    if {[lindex [r config get proto-max-bulk-len] 1] == 10000000000} {

        set str_length 4400000000 ;#~4.4GB

        test {SADD, SCARD, SISMEMBER - large data} {
            r flushdb
            r write "*3\r\n\$4\r\nSADD\r\n\$5\r\nmyset\r\n"
            assert_equal 1 [write_big_bulk $str_length "aaa"]
            r write "*3\r\n\$4\r\nSADD\r\n\$5\r\nmyset\r\n"
            assert_equal 1 [write_big_bulk $str_length "bbb"]
            r write "*3\r\n\$4\r\nSADD\r\n\$5\r\nmyset\r\n"
            assert_equal 0 [write_big_bulk $str_length "aaa"]
            assert_encoding hashtable myset
            set s0 [s used_memory]
            assert {$s0 > [expr $str_length * 2]}
            assert_equal 2 [r scard myset]

            r write "*3\r\n\$9\r\nSISMEMBER\r\n\$5\r\nmyset\r\n"
            assert_equal 1 [write_big_bulk $str_length "aaa"]
            r write "*3\r\n\$9\r\nSISMEMBER\r\n\$5\r\nmyset\r\n"
            assert_equal 0 [write_big_bulk $str_length "ccc"]
            r write "*3\r\n\$4\r\nSREM\r\n\$5\r\nmyset\r\n"
            assert_equal 1 [write_big_bulk $str_length "bbb"]
            assert_equal [read_big_bulk {r spop myset} yes "aaa"] $str_length
        }

        # restore defaults
        r config set proto-max-bulk-len 536870912
        r config set client-query-buffer-limit 1073741824

    } ;# skip 32bit builds
    }
}
"""


# --- stubs for unimplemented TCL helpers ---


def array(*args):
    raise NotImplementedError("array")


def assert_encoding(*args):
    raise NotImplementedError("assert_encoding")


def assert_replication_stream(*args):
    raise NotImplementedError("assert_replication_stream")


def attach_to_replication_stream(*args):
    raise NotImplementedError("attach_to_replication_stream")


def chi_square_value(*args):
    raise NotImplementedError("chi_square_value")


def close_replication_stream(*args):
    raise NotImplementedError("close_replication_stream")


def concat(*args):
    raise NotImplementedError("concat")


def create_set(*args):
    raise NotImplementedError("create_set")


def expr(*args):
    raise NotImplementedError("expr")


def for_(*args):
    raise NotImplementedError("for_")


def foreach(*args):
    raise NotImplementedError("foreach")


def format_(*args):
    raise NotImplementedError("format_")


def proc(*args):
    raise NotImplementedError("proc")


def random_int(*args):
    raise NotImplementedError("random_int")


def set_(*args):
    raise NotImplementedError("set_")


def setup_move(*args):
    raise NotImplementedError("setup_move")


def string(*args):
    raise NotImplementedError("string")


def unset(*args):
    raise NotImplementedError("unset")


def while_(*args):
    raise NotImplementedError("while_")
