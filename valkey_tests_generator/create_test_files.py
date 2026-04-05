from __future__ import annotations

import keyword
import math
import re
import sys
import textwrap
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from itertools import cycle, zip_longest
from typing import IO, TYPE_CHECKING, ClassVar, TextIO

if TYPE_CHECKING:
    from pathlib import Path

from pytcl.commands import TCLBracesWord, TCLCommandForEach, TCLCommandIf, TCLList, TCLScript
from pytcl.words import (
    TCLBracketWord,
    TCLCommandArguments,
    TCLCommandWord,
    TCLDoubleQuotedWord,
    TCLVariableSubstitutionWord,
    TCLWord,
)


def _reconstruct_argument(argument: TCLCommandArguments) -> str:
    if isinstance(argument, TCLBracesWord):
        return "{" + argument.value + "}"
    if isinstance(argument, TCLDoubleQuotedWord):
        return '"' + argument.value + '"'
    return str(argument)


def _reconstruct_command(command: TCLCommandWord) -> str:
    parts = [command.name, *(_reconstruct_argument(argument) for argument in command.args)]
    return " ".join(parts)


def _format_argument(argument: TCLCommandArguments) -> str:
    if isinstance(argument, TCLBracesWord) and "\n" in argument.value:
        body = textwrap.indent(textwrap.dedent(argument.value).strip(), "    ")
        return "{\n" + body + "\n}"
    return _reconstruct_argument(argument)


def _format_command(command: TCLCommandWord) -> str:
    parts = [command.name, *(_format_argument(argument) for argument in command.args)]
    return " ".join(parts)


def _translate_argument(argument: TCLCommandArguments, defined_vars: set[str]) -> str | None:
    if isinstance(argument, TCLVariableSubstitutionWord):
        if "::" in argument.variable_name or argument.variable_name not in defined_vars:
            return None
        return argument.variable_name
    if isinstance(argument, TCLBracketWord):
        commands = [c for c in argument.script.commands if c.name]
        if len(commands) != 1:
            return None
        return _translate_command_expr(commands[0], defined_vars)
    if isinstance(argument, TCLBracesWord):
        return repr(argument.value)
    if isinstance(argument, TCLDoubleQuotedWord):
        if "$" in argument.value or "\\" in argument.value:
            return None
        return repr(argument.value)
    s = argument.value
    try:
        int(s)
        return s
    except ValueError:
        pass
    try:
        v = float(s)
        if math.isinf(v):
            return f"float('{s}')"
        if math.isnan(v):
            return "float('nan')"
        return s
    except ValueError:
        pass
    return repr(s)


def _translate_r_arguments(arguments: list[TCLCommandArguments], defined_vars: set[str]) -> str | None:
    if not arguments:
        return None
    subcmd = _translate_argument(arguments[0], defined_vars)
    if subcmd is None:
        return None
    rest = []
    for argument in arguments[1:]:
        t = _translate_argument(argument, defined_vars)
        if t is None:
            return None
        rest.append(t)
    call_arguments = ", ".join([subcmd, *rest])
    return f"r.run({call_arguments})"


def _translate_command_expr(command: TCLCommandWord, defined_vars: set[str]) -> str | None:
    if command.name == "r":
        return _translate_r_arguments(command.args, defined_vars)
    return None


class StatementTranslator:
    MAPPING: ClassVar[dict[str, StatementTranslator]] = {}

    def get_statement(self, arguments: list[TCLCommandArguments], defined_vars: set[str]) -> list[str] | None:
        raise NotImplementedError


class RStatementTranslator(StatementTranslator):
    def get_statement(self, arguments: list[TCLCommandArguments], defined_vars: set[str]) -> list[str] | None:
        expr = _translate_r_arguments(arguments, defined_vars)
        return None if expr is None else [expr]


