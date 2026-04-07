# ruff: noqa: ANN002, ANN201


from tests.valkey_test_client import ValkeyTestClient

"""
run_solo {violations} {
    start_server [list overrides [list save ""] tags {"large-memory"}] {
        test {XADD one huge field} {
            r config set proto-max-bulk-len 10000000000 ;#10gb
            r config set client-query-buffer-limit 10000000000 ;#10gb
            r write "*5\r\n\$4\r\nXADD\r\n\$2\r\nS1\r\n\$1\r\n*\r\n"
            r write "\$1\r\nA\r\n"
            catch {
                write_big_bulk 5000000000 ;#5gb
            } err
            assert_match {*too large*} $err
            r xlen S1
        } {0}
    }

    # One XADD with one huge (exactly nearly) 4GB field
    # This uncovers the overflow in lpEncodeGetType
    # Expected to fail resulting in an empty stream
    start_server [list overrides [list save ""] tags {"large-memory"}] {
        test {XADD one huge field - 1} {
            r config set proto-max-bulk-len 10000000000 ;#10gb
            r config set client-query-buffer-limit 10000000000 ;#10gb
            r write "*5\r\n\$4\r\nXADD\r\n\$2\r\nS1\r\n\$1\r\n*\r\n"
            r write "\$1\r\nA\r\n"
            catch {
                write_big_bulk 4294967295 ;#4gb-1
            } err
            assert_match {*too large*} $err
            r xlen S1
        } {0}
    }

    # Gradually add big stream fields using repeated XADD calls
    start_server [list overrides [list save ""] tags {"large-memory"}] {
        test {several XADD big fields} {
            r config set stream-node-max-bytes 0
            for {set j 0} {$j<10} {incr j} {
                r xadd stream * 1 $::str500 2 $::str500
            }
            r ping
            r xlen stream
        } {10}
    }

    # Add over 4GB to a single stream listpack (one XADD command)
    # Expected to fail resulting in an empty stream
    start_server [list overrides [list save ""] tags {"large-memory"}] {
        test {single XADD big fields} {
            r write "*23\r\n\$4\r\nXADD\r\n\$1\r\nS\r\n\$1\r\n*\r\n"
            for {set j 0} {$j<10} {incr j} {
                r write "\$1\r\n$j\r\n"
                write_big_bulk 500000000 "" yes ;#500mb
            }
            r flush
            catch {r read} err
            assert_match {*too large*} $err
            r xlen S
        } {0}
    }

    # Gradually add big hash fields using repeated HSET calls
    # This reproduces the overflow in the call to ziplistResize
    # Object will be converted to hashtable encoding
    start_server [list overrides [list save ""] tags {"large-memory"}] {
        r config set hash-max-ziplist-value 1000000000 ;#1gb
        test {hash with many big fields} {
            for {set j 0} {$j<10} {incr j} {
                r hset h $j $::str500
            }
            r object encoding h
        } {hashtable}
    }

    # Add over 4GB to a single hash field (one HSET command)
    # Object will be converted to hashtable encoding
    start_server [list overrides [list save ""] tags {"large-memory"}] {
        test {hash with one huge field} {
            catch {r config set hash-max-ziplist-value 10000000000} ;#10gb
            r config set proto-max-bulk-len 10000000000 ;#10gb
            r config set client-query-buffer-limit 10000000000 ;#10gb
            r write "*4\r\n\$4\r\nHSET\r\n\$2\r\nH1\r\n"
            r write "\$1\r\nA\r\n"
            write_big_bulk 5000000000 ;#5gb
            r object encoding H1
        } {hashtable}
    }
}
"""


def test_sort_adds_integer_field_to_list(r: ValkeyTestClient) -> None:
    """
    test {SORT adds integer field to list} {
        r set S1 asdf
        r set S2 123 ;# integer encoded
        assert_encoding "int" S2
        r sadd myset 1 2
        r mset D1 1 D2 2
        r sort myset by D* get S* store mylist
        r llen mylist
    } {2} {cluster:skip}
    """
    r.run("set", "S1", "asdf")
    r.run("set", "S2", 123)
    assert_encoding("int", "S2")
    r.run("sadd", "myset", 1, 2)
    r.run("mset", "D1", 1, "D2", 2)
    r.run("sort", "myset", "by", "D*", "get", "S*", "store", "mylist")
    assert r.run("llen", "mylist") == "2"


# --- stubs for unimplemented TCL helpers ---


def assert_encoding(*args):
    raise NotImplementedError("assert_encoding")
