from __future__ import annotations

import re
from typing import TYPE_CHECKING, ClassVar

if TYPE_CHECKING:
    from collections.abc import Callable

from pytcl.commands import TCLBracesWord, TCLScript
from pytcl.words import (
    TCLBracketWord,
    TCLCommandArguments,
    TCLCommandWord,
    TCLDoubleQuotedWord,
    TCLWord,
)

from valkey_tests_generator.argument_translators import ArgumentTranslator, ExpressionTranslator

StatementTranslatorType = type["StatementTranslator"]


class StatementTranslator:
    MAPPING: ClassVar[dict[str, StatementTranslator]] = {}

    def get_statement(self, arguments: list[TCLCommandArguments], defined_vars: set[str]) -> list[str] | None:
        raise NotImplementedError

    @classmethod
    def register(cls, key: str) -> Callable[[StatementTranslatorType], StatementTranslatorType]:
        def decorator(translator_cls: StatementTranslatorType) -> StatementTranslatorType:
            cls.MAPPING[key] = translator_cls()
            return translator_cls

        return decorator

    @classmethod
    def translate(cls, command: TCLCommandWord, defined_vars: set[str]) -> list[str] | None:
        translator = cls.MAPPING.get(command.name)
        if translator is None:
            return None
        return translator.get_statement(command.args, defined_vars)


@StatementTranslator.register("r")
class RStatementTranslator(StatementTranslator):
    def get_statement(self, arguments: list[TCLCommandArguments], defined_vars: set[str]) -> list[str] | None:
        expr = ArgumentTranslator.translate_r(arguments, defined_vars)
        return None if expr is None else [expr]


@StatementTranslator.register("set")
class SetStatementTranslator(StatementTranslator):
    def get_statement(self, arguments: list[TCLCommandArguments], defined_vars: set[str]) -> list[str] | None:
        if not arguments[1:]:
            return None
        name_argument = arguments[0]
        if not isinstance(name_argument, TCLWord) or "(" in name_argument.value:
            return None
        val = ArgumentTranslator.translate(arguments[1], defined_vars)
        return None if val is None else [f"{name_argument.value} = {val}"]


@StatementTranslator.register("assert_equal")
class AssertEqualStatementTranslator(StatementTranslator):
    def get_statement(self, arguments: list[TCLCommandArguments], defined_vars: set[str]) -> list[str] | None:
        if not arguments[1:]:
            return None
        a = ArgumentTranslator.translate(arguments[0], defined_vars)
        b = ArgumentTranslator.translate(arguments[1], defined_vars)
        return None if a is None or b is None else [f"assert {a} == {b}"]


@StatementTranslator.register("assert_match")
class AssertMatchStatementTranslator(StatementTranslator):
    def get_statement(self, arguments: list[TCLCommandArguments], defined_vars: set[str]) -> list[str] | None:
        if not arguments[1:]:
            return None
        pat = ArgumentTranslator.translate(arguments[0], defined_vars)
        val = ArgumentTranslator.translate(arguments[1], defined_vars)
        return None if pat is None or val is None else [f"assert fnmatch(str({val}), str({pat}))"]


@StatementTranslator.register("assert")
class AssertStatementTranslator(StatementTranslator):
    def get_statement(self, arguments: list[TCLCommandArguments], defined_vars: set[str]) -> list[str] | None:
        if not arguments or not isinstance(arguments[0], TCLBracketWord):
            return None
        inner = [c for c in arguments[0].script.commands if c.name]
        if len(inner) != 1:
            return None
        expr = ExpressionTranslator.translate(inner[0], defined_vars)
        return None if expr is None else [f"assert {expr}"]


@StatementTranslator.register("incr")
class IncrStatementTranslator(StatementTranslator):
    def get_statement(self, arguments: list[TCLCommandArguments], defined_vars: set[str]) -> list[str] | None:
        if not arguments or not isinstance(arguments[0], TCLWord):
            return None
        name = arguments[0].value
        if name not in defined_vars:
            return None
        if len(arguments) > 1:
            amount = ArgumentTranslator.translate(arguments[1], defined_vars)
            return None if amount is None else [f"{name} += {amount}"]
        return [f"{name} += 1"]


@StatementTranslator.register("assert_error")
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
            statement = StatementTranslator.translate(command, defined_vars)
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


@StatementTranslator.register("after")
class AfterStatementTranslator(StatementTranslator):
    def get_statement(self, arguments: list[TCLCommandArguments], defined_vars: set[str]) -> list[str] | None:
        if not arguments:
            return None
        ms = ArgumentTranslator.translate(arguments[0], defined_vars)
        return None if ms is None else [f"time.sleep({ms} / 1000)"]


@StatementTranslator.register("puts")
class PutsStatementTranslator(StatementTranslator):
    def get_statement(self, arguments: list[TCLCommandArguments], defined_vars: set[str]) -> list[str] | None:
        return []


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
                expr = ExpressionTranslator.translate(command, defined_vars)
                if expr is not None:
                    lines.append(f"assert {expr} == {expected!r}")
                    continue
            else:
                statement = StatementTranslator.translate(command, defined_vars)
                if statement is not None:
                    lines.extend(statement)
                    if command.name == "set" and isinstance(command.args[0], TCLWord):
                        defined_vars.add(command.args[0].value)
                    continue

            formatted = command.formatted()
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
