# ruff: noqa: F841, ANN002, ANN201

import pytest

from tests.valkey_test_client import ValkeyTestClient

"""
set testmodule file normalize tests/modules/moduleconfigs.so
"""


"""
set testmoduletwo file normalize tests/modules/moduleconfigstwo.so
"""


"""
set testmoduleparameter file normalize tests/modules/moduleparameter.so
"""


"""
proc module_get_args {mod} {
    foreach line [r module list] {
        if {[dict get $line name] eq $mod} {
            return [dict get $line args]
        }
    }
    throw error {module not found}
}
"""

pytestmark = [pytest.mark.modules]


"""
r module load testmodule
"""


def test_config_get_commands_work(r: ValkeyTestClient) -> None:
    """
    test {Config get commands work} {
        # Make sure config get module config works
        assert_not_equal [lsearch [lmap x [r module list] {dict get $x name}] moduleconfigs] -1
        assert_equal [r config get moduleconfigs.mutable_bool] "moduleconfigs.mutable_bool yes"
        assert_equal [r config get moduleconfigs.immutable_bool] "moduleconfigs.immutable_bool no"
        assert_equal [r config get moduleconfigs.memory_numeric] "moduleconfigs.memory_numeric 1024"
        assert_equal [r config get moduleconfigs.string] "moduleconfigs.string {secret password}"
        assert_equal [r config get moduleconfigs.enum] "moduleconfigs.enum one"
        assert_equal [r config get moduleconfigs.flags] "moduleconfigs.flags {one two}"
        assert_equal [r config get moduleconfigs.numeric] "moduleconfigs.numeric -1"
    }
    """
    assert_not_equal(lsearch(lmap("x", r.run("module", "list"), "dict get $x name"), "moduleconfigs"), -1)
    assert r.run("config", "get", "moduleconfigs.mutable_bool") == "moduleconfigs.mutable_bool yes"
    assert r.run("config", "get", "moduleconfigs.immutable_bool") == "moduleconfigs.immutable_bool no"
    assert r.run("config", "get", "moduleconfigs.memory_numeric") == "moduleconfigs.memory_numeric 1024"
    assert r.run("config", "get", "moduleconfigs.string") == "moduleconfigs.string {secret password}"
    assert r.run("config", "get", "moduleconfigs.enum") == "moduleconfigs.enum one"
    assert r.run("config", "get", "moduleconfigs.flags") == "moduleconfigs.flags {one two}"
    assert r.run("config", "get", "moduleconfigs.numeric") == "moduleconfigs.numeric -1"


def test_config_set_commands_work(r: ValkeyTestClient) -> None:
    """
    test {Config set commands work} {
        # Make sure that config sets work during runtime
        r config set moduleconfigs.mutable_bool no
        assert_equal [r config get moduleconfigs.mutable_bool] "moduleconfigs.mutable_bool no"
        r config set moduleconfigs.memory_numeric 1mb
        assert_equal [r config get moduleconfigs.memory_numeric] "moduleconfigs.memory_numeric 1048576"
        r config set moduleconfigs.string wafflewednesdays
        assert_equal [r config get moduleconfigs.string] "moduleconfigs.string wafflewednesdays"
        set not_embstr [string repeat A 50]
        r config set moduleconfigs.string $not_embstr
        assert_equal [r config get moduleconfigs.string] "moduleconfigs.string $not_embstr"
        r config set moduleconfigs.string \x73\x75\x70\x65\x72\x20\x00\x73\x65\x63\x72\x65\x74\x20\x70\x61\x73\x73\x77\x6f\x72\x64
        assert_equal [r config get moduleconfigs.string] "moduleconfigs.string {super \0secret password}"
        r config set moduleconfigs.enum two
        assert_equal [r config get moduleconfigs.enum] "moduleconfigs.enum two"
        r config set moduleconfigs.flags two
        assert_equal [r config get moduleconfigs.flags] "moduleconfigs.flags two"
        r config set moduleconfigs.numeric -2
        assert_equal [r config get moduleconfigs.numeric] "moduleconfigs.numeric -2"
    }
    """
    r.run("config", "set", "moduleconfigs.mutable_bool", "no")
    assert r.run("config", "get", "moduleconfigs.mutable_bool") == "moduleconfigs.mutable_bool no"
    r.run("config", "set", "moduleconfigs.memory_numeric", "1mb")
    assert r.run("config", "get", "moduleconfigs.memory_numeric") == "moduleconfigs.memory_numeric 1048576"
    r.run("config", "set", "moduleconfigs.string", "wafflewednesdays")
    assert r.run("config", "get", "moduleconfigs.string") == "moduleconfigs.string wafflewednesdays"
    not_embstr = string("repeat", "A", 50)
    r.run("config", "set", "moduleconfigs.string", not_embstr)
    assert r.run("config", "get", "moduleconfigs.string") == f"moduleconfigs.string {not_embstr}"
    r.run(
        "config",
        "set",
        "moduleconfigs.string",
        "\\x73\\x75\\x70\\x65\\x72\\x20\\x00\\x73\\x65\\x63\\x72\\x65\\x74\\x20\\x70\\x61\\x73\\x73\\x77\\x6f\\x72\\x64",
    )
    assert r.run("config", "get", "moduleconfigs.string") == "moduleconfigs.string {super \\0secret password}"
    r.run("config", "set", "moduleconfigs.enum", "two")
    assert r.run("config", "get", "moduleconfigs.enum") == "moduleconfigs.enum two"
    r.run("config", "set", "moduleconfigs.flags", "two")
    assert r.run("config", "get", "moduleconfigs.flags") == "moduleconfigs.flags two"
    r.run("config", "set", "moduleconfigs.numeric", -2)
    assert r.run("config", "get", "moduleconfigs.numeric") == "moduleconfigs.numeric -2"


