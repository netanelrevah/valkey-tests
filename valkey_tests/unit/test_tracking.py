# ruff: noqa: PLR2004, PLR1714, F841, N806, ANN001, ANN002, ANN201
import time
from fnmatch import fnmatch

import pytest

from tests.valkey_test_client import ValkeyTestClient

pytestmark = [pytest.mark.tracking_network_logreqres_skip]


def test_client_tracking_prefixes_memory_overhead(r: ValkeyTestClient) -> None:
    """
    test {Client tracking prefixes memory overhead} {
        r CLIENT TRACKING off
        set tot_mem_before [get_field_in_client_info [r client info] "tot-mem"]

        # We add multiple $i to prefix to avoid prefix conflicts, so in this
        # args we will have about 20000 rax nodes.
        set args {}
        for {set i 0} {$i < 10240} {incr i} {
            lappend args PREFIX
            lappend args PREFIX-$i-$i-$i-$i-$i-$i-$i
        }
        r CLIENT TRACKING on BCAST {*}$args

        set arch_bits [s arch_bits]
        set tot_mem_after [get_field_in_client_info [r client info] "tot-mem"]
        set diff [expr $tot_mem_after - $tot_mem_before]

        # In 64 bits, before we would consume about 20000 * (4 * 8), that is 640000.
        # And now we are 20000 * (4 + 8), that is 240000.
        if {$arch_bits == 64} {
            assert_lessthan $diff 300000
        } elseif {$arch_bits == 32} {
            assert_lessthan $diff 200000
        }

        r CLIENT TRACKING off
    }
    """
    rd_redirection = ValkeyTestClient.create_from(r)
    rd_redirection.run("client", "id")
    redir_id = rd_redirection.run("read")
    rd_redirection.run("subscribe", "__redis__:invalidate")
    rd_redirection.run("read")
    rd = ValkeyTestClient.create_from(r)
    rd_sg = ValkeyTestClient.create_from(r)
    proc(
        "clean_all",
        "",
        "        uplevel {\n            # We should make r TRACKING off first. If r is in RESP3,\n            # r FLUSH ALL will send us tracking-redir-broken or other\n            # info which will not be consumed.\n            r CLIENT TRACKING off\n            $rd QUIT\n            $rd close\n            $rd_redirection QUIT\n            $rd_redirection close\n            set rd [valkey_deferring_client]\n            set rd_redirection [valkey_deferring_client]\n            $rd_redirection client id\n            set redir_id [$rd_redirection read]\n            $rd_redirection subscribe __redis__:invalidate\n            $rd_redirection read ; # Consume the SUBSCRIBE reply.\n            r FLUSHALL\n            r HELLO 2\n            r config set tracking-table-max-keys 1000000\n        }\n    ",
    )
    r.run("CLIENT", "TRACKING", "off")
    tot_mem_before = get_field_in_client_info(r.run("client", "info"), "tot-mem")
    args = []
    i = 0
    while i < 10240:
        args.append("PREFIX")
        args.append("PREFIX-$i-$i-$i-$i-$i-$i-$i")
        i += 1
    r.run("CLIENT", "TRACKING", "on", "BCAST", "*", args)
    arch_bits = s("arch_bits")
    tot_mem_after = get_field_in_client_info(r.run("client", "info"), "tot-mem")
    diff = expr(tot_mem_after, "-", tot_mem_before)
    if arch_bits == 64:
        assert diff < 300000
    elif arch_bits == 32:
        assert diff < 200000
    r.run("CLIENT", "TRACKING", "off")


def test_clients_are_able_to_enable_tracking_and_redirect_it(r: ValkeyTestClient) -> None:
    """
    test {Clients are able to enable tracking and redirect it} {
        r CLIENT TRACKING on REDIRECT $redir_id
    } {*OK}
    """
    rd_redirection = ValkeyTestClient.create_from(r)
    rd_redirection.run("client", "id")
    redir_id = rd_redirection.run("read")
    rd_redirection.run("subscribe", "__redis__:invalidate")
    rd_redirection.run("read")
    rd = ValkeyTestClient.create_from(r)
    rd_sg = ValkeyTestClient.create_from(r)
    proc(
        "clean_all",
        "",
        "        uplevel {\n            # We should make r TRACKING off first. If r is in RESP3,\n            # r FLUSH ALL will send us tracking-redir-broken or other\n            # info which will not be consumed.\n            r CLIENT TRACKING off\n            $rd QUIT\n            $rd close\n            $rd_redirection QUIT\n            $rd_redirection close\n            set rd [valkey_deferring_client]\n            set rd_redirection [valkey_deferring_client]\n            $rd_redirection client id\n            set redir_id [$rd_redirection read]\n            $rd_redirection subscribe __redis__:invalidate\n            $rd_redirection read ; # Consume the SUBSCRIBE reply.\n            r FLUSHALL\n            r HELLO 2\n            r config set tracking-table-max-keys 1000000\n        }\n    ",
    )
    assert fnmatch(str(r.run("CLIENT", "TRACKING", "on", "REDIRECT", redir_id)), "*OK")


def test_the_other_connection_is_able_to_get_invalidations(r: ValkeyTestClient) -> None:
    """
    test {The other connection is able to get invalidations} {
        r SET a{t} 1
        r SET b{t} 1
        r GET a{t}
        r INCR b{t} ; # This key should not be notified, since it wasn't fetched.
        r INCR a{t}
        set keys [lindex [$rd_redirection read] 2]
        assert {[llength $keys] == 1}
        assert {[lindex $keys 0] eq {a{t}}}
    }
    """
    rd_redirection = ValkeyTestClient.create_from(r)
    rd_redirection.run("client", "id")
    redir_id = rd_redirection.run("read")
    rd_redirection.run("subscribe", "__redis__:invalidate")
    rd_redirection.run("read")
    rd = ValkeyTestClient.create_from(r)
    rd_sg = ValkeyTestClient.create_from(r)
    proc(
        "clean_all",
        "",
        "        uplevel {\n            # We should make r TRACKING off first. If r is in RESP3,\n            # r FLUSH ALL will send us tracking-redir-broken or other\n            # info which will not be consumed.\n            r CLIENT TRACKING off\n            $rd QUIT\n            $rd close\n            $rd_redirection QUIT\n            $rd_redirection close\n            set rd [valkey_deferring_client]\n            set rd_redirection [valkey_deferring_client]\n            $rd_redirection client id\n            set redir_id [$rd_redirection read]\n            $rd_redirection subscribe __redis__:invalidate\n            $rd_redirection read ; # Consume the SUBSCRIBE reply.\n            r FLUSHALL\n            r HELLO 2\n            r config set tracking-table-max-keys 1000000\n        }\n    ",
    )
    r.run("SET", "a{t}", 1)
    r.run("SET", "b{t}", 1)
    r.run("GET", "a{t}")
    r.run("INCR", "b{t}")
    r.run("INCR", "a{t}")
    keys = rd_redirection.run("read")[2]
    assert len(keys) == 1
    assert keys[0] == "a{t}"


def test_the_client_is_now_able_to_disable_tracking(r: ValkeyTestClient) -> None:
    """
    test {The client is now able to disable tracking} {
        # Make sure to add a few more keys in the tracking list
        # so that we can check for leaks, as a side effect.
        r MGET a{t} b{t} c{t} d{t} e{t} f{t} g{t}
        r CLIENT TRACKING off
    } {*OK}
    """
    rd_redirection = ValkeyTestClient.create_from(r)
    rd_redirection.run("client", "id")
    redir_id = rd_redirection.run("read")
    rd_redirection.run("subscribe", "__redis__:invalidate")
    rd_redirection.run("read")
    rd = ValkeyTestClient.create_from(r)
    rd_sg = ValkeyTestClient.create_from(r)
    proc(
        "clean_all",
        "",
        "        uplevel {\n            # We should make r TRACKING off first. If r is in RESP3,\n            # r FLUSH ALL will send us tracking-redir-broken or other\n            # info which will not be consumed.\n            r CLIENT TRACKING off\n            $rd QUIT\n            $rd close\n            $rd_redirection QUIT\n            $rd_redirection close\n            set rd [valkey_deferring_client]\n            set rd_redirection [valkey_deferring_client]\n            $rd_redirection client id\n            set redir_id [$rd_redirection read]\n            $rd_redirection subscribe __redis__:invalidate\n            $rd_redirection read ; # Consume the SUBSCRIBE reply.\n            r FLUSHALL\n            r HELLO 2\n            r config set tracking-table-max-keys 1000000\n        }\n    ",
    )
    r.run("MGET", "a{t}", "b{t}", "c{t}", "d{t}", "e{t}", "f{t}", "g{t}")
    assert fnmatch(str(r.run("CLIENT", "TRACKING", "off")), "*OK")


def test_clients_can_enable_the_bcast_mode_with_the_empty_prefix(r: ValkeyTestClient) -> None:
    """
    test {Clients can enable the BCAST mode with the empty prefix} {
        r CLIENT TRACKING on BCAST REDIRECT $redir_id
    } {*OK*}
    """
    rd_redirection = ValkeyTestClient.create_from(r)
    rd_redirection.run("client", "id")
    redir_id = rd_redirection.run("read")
    rd_redirection.run("subscribe", "__redis__:invalidate")
    rd_redirection.run("read")
    rd = ValkeyTestClient.create_from(r)
    rd_sg = ValkeyTestClient.create_from(r)
    proc(
        "clean_all",
        "",
        "        uplevel {\n            # We should make r TRACKING off first. If r is in RESP3,\n            # r FLUSH ALL will send us tracking-redir-broken or other\n            # info which will not be consumed.\n            r CLIENT TRACKING off\n            $rd QUIT\n            $rd close\n            $rd_redirection QUIT\n            $rd_redirection close\n            set rd [valkey_deferring_client]\n            set rd_redirection [valkey_deferring_client]\n            $rd_redirection client id\n            set redir_id [$rd_redirection read]\n            $rd_redirection subscribe __redis__:invalidate\n            $rd_redirection read ; # Consume the SUBSCRIBE reply.\n            r FLUSHALL\n            r HELLO 2\n            r config set tracking-table-max-keys 1000000\n        }\n    ",
    )
    assert fnmatch(str(r.run("CLIENT", "TRACKING", "on", "BCAST", "REDIRECT", redir_id)), "*OK*")


def test_the_connection_gets_invalidation_messages_about_all_the_keys(r: ValkeyTestClient) -> None:
    """
    test {The connection gets invalidation messages about all the keys} {
        r MSET a{t} 1 b{t} 2 c{t} 3
        set keys [lsort [lindex [$rd_redirection read] 2]]
        assert {$keys eq {a{t} b{t} c{t}}}
    }
    """
    rd_redirection = ValkeyTestClient.create_from(r)
    rd_redirection.run("client", "id")
    redir_id = rd_redirection.run("read")
    rd_redirection.run("subscribe", "__redis__:invalidate")
    rd_redirection.run("read")
    rd = ValkeyTestClient.create_from(r)
    rd_sg = ValkeyTestClient.create_from(r)
    proc(
        "clean_all",
        "",
        "        uplevel {\n            # We should make r TRACKING off first. If r is in RESP3,\n            # r FLUSH ALL will send us tracking-redir-broken or other\n            # info which will not be consumed.\n            r CLIENT TRACKING off\n            $rd QUIT\n            $rd close\n            $rd_redirection QUIT\n            $rd_redirection close\n            set rd [valkey_deferring_client]\n            set rd_redirection [valkey_deferring_client]\n            $rd_redirection client id\n            set redir_id [$rd_redirection read]\n            $rd_redirection subscribe __redis__:invalidate\n            $rd_redirection read ; # Consume the SUBSCRIBE reply.\n            r FLUSHALL\n            r HELLO 2\n            r config set tracking-table-max-keys 1000000\n        }\n    ",
    )
    r.run("MSET", "a{t}", 1, "b{t}", 2, "c{t}", 3)
    keys = sorted(rd_redirection.run("read")[2])
    assert keys == "a{t} b{t} c{t}"


def test_clients_can_enable_the_bcast_mode_with_prefixes(r: ValkeyTestClient) -> None:
    """
    test {Clients can enable the BCAST mode with prefixes} {
        r CLIENT TRACKING off
        r CLIENT TRACKING on BCAST REDIRECT $redir_id PREFIX a: PREFIX b:
        r MULTI
        r INCR a:1{t}
        r INCR a:2{t}
        r INCR b:1{t}
        r INCR b:2{t}
        # we should not get this key
        r INCR c:1{t}
        r EXEC
        # Because of the internals, we know we are going to receive
        # two separated notifications for the two different prefixes.
        set keys1 [lsort [lindex [$rd_redirection read] 2]]
        set keys2 [lsort [lindex [$rd_redirection read] 2]]
        set keys [lsort [list {*}$keys1 {*}$keys2]]
        assert {$keys eq {a:1{t} a:2{t} b:1{t} b:2{t}}}
    }
    """
    rd_redirection = ValkeyTestClient.create_from(r)
    rd_redirection.run("client", "id")
    redir_id = rd_redirection.run("read")
    rd_redirection.run("subscribe", "__redis__:invalidate")
    rd_redirection.run("read")
    rd = ValkeyTestClient.create_from(r)
    rd_sg = ValkeyTestClient.create_from(r)
    proc(
        "clean_all",
        "",
        "        uplevel {\n            # We should make r TRACKING off first. If r is in RESP3,\n            # r FLUSH ALL will send us tracking-redir-broken or other\n            # info which will not be consumed.\n            r CLIENT TRACKING off\n            $rd QUIT\n            $rd close\n            $rd_redirection QUIT\n            $rd_redirection close\n            set rd [valkey_deferring_client]\n            set rd_redirection [valkey_deferring_client]\n            $rd_redirection client id\n            set redir_id [$rd_redirection read]\n            $rd_redirection subscribe __redis__:invalidate\n            $rd_redirection read ; # Consume the SUBSCRIBE reply.\n            r FLUSHALL\n            r HELLO 2\n            r config set tracking-table-max-keys 1000000\n        }\n    ",
    )
    r.run("CLIENT", "TRACKING", "off")
    r.run("CLIENT", "TRACKING", "on", "BCAST", "REDIRECT", redir_id, "PREFIX", "a:", "PREFIX", "b:")
    r.run("MULTI")
    r.run("INCR", "a:1{t}")
    r.run("INCR", "a:2{t}")
    r.run("INCR", "b:1{t}")
    r.run("INCR", "b:2{t}")
    r.run("INCR", "c:1{t}")
    r.run("EXEC")
    keys1 = sorted(rd_redirection.run("read")[2])
    keys2 = sorted(rd_redirection.run("read")[2])
    keys = sorted(["*", keys1, "*", keys2])
    assert keys == "a:1{t} a:2{t} b:1{t} b:2{t}"


def test_adding_prefixes_to_bcast_mode_works(r: ValkeyTestClient) -> None:
    """
    test {Adding prefixes to BCAST mode works} {
        r CLIENT TRACKING on BCAST REDIRECT $redir_id PREFIX c:
        r INCR c:1234
        set keys [lsort [lindex [$rd_redirection read] 2]]
        assert {$keys eq {c:1234}}
    }
    """
    rd_redirection = ValkeyTestClient.create_from(r)
    rd_redirection.run("client", "id")
    redir_id = rd_redirection.run("read")
    rd_redirection.run("subscribe", "__redis__:invalidate")
    rd_redirection.run("read")
    rd = ValkeyTestClient.create_from(r)
    rd_sg = ValkeyTestClient.create_from(r)
    proc(
        "clean_all",
        "",
        "        uplevel {\n            # We should make r TRACKING off first. If r is in RESP3,\n            # r FLUSH ALL will send us tracking-redir-broken or other\n            # info which will not be consumed.\n            r CLIENT TRACKING off\n            $rd QUIT\n            $rd close\n            $rd_redirection QUIT\n            $rd_redirection close\n            set rd [valkey_deferring_client]\n            set rd_redirection [valkey_deferring_client]\n            $rd_redirection client id\n            set redir_id [$rd_redirection read]\n            $rd_redirection subscribe __redis__:invalidate\n            $rd_redirection read ; # Consume the SUBSCRIBE reply.\n            r FLUSHALL\n            r HELLO 2\n            r config set tracking-table-max-keys 1000000\n        }\n    ",
    )
    r.run("CLIENT", "TRACKING", "on", "BCAST", "REDIRECT", redir_id, "PREFIX", "c:")
    r.run("INCR", "c:1234")
    keys = sorted(rd_redirection.run("read")[2])
    assert keys == "c:1234"


