# ruff: noqa: PLR2004, PLR1714, F841, RUF043, ANN001, ANN002, ANN201
import time
from fnmatch import fnmatch

import pytest

from tests.valkey_test_client import ValkeyTestClient

"""
proc wait_for_dbsize {size} {
    set r2 [valkey_client]
    wait_for_condition 50 100 {
        [$r2 dbsize] == $size
    } else {
        fail "Target dbsize not reached"
    }
    $r2 close
}
"""

pytestmark = [pytest.mark.multi]


@pytest.mark.xfail(reason="not implemented")
def test_multi_or_exec_basics(r: ValkeyTestClient) -> None:
    """
    test {MULTI / EXEC basics} {
        r del mylist
        r rpush mylist a
        r rpush mylist b
        r rpush mylist c
        r multi
        set v1 [r lrange mylist 0 -1]
        set v2 [r ping]
        set v3 [r exec]
        list $v1 $v2 $v3
    } {QUEUED QUEUED {{a b c} PONG}}
    """
    r.run("del", "mylist")
    r.run("rpush", "mylist", "a")
    r.run("rpush", "mylist", "b")
    r.run("rpush", "mylist", "c")
    r.run("multi")
    v1 = r.run("lrange", "mylist", 0, -1)
    v2 = r.run("ping")
    v3 = r.run("exec")
    # TODO: list v1 v2 v3
    assert False


@pytest.mark.xfail(reason="not implemented")
def test_discard(r: ValkeyTestClient) -> None:
    """
    test {DISCARD} {
        r del mylist
        r rpush mylist a
        r rpush mylist b
        r rpush mylist c
        r multi
        set v1 [r del mylist]
        set v2 [r discard]
        set v3 [r lrange mylist 0 -1]
        list $v1 $v2 $v3
    } {QUEUED OK {a b c}}
    """
    r.run("del", "mylist")
    r.run("rpush", "mylist", "a")
    r.run("rpush", "mylist", "b")
    r.run("rpush", "mylist", "c")
    r.run("multi")
    v1 = r.run("del", "mylist")
    v2 = r.run("discard")
    v3 = r.run("lrange", "mylist", 0, -1)
    # TODO: list v1 v2 v3
    assert False


def test_nested_multi_are_not_allowed(r: ValkeyTestClient) -> None:
    """
    test {Nested MULTI are not allowed} {
        r multi
        assert_error "ERR Command 'multi' not allowed inside a transaction*" {r multi}
        assert_error "EXECABORT*" {r exec}
    }
    """
    r.run("multi")
    with pytest.raises(Exception, match="ERR\\ Command\\ 'multi'\\ not\\ allowed\\ inside\\ a\\ transaction.*"):
        r.run("multi")
    with pytest.raises(Exception, match="EXECABORT.*"):
        r.run("exec")


@pytest.mark.xfail(reason="not implemented")
def test_multi_where_commands_alter_argc_or_argv(r: ValkeyTestClient) -> None:
    """
    test {MULTI where commands alter argc/argv} {
        r sadd myset a
        r multi
        r spop myset
        list [r exec] [r exists myset]
    } {a 0}
    """
    r.run("sadd", "myset", "a")
    r.run("multi")
    r.run("spop", "myset")
    # TODO: list r exec r exists myset
    assert False


def test_watch_inside_multi_is_not_allowed(r: ValkeyTestClient) -> None:
    """
    test {WATCH inside MULTI is not allowed} {
        r multi
        assert_error "ERR Command 'watch' not allowed inside a transaction*" {r watch x}
        assert_error "EXECABORT*" {r exec}
    }
    """
    r.run("multi")
    with pytest.raises(Exception, match="ERR\\ Command\\ 'watch'\\ not\\ allowed\\ inside\\ a\\ transaction.*"):
        r.run("watch", "x")
    with pytest.raises(Exception, match="EXECABORT.*"):
        r.run("exec")


@pytest.mark.xfail(reason="not implemented")
def test_exec_fails_if_there_are_errors_while_queueing_commands_1(r: ValkeyTestClient) -> None:
    """
    test {EXEC fails if there are errors while queueing commands #1} {
        r del foo1{t} foo2{t}
        r multi
        r set foo1{t} bar1
        catch {r non-existing-command}
        r set foo2{t} bar2
        catch {r exec} e
        assert_match {EXECABORT*} $e
        list [r exists foo1{t}] [r exists foo2{t}]
    } {0 0}
    """
    r.run("del", "foo1{t}", "foo2{t}")
    r.run("multi")
    r.run("set", "foo1{t}", "bar1")
    try:
        r.run("non-existing-command")
    except Exception:
        pass
    r.run("set", "foo2{t}", "bar2")
    try:
        e = r.run("exec")
    except Exception as _catch_err:
        e = str(_catch_err)
    assert fnmatch(str(e), "EXECABORT*")
    # TODO: list r exists foo1{t} r exists foo2{t}
    assert False


@pytest.mark.xfail(reason="not implemented")
def test_exec_fails_if_there_are_errors_while_queueing_commands_2(r: ValkeyTestClient) -> None:
    """
    test {EXEC fails if there are errors while queueing commands #2} {
        set rd [valkey_deferring_client]
        r del foo1{t} foo2{t}
        r multi
        r set foo1{t} bar1
        $rd config set maxmemory 1
        assert  {[$rd read] eq {OK}}
        catch {r lpush mylist{t} myvalue}
        $rd config set maxmemory 0
        assert  {[$rd read] eq {OK}}
        r set foo2{t} bar2
        catch {r exec} e
        assert_match {EXECABORT*} $e
        $rd close
        list [r exists foo1{t}] [r exists foo2{t}]
    } {0 0} {needs:config-maxmemory}
    """
    rd = valkey_deferring_client()
    r.run("del", "foo1{t}", "foo2{t}")
    r.run("multi")
    r.run("set", "foo1{t}", "bar1")
    rd.run("config", "set", "maxmemory", 1)
    assert rd.run("read") == "OK"
    try:
        r.run("lpush", "mylist{t}", "myvalue")
    except Exception:
        pass
    rd.run("config", "set", "maxmemory", 0)
    assert rd.run("read") == "OK"
    r.run("set", "foo2{t}", "bar2")
    try:
        e = r.run("exec")
    except Exception as _catch_err:
        e = str(_catch_err)
    assert fnmatch(str(e), "EXECABORT*")
    rd.run("close")
    # TODO: list r exists foo1{t} r exists foo2{t}
    assert False


def test_if_exec_aborts_the_client_multi_state_is_cleared(r: ValkeyTestClient) -> None:
    """
    test {If EXEC aborts, the client MULTI state is cleared} {
        r del foo1{t} foo2{t}
        r multi
        r set foo1{t} bar1
        catch {r non-existing-command}
        r set foo2{t} bar2
        catch {r exec} e
        assert_match {EXECABORT*} $e
        r ping
    } {PONG}
    """
    r.run("del", "foo1{t}", "foo2{t}")
    r.run("multi")
    r.run("set", "foo1{t}", "bar1")
    try:
        r.run("non-existing-command")
    except Exception:
        pass
    r.run("set", "foo2{t}", "bar2")
    try:
        e = r.run("exec")
    except Exception as _catch_err:
        e = str(_catch_err)
    assert fnmatch(str(e), "EXECABORT*")
    assert r.run("ping") == "PONG"


def test_exec_works_on_watched_key_not_modified(r: ValkeyTestClient) -> None:
    """
    test {EXEC works on WATCHed key not modified} {
        r watch x{t} y{t} z{t}
        r watch k{t}
        r multi
        r ping
        r exec
    } {PONG}
    """
    r.run("watch", "x{t}", "y{t}", "z{t}")
    r.run("watch", "k{t}")
    r.run("multi")
    r.run("ping")
    assert r.run("exec") == "PONG"