def test_config_set_commands_enum_flags(r: ValkeyTestClient) -> None:
    """
    test {Config set commands enum flags} {
        r config set moduleconfigs.flags "none"
        assert_equal [r config get moduleconfigs.flags] "moduleconfigs.flags none"

        r config set moduleconfigs.flags "two four"
        assert_equal [r config get moduleconfigs.flags] "moduleconfigs.flags {two four}"

        r config set moduleconfigs.flags "five"
        assert_equal [r config get moduleconfigs.flags] "moduleconfigs.flags five"

        r config set moduleconfigs.flags "one four"
        assert_equal [r config get moduleconfigs.flags] "moduleconfigs.flags five"

        r config set moduleconfigs.flags "one two four"
        assert_equal [r config get moduleconfigs.flags] "moduleconfigs.flags {five two}"
    }
    """
    r.run("config", "set", "moduleconfigs.flags", "none")
    assert r.run("config", "get", "moduleconfigs.flags") == "moduleconfigs.flags none"
    r.run("config", "set", "moduleconfigs.flags", "two four")
    assert r.run("config", "get", "moduleconfigs.flags") == "moduleconfigs.flags {two four}"
    r.run("config", "set", "moduleconfigs.flags", "five")
    assert r.run("config", "get", "moduleconfigs.flags") == "moduleconfigs.flags five"
    r.run("config", "set", "moduleconfigs.flags", "one four")
    assert r.run("config", "get", "moduleconfigs.flags") == "moduleconfigs.flags five"
    r.run("config", "set", "moduleconfigs.flags", "one two four")
    assert r.run("config", "get", "moduleconfigs.flags") == "moduleconfigs.flags {five two}"


@pytest.mark.xfail(reason="not implemented")
def test_immutable_flag_works_properly_and_rejected_strings_dont_leak(r: ValkeyTestClient) -> None:
    """
    test {Immutable flag works properly and rejected strings dont leak} {
        # Configs flagged immutable should not allow sets
        catch {[r config set moduleconfigs.immutable_bool yes]} e
        assert_match {*can't set immutable config*} $e
        catch {[r config set moduleconfigs.string rejectisfreed]} e
        assert_match {*Cannot set string to 'rejectisfreed'*} $e
    }
    """
    catch("[r config set moduleconfigs.immutable_bool yes]", "e")
    # TODO: assert_match {*can't set immutable config*} e
    catch("[r config set moduleconfigs.string rejectisfreed]", "e")
    # TODO: assert_match {*Cannot set string to 'rejectisfreed'*} e


