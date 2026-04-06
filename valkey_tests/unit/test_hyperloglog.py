# ruff: noqa: PLR2004, F841, RUF043

from fnmatch import fnmatch

import pytest

from tests.valkey_test_client import ValkeyTestClient

pytestmark = [pytest.mark.hll_large_memory]


@pytest.mark.xfail(reason="not implemented")
def test_cve_2025_32023_sparse_hll_xzero_overflow_triggers_crash(r: ValkeyTestClient) -> None:
    """
    test {CVE-2025-32023: Sparse HLL XZERO overflow triggers crash} {
        # Build a valid HLL header for sparse encoding
        set hll [binary format cccc 72 89 76 76] ; # "HYLL"
        append hll [binary format cccc 1 0 0 0] ; # encoding=sparse, 3 reserved
        append hll [binary format cccccccc 0 0 0 0 0 0 0 0] ; # cached cardinality

        # We need alternating XZERO and ZERO opcodes to build up a large enough
        # HyperLogLog value that will overflow the runlength.
        # 0x7f 0xff is the XZERO opcode that sets the index to 16384.
        # 0x3f is the ZERO opcode that sets the index to 256.
        # We repeat this pattern at least 33554432 times to overflow the runlength,
        # 50331648 is just 33554432 * 1.5, which is just a round number.
        append hll [string repeat [binary format ccc 0x7f 0xff 0x3f] 50331648]

        # We need an actual value at the end to trigger the out of bounds write
        append hll [binary format c 0x80]

        # Set the raw value into the key
        r set hll_overflow $hll
        r pfadd hll_merge_source hi

        # Test pfadd and pfmerge, these used to crash but now error
        assert_error {*INVALIDOBJ*} {r pfmerge fail_target hll_overflow hll_merge_source}
        assert_error {*INVALIDOBJ*} {r pfadd hll_overflow foo}
    }
    """
    # TODO: set hll binary format cccc 72 89 76 76
    # TODO: append hll binary format cccc 1 0 0 0
    # TODO: append hll binary format cccccccc 0 0 0 0 0 0 0 0
    # TODO: append hll string repeat [binary format ccc 0x7f 0xff 0x3f] 50331648
    # TODO: append hll binary format c 0x80
    # TODO: r set hll_overflow hll
    r.run("pfadd", "hll_merge_source", "hi")
    with pytest.raises(Exception, match=".*INVALIDOBJ.*"):
        r.run("pfmerge", "fail_target", "hll_overflow", "hll_merge_source")
    with pytest.raises(Exception, match=".*INVALIDOBJ.*"):
        r.run("pfadd", "hll_overflow", "foo")


pytestmark = [pytest.mark.hll]


def test_hyperloglog_self_test_passes(r: ValkeyTestClient) -> None:
    """
    test {HyperLogLog self test passes} {
        catch {r pfselftest} e
        set e
    } {OK} {needs:pfdebug}
    """
    try:
        e = r.run("pfselftest")
    except Exception as _catch_err:
        e = str(_catch_err)
    assert e == "OK"


def test_pfadd_without_arguments_creates_an_hll_value(r: ValkeyTestClient) -> None:
    """
    test {PFADD without arguments creates an HLL value} {
        r pfadd hll
        r exists hll
    } {1}
    """
    r.run("pfadd", "hll")
    assert r.run("exists", "hll") == "1"


def test_approximated_cardinality_after_creation_is_zero(r: ValkeyTestClient) -> None:
    """
    test {Approximated cardinality after creation is zero} {
        r pfcount hll
    } {0}
    """
    assert r.run("pfcount", "hll") == "0"


def test_pfadd_returns_1_when_at_least_1_reg_was_modified(r: ValkeyTestClient) -> None:
    """
    test {PFADD returns 1 when at least 1 reg was modified} {
        r pfadd hll a b c
    } {1}
    """
    assert r.run("pfadd", "hll", "a", "b", "c") == "1"


def test_pfadd_returns_0_when_no_reg_was_modified(r: ValkeyTestClient) -> None:
    """
    test {PFADD returns 0 when no reg was modified} {
        r pfadd hll a b c
    } {0}
    """
    assert r.run("pfadd", "hll", "a", "b", "c") == "0"