def test_exec_fail_on_watched_key_modified_1_key_of_1_watched(r: ValkeyTestClient) -> None:
    """
    test {EXEC fail on WATCHed key modified (1 key of 1 watched)} {
        r set x 30
        r watch x
        r set x 40
        r multi
        r ping
        r exec
    } {}
    """
    r.run("set", "x", 30)
    r.run("watch", "x")
    r.run("set", "x", 40)
    r.run("multi")
    r.run("ping")
    r.run("exec")


def test_exec_fail_on_watched_key_modified_1_key_of_5_watched(r: ValkeyTestClient) -> None:
    """
    test {EXEC fail on WATCHed key modified (1 key of 5 watched)} {
        r set x{t} 30
        r watch a{t} b{t} x{t} k{t} z{t}
        r set x{t} 40
        r multi
        r ping
        r exec
    } {}
    """
    r.run("set", "x{t}", 30)
    r.run("watch", "a{t}", "b{t}", "x{t}", "k{t}", "z{t}")
    r.run("set", "x{t}", 40)
    r.run("multi")
    r.run("ping")
    r.run("exec")


def test_exec_fail_on_watched_key_modified_by_sort_with_store_even_if_the_result_is_empty(r: ValkeyTestClient) -> None:
    """
    test {EXEC fail on WATCHed key modified by SORT with STORE even if the result is empty} {
        r flushdb
        r lpush foo bar
        r watch foo
        r sort emptylist store foo
        r multi
        r ping
        r exec
    } {} {cluster:skip}
    """
    r.run("flushdb")
    r.run("lpush", "foo", "bar")
    r.run("watch", "foo")
    r.run("sort", "emptylist", "store", "foo")
    r.run("multi")
    r.run("ping")
    r.run("exec")


@pytest.mark.xfail(reason="not implemented")
def test_exec_fail_on_lazy_expired_watched_key(r: ValkeyTestClient) -> None:
    """
    test {EXEC fail on lazy expired WATCHed key} {
        r del key
        r debug set-active-expire 0

        for {set j 0} {$j < 10} {incr j} {
            r set key 1 px 100
            r watch key
            after 101
            r multi
            r incr key

            set res [r exec]
            if {$res eq {}} break
        }
        if {$::verbose} { puts "EXEC fail on lazy expired WATCHed key attempts: $j" }

        r debug set-active-expire 1
        set _ $res
    } {} {needs:debug}
    """
    r.run("del", "key")
    r.run("debug", "set-active-expire", 0)
    j = 0
    while j < 10:
        r.run("set", "key", 1, "px", 100)
        r.run("watch", "key")
        time.sleep(101 / 1000)
        r.run("multi")
        r.run("incr", "key")
        res = r.run("exec")
        if res == "":
            break_()
        j += 1
    if_("$::verbose", ' puts "EXEC fail on lazy expired WATCHed key attempts: $j" ')
    r.run("debug", "set-active-expire", 1)
    # TODO: set _ res


def test_watch_stale_keys_should_not_fail_exec(r: ValkeyTestClient) -> None:
    """
    test {WATCH stale keys should not fail EXEC} {
        r del x
        r debug set-active-expire 0
        r set x foo px 1
        after 2
        r watch x
        r multi
        r ping
        assert_equal {PONG} [r exec]
        r debug set-active-expire 1
    } {OK} {needs:debug}
    """
    r.run("del", "x")
    r.run("debug", "set-active-expire", 0)
    r.run("set", "x", "foo", "px", 1)
    time.sleep(2 / 1000)
    r.run("watch", "x")
    r.run("multi")
    r.run("ping")
    assert "PONG" == r.run("exec")
    assert r.run("debug", "set-active-expire", 1) == "OK"


def test_delete_watched_stale_keys_should_not_fail_exec(r: ValkeyTestClient) -> None:
    """
    test {Delete WATCHed stale keys should not fail EXEC} {
        r del x
        r debug set-active-expire 0
        r set x foo px 1
        after 2
        r watch x
        # EXISTS triggers lazy expiry/deletion
        assert_equal 0 [r exists x]
        r multi
        r ping
        assert_equal {PONG} [r exec]
        r debug set-active-expire 1
    } {OK} {needs:debug}
    """
    r.run("del", "x")
    r.run("debug", "set-active-expire", 0)
    r.run("set", "x", "foo", "px", 1)
    time.sleep(2 / 1000)
    r.run("watch", "x")
    assert 0 == r.run("exists", "x")
    r.run("multi")
    r.run("ping")
    assert "PONG" == r.run("exec")
    assert r.run("debug", "set-active-expire", 1) == "OK"


def test_flushdb_while_watching_stale_keys_should_not_fail_exec(r: ValkeyTestClient) -> None:
    """
    test {FLUSHDB while watching stale keys should not fail EXEC} {
        r del x
        r debug set-active-expire 0
        r set x foo px 1
        after 2
        r watch x
        r flushdb
        r multi
        r ping
        assert_equal {PONG} [r exec]
        r debug set-active-expire 1
    } {OK} {needs:debug}
    """
    r.run("del", "x")
    r.run("debug", "set-active-expire", 0)
    r.run("set", "x", "foo", "px", 1)
    time.sleep(2 / 1000)
    r.run("watch", "x")
    r.run("flushdb")
    r.run("multi")
    r.run("ping")
    assert "PONG" == r.run("exec")
    assert r.run("debug", "set-active-expire", 1) == "OK"


def test_after_successful_exec_key_is_no_longer_watched(r: ValkeyTestClient) -> None:
    """
    test {After successful EXEC key is no longer watched} {
        r set x 30
        r watch x
        r multi
        r ping
        r exec
        r set x 40
        r multi
        r ping
        r exec
    } {PONG}
    """
    r.run("set", "x", 30)
    r.run("watch", "x")
    r.run("multi")
    r.run("ping")
    r.run("exec")
    r.run("set", "x", 40)
    r.run("multi")
    r.run("ping")
    assert r.run("exec") == "PONG"


def test_after_failed_exec_key_is_no_longer_watched(r: ValkeyTestClient) -> None:
    """
    test {After failed EXEC key is no longer watched} {
        r set x 30
        r watch x
        r set x 40
        r multi
        r ping
        r exec
        r set x 40
        r multi
        r ping
        r exec
    } {PONG}
    """
    r.run("set", "x", 30)
    r.run("watch", "x")
    r.run("set", "x", 40)
    r.run("multi")
    r.run("ping")
    r.run("exec")
    r.run("set", "x", 40)
    r.run("multi")
    r.run("ping")
    assert r.run("exec") == "PONG"


def test_it_is_possible_to_unwatch(r: ValkeyTestClient) -> None:
    """
    test {It is possible to UNWATCH} {
        r set x 30
        r watch x
        r set x 40
        r unwatch
        r multi
        r ping
        r exec
    } {PONG}
    """
    r.run("set", "x", 30)
    r.run("watch", "x")
    r.run("set", "x", 40)
    r.run("unwatch")
    r.run("multi")
    r.run("ping")
    assert r.run("exec") == "PONG"


def test_unwatch_when_there_is_nothing_watched_works_as_expected(r: ValkeyTestClient) -> None:
    """
    test {UNWATCH when there is nothing watched works as expected} {
        r unwatch
    } {OK}
    """
    assert r.run("unwatch") == "OK"


def test_flushall_is_able_to_touch_the_watched_keys(r: ValkeyTestClient) -> None:
    """
    test {FLUSHALL is able to touch the watched keys} {
        r set x 30
        r watch x
        r flushall
        r multi
        r ping
        r exec
    } {}
    """
    r.run("set", "x", 30)
    r.run("watch", "x")
    r.run("flushall")
    r.run("multi")
    r.run("ping")
    r.run("exec")