@pytest.mark.xfail(reason="not implemented")
def test_numeric_limits_work_properly(r: ValkeyTestClient) -> None:
    """
    test {Numeric limits work properly} {
        # Configs over/under the limit shouldn't be allowed, and memory configs should only take memory values
        catch {[r config set moduleconfigs.memory_numeric 200gb]} e
        assert_match {*argument must be between*} $e
        catch {[r config set moduleconfigs.memory_numeric -5]} e
        assert_match {*argument must be a memory value*} $e
        catch {[r config set moduleconfigs.numeric -10]} e
        assert_match {*argument must be between*} $e
    }
    """
    catch("[r config set moduleconfigs.memory_numeric 200gb]", "e")
    # TODO: assert_match {*argument must be between*} e
    catch("[r config set moduleconfigs.memory_numeric -5]", "e")
    # TODO: assert_match {*argument must be a memory value*} e
    catch("[r config set moduleconfigs.numeric -10]", "e")
    # TODO: assert_match {*argument must be between*} e


@pytest.mark.xfail(reason="not implemented")
def test_enums_only_able_to_be_set_to_passed_in_values(r: ValkeyTestClient) -> None:
    """
    test {Enums only able to be set to passed in values} {
        # Module authors specify what values are valid for enums, check that only those values are ok on a set
        catch {[r config set moduleconfigs.enum asdf]} e
        assert_match {*must be one of the following*} $e
    }
    """
    catch("[r config set moduleconfigs.enum asdf]", "e")
    # TODO: assert_match {*must be one of the following*} e


def test_test_blocking_of_config_registration_and_load_outside_of_onload(r: ValkeyTestClient) -> None:
    """
    test {test blocking of config registration and load outside of OnLoad} {
        assert_equal [r block.register.configs.outside.onload] OK
    }
    """
    assert r.run("block.register.configs.outside.onload") == "OK"


@pytest.mark.xfail(reason="not implemented")
def test_unload_removes_module_configs(r: ValkeyTestClient) -> None:
    """
    test {Unload removes module configs} {
        r module unload moduleconfigs
        assert_equal [r config get moduleconfigs.*] ""
        r module load $testmodule
        # these should have reverted back to their module specified values
        assert_equal [r config get moduleconfigs.mutable_bool] "moduleconfigs.mutable_bool yes"
        assert_equal [r config get moduleconfigs.immutable_bool] "moduleconfigs.immutable_bool no"
        assert_equal [r config get moduleconfigs.memory_numeric] "moduleconfigs.memory_numeric 1024"
        assert_equal [r config get moduleconfigs.string] "moduleconfigs.string {secret password}"
        assert_equal [r config get moduleconfigs.enum] "moduleconfigs.enum one"
        assert_equal [r config get moduleconfigs.flags] "moduleconfigs.flags {one two}"
        assert_equal [r config get moduleconfigs.numeric] "moduleconfigs.numeric -1"
        r module unload moduleconfigs
    }
    """
    r.run("module", "unload", "moduleconfigs")
    assert r.run("config", "get", "moduleconfigs.*") == ""
    # TODO: r module load testmodule
    assert r.run("config", "get", "moduleconfigs.mutable_bool") == "moduleconfigs.mutable_bool yes"
    assert r.run("config", "get", "moduleconfigs.immutable_bool") == "moduleconfigs.immutable_bool no"
    assert r.run("config", "get", "moduleconfigs.memory_numeric") == "moduleconfigs.memory_numeric 1024"
    assert r.run("config", "get", "moduleconfigs.string") == "moduleconfigs.string {secret password}"
    assert r.run("config", "get", "moduleconfigs.enum") == "moduleconfigs.enum one"
    assert r.run("config", "get", "moduleconfigs.flags") == "moduleconfigs.flags {one two}"
    assert r.run("config", "get", "moduleconfigs.numeric") == "moduleconfigs.numeric -1"
    r.run("module", "unload", "moduleconfigs")


