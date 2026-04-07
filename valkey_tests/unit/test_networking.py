# ruff: noqa: PLR2004, F841, ANN002, ANN201
from fnmatch import fnmatch

import pytest

from tests.valkey_test_client import ValkeyTestClient

"""
source tests/support/cli.tcl
"""


"""
test {CONFIG SET port number} {
    start_server {} {
        if {$::tls} { set port_cfg tls-port} else { set port_cfg port }

        # available port
        set avail_port [find_available_port $::baseport $::portcount]
        set rd [valkey [srv 0 host] [srv 0 port] 0 $::tls]
        $rd CONFIG SET $port_cfg $avail_port
        $rd close
        set rd [valkey [srv 0 host] $avail_port 0 $::tls]
        $rd PING

        # already inuse port
        catch {$rd CONFIG SET $port_cfg $::test_server_port} e
        assert_match {*Unable to listen on this port*} $e
        $rd close

        # make sure server still listening on the previous port
        set rd [valkey [srv 0 host] $avail_port 0 $::tls]
        $rd PING
        $rd close
    }
} {} {external:skip}
"""


"""
test {CONFIG SET bind address} {
    start_server {} {
        # non-valid address
        catch {r CONFIG SET bind "999.999.999.999"} e
        assert_match {*Failed to bind to specified addresses*} $e

        # make sure server still bound to the previous address
        set rd [valkey [srv 0 host] [srv 0 port] 0 $::tls]
        $rd PING
        $rd close
    }
} {} {external:skip}
"""


"""
proc test_loopback {host bindaddr timeout} {
    if {[exec uname] != {Linux}} {
        return 0
    }

    after $timeout set ::test_loopback_state timeout
    if {[catch {
        set server_sock [socket -server accept 0]
        set port [lindex [fconfigure $server_sock -sockname] 2] } err]} {
            return 0
    }

    proc accept {channel clientaddr clientport} {
        set ::test_loopback_state "connected"
        close $channel
    }

    if {[catch {set client_sock [socket -async -myaddr $bindaddr $host $port]} err]} {
        puts "test_loopback: Client connect failed: $err"
    } else {
        close $client_sock
    }

    vwait ::test_loopback_state
    close $server_sock

    return [expr {$::test_loopback_state == {connected}}]
}
"""


"""
test {CONFIG SET bind-source-addr} {
    if {[test_loopback 127.0.0.1 127.0.0.2 1000]} {
        start_server {} {
            start_server {} {
                set replica [srv 0 client]
                set master [srv -1 client]

                $master config set protected-mode no

                $replica config set bind-source-addr 127.0.0.2
                $replica replicaof [srv -1 host] [srv -1 port]

                wait_for_condition 50 100 {
                    [s 0 master_link_status] eq {up}
                } else {
                    fail "Replication not started."
                }

                assert_match {*ip=127.0.0.2*} [s -1 slave0]
            }
        }
    } else {
        if {$::verbose} { puts "Skipping bind-source-addr test." }
    }
} {} {external:skip}
"""

pytestmark = [pytest.mark.external_skip]


def test_default_bind_address_configuration_handling(r: ValkeyTestClient) -> None:
    """
    test {Default bind address configuration handling} {
        # Default is explicit and sane
        assert_equal "* -::*" [lindex [r CONFIG GET bind] 1]

        # CONFIG REWRITE acknowledges this as a default
        r CONFIG REWRITE
        assert_equal 0 [count_message_lines [srv 0 config_file] bind]

        # Removing the bind address works
        r CONFIG SET bind ""
        assert_equal "" [lindex [r CONFIG GET bind] 1]

        # No additional clients can connect
        catch {valkey_client} err
        assert_match {*connection refused*} $err

        # CONFIG REWRITE handles empty bindaddr
        r CONFIG REWRITE
        assert_equal 1 [count_message_lines [srv 0 config_file] bind]

        # Make sure we're able to restart
        restart_server 0 0 0 0

        # Make sure bind parameter is as expected and server handles binding
        # accordingly.
        # (it seems that valkeycli_exec behaves differently in RESP3, possibly
        # because CONFIG GET returns a dict instead of a list so valkey-cli emits
        # it in a single line)
        if {$::force_resp3} {
            assert_equal {{bind }} [valkeycli_exec 0 config get bind]
        } else {
            assert_equal {bind {}} [valkeycli_exec 0 config get bind]
        }
        catch {reconnect 0} err
        assert_match {*connection refused*} $err

        assert_equal {OK} [valkeycli_exec 0 config set bind *]
        reconnect 0
        r ping
    } {PONG}
    """
    assert "* -::*" == r.run("CONFIG", "GET", "bind")[1]
    r.run("CONFIG", "REWRITE")
    assert 0 == count_message_lines(srv(0, "config_file"), "bind")
    r.run("CONFIG", "SET", "bind", "")
    assert "" == r.run("CONFIG", "GET", "bind")[1]
    err = None
    try:
        err = valkey_client()
    except Exception as _catch_err:
        err = str(_catch_err)
    assert fnmatch(str(err), "*connection refused*")
    r.run("CONFIG", "REWRITE")
    assert 1 == count_message_lines(srv(0, "config_file"), "bind")
    restart_server(0, 0, 0, 0)
    if_(
        "$::force_resp3",
        "            assert_equal {{bind }} [valkeycli_exec 0 config get bind]\n        ",
        "else",
        "            assert_equal {bind {}} [valkeycli_exec 0 config get bind]\n        ",
    )
    err = None
    try:
        err = reconnect(0)
    except Exception as _catch_err:
        err = str(_catch_err)
    assert fnmatch(str(err), "*connection refused*")
    assert "OK" == valkeycli_exec(0, "config", "set", "bind", "*")
    reconnect(0)
    assert r.run("ping") == "PONG"