class SetStatementTranslator(StatementTranslator):
    def get_statement(self, arguments: list[TCLCommandArguments], defined_vars: set[str]) -> list[str] | None:
        if not arguments[1:]:
            return None
        name_argument = arguments[0]
        if not isinstance(name_argument, TCLWord) or "(" in name_argument.value:
            return None
        val = _translate_argument(arguments[1], defined_vars)
        return None if val is None else [f"{name_argument.value} = {val}"]


class AssertEqualStatementTranslator(StatementTranslator):
    def get_statement(self, arguments: list[TCLCommandArguments], defined_vars: set[str]) -> list[str] | None:
        if not arguments[1:]:
            return None
        a = _translate_argument(arguments[0], defined_vars)
        b = _translate_argument(arguments[1], defined_vars)
        return None if a is None or b is None else [f"assert {a} == {b}"]


class AssertMatchStatementTranslator(StatementTranslator):
    def get_statement(self, arguments: list[TCLCommandArguments], defined_vars: set[str]) -> list[str] | None:
        if not arguments[1:]:
            return None
        pat = _translate_argument(arguments[0], defined_vars)
        val = _translate_argument(arguments[1], defined_vars)
        return None if pat is None or val is None else [f"assert fnmatch(str({val}), str({pat}))"]


class AssertStatementTranslator(StatementTranslator):
    def get_statement(self, arguments: list[TCLCommandArguments], defined_vars: set[str]) -> list[str] | None:
        if not arguments or not isinstance(arguments[0], TCLBracketWord):
            return None
        inner = [c for c in arguments[0].script.commands if c.name]
        if len(inner) != 1:
            return None
        expr = _translate_command_expr(inner[0], defined_vars)
        return None if expr is None else [f"assert {expr}"]


class IncrStatementTranslator(StatementTranslator):
    def get_statement(self, arguments: list[TCLCommandArguments], defined_vars: set[str]) -> list[str] | None:
        if not arguments or not isinstance(arguments[0], TCLWord):
            return None
        name = arguments[0].value
        if name not in defined_vars:
            return None
        if len(arguments) > 1:
            amount = _translate_argument(arguments[1], defined_vars)
            return None if amount is None else [f"{name} += {amount}"]
        return [f"{name} += 1"]


class AssertErrorStatementTranslator(StatementTranslator):
    def get_statement(self, arguments: list[TCLCommandArguments], defined_vars: set[str]) -> list[str] | None:
        if not arguments[1:]:
            return None
        pattern_argument, body_argument = arguments[0], arguments[1]
        if not isinstance(pattern_argument, (TCLDoubleQuotedWord, TCLBracesWord, TCLWord)):
            return None
        if not isinstance(body_argument, TCLBracesWord):
            return None
        pattern_regex = re.escape(pattern_argument.value).replace(r"\*", ".*").replace(r"\?", ".")
        body_commands = [c for c in TCLScript.read(iter(body_argument.value)).commands if c.name]
        if not body_commands:
            return None
        body_lines: list[str] = []
        for command in body_commands:
            statement = _translate_command_statement(command, defined_vars)
            if statement is None:
                return None
            body_lines.extend(statement)
        return (
            None
            if not body_lines
            else [
                f"with pytest.raises(Exception, match={pattern_regex!r}):",
                *[f"    {line}" for line in body_lines],
            ]
        )


class AfterStatementTranslator(StatementTranslator):
    def get_statement(self, arguments: list[TCLCommandArguments], defined_vars: set[str]) -> list[str] | None:
        if not arguments:
            return None
        ms = _translate_argument(arguments[0], defined_vars)
        return None if ms is None else [f"time.sleep({ms} / 1000)"]


class PutsStatementTranslator(StatementTranslator):
    def get_statement(self, arguments: list[TCLCommandArguments], defined_vars: set[str]) -> list[str] | None:
        return []


StatementTranslator.MAPPING.update(
    {
        "r": RStatementTranslator(),
        "set": SetStatementTranslator(),
        "assert_equal": AssertEqualStatementTranslator(),
        "assert_match": AssertMatchStatementTranslator(),
        "assert": AssertStatementTranslator(),
        "incr": IncrStatementTranslator(),
        "assert_error": AssertErrorStatementTranslator(),
        "after": AfterStatementTranslator(),
        "puts": PutsStatementTranslator(),
    }
)