def test_tracking_noloop_mode_in_standard_mode_works(r: ValkeyTestClient) -> None:
    """
    test {Tracking NOLOOP mode in standard mode works} {
        r CLIENT TRACKING off
        r CLIENT TRACKING on REDIRECT $redir_id NOLOOP
        r MGET otherkey1{t} loopkey{t} otherkey2{t}
        $rd_sg SET otherkey1{t} 1; # We should get this
        r SET loopkey{t} 1 ; # We should not get this
        $rd_sg SET otherkey2{t} 1; # We should get this
        # Because of the internals, we know we are going to receive
        # two separated notifications for the two different keys.
        set keys1 [lsort [lindex [$rd_redirection read] 2]]
        set keys2 [lsort [lindex [$rd_redirection read] 2]]
        set keys [lsort [list {*}$keys1 {*}$keys2]]
        assert {$keys eq {otherkey1{t} otherkey2{t}}}
    }
    """
    rd_redirection = ValkeyTestClient.create_from(r)
    rd_redirection.run("client", "id")
    redir_id = rd_redirection.run("read")
    rd_redirection.run("subscribe", "__redis__:invalidate")
    rd_redirection.run("read")
    rd = ValkeyTestClient.create_from(r)
    rd_sg = ValkeyTestClient.create_from(r)
    proc(
        "clean_all",
        "",
        "        uplevel {\n            # We should make r TRACKING off first. If r is in RESP3,\n            # r FLUSH ALL will send us tracking-redir-broken or other\n            # info which will not be consumed.\n            r CLIENT TRACKING off\n            $rd QUIT\n            $rd close\n            $rd_redirection QUIT\n            $rd_redirection close\n            set rd [valkey_deferring_client]\n            set rd_redirection [valkey_deferring_client]\n            $rd_redirection client id\n            set redir_id [$rd_redirection read]\n            $rd_redirection subscribe __redis__:invalidate\n            $rd_redirection read ; # Consume the SUBSCRIBE reply.\n            r FLUSHALL\n            r HELLO 2\n            r config set tracking-table-max-keys 1000000\n        }\n    ",
    )
    r.run("CLIENT", "TRACKING", "off")
    r.run("CLIENT", "TRACKING", "on", "REDIRECT", redir_id, "NOLOOP")
    r.run("MGET", "otherkey1{t}", "loopkey{t}", "otherkey2{t}")
    rd_sg.run("SET", "otherkey1{t}", 1)
    r.run("SET", "loopkey{t}", 1)
    rd_sg.run("SET", "otherkey2{t}", 1)
    keys1 = sorted(rd_redirection.run("read")[2])
    keys2 = sorted(rd_redirection.run("read")[2])
    keys = sorted(["*", keys1, "*", keys2])
    assert keys == "otherkey1{t} otherkey2{t}"


def test_tracking_noloop_mode_in_bcast_mode_works(r: ValkeyTestClient) -> None:
    """
    test {Tracking NOLOOP mode in BCAST mode works} {
        r CLIENT TRACKING off
        r CLIENT TRACKING on BCAST REDIRECT $redir_id NOLOOP
        $rd_sg SET otherkey1 1; # We should get this
        r SET loopkey 1 ; # We should not get this
        $rd_sg SET otherkey2 1; # We should get this
        # Because $rd_sg send command synchronously, we know we are
        # going to receive two separated notifications.
        set keys1 [lsort [lindex [$rd_redirection read] 2]]
        set keys2 [lsort [lindex [$rd_redirection read] 2]]
        set keys [lsort [list {*}$keys1 {*}$keys2]]
        assert {$keys eq {otherkey1 otherkey2}}
    }
    """
    rd_redirection = ValkeyTestClient.create_from(r)
    rd_redirection.run("client", "id")
    redir_id = rd_redirection.run("read")
    rd_redirection.run("subscribe", "__redis__:invalidate")
    rd_redirection.run("read")
    rd = ValkeyTestClient.create_from(r)
    rd_sg = ValkeyTestClient.create_from(r)
    proc(
        "clean_all",
        "",
        "        uplevel {\n            # We should make r TRACKING off first. If r is in RESP3,\n            # r FLUSH ALL will send us tracking-redir-broken or other\n            # info which will not be consumed.\n            r CLIENT TRACKING off\n            $rd QUIT\n            $rd close\n            $rd_redirection QUIT\n            $rd_redirection close\n            set rd [valkey_deferring_client]\n            set rd_redirection [valkey_deferring_client]\n            $rd_redirection client id\n            set redir_id [$rd_redirection read]\n            $rd_redirection subscribe __redis__:invalidate\n            $rd_redirection read ; # Consume the SUBSCRIBE reply.\n            r FLUSHALL\n            r HELLO 2\n            r config set tracking-table-max-keys 1000000\n        }\n    ",
    )
    r.run("CLIENT", "TRACKING", "off")
    r.run("CLIENT", "TRACKING", "on", "BCAST", "REDIRECT", redir_id, "NOLOOP")
    rd_sg.run("SET", "otherkey1", 1)
    r.run("SET", "loopkey", 1)
    rd_sg.run("SET", "otherkey2", 1)
    keys1 = sorted(rd_redirection.run("read")[2])
    keys2 = sorted(rd_redirection.run("read")[2])
    keys = sorted(["*", keys1, "*", keys2])
    assert keys == "otherkey1 otherkey2"


def test_tracking_gets_notification_of_expired_keys(r: ValkeyTestClient) -> None:
    """
    test {Tracking gets notification of expired keys} {
        r CLIENT TRACKING off
        r CLIENT TRACKING on BCAST REDIRECT $redir_id NOLOOP
        r SET mykey myval px 1
        r SET mykeyotherkey myval ; # We should not get it
        after 1000
        set keys [lsort [lindex [$rd_redirection read] 2]]
        assert {$keys eq {mykey}}
    }
    """
    rd_redirection = ValkeyTestClient.create_from(r)
    rd_redirection.run("client", "id")
    redir_id = rd_redirection.run("read")
    rd_redirection.run("subscribe", "__redis__:invalidate")
    rd_redirection.run("read")
    rd = ValkeyTestClient.create_from(r)
    rd_sg = ValkeyTestClient.create_from(r)
    proc(
        "clean_all",
        "",
        "        uplevel {\n            # We should make r TRACKING off first. If r is in RESP3,\n            # r FLUSH ALL will send us tracking-redir-broken or other\n            # info which will not be consumed.\n            r CLIENT TRACKING off\n            $rd QUIT\n            $rd close\n            $rd_redirection QUIT\n            $rd_redirection close\n            set rd [valkey_deferring_client]\n            set rd_redirection [valkey_deferring_client]\n            $rd_redirection client id\n            set redir_id [$rd_redirection read]\n            $rd_redirection subscribe __redis__:invalidate\n            $rd_redirection read ; # Consume the SUBSCRIBE reply.\n            r FLUSHALL\n            r HELLO 2\n            r config set tracking-table-max-keys 1000000\n        }\n    ",
    )
    r.run("CLIENT", "TRACKING", "off")
    r.run("CLIENT", "TRACKING", "on", "BCAST", "REDIRECT", redir_id, "NOLOOP")
    r.run("SET", "mykey", "myval", "px", 1)
    r.run("SET", "mykeyotherkey", "myval")
    time.sleep(1000 / 1000)
    keys = sorted(rd_redirection.run("read")[2])
    assert keys == "mykey"


def test_tracking_gets_notification_of_lazy_expired_keys(r: ValkeyTestClient) -> None:
    """
    test {Tracking gets notification of lazy expired keys} {
        r CLIENT TRACKING off
        r CLIENT TRACKING on BCAST REDIRECT $redir_id NOLOOP
        # Use multi-exec to expose a race where the key gets an two invalidations
        # in the same event loop, once by the client so filtered by NOLOOP, and
        # the second one by the lazy expire
        r MULTI
        r SET mykey{t} myval px 1
        r SET mykeyotherkey{t} myval ; # We should not get it
        r DEBUG SLEEP 0.1
        r GET mykey{t}
        r EXEC
        set keys [lsort [lindex [$rd_redirection read] 2]]
        assert {$keys eq {mykey{t}}}
    } {} {needs:debug}
    """
    rd_redirection = ValkeyTestClient.create_from(r)
    rd_redirection.run("client", "id")
    redir_id = rd_redirection.run("read")
    rd_redirection.run("subscribe", "__redis__:invalidate")
    rd_redirection.run("read")
    rd = ValkeyTestClient.create_from(r)
    rd_sg = ValkeyTestClient.create_from(r)
    proc(
        "clean_all",
        "",
        "        uplevel {\n            # We should make r TRACKING off first. If r is in RESP3,\n            # r FLUSH ALL will send us tracking-redir-broken or other\n            # info which will not be consumed.\n            r CLIENT TRACKING off\n            $rd QUIT\n            $rd close\n            $rd_redirection QUIT\n            $rd_redirection close\n            set rd [valkey_deferring_client]\n            set rd_redirection [valkey_deferring_client]\n            $rd_redirection client id\n            set redir_id [$rd_redirection read]\n            $rd_redirection subscribe __redis__:invalidate\n            $rd_redirection read ; # Consume the SUBSCRIBE reply.\n            r FLUSHALL\n            r HELLO 2\n            r config set tracking-table-max-keys 1000000\n        }\n    ",
    )
    r.run("CLIENT", "TRACKING", "off")
    r.run("CLIENT", "TRACKING", "on", "BCAST", "REDIRECT", redir_id, "NOLOOP")
    r.run("MULTI")
    r.run("SET", "mykey{t}", "myval", "px", 1)
    r.run("SET", "mykeyotherkey{t}", "myval")
    r.run("DEBUG", "SLEEP", 0.1)
    r.run("GET", "mykey{t}")
    r.run("EXEC")
    keys = sorted(rd_redirection.run("read")[2])
    assert keys == "mykey{t}"


def test_hello_3_reply_is_correct(r: ValkeyTestClient) -> None:
    """
    test {HELLO 3 reply is correct} {
        set reply [r HELLO 3]
        assert_equal [dict get $reply proto] 3
    }
    """
    rd_redirection = ValkeyTestClient.create_from(r)
    rd_redirection.run("client", "id")
    redir_id = rd_redirection.run("read")
    rd_redirection.run("subscribe", "__redis__:invalidate")
    rd_redirection.run("read")
    rd = ValkeyTestClient.create_from(r)
    rd_sg = ValkeyTestClient.create_from(r)
    proc(
        "clean_all",
        "",
        "        uplevel {\n            # We should make r TRACKING off first. If r is in RESP3,\n            # r FLUSH ALL will send us tracking-redir-broken or other\n            # info which will not be consumed.\n            r CLIENT TRACKING off\n            $rd QUIT\n            $rd close\n            $rd_redirection QUIT\n            $rd_redirection close\n            set rd [valkey_deferring_client]\n            set rd_redirection [valkey_deferring_client]\n            $rd_redirection client id\n            set redir_id [$rd_redirection read]\n            $rd_redirection subscribe __redis__:invalidate\n            $rd_redirection read ; # Consume the SUBSCRIBE reply.\n            r FLUSHALL\n            r HELLO 2\n            r config set tracking-table-max-keys 1000000\n        }\n    ",
    )
    reply = r.run("HELLO", 3)
    assert reply["proto"] == 3


def test_resp3_based_basic_invalidation(r: ValkeyTestClient) -> None:
    """
    test {RESP3 based basic invalidation} {
        r CLIENT TRACKING off
        r CLIENT TRACKING on
        $rd_sg SET key1 1
        r GET key1
        $rd_sg SET key1 2
        r read
    } {invalidate key1}
    """
    rd_redirection = ValkeyTestClient.create_from(r)
    rd_redirection.run("client", "id")
    redir_id = rd_redirection.run("read")
    rd_redirection.run("subscribe", "__redis__:invalidate")
    rd_redirection.run("read")
    rd = ValkeyTestClient.create_from(r)
    rd_sg = ValkeyTestClient.create_from(r)
    proc(
        "clean_all",
        "",
        "        uplevel {\n            # We should make r TRACKING off first. If r is in RESP3,\n            # r FLUSH ALL will send us tracking-redir-broken or other\n            # info which will not be consumed.\n            r CLIENT TRACKING off\n            $rd QUIT\n            $rd close\n            $rd_redirection QUIT\n            $rd_redirection close\n            set rd [valkey_deferring_client]\n            set rd_redirection [valkey_deferring_client]\n            $rd_redirection client id\n            set redir_id [$rd_redirection read]\n            $rd_redirection subscribe __redis__:invalidate\n            $rd_redirection read ; # Consume the SUBSCRIBE reply.\n            r FLUSHALL\n            r HELLO 2\n            r config set tracking-table-max-keys 1000000\n        }\n    ",
    )
    r.run("CLIENT", "TRACKING", "off")
    r.run("CLIENT", "TRACKING", "on")
    rd_sg.run("SET", "key1", 1)
    r.run("GET", "key1")
    rd_sg.run("SET", "key1", 2)
    assert r.run("read") == "invalidate key1"


def test_resp3_tracking_redirection(r: ValkeyTestClient) -> None:
    """
    test {RESP3 tracking redirection} {
        r CLIENT TRACKING off
        r CLIENT TRACKING on REDIRECT $redir_id
        $rd_sg SET key1 1
        r GET key1
        $rd_sg SET key1 2
        set res [lindex [$rd_redirection read] 2]
        assert {$res eq {key1}}
    }
    """
    rd_redirection = ValkeyTestClient.create_from(r)
    rd_redirection.run("client", "id")
    redir_id = rd_redirection.run("read")
    rd_redirection.run("subscribe", "__redis__:invalidate")
    rd_redirection.run("read")
    rd = ValkeyTestClient.create_from(r)
    rd_sg = ValkeyTestClient.create_from(r)
    proc(
        "clean_all",
        "",
        "        uplevel {\n            # We should make r TRACKING off first. If r is in RESP3,\n            # r FLUSH ALL will send us tracking-redir-broken or other\n            # info which will not be consumed.\n            r CLIENT TRACKING off\n            $rd QUIT\n            $rd close\n            $rd_redirection QUIT\n            $rd_redirection close\n            set rd [valkey_deferring_client]\n            set rd_redirection [valkey_deferring_client]\n            $rd_redirection client id\n            set redir_id [$rd_redirection read]\n            $rd_redirection subscribe __redis__:invalidate\n            $rd_redirection read ; # Consume the SUBSCRIBE reply.\n            r FLUSHALL\n            r HELLO 2\n            r config set tracking-table-max-keys 1000000\n        }\n    ",
    )
    r.run("CLIENT", "TRACKING", "off")
    r.run("CLIENT", "TRACKING", "on", "REDIRECT", redir_id)
    rd_sg.run("SET", "key1", 1)
    r.run("GET", "key1")
    rd_sg.run("SET", "key1", 2)
    res = rd_redirection.run("read")[2]
    assert res == "key1"


