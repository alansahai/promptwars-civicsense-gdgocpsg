"""Code quality enforcement test suite.

Validates using AST that:
1. Every public module, class, and function/method has a docstring.
2. No function or method in `app/` exceeds 40 lines (excluding docstrings).
"""

import ast
from pathlib import Path


def _get_effective_function_lines(fn_node: ast.FunctionDef | ast.AsyncFunctionDef) -> int:
    """Calculate line count of a function excluding its docstring."""
    total = fn_node.end_lineno - fn_node.lineno + 1  # type: ignore[operator]
    if (
        fn_node.body
        and isinstance(fn_node.body[0], ast.Expr)
        and isinstance(fn_node.body[0].value, ast.Constant)
        and isinstance(fn_node.body[0].value.value, str)
    ):
        doc_node = fn_node.body[0]
        doc_lines = doc_node.end_lineno - doc_node.lineno + 1  # type: ignore[operator]
        return total - doc_lines
    return total


def _check_class_docstrings(node: ast.ClassDef, rel_path: str, missing: list[str]) -> None:
    """Validate docstrings for public class and its methods."""
    if not node.name.startswith("_") and not ast.get_docstring(node):
        missing.append(f"Class missing docstring: {rel_path}:{node.name}")
    for sub in node.body:
        if (
            isinstance(sub, (ast.FunctionDef, ast.AsyncFunctionDef))
            and not sub.name.startswith("_")
            and not ast.get_docstring(sub)
        ):
            missing.append(f"Method missing docstring: {rel_path}:{node.name}.{sub.name}")


def _check_top_level_function(node: ast.AST, rel_path: str, missing: list[str]) -> None:
    """Validate docstring for public top-level function."""
    if (
        isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and not node.name.startswith("_")
        and not ast.get_docstring(node)
    ):
        missing.append(f"Function missing docstring: {rel_path}:{node.name}")


def test_public_elements_have_docstrings() -> None:
    """Ensure all public modules, classes, and functions in app/ have docstrings."""
    app_dir = Path("app")
    missing_docstrings: list[str] = []

    for py_file in app_dir.rglob("*.py"):
        if py_file.name.startswith("__") and py_file.name != "__init__.py":
            continue

        tree = ast.parse(py_file.read_text(encoding="utf-8"), filename=str(py_file))
        rel_path = py_file.as_posix()

        if not ast.get_docstring(tree):
            missing_docstrings.append(f"Module missing docstring: {rel_path}")

        for node in tree.body:
            if isinstance(node, ast.ClassDef):
                _check_class_docstrings(node, rel_path, missing_docstrings)
            else:
                _check_top_level_function(node, rel_path, missing_docstrings)

    assert not missing_docstrings, "Missing docstrings found:\n" + "\n".join(missing_docstrings)


def test_functions_do_not_exceed_forty_lines() -> None:
    """Ensure no function or method in app/ exceeds 40 lines (excluding docstrings)."""
    app_dir = Path("app")
    oversized_functions: list[str] = []

    for py_file in app_dir.rglob("*.py"):
        tree = ast.parse(py_file.read_text(encoding="utf-8"), filename=str(py_file))
        rel_path = py_file.as_posix()

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                effective_lines = _get_effective_function_lines(node)
                if effective_lines > 40:
                    oversized_functions.append(
                        f"{rel_path}:{node.name} has {effective_lines} lines (max allowed: 40)"
                    )

    assert not oversized_functions, "Oversized functions found in app/:\n" + "\n".join(
        oversized_functions
    )
