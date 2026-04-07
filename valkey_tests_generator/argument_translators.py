from __future__ import annotations

import builtins
import keyword
import math
import re
from typing import TYPE_CHECKING, ClassVar

if TYPE_CHECKING:
    from collections.abc import Callable

from pytcl.commands import TCLBracesWord
from pytcl.words import (
    TCLBracketWord,
    TCLCommandArguments,
    TCLCommandWord,
    TCLDoubleQuotedWord,
    TCLVariableSubstitutionWord,
    TCLWord,
)

ArgumentTranslatorType = type["ArgumentTranslator"]
ExpressionTranslatorType = type["ExpressionTranslator"]

# Collects unknown function names encountered during translation of one file.
# Managed by TCLTestFileGenerator: call clear() before each file, read after.
collected_stubs: set[str] = set()


_AMBIGUOUS_VAR_RENAMES = {"l": "L", "O": "o", "I": "i"}


def _safe_var_name(name: str) -> str:
    """Rename ambiguous single-letter variable names to avoid E741."""
    return _AMBIGUOUS_VAR_RENAMES.get(name, name)


def _to_snake_case(name: str) -> str:
    s = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", name)
    s = re.sub(r"([a-z\d])([A-Z])", r"\1_\2", s)
    return s.lower()


def _safe_stub_name(name: str) -> str:
    """Return a Python-safe snake_case name for a stub, avoiding builtins and keywords."""
    name = _to_snake_case(name)
    if keyword.iskeyword(name) or hasattr(builtins, name):
        return name + "_"
    return name


class ArgumentTranslator:
    MAPPING: ClassVar[dict[type, ArgumentTranslator]] = {}

    def get_translation(self, argument: TCLCommandArguments, defined_vars: set[str]) -> str | None:
        raise NotImplementedError

    @classmethod
    def register(cls, key: type) -> Callable[[ArgumentTranslatorType], ArgumentTranslatorType]:
        def decorator(translator_cls: ArgumentTranslatorType) -> ArgumentTranslatorType:
            cls.MAPPING[key] = translator_cls()
            return translator_cls

        return decorator

    @classmethod
    def translate(cls, argument: TCLCommandArguments, defined_vars: set[str]) -> str | None:
        translator = cls.MAPPING.get(type(argument))
        if translator is None:
            return None
        return translator.get_translation(argument, defined_vars)

    @classmethod
    def translate_r(cls, arguments: list[TCLCommandArguments], defined_vars: set[str]) -> str | None:
        if not arguments:
            return None
        subcmd = cls.translate(arguments[0], defined_vars)
        if subcmd is None:
            return None
        rest = []
        for argument in arguments[1:]:
            t = cls.translate(argument, defined_vars)
            if t is None:
                return None
            rest.append(t)
        return f"r.run({', '.join([subcmd, *rest])})"

    @classmethod
    def translate_all(cls, arguments: list[TCLCommandArguments], defined_vars: set[str]) -> list[str] | None:
        translated = [cls.translate(a, defined_vars) for a in arguments]
        if any(t is None for t in translated):
            return None
        return [t for t in translated if t is not None]


class ExpressionTranslator:
    MAPPING: ClassVar[dict[str, ExpressionTranslator]] = {}

    def get_expression(self, arguments: list[TCLCommandArguments], defined_vars: set[str]) -> str | None:
        raise NotImplementedError

    @classmethod
    def register(cls, key: str) -> Callable[[ExpressionTranslatorType], ExpressionTranslatorType]:
        def decorator(translator_cls: ExpressionTranslatorType) -> ExpressionTranslatorType:
            cls.MAPPING[key] = translator_cls()
            return translator_cls

        return decorator

    @classmethod
    def translate(cls, command: TCLCommandWord, defined_vars: set[str]) -> str | None:
        translator = cls.MAPPING.get(command.name)
        if translator is None:
            return None
        return translator.get_expression(command.args, defined_vars)


@ArgumentTranslator.register(TCLVariableSubstitutionWord)
class VariableSubstitutionArgumentTranslator(ArgumentTranslator):
    def get_translation(self, argument: TCLCommandArguments, defined_vars: set[str]) -> str | None:
        assert isinstance(argument, TCLVariableSubstitutionWord)
        if "::" in argument.variable_name or argument.variable_name not in defined_vars:
            return None
        return _safe_var_name(argument.variable_name)


