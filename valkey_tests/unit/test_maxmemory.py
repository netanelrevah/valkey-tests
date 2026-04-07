# ruff: noqa: PLR2004, F841, RUF043, ANN001, ANN002, ANN201
import time

import pytest

from tests.valkey_test_client import ValkeyTestClient

pytestmark = [pytest.mark.maxmemory_external_skip]


"""
r config set maxmemory 11mb
"""


"""
r config set maxmemory-policy allkeys-lru
"""


"""
set server_pid s process_id
"""


"""
r config set min-io-threads-avoid-copy-reply 0
"""


"""
r config set min-string-size-avoid-copy-reply 0
"""


"""
r config set min-string-size-avoid-copy-reply-threaded 0
"""


"""
proc init_test {client_eviction} {
    r flushdb sync

    set prev_maxmemory_clients [r config get maxmemory-clients]
    if $client_eviction {
        r config set maxmemory-clients 3mb
        r client no-evict on
    } else {
        r config set maxmemory-clients 0
    }

    r config resetstat
    # fill 5mb using 50 keys of 100kb
    for {set j 0} {$j < 50} {incr j} {
        r setrange $j 100000 x
    }
    assert_equal [r dbsize] 50
}
"""


"""
proc check_eviction_test {client_eviction} {
    set evicted_keys [s evicted_keys]
    set evicted_clients [s evicted_clients]
    set dbsize [r dbsize]

    if $client_eviction {
        return [expr $evicted_clients > 0 && $evicted_keys == 0 && $dbsize == 50]
    } else {
        return [expr $evicted_clients == 0 && $evicted_keys > 0 && $dbsize < 50]
    }
}
"""


"""
proc verify_eviction_test {client_eviction} {
    set evicted_keys [s evicted_keys]
    set evicted_clients [s evicted_clients]
    set dbsize [r dbsize]

    if $::verbose {
        puts "evicted keys: $evicted_keys"
        puts "evicted clients: $evicted_clients"
        puts "dbsize: $dbsize"
    }

    assert [check_eviction_test $client_eviction]
}
"""


"""
set clients {}
"""


@pytest.mark.parametrize(["client_eviction"], [("false"), ("true")])
def test_eviction_due_to_output_buffers_of_many_mget_clients_client_eviction_client_eviction(
    r: ValkeyTestClient, client_eviction
) -> None:
    """
    test "eviction due to output buffers of many MGET clients, client eviction: $client_eviction" {
        init_test $client_eviction

        for {set j 0} {$j < 20} {incr j} {
            set rr [valkey_deferring_client]
            lappend clients $rr
        }

        # Generate client output buffers via MGET until we can observe some effect on
        # keys / client eviction, or we time out.
        set t [clock seconds]
        while {![check_eviction_test $client_eviction] && [expr [clock seconds] - $t] < 20} {
            foreach rr $clients {
                if {[catch {
                    $rr mget 1
                    $rr flush
                } err]} {
                    lremove clients $rr
                }
            }
        }

        verify_eviction_test $client_eviction
    }
    """
    init_test(client_eviction)
    j = 0
    while j < 20:
        rr = valkey_deferring_client()
        lappend("clients", rr)
        j += 1
    t = clock("seconds")
    while_(
        "![check_eviction_test $client_eviction] && [expr [clock seconds] - $t] < 20",
        "                foreach rr $clients {\n                    if {[catch {\n                        $rr mget 1\n                        $rr flush\n                    } err]} {\n                        lremove clients $rr\n                    }\n                }\n            ",
    )
    verify_eviction_test(client_eviction)


"""
foreach rr clients {
    $rr close
}
"""


"""
set clients {}
"""


