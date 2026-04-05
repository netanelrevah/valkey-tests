from __future__ import annotations

import math
from typing import ClassVar

from pytcl.commands import TCLBracesWord
from pytcl.words import (
    TCLBracketWord,
    TCLCommandArguments,
    TCLCommandWord,
    TCLDoubleQuotedWord,
    TCLVariableSubstitutionWord,
    TCLWord,
)


class ArgumentTranslator:
    MAPPING: ClassVar[dict[type, ArgumentTranslator]] = {}

    def get_translation(self, argument: TCLCommandArguments, defined_vars: set[str]) -> str | None:
        raise NotImplementedError


class VariableSubstitutionArgumentTranslator(ArgumentTranslator):
    def get_translation(self, argument: TCLCommandArguments, defined_vars: set[str]) -> str | None:
        assert isinstance(argument, TCLVariableSubstitutionWord)
        if "::" in argument.variable_name or argument.variable_name not in defined_vars:
            return None
        return argument.variable_name


class BracketArgumentTranslator(ArgumentTranslator):
    def get_translation(self, argument: TCLCommandArguments, defined_vars: set[str]) -> str | None:
        assert isinstance(argument, TCLBracketWord)
        commands = [c for c in argument.script.commands if c.name]
        if len(commands) != 1:
            return None
        return _translate_command_expr(commands[0], defined_vars)


class BracesArgumentTranslator(ArgumentTranslator):
    def get_translation(self, argument: TCLCommandArguments, defined_vars: set[str]) -> str | None:
        assert isinstance(argument, TCLBracesWord)
        return repr(argument.value)


class DoubleQuotedArgumentTranslator(ArgumentTranslator):
    def get_translation(self, argument: TCLCommandArguments, defined_vars: set[str]) -> str | None:
        assert isinstance(argument, TCLDoubleQuotedWord)
        if "$" in argument.value or "\\" in argument.value:
            return None
        return repr(argument.value)


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


ArgumentTranslator.MAPPING.update(
    {
        TCLVariableSubstitutionWord: VariableSubstitutionArgumentTranslator(),
        TCLBracketWord: BracketArgumentTranslator(),
        TCLBracesWord: BracesArgumentTranslator(),
        TCLDoubleQuotedWord: DoubleQuotedArgumentTranslator(),
        TCLWord: WordArgumentTranslator(),
    }
)


def _translate_argument(argument: TCLCommandArguments, defined_vars: set[str]) -> str | None:
    translator = ArgumentTranslator.MAPPING.get(type(argument))
    if translator is None:
        return None
    return translator.get_translation(argument, defined_vars)


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