def test_invalidations_of_previous_keys_can_be_redirected_after_switching_to_resp3(r: ValkeyTestClient) -> None:
    """
    test {Invalidations of previous keys can be redirected after switching to RESP3} {
        r HELLO 2
        $rd_sg SET key1 1
        r GET key1
        r HELLO 3
        $rd_sg SET key1 2
        set res [lindex [$rd_redirection read] 2]
        assert {$res eq {key1}}
    }
    """
    rd_redirection = ValkeyTestClient.create_from(r)
    rd_redirection.run("client", "id")
    redir_id = rd_redirection.run("read")
    rd_redirection.run("subscribe", "__redis__:invalidate")
    rd_redirection.run("read")
    rd = ValkeyTestClient.create_from(r)
    rd_sg = ValkeyTestClient.create_from(r)
    proc(
        "clean_all",
        "",
        "        uplevel {\n            # We should make r TRACKING off first. If r is in RESP3,\n            # r FLUSH ALL will send us tracking-redir-broken or other\n            # info which will not be consumed.\n            r CLIENT TRACKING off\n            $rd QUIT\n            $rd close\n            $rd_redirection QUIT\n            $rd_redirection close\n            set rd [valkey_deferring_client]\n            set rd_redirection [valkey_deferring_client]\n            $rd_redirection client id\n            set redir_id [$rd_redirection read]\n            $rd_redirection subscribe __redis__:invalidate\n            $rd_redirection read ; # Consume the SUBSCRIBE reply.\n            r FLUSHALL\n            r HELLO 2\n            r config set tracking-table-max-keys 1000000\n        }\n    ",
    )
    r.run("HELLO", 2)
    rd_sg.run("SET", "key1", 1)
    r.run("GET", "key1")
    r.run("HELLO", 3)
    rd_sg.run("SET", "key1", 2)
    res = rd_redirection.run("read")[2]
    assert res == "key1"


def test_invalidations_of_new_keys_can_be_redirected_after_switching_to_resp3(r: ValkeyTestClient) -> None:
    """
    test {Invalidations of new keys can be redirected after switching to RESP3} {
        r HELLO 3
        $rd_sg SET key1 1
        r GET key1
        $rd_sg SET key1 2
        set res [lindex [$rd_redirection read] 2]
        assert {$res eq {key1}}
    }
    """
    rd_redirection = ValkeyTestClient.create_from(r)
    rd_redirection.run("client", "id")
    redir_id = rd_redirection.run("read")
    rd_redirection.run("subscribe", "__redis__:invalidate")
    rd_redirection.run("read")
    rd = ValkeyTestClient.create_from(r)
    rd_sg = ValkeyTestClient.create_from(r)
    proc(
        "clean_all",
        "",
        "        uplevel {\n            # We should make r TRACKING off first. If r is in RESP3,\n            # r FLUSH ALL will send us tracking-redir-broken or other\n            # info which will not be consumed.\n            r CLIENT TRACKING off\n            $rd QUIT\n            $rd close\n            $rd_redirection QUIT\n            $rd_redirection close\n            set rd [valkey_deferring_client]\n            set rd_redirection [valkey_deferring_client]\n            $rd_redirection client id\n            set redir_id [$rd_redirection read]\n            $rd_redirection subscribe __redis__:invalidate\n            $rd_redirection read ; # Consume the SUBSCRIBE reply.\n            r FLUSHALL\n            r HELLO 2\n            r config set tracking-table-max-keys 1000000\n        }\n    ",
    )
    r.run("HELLO", 3)
    rd_sg.run("SET", "key1", 1)
    r.run("GET", "key1")
    rd_sg.run("SET", "key1", 2)
    res = rd_redirection.run("read")[2]
    assert res == "key1"


def test_invalid_keys_should_not_be_tracked_for_scripts_in_noloop_mode(r: ValkeyTestClient) -> None:
    """
    test {Invalid keys should not be tracked for scripts in NOLOOP mode} {
        $rd_sg CLIENT TRACKING off
        $rd_sg CLIENT TRACKING on NOLOOP
        $rd_sg HELLO 3
        $rd_sg SET key1 1
        assert_equal "1" [$rd_sg GET key1]

        # For write command in script, invalid key should not be tracked with NOLOOP flag
        $rd_sg eval "return redis.call('set', 'key1', '2')" 1 key1
        assert_equal "2" [$rd_sg GET key1]
        $rd_sg CLIENT TRACKING off
    }
    """
    rd_redirection = ValkeyTestClient.create_from(r)
    rd_redirection.run("client", "id")
    redir_id = rd_redirection.run("read")
    rd_redirection.run("subscribe", "__redis__:invalidate")
    rd_redirection.run("read")
    rd = ValkeyTestClient.create_from(r)
    rd_sg = ValkeyTestClient.create_from(r)
    proc(
        "clean_all",
        "",
        "        uplevel {\n            # We should make r TRACKING off first. If r is in RESP3,\n            # r FLUSH ALL will send us tracking-redir-broken or other\n            # info which will not be consumed.\n            r CLIENT TRACKING off\n            $rd QUIT\n            $rd close\n            $rd_redirection QUIT\n            $rd_redirection close\n            set rd [valkey_deferring_client]\n            set rd_redirection [valkey_deferring_client]\n            $rd_redirection client id\n            set redir_id [$rd_redirection read]\n            $rd_redirection subscribe __redis__:invalidate\n            $rd_redirection read ; # Consume the SUBSCRIBE reply.\n            r FLUSHALL\n            r HELLO 2\n            r config set tracking-table-max-keys 1000000\n        }\n    ",
    )
    rd_sg.run("CLIENT", "TRACKING", "off")
    rd_sg.run("CLIENT", "TRACKING", "on", "NOLOOP")
    rd_sg.run("HELLO", 3)
    rd_sg.run("SET", "key1", 1)
    assert "1" == rd_sg.run("GET", "key1")
    rd_sg.run("eval", "return redis.call('set', 'key1', '2')", 1, "key1")
    assert "2" == rd_sg.run("GET", "key1")
    rd_sg.run("CLIENT", "TRACKING", "off")


def test_tracking_only_occurs_for_scripts_when_a_command_calls_a_read_only_command(r: ValkeyTestClient) -> None:
    """
    test {Tracking only occurs for scripts when a command calls a read-only command} {
        r CLIENT TRACKING off
        r CLIENT TRACKING on
        $rd_sg MSET key2{t} 1 key2{t} 1

        # If a script doesn't call any read command, don't track any keys
        r EVAL "redis.call('set', 'key3{t}', 'bar')" 2 key1{t} key2{t}
        $rd_sg MSET key2{t} 2 key1{t} 2
        assert_equal "PONG" [r ping]

        # If a script calls a read command, just the read keys
        r EVAL "redis.call('get', 'key2{t}')" 2 key1{t} key2{t}
        $rd_sg MSET key2{t} 2 key3{t} 2
        assert_equal {invalidate key2{t}} [r read]
        assert_equal "PONG" [r ping]

        # RO variants work like the normal variants

        # If a RO script doesn't call any read command, don't track any keys
        r EVAL_RO "redis.call('ping')" 2 key1{t} key2{t}
        $rd_sg MSET key2{t} 2 key1{t} 2
        assert_equal "PONG" [r ping]

        # If a RO script calls a read command, just the read keys
        r EVAL_RO "redis.call('get', 'key2{t}')" 2 key1{t} key2{t}
        $rd_sg MSET key2{t} 2 key3{t} 2
        assert_equal {invalidate key2{t}} [r read]
        assert_equal "PONG" [r ping]
    }
    """
    rd_redirection = ValkeyTestClient.create_from(r)
    rd_redirection.run("client", "id")
    redir_id = rd_redirection.run("read")
    rd_redirection.run("subscribe", "__redis__:invalidate")
    rd_redirection.run("read")
    rd = ValkeyTestClient.create_from(r)
    rd_sg = ValkeyTestClient.create_from(r)
    proc(
        "clean_all",
        "",
        "        uplevel {\n            # We should make r TRACKING off first. If r is in RESP3,\n            # r FLUSH ALL will send us tracking-redir-broken or other\n            # info which will not be consumed.\n            r CLIENT TRACKING off\n            $rd QUIT\n            $rd close\n            $rd_redirection QUIT\n            $rd_redirection close\n            set rd [valkey_deferring_client]\n            set rd_redirection [valkey_deferring_client]\n            $rd_redirection client id\n            set redir_id [$rd_redirection read]\n            $rd_redirection subscribe __redis__:invalidate\n            $rd_redirection read ; # Consume the SUBSCRIBE reply.\n            r FLUSHALL\n            r HELLO 2\n            r config set tracking-table-max-keys 1000000\n        }\n    ",
    )
    r.run("CLIENT", "TRACKING", "off")
    r.run("CLIENT", "TRACKING", "on")
    rd_sg.run("MSET", "key2{t}", 1, "key2{t}", 1)
    r.run("EVAL", "redis.call('set', 'key3{t}', 'bar')", 2, "key1{t}", "key2{t}")
    rd_sg.run("MSET", "key2{t}", 2, "key1{t}", 2)
    assert "PONG" == r.run("ping")
    r.run("EVAL", "redis.call('get', 'key2{t}')", 2, "key1{t}", "key2{t}")
    rd_sg.run("MSET", "key2{t}", 2, "key3{t}", 2)
    assert "invalidate key2{t}" == r.run("read")
    assert "PONG" == r.run("ping")
    r.run("EVAL_RO", "redis.call('ping')", 2, "key1{t}", "key2{t}")
    rd_sg.run("MSET", "key2{t}", 2, "key1{t}", 2)
    assert "PONG" == r.run("ping")
    r.run("EVAL_RO", "redis.call('get', 'key2{t}')", 2, "key1{t}", "key2{t}")
    rd_sg.run("MSET", "key2{t}", 2, "key3{t}", 2)
    assert "invalidate key2{t}" == r.run("read")
    assert "PONG" == r.run("ping")


def test_resp3_client_gets_tracking_redir_broken_push_message_after_cached_key_changed_when_rediretion_client_is_terminated(
    r: ValkeyTestClient,
) -> None:
    """
    test {RESP3 Client gets tracking-redir-broken push message after cached key changed when rediretion client is terminated} {
        # make sure r is working resp 3
        r HELLO 3
        r CLIENT TRACKING on REDIRECT $redir_id
        set redir_error "tracking-redir-broken $redir_id"
        $rd_sg SET key1 1
        r GET key1
        $rd_redirection QUIT
        assert_equal OK [$rd_redirection read]
        $rd_redirection close
        $rd_sg SET key1 2

        # Reinstantiating after QUIT
        set rd_redirection [valkey_deferring_client]
        $rd_redirection CLIENT ID
        set redir_id [$rd_redirection read]
        $rd_redirection SUBSCRIBE __redis__:invalidate
        $rd_redirection read ; # Consume the SUBSCRIBE reply

        # Wait to read the tracking-redir-broken
        wait_for_condition 1000 50 {
            [set response [r PING]] != "PONG"
        } else {
            fail "Failed to get redirect broken indication"
        }
        assert_equal $redir_error $response
        # Consume PING reply
        assert_equal PONG [r read]
    }
    """
    rd_redirection = ValkeyTestClient.create_from(r)
    rd_redirection.run("client", "id")
    redir_id = rd_redirection.run("read")
    rd_redirection.run("subscribe", "__redis__:invalidate")
    rd_redirection.run("read")
    rd = ValkeyTestClient.create_from(r)
    rd_sg = ValkeyTestClient.create_from(r)
    proc(
        "clean_all",
        "",
        "        uplevel {\n            # We should make r TRACKING off first. If r is in RESP3,\n            # r FLUSH ALL will send us tracking-redir-broken or other\n            # info which will not be consumed.\n            r CLIENT TRACKING off\n            $rd QUIT\n            $rd close\n            $rd_redirection QUIT\n            $rd_redirection close\n            set rd [valkey_deferring_client]\n            set rd_redirection [valkey_deferring_client]\n            $rd_redirection client id\n            set redir_id [$rd_redirection read]\n            $rd_redirection subscribe __redis__:invalidate\n            $rd_redirection read ; # Consume the SUBSCRIBE reply.\n            r FLUSHALL\n            r HELLO 2\n            r config set tracking-table-max-keys 1000000\n        }\n    ",
    )
    r.run("HELLO", 3)
    r.run("CLIENT", "TRACKING", "on", "REDIRECT", redir_id)
    redir_error = f"tracking-redir-broken {redir_id}"
    rd_sg.run("SET", "key1", 1)
    r.run("GET", "key1")
    rd_redirection.run("QUIT")
    assert "OK" == rd_redirection.run("read")
    rd_redirection.run("close")
    rd_sg.run("SET", "key1", 2)
    rd_redirection = ValkeyTestClient.create_from(r)
    rd_redirection.run("CLIENT", "ID")
    redir_id = rd_redirection.run("read")
    rd_redirection.run("SUBSCRIBE", "__redis__:invalidate")
    rd_redirection.run("read")
    wait_for_condition(
        1000, 50, lambda: r.run("PING") != "PONG", lambda: fail("Failed to get redirect broken indication")
    )
    assert redir_error == response
    assert "PONG" == r.run("read")


def test_different_clients_can_redirect_to_the_same_connection(r: ValkeyTestClient) -> None:
    """
    test {Different clients can redirect to the same connection} {
        r CLIENT TRACKING on REDIRECT $redir_id
        $rd CLIENT TRACKING on REDIRECT $redir_id
        assert_equal OK [$rd read] ; # Consume the TRACKING reply
        $rd_sg MSET key1{t} 1 key2{t} 1
        r GET key1{t}
        $rd GET key2{t}
        assert_equal 1 [$rd read] ; # Consume the GET reply
        $rd_sg INCR key1{t}
        $rd_sg INCR key2{t}
        set res1 [lindex [$rd_redirection read] 2]
        set res2 [lindex [$rd_redirection read] 2]
        assert {$res1 eq {key1{t}}}
        assert {$res2 eq {key2{t}}}
    }
    """
    rd_redirection = ValkeyTestClient.create_from(r)
    rd_redirection.run("client", "id")
    redir_id = rd_redirection.run("read")
    rd_redirection.run("subscribe", "__redis__:invalidate")
    rd_redirection.run("read")
    rd = ValkeyTestClient.create_from(r)
    rd_sg = ValkeyTestClient.create_from(r)
    proc(
        "clean_all",
        "",
        "        uplevel {\n            # We should make r TRACKING off first. If r is in RESP3,\n            # r FLUSH ALL will send us tracking-redir-broken or other\n            # info which will not be consumed.\n            r CLIENT TRACKING off\n            $rd QUIT\n            $rd close\n            $rd_redirection QUIT\n            $rd_redirection close\n            set rd [valkey_deferring_client]\n            set rd_redirection [valkey_deferring_client]\n            $rd_redirection client id\n            set redir_id [$rd_redirection read]\n            $rd_redirection subscribe __redis__:invalidate\n            $rd_redirection read ; # Consume the SUBSCRIBE reply.\n            r FLUSHALL\n            r HELLO 2\n            r config set tracking-table-max-keys 1000000\n        }\n    ",
    )
    r.run("CLIENT", "TRACKING", "on", "REDIRECT", redir_id)
    rd.run("CLIENT", "TRACKING", "on", "REDIRECT", redir_id)
    assert "OK" == rd.run("read")
    rd_sg.run("MSET", "key1{t}", 1, "key2{t}", 1)
    r.run("GET", "key1{t}")
    rd.run("GET", "key2{t}")
    assert 1 == rd.run("read")
    rd_sg.run("INCR", "key1{t}")
    rd_sg.run("INCR", "key2{t}")
    res1 = rd_redirection.run("read")[2]
    res2 = rd_redirection.run("read")[2]
    assert res1 == "key1{t}"
    assert res2 == "key2{t}"