@pytest.mark.xfail(reason="not implemented")
def test_test_loadex_functionality(r: ValkeyTestClient) -> None:
    """
    test {test loadex functionality} {
        r module loadex $testmodule CONFIG moduleconfigs.mutable_bool no CONFIG moduleconfigs.immutable_bool yes CONFIG moduleconfigs.memory_numeric 2mb CONFIG moduleconfigs.string tclortickle
        assert_not_equal [lsearch [lmap x [r module list] {dict get $x name}] moduleconfigs] -1
        assert_equal [r config get moduleconfigs.mutable_bool] "moduleconfigs.mutable_bool no"
        assert_equal [r config get moduleconfigs.immutable_bool] "moduleconfigs.immutable_bool yes"
        assert_equal [r config get moduleconfigs.memory_numeric] "moduleconfigs.memory_numeric 2097152"
        assert_equal [r config get moduleconfigs.string] "moduleconfigs.string tclortickle"
        # Configs that were not changed should still be their module specified value
        assert_equal [r config get moduleconfigs.enum] "moduleconfigs.enum one"
        assert_equal [r config get moduleconfigs.flags] "moduleconfigs.flags {one two}"
        assert_equal [r config get moduleconfigs.numeric] "moduleconfigs.numeric -1"
    }
    """
    # TODO: r module loadex testmodule CONFIG moduleconfigs.mutable_bool no CONFIG moduleconfigs.immutable_bool yes CONFIG moduleconfigs.memory_numeric 2mb CONFIG moduleconfigs.string tclortickle
    assert_not_equal(lsearch(lmap("x", r.run("module", "list"), "dict get $x name"), "moduleconfigs"), -1)
    assert r.run("config", "get", "moduleconfigs.mutable_bool") == "moduleconfigs.mutable_bool no"
    assert r.run("config", "get", "moduleconfigs.immutable_bool") == "moduleconfigs.immutable_bool yes"
    assert r.run("config", "get", "moduleconfigs.memory_numeric") == "moduleconfigs.memory_numeric 2097152"
    assert r.run("config", "get", "moduleconfigs.string") == "moduleconfigs.string tclortickle"
    assert r.run("config", "get", "moduleconfigs.enum") == "moduleconfigs.enum one"
    assert r.run("config", "get", "moduleconfigs.flags") == "moduleconfigs.flags {one two}"
    assert r.run("config", "get", "moduleconfigs.numeric") == "moduleconfigs.numeric -1"


@pytest.mark.xfail(reason="not implemented")
def test_apply_function_works(r: ValkeyTestClient) -> None:
    """
    test {apply function works} {
        catch {[r config set moduleconfigs.mutable_bool yes]} e
        assert_match {*Bool configs*} $e
        assert_equal [r config get moduleconfigs.mutable_bool] "moduleconfigs.mutable_bool no"
        catch {[r config set moduleconfigs.memory_numeric 1000 moduleconfigs.numeric 1000]} e
        assert_match {*cannot equal*} $e
        assert_equal [r config get moduleconfigs.memory_numeric] "moduleconfigs.memory_numeric 2097152"
        assert_equal [r config get moduleconfigs.numeric] "moduleconfigs.numeric -1"
        r module unload moduleconfigs
    }
    """
    catch("[r config set moduleconfigs.mutable_bool yes]", "e")
    # TODO: assert_match {*Bool configs*} e
    assert r.run("config", "get", "moduleconfigs.mutable_bool") == "moduleconfigs.mutable_bool no"
    catch("[r config set moduleconfigs.memory_numeric 1000 moduleconfigs.numeric 1000]", "e")
    # TODO: assert_match {*cannot equal*} e
    assert r.run("config", "get", "moduleconfigs.memory_numeric") == "moduleconfigs.memory_numeric 2097152"
    assert r.run("config", "get", "moduleconfigs.numeric") == "moduleconfigs.numeric -1"
    r.run("module", "unload", "moduleconfigs")


@pytest.mark.xfail(reason="not implemented")
def test_test_double_config_argument_to_loadex(r: ValkeyTestClient) -> None:
    """
    test {test double config argument to loadex} {
        r module loadex $testmodule CONFIG moduleconfigs.mutable_bool yes CONFIG moduleconfigs.mutable_bool no
        assert_equal [r config get moduleconfigs.mutable_bool] "moduleconfigs.mutable_bool no"
        r module unload moduleconfigs
    }
    """
    # TODO: r module loadex testmodule CONFIG moduleconfigs.mutable_bool yes CONFIG moduleconfigs.mutable_bool no
    assert r.run("config", "get", "moduleconfigs.mutable_bool") == "moduleconfigs.mutable_bool no"
    r.run("module", "unload", "moduleconfigs")


