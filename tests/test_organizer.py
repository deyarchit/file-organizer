import pytest
from organizer.disk_operations import (
    create_json_from_dir,
    compare_structures,
    apply_changes,
    _calculate_md5,
    FlatFileItem,
)
import os
from typing import List
import shutil


# Helper function to create dummy files for testing
def create_dummy_file(filepath: str, content: str):
    """Creates a dummy file with specified content."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w") as f:
        f.write(content)


@pytest.fixture
def temp_dir_structure(tmp_path):
    """Fixture to create a temporary directory structure for testing."""
    root_dir = tmp_path / "root"
    os.makedirs(root_dir)

    # Create files and directories
    create_dummy_file(root_dir / "file1.txt", "content1")
    create_dummy_file(root_dir / "subdir1" / "file2.txt", "content2")
    os.makedirs(root_dir / "empty_dir")
    os.makedirs(root_dir / "subdir2")

    return str(root_dir)


# --- Tests for create_json_from_dir ---


def test_create_json_from_dir_valid(temp_dir_structure):
    """Test JSON creation from a valid directory structure."""
    items = create_json_from_dir(temp_dir_structure)
    assert items is not None
    # FIX: The fixture correctly creates two empty directories ('empty_dir' and 'subdir2')
    # and two files, for a total of 4 items.
    assert len(items) == 4

    paths = {item.path for item in items}
    assert "file1.txt" in paths
    assert "subdir1/file2.txt" in paths
    assert "empty_dir/" in paths
    assert "subdir2/" in paths


def test_create_json_from_dir_non_existent():
    """Test with a non-existent directory."""
    assert create_json_from_dir("non_existent_dir") is None


def test_create_json_from_dir_empty(tmp_path):
    """Test with an empty directory."""
    empty_dir = tmp_path / "empty"
    os.makedirs(empty_dir)
    # An empty directory contains nothing, so the function should return an empty list
    # as there are no files or empty subdirectories to report.
    assert create_json_from_dir(str(empty_dir)) == []


# --- Tests for compare_structures ---


def test_compare_structures_no_changes():
    """Test comparison with identical structures."""
    items = [
        FlatFileItem(path="file.txt", hash="h1", size=10),
        FlatFileItem(path="dir/"),
    ]
    missing, added = compare_structures(items, items)
    assert missing == []
    assert added == []


def test_compare_structures_with_changes():
    """Test comparison with added and missing files."""
    current = [
        FlatFileItem(path="file1.txt", hash="h1", size=10),
        FlatFileItem(path="dir1/"),
    ]
    desired = [
        FlatFileItem(path="file2.txt", hash="h2", size=20),
        FlatFileItem(path="dir1/"),
    ]
    missing, added = compare_structures(current, desired)
    assert missing == ["file1.txt"]
    assert added == ["file2.txt"]


def test_compare_same_filename_different_hash():
    """Test files with the same name but different hashes are detected as changes."""
    current = [FlatFileItem(path="file.txt", hash="h1", size=10)]
    desired = [FlatFileItem(path="file.txt", hash="h2", size=10)]
    missing, added = compare_structures(current, desired)
    assert missing == ["file.txt"]
    assert added == ["file.txt"]


def test_compare_files_only_mode():
    """Test files_only=True ignores paths and directories."""
    current = [
        FlatFileItem(path="a/file.txt", hash="h1", size=10),
        FlatFileItem(path="b/stale.txt", hash="h_stale", size=10),
        FlatFileItem(path="empty_dir/"),
    ]
    desired = [
        FlatFileItem(path="x/file.txt", hash="h1", size=10),  # Same name & hash
        FlatFileItem(path="y/new.txt", hash="h_new", size=10),
    ]
    missing, added = compare_structures(current, desired, files_only=True)
    assert missing == ["stale.txt"]
    assert added == ["new.txt"]


def test_compare_multiple_files_same_name_different_hash():
    """Test multiple files with same name but different hashes."""
    current = [
        FlatFileItem(path="a/file.txt", hash="h1", size=10),
        FlatFileItem(path="b/file.txt", hash="h2", size=20),
    ]
    desired = [
        # This file could be a move of "a/file.txt" since hash is same
        FlatFileItem(path="c/file.txt", hash="h1", size=10),
        # This is a new file
        FlatFileItem(path="d/file.txt", hash="h3", size=30),
    ]
    missing, added = compare_structures(current, desired)

    # ✅ **FIXED ASSERTION**
    # The comparison is on `path::hash`. Since no exact match exists for
    # the items in `current` within `desired`, both are considered missing.
    assert sorted(missing) == sorted(["a/file.txt", "b/file.txt"])

    # Conversely, the items in `desired` are not in `current` and are considered added.
    assert sorted(added) == sorted(["c/file.txt", "d/file.txt"])


# --- Tests for apply_changes ---


def test_apply_changes_integration(tmp_path):
    """Integration test for applying changes to a directory."""
    root_dir = tmp_path / "sync_root"
    os.makedirs(root_dir)

    # --- Initial state ---
    create_dummy_file(root_dir / "delete_me.txt", "old")
    create_dummy_file(root_dir / "a" / "move_me.txt", "content")
    os.makedirs(root_dir / "delete_me_dir")
    os.makedirs(root_dir / "nested_empty" / "nested_empty" / "nested_empty")
    current_items = create_json_from_dir(str(root_dir))
    move_hash = _calculate_md5(str(root_dir / "a" / "move_me.txt"))

    # --- Desired state ---
    # Note: apply_changes cannot create new file content, only move existing files.
    # Therefore, we don't include a totally new file in desired_items for this test.
    desired_items = [
        FlatFileItem(path="b/moved.txt", hash=move_hash, size=len("content")),
        FlatFileItem(path="new_dir/"),
    ]

    # --- Apply changes ---
    apply_changes(current_items, desired_items, str(root_dir))

    # --- Verify final state ---
    assert not (root_dir / "delete_me.txt").exists()
    assert not (root_dir / "a" / "move_me.txt").exists()
    assert not (root_dir / "delete_me_dir").exists()
    assert not (root_dir / "a").exists()
    assert not (root_dir / "nested_empty").exists()

    assert (root_dir / "new_dir").is_dir()
    moved_file = root_dir / "b" / "moved.txt"
    assert moved_file.exists()
    assert moved_file.read_text() == "content"
