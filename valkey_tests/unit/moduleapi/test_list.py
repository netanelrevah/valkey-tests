# ruff: noqa: RUF043, ANN002, ANN201

import pytest

from tests.valkey_test_client import ValkeyTestClient

"""
set testmodule file normalize tests/modules/list.so
"""


"""
proc verify_list_edit_reply {reply argv} {
    foreach {k v} $argv {
        assert_equal [dict get $reply $k] $v
    }
}
"""

pytestmark = [pytest.mark.modules]


"""
r module load testmodule
"""


def test_module_list_set_get_insert_delete(r: ValkeyTestClient) -> None:
    """
    test {Module list set, get, insert, delete} {
        r del k
        assert_error {WRONGTYPE Operation against a key holding the wrong kind of value*} {r list.set k 1 xyz}
        r rpush k x
        # insert, set, get
        r list.insert k 0 foo
        r list.insert k -1 bar
        r list.set k 1 xyz
        assert_equal {foo xyz bar} [r list.getall k]
        assert_equal {foo} [r list.get k 0]
        assert_equal {xyz} [r list.get k 1]
        assert_equal {bar} [r list.get k 2]
        assert_equal {bar} [r list.get k -1]
        assert_equal {foo} [r list.get k -3]
        assert_error {ERR index out*} {r list.get k -4}
        assert_error {ERR index out*} {r list.get k 3}
        # remove
        assert_error {ERR index out*} {r list.delete k -4}
        assert_error {ERR index out*} {r list.delete k 3}
        r list.delete k 0
        r list.delete k -1
        assert_equal {xyz} [r list.getall k]
        # removing the last element deletes the list
        r list.delete k 0
        assert_equal 0 [r exists k]
    }
    """
    r.run("del", "k")
    with pytest.raises(
        Exception, match="WRONGTYPE\\ Operation\\ against\\ a\\ key\\ holding\\ the\\ wrong\\ kind\\ of\\ value.*"
    ):
        r.run("list.set", "k", 1, "xyz")
    r.run("rpush", "k", "x")
    r.run("list.insert", "k", 0, "foo")
    r.run("list.insert", "k", -1, "bar")
    r.run("list.set", "k", 1, "xyz")
    assert "foo xyz bar" == r.run("list.getall", "k")
    assert "foo" == r.run("list.get", "k", 0)
    assert "xyz" == r.run("list.get", "k", 1)
    assert "bar" == r.run("list.get", "k", 2)
    assert "bar" == r.run("list.get", "k", -1)
    assert "foo" == r.run("list.get", "k", -3)
    with pytest.raises(Exception, match="ERR\\ index\\ out.*"):
        r.run("list.get", "k", -4)
    with pytest.raises(Exception, match="ERR\\ index\\ out.*"):
        r.run("list.get", "k", 3)
    with pytest.raises(Exception, match="ERR\\ index\\ out.*"):
        r.run("list.delete", "k", -4)
    with pytest.raises(Exception, match="ERR\\ index\\ out.*"):
        r.run("list.delete", "k", 3)
    r.run("list.delete", "k", 0)
    r.run("list.delete", "k", -1)
    assert "xyz" == r.run("list.getall", "k")
    r.run("list.delete", "k", 0)
    assert 0 == r.run("exists", "k")


def test_module_list_iteration(r: ValkeyTestClient) -> None:
    """
    test {Module list iteration} {
        r del k
        r rpush k x y z
        assert_equal {x y z} [r list.getall k]
        assert_equal {z y x} [r list.getall k REVERSE]
    }
    """
    r.run("del", "k")
    r.run("rpush", "k", "x", "y", "z")
    assert "x y z" == r.run("list.getall", "k")
    assert "z y x" == r.run("list.getall", "k", "REVERSE")


def test_module_list_insert_delete(r: ValkeyTestClient) -> None:
    """
    test {Module list insert & delete} {
        r del k
        r rpush k x y z
        verify_list_edit_reply [r list.edit k ikikdi foo bar baz] {i 3 index 5}
        r list.getall k
    } {foo x bar y baz}
    """
    r.run("del", "k")
    r.run("rpush", "k", "x", "y", "z")
    verify_list_edit_reply(r.run("list.edit", "k", "ikikdi", "foo", "bar", "baz"), "i 3 index 5")
    assert r.run("list.getall", "k") == "foo x bar y baz"


