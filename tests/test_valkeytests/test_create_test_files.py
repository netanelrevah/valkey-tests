from __future__ import annotations

import io
import textwrap

from valkey_tests_generator.create_test_files import TCLTestFileGenerator


def generate(tcl: str) -> str:
    tcl = textwrap.dedent(tcl).strip()
    output = io.StringIO()
    TCLTestFileGenerator(output=output).generate(io.StringIO(tcl))
    return output.getvalue()


def test_generate_file__header():
    output = generate("""
        start_server {tags {"string"}} {
        }
    """)
    assert "import pytest" in output
    assert "from tests.valkey_test_client import ValkeyTestClient" in output


def test_generate_file__pytestmark():
    output = generate("""
        start_server {tags {"string"}} {
        }
    """)
    assert "pytestmark = [pytest.mark.string]" in output


def test_generate_file__simple_test():
    output = generate("""
        start_server {tags {}} {
            test {SET and GET an item} {
                r set x foobar
                r get x
            } {foobar}
        }
    """)
    assert "def test_set_and_get_an_item(r: ValkeyTestClient) -> None:" in output
    assert "SET and GET an item" in output
    assert "@pytest.mark.xfail" not in output
    assert "r.run('set', 'x', 'foobar')" in output
    assert "assert r.run('get', 'x') == 'foobar'" in output


def test_generate_file__body_translated_no_xfail():
    output = generate("""
        start_server {tags {}} {
            test {ping test} {
                r ping
            } {PONG}
        }
    """)
    assert "@pytest.mark.xfail" not in output
    assert "assert r.run('ping') == 'PONG'" in output


def test_generate_file__untranslatable_body_gets_xfail():
    output = generate("""
        start_server {tags {}} {
            test {complex test} {
                some_unknown_command arg
            } {result}
        }
    """)
    assert "@pytest.mark.xfail(reason='not implemented')" in output
    assert "# TODO:" in output
    assert "assert False" in output


def test_generate_file__test_prefix():
    output = generate("""
        start_server {tags {}} {
            test {My Test Name} {
                r ping
            } {PONG}
        }
    """)
    assert "def test_my_test_name(" in output


def test_generate_file__foreach_parametrize():
    output = generate("""
        start_server {tags {}} {
            foreach cmd {get set del} {
                test {command $cmd works} {
                    r $cmd foo
                } {}
            }
        }
    """)
    assert "@pytest.mark.parametrize" in output
    assert '"cmd"' in output


def test_generate_file__foreach_var_in_signature_and_body():
    output = generate("""
        start_server {tags {}} {
            foreach cmd {get set} {
                test {run $cmd} {
                    set result [r $cmd foo]
                } {}
            }
        }
    """)
    assert "def test_run_cmd(r: ValkeyTestClient, cmd) -> None:" in output
    assert "@pytest.mark.xfail" not in output
    assert "result = r.run(cmd, 'foo')" in output


def test_generate_file__unknown_bracket_call_generates_stub():
    output = generate("""
        start_server {tags {}} {
            foreach cmd {EX PX} {
                test {ttl $cmd} {
                    set ttl_cmd [get_ttl_command $cmd]
                    r set key val
                } {}
            }
        }
    """)
    assert "@pytest.mark.xfail" not in output
    assert "ttl_cmd = get_ttl_command(cmd)" in output
    assert "def get_ttl_command(*args):" in output
    assert "raise NotImplementedError('get_ttl_command')" in output


def test_generate_file__if_with_tests():
    output = generate("""
        start_server {tags {}} {
            if {1} {
                test {conditional test} {
                    r ping
                } {PONG}
            }
        }
    """)
    assert "def test_conditional_test(" in output
    assert "@pytest.mark.skipif" in output


def test_generate_file__non_test_command_becomes_comment():
    output = generate("""
        start_server {tags {}} {
            proc helper {} {
                r flushall
            }
        }
    """)
    assert '"""' in output
    assert "proc helper" in output