def test_flushall_does_not_touch_non_affected_keys(r: ValkeyTestClient) -> None:
    """
    test {FLUSHALL does not touch non affected keys} {
        r del x
        r watch x
        r flushall
        r multi
        r ping
        r exec
    } {PONG}
    """
    r.run("del", "x")
    r.run("watch", "x")
    r.run("flushall")
    r.run("multi")
    r.run("ping")
    assert r.run("exec") == "PONG"


def test_flushdb_is_able_to_touch_the_watched_keys(r: ValkeyTestClient) -> None:
    """
    test {FLUSHDB is able to touch the watched keys} {
        r set x 30
        r watch x
        r flushdb
        r multi
        r ping
        r exec
    } {}
    """
    r.run("set", "x", 30)
    r.run("watch", "x")
    r.run("flushdb")
    r.run("multi")
    r.run("ping")
    r.run("exec")


def test_flushdb_does_not_touch_non_affected_keys(r: ValkeyTestClient) -> None:
    """
    test {FLUSHDB does not touch non affected keys} {
        r del x
        r watch x
        r flushdb
        r multi
        r ping
        r exec
    } {PONG}
    """
    r.run("del", "x")
    r.run("watch", "x")
    r.run("flushdb")
    r.run("multi")
    r.run("ping")
    assert r.run("exec") == "PONG"


def test_swapdb_is_able_to_touch_the_watched_keys_that_exist(r: ValkeyTestClient) -> None:
    """
    test {SWAPDB is able to touch the watched keys that exist} {
        r flushall
        r select 0
        r set x 30
        r watch x ;# make sure x (set to 30) doesn't change (SWAPDB will "delete" it)
        r swapdb 0 1
        r multi
        r ping
        r exec
    } {} {cluster:skip}
    """
    r.run("flushall")
    r.run("select", 0)
    r.run("set", "x", 30)
    r.run("watch", "x")
    r.run("swapdb", 0, 1)
    r.run("multi")
    r.run("ping")
    r.run("exec")


def test_swapdb_is_able_to_touch_the_watched_keys_that_do_not_exist(r: ValkeyTestClient) -> None:
    """
    test {SWAPDB is able to touch the watched keys that do not exist} {
        r flushall
        r select 1
        r set x 30
        r select 0
        r watch x ;# make sure the key x (currently missing) doesn't change (SWAPDB will create it)
        r swapdb 0 1
        r multi
        r ping
        r exec
    } {} {singledb:skip cluster:skip}
    """
    r.run("flushall")
    r.run("select", 1)
    r.run("set", "x", 30)
    r.run("select", 0)
    r.run("watch", "x")
    r.run("swapdb", 0, 1)
    r.run("multi")
    r.run("ping")
    r.run("exec")


def test_swapdb_does_not_touch_watched_stale_keys(r: ValkeyTestClient) -> None:
    """
    test {SWAPDB does not touch watched stale keys} {
        r flushall
        r select 1
        r debug set-active-expire 0
        r set x foo px 1
        after 2
        r watch x
        r swapdb 0 1 ; # expired key replaced with no key => no change
        r multi
        r ping
        assert_equal {PONG} [r exec]
        r debug set-active-expire 1
    } {OK} {singledb:skip cluster:skip needs:debug}
    """
    r.run("flushall")
    r.run("select", 1)
    r.run("debug", "set-active-expire", 0)
    r.run("set", "x", "foo", "px", 1)
    time.sleep(2 / 1000)
    r.run("watch", "x")
    r.run("swapdb", 0, 1)
    r.run("multi")
    r.run("ping")
    assert "PONG" == r.run("exec")
    assert r.run("debug", "set-active-expire", 1) == "OK"


def test_swapdb_does_not_touch_non_existing_key_replaced_with_stale_key(r: ValkeyTestClient) -> None:
    """
    test {SWAPDB does not touch non-existing key replaced with stale key} {
        r flushall
        r select 0
        r debug set-active-expire 0
        r set x foo px 1
        after 2
        r select 1
        r watch x
        r swapdb 0 1 ; # no key replaced with expired key => no change
        r multi
        r ping
        assert_equal {PONG} [r exec]
        r debug set-active-expire 1
    } {OK} {singledb:skip cluster:skip needs:debug}
    """
    r.run("flushall")
    r.run("select", 0)
    r.run("debug", "set-active-expire", 0)
    r.run("set", "x", "foo", "px", 1)
    time.sleep(2 / 1000)
    r.run("select", 1)
    r.run("watch", "x")
    r.run("swapdb", 0, 1)
    r.run("multi")
    r.run("ping")
    assert "PONG" == r.run("exec")
    assert r.run("debug", "set-active-expire", 1) == "OK"


def test_swapdb_does_not_touch_stale_key_replaced_with_another_stale_key(r: ValkeyTestClient) -> None:
    """
    test {SWAPDB does not touch stale key replaced with another stale key} {
        r flushall
        r debug set-active-expire 0
        r select 1
        r set x foo px 1
        r select 0
        r set x bar px 1
        after 2
        r select 1
        r watch x
        r swapdb 0 1 ; # no key replaced with expired key => no change
        r multi
        r ping
        assert_equal {PONG} [r exec]
        r debug set-active-expire 1
    } {OK} {singledb:skip cluster:skip needs:debug}
    """
    r.run("flushall")
    r.run("debug", "set-active-expire", 0)
    r.run("select", 1)
    r.run("set", "x", "foo", "px", 1)
    r.run("select", 0)
    r.run("set", "x", "bar", "px", 1)
    time.sleep(2 / 1000)
    r.run("select", 1)
    r.run("watch", "x")
    r.run("swapdb", 0, 1)
    r.run("multi")
    r.run("ping")
    assert "PONG" == r.run("exec")
    assert r.run("debug", "set-active-expire", 1) == "OK"


def test_watch_is_able_to_remember_the_db_a_key_belongs_to(r: ValkeyTestClient) -> None:
    """
    test {WATCH is able to remember the DB a key belongs to} {
        r select 5
        r set x 30
        r watch x
        r select 1
        r set x 10
        r select 5
        r multi
        r ping
        set res [r exec]
        # Restore original DB
        r select 9
        set res
    } {PONG} {singledb:skip}
    """
    r.run("select", 5)
    r.run("set", "x", 30)
    r.run("watch", "x")
    r.run("select", 1)
    r.run("set", "x", 10)
    r.run("select", 5)
    r.run("multi")
    r.run("ping")
    res = r.run("exec")
    r.run("select", 9)
    assert res == "PONG"


def test_watch_will_consider_touched_keys_target_of_expire(r: ValkeyTestClient) -> None:
    """
    test {WATCH will consider touched keys target of EXPIRE} {
        r del x
        r set x foo
        r watch x
        r expire x 10
        r multi
        r ping
        r exec
    } {}
    """
    r.run("del", "x")
    r.run("set", "x", "foo")
    r.run("watch", "x")
    r.run("expire", "x", 10)
    r.run("multi")
    r.run("ping")
    r.run("exec")


def test_watch_will_consider_touched_expired_keys(r: ValkeyTestClient) -> None:
    """
    test {WATCH will consider touched expired keys} {
        r flushall
        r del x
        r set x foo
        r expire x 1
        r watch x

        # Wait for the keys to expire.
        wait_for_dbsize 0

        r multi
        r ping
        r exec
    } {}
    """
    r.run("flushall")
    r.run("del", "x")
    r.run("set", "x", "foo")
    r.run("expire", "x", 1)
    r.run("watch", "x")
    wait_for_dbsize(0)
    r.run("multi")
    r.run("ping")
    r.run("exec")


