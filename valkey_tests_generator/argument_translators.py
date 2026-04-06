from __future__ import annotations

import math
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
        return argument.variable_name


@ArgumentTranslator.register(TCLBracketWord)
class BracketArgumentTranslator(ArgumentTranslator):
    def get_translation(self, argument: TCLCommandArguments, defined_vars: set[str]) -> str | None:
        assert isinstance(argument, TCLBracketWord)
        commands = [c for c in argument.script.commands if c.name]
        if len(commands) != 1:
            return None
        return ExpressionTranslator.translate(commands[0], defined_vars)


@ArgumentTranslator.register(TCLBracesWord)
class BracesArgumentTranslator(ArgumentTranslator):
    def get_translation(self, argument: TCLCommandArguments, defined_vars: set[str]) -> str | None:
        assert isinstance(argument, TCLBracesWord)
        return repr(argument.value)


@ArgumentTranslator.register(TCLDoubleQuotedWord)
class DoubleQuotedArgumentTranslator(ArgumentTranslator):
    def get_translation(self, argument: TCLCommandArguments, defined_vars: set[str]) -> str | None:
        assert isinstance(argument, TCLDoubleQuotedWord)
        if "$" in argument.value or "\\" in argument.value:
            return None
        return repr(argument.value)


@ArgumentTranslator.register(TCLWord)
class WordArgumentTranslator(ArgumentTranslator):
    def get_translation(self, argument: TCLCommandArguments, defined_vars: set[str]) -> str | None:
        assert isinstance(argument, TCLWord)
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


@ExpressionTranslator.register("r")
class RExpressionTranslator(ExpressionTranslator):
    def get_expression(self, arguments: list[TCLCommandArguments], defined_vars: set[str]) -> str | None:
        return ArgumentTranslator.translate_r(arguments, defined_vars)


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