@pytest.mark.xfail(reason="not implemented")
@pytest.mark.parametrize(["client_eviction"], [("false"), ("true")])
def test_eviction_due_to_input_buffer_of_a_dead_client_client_eviction_client_eviction(
    r: ValkeyTestClient, client_eviction
) -> None:
    """
    test "eviction due to input buffer of a dead client, client eviction: $client_eviction" {
        init_test $client_eviction

        for {set j 0} {$j < 30} {incr j} {
            set rr [valkey_deferring_client]
            lappend clients $rr
        }

        foreach rr $clients {
            if {[catch {
                $rr write "*250\r\n"
                for {set j 0} {$j < 249} {incr j} {
                    $rr write "\$1000\r\n"
                    $rr write [string repeat x 1000]
                    $rr write "\r\n"
                    $rr flush
                }
                after 100; # give the server some time to process the input buffer - this was added to make sure the test pass with io-threads active.
            }]} {
                lremove clients $rr
            }
        }

        verify_eviction_test $client_eviction
    }
    """
    init_test(client_eviction)
    j = 0
    while j < 30:
        rr = valkey_deferring_client()
        lappend("clients", rr)
        j += 1
    # TODO: foreach rr clients {
    #       if {[catch {
    #           $rr write "*250\r\n"
    #           for {set j 0} {$j < 249} {incr j} {
    #               $rr write "\$1000\r\n"
    #               $rr write [string repeat x 1000]
    #               $rr write "\r\n"
    #               $rr flush
    #           }
    #           after 100; # give the server some time to process the input buffer - this was added to make sure the test pass with io-threads active.
    #       }]} {
    #           lremove clients $rr
    #       }
    #   }
    verify_eviction_test(client_eviction)


"""
foreach rr clients {
    $rr close
}
"""


"""
set clients {}
"""


@pytest.mark.xfail(reason="not implemented")
@pytest.mark.parametrize(["client_eviction"], [("false"), ("true")])
def test_eviction_due_to_output_buffers_of_pubsub_client_eviction_client_eviction(
    r: ValkeyTestClient, client_eviction
) -> None:
    """
    test "eviction due to output buffers of pubsub, client eviction: $client_eviction" {
        init_test $client_eviction

        for {set j 0} {$j < 20} {incr j} {
            set rr [valkey_client]
            lappend clients $rr
        }

        foreach rr $clients {
            $rr subscribe bla
        }

        # Generate client output buffers via PUBLISH until we can observe some effect on
        # keys / client eviction, or we time out.
        set bigstr [string repeat x 100000]
        set t [clock seconds]
        while {![check_eviction_test $client_eviction] && [expr [clock seconds] - $t] < 20} {
            if {[catch { r publish bla $bigstr } err]} {
                if $::verbose {
                    puts "Error publishing: $err"
                }
            }
        }

        verify_eviction_test $client_eviction
    }
    """
    init_test(client_eviction)
    j = 0
    while j < 20:
        rr = valkey_client()
        lappend("clients", rr)
        j += 1
    # TODO: foreach rr clients {
    #       $rr subscribe bla
    #   }
    bigstr = string("repeat", "x", 100000)
    t = clock("seconds")
    while_(
        "![check_eviction_test $client_eviction] && [expr [clock seconds] - $t] < 20",
        '                if {[catch { r publish bla $bigstr } err]} {\n                    if $::verbose {\n                        puts "Error publishing: $err"\n                    }\n                }\n            ',
    )
    verify_eviction_test(client_eviction)


"""
foreach rr clients {
    $rr close
}
"""

pytestmark = [pytest.mark.maxmemory_external_skip]


@pytest.mark.parametrize(
    ["policy"],
    [
        ("allkeys-random"),
        ("allkeys-lru"),
        ("allkeys-lfu"),
        ("volatile-lru"),
        ("volatile-lfu"),
        ("volatile-random"),
        ("volatile-ttl"),
    ],
)
def test_maxmemory_is_the_memory_limit_honoured_policy_policy(r: ValkeyTestClient, policy) -> None:
    """
    test "maxmemory - is the memory limit honoured? (policy $policy)" {
        # make sure to start with a blank instance
        r flushall
        # Get the current memory limit and calculate a new limit.
        # We just add 100k to the current memory size so that it is
        # fast for us to reach that limit.
        set used [s used_memory]
        set limit [expr {$used+100*1024}]
        r config set maxmemory $limit
        r config set maxmemory-policy $policy
        # Now add keys until the limit is almost reached.
        set numkeys 0
        while 1 {
            r setex [randomKey] 10000 x
            incr numkeys
            if {[s used_memory]+4096 > $limit} {
                assert {$numkeys > 10}
                break
            }
        }
        # If we add the same number of keys already added again, we
        # should still be under the limit.
        for {set j 0} {$j < $numkeys} {incr j} {
            r setex [randomKey] 10000 x
        }
        assert {[s used_memory] < ($limit+4096)}
    }
    """
    r.run("flushall")
    used = s("used_memory")
    limit = expr("$used+100*1024")
    r.run("config", "set", "maxmemory", limit)
    r.run("config", "set", "maxmemory-policy", policy)
    numkeys = 0
    while_(
        1,
        "                r setex [randomKey] 10000 x\n                incr numkeys\n                if {[s used_memory]+4096 > $limit} {\n                    assert {$numkeys > 10}\n                    break\n                }\n            ",
    )
    j = 0
    while j < numkeys:
        r.run("setex", random_key(), 10000, "x")
        j += 1
    assert_("[s used_memory] < ($limit+4096)")