def test_different_clients_using_different_protocols_can_track_the_same_key(r: ValkeyTestClient) -> None:
    """
    test {Different clients using different protocols can track the same key} {
        $rd HELLO 3
        set reply [$rd read] ; # Consume the HELLO reply
        assert_equal 3 [dict get $reply proto]
        $rd CLIENT TRACKING on
        assert_equal OK [$rd read] ; # Consume the TRACKING reply
        $rd_sg set key1 1
        r GET key1
        $rd GET key1
        assert_equal 1 [$rd read] ; # Consume the GET reply
        $rd_sg INCR key1
        set res1 [lindex [$rd_redirection read] 2]
        $rd PING ; # Non redirecting client has to talk to the server in order to get invalidation message
        set res2 [lindex [split [$rd read] " "] 1]
        assert_equal PONG [$rd read] ; # Consume the PING reply, which comes together with the invalidation message
        assert {$res1 eq {key1}}
        assert {$res2 eq {key1}}
    }
    """
    rd_redirection = ValkeyTestClient.create_from(r)
    rd_redirection.run("client", "id")
    redir_id = rd_redirection.run("read")
    rd_redirection.run("subscribe", "__redis__:invalidate")
    rd_redirection.run("read")
    rd = ValkeyTestClient.create_from(r)
    rd_sg = ValkeyTestClient.create_from(r)
    proc(
        "clean_all",
        "",
        "        uplevel {\n            # We should make r TRACKING off first. If r is in RESP3,\n            # r FLUSH ALL will send us tracking-redir-broken or other\n            # info which will not be consumed.\n            r CLIENT TRACKING off\n            $rd QUIT\n            $rd close\n            $rd_redirection QUIT\n            $rd_redirection close\n            set rd [valkey_deferring_client]\n            set rd_redirection [valkey_deferring_client]\n            $rd_redirection client id\n            set redir_id [$rd_redirection read]\n            $rd_redirection subscribe __redis__:invalidate\n            $rd_redirection read ; # Consume the SUBSCRIBE reply.\n            r FLUSHALL\n            r HELLO 2\n            r config set tracking-table-max-keys 1000000\n        }\n    ",
    )
    rd.run("HELLO", 3)
    reply = rd.run("read")
    assert 3 == reply["proto"]
    rd.run("CLIENT", "TRACKING", "on")
    assert "OK" == rd.run("read")
    rd_sg.run("set", "key1", 1)
    r.run("GET", "key1")
    rd.run("GET", "key1")
    assert 1 == rd.run("read")
    rd_sg.run("INCR", "key1")
    res1 = rd_redirection.run("read")[2]
    rd.run("PING")
    res2 = split(rd.run("read"), " ")[1]
    assert "PONG" == rd.run("read")
    assert res1 == "key1"
    assert res2 == "key1"


def test_no_invalidation_message_when_using_optin_option(r: ValkeyTestClient) -> None:
    """
    test {No invalidation message when using OPTIN option} {
        r CLIENT TRACKING on OPTIN REDIRECT $redir_id
        $rd_sg SET key1 1
        r GET key1 ; # This key should not be notified, since OPTIN is on and CLIENT CACHING yes wasn't called
        $rd_sg SET key1 2
        # Preparing some message to consume on $rd_redirection so we don't get blocked
        r CLIENT TRACKING off
        r CLIENT TRACKING on REDIRECT $redir_id
        $rd_sg SET key2 1
        r GET key2 ; # This key should be notified
        $rd_sg SET key2 2
        set res [lindex [$rd_redirection read] 2]
        assert {$res eq {key2}}
    }
    """
    rd_redirection = ValkeyTestClient.create_from(r)
    rd_redirection.run("client", "id")
    redir_id = rd_redirection.run("read")
    rd_redirection.run("subscribe", "__redis__:invalidate")
    rd_redirection.run("read")
    rd = ValkeyTestClient.create_from(r)
    rd_sg = ValkeyTestClient.create_from(r)
    proc(
        "clean_all",
        "",
        "        uplevel {\n            # We should make r TRACKING off first. If r is in RESP3,\n            # r FLUSH ALL will send us tracking-redir-broken or other\n            # info which will not be consumed.\n            r CLIENT TRACKING off\n            $rd QUIT\n            $rd close\n            $rd_redirection QUIT\n            $rd_redirection close\n            set rd [valkey_deferring_client]\n            set rd_redirection [valkey_deferring_client]\n            $rd_redirection client id\n            set redir_id [$rd_redirection read]\n            $rd_redirection subscribe __redis__:invalidate\n            $rd_redirection read ; # Consume the SUBSCRIBE reply.\n            r FLUSHALL\n            r HELLO 2\n            r config set tracking-table-max-keys 1000000\n        }\n    ",
    )
    r.run("CLIENT", "TRACKING", "on", "OPTIN", "REDIRECT", redir_id)
    rd_sg.run("SET", "key1", 1)
    r.run("GET", "key1")
    rd_sg.run("SET", "key1", 2)
    r.run("CLIENT", "TRACKING", "off")
    r.run("CLIENT", "TRACKING", "on", "REDIRECT", redir_id)
    rd_sg.run("SET", "key2", 1)
    r.run("GET", "key2")
    rd_sg.run("SET", "key2", 2)
    res = rd_redirection.run("read")[2]
    assert res == "key2"


def test_invalidation_message_sent_when_using_optin_option_with_client_caching_yes(r: ValkeyTestClient) -> None:
    """
    test {Invalidation message sent when using OPTIN option with CLIENT CACHING yes} {
        r CLIENT TRACKING on OPTIN REDIRECT $redir_id
        $rd_sg SET key1 3
        r CLIENT CACHING yes
        r GET key1
        $rd_sg SET key1 4
        set res [lindex [$rd_redirection read] 2]
        assert {$res eq {key1}}
    }
    """
    rd_redirection = ValkeyTestClient.create_from(r)
    rd_redirection.run("client", "id")
    redir_id = rd_redirection.run("read")
    rd_redirection.run("subscribe", "__redis__:invalidate")
    rd_redirection.run("read")
    rd = ValkeyTestClient.create_from(r)
    rd_sg = ValkeyTestClient.create_from(r)
    proc(
        "clean_all",
        "",
        "        uplevel {\n            # We should make r TRACKING off first. If r is in RESP3,\n            # r FLUSH ALL will send us tracking-redir-broken or other\n            # info which will not be consumed.\n            r CLIENT TRACKING off\n            $rd QUIT\n            $rd close\n            $rd_redirection QUIT\n            $rd_redirection close\n            set rd [valkey_deferring_client]\n            set rd_redirection [valkey_deferring_client]\n            $rd_redirection client id\n            set redir_id [$rd_redirection read]\n            $rd_redirection subscribe __redis__:invalidate\n            $rd_redirection read ; # Consume the SUBSCRIBE reply.\n            r FLUSHALL\n            r HELLO 2\n            r config set tracking-table-max-keys 1000000\n        }\n    ",
    )
    r.run("CLIENT", "TRACKING", "on", "OPTIN", "REDIRECT", redir_id)
    rd_sg.run("SET", "key1", 3)
    r.run("CLIENT", "CACHING", "yes")
    r.run("GET", "key1")
    rd_sg.run("SET", "key1", 4)
    res = rd_redirection.run("read")[2]
    assert res == "key1"


def test_invalidation_message_sent_when_using_optout_option(r: ValkeyTestClient) -> None:
    """
    test {Invalidation message sent when using OPTOUT option} {
        r CLIENT TRACKING off
        r CLIENT TRACKING on OPTOUT REDIRECT $redir_id
        $rd_sg SET key1 1
        r GET key1
        $rd_sg SET key1 2
        set res [lindex [$rd_redirection read] 2]
        assert {$res eq {key1}}
    }
    """
    rd_redirection = ValkeyTestClient.create_from(r)
    rd_redirection.run("client", "id")
    redir_id = rd_redirection.run("read")
    rd_redirection.run("subscribe", "__redis__:invalidate")
    rd_redirection.run("read")
    rd = ValkeyTestClient.create_from(r)
    rd_sg = ValkeyTestClient.create_from(r)
    proc(
        "clean_all",
        "",
        "        uplevel {\n            # We should make r TRACKING off first. If r is in RESP3,\n            # r FLUSH ALL will send us tracking-redir-broken or other\n            # info which will not be consumed.\n            r CLIENT TRACKING off\n            $rd QUIT\n            $rd close\n            $rd_redirection QUIT\n            $rd_redirection close\n            set rd [valkey_deferring_client]\n            set rd_redirection [valkey_deferring_client]\n            $rd_redirection client id\n            set redir_id [$rd_redirection read]\n            $rd_redirection subscribe __redis__:invalidate\n            $rd_redirection read ; # Consume the SUBSCRIBE reply.\n            r FLUSHALL\n            r HELLO 2\n            r config set tracking-table-max-keys 1000000\n        }\n    ",
    )
    r.run("CLIENT", "TRACKING", "off")
    r.run("CLIENT", "TRACKING", "on", "OPTOUT", "REDIRECT", redir_id)
    rd_sg.run("SET", "key1", 1)
    r.run("GET", "key1")
    rd_sg.run("SET", "key1", 2)
    res = rd_redirection.run("read")[2]
    assert res == "key1"


def test_no_invalidation_message_when_using_optout_option_with_client_caching_no(r: ValkeyTestClient) -> None:
    """
    test {No invalidation message when using OPTOUT option with CLIENT CACHING no} {
        $rd_sg SET key1 1
        r CLIENT CACHING no
        r GET key1 ; # This key should not be notified, since OPTOUT is on and CLIENT CACHING no was called
        $rd_sg SET key1 2
        # Preparing some message to consume on $rd_redirection so we don't get blocked
        $rd_sg SET key2 1
        r GET key2 ; # This key should be notified
        $rd_sg SET key2 2
        set res [lindex [$rd_redirection read] 2]
        assert {$res eq {key2}}
    }
    """
    rd_redirection = ValkeyTestClient.create_from(r)
    rd_redirection.run("client", "id")
    redir_id = rd_redirection.run("read")
    rd_redirection.run("subscribe", "__redis__:invalidate")
    rd_redirection.run("read")
    rd = ValkeyTestClient.create_from(r)
    rd_sg = ValkeyTestClient.create_from(r)
    proc(
        "clean_all",
        "",
        "        uplevel {\n            # We should make r TRACKING off first. If r is in RESP3,\n            # r FLUSH ALL will send us tracking-redir-broken or other\n            # info which will not be consumed.\n            r CLIENT TRACKING off\n            $rd QUIT\n            $rd close\n            $rd_redirection QUIT\n            $rd_redirection close\n            set rd [valkey_deferring_client]\n            set rd_redirection [valkey_deferring_client]\n            $rd_redirection client id\n            set redir_id [$rd_redirection read]\n            $rd_redirection subscribe __redis__:invalidate\n            $rd_redirection read ; # Consume the SUBSCRIBE reply.\n            r FLUSHALL\n            r HELLO 2\n            r config set tracking-table-max-keys 1000000\n        }\n    ",
    )
    rd_sg.run("SET", "key1", 1)
    r.run("CLIENT", "CACHING", "no")
    r.run("GET", "key1")
    rd_sg.run("SET", "key1", 2)
    rd_sg.run("SET", "key2", 1)
    r.run("GET", "key2")
    rd_sg.run("SET", "key2", 2)
    res = rd_redirection.run("read")[2]
    assert res == "key2"


def test_able_to_redirect_to_a_resp3_client(r: ValkeyTestClient) -> None:
    """
    test {Able to redirect to a RESP3 client} {
        $rd_redirection UNSUBSCRIBE __redis__:invalidate ; # Need to unsub first before we can do HELLO 3
        set res [$rd_redirection read] ; # Consume the UNSUBSCRIBE reply
        assert_equal {__redis__:invalidate} [lindex $res 1]
        $rd_redirection HELLO 3
        set res [$rd_redirection read] ; # Consume the HELLO reply
        assert_equal [dict get $reply proto] 3
        $rd_redirection SUBSCRIBE __redis__:invalidate
        set res [$rd_redirection read] ; # Consume the SUBSCRIBE reply
        assert_equal {__redis__:invalidate} [lindex $res 1]
        r CLIENT TRACKING on REDIRECT $redir_id
        $rd_sg SET key1 1
        r GET key1
        $rd_sg INCR key1
        set res [lindex [$rd_redirection read] 1]
        assert {$res eq {key1}}
        $rd_redirection HELLO 2
        set res [$rd_redirection read] ; # Consume the HELLO reply
        assert_equal [dict get $res proto] 2
    }
    """
    rd_redirection = ValkeyTestClient.create_from(r)
    rd_redirection.run("client", "id")
    redir_id = rd_redirection.run("read")
    rd_redirection.run("subscribe", "__redis__:invalidate")
    rd_redirection.run("read")
    rd = ValkeyTestClient.create_from(r)
    rd_sg = ValkeyTestClient.create_from(r)
    proc(
        "clean_all",
        "",
        "        uplevel {\n            # We should make r TRACKING off first. If r is in RESP3,\n            # r FLUSH ALL will send us tracking-redir-broken or other\n            # info which will not be consumed.\n            r CLIENT TRACKING off\n            $rd QUIT\n            $rd close\n            $rd_redirection QUIT\n            $rd_redirection close\n            set rd [valkey_deferring_client]\n            set rd_redirection [valkey_deferring_client]\n            $rd_redirection client id\n            set redir_id [$rd_redirection read]\n            $rd_redirection subscribe __redis__:invalidate\n            $rd_redirection read ; # Consume the SUBSCRIBE reply.\n            r FLUSHALL\n            r HELLO 2\n            r config set tracking-table-max-keys 1000000\n        }\n    ",
    )
    rd_redirection.run("UNSUBSCRIBE", "__redis__:invalidate")
    res = rd_redirection.run("read")
    assert "__redis__:invalidate" == res[1]
    rd_redirection.run("HELLO", 3)
    res = rd_redirection.run("read")
    assert reply["proto"] == 3
    rd_redirection.run("SUBSCRIBE", "__redis__:invalidate")
    res = rd_redirection.run("read")
    assert "__redis__:invalidate" == res[1]
    r.run("CLIENT", "TRACKING", "on", "REDIRECT", redir_id)
    rd_sg.run("SET", "key1", 1)
    r.run("GET", "key1")
    rd_sg.run("INCR", "key1")
    res = rd_redirection.run("read")[1]
    assert res == "key1"
    rd_redirection.run("HELLO", 2)
    res = rd_redirection.run("read")
    assert res["proto"] == 2


def test_after_switching_from_normal_tracking_to_bcast_mode_no_invalidation_message_is_produced_for_pre_bcast_keys(
    r: ValkeyTestClient,
) -> None:
    """
    test {After switching from normal tracking to BCAST mode, no invalidation message is produced for pre-BCAST keys} {
        r CLIENT TRACKING off
        r HELLO 3
        r CLIENT TRACKING on
        $rd_sg SET key1 1
        r GET key1
        r CLIENT TRACKING off
        r CLIENT TRACKING on BCAST
        $rd_sg INCR key1
        set inv_msg [r PING]
        set ping_reply [r read]
        assert {$inv_msg eq {invalidate key1}}
        assert {$ping_reply eq {PONG}}
    }
    """
    rd_redirection = ValkeyTestClient.create_from(r)
    rd_redirection.run("client", "id")
    redir_id = rd_redirection.run("read")
    rd_redirection.run("subscribe", "__redis__:invalidate")
    rd_redirection.run("read")
    rd = ValkeyTestClient.create_from(r)
    rd_sg = ValkeyTestClient.create_from(r)
    proc(
        "clean_all",
        "",
        "        uplevel {\n            # We should make r TRACKING off first. If r is in RESP3,\n            # r FLUSH ALL will send us tracking-redir-broken or other\n            # info which will not be consumed.\n            r CLIENT TRACKING off\n            $rd QUIT\n            $rd close\n            $rd_redirection QUIT\n            $rd_redirection close\n            set rd [valkey_deferring_client]\n            set rd_redirection [valkey_deferring_client]\n            $rd_redirection client id\n            set redir_id [$rd_redirection read]\n            $rd_redirection subscribe __redis__:invalidate\n            $rd_redirection read ; # Consume the SUBSCRIBE reply.\n            r FLUSHALL\n            r HELLO 2\n            r config set tracking-table-max-keys 1000000\n        }\n    ",
    )
    r.run("CLIENT", "TRACKING", "off")
    r.run("HELLO", 3)
    r.run("CLIENT", "TRACKING", "on")
    rd_sg.run("SET", "key1", 1)
    r.run("GET", "key1")
    r.run("CLIENT", "TRACKING", "off")
    r.run("CLIENT", "TRACKING", "on", "BCAST")
    rd_sg.run("INCR", "key1")
    inv_msg = r.run("PING")
    ping_reply = r.run("read")
    assert inv_msg == "invalidate key1"
    assert ping_reply == "PONG"