def test_protected_mode_works_as_expected(r: ValkeyTestClient) -> None:
    """
    test {Protected mode works as expected} {
        # Get a non-loopback address of this instance for this test.
        set myaddr [get_nonloopback_addr]
        if {$myaddr != "" && ![string match {127.*} $myaddr]} {
            # Non-loopback client should fail by default
            set r2 [get_nonloopback_client]
            catch {$r2 ping} err
            assert_match {*DENIED*} $err
            $r2 close

            # Bind configuration should not matter
            assert_equal {OK} [r config set bind "*"]
            set r2 [get_nonloopback_client]
            catch {$r2 ping} err
            assert_match {*DENIED*} $err
            $r2 close

            # Setting a password should disable protected mode
            assert_equal {OK} [r config set requirepass "secret"]
            set r2 [valkey $myaddr [srv 0 "port"] 0 $::tls]
            assert_equal {OK} [$r2 auth secret]
            assert_equal {PONG} [$r2 ping]
            $r2 close

            # Clearing the password re-enables protected mode
            assert_equal {OK} [r config set requirepass ""]
            set r2 [valkey $myaddr [srv 0 "port"] 0 $::tls]
            assert_match {*DENIED*} $err
            $r2 close

            # Explicitly disabling protected-mode works
            assert_equal {OK} [r config set protected-mode no]
            set r2 [valkey $myaddr [srv 0 "port"] 0 $::tls]
            assert_equal {PONG} [$r2 ping]
            $r2 close
        }
    }
    """
    myaddr = get_nonloopback_addr()
    if_(
        '$myaddr != "" && ![string match {127.*} $myaddr]',
        '            # Non-loopback client should fail by default\n            set r2 [get_nonloopback_client]\n            catch {$r2 ping} err\n            assert_match {*DENIED*} $err\n            $r2 close\n\n            # Bind configuration should not matter\n            assert_equal {OK} [r config set bind "*"]\n            set r2 [get_nonloopback_client]\n            catch {$r2 ping} err\n            assert_match {*DENIED*} $err\n            $r2 close\n\n            # Setting a password should disable protected mode\n            assert_equal {OK} [r config set requirepass "secret"]\n            set r2 [valkey $myaddr [srv 0 "port"] 0 $::tls]\n            assert_equal {OK} [$r2 auth secret]\n            assert_equal {PONG} [$r2 ping]\n            $r2 close\n\n            # Clearing the password re-enables protected mode\n            assert_equal {OK} [r config set requirepass ""]\n            set r2 [valkey $myaddr [srv 0 "port"] 0 $::tls]\n            assert_match {*DENIED*} $err\n            $r2 close\n\n            # Explicitly disabling protected-mode works\n            assert_equal {OK} [r config set protected-mode no]\n            set r2 [valkey $myaddr [srv 0 "port"] 0 $::tls]\n            assert_equal {PONG} [$r2 ping]\n            $r2 close\n        ',
    )


pytestmark = [pytest.mark.external_skip]


"""
set server_pid s process_id
"""