def test_pfadd_works_with_empty_string_regression(r: ValkeyTestClient) -> None:
    """
    test {PFADD works with empty string (regression)} {
        r pfadd hll ""
    }
    """
    r.run("pfadd", "hll", "")


@pytest.mark.xfail(reason="not implemented")
def test_pfcount_returns_approximated_cardinality_of_set(r: ValkeyTestClient) -> None:
    """
    test {PFCOUNT returns approximated cardinality of set} {
        r del hll
        set res {}
        r pfadd hll 1 2 3 4 5
        lappend res [r pfcount hll]
        # Call it again to test cached value invalidation.
        r pfadd hll 6 7 8 8 9 10
        lappend res [r pfcount hll]
        set res
    } {5 10}
    """
    r.run("del", "hll")
    res = ""
    r.run("pfadd", "hll", 1, 2, 3, 4, 5)
    # TODO: lappend res r pfcount hll
    r.run("pfadd", "hll", 6, 7, 8, 8, 9, 10)
    # TODO: lappend res r pfcount hll
    assert res == "5 10"


@pytest.mark.xfail(reason="not implemented")
def test_hyperloglogs_are_promote_from_sparse_to_dense(r: ValkeyTestClient) -> None:
    """
    test {HyperLogLogs are promote from sparse to dense} {
        r del hll
        r config set hll-sparse-max-bytes 3000
        set n 0
        while {$n < 100000} {
            set elements {}
            for {set j 0} {$j < 100} {incr j} {lappend elements [expr rand()]}
            incr n 100
            r pfadd hll {*}$elements
            set card [r pfcount hll]
            set err [expr {abs($card-$n)}]
            assert {$err < (double($card)/100)*5}
            if {$n < 1000} {
                assert {[r pfdebug encoding hll] eq {sparse}}
            } elseif {$n > 10000} {
                assert {[r pfdebug encoding hll] eq {dense}}
            }
        }
    } {} {needs:pfdebug}
    """
    r.run("del", "hll")
    r.run("config", "set", "hll-sparse-max-bytes", 3000)
    n = 0
    # TODO: while {$n < 100000} {
    #       set elements {}
    #       for {set j 0} {$j < 100} {incr j} {lappend elements [expr rand()]}
    #       incr n 100
    #       r pfadd hll {*}$elements
    #       set card [r pfcount hll]
    #       set err [expr {abs($card-$n)}]
    #       assert {$err < (double($card)/100)*5}
    #       if {$n < 1000} {
    #           assert {[r pfdebug encoding hll] eq {sparse}}
    #       } elseif {$n > 10000} {
    #           assert {[r pfdebug encoding hll] eq {dense}}
    #       }
    #   }


@pytest.mark.xfail(reason="not implemented")
def test_change_hll_sparse_max_bytes(r: ValkeyTestClient) -> None:
    """
    test {Change hll-sparse-max-bytes} {
        r config set hll-sparse-max-bytes 3000
        r del hll
        r pfadd hll a b c d e d g h i j k
        assert {[r pfdebug encoding hll] eq {sparse}}
        r config set hll-sparse-max-bytes 30
        r pfadd hll new_element
        assert {[r pfdebug encoding hll] eq {dense}}
    } {} {needs:pfdebug}
    """
    r.run("config", "set", "hll-sparse-max-bytes", 3000)
    r.run("del", "hll")
    r.run("pfadd", "hll", "a", "b", "c", "d", "e", "d", "g", "h", "i", "j", "k")
    # TODO: assert {[r pfdebug encoding hll] eq {sparse}}
    r.run("config", "set", "hll-sparse-max-bytes", 30)
    r.run("pfadd", "hll", "new_element")
    # TODO: assert {[r pfdebug encoding hll] eq {dense}}