def test_discard_should_clear_the_watch_dirty_flag_on_the_client(r: ValkeyTestClient) -> None:
    """
    test {DISCARD should clear the WATCH dirty flag on the client} {
        r watch x
        r set x 10
        r multi
        r discard
        r multi
        r incr x
        r exec
    } {11}
    """
    r.run("watch", "x")
    r.run("set", "x", 10)
    r.run("multi")
    r.run("discard")
    r.run("multi")
    r.run("incr", "x")
    assert r.run("exec") == "11"


def test_discard_should_unwatch_all_the_keys(r: ValkeyTestClient) -> None:
    """
    test {DISCARD should UNWATCH all the keys} {
        r watch x
        r set x 10
        r multi
        r discard
        r set x 10
        r multi
        r incr x
        r exec
    } {11}
    """
    r.run("watch", "x")
    r.run("set", "x", 10)
    r.run("multi")
    r.run("discard")
    r.run("set", "x", 10)
    r.run("multi")
    r.run("incr", "x")
    assert r.run("exec") == "11"


def test_multi_or_exec_is_not_propagated_single_write_command(r: ValkeyTestClient) -> None:
    """
    test {MULTI / EXEC is not propagated (single write command)} {
        set repl [attach_to_replication_stream]
        r multi
        r set foo bar
        r exec
        r set foo2 bar
        assert_replication_stream $repl {
            {select *}
            {set foo bar}
            {set foo2 bar}
        }
        close_replication_stream $repl
    } {} {needs:repl}
    """
    repl = attach_to_replication_stream()
    r.run("multi")
    r.run("set", "foo", "bar")
    r.run("exec")
    r.run("set", "foo2", "bar")
    assert_replication_stream(
        repl, "            {select *}\n            {set foo bar}\n            {set foo2 bar}\n        "
    )
    close_replication_stream(repl)


def test_multi_or_exec_is_propagated_correctly_multiple_commands(r: ValkeyTestClient) -> None:
    """
    test {MULTI / EXEC is propagated correctly (multiple commands)} {
        set repl [attach_to_replication_stream]
        r multi
        r set foo{t} bar
        r get foo{t}
        r set foo2{t} bar2
        r get foo2{t}
        r set foo3{t} bar3
        r get foo3{t}
        r exec

        assert_replication_stream $repl {
            {multi}
            {select *}
            {set foo{t} bar}
            {set foo2{t} bar2}
            {set foo3{t} bar3}
            {exec}
        }
        close_replication_stream $repl
    } {} {needs:repl}
    """
    repl = attach_to_replication_stream()
    r.run("multi")
    r.run("set", "foo{t}", "bar")
    r.run("get", "foo{t}")
    r.run("set", "foo2{t}", "bar2")
    r.run("get", "foo2{t}")
    r.run("set", "foo3{t}", "bar3")
    r.run("get", "foo3{t}")
    r.run("exec")
    assert_replication_stream(
        repl,
        "            {multi}\n            {select *}\n            {set foo{t} bar}\n            {set foo2{t} bar2}\n            {set foo3{t} bar3}\n            {exec}\n        ",
    )
    close_replication_stream(repl)


def test_multi_or_exec_is_propagated_correctly_multiple_commands_with_select(r: ValkeyTestClient) -> None:
    """
    test {MULTI / EXEC is propagated correctly (multiple commands with SELECT)} {
        set repl [attach_to_replication_stream]
        r multi
        r select 1
        r set foo{t} bar
        r get foo{t}
        r select 2
        r set foo2{t} bar2
        r get foo2{t}
        r select 3
        r set foo3{t} bar3
        r get foo3{t}
        r exec

        assert_replication_stream $repl {
            {multi}
            {select *}
            {set foo{t} bar}
            {select *}
            {set foo2{t} bar2}
            {select *}
            {set foo3{t} bar3}
            {exec}
        }
        close_replication_stream $repl
    } {} {needs:repl singledb:skip}
    """
    repl = attach_to_replication_stream()
    r.run("multi")
    r.run("select", 1)
    r.run("set", "foo{t}", "bar")
    r.run("get", "foo{t}")
    r.run("select", 2)
    r.run("set", "foo2{t}", "bar2")
    r.run("get", "foo2{t}")
    r.run("select", 3)
    r.run("set", "foo3{t}", "bar3")
    r.run("get", "foo3{t}")
    r.run("exec")
    assert_replication_stream(
        repl,
        "            {multi}\n            {select *}\n            {set foo{t} bar}\n            {select *}\n            {set foo2{t} bar2}\n            {select *}\n            {set foo3{t} bar3}\n            {exec}\n        ",
    )
    close_replication_stream(repl)


def test_multi_or_exec_is_propagated_correctly_empty_transaction(r: ValkeyTestClient) -> None:
    """
    test {MULTI / EXEC is propagated correctly (empty transaction)} {
        set repl [attach_to_replication_stream]
        r multi
        r exec
        r set foo bar
        assert_replication_stream $repl {
            {select *}
            {set foo bar}
        }
        close_replication_stream $repl
    } {} {needs:repl}
    """
    repl = attach_to_replication_stream()
    r.run("multi")
    r.run("exec")
    r.run("set", "foo", "bar")
    assert_replication_stream(repl, "            {select *}\n            {set foo bar}\n        ")
    close_replication_stream(repl)


def test_multi_or_exec_is_propagated_correctly_read_only_commands(r: ValkeyTestClient) -> None:
    """
    test {MULTI / EXEC is propagated correctly (read-only commands)} {
        r set foo value1
        set repl [attach_to_replication_stream]
        r multi
        r get foo
        r exec
        r set foo value2
        assert_replication_stream $repl {
            {select *}
            {set foo value2}
        }
        close_replication_stream $repl
    } {} {needs:repl}
    """
    r.run("set", "foo", "value1")
    repl = attach_to_replication_stream()
    r.run("multi")
    r.run("get", "foo")
    r.run("exec")
    r.run("set", "foo", "value2")
    assert_replication_stream(repl, "            {select *}\n            {set foo value2}\n        ")
    close_replication_stream(repl)


def test_multi_or_exec_is_propagated_correctly_write_command_no_effect(r: ValkeyTestClient) -> None:
    """
    test {MULTI / EXEC is propagated correctly (write command, no effect)} {
        r del bar
        r del foo
        set repl [attach_to_replication_stream]
        r multi
        r del foo
        r exec

        # add another command so that when we see it we know multi-exec wasn't
        # propagated
        r incr foo

        assert_replication_stream $repl {
            {select *}
            {incr foo}
        }
        close_replication_stream $repl
    } {} {needs:repl}
    """
    r.run("del", "bar")
    r.run("del", "foo")
    repl = attach_to_replication_stream()
    r.run("multi")
    r.run("del", "foo")
    r.run("exec")
    r.run("incr", "foo")
    assert_replication_stream(repl, "            {select *}\n            {incr foo}\n        ")
    close_replication_stream(repl)


def test_multi_or_exec_with_replicaof(r: ValkeyTestClient) -> None:
    """
    test {MULTI / EXEC with REPLICAOF} {
        # This test verifies that if we demote a master to replica inside a transaction, the
        # entire transaction is not propagated to the already-connected replica
        set repl [attach_to_replication_stream]
        r set foo bar
        r multi
        r set foo2 bar
        r replicaof localhost 9999
        r set foo3 bar
        r exec
        catch {r set foo4 bar} e
        assert_match {READONLY*} $e
        assert_replication_stream $repl {
            {select *}
            {set foo bar}
        }
        close_replication_stream $repl
        r replicaof no one
    } {OK} {needs:repl cluster:skip}
    """
    repl = attach_to_replication_stream()
    r.run("set", "foo", "bar")
    r.run("multi")
    r.run("set", "foo2", "bar")
    r.run("replicaof", "localhost", 9999)
    r.run("set", "foo3", "bar")
    r.run("exec")
    try:
        e = r.run("set", "foo4", "bar")
    except Exception as _catch_err:
        e = str(_catch_err)
    assert fnmatch(str(e), "READONLY*")
    assert_replication_stream(repl, "            {select *}\n            {set foo bar}\n        ")
    close_replication_stream(repl)
    assert r.run("replicaof", "no", "one") == "OK"