@pytest.mark.xfail(reason="not implemented")
def test_missing_loadconfigs_call(r: ValkeyTestClient) -> None:
    """
    test {missing loadconfigs call} {
        catch {[r module loadex $testmodule CONFIG moduleconfigs.string "cool" ARGS noload]} e
        assert_match {*ERR*} $e
    }
    """
    catch('[r module loadex $testmodule CONFIG moduleconfigs.string "cool" ARGS noload]', "e")
    # TODO: assert_match {*ERR*} e


@pytest.mark.xfail(reason="not implemented")
def test_test_loadex_rejects_bad_configs(r: ValkeyTestClient) -> None:
    """
    test {test loadex rejects bad configs} {
        # Bad config 200gb is over the limit
        catch {[r module loadex $testmodule CONFIG moduleconfigs.memory_numeric 200gb ARGS]} e
        assert_match {*ERR*} $e
        # We should completely remove all configs on a failed load
        assert_equal [r config get moduleconfigs.*] ""
        # No value for config, should error out
        catch {[r module loadex $testmodule CONFIG moduleconfigs.mutable_bool CONFIG moduleconfigs.enum two ARGS]} e
        assert_match {*ERR*} $e
        assert_equal [r config get moduleconfigs.*] ""
        # Asan will catch this if this string is not freed
        catch {[r module loadex $testmodule CONFIG moduleconfigs.string rejectisfreed]}
        assert_match {*ERR*} $e
        assert_equal [r config get moduleconfigs.*] ""
        # test we can't set random configs
        catch {[r module loadex $testmodule CONFIG maxclients 333]}
        assert_match {*ERR*} $e
        assert_equal [r config get moduleconfigs.*] ""
        assert_not_equal [r config get maxclients] "maxclients 333"
        # test we can't set other module's configs
        r module load $testmoduletwo
        catch {[r module loadex $testmodule CONFIG configs.test no]}
        assert_match {*ERR*} $e
        assert_equal [r config get configs.test] "configs.test yes"
        r module unload configs
    }
    """
    catch("[r module loadex $testmodule CONFIG moduleconfigs.memory_numeric 200gb ARGS]", "e")
    # TODO: assert_match {*ERR*} e
    assert r.run("config", "get", "moduleconfigs.*") == ""
    catch("[r module loadex $testmodule CONFIG moduleconfigs.mutable_bool CONFIG moduleconfigs.enum two ARGS]", "e")
    # TODO: assert_match {*ERR*} e
    assert r.run("config", "get", "moduleconfigs.*") == ""
    catch("[r module loadex $testmodule CONFIG moduleconfigs.string rejectisfreed]")
    # TODO: assert_match {*ERR*} e
    assert r.run("config", "get", "moduleconfigs.*") == ""
    catch("[r module loadex $testmodule CONFIG maxclients 333]")
    # TODO: assert_match {*ERR*} e
    assert r.run("config", "get", "moduleconfigs.*") == ""
    assert_not_equal(r.run("config", "get", "maxclients"), "maxclients 333")
    # TODO: r module load testmoduletwo
    catch("[r module loadex $testmodule CONFIG configs.test no]")
    # TODO: assert_match {*ERR*} e
    assert r.run("config", "get", "configs.test") == "configs.test yes"
    r.run("module", "unload", "configs")


