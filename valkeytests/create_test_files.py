from __future__ import annotations

import logging
import re
import subprocess
import sys
import textwrap
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from itertools import cycle, zip_longest
from pathlib import Path
from typing import IO, TextIO

import typer
from pytcl.commands import TCLBracesWord, TCLCommandForEach, TCLCommandIf, TCLList, TCLScript
from pytcl.words import (
    TCLBracketWord,
    TCLCommandArguments,
    TCLCommandWord,
    TCLDoubleQuotedWord,
    TCLVariableSubstitutionWord,
    TCLWord,
)

app = typer.Typer(pretty_exceptions_enable=False)
logger = logging.getLogger(__name__)


def _reconstruct_arg(arg: TCLCommandArguments) -> str:
    if isinstance(arg, TCLBracesWord):
        return "{" + arg.value + "}"
    if isinstance(arg, TCLDoubleQuotedWord):
        return '"' + arg.value + '"'
    return str(arg)


def _reconstruct_command(command: TCLCommandWord) -> str:
    parts = [command.name, *(_reconstruct_arg(arg) for arg in command.args)]
    return " ".join(parts)


def _translate_arg(arg: TCLCommandArguments) -> str | None:
    if isinstance(arg, TCLVariableSubstitutionWord):
        if "::" in arg.variable_name:
            return None
        return arg.variable_name
    if isinstance(arg, TCLBracketWord):
        commands = [c for c in arg.script.commands if c.name]
        if len(commands) != 1:
            return None
        return _translate_command_expr(commands[0])
    if isinstance(arg, TCLBracesWord):
        return repr(arg.value)
    if isinstance(arg, TCLDoubleQuotedWord):
        if "$" in arg.value or "\\" in arg.value:
            return None
        return repr(arg.value)
    s = arg.value
    try:
        int(s)
        return s
    except ValueError:
        pass
    try:
        float(s)
        return s
    except ValueError:
        pass
    return repr(s)


def _translate_r_args(args: list[TCLCommandArguments]) -> str | None:
    if not args:
        return None
    subcmd = _translate_arg(args[0])
    if subcmd is None:
        return None
    rest = []
    for arg in args[1:]:
        t = _translate_arg(arg)
        if t is None:
            return None
        rest.append(t)
    call_args = ", ".join([subcmd, *rest])
    return f"r.run({call_args})"


def _translate_command_expr(command: TCLCommandWord) -> str | None:
    if command.name == "r":
        return _translate_r_args(command.args)
    return None


def _translate_command_stmt(command: TCLCommandWord) -> list[str] | None:
    match command.name:
        case "r":
            expr = _translate_r_args(command.args)
            if expr is None:
                return None
            return [expr]
        case "set":
            if not command.args[1:]:
                return None
            name_arg = command.args[0]
            if not isinstance(name_arg, TCLWord):
                return None
            val = _translate_arg(command.args[1])
            if val is None:
                return None
            return [f"{name_arg.value} = {val}"]
        case "assert_equal":
            if not command.args[1:]:
                return None
            a = _translate_arg(command.args[0])
            b = _translate_arg(command.args[1])
            if a is None or b is None:
                return None
            return [f"assert {a} == {b}"]
        case "assert_match":
            if not command.args[1:]:
                return None
            pat = _translate_arg(command.args[0])
            val = _translate_arg(command.args[1])
            if pat is None or val is None:
                return None
            return [f"assert fnmatch({val}, {pat})"]
        case "assert":
            if not command.args:
                return None
            expr = _translate_arg(command.args[0])
            if expr is None:
                return None
            return [f"assert {expr}"]
        case "incr":
            if not command.args:
                return None
            name_arg = command.args[0]
            if not isinstance(name_arg, TCLWord):
                return None
            if len(command.args) > 1:
                amount = _translate_arg(command.args[1])
                if amount is None:
                    return None
                return [f"{name_arg.value} += {amount}"]
            return [f"{name_arg.value} += 1"]
        case "puts":
            return []
        case _:
            return None


