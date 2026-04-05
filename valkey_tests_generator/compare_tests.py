from __future__ import annotations

import ast
import difflib
import re
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path


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
        elif isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
            tcl_blocks.append(node.value.value)

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
