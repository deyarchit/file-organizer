import pytest
from rich.tree import Tree
from organizer.renderer import (
    ConsoleRenderer,
    FlatFileItem,
)  # replace with actual module/class names


@pytest.fixture
def generator():
    return ConsoleRenderer()  # replace with your actual class instantiation


def get_tree_labels(tree: Tree) -> list:
    """Helper to flatten the Tree into a list of labels for testing."""
    labels = [tree.label]
    for child in tree.children:
        labels.extend(get_tree_labels(child))
    return labels


def test_single_file_at_root(generator):
    items = [FlatFileItem(path="file.txt")]
    tree = generator.generate_file_tree(items)
    labels = get_tree_labels(tree)
    assert labels == ["📁 .", "📄 file.txt"]


def test_nested_file_structure(generator):
    items = [
        FlatFileItem(path="dir1/file1.txt"),
        FlatFileItem(path="dir1/dir2/file2.txt"),
        FlatFileItem(path="dir1/dir2/file3.txt"),
    ]
    tree = generator.generate_file_tree(items)
    labels = get_tree_labels(tree)
    assert sorted(labels) == sorted(
        [
            "📁 dir1",
            "📄 file1.txt",
            "📁 dir2",
            "📄 file2.txt",
            "📄 file3.txt",
        ]
    )


def test_multiple_root_folders(generator):
    items = [
        FlatFileItem(path="alpha/file_a.txt"),
        FlatFileItem(path="beta/file_b.txt"),
    ]
    tree = generator.generate_file_tree(items)
    labels = get_tree_labels(tree)
    assert sorted(labels) == sorted(
        [
            "📁 .",
            "📁 alpha",
            "📄 file_a.txt",
            "📁 beta",
            "📄 file_b.txt",
        ]
    )


def test_common_prefix_is_trimmed(generator):
    items = [
        FlatFileItem(path="common/dir1/file1.txt"),
        FlatFileItem(path="common/dir2/file2.txt"),
    ]
    tree = generator.generate_file_tree(items)
    labels = get_tree_labels(tree)
    assert labels[0] == "📁 common"


def test_empty_input(generator):
    tree = generator.generate_file_tree([])
    assert isinstance(tree, Tree)
    assert tree.label == "📁 ."
    assert tree.children == []


def test_trailing_slash_folders(generator):
    items = [
        FlatFileItem(path="dir1/"),
        FlatFileItem(path="dir1/file1.txt"),
    ]
    tree = generator.generate_file_tree(items)
    labels = get_tree_labels(tree)
    assert "📁 dir1" in labels
    assert "📄 file1.txt" in labels