@pytest.mark.parametrize(
    ["policy"], [("allkeys-random"), ("allkeys-lru"), ("volatile-lru"), ("volatile-random"), ("volatile-ttl")]
)
def test_maxmemory_only_allkeys_should_remove_non_volatile_keys_policy(r: ValkeyTestClient, policy) -> None:
    """
    test "maxmemory - only allkeys-* should remove non-volatile keys ($policy)" {
        # make sure to start with a blank instance
        r flushall
        # Get the current memory limit and calculate a new limit.
        # We just add 100k to the current memory size so that it is
        # fast for us to reach that limit.
        set used [s used_memory]
        set limit [expr {$used+100*1024}]
        r config set maxmemory $limit
        r config set maxmemory-policy $policy
        # Now add keys until the limit is almost reached.
        set numkeys 0
        while 1 {
            r set [randomKey] x
            incr numkeys
            if {[s used_memory]+4096 > $limit} {
                assert {$numkeys > 10}
                break
            }
        }
        # If we add the same number of keys already added again and
        # the policy is allkeys-* we should still be under the limit.
        # Otherwise we should see an error reported by Server.
        set err 0
        for {set j 0} {$j < $numkeys} {incr j} {
            if {[catch {r set [randomKey] x} e]} {
                if {[string match {*used memory*} $e]} {
                    set err 1
                }
            }
        }
        if {[string match allkeys-* $policy]} {
            assert {[s used_memory] < ($limit+4096)}
        } else {
            assert {$err == 1}
        }
    }
    """
    r.run("flushall")
    used = s("used_memory")
    limit = expr("$used+100*1024")
    r.run("config", "set", "maxmemory", limit)
    r.run("config", "set", "maxmemory-policy", policy)
    numkeys = 0
    while_(
        1,
        "                r set [randomKey] x\n                incr numkeys\n                if {[s used_memory]+4096 > $limit} {\n                    assert {$numkeys > 10}\n                    break\n                }\n            ",
    )
    err = 0
    j = 0
    while j < numkeys:
        if catch("r set [randomKey] x", "e"):
            if_("[string match {*used memory*} $e]", "                        set err 1\n                    ")
        j += 1
    if string("match", "allkeys-*", policy):
        assert_("[s used_memory] < ($limit+4096)")
    else:
        assert_("$err == 1")


