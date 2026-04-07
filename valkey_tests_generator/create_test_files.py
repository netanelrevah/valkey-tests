from __future__ import annotations

import keyword
import re
import sys
import textwrap
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from itertools import cycle, zip_longest
from typing import IO, TYPE_CHECKING, TextIO

if TYPE_CHECKING:
    from pathlib import Path

from pytcl.commands import TCLBracesWord, TCLCommandForEach, TCLList, TCLScript
from pytcl.words import TCLCommandWord, TCLDoubleQuotedWord, TCLVariableSubstitutionWord, TCLWord

import valkey_tests_generator.argument_translators as _arg_translators
from valkey_tests_generator.argument_translators import _safe_var_name
from valkey_tests_generator.command_generators import CommandGenerator
from valkey_tests_generator.statement_translators import TCLBodyTranslator, _extract_todo_commands, _has_todos

_TEST_NAME_TRANSLATE_TABLE = str.maketrans({"/": "_or_", **{c: "_" for c in "{}\",#: -()<>=$'.,*&@!?|+~^%"}})

_KNOWN_FIXTURE_VARS = frozenset({"rd", "rd1", "rd2", "rd3", "rr", "r2", "rd_trk", "plain_client", "db"})


_VAR_REF_RE = re.compile(r"\$\{?([A-Za-z0-9_]+)\}?")


def _collect_fixture_refs(body: TCLScript) -> set[str]:
    """Return known fixture variable names referenced but NOT locally set in a TCL script body."""
    refs: set[str] = set()
    locally_set: set[str] = set()
    for command in body.commands:
        if command.name == "set" and command.args and isinstance(command.args[0], TCLWord):
            locally_set.add(command.args[0].value)
        # $var used as a command name: "$rd close"
        if command.name.startswith("$"):
            var_name = command.name[1:]
            if var_name in _KNOWN_FIXTURE_VARS:
                refs.add(var_name)
        for arg in command.args:
            if isinstance(arg, TCLVariableSubstitutionWord) and arg.variable_name in _KNOWN_FIXTURE_VARS:
                refs.add(arg.variable_name)
            elif isinstance(arg, TCLDoubleQuotedWord):
                for m in _VAR_REF_RE.finditer(arg.value):
                    if m.group(1) in _KNOWN_FIXTURE_VARS:
                        refs.add(m.group(1))
    return refs - locally_set


def _test_name_from(raw: str) -> str:
    normalized = re.sub(
        "_+", "_", re.sub(r"[^a-z0-9_]", "_", raw.lower().translate(_TEST_NAME_TRANSLATE_TABLE)).strip("_")
    )
    return "test_" + normalized


def _translate_test_body(
    test_command: TCLCommandWord, initial_vars: set[str] | None = None
) -> tuple[list[str], set[str]]:
    body_arg = test_command.args[1] if len(test_command.args) > 1 else None
    expected_arg = test_command.args[2] if test_command.args[2:] else None
    body = TCLScript.read(iter(body_arg.value)) if isinstance(body_arg, TCLBracesWord) else None
    expected = expected_arg.value if isinstance(expected_arg, TCLBracesWord) else None
    fixture_refs = _collect_fixture_refs(body) - (initial_vars or set()) if body else set()
    all_initial_vars = (initial_vars or set()) | fixture_refs
    lines = (
        TCLBodyTranslator().translate(body, expected, initial_vars=all_initial_vars)
        if body is not None
        else ["assert False"]
    )
    return lines, fixture_refs


def _format_parametrize_value(value: str | None) -> str:
    if not value:
        return '"""None"""'
    if "\n" in value:
        return f'"""{value}"""'
    try:
        return str(int(value))
    except ValueError:
        pass
    try:
        return str(float(value))
    except ValueError:
        pass
    return f'"{value}"'


