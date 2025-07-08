import os
import shutil
from typing import List, Optional, Tuple
from .models import FlatFileItem
from .utils import _calculate_md5


def create_json_from_dir(root_dir: str) -> Optional[List[FlatFileItem]]:
    """
    Scans a directory and creates a flat list of file items and empty directories only.
    """
    if not os.path.isdir(root_dir):
        print(f"Error: Directory '{root_dir}' does not exist.")
        return None

    items: List[FlatFileItem] = []

    for dirpath, dirnames, filenames in os.walk(root_dir):
        # Check for empty directories
        if not filenames and not dirnames:
            rel_path = os.path.relpath(dirpath, root_dir)
            # FIX: Do not include the root directory itself ('.')
            if rel_path != ".":
                items.append(FlatFileItem(path=rel_path.replace(os.sep, "/") + "/"))

        for filename in filenames:
            full_path = os.path.join(dirpath, filename)
            rel_path = os.path.relpath(full_path, root_dir)
            items.append(
                FlatFileItem(
                    path=rel_path.replace(os.sep, "/"),
                    hash=_calculate_md5(full_path),
                    size=os.path.getsize(full_path),
                )
            )

    return sorted(items, key=lambda x: x.path)


def compare_structures(
    current_items: List[FlatFileItem],
    desired_items: List[FlatFileItem],
    files_only: bool = False,
) -> Tuple[List[str], List[str]]:
    """
    Compares file system items and returns missing and added paths.

    Args:
        current_items: List of FlatFileItem from current state.
        desired_items: List of FlatFileItem from desired state.
        files_only: If True, only compare file name and hash (ignore directories and paths).

    Returns:
        missing (List[str]): Paths in current but not in desired.
        added (List[str]): Paths in desired but not in current.
    """

    def item_key(item: FlatFileItem) -> str:
        if files_only and not item.path.endswith("/"):
            filename = os.path.basename(item.path)
            return f"{filename}::{item.hash}"
        if item.path.endswith("/"):
            return item.path
        return f"{item.path}::{item.hash}"

    current_keys = {
        item_key(item)
        for item in current_items
        if not files_only or not item.path.endswith("/")
    }
    desired_keys = {
        item_key(item)
        for item in desired_items
        if not files_only or not item.path.endswith("/")
    }

    missing = sorted([k.split("::")[0] for k in (current_keys - desired_keys)])
    added = sorted([k.split("::")[0] for k in (desired_keys - current_keys)])

    return missing, added


def apply_changes(
    current_items: List[FlatFileItem],
    desired_items: List[FlatFileItem],
    root_dir: str,
) -> None:
    """
    Applies filesystem changes to match the desired structure, including the removal
    of nested empty directories.
    """
    if not os.path.isdir(root_dir):
        print(f"Error: Root directory '{root_dir}' does not exist.")
        return

    current_map = {item.path: item for item in current_items}
    desired_map = {item.path: item for item in desired_items}

    missing_paths, added_paths = compare_structures(current_items, desired_items)

    handled_paths = set()

    # Step 1: Create directories (no changes)
    for path in added_paths:
        if path.endswith("/"):
            full_path = os.path.join(root_dir, path.replace("/", os.sep))
            if not os.path.exists(full_path):
                print(f"Creating directory: {full_path}")
                os.makedirs(full_path, exist_ok=True)
            handled_paths.add(path)

    # Step 2: Move files by hash (no changes)
    missing_files_by_hash = {
        item.hash: item
        for path, item in current_map.items()
        if path in missing_paths and not path.endswith("/") and item.hash
    }
    added_files_by_hash = {
        item.hash: item
        for path, item in desired_map.items()
        if path in added_paths and not path.endswith("/") and item.hash
    }

    for file_hash, old_item in missing_files_by_hash.items():
        if file_hash in added_files_by_hash:
            new_item = added_files_by_hash[file_hash]
            old_rel_path = old_item.path
            new_rel_path = new_item.path

            full_old_path = os.path.join(root_dir, old_rel_path.replace("/", os.sep))
            full_new_path = os.path.join(root_dir, new_rel_path.replace("/", os.sep))
            dest_dir = os.path.dirname(full_new_path)

            if not os.path.exists(dest_dir):
                os.makedirs(dest_dir, exist_ok=True)

            print(
                f"Moving file (matched by hash): '{full_old_path}' -> '{full_new_path}'"
            )
            shutil.move(full_old_path, full_new_path)

            handled_paths.add(old_rel_path)
            handled_paths.add(new_rel_path)

    # Step 3: Delete remaining missing files (no changes)
    for path in missing_paths:
        if path in handled_paths or path.endswith("/"):
            continue
        full_path = os.path.join(root_dir, path.replace("/", os.sep))
        if os.path.exists(full_path):
            print(f"Removing file: {full_path}")
            os.remove(full_path)
            handled_paths.add(path)

    # Step 4: Delete empty directories (bottom-up)
    # This logic now correctly handles nested empty directories.
    dirs_to_check = set()
    for path in missing_paths:
        # Start with the directory itself if it's a dir, or the file's parent dir.
        current_dir = path.strip("/") if path.endswith("/") else os.path.dirname(path)

        # Walk up the tree, adding each parent to the set of candidates for removal.
        while current_dir:
            dirs_to_check.add(current_dir)
            parent = os.path.dirname(current_dir)
            # Stop if we hit the top of the relative path.
            if parent == current_dir:
                break
            current_dir = parent

    # Sort by depth (deepest first) to ensure we delete subdirectories before parents.
    for dir_path in sorted(
        list(dirs_to_check), key=lambda p: p.count("/") + p.count("\\"), reverse=True
    ):
        full_path = os.path.join(root_dir, dir_path.replace("/", os.sep))
        # Check if directory exists and is empty before trying to remove it.
        if os.path.isdir(full_path):
            try:
                os.rmdir(full_path)
                print(f"✅ Removed empty directory: {full_path}")
            except OSError:
                # This is expected if the directory is not empty.
                pass
