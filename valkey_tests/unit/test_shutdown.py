# ruff: noqa: PLR2004, F841, ANN002, ANN201
import time
from fnmatch import fnmatch

import pytest

from tests.valkey_test_client import ValkeyTestClient

pytestmark = [pytest.mark.shutdown_external_skip]


def test_temp_rdb_will_be_deleted_if_we_use_bg_unlink_when_shutdown(r: ValkeyTestClient) -> None:
    """
    test {Temp rdb will be deleted if we use bg_unlink when shutdown} {
        for {set i 0} {$i < 20} {incr i} {
            r set $i $i
        }
        r config set rdb-key-save-delay 10000000

        # Child is dumping rdb
        r bgsave
        wait_for_condition 1000 10 {
            [s rdb_bgsave_in_progress] eq 1
        } else {
            fail "bgsave did not start in time"
        }
        after 100 ;# give the child a bit of time for the file to be created

        set dir [lindex [r config get dir] 1]
        set child_pid [get_child_pid 0]
        set temp_rdb [file join [lindex [r config get dir] 1] temp-${child_pid}.rdb]
        # Temp rdb must be existed
        assert {[file exists $temp_rdb]}

        catch {r shutdown nosave}
        # Make sure the server was killed
        catch {set rd [valkey_deferring_client]} e
        assert_match {*connection refused*} $e

        # Temp rdb file must be deleted
        assert {![file exists $temp_rdb]}
    }
    """
    i = 0
    while i < 20:
        r.run("set", i, i)
        i += 1
    r.run("config", "set", "rdb-key-save-delay", 10000000)
    r.run("bgsave")
    wait_for_condition(1000, 10, lambda: s("rdb_bgsave_in_progress") == 1, lambda: fail("bgsave did not start in time"))
    time.sleep(100 / 1000)
    dir = r.run("config", "get", "dir")[1]
    child_pid = get_child_pid(0)
    temp_rdb = file("join", r.run("config", "get", "dir")[1], "temp-${child_pid}.rdb")
    assert file("exists", temp_rdb)
    try:
        r.run("shutdown", "nosave")
    except Exception:
        pass
    try:
        e = ValkeyTestClient.create_from(r)
    except Exception as _catch_err:
        e = str(_catch_err)
    assert fnmatch(str(e), "*connection refused*")
    assert_("![file exists $temp_rdb]")


pytestmark = [pytest.mark.shutdown_external_skip]


def test_shutdown_abort_can_cancel_sigterm(r: ValkeyTestClient) -> None:
    """
    test {SHUTDOWN ABORT can cancel SIGTERM} {
        r debug pause-cron 1
        set pid [s process_id]
        exec kill -SIGTERM $pid
        after 10;               # Give signal handler some time to run
        r shutdown abort
        verify_log_message 0 "*Shutdown manually aborted*" 0
        r debug pause-cron 0
        r ping
    } {PONG}
    """
    r.run("debug", "pause-cron", 1)
    pid = s("process_id")
    exec_("kill", "-SIGTERM", pid)
    time.sleep(10 / 1000)
    r.run("shutdown", "abort")
    verify_log_message(0, "*Shutdown manually aborted*", 0)
    r.run("debug", "pause-cron", 0)
    assert r.run("ping") == "PONG"


def test_temp_rdb_will_be_deleted_in_signal_handle(r: ValkeyTestClient) -> None:
    """
    test {Temp rdb will be deleted in signal handle} {
        for {set i 0} {$i < 20} {incr i} {
            r set $i $i
        }
        # It will cost 2s (20 * 100ms) to dump rdb
        r config set rdb-key-save-delay 100000

        set pid [s process_id]
        set temp_rdb [file join [lindex [r config get dir] 1] temp-${pid}.rdb]

        # trigger a shutdown which will save an rdb
        exec kill -SIGINT $pid
        # Wait for creation of temp rdb
        wait_for_condition 50 10 {
            [file exists $temp_rdb]
        } else {
            fail "Can't trigger rdb save on shutdown"
        }

        # Insist on immediate shutdown, temp rdb file must be deleted
        exec kill -SIGINT $pid
        # wait for the rdb file to be deleted
        wait_for_condition 50 10 {
            ![file exists $temp_rdb]
        } else {
            fail "Can't delete rdb temp file on shutdown"
        }
    }
    """
    i = 0
    while i < 20:
        r.run("set", i, i)
        i += 1
    r.run("config", "set", "rdb-key-save-delay", 100000)
    pid = s("process_id")
    temp_rdb = file("join", r.run("config", "get", "dir")[1], "temp-${pid}.rdb")
    exec_("kill", "-SIGINT", pid)
    wait_for_condition(50, 10, lambda: file("exists", temp_rdb), lambda: fail("Can't trigger rdb save on shutdown"))
    exec_("kill", "-SIGINT", pid)
    wait_for_condition(
        50,
        10,
        "            ![file exists $temp_rdb]\n        ",
        "else",
        '            fail "Can\'t delete rdb temp file on shutdown"\n        ',
    )


pytestmark = [pytest.mark.shutdown_external_skip]


"""
set pid s process_id
"""


"""
set dump_rdb file join [lindex [r config get dir] 1] dump.rdb
"""


