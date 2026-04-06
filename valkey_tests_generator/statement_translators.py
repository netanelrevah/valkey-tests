from __future__ import annotations

import re
from typing import TYPE_CHECKING, ClassVar

if TYPE_CHECKING:
    from collections.abc import Callable

from pytcl.commands import TCLBracesWord, TCLCommandCatch, TCLCommandFor, TCLCommandIf, TCLExpression, TCLScript
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
        if not arguments:
            return None
        argument = arguments[0]
        if isinstance(argument, TCLBracketWord):
            inner = [c for c in argument.script.commands if c.name]
            if len(inner) != 1:
                return None
            expr = ExpressionTranslator.translate(inner[0], defined_vars)
            return None if expr is None else [f"assert {expr}"]
        if isinstance(argument, TCLBracesWord):
            try:
                expression = TCLExpression.build([argument], {})
            except Exception:
                return None
            expr = _translate_tcl_expression(expression, defined_vars)
            return None if expr is None else [f"assert {expr}"]
        return None


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
    def translate(self, body: TCLScript, expected: str | None, initial_vars: set[str] | None = None) -> list[str]:
        commands = [c for c in body.commands if c.name]
        if not commands:
            if expected is not None:
                return [f"assert False  # expected: {expected!r}"]
            return []

        lines: list[str] = []
        defined_vars: set[str] = set(initial_vars) if initial_vars else set()

        for i, command in enumerate(commands):
            is_last = i == len(commands) - 1

            if is_last and expected:
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
                    elif command.name == "catch" and len(command.args) > 1 and isinstance(command.args[1], TCLWord):
                        defined_vars.add(command.args[1].value)
                    continue

            formatted = command.formatted()
            first_line, *rest_lines = formatted.splitlines()
            lines.append(f"# TODO: {first_line}")
            lines.extend(f"#   {rest}" for rest in rest_lines)
            if is_last and expected:
                lines.append("assert False")

        return lines


_BINARY_OPERATORS = {"==", "!=", "<", ">", "<=", ">=", "+", "-", "*", "/", "%", "**", "<<", ">>", "|", "&", "^"}
_BINARY_OPERATOR_MAP = {"||": "or", "&&": "and", **{op: op for op in _BINARY_OPERATORS}}
_ALL_OPERATORS = _BINARY_OPERATOR_MAP | {"!": "not ", "~": "~"}


def _translate_str_literal(token: str) -> str | None:
    if any(c in token for c in "()$"):
        return None
    try:
        int(token)
        return token
    except ValueError:
        pass
    try:
        float(token)
        return token
    except ValueError:
        pass
    return repr(token)


def _translate_tcl_expression(expression: TCLExpression, defined_vars: set[str]) -> str | None:
    stack: list[str] = []
    for token in expression.postfix:
        if isinstance(token, str):
            if token not in _ALL_OPERATORS:
                literal = _translate_str_literal(token)
                if literal is None:
                    return None
                stack.append(literal)
            elif token == "!":
                if not stack:
                    return None
                stack.append(f"not {stack.pop()}")
            elif token == "~":
                if not stack:
                    return None
                stack.append(f"~{stack.pop()}")
            elif token in _BINARY_OPERATOR_MAP:
                if len(stack) < 2:
                    return None
                right, left = stack.pop(), stack.pop()
                stack.append(f"({left} {_BINARY_OPERATOR_MAP[token]} {right})")
            else:
                return None
        else:
            translated = ArgumentTranslator.translate(token, defined_vars)
            if translated is None:
                return None
            stack.append(translated)
    if len(stack) != 1:
        return None
    result = stack[0]
    return result[1:-1] if result.startswith("(") and result.endswith(")") else result


@StatementTranslator.register("catch")
class CatchStatementTranslator(StatementTranslator):
    def get_statement(self, arguments: list[TCLCommandArguments], defined_vars: set[str]) -> list[str] | None:
        try:
            catch_command = TCLCommandCatch.build(arguments, {})
        except ValueError:
            return None
        var_name = catch_command.var_name
        body_commands = [c for c in catch_command.body.commands if c.name]
        if not body_commands:
            return None
        body_lines: list[str] = []
        for command in body_commands[:-1]:
            statement = StatementTranslator.translate(command, defined_vars)
            if statement is None:
                return None
            body_lines.extend(statement)
        last_expr = ExpressionTranslator.translate(body_commands[-1], defined_vars)
        if last_expr is None:
            return None
        if var_name is not None:
            body_lines.append(f"{var_name} = {last_expr}")
            return [
                "try:",
                *[f"    {line}" for line in body_lines],
                "except Exception as _catch_err:",
                f"    {var_name} = str(_catch_err)",
            ]
        body_lines.append(last_expr)
        return [
            "try:",
            *[f"    {line}" for line in body_lines],
            "except Exception:",
            "    pass",
        ]


@StatementTranslator.register("if")
class IfStatementTranslator(StatementTranslator):
    def get_statement(self, arguments: list[TCLCommandArguments], defined_vars: set[str]) -> list[str] | None:
        try:
            if_command = TCLCommandIf.build(arguments, {})
        except ValueError:
            return None

        lines: list[str] = []
        for keyword, (condition, body) in [("if", if_command.if_part), *[("elif", p) for p in if_command.elseif_parts]]:
            cond_str = _translate_tcl_expression(condition, defined_vars)
            if cond_str is None:
                return None
            body_lines = TCLBodyTranslator().translate(body, None)
            if _has_todos(body_lines):
                return None
            lines.append(f"{keyword} {cond_str}:")
            if body_lines:
                lines.extend(f"    {line}" for line in body_lines)
            else:
                lines.append("    pass")

        if if_command.else_part is not None:
            body_lines = TCLBodyTranslator().translate(if_command.else_part, None)
            if _has_todos(body_lines):
                return None
            lines.append("else:")
            if body_lines:
                lines.extend(f"    {line}" for line in body_lines)
            else:
                lines.append("    pass")

        return lines


@StatementTranslator.register("for")
class ForStatementTranslator(StatementTranslator):
    def get_statement(self, arguments: list[TCLCommandArguments], defined_vars: set[str]) -> list[str] | None:
        try:
            for_command = TCLCommandFor.build(arguments, {})
        except Exception:
            return None

        # Translate init script as assignment statements
        init_commands = [c for c in for_command.init.commands if c.name]
        init_lines: list[str] = []
        loop_vars: set[str] = set()
        for command in init_commands:
            statement = StatementTranslator.translate(command, defined_vars)
            if statement is None:
                return None
            init_lines.extend(statement)
            if command.name == "set" and len(command.args) >= 1 and isinstance(command.args[0], TCLWord):
                loop_vars.add(command.args[0].value)

        body_vars = defined_vars | loop_vars

        # Translate condition
        cond_str = _translate_tcl_expression(for_command.condition, body_vars)
        if cond_str is None:
            return None

        # Translate step script
        step_commands = [c for c in for_command.step.commands if c.name]
        step_lines: list[str] = []
        for command in step_commands:
            statement = StatementTranslator.translate(command, body_vars)
            if statement is None:
                return None
            step_lines.extend(statement)

        # Translate body (loop vars are in scope)
        body_lines = TCLBodyTranslator().translate(for_command.body, None, initial_vars=body_vars)
        if _has_todos(body_lines):
            return None

        lines: list[str] = [*init_lines, f"while {cond_str}:"]
        if body_lines:
            lines.extend(f"    {line}" for line in body_lines)
        else:
            lines.append("    pass")
        lines.extend(f"    {line}" for line in step_lines)
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