def test_module_list_insert_delete_neg_index(r: ValkeyTestClient) -> None:
    """
    test {Module list insert & delete, neg index} {
        r del k
        r rpush k x y z
        verify_list_edit_reply [r list.edit k REVERSE ikikdi foo bar baz] {i 3 index -6}
        r list.getall k
    } {baz y bar z foo}
    """
    r.run("del", "k")
    r.run("rpush", "k", "x", "y", "z")
    verify_list_edit_reply(r.run("list.edit", "k", "REVERSE", "ikikdi", "foo", "bar", "baz"), "i 3 index -6")
    assert r.run("list.getall", "k") == "baz y bar z foo"


def test_module_list_set_while_iterating(r: ValkeyTestClient) -> None:
    """
    test {Module list set while iterating} {
        r del k
        r rpush k x y z
        verify_list_edit_reply [r list.edit k rkr foo bar] {r 2 index 3}
        r list.getall k
    } {foo y bar}
    """
    r.run("del", "k")
    r.run("rpush", "k", "x", "y", "z")
    verify_list_edit_reply(r.run("list.edit", "k", "rkr", "foo", "bar"), "r 2 index 3")
    assert r.run("list.getall", "k") == "foo y bar"


def test_module_list_set_while_iterating_neg_index(r: ValkeyTestClient) -> None:
    """
    test {Module list set while iterating, neg index} {
        r del k
        r rpush k x y z
        verify_list_edit_reply [r list.edit k reverse rkr foo bar] {r 2 index -4}
        r list.getall k
    } {bar y foo}
    """
    r.run("del", "k")
    r.run("rpush", "k", "x", "y", "z")
    verify_list_edit_reply(r.run("list.edit", "k", "reverse", "rkr", "foo", "bar"), "r 2 index -4")
    assert r.run("list.getall", "k") == "bar y foo"


def test_module_list_encoding_conversion_while_inserting(r: ValkeyTestClient) -> None:
    """
    test {Module list - encoding conversion while inserting} {
        r config set list-max-listpack-size 4
        r del k
        r rpush k a b c d
        assert_encoding listpack k

        # Converts to quicklist after inserting.
        r list.edit k dii foo bar
        assert_encoding quicklist k
        assert_equal [r list.getall k] {foo bar b c d}

        # Converts to listpack after deleting three entries.
        r list.edit k ddd e
        assert_encoding listpack k
        assert_equal [r list.getall k] {c d}
    }
    """
    r.run("config", "set", "list-max-listpack-size", 4)
    r.run("del", "k")
    r.run("rpush", "k", "a", "b", "c", "d")
    assert_encoding("listpack", "k")
    r.run("list.edit", "k", "dii", "foo", "bar")
    assert_encoding("quicklist", "k")
    assert r.run("list.getall", "k") == "foo bar b c d"
    r.run("list.edit", "k", "ddd", "e")
    assert_encoding("listpack", "k")
    assert r.run("list.getall", "k") == "c d"


@pytest.mark.xfail(reason="not implemented")
def test_module_list_encoding_conversion_while_replacing(r: ValkeyTestClient) -> None:
    """
    test {Module list - encoding conversion while replacing} {
        r config set list-max-listpack-size -1
        r del k
        r rpush k x y z
        assert_encoding listpack k

        # Converts to quicklist after replacing.
        set big [string repeat "x" 4096]
        r list.edit k r $big
        assert_encoding quicklist k
        assert_equal [r list.getall k] "$big y z"

        # Converts to listpack after deleting the big entry.
        r list.edit k d
        assert_encoding listpack k
        assert_equal [r list.getall k] {y z}
    }
    """
    r.run("config", "set", "list-max-listpack-size", -1)
    r.run("del", "k")
    r.run("rpush", "k", "x", "y", "z")
    assert_encoding("listpack", "k")
    big = string("repeat", "x", 4096)
    r.run("list.edit", "k", "r", big)
    assert_encoding("quicklist", "k")
    # TODO: assert_equal r list.getall k "$big y z"
    r.run("list.edit", "k", "d")
    assert_encoding("listpack", "k")
    assert r.run("list.getall", "k") == "y z"


