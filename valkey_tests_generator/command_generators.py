from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar, Protocol, cast

from pytcl.commands import TCLCommandForEach, TCLCommandIf
from pytcl.words import TCLCommandWord, TCLVariableSubstitutionWord, TCLWord

if TYPE_CHECKING:
    from pytcl.commands import TCLScript


def _collect_set_values(script: TCLScript) -> dict[str, str]:
    """Return {var_name: raw_value} for all top-level set commands in a script."""
    result: dict[str, str] = {}
    for cmd in script.commands:
        if cmd.name == "set" and len(cmd.args) >= 2 and isinstance(cmd.args[0], TCLWord):
            result[cmd.args[0].value] = cmd.args[1].substitute({})
    return result


def _get_foreach_cases(foreach_command: TCLCommandForEach) -> list[dict[str, str]]:
    """Return one dict per parametrize case with the foreach var bindings."""
    if len(foreach_command.variables_names_and_values_lists) != 1:
        return []
    names, values_list = foreach_command.variables_names_and_values_lists[0]
    words = values_list.words
    chunk = len(names)
    return [
        dict(zip(names, words[i : i + chunk]))
        for i in range(0, len(words), chunk)
        if len(words[i : i + chunk]) == chunk
    ]


def _extract_foreach_derived_vars(
    foreach_command: TCLCommandForEach,
    foreach_var_names: list[str],
) -> dict[str, list[str]]:
    """
    Scan foreach body for outer-scope if/else blocks that derive new variables
    from a foreach parametrize var via a simple equality test.

    Pattern: if {$param eq "VALUE"} { set var v1 } else { set var v2 }

    Returns {derived_var_name: [value_for_case0, value_for_case1, ...]}.
    """
    cases = _get_foreach_cases(foreach_command)
    if not cases:
        return {}

    derived: dict[str, list[str | None]] = {}

    for command in foreach_command.body.commands:
        if not isinstance(command, TCLCommandWord) or command.name != "if":
            continue
        try:
            if_cmd = TCLCommandIf.build(command.args, {})
        except Exception:
            continue

        # Skip if-blocks that wrap test commands — those are handled by IfCommandGenerator
        _, if_body = if_cmd.if_part
        if any(getattr(c, "name", None) == "test" for c in if_body.commands):
            continue

        # Parse condition: must be a simple 3-token postfix: operand op operand
        condition = if_cmd.if_part[0]
        postfix = condition.postfix
        operator = postfix[2] if len(postfix) == 3 else None
        if not isinstance(operator, str) or operator not in ("eq", "=="):
            continue

        lhs, rhs = postfix[0], postfix[1]
        if (
            isinstance(lhs, TCLVariableSubstitutionWord)
            and lhs.variable_name in foreach_var_names
            and not isinstance(rhs, str)
        ):
            param_var, match_val = lhs.variable_name, rhs.substitute({})
        elif (
            isinstance(rhs, TCLVariableSubstitutionWord)
            and rhs.variable_name in foreach_var_names
            and not isinstance(lhs, str)
        ):
            param_var, match_val = rhs.variable_name, lhs.substitute({})
        else:
            continue

        if_sets = _collect_set_values(if_body)
        else_sets = _collect_set_values(if_cmd.else_part) if if_cmd.else_part else {}
        all_derived_vars = set(if_sets) | set(else_sets)
        if not all_derived_vars:
            continue

        for var in all_derived_vars:
            if var not in derived:
                derived[var] = [None] * len(cases)
            for i, case in enumerate(cases):
                derived[var][i] = if_sets.get(var) if case.get(param_var) == match_val else else_sets.get(var)

    return {k: cast("list[str]", v) for k, v in derived.items() if all(x is not None for x in v)}


