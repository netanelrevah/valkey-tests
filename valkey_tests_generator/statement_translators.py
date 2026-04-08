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

from valkey_tests_generator.argument_translators import (
    ArgumentTranslator,
    ExpressionTranslator,
    _safe_stub_name,
    _safe_var_name,
    collected_stubs,
)

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


@StatementTranslator.register("variable")
@StatementTranslator.register("set")
class SetStatementTranslator(StatementTranslator):
    def get_statement(self, arguments: list[TCLCommandArguments], defined_vars: set[str]) -> list[str] | None:
        if not arguments[1:]:
            return None
        name_argument = arguments[0]
        if not isinstance(name_argument, TCLWord) or not name_argument.value.isidentifier():
            return None
        value_arg = arguments[1]
        if isinstance(value_arg, TCLBracesWord) and not value_arg.value.strip():
            return [f"{_safe_var_name(name_argument.value)} = []"]
        val = ArgumentTranslator.translate(value_arg, defined_vars)
        return None if val is None else [f"{_safe_var_name(name_argument.value)} = {val}"]


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


@StatementTranslator.register("assert_morethan")
class AssertMoreThanStatementTranslator(StatementTranslator):
    def get_statement(self, arguments: list[TCLCommandArguments], defined_vars: set[str]) -> list[str] | None:
        if not arguments[1:]:
            return None
        a = ArgumentTranslator.translate(arguments[0], defined_vars)
        b = ArgumentTranslator.translate(arguments[1], defined_vars)
        return None if a is None or b is None else [f"assert {a} > {b}"]


@StatementTranslator.register("assert_lessthan")
class AssertLessThanStatementTranslator(StatementTranslator):
    def get_statement(self, arguments: list[TCLCommandArguments], defined_vars: set[str]) -> list[str] | None:
        if not arguments[1:]:
            return None
        a = ArgumentTranslator.translate(arguments[0], defined_vars)
        b = ArgumentTranslator.translate(arguments[1], defined_vars)
        return None if a is None or b is None else [f"assert {a} < {b}"]


@StatementTranslator.register("assert_morethan_equal")
class AssertMoreThanEqualStatementTranslator(StatementTranslator):
    def get_statement(self, arguments: list[TCLCommandArguments], defined_vars: set[str]) -> list[str] | None:
        if not arguments[1:]:
            return None
        a = ArgumentTranslator.translate(arguments[0], defined_vars)
        b = ArgumentTranslator.translate(arguments[1], defined_vars)
        return None if a is None or b is None else [f"assert {a} >= {b}"]


@StatementTranslator.register("assert_lessthan_equal")
class AssertLessThanEqualStatementTranslator(StatementTranslator):
    def get_statement(self, arguments: list[TCLCommandArguments], defined_vars: set[str]) -> list[str] | None:
        if not arguments[1:]:
            return None
        a = ArgumentTranslator.translate(arguments[0], defined_vars)
        b = ArgumentTranslator.translate(arguments[1], defined_vars)
        return None if a is None or b is None else [f"assert {a} <= {b}"]


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


@StatementTranslator.register("lappend")
class LAppendStatementTranslator(StatementTranslator):
    def get_statement(self, arguments: list[TCLCommandArguments], defined_vars: set[str]) -> list[str] | None:
        if len(arguments) < 2:
            return None
        if not isinstance(arguments[0], TCLWord) or arguments[0].value not in defined_vars:
            return None
        var = _safe_var_name(arguments[0].value)
        lines = []
        for val_arg in arguments[1:]:
            val = ArgumentTranslator.translate(val_arg, defined_vars)
            if val is None:
                return None
            lines.append(f"{var}.append({val})")
        return lines


@StatementTranslator.register("incr")
class IncrStatementTranslator(StatementTranslator):
    def get_statement(self, arguments: list[TCLCommandArguments], defined_vars: set[str]) -> list[str] | None:
        if not arguments or not isinstance(arguments[0], TCLWord):
            return None
        name = arguments[0].value
        if name not in defined_vars:
            return None
        safe = _safe_var_name(name)
        if len(arguments) > 1:
            amount = ArgumentTranslator.translate(arguments[1], defined_vars)
            return None if amount is None else [f"{safe} += {amount}"]
        return [f"{safe} += 1"]


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