def test_discard_should_not_fail_during_oom(r: ValkeyTestClient) -> None:
    """
    test {DISCARD should not fail during OOM} {
        set rd [valkey_deferring_client]
        $rd config set maxmemory 1
        assert  {[$rd read] eq {OK}}
        r multi
        catch {r set x 1} e
        assert_match {OOM*} $e
        r discard
        $rd config set maxmemory 0
        assert  {[$rd read] eq {OK}}
        $rd close
        r ping
    } {PONG} {needs:config-maxmemory}
    """
    rd = valkey_deferring_client()
    rd.run("config", "set", "maxmemory", 1)
    assert rd.run("read") == "OK"
    r.run("multi")
    try:
        e = r.run("set", "x", 1)
    except Exception as _catch_err:
        e = str(_catch_err)
    assert fnmatch(str(e), "OOM*")
    r.run("discard")
    rd.run("config", "set", "maxmemory", 0)
    assert rd.run("read") == "OK"
    rd.run("close")
    assert r.run("ping") == "PONG"


@pytest.mark.xfail(reason="not implemented")
def test_multi_and_script_timeout(r: ValkeyTestClient) -> None:
    """
    test {MULTI and script timeout} {
        # check that if MULTI arrives during timeout, it is either refused, or
        # allowed to pass, and we don't end up executing half of the transaction
        set rd1 [valkey_deferring_client]
        set r2 [valkey_client]
        r config set lua-time-limit 10
        r set xx 1
        $rd1 eval {while true do end} 0
        after 200
        catch { $r2 multi; } e
        catch { $r2 incr xx; } e
        r script kill
        after 200 ; # Give some time to Lua to call the hook again...
        catch { $r2 incr xx; } e
        catch { $r2 exec; } e
        assert_match {EXECABORT*previous errors*} $e
        set xx [r get xx]
        # make sure that either the whole transaction passed or none of it (we actually expect none)
        assert { $xx == 1 || $xx == 3}
        # check that the connection is no longer in multi state
        set pong [$r2 ping asdf]
        assert_equal $pong "asdf"
        $rd1 close; $r2 close
    }
    """
    rd1 = valkey_deferring_client()
    r2 = valkey_client()
    r.run("config", "set", "lua-time-limit", 10)
    r.run("set", "xx", 1)
    rd1.run("eval", "while true do end", 0)
    time.sleep(200 / 1000)
    catch(" $r2 multi; ", "e")
    catch(" $r2 incr xx; ", "e")
    r.run("script", "kill")
    time.sleep(200 / 1000)
    catch(" $r2 incr xx; ", "e")
    catch(" $r2 exec; ", "e")
    # TODO: assert_match {EXECABORT*previous errors*} e
    xx = r.run("get", "xx")
    assert (xx == 1) or (xx == 3)
    pong = r2.run("ping", "asdf")
    assert pong == "asdf"
    rd1.run("close")
    r2.run("close")


@pytest.mark.xfail(reason="not implemented")
def test_exec_and_script_timeout(r: ValkeyTestClient) -> None:
    """
    test {EXEC and script timeout} {
        # check that if EXEC arrives during timeout, we don't end up executing
        # half of the transaction, and also that we exit the multi state
        set rd1 [valkey_deferring_client]
        set r2 [valkey_client]
        r config set lua-time-limit 10
        r set xx 1
        catch { $r2 multi; } e
        catch { $r2 incr xx; } e
        $rd1 eval {while true do end} 0
        after 200
        catch { $r2 incr xx; } e
        catch { $r2 exec; } e
        assert_match {EXECABORT*BUSY*} $e
        r script kill
        after 200 ; # Give some time to Lua to call the hook again...
        set xx [r get xx]
        # make sure that either the whole transaction passed or none of it (we actually expect none)
        assert { $xx == 1 || $xx == 3}
        # check that the connection is no longer in multi state
        set pong [$r2 ping asdf]
        assert_equal $pong "asdf"
        $rd1 close; $r2 close
    }
    """
    rd1 = valkey_deferring_client()
    r2 = valkey_client()
    r.run("config", "set", "lua-time-limit", 10)
    r.run("set", "xx", 1)
    catch(" $r2 multi; ", "e")
    catch(" $r2 incr xx; ", "e")
    rd1.run("eval", "while true do end", 0)
    time.sleep(200 / 1000)
    catch(" $r2 incr xx; ", "e")
    catch(" $r2 exec; ", "e")
    # TODO: assert_match {EXECABORT*BUSY*} e
    r.run("script", "kill")
    time.sleep(200 / 1000)
    xx = r.run("get", "xx")
    assert (xx == 1) or (xx == 3)
    pong = r2.run("ping", "asdf")
    assert pong == "asdf"
    rd1.run("close")
    r2.run("close")


@pytest.mark.xfail(reason="not implemented")
def test_multi_exec_body_and_script_timeout(r: ValkeyTestClient) -> None:
    """
    test {MULTI-EXEC body and script timeout} {
        # check that we don't run an incomplete transaction due to some commands
        # arriving during busy script
        set rd1 [valkey_deferring_client]
        set r2 [valkey_client]
        r config set lua-time-limit 10
        r set xx 1
        catch { $r2 multi; } e
        catch { $r2 incr xx; } e
        $rd1 eval {while true do end} 0
        after 200
        catch { $r2 incr xx; } e
        r script kill
        after 200 ; # Give some time to Lua to call the hook again...
        catch { $r2 exec; } e
        assert_match {EXECABORT*previous errors*} $e
        set xx [r get xx]
        # make sure that either the whole transaction passed or none of it (we actually expect none)
        assert { $xx == 1 || $xx == 3}
        # check that the connection is no longer in multi state
        set pong [$r2 ping asdf]
        assert_equal $pong "asdf"
        $rd1 close; $r2 close
    }
    """
    rd1 = valkey_deferring_client()
    r2 = valkey_client()
    r.run("config", "set", "lua-time-limit", 10)
    r.run("set", "xx", 1)
    catch(" $r2 multi; ", "e")
    catch(" $r2 incr xx; ", "e")
    rd1.run("eval", "while true do end", 0)
    time.sleep(200 / 1000)
    catch(" $r2 incr xx; ", "e")
    r.run("script", "kill")
    time.sleep(200 / 1000)
    catch(" $r2 exec; ", "e")
    # TODO: assert_match {EXECABORT*previous errors*} e
    xx = r.run("get", "xx")
    assert (xx == 1) or (xx == 3)
    pong = r2.run("ping", "asdf")
    assert pong == "asdf"
    rd1.run("close")
    r2.run("close")


