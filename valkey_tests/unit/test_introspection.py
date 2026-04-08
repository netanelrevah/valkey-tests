# ruff: noqa: PLR2004, F841, RUF043, ANN001, ANN002, ANN201
import time
from fnmatch import fnmatch

import pytest

from tests.valkey_test_client import ValkeyTestClient

pytestmark = [pytest.mark.introspection]


def test_ping(r: ValkeyTestClient) -> None:
    """
    test "PING" {
        assert_equal {PONG} [r ping]
        assert_equal {valkey} [r ping valkey]
        assert_error {*wrong number of arguments for 'ping' command} {r ping hello valkey}
    }
    """
    assert "PONG" == r.run("ping")
    assert "valkey" == r.run("ping", "valkey")
    with pytest.raises(Exception, match=".*wrong\\ number\\ of\\ arguments\\ for\\ 'ping'\\ command"):
        r.run("ping", "hello", "valkey")


def test_client_list(r: ValkeyTestClient) -> None:
    """
    test {CLIENT LIST} {
        r client list
    } {id=* addr=*:* laddr=*:* fd=* name=* age=* idle=* flags=N capa= db=* sub=0 psub=0 ssub=0 multi=-1 watch=0 qbuf=0 qbuf-free=* argv-mem=* multi-mem=0 rbs=* rbp=* obl=0 oll=0 omem=0 tot-mem=* events=r cmd=client|list user=* redir=-1 resp=* lib-name=* lib-ver=* tot-net-in=* tot-net-out=* tot-cmds=*}
    """
    assert fnmatch(
        str(r.run("client", "list")),
        "id=* addr=*:* laddr=*:* fd=* name=* age=* idle=* flags=N capa= db=* sub=0 psub=0 ssub=0 multi=-1 watch=0 qbuf=0 qbuf-free=* argv-mem=* multi-mem=0 rbs=* rbp=* obl=0 oll=0 omem=0 tot-mem=* events=r cmd=client|list user=* redir=-1 resp=* lib-name=* lib-ver=* tot-net-in=* tot-net-out=* tot-cmds=*",
    )


def test_client_list_with_ids(r: ValkeyTestClient) -> None:
    """
    test {CLIENT LIST with IDs} {
        set myid [r client id]
        set cl [split [r client list id $myid] "\r\n"]
        assert_match "id=$myid * cmd=client|list *" [lindex $cl 0]
    }
    """
    myid = r.run("client", "id")
    cl = split(r.run("client", "list", "id", myid), "\r\n")
    assert fnmatch(str(cl[0]), str(f"id={myid} * cmd=client|list *"))


def test_client_info(r: ValkeyTestClient) -> None:
    """
    test {CLIENT INFO} {
        r client info
    } {id=* addr=*:* laddr=*:* fd=* name=* age=* idle=* flags=N capa= db=* sub=0 psub=0 ssub=0 multi=-1 watch=0 qbuf=0 qbuf-free=* argv-mem=* multi-mem=0 rbs=* rbp=* obl=0 oll=0 omem=0 tot-mem=* events=r cmd=client|info user=* redir=-1 resp=* lib-name=* lib-ver=* tot-net-in=* tot-net-out=* tot-cmds=*}
    """
    assert fnmatch(
        str(r.run("client", "info")),
        "id=* addr=*:* laddr=*:* fd=* name=* age=* idle=* flags=N capa= db=* sub=0 psub=0 ssub=0 multi=-1 watch=0 qbuf=0 qbuf-free=* argv-mem=* multi-mem=0 rbs=* rbp=* obl=0 oll=0 omem=0 tot-mem=* events=r cmd=client|info user=* redir=-1 resp=* lib-name=* lib-ver=* tot-net-in=* tot-net-out=* tot-cmds=*",
    )


@pytest.mark.xfail(reason="not implemented")
def test_client_list_with_addr_filter(r: ValkeyTestClient) -> None:
    """
    test {CLIENT LIST with ADDR filter} {
        set client_info [r client info]
        regexp {addr=([^ ]+)} $client_info match myaddr
        set cl [split [r client list addr $myaddr] "\r\n"]
        regexp {addr=([^ ]+) .* cmd=([^ ]+)} [lindex $cl 0] _ actual_addr actual_cmd
        assert_equal $myaddr $actual_addr
        assert_equal "client|list" $actual_cmd
    }
    """
    client_info = r.run("client", "info")
    regexp("addr=([^ ]+)", client_info, "match", "myaddr")
    # TODO: set cl split [r client list addr $myaddr] "\r\n"
    # TODO: regexp {addr=([^ ]+) .* cmd=([^ ]+)} lindex $cl 0 _ actual_addr actual_cmd
    # TODO: assert_equal myaddr actual_addr
    # TODO: assert_equal "client|list" actual_cmd


@pytest.mark.xfail(reason="not implemented")
def test_client_list_with_laddr_filter(r: ValkeyTestClient) -> None:
    """
    test {CLIENT LIST with LADDR filter} {
        set client_info [r client info]
        regexp {laddr=([^ ]+)} $client_info match myladdr
        set cl [split [r client list laddr $myladdr] "\r\n"]

        regexp {laddr=([^ ]+)} [lindex $cl 0] _ actual_laddr

        assert_equal $myladdr $actual_laddr
    }
    """
    client_info = r.run("client", "info")
    regexp("laddr=([^ ]+)", client_info, "match", "myladdr")
    # TODO: set cl split [r client list laddr $myladdr] "\r\n"
    # TODO: regexp {laddr=([^ ]+)} lindex $cl 0 _ actual_laddr
    # TODO: assert_equal myladdr actual_laddr


def test_client_list_with_maxage_filter(r: ValkeyTestClient) -> None:
    """
    test {CLIENT LIST with MAXAGE filter} {
        set cl [split [r client list maxage 1000000] "\r\n"]

        foreach line $cl {
            regexp {age=([0-9]+)} $line _ age
            assert {[expr {$age <= 1000000}]}
        }
    }
    """
    cl = split(r.run("client", "list", "maxage", 1000000), "\r\n")
    foreach(
        "line",
        cl,
        "            regexp {age=([0-9]+)} $line _ age\n            assert {[expr {$age <= 1000000}]}\n        ",
    )


def test_client_list_with_type_filter(r: ValkeyTestClient) -> None:
    """
    test {CLIENT LIST with TYPE filter} {
        set cl [split [r client list type normal] "\r\n"]

        foreach line $cl {
            regexp {flags=([^ ]+)} $line _ flags
            assert [regexp {.*N.*} $flags]
        }
    }
    """
    cl = split(r.run("client", "list", "type", "normal"), "\r\n")
    foreach(
        "line",
        cl,
        "            regexp {flags=([^ ]+)} $line _ flags\n            assert [regexp {.*N.*} $flags]\n        ",
    )


@pytest.mark.xfail(reason="not implemented")
def test_client_list_with_user_filter(r: ValkeyTestClient) -> None:
    """
    test {CLIENT LIST with USER filter} {
        set client_info [r client info]
        regexp {user=([^ ]+)} $client_info match myuser
        set cl [split [r client list user $myuser] "\r\n"]

        foreach line $cl {
            regexp {user=([^ ]+)} $line _ actual_user
            assert_equal $myuser $actual_user
        }
    }
    """
    client_info = r.run("client", "info")
    regexp("user=([^ ]+)", client_info, "match", "myuser")
    # TODO: set cl split [r client list user $myuser] "\r\n"
    # TODO: foreach line cl {
    #       regexp {user=([^ ]+)} $line _ actual_user
    #       assert_equal $myuser $actual_user
    #   }


def test_client_list_with_skipme_filter(r: ValkeyTestClient) -> None:
    """
    test {CLIENT LIST with SKIPME filter} {
        set cl [split [r client list skipme no] "\r\n"]

        set found_self 0
        foreach line $cl {
            regexp {id=([0-9]+)} $line _ client_id
            if {[expr {$client_id == [r client id]}]} {
                set found_self 1
            }
        }

        assert_equal $found_self 1
    }
    """
    cl = split(r.run("client", "list", "skipme", "no"), "\r\n")
    found_self = 0
    foreach(
        "line",
        cl,
        "            regexp {id=([0-9]+)} $line _ client_id\n            if {[expr {$client_id == [r client id]}]} {\n                set found_self 1\n            }\n        ",
    )
    assert found_self == 1


def test_client_list_with_multiple_ids_and_type_filter(r: ValkeyTestClient) -> None:
    """
    test {CLIENT LIST with multiple IDs and TYPE filter} {
        # Create multiple clients
        set c1 [valkey_client]
        set c2 [valkey_client]
        set c3 [valkey_client]

        # Fetch their IDs
        set id1 [$c1 client id]
        set id2 [$c2 client id]
        set id3 [$c3 client id]

        # Filter by multiple IDs and TYPE
        set cl [split [r client list id $id1 $id2 type normal] "\r\n"]

        # Assert only c1 and c2 are present and match TYPE=N (NORMAL)
        foreach line $cl {
            regexp {id=([0-9]+).*flags=([^ ]+)} $line _ client_id flags
            assert {[lsearch -exact "$id1 $id2" $client_id] != -1}
            assert {[string match *N* $flags]}
        }

        # Close clients
        $c1 close
        $c2 close
        $c3 close
    }
    """
    c1 = ValkeyTestClient.create_from(r)
    c2 = ValkeyTestClient.create_from(r)
    c3 = ValkeyTestClient.create_from(r)
    id1 = c1.run("client", "id")
    id2 = c2.run("client", "id")
    id3 = c3.run("client", "id")
    cl = split(r.run("client", "list", "id", id1, id2, "type", "normal"), "\r\n")
    foreach(
        "line",
        cl,
        '            regexp {id=([0-9]+).*flags=([^ ]+)} $line _ client_id flags\n            assert {[lsearch -exact "$id1 $id2" $client_id] != -1}\n            assert {[string match *N* $flags]}\n        ',
    )
    c1.run("close")
    c2.run("close")
    c3.run("close")


def test_client_list_with_filters_matching_no_clients(r: ValkeyTestClient) -> None:
    """
    test {CLIENT LIST with filters matching no clients} {
        # Create multiple clients
        set c1 [valkey_client]
        set c2 [valkey_client]

        # Use a filter that doesn't match any client (e.g., invalid user)
        assert_error "ERR No such user 'invalid_user'" {r client list user invalid_user}

        # Close clients
        $c1 close
        $c2 close
    }
    """
    c1 = ValkeyTestClient.create_from(r)
    c2 = ValkeyTestClient.create_from(r)
    with pytest.raises(Exception, match="ERR\\ No\\ such\\ user\\ 'invalid_user'"):
        r.run("client", "list", "user", "invalid_user")
    c1.run("close")
    c2.run("close")


@pytest.mark.xfail(reason="not implemented")
def test_client_list_with_name_filter(r: ValkeyTestClient) -> None:
    """
    test {CLIENT LIST with NAME filter} {
        r client setname mytestclient
        set client_info [r client info]
        regexp {name=([^ ]+)} $client_info match myname
        set cl [split [r client list name $myname] "\r\n"]
        regexp {name=([^ ]+) .* cmd=([^ ]+)} [lindex $cl 0] _ actual_name actual_cmd
        assert_equal $myname $actual_name
        assert_equal "client|list" $actual_cmd
    }
    """
    r.run("client", "setname", "mytestclient")
    client_info = r.run("client", "info")
    regexp("name=([^ ]+)", client_info, "match", "myname")
    # TODO: set cl split [r client list name $myname] "\r\n"
    # TODO: regexp {name=([^ ]+) .* cmd=([^ ]+)} lindex $cl 0 _ actual_name actual_cmd
    # TODO: assert_equal myname actual_name
    # TODO: assert_equal "client|list" actual_cmd


def test_client_list_with_flags_filter(r: ValkeyTestClient) -> None:
    """
    test {CLIENT LIST with FLAGS filter} {
        r client setname mytestclient
        set cl [split [r client list flags N] "\r\n"]
        set line [lindex $cl 0]
        set info [dict create]
        foreach pair [split $line " "] {
            lassign [split $pair "="] key val
            dict set info $key $val
        }
        assert_equal "N" [dict get $info flags]
    }
    """
    r.run("client", "setname", "mytestclient")
    cl = split(r.run("client", "list", "flags", "N"), "\r\n")
    line = cl[0]
    info = dict_("create")
    foreach(
        "pair",
        split(line, " "),
        '            lassign [split $pair "="] key val\n            dict set info $key $val\n        ',
    )
    assert "N" == info["flags"]


def test_client_list_with_type_filter_1(r: ValkeyTestClient) -> None:
    """
    test {CLIENT LIST with TYPE filter} {
        set cl [split [r client list type normal] "\r\n"]
        set line [lindex $cl 0]
        set info [dict create]
        foreach pair [split $line " "] {
            lassign [split $pair "="] key val
            dict set info $key $val
        }
        assert {[string match *N* [dict get $info flags]]}
    }
    """
    cl = split(r.run("client", "list", "type", "normal"), "\r\n")
    line = cl[0]
    info = dict_("create")
    foreach(
        "pair",
        split(line, " "),
        '            lassign [split $pair "="] key val\n            dict set info $key $val\n        ',
    )
    assert string("match", "*N*", info["flags"])


@pytest.mark.xfail(reason="not implemented")
def test_client_list_with_multiple_filters(r: ValkeyTestClient) -> None:
    """
    test {CLIENT LIST with multiple filters} {
        r client setname mytestclient
        set client_info [r client info]
        set fields [split $client_info " "]
        foreach pair $fields {
            lassign [split $pair "="] key val
            if {$key eq "id"} { set myid $val }
            if {$key eq "name"} { set myname $val }
        }

        set cl [split [r client list id $myid name $myname] "\r\n"]
        set line [lindex $cl 0]
        set info [dict create]
        foreach pair [split $line " "] {
            lassign [split $pair "="] key val
            dict set info $key $val
        }

        assert_equal $myid [dict get $info id]
        assert_equal $myname [dict get $info name]
        assert_equal "client|list" [dict get $info cmd]
    }
    """
    r.run("client", "setname", "mytestclient")
    client_info = r.run("client", "info")
    fields = split(client_info, " ")
    foreach(
        "pair",
        fields,
        '            lassign [split $pair "="] key val\n            if {$key eq "id"} { set myid $val }\n            if {$key eq "name"} { set myname $val }\n        ',
    )
    # TODO: set cl split [r client list id $myid name $myname] "\r\n"
    # TODO: set line lindex $cl 0
    info = dict_("create")
    # TODO: foreach pair split $line " " {
    #       lassign [split $pair "="] key val
    #       dict set info $key $val
    #   }
    # TODO: assert_equal myid dict get $info id
    # TODO: assert_equal myname dict get $info name
    assert "client|list" == info["cmd"]


def test_client_list_with_multiple_filters_1(r: ValkeyTestClient) -> None:
    """
    test {CLIENT LIST with multiple filters} {
        # Create multiple clients with different names and flags
        set c1 [valkey_client]
        set c2 [valkey_client]
        set c3 [valkey_client]
        $c1 client setname client1
        $c2 client setname client1
        $c3 client setname client2
        $c3 multi

        # Wait 1 second to ensure idle time
        after 1000

        # Fetch the client list filtered by name and flags
        set cl [split [r client list name client1 flags N] "\r\n"]

        # Assert the clients returned match the filters
        foreach line $cl {
            regexp {name=([^ ]+) .* flags=([^ ]+)} $line _ actual_name flags
            assert {[string match *client1* $actual_name] || [string match *client2* $actual_name]}
            assert {[string match *N* $flags]}
        }

        # Test error when inputting an invalid flag/s
        assert_error "ERR Unknown flags found in the provided filter: Q" {r client list name client1 flags Q}
        assert_error "ERR Unknown flags found in the provided filter: NZ" {r client list name client1 flags NZ}

        # Close clients
        $c1 close
        $c2 close
        $c3 close
    }
    """
    c1 = ValkeyTestClient.create_from(r)
    c2 = ValkeyTestClient.create_from(r)
    c3 = ValkeyTestClient.create_from(r)
    c1.run("client", "setname", "client1")
    c2.run("client", "setname", "client1")
    c3.run("client", "setname", "client2")
    c3.run("multi")
    time.sleep(1000 / 1000)
    cl = split(r.run("client", "list", "name", "client1", "flags", "N"), "\r\n")
    foreach(
        "line",
        cl,
        "            regexp {name=([^ ]+) .* flags=([^ ]+)} $line _ actual_name flags\n            assert {[string match *client1* $actual_name] || [string match *client2* $actual_name]}\n            assert {[string match *N* $flags]}\n        ",
    )
    with pytest.raises(Exception, match="ERR\\ Unknown\\ flags\\ found\\ in\\ the\\ provided\\ filter:\\ Q"):
        r.run("client", "list", "name", "client1", "flags", "Q")
    with pytest.raises(Exception, match="ERR\\ Unknown\\ flags\\ found\\ in\\ the\\ provided\\ filter:\\ NZ"):
        r.run("client", "list", "name", "client1", "flags", "NZ")
    c1.run("close")
    c2.run("close")
    c3.run("close")


@pytest.mark.xfail(reason="not implemented")
def test_client_list_with_ip_filter(r: ValkeyTestClient) -> None:
    """
    test {CLIENT LIST with IP filter} {
        r client setname "client-ip"

        set client_info [r client info]
        regexp {addr=([^:]+):} $client_info -> iponly

        # Use the extracted IP for filtering.
        set filtered [r client list ip $iponly ip $iponly]
        assert_match *client-ip* $filtered
    } {}
    """
    r.run("client", "setname", "client-ip")
    client_info = r.run("client", "info")
    regexp("addr=([^:]+):", client_info, "->", "iponly")
    # TODO: set filtered r client list ip $iponly ip $iponly
    # TODO: assert_match *client-ip* filtered