def test_generate_file__multiple_tests():
    output = generate("""
        start_server {tags {}} {
            test {First test} {
                r set a 1
            } {OK}
            test {Second test} {
                r get a
            } {1}
        }
    """)
    assert "def test_first_test(" in output
    assert "def test_second_test(" in output


def test_generate_file__docstring_contains_tcl_command():
    output = generate("""
        start_server {tags {}} {
            test {SET and GET an item} {
                r set x foobar
                r get x
            } {foobar}
        }
    """)
    assert "test {SET and GET an item}" in output


def test_generate_file__tag_with_spaces():
    output = generate("""
        start_server {tags {"protocol network"}} {
            test {basic test} {
                r ping
            } {PONG}
        }
    """)
    assert "def test_basic_test(" in output
    assert "pytest.mark.protocol_network" in output


def test_generate_file__tag_with_colon():
    output = generate("""
        start_server {tags {"auth external:skip"}} {
            test {basic test} {
                r ping
            } {PONG}
        }
    """)
    assert "pytest.mark.auth_external_skip" in output


def test_generate_file__lindex_in_assert_equal():
    output = generate("""
        start_server {tags {}} {
            test {lindex test} {
                set reply [r lrange mylist 0 -1]
                assert_equal [lindex $reply 0] {foo}
            }
        }
    """)
    assert "@pytest.mark.xfail" not in output
    assert "reply = r.run('lrange', 'mylist', 0, -1)" in output
    assert "assert reply[0] == 'foo'" in output


def test_generate_file__llength_in_assert_equal():
    output = generate("""
        start_server {tags {}} {
            test {llength test} {
                set reply [r lrange mylist 0 -1]
                assert_equal [llength $reply] 3
            }
        }
    """)
    assert "@pytest.mark.xfail" not in output
    assert "assert len(reply) == 3" in output


def test_generate_file__dict_get_in_assert_equal():
    output = generate("""
        start_server {tags {}} {
            test {dict get test} {
                set info [r xinfo groups mystream]
                assert_equal [dict get $info lag] 0
            }
        }
    """)
    assert "@pytest.mark.xfail" not in output
    assert "assert info['lag'] == 0" in output


def test_generate_file__string_length_in_assert_equal():
    output = generate("""
        start_server {tags {}} {
            test {string length test} {
                set data [r get mykey]
                assert_equal [string length $data] 5
            }
        }
    """)
    assert "@pytest.mark.xfail" not in output
    assert "assert len(data) == 5" in output


def test_generate_file__assert_error():
    output = generate("""
        start_server {tags {}} {
            test {error test} {
                assert_error "*ERR*" {r set}
            }
        }
    """)
    assert "@pytest.mark.xfail" not in output
    assert "with pytest.raises(Exception, match=" in output
    assert "r.run('set')" in output


def test_generate_file__multiple_start_server_blocks():
    output = generate("""
        start_server {tags {"first"}} {
            test {test in first block} {
                r ping
            } {PONG}
        }
        start_server {tags {"second"}} {
            test {test in second block} {
                r ping
            } {PONG}
        }
    """)
    assert "def test_test_in_first_block(" in output
    assert "def test_test_in_second_block(" in output


def test_generate_file__if_with_variable_condition_becomes_comment():
    output = generate("""
        start_server {tags {}} {
            if {$::tls} {
                test {tls only test} {
                    r ping
                } {PONG}
            }
        }
    """)
    assert '"""' in output
    assert "if" in output


_IF_IN_BODY_TCL = """
    start_server {tags {}} {
        test {if test} {
            set x [r get key]
            if {$x == 1} {
                r set key 2
            }
        }
    }
"""

_IF_IN_BODY_EXPECTED = """
    x = r.run('get', 'key')
    if x == 1:
        r.run('set', 'key', 2)
"""

