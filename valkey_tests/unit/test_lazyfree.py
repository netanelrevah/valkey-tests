# ruff: noqa: F841

import pytest

from tests.valkey_test_client import ValkeyTestClient

pytestmark = [pytest.mark.lazyfree]


@pytest.mark.xfail(reason="not implemented")
def test_unlink_can_reclaim_memory_in_background(r: ValkeyTestClient) -> None:
    """
    test "UNLINK can reclaim memory in background" {
        # make sure the previous test is really done before sampling used_memory
        wait_lazyfree_done r

        set orig_mem [s used_memory]
        set args {}
        for {set i 0} {$i < 100000} {incr i} {
            lappend args $i
        }
        r sadd myset {*}$args
        assert {[r scard myset] == 100000}
        set peak_mem [s used_memory]
        assert {[r unlink myset] == 1}
        assert {$peak_mem > $orig_mem+1000000}
        wait_for_condition 50 100 {
            [s used_memory] < $peak_mem &&
            [s used_memory] < $orig_mem*2
        } else {
            fail "Memory is not reclaimed by UNLINK"
        }
    }
    """
    # TODO: wait_lazyfree_done r
    # TODO: set orig_mem s used_memory
    args = ""
    # TODO: for {set i 0} {$i < 100000} {incr i} {
    #       lappend args $i
    #   }
    r.run("sadd", "myset", "*", args)
    # TODO: assert {[r scard myset] == 100000}
    # TODO: set peak_mem s used_memory
    # TODO: assert {[r unlink myset] == 1}
    # TODO: assert {$peak_mem > $orig_mem+1000000}
    # TODO: wait_for_condition 50 100 {
    #       [s used_memory] < $peak_mem &&
    #       [s used_memory] < $orig_mem*2
    #   } else {
    #       fail "Memory is not reclaimed by UNLINK"
    #   }


@pytest.mark.xfail(reason="not implemented")
def test_flushdb_async_can_reclaim_memory_in_background(r: ValkeyTestClient) -> None:
    """
    test "FLUSHDB ASYNC can reclaim memory in background" {
        # make sure the previous test is really done before sampling used_memory
        wait_lazyfree_done r

        set orig_mem [s used_memory]
        set args {}
        for {set i 0} {$i < 100000} {incr i} {
            lappend args $i
        }
        r sadd myset {*}$args
        assert {[r scard myset] == 100000}
        set peak_mem [s used_memory]
        r flushdb async
        assert {$peak_mem > $orig_mem+1000000}
        wait_for_condition 50 100 {
            [s used_memory] < $peak_mem &&
            [s used_memory] < $orig_mem*2
        } else {
            fail "Memory is not reclaimed by FLUSHDB ASYNC"
        }
    }
    """
    # TODO: wait_lazyfree_done r
    # TODO: set orig_mem s used_memory
    args = ""
    # TODO: for {set i 0} {$i < 100000} {incr i} {
    #       lappend args $i
    #   }
    r.run("sadd", "myset", "*", args)
    # TODO: assert {[r scard myset] == 100000}
    # TODO: set peak_mem s used_memory
    r.run("flushdb", "async")
    # TODO: assert {$peak_mem > $orig_mem+1000000}
    # TODO: wait_for_condition 50 100 {
    #       [s used_memory] < $peak_mem &&
    #       [s used_memory] < $orig_mem*2
    #   } else {
    #       fail "Memory is not reclaimed by FLUSHDB ASYNC"
    #   }


@pytest.mark.xfail(reason="not implemented")
def test_lazy_free_a_stream_with_all_types_of_metadata(r: ValkeyTestClient) -> None:
    """
    test "lazy free a stream with all types of metadata" {
        # make the previous test is really done before doing RESETSTAT
        wait_for_condition 50 100 {
            [s lazyfree_pending_objects] == 0
        } else {
            fail "lazyfree isn't done"
        }

        r config resetstat
        r config set stream-node-max-entries 5
        for {set j 0} {$j < 1000} {incr j} {
            if {rand() < 0.9} {
                r xadd stream * foo $j
            } else {
                r xadd stream * bar $j
            }
        }
        r xgroup create stream mygroup 0
        set records [r xreadgroup GROUP mygroup Alice COUNT 2 STREAMS stream >]
        r xdel stream [lindex [lindex [lindex [lindex $records 0] 1] 1] 0]
        r xack stream mygroup [lindex [lindex [lindex [lindex $records 0] 1] 0] 0]
        r unlink stream

        # make sure it was lazy freed
        wait_for_condition 50 100 {
            [s lazyfree_pending_objects] == 0
        } else {
            fail "lazyfree isn't done"
        }
        assert_equal [s lazyfreed_objects] 1
    } {} {needs:config-resetstat}
    """
    # TODO: wait_for_condition 50 100 {
    #       [s lazyfree_pending_objects] == 0
    #   } else {
    #       fail "lazyfree isn't done"
    #   }
    r.run("config", "resetstat")
    r.run("config", "set", "stream-node-max-entries", 5)
    # TODO: for {set j 0} {$j < 1000} {incr j} {
    #       if {rand() < 0.9} {
    #           r xadd stream * foo $j
    #       } else {
    #           r xadd stream * bar $j
    #       }
    #   }
    r.run("xgroup", "create", "stream", "mygroup", 0)
    records = r.run("xreadgroup", "GROUP", "mygroup", "Alice", "COUNT", 2, "STREAMS", "stream", ">")
    # TODO: r xdel stream lindex [lindex [lindex [lindex $records 0] 1] 1] 0
    # TODO: r xack stream mygroup lindex [lindex [lindex [lindex $records 0] 1] 0] 0
    r.run("unlink", "stream")
    # TODO: wait_for_condition 50 100 {
    #       [s lazyfree_pending_objects] == 0
    #   } else {
    #       fail "lazyfree isn't done"
    #   }
    # TODO: assert_equal s lazyfreed_objects 1
    assert False


@pytest.mark.xfail(reason="not implemented")
def test_lazy_free_a_stream_with_deleted_cgroup(r: ValkeyTestClient) -> None:
    """
    test "lazy free a stream with deleted cgroup" {
        r config resetstat
        r xadd s * a b
        r xgroup create s bla $
        r xgroup destroy s bla
        r unlink s

        # make sure it was not lazy freed
        wait_for_condition 50 100 {
            [s lazyfree_pending_objects] == 0
        } else {
            fail "lazyfree isn't done"
        }
        assert_equal [s lazyfreed_objects] 0
    } {} {needs:config-resetstat}
    """
    r.run("config", "resetstat")
    r.run("xadd", "s", "*", "a", "b")
    # TODO: r xgroup create s bla
    r.run("xgroup", "destroy", "s", "bla")
    r.run("unlink", "s")
    # TODO: wait_for_condition 50 100 {
    #       [s lazyfree_pending_objects] == 0
    #   } else {
    #       fail "lazyfree isn't done"
    #   }
    # TODO: assert_equal s lazyfreed_objects 0
    assert False