@pytest.mark.xfail(reason="not implemented")
def test_just_exec_and_script_timeout(r: ValkeyTestClient) -> None:
    """
    test {just EXEC and script timeout} {
        # check that if EXEC arrives during timeout, we don't end up executing
        # actual commands during busy script, and also that we exit the multi state
        set rd1 [valkey_deferring_client]
        set r2 [valkey_client]
        r config set lua-time-limit 10
        r set xx 1
        catch { $r2 multi; } e
        catch { $r2 incr xx; } e
        $rd1 eval {while true do end} 0
        after 200
        catch { $r2 exec; } e
        assert_match {EXECABORT*BUSY*} $e
        r script kill
        after 200 ; # Give some time to Lua to call the hook again...
        set xx [r get xx]
        # make we didn't execute the transaction
        assert { $xx == 1}
        # check that the connection is no longer in multi state
        set pong [$r2 ping asdf]
        assert_equal $pong "asdf"
        $rd1 close; $r2 close
    }
    """
    rd1 = valkey_deferring_client()
    r2 = valkey_client()
    r.run("config", "set", "lua-time-limit", 10)
    r.run("set", "xx", 1)
    catch(" $r2 multi; ", "e")
    catch(" $r2 incr xx; ", "e")
    rd1.run("eval", "while true do end", 0)
    time.sleep(200 / 1000)
    catch(" $r2 exec; ", "e")
    # TODO: assert_match {EXECABORT*BUSY*} e
    r.run("script", "kill")
    time.sleep(200 / 1000)
    xx = r.run("get", "xx")
    assert xx == 1
    pong = r2.run("ping", "asdf")
    assert pong == "asdf"
    rd1.run("close")
    r2.run("close")


@pytest.mark.xfail(reason="not implemented")
def test_exec_with_write_commands_and_state_change(r: ValkeyTestClient) -> None:
    """
    test {exec with write commands and state change} {
        # check that exec that contains write commands fails if server state changed since they were queued
        set r1 [valkey_client]
        r set xx 1
        r multi
        r incr xx
        $r1 config set min-replicas-to-write 2
        catch {r exec} e
        assert_match {*EXECABORT*NOREPLICAS*} $e
        set xx [r get xx]
        # make sure that the INCR wasn't executed
        assert { $xx == 1}
        $r1 config set min-replicas-to-write 0
        $r1 close
    } {0} {needs:repl}
    """
    r1 = valkey_client()
    r.run("set", "xx", 1)
    r.run("multi")
    r.run("incr", "xx")
    r1.run("config", "set", "min-replicas-to-write", 2)
    try:
        e = r.run("exec")
    except Exception as _catch_err:
        e = str(_catch_err)
    assert fnmatch(str(e), "*EXECABORT*NOREPLICAS*")
    xx = r.run("get", "xx")
    assert xx == 1
    r1.run("config", "set", "min-replicas-to-write", 0)
    # TODO: $r1 close
    assert False


@pytest.mark.xfail(reason="not implemented")
def test_exec_with_read_commands_and_stale_replica_state_change(r: ValkeyTestClient) -> None:
    """
    test {exec with read commands and stale replica state change} {
        # check that exec that contains read commands fails if server state changed since they were queued
        r config set replica-serve-stale-data no
        set r1 [valkey_client]
        r set xx 1

        # check that GET and PING are disallowed on stale replica, even if the replica becomes stale only after queuing.
        r multi
        r get xx
        $r1 replicaof localhost_ 0
        catch {r exec} e
        assert_match {*EXECABORT*MASTERDOWN*} $e

        # reset
        $r1 replicaof no one

        r multi
        r ping
        $r1 replicaof localhost_ 0
        catch {r exec} e
        assert_match {*EXECABORT*MASTERDOWN*} $e

        # check that when replica is not stale, GET is allowed
        # while we're at it, let's check that multi is allowed on stale replica too
        r multi
        $r1 replicaof no one
        r get xx
        set xx [r exec]
        # make sure that the INCR was executed
        assert { $xx == 1 }
        $r1 close
    } {0} {needs:repl cluster:skip}
    """
    r.run("config", "set", "replica-serve-stale-data", "no")
    r1 = valkey_client()
    r.run("set", "xx", 1)
    r.run("multi")
    r.run("get", "xx")
    r1.run("replicaof", "localhost_", 0)
    try:
        e = r.run("exec")
    except Exception as _catch_err:
        e = str(_catch_err)
    assert fnmatch(str(e), "*EXECABORT*MASTERDOWN*")
    r1.run("replicaof", "no", "one")
    r.run("multi")
    r.run("ping")
    r1.run("replicaof", "localhost_", 0)
    try:
        e = r.run("exec")
    except Exception as _catch_err:
        e = str(_catch_err)
    assert fnmatch(str(e), "*EXECABORT*MASTERDOWN*")
    r.run("multi")
    r1.run("replicaof", "no", "one")
    r.run("get", "xx")
    xx = r.run("exec")
    assert xx == 1
    # TODO: $r1 close
    assert False


@pytest.mark.xfail(reason="not implemented")
def test_exec_with_only_read_commands_should_not_be_rejected_when_oom(r: ValkeyTestClient) -> None:
    """
    test {EXEC with only read commands should not be rejected when OOM} {
        set r2 [valkey_client]

        r set x value
        r multi
        r get x
        r ping

        # enforcing OOM
        $r2 config set maxmemory 1

        # finish the multi transaction with exec
        assert { [r exec] == {value PONG} }

        # releasing OOM
        $r2 config set maxmemory 0
        $r2 close
    } {0} {needs:config-maxmemory}
    """
    r2 = valkey_client()
    r.run("set", "x", "value")
    r.run("multi")
    r.run("get", "x")
    r.run("ping")
    r2.run("config", "set", "maxmemory", 1)
    assert r.run("exec") == "value PONG"
    r2.run("config", "set", "maxmemory", 0)
    # TODO: $r2 close
    assert False


@pytest.mark.xfail(reason="not implemented")
def test_exec_with_at_least_one_use_memory_command_should_fail(r: ValkeyTestClient) -> None:
    """
    test {EXEC with at least one use-memory command should fail} {
        set r2 [valkey_client]

        r multi
        r set x 1
        r get x

        # enforcing OOM
        $r2 config set maxmemory 1

        # finish the multi transaction with exec
        catch {r exec} e
        assert_match {EXECABORT*OOM*} $e

        # releasing OOM
        $r2 config set maxmemory 0
        $r2 close
    } {0} {needs:config-maxmemory}
    """
    r2 = valkey_client()
    r.run("multi")
    r.run("set", "x", 1)
    r.run("get", "x")
    r2.run("config", "set", "maxmemory", 1)
    try:
        e = r.run("exec")
    except Exception as _catch_err:
        e = str(_catch_err)
    assert fnmatch(str(e), "EXECABORT*OOM*")
    r2.run("config", "set", "maxmemory", 0)
    # TODO: $r2 close
    assert False


@pytest.mark.xfail(reason="not implemented")
def test_blocking_commands_ignores_the_timeout(r: ValkeyTestClient) -> None:
    """
    test {Blocking commands ignores the timeout} {
        r xgroup create s{t} g $ MKSTREAM

        set m [r multi]
        r blpop empty_list{t} 0
        r brpop empty_list{t} 0
        r brpoplpush empty_list1{t} empty_list2{t} 0
        r blmove empty_list1{t} empty_list2{t} LEFT LEFT 0
        r bzpopmin empty_zset{t} 0
        r bzpopmax empty_zset{t} 0
        r xread BLOCK 0 STREAMS s{t} $
        r xreadgroup group g c BLOCK 0 STREAMS s{t} >
        set res [r exec]

        list $m $res
    } {OK {{} {} {} {} {} {} {} {}}}
    """
    # TODO: r xgroup create s{t} g  MKSTREAM
    m = r.run("multi")
    r.run("blpop", "empty_list{t}", 0)
    r.run("brpop", "empty_list{t}", 0)
    r.run("brpoplpush", "empty_list1{t}", "empty_list2{t}", 0)
    r.run("blmove", "empty_list1{t}", "empty_list2{t}", "LEFT", "LEFT", 0)
    r.run("bzpopmin", "empty_zset{t}", 0)
    r.run("bzpopmax", "empty_zset{t}", 0)
    # TODO: r xread BLOCK 0 STREAMS s{t}
    r.run("xreadgroup", "group", "g", "c", "BLOCK", 0, "STREAMS", "s{t}", ">")
    res = r.run("exec")
    # TODO: list m res
    assert False