@pytest.mark.parametrize(["policy"], [("volatile-lru"), ("volatile-lfu"), ("volatile-random"), ("volatile-ttl")])
def test_maxmemory_policy_policy_should_only_remove_volatile_keys(r: ValkeyTestClient, policy) -> None:
    """
    test "maxmemory - policy $policy should only remove volatile keys." {
        # make sure to start with a blank instance
        r flushall
        # Get the current memory limit and calculate a new limit.
        # We just add 400KiB to the current memory size so that it is
        # fast for us to reach that limit.
        set used [s used_memory]
        set limit [expr {$used+400*1024}]
        r config set maxmemory $limit
        r config set maxmemory-policy $policy
        # Now add keys until the limit is almost reached.
        set numkeys 0
        while 1 {
            # Odd keys are volatile
            # Even keys are non volatile
            if {$numkeys % 2} {
                r setex "key:$numkeys" 10000 x
            } else {
                r set "key:$numkeys" x
            }
            if {[s used_memory]+4096 > $limit} {
                assert {$numkeys > 10}
                break
            }
            incr numkeys
        }
        # Now we add the same number of volatile keys already added.
        # We expect the server to evict only volatile keys in order to make
        # space.
        set err 0
        for {set j 0} {$j < $numkeys} {incr j} {
            catch {r setex "foo:$j" 10000 x}
        }
        # We should still be under the limit.
        assert {[s used_memory] < ($limit+4096)}
        # However all our non volatile keys should be here.
        for {set j 0} {$j < $numkeys} {incr j 2} {
            assert {[r exists "key:$j"]}
        }
    }
    """
    r.run("flushall")
    used = s("used_memory")
    limit = expr("$used+400*1024")
    r.run("config", "set", "maxmemory", limit)
    r.run("config", "set", "maxmemory-policy", policy)
    numkeys = 0
    while_(
        1,
        '                # Odd keys are volatile\n                # Even keys are non volatile\n                if {$numkeys % 2} {\n                    r setex "key:$numkeys" 10000 x\n                } else {\n                    r set "key:$numkeys" x\n                }\n                if {[s used_memory]+4096 > $limit} {\n                    assert {$numkeys > 10}\n                    break\n                }\n                incr numkeys\n            ',
    )
    err = 0
    j = 0
    while j < numkeys:
        try:
            r.run("setex", f"foo:{j}", 10000, "x")
        except Exception:
            pass
        j += 1
    assert_("[s used_memory] < ($limit+4096)")
    j = 0
    while j < numkeys:
        assert r.run("exists", f"key:{j}")
        j += 2


"""
proc slave_query_buffer {srv} {
    set clients [split [$srv client list] "\r\n"]
    set c [lsearch -inline $clients *flags=S*]
    if {[string length $c] > 0} {
        assert {[regexp {qbuf=([0-9]+)} $c - qbuf]}
        assert {[regexp {qbuf-free=([0-9]+)} $c - qbuf_free]}
        return [expr $qbuf + $qbuf_free]
    }
    return 0
}
"""