@dataclass
class TCLTestFileGenerator:
    output: IO = field(default=sys.stdout)
    _todo_counter: Counter = field(default_factory=Counter)
    _total_tests: int = field(default=0)
    _translated_tests: int = field(default=0)
    _used_names: Counter = field(default_factory=Counter)

    def generate_parametrize_extended(self, foreach_command: TCLCommandForEach, derived: dict[str, list[str]]) -> str:
        name_to_values: dict[str, list] = defaultdict(list)
        for var_names, var_values in foreach_command.variables_names_and_values_lists:
            for value, name in zip(var_values.words, cycle(var_names)):
                name_to_values[name].append(value)
        name_to_values.update(derived)

        names = ",".join(f'"{_safe_var_name(n)}"' for n in name_to_values)
        tuples = ",".join(
            "(" + ",".join(_format_parametrize_value(v) for v in row) + ")"
            for row in zip_longest(*name_to_values.values(), fillvalue=None)
        )
        return f"@pytest.mark.parametrize([{names}], [{tuples}])\n"

    def generate_parametrize(self, foreach_command: TCLCommandForEach) -> str:
        name_to_values: dict[str, list] = defaultdict(list)
        for var_names, var_values in foreach_command.variables_names_and_values_lists:
            for value, name in zip(var_values.words, cycle(var_names)):
                name_to_values[name].append(value)

        names = ",".join(f'"{_safe_var_name(n)}"' for n in name_to_values)
        tuples = ",".join(
            "(" + ",".join(_format_parametrize_value(v) for v in row) + ")"
            for row in zip_longest(*name_to_values.values(), fillvalue=None)
        )
        return f"@pytest.mark.parametrize([{names}], [{tuples}])\n"

    def generate_test(
        self,
        test_command: TCLCommandWord,
        if_expressions: list[str] | None = None,
        parametrizes: list[str] | None = None,
        parametrize_vars: list[str] | None = None,
    ) -> None:
        raw_name = (
            test_command.args[0].value if isinstance(test_command.args[0], TCLBracesWord) else str(test_command.args[0])
        )
        base_name = _test_name_from(raw_name)
        count = self._used_names[base_name]
        self._used_names[base_name] += 1
        test_name = base_name if count == 0 else f"{base_name}_{count}"

        initial_vars = set(parametrize_vars) if parametrize_vars else None
        lines, fixture_refs = _translate_test_body(test_command, initial_vars=initial_vars)

        self._total_tests += 1
        if _has_todos(lines):
            self._todo_counter.update(_extract_todo_commands(lines))
        else:
            self._translated_tests += 1

        self.output.write("\n\n")
        if _has_todos(lines):
            self.output.write("@pytest.mark.xfail(reason='not implemented')\n")
        for if_expression in if_expressions or []:
            self.output.write(f"@pytest.mark.skipif('', reason={if_expression!r})\n")
        if parametrizes:
            self.output.writelines(parametrizes)
        extra_params = "".join(f", {_safe_var_name(v)}" for v in (parametrize_vars or []))
        fixture_params = "".join(f", {v}" for v in sorted(fixture_refs))
        self.output.write(f"def {test_name}(r: ValkeyTestClient{extra_params}{fixture_params}) -> None:\n")
        self.output.write('    """\n')
        self.output.write(textwrap.indent(test_command.formatted(), "    ") + "\n")
        self.output.write('    """\n')
        for line in lines:
            self.output.write(f"    {line}\n")

    def generate_comment(self, command: TCLCommandWord) -> None:
        self.output.write('\n\n"""\n')
        self.output.write(command.formatted() + "\n")
        self.output.write('"""\n')

    def generate_tests(
        self,
        script: TCLScript,
        if_expressions: list[str] | None = None,
        foreach_commands: list[str] | None = None,
        parametrize_vars: list[str] | None = None,
    ) -> None:
        for command in script.commands:
            if not isinstance(command, TCLCommandWord):
                continue
            handler = CommandGenerator.MAPPING.get(command.name)
            if handler is not None:
                handler.generate(command, self, if_expressions, foreach_commands, parametrize_vars)
            else:
                self.generate_comment(command)

    def _process_start_server(self, command: TCLCommandWord) -> None:
        tags: list[str] = []

        options = TCLList.build(command.args[0], namespace={}).words
        for option, value in zip(options[::2], options[1::2]):
            match option:
                case "tags":
                    for word in TCLList.words_iterator(iter(value), {}):
                        tag = re.sub(r"[^a-zA-Z0-9]+", "_", word).strip("_")
                        if tag:
                            tags.append(tag)

        if tags:
            safe_tags = [f"tag_{t}" if keyword.iskeyword(t) else t for t in dict.fromkeys(tags)]
            marks = ", ".join(["pytest.mark." + tag for tag in safe_tags])
            self.output.write("\n")
            self.output.write(f"pytestmark = [{marks}]\n")

        assert isinstance(command.args[1], TCLBracesWord)
        start_server_code = TCLScript.read(iter(command.args[1].value))

        if start_server_code:
            self.generate_tests(start_server_code)

    def generate(self, source_file: TextIO) -> None:
        _arg_translators.collected_stubs.clear()

        self.output.write("# ruff: noqa: PLR2004, PLR1714, F841, N806, RUF043, ANN001, ANN002, ANN201\n")
        self.output.write("import time\n\n")
        self.output.write("import pytest\n")
        self.output.write("from fnmatch import fnmatch\n\n")
        self.output.write("from tests.valkey_test_client import ValkeyTestClient\n")

        script = TCLScript.read_text_io(source_file)

        for command in script.commands:
            if not isinstance(command, TCLCommandWord):
                continue
            if command.name == "start_server":
                self._process_start_server(command)
            else:
                self.generate_comment(command)

        if _arg_translators.collected_stubs:
            self.output.write("\n\n# --- stubs for unimplemented TCL helpers ---\n")
            for name in sorted(_arg_translators.collected_stubs):
                self.output.write(f"\ndef {name}(*args):\n    raise NotImplementedError({name!r})\n")

    def generate_file(self, source_file_path: Path) -> None:
        with open(source_file_path, encoding="utf-8", errors="replace") as source_file:
            self.generate(source_file)


def _discover_tcl_files(tests_path: Path) -> list[Path]:
    return list(sorted(tests_path.rglob("*.tcl")))


def _tcl_path_to_python_path(tcl_file: Path, base_tcl_path: Path) -> Path:
    relative = tcl_file.relative_to(base_tcl_path)
    return relative.parent / f"test_{relative.stem}.py"
