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