@StatementTranslator.register("wait_for_condition")
class WaitForConditionStatementTranslator(StatementTranslator):
    def get_statement(self, arguments: list[TCLCommandArguments], defined_vars: set[str]) -> list[str] | None:
        if len(arguments) < 3:
            return None
        retries = ArgumentTranslator.translate(arguments[0], defined_vars)
        delay = ArgumentTranslator.translate(arguments[1], defined_vars)
        if retries is None or delay is None:
            return None
        condition_arg = arguments[2]
        if not isinstance(condition_arg, TCLBracesWord):
            return None
        try:
            condition_expr = TCLExpression.build([condition_arg], {})
        except Exception:
            return None
        cond_str = _translate_tcl_expression(condition_expr, defined_vars)
        if cond_str is None:
            return None
        # Translate else body as a lambda: wait_for_condition(n, ms, lambda: cond, lambda: else_body)
        else_lambda: str | None = None
        if len(arguments) >= 5 and isinstance(arguments[4], TCLBracesWord):
            try:
                else_script = TCLScript.read(iter(arguments[4].value))
                else_lines = TCLBodyTranslator().translate(else_script, None, initial_vars=defined_vars)
                if len(else_lines) == 1 and not else_lines[0].startswith("#"):
                    else_lambda = f"lambda: {else_lines[0]}"
            except Exception:
                pass
        collected_stubs.add("wait_for_condition")
        if else_lambda is not None:
            return [f"wait_for_condition({retries}, {delay}, lambda: {cond_str}, {else_lambda})"]
        return [f"wait_for_condition({retries}, {delay}, lambda: {cond_str})"]


def _collect_set_vars(script: TCLScript) -> set[str]:
    """Return names of all top-level set-command variables in a script."""
    result: set[str] = set()
    for cmd in script.commands:
        if cmd.name == "set" and cmd.args and isinstance(cmd.args[0], TCLWord):
            result.add(cmd.args[0].value)
    return result


def _collect_lappend_vars_deep(script: TCLScript) -> set[str]:
    """Return all variable names used with lappend anywhere in the script (recursively)."""
    result: set[str] = set()
    for cmd in script.commands:
        if cmd.name == "lappend" and cmd.args and isinstance(cmd.args[0], TCLWord):
            result.add(cmd.args[0].value)
        # Recurse into braces body arguments (while/for/if bodies etc.)
        for arg in cmd.args:
            if isinstance(arg, TCLBracesWord) and arg.value.strip():
                try:
                    sub = TCLScript.read(iter(arg.value))
                    result.update(_collect_lappend_vars_deep(sub))
                except Exception:
                    pass
    return result


def _collect_list_vars(script: TCLScript) -> set[str]:
    """Return names of vars initialized with `set var {}` and later used with lappend (deep)."""
    empty_set: set[str] = set()
    for cmd in script.commands:
        if cmd.name == "set" and len(cmd.args) == 2 and isinstance(cmd.args[0], TCLWord):
            if isinstance(cmd.args[1], TCLBracesWord) and cmd.args[1].value == "":
                empty_set.add(cmd.args[0].value)
    lappend_vars = _collect_lappend_vars_deep(script)
    return empty_set & lappend_vars