"""
proc test_slave_buffers {test_name cmd_count payload_len limit_memory pipeline} {
    start_server {tags {"maxmemory external:skip"}} {
        start_server {} {
        set slave_pid [s process_id]
        test "$test_name" {
            set slave [srv 0 client]
            set slave_host [srv 0 host]
            set slave_port [srv 0 port]
            set master [srv -1 client]
            set master_host [srv -1 host]
            set master_port [srv -1 port]

            # Disable slow log for master to avoid memory growth in slow env.
            $master config set slowlog-log-slower-than -1

            # add 100 keys of 100k (10MB total)
            for {set j 0} {$j < 100} {incr j} {
                $master setrange "key:$j" 100000 asdf
            }

            # make sure master doesn't disconnect slave because of timeout
            $master config set repl-timeout 1200 ;# 20 minutes (for valgrind and slow machines)
            $master config set maxmemory-policy allkeys-random
            $master config set client-output-buffer-limit "replica 100000000 100000000 300"
            $master config set repl-backlog-size [expr {10*1024}]

            # disable latency tracking
            $master config set latency-tracking no
            $slave config set latency-tracking no

            $slave slaveof $master_host $master_port
            wait_for_condition 50 100 {
                [s 0 master_link_status] eq {up}
            } else {
                fail "Replication not started."
            }

            # measure used memory after the slave connected and set maxmemory
            set orig_used [s -1 used_memory]
            set orig_client_buf [s -1 mem_clients_normal]
            set orig_mem_not_counted_for_evict [s -1 mem_not_counted_for_evict]
            set orig_used_no_repl [expr {$orig_used - $orig_mem_not_counted_for_evict}]
            set limit [expr {$orig_used - $orig_mem_not_counted_for_evict + 32*1024}]

            if {$limit_memory==1} {
                $master config set maxmemory $limit
            }

            # put the slave to sleep
            set rd_slave [valkey_deferring_client]
            pause_process $slave_pid

            # send some 10mb worth of commands that don't increase the memory usage
            if {$pipeline == 1} {
                set rd_master [valkey_deferring_client -1]
                for {set k 0} {$k < $cmd_count} {incr k} {
                    $rd_master setrange key:0 0 [string repeat A $payload_len]
                }
                for {set k 0} {$k < $cmd_count} {incr k} {
                    $rd_master read
                }
            } else {
                for {set k 0} {$k < $cmd_count} {incr k} {
                    $master setrange key:0 0 [string repeat A $payload_len]
                }
            }

            set new_used [s -1 used_memory]
            set slave_buf [s -1 mem_clients_slaves]
            set client_buf [s -1 mem_clients_normal]
            set mem_not_counted_for_evict [s -1 mem_not_counted_for_evict]
            set used_no_repl [expr {$new_used - $mem_not_counted_for_evict - [slave_query_buffer $master]}]
            # we need to exclude replies buffer and query buffer of replica from used memory.
            # removing the replica (output) buffers is done so that we are able to measure any other
            # changes to the used memory and see that they're insignificant (the test's purpose is to check that
            # the replica buffers are counted correctly, so the used memory growth after deducting them
            # should be nearly 0).
            # we remove the query buffers because on slow test platforms, they can accumulate many ACKs.
            set delta [expr {($used_no_repl - $client_buf) - ($orig_used_no_repl - $orig_client_buf)}]

            assert {[$master dbsize] == 100}
            assert {$slave_buf > 2*1024*1024} ;# some of the data may have been pushed to the OS buffers
            set delta_max [expr {$cmd_count / 2}] ;# 1 byte unaccounted for, with 1M commands will consume some 1MB
            assert {$delta < $delta_max && $delta > -$delta_max}

            $master client kill type slave
            set info_str [$master info memory]
            set killed_used [getInfoProperty $info_str used_memory]
            set killed_mem_not_counted_for_evict [getInfoProperty $info_str mem_not_counted_for_evict]
            set killed_slave_buf [s -1 mem_clients_slaves]
            # we need to exclude replies buffer and query buffer of slave from used memory after kill slave
            set killed_used_no_repl [expr {$killed_used - $killed_mem_not_counted_for_evict - [slave_query_buffer $master]}]
            set delta_no_repl [expr {$killed_used_no_repl - $used_no_repl}]
            assert {[$master dbsize] == 100}
            assert {$killed_slave_buf == 0}
            assert {$delta_no_repl > -$delta_max && $delta_no_repl < $delta_max}

        }
        # unfreeze slave process (after the 'test' succeeded or failed, but before we attempt to terminate the server
        resume_process $slave_pid
        }
    }
}
"""


"""
test_slave_buffers {slave buffer are counted correctly} 1000000 10 0 1
"""


"""
test_slave_buffers "replica buffer don't induce eviction" 100000 100 1 0
"""

pytestmark = [pytest.mark.maxmemory_external_skip]


def test_don_t_rehash_if_used_memory_exceeds_maxmemory_after_rehash(r: ValkeyTestClient) -> None:
    """
    test {Don't rehash if used memory exceeds maxmemory after rehash} {
        r config set latency-tracking no
        r config set maxmemory 0
        r config set maxmemory-policy allkeys-random
        set dbnum [expr {$::singledb ? 0 : 9}]

        # Populate some, then check table size and populate more up to one less
        # than the soft maximum fill factor. Adding some more elements after
        # this does not trigger rehashing, because rehashing would eat some
        # kilobytes of memory.
        populate 2000 a 1
        set table_size [main_hash_table_size]
        populate [main_hash_table_keys_before_rehashing_starts] b 1

        # Now we are close to resizing. Check that rehashing didn't start.
        assert_equal $table_size [main_hash_table_size]
        assert_no_match "*Hash table 1 stats*" [r debug htstats $dbnum]

        set dbsize_before [r dbsize]
        set used [s used_memory]
        set limit [expr {$used + 10*1024}]
        r config set maxmemory $limit

        # Adding a key to meet the 1:1 radio.
        r set k0 v0
        # The table has reached the soft max fill factor.
        # It can be resized in tryResizeHashTables in cron,
        # or we add a key to let it check whether it can be resized.
        r set k1 v1
        # Next writing command will trigger evicting some keys if last
        # command trigger DB dict rehash
        r set k2 v2
        # There must be three more keys because the server doesn't evict keys.
        assert_equal [r dbsize] [expr {$dbsize_before + 3}]
    }
    """
    r.run("config", "set", "latency-tracking", "no")
    r.run("config", "set", "maxmemory", 0)
    r.run("config", "set", "maxmemory-policy", "allkeys-random")
    dbnum = expr("$::singledb ? 0 : 9")
    populate(2000, "a", 1)
    table_size = main_hash_table_size()
    populate(main_hash_table_keys_before_rehashing_starts(), "b", 1)
    assert table_size == main_hash_table_size()
    assert_no_match("*Hash table 1 stats*", r.run("debug", "htstats", dbnum))
    dbsize_before = r.run("dbsize")
    used = s("used_memory")
    limit = expr("$used + 10*1024")
    r.run("config", "set", "maxmemory", limit)
    r.run("set", "k0", "v0")
    r.run("set", "k1", "v1")
    r.run("set", "k2", "v2")
    assert r.run("dbsize") == expr("$dbsize_before + 3")


