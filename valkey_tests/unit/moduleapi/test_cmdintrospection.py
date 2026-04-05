import pytest

from tests.valkey_test_client import ValkeyTestClient

"""
set testmodule file normalize tests/modules/cmdintrospection.so
"""

pytestmark = [pytest.mark.modules]


"""
r module load testmodule
"""


@pytest.mark.xfail(reason="not implemented")
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
    # TODO: set redis_reply lindex [r command info xadd] 0
    # TODO: set module_reply lindex [r command info cmdintrospection.xadd] 0
    # TODO: for {set i 1} {$i < [llength $redis_reply]} {incr i} {
    #       if {$i == 2} {
    #           # Remove the "module" flag
    #           set mylist [lindex $module_reply $i]
    #           set idx [lsearch $mylist "module"]
    #           set mylist [lreplace $mylist $idx $idx]
    #           lset module_reply $i $mylist
    #       }
    #       if {$i == 6} {
    #           # Skip ACL categories
    #           continue
    #       }
    #       assert_equal [lindex $redis_reply $i] [lindex $module_reply $i]
    #   }


@pytest.mark.xfail(reason="not implemented")
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
    # TODO: set redis_reply dict create {*}[lindex [r command docs xadd] 1]
    # TODO: set module_reply dict create {*}[lindex [r command docs cmdintrospection.xadd] 1]
    # TODO: dict unset redis_reply group
    # TODO: dict unset module_reply group
    # TODO: dict unset module_reply module
    # TODO: if {$::log_req_res} {
    #       dict unset redis_reply reply_schema
    #   }
    # TODO: assert_equal redis _reply module _reply


def test_unload_the_module_cmdintrospection(r: ValkeyTestClient) -> None:
    """
    test "Unload the module - cmdintrospection" {
        assert_equal {OK} [r module unload cmdintrospection]
    }
    """
    assert "OK" == r.run("module", "unload", "cmdintrospection")