@pytest.mark.xfail(reason="not implemented")
def test_test_config_rewrite_with_dynamic_load(r: ValkeyTestClient) -> None:
    """
    test {test config rewrite with dynamic load} {
        #translates to: super \0secret password
        r module loadex $testmodule CONFIG moduleconfigs.string \x73\x75\x70\x65\x72\x20\x00\x73\x65\x63\x72\x65\x74\x20\x70\x61\x73\x73\x77\x6f\x72\x64 ARGS
        assert_not_equal [lsearch [lmap x [r module list] {dict get $x name}] moduleconfigs] -1
        assert_equal [r config get moduleconfigs.string] "moduleconfigs.string {super \0secret password}"
        r config set moduleconfigs.mutable_bool yes
        r config set moduleconfigs.memory_numeric 750
        r config set moduleconfigs.enum two
        r config set moduleconfigs.flags "four two"
        r config rewrite
        restart_server 0 true false
        # Ensure configs we rewrote are present and that the conf file is readable
        assert_equal [r config get moduleconfigs.mutable_bool] "moduleconfigs.mutable_bool yes"
        assert_equal [r config get moduleconfigs.memory_numeric] "moduleconfigs.memory_numeric 750"
        assert_equal [r config get moduleconfigs.string] "moduleconfigs.string {super \0secret password}"
        assert_equal [r config get moduleconfigs.enum] "moduleconfigs.enum two"
        assert_equal [r config get moduleconfigs.flags] "moduleconfigs.flags {two four}"
        assert_equal [r config get moduleconfigs.numeric] "moduleconfigs.numeric -1"
        r module unload moduleconfigs
    }
    """
    # TODO: r module loadex testmodule CONFIG moduleconfigs.string \x73\x75\x70\x65\x72\x20\x00\x73\x65\x63\x72\x65\x74\x20\x70\x61\x73\x73\x77\x6f\x72\x64 ARGS
    assert_not_equal(lsearch(lmap("x", r.run("module", "list"), "dict get $x name"), "moduleconfigs"), -1)
    assert r.run("config", "get", "moduleconfigs.string") == "moduleconfigs.string {super \\0secret password}"
    r.run("config", "set", "moduleconfigs.mutable_bool", "yes")
    r.run("config", "set", "moduleconfigs.memory_numeric", 750)
    r.run("config", "set", "moduleconfigs.enum", "two")
    r.run("config", "set", "moduleconfigs.flags", "four two")
    r.run("config", "rewrite")
    restart_server(0, "true", "false")
    assert r.run("config", "get", "moduleconfigs.mutable_bool") == "moduleconfigs.mutable_bool yes"
    assert r.run("config", "get", "moduleconfigs.memory_numeric") == "moduleconfigs.memory_numeric 750"
    assert r.run("config", "get", "moduleconfigs.string") == "moduleconfigs.string {super \\0secret password}"
    assert r.run("config", "get", "moduleconfigs.enum") == "moduleconfigs.enum two"
    assert r.run("config", "get", "moduleconfigs.flags") == "moduleconfigs.flags {two four}"
    assert r.run("config", "get", "moduleconfigs.numeric") == "moduleconfigs.numeric -1"
    r.run("module", "unload", "moduleconfigs")