pytestmark = [pytest.mark.maxmemory_external_skip_io_threads_skip]


def test_client_tracking_don_t_cause_eviction_feedback_loop(r: ValkeyTestClient) -> None:
    """
    test {client tracking don't cause eviction feedback loop} {
        r config set latency-tracking no
        r config set maxmemory 0
        r config set maxmemory-policy allkeys-lru
        r config set maxmemory-eviction-tenacity 100
        # 10 clients listening on tracking messages
        set clients {}
        for {set j 0} {$j < 10} {incr j} {
            lappend clients [valkey_deferring_client]
        }
        foreach rd $clients {
            $rd HELLO 3
            $rd read ; # Consume the HELLO reply
            $rd CLIENT TRACKING on
            $rd read ; # Consume the CLIENT reply
        }

        # populate 300 keys, with long key name and short value
        for {set j 0} {$j < 300} {incr j} {
            set key $j[string repeat x 1000]
            r set $key x

            # for each key, enable caching for this key
            foreach rd $clients {
                $rd get $key
                $rd read
            }
        }

        # we need to wait one second for the client querybuf excess memory to be
        # trimmed by cron, otherwise the INFO used_memory and CONFIG maxmemory
        # below (on slow machines) won't be "atomic" and won't trigger eviction.
        after 1100

        # set the memory limit which will cause a few keys to be evicted
        # we need to make sure to evict keynames of a total size of more than
        # 16kb since the (PROTO_REPLY_CHUNK_BYTES), only after that the
        # invalidation messages have a chance to trigger further eviction.
        set used [s used_memory]
        set limit [expr {$used - 40000}]
        r config set maxmemory $limit

        # make sure some eviction happened
        set evicted [s evicted_keys]
        if {$::verbose} { puts "evicted: $evicted" }

        # make sure we didn't drain the database
        assert_range [r dbsize] 200 300

        assert_range $evicted 10 50
        foreach rd $clients {
            $rd read ;# make sure we have some invalidation message waiting
            $rd close
        }

        # eviction continues (known problem described in #8069)
        # for now this test only make sures the eviction loop itself doesn't
        # have feedback loop
        set evicted [s evicted_keys]
        if {$::verbose} { puts "evicted: $evicted" }
    }
    """
    r.run("config", "set", "latency-tracking", "no")
    r.run("config", "set", "maxmemory", 0)
    r.run("config", "set", "maxmemory-policy", "allkeys-lru")
    r.run("config", "set", "maxmemory-eviction-tenacity", 100)
    clients = ""
    j = 0
    while j < 10:
        lappend("clients", valkey_deferring_client())
        j += 1
    foreach(
        "rd",
        clients,
        "            $rd HELLO 3\n            $rd read ; # Consume the HELLO reply\n            $rd CLIENT TRACKING on\n            $rd read ; # Consume the CLIENT reply\n        ",
    )
    j = 0
    while j < 300:
        key = j
        r.run("set", key, "x")
        foreach("rd", clients, "                $rd get $key\n                $rd read\n            ")
        j += 1
    time.sleep(1100 / 1000)
    used = s("used_memory")
    limit = expr("$used - 40000")
    r.run("config", "set", "maxmemory", limit)
    evicted = s("evicted_keys")
    if_("$::verbose", ' puts "evicted: $evicted" ')
    assert_range(r.run("dbsize"), 200, 300)
    assert_range(evicted, 10, 50)
    foreach(
        "rd",
        clients,
        "            $rd read ;# make sure we have some invalidation message waiting\n            $rd close\n        ",
    )
    evicted = s("evicted_keys")
    if_("$::verbose", ' puts "evicted: $evicted" ')