def test_bcast_with_prefix_collisions_throw_errors(r: ValkeyTestClient) -> None:
    """
    test {BCAST with prefix collisions throw errors} {
        set r [valkey_client]
        catch {$r CLIENT TRACKING ON BCAST PREFIX FOOBAR PREFIX FOO} output
        assert_match {ERR Prefix 'FOOBAR'*'FOO'*} $output

        catch {$r CLIENT TRACKING ON BCAST PREFIX FOO PREFIX FOOBAR} output
        assert_match {ERR Prefix 'FOO'*'FOOBAR'*} $output

        $r CLIENT TRACKING ON BCAST PREFIX FOO PREFIX BAR
        catch {$r CLIENT TRACKING ON BCAST PREFIX FO} output
        assert_match {ERR Prefix 'FO'*'FOO'*} $output

        catch {$r CLIENT TRACKING ON BCAST PREFIX BARB} output
        assert_match {ERR Prefix 'BARB'*'BAR'*} $output

        $r CLIENT TRACKING OFF
    }
    """
    rd_redirection = ValkeyTestClient.create_from(r)
    rd_redirection.run("client", "id")
    redir_id = rd_redirection.run("read")
    rd_redirection.run("subscribe", "__redis__:invalidate")
    rd_redirection.run("read")
    rd = ValkeyTestClient.create_from(r)
    rd_sg = ValkeyTestClient.create_from(r)
    proc(
        "clean_all",
        "",
        "        uplevel {\n            # We should make r TRACKING off first. If r is in RESP3,\n            # r FLUSH ALL will send us tracking-redir-broken or other\n            # info which will not be consumed.\n            r CLIENT TRACKING off\n            $rd QUIT\n            $rd close\n            $rd_redirection QUIT\n            $rd_redirection close\n            set rd [valkey_deferring_client]\n            set rd_redirection [valkey_deferring_client]\n            $rd_redirection client id\n            set redir_id [$rd_redirection read]\n            $rd_redirection subscribe __redis__:invalidate\n            $rd_redirection read ; # Consume the SUBSCRIBE reply.\n            r FLUSHALL\n            r HELLO 2\n            r config set tracking-table-max-keys 1000000\n        }\n    ",
    )
    r = ValkeyTestClient.create_from(r)
    try:
        output = r.run("CLIENT", "TRACKING", "ON", "BCAST", "PREFIX", "FOOBAR", "PREFIX", "FOO")
    except Exception as _catch_err:
        output = str(_catch_err)
    assert fnmatch(str(output), "ERR Prefix 'FOOBAR'*'FOO'*")
    try:
        output = r.run("CLIENT", "TRACKING", "ON", "BCAST", "PREFIX", "FOO", "PREFIX", "FOOBAR")
    except Exception as _catch_err:
        output = str(_catch_err)
    assert fnmatch(str(output), "ERR Prefix 'FOO'*'FOOBAR'*")
    r.run("CLIENT", "TRACKING", "ON", "BCAST", "PREFIX", "FOO", "PREFIX", "BAR")
    try:
        output = r.run("CLIENT", "TRACKING", "ON", "BCAST", "PREFIX", "FO")
    except Exception as _catch_err:
        output = str(_catch_err)
    assert fnmatch(str(output), "ERR Prefix 'FO'*'FOO'*")
    try:
        output = r.run("CLIENT", "TRACKING", "ON", "BCAST", "PREFIX", "BARB")
    except Exception as _catch_err:
        output = str(_catch_err)
    assert fnmatch(str(output), "ERR Prefix 'BARB'*'BAR'*")
    r.run("CLIENT", "TRACKING", "OFF")


def test_hdel_deliver_invalidate_message_after_response_in_the_same_connection(r: ValkeyTestClient) -> None:
    """
    test {hdel deliver invalidate message after response in the same connection} {
        r CLIENT TRACKING off
        r HELLO 3
        r CLIENT TRACKING on
        r HSET myhash f 1
        r HGET myhash f
        set res [r HDEL myhash f]
        assert_equal $res 1
        set res [r read]
        assert_equal $res {invalidate myhash}
    }
    """
    rd_redirection = ValkeyTestClient.create_from(r)
    rd_redirection.run("client", "id")
    redir_id = rd_redirection.run("read")
    rd_redirection.run("subscribe", "__redis__:invalidate")
    rd_redirection.run("read")
    rd = ValkeyTestClient.create_from(r)
    rd_sg = ValkeyTestClient.create_from(r)
    proc(
        "clean_all",
        "",
        "        uplevel {\n            # We should make r TRACKING off first. If r is in RESP3,\n            # r FLUSH ALL will send us tracking-redir-broken or other\n            # info which will not be consumed.\n            r CLIENT TRACKING off\n            $rd QUIT\n            $rd close\n            $rd_redirection QUIT\n            $rd_redirection close\n            set rd [valkey_deferring_client]\n            set rd_redirection [valkey_deferring_client]\n            $rd_redirection client id\n            set redir_id [$rd_redirection read]\n            $rd_redirection subscribe __redis__:invalidate\n            $rd_redirection read ; # Consume the SUBSCRIBE reply.\n            r FLUSHALL\n            r HELLO 2\n            r config set tracking-table-max-keys 1000000\n        }\n    ",
    )
    r.run("CLIENT", "TRACKING", "off")
    r.run("HELLO", 3)
    r.run("CLIENT", "TRACKING", "on")
    r.run("HSET", "myhash", "f", 1)
    r.run("HGET", "myhash", "f")
    res = r.run("HDEL", "myhash", "f")
    assert res == 1
    res = r.run("read")
    assert res == "invalidate myhash"


def test_tracking_invalidation_message_is_not_interleaved_with_multiple_keys_response(r: ValkeyTestClient) -> None:
    """
    test {Tracking invalidation message is not interleaved with multiple keys response} {
        r CLIENT TRACKING off
        r HELLO 3
        r CLIENT TRACKING on
        # We need disable active expire, so we can trigger lazy expire
        r DEBUG SET-ACTIVE-EXPIRE 0
        r MULTI
        r MSET x{t} 1 y{t} 2
        r PEXPIRE y{t} 100
        r GET y{t}
        r EXEC
        after 110
        # Read expired key y{t}, generate invalidate message about this key
        set res [r MGET x{t} y{t}]
        assert_equal $res {1 {}}
        # Consume the invalidate message which is after command response
        set res [r read]
        assert_equal $res {invalidate y{t}}
        r DEBUG SET-ACTIVE-EXPIRE 1
    } {OK} {needs:debug}
    """
    rd_redirection = ValkeyTestClient.create_from(r)
    rd_redirection.run("client", "id")
    redir_id = rd_redirection.run("read")
    rd_redirection.run("subscribe", "__redis__:invalidate")
    rd_redirection.run("read")
    rd = ValkeyTestClient.create_from(r)
    rd_sg = ValkeyTestClient.create_from(r)
    proc(
        "clean_all",
        "",
        "        uplevel {\n            # We should make r TRACKING off first. If r is in RESP3,\n            # r FLUSH ALL will send us tracking-redir-broken or other\n            # info which will not be consumed.\n            r CLIENT TRACKING off\n            $rd QUIT\n            $rd close\n            $rd_redirection QUIT\n            $rd_redirection close\n            set rd [valkey_deferring_client]\n            set rd_redirection [valkey_deferring_client]\n            $rd_redirection client id\n            set redir_id [$rd_redirection read]\n            $rd_redirection subscribe __redis__:invalidate\n            $rd_redirection read ; # Consume the SUBSCRIBE reply.\n            r FLUSHALL\n            r HELLO 2\n            r config set tracking-table-max-keys 1000000\n        }\n    ",
    )
    r.run("CLIENT", "TRACKING", "off")
    r.run("HELLO", 3)
    r.run("CLIENT", "TRACKING", "on")
    r.run("DEBUG", "SET-ACTIVE-EXPIRE", 0)
    r.run("MULTI")
    r.run("MSET", "x{t}", 1, "y{t}", 2)
    r.run("PEXPIRE", "y{t}", 100)
    r.run("GET", "y{t}")
    r.run("EXEC")
    time.sleep(110 / 1000)
    res = r.run("MGET", "x{t}", "y{t}")
    assert res == "1 {}"
    res = r.run("read")
    assert res == "invalidate y{t}"
    assert r.run("DEBUG", "SET-ACTIVE-EXPIRE", 1) == "OK"


def test_tracking_invalidation_message_is_not_interleaved_with_transaction_response(r: ValkeyTestClient) -> None:
    """
    test {Tracking invalidation message is not interleaved with transaction response} {
        r CLIENT TRACKING off
        r HELLO 3
        r CLIENT TRACKING on
        r MSET a{t} 1 b{t} 2
        r GET a{t}
        # Start a transaction, make a{t} generate an invalidate message
        r MULTI
        r INCR a{t}
        r GET b{t}
        set res [r EXEC]
        assert_equal $res {2 2}
        set res [r read]
        # Consume the invalidate message which is after command response
        assert_equal $res {invalidate a{t}}
    }
    """
    rd_redirection = ValkeyTestClient.create_from(r)
    rd_redirection.run("client", "id")
    redir_id = rd_redirection.run("read")
    rd_redirection.run("subscribe", "__redis__:invalidate")
    rd_redirection.run("read")
    rd = ValkeyTestClient.create_from(r)
    rd_sg = ValkeyTestClient.create_from(r)
    proc(
        "clean_all",
        "",
        "        uplevel {\n            # We should make r TRACKING off first. If r is in RESP3,\n            # r FLUSH ALL will send us tracking-redir-broken or other\n            # info which will not be consumed.\n            r CLIENT TRACKING off\n            $rd QUIT\n            $rd close\n            $rd_redirection QUIT\n            $rd_redirection close\n            set rd [valkey_deferring_client]\n            set rd_redirection [valkey_deferring_client]\n            $rd_redirection client id\n            set redir_id [$rd_redirection read]\n            $rd_redirection subscribe __redis__:invalidate\n            $rd_redirection read ; # Consume the SUBSCRIBE reply.\n            r FLUSHALL\n            r HELLO 2\n            r config set tracking-table-max-keys 1000000\n        }\n    ",
    )
    r.run("CLIENT", "TRACKING", "off")
    r.run("HELLO", 3)
    r.run("CLIENT", "TRACKING", "on")
    r.run("MSET", "a{t}", 1, "b{t}", 2)
    r.run("GET", "a{t}")
    r.run("MULTI")
    r.run("INCR", "a{t}")
    r.run("GET", "b{t}")
    res = r.run("EXEC")
    assert res == "2 2"
    res = r.run("read")
    assert res == "invalidate a{t}"


def test_tracking_invalidation_message_of_eviction_keys_should_be_before_response(r: ValkeyTestClient) -> None:
    """
    test {Tracking invalidation message of eviction keys should be before response} {
        # Get the current memory limit and calculate a new limit.
        r CLIENT TRACKING off
        r HELLO 3
        r CLIENT TRACKING on

        # make the previous test is really done before sampling used_memory
        wait_lazyfree_done r

        set used [expr {[s used_memory] - [s mem_not_counted_for_evict]}]
        set limit [expr {$used+100*1024}]
        set old_policy [lindex [r config get maxmemory-policy] 1]
        r config set maxmemory $limit
        # We set policy volatile-random, so only keys with ttl will be evicted
        r config set maxmemory-policy volatile-random
        # Add a volatile key and tracking it.
        r setex volatile-key 10000 x
        r get volatile-key
        # We use SETBIT here, so we can set a big key and get the used_memory
        # bigger than maxmemory. Next command will evict volatile keys. We
        # can't use SET, as SET uses big input buffer, so it will fail.
        r setbit big-key 1600000 0 ;# this will consume 200kb
        # volatile-key is evicted before response.
        set res [r getbit big-key 0]
        assert_equal $res {invalidate volatile-key}
        set res [r read]
        assert_equal $res 0
        r config set maxmemory-policy $old_policy
        r config set maxmemory 0
    }
    """
    rd_redirection = ValkeyTestClient.create_from(r)
    rd_redirection.run("client", "id")
    redir_id = rd_redirection.run("read")
    rd_redirection.run("subscribe", "__redis__:invalidate")
    rd_redirection.run("read")
    rd = ValkeyTestClient.create_from(r)
    rd_sg = ValkeyTestClient.create_from(r)
    proc(
        "clean_all",
        "",
        "        uplevel {\n            # We should make r TRACKING off first. If r is in RESP3,\n            # r FLUSH ALL will send us tracking-redir-broken or other\n            # info which will not be consumed.\n            r CLIENT TRACKING off\n            $rd QUIT\n            $rd close\n            $rd_redirection QUIT\n            $rd_redirection close\n            set rd [valkey_deferring_client]\n            set rd_redirection [valkey_deferring_client]\n            $rd_redirection client id\n            set redir_id [$rd_redirection read]\n            $rd_redirection subscribe __redis__:invalidate\n            $rd_redirection read ; # Consume the SUBSCRIBE reply.\n            r FLUSHALL\n            r HELLO 2\n            r config set tracking-table-max-keys 1000000\n        }\n    ",
    )
    r.run("CLIENT", "TRACKING", "off")
    r.run("HELLO", 3)
    r.run("CLIENT", "TRACKING", "on")
    wait_lazyfree_done("r")
    used = expr("[s used_memory] - [s mem_not_counted_for_evict]")
    limit = expr("$used+100*1024")
    old_policy = r.run("config", "get", "maxmemory-policy")[1]
    r.run("config", "set", "maxmemory", limit)
    r.run("config", "set", "maxmemory-policy", "volatile-random")
    r.run("setex", "volatile-key", 10000, "x")
    r.run("get", "volatile-key")
    r.run("setbit", "big-key", 1600000, 0)
    res = r.run("getbit", "big-key", 0)
    assert res == "invalidate volatile-key"
    res = r.run("read")
    assert res == 0
    r.run("config", "set", "maxmemory-policy", old_policy)
    r.run("config", "set", "maxmemory", 0)


def test_unblocked_blmove_gets_notification_after_response(r: ValkeyTestClient) -> None:
    """
    test {Unblocked BLMOVE gets notification after response} {
        r RPUSH list2{t} a
        $rd HELLO 3
        $rd read
        $rd CLIENT TRACKING on
        $rd read
        # Tracking key list2{t}
        $rd LRANGE list2{t} 0 -1
        $rd read
        # We block on list1{t}
        $rd BLMOVE list1{t} list2{t} left left 0
        wait_for_blocked_clients_count 1
        # unblock $rd, list2{t} gets element and generate invalidation message
        r rpush list1{t} foo
        assert_equal [$rd read] {foo}
        assert_equal [$rd read] {invalidate list2{t}}
    }
    """
    rd_redirection = ValkeyTestClient.create_from(r)
    rd_redirection.run("client", "id")
    redir_id = rd_redirection.run("read")
    rd_redirection.run("subscribe", "__redis__:invalidate")
    rd_redirection.run("read")
    rd = ValkeyTestClient.create_from(r)
    rd_sg = ValkeyTestClient.create_from(r)
    proc(
        "clean_all",
        "",
        "        uplevel {\n            # We should make r TRACKING off first. If r is in RESP3,\n            # r FLUSH ALL will send us tracking-redir-broken or other\n            # info which will not be consumed.\n            r CLIENT TRACKING off\n            $rd QUIT\n            $rd close\n            $rd_redirection QUIT\n            $rd_redirection close\n            set rd [valkey_deferring_client]\n            set rd_redirection [valkey_deferring_client]\n            $rd_redirection client id\n            set redir_id [$rd_redirection read]\n            $rd_redirection subscribe __redis__:invalidate\n            $rd_redirection read ; # Consume the SUBSCRIBE reply.\n            r FLUSHALL\n            r HELLO 2\n            r config set tracking-table-max-keys 1000000\n        }\n    ",
    )
    r.run("RPUSH", "list2{t}", "a")
    rd.run("HELLO", 3)
    rd.run("read")
    rd.run("CLIENT", "TRACKING", "on")
    rd.run("read")
    rd.run("LRANGE", "list2{t}", 0, -1)
    rd.run("read")
    rd.run("BLMOVE", "list1{t}", "list2{t}", "left", "left", 0)
    wait_for_blocked_clients_count(1)
    r.run("rpush", "list1{t}", "foo")
    assert rd.run("read") == "foo"
    assert rd.run("read") == "invalidate list2{t}"


