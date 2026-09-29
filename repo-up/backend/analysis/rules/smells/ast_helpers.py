"""
analysis/rules/smells/ast_helpers.py
Common Tree-sitter traversal utilities for all smell rules.

All helpers accept a tree-sitter Node and return plain Python data structures
so that individual rules stay focused and testable.
"""

from __future__ import annotations
from typing import Generator


def walk_depth_first(node) -> Generator:
    """Yield all nodes in depth-first pre-order."""
    yield node
    for child in node.children:
        yield from walk_depth_first(child)


def node_text(node) -> str:
    """Decode a node's source text as UTF-8 (returns '' on error)."""
    try:
        return node.text.decode("utf-8")
    except Exception:
        return ""


def children_of_type(node, *types: str):
    """Return direct children whose .type is in *types*."""
    return [c for c in node.children if c.type in types]


def first_child_of_type(node, *types: str):
    """Return the first direct child with .type in *types*, or None."""
    for c in node.children:
        if c.type in types:
            return c
    return None


def find_all(node, *types: str):
    """Yield all descendant nodes (including node itself) whose type is in *types*."""
    for n in walk_depth_first(node):
        if n.type in types:
            yield n


def source_lines(filepath: str) -> list[str]:
    """Read source lines from *filepath*; returns [] on error."""
    try:
        with open(filepath, "r", encoding="utf-8", errors="replace") as fh:
            return fh.readlines()
    except Exception:
        return []