def test_module_list_list_entry_and_index_should_be_updated_when_deletion(r: ValkeyTestClient) -> None:
    """
    test {Module list - list entry and index should be updated when deletion} {
        set original_config [config_get_set list-max-listpack-size 1]

        # delete from start (index 0)
        r del l
        r rpush l x y z
        verify_list_edit_reply [r list.edit l dd] {d 2 index 0 entry z}
        assert_equal [r list.getall l] {z}

        # delete from start (index -3)
        r del l
        r rpush l x y z
        verify_list_edit_reply [r list.edit l reverse kkd] {d 1 index -3}
        assert_equal [r list.getall l] {y z}

        # # delete from tail (index 2)
        r del l
        r rpush l x y z
        verify_list_edit_reply [r list.edit l kkd] {d 1 index 2}
        assert_equal [r list.getall l] {x y}

        # # delete from tail (index -1)
        r del l
        r rpush l x y z
        verify_list_edit_reply [r list.edit l reverse dd] {d 2 index -1 entry x}
        assert_equal [r list.getall l] {x}

        # # delete from middle (index 1)
        r del l
        r rpush l x y z
        verify_list_edit_reply [r list.edit l kdd] {d 2 index 1}
        assert_equal [r list.getall l] {x}

        # # delete from middle (index -2)
        r del l
        r rpush l x y z
        verify_list_edit_reply [r list.edit l reverse kdd] {d 2 index -2}
        assert_equal [r list.getall l] {z}

        config_set list-max-listpack-size $original_config
    }
    """
    original_config = config_get_set("list-max-listpack-size", 1)
    r.run("del", "l")
    r.run("rpush", "l", "x", "y", "z")
    verify_list_edit_reply(r.run("list.edit", "l", "dd"), "d 2 index 0 entry z")
    assert r.run("list.getall", "l") == "z"
    r.run("del", "l")
    r.run("rpush", "l", "x", "y", "z")
    verify_list_edit_reply(r.run("list.edit", "l", "reverse", "kkd"), "d 1 index -3")
    assert r.run("list.getall", "l") == "y z"
    r.run("del", "l")
    r.run("rpush", "l", "x", "y", "z")
    verify_list_edit_reply(r.run("list.edit", "l", "kkd"), "d 1 index 2")
    assert r.run("list.getall", "l") == "x y"
    r.run("del", "l")
    r.run("rpush", "l", "x", "y", "z")
    verify_list_edit_reply(r.run("list.edit", "l", "reverse", "dd"), "d 2 index -1 entry x")
    assert r.run("list.getall", "l") == "x"
    r.run("del", "l")
    r.run("rpush", "l", "x", "y", "z")
    verify_list_edit_reply(r.run("list.edit", "l", "kdd"), "d 2 index 1")
    assert r.run("list.getall", "l") == "x"
    r.run("del", "l")
    r.run("rpush", "l", "x", "y", "z")
    verify_list_edit_reply(r.run("list.edit", "l", "reverse", "kdd"), "d 2 index -2")
    assert r.run("list.getall", "l") == "z"
    config_set("list-max-listpack-size", original_config)


def test_unload_the_module_list(r: ValkeyTestClient) -> None:
    """
    test "Unload the module - list" {
        assert_equal {OK} [r module unload list]
    }
    """
    assert "OK" == r.run("module", "unload", "list")


# --- stubs for unimplemented TCL helpers ---


def assert_encoding(*args):
    raise NotImplementedError("assert_encoding")


def config_get_set(*args):
    raise NotImplementedError("config_get_set")


def config_set(*args):
    raise NotImplementedError("config_set")


def string(*args):
    raise NotImplementedError("string")


def verify_list_edit_reply(*args):
    raise NotImplementedError("verify_list_edit_reply")