@pytest.mark.xfail(reason="not implemented")
@pytest.mark.skipif("", reason='{[r config get io-threads] ne "io-threads 1"}')
def test_prefetch_works_as_expected_when_killing_a_client_from_the_middle_of_prefetch_commands_batch(
    r: ValkeyTestClient,
) -> None:
    """
    test {prefetch works as expected when killing a client from the middle of prefetch commands batch} {
        # Create 16 (prefetch batch size) +1 clients
        for {set i 0} {$i < 16} {incr i} {
            set rd$i [valkey_deferring_client]
        }

        # set a key that will be later be prefetch
        r set a 0

        # Get the client ID of rd4
        $rd4 client id
        set rd4_id [$rd4 read]

        # Create a batch of commands by suspending the server for a while
        # before responding to the first command
        pause_process $server_pid

        # The first client will kill the fourth client
        $rd0 client kill id $rd4_id

        # Send set commands for all clients except the first
        for {set i 1} {$i < 16} {incr i} {
            [set rd$i] set a $i
            [set rd$i] flush
        }

        # Resume the server
        resume_process $server_pid

        # Read the results
        assert_equal {1} [$rd0 read]
        catch {$rd4 read} err
        assert_match {I/O error reading reply} $err

        # verify the prefetch stats are as expected
        set info [r info stats]
        set prefetch_entries [getInfoProperty $info io_threaded_total_prefetch_entries]
        assert_range $prefetch_entries 2 15; # With slower machines, the number of prefetch entries can be lower
        set prefetch_batches [getInfoProperty $info io_threaded_total_prefetch_batches]
        assert_range $prefetch_batches 1 7; # With slower machines, the number of batches can be higher

        # Verify the final state
        $rd15 get a
        assert_equal {OK} [$rd15 read]
        assert_equal {15} [$rd15 read]
    }
    """
    i = 0
    while i < 16:
        set_("rd$i", ValkeyTestClient.create_from(r))
        i += 1
    r.run("set", "a", 0)
    # TODO: $rd4 client id
    # TODO: set rd4_id $rd4 read
    # TODO: pause_process server_pid
    # TODO: $rd0 client kill id rd4_id
    for_(
        "set i 1",
        "$i < 16",
        "incr i",
        "                [set rd$i] set a $i\n                [set rd$i] flush\n            ",
    )
    # TODO: resume_process server_pid
    # TODO: assert_equal {1} $rd0 read
    catch("$rd4 read", "err")
    # TODO: assert_match {I/O error reading reply} err
    info = r.run("info", "stats")
    prefetch_entries = get_info_property(info, "io_threaded_total_prefetch_entries")
    assert_range(prefetch_entries, 2, 15)
    prefetch_batches = get_info_property(info, "io_threaded_total_prefetch_batches")
    assert_range(prefetch_batches, 1, 7)
    # TODO: $rd15 get a
    # TODO: assert_equal {OK} $rd15 read
    # TODO: assert_equal {15} $rd15 read


@pytest.mark.xfail(reason="not implemented")
@pytest.mark.skipif("", reason='{[r config get io-threads] ne "io-threads 1"}')
def test_prefetch_works_as_expected_when_changing_the_batch_size_while_executing_the_commands_batch(
    r: ValkeyTestClient,
) -> None:
    """
    test {prefetch works as expected when changing the batch size while executing the commands batch} {
        # Create 16 (default prefetch batch size) clients
        for {set i 0} {$i < 16} {incr i} {
            set rd$i [valkey_deferring_client]
        }

        # Create a batch of commands by suspending the server for a while
        # before responding to the first command
        pause_process $server_pid

        # Send set commands for all clients the 5th client will change the prefetch batch size
        for {set i 0} {$i < 16} {incr i} {
            if {$i == 4} {
                [set rd$i] config set prefetch-batch-max-size 1
            }
            [set rd$i] set a $i
            [set rd$i] flush
        }
        # Resume the server
        resume_process $server_pid
        # Read the results
        for {set i 0} {$i < 16} {incr i} {
            assert_equal {OK} [[set rd$i] read]
        }

        # assert the configured prefetch batch size was changed
        assert {[r config get prefetch-batch-max-size] eq "prefetch-batch-max-size 1"}
    }
    """
    i = 0
    while i < 16:
        set_("rd$i", ValkeyTestClient.create_from(r))
        i += 1
    # TODO: pause_process server_pid
    for_(
        "set i 0",
        "$i < 16",
        "incr i",
        "                if {$i == 4} {\n                    [set rd$i] config set prefetch-batch-max-size 1\n                }\n                [set rd$i] set a $i\n                [set rd$i] flush\n            ",
    )
    # TODO: resume_process server_pid
    for_("set i 0", "$i < 16", "incr i", "                assert_equal {OK} [[set rd$i] read]\n            ")
    assert r.run("config", "get", "prefetch-batch-max-size") == "prefetch-batch-max-size 1"


