from __future__ import annotations

import logging
import subprocess
from collections import Counter
from pathlib import Path

import typer

from valkeytests.compare_tests import compare_file, print_result
from valkeytests.create_test_files import TCLTestFileGenerator, _discover_tcl_files, _tcl_path_to_python_path

app = typer.Typer(pretty_exceptions_enable=False)
logger = logging.getLogger(__name__)


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


@app.command()
def compare(
    valkey_directory: Path = typer.Argument(..., envvar="VALKEY_DIRECTORY"),
    generated_dir: Path = typer.Option(
        Path("valkeytests/generated/unit"), help="Directory with generated Python files"
    ),
    file: str | None = typer.Option(None, help="Compare a single TCL file (relative path, e.g. type/string.tcl)"),
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
        print_result(compare_file(tcl_path, python_path))
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