@pytest.mark.xfail(reason="not implemented")
def test_hyperloglog_promote_to_dense_well_in_different_hll_sparse_max_bytes(r: ValkeyTestClient) -> None:
    """
    test {Hyperloglog promote to dense well in different hll-sparse-max-bytes} {
        set max(0) 100
        set max(1) 500
        set max(2) 3000
        for {set i 0} {$i < [array size max]} {incr i} {
            r config set hll-sparse-max-bytes $max($i)
            r del hll
            r pfadd hll
            set len [r strlen hll]
            while {$len <= $max($i)} {
                assert {[r pfdebug encoding hll] eq {sparse}}
                set elements {}
                for {set j 0} {$j < 10} {incr j} { lappend elements [expr rand()]}
                r pfadd hll {*}$elements
                set len [r strlen hll]
            }
            assert {[r pfdebug encoding hll] eq {dense}}
        }
    } {} {needs:pfdebug}
    """
    # TODO: set max(0) 100
    # TODO: set max(1) 500
    # TODO: set max(2) 3000
    # TODO: for {set i 0} {$i < [array size max]} {incr i} {
    #       r config set hll-sparse-max-bytes $max($i)
    #       r del hll
    #       r pfadd hll
    #       set len [r strlen hll]
    #       while {$len <= $max($i)} {
    #           assert {[r pfdebug encoding hll] eq {sparse}}
    #           set elements {}
    #           for {set j 0} {$j < 10} {incr j} { lappend elements [expr rand()]}
    #           r pfadd hll {*}$elements
    #           set len [r strlen hll]
    #       }
    #       assert {[r pfdebug encoding hll] eq {dense}}
    #   }


@pytest.mark.xfail(reason="not implemented")
def test_hyperloglog_sparse_encoding_stress_test(r: ValkeyTestClient) -> None:
    """
    test {HyperLogLog sparse encoding stress test} {
        for {set x 0} {$x < 1000} {incr x} {
            r del hll1
            r del hll2
            set numele [randomInt 100]
            set elements {}
            for {set j 0} {$j < $numele} {incr j} {
                lappend elements [expr rand()]
            }
            # Force dense representation of hll2
            r pfadd hll2
            r pfdebug todense hll2
            r pfadd hll1 {*}$elements
            r pfadd hll2 {*}$elements
            assert {[r pfdebug encoding hll1] eq {sparse}}
            assert {[r pfdebug encoding hll2] eq {dense}}
            # Cardinality estimated should match exactly.
            assert {[r pfcount hll1] eq [r pfcount hll2]}
        }
    } {} {needs:pfdebug}
    """
    # TODO: for {set x 0} {$x < 1000} {incr x} {
    #       r del hll1
    #       r del hll2
    #       set numele [randomInt 100]
    #       set elements {}
    #       for {set j 0} {$j < $numele} {incr j} {
    #           lappend elements [expr rand()]
    #       }
    #       # Force dense representation of hll2
    #       r pfadd hll2
    #       r pfdebug todense hll2
    #       r pfadd hll1 {*}$elements
    #       r pfadd hll2 {*}$elements
    #       assert {[r pfdebug encoding hll1] eq {sparse}}
    #       assert {[r pfdebug encoding hll2] eq {dense}}
    #       # Cardinality estimated should match exactly.
    #       assert {[r pfcount hll1] eq [r pfcount hll2]}
    #   }


def test_corrupted_sparse_hyperloglogs_are_detected_additional_at_tail(r: ValkeyTestClient) -> None:
    """
    test {Corrupted sparse HyperLogLogs are detected: Additional at tail} {
        r del hll
        r pfadd hll a b c
        r append hll "hello"
        set e {}
        catch {r pfcount hll} e
        set e
    } {*INVALIDOBJ*}
    """
    r.run("del", "hll")
    r.run("pfadd", "hll", "a", "b", "c")
    r.run("append", "hll", "hello")
    e = ""
    try:
        e = r.run("pfcount", "hll")
    except Exception as _catch_err:
        e = str(_catch_err)
    assert e == "*INVALIDOBJ*"


def test_corrupted_sparse_hyperloglogs_are_detected_broken_magic(r: ValkeyTestClient) -> None:
    """
    test {Corrupted sparse HyperLogLogs are detected: Broken magic} {
        r del hll
        r pfadd hll a b c
        r setrange hll 0 "0123"
        set e {}
        catch {r pfcount hll} e
        set e
    } {*WRONGTYPE*}
    """
    r.run("del", "hll")
    r.run("pfadd", "hll", "a", "b", "c")
    r.run("setrange", "hll", 0, "0123")
    e = ""
    try:
        e = r.run("pfcount", "hll")
    except Exception as _catch_err:
        e = str(_catch_err)
    assert e == "*WRONGTYPE*"


