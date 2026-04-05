from __future__ import annotations

import ast
import io
import textwrap

from valkeytests.compare_tests import normalize_text
from valkeytests.create_test_files import TCLTestFileGenerator


def generate_python(tcl: str) -> str:
    tcl = textwrap.dedent(tcl).strip()
    output = io.StringIO()
    TCLTestFileGenerator(output=output).generate(io.StringIO(tcl))
    return output.getvalue()


def test_reconstruct_tcl__simple_test():
    tcl = """
        start_server {tags {}} {
            test {SET and GET an item} {
                r set x foobar
                r get x
            } {foobar}
        }
    """
    python_code = generate_python(tcl)
    reconstructed = reconstruct_tcl_from_python_str(python_code)

    assert "SET and GET an item" in reconstructed
    assert "r set x foobar" in reconstructed
    assert "foobar" in reconstructed


def test_reconstruct_tcl__comment_block():
    tcl = """
        start_server {tags {}} {
            proc helper {} {
                r flushall
            }
        }
    """
    python_code = generate_python(tcl)
    reconstructed = reconstruct_tcl_from_python_str(python_code)

    assert "proc helper" in reconstructed
    assert "r flushall" in reconstructed


def test_normalize_text__strips_whitespace():
    text = "  hello  \n  world  \n\n"
    result = normalize_text(text)
    assert result == ["hello", "world"]


def test_normalize_text__removes_blank_lines():
    text = "a\n\n\nb"
    result = normalize_text(text)
    assert result == ["a", "b"]


def reconstruct_tcl_from_python_str(python_code: str) -> str:
    tree = ast.parse(python_code)
    tcl_blocks = []

    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
            docstring = ast.get_docstring(node, clean=False)
            if docstring:
                tcl_blocks.append(docstring)
        elif isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant):
            if isinstance(node.value.value, str):
                tcl_blocks.append(node.value.value)

    return "\n".join(tcl_blocks)