"""
start_server {tags {"ipv6"} overrides {bind {127.0.0.1 ::1}}} {
    test {CLIENT LIST with IPv6 filter} {
        set c [valkey ::1 [srv 0 port] 0 $::tls]
        $c client setname "client-ipv6"

        set client_info [$c client info]

        regexp {addr=\[([a-fA-F0-9:]+)\]:\d+} $client_info -> ipv6only
        set filtered [$c client list ip $ipv6only]
        assert_match *client-ipv6* $filtered

        $c close
    }
}
"""


def test_client_list_with_capa_filter(r: ValkeyTestClient) -> None:
    """
    test {CLIENT LIST with CAPA filter} {
        set c1 [valkey_client]
        $c1 client setname "client-with-r"
        $c1 client capa redirect

        set output [r client list capa r capa r]
        assert_match *client-with-r* $output
        catch {$c1 close}
    }
    """
    c1 = ValkeyTestClient.create_from(r)
    c1.run("client", "setname", "client-with-r")
    c1.run("client", "capa", "redirect")
    output = r.run("client", "list", "capa", "r", "capa", "r")
    assert fnmatch(str(output), "*client-with-r*")
    try:
        c1.run("close")
    except Exception:
        pass


@pytest.mark.xfail(reason="not implemented")
def test_client_kill_with_ip_filter(r: ValkeyTestClient) -> None:
    """
    test {CLIENT KILL with IP filter} {
        set c1 [valkey_client]
        $c1 client setname "killme-ip"
        r client setname "client-normal"

        set client_info [$c1 client info]
        regexp {addr=([^:]+):} $client_info -> iponly

        # Kill client by IP only
        r client kill ip $iponly skipme yes

        assert_error "*I/O error*" {$c1 ping}
    } {}
    """
    c1 = ValkeyTestClient.create_from(r)
    c1.run("client", "setname", "killme-ip")
    r.run("client", "setname", "client-normal")
    client_info = c1.run("client", "info")
    regexp("addr=([^:]+):", client_info, "->", "iponly")
    # TODO: r client kill ip iponly skipme yes
    assert_error("*I/O error*", "$c1 ping")


"""
start_server {tags {"ipv6"} overrides {bind {127.0.0.1 ::1}}} {
    test {CLIENT KILL with IPv6 filter} {
        set c [valkey ::1 [srv 0 port] 0 $::tls]
        $c client setname "client-ipv6"

        set client_info [$c client info]

        regexp {addr=\[([a-fA-F0-9:]+)\]:\d+} $client_info -> ipv6only
        set filtered [r client kill ip $ipv6only]

        assert_error "*I/O error*" {$c ping}

        $c close
    }
}
"""


def test_client_kill_with_capa_filter(r: ValkeyTestClient) -> None:
    """
    test {CLIENT KILL with CAPA filter} {
        set c1 [valkey_client]
        $c1 client setname "killme-capa"
        $c1 client capa redirect

        # Kill using capa filter
        r client kill capa r skipme yes

        assert_error "*I/O error*" {$c1 ping}
    } {}
    """
    c1 = ValkeyTestClient.create_from(r)
    c1.run("client", "setname", "killme-capa")
    c1.run("client", "capa", "redirect")
    r.run("client", "kill", "capa", "r", "skipme", "yes")
    assert_error("*I/O error*", "$c1 ping")


def test_client_kill_with_name_filter(r: ValkeyTestClient) -> None:
    """
    test {CLIENT KILL with NAME filter} {
        # Create a client and set its name
        set c1 [valkey_client]
        $c1 client setname mytestclient

        # Kill the client by name - last filter value takes precedence
        r client kill name myclient name mytestclient

        # Assert the client was killed
        assert_error "*I/O error*" {$c1 ping}

        # Cleanup
        catch {$c1 close}
    }
    """
    c1 = ValkeyTestClient.create_from(r)
    c1.run("client", "setname", "mytestclient")
    r.run("client", "kill", "name", "myclient", "name", "mytestclient")
    assert_error("*I/O error*", "$c1 ping")
    try:
        c1.run("close")
    except Exception:
        pass


def test_client_kill_with_flags_filter(r: ValkeyTestClient) -> None:
    """
    test {CLIENT KILL with FLAGS filter} {
        # Create a client and set its name
        set c1 [valkey_client]
        $c1 client setname mytestclient

        # Kill the client by flag - last filter value takes precedence
        r client kill flags O flags N

        # Assert the client was killed
        assert_error "*I/O error*" {$c1 ping}

        # Cleanup
        catch {$c1 close}
    }
    """
    c1 = ValkeyTestClient.create_from(r)
    c1.run("client", "setname", "mytestclient")
    r.run("client", "kill", "flags", "O", "flags", "N")
    assert_error("*I/O error*", "$c1 ping")
    try:
        c1.run("close")
    except Exception:
        pass


def test_client_kill_with_type_filter(r: ValkeyTestClient) -> None:
    """
    test {CLIENT KILL with TYPE filter} {
        # Create a client
        set c1 [valkey_client]

        # Kill the client by type
        r client kill type replica type normal

        # Assert the client was killed
        assert_error "*I/O error*" {$c1 ping}

        # Cleanup
        catch {$c1 close}
    }
    """
    c1 = ValkeyTestClient.create_from(r)
    r.run("client", "kill", "type", "replica", "type", "normal")
    assert_error("*I/O error*", "$c1 ping")
    try:
        c1.run("close")
    except Exception:
        pass


def test_client_kill_with_multiple_filters(r: ValkeyTestClient) -> None:
    """
    test {CLIENT KILL with multiple filters} {
        # Create two clients
        set c1 [valkey_client]
        set c2 [valkey_client]
        $c1 client setname client1
        $c2 client setname client2

        # Kill the client with name and flag filters
        r client kill name client1 flags N

        # Assert client1 was killed
        set err1 [catch {$c1 ping} error_message1]
        assert {$err1 == 1}
        assert {[string match "*I/O error*" $error_message1]}

        # Assert client2 is still alive
        assert {[catch {$c2 ping}] == 0}

        # Cleanup
        catch {$c2 close}
    }
    """
    c1 = ValkeyTestClient.create_from(r)
    c2 = ValkeyTestClient.create_from(r)
    c1.run("client", "setname", "client1")
    c2.run("client", "setname", "client2")
    r.run("client", "kill", "name", "client1", "flags", "N")
    err1 = catch("$c1 ping", "error_message1")
    assert err1 == 1
    assert_('[string match "*I/O error*" $error_message1]')
    assert catch("$c2 ping") == 0
    try:
        c2.run("close")
    except Exception:
        pass


def test_client_kill_with_multiple_filters_including_idle_time(r: ValkeyTestClient) -> None:
    """
    test {CLIENT KILL with multiple filters including idle time} {
        # Create two clients
        set c1 [valkey_client]
        set c2 [valkey_client]
        $c1 client setname client1
        $c2 client setname client2

        # Wait 1 second to ensure idle time
        after 1000

        # Kill the client with name and idle time filters
        r client kill name client1 idle 100 idle 1

        # Assert client1 was killed
        set err1 [catch {$c1 ping} error_message1]
        assert {$err1 == 1}
        assert {[string match "*I/O error*" $error_message1]}

        # Assert client2 is still alive
        assert {[catch {$c2 ping}] == 0}

        # Cleanup
        catch {$c2 close}
    }
    """
    c1 = ValkeyTestClient.create_from(r)
    c2 = ValkeyTestClient.create_from(r)
    c1.run("client", "setname", "client1")
    c2.run("client", "setname", "client2")
    time.sleep(1000 / 1000)
    r.run("client", "kill", "name", "client1", "idle", 100, "idle", 1)
    err1 = catch("$c1 ping", "error_message1")
    assert err1 == 1
    assert_('[string match "*I/O error*" $error_message1]')
    assert catch("$c2 ping") == 0
    try:
        c2.run("close")
    except Exception:
        pass


def test_client_list_with_not_name_filter(r: ValkeyTestClient) -> None:
    """
    test {CLIENT LIST with NOT-NAME filter} {
        r client setname mytestclient
        set c1 [valkey_client]
        $c1 client setname client1
        set cl [r client list not-name mytestclient not-name mytestclient]
        assert_match "*name=client1*" $cl
        assert_no_match "*name=mytestclient*" $cl
        catch {$c1 close}
    }
    """
    r.run("client", "setname", "mytestclient")
    c1 = ValkeyTestClient.create_from(r)
    c1.run("client", "setname", "client1")
    cl = r.run("client", "list", "not-name", "mytestclient", "not-name", "mytestclient")
    assert fnmatch(str(cl), "*name=client1*")
    assert_no_match("*name=mytestclient*", cl)
    try:
        c1.run("close")
    except Exception:
        pass


def test_client_list_with_not_flags_filter(r: ValkeyTestClient) -> None:
    """
    test {CLIENT LIST with NOT-FLAGS filter} {
        set c1 [valkey_client]
        $c1 readonly
        set cl [r client list not-flags r not-flags N]
        assert_match "*flags=r*" $cl
        assert_no_match "*flags=N*" $cl
        catch {$c1 close}
    }
    """
    c1 = ValkeyTestClient.create_from(r)
    c1.run("readonly")
    cl = r.run("client", "list", "not-flags", "r", "not-flags", "N")
    assert fnmatch(str(cl), "*flags=r*")
    assert_no_match("*flags=N*", cl)
    try:
        c1.run("close")
    except Exception:
        pass


def test_client_list_with_not_type_filter(r: ValkeyTestClient) -> None:
    """
    test {CLIENT LIST with NOT-TYPE filter} {
        r client setname mytestclient
        set c1 [valkey_client]
        $c1 client setname client1
        $c1 subscribe x
        set cl [r client list not-type pubsub not-type normal]
        assert_match "*name=client1*" $cl
        assert_no_match "*name=mytestclient*" $cl
        catch {$c1 close}
    }
    """
    r.run("client", "setname", "mytestclient")
    c1 = ValkeyTestClient.create_from(r)
    c1.run("client", "setname", "client1")
    c1.run("subscribe", "x")
    cl = r.run("client", "list", "not-type", "pubsub", "not-type", "normal")
    assert fnmatch(str(cl), "*name=client1*")
    assert_no_match("*name=mytestclient*", cl)
    try:
        c1.run("close")
    except Exception:
        pass


@pytest.mark.xfail(reason="not implemented")
def test_client_list_with_multiple_negative_filters(r: ValkeyTestClient) -> None:
    """
    test {CLIENT LIST with multiple negative filters} {
        r client setname mytestclient
        set client_info [r client info]
        set fields [split $client_info " "]
        foreach pair $fields {
            lassign [split $pair "="] key val
            if {$key eq "id"} { set myid $val }
            if {$key eq "name"} { set myname $val }
        }

        set c1 [valkey_client]
        $c1 client setname client1

        set cl [r client list not-id $myid not-name $myname]

        assert_match "*name=client1*" $cl
        assert_no_match "*name=mytestclient*" $cl
        catch {$c1 close}
    }
    """
    r.run("client", "setname", "mytestclient")
    client_info = r.run("client", "info")
    fields = split(client_info, " ")
    foreach(
        "pair",
        fields,
        '            lassign [split $pair "="] key val\n            if {$key eq "id"} { set myid $val }\n            if {$key eq "name"} { set myname $val }\n        ',
    )
    c1 = ValkeyTestClient.create_from(r)
    c1.run("client", "setname", "client1")
    # TODO: set cl r client list not-id $myid not-name $myname
    # TODO: assert_match "*name=client1*" cl
    # TODO: assert_no_match "*name=mytestclient*" cl
    try:
        c1.run("close")
    except Exception:
        pass


def test_client_list_with_multiple_id_filters(r: ValkeyTestClient) -> None:
    """
    test {CLIENT LIST with multiple id filters} {
        # Create multiple clients
        set c1 [valkey_client]
        set c2 [valkey_client]
        set c3 [valkey_client]

        # Fetch their IDs
        set id1 [$c1 client id]
        set id2 [$c2 client id]
        set id3 [$c3 client id]

        set result [r client list id $id1 id $id2 id $id3]
        assert_match "*id=$id1*" $result
        assert_match "*id=$id2*" $result
        assert_match "*id=$id3*" $result

        catch {$c1 close}
        catch {$c2 close}
        catch {$c3 close}
    }
    """
    c1 = ValkeyTestClient.create_from(r)
    c2 = ValkeyTestClient.create_from(r)
    c3 = ValkeyTestClient.create_from(r)
    id1 = c1.run("client", "id")
    id2 = c2.run("client", "id")
    id3 = c3.run("client", "id")
    result = r.run("client", "list", "id", id1, "id", id2, "id", id3)
    assert fnmatch(str(result), str(f"*id={id1}*"))
    assert fnmatch(str(result), str(f"*id={id2}*"))
    assert fnmatch(str(result), str(f"*id={id3}*"))
    try:
        c1.run("close")
    except Exception:
        pass
    try:
        c2.run("close")
    except Exception:
        pass
    try:
        c3.run("close")
    except Exception:
        pass


def test_client_kill_with_multiple_id_filters(r: ValkeyTestClient) -> None:
    """
    test {CLIENT KILL with multiple id filters} {
        # Create multiple clients
        set c1 [valkey_client]
        set c2 [valkey_client]
        set c3 [valkey_client]

        # Fetch their IDs
        set id1 [$c1 client id]
        set id2 [$c2 client id]
        set id3 [$c3 client id]

        assert_equal [r client kill id $id1 id $id2 id $id3] 3
    }
    """
    c1 = ValkeyTestClient.create_from(r)
    c2 = ValkeyTestClient.create_from(r)
    c3 = ValkeyTestClient.create_from(r)
    id1 = c1.run("client", "id")
    id2 = c2.run("client", "id")
    id3 = c3.run("client", "id")
    assert r.run("client", "kill", "id", id1, "id", id2, "id", id3) == 3


def test_client_list_with_multiple_negative_filters_1(r: ValkeyTestClient) -> None:
    """
    test {CLIENT LIST with multiple negative filters} {
        # Create multiple clients with different names and flags
        set c1 [valkey_client]
        set c2 [valkey_client]
        set c3 [valkey_client]
        $c1 client setname client1
        $c2 client setname client1
        $c3 client setname client2
        $c3 multi

        # Wait 1 second to ensure idle time
        after 1000

        # Fetch the client list filtered by name and not-flags
        set cl [split [r client list name client1 not-flags x] "\r\n"]

        # Assert the clients returned match the filters
        foreach line $cl {
            regexp {name=([^ ]+) .* flags=([^ ]+)} $line _ actual_name flags
            assert {[string match *client1* $actual_name] || [string match *client2* $actual_name]}
            assert {[string match *N* $flags]}
        }

        # Close clients
        $c1 close
        $c2 close
        $c3 close
    }
    """
    c1 = ValkeyTestClient.create_from(r)
    c2 = ValkeyTestClient.create_from(r)
    c3 = ValkeyTestClient.create_from(r)
    c1.run("client", "setname", "client1")
    c2.run("client", "setname", "client1")
    c3.run("client", "setname", "client2")
    c3.run("multi")
    time.sleep(1000 / 1000)
    cl = split(r.run("client", "list", "name", "client1", "not-flags", "x"), "\r\n")
    foreach(
        "line",
        cl,
        "            regexp {name=([^ ]+) .* flags=([^ ]+)} $line _ actual_name flags\n            assert {[string match *client1* $actual_name] || [string match *client2* $actual_name]}\n            assert {[string match *N* $flags]}\n        ",
    )
    c1.run("close")
    c2.run("close")
    c3.run("close")


@pytest.mark.xfail(reason="not implemented")
def test_client_list_with_not_ip_filter(r: ValkeyTestClient) -> None:
    """
    test {CLIENT LIST with NOT-IP filter} {
        r client setname "not-ip"

        set client_info [r client info]
        regexp {addr=([^:]+):} $client_info -> not_ip

        # Use the extracted IP for filtering.
        r client list not-ip $not_ip not-ip $not_ip
    } {}
    """
    r.run("client", "setname", "not-ip")
    client_info = r.run("client", "info")
    regexp("addr=([^:]+):", client_info, "->", "not_ip")
    # TODO: r client list not-ip not_ip not-ip not_ip


"""
start_server {tags {"ipv6"} overrides {bind {127.0.0.1 ::1}}} {
    test {CLIENT LIST with IPv6 negative filter} {
        set c [valkey ::1 [srv 0 port] 0 $::tls]
        $c client setname "client-ipv6"

        set client_info [$c client info]

        regexp {addr=\[([a-fA-F0-9:]+)\]:\d+} $client_info -> ipv6only
        set filtered [$c client list not-ip "1.2.3.4" not-ip $ipv6only]
        assert_no_match *client-ipv6* $filtered

        $c close
    }
}
"""


def test_client_list_with_not_capa_filter(r: ValkeyTestClient) -> None:
    """
    test {CLIENT LIST with NOT-CAPA filter} {
        r client setname mytestclient
        set c1 [valkey_client]
        $c1 client setname client-with-r
        $c1 client capa redirect
        set cl [r client list not-capa r not-capa r]
        assert_match "*name=mytestclient*" $cl
        assert_no_match "*name=client-with-r*" $cl
        catch {$c1 close}
    }
    """
    r.run("client", "setname", "mytestclient")
    c1 = ValkeyTestClient.create_from(r)
    c1.run("client", "setname", "client-with-r")
    c1.run("client", "capa", "redirect")
    cl = r.run("client", "list", "not-capa", "r", "not-capa", "r")
    assert fnmatch(str(cl), "*name=mytestclient*")
    assert_no_match("*name=client-with-r*", cl)
    try:
        c1.run("close")
    except Exception:
        pass