_IF_ELSE_IN_BODY_TCL = """
    start_server {tags {}} {
        test {if else test} {
            set x [r get key]
            if {$x == 1} {
                r set key 2
            } else {
                r set key 3
            }
        }
    }
"""

_IF_ELSE_IN_BODY_EXPECTED = """
    if x == 1:
        r.run('set', 'key', 2)
    else:
        r.run('set', 'key', 3)
"""

_IF_ELSEIF_IN_BODY_TCL = """
    start_server {tags {}} {
        test {if elseif test} {
            set x [r get key]
            if {$x == 1} {
                r set key 2
            } elseif {$x == 2} {
                r set key 3
            }
        }
    }
"""

_IF_ELSEIF_IN_BODY_EXPECTED = """
    if x == 1:
        r.run('set', 'key', 2)
    elif x == 2:
        r.run('set', 'key', 3)
"""

_IF_UNTRANSLATABLE_TCL = """
    start_server {tags {}} {
        test {if ne test} {
            set x [r get key]
            if {$x ne {hello}} {
                r set key 2
            }
        }
    }
"""


def test_generate_file__if_in_body():
    assert _IF_IN_BODY_EXPECTED in generate(_IF_IN_BODY_TCL)


def test_generate_file__if_else_in_body():
    assert _IF_ELSE_IN_BODY_EXPECTED in generate(_IF_ELSE_IN_BODY_TCL)


def test_generate_file__if_elseif_in_body():
    assert _IF_ELSEIF_IN_BODY_EXPECTED in generate(_IF_ELSEIF_IN_BODY_TCL)


_IF_NE_IN_BODY_EXPECTED = """
    x = r.run('get', 'key')
    if x != 'hello':
        r.run('set', 'key', 2)
"""


def test_generate_file__if_ne_condition_translates():
    output = generate(_IF_UNTRANSLATABLE_TCL)
    assert "@pytest.mark.xfail" not in output
    assert _IF_NE_IN_BODY_EXPECTED in output


_CATCH_WITH_VAR_TCL = """
    start_server {tags {}} {
        test {catch test} {
            catch {r set} ex
            set ex
        } {*wrong*}
    }
"""

_CATCH_WITH_VAR_EXPECTED = """
    try:
        ex = r.run('set')
    except Exception as _catch_err:
        ex = str(_catch_err)
    assert ex == '*wrong*'
"""

_CATCH_WITHOUT_VAR_TCL = """
    start_server {tags {}} {
        test {catch no var test} {
            catch {r ping}
            r set x 1
        }
    }
"""

_CATCH_WITHOUT_VAR_EXPECTED = """
    try:
        r.run('ping')
    except Exception:
        pass
    r.run('set', 'x', 1)
"""


_ASSERT_BRACES_TCL = """
    start_server {tags {}} {
        test {assert braces} {
            set ttl [r ttl foo]
            assert {$ttl <= 10}
        }
    }
"""

_ASSERT_BRACES_EXPECTED = """
    ttl = r.run('ttl', 'foo')
    assert ttl <= 10
"""

_EMPTY_EXPECTED_LAST_ASSERT_TCL = """
    start_server {tags {}} {
        test {empty expected with assert last} {
            r SET foo bar
            assert_equal [r TTL foo] -1
        } {}
    }
"""

_EMPTY_EXPECTED_LAST_ASSERT_EXPECTED = """
    r.run('SET', 'foo', 'bar')
    assert r.run('TTL', 'foo') == -1
"""


_ASSERT_EQ_TCL = """
    start_server {tags {}} {
        test {assert eq test} {
            set name [r get user]
            assert {$name eq {alice}}
        }
    }
"""

_ASSERT_EQ_EXPECTED = """
    name = r.run('get', 'user')
    assert name == 'alice'
"""


def test_generate_file__assert_braces():
    output = generate(_ASSERT_BRACES_TCL)
    assert "@pytest.mark.xfail" not in output
    assert _ASSERT_BRACES_EXPECTED in output


