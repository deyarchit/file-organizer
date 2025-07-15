import os
from typing import List
import pytest

from organizer.disk_operations import DiskOperations, FlatFileItem
from organizer.utils import _calculate_short_sha256


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

    create_dummy_file(root_dir / "file1.txt", "content1")
    create_dummy_file(root_dir / "subdir1" / "file2.txt", "content2")
    os.makedirs(root_dir / "empty_dir")
    os.makedirs(root_dir / "subdir2")

    return str(root_dir)


# --- Tests for create_snapshot ---


def test_create_snapshot_valid(temp_dir_structure):
    items = DiskOperations.create_snapshot(temp_dir_structure)
    assert items is not None
    assert len(items) == 4

    paths = {item.path for item in items}
    assert "file1.txt" in paths
    assert "subdir1/file2.txt" in paths
    assert "empty_dir/" in paths
    assert "subdir2/" in paths


def test_create_snapshot_non_existent():
    assert DiskOperations.create_snapshot("non_existent_dir") is None


def test_create_snapshot_empty(tmp_path):
    empty_dir = tmp_path / "empty"
    os.makedirs(empty_dir)
    assert DiskOperations.create_snapshot(str(empty_dir)) == []


# --- Tests for compare_structures ---


def test_compare_structures_no_changes():
    items = [
        FlatFileItem(path="file.txt", hash="h1", size=10),
        FlatFileItem(path="dir/"),
    ]
    missing, added = DiskOperations.compare_structures(items, items)
    assert missing == []
    assert added == []


def test_compare_structures_with_changes():
    current = [
        FlatFileItem(path="file1.txt", hash="h1", size=10),
        FlatFileItem(path="dir1/"),
    ]
    desired = [
        FlatFileItem(path="file2.txt", hash="h2", size=20),
        FlatFileItem(path="dir1/"),
    ]
    missing, added = DiskOperations.compare_structures(current, desired)
    assert missing == [FlatFileItem(path="file1.txt", hash="h1", size=10)]
    assert added == [FlatFileItem(path="file2.txt", hash="h2", size=20)]


def test_compare_same_filename_different_hash():
    current = [FlatFileItem(path="file.txt", hash="h1", size=10)]
    desired = [FlatFileItem(path="file.txt", hash="h2", size=10)]
    missing, added = DiskOperations.compare_structures(current, desired)
    assert missing == current
    assert added == desired


def test_compare_files_only_mode():
    current = [
        FlatFileItem(path="a/b/c/file.txt", hash="h1", size=10),
        FlatFileItem(path="b/stale.txt", hash="h_stale", size=10),
        FlatFileItem(path="empty_dir/"),
    ]
    desired = [
        FlatFileItem(path="x/file.txt", hash="h1", size=10),
        FlatFileItem(path="y/new.txt", hash="h_new", size=10),
    ]

    missing, added = DiskOperations.compare_structures(
        current, desired, files_only=True
    )

    assert missing == [FlatFileItem(path="b/stale.txt", hash="h_stale", size=10)]
    assert added == [FlatFileItem(path="y/new.txt", hash="h_new", size=10)]


def test_compare_multiple_files_same_name_different_hash():
    current = [
        FlatFileItem(path="a/file.txt", hash="h1", size=10),
        FlatFileItem(path="b/file.txt", hash="h2", size=20),
    ]
    desired = [
        FlatFileItem(path="c/file.txt", hash="h1", size=10),
        FlatFileItem(path="d/file.txt", hash="h3", size=30),
    ]

    missing, added = DiskOperations.compare_structures(current, desired)

    assert sorted(missing, key=lambda x: x.path) == sorted(
        current, key=lambda x: x.path
    )
    assert sorted(added, key=lambda x: x.path) == sorted(desired, key=lambda x: x.path)


# --- Tests for FileSystemSync.sync ---


def test_apply_changes_integration(tmp_path):
    root_dir = tmp_path / "sync_root"
    os.makedirs(root_dir)

    create_dummy_file(root_dir / "delete_me.txt", "old")
    create_dummy_file(root_dir / "a" / "move_me.txt", "content")
    os.makedirs(root_dir / "delete_me_dir")
    os.makedirs(root_dir / "nested_empty" / "nested_empty" / "nested_empty")

    current_items = DiskOperations.create_snapshot(str(root_dir))
    assert current_items is not None

    move_hash = _calculate_short_sha256(str(root_dir / "a" / "move_me.txt"))

    desired_items = [
        FlatFileItem(path="b/moved.txt", hash=move_hash, size=len("content")),
        FlatFileItem(path="new_dir/"),
    ]

    syncer = DiskOperations(str(root_dir))
    syncer.sync(current_items, desired_items)

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
    root_dir = tmp_path / "target"
    root_dir.mkdir()

    sensitive_file = tmp_path / "sensitive.txt"
    sensitive_file.write_text("do not delete this file")

    current_items = [FlatFileItem(path="../sensitive.txt", hash="any_hash", size=100)]
    desired_items: List[FlatFileItem] = []

    syncer = DiskOperations(str(root_dir))
    syncer.sync(current_items, desired_items)

    assert sensitive_file.exists()
    assert sensitive_file.read_text() == "do not delete this file"