def test_tracking_gets_notification_on_tracking_table_key_eviction(r: ValkeyTestClient) -> None:
    """
    test {Tracking gets notification on tracking table key eviction} {
        r CLIENT TRACKING off
        r CLIENT TRACKING on REDIRECT $redir_id NOLOOP
        r MSET key1{t} 1 key2{t} 2
        # Let the server track the two keys for us
        r MGET key1{t} key2{t}
        # Force the eviction of all the keys but one:
        r config set tracking-table-max-keys 1
        # Note that we may have other keys in the table for this client,
        # since we disabled/enabled tracking multiple time with the same
        # ID, and tracking does not do ID cleanups for performance reasons.
        # So we check that eventually we'll receive one or the other key,
        # otherwise the test will die for timeout.
        while 1 {
            set keys [lindex [$rd_redirection read] 2]
            if {$keys eq {key1{t}} || $keys eq {key2{t}}} break
        }
        # We should receive an expire notification for one of
        # the two keys (only one must remain)
        assert {$keys eq {key1{t}} || $keys eq {key2{t}}}
    }
    """
    rd_redirection = ValkeyTestClient.create_from(r)
    rd_redirection.run("client", "id")
    redir_id = rd_redirection.run("read")
    rd_redirection.run("subscribe", "__redis__:invalidate")
    rd_redirection.run("read")
    rd = ValkeyTestClient.create_from(r)
    rd_sg = ValkeyTestClient.create_from(r)
    proc(
        "clean_all",
        "",
        "        uplevel {\n            # We should make r TRACKING off first. If r is in RESP3,\n            # r FLUSH ALL will send us tracking-redir-broken or other\n            # info which will not be consumed.\n            r CLIENT TRACKING off\n            $rd QUIT\n            $rd close\n            $rd_redirection QUIT\n            $rd_redirection close\n            set rd [valkey_deferring_client]\n            set rd_redirection [valkey_deferring_client]\n            $rd_redirection client id\n            set redir_id [$rd_redirection read]\n            $rd_redirection subscribe __redis__:invalidate\n            $rd_redirection read ; # Consume the SUBSCRIBE reply.\n            r FLUSHALL\n            r HELLO 2\n            r config set tracking-table-max-keys 1000000\n        }\n    ",
    )
    r.run("CLIENT", "TRACKING", "off")
    r.run("CLIENT", "TRACKING", "on", "REDIRECT", redir_id, "NOLOOP")
    r.run("MSET", "key1{t}", 1, "key2{t}", 2)
    r.run("MGET", "key1{t}", "key2{t}")
    r.run("config", "set", "tracking-table-max-keys", 1)
    while_(
        1,
        "            set keys [lindex [$rd_redirection read] 2]\n            if {$keys eq {key1{t}} || $keys eq {key2{t}}} break\n        ",
    )
    assert (keys == "key1{t}") or (keys == "key2{t}")


def test_invalidation_message_received_for_flushall(r: ValkeyTestClient) -> None:
    """
    test {Invalidation message received for flushall} {
        clean_all
        r CLIENT TRACKING on REDIRECT $redir_id
        $rd_sg SET key1 1
        r GET key1
        $rd_sg FLUSHALL
        set msg [$rd_redirection read]
        assert {[lindex msg 2] eq {} }
    }
    """
    rd_redirection = ValkeyTestClient.create_from(r)
    rd_redirection.run("client", "id")
    redir_id = rd_redirection.run("read")
    rd_redirection.run("subscribe", "__redis__:invalidate")
    rd_redirection.run("read")
    rd = ValkeyTestClient.create_from(r)
    rd_sg = ValkeyTestClient.create_from(r)
    proc(
        "clean_all",
        "",
        "        uplevel {\n            # We should make r TRACKING off first. If r is in RESP3,\n            # r FLUSH ALL will send us tracking-redir-broken or other\n            # info which will not be consumed.\n            r CLIENT TRACKING off\n            $rd QUIT\n            $rd close\n            $rd_redirection QUIT\n            $rd_redirection close\n            set rd [valkey_deferring_client]\n            set rd_redirection [valkey_deferring_client]\n            $rd_redirection client id\n            set redir_id [$rd_redirection read]\n            $rd_redirection subscribe __redis__:invalidate\n            $rd_redirection read ; # Consume the SUBSCRIBE reply.\n            r FLUSHALL\n            r HELLO 2\n            r config set tracking-table-max-keys 1000000\n        }\n    ",
    )
    clean_all()
    r.run("CLIENT", "TRACKING", "on", "REDIRECT", redir_id)
    rd_sg.run("SET", "key1", 1)
    r.run("GET", "key1")
    rd_sg.run("FLUSHALL")
    msg = rd_redirection.run("read")
    assert "msg"[2] == ""


def test_invalidation_message_received_for_flushdb(r: ValkeyTestClient) -> None:
    """
    test {Invalidation message received for flushdb} {
        clean_all
        r CLIENT TRACKING on REDIRECT $redir_id
        $rd_sg SET key1 1
        r GET key1
        $rd_sg FLUSHDB
        set msg [$rd_redirection read]
        assert {[lindex msg 2] eq {} }
    }
    """
    rd_redirection = ValkeyTestClient.create_from(r)
    rd_redirection.run("client", "id")
    redir_id = rd_redirection.run("read")
    rd_redirection.run("subscribe", "__redis__:invalidate")
    rd_redirection.run("read")
    rd = ValkeyTestClient.create_from(r)
    rd_sg = ValkeyTestClient.create_from(r)
    proc(
        "clean_all",
        "",
        "        uplevel {\n            # We should make r TRACKING off first. If r is in RESP3,\n            # r FLUSH ALL will send us tracking-redir-broken or other\n            # info which will not be consumed.\n            r CLIENT TRACKING off\n            $rd QUIT\n            $rd close\n            $rd_redirection QUIT\n            $rd_redirection close\n            set rd [valkey_deferring_client]\n            set rd_redirection [valkey_deferring_client]\n            $rd_redirection client id\n            set redir_id [$rd_redirection read]\n            $rd_redirection subscribe __redis__:invalidate\n            $rd_redirection read ; # Consume the SUBSCRIBE reply.\n            r FLUSHALL\n            r HELLO 2\n            r config set tracking-table-max-keys 1000000\n        }\n    ",
    )
    clean_all()
    r.run("CLIENT", "TRACKING", "on", "REDIRECT", redir_id)
    rd_sg.run("SET", "key1", 1)
    r.run("GET", "key1")
    rd_sg.run("FLUSHDB")
    msg = rd_redirection.run("read")
    assert "msg"[2] == ""


def test_test_async_flushall(r: ValkeyTestClient) -> None:
    """
    test {Test ASYNC flushall} {
        clean_all
        r CLIENT TRACKING on REDIRECT $redir_id
        r GET key1
        r GET key2
        assert_equal [s 0 tracking_total_keys] 2
        $rd_sg FLUSHALL ASYNC
        assert_equal [s 0 tracking_total_keys] 0
        assert_equal [lindex [$rd_redirection read] 2] {}
    }
    """
    rd_redirection = ValkeyTestClient.create_from(r)
    rd_redirection.run("client", "id")
    redir_id = rd_redirection.run("read")
    rd_redirection.run("subscribe", "__redis__:invalidate")
    rd_redirection.run("read")
    rd = ValkeyTestClient.create_from(r)
    rd_sg = ValkeyTestClient.create_from(r)
    proc(
        "clean_all",
        "",
        "        uplevel {\n            # We should make r TRACKING off first. If r is in RESP3,\n            # r FLUSH ALL will send us tracking-redir-broken or other\n            # info which will not be consumed.\n            r CLIENT TRACKING off\n            $rd QUIT\n            $rd close\n            $rd_redirection QUIT\n            $rd_redirection close\n            set rd [valkey_deferring_client]\n            set rd_redirection [valkey_deferring_client]\n            $rd_redirection client id\n            set redir_id [$rd_redirection read]\n            $rd_redirection subscribe __redis__:invalidate\n            $rd_redirection read ; # Consume the SUBSCRIBE reply.\n            r FLUSHALL\n            r HELLO 2\n            r config set tracking-table-max-keys 1000000\n        }\n    ",
    )
    clean_all()
    r.run("CLIENT", "TRACKING", "on", "REDIRECT", redir_id)
    r.run("GET", "key1")
    r.run("GET", "key2")
    assert s(0, "tracking_total_keys") == 2
    rd_sg.run("FLUSHALL", "ASYNC")
    assert s(0, "tracking_total_keys") == 0
    assert rd_redirection.run("read")[2] == ""


def test_flushdb_tracking_invalidation_message_is_not_interleaved_with_transaction_response(
    r: ValkeyTestClient,
) -> None:
    """
    test {flushdb tracking invalidation message is not interleaved with transaction response} {
        clean_all
        r HELLO 3
        r CLIENT TRACKING on
        r SET a{t} 1
        r GET a{t}
        r MULTI
        r FLUSHDB
        set res [r EXEC]
        assert_equal $res {OK}
        # Consume the invalidate message which is after command response
        r read
    } {invalidate {}}
    """
    rd_redirection = ValkeyTestClient.create_from(r)
    rd_redirection.run("client", "id")
    redir_id = rd_redirection.run("read")
    rd_redirection.run("subscribe", "__redis__:invalidate")
    rd_redirection.run("read")
    rd = ValkeyTestClient.create_from(r)
    rd_sg = ValkeyTestClient.create_from(r)
    proc(
        "clean_all",
        "",
        "        uplevel {\n            # We should make r TRACKING off first. If r is in RESP3,\n            # r FLUSH ALL will send us tracking-redir-broken or other\n            # info which will not be consumed.\n            r CLIENT TRACKING off\n            $rd QUIT\n            $rd close\n            $rd_redirection QUIT\n            $rd_redirection close\n            set rd [valkey_deferring_client]\n            set rd_redirection [valkey_deferring_client]\n            $rd_redirection client id\n            set redir_id [$rd_redirection read]\n            $rd_redirection subscribe __redis__:invalidate\n            $rd_redirection read ; # Consume the SUBSCRIBE reply.\n            r FLUSHALL\n            r HELLO 2\n            r config set tracking-table-max-keys 1000000\n        }\n    ",
    )
    clean_all()
    r.run("HELLO", 3)
    r.run("CLIENT", "TRACKING", "on")
    r.run("SET", "a{t}", 1)
    r.run("GET", "a{t}")
    r.run("MULTI")
    r.run("FLUSHDB")
    res = r.run("EXEC")
    assert res == "OK"
    assert r.run("read") == "invalidate {}"


def test_server_is_able_to_evacuate_enough_keys_when_num_of_keys_surpasses_limit_by_more_than_defined_initial_effort(
    r: ValkeyTestClient,
) -> None:
    """
    test {Server is able to evacuate enough keys when num of keys surpasses limit by more than defined initial effort} {
        clean_all
        set NUM_OF_KEYS_TO_TEST 250
        set TRACKING_TABLE_MAX_KEYS 1
        r CLIENT TRACKING on REDIRECT $redir_id
        for {set i 0} {$i < $NUM_OF_KEYS_TO_TEST} {incr i} {
            $rd_sg SET key$i $i
            r GET key$i
        }
        r config set tracking-table-max-keys $TRACKING_TABLE_MAX_KEYS
        # If not enough keys are evicted, we won't get enough invalidation
        # messages, and "$rd_redirection read" will block.
        # If too many keys are evicted, we will get too many invalidation
        # messages, and the assert will fail.
        for {set i 0} {$i < $NUM_OF_KEYS_TO_TEST - $TRACKING_TABLE_MAX_KEYS} {incr i} {
            $rd_redirection read
        }
        $rd_redirection PING
        assert {[$rd_redirection read] eq {pong {}}}
    }
    """
    rd_redirection = ValkeyTestClient.create_from(r)
    rd_redirection.run("client", "id")
    redir_id = rd_redirection.run("read")
    rd_redirection.run("subscribe", "__redis__:invalidate")
    rd_redirection.run("read")
    rd = ValkeyTestClient.create_from(r)
    rd_sg = ValkeyTestClient.create_from(r)
    proc(
        "clean_all",
        "",
        "        uplevel {\n            # We should make r TRACKING off first. If r is in RESP3,\n            # r FLUSH ALL will send us tracking-redir-broken or other\n            # info which will not be consumed.\n            r CLIENT TRACKING off\n            $rd QUIT\n            $rd close\n            $rd_redirection QUIT\n            $rd_redirection close\n            set rd [valkey_deferring_client]\n            set rd_redirection [valkey_deferring_client]\n            $rd_redirection client id\n            set redir_id [$rd_redirection read]\n            $rd_redirection subscribe __redis__:invalidate\n            $rd_redirection read ; # Consume the SUBSCRIBE reply.\n            r FLUSHALL\n            r HELLO 2\n            r config set tracking-table-max-keys 1000000\n        }\n    ",
    )
    clean_all()
    NUM_OF_KEYS_TO_TEST = 250
    TRACKING_TABLE_MAX_KEYS = 1
    r.run("CLIENT", "TRACKING", "on", "REDIRECT", redir_id)
    i = 0
    while i < NUM_OF_KEYS_TO_TEST:
        rd_sg.run("SET", "key$i", i)
        r.run("GET", "key$i")
        i += 1
    r.run("config", "set", "tracking-table-max-keys", TRACKING_TABLE_MAX_KEYS)
    i = 0
    while i < (NUM_OF_KEYS_TO_TEST - TRACKING_TABLE_MAX_KEYS):
        rd_redirection.run("read")
        i += 1
    rd_redirection.run("PING")
    assert rd_redirection.run("read") == "pong {}"