@pytest.mark.xfail(reason="not implemented")
def test_test_multiple_modules_with_configs(r: ValkeyTestClient) -> None:
    """
    test {test multiple modules with configs} {
        r module load $testmodule
        r module loadex $testmoduletwo CONFIG configs.test yes
        assert_equal [r config get moduleconfigs.mutable_bool] "moduleconfigs.mutable_bool yes"
        assert_equal [r config get moduleconfigs.immutable_bool] "moduleconfigs.immutable_bool no"
        assert_equal [r config get moduleconfigs.memory_numeric] "moduleconfigs.memory_numeric 1024"
        assert_equal [r config get moduleconfigs.string] "moduleconfigs.string {secret password}"
        assert_equal [r config get moduleconfigs.enum] "moduleconfigs.enum one"
        assert_equal [r config get moduleconfigs.numeric] "moduleconfigs.numeric -1"
        assert_equal [r config get configs.test] "configs.test yes"
        r config set moduleconfigs.mutable_bool no
        r config set moduleconfigs.string nice
        r config set moduleconfigs.enum two
        r config set configs.test no
        assert_equal [r config get moduleconfigs.mutable_bool] "moduleconfigs.mutable_bool no"
        assert_equal [r config get moduleconfigs.string] "moduleconfigs.string nice"
        assert_equal [r config get moduleconfigs.enum] "moduleconfigs.enum two"
        assert_equal [r config get configs.test] "configs.test no"
        r config rewrite
        # test we can load from conf file with multiple different modules.
        restart_server 0 true false
        assert_equal [r config get moduleconfigs.mutable_bool] "moduleconfigs.mutable_bool no"
        assert_equal [r config get moduleconfigs.string] "moduleconfigs.string nice"
        assert_equal [r config get moduleconfigs.enum] "moduleconfigs.enum two"
        assert_equal [r config get configs.test] "configs.test no"
        r module unload moduleconfigs
        r module unload configs
    }
    """
    # TODO: r module load testmodule
    # TODO: r module loadex testmoduletwo CONFIG configs.test yes
    assert r.run("config", "get", "moduleconfigs.mutable_bool") == "moduleconfigs.mutable_bool yes"
    assert r.run("config", "get", "moduleconfigs.immutable_bool") == "moduleconfigs.immutable_bool no"
    assert r.run("config", "get", "moduleconfigs.memory_numeric") == "moduleconfigs.memory_numeric 1024"
    assert r.run("config", "get", "moduleconfigs.string") == "moduleconfigs.string {secret password}"
    assert r.run("config", "get", "moduleconfigs.enum") == "moduleconfigs.enum one"
    assert r.run("config", "get", "moduleconfigs.numeric") == "moduleconfigs.numeric -1"
    assert r.run("config", "get", "configs.test") == "configs.test yes"
    r.run("config", "set", "moduleconfigs.mutable_bool", "no")
    r.run("config", "set", "moduleconfigs.string", "nice")
    r.run("config", "set", "moduleconfigs.enum", "two")
    r.run("config", "set", "configs.test", "no")
    assert r.run("config", "get", "moduleconfigs.mutable_bool") == "moduleconfigs.mutable_bool no"
    assert r.run("config", "get", "moduleconfigs.string") == "moduleconfigs.string nice"
    assert r.run("config", "get", "moduleconfigs.enum") == "moduleconfigs.enum two"
    assert r.run("config", "get", "configs.test") == "configs.test no"
    r.run("config", "rewrite")
    restart_server(0, "true", "false")
    assert r.run("config", "get", "moduleconfigs.mutable_bool") == "moduleconfigs.mutable_bool no"
    assert r.run("config", "get", "moduleconfigs.string") == "moduleconfigs.string nice"
    assert r.run("config", "get", "moduleconfigs.enum") == "moduleconfigs.enum two"
    assert r.run("config", "get", "configs.test") == "configs.test no"
    r.run("module", "unload", "moduleconfigs")
    r.run("module", "unload", "configs")


@pytest.mark.xfail(reason="not implemented")
def test_test_1_module_load_2_config_rewrite_3_module_unload_4_config_rewrite_works(r: ValkeyTestClient) -> None:
    """
    test {test 1.module load 2.config rewrite 3.module unload 4.config rewrite works} {
        # Configs need to be removed from the old config file in this case.
        r module loadex $testmodule CONFIG moduleconfigs.memory_numeric 500 ARGS
        assert_not_equal [lsearch [lmap x [r module list] {dict get $x name}] moduleconfigs] -1
        r config rewrite
        r module unload moduleconfigs
        r config rewrite
        restart_server 0 true false
        # Ensure configs we rewrote are no longer present
        assert_equal [r config get moduleconfigs.*] ""
    }
    """
    # TODO: r module loadex testmodule CONFIG moduleconfigs.memory_numeric 500 ARGS
    assert_not_equal(lsearch(lmap("x", r.run("module", "list"), "dict get $x name"), "moduleconfigs"), -1)
    r.run("config", "rewrite")
    r.run("module", "unload", "moduleconfigs")
    r.run("config", "rewrite")
    restart_server(0, "true", "false")
    assert r.run("config", "get", "moduleconfigs.*") == ""