pytestmark = [pytest.mark.maxmemory, pytest.mark.external_skip]


def test_propagation_with_eviction(r: ValkeyTestClient) -> None:
    """
    test {propagation with eviction} {
        set repl [attach_to_replication_stream]

        r set asdf1 1
        r set asdf2 2
        r set asdf3 3

        r config set maxmemory-policy allkeys-lru
        r config set maxmemory 1

        wait_for_condition 5000 10 {
            [r dbsize] eq 0
        } else {
            fail "Not all keys have been evicted"
        }

        r config set maxmemory 0
        r config set maxmemory-policy noeviction

        r set asdf4 4

        assert_replication_stream $repl {
            {select *}
            {set asdf1 1}
            {set asdf2 2}
            {set asdf3 3}
            {unlink asdf*}
            {unlink asdf*}
            {unlink asdf*}
            {set asdf4 4}
        }
        close_replication_stream $repl

        r config set maxmemory 0
        r config set maxmemory-policy noeviction
    }
    """
    repl = attach_to_replication_stream()
    r.run("set", "asdf1", 1)
    r.run("set", "asdf2", 2)
    r.run("set", "asdf3", 3)
    r.run("config", "set", "maxmemory-policy", "allkeys-lru")
    r.run("config", "set", "maxmemory", 1)
    wait_for_condition(
        5000,
        10,
        "            [r dbsize] eq 0\n        ",
        "else",
        '            fail "Not all keys have been evicted"\n        ',
    )
    r.run("config", "set", "maxmemory", 0)
    r.run("config", "set", "maxmemory-policy", "noeviction")
    r.run("set", "asdf4", 4)
    assert_replication_stream(
        repl,
        "            {select *}\n            {set asdf1 1}\n            {set asdf2 2}\n            {set asdf3 3}\n            {unlink asdf*}\n            {unlink asdf*}\n            {unlink asdf*}\n            {set asdf4 4}\n        ",
    )
    close_replication_stream(repl)
    r.run("config", "set", "maxmemory", 0)
    r.run("config", "set", "maxmemory-policy", "noeviction")


pytestmark = [pytest.mark.maxmemory, pytest.mark.external_skip]


def test_propagation_with_eviction_in_multi(r: ValkeyTestClient) -> None:
    """
    test {propagation with eviction in MULTI} {
        set repl [attach_to_replication_stream]

        r config set maxmemory-policy allkeys-lru

        r multi
        r incr x
        r config set maxmemory 1
        r incr x
        assert_equal [r exec] {1 OK 2}

        wait_for_condition 5000 10 {
            [r dbsize] eq 0
        } else {
            fail "Not all keys have been evicted"
        }

        assert_replication_stream $repl {
            {multi}
            {select *}
            {incr x}
            {incr x}
            {exec}
            {unlink x}
        }
        close_replication_stream $repl

        r config set maxmemory 0
        r config set maxmemory-policy noeviction
    }
    """
    repl = attach_to_replication_stream()
    r.run("config", "set", "maxmemory-policy", "allkeys-lru")
    r.run("multi")
    r.run("incr", "x")
    r.run("config", "set", "maxmemory", 1)
    r.run("incr", "x")
    assert r.run("exec") == "1 OK 2"
    wait_for_condition(
        5000,
        10,
        "            [r dbsize] eq 0\n        ",
        "else",
        '            fail "Not all keys have been evicted"\n        ',
    )
    assert_replication_stream(
        repl,
        "            {multi}\n            {select *}\n            {incr x}\n            {incr x}\n            {exec}\n            {unlink x}\n        ",
    )
    close_replication_stream(repl)
    r.run("config", "set", "maxmemory", 0)
    r.run("config", "set", "maxmemory-policy", "noeviction")