def test_tracking_info_is_correct(r: ValkeyTestClient) -> None:
    """
    test {Tracking info is correct} {
        clean_all
        r CLIENT TRACKING on REDIRECT $redir_id
        $rd_sg SET key1 1
        $rd_sg SET key2 2
        r GET key1
        r GET key2
        $rd CLIENT TRACKING on BCAST PREFIX prefix:
        assert [string match *OK* [$rd read]]
        $rd_sg SET prefix:key1 1
        $rd_sg SET prefix:key2 2
        set info [r info]
        regexp "\r\ntracking_total_items:(.*?)\r\n" $info _ total_items
        regexp "\r\ntracking_total_keys:(.*?)\r\n" $info _ total_keys
        regexp "\r\ntracking_total_prefixes:(.*?)\r\n" $info _ total_prefixes
        regexp "\r\ntracking_clients:(.*?)\r\n" $info _ tracking_clients
        assert {$total_items == 2}
        assert {$total_keys == 2}
        assert {$total_prefixes == 1}
        assert {$tracking_clients == 2}
    }
    """
    rd_redirection = ValkeyTestClient.create_from(r)
    rd_redirection.run("client", "id")
    redir_id = rd_redirection.run("read")
    rd_redirection.run("subscribe", "__redis__:invalidate")
    rd_redirection.run("read")
    rd = ValkeyTestClient.create_from(r)
    rd_sg = ValkeyTestClient.create_from(r)
    proc(
        "clean_all",
        "",
        "        uplevel {\n            # We should make r TRACKING off first. If r is in RESP3,\n            # r FLUSH ALL will send us tracking-redir-broken or other\n            # info which will not be consumed.\n            r CLIENT TRACKING off\n            $rd QUIT\n            $rd close\n            $rd_redirection QUIT\n            $rd_redirection close\n            set rd [valkey_deferring_client]\n            set rd_redirection [valkey_deferring_client]\n            $rd_redirection client id\n            set redir_id [$rd_redirection read]\n            $rd_redirection subscribe __redis__:invalidate\n            $rd_redirection read ; # Consume the SUBSCRIBE reply.\n            r FLUSHALL\n            r HELLO 2\n            r config set tracking-table-max-keys 1000000\n        }\n    ",
    )
    clean_all()
    r.run("CLIENT", "TRACKING", "on", "REDIRECT", redir_id)
    rd_sg.run("SET", "key1", 1)
    rd_sg.run("SET", "key2", 2)
    r.run("GET", "key1")
    r.run("GET", "key2")
    rd.run("CLIENT", "TRACKING", "on", "BCAST", "PREFIX", "prefix:")
    assert_(string("match", "*OK*", rd.run("read")))
    rd_sg.run("SET", "prefix:key1", 1)
    rd_sg.run("SET", "prefix:key2", 2)
    info = r.run("info")
    regexp("\r\ntracking_total_items:(.*?)\r\n", info, "_", "total_items")
    regexp("\r\ntracking_total_keys:(.*?)\r\n", info, "_", "total_keys")
    regexp("\r\ntracking_total_prefixes:(.*?)\r\n", info, "_", "total_prefixes")
    regexp("\r\ntracking_clients:(.*?)\r\n", info, "_", "tracking_clients")
    assert total_items == 2
    assert total_keys == 2
    assert total_prefixes == 1
    assert tracking_clients == 2


def test_client_getredir_provides_correct_client_id(r: ValkeyTestClient) -> None:
    """
    test {CLIENT GETREDIR provides correct client id} {
        set res [r CLIENT GETREDIR]
        assert_equal $redir_id $res
        r CLIENT TRACKING off
        set res [r CLIENT GETREDIR]
        assert_equal -1 $res
        r CLIENT TRACKING on
        set res [r CLIENT GETREDIR]
        assert_equal 0 $res
    }
    """
    rd_redirection = ValkeyTestClient.create_from(r)
    rd_redirection.run("client", "id")
    redir_id = rd_redirection.run("read")
    rd_redirection.run("subscribe", "__redis__:invalidate")
    rd_redirection.run("read")
    rd = ValkeyTestClient.create_from(r)
    rd_sg = ValkeyTestClient.create_from(r)
    proc(
        "clean_all",
        "",
        "        uplevel {\n            # We should make r TRACKING off first. If r is in RESP3,\n            # r FLUSH ALL will send us tracking-redir-broken or other\n            # info which will not be consumed.\n            r CLIENT TRACKING off\n            $rd QUIT\n            $rd close\n            $rd_redirection QUIT\n            $rd_redirection close\n            set rd [valkey_deferring_client]\n            set rd_redirection [valkey_deferring_client]\n            $rd_redirection client id\n            set redir_id [$rd_redirection read]\n            $rd_redirection subscribe __redis__:invalidate\n            $rd_redirection read ; # Consume the SUBSCRIBE reply.\n            r FLUSHALL\n            r HELLO 2\n            r config set tracking-table-max-keys 1000000\n        }\n    ",
    )
    res = r.run("CLIENT", "GETREDIR")
    assert redir_id == res
    r.run("CLIENT", "TRACKING", "off")
    res = r.run("CLIENT", "GETREDIR")
    assert -1 == res
    r.run("CLIENT", "TRACKING", "on")
    res = r.run("CLIENT", "GETREDIR")
    assert 0 == res


def test_client_trackinginfo_provides_reasonable_results_when_tracking_off(r: ValkeyTestClient) -> None:
    """
    test {CLIENT TRACKINGINFO provides reasonable results when tracking off} {
        r CLIENT TRACKING off
        set res [r client trackinginfo]
        set flags [dict get $res flags]
        assert_equal {off} $flags
        set redirect [dict get $res redirect]
        assert_equal {-1} $redirect
        set prefixes [dict get $res prefixes]
        assert_equal {} $prefixes
    }
    """
    rd_redirection = ValkeyTestClient.create_from(r)
    rd_redirection.run("client", "id")
    redir_id = rd_redirection.run("read")
    rd_redirection.run("subscribe", "__redis__:invalidate")
    rd_redirection.run("read")
    rd = ValkeyTestClient.create_from(r)
    rd_sg = ValkeyTestClient.create_from(r)
    proc(
        "clean_all",
        "",
        "        uplevel {\n            # We should make r TRACKING off first. If r is in RESP3,\n            # r FLUSH ALL will send us tracking-redir-broken or other\n            # info which will not be consumed.\n            r CLIENT TRACKING off\n            $rd QUIT\n            $rd close\n            $rd_redirection QUIT\n            $rd_redirection close\n            set rd [valkey_deferring_client]\n            set rd_redirection [valkey_deferring_client]\n            $rd_redirection client id\n            set redir_id [$rd_redirection read]\n            $rd_redirection subscribe __redis__:invalidate\n            $rd_redirection read ; # Consume the SUBSCRIBE reply.\n            r FLUSHALL\n            r HELLO 2\n            r config set tracking-table-max-keys 1000000\n        }\n    ",
    )
    r.run("CLIENT", "TRACKING", "off")
    res = r.run("client", "trackinginfo")
    flags = res["flags"]
    assert "off" == flags
    redirect = res["redirect"]
    assert "-1" == redirect
    prefixes = res["prefixes"]
    assert "" == prefixes


def test_client_trackinginfo_provides_reasonable_results_when_tracking_on(r: ValkeyTestClient) -> None:
    """
    test {CLIENT TRACKINGINFO provides reasonable results when tracking on} {
        r CLIENT TRACKING on
        set res [r client trackinginfo]
        set flags [dict get $res flags]
        assert_equal {on} $flags
        set redirect [dict get $res redirect]
        assert_equal {0} $redirect
        set prefixes [dict get $res prefixes]
        assert_equal {} $prefixes
    }
    """
    rd_redirection = ValkeyTestClient.create_from(r)
    rd_redirection.run("client", "id")
    redir_id = rd_redirection.run("read")
    rd_redirection.run("subscribe", "__redis__:invalidate")
    rd_redirection.run("read")
    rd = ValkeyTestClient.create_from(r)
    rd_sg = ValkeyTestClient.create_from(r)
    proc(
        "clean_all",
        "",
        "        uplevel {\n            # We should make r TRACKING off first. If r is in RESP3,\n            # r FLUSH ALL will send us tracking-redir-broken or other\n            # info which will not be consumed.\n            r CLIENT TRACKING off\n            $rd QUIT\n            $rd close\n            $rd_redirection QUIT\n            $rd_redirection close\n            set rd [valkey_deferring_client]\n            set rd_redirection [valkey_deferring_client]\n            $rd_redirection client id\n            set redir_id [$rd_redirection read]\n            $rd_redirection subscribe __redis__:invalidate\n            $rd_redirection read ; # Consume the SUBSCRIBE reply.\n            r FLUSHALL\n            r HELLO 2\n            r config set tracking-table-max-keys 1000000\n        }\n    ",
    )
    r.run("CLIENT", "TRACKING", "on")
    res = r.run("client", "trackinginfo")
    flags = res["flags"]
    assert "on" == flags
    redirect = res["redirect"]
    assert "0" == redirect
    prefixes = res["prefixes"]
    assert "" == prefixes


def test_client_trackinginfo_provides_reasonable_results_when_tracking_on_with_options(r: ValkeyTestClient) -> None:
    """
    test {CLIENT TRACKINGINFO provides reasonable results when tracking on with options} {
        r CLIENT TRACKING on REDIRECT $redir_id noloop
        set res [r client trackinginfo]
        set flags [dict get $res flags]
        assert_equal {on noloop} $flags
        set redirect [dict get $res redirect]
        assert_equal $redir_id $redirect
        set prefixes [dict get $res prefixes]
        assert_equal {} $prefixes
    }
    """
    rd_redirection = ValkeyTestClient.create_from(r)
    rd_redirection.run("client", "id")
    redir_id = rd_redirection.run("read")
    rd_redirection.run("subscribe", "__redis__:invalidate")
    rd_redirection.run("read")
    rd = ValkeyTestClient.create_from(r)
    rd_sg = ValkeyTestClient.create_from(r)
    proc(
        "clean_all",
        "",
        "        uplevel {\n            # We should make r TRACKING off first. If r is in RESP3,\n            # r FLUSH ALL will send us tracking-redir-broken or other\n            # info which will not be consumed.\n            r CLIENT TRACKING off\n            $rd QUIT\n            $rd close\n            $rd_redirection QUIT\n            $rd_redirection close\n            set rd [valkey_deferring_client]\n            set rd_redirection [valkey_deferring_client]\n            $rd_redirection client id\n            set redir_id [$rd_redirection read]\n            $rd_redirection subscribe __redis__:invalidate\n            $rd_redirection read ; # Consume the SUBSCRIBE reply.\n            r FLUSHALL\n            r HELLO 2\n            r config set tracking-table-max-keys 1000000\n        }\n    ",
    )
    r.run("CLIENT", "TRACKING", "on", "REDIRECT", redir_id, "noloop")
    res = r.run("client", "trackinginfo")
    flags = res["flags"]
    assert "on noloop" == flags
    redirect = res["redirect"]
    assert redir_id == redirect
    prefixes = res["prefixes"]
    assert "" == prefixes


def test_client_trackinginfo_provides_reasonable_results_when_tracking_optin(r: ValkeyTestClient) -> None:
    """
    test {CLIENT TRACKINGINFO provides reasonable results when tracking optin} {
        r CLIENT TRACKING off
        r CLIENT TRACKING on optin
        set res [r client trackinginfo]
        set flags [dict get $res flags]
        assert_equal {on optin} $flags
        set redirect [dict get $res redirect]
        assert_equal {0} $redirect
        set prefixes [dict get $res prefixes]
        assert_equal {} $prefixes

        r CLIENT CACHING yes
        set res [r client trackinginfo]
        set flags [dict get $res flags]
        assert_equal {on optin caching-yes} $flags
    }
    """
    rd_redirection = ValkeyTestClient.create_from(r)
    rd_redirection.run("client", "id")
    redir_id = rd_redirection.run("read")
    rd_redirection.run("subscribe", "__redis__:invalidate")
    rd_redirection.run("read")
    rd = ValkeyTestClient.create_from(r)
    rd_sg = ValkeyTestClient.create_from(r)
    proc(
        "clean_all",
        "",
        "        uplevel {\n            # We should make r TRACKING off first. If r is in RESP3,\n            # r FLUSH ALL will send us tracking-redir-broken or other\n            # info which will not be consumed.\n            r CLIENT TRACKING off\n            $rd QUIT\n            $rd close\n            $rd_redirection QUIT\n            $rd_redirection close\n            set rd [valkey_deferring_client]\n            set rd_redirection [valkey_deferring_client]\n            $rd_redirection client id\n            set redir_id [$rd_redirection read]\n            $rd_redirection subscribe __redis__:invalidate\n            $rd_redirection read ; # Consume the SUBSCRIBE reply.\n            r FLUSHALL\n            r HELLO 2\n            r config set tracking-table-max-keys 1000000\n        }\n    ",
    )
    r.run("CLIENT", "TRACKING", "off")
    r.run("CLIENT", "TRACKING", "on", "optin")
    res = r.run("client", "trackinginfo")
    flags = res["flags"]
    assert "on optin" == flags
    redirect = res["redirect"]
    assert "0" == redirect
    prefixes = res["prefixes"]
    assert "" == prefixes
    r.run("CLIENT", "CACHING", "yes")
    res = r.run("client", "trackinginfo")
    flags = res["flags"]
    assert "on optin caching-yes" == flags


def test_client_trackinginfo_provides_reasonable_results_when_tracking_optout(r: ValkeyTestClient) -> None:
    """
    test {CLIENT TRACKINGINFO provides reasonable results when tracking optout} {
        r CLIENT TRACKING off
        r CLIENT TRACKING on optout
        set res [r client trackinginfo]
        set flags [dict get $res flags]
        assert_equal {on optout} $flags
        set redirect [dict get $res redirect]
        assert_equal {0} $redirect
        set prefixes [dict get $res prefixes]
        assert_equal {} $prefixes

        r CLIENT CACHING no
        set res [r client trackinginfo]
        set flags [dict get $res flags]
        assert_equal {on optout caching-no} $flags
    }
    """
    rd_redirection = ValkeyTestClient.create_from(r)
    rd_redirection.run("client", "id")
    redir_id = rd_redirection.run("read")
    rd_redirection.run("subscribe", "__redis__:invalidate")
    rd_redirection.run("read")
    rd = ValkeyTestClient.create_from(r)
    rd_sg = ValkeyTestClient.create_from(r)
    proc(
        "clean_all",
        "",
        "        uplevel {\n            # We should make r TRACKING off first. If r is in RESP3,\n            # r FLUSH ALL will send us tracking-redir-broken or other\n            # info which will not be consumed.\n            r CLIENT TRACKING off\n            $rd QUIT\n            $rd close\n            $rd_redirection QUIT\n            $rd_redirection close\n            set rd [valkey_deferring_client]\n            set rd_redirection [valkey_deferring_client]\n            $rd_redirection client id\n            set redir_id [$rd_redirection read]\n            $rd_redirection subscribe __redis__:invalidate\n            $rd_redirection read ; # Consume the SUBSCRIBE reply.\n            r FLUSHALL\n            r HELLO 2\n            r config set tracking-table-max-keys 1000000\n        }\n    ",
    )
    r.run("CLIENT", "TRACKING", "off")
    r.run("CLIENT", "TRACKING", "on", "optout")
    res = r.run("client", "trackinginfo")
    flags = res["flags"]
    assert "on optout" == flags
    redirect = res["redirect"]
    assert "0" == redirect
    prefixes = res["prefixes"]
    assert "" == prefixes
    r.run("CLIENT", "CACHING", "no")
    res = r.run("client", "trackinginfo")
    flags = res["flags"]
    assert "on optout caching-no" == flags