def test_corrupted_sparse_hyperloglogs_are_detected_invalid_encoding(r: ValkeyTestClient) -> None:
    """
    test {Corrupted sparse HyperLogLogs are detected: Invalid encoding} {
        r del hll
        r pfadd hll a b c
        r setrange hll 4 "x"
        set e {}
        catch {r pfcount hll} e
        set e
    } {*WRONGTYPE*}
    """
    r.run("del", "hll")
    r.run("pfadd", "hll", "a", "b", "c")
    r.run("setrange", "hll", 4, "x")
    e = ""
    try:
        e = r.run("pfcount", "hll")
    except Exception as _catch_err:
        e = str(_catch_err)
    assert e == "*WRONGTYPE*"


@pytest.mark.xfail(reason="not implemented")
def test_corrupted_dense_hyperloglogs_are_detected_wrong_length(r: ValkeyTestClient) -> None:
    """
    test {Corrupted dense HyperLogLogs are detected: Wrong length} {
        r del hll
        r pfadd hll a b c
        r setrange hll 4 "\x00"
        set e {}
        catch {r pfcount hll} e
        set e
    } {*WRONGTYPE*}
    """
    r.run("del", "hll")
    r.run("pfadd", "hll", "a", "b", "c")
    # TODO: r setrange hll 4 "\x00"
    e = ""
    try:
        e = r.run("pfcount", "hll")
    except Exception as _catch_err:
        e = str(_catch_err)
    assert e == "*WRONGTYPE*"


@pytest.mark.xfail(reason="not implemented")
def test_fuzzing_dense_or_sparse_encoding_server_should_always_detect_errors(r: ValkeyTestClient) -> None:
    """
    test {Fuzzing dense/sparse encoding: Server should always detect errors} {
        for {set j 0} {$j < 1000} {incr j} {
            r del hll
            set items {}
            set numitems [randomInt 3000]
            for {set i 0} {$i < $numitems} {incr i} {
                lappend items [expr {rand()}]
            }
            r pfadd hll {*}$items

            # Corrupt it in some random way.
            for {set i 0} {$i < 5} {incr i} {
                set len [r strlen hll]
                set pos [randomInt $len]
                set byte [randstring 1 1 binary]
                r setrange hll $pos $byte
                # Don't modify more bytes 50% of times
                if {rand() < 0.5} break
            }

            # Use the hyperloglog to check if it crashes
            # the server in some way.
            catch {
                r pfcount hll
            }
        }
    }
    """
    # TODO: for {set j 0} {$j < 1000} {incr j} {
    #       r del hll
    #       set items {}
    #       set numitems [randomInt 3000]
    #       for {set i 0} {$i < $numitems} {incr i} {
    #           lappend items [expr {rand()}]
    #       }
    #       r pfadd hll {*}$items
    #
    #       # Corrupt it in some random way.
    #       for {set i 0} {$i < 5} {incr i} {
    #           set len [r strlen hll]
    #           set pos [randomInt $len]
    #           set byte [randstring 1 1 binary]
    #           r setrange hll $pos $byte
    #           # Don't modify more bytes 50% of times
    #           if {rand() < 0.5} break
    #       }
    #
    #       # Use the hyperloglog to check if it crashes
    #       # the server in some way.
    #       catch {
    #           r pfcount hll
    #       }
    #   }