def test_client_kill_with_not_ip_filter(r: ValkeyTestClient) -> None:
    """
    test {CLIENT KILL with NOT-IP filter} {
        set c1 [valkey_client]
        $c1 client setname "killme-not-ip"
        r client setname "client-normal"

        # Kill client by NOT-IP
        r client kill not-ip "1.2.3.4" skipme yes

        assert_error "*I/O error*" {$c1 ping}
        catch {$c1 close}

        set list_reply [r client list]
        assert_match "*name=client-normal*" $list_reply
        assert_no_match "*name=killme-not-ip*" $list_reply
    }
    """
    c1 = ValkeyTestClient.create_from(r)
    c1.run("client", "setname", "killme-not-ip")
    r.run("client", "setname", "client-normal")
    r.run("client", "kill", "not-ip", "1.2.3.4", "skipme", "yes")
    assert_error("*I/O error*", "$c1 ping")
    try:
        c1.run("close")
    except Exception:
        pass
    list_reply = r.run("client", "list")
    assert fnmatch(str(list_reply), "*name=client-normal*")
    assert_no_match("*name=killme-not-ip*", list_reply)


def test_client_kill_with_not_capa_filter(r: ValkeyTestClient) -> None:
    """
    test {CLIENT KILL with NOT-CAPA filter} {
        set c1 [valkey_client]
        $c1 client setname "killme-not-capa"
        r client setname "client-normal"

        # Kill using not-capa filter
        r client kill not-capa r not-capa r skipme yes

        assert_error "*I/O error*" {$c1 ping}
        catch {$c1 close}

        set cl [r client list]
        assert_match "*name=client-normal*" $cl
        assert_no_match "*name=killme-not-capa*" $cl
    }
    """
    c1 = ValkeyTestClient.create_from(r)
    c1.run("client", "setname", "killme-not-capa")
    r.run("client", "setname", "client-normal")
    r.run("client", "kill", "not-capa", "r", "not-capa", "r", "skipme", "yes")
    assert_error("*I/O error*", "$c1 ping")
    try:
        c1.run("close")
    except Exception:
        pass
    cl = r.run("client", "list")
    assert fnmatch(str(cl), "*name=client-normal*")
    assert_no_match("*name=killme-not-capa*", cl)


def test_client_kill_with_not_name_filter(r: ValkeyTestClient) -> None:
    """
    test {CLIENT KILL with NOT-NAME filter} {
        r client setname "client-normal"
        # Create a client and set its name
        set c1 [valkey_client]
        $c1 client setname "killme-not-name"

        # Kill the client by not-name
        r client kill not-name client-normal not-name client-normal

        # Assert the client was killed
        assert_error "*I/O error*" {$c1 ping}
        catch {$c1 close}

        set cl [r client list]
        assert_match "*name=client-normal*" $cl
        assert_no_match "*name=killme-not-name*" $cl
    }
    """
    r.run("client", "setname", "client-normal")
    c1 = ValkeyTestClient.create_from(r)
    c1.run("client", "setname", "killme-not-name")
    r.run("client", "kill", "not-name", "client-normal", "not-name", "client-normal")
    assert_error("*I/O error*", "$c1 ping")
    try:
        c1.run("close")
    except Exception:
        pass
    cl = r.run("client", "list")
    assert fnmatch(str(cl), "*name=client-normal*")
    assert_no_match("*name=killme-not-name*", cl)


def test_client_kill_with_not_flags_filter(r: ValkeyTestClient) -> None:
    """
    test {CLIENT KILL with NOT-FLAGS filter} {
        r client setname "client-normal"
        # Create a client and set its name
        set c1 [valkey_client]
        $c1 client setname "killme-not-flags"
        $c1 readonly

        # Kill the client by not-flag
        r client kill not-flags N not-flags N

        # Assert the client was killed
        assert_error "*I/O error*" {$c1 ping}
        catch {$c1 close}

        set cl [r client list]
        assert_match "*name=client-normal*" $cl
        assert_no_match "*name=killme-not-flags*" $cl
    }
    """
    r.run("client", "setname", "client-normal")
    c1 = ValkeyTestClient.create_from(r)
    c1.run("client", "setname", "killme-not-flags")
    c1.run("readonly")
    r.run("client", "kill", "not-flags", "N", "not-flags", "N")
    assert_error("*I/O error*", "$c1 ping")
    try:
        c1.run("close")
    except Exception:
        pass
    cl = r.run("client", "list")
    assert fnmatch(str(cl), "*name=client-normal*")
    assert_no_match("*name=killme-not-flags*", cl)


def test_client_kill_with_not_type_filter(r: ValkeyTestClient) -> None:
    """
    test {CLIENT KILL with NOT-TYPE filter} {
        r client setname "client-normal"
        # Create a client
        set c1 [valkey_client]
        $c1 client setname "killme-not-type"
        $c1 subscribe x

        # Kill the client by not-type
        r client kill not-type normal

        # Assert the client was killed
        assert_error "*I/O error*" {$c1 ping}
        catch {$c1 close}

        set cl [r client list]
        assert_match "*name=client-normal*" $cl
        assert_no_match "*name=killme-not-type*" $cl
    }
    """
    r.run("client", "setname", "client-normal")
    c1 = ValkeyTestClient.create_from(r)
    c1.run("client", "setname", "killme-not-type")
    c1.run("subscribe", "x")
    r.run("client", "kill", "not-type", "normal")
    assert_error("*I/O error*", "$c1 ping")
    try:
        c1.run("close")
    except Exception:
        pass
    cl = r.run("client", "list")
    assert fnmatch(str(cl), "*name=client-normal*")
    assert_no_match("*name=killme-not-type*", cl)


def test_client_kill_with_multiple_negative_filters(r: ValkeyTestClient) -> None:
    """
    test {CLIENT KILL with multiple negative filters} {
        # Create two clients
        set c1 [valkey_client]
        set c2 [valkey_client]
        $c1 client setname client1
        $c2 client setname client2

        # Kill the client with not-name and not-flag filters
        r client kill not-name client2 not-flags x

        # Assert client1 was killed
        set err1 [catch {$c1 ping} error_message1]
        assert {$err1 == 1}
        assert {[string match "*I/O error*" $error_message1]}

        # Assert client2 is still alive
        assert {[catch {$c2 ping}] == 0}

        # Cleanup
        catch {$c2 close}
    }
    """
    c1 = ValkeyTestClient.create_from(r)
    c2 = ValkeyTestClient.create_from(r)
    c1.run("client", "setname", "client1")
    c2.run("client", "setname", "client2")
    r.run("client", "kill", "not-name", "client2", "not-flags", "x")
    err1 = catch("$c1 ping", "error_message1")
    assert err1 == 1
    assert_('[string match "*I/O error*" $error_message1]')
    assert catch("$c2 ping") == 0
    try:
        c2.run("close")
    except Exception:
        pass


def test_client_kill_with_both_positive_and_negative_filters_including_idle_time(r: ValkeyTestClient) -> None:
    """
    test {CLIENT KILL with both positive and negative filters including idle time} {
        # Create two clients
        set c1 [valkey_client]
        set c2 [valkey_client]
        $c1 client setname client1
        $c2 client setname client2

        # Wait 1 second to ensure idle time
        after 1000

        # Kill the client with not-name and idle filters
        r client kill not-name client2 idle 1

        # Assert client1 was killed
        set err1 [catch {$c1 ping} error_message1]
        assert {$err1 == 1}
        assert {[string match "*I/O error*" $error_message1]}

        # Assert client2 is still alive
        assert {[catch {$c2 ping}] == 0}

        # Cleanup
        catch {$c2 close}
    }
    """
    c1 = ValkeyTestClient.create_from(r)
    c2 = ValkeyTestClient.create_from(r)
    c1.run("client", "setname", "client1")
    c2.run("client", "setname", "client2")
    time.sleep(1000 / 1000)
    r.run("client", "kill", "not-name", "client2", "idle", 1)
    err1 = catch("$c1 ping", "error_message1")
    assert err1 == 1
    assert_('[string match "*I/O error*" $error_message1]')
    assert catch("$c2 ping") == 0
    try:
        c2.run("close")
    except Exception:
        pass


def test_client_list_with_illegal_arguments(r: ValkeyTestClient) -> None:
    """
    test {CLIENT LIST with illegal arguments} {
        assert_error "ERR syntax error" {r client list id 10 wrong_arg}

        assert_error "ERR syntax error" {r client list id str}
        assert_error "ERR *greater than 0*" {r client list id -1}
        assert_error "ERR *greater than 0*" {r client list id 0}

        assert_error "ERR Unknown client type*" {r client list type wrong_type}

        assert_error "ERR No such user*" {r client list user wrong_user}

        assert_error "ERR syntax error*" {r client list skipme yes_or_no}

        assert_error "ERR *not an integer or out of range*" {r client list maxage str}
        assert_error "ERR *not an integer or out of range*" {r client list maxage 9999999999999999999}
        assert_error "ERR *greater than 0*" {r client list maxage -1}

        assert_error "ERR syntax error" {r client list not-id 10 wrong_arg}

        assert_error "ERR syntax error" {r client list not-id str}
        assert_error "ERR *greater than 0*" {r client list not-id -1}
        assert_error "ERR *greater than 0*" {r client list not-id 0}

        assert_error "ERR Unknown client type*" {r client list not-type wrong_type}

        assert_error "ERR No such user*" {r client list not-user wrong_user}
    }
    """
    with pytest.raises(Exception, match="ERR\\ syntax\\ error"):
        r.run("client", "list", "id", 10, "wrong_arg")
    with pytest.raises(Exception, match="ERR\\ syntax\\ error"):
        r.run("client", "list", "id", "str")
    with pytest.raises(Exception, match="ERR\\ .*greater\\ than\\ 0.*"):
        r.run("client", "list", "id", -1)
    with pytest.raises(Exception, match="ERR\\ .*greater\\ than\\ 0.*"):
        r.run("client", "list", "id", 0)
    with pytest.raises(Exception, match="ERR\\ Unknown\\ client\\ type.*"):
        r.run("client", "list", "type", "wrong_type")
    with pytest.raises(Exception, match="ERR\\ No\\ such\\ user.*"):
        r.run("client", "list", "user", "wrong_user")
    with pytest.raises(Exception, match="ERR\\ syntax\\ error.*"):
        r.run("client", "list", "skipme", "yes_or_no")
    with pytest.raises(Exception, match="ERR\\ .*not\\ an\\ integer\\ or\\ out\\ of\\ range.*"):
        r.run("client", "list", "maxage", "str")
    with pytest.raises(Exception, match="ERR\\ .*not\\ an\\ integer\\ or\\ out\\ of\\ range.*"):
        r.run("client", "list", "maxage", 9999999999999999999)
    with pytest.raises(Exception, match="ERR\\ .*greater\\ than\\ 0.*"):
        r.run("client", "list", "maxage", -1)
    with pytest.raises(Exception, match="ERR\\ syntax\\ error"):
        r.run("client", "list", "not-id", 10, "wrong_arg")
    with pytest.raises(Exception, match="ERR\\ syntax\\ error"):
        r.run("client", "list", "not-id", "str")
    with pytest.raises(Exception, match="ERR\\ .*greater\\ than\\ 0.*"):
        r.run("client", "list", "not-id", -1)
    with pytest.raises(Exception, match="ERR\\ .*greater\\ than\\ 0.*"):
        r.run("client", "list", "not-id", 0)
    with pytest.raises(Exception, match="ERR\\ Unknown\\ client\\ type.*"):
        r.run("client", "list", "not-type", "wrong_type")
    with pytest.raises(Exception, match="ERR\\ No\\ such\\ user.*"):
        r.run("client", "list", "not-user", "wrong_user")


"""
proc get_client_tot_in_out_cmds {id} {
    set info_list [r client list]
    set in [get_field_in_client_list $id $info_list "tot-net-in"]
    set out [get_field_in_client_list $id $info_list "tot-net-out"]
    set cmds [get_field_in_client_list $id $info_list "tot-cmds"]
    return [list $in $out $cmds]
}
"""


def test_client_input_output_and_command_process_statistics(r: ValkeyTestClient) -> None:
    """
    test {client input output and command process statistics} {
        set info1 [r client info]
        set input1 [get_field_in_client_info $info1 "tot-net-in"]
        set output1 [get_field_in_client_info $info1 "tot-net-out"]
        set cmd1 [get_field_in_client_info $info1 "tot-cmds"]
        set info2 [r client info]
        set input2 [get_field_in_client_info $info2 "tot-net-in"]
        set output2 [get_field_in_client_info $info2 "tot-net-out"]
        set cmd2 [get_field_in_client_info $info2 "tot-cmds"]
        assert_equal [expr $input1+26] $input2
        assert {[expr $output1+300] < $output2}
        assert_equal [expr $cmd1+1] $cmd2
        # test blocking command
        r del mylist
        set rd [valkey_deferring_client]
        $rd client id
        set rd_id [$rd read]
        set info_list [r client list]
        set input3 [get_field_in_client_list $rd_id $info_list "tot-net-in"]
        set output3 [get_field_in_client_list $rd_id $info_list "tot-net-out"]
        set cmd3 [get_field_in_client_list $rd_id $info_list "tot-cmds"]
        $rd blpop mylist 0
        set input4 [expr $input3 + 34]
        set output4 $output3
        set cmd4 $cmd3
        wait_for_condition 5 100 {
            [list $input4 $output4 $cmd4] eq [get_client_tot_in_out_cmds $rd_id]
        } else {
            puts "--------- tot-net-in tot-net-out tot-cmds (4)"
            puts "Expected: [list $input4 $output4 $cmd4]"
            puts "Actual:   [get_client_tot_in_out_cmds $rd_id]"
            fail "Blocked BLPOP didn't increment expected client fields"
        }
        r lpush mylist a
        set input5 $input4
        set output5 [expr $output4 + 23]
        set cmd5 [expr $cmd4 + 1]
        wait_for_condition 5 100 {
            [list $input5 $output5 $cmd5] eq [get_client_tot_in_out_cmds $rd_id]
        } else {
            puts "--------- tot-net-in tot-net-out tot-cmds (5)"
            puts "Expected: [list $input5 $output5 $cmd5]"
            puts "Actual:   [get_client_tot_in_out_cmds $rd_id]"
            fail "Unblocked BLPOP didn't increment expected client fields"
        }
        $rd close
        # test recursive command
        set info [r client info]
        set cmd6 [get_field_in_client_info $info "tot-cmds"]
        r eval "server.call('ping')" 0
        set info [r client info]
        set cmd7 [get_field_in_client_info $info "tot-cmds"]
        assert_equal [expr $cmd6+3] $cmd7
    }
    """
    info1 = r.run("client", "info")
    input1 = get_field_in_client_info(info1, "tot-net-in")
    output1 = get_field_in_client_info(info1, "tot-net-out")
    cmd1 = get_field_in_client_info(info1, "tot-cmds")
    info2 = r.run("client", "info")
    input2 = get_field_in_client_info(info2, "tot-net-in")
    output2 = get_field_in_client_info(info2, "tot-net-out")
    cmd2 = get_field_in_client_info(info2, "tot-cmds")
    assert expr(input1, 26) == input2
    assert expr(output1, 300) < output2
    assert expr(cmd1, 1) == cmd2
    r.run("del", "mylist")
    rd = ValkeyTestClient.create_from(r)
    rd.run("client", "id")
    rd_id = rd.run("read")
    info_list = r.run("client", "list")
    input3 = get_field_in_client_list(rd_id, info_list, "tot-net-in")
    output3 = get_field_in_client_list(rd_id, info_list, "tot-net-out")
    cmd3 = get_field_in_client_list(rd_id, info_list, "tot-cmds")
    rd.run("blpop", "mylist", 0)
    input4 = expr(input3, "+", 34)
    output4 = output3
    cmd4 = cmd3
    wait_for_condition(
        5,
        100,
        lambda: [input4, output4, cmd4] == get_client_tot_in_out_cmds(rd_id),
        lambda: fail("Blocked BLPOP didn't increment expected client fields"),
    )
    r.run("lpush", "mylist", "a")
    input5 = input4
    output5 = expr(output4, "+", 23)
    cmd5 = expr(cmd4, "+", 1)
    wait_for_condition(
        5,
        100,
        lambda: [input5, output5, cmd5] == get_client_tot_in_out_cmds(rd_id),
        lambda: fail("Unblocked BLPOP didn't increment expected client fields"),
    )
    rd.run("close")
    info = r.run("client", "info")
    cmd6 = get_field_in_client_info(info, "tot-cmds")
    r.run("eval", "server.call('ping')", 0)
    info = r.run("client", "info")
    cmd7 = get_field_in_client_info(info, "tot-cmds")
    assert expr(cmd6, 3) == cmd7