pytestmark = [pytest.mark.maxmemory, pytest.mark.external_skip]


def test_lru_or_lfu_value_of_the_key_just_added(r: ValkeyTestClient) -> None:
    """
    test {lru/lfu value of the key just added} {
        r config set maxmemory-policy allkeys-lru
        r set foo a
        assert {[r object idletime foo] <= 2}
        r del foo
        r set foo 1
        r get foo
        assert {[r object idletime foo] <= 2}

        r config set maxmemory-policy allkeys-lfu
        r del foo
        r set foo a
        assert {[r object freq foo] == 5}
    }
    """
    r.run("config", "set", "maxmemory-policy", "allkeys-lru")
    r.run("set", "foo", "a")
    assert r.run("object", "idletime", "foo") <= 2
    r.run("del", "foo")
    r.run("set", "foo", 1)
    r.run("get", "foo")
    assert r.run("object", "idletime", "foo") <= 2
    r.run("config", "set", "maxmemory-policy", "allkeys-lfu")
    r.run("del", "foo")
    r.run("set", "foo", "a")
    assert r.run("object", "freq", "foo") == 5


pytestmark = [pytest.mark.maxmemory, pytest.mark.external_skip]


def test_import_mode_should_forbid_eviction(r: ValkeyTestClient) -> None:
    """
    test {Import mode should forbid eviction} {
        r set key val
        r config set import-mode yes
        assert_equal [r client import-source on] {OK}
        r config set maxmemory-policy allkeys-lru
        r config set maxmemory 1

        assert_equal [r dbsize] {1}
        assert_error {OOM command not allowed*} {r set key1 val1}

        assert_equal [r client import-source off] {OK}
        r config set import-mode no

        assert_equal [r dbsize] {0}
    }
    """
    r.run("set", "key", "val")
    r.run("config", "set", "import-mode", "yes")
    assert r.run("client", "import-source", "on") == "OK"
    r.run("config", "set", "maxmemory-policy", "allkeys-lru")
    r.run("config", "set", "maxmemory", 1)
    assert r.run("dbsize") == "1"
    with pytest.raises(Exception, match="OOM\\ command\\ not\\ allowed.*"):
        r.run("set", "key1", "val1")
    assert r.run("client", "import-source", "off") == "OK"
    r.run("config", "set", "import-mode", "no")
    assert r.run("dbsize") == "0"


# --- stubs for unimplemented TCL helpers ---


def assert_(*args):
    raise NotImplementedError("assert_")


def assert_no_match(*args):
    raise NotImplementedError("assert_no_match")


def assert_range(*args):
    raise NotImplementedError("assert_range")


def assert_replication_stream(*args):
    raise NotImplementedError("assert_replication_stream")


def attach_to_replication_stream(*args):
    raise NotImplementedError("attach_to_replication_stream")


def catch(*args):
    raise NotImplementedError("catch")


def clock(*args):
    raise NotImplementedError("clock")


def close_replication_stream(*args):
    raise NotImplementedError("close_replication_stream")


def expr(*args):
    raise NotImplementedError("expr")


def foreach(*args):
    raise NotImplementedError("foreach")


def if_(*args):
    raise NotImplementedError("if_")


def init_test(*args):
    raise NotImplementedError("init_test")


def lappend(*args):
    raise NotImplementedError("lappend")


def main_hash_table_keys_before_rehashing_starts(*args):
    raise NotImplementedError("main_hash_table_keys_before_rehashing_starts")


def main_hash_table_size(*args):
    raise NotImplementedError("main_hash_table_size")


def populate(*args):
    raise NotImplementedError("populate")


def random_key(*args):
    raise NotImplementedError("random_key")


def s(*args):
    raise NotImplementedError("s")


def string(*args):
    raise NotImplementedError("string")


def valkey_client(*args):
    raise NotImplementedError("valkey_client")


def valkey_deferring_client(*args):
    raise NotImplementedError("valkey_deferring_client")


def verify_eviction_test(*args):
    raise NotImplementedError("verify_eviction_test")


def wait_for_condition(*args):
    raise NotImplementedError("wait_for_condition")


def while_(*args):
    raise NotImplementedError("while_")