class TCLBodyTranslator:
    def translate(self, body: TCLScript, expected: str | None) -> list[str]:
        commands = [c for c in body.commands if c.name]
        if not commands:
            if expected is not None:
                return [f"assert False  # expected: {expected!r}"]
            return []

        lines: list[str] = []
        for i, command in enumerate(commands):
            is_last = i == len(commands) - 1
            if is_last and expected is not None:
                expr = _translate_command_expr(command)
                if expr is not None:
                    lines.append(f"assert {expr} == {expected!r}")
                else:
                    lines.append(f"# TODO: {_reconstruct_command(command)}")
                    lines.append("assert False")
            else:
                stmt = _translate_command_stmt(command)
                if stmt is not None:
                    lines.extend(stmt)
                else:
                    lines.append(f"# TODO: {_reconstruct_command(command)}")

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
                **{c: "_" for c in "{}\",#: -()<>=$'"},
            }
        )
        test_name = "test_" + re.sub("_+", "_", name.lower().translate(translate_table).strip("_"))

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
                self.output.write(f"@pytest.mark.skipif('', reason='{if_expression}')\n")
        if parametrizes:
            self.output.writelines(parametrizes)

        reconstructed = _reconstruct_command(test_command)
        self.output.write(f"def {test_name}(r: ValkeyTestClient):\n")
        self.output.write('    """\n')
        self.output.write(f"{textwrap.indent(textwrap.dedent(reconstructed), '    ')}\n")
        self.output.write('    """\n')
        for line in lines:
            self.output.write(f"    {line}\n")

    def generate_comment(self, command: TCLCommandWord) -> None:
        reconstructed = _reconstruct_command(command)
        self.output.write('\n\n"""\n')
        self.output.write(f"{textwrap.dedent(reconstructed)}\n")
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
                        expression, body = if_command.if_part

                        if not any([c for c in body.commands if c.name == "test"]):
                            self.generate_comment(command)
                            continue

                        self.generate_tests(
                            body,
                            (if_expressions or []) + [str(expression.postfix)],
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
                    tags.extend([word for word in TCLList.words_iterator(iter(value), {})])

        if tags:
            marks = ", ".join(["pytest.mark." + tag for tag in set(tags)])
            self.output.write("\n")
            self.output.write(f"pytestmark = [{marks}]\n")

        assert isinstance(command.args[1], TCLBracesWord)
        start_server_code = TCLScript.read(iter(command.args[1].value))

        if start_server_code:
            self.generate_tests(start_server_code)

    def generate(self, source_file: TextIO) -> None:
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
        with open(source_file_path) as source_file:
            self.generate(source_file)


def _discover_tcl_files(tests_path: Path) -> list[Path]:
    return list(sorted(tests_path.rglob("*.tcl")))


def _tcl_path_to_python_path(tcl_file: Path, base_tcl_path: Path) -> Path:
    relative = tcl_file.relative_to(base_tcl_path)
    return relative.parent / f"test_{relative.stem}.py"


def _get_git_commit(repo_dir: Path) -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repo_dir,
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except Exception:
        return "unknown"


@app.command()
def generate(
    valkey_directory: Path = typer.Argument(..., envvar="VALKEY_DIRECTORY"),
    output_dir: Path = typer.Option(Path("valkeytests/generated/unit"), help="Output directory for generated files"),
    skip_errors: bool = typer.Option(False, help="Skip files that fail to parse"),
    stats: bool = typer.Option(False, "--stats", help="Print translation statistics after generation"),
) -> None:
    unit_tests_path = valkey_directory / "tests" / "unit"
    tcl_files = _discover_tcl_files(unit_tests_path)

    output_dir.mkdir(parents=True, exist_ok=True)

    commit = _get_git_commit(valkey_directory)
    (output_dir.parent / "VALKEY_COMMIT").write_text(commit + "\n")
    logger.info(f"Valkey commit: {commit}")

    total_todo_counter: Counter = Counter()
    total_tests = 0
    total_translated = 0

    for tcl_file in tcl_files:
        python_path = output_dir / _tcl_path_to_python_path(tcl_file, unit_tests_path)
        python_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            with open(python_path, "w") as output_file:
                gen = TCLTestFileGenerator(output=output_file)
                gen.generate_file(tcl_file)
                total_tests += gen._total_tests
                total_translated += gen._translated_tests
                total_todo_counter.update(gen._todo_counter)
            logger.info(f"Generated {python_path}")
        except Exception as e:
            if skip_errors:
                logger.warning(f"Skipping {tcl_file}: {e}")
                python_path.unlink(missing_ok=True)
            else:
                raise

    if stats:
        pct = int(100 * total_translated / total_tests) if total_tests else 0
        print(f"Tests: {total_tests}  Translated: {total_translated} ({pct}%)  Stubs: {total_tests - total_translated}")
        print("Top untranslated commands:")
        for cmd, count in total_todo_counter.most_common(15):
            print(f"  {cmd}: {count}")


if __name__ == "__main__":
    app()