class TCLBodyTranslator:
    def translate(self, body: TCLScript, expected: str | None, initial_vars: set[str] | None = None) -> list[str]:
        commands = [c for c in body.commands if c.name]
        if not commands:
            return [f"assert False  # expected: {expected!r}"] if expected is not None else []

        defined_vars: set[str] = set(initial_vars) if initial_vars else set()
        list_vars = _collect_list_vars(body)
        lines: list[str] = []

        for i, command in enumerate(commands):
            is_last = i == len(commands) - 1
            result = self._translate_command(command, defined_vars, list_vars, is_last, expected)
            lines.extend(result if result is not None else self._make_todo(command, is_last, expected))

        return lines

    def _translate_command(
        self,
        command: TCLCommandWord,
        defined_vars: set[str],
        list_vars: set[str],
        is_last: bool,
        expected: str | None,
    ) -> list[str] | None:
        if is_last and expected:
            result = self._try_expression_assert(command, defined_vars, expected)
            if result is not None:
                return result

        for attempt in [
            lambda: self._try_list_init(command, defined_vars, list_vars),
            lambda: self._try_statement(command, defined_vars),
            lambda: self._try_stub_call(command, defined_vars),
            lambda: self._try_var_command(command, defined_vars),
        ]:
            result = attempt()
            if result is not None:
                return result

        return None

    @classmethod
    def _try_expression_assert(cls, command: TCLCommandWord, defined_vars: set[str], expected: str) -> list[str] | None:
        expr = ExpressionTranslator.translate(command, defined_vars)
        if expr is None:
            return None
        if any(c in expected for c in "*?["):
            return [f"assert fnmatch(str({expr}), {expected!r})"]
        return [f"assert {expr} == {expected!r}"]

    @classmethod
    def _try_list_init(cls, command: TCLCommandWord, defined_vars: set[str], list_vars: set[str]) -> list[str] | None:
        if (
            command.name != "set"
            or len(command.args) != 2
            or not isinstance(command.args[0], TCLWord)
            or command.args[0].value not in list_vars
            or not isinstance(command.args[1], TCLBracesWord)
            or command.args[1].value != ""
        ):
            return None
        var = _safe_var_name(command.args[0].value)
        defined_vars.add(command.args[0].value)
        return [f"{var} = []"]

    @classmethod
    def _try_statement(cls, command: TCLCommandWord, defined_vars: set[str]) -> list[str] | None:
        result = StatementTranslator.translate(command, defined_vars)
        if result is None:
            return None
        cls._update_scope_after_statement(command, defined_vars)
        return result

    @classmethod
    def _update_scope_after_statement(cls, command: TCLCommandWord, defined_vars: set[str]) -> None:
        if command.name in ("set", "variable") and isinstance(command.args[0], TCLWord):
            defined_vars.add(command.args[0].value)
        elif command.name == "catch" and len(command.args) > 1 and isinstance(command.args[1], TCLWord):
            defined_vars.add(command.args[1].value)
        elif command.name == "if":
            try:
                if_cmd = TCLCommandIf.build(command.args, {})
                _, if_body = if_cmd.if_part
                defined_vars.update(_collect_set_vars(if_body))
                for _, elif_body in if_cmd.elseif_parts:
                    defined_vars.update(_collect_set_vars(elif_body))
                if if_cmd.else_part is not None:
                    defined_vars.update(_collect_set_vars(if_cmd.else_part))
            except Exception:
                pass
        elif command.name == "for":
            try:
                for_cmd = TCLCommandFor.build(command.args, {})
                for cmd in for_cmd.init.commands:
                    if cmd.name in ("set", "variable") and cmd.args and isinstance(cmd.args[0], TCLWord):
                        defined_vars.add(cmd.args[0].value)
            except Exception:
                pass

    @classmethod
    def _try_stub_call(cls, command: TCLCommandWord, defined_vars: set[str]) -> list[str] | None:
        if not command.name.isidentifier():
            return None
        args = ArgumentTranslator.translate_all(command.args, defined_vars)
        if args is None:
            return None
        safe_name = _safe_stub_name(command.name)
        collected_stubs.add(safe_name)
        return [f"{safe_name}({', '.join(args)})"]

    @classmethod
    def _try_var_command(cls, command: TCLCommandWord, defined_vars: set[str]) -> list[str] | None:
        if not command.name.startswith("$"):
            return None
        var_name = command.name[1:]
        if not var_name.isidentifier() or var_name not in defined_vars or not command.args:
            return None
        subcmd_arg = command.args[0]
        if not isinstance(subcmd_arg, TCLWord):
            return None
        rest = ArgumentTranslator.translate_all(command.args[1:], defined_vars)
        if rest is None:
            return None
        return [f"{_safe_var_name(var_name)}.run({', '.join([repr(subcmd_arg.value), *rest])})"]

    @classmethod
    def _make_todo(cls, command: TCLCommandWord, is_last: bool, expected: str | None) -> list[str]:
        formatted = command.formatted()
        first_line, *rest_lines = formatted.splitlines()
        lines = [f"# TODO: {first_line}", *[f"#   {rest}" for rest in rest_lines]]
        if is_last and expected:
            lines.append("assert False")
        return lines


_BINARY_OPERATORS = {"==", "!=", "<", ">", "<=", ">=", "+", "-", "*", "/", "%", "**", "<<", ">>", "|", "&", "^"}
_BINARY_OPERATOR_MAP = {"||": "or", "&&": "and", "eq": "==", "ne": "!=", **{op: op for op in _BINARY_OPERATORS}}
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
        body_lines = self._translate_body(arguments[0], catch_command, defined_vars)
        if body_lines is None:
            return None
        if _has_todos(body_lines) or not body_lines:
            return None
        if var_name is None:
            return ["try:", *[f"    {line}" for line in body_lines], "except Exception:", "    pass"]
        safe_var = _safe_var_name(var_name)
        *preceding, last = body_lines
        _stmt_prefixes = ("assert ", "if ", "for ", "while ", "try:", "with ", "return ", "pass")
        assigns_var = not any(last.startswith(p) for p in _stmt_prefixes)
        try_body = [*preceding, f"{safe_var} = {last}"] if assigns_var else body_lines
        init = [] if assigns_var else [f"{safe_var} = None"]
        return [
            *init,
            "try:",
            *[f"    {line}" for line in try_body],
            "except Exception as _catch_err:",
            f"    {safe_var} = str(_catch_err)",
        ]

    @classmethod
    def _translate_body(
        cls,
        body_arg: TCLCommandArguments,
        catch_command: TCLCommandCatch,
        defined_vars: set[str],
    ) -> list[str] | None:
        if isinstance(body_arg, TCLBracesWord):
            stripped = body_arg.value.strip()
            if stripped.startswith("[") and stripped.endswith("]"):
                inner_script = TCLScript.read(iter(stripped[1:-1]))
                bracket = TCLBracketWord(script=inner_script)
                expr = ArgumentTranslator.translate(bracket, defined_vars)
                return [expr] if expr is not None else None
        lines = TCLBodyTranslator().translate(catch_command.body, None, initial_vars=defined_vars)
        return None if _has_todos(lines) or not lines else lines


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