@ArgumentTranslator.register(TCLBracketWord)
class BracketArgumentTranslator(ArgumentTranslator):
    def get_translation(self, argument: TCLCommandArguments, defined_vars: set[str]) -> str | None:
        assert isinstance(argument, TCLBracketWord)
        commands = [c for c in argument.script.commands if c.name]
        if len(commands) != 1:
            return None
        result = ExpressionTranslator.translate(commands[0], defined_vars)
        if result is not None:
            return result
        # Fallback: unknown function call with translatable args → emit stub
        name = commands[0].name
        if name.isidentifier():
            args = ArgumentTranslator.translate_all(commands[0].args, defined_vars)
            if args is not None:
                safe_name = _safe_stub_name(name)
                collected_stubs.add(safe_name)
                return f"{safe_name}({', '.join(args)})"
        # Variable-as-command: [$var subcmd args] → var.run(subcmd, args)
        if name.startswith("$"):
            var_name = name[1:]
            if var_name.isidentifier() and var_name in defined_vars and commands[0].args:
                subcmd_arg = commands[0].args[0]
                if isinstance(subcmd_arg, TCLWord):
                    rest = ArgumentTranslator.translate_all(commands[0].args[1:], defined_vars)
                    if rest is not None:
                        return f"{_safe_var_name(var_name)}.run({', '.join([repr(subcmd_arg.value), *rest])})"
        return None


@ArgumentTranslator.register(TCLBracesWord)
class BracesArgumentTranslator(ArgumentTranslator):
    def get_translation(self, argument: TCLCommandArguments, defined_vars: set[str]) -> str | None:
        assert isinstance(argument, TCLBracesWord)
        return repr(argument.value)


_SIMPLE_ESCAPES: dict[str, str] = {"a": "\\a", "b": "\\b", "f": "\\f", "n": "\\n", "r": "\\r", "t": "\\t", "v": "\\v"}


def _translate_double_quoted(raw: str, defined_vars: set[str]) -> str | None:
    """Translate a TCL double-quoted string value to a Python string or f-string literal."""
    parts: list[str] = []
    has_sub = False
    i = 0
    while i < len(raw):
        c = raw[i]
        if c == "$":
            i += 1
            if i >= len(raw) or raw[i] in (" ", "\n", "$"):
                parts.append("$")
                continue
            if raw[i] == "{":
                end = raw.find("}", i + 1)
                if end == -1:
                    return None
                var_name = raw[i + 1 : end]
                i = end + 1
            else:
                j = i
                while j < len(raw) and (raw[j].isalnum() or raw[j] in ":_"):
                    j += 1
                var_name = raw[i:j]
                i = j
            if not var_name or "::" in var_name:
                return None
            if var_name not in defined_vars:
                return None
            parts.append("{" + _safe_var_name(var_name) + "}")
            has_sub = True
        elif c == "\\":
            i += 1
            if i >= len(raw):
                return None
            ec = raw[i]
            if ec in _SIMPLE_ESCAPES:
                parts.append(_SIMPLE_ESCAPES[ec])
                i += 1
            elif ec in "xuU":
                return None  # binary/unicode escape — too complex
            elif ec == "\n":
                parts.append(" ")
                i += 1
            else:
                parts.append(ec)
                i += 1
        elif c in "{}":
            parts.append(c + c)  # escape braces in f-strings
            i += 1
        elif c == "'":
            parts.append("\\'")
            i += 1
        elif c == "\\":
            parts.append("\\\\")
            i += 1
        else:
            parts.append(c)
            i += 1
    content = "".join(parts)
    return f"f'{content}'" if has_sub else repr(raw)


@ArgumentTranslator.register(TCLDoubleQuotedWord)
class DoubleQuotedArgumentTranslator(ArgumentTranslator):
    def get_translation(self, argument: TCLCommandArguments, defined_vars: set[str]) -> str | None:
        assert isinstance(argument, TCLDoubleQuotedWord)
        if "\\" in argument.value:
            # Binary/escape sequences handled by _translate_double_quoted
            return _translate_double_quoted(argument.value, defined_vars)
        if "$" not in argument.value:
            return repr(argument.value)
        return _translate_double_quoted(argument.value, defined_vars)


@ArgumentTranslator.register(TCLWord)
class WordArgumentTranslator(ArgumentTranslator):
    def get_translation(self, argument: TCLCommandArguments, defined_vars: set[str]) -> str | None:
        assert isinstance(argument, TCLWord)
        s = argument.value
        try:
            return str(int(s))
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


@ExpressionTranslator.register("set")
class SetExpressionTranslator(ExpressionTranslator):
    def get_expression(self, arguments: list[TCLCommandArguments], defined_vars: set[str]) -> str | None:
        if not arguments or not isinstance(arguments[0], TCLWord):
            return None
        name = arguments[0].value
        if len(arguments) == 1:
            # getter: [set varname] — return the variable if already in scope
            return _safe_var_name(name) if name in defined_vars else None
        # setter: [set varname value] — TCL returns the assigned value
        return ArgumentTranslator.translate(arguments[1], defined_vars)