def test_client_kill_with_illegal_arguments(r: ValkeyTestClient) -> None:
    """
    test {CLIENT KILL with illegal arguments} {
        assert_error "ERR wrong number of arguments for 'client|kill' command" {r client kill}
        assert_error "ERR syntax error*" {r client kill id 10 wrong_arg}

        assert_error "ERR syntax error*" {r client kill id str}
        assert_error "ERR *greater than 0*" {r client kill id -1}
        assert_error "ERR *greater than 0*" {r client kill id 0}

        assert_error "ERR Unknown client type*" {r client kill type wrong_type}

        assert_error "ERR No such user*" {r client kill user wrong_user}

        assert_error "ERR syntax error*" {r client kill skipme yes_or_no}

        assert_error "ERR *not an integer or out of range*" {r client kill maxage str}
        assert_error "ERR *not an integer or out of range*" {r client kill maxage 9999999999999999999}
        assert_error "ERR *greater than 0*" {r client kill maxage -1}
    }
    """
    with pytest.raises(Exception, match="ERR\\ wrong\\ number\\ of\\ arguments\\ for\\ 'client\\|kill'\\ command"):
        r.run("client", "kill")
    with pytest.raises(Exception, match="ERR\\ syntax\\ error.*"):
        r.run("client", "kill", "id", 10, "wrong_arg")
    with pytest.raises(Exception, match="ERR\\ syntax\\ error.*"):
        r.run("client", "kill", "id", "str")
    with pytest.raises(Exception, match="ERR\\ .*greater\\ than\\ 0.*"):
        r.run("client", "kill", "id", -1)
    with pytest.raises(Exception, match="ERR\\ .*greater\\ than\\ 0.*"):
        r.run("client", "kill", "id", 0)
    with pytest.raises(Exception, match="ERR\\ Unknown\\ client\\ type.*"):
        r.run("client", "kill", "type", "wrong_type")
    with pytest.raises(Exception, match="ERR\\ No\\ such\\ user.*"):
        r.run("client", "kill", "user", "wrong_user")
    with pytest.raises(Exception, match="ERR\\ syntax\\ error.*"):
        r.run("client", "kill", "skipme", "yes_or_no")
    with pytest.raises(Exception, match="ERR\\ .*not\\ an\\ integer\\ or\\ out\\ of\\ range.*"):
        r.run("client", "kill", "maxage", "str")
    with pytest.raises(Exception, match="ERR\\ .*not\\ an\\ integer\\ or\\ out\\ of\\ range.*"):
        r.run("client", "kill", "maxage", 9999999999999999999)
    with pytest.raises(Exception, match="ERR\\ .*greater\\ than\\ 0.*"):
        r.run("client", "kill", "maxage", -1)


@pytest.mark.xfail(reason="not implemented")
def test_client_kill_maxage_will_kill_old_clients(r: ValkeyTestClient, rd1, rd2) -> None:
    """
    test {CLIENT KILL maxAGE will kill old clients} {
        # This test is very likely to do a false positive if the execute time
        # takes longer than the max age, so give it a few more chances. Go with
        # 3 retries of increasing sleep_time, i.e. start with 2s, then go 4s, 8s.
        set sleep_time 2
        for {set i 0} {$i < 3} {incr i} {
            set rd1 [valkey_deferring_client]
            r debug sleep $sleep_time
            set rd2 [valkey_deferring_client]
            r acl setuser dummy on nopass +ping
            $rd1 auth dummy ""
            $rd1 read
            $rd2 auth dummy ""
            $rd2 read

            # Should kill rd1 but not rd2
            set max_age [expr $sleep_time / 2]
            set res [r client kill user dummy maxage $max_age]
            if {$res == 1} {
                break
            } else {
                # Clean up and try again next time
                set sleep_time [expr $sleep_time * 2]
                $rd1 close
                $rd2 close
            }

        } ;# for

        if {$::verbose} { puts "CLIENT KILL maxAGE will kill old clients test attempts: $i" }
        assert_equal $res 1

        # rd2 should still be connected
        $rd2 ping
        assert_equal "PONG" [$rd2 read]

        $rd1 close
        $rd2 close
    } {0} {"needs:debug"}
    """
    sleep_time = 2
    i = 0
    while i < 3:
        rd1 = ValkeyTestClient.create_from(r)
        r.run("debug", "sleep", sleep_time)
        rd2 = ValkeyTestClient.create_from(r)
        r.run("acl", "setuser", "dummy", "on", "nopass", "+ping")
        rd1.run("auth", "dummy", "")
        rd1.run("read")
        rd2.run("auth", "dummy", "")
        rd2.run("read")
        max_age = expr(sleep_time, "/", 2)
        res = r.run("client", "kill", "user", "dummy", "maxage", max_age)
        if_(
            "$res == 1",
            "                break\n            ",
            "else",
            "                # Clean up and try again next time\n                set sleep_time [expr $sleep_time * 2]\n                $rd1 close\n                $rd2 close\n            ",
        )
        i += 1
    if False:
        pass
    # TODO: assert_equal res 1
    rd2.run("ping")
    assert "PONG" == rd2.run("read")
    rd1.run("close")
    rd2.run("close")


def test_client_kill_skipme_yes_or_no_will_kill_all_clients(r: ValkeyTestClient) -> None:
    """
    test {CLIENT KILL SKIPME YES/NO will kill all clients} {
        # Kill all clients except `me`
        set rd1 [valkey_deferring_client]
        set rd2 [valkey_deferring_client]
        set connected_clients [s connected_clients]
        assert {$connected_clients >= 3}
        set res [r client kill skipme yes]
        assert {$res == $connected_clients - 1}

        # Kill all clients, including `me`
        set rd3 [valkey_deferring_client]
        set rd4 [valkey_deferring_client]
        set connected_clients [s connected_clients]
        assert {$connected_clients == 3}
        set res [r client kill skipme no]
        assert_equal $res $connected_clients

        # After killing `me`, the first ping will throw an error
        assert_error "*I/O error*" {r ping}
        assert_equal "PONG" [r ping]

        $rd1 close
        $rd2 close
        $rd3 close
        $rd4 close
    }
    """
    rd1 = ValkeyTestClient.create_from(r)
    rd2 = ValkeyTestClient.create_from(r)
    connected_clients = s("connected_clients")
    assert connected_clients >= 3
    res = r.run("client", "kill", "skipme", "yes")
    assert res == (connected_clients - 1)
    rd3 = ValkeyTestClient.create_from(r)
    rd4 = ValkeyTestClient.create_from(r)
    connected_clients = s("connected_clients")
    assert connected_clients == 3
    res = r.run("client", "kill", "skipme", "no")
    assert res == connected_clients
    with pytest.raises(Exception, match=".*I/O\\ error.*"):
        r.run("ping")
    assert "PONG" == r.run("ping")
    rd1.run("close")
    rd2.run("close")
    rd3.run("close")
    rd4.run("close")


def test_client_command_unhappy_path_coverage(r: ValkeyTestClient) -> None:
    """
    test {CLIENT command unhappy path coverage} {
        assert_error "ERR*wrong number of arguments*" {r client caching}
        assert_error "ERR*when the client is in tracking mode*" {r client caching maybe}
        assert_error "ERR*syntax*" {r client no-evict wrongInput}
        assert_error "ERR*syntax*" {r client reply wrongInput}
        assert_error "ERR*syntax*" {r client tracking wrongInput}
        assert_error "ERR*syntax*" {r client tracking on wrongInput}
        assert_error "ERR*when the client is in tracking mode*" {r client caching off}
        assert_error "ERR*when the client is in tracking mode*" {r client caching on}

        r CLIENT TRACKING ON optout
        assert_error "ERR*syntax*" {r client caching on}

        r CLIENT TRACKING off optout
        assert_error "ERR*when the client is in tracking mode*" {r client caching on}

        assert_error "ERR*No such*" {r client kill 000.123.321.567:0000}
        assert_error "ERR*No such*" {r client kill 127.0.0.1:}

        assert_error "ERR*timeout is not an integer*" {r client pause abc}
        assert_error "ERR timeout is negative" {r client pause -1}
    }
    """
    with pytest.raises(Exception, match="ERR.*wrong\\ number\\ of\\ arguments.*"):
        r.run("client", "caching")
    with pytest.raises(Exception, match="ERR.*when\\ the\\ client\\ is\\ in\\ tracking\\ mode.*"):
        r.run("client", "caching", "maybe")
    with pytest.raises(Exception, match="ERR.*syntax.*"):
        r.run("client", "no-evict", "wrongInput")
    with pytest.raises(Exception, match="ERR.*syntax.*"):
        r.run("client", "reply", "wrongInput")
    with pytest.raises(Exception, match="ERR.*syntax.*"):
        r.run("client", "tracking", "wrongInput")
    with pytest.raises(Exception, match="ERR.*syntax.*"):
        r.run("client", "tracking", "on", "wrongInput")
    with pytest.raises(Exception, match="ERR.*when\\ the\\ client\\ is\\ in\\ tracking\\ mode.*"):
        r.run("client", "caching", "off")
    with pytest.raises(Exception, match="ERR.*when\\ the\\ client\\ is\\ in\\ tracking\\ mode.*"):
        r.run("client", "caching", "on")
    r.run("CLIENT", "TRACKING", "ON", "optout")
    with pytest.raises(Exception, match="ERR.*syntax.*"):
        r.run("client", "caching", "on")
    r.run("CLIENT", "TRACKING", "off", "optout")
    with pytest.raises(Exception, match="ERR.*when\\ the\\ client\\ is\\ in\\ tracking\\ mode.*"):
        r.run("client", "caching", "on")
    with pytest.raises(Exception, match="ERR.*No\\ such.*"):
        r.run("client", "kill", "000.123.321.567:0000")
    with pytest.raises(Exception, match="ERR.*No\\ such.*"):
        r.run("client", "kill", "127.0.0.1:")
    with pytest.raises(Exception, match="ERR.*timeout\\ is\\ not\\ an\\ integer.*"):
        r.run("client", "pause", "abc")
    with pytest.raises(Exception, match="ERR\\ timeout\\ is\\ negative"):
        r.run("client", "pause", -1)


def test_client_kill_close_the_client_connection_during_bgsave(r: ValkeyTestClient) -> None:
    """
    test "CLIENT KILL close the client connection during bgsave" {
        # Start a slow bgsave, trigger an active fork.
        r flushall
        r set k v
        r config set rdb-key-save-delay 10000000
        r bgsave
        wait_for_condition 1000 10 {
            [s rdb_bgsave_in_progress] eq 1
        } else {
            fail "bgsave did not start in time"
        }

        # Kill (close) the connection
        r client kill skipme no

        # In the past, client connections needed to wait for bgsave
        # to end before actually closing, now they are closed immediately.
        assert_error "*I/O error*" {r ping} ;# get the error very quickly
        assert_equal "PONG" [r ping]

        # Make sure the bgsave is still in progress
        assert_equal [s rdb_bgsave_in_progress] 1

        # Stop the child before we proceed to the next test
        r config set rdb-key-save-delay 0
        r flushall
        wait_for_condition 1000 10 {
            [s rdb_bgsave_in_progress] eq 0
        } else {
            fail "bgsave did not stop in time"
        }
    } {} {needs:save}
    """
    r.run("flushall")
    r.run("set", "k", "v")
    r.run("config", "set", "rdb-key-save-delay", 10000000)
    r.run("bgsave")
    wait_for_condition(1000, 10, lambda: s("rdb_bgsave_in_progress") == 1, lambda: fail("bgsave did not start in time"))
    r.run("client", "kill", "skipme", "no")
    with pytest.raises(Exception, match=".*I/O\\ error.*"):
        r.run("ping")
    assert "PONG" == r.run("ping")
    assert s("rdb_bgsave_in_progress") == 1
    r.run("config", "set", "rdb-key-save-delay", 0)
    r.run("flushall")
    wait_for_condition(1000, 10, lambda: s("rdb_bgsave_in_progress") == 0, lambda: fail("bgsave did not stop in time"))


def test_client_reply_off_or_on_disable_all_commands_reply(r: ValkeyTestClient) -> None:
    """
    test "CLIENT REPLY OFF/ON: disable all commands reply" {
        set rd [valkey_deferring_client]

        # These replies were silenced.
        $rd client reply off
        $rd ping pong
        $rd ping pong2

        $rd client reply on
        assert_equal {OK} [$rd read]
        $rd ping pong3
        assert_equal {pong3} [$rd read]

        $rd close
    }
    """
    rd = ValkeyTestClient.create_from(r)
    rd.run("client", "reply", "off")
    rd.run("ping", "pong")
    rd.run("ping", "pong2")
    rd.run("client", "reply", "on")
    assert "OK" == rd.run("read")
    rd.run("ping", "pong3")
    assert "pong3" == rd.run("read")
    rd.run("close")


def test_client_reply_skip_skip_the_next_command_reply(r: ValkeyTestClient) -> None:
    """
    test "CLIENT REPLY SKIP: skip the next command reply" {
        set rd [valkey_deferring_client]

        # The first pong reply was silenced.
        $rd client reply skip
        $rd ping pong

        $rd ping pong2
        assert_equal {pong2} [$rd read]

        $rd close
    }
    """
    rd = ValkeyTestClient.create_from(r)
    rd.run("client", "reply", "skip")
    rd.run("ping", "pong")
    rd.run("ping", "pong2")
    assert "pong2" == rd.run("read")
    rd.run("close")


def test_client_reply_on_unset_skip_flag(r: ValkeyTestClient) -> None:
    """
    test "CLIENT REPLY ON: unset SKIP flag" {
        set rd [valkey_deferring_client]

        $rd client reply skip
        $rd client reply on
        assert_equal {OK} [$rd read] ;# OK from CLIENT REPLY ON command

        $rd ping
        assert_equal {PONG} [$rd read]

        $rd close
    }
    """
    rd = ValkeyTestClient.create_from(r)
    rd.run("client", "reply", "skip")
    rd.run("client", "reply", "on")
    assert "OK" == rd.run("read")
    rd.run("ping")
    assert "PONG" == rd.run("read")
    rd.run("close")


def test_monitor_can_log_executed_commands(r: ValkeyTestClient) -> None:
    """
    test {MONITOR can log executed commands} {
        set rd [valkey_deferring_client]
        $rd monitor
        assert_match {*OK*} [$rd read]
        r set foo bar
        r get foo
        set res [list [$rd read] [$rd read]]
        $rd close
        set _ $res
    } {*"set" "foo"*"get" "foo"*}
    """
    rd = ValkeyTestClient.create_from(r)
    rd.run("monitor")
    assert fnmatch(str(rd.run("read")), "*OK*")
    r.run("set", "foo", "bar")
    r.run("get", "foo")
    res = [rd.run("read"), rd.run("read")]
    rd.run("close")
    assert fnmatch(str(res), '*"set" "foo"*"get" "foo"*')


def test_monitor_properly_escapes_special_characters_through_sdscatrepr(r: ValkeyTestClient) -> None:
    """
    test {MONITOR properly escapes special characters through sdscatrepr} {
        set rd [valkey_deferring_client]
        $rd monitor
        assert_match {*OK*} [$rd read]
        r echo "backslash\\quotes\"newline\ncarriagereturn\rtab\talert\abackspace\bhexnormal\x7ahexspecial\x7f"
        assert_match {*"echo" "backslash\\\\quotes\\"newline\\ncarriagereturn\\rtab\\talert\\abackspace\\bhexnormalzhexspecial\\x7f"*} [$rd read]
        $rd close
    }
    """
    rd = ValkeyTestClient.create_from(r)
    rd.run("monitor")
    assert fnmatch(str(rd.run("read")), "*OK*")
    r.run("echo", 'backslash\quotes"newline\ncarriagereturn\rtab\talert\abackspace\bhexnormal\x7ahexspecial\x7f')
    assert fnmatch(
        str(rd.run("read")),
        '*"echo" "backslash\\\\\\\\quotes\\\\"newline\\\\ncarriagereturn\\\\rtab\\\\talert\\\\abackspace\\\\bhexnormalzhexspecial\\\\x7f"*',
    )
    rd.run("close")


def test_monitor_can_log_commands_issued_by_the_scripting_engine(r: ValkeyTestClient) -> None:
    """
    test {MONITOR can log commands issued by the scripting engine} {
        set rd [valkey_deferring_client]
        $rd monitor
        $rd read ;# Discard the OK
        r eval {redis.call('set',KEYS[1],ARGV[1])} 1 foo bar
        assert_match {*eval*} [$rd read]
        assert_match {*lua*"set"*"foo"*"bar"*} [$rd read]
        $rd close
    }
    """
    rd = ValkeyTestClient.create_from(r)
    rd.run("monitor")
    rd.run("read")
    r.run("eval", "redis.call('set',KEYS[1],ARGV[1])", 1, "foo", "bar")
    assert fnmatch(str(rd.run("read")), "*eval*")
    assert fnmatch(str(rd.run("read")), '*lua*"set"*"foo"*"bar"*')
    rd.run("close")


def test_monitor_can_log_commands_issued_by_functions(r: ValkeyTestClient) -> None:
    """
    test {MONITOR can log commands issued by functions} {
        r function load replace {#!lua name=test
            server.register_function('test', function() return redis.call('set', 'foo', 'bar') end)
        }
        set rd [valkey_deferring_client]
        $rd monitor
        $rd read ;# Discard the OK
        r fcall test 0
        assert_match {*fcall*test*} [$rd read]
        assert_match {*lua*"set"*"foo"*"bar"*} [$rd read]
        $rd close
    }
    """
    r.run(
        "function",
        "load",
        "replace",
        "#!lua name=test\n            server.register_function('test', function() return redis.call('set', 'foo', 'bar') end)\n        ",
    )
    rd = ValkeyTestClient.create_from(r)
    rd.run("monitor")
    rd.run("read")
    r.run("fcall", "test", 0)
    assert fnmatch(str(rd.run("read")), "*fcall*test*")
    assert fnmatch(str(rd.run("read")), '*lua*"set"*"foo"*"bar"*')
    rd.run("close")


