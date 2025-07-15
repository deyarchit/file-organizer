from typing import Dict, Optional
import pytest
from rich.tree import Tree
from organizer.renderer import (
    ConsoleRenderer,
    FlatFileItem,
)


@pytest.fixture
def generator():
    return ConsoleRenderer()


def tree_to_dict(tree: Tree) -> Dict[str, Optional[dict]]:
    """Convert a Rich Tree into a nested dictionary"""

    def helper(node: Tree) -> Dict[str, Optional[dict]]:
        label = str(node.label)
        if not node.children:
            return {label: None}
        children_dict: Dict[str, Optional[dict]] = {}
        for child in node.children:
            children_dict.update(helper(child))
        return {label: children_dict}

    return helper(tree)


def test_single_file_at_root(generator):
    items = [FlatFileItem(path="file.txt")]
    tree = generator.generate_file_tree(items)
    assert tree_to_dict(tree) == {"📁 .": {"📄 file.txt": None}}


def test_nested_file_structure(generator):
    items = [
        FlatFileItem(path="dir1/file1.txt"),
        FlatFileItem(path="dir1/dir2/file2.txt"),
        FlatFileItem(path="dir1/dir2/file3.txt"),
    ]
    tree = generator.generate_file_tree(items)
    assert tree_to_dict(tree) == {
        "📁 dir1": {
            "📄 file1.txt": None,
            "📁 dir2": {"📄 file2.txt": None, "📄 file3.txt": None},
        }
    }


def test_multiple_root_folders(generator):
    items = [
        FlatFileItem(path="alpha/file_a.txt"),
        FlatFileItem(path="beta/file_b.txt"),
    ]
    tree = generator.generate_file_tree(items)
    assert tree_to_dict(tree) == {
        "📁 .": {
            "📁 alpha": {"📄 file_a.txt": None},
            "📁 beta": {"📄 file_b.txt": None},
        }
    }


def test_common_prefix_is_trimmed(generator):
    items = [
        FlatFileItem(path="common/dir1/file1.txt"),
        FlatFileItem(path="common/dir2/file2.txt"),
    ]
    tree = generator.generate_file_tree(items)
    assert tree_to_dict(tree) == {
        "📁 common": {
            "📁 dir1": {"📄 file1.txt": None},
            "📁 dir2": {"📄 file2.txt": None},
        }
    }


def test_empty_input(generator):
    tree = generator.generate_file_tree([])
    assert tree_to_dict(tree) == {"📁 .": None}


def test_trailing_slash_folders(generator):
    items = [
        FlatFileItem(path="dir1/dir2/"),
        FlatFileItem(path="dir1/file1.txt"),
    ]
    tree = generator.generate_file_tree(items)
    assert tree_to_dict(tree) == {"📁 dir1": {"📁 dir2": None, "📄 file1.txt": None}}