def test_pfadd_pfcount_pfmerge_type_checking_works(r: ValkeyTestClient) -> None:
    """
    test {PFADD, PFCOUNT, PFMERGE type checking works} {
        r set foo{t} bar
        catch {r pfadd foo{t} 1} e
        assert_match {*WRONGTYPE*} $e
        catch {r pfcount foo{t}} e
        assert_match {*WRONGTYPE*} $e
        catch {r pfmerge bar{t} foo{t}} e
        assert_match {*WRONGTYPE*} $e
        catch {r pfmerge foo{t} bar{t}} e
        assert_match {*WRONGTYPE*} $e
    }
    """
    r.run("set", "foo{t}", "bar")
    try:
        e = r.run("pfadd", "foo{t}", 1)
    except Exception as _catch_err:
        e = str(_catch_err)
    assert fnmatch(str(e), "*WRONGTYPE*")
    try:
        e = r.run("pfcount", "foo{t}")
    except Exception as _catch_err:
        e = str(_catch_err)
    assert fnmatch(str(e), "*WRONGTYPE*")
    try:
        e = r.run("pfmerge", "bar{t}", "foo{t}")
    except Exception as _catch_err:
        e = str(_catch_err)
    assert fnmatch(str(e), "*WRONGTYPE*")
    try:
        e = r.run("pfmerge", "foo{t}", "bar{t}")
    except Exception as _catch_err:
        e = str(_catch_err)
    assert fnmatch(str(e), "*WRONGTYPE*")


def test_pfmerge_results_on_the_cardinality_of_union_of_sets(r: ValkeyTestClient) -> None:
    """
    test {PFMERGE results on the cardinality of union of sets} {
        r del hll{t} hll1{t} hll2{t} hll3{t}
        r pfadd hll1{t} a b c
        r pfadd hll2{t} b c d
        r pfadd hll3{t} c d e
        r pfmerge hll{t} hll1{t} hll2{t} hll3{t}
        r pfcount hll{t}
    } {5}
    """
    r.run("del", "hll{t}", "hll1{t}", "hll2{t}", "hll3{t}")
    r.run("pfadd", "hll1{t}", "a", "b", "c")
    r.run("pfadd", "hll2{t}", "b", "c", "d")
    r.run("pfadd", "hll3{t}", "c", "d", "e")
    r.run("pfmerge", "hll{t}", "hll1{t}", "hll2{t}", "hll3{t}")
    assert r.run("pfcount", "hll{t}") == "5"


def test_pfmerge_on_missing_source_keys_will_create_an_empty_destkey(r: ValkeyTestClient) -> None:
    """
    test {PFMERGE on missing source keys will create an empty destkey} {
        r del sourcekey{t} sourcekey2{t} destkey{t} destkey2{t}

        assert_equal {OK} [r pfmerge destkey{t} sourcekey{t}]
        assert_equal 1 [r exists destkey{t}]
        assert_equal 0 [r pfcount destkey{t}]

        assert_equal {OK} [r pfmerge destkey2{t} sourcekey{t} sourcekey2{t}]
        assert_equal 1 [r exists destkey2{t}]
        assert_equal 0 [r pfcount destkey{t}]
    }
    """
    r.run("del", "sourcekey{t}", "sourcekey2{t}", "destkey{t}", "destkey2{t}")
    assert "OK" == r.run("pfmerge", "destkey{t}", "sourcekey{t}")
    assert 1 == r.run("exists", "destkey{t}")
    assert 0 == r.run("pfcount", "destkey{t}")
    assert "OK" == r.run("pfmerge", "destkey2{t}", "sourcekey{t}", "sourcekey2{t}")
    assert 1 == r.run("exists", "destkey2{t}")
    assert 0 == r.run("pfcount", "destkey{t}")


def test_pfmerge_with_one_empty_input_key_create_an_empty_destkey(r: ValkeyTestClient) -> None:
    """
    test {PFMERGE with one empty input key, create an empty destkey} {
        r del destkey
        assert_equal {OK} [r pfmerge destkey]
        assert_equal 1 [r exists destkey]
        assert_equal 0 [r pfcount destkey]
    }
    """
    r.run("del", "destkey")
    assert "OK" == r.run("pfmerge", "destkey")
    assert 1 == r.run("exists", "destkey")
    assert 0 == r.run("pfcount", "destkey")