# def test_move_skipped_when_destination_outside_root(tmp_path):
#     root_dir = tmp_path / "root"
#     os.makedirs(root_dir)
#     malicious_path = "../outside.txt"
#     create_dummy_file(root_dir / "move_me.txt", "data")
#     hash_val = _calculate_short_sha256(str(root_dir / "move_me.txt"))

#     current_items = [FlatFileItem(path="move_me.txt", hash=hash_val, size=4)]
#     desired_items = [FlatFileItem(path=malicious_path, hash=hash_val, size=4)]

#     syncer = FileSystemSync(str(root_dir))
#     syncer.sync(current_items, desired_items)

#     # File should not be moved outside the root
#     assert (root_dir / "move_me.txt").exists()
#     assert not (tmp_path / "outside.txt").exists()


# def test_files_with_same_hash_but_different_sizes_are_ignored(tmp_path):
#     root_dir = tmp_path / "root"
#     os.makedirs(root_dir)
#     create_dummy_file(root_dir / "file1.txt", "abcde")  # 5 bytes
#     hash_val = _calculate_short_sha256(str(root_dir / "file1.txt"))

#     current_items = [FlatFileItem(path="file1.txt", hash=hash_val, size=5)]
#     # Desired has same hash but wrong size
#     desired_items = [FlatFileItem(path="moved.txt", hash=hash_val, size=10)]

#     syncer = FileSystemSync(str(root_dir))
#     syncer.sync(current_items, desired_items)

#     # File should not move since size doesn't match
#     assert (root_dir / "file1.txt").exists()
#     assert not (root_dir / "moved.txt").exists()


def test_partial_structure_move(tmp_path):
    root_dir = tmp_path / "root"
    os.makedirs(root_dir)
    create_dummy_file(root_dir / "a" / "b" / "c" / "d.txt", "deep")

    hash_val = _calculate_short_sha256(str(root_dir / "a" / "b" / "c" / "d.txt"))
    current_items = DiskOperations.create_snapshot(str(root_dir))
    assert current_items is not None

    desired_items = [
        FlatFileItem(path="x/y/z/d.txt", hash=hash_val, size=len("deep")),
    ]

    syncer = DiskOperations(str(root_dir))
    syncer.sync(current_items, desired_items)

    assert not (root_dir / "a").exists()
    assert (root_dir / "x/y/z/d.txt").exists()
    assert (root_dir / "x/y/z/d.txt").read_text() == "deep"


# def test_conflicting_file_and_dir(tmp_path):
#     root_dir = tmp_path / "root"
#     os.makedirs(root_dir)
#     create_dummy_file(root_dir / "conflict", "I am a file")

#     current_items = FileSystemSync.create_snapshot(str(root_dir))
#     desired_items = [FlatFileItem(path="conflict/", hash=None, size=None)]

#     syncer = FileSystemSync(str(root_dir))
#     syncer.sync(current_items, desired_items)

#     # File still exists because we don't auto-remove conflicting files for dirs
#     assert (root_dir / "conflict").is_file()


# def test_existing_directory_is_preserved(tmp_path):
#     root_dir = tmp_path / "root"
#     (root_dir / "pre_existing").mkdir()

#     current_items = FileSystemSync.create_snapshot(str(root_dir))
#     desired_items = [FlatFileItem(path="pre_existing/")]

#     syncer = FileSystemSync(str(root_dir))
#     syncer.sync(current_items, desired_items)

#     # Directory should not be deleted
#     assert (root_dir / "pre_existing").is_dir()


# def test_ignored_non_matching_hash_move(tmp_path):
#     root_dir = tmp_path / "root"
#     os.makedirs(root_dir)
#     create_dummy_file(root_dir / "original.txt", "original content")

#     hash_actual = _calculate_short_sha256(str(root_dir / "original.txt"))
#     hash_fake = "deadbeef"  # Mismatched hash

#     current_items = [FlatFileItem(path="original.txt", hash=hash_actual, size=17)]
#     desired_items = [FlatFileItem(path="new_place.txt", hash=hash_fake, size=17)]

#     syncer = FileSystemSync(str(root_dir))
#     syncer.sync(current_items, desired_items)

#     # File should not be moved since hashes don't match
#     assert (root_dir / "original.txt").exists()
#     assert not (root_dir / "new_place.txt").exists()