def test_monitor_supports_redacting_command_arguments(r: ValkeyTestClient) -> None:
    """
    test {MONITOR supports redacting command arguments} {
        set rd [valkey_deferring_client]
        $rd monitor
        $rd read ; # Discard the OK

        r migrate [srv 0 host] [srv 0 port] key 9 5000
        r migrate [srv 0 host] [srv 0 port] key 9 5000 AUTH user
        r migrate [srv 0 host] [srv 0 port] key 9 5000 AUTH2 user password
        catch {r auth not-real} _
        catch {r auth not-real not-a-password} _

        assert_match {*"key"*"9"*"5000"*} [$rd read]
        assert_match {*"key"*"9"*"5000"*"(redacted)"*} [$rd read]
        assert_match {*"key"*"9"*"5000"*"(redacted)"*"(redacted)"*} [$rd read]
        assert_match {*"auth"*"(redacted)"*} [$rd read]
        assert_match {*"auth"*"(redacted)"*"(redacted)"*} [$rd read]

        foreach resp {3 2} {
            if {[lsearch $::denytags "resp3"] >= 0} {
                if {$resp == 3} {continue}
            } elseif {$::force_resp3} {
                if {$resp == 2} {continue}
            }
            catch {r hello $resp AUTH not-real not-a-password} _
            assert_match "*\"hello\"*\"$resp\"*\"AUTH\"*\"(redacted)\"*\"(redacted)\"*" [$rd read]
        }
        $rd close
    } {0} {needs:repl}
    """
    rd = ValkeyTestClient.create_from(r)
    rd.run("monitor")
    rd.run("read")
    r.run("migrate", r.host, r.port, "key", 9, 5000)
    r.run("migrate", r.host, r.port, "key", 9, 5000, "AUTH", "user")
    r.run("migrate", r.host, r.port, "key", 9, 5000, "AUTH2", "user", "password")
    try:
        _ = r.run("auth", "not-real")
    except Exception as _catch_err:
        _ = str(_catch_err)
    try:
        _ = r.run("auth", "not-real", "not-a-password")
    except Exception as _catch_err:
        _ = str(_catch_err)
    assert fnmatch(str(rd.run("read")), '*"key"*"9"*"5000"*')
    assert fnmatch(str(rd.run("read")), '*"key"*"9"*"5000"*"(redacted)"*')
    assert fnmatch(str(rd.run("read")), '*"key"*"9"*"5000"*"(redacted)"*"(redacted)"*')
    assert fnmatch(str(rd.run("read")), '*"auth"*"(redacted)"*')
    assert fnmatch(str(rd.run("read")), '*"auth"*"(redacted)"*"(redacted)"*')
    foreach(
        "resp",
        "3 2",
        '            if {[lsearch $::denytags "resp3"] >= 0} {\n                if {$resp == 3} {continue}\n            } elseif {$::force_resp3} {\n                if {$resp == 2} {continue}\n            }\n            catch {r hello $resp AUTH not-real not-a-password} _\n            assert_match "*\\"hello\\"*\\"$resp\\"*\\"AUTH\\"*\\"(redacted)\\"*\\"(redacted)\\"*" [$rd read]\n        ',
    )
    rd.run("close")


def test_monitor_correctly_handles_multi_exec_cases(r: ValkeyTestClient) -> None:
    """
    test {MONITOR correctly handles multi-exec cases} {
        set rd [valkey_deferring_client]
        $rd monitor
        $rd read ; # Discard the OK

        # Make sure multi-exec statements are ordered
        # correctly
        r multi
        r set foo bar
        r exec
        assert_match {*"multi"*} [$rd read]
        assert_match {*"set"*"foo"*"bar"*} [$rd read]
        assert_match {*"exec"*} [$rd read]

        # Make sure we close multi statements on errors
        r multi
        catch {r syntax error} _
        catch {r exec} _

        assert_match {*"multi"*} [$rd read]
        assert_match {*"exec"*} [$rd read]

        $rd close
    }
    """
    rd = ValkeyTestClient.create_from(r)
    rd.run("monitor")
    rd.run("read")
    r.run("multi")
    r.run("set", "foo", "bar")
    r.run("exec")
    assert fnmatch(str(rd.run("read")), '*"multi"*')
    assert fnmatch(str(rd.run("read")), '*"set"*"foo"*"bar"*')
    assert fnmatch(str(rd.run("read")), '*"exec"*')
    r.run("multi")
    try:
        _ = r.run("syntax", "error")
    except Exception as _catch_err:
        _ = str(_catch_err)
    try:
        _ = r.run("exec")
    except Exception as _catch_err:
        _ = str(_catch_err)
    assert fnmatch(str(rd.run("read")), '*"multi"*')
    assert fnmatch(str(rd.run("read")), '*"exec"*')
    rd.run("close")


def test_monitor_correctly_records_set_ex_in_multi_exec(r: ValkeyTestClient) -> None:
    """
    test {MONITOR correctly records SET EX in MULTI-EXEC} {
        # Start monitoring client
        set rd [valkey_deferring_client]
        $rd monitor
        $rd read ; # Discard the OK

        # Execute multi-exec block with SET EX commands
        r multi
        r set "{slot}key1" value1 ex 3600
        r set "{slot}key2" value2 ex 1800
        r exec

        # Verify monitor output shows the original commands:
        assert_match {*"multi"*} [$rd read]
        assert_match {*"set"*"{slot}key1"*"value1"*"ex"*"3600"*} [$rd read]
        assert_match {*"set"*"{slot}key2"*"value2"*"ex"*"1800"*} [$rd read]
        assert_match {*"exec"*} [$rd read]

        # Clean up monitoring client
        $rd close
    }
    """
    rd = ValkeyTestClient.create_from(r)
    rd.run("monitor")
    rd.run("read")
    r.run("multi")
    r.run("set", "{slot}key1", "value1", "ex", 3600)
    r.run("set", "{slot}key2", "value2", "ex", 1800)
    r.run("exec")
    assert fnmatch(str(rd.run("read")), '*"multi"*')
    assert fnmatch(str(rd.run("read")), '*"set"*"{slot}key1"*"value1"*"ex"*"3600"*')
    assert fnmatch(str(rd.run("read")), '*"set"*"{slot}key2"*"value2"*"ex"*"1800"*')
    assert fnmatch(str(rd.run("read")), '*"exec"*')
    rd.run("close")


def test_monitor_log_blocked_command_only_once(r: ValkeyTestClient) -> None:
    """
    test {MONITOR log blocked command only once} {
        # need to reconnect in order to reset the clients state
        reconnect

        set rd [valkey_deferring_client]
        set bc [valkey_deferring_client]
        r del mylist

        $rd monitor
        $rd read ; # Discard the OK

        $bc blpop mylist 0
        wait_for_blocked_clients_count 1
        r lpush mylist 1
        wait_for_blocked_clients_count 0
        r lpush mylist 2

        # we scan out all the info commands
        set monitor_output [$rd read]
        while { [string match {*"info"*} $monitor_output] } {
            set monitor_output [$rd read]
        }

        # we expect to see the blpop on the monitor first
        assert_match {*"blpop"*"mylist"*"0"*} $monitor_output

        # we scan out all the info commands on the monitor
        set monitor_output [$rd read]
        while { [string match {*"info"*} $monitor_output] } {
            set monitor_output [$rd read]
        }

        # we expect to locate the lpush right when the client was unblocked
        assert_match {*"lpush"*"mylist"*"1"*} $monitor_output

        # we scan out all the info commands
        set monitor_output [$rd read]
        while { [string match {*"info"*} $monitor_output] } {
            set monitor_output [$rd read]
        }

        # we expect to see the next lpush and not duplicate blpop command
        assert_match {*"lpush"*"mylist"*"2"*} $monitor_output

        $rd close
        $bc close
    }
    """
    reconnect()
    rd = ValkeyTestClient.create_from(r)
    bc = ValkeyTestClient.create_from(r)
    r.run("del", "mylist")
    rd.run("monitor")
    rd.run("read")
    bc.run("blpop", "mylist", 0)
    wait_for_blocked_clients_count(1)
    r.run("lpush", "mylist", 1)
    wait_for_blocked_clients_count(0)
    r.run("lpush", "mylist", 2)
    monitor_output = rd.run("read")
    while_(' [string match {*"info"*} $monitor_output] ', "            set monitor_output [$rd read]\n        ")
    assert fnmatch(str(monitor_output), '*"blpop"*"mylist"*"0"*')
    monitor_output = rd.run("read")
    while_(' [string match {*"info"*} $monitor_output] ', "            set monitor_output [$rd read]\n        ")
    assert fnmatch(str(monitor_output), '*"lpush"*"mylist"*"1"*')
    monitor_output = rd.run("read")
    while_(' [string match {*"info"*} $monitor_output] ', "            set monitor_output [$rd read]\n        ")
    assert fnmatch(str(monitor_output), '*"lpush"*"mylist"*"2"*')
    rd.run("close")
    bc.run("close")


def test_client_getname_should_return_nil_if_name_is_not_assigned(r: ValkeyTestClient) -> None:
    """
    test {CLIENT GETNAME should return NIL if name is not assigned} {
        r client getname
    } {}
    """
    r.run("client", "getname")


def test_client_getname_check_if_name_set_correctly(r: ValkeyTestClient) -> None:
    """
    test {CLIENT GETNAME check if name set correctly} {
        r client setname testName
        r client getName
    } {testName}
    """
    r.run("client", "setname", "testName")
    assert r.run("client", "getName") == "testName"


def test_client_list_shows_empty_fields_for_unassigned_names(r: ValkeyTestClient) -> None:
    """
    test {CLIENT LIST shows empty fields for unassigned names} {
        r client list
    } {*name= *}
    """
    assert fnmatch(str(r.run("client", "list")), "*name= *")


def test_client_setname_does_not_accept_spaces(r: ValkeyTestClient) -> None:
    """
    test {CLIENT SETNAME does not accept spaces} {
        catch {r client setname "foo bar"} e
        set e
    } {ERR*}
    """
    try:
        e = r.run("client", "setname", "foo bar")
    except Exception as _catch_err:
        e = str(_catch_err)
    assert fnmatch(str(e), "ERR*")


def test_client_setname_can_assign_a_name_to_this_connection(r: ValkeyTestClient) -> None:
    """
    test {CLIENT SETNAME can assign a name to this connection} {
        assert_equal [r client setname myname] {OK}
        r client list
    } {*name=myname*}
    """
    assert r.run("client", "setname", "myname") == "OK"
    assert fnmatch(str(r.run("client", "list")), "*name=myname*")


def test_client_setname_can_change_the_name_of_an_existing_connection(r: ValkeyTestClient) -> None:
    """
    test {CLIENT SETNAME can change the name of an existing connection} {
        assert_equal [r client setname someothername] {OK}
        r client list
    } {*name=someothername*}
    """
    assert r.run("client", "setname", "someothername") == "OK"
    assert fnmatch(str(r.run("client", "list")), "*name=someothername*")


def test_after_client_setname_connection_can_still_be_closed(r: ValkeyTestClient) -> None:
    """
    test {After CLIENT SETNAME, connection can still be closed} {
        set rd [valkey_deferring_client]
        $rd client setname foobar
        assert_equal [$rd read] "OK"
        assert_match {*foobar*} [r client list]
        $rd close
        # Now the client should no longer be listed
        wait_for_condition 50 100 {
            [string match {*foobar*} [r client list]] == 0
        } else {
            fail "Client still listed in CLIENT LIST after SETNAME."
        }
    }
    """
    rd = ValkeyTestClient.create_from(r)
    rd.run("client", "setname", "foobar")
    assert rd.run("read") == "OK"
    assert fnmatch(str(r.run("client", "list")), "*foobar*")
    rd.run("close")
    wait_for_condition(
        50,
        100,
        lambda: string("match", "*foobar*", r.run("client", "list")) == 0,
        lambda: fail("Client still listed in CLIENT LIST after SETNAME."),
    )


def test_client_setinfo_can_set_a_library_name_to_this_connection(r: ValkeyTestClient) -> None:
    """
    test {CLIENT SETINFO can set a library name to this connection} {
        r CLIENT SETINFO lib-name redis.py
        r CLIENT SETINFO lib-ver 1.2.3
        r client info
    } {*lib-name=redis.py lib-ver=1.2.3*}
    """
    r.run("CLIENT", "SETINFO", "lib-name", "redis.py")
    r.run("CLIENT", "SETINFO", "lib-ver", "1.2.3")
    assert fnmatch(str(r.run("client", "info")), "*lib-name=redis.py lib-ver=1.2.3*")


def test_client_setinfo_invalid_args(r: ValkeyTestClient) -> None:
    """
    test {CLIENT SETINFO invalid args} {
        assert_error {*wrong number of arguments*} {r CLIENT SETINFO lib-name}
        assert_error {*cannot contain spaces*} {r CLIENT SETINFO lib-name "valkey py"}
        assert_error {*newlines*} {r CLIENT SETINFO lib-name "redis.py\n"}
        assert_error {*Unrecognized*} {r CLIENT SETINFO badger hamster}
        # test that all of these didn't affect the previously set values
        r client info
    } {*lib-name=redis.py lib-ver=1.2.3*}
    """
    with pytest.raises(Exception, match=".*wrong\\ number\\ of\\ arguments.*"):
        r.run("CLIENT", "SETINFO", "lib-name")
    with pytest.raises(Exception, match=".*cannot\\ contain\\ spaces.*"):
        r.run("CLIENT", "SETINFO", "lib-name", "valkey py")
    with pytest.raises(Exception, match=".*newlines.*"):
        r.run("CLIENT", "SETINFO", "lib-name", "redis.py\n")
    with pytest.raises(Exception, match=".*Unrecognized.*"):
        r.run("CLIENT", "SETINFO", "badger", "hamster")
    assert fnmatch(str(r.run("client", "info")), "*lib-name=redis.py lib-ver=1.2.3*")


def test_reset_does_not_clean_library_name(r: ValkeyTestClient) -> None:
    """
    test {RESET does NOT clean library name} {
        r reset
        r client info
    } {*lib-name=redis.py*} {needs:reset}
    """
    r.run("reset")
    assert fnmatch(str(r.run("client", "info")), "*lib-name=redis.py*")


def test_client_setinfo_can_clear_library_name(r: ValkeyTestClient) -> None:
    """
    test {CLIENT SETINFO can clear library name} {
        r CLIENT SETINFO lib-name ""
        r client info
    } {*lib-name= *}
    """
    r.run("CLIENT", "SETINFO", "lib-name", "")
    assert fnmatch(str(r.run("client", "info")), "*lib-name= *")


def test_config_get_should_return_sorted_output(r: ValkeyTestClient) -> None:
    """
    test {CONFIG GET should return sorted output} {
        set config [r config get *]
        set keys {}
        foreach {key value} $config {
            lappend keys $key
        }
        assert_equal [lsort $keys] $keys
    }
    """
    config = r.run("config", "get", "*")
    keys = []
    foreach("key value", config, "            lappend keys $key\n        ")
    assert sorted(keys) == keys


def test_config_save_params_special_case_handled_properly(r: ValkeyTestClient) -> None:
    """
    test {CONFIG save params special case handled properly} {
        # No "save" keyword - defaults should apply
        start_server {config "minimal.conf"} {
            assert_match [r config get save] {save {3600 1 300 100 60 10000}}
        }

        # First "save" keyword overrides hard coded defaults
        start_server {config "minimal.conf" overrides {save {100 100}}} {
            # Defaults
            assert_match [r config get save] {save {100 100}}
        }

        # First "save" keyword appends default from config file
        start_server {config "default.conf" overrides {save {900 1}} args {--save 100 100}} {
            assert_match [r config get save] {save {900 1 100 100}}
        }

        # Empty "save" keyword resets all
        start_server {config "default.conf" overrides {save {900 1}} args {--save {}}} {
            assert_match [r config get save] {save {}}
        }
    } {} {external:skip}
    """
    start_server(
        'config "minimal.conf"',
        "            assert_match [r config get save] {save {3600 1 300 100 60 10000}}\n        ",
    )
    start_server(
        'config "minimal.conf" overrides {save {100 100}}',
        "            # Defaults\n            assert_match [r config get save] {save {100 100}}\n        ",
    )
    start_server(
        'config "default.conf" overrides {save {900 1}} args {--save 100 100}',
        "            assert_match [r config get save] {save {900 1 100 100}}\n        ",
    )
    start_server(
        'config "default.conf" overrides {save {900 1}} args {--save {}}',
        "            assert_match [r config get save] {save {}}\n        ",
    )