@pytest.mark.xfail(reason="not implemented")
@pytest.mark.skipif("", reason='{[r config get io-threads] ne "io-threads 1"}')
def test_no_prefetch_when_the_batch_size_is_set_to_0(r: ValkeyTestClient) -> None:
    """
    test {no prefetch when the batch size is set to 0} {
        # set the batch size to 0
        r config set prefetch-batch-max-size 0
        # save the current value of prefetch entries
        set info [r info stats]
        set prefetch_entries [getInfoProperty $info io_threaded_total_prefetch_entries]

        # Create 16 (default prefetch batch size) clients
        for {set i 0} {$i < 16} {incr i} {
            set rd$i [valkey_deferring_client]
        }

        # Create a batch of commands by suspending the server for a while
        # before responding to the first command
        pause_process $server_pid

        # Send set commands for all clients
        for {set i 0} {$i < 16} {incr i} {
            [set rd$i] set a $i
            [set rd$i] flush
        }

        # Resume the server
        resume_process $server_pid

        # Read the results
        for {set i 0} {$i < 16} {incr i} {
            assert_equal {OK} [[set rd$i] read]
        }

        # assert the prefetch entries did not change
        set info [r info stats]
        set new_prefetch_entries [getInfoProperty $info io_threaded_total_prefetch_entries]
        assert_equal $prefetch_entries $new_prefetch_entries
    }
    """
    r.run("config", "set", "prefetch-batch-max-size", 0)
    info = r.run("info", "stats")
    prefetch_entries = get_info_property(info, "io_threaded_total_prefetch_entries")
    i = 0
    while i < 16:
        set_("rd$i", ValkeyTestClient.create_from(r))
        i += 1
    # TODO: pause_process server_pid
    for_(
        "set i 0",
        "$i < 16",
        "incr i",
        "                [set rd$i] set a $i\n                [set rd$i] flush\n            ",
    )
    # TODO: resume_process server_pid
    for_("set i 0", "$i < 16", "incr i", "                assert_equal {OK} [[set rd$i] read]\n            ")
    info = r.run("info", "stats")
    new_prefetch_entries = get_info_property(info, "io_threaded_total_prefetch_entries")
    assert prefetch_entries == new_prefetch_entries


"""
start_server {} {
    test {replicas writes are offloaded to IO threads} {
        set primary [srv -1 client]
        set primary_host [srv -1 host]
        set primary_port [srv -1 port]

        set replica [srv 0 client]
        $replica replicaof $primary_host $primary_port

        wait_for_condition 500 100 {
            [s 0 master_link_status] eq {up}
        } else {
            fail "Replication not started."
        }

        # get the current io_threaded_writes_processed
        set info [$primary info stats]
        set io_threaded_writes_processed [getInfoProperty $info io_threaded_writes_processed]

        # Send a write command to the primary
        $primary set a 1

        # Wait for the write to be propagated to the replica
        wait_for_condition 50 100 {
            [$replica get a] eq {1}
        } else {
            fail "Replication not propagated."
        }

        # Get the new io_threaded_writes_processed
        set info [$primary info stats]
        set new_io_threaded_writes_processed [getInfoProperty $info io_threaded_writes_processed]
        # Assert new is old + 3, 3 for the write to the info-client, set-client and to the replica.
        assert {$new_io_threaded_writes_processed >= $io_threaded_writes_processed + 3} ;

        # Verify the write was propagated to the replica
        assert_equal {1} [$replica get a]
    }
}
"""


# --- stubs for unimplemented TCL helpers ---


def assert_range(*args):
    raise NotImplementedError("assert_range")


def catch(*args):
    raise NotImplementedError("catch")


def count_message_lines(*args):
    raise NotImplementedError("count_message_lines")


def for_(*args):
    raise NotImplementedError("for_")


def get_info_property(*args):
    raise NotImplementedError("get_info_property")


def get_nonloopback_addr(*args):
    raise NotImplementedError("get_nonloopback_addr")


def if_(*args):
    raise NotImplementedError("if_")


def reconnect(*args):
    raise NotImplementedError("reconnect")


def restart_server(*args):
    raise NotImplementedError("restart_server")


def set_(*args):
    raise NotImplementedError("set_")


def srv(*args):
    raise NotImplementedError("srv")


def valkey_client(*args):
    raise NotImplementedError("valkey_client")


def valkeycli_exec(*args):
    raise NotImplementedError("valkeycli_exec")