class TestFileGenerator(Protocol):
    def generate_test(
        self,
        test_command: TCLCommandWord,
        if_expressions: list[str] | None,
        parametrizes: list[str] | None,
        parametrize_vars: list[str] | None,
    ) -> None: ...

    def generate_comment(self, command: TCLCommandWord) -> None: ...

    def generate_tests(
        self,
        script: TCLScript,
        if_expressions: list[str] | None,
        foreach_commands: list[str] | None,
        parametrize_vars: list[str] | None,
    ) -> None: ...

    def generate_parametrize(self, foreach_command: TCLCommandForEach) -> str: ...

    def generate_parametrize_extended(
        self, foreach_command: TCLCommandForEach, derived: dict[str, list[str]]
    ) -> str: ...


class CommandGenerator:
    MAPPING: ClassVar[dict[str, CommandGenerator]] = {}

    def generate(
        self,
        command: TCLCommandWord,
        generator: TestFileGenerator,
        if_expressions: list[str] | None,
        foreach_commands: list[str] | None,
        parametrize_vars: list[str] | None = None,
    ) -> None:
        raise NotImplementedError


class TestCommandGenerator(CommandGenerator):
    def generate(
        self,
        command: TCLCommandWord,
        generator: TestFileGenerator,
        if_expressions: list[str] | None,
        foreach_commands: list[str] | None,
        parametrize_vars: list[str] | None = None,
    ) -> None:
        generator.generate_test(command, if_expressions, foreach_commands, parametrize_vars)


class IfCommandGenerator(CommandGenerator):
    def generate(
        self,
        command: TCLCommandWord,
        generator: TestFileGenerator,
        if_expressions: list[str] | None,
        foreach_commands: list[str] | None,
        parametrize_vars: list[str] | None = None,
    ) -> None:
        try:
            if_command = TCLCommandIf.build(command.args, {})
        except Exception:
            generator.generate_comment(command)
            return
        _, body = if_command.if_part
        if not any(c for c in body.commands if c.name == "test"):
            generator.generate_comment(command)
            return
        generator.generate_tests(
            body,
            (if_expressions or []) + [str(command.args[0])],
            foreach_commands,
            parametrize_vars,
        )


class ForeachCommandGenerator(CommandGenerator):
    def generate(
        self,
        command: TCLCommandWord,
        generator: TestFileGenerator,
        if_expressions: list[str] | None,
        foreach_commands: list[str] | None,
        parametrize_vars: list[str] | None = None,
    ) -> None:
        try:
            foreach_command = TCLCommandForEach.build(command.args, {})
        except Exception:
            generator.generate_comment(command)
            return
        has_unresolved_values = any(len(vl.words) == 0 for _, vl in foreach_command.variables_names_and_values_lists)
        if has_unresolved_values:
            generator.generate_comment(command)
            return
        if not any(c for c in foreach_command.body.commands if c.name == "test"):
            generator.generate_comment(command)
            return
        new_vars = [name for names, _ in foreach_command.variables_names_and_values_lists for name in names]
        derived = _extract_foreach_derived_vars(foreach_command, new_vars)
        if derived:
            parametrize_str = generator.generate_parametrize_extended(foreach_command, derived)
            all_new_vars = new_vars + list(derived.keys())
        else:
            parametrize_str = generator.generate_parametrize(foreach_command)
            all_new_vars = new_vars
        generator.generate_tests(
            foreach_command.body,
            if_expressions,
            (foreach_commands or []) + [parametrize_str],
            (parametrize_vars or []) + all_new_vars,
        )


class TagsCommandGenerator(CommandGenerator):
    def generate(
        self,
        command: TCLCommandWord,
        generator: TestFileGenerator,
        if_expressions: list[str] | None,
        foreach_commands: list[str] | None,
        parametrize_vars: list[str] | None = None,
    ) -> None:
        pass


CommandGenerator.MAPPING.update(
    {
        "test": TestCommandGenerator(),
        "if": IfCommandGenerator(),
        "foreach": ForeachCommandGenerator(),
        "tags": TagsCommandGenerator(),
    }
)
