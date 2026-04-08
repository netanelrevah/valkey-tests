# ruff: noqa: PLR2004, ANN002, ANN201

import pytest

from tests.valkey_test_client import ValkeyTestClient

"""
set testmodule file normalize tests/modules/cmdintrospection.so
"""

pytestmark = [pytest.mark.modules]


"""
r module load testmodule
"""


def test_module_command_introspection_via_command_info(r: ValkeyTestClient) -> None:
    """
    test "Module command introspection via COMMAND INFO" {
        set redis_reply [lindex [r command info xadd] 0]
        set module_reply [lindex [r command info cmdintrospection.xadd] 0]
        for {set i 1} {$i < [llength $redis_reply]} {incr i} {
            if {$i == 2} {
                # Remove the "module" flag
                set mylist [lindex $module_reply $i]
                set idx [lsearch $mylist "module"]
                set mylist [lreplace $mylist $idx $idx]
                lset module_reply $i $mylist
            }
            if {$i == 6} {
                # Skip ACL categories
                continue
            }
            assert_equal [lindex $redis_reply $i] [lindex $module_reply $i]
        }
    }
    """
    redis_reply = r.run("command", "info", "xadd")[0]
    module_reply = r.run("command", "info", "cmdintrospection.xadd")[0]
    i = 1
    while i < len(redis_reply):
        if_(
            "$i == 2",
            '                # Remove the "module" flag\n                set mylist [lindex $module_reply $i]\n                set idx [lsearch $mylist "module"]\n                set mylist [lreplace $mylist $idx $idx]\n                lset module_reply $i $mylist\n            ',
        )
        if i == 6:
            continue_()
        assert redis_reply[i] == module_reply[i]
        i += 1


def test_module_command_introspection_via_command_docs(r: ValkeyTestClient) -> None:
    """
    test "Module command introspection via COMMAND DOCS" {
        set redis_reply [dict create {*}[lindex [r command docs xadd] 1]]
        set module_reply [dict create {*}[lindex [r command docs cmdintrospection.xadd] 1]]
        # Compare the maps. We need to pop "group" first.
        dict unset redis_reply group
        dict unset module_reply group
        dict unset module_reply module
        if {$::log_req_res} {
            dict unset redis_reply reply_schema
        }

        assert_equal $redis_reply $module_reply
    }
    """
    redis_reply = dict_("create", "*", r.run("command", "docs", "xadd")[1])
    module_reply = dict_("create", "*", r.run("command", "docs", "cmdintrospection.xadd")[1])
    dict_("unset", "redis_reply", "group")
    dict_("unset", "module_reply", "group")
    dict_("unset", "module_reply", "module")
    if False:
        dict_("unset", "redis_reply", "reply_schema")
    assert redis_reply == module_reply


def test_unload_the_module_cmdintrospection(r: ValkeyTestClient) -> None:
    """
    test "Unload the module - cmdintrospection" {
        assert_equal {OK} [r module unload cmdintrospection]
    }
    """
    assert "OK" == r.run("module", "unload", "cmdintrospection")


# --- stubs for unimplemented TCL helpers ---


def continue_(*args):
    raise NotImplementedError("continue_")


def dict_(*args):
    raise NotImplementedError("dict_")


def if_(*args):
    raise NotImplementedError("if_")
