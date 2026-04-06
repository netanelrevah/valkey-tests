from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar, Protocol

from pytcl.commands import TCLCommandForEach, TCLCommandIf

if TYPE_CHECKING:
    from pytcl.commands import TCLScript
    from pytcl.words import TCLCommandWord


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
        generator.generate_tests(
            foreach_command.body,
            if_expressions,
            (foreach_commands or []) + [generator.generate_parametrize(foreach_command)],
            (parametrize_vars or []) + new_vars,
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