def test_multi_propagation_of_publish(r: ValkeyTestClient) -> None:
    """
    test {MULTI propagation of PUBLISH} {
        set repl [attach_to_replication_stream]

        r multi
        r publish bla bla
        r exec

        assert_replication_stream $repl {
            {select *}
            {publish bla bla}
        }
        close_replication_stream $repl
    } {} {needs:repl cluster:skip}
    """
    repl = attach_to_replication_stream()
    r.run("multi")
    r.run("publish", "bla", "bla")
    r.run("exec")
    assert_replication_stream(repl, "            {select *}\n            {publish bla bla}\n        ")
    close_replication_stream(repl)


def test_multi_propagation_of_script_load(r: ValkeyTestClient) -> None:
    """
    test {MULTI propagation of SCRIPT LOAD} {
        set repl [attach_to_replication_stream]

        # make sure that SCRIPT LOAD inside MULTI isn't propagated
        r multi
        r script load {redis.call('set', KEYS[1], 'foo')}
        r set foo bar
        set res [r exec]
        set sha [lindex $res 0]

        assert_replication_stream $repl {
            {select *}
            {set foo bar}
        }
        close_replication_stream $repl
    } {} {needs:repl}
    """
    repl = attach_to_replication_stream()
    r.run("multi")
    r.run("script", "load", "redis.call('set', KEYS[1], 'foo')")
    r.run("set", "foo", "bar")
    res = r.run("exec")
    sha = res[0]
    assert_replication_stream(repl, "            {select *}\n            {set foo bar}\n        ")
    close_replication_stream(repl)


def test_multi_propagation_of_eval(r: ValkeyTestClient) -> None:
    """
    test {MULTI propagation of EVAL} {
        set repl [attach_to_replication_stream]

        # make sure that EVAL inside MULTI is propagated in a transaction in effects
        r multi
        r eval {redis.call('set', KEYS[1], 'bar')} 1 bar
        r exec

        assert_replication_stream $repl {
            {select *}
            {set bar bar}
        }
        close_replication_stream $repl
    } {} {needs:repl}
    """
    repl = attach_to_replication_stream()
    r.run("multi")
    r.run("eval", "redis.call('set', KEYS[1], 'bar')", 1, "bar")
    r.run("exec")
    assert_replication_stream(repl, "            {select *}\n            {set bar bar}\n        ")
    close_replication_stream(repl)


def test_multi_propagation_of_script_flush(r: ValkeyTestClient) -> None:
    """
    test {MULTI propagation of SCRIPT FLUSH} {
        set repl [attach_to_replication_stream]

        # make sure that SCRIPT FLUSH isn't propagated
        r multi
        r script flush
        r set foo bar
        r exec

        assert_replication_stream $repl {
            {select *}
            {set foo bar}
        }
        close_replication_stream $repl
    } {} {needs:repl}
    """
    repl = attach_to_replication_stream()
    r.run("multi")
    r.run("script", "flush")
    r.run("set", "foo", "bar")
    r.run("exec")
    assert_replication_stream(repl, "            {select *}\n            {set foo bar}\n        ")
    close_replication_stream(repl)


@pytest.mark.parametrize(["cmd"], [("SAVE"), ("SHUTDOWN")])
def test_multi_with_cmd(r: ValkeyTestClient, cmd) -> None:
    """
    test "MULTI with $cmd" {
        r del foo
        r multi
        r set foo bar
        set cmd_lower [string tolower $cmd]
        assert_error "ERR Command '$cmd_lower' not allowed inside a transaction*" {r $cmd}
        assert_error "EXECABORT Transaction discarded because of previous errors*" {r exec}
        assert_equal [r get foo] {}
    }
    """
    r.run("del", "foo")
    r.run("multi")
    r.run("set", "foo", "bar")
    cmd_lower = string("tolower", cmd)
    with pytest.raises(Exception, match="ERR\\ Command\\ '\\$cmd_lower'\\ not\\ allowed\\ inside\\ a\\ transaction.*"):
        r.run(cmd)
    with pytest.raises(Exception, match="EXECABORT\\ Transaction\\ discarded\\ because\\ of\\ previous\\ errors.*"):
        r.run("exec")
    assert r.run("get", "foo") == ""


def test_multi_with_bgrewriteaof(r: ValkeyTestClient) -> None:
    """
    test "MULTI with BGREWRITEAOF" {
        set forks [s total_forks]
        r multi
        r set foo bar
        r BGREWRITEAOF
        set res [r exec]
        assert_match "*rewriting scheduled*" [lindex $res 1]
        wait_for_condition 50 100 {
            [s total_forks] > $forks
        } else {
            fail "aofrw didn't start"
        }
        waitForBgrewriteaof r
    } {} {external:skip}
    """
    forks = s("total_forks")
    r.run("multi")
    r.run("set", "foo", "bar")
    r.run("BGREWRITEAOF")
    res = r.run("exec")
    assert fnmatch(str(res[1]), "*rewriting scheduled*")
    wait_for_condition(
        50,
        100,
        "            [s total_forks] > $forks\n        ",
        "else",
        '            fail "aofrw didn\'t start"\n        ',
    )
    wait_for_bgrewriteaof("r")


def test_multi_with_config_set_appendonly(r: ValkeyTestClient) -> None:
    """
    test "MULTI with config set appendonly" {
        set lines [count_log_lines 0]
        set forks [s total_forks]
        r multi
        r set foo bar
        r config set appendonly yes
        r exec
        verify_log_message 0 "*AOF background was scheduled*" $lines
        wait_for_condition 50 100 {
            [s total_forks] > $forks
        } else {
            fail "aofrw didn't start"
        }
        waitForBgrewriteaof r
    } {} {external:skip}
    """
    lines = count_log_lines(0)
    forks = s("total_forks")
    r.run("multi")
    r.run("set", "foo", "bar")
    r.run("config", "set", "appendonly", "yes")
    r.run("exec")
    verify_log_message(0, "*AOF background was scheduled*", lines)
    wait_for_condition(
        50,
        100,
        "            [s total_forks] > $forks\n        ",
        "else",
        '            fail "aofrw didn\'t start"\n        ',
    )
    wait_for_bgrewriteaof("r")


def test_multi_with_config_error(r: ValkeyTestClient) -> None:
    """
    test "MULTI with config error" {
        r multi
        r set foo bar
        r config set maxmemory bla

        # letting the server parser read it, it'll throw an exception instead of
        # reply with an array that contains an error, so we switch to reading
        # raw RESP instead
        r readraw 1

        set res [r exec]
        assert_equal $res "*2"
        set res [r read]
        assert_equal $res "+OK"
        set res [r read]
        r readraw 0
        set _ $res
    } {*CONFIG SET failed*}
    """
    r.run("multi")
    r.run("set", "foo", "bar")
    r.run("config", "set", "maxmemory", "bla")
    r.run("readraw", 1)
    res = r.run("exec")
    assert res == "*2"
    res = r.run("read")
    assert res == "+OK"
    res = r.run("read")
    r.run("readraw", 0)
    assert res == "*CONFIG SET failed*"


def test_flushall_while_watching_several_keys_by_one_client(r: ValkeyTestClient) -> None:
    """
    test "Flushall while watching several keys by one client" {
        r flushall
        r mset a{t} a b{t} b
        r watch b{t} a{t}
        r flushall
        r ping
        r unwatch
    }
    """
    r.run("flushall")
    r.run("mset", "a{t}", "a", "b{t}", "b")
    r.run("watch", "b{t}", "a{t}")
    r.run("flushall")
    r.run("ping")
    r.run("unwatch")