@ExpressionTranslator.register("r")
class RExpressionTranslator(ExpressionTranslator):
    def get_expression(self, arguments: list[TCLCommandArguments], defined_vars: set[str]) -> str | None:
        return ArgumentTranslator.translate_r(arguments, defined_vars)


@ExpressionTranslator.register("valkey_deferring_client")
@ExpressionTranslator.register("valkey_client")
class ValkeyClientExpressionTranslator(ExpressionTranslator):
    def get_expression(self, arguments: list[TCLCommandArguments], defined_vars: set[str]) -> str | None:
        return "ValkeyTestClient.create_from(r)"


@ExpressionTranslator.register("list")
class ListExpressionTranslator(ExpressionTranslator):
    def get_expression(self, arguments: list[TCLCommandArguments], defined_vars: set[str]) -> str | None:
        parts = ArgumentTranslator.translate_all(arguments, defined_vars)
        return None if parts is None else f"[{', '.join(parts)}]"


@ExpressionTranslator.register("lindex")
class LIndexExpressionTranslator(ExpressionTranslator):
    def get_expression(self, arguments: list[TCLCommandArguments], defined_vars: set[str]) -> str | None:
        if len(arguments) != 2:
            return None
        args = ArgumentTranslator.translate_all(arguments, defined_vars)
        return None if args is None else f"{args[0]}[{args[1]}]"


@ExpressionTranslator.register("llength")
class LLengthExpressionTranslator(ExpressionTranslator):
    def get_expression(self, arguments: list[TCLCommandArguments], defined_vars: set[str]) -> str | None:
        if len(arguments) != 1:
            return None
        args = ArgumentTranslator.translate_all(arguments, defined_vars)
        return None if args is None else f"len({args[0]})"


@ExpressionTranslator.register("dict")
class DictSubcommandExpressionTranslator(ExpressionTranslator):
    SUBCOMMANDS: ClassVar[dict[str, ExpressionTranslator]] = {}

    @classmethod
    def register(cls, key: str) -> Callable[[ExpressionTranslatorType], ExpressionTranslatorType]:
        def decorator(translator_cls: ExpressionTranslatorType) -> ExpressionTranslatorType:
            cls.SUBCOMMANDS[key] = translator_cls()
            return translator_cls

        return decorator

    def get_expression(self, arguments: list[TCLCommandArguments], defined_vars: set[str]) -> str | None:
        if not arguments or not isinstance(arguments[0], TCLWord):
            return None
        sub = self.SUBCOMMANDS.get(arguments[0].value.lower())
        return None if sub is None else sub.get_expression(arguments[1:], defined_vars)


@DictSubcommandExpressionTranslator.register("get")
class DictGetExpressionTranslator(ExpressionTranslator):
    def get_expression(self, arguments: list[TCLCommandArguments], defined_vars: set[str]) -> str | None:
        if len(arguments) < 2:
            return None
        args = ArgumentTranslator.translate_all(arguments, defined_vars)
        if args is None:
            return None
        result = args[0]
        for key in args[1:]:
            result = f"{result}[{key}]"
        return result


@ExpressionTranslator.register("string")
class StringSubcommandExpressionTranslator(ExpressionTranslator):
    SUBCOMMANDS: ClassVar[dict[str, ExpressionTranslator]] = {}

    @classmethod
    def register(cls, key: str) -> Callable[[ExpressionTranslatorType], ExpressionTranslatorType]:
        def decorator(translator_cls: ExpressionTranslatorType) -> ExpressionTranslatorType:
            cls.SUBCOMMANDS[key] = translator_cls()
            return translator_cls

        return decorator

    def get_expression(self, arguments: list[TCLCommandArguments], defined_vars: set[str]) -> str | None:
        if not arguments or not isinstance(arguments[0], TCLWord):
            return None
        sub = self.SUBCOMMANDS.get(arguments[0].value.lower())
        return None if sub is None else sub.get_expression(arguments[1:], defined_vars)


@StringSubcommandExpressionTranslator.register("length")
class StringLengthExpressionTranslator(ExpressionTranslator):
    def get_expression(self, arguments: list[TCLCommandArguments], defined_vars: set[str]) -> str | None:
        if len(arguments) != 1:
            return None
        args = ArgumentTranslator.translate_all(arguments, defined_vars)
        return None if args is None else f"len({args[0]})"