def test_config_sanity(r: ValkeyTestClient) -> None:
    """
    test {CONFIG sanity} {
        # Do CONFIG GET, CONFIG SET and then CONFIG GET again
        # Skip immutable configs, one with no get, and other complicated configs
        set skip_configs {
            rdbchecksum
            daemonize
            tcp-backlog
            mptcp
            repl-mptcp
            always-show-logo
            syslog-enabled
            cluster-enabled
            disable-thp
            aclfile
            unixsocket
            hash-seed
            pidfile
            syslog-ident
            appendfilename
            appenddirname
            supervised
            syslog-facility
            databases
            cluster-databases
            io-threads
            logfile
            unixsocketperm
            unixsocketgroup
            replicaof
            slaveof
            requirepass
            server-cpulist
            bio-cpulist
            aof-rewrite-cpulist
            bgsave-cpulist
            server_cpulist
            bio_cpulist
            aof_rewrite_cpulist
            bgsave_cpulist
            set-proc-title
            cluster-config-file
            cluster-port
            oom-score-adj
            oom-score-adj-values
            enable-protected-configs
            enable-debug-command
            enable-module-command
            dbfilename
            logfile
            dir
            socket-mark-id
            req-res-logfile
            client-default-resp
            dual-channel-replication-enabled
            rdma-completion-vector
            rdma-rx-size
            rdma-bind
            rdma-port
        }

        if {!$::tls} {
            append skip_configs {
                tls-prefer-server-ciphers
                tls-session-cache-timeout
                tls-session-cache-size
                tls-session-caching
                tls-cert-file
                tls-key-file
                tls-client-cert-file
                tls-client-key-file
                tls-dh-params-file
                tls-ca-cert-file
                tls-ca-cert-dir
                tls-protocols
                tls-ciphers
                tls-ciphersuites
                tls-port
            }
        }

        set configs {}
        foreach {k v} [r config get *] {
            if {[lsearch $skip_configs $k] != -1} {
                continue
            }
            dict set configs $k $v
            # try to set the config to the same value it already has
            r config set $k $v
        }

        set newconfigs {}
        foreach {k v} [r config get *] {
            if {[lsearch $skip_configs $k] != -1} {
                continue
            }
            dict set newconfigs $k $v
        }

        dict for {k v} $configs {
            set vv [dict get $newconfigs $k]
            if {$v != $vv} {
                fail "config $k mismatch, expecting $v but got $vv"
            }

        }
    }
    """
    skip_configs = "            rdbchecksum\n            daemonize\n            tcp-backlog\n            mptcp\n            repl-mptcp\n            always-show-logo\n            syslog-enabled\n            cluster-enabled\n            disable-thp\n            aclfile\n            unixsocket\n            hash-seed\n            pidfile\n            syslog-ident\n            appendfilename\n            appenddirname\n            supervised\n            syslog-facility\n            databases\n            cluster-databases\n            io-threads\n            logfile\n            unixsocketperm\n            unixsocketgroup\n            replicaof\n            slaveof\n            requirepass\n            server-cpulist\n            bio-cpulist\n            aof-rewrite-cpulist\n            bgsave-cpulist\n            server_cpulist\n            bio_cpulist\n            aof_rewrite_cpulist\n            bgsave_cpulist\n            set-proc-title\n            cluster-config-file\n            cluster-port\n            oom-score-adj\n            oom-score-adj-values\n            enable-protected-configs\n            enable-debug-command\n            enable-module-command\n            dbfilename\n            logfile\n            dir\n            socket-mark-id\n            req-res-logfile\n            client-default-resp\n            dual-channel-replication-enabled\n            rdma-completion-vector\n            rdma-rx-size\n            rdma-bind\n            rdma-port\n        "
    if_(
        "!$::tls",
        "            append skip_configs {\n                tls-prefer-server-ciphers\n                tls-session-cache-timeout\n                tls-session-cache-size\n                tls-session-caching\n                tls-cert-file\n                tls-key-file\n                tls-client-cert-file\n                tls-client-key-file\n                tls-dh-params-file\n                tls-ca-cert-file\n                tls-ca-cert-dir\n                tls-protocols\n                tls-ciphers\n                tls-ciphersuites\n                tls-port\n            }\n        ",
    )
    configs = ""
    foreach(
        "k v",
        r.run("config", "get", "*"),
        "            if {[lsearch $skip_configs $k] != -1} {\n                continue\n            }\n            dict set configs $k $v\n            # try to set the config to the same value it already has\n            r config set $k $v\n        ",
    )
    newconfigs = ""
    foreach(
        "k v",
        r.run("config", "get", "*"),
        "            if {[lsearch $skip_configs $k] != -1} {\n                continue\n            }\n            dict set newconfigs $k $v\n        ",
    )
    dict_(
        "for",
        "k v",
        configs,
        '            set vv [dict get $newconfigs $k]\n            if {$v != $vv} {\n                fail "config $k mismatch, expecting $v but got $vv"\n            }\n\n        ',
    )


def test_config_rewrite_sanity(r: ValkeyTestClient) -> None:
    """
    test {CONFIG REWRITE sanity} {
        # Capture state of config before
        set configs {}
        foreach {k v} [r config get *] {
            dict set configs $k $v
        }

        # Rewrite entire configuration, restart and confirm the
        # server is able to parse it and start.
        assert_equal [r debug config-rewrite-force-all] "OK"
        restart_server 0 true false
        wait_done_loading r

        # Verify no changes were introduced
        dict for {k v} $configs {
            assert_equal $v [lindex [r config get $k] 1]
        }
    } {} {external:skip}
    """
    configs = ""
    foreach("k v", r.run("config", "get", "*"), "            dict set configs $k $v\n        ")
    assert r.run("debug", "config-rewrite-force-all") == "OK"
    restart_server(0, "true", "false")
    wait_done_loading("r")
    dict_("for", "k v", configs, "            assert_equal $v [lindex [r config get $k] 1]\n        ")


def test_config_rewrite_handles_save_and_shutdown_properly(r: ValkeyTestClient) -> None:
    """
    test {CONFIG REWRITE handles save and shutdown properly} {
        r config set save "3600 1 300 100 60 10000"
        r config set shutdown-on-sigterm "nosave now"
        r config set shutdown-on-sigint "save"
        r config rewrite
        restart_server 0 true false
        assert_equal [r config get save] {save {3600 1 300 100 60 10000}}
        assert_equal [r config get shutdown-on-sigterm] {shutdown-on-sigterm {nosave now}}
        assert_equal [r config get shutdown-on-sigint] {shutdown-on-sigint save}

        r config set save ""
        r config set shutdown-on-sigterm "default"
        r config rewrite
        restart_server 0 true false
        assert_equal [r config get save] {save {}}
        assert_equal [r config get shutdown-on-sigterm] {shutdown-on-sigterm default}

        start_server {config "minimal.conf"} {
            assert_equal [r config get save] {save {3600 1 300 100 60 10000}}
            r config set save ""
            r config rewrite
            restart_server 0 true false
            assert_equal [r config get save] {save {}}
        }
    } {} {external:skip}
    """
    r.run("config", "set", "save", "3600 1 300 100 60 10000")
    r.run("config", "set", "shutdown-on-sigterm", "nosave now")
    r.run("config", "set", "shutdown-on-sigint", "save")
    r.run("config", "rewrite")
    restart_server(0, "true", "false")
    assert r.run("config", "get", "save") == "save {3600 1 300 100 60 10000}"
    assert r.run("config", "get", "shutdown-on-sigterm") == "shutdown-on-sigterm {nosave now}"
    assert r.run("config", "get", "shutdown-on-sigint") == "shutdown-on-sigint save"
    r.run("config", "set", "save", "")
    r.run("config", "set", "shutdown-on-sigterm", "default")
    r.run("config", "rewrite")
    restart_server(0, "true", "false")
    assert r.run("config", "get", "save") == "save {}"
    assert r.run("config", "get", "shutdown-on-sigterm") == "shutdown-on-sigterm default"
    start_server(
        'config "minimal.conf"',
        '            assert_equal [r config get save] {save {3600 1 300 100 60 10000}}\n            r config set save ""\n            r config rewrite\n            restart_server 0 true false\n            assert_equal [r config get save] {save {}}\n        ',
    )


def test_config_set_with_multiple_args(r: ValkeyTestClient) -> None:
    """
    test {CONFIG SET with multiple args} {
        set some_configs {maxmemory 10000001 repl-backlog-size 10000002 save {3000 5}}

        # Backup
        set backups {}
        foreach c [dict keys $some_configs] {
            lappend backups $c [lindex [r config get $c] 1]
        }

        # multi config set and veirfy
        assert_equal [eval "r config set $some_configs"] "OK"
        dict for {c val} $some_configs {
            assert_equal [lindex [r config get $c] 1] $val
        }

        # Restore backup
        assert_equal [eval "r config set $backups"] "OK"
    }
    """
    some_configs = "maxmemory 10000001 repl-backlog-size 10000002 save {3000 5}"
    backups = []
    foreach("c", dict_("keys", some_configs), "            lappend backups $c [lindex [r config get $c] 1]\n        ")
    assert eval_(f"r config set {some_configs}") == "OK"
    dict_("for", "c val", some_configs, "            assert_equal [lindex [r config get $c] 1] $val\n        ")
    assert eval_(f"r config set {backups}") == "OK"


def test_config_set_rollback_on_set_error(r: ValkeyTestClient) -> None:
    """
    test {CONFIG SET rollback on set error} {
        # This test passes an invalid percent value to maxmemory-clients which should cause an
        # input verification failure during the "set" phase before trying to apply the
        # configuration. We want to make sure the correct failure happens and everything
        # is rolled back.
        # backup maxmemory config
        set mm_backup [lindex [r config get maxmemory] 1]
        set mmc_backup [lindex [r config get maxmemory-clients] 1]
        set qbl_backup [lindex [r config get client-query-buffer-limit] 1]
        # Set some value to maxmemory
        assert_equal [r config set maxmemory 10000002] "OK"
        # Set another value to maxmemory together with another invalid config
        assert_error "ERR CONFIG SET failed (possibly related to argument 'maxmemory-clients') - percentage argument must be less or equal to 100" {
            r config set maxmemory 10000001 maxmemory-clients 200% client-query-buffer-limit invalid
        }
        # Validate we rolled back to original values
        assert_equal [lindex [r config get maxmemory] 1] 10000002
        assert_equal [lindex [r config get maxmemory-clients] 1] $mmc_backup
        assert_equal [lindex [r config get client-query-buffer-limit] 1] $qbl_backup
        # Make sure we revert back to the previous maxmemory
        assert_equal [r config set maxmemory $mm_backup] "OK"
    }
    """
    mm_backup = r.run("config", "get", "maxmemory")[1]
    mmc_backup = r.run("config", "get", "maxmemory-clients")[1]
    qbl_backup = r.run("config", "get", "client-query-buffer-limit")[1]
    assert r.run("config", "set", "maxmemory", 10000002) == "OK"
    with pytest.raises(
        Exception,
        match="ERR\\ CONFIG\\ SET\\ failed\\ \\(possibly\\ related\\ to\\ argument\\ 'maxmemory\\-clients'\\)\\ \\-\\ percentage\\ argument\\ must\\ be\\ less\\ or\\ equal\\ to\\ 100",
    ):
        r.run(
            "config", "set", "maxmemory", 10000001, "maxmemory-clients", "200%", "client-query-buffer-limit", "invalid"
        )
    assert r.run("config", "get", "maxmemory")[1] == 10000002
    assert r.run("config", "get", "maxmemory-clients")[1] == mmc_backup
    assert r.run("config", "get", "client-query-buffer-limit")[1] == qbl_backup
    assert r.run("config", "set", "maxmemory", mm_backup) == "OK"


@pytest.mark.xfail(reason="not implemented")
def test_config_set_rollback_on_apply_error(r: ValkeyTestClient) -> None:
    """
    test {CONFIG SET rollback on apply error} {
        # This test tries to configure a used port number in the server. This is expected
        # to pass the `CONFIG SET` validity checking implementation but fail on
        # actual "apply" of the setting. This will validate that after an "apply"
        # failure we rollback to the previous values.
        proc dummy_accept {chan addr port} {}

        set some_configs {maxmemory 10000001 port 0 client-query-buffer-limit 10m}

        # On Linux we also set the oom score adj which has an apply function. This is
        # used to verify that even successful applies are rolled back if some other
        # config's apply fails.
        set oom_adj_avail [expr {!$::external && [exec uname] == "Linux"}]
        if {$oom_adj_avail} {
            proc get_oom_score_adj {} {
                set pid [srv 0 pid]
                set fd [open "/proc/$pid/oom_score_adj" "r"]
                set val [gets $fd]
                close $fd
                return $val
            }
            set some_configs [linsert $some_configs 0 oom-score-adj yes oom-score-adj-values {1 1 1}]
            set read_oom_adj [get_oom_score_adj]
        }

        # Backup
        set backups {}
        foreach c [dict keys $some_configs] {
            lappend backups $c [lindex [r config get $c] 1]
        }

        set used_port [find_available_port $::baseport $::portcount]
        dict set some_configs port $used_port

        # Run a dummy server on used_port so we know we can't configure the server to
        # use it. It's ok for this to fail because that means used_port is invalid
        # anyway
        catch {socket -server dummy_accept -myaddr 127.0.0.1 $used_port} e
        if {$::verbose} { puts "dummy_accept: $e" }

        # Try to listen on the used port, pass some more configs to make sure the
        # returned failure message is for the first bad config and everything is rolled back.
        assert_error "ERR CONFIG SET failed (possibly related to argument 'port') - Unable to listen on this port*" {
            eval "r config set $some_configs"
        }

        # Make sure we reverted back to previous configs
        dict for {conf val} $backups {
            assert_equal [lindex [r config get $conf] 1] $val
        }

        if {$oom_adj_avail} {
            assert_equal [get_oom_score_adj] $read_oom_adj
        }

        # Make sure we can still communicate with the server (on the original port)
        set r1 [valkey_client]
        assert_equal [$r1 ping] "PONG"
        $r1 close
    }
    """
    proc("dummy_accept", "chan addr port", "")
    some_configs = "maxmemory 10000001 port 0 client-query-buffer-limit 10m"
    oom_adj_avail = expr('!$::external && [exec uname] == "Linux"')
    if_(
        "$oom_adj_avail",
        '            proc get_oom_score_adj {} {\n                set pid [srv 0 pid]\n                set fd [open "/proc/$pid/oom_score_adj" "r"]\n                set val [gets $fd]\n                close $fd\n                return $val\n            }\n            set some_configs [linsert $some_configs 0 oom-score-adj yes oom-score-adj-values {1 1 1}]\n            set read_oom_adj [get_oom_score_adj]\n        ',
    )
    backups = []
    foreach("c", dict_("keys", some_configs), "            lappend backups $c [lindex [r config get $c] 1]\n        ")
    # TODO: set used_port find_available_port $::baseport $::portcount
    # TODO: dict set some_configs port used_port
    catch("socket -server dummy_accept -myaddr 127.0.0.1 $used_port", "e")
    if False:
        pass
    assert_error(
        "ERR CONFIG SET failed (possibly related to argument 'port') - Unable to listen on this port*",
        '            eval "r config set $some_configs"\n        ',
    )
    dict_("for", "conf val", backups, "            assert_equal [lindex [r config get $conf] 1] $val\n        ")
    if_("$oom_adj_avail", "            assert_equal [get_oom_score_adj] $read_oom_adj\n        ")
    r1 = ValkeyTestClient.create_from(r)
    assert r1.run("ping") == "PONG"
    r1.run("close")


def test_config_set_duplicate_configs(r: ValkeyTestClient) -> None:
    """
    test {CONFIG SET duplicate configs} {
        assert_error "ERR *duplicate*" {r config set maxmemory 10000001 maxmemory 10000002}
    }
    """
    with pytest.raises(Exception, match="ERR\\ .*duplicate.*"):
        r.run("config", "set", "maxmemory", 10000001, "maxmemory", 10000002)


def test_config_set_set_immutable(r: ValkeyTestClient) -> None:
    """
    test {CONFIG SET set immutable} {
        assert_error "ERR *immutable*" {r config set daemonize yes}
    }
    """
    with pytest.raises(Exception, match="ERR\\ .*immutable.*"):
        r.run("config", "set", "daemonize", "yes")


def test_config_get_hidden_configs(r: ValkeyTestClient) -> None:
    """
    test {CONFIG GET hidden configs} {
        set hidden_config "key-load-delay"

        # When we use a pattern we shouldn't get the hidden config
        assert {![dict exists [r config get *] $hidden_config]}

        # When we explicitly request the hidden config we should get it
        assert {[dict exists [r config get $hidden_config] "$hidden_config"]}
    }
    """
    hidden_config = "key-load-delay"
    assert_("![dict exists [r config get *] $hidden_config]")
    assert dict_("exists", r.run("config", "get", hidden_config), f"{hidden_config}")


def test_config_get_multiple_args(r: ValkeyTestClient) -> None:
    """
    test {CONFIG GET multiple args} {
        set res [r config get maxmemory maxmemory* bind *of]

        # Verify there are no duplicates in the result
        assert_equal [expr [llength [dict keys $res]]*2] [llength $res]

        # Verify we got both name and alias in result
        assert {[dict exists $res slaveof] && [dict exists $res replicaof]}

        # Verify pattern found multiple maxmemory* configs
        assert {[dict exists $res maxmemory] && [dict exists $res maxmemory-samples] && [dict exists $res maxmemory-clients]}

        # Verify we also got the explicit config
        assert {[dict exists $res bind]}
    }
    """
    res = r.run("config", "get", "maxmemory", "maxmemory*", "bind", "*of")
    assert expr(len(dict_("keys", res)), "*2") == len(res)
    assert dict_("exists", res, "slaveof") and dict_("exists", res, "replicaof")
    assert (dict_("exists", res, "maxmemory") and dict_("exists", res, "maxmemory-samples")) and dict_(
        "exists", res, "maxmemory-clients"
    )
    assert dict_("exists", res, "bind")