def test_pfmerge_with_one_non_empty_input_key_dest_key_is_actually_one_of_the_source_keys(r: ValkeyTestClient) -> None:
    """
    test {PFMERGE with one non-empty input key, dest key is actually one of the source keys} {
        r del destkey
        assert_equal 1 [r pfadd destkey a b c]
        assert_equal {OK} [r pfmerge destkey]
        assert_equal 1 [r exists destkey]
        assert_equal 3 [r pfcount destkey]
    }
    """
    r.run("del", "destkey")
    assert 1 == r.run("pfadd", "destkey", "a", "b", "c")
    assert "OK" == r.run("pfmerge", "destkey")
    assert 1 == r.run("exists", "destkey")
    assert 3 == r.run("pfcount", "destkey")


@pytest.mark.xfail(reason="not implemented")
def test_pfmerge_results_with_simd(r: ValkeyTestClient) -> None:
    """
    test {PFMERGE results with simd} {
        r del hllscalar{t} hllsimd{t} hll1{t} hll2{t} hll3{t}
        for {set x 1} {$x < 2000} {incr x} {
            r pfadd hll1{t} [expr rand()]
        }
        for {set x 1} {$x < 4000} {incr x} {
            r pfadd hll2{t} [expr rand()]
        }
        for {set x 1} {$x < 8000} {incr x} {
            r pfadd hll3{t} [expr rand()]
        }
        assert {[r pfcount hll1{t}] > 0}
        assert {[r pfcount hll2{t}] > 0}
        assert {[r pfcount hll3{t}] > 0}

        r pfdebug simd off
        set scalar [r pfcount hll1{t} hll2{t} hll3{t}]
        r pfdebug simd on
        set simd [r pfcount hll1{t} hll2{t} hll3{t}]
        assert {$scalar > 0}
        assert {$simd > 0}
        assert_equal $scalar $simd

        r pfdebug simd off
        r pfmerge hllscalar{t} hll1{t} hll2{t} hll3{t}
        r pfdebug simd on
        r pfmerge hllsimd{t} hll1{t} hll2{t} hll3{t}

        set scalar [r pfcount hllscalar{t}]
        set simd [r pfcount hllsimd{t}]
        assert {$scalar > 0}
        assert {$simd > 0}
        assert_equal $scalar $simd

        set scalar [r get hllscalar{t}]
        set simd [r get hllsimd{t}]
        assert_equal $scalar $simd
    } {} {needs:pfdebug}
    """
    r.run("del", "hllscalar{t}", "hllsimd{t}", "hll1{t}", "hll2{t}", "hll3{t}")
    # TODO: for {set x 1} {$x < 2000} {incr x} {
    #       r pfadd hll1{t} [expr rand()]
    #   }
    # TODO: for {set x 1} {$x < 4000} {incr x} {
    #       r pfadd hll2{t} [expr rand()]
    #   }
    # TODO: for {set x 1} {$x < 8000} {incr x} {
    #       r pfadd hll3{t} [expr rand()]
    #   }
    assert r.run("pfcount", "hll1{t}") > 0
    assert r.run("pfcount", "hll2{t}") > 0
    assert r.run("pfcount", "hll3{t}") > 0
    r.run("pfdebug", "simd", "off")
    scalar = r.run("pfcount", "hll1{t}", "hll2{t}", "hll3{t}")
    r.run("pfdebug", "simd", "on")
    simd = r.run("pfcount", "hll1{t}", "hll2{t}", "hll3{t}")
    assert scalar > 0
    assert simd > 0
    assert scalar == simd
    r.run("pfdebug", "simd", "off")
    r.run("pfmerge", "hllscalar{t}", "hll1{t}", "hll2{t}", "hll3{t}")
    r.run("pfdebug", "simd", "on")
    r.run("pfmerge", "hllsimd{t}", "hll1{t}", "hll2{t}", "hll3{t}")
    scalar = r.run("pfcount", "hllscalar{t}")
    simd = r.run("pfcount", "hllsimd{t}")
    assert scalar > 0
    assert simd > 0
    assert scalar == simd
    scalar = r.run("get", "hllscalar{t}")
    simd = r.run("get", "hllsimd{t}")
    assert scalar == simd