@pytest.mark.xfail(reason="not implemented")
def test_startup_moduleconfigs(r: ValkeyTestClient) -> None:
    """
    test {startup moduleconfigs} {
        # No loadmodule directive
        catch {exec $::VALKEY_SERVER_BIN --moduleconfigs.string "hello"} err
        assert_match {*Module Configuration detected without loadmodule directive or no ApplyConfig call: aborting*} $err

        # Bad config value
        catch {exec $::VALKEY_SERVER_BIN --loadmodule "$testmodule" --moduleconfigs.string "rejectisfreed"} err
        assert_match {*Issue during loading of configuration moduleconfigs.string : Cannot set string to 'rejectisfreed'*} $err

        # missing LoadConfigs call
        catch {exec $::VALKEY_SERVER_BIN --loadmodule "$testmodule" noload --moduleconfigs.string "hello"} err
        assert_match {*Module Configurations were not set, likely a missing LoadConfigs call. Unloading the module.*} $err

        # successful
        start_server [list overrides [list loadmodule "$testmodule" moduleconfigs.string "bootedup" moduleconfigs.enum two moduleconfigs.flags "two four"]] {
            assert_equal [r config get moduleconfigs.string] "moduleconfigs.string bootedup"
            assert_equal [r config get moduleconfigs.mutable_bool] "moduleconfigs.mutable_bool yes"
            assert_equal [r config get moduleconfigs.immutable_bool] "moduleconfigs.immutable_bool no"
            assert_equal [r config get moduleconfigs.enum] "moduleconfigs.enum two"
            assert_equal [r config get moduleconfigs.flags] "moduleconfigs.flags {two four}"
            assert_equal [r config get moduleconfigs.numeric] "moduleconfigs.numeric -1"
            assert_equal [r config get moduleconfigs.memory_numeric] "moduleconfigs.memory_numeric 1024"
        }
    }
    """
    catch('exec $::VALKEY_SERVER_BIN --moduleconfigs.string "hello"', "err")
    # TODO: assert_match {*Module Configuration detected without loadmodule directive or no ApplyConfig call: aborting*} err
    catch('exec $::VALKEY_SERVER_BIN --loadmodule "$testmodule" --moduleconfigs.string "rejectisfreed"', "err")
    # TODO: assert_match {*Issue during loading of configuration moduleconfigs.string : Cannot set string to 'rejectisfreed'*} err
    catch('exec $::VALKEY_SERVER_BIN --loadmodule "$testmodule" noload --moduleconfigs.string "hello"', "err")
    # TODO: assert_match {*Module Configurations were not set, likely a missing LoadConfigs call. Unloading the module.*} err
    # TODO: start_server list overrides [list loadmodule "$testmodule" moduleconfigs.string "bootedup" moduleconfigs.enum two moduleconfigs.flags "two four"] {
    #       assert_equal [r config get moduleconfigs.string] "moduleconfigs.string bootedup"
    #       assert_equal [r config get moduleconfigs.mutable_bool] "moduleconfigs.mutable_bool yes"
    #       assert_equal [r config get moduleconfigs.immutable_bool] "moduleconfigs.immutable_bool no"
    #       assert_equal [r config get moduleconfigs.enum] "moduleconfigs.enum two"
    #       assert_equal [r config get moduleconfigs.flags] "moduleconfigs.flags {two four}"
    #       assert_equal [r config get moduleconfigs.numeric] "moduleconfigs.numeric -1"
    #       assert_equal [r config get moduleconfigs.memory_numeric] "moduleconfigs.memory_numeric 1024"
    #   }


@pytest.mark.xfail(reason="not implemented")
def test_module_update_args(r: ValkeyTestClient) -> None:
    """
    test {Module Update Args} {
        r module load $testmoduleparameter 10 20 30

        set t [r module list]
        set modulename [lmap x [r module list] {dict get $x name}]
        assert_not_equal [lsearch $modulename moduleparameter] -1
        assert_equal {10 20 30} [module_get_args moduleparameter]
        assert_equal OK [r testmoduleparameter.update.parameter 40 50 60 70]
        assert_equal {40 50 60 70} [module_get_args moduleparameter]
    }
    """
    # TODO: r module load testmoduleparameter 10 20 30
    t = r.run("module", "list")
    modulename = lmap("x", r.run("module", "list"), "dict get $x name")
    assert_not_equal(lsearch(modulename, "moduleparameter"), -1)
    assert "10 20 30" == module_get_args("moduleparameter")
    assert "OK" == r.run("testmoduleparameter.update.parameter", 40, 50, 60, 70)
    assert "40 50 60 70" == module_get_args("moduleparameter")


# --- stubs for unimplemented TCL helpers ---


def assert_not_equal(*args):
    raise NotImplementedError("assert_not_equal")


def catch(*args):
    raise NotImplementedError("catch")


def lmap(*args):
    raise NotImplementedError("lmap")


def lsearch(*args):
    raise NotImplementedError("lsearch")


def module_get_args(*args):
    raise NotImplementedError("module_get_args")


def restart_server(*args):
    raise NotImplementedError("restart_server")


def string(*args):
    raise NotImplementedError("string")