@pytest.mark.xfail(reason="not implemented")
def test_valkey_server_command_line_arguments_error_cases(r: ValkeyTestClient) -> None:
    """
    test {valkey-server command line arguments - error cases} {
        # Take '--invalid' as the option.
        catch {exec $::VALKEY_SERVER_BIN --invalid} err
        assert_match {*Bad directive or wrong number of arguments*} $err

        catch {exec $::VALKEY_SERVER_BIN --port} err
        assert_match {*'port'*wrong number of arguments*} $err

        catch {exec $::VALKEY_SERVER_BIN --port 6380 --loglevel} err
        assert_match {*'loglevel'*wrong number of arguments*} $err

        # Take `6379` and `6380` as the port option value.
        catch {exec $::VALKEY_SERVER_BIN --port 6379 6380} err
        assert_match {*'port "6379" "6380"'*wrong number of arguments*} $err

        # Take `--loglevel` and `verbose` as the port option value.
        catch {exec $::VALKEY_SERVER_BIN --port --loglevel verbose} err
        assert_match {*'port "--loglevel" "verbose"'*wrong number of arguments*} $err

        # Take `--bla` as the port option value.
        catch {exec $::VALKEY_SERVER_BIN --port --bla --loglevel verbose} err
        assert_match {*'port "--bla"'*argument couldn't be parsed into an integer*} $err

        # Take `--bla` as the loglevel option value.
        catch {exec $::VALKEY_SERVER_BIN --logfile --my--log--file --loglevel --bla} err
        assert_match {*'loglevel "--bla"'*argument(s) must be one of the following*} $err

        # Using MULTI_ARG's own check, empty option value
        catch {exec $::VALKEY_SERVER_BIN --shutdown-on-sigint} err
        assert_match {*'shutdown-on-sigint'*argument(s) must be one of the following*} $err
        catch {exec $::VALKEY_SERVER_BIN --shutdown-on-sigint "now force" --shutdown-on-sigterm} err
        assert_match {*'shutdown-on-sigterm'*argument(s) must be one of the following*} $err

        # Something like `valkey-server --some-config --config-value1 --config-value2 --loglevel debug` would break,
        # because if you want to pass a value to a config starting with `--`, it can only be a single value.
        catch {exec $::VALKEY_SERVER_BIN --replicaof 127.0.0.1 abc} err
        assert_match {*'replicaof "127.0.0.1" "abc"'*Invalid primary port*} $err
        catch {exec $::VALKEY_SERVER_BIN --replicaof --127.0.0.1 abc} err
        assert_match {*'replicaof "--127.0.0.1" "abc"'*Invalid primary port*} $err
        catch {exec $::VALKEY_SERVER_BIN --replicaof --127.0.0.1 --abc} err
        assert_match {*'replicaof "--127.0.0.1"'*wrong number of arguments*} $err
    } {} {external:skip}
    """
    catch("exec $::VALKEY_SERVER_BIN --invalid", "err")
    # TODO: assert_match {*Bad directive or wrong number of arguments*} err
    catch("exec $::VALKEY_SERVER_BIN --port", "err")
    # TODO: assert_match {*'port'*wrong number of arguments*} err
    catch("exec $::VALKEY_SERVER_BIN --port 6380 --loglevel", "err")
    # TODO: assert_match {*'loglevel'*wrong number of arguments*} err
    catch("exec $::VALKEY_SERVER_BIN --port 6379 6380", "err")
    # TODO: assert_match {*'port "6379" "6380"'*wrong number of arguments*} err
    catch("exec $::VALKEY_SERVER_BIN --port --loglevel verbose", "err")
    # TODO: assert_match {*'port "--loglevel" "verbose"'*wrong number of arguments*} err
    catch("exec $::VALKEY_SERVER_BIN --port --bla --loglevel verbose", "err")
    # TODO: assert_match {*'port "--bla"'*argument couldn't be parsed into an integer*} err
    catch("exec $::VALKEY_SERVER_BIN --logfile --my--log--file --loglevel --bla", "err")
    # TODO: assert_match {*'loglevel "--bla"'*argument(s) must be one of the following*} err
    catch("exec $::VALKEY_SERVER_BIN --shutdown-on-sigint", "err")
    # TODO: assert_match {*'shutdown-on-sigint'*argument(s) must be one of the following*} err
    catch('exec $::VALKEY_SERVER_BIN --shutdown-on-sigint "now force" --shutdown-on-sigterm', "err")
    # TODO: assert_match {*'shutdown-on-sigterm'*argument(s) must be one of the following*} err
    catch("exec $::VALKEY_SERVER_BIN --replicaof 127.0.0.1 abc", "err")
    # TODO: assert_match {*'replicaof "127.0.0.1" "abc"'*Invalid primary port*} err
    catch("exec $::VALKEY_SERVER_BIN --replicaof --127.0.0.1 abc", "err")
    # TODO: assert_match {*'replicaof "--127.0.0.1" "abc"'*Invalid primary port*} err
    catch("exec $::VALKEY_SERVER_BIN --replicaof --127.0.0.1 --abc", "err")
    # TODO: assert_match {*'replicaof "--127.0.0.1"'*wrong number of arguments*} err


def test_tot_net_out_for_replica_client(r: ValkeyTestClient) -> None:
    """
    test {tot-net-out for replica client} {
        start_server {} {
            start_server {} {
                set primary [srv -1 client]
                set primary_host [srv -1 host]
                set primary_port [srv -1 port]
                set primary_pid [srv -1 pid]
                set replica [srv 0 client]
                set replica_pid [srv 0 pid]

                $replica replicaof $primary_host $primary_port

                # Wait for replica to be connected before proceeding.
                wait_replica_online $primary

                # Avoid PINGs to make sure tot-net-out is stable.
                $primary config set repl-ping-replica-period 3600

                # Increase repl timeout to avoid replica disconnecting
                $primary config set repl-timeout 3600
                $replica config set repl-timeout 3600

                # Get the tot-net-out of the replica before sending the command.
                set info_list [$primary client list]
                foreach info [split $info_list "\r\n"] {
                    if {[string match "* flags=S *" $info]} {
                        set out_before [get_field_in_client_info $info "tot-net-out"]
                        break
                    }
                }

                # Send a command to the primary.
                set value_size 10000
                $primary set foo [string repeat "a" $value_size]

                # Get the tot-net-out of the replica after sending the command.
                set info_list [$primary client list]
                foreach info [split $info_list "\r\n"] {
                    if {[string match "* flags=S *" $info]} {
                        set out_after [get_field_in_client_info $info "tot-net-out"]
                        break
                    }
                }

                assert_morethan $out_before 0
                assert_morethan $out_after 0
                assert_lessthan $out_after [expr $out_before + $value_size + 1000] ; # + 1000 to account for protocol overhead etc
            }
        }
    } {} {external:skip}
    """
    start_server(
        "",
        '            start_server {} {\n                set primary [srv -1 client]\n                set primary_host [srv -1 host]\n                set primary_port [srv -1 port]\n                set primary_pid [srv -1 pid]\n                set replica [srv 0 client]\n                set replica_pid [srv 0 pid]\n\n                $replica replicaof $primary_host $primary_port\n\n                # Wait for replica to be connected before proceeding.\n                wait_replica_online $primary\n\n                # Avoid PINGs to make sure tot-net-out is stable.\n                $primary config set repl-ping-replica-period 3600\n\n                # Increase repl timeout to avoid replica disconnecting\n                $primary config set repl-timeout 3600\n                $replica config set repl-timeout 3600\n\n                # Get the tot-net-out of the replica before sending the command.\n                set info_list [$primary client list]\n                foreach info [split $info_list "\\r\\n"] {\n                    if {[string match "* flags=S *" $info]} {\n                        set out_before [get_field_in_client_info $info "tot-net-out"]\n                        break\n                    }\n                }\n\n                # Send a command to the primary.\n                set value_size 10000\n                $primary set foo [string repeat "a" $value_size]\n\n                # Get the tot-net-out of the replica after sending the command.\n                set info_list [$primary client list]\n                foreach info [split $info_list "\\r\\n"] {\n                    if {[string match "* flags=S *" $info]} {\n                        set out_after [get_field_in_client_info $info "tot-net-out"]\n                        break\n                    }\n                }\n\n                assert_morethan $out_before 0\n                assert_morethan $out_after 0\n                assert_lessthan $out_after [expr $out_before + $value_size + 1000] ; # + 1000 to account for protocol overhead etc\n            }\n        ',
    )


def test_client_list_can_filter_by_lib_name(r: ValkeyTestClient) -> None:
    """
    test {CLIENT LIST can filter by LIB-NAME} {
        set c1 [valkey_client]
        $c1 client setinfo lib-name test-lib
        r CLIENT SETINFO lib-name mylib
        set result [r client list lib-name test-lib lib-name mylib]
        assert_match {*lib-name=mylib*} $result
        assert_no_match {*lib-name=test-lib*} $result
        catch {$c1 close}
    }
    """
    c1 = ValkeyTestClient.create_from(r)
    c1.run("client", "setinfo", "lib-name", "test-lib")
    r.run("CLIENT", "SETINFO", "lib-name", "mylib")
    result = r.run("client", "list", "lib-name", "test-lib", "lib-name", "mylib")
    assert fnmatch(str(result), "*lib-name=mylib*")
    assert_no_match("*lib-name=test-lib*", result)
    try:
        c1.run("close")
    except Exception:
        pass


def test_client_list_can_filter_by_lib_ver(r: ValkeyTestClient) -> None:
    """
    test {CLIENT LIST can filter by LIB-VER} {
        set c1 [valkey_client]
        $c1 client setinfo lib-ver 3.2.1
        r CLIENT SETINFO lib-ver 1.2.3
        set result [r client list lib-ver 3.2.1 lib-ver 1.2.3]
        assert_match {*lib-ver=1.2.3*} $result
        assert_no_match {*lib-ver=3.2.1*} $result
        catch {$c1 close}
    }
    """
    c1 = ValkeyTestClient.create_from(r)
    c1.run("client", "setinfo", "lib-ver", "3.2.1")
    r.run("CLIENT", "SETINFO", "lib-ver", "1.2.3")
    result = r.run("client", "list", "lib-ver", "3.2.1", "lib-ver", "1.2.3")
    assert fnmatch(str(result), "*lib-ver=1.2.3*")
    assert_no_match("*lib-ver=3.2.1*", result)
    try:
        c1.run("close")
    except Exception:
        pass


def test_client_list_can_filter_by_db_number(r: ValkeyTestClient) -> None:
    """
    test {CLIENT LIST can filter by DB number} {
        set c1 [valkey_client]
        $c1 select 0
        r select 2
        set result [r client list db 0 db 2]
        assert_match {*db=2*} $result
        assert_no_match {*db=0*} $result
        catch {$c1 close}
    }
    """
    c1 = ValkeyTestClient.create_from(r)
    c1.run("select", 0)
    r.run("select", 2)
    result = r.run("client", "list", "db", 0, "db", 2)
    assert fnmatch(str(result), "*db=2*")
    assert_no_match("*db=0*", result)
    try:
        c1.run("close")
    except Exception:
        pass


def test_client_kill_can_filter_by_db(r: ValkeyTestClient) -> None:
    """
    test {CLIENT KILL can filter by DB} {
        set c1 [valkey_client]

        $c1 select 2
        r select 0

        r client kill db 0 db 2

        set result [r client list]
        assert_no_match {*db=2*} $result
        assert_match {*db=0*} $result
        catch {$c1 close}
    }
    """
    c1 = ValkeyTestClient.create_from(r)
    c1.run("select", 2)
    r.run("select", 0)
    r.run("client", "kill", "db", 0, "db", 2)
    result = r.run("client", "list")
    assert_no_match("*db=2*", result)
    assert fnmatch(str(result), "*db=0*")
    try:
        c1.run("close")
    except Exception:
        pass


def test_client_kill_can_filter_by_lib_name(r: ValkeyTestClient) -> None:
    """
    test {CLIENT KILL can filter by LIB-NAME} {
        r client setinfo lib-name ""
        r client setinfo lib-ver ""
        set c1 [valkey_client]
        set c2 [valkey_client]

        $c1 client setinfo lib-name mylib
        $c2 client setinfo lib-name test
        $c2 client kill lib-name test lib-name mylib

        set result [$c2 client list]
        assert {[string match {*lib-name=mylib*} $result] == 0}

        catch {$c2 close}
    }
    """
    r.run("client", "setinfo", "lib-name", "")
    r.run("client", "setinfo", "lib-ver", "")
    c1 = ValkeyTestClient.create_from(r)
    c2 = ValkeyTestClient.create_from(r)
    c1.run("client", "setinfo", "lib-name", "mylib")
    c2.run("client", "setinfo", "lib-name", "test")
    c2.run("client", "kill", "lib-name", "test", "lib-name", "mylib")
    result = c2.run("client", "list")
    assert string("match", "*lib-name=mylib*", result) == 0
    try:
        c2.run("close")
    except Exception:
        pass


def test_client_kill_can_filter_by_lib_ver(r: ValkeyTestClient) -> None:
    """
    test {CLIENT KILL can filter by LIB-VER} {
        set c1 [valkey_client]
        set c2 [valkey_client]

        $c1 client setinfo lib-ver 1.2.3
        $c2 client setinfo lib-ver 3.2.1
        $c2 client kill lib-ver 3.2.1 lib-ver 1.2.3

        set result [$c2 client list]
        assert_no_match {*lib-ver=1.2.3*} $result
        assert_match {*lib-ver=3.2.1*} $result
        catch {$c1 close}
        catch {$c2 close}
    }
    """
    c1 = ValkeyTestClient.create_from(r)
    c2 = ValkeyTestClient.create_from(r)
    c1.run("client", "setinfo", "lib-ver", "1.2.3")
    c2.run("client", "setinfo", "lib-ver", "3.2.1")
    c2.run("client", "kill", "lib-ver", "3.2.1", "lib-ver", "1.2.3")
    result = c2.run("client", "list")
    assert_no_match("*lib-ver=1.2.3*", result)
    assert fnmatch(str(result), "*lib-ver=3.2.1*")
    try:
        c1.run("close")
    except Exception:
        pass
    try:
        c2.run("close")
    except Exception:
        pass


def test_client_list_can_filter_by_not_lib_name(r: ValkeyTestClient) -> None:
    """
    test {CLIENT LIST can filter by NOT-LIB-NAME} {
        set c1 [valkey_client]
        $c1 CLIENT SETINFO lib-name testlib
        r CLIENT SETINFO lib-name mylib
        set result [r client list not-lib-name testlib not-lib-name mylib]
        assert_no_match {*lib-name=mylib*} $result
        assert_match {*lib-name=testlib*} $result
        catch {$c1 close}
    }
    """
    c1 = ValkeyTestClient.create_from(r)
    c1.run("CLIENT", "SETINFO", "lib-name", "testlib")
    r.run("CLIENT", "SETINFO", "lib-name", "mylib")
    result = r.run("client", "list", "not-lib-name", "testlib", "not-lib-name", "mylib")
    assert_no_match("*lib-name=mylib*", result)
    assert fnmatch(str(result), "*lib-name=testlib*")
    try:
        c1.run("close")
    except Exception:
        pass


def test_client_list_can_filter_by_not_lib_ver(r: ValkeyTestClient) -> None:
    """
    test {CLIENT LIST can filter by NOT-LIB-VER} {
        set c1 [valkey_client]
        $c1 CLIENT SETINFO lib-ver 3.2.1
        r CLIENT SETINFO lib-ver 1.2.3
        set result [r client list not-lib-ver 3.2.1 not-lib-ver 1.2.3]
        assert_no_match {*lib-ver=1.2.3*} $result
        assert_match {*lib-ver=3.2.1*} $result
        catch {$c1 close}
    }
    """
    c1 = ValkeyTestClient.create_from(r)
    c1.run("CLIENT", "SETINFO", "lib-ver", "3.2.1")
    r.run("CLIENT", "SETINFO", "lib-ver", "1.2.3")
    result = r.run("client", "list", "not-lib-ver", "3.2.1", "not-lib-ver", "1.2.3")
    assert_no_match("*lib-ver=1.2.3*", result)
    assert fnmatch(str(result), "*lib-ver=3.2.1*")
    try:
        c1.run("close")
    except Exception:
        pass


def test_client_list_can_filter_by_not_db_number(r: ValkeyTestClient) -> None:
    """
    test {CLIENT LIST can filter by NOT-DB number} {
        set c1 [valkey_client]
        $c1 select 0
        r select 2
        set result [r client list not-db 0 not-db 2]
        assert_no_match {*db=2*} $result
        assert_match {*db=0*} $result
        catch {$c1 close}
    }
    """
    c1 = ValkeyTestClient.create_from(r)
    c1.run("select", 0)
    r.run("select", 2)
    result = r.run("client", "list", "not-db", 0, "not-db", 2)
    assert_no_match("*db=2*", result)
    assert fnmatch(str(result), "*db=0*")
    try:
        c1.run("close")
    except Exception:
        pass


def test_client_kill_can_filter_by_not_db(r: ValkeyTestClient) -> None:
    """
    test {CLIENT KILL can filter by NOT-DB} {
        set c1 [valkey_client]

        $c1 select 2
        r select 0

        r client kill not-db 2 not-db 0

        set result [r client list]
        assert_no_match {*db=2*} $result
        assert_match {*db=0*} $result
    }
    """
    c1 = ValkeyTestClient.create_from(r)
    c1.run("select", 2)
    r.run("select", 0)
    r.run("client", "kill", "not-db", 2, "not-db", 0)
    result = r.run("client", "list")
    assert_no_match("*db=2*", result)
    assert fnmatch(str(result), "*db=0*")