def test_multi_is_rejected_when_client_reply_is_on_or_off_or_skip(r: ValkeyTestClient) -> None:
    """
    test {MULTI is rejected when CLIENT REPLY is ON/OFF/SKIP} {
        r multi
        assert_error "ERR Command 'client|reply' not allowed inside a transaction" {r client reply on}
        assert_error "EXECABORT *" {r exec}

        r multi
        assert_error "ERR Command 'client|reply' not allowed inside a transaction" {r client reply skip}
        assert_error "EXECABORT *" {r exec}

        r multi
        assert_error "ERR Command 'client|reply' not allowed inside a transaction" {r client reply off}
        assert_error "EXECABORT *" {r exec}

        r client reply on
    }
    """
    r.run("multi")
    with pytest.raises(Exception, match="ERR\\ Command\\ 'client\\|reply'\\ not\\ allowed\\ inside\\ a\\ transaction"):
        r.run("client", "reply", "on")
    with pytest.raises(Exception, match="EXECABORT\\ .*"):
        r.run("exec")
    r.run("multi")
    with pytest.raises(Exception, match="ERR\\ Command\\ 'client\\|reply'\\ not\\ allowed\\ inside\\ a\\ transaction"):
        r.run("client", "reply", "skip")
    with pytest.raises(Exception, match="EXECABORT\\ .*"):
        r.run("exec")
    r.run("multi")
    with pytest.raises(Exception, match="ERR\\ Command\\ 'client\\|reply'\\ not\\ allowed\\ inside\\ a\\ transaction"):
        r.run("client", "reply", "off")
    with pytest.raises(Exception, match="EXECABORT\\ .*"):
        r.run("exec")
    r.run("client", "reply", "on")


def test_client_reply_off_or_skip_multi_command(r: ValkeyTestClient) -> None:
    """
    test "CLIENT REPLY OFF/SKIP: multi command" {
        set rd [valkey_deferring_client]

        # Turning the reply off
        $rd client reply off

        $rd multi
        # These replies were skipped.
        $rd ping pong2
        $rd ping pong3
        $rd exec

        $rd client reply on
        $rd ping
        assert_equal {OK} [$rd read]
        assert_equal {PONG} [$rd read]

        $rd client reply skip

        # Just this command was skipped
        $rd multi

        $rd ping pong2
        $rd ping pong3
        $rd exec
        assert_equal {QUEUED} [$rd read]
        assert_equal {QUEUED} [$rd read]
        assert_equal {pong2 pong3} [$rd read]

        $rd client reply on
        $rd ping
        assert_equal {OK} [$rd read]
        assert_equal {PONG} [$rd read]

        $rd close
    }
    """
    rd = valkey_deferring_client()
    rd.run("client", "reply", "off")
    rd.run("multi")
    rd.run("ping", "pong2")
    rd.run("ping", "pong3")
    rd.run("exec")
    rd.run("client", "reply", "on")
    rd.run("ping")
    assert "OK" == rd.run("read")
    assert "PONG" == rd.run("read")
    rd.run("client", "reply", "skip")
    rd.run("multi")
    rd.run("ping", "pong2")
    rd.run("ping", "pong3")
    rd.run("exec")
    assert "QUEUED" == rd.run("read")
    assert "QUEUED" == rd.run("read")
    assert "pong2 pong3" == rd.run("read")
    rd.run("client", "reply", "on")
    rd.run("ping")
    assert "OK" == rd.run("read")
    assert "PONG" == rd.run("read")
    rd.run("close")


def test_auth_errored_inside_multi_will_add_the_reply(r: ValkeyTestClient) -> None:
    """
    test "AUTH errored inside MULTI will add the reply" {
        r config set requirepass ""
        r multi
        r auth no-user foobar
        assert_error {WRONGPASS invalid username-password pair or user is disabled.} {r exec}
    }
    """
    r.run("config", "set", "requirepass", "")
    r.run("multi")
    r.run("auth", "no-user", "foobar")
    with pytest.raises(
        Exception, match="WRONGPASS\\ invalid\\ username\\-password\\ pair\\ or\\ user\\ is\\ disabled\\."
    ):
        r.run("exec")


pytestmark = [pytest.mark.external_skip]


def test_multi_with_flushall_and_aof(r: ValkeyTestClient) -> None:
    """
    test {MULTI with FLUSHALL and AOF} {
        set aof [get_last_incr_aof_path r]
        r multi
        r set foo bar
        r flushall
        r exec
        assert_aof_content $aof {
            {multi}
            {select *}
            {set *}
            {flushall}
            {exec}
        }
        r get foo
    } {}
    """
    aof = get_last_incr_aof_path("r")
    r.run("multi")
    r.run("set", "foo", "bar")
    r.run("flushall")
    r.run("exec")
    assert_aof_content(
        aof,
        "            {multi}\n            {select *}\n            {set *}\n            {flushall}\n            {exec}\n        ",
    )
    r.run("get", "foo")


"""
start_cluster 1 0 {tags {"external:skip cluster"}} {
    test "Regression test for multi-exec with RANDOMKEY accessing the wrong per-slot dictionary" {
        R 0 SETEX FOO 10000 BAR
        R 0 SETEX FIZZ 10000 BUZZ

        R 0 MULTI
        R 0 DEL FOO
        R 0 RANDOMKEY
        assert_equal [R 0 EXEC] {1 FIZZ}
    }
}
"""


"""
start_cluster 1 0 {tags {"external:skip cluster needs:debug"} overrides {appendonly yes}} {
    test "Regression test for #2995: MULTI/EXEC with different slot keys should not duplicate on AOF reload" {
        R 0 SET k0 a
        R 0 BGREWRITEAOF
        waitForBgrewriteaof [srv 0 client]

        R 0 SET k1 b
        R 0 MULTI
        R 0 SET k0 c
        R 0 APPEND k0 d
        assert_equal [R 0 EXEC] {OK 2}

        R 0 DEBUG LOADAOF

        assert_equal [llength [R 0 KEYS *]] 2
        assert_equal [R 0 GET k0] "cd"
        assert_equal [R 0 GET k1] "b"
    }
}
"""


# --- stubs for unimplemented TCL helpers ---


def assert_aof_content(*args):
    raise NotImplementedError("assert_aof_content")


def assert_replication_stream(*args):
    raise NotImplementedError("assert_replication_stream")


def attach_to_replication_stream(*args):
    raise NotImplementedError("attach_to_replication_stream")


def break_(*args):
    raise NotImplementedError("break_")


def catch(*args):
    raise NotImplementedError("catch")


def close_replication_stream(*args):
    raise NotImplementedError("close_replication_stream")


def count_log_lines(*args):
    raise NotImplementedError("count_log_lines")


def get_last_incr_aof_path(*args):
    raise NotImplementedError("get_last_incr_aof_path")


def if_(*args):
    raise NotImplementedError("if_")


def s(*args):
    raise NotImplementedError("s")


def string(*args):
    raise NotImplementedError("string")


def valkey_client(*args):
    raise NotImplementedError("valkey_client")


def valkey_deferring_client(*args):
    raise NotImplementedError("valkey_deferring_client")


def verify_log_message(*args):
    raise NotImplementedError("verify_log_message")


def wait_for_bgrewriteaof(*args):
    raise NotImplementedError("wait_for_bgrewriteaof")


def wait_for_condition(*args):
    raise NotImplementedError("wait_for_condition")


def wait_for_dbsize(*args):
    raise NotImplementedError("wait_for_dbsize")