def _translate_command_statement(command: TCLCommandWord, defined_vars: set[str]) -> list[str] | None:
    translator = StatementTranslator.MAPPING.get(command.name)
    if translator is None:
        return None
    return translator.get_statement(command.args, defined_vars)


class TCLBodyTranslator:
    def translate(self, body: TCLScript, expected: str | None) -> list[str]:
        commands = [c for c in body.commands if c.name]
        if not commands:
            if expected is not None:
                return [f"assert False  # expected: {expected!r}"]
            return []

        lines: list[str] = []
        defined_vars: set[str] = set()

        for i, command in enumerate(commands):
            is_last = i == len(commands) - 1

            if is_last and expected is not None:
                expr = _translate_command_expr(command, defined_vars)
                if expr is not None:
                    lines.append(f"assert {expr} == {expected!r}")
                    continue
            else:
                statement = _translate_command_statement(command, defined_vars)
                if statement is not None:
                    lines.extend(statement)
                    if command.name == "set" and isinstance(command.args[0], TCLWord):
                        defined_vars.add(command.args[0].value)
                    continue

            formatted = _format_command(command)
            first_line, *rest_lines = formatted.splitlines()
            lines.append(f"# TODO: {first_line}")
            lines.extend(f"#   {rest}" for rest in rest_lines)
            if is_last and expected is not None:
                lines.append("assert False")

        return lines


def _has_todos(lines: list[str]) -> bool:
    return any("# TODO:" in line for line in lines)


def _extract_todo_commands(lines: list[str]) -> list[str]:
    result = []
    for line in lines:
        if "# TODO:" not in line:
            continue
        rest = line[line.index("# TODO:") + len("# TODO:") :].strip()
        if rest:
            result.append(rest.split()[0])
    return result