@pytest.mark.xfail(reason="not implemented")
def test_pfcount_multiple_keys_merge_returns_cardinality_of_union_1(r: ValkeyTestClient) -> None:
    """
    test {PFCOUNT multiple-keys merge returns cardinality of union #1} {
        r del hll1{t} hll2{t} hll3{t}
        for {set x 1} {$x < 10000} {incr x} {
            r pfadd hll1{t} "foo-$x"
            r pfadd hll2{t} "bar-$x"
            r pfadd hll3{t} "zap-$x"

            set card [r pfcount hll1{t} hll2{t} hll3{t}]
            set realcard [expr {$x*3}]
            set err [expr {abs($card-$realcard)}]
            assert {$err < (double($card)/100)*5}
        }
    }
    """
    r.run("del", "hll1{t}", "hll2{t}", "hll3{t}")
    # TODO: for {set x 1} {$x < 10000} {incr x} {
    #       r pfadd hll1{t} "foo-$x"
    #       r pfadd hll2{t} "bar-$x"
    #       r pfadd hll3{t} "zap-$x"
    #
    #       set card [r pfcount hll1{t} hll2{t} hll3{t}]
    #       set realcard [expr {$x*3}]
    #       set err [expr {abs($card-$realcard)}]
    #       assert {$err < (double($card)/100)*5}
    #   }


@pytest.mark.xfail(reason="not implemented")
def test_pfcount_multiple_keys_merge_returns_cardinality_of_union_2(r: ValkeyTestClient) -> None:
    """
    test {PFCOUNT multiple-keys merge returns cardinality of union #2} {
        r del hll1{t} hll2{t} hll3{t}
        set elements {}
        for {set x 1} {$x < 10000} {incr x} {
            for {set j 1} {$j <= 3} {incr j} {
                set rint [randomInt 20000]
                r pfadd hll$j{t} $rint
                lappend elements $rint
            }
        }
        set realcard [llength [lsort -unique $elements]]
        set card [r pfcount hll1{t} hll2{t} hll3{t}]
        set err [expr {abs($card-$realcard)}]
        assert {$err < (double($card)/100)*5}
    }
    """
    r.run("del", "hll1{t}", "hll2{t}", "hll3{t}")
    elements = ""
    # TODO: for {set x 1} {$x < 10000} {incr x} {
    #       for {set j 1} {$j <= 3} {incr j} {
    #           set rint [randomInt 20000]
    #           r pfadd hll$j{t} $rint
    #           lappend elements $rint
    #       }
    #   }
    # TODO: set realcard llength [lsort -unique $elements]
    card = r.run("pfcount", "hll1{t}", "hll2{t}", "hll3{t}")
    # TODO: set err expr {abs($card-$realcard)}
    # TODO: assert {$err < (double($card)/100)*5}


def test_pfdebug_getreg_returns_the_hyperloglog_raw_registers(r: ValkeyTestClient) -> None:
    """
    test {PFDEBUG GETREG returns the HyperLogLog raw registers} {
        r del hll
        r pfadd hll 1 2 3
        llength [r pfdebug getreg hll]
    } {16384} {needs:pfdebug}
    """
    r.run("del", "hll")
    r.run("pfadd", "hll", 1, 2, 3)
    assert len(r.run("pfdebug", "getreg", "hll")) == "16384"


@pytest.mark.xfail(reason="not implemented")
def test_pfadd_or_pfcount_cache_invalidation_works(r: ValkeyTestClient) -> None:
    """
    test {PFADD / PFCOUNT cache invalidation works} {
        r del hll
        r pfadd hll a b c
        r pfcount hll
        assert {[r getrange hll 15 15] eq "\x00"}
        r pfadd hll a b c
        assert {[r getrange hll 15 15] eq "\x00"}
        r pfadd hll 1 2 3
        assert {[r getrange hll 15 15] eq "\x80"}
    }
    """
    r.run("del", "hll")
    r.run("pfadd", "hll", "a", "b", "c")
    r.run("pfcount", "hll")
    # TODO: assert {[r getrange hll 15 15] eq "\x00"}
    r.run("pfadd", "hll", "a", "b", "c")
    # TODO: assert {[r getrange hll 15 15] eq "\x00"}
    r.run("pfadd", "hll", 1, 2, 3)
    # TODO: assert {[r getrange hll 15 15] eq "\x80"}