@pytest.mark.xfail(reason="not implemented")
def test_rdb_save_will_be_failed_in_shutdown(r: ValkeyTestClient) -> None:
    """
    test {RDB save will be failed in shutdown} {
        for {set i 0} {$i < 20} {incr i} {
            r set $i $i
        }

        # create a folder called 'dump.rdb' to trigger temp-rdb rename failure
        # and it will cause rdb save to fail eventually.
        if {[file exists $dump_rdb]} {
            exec rm -f $dump_rdb
        }
        exec mkdir -p $dump_rdb
    }
    """
    i = 0
    while i < 20:
        r.run("set", i, i)
        i += 1
    if_("[file exists $dump_rdb]", "            exec rm -f $dump_rdb\n        ")
    # TODO: exec mkdir -p dump_rdb


@pytest.mark.xfail(reason="not implemented")
def test_shutdown_will_abort_if_rdb_save_failed_on_signal(r: ValkeyTestClient) -> None:
    """
    test {SHUTDOWN will abort if rdb save failed on signal} {
        # trigger a shutdown which will save an rdb
        exec kill -SIGINT $pid
        wait_for_log_messages 0 {"*Error trying to save the DB, can't exit*"} 0 100 10
    }
    """
    # TODO: exec kill -SIGINT pid
    wait_for_log_messages(0, '"*Error trying to save the DB, can\'t exit*"', 0, 100, 10)


@pytest.mark.xfail(reason="not implemented")
def test_shutdown_will_abort_if_rdb_save_failed_on_shutdown_command(r: ValkeyTestClient) -> None:
    """
    test {SHUTDOWN will abort if rdb save failed on shutdown command} {
        catch {[r shutdown]} err
        assert_match {*Errors trying to SHUTDOWN*} $err
        # make sure the server is still alive
        assert_equal [r ping] {PONG}
    }
    """
    catch("[r shutdown]", "err")
    # TODO: assert_match {*Errors trying to SHUTDOWN*} err
    assert r.run("ping") == "PONG"


def test_shutdown_can_proceed_if_shutdown_command_was_with_nosave(r: ValkeyTestClient) -> None:
    """
    test {SHUTDOWN can proceed if shutdown command was with nosave} {
        catch {[r shutdown nosave]}
        wait_for_log_messages 0 {"*ready to exit, bye bye*"} 0 100 10
    }
    """
    catch("[r shutdown nosave]")
    wait_for_log_messages(0, '"*ready to exit, bye bye*"', 0, 100, 10)


@pytest.mark.xfail(reason="not implemented")
def test_clean_up_rdb_same_named_folder(r: ValkeyTestClient) -> None:
    """
    test {Clean up rdb same named folder} {
        exec rm -r $dump_rdb
    }
    """
    # TODO: exec rm -r dump_rdb


pytestmark = [pytest.mark.shutdown_external_skip]


def test_shutdown_sigterm_will_abort_if_there_s_an_initial_aofrw_default(r: ValkeyTestClient) -> None:
    """
    test {SHUTDOWN SIGTERM will abort if there's an initial AOFRW - default} {
        r config set shutdown-on-sigterm default
        r config set rdb-key-save-delay 10000000
        for {set i 0} {$i < 10} {incr i} {
            r set $i $i
        }

        r config set appendonly yes
        wait_for_condition 1000 10 {
            [s aof_rewrite_in_progress] eq 1
        } else {
            fail "aof rewrite did not start in time"
        }

        set pid [s process_id]
        exec kill -SIGTERM $pid
        wait_for_log_messages 0 {"*Writing initial AOF, can't exit*"} 0 1000 10

        r config set shutdown-on-sigterm force
    }
    """
    r.run("config", "set", "shutdown-on-sigterm", "default")
    r.run("config", "set", "rdb-key-save-delay", 10000000)
    i = 0
    while i < 10:
        r.run("set", i, i)
        i += 1
    r.run("config", "set", "appendonly", "yes")
    wait_for_condition(
        1000, 10, lambda: s("aof_rewrite_in_progress") == 1, lambda: fail("aof rewrite did not start in time")
    )
    pid = s("process_id")
    exec_("kill", "-SIGTERM", pid)
    wait_for_log_messages(0, '"*Writing initial AOF, can\'t exit*"', 0, 1000, 10)
    r.run("config", "set", "shutdown-on-sigterm", "force")


# --- stubs for unimplemented TCL helpers ---


def assert_(*args):
    raise NotImplementedError("assert_")


def catch(*args):
    raise NotImplementedError("catch")


def exec_(*args):
    raise NotImplementedError("exec_")


def fail(*args):
    raise NotImplementedError("fail")


def file(*args):
    raise NotImplementedError("file")


def get_child_pid(*args):
    raise NotImplementedError("get_child_pid")


def if_(*args):
    raise NotImplementedError("if_")


def s(*args):
    raise NotImplementedError("s")


def verify_log_message(*args):
    raise NotImplementedError("verify_log_message")


def wait_for_condition(*args):
    raise NotImplementedError("wait_for_condition")


def wait_for_log_messages(*args):
    raise NotImplementedError("wait_for_log_messages")