@dataclass
class TCLTestFileGenerator:
    output: IO = field(default=sys.stdout)
    _todo_counter: Counter = field(default_factory=Counter)
    _total_tests: int = field(default=0)
    _translated_tests: int = field(default=0)
    _used_names: Counter = field(default_factory=Counter)

    @classmethod
    def collect_foreach_name_to_values(cls, foreach_command: TCLCommandForEach) -> dict[str, list]:
        foreach_name_to_values = defaultdict(list)

        for variable_names_list, variable_values_list in foreach_command.variables_names_and_values_lists:
            for value, name in zip(variable_values_list.words, cycle(variable_names_list)):
                foreach_name_to_values[name].append(value)

        return dict(foreach_name_to_values)

    @classmethod
    def generate_parametrize(cls, foreach_command: TCLCommandForEach) -> str:
        foreach_name_to_values = cls.collect_foreach_name_to_values(foreach_command)

        generated = "@pytest.mark.parametrize(["
        generated += ",".join([f'"{values_name}"' for values_name, values_list in foreach_name_to_values.items()])
        generated += "], ["

        values_tuples = []

        for args in zip_longest(
            *[values_list for values_name, values_list in foreach_name_to_values.items()], fillvalue=None
        ):
            values = []
            for value in args:
                if not value:
                    values.append('"""None"""')
                elif "\n" in value:
                    values.append(f'"""{value}"""')
                else:
                    values.append(f'"{value}"')

            values_tuples.append("(" + ",".join(values) + ")")

        generated += ",".join(values_tuples)
        generated += "])\n"

        return generated

    def generate_test(
        self,
        test_command: TCLCommandWord,
        if_expressions: list[str] | None = None,
        parametrizes: list[str] | None = None,
    ) -> None:
        self.output.write("\n\n")

        name = (
            test_command.args[0].value if isinstance(test_command.args[0], TCLBracesWord) else str(test_command.args[0])
        )

        translate_table = str.maketrans(
            {
                "/": "_or_",
                **{c: "_" for c in "{}\",#: -()<>=$'.,*&@!?|+~^%"},
            }
        )
        base_name = "test_" + re.sub(
            "_+", "_", re.sub(r"[^a-z0-9_]", "_", name.lower().translate(translate_table)).strip("_")
        )
        count = self._used_names[base_name]
        self._used_names[base_name] += 1
        test_name = base_name if count == 0 else f"{base_name}_{count}"

        body_arg = test_command.args[1] if len(test_command.args) > 1 else None
        expected_arg = test_command.args[2] if test_command.args[2:] else None

        body = TCLScript.read(iter(body_arg.value)) if isinstance(body_arg, TCLBracesWord) else None
        expected = expected_arg.value if isinstance(expected_arg, TCLBracesWord) else None

        if body is not None:
            lines = TCLBodyTranslator().translate(body, expected)
        else:
            lines = ["assert False"]

        self._total_tests += 1
        if _has_todos(lines):
            self._todo_counter.update(_extract_todo_commands(lines))
        else:
            self._translated_tests += 1

        if _has_todos(lines):
            self.output.write("@pytest.mark.xfail(reason='not implemented')\n")
        if if_expressions:
            for if_expression in if_expressions:
                self.output.write(f"@pytest.mark.skipif('', reason={if_expression!r})\n")
        if parametrizes:
            self.output.writelines(parametrizes)

        self.output.write(f"def {test_name}(r: ValkeyTestClient) -> None:\n")
        self.output.write('    """\n')
        self.output.write(textwrap.indent(_format_command(test_command), "    ") + "\n")
        self.output.write('    """\n')
        for line in lines:
            self.output.write(f"    {line}\n")

    def generate_comment(self, command: TCLCommandWord) -> None:
        self.output.write('\n\n"""\n')
        self.output.write(_format_command(command) + "\n")
        self.output.write('"""\n')

    def generate_tests(
        self, script: TCLScript, if_expressions: list[str] | None = None, foreach_commands: list[str] | None = None
    ) -> None:
        for command in script.commands:
            if isinstance(command, TCLCommandWord):
                match command.name:
                    case "test":
                        self.generate_test(command, if_expressions, foreach_commands)
                    case "if":
                        try:
                            if_command = TCLCommandIf.build(command.args, {})
                        except Exception:
                            self.generate_comment(command)
                            continue
                        _, body = if_command.if_part

                        if not any([c for c in body.commands if c.name == "test"]):
                            self.generate_comment(command)
                            continue

                        self.generate_tests(
                            body,
                            (if_expressions or []) + [_reconstruct_argument(command.args[0])],
                            foreach_commands,
                        )
                    case "foreach":
                        try:
                            foreach_command = TCLCommandForEach.build(command.args, {})
                        except Exception:
                            self.generate_comment(command)
                            continue

                        has_unresolved_values = any(
                            len(vl.words) == 0 for _, vl in foreach_command.variables_names_and_values_lists
                        )
                        if has_unresolved_values:
                            self.generate_comment(command)
                            continue

                        if not any([c for c in foreach_command.body.commands if c.name == "test"]):
                            self.generate_comment(command)
                            continue

                        self.generate_tests(
                            foreach_command.body,
                            if_expressions,
                            (foreach_commands or []) + [self.generate_parametrize(foreach_command)],
                        )
                    case "tags":
                        pass
                    case _:
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
        self.output.write("# ruff: noqa: PLR2004, F841, N806, RUF043\n")
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

    def generate_file(self, source_file_path: Path) -> None:
        with open(source_file_path, encoding="utf-8", errors="replace") as source_file:
            self.generate(source_file)


def _discover_tcl_files(tests_path: Path) -> list[Path]:
    return list(sorted(tests_path.rglob("*.tcl")))


def _tcl_path_to_python_path(tcl_file: Path, base_tcl_path: Path) -> Path:
    relative = tcl_file.relative_to(base_tcl_path)
    return relative.parent / f"test_{relative.stem}.py"
