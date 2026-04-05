from __future__ import annotations

import ast
import difflib
import re
from dataclasses import dataclass, field
from pathlib import Path

import typer

from valkeytests.create_test_files import _discover_tcl_files, _tcl_path_to_python_path

app = typer.Typer(pretty_exceptions_enable=False)


@dataclass
class ComparisonResult:
    tcl_file: Path
    python_file: Path
    total_tcl_lines: int = 0
    reconstructed_lines: int = 0
    diff_lines: list[str] = field(default_factory=list)
    new_tests: list[str] = field(default_factory=list)
    modified_tests: list[str] = field(default_factory=list)
    removed_tests: list[str] = field(default_factory=list)


def reconstruct_tcl_from_python(python_path: Path) -> str:
    source = python_path.read_text(encoding="utf-8")
    tree = ast.parse(source)

    tcl_blocks: list[str] = []

    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
            docstring = ast.get_docstring(node, clean=False)
            if docstring:
                tcl_blocks.append(docstring)
        elif isinstance(node, ast.Expr) and isinstance(node.value, (ast.Constant, ast.Str)):
            value = node.value.value if isinstance(node.value, ast.Constant) else node.value.s
            if isinstance(value, str):
                tcl_blocks.append(value)

    return "\n".join(tcl_blocks)


def normalize_text(text: str) -> list[str]:
    lines = text.splitlines()
    normalized = []
    for line in lines:
        stripped = line.strip()
        if stripped:
            normalized.append(stripped)
    return normalized


def extract_test_names_from_tcl(text: str) -> set[str]:
    return set(re.findall(r"test\s+\{([^}]+)\}", text))


def compare_file(tcl_path: Path, python_path: Path) -> ComparisonResult:
    result = ComparisonResult(tcl_file=tcl_path, python_file=python_path)

    tcl_text = tcl_path.read_text(encoding="utf-8")
    reconstructed_text = reconstruct_tcl_from_python(python_path)

    tcl_normalized = normalize_text(tcl_text)
    reconstructed_normalized = normalize_text(reconstructed_text)

    result.total_tcl_lines = len(tcl_normalized)
    result.reconstructed_lines = len(reconstructed_normalized)

    diff = list(
        difflib.unified_diff(
            reconstructed_normalized,
            tcl_normalized,
            fromfile=f"generated/{python_path.name}",
            tofile=str(tcl_path.name),
            lineterm="",
        )
    )
    result.diff_lines = diff

    tcl_tests = extract_test_names_from_tcl(tcl_text)
    reconstructed_tests = extract_test_names_from_tcl(reconstructed_text)

    result.new_tests = sorted(tcl_tests - reconstructed_tests)
    result.removed_tests = sorted(reconstructed_tests - tcl_tests)
    result.modified_tests = []

    return result


def print_result(result: ComparisonResult) -> None:
    print(f"\n{'=' * 60}")
    print(f"  {result.tcl_file.name}")
    print(f"{'=' * 60}")

    if not result.diff_lines:
        print("  No changes detected.")
        return

    if result.new_tests:
        print(f"\n  New tests ({len(result.new_tests)}):")
        for name in result.new_tests:
            print(f"    + {name}")

    if result.removed_tests:
        print(f"\n  Removed tests ({len(result.removed_tests)}):")
        for name in result.removed_tests:
            print(f"    - {name}")

    print(f"\n  Diff ({len(result.diff_lines)} lines):")
    max_diff_lines = 50
    for line in result.diff_lines[:max_diff_lines]:
        print(f"    {line}")
    if len(result.diff_lines) > max_diff_lines:
        print(f"    ... ({len(result.diff_lines) - max_diff_lines} more lines)")


@app.command()
def compare(
    valkey_directory: Path = typer.Argument(..., envvar="VALKEY_DIRECTORY"),
    generated_dir: Path = typer.Option(
        Path("valkeytests/generated/unit"), help="Directory with generated Python files"
    ),
    file: str | None = typer.Option(None, help="Compare a single Tcl file (relative path, e.g. type/string.tcl)"),
) -> None:
    commit_file = generated_dir.parent / "VALKEY_COMMIT"
    if commit_file.exists():
        snapshot_commit = commit_file.read_text().strip()
        print(f"Snapshot generated from Valkey commit: {snapshot_commit}")

    unit_tests_path = valkey_directory / "tests" / "unit"

    if file:
        tcl_path = unit_tests_path / file
        python_path = generated_dir / _tcl_path_to_python_path(tcl_path, unit_tests_path)
        if not python_path.exists():
            print(f"Generated file not found: {python_path}")
            print("Run the generator first.")
            raise typer.Exit(1)
        result = compare_file(tcl_path, python_path)
        print_result(result)
        return

    tcl_files = _discover_tcl_files(unit_tests_path)

    total_new = 0
    total_removed = 0
    total_changed = 0
    total_unchanged = 0

    for tcl_file in tcl_files:
        python_path = generated_dir / _tcl_path_to_python_path(tcl_file, unit_tests_path)
        if not python_path.exists():
            print(f"  MISSING: {tcl_file.name} (no generated file)")
            continue

        result = compare_file(tcl_file, python_path)

        if result.diff_lines:
            print_result(result)
            total_changed += 1
        else:
            total_unchanged += 1

        total_new += len(result.new_tests)
        total_removed += len(result.removed_tests)

    print(f"\n{'=' * 60}")
    print("  Summary")
    print(f"{'=' * 60}")
    print(f"  Files unchanged: {total_unchanged}")
    print(f"  Files changed:   {total_changed}")
    print(f"  New tests:       {total_new}")
    print(f"  Removed tests:   {total_removed}")


if __name__ == "__main__":
    app()