def test_generate_file__assert_eq_operator():
    output = generate(_ASSERT_EQ_TCL)
    assert "@pytest.mark.xfail" not in output
    assert _ASSERT_EQ_EXPECTED in output


def test_generate_file__empty_expected_with_last_assert():
    output = generate(_EMPTY_EXPECTED_LAST_ASSERT_TCL)
    assert "@pytest.mark.xfail" not in output
    assert _EMPTY_EXPECTED_LAST_ASSERT_EXPECTED in output


def test_generate_file__catch_with_var():
    output = generate(_CATCH_WITH_VAR_TCL)
    assert "@pytest.mark.xfail" not in output
    assert _CATCH_WITH_VAR_EXPECTED in output


def test_generate_file__catch_without_var():
    output = generate(_CATCH_WITHOUT_VAR_TCL)
    assert "@pytest.mark.xfail" not in output
    assert _CATCH_WITHOUT_VAR_EXPECTED in output


def test_generate_file__foreach_with_variable_list_becomes_comment():
    output = generate("""
        start_server {tags {}} {
            foreach {type large} [array get largevalue] {
                test {test $type} {
                    r ping
                } {}
            }
        }
    """)
    assert '"""' in output
    assert "foreach" in output


_FOR_LOOP_TCL = """
    start_server {tags {}} {
        test {for loop test} {
            for {set i 0} {$i < 3} {incr i} {
                r set key $i
            }
        }
    }
"""

_FOR_LOOP_EXPECTED = """
    i = 0
    while i < 3:
        r.run('set', 'key', i)
        i += 1
"""


def test_generate_file__for_loop():
    output = generate(_FOR_LOOP_TCL)
    assert "@pytest.mark.xfail" not in output
    assert _FOR_LOOP_EXPECTED in output


def test_generate_file__rd_fixture_added_to_signature():
    output = generate("""
        start_server {tags {}} {
            test {keyspace notification test} {
                assert_keyevent_patterns $rd myhash hset hexpire
            }
        }
    """)
    assert "def test_keyspace_notification_test(r: ValkeyTestClient, rd)" in output
    assert "assert_keyevent_patterns(rd, " in output


def test_generate_file__rd_method_call_translates():
    output = generate("""
        start_server {tags {}} {
            test {rd method call} {
                set rd [setup_rd]
                $rd SET foo bar
                $rd close
            }
        }
    """)
    assert "@pytest.mark.xfail" not in output
    assert "rd.run('SET', 'foo', 'bar')" in output
    assert "rd.run('close')" in output


def test_generate_file__outer_if_else_extends_parametrize():
    output = generate("""
        start_server {tags {}} {
            foreach cmd {HINCRBY HINCRBYFLOAT} {
                if {$cmd eq "HINCRBY"} {
                    set inc1 2
                } else {
                    set inc1 2.5
                }
                test {$cmd uses inc1} {
                    r $cmd myhash f1 $inc1
                }
            }
        }
    """)
    assert '@pytest.mark.parametrize(["cmd","inc1"], [("HINCRBY",2),("HINCRBYFLOAT",2.5)])' in output
    assert "def test_cmd_uses_inc1(r: ValkeyTestClient, cmd, inc1)" in output
    assert "r.run(cmd, 'myhash', 'f1', inc1)" in output
    assert "@pytest.mark.xfail" not in output


def test_generate_file__vars_set_in_if_else_available_after():
    output = generate("""
        start_server {tags {}} {
            foreach cmd {HINCRBY HINCRBYFLOAT} {
                test {if else var scope} {
                    if {$cmd eq "HINCRBY"} {
                        set inc1 2
                    } else {
                        set inc1 2.5
                    }
                    r $cmd myhash f1 $inc1
                }
            }
        }
    """)
    assert "@pytest.mark.xfail" not in output
    assert "r.run(cmd, 'myhash', 'f1', inc1)" in output
