# ruff: noqa: F841

import pytest

from tests.valkey_test_client import ValkeyTestClient

pytestmark = [pytest.mark.info_and_its_relative_command]


@pytest.mark.xfail(reason="not implemented")
def test_extract_version_and_sha1_details_from_info_command_and_print(r: ValkeyTestClient) -> None:
    """
    test "Extract version and sha1 details from info command and print" {
        set i [r info]
        regexp {redis_version:(.*?)\r\n} $i - version
        regexp {redis_git_sha1:(.*?)\r\n} $i - sha1
        puts "Testing Valkey version $version ($sha1)"
    }
    """
    i = r.run("info")
    # TODO: regexp {redis_version:(.*?)\r\n} i - version
    # TODO: regexp {redis_git_sha1:(.*?)\r\n} i - sha1


@pytest.mark.xfail(reason="not implemented")
def test_info_command_with_at_most_one_sub_command(r: ValkeyTestClient) -> None:
    """
    test "info command with at most one sub command" {
        foreach arg {"" "all" "default" "everything"} {
            if {$arg == ""} {
                set info [r 0 info]
            } else {
                set info [r 0 info $arg]
            }

            assert { [string match "*redis_version*" $info] }
            assert { [string match "*used_cpu_user*" $info] }
            assert { ![string match "*sentinel_tilt*" $info] }
            assert { [string match "*used_memory*" $info] }
            if {$arg == "" || $arg == "default"} {
                assert { ![string match "*rejected_calls*" $info] }
            } else {
                assert { [string match "*rejected_calls*" $info] }
            }
        }
    }
    """
    # TODO: foreach arg {"" "all" "default" "everything"} {
    #       if {$arg == ""} {
    #           set info [r 0 info]
    #       } else {
    #           set info [r 0 info $arg]
    #       }
    #
    #       assert { [string match "*redis_version*" $info] }
    #       assert { [string match "*used_cpu_user*" $info] }
    #       assert { ![string match "*sentinel_tilt*" $info] }
    #       assert { [string match "*used_memory*" $info] }
    #       if {$arg == "" || $arg == "default"} {
    #           assert { ![string match "*rejected_calls*" $info] }
    #       } else {
    #           assert { [string match "*rejected_calls*" $info] }
    #       }
    #   }


@pytest.mark.xfail(reason="not implemented")
def test_info_command_with_one_sub_section(r: ValkeyTestClient) -> None:
    """
    test "info command with one sub-section" {
        set info [r info cpu]
        assert { [string match "*used_cpu_user*" $info] }
        assert { ![string match "*sentinel_tilt*" $info] }
        assert { ![string match "*used_memory*" $info] }

        set info [r info sentinel]
        assert { ![string match "*sentinel_tilt*" $info] }
        assert { ![string match "*used_memory*" $info] }

        set info [r info commandSTATS] ;# test case insensitive compare
        assert { ![string match "*used_memory*" $info] }
        assert { [string match "*rejected_calls*" $info] }
    }
    """
    info = r.run("info", "cpu")
    # TODO: assert { [string match "*used_cpu_user*" $info] }
    # TODO: assert { ![string match "*sentinel_tilt*" $info] }
    # TODO: assert { ![string match "*used_memory*" $info] }
    info = r.run("info", "sentinel")
    # TODO: assert { ![string match "*sentinel_tilt*" $info] }
    # TODO: assert { ![string match "*used_memory*" $info] }
    info = r.run("info", "commandSTATS")
    # TODO: assert { ![string match "*used_memory*" $info] }
    # TODO: assert { [string match "*rejected_calls*" $info] }


@pytest.mark.xfail(reason="not implemented")
def test_info_command_with_multiple_sub_sections(r: ValkeyTestClient) -> None:
    """
    test "info command with multiple sub-sections" {
        set info [r info cpu sentinel]
        assert { [string match "*used_cpu_user*" $info] }
        assert { ![string match "*sentinel_tilt*" $info] }
        assert { ![string match "*master_repl_offset*" $info] }

        set info [r info cpu all]
        assert { [string match "*used_cpu_user*" $info] }
        assert { ![string match "*sentinel_tilt*" $info] }
        assert { [string match "*used_memory*" $info] }
        assert { [string match "*master_repl_offset*" $info] }
        assert { [string match "*rejected_calls*" $info] }
        # check that we didn't get the same info twice
        assert { ![string match "*used_cpu_user_children*used_cpu_user_children*" $info] }

        set info [r info cpu default]
        assert { [string match "*used_cpu_user*" $info] }
        assert { ![string match "*sentinel_tilt*" $info] }
        assert { [string match "*used_memory*" $info] }
        assert { [string match "*master_repl_offset*" $info] }
        assert { ![string match "*rejected_calls*" $info] }
        # check that we didn't get the same info twice
        assert { ![string match "*used_cpu_user_children*used_cpu_user_children*" $info] }
    }
    """
    info = r.run("info", "cpu", "sentinel")
    # TODO: assert { [string match "*used_cpu_user*" $info] }
    # TODO: assert { ![string match "*sentinel_tilt*" $info] }
    # TODO: assert { ![string match "*master_repl_offset*" $info] }
    info = r.run("info", "cpu", "all")
    # TODO: assert { [string match "*used_cpu_user*" $info] }
    # TODO: assert { ![string match "*sentinel_tilt*" $info] }
    # TODO: assert { [string match "*used_memory*" $info] }
    # TODO: assert { [string match "*master_repl_offset*" $info] }
    # TODO: assert { [string match "*rejected_calls*" $info] }
    # TODO: assert { ![string match "*used_cpu_user_children*used_cpu_user_children*" $info] }
    info = r.run("info", "cpu", "default")
    # TODO: assert { [string match "*used_cpu_user*" $info] }
    # TODO: assert { ![string match "*sentinel_tilt*" $info] }
    # TODO: assert { [string match "*used_memory*" $info] }
    # TODO: assert { [string match "*master_repl_offset*" $info] }
    # TODO: assert { ![string match "*rejected_calls*" $info] }
    # TODO: assert { ![string match "*used_cpu_user_children*used_cpu_user_children*" $info] }


@pytest.mark.xfail(reason="not implemented")
def test_info_command_includes_used_active_time_main_thread_field(r: ValkeyTestClient) -> None:
    """
    test "info command includes used_active_time_main_thread field" {
        # Execute some commands to generate activity
        r set test_key test_value
        r get test_key
        r del test_key

        set info [r info]
        set active_time [getInfoProperty $info used_active_time_main_thread]

        # Verify the field has a non-zero value after activity
        assert {$active_time > 0}
    }
    """
    r.run("set", "test_key", "test_value")
    r.run("get", "test_key")
    r.run("del", "test_key")
    info = r.run("info")
    # TODO: set active_time getInfoProperty $info used_active_time_main_thread
    # TODO: assert {$active_time > 0}
