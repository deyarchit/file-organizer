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


# Helper function to create dummy files for testing
def create_dummy_file(filepath: str, content: str) -> None:
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


# ---


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

    expected_missing = [FlatFileItem(path="file1.txt", hash="h1", size=10)]
    expected_added = [FlatFileItem(path="file2.txt", hash="h2", size=20)]

    missing, added = compare_structures(current, desired)

    assert missing == expected_missing
    assert added == expected_added


# ---


def test_compare_same_filename_different_hash():
    """Test files with the same name but different hashes are detected as changes."""
    current = [FlatFileItem(path="file.txt", hash="h1", size=10)]
    desired = [FlatFileItem(path="file.txt", hash="h2", size=10)]

    missing, added = compare_structures(current, desired)

    assert missing == current
    assert added == desired


# ---


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

    expected_missing = [FlatFileItem(path="b/stale.txt", hash="h_stale", size=10)]
    expected_added = [FlatFileItem(path="y/new.txt", hash="h_new", size=10)]

    missing, added = compare_structures(current, desired, files_only=True)

    assert missing == expected_missing
    assert added == expected_added


# ---


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

    # The comparison is on `path::hash`. Since no exact match exists for
    # the items in `current` within `desired`, both are considered missing.
    # We sort the lists to ensure the comparison is order-independent.
    assert sorted(missing, key=lambda item: item.path) == sorted(
        current, key=lambda item: item.path
    )

    # Conversely, the items in `desired` are not in `current` and are considered added.
    assert sorted(added, key=lambda item: item.path) == sorted(
        desired, key=lambda item: item.path
    )


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

    assert current_items is not None

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


def test_apply_changes_does_not_affect_outside_directory(tmp_path):
    """
    Test that apply_changes refuses to delete files outside the target directory.
    This is a test for a path traversal vulnerability.
    """
    # Setup: Create a root directory and a sensitive file outside of it
    root_dir = tmp_path / "target"
    root_dir.mkdir()

    sensitive_file = tmp_path / "sensitive.txt"
    sensitive_file.write_text("do not delete this file")

    # Define a state where a "current" file path points outside the root_dir
    # This simulates a malicious or corrupted state file.
    current_items = [FlatFileItem(path="../sensitive.txt", hash="any_hash", size=100)]
    # The desired state is empty, so the function will try to delete the "missing" item.
    desired_items: List[FlatFileItem] = []

    # Action: Run apply_changes, which should detect the dangerous path and skip it
    apply_changes(current_items, desired_items, str(root_dir))

    # Assert: The sensitive file outside the root directory MUST still exist.
    assert sensitive_file.exists()
    assert sensitive_file.read_text() == "do not delete this file"