def test_client_trackinginfo_provides_reasonable_results_when_tracking_bcast_mode(r: ValkeyTestClient) -> None:
    """
    test {CLIENT TRACKINGINFO provides reasonable results when tracking bcast mode} {
        r CLIENT TRACKING off
        r CLIENT TRACKING on BCAST PREFIX foo PREFIX bar
        set res [r client trackinginfo]
        set flags [dict get $res flags]
        assert_equal {on bcast} $flags
        set redirect [dict get $res redirect]
        assert_equal {0} $redirect
        set prefixes [lsort [dict get $res prefixes]]
        assert_equal {bar foo} $prefixes

        r CLIENT TRACKING off
        r CLIENT TRACKING on BCAST
        set res [r client trackinginfo]
        set prefixes [dict get $res prefixes]
        assert_equal {{}} $prefixes
    }
    """
    rd_redirection = ValkeyTestClient.create_from(r)
    rd_redirection.run("client", "id")
    redir_id = rd_redirection.run("read")
    rd_redirection.run("subscribe", "__redis__:invalidate")
    rd_redirection.run("read")
    rd = ValkeyTestClient.create_from(r)
    rd_sg = ValkeyTestClient.create_from(r)
    proc(
        "clean_all",
        "",
        "        uplevel {\n            # We should make r TRACKING off first. If r is in RESP3,\n            # r FLUSH ALL will send us tracking-redir-broken or other\n            # info which will not be consumed.\n            r CLIENT TRACKING off\n            $rd QUIT\n            $rd close\n            $rd_redirection QUIT\n            $rd_redirection close\n            set rd [valkey_deferring_client]\n            set rd_redirection [valkey_deferring_client]\n            $rd_redirection client id\n            set redir_id [$rd_redirection read]\n            $rd_redirection subscribe __redis__:invalidate\n            $rd_redirection read ; # Consume the SUBSCRIBE reply.\n            r FLUSHALL\n            r HELLO 2\n            r config set tracking-table-max-keys 1000000\n        }\n    ",
    )
    r.run("CLIENT", "TRACKING", "off")
    r.run("CLIENT", "TRACKING", "on", "BCAST", "PREFIX", "foo", "PREFIX", "bar")
    res = r.run("client", "trackinginfo")
    flags = res["flags"]
    assert "on bcast" == flags
    redirect = res["redirect"]
    assert "0" == redirect
    prefixes = sorted(res["prefixes"])
    assert "bar foo" == prefixes
    r.run("CLIENT", "TRACKING", "off")
    r.run("CLIENT", "TRACKING", "on", "BCAST")
    res = r.run("client", "trackinginfo")
    prefixes = res["prefixes"]
    assert "{}" == prefixes


def test_client_trackinginfo_provides_reasonable_results_when_tracking_redir_broken(r: ValkeyTestClient) -> None:
    """
    test {CLIENT TRACKINGINFO provides reasonable results when tracking redir broken} {
        clean_all
        r HELLO 3
        r CLIENT TRACKING on REDIRECT $redir_id
        $rd_sg SET key1 1
        r GET key1
        $rd_redirection QUIT
        assert_equal OK [$rd_redirection read]
        $rd_sg SET key1 2
        set res [lsearch -exact [r read] "tracking-redir-broken"]
        assert {$res >= 0}
        set res [r client trackinginfo]
        set flags [dict get $res flags]
        assert_equal {on broken_redirect} $flags
        set redirect [dict get $res redirect]
        assert_equal $redir_id $redirect
        set prefixes [dict get $res prefixes]
        assert_equal {} $prefixes
    }
    """
    rd_redirection = ValkeyTestClient.create_from(r)
    rd_redirection.run("client", "id")
    redir_id = rd_redirection.run("read")
    rd_redirection.run("subscribe", "__redis__:invalidate")
    rd_redirection.run("read")
    rd = ValkeyTestClient.create_from(r)
    rd_sg = ValkeyTestClient.create_from(r)
    proc(
        "clean_all",
        "",
        "        uplevel {\n            # We should make r TRACKING off first. If r is in RESP3,\n            # r FLUSH ALL will send us tracking-redir-broken or other\n            # info which will not be consumed.\n            r CLIENT TRACKING off\n            $rd QUIT\n            $rd close\n            $rd_redirection QUIT\n            $rd_redirection close\n            set rd [valkey_deferring_client]\n            set rd_redirection [valkey_deferring_client]\n            $rd_redirection client id\n            set redir_id [$rd_redirection read]\n            $rd_redirection subscribe __redis__:invalidate\n            $rd_redirection read ; # Consume the SUBSCRIBE reply.\n            r FLUSHALL\n            r HELLO 2\n            r config set tracking-table-max-keys 1000000\n        }\n    ",
    )
    clean_all()
    r.run("HELLO", 3)
    r.run("CLIENT", "TRACKING", "on", "REDIRECT", redir_id)
    rd_sg.run("SET", "key1", 1)
    r.run("GET", "key1")
    rd_redirection.run("QUIT")
    assert "OK" == rd_redirection.run("read")
    rd_sg.run("SET", "key1", 2)
    res = lsearch("-exact", r.run("read"), "tracking-redir-broken")
    assert res >= 0
    res = r.run("client", "trackinginfo")
    flags = res["flags"]
    assert "on broken_redirect" == flags
    redirect = res["redirect"]
    assert redir_id == redirect
    prefixes = res["prefixes"]
    assert "" == prefixes


def test_regression_test_for_11715(r: ValkeyTestClient) -> None:
    """
    test {Regression test for #11715} {
        # This issue manifests when a client invalidates keys through the max key
        # limit, which invalidates keys to get the server below the limit, but no command is
        # then executed. This can occur in several ways but the simplest is through
        # multi-exec which queues commands.
        clean_all
        r config set tracking-table-max-keys 2

        # The cron will invalidate keys if we're above the limit, so disable it.
        r debug pause-cron 1

        # Set up a client that has listened to 2 keys and start a multi, this
        # sets up the crash for later.
        $rd HELLO 3
        $rd read
        $rd CLIENT TRACKING on
        assert_match "OK" [$rd read]
        $rd mget "1{tag}" "2{tag}"
        assert_match "{} {}" [$rd read]
        $rd multi
        assert_match "OK" [$rd read]

        # Reduce the tracking table keys to 1, this doesn't immediately take affect, but
        # instead will apply on the next command.
        r config set tracking-table-max-keys 1

        # This command will get queued, so make sure this command doesn't crash.
        $rd ping
        $rd exec

        # Validate we got some invalidation message and then the command was queued.
        assert_match "invalidate *{tag}" [$rd read]
        assert_match "QUEUED" [$rd read]
        assert_match "PONG" [$rd read]

        r debug pause-cron 0
    } {OK} {needs:debug}
    """
    rd_redirection = ValkeyTestClient.create_from(r)
    rd_redirection.run("client", "id")
    redir_id = rd_redirection.run("read")
    rd_redirection.run("subscribe", "__redis__:invalidate")
    rd_redirection.run("read")
    rd = ValkeyTestClient.create_from(r)
    rd_sg = ValkeyTestClient.create_from(r)
    proc(
        "clean_all",
        "",
        "        uplevel {\n            # We should make r TRACKING off first. If r is in RESP3,\n            # r FLUSH ALL will send us tracking-redir-broken or other\n            # info which will not be consumed.\n            r CLIENT TRACKING off\n            $rd QUIT\n            $rd close\n            $rd_redirection QUIT\n            $rd_redirection close\n            set rd [valkey_deferring_client]\n            set rd_redirection [valkey_deferring_client]\n            $rd_redirection client id\n            set redir_id [$rd_redirection read]\n            $rd_redirection subscribe __redis__:invalidate\n            $rd_redirection read ; # Consume the SUBSCRIBE reply.\n            r FLUSHALL\n            r HELLO 2\n            r config set tracking-table-max-keys 1000000\n        }\n    ",
    )
    clean_all()
    r.run("config", "set", "tracking-table-max-keys", 2)
    r.run("debug", "pause-cron", 1)
    rd.run("HELLO", 3)
    rd.run("read")
    rd.run("CLIENT", "TRACKING", "on")
    assert fnmatch(str(rd.run("read")), "OK")
    rd.run("mget", "1{tag}", "2{tag}")
    assert fnmatch(str(rd.run("read")), "{} {}")
    rd.run("multi")
    assert fnmatch(str(rd.run("read")), "OK")
    r.run("config", "set", "tracking-table-max-keys", 1)
    rd.run("ping")
    rd.run("exec")
    assert fnmatch(str(rd.run("read")), "invalidate *{tag}")
    assert fnmatch(str(rd.run("read")), "QUEUED")
    assert fnmatch(str(rd.run("read")), "PONG")
    assert r.run("debug", "pause-cron", 0) == "OK"


@pytest.mark.parametrize(["resp"], [(3), (2)])
def test_resp_resp_based_basic_invalidation_with_client_reply_off(r: ValkeyTestClient, resp: int, rd, rd_sg) -> None:
    """
    test "RESP$resp based basic invalidation with client reply off" {
        # This entire test is mostly irrelevant for RESP2, but we run it anyway just for some extra coverage.
        clean_all

        $rd hello $resp
        $rd read
        $rd client tracking on
        $rd read

        $rd_sg set foo bar
        $rd get foo
        $rd read

        $rd client reply off

        $rd_sg set foo bar2

        if {$resp == 3} {
            assert_equal {invalidate foo} [$rd read]
        } elseif {$resp == 2} { } ;# Just coverage

        # Verify things didn't get messed up and no unexpected reply was pushed to the client.
        $rd client reply on
        assert_equal {OK} [$rd read]
        $rd ping
        assert_equal {PONG} [$rd read]
    }
    """
    clean_all()
    rd.run("hello", resp)
    rd.run("read")
    rd.run("client", "tracking", "on")
    rd.run("read")
    rd_sg.run("set", "foo", "bar")
    rd.run("get", "foo")
    rd.run("read")
    rd.run("client", "reply", "off")
    rd_sg.run("set", "foo", "bar2")
    if resp == 3:
        assert "invalidate foo" == rd.run("read")
    elif resp == 2:
        pass
    rd.run("client", "reply", "on")
    assert "OK" == rd.run("read")
    rd.run("ping")
    assert "PONG" == rd.run("read")


def test_resp3_based_basic_redirect_invalidation_with_client_reply_off(r: ValkeyTestClient, rd, rd_sg) -> None:
    """
    test {RESP3 based basic redirect invalidation with client reply off} {
        clean_all

        set rd_redir [valkey_deferring_client]
        $rd_redir hello 3
        $rd_redir read

        $rd_redir client id
        set rd_redir_id [$rd_redir read]

        $rd client tracking on redirect $rd_redir_id
        $rd read

        $rd_sg set foo bar
        $rd get foo
        $rd read

        $rd_redir client reply off

        $rd_sg set foo bar2
        assert_equal {invalidate foo} [$rd_redir read]

        # Verify things didn't get messed up and no unexpected reply was pushed to the client.
        $rd_redir client reply on
        assert_equal {OK} [$rd_redir read]
        $rd_redir ping
        assert_equal {PONG} [$rd_redir read]

        $rd_redir close
    }
    """
    clean_all()
    rd_redir = ValkeyTestClient.create_from(r)
    rd_redir.run("hello", 3)
    rd_redir.run("read")
    rd_redir.run("client", "id")
    rd_redir_id = rd_redir.run("read")
    rd.run("client", "tracking", "on", "redirect", rd_redir_id)
    rd.run("read")
    rd_sg.run("set", "foo", "bar")
    rd.run("get", "foo")
    rd.run("read")
    rd_redir.run("client", "reply", "off")
    rd_sg.run("set", "foo", "bar2")
    assert "invalidate foo" == rd_redir.run("read")
    rd_redir.run("client", "reply", "on")
    assert "OK" == rd_redir.run("read")
    rd_redir.run("ping")
    assert "PONG" == rd_redir.run("read")
    rd_redir.run("close")


def test_resp3_based_basic_tracking_redir_broken_with_client_reply_off(
    r: ValkeyTestClient, rd, rd_redirection, rd_sg
) -> None:
    """
    test {RESP3 based basic tracking-redir-broken with client reply off} {
        clean_all

        $rd hello 3
        $rd read
        $rd client tracking on redirect $redir_id
        $rd read

        $rd_sg set foo bar
        $rd get foo
        $rd read

        $rd client reply off

        $rd_redirection quit
        $rd_redirection read

        $rd_sg set foo bar2

        set res [lsearch -exact [$rd read] "tracking-redir-broken"]
        assert_morethan_equal $res 0

        # Verify things didn't get messed up and no unexpected reply was pushed to the client.
        $rd client reply on
        assert_equal {OK} [$rd read]
        $rd ping
        assert_equal {PONG} [$rd read]
    }
    """
    clean_all()
    rd.run("hello", 3)
    rd.run("read")
    rd.run("client", "tracking", "on", "redirect", redir_id)
    rd.run("read")
    rd_sg.run("set", "foo", "bar")
    rd.run("get", "foo")
    rd.run("read")
    rd.run("client", "reply", "off")
    rd_redirection.run("quit")
    rd_redirection.run("read")
    rd_sg.run("set", "foo", "bar2")
    res = lsearch("-exact", rd.run("read"), "tracking-redir-broken")
    assert res >= 0
    rd.run("client", "reply", "on")
    assert "OK" == rd.run("read")
    rd.run("ping")
    assert "PONG" == rd.run("read")


"""
$rd_redirection close
"""


"""
$rd_sg close
"""


"""
$rd close
"""

pytestmark = [pytest.mark.tracking_network]


def test_client_trackinginfo_when_start(r: ValkeyTestClient) -> None:
    """
    test {CLIENT TRACKINGINFO when start} {
        set res [r client trackinginfo]
        set flags [dict get $res flags]
        assert_equal {off} $flags
        set redirect [dict get $res redirect]
        assert_equal {-1} $redirect
        set prefixes [dict get $res prefixes]
        assert_equal {} $prefixes
    }
    """
    res = r.run("client", "trackinginfo")
    flags = res["flags"]
    assert "off" == flags
    redirect = res["redirect"]
    assert "-1" == redirect
    prefixes = res["prefixes"]
    assert "" == prefixes


def test_coverage_basic_client_caching(r: ValkeyTestClient) -> None:
    """
    test {Coverage: Basic CLIENT CACHING} {
        set rd_redirection [valkey_deferring_client]
        $rd_redirection client id
        set redir_id [$rd_redirection read]
        assert_equal {OK} [r CLIENT TRACKING on OPTIN REDIRECT $redir_id]
        assert_equal {OK} [r CLIENT CACHING yes]
        r CLIENT TRACKING off
    } {OK}
    """
    rd_redirection = ValkeyTestClient.create_from(r)
    rd_redirection.run("client", "id")
    redir_id = rd_redirection.run("read")
    assert "OK" == r.run("CLIENT", "TRACKING", "on", "OPTIN", "REDIRECT", redir_id)
    assert "OK" == r.run("CLIENT", "CACHING", "yes")
    assert r.run("CLIENT", "TRACKING", "off") == "OK"


def test_coverage_basic_client_reply(r: ValkeyTestClient) -> None:
    """
    test {Coverage: Basic CLIENT REPLY} {
        r CLIENT REPLY on
    } {OK}
    """
    assert r.run("CLIENT", "REPLY", "on") == "OK"


def test_coverage_basic_client_trackinginfo(r: ValkeyTestClient) -> None:
    """
    test {Coverage: Basic CLIENT TRACKINGINFO} {
        r CLIENT TRACKINGINFO
    } {flags off redirect -1 prefixes {}}
    """
    assert r.run("CLIENT", "TRACKINGINFO") == "flags off redirect -1 prefixes {}"


def test_coverage_basic_client_getredir(r: ValkeyTestClient) -> None:
    """
    test {Coverage: Basic CLIENT GETREDIR} {
        r CLIENT GETREDIR
    } {-1}
    """
    assert r.run("CLIENT", "GETREDIR") == "-1"


# --- stubs for unimplemented TCL helpers ---


def assert_(*args):
    raise NotImplementedError("assert_")


def clean_all(*args):
    raise NotImplementedError("clean_all")


def expr(*args):
    raise NotImplementedError("expr")


def fail(*args):
    raise NotImplementedError("fail")


def get_field_in_client_info(*args):
    raise NotImplementedError("get_field_in_client_info")


def lsearch(*args):
    raise NotImplementedError("lsearch")


def proc(*args):
    raise NotImplementedError("proc")


def regexp(*args):
    raise NotImplementedError("regexp")


def s(*args):
    raise NotImplementedError("s")


def split(*args):
    raise NotImplementedError("split")


def string(*args):
    raise NotImplementedError("string")


def wait_for_blocked_clients_count(*args):
    raise NotImplementedError("wait_for_blocked_clients_count")


def wait_for_condition(*args):
    raise NotImplementedError("wait_for_condition")


def wait_lazyfree_done(*args):
    raise NotImplementedError("wait_lazyfree_done")


def while_(*args):
    raise NotImplementedError("while_")