def test_client_kill_can_filter_by_not_lib_name(r: ValkeyTestClient) -> None:
    """
    test {CLIENT KILL can filter by NOT-LIB-NAME} {
        set c1 [valkey_client]
        set c2 [valkey_client]

        $c1 client setinfo lib-name mylib
        $c2 client setinfo lib-name not-mylib
        $c2 client kill not-lib-name mylib not-lib-name not-mylib

        set result [$c2 client list]
        assert_no_match {*lib-name=mylib*} $result
        assert_match {*lib-name=not-mylib*} $result


        catch {$c2 close}
    }
    """
    c1 = ValkeyTestClient.create_from(r)
    c2 = ValkeyTestClient.create_from(r)
    c1.run("client", "setinfo", "lib-name", "mylib")
    c2.run("client", "setinfo", "lib-name", "not-mylib")
    c2.run("client", "kill", "not-lib-name", "mylib", "not-lib-name", "not-mylib")
    result = c2.run("client", "list")
    assert_no_match("*lib-name=mylib*", result)
    assert fnmatch(str(result), "*lib-name=not-mylib*")
    try:
        c2.run("close")
    except Exception:
        pass


def test_client_kill_can_filter_by_not_lib_ver(r: ValkeyTestClient) -> None:
    """
    test {CLIENT KILL can filter by NOT-LIB-VER} {
        set c1 [valkey_client]
        set c2 [valkey_client]

        $c1 client setinfo lib-ver 1.2.3
        $c2 client kill not-lib-ver 1.2.3 not-lib-ver 0.0.0

        set result [$c2 client list]
        assert {[string match {*lib-ver=1.2.3*} $result] == 0}

        catch {$c2 close}
    }
    """
    c1 = ValkeyTestClient.create_from(r)
    c2 = ValkeyTestClient.create_from(r)
    c1.run("client", "setinfo", "lib-ver", "1.2.3")
    c2.run("client", "kill", "not-lib-ver", "1.2.3", "not-lib-ver", "0.0.0")
    result = c2.run("client", "list")
    assert string("match", "*lib-ver=1.2.3*", result) == 0
    try:
        c2.run("close")
    except Exception:
        pass


def test_valkey_server_command_line_arguments_allow_passing_option_name_and_option_value_in_the_same_arg(
    r: ValkeyTestClient,
) -> None:
    """
    test {valkey-server command line arguments - allow passing option name and option value in the same arg} {
        start_server {config "default.conf" args {"--maxmemory 700mb" "--maxmemory-policy volatile-lru"}} {
            assert_match [r config get maxmemory] {maxmemory 734003200}
            assert_match [r config get maxmemory-policy] {maxmemory-policy volatile-lru}
        }
    } {} {external:skip}
    """
    start_server(
        'config "default.conf" args {"--maxmemory 700mb" "--maxmemory-policy volatile-lru"}',
        "            assert_match [r config get maxmemory] {maxmemory 734003200}\n            assert_match [r config get maxmemory-policy] {maxmemory-policy volatile-lru}\n        ",
    )


def test_valkey_server_command_line_arguments_wrong_usage_that_we_support_anyway(r: ValkeyTestClient) -> None:
    """
    test {valkey-server command line arguments - wrong usage that we support anyway} {
        start_server {config "default.conf" args {loglevel verbose "--maxmemory '700mb'" "--maxmemory-policy 'volatile-lru'"}} {
            assert_match [r config get loglevel] {loglevel verbose}
            assert_match [r config get maxmemory] {maxmemory 734003200}
            assert_match [r config get maxmemory-policy] {maxmemory-policy volatile-lru}
        }
    } {} {external:skip}
    """
    start_server(
        'config "default.conf" args {loglevel verbose "--maxmemory \'700mb\'" "--maxmemory-policy \'volatile-lru\'"}',
        "            assert_match [r config get loglevel] {loglevel verbose}\n            assert_match [r config get maxmemory] {maxmemory 734003200}\n            assert_match [r config get maxmemory-policy] {maxmemory-policy volatile-lru}\n        ",
    )


def test_valkey_server_command_line_arguments_allow_option_value_to_use_the_prefix(r: ValkeyTestClient) -> None:
    """
    test {valkey-server command line arguments - allow option value to use the `--` prefix} {
        start_server {config "default.conf" args {--proc-title-template --my--title--template --loglevel verbose}} {
            assert_match [r config get proc-title-template] {proc-title-template --my--title--template}
            assert_match [r config get loglevel] {loglevel verbose}
        }
    } {} {external:skip}
    """
    start_server(
        'config "default.conf" args {--proc-title-template --my--title--template --loglevel verbose}',
        "            assert_match [r config get proc-title-template] {proc-title-template --my--title--template}\n            assert_match [r config get loglevel] {loglevel verbose}\n        ",
    )


def test_valkey_server_command_line_arguments_option_name_and_option_value_in_the_same_arg_and_prefix(
    r: ValkeyTestClient,
) -> None:
    """
    test {valkey-server command line arguments - option name and option value in the same arg and `--` prefix} {
        start_server {config "default.conf" args {"--proc-title-template --my--title--template" "--loglevel verbose"}} {
            assert_match [r config get proc-title-template] {proc-title-template --my--title--template}
            assert_match [r config get loglevel] {loglevel verbose}
        }
    } {} {external:skip}
    """
    start_server(
        'config "default.conf" args {"--proc-title-template --my--title--template" "--loglevel verbose"}',
        "            assert_match [r config get proc-title-template] {proc-title-template --my--title--template}\n            assert_match [r config get loglevel] {loglevel verbose}\n        ",
    )


def test_valkey_server_command_line_arguments_save_with_empty_input(r: ValkeyTestClient) -> None:
    """
    test {valkey-server command line arguments - save with empty input} {
        start_server {config "default.conf" args {--save --loglevel verbose}} {
            assert_match [r config get save] {save {}}
            assert_match [r config get loglevel] {loglevel verbose}
        }

        start_server {config "default.conf" args {--loglevel verbose --save}} {
            assert_match [r config get save] {save {}}
            assert_match [r config get loglevel] {loglevel verbose}
        }

        start_server {config "default.conf" args {--save {} --loglevel verbose}} {
            assert_match [r config get save] {save {}}
            assert_match [r config get loglevel] {loglevel verbose}
        }

        start_server {config "default.conf" args {--loglevel verbose --save {}}} {
            assert_match [r config get save] {save {}}
            assert_match [r config get loglevel] {loglevel verbose}
        }

        start_server {config "default.conf" args {--proc-title-template --save --save {} --loglevel verbose}} {
            assert_match [r config get proc-title-template] {proc-title-template --save}
            assert_match [r config get save] {save {}}
            assert_match [r config get loglevel] {loglevel verbose}
        }
    } {} {external:skip}
    """
    start_server(
        'config "default.conf" args {--save --loglevel verbose}',
        "            assert_match [r config get save] {save {}}\n            assert_match [r config get loglevel] {loglevel verbose}\n        ",
    )
    start_server(
        'config "default.conf" args {--loglevel verbose --save}',
        "            assert_match [r config get save] {save {}}\n            assert_match [r config get loglevel] {loglevel verbose}\n        ",
    )
    start_server(
        'config "default.conf" args {--save {} --loglevel verbose}',
        "            assert_match [r config get save] {save {}}\n            assert_match [r config get loglevel] {loglevel verbose}\n        ",
    )
    start_server(
        'config "default.conf" args {--loglevel verbose --save {}}',
        "            assert_match [r config get save] {save {}}\n            assert_match [r config get loglevel] {loglevel verbose}\n        ",
    )
    start_server(
        'config "default.conf" args {--proc-title-template --save --save {} --loglevel verbose}',
        "            assert_match [r config get proc-title-template] {proc-title-template --save}\n            assert_match [r config get save] {save {}}\n            assert_match [r config get loglevel] {loglevel verbose}\n        ",
    )


def test_valkey_server_command_line_arguments_take_one_bulk_string_with_spaces_for_multi_arg_configs_parsing(
    r: ValkeyTestClient,
) -> None:
    """
    test {valkey-server command line arguments - take one bulk string with spaces for MULTI_ARG configs parsing} {
        start_server {config "default.conf" args {--shutdown-on-sigint nosave force now --shutdown-on-sigterm "nosave force"}} {
            assert_match [r config get shutdown-on-sigint] {shutdown-on-sigint {nosave now force}}
            assert_match [r config get shutdown-on-sigterm] {shutdown-on-sigterm {nosave force}}
        }
    } {} {external:skip}
    """
    start_server(
        'config "default.conf" args {--shutdown-on-sigint nosave force now --shutdown-on-sigterm "nosave force"}',
        "            assert_match [r config get shutdown-on-sigint] {shutdown-on-sigint {nosave now force}}\n            assert_match [r config get shutdown-on-sigterm] {shutdown-on-sigterm {nosave force}}\n        ",
    )


def test_valkey_server_command_line_arguments_dir_multiple_times(r: ValkeyTestClient) -> None:
    """
    test {valkey-server command line arguments - dir multiple times} {
        start_server {config "default.conf" args {--dir "./" --dir "./"}} {
            r config get dir
            assert_equal {PONG} [r ping]
        }
    } {} {external:skip}
    """
    start_server(
        'config "default.conf" args {--dir "./" --dir "./"}',
        "            r config get dir\n            assert_equal {PONG} [r ping]\n        ",
    )


pytestmark = [pytest.mark.introspection_external_skip]


def test_auth_check_before_command_existence_check_and_command_arity_check(r: ValkeyTestClient) -> None:
    """
    test {auth check before command existence check and command arity check} {
        assert_error "NOAUTH *" {r non-existing-command}
        assert_error "NOAUTH *" {r set key value wrong_arg}
    }
    """
    with pytest.raises(Exception, match="NOAUTH\\ .*"):
        r.run("non-existing-command")
    with pytest.raises(Exception, match="NOAUTH\\ .*"):
        r.run("set", "key", "value", "wrong_arg")


def test_cannot_modify_protected_configuration_no(r: ValkeyTestClient) -> None:
    """
    test {cannot modify protected configuration - no} {
        assert_error "NOAUTH *" {r config set dir somedir}
        assert_error "NOAUTH *" {r DEBUG HELP}

        r auth mypass
        assert_error "ERR *protected*" {r config set dir somedir}
        assert_error "ERR *DEBUG command not allowed*" {r DEBUG HELP}
    } {} {needs:debug}
    """
    with pytest.raises(Exception, match="NOAUTH\\ .*"):
        r.run("config", "set", "dir", "somedir")
    with pytest.raises(Exception, match="NOAUTH\\ .*"):
        r.run("DEBUG", "HELP")
    r.run("auth", "mypass")
    with pytest.raises(Exception, match="ERR\\ .*protected.*"):
        r.run("config", "set", "dir", "somedir")
    with pytest.raises(Exception, match="ERR\\ .*DEBUG\\ command\\ not\\ allowed.*"):
        r.run("DEBUG", "HELP")


pytestmark = [pytest.mark.introspection_external_skip]


def test_cannot_modify_protected_configuration_local(r: ValkeyTestClient) -> None:
    """
    test {cannot modify protected configuration - local} {
        # verify that for local connection it doesn't error
        r config set dbfilename somename
        r DEBUG HELP

        # Get a non-loopback address of this instance for this test.
        set myaddr [get_nonloopback_addr]
        if {$myaddr != "" && ![string match {127.*} $myaddr]} {
            # Non-loopback client should fail
            set r2 [get_nonloopback_client]
            assert_error "ERR *protected*" {$r2 config set dir somedir}
            assert_error "ERR *DEBUG command not allowed*" {$r2 DEBUG HELP}
            assert_equal [$r2 close] 0
        }
    } {} {needs:debug}
    """
    r.run("config", "set", "dbfilename", "somename")
    r.run("DEBUG", "HELP")
    myaddr = get_nonloopback_addr()
    if_(
        '$myaddr != "" && ![string match {127.*} $myaddr]',
        '            # Non-loopback client should fail\n            set r2 [get_nonloopback_client]\n            assert_error "ERR *protected*" {$r2 config set dir somedir}\n            assert_error "ERR *DEBUG command not allowed*" {$r2 DEBUG HELP}\n            assert_equal [$r2 close] 0\n        ',
    )


"""
test {config during loading} {
    start_server [list overrides [list key-load-delay 50 loading-process-events-interval-bytes 1024 rdbcompression no save "900 1"]] {
        # create a big rdb that will take long to load. it is important
        # for keys to be big since the server processes events only once in 2mb.
        # 100mb of rdb, 100k keys will load in more than 5 seconds
        r debug populate 100000 key 1000

        restart_server 0 false false

        # make sure it's still loading
        assert_equal [s loading] 1

        # verify some configs are allowed during loading
        r config set loglevel debug
        assert_equal [lindex [r config get loglevel] 1] debug

        # verify some configs are forbidden during loading
        assert_error {LOADING*} {r config set dir asdf}

        # make sure it's still loading
        assert_equal [s loading] 1

        # no need to keep waiting for loading to complete
        exec kill [srv 0 pid]
    }
} {} {external:skip}
"""


"""
test {MEMORY commands during loading} {
    start_server [list overrides [list key-load-delay 50 loading-process-events-interval-bytes 1024]] {
        # Set up some initial data
        r debug populate 100000 key 1000

        # Save and restart
        r save
        restart_server 0 false false

        # At this point, keys are loaded one at time, busy looping 50usec
        # between each. Further, other events are processed every 1024 bytes
        # of RDB. We're sending all our commands deferred, so they have a
        # chance to be processed all at once between loading two keys.

        set rd [valkey_deferring_client]

        # Allowed during loading
        $rd memory help
        $rd memory malloc-stats
        $rd memory purge

        # Disallowed during loading (because directly dependent on the dataset)
        $rd memory doctor
        $rd memory stats
        $rd memory usage key:1

        # memory help
        assert_match {{MEMORY <subcommand> *}} [$rd read]
        # memory malloc-stats
        assert_match {*alloc*} [$rd read]
        # memory purge
        assert_match OK [$rd read]
        # memory doctor
        assert_error {*LOADING*} {$rd read}
        # memory stats
        assert_error {*LOADING*} {$rd read}
        # memory usage key:1
        assert_error {*LOADING*} {$rd read}

        $rd close
    }
} {} {external:skip}
"""


"""
test {CONFIG REWRITE handles rename-command properly} {
    start_server {tags {"introspection"} overrides {rename-command {flushdb badger}}} {
        assert_error {ERR unknown command*} {r flushdb}

        r config rewrite
        restart_server 0 true false

        assert_error {ERR unknown command*} {r flushdb}
    }
} {} {external:skip}
"""


"""
test {CONFIG REWRITE handles alias config properly} {
    start_server {tags {"introspection"} overrides {hash-max-listpack-entries 20 hash-max-ziplist-entries 21}} {
        assert_equal [r config get hash-max-listpack-entries] {hash-max-listpack-entries 21}
        assert_equal [r config get hash-max-ziplist-entries] {hash-max-ziplist-entries 21}
        r config set hash-max-listpack-entries 100

        r config rewrite
        restart_server 0 true false

        assert_equal [r config get hash-max-listpack-entries] {hash-max-listpack-entries 100}
    }
    # test the order doesn't matter
    start_server {tags {"introspection"} overrides {hash-max-ziplist-entries 20 hash-max-listpack-entries 21}} {
        assert_equal [r config get hash-max-listpack-entries] {hash-max-listpack-entries 21}
        assert_equal [r config get hash-max-ziplist-entries] {hash-max-ziplist-entries 21}
        r config set hash-max-listpack-entries 100

        r config rewrite
        restart_server 0 true false

        assert_equal [r config get hash-max-listpack-entries] {hash-max-listpack-entries 100}
    }
} {} {external:skip}
"""


"""
test {CONFIG hash-seed is immutable and settable at startup} {
    start_server {tags {"introspection"} overrides {hash-seed aabbccddeeffgghh}} {
        assert_error "ERR CONFIG SET failed (possibly related to argument 'hash-seed') - can't set immutable config*" {
            r config set hash-seed newseed
        }
    }
} {} {external:skip}
"""


# --- stubs for unimplemented TCL helpers ---


def assert_(*args):
    raise NotImplementedError("assert_")


def assert_error(*args):
    raise NotImplementedError("assert_error")


def assert_no_match(*args):
    raise NotImplementedError("assert_no_match")


def break_(*args):
    raise NotImplementedError("break_")


def catch(*args):
    raise NotImplementedError("catch")


def dict_(*args):
    raise NotImplementedError("dict_")


def eval_(*args):
    raise NotImplementedError("eval_")


def expr(*args):
    raise NotImplementedError("expr")


def fail(*args):
    raise NotImplementedError("fail")


def foreach(*args):
    raise NotImplementedError("foreach")


def get_client_tot_in_out_cmds(*args):
    raise NotImplementedError("get_client_tot_in_out_cmds")


def get_field_in_client_info(*args):
    raise NotImplementedError("get_field_in_client_info")


def get_field_in_client_list(*args):
    raise NotImplementedError("get_field_in_client_list")


def get_nonloopback_addr(*args):
    raise NotImplementedError("get_nonloopback_addr")


def get_oom_score_adj(*args):
    raise NotImplementedError("get_oom_score_adj")


def if_(*args):
    raise NotImplementedError("if_")


def proc(*args):
    raise NotImplementedError("proc")


def reconnect(*args):
    raise NotImplementedError("reconnect")


def regexp(*args):
    raise NotImplementedError("regexp")


def restart_server(*args):
    raise NotImplementedError("restart_server")


def s(*args):
    raise NotImplementedError("s")


def split(*args):
    raise NotImplementedError("split")


def start_server(*args):
    raise NotImplementedError("start_server")


def string(*args):
    raise NotImplementedError("string")


def wait_done_loading(*args):
    raise NotImplementedError("wait_done_loading")


def wait_for_blocked_clients_count(*args):
    raise NotImplementedError("wait_for_blocked_clients_count")


def wait_for_condition(*args):
    raise NotImplementedError("wait_for_condition")


def while_(*args):
    raise NotImplementedError("while_")
