# ruff: noqa: PLR2004, F841, ANN002, ANN201

import pytest

from tests.valkey_test_client import ValkeyTestClient

testmodule = "tests/modules/reply.so"

pytestmark = [pytest.mark.modules]


def test_unload_the_module_replywith(r: ValkeyTestClient) -> None:
    """
    test "Unload the module - replywith" {
        assert_equal {OK} [r module unload replywith]
    }
    """
    r.run("module", "load", testmodule)
    proto = 2
    while proto <= 3:
        if lsearch(denytags, "resp3") >= 0:
            if proto == 3:
                continue_()
        elif False:
            if proto == 2:
                continue_()
        r.run("hello", proto)
        test(
            f"RESP{proto:} RM_ReplyWithString: an string reply",
            '            # RedisString\n            set string [r rw.string "Redis"]\n            assert_equal "Redis" $string\n            # C string\n            set string [r rw.cstring]\n            assert_equal "A simple string" $string\n        ',
        )
        test(
            f"RESP{proto:} RM_ReplyWithBigNumber: an string reply",
            '            assert_equal "123456778901234567890" [r rw.bignumber "123456778901234567890"]\n        ',
        )
        test(f"RESP{proto:} RM_ReplyWithInt: an integer reply", "            assert_equal 42 [r rw.int 42]\n        ")
        test(
            f"RESP{proto:} RM_ReplyWithDouble: a float reply",
            "            assert_equal 3.141 [r rw.double 3.141]\n        ",
        )
        test(
            f"RESP{proto:} RM_ReplyWithDouble: inf",
            '            if {$proto == 2} {\n                assert_equal "inf" [r rw.double inf]\n                assert_equal "-inf" [r rw.double -inf]\n            } else {\n                # TCL convert inf to different results on different platforms, e.g. inf on mac\n                # and Inf on others, so use readraw to verify the protocol\n                r readraw 1\n                assert_equal ",inf" [r rw.double inf]\n                assert_equal ",-inf" [r rw.double -inf]\n                r readraw 0\n            }\n        ',
        )
        test(
            f"RESP{proto:} RM_ReplyWithDouble: NaN",
            '            if {$proto == 2} {\n                assert_equal "nan" [r rw.double 0 0]\n                assert_equal "nan" [r rw.double]\n            } else {\n                # TCL won\'t convert nan into a double, use readraw to verify the protocol\n                r readraw 1\n                assert_equal ",nan" [r rw.double 0 0]\n                assert_equal ",nan" [r rw.double]\n                r readraw 0\n            }\n        ',
        )
        ld = 0.00000000000000001
        test(
            f"RESP{proto:} RM_ReplyWithLongDouble: a float reply",
            '            if {$proto == 2} {\n                # here the response gets to TCL as a string\n                assert_equal $ld [r rw.longdouble $ld]\n            } else {\n                # TCL doesn\'t support long double and the test infra converts it to a\n                # normal double which causes precision loss. so we use readraw instead\n                r readraw 1\n                assert_equal ",$ld" [r rw.longdouble $ld]\n                r readraw 0\n            }\n        ',
        )
        test(
            f"RESP{proto:} RM_ReplyWithVerbatimString: a string reply",
            '            assert_equal "bla\\nbla\\nbla" [r rw.verbatim "bla\\nbla\\nbla"]\n        ',
        )
        test(
            f"RESP{proto:} RM_ReplyWithArray: an array reply",
            "            assert_equal {0 1 2 3 4} [r rw.array 5]\n        ",
        )
        test(
            f"RESP{proto:} RM_ReplyWithMap: an map reply",
            "            set res [r rw.map 3]\n            if {$proto == 2} {\n                assert_equal {0 0 1 1.5 2 3} $res\n            } else {\n                assert_equal [dict create 0 0.0 1 1.5 2 3.0] $res\n            }\n        ",
        )
        test(f"RESP{proto:} RM_ReplyWithSet: an set reply", "            assert_equal {0 1 2} [r rw.set 3]\n        ")
        test(
            f"RESP{proto:} RM_ReplyWithAttribute: an set reply",
            '            if {$proto == 2} {\n                catch {[r rw.attribute 3]} e\n                assert_match "Attributes aren\'t supported by RESP 2" $e\n            } else {\n                r readraw 1\n                set res [r rw.attribute 3]\n                assert_equal [r read] {:0}\n                assert_equal [r read] {,0}\n                assert_equal [r read] {:1}\n                assert_equal [r read] {,1.5}\n                assert_equal [r read] {:2}\n                assert_equal [r read] {,3}\n                assert_equal [r read] {+OK}\n                r readraw 0\n            }\n        ',
        )
        test(f"RESP{proto:} RM_ReplyWithBool: a boolean reply", "            assert_equal {0 1} [r rw.bool]\n        ")
        test(f"RESP{proto:} RM_ReplyWithNull: a NULL reply", "            assert_equal {} [r rw.null]\n        ")
        test(
            f"RESP{proto:} RM_ReplyWithError: an error reply",
            '            catch {r rw.error} e\n            assert_match "An error" $e\n        ',
        )
        test(
            f"RESP{proto:} RM_ReplyWithErrorFormat: error format reply",
            '            catch {r rw.error_format "An error: %s" foo} e\n            assert_match "An error: foo" $e  ;# Should not be used by a user, but compatible with RM_ReplyError\n\n            catch {r rw.error_format "-ERR An error: %s" foo2} e\n            assert_match "-ERR An error: foo2" $e  ;# Should not be used by a user, but compatible with RM_ReplyError (There are two hyphens, TCL removes the first one)\n\n            catch {r rw.error_format "-WRONGTYPE A type error: %s" foo3} e\n            assert_match "-WRONGTYPE A type error: foo3" $e  ;# Should not be used by a user, but compatible with RM_ReplyError (There are two hyphens, TCL removes the first one)\n\n            catch {r rw.error_format "ERR An error: %s" foo4} e\n            assert_match "ERR An error: foo4" $e\n\n            catch {r rw.error_format "WRONGTYPE A type error: %s" foo5} e\n            assert_match "WRONGTYPE A type error: foo5" $e\n        ',
        )
        r.run("hello", 2)
        proto += 1
    assert "OK" == r.run("module", "unload", "replywith")


# --- stubs for unimplemented TCL helpers ---


def continue_(*args):
    raise NotImplementedError("continue_")


def lsearch(*args):
    raise NotImplementedError("lsearch")


def test(*args):
    raise NotImplementedError("test")
