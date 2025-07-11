import os
import shutil
from typing import List, Optional, Tuple, Set
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
) -> Tuple[List[FlatFileItem], List[FlatFileItem]]:
    """
    Compares file system items and returns missing and added items.

    Args:
        current_items: List of FlatFileItem from current state.
        desired_items: List of FlatFileItem from desired state.
        files_only: If True, only compare file name and hash (ignore directories and paths).

    Returns:
        missing (List[FlatFileItem]): Items in current but not in desired.
        added (List[FlatFileItem]): Items in desired but not in current.
    """

    def item_key(item: FlatFileItem) -> str:
        if files_only and not item.path.endswith("/"):
            filename = os.path.basename(item.path)
            return f"{filename}::{item.hash}"
        if item.path.endswith("/"):
            return item.path
        return f"{item.path}::{item.hash}"

    current_map = {
        item_key(item): item
        for item in current_items
        if not files_only or not item.path.endswith("/")
    }
    desired_map = {
        item_key(item): item
        for item in desired_items
        if not files_only or not item.path.endswith("/")
    }

    current_keys = set(current_map.keys())
    desired_keys = set(desired_map.keys())

    missing_keys = current_keys - desired_keys
    added_keys = desired_keys - current_keys

    missing = sorted([current_map[k] for k in missing_keys], key=lambda x: x.path)
    added = sorted([desired_map[k] for k in added_keys], key=lambda x: x.path)

    return missing, added


def apply_changes(
    current_items: List[FlatFileItem],
    desired_items: List[FlatFileItem],
    root_dir: str,
) -> None:
    """
    Applies filesystem changes to match the desired structure, ensuring all
    operations are securely within the root_dir.
    """
    if not os.path.isdir(root_dir):
        print(f"Error: Root directory '{root_dir}' does not exist.")
        return

    # Get the real, absolute path of the root directory for security checks
    real_root_dir = os.path.realpath(root_dir)

    missing_items, added_items = compare_structures(current_items, desired_items)

    handled_paths = set()

    # Step 1: Create directories
    for item in added_items:
        if item.path.endswith("/"):
            full_path = os.path.join(root_dir, item.path.replace("/", os.sep))
            if not os.path.exists(full_path):
                print(f"Creating directory: {full_path}")
                os.makedirs(full_path, exist_ok=True)
            handled_paths.add(item.path)

    # Step 2: Move files by hash
    missing_files_by_hash = {
        item.hash: item
        for item in missing_items
        if not item.path.endswith("/") and item.hash
    }
    added_files_by_hash = {
        item.hash: item
        for item in added_items
        if not item.path.endswith("/") and item.hash
    }

    for file_hash, old_item in missing_files_by_hash.items():
        if file_hash in added_files_by_hash:
            new_item = added_files_by_hash[file_hash]

            full_old_path = os.path.join(root_dir, old_item.path.replace("/", os.sep))
            full_new_path = os.path.join(root_dir, new_item.path.replace("/", os.sep))

            # Ensure both source and destination are within the root directory
            real_old_path = os.path.realpath(full_old_path)
            real_new_path = os.path.realpath(full_new_path)

            if not real_old_path.startswith(
                real_root_dir
            ) or not real_new_path.startswith(real_root_dir):
                print(
                    f"Skipping move from '{old_item.path}' to '{new_item.path}' as it's outside the target directory."
                )
                continue

            dest_dir = os.path.dirname(full_new_path)
            if not os.path.exists(dest_dir):
                os.makedirs(dest_dir, exist_ok=True)

            print(
                f"Moving file (matched by hash): '{full_old_path}' -> '{full_new_path}'"
            )
            shutil.move(full_old_path, full_new_path)

            handled_paths.add(old_item.path)
            handled_paths.add(new_item.path)

    # Step 3: Delete remaining missing files
    for item in missing_items:
        if item.path in handled_paths or item.path.endswith("/"):
            continue

        full_path = os.path.join(root_dir, item.path.replace("/", os.sep))

        # Ensure the path to be deleted is within the root directory
        if not os.path.realpath(full_path).startswith(real_root_dir):
            print(
                f"Skipping deletion of '{item.path}' because it is outside the target directory."
            )
            continue

        if os.path.exists(full_path):
            print(f"Removing file: {full_path}")
            os.remove(full_path)
            handled_paths.add(item.path)

    # Step 4: Delete empty directories (bottom-up)
    dirs_to_check: Set[str] = set()
    for item in missing_items:
        # Start with the directory itself if it's a dir, or the file's parent dir.
        path = item.path
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

        # Ensure the directory to be deleted is within the root directory
        if not os.path.realpath(full_path).startswith(real_root_dir):
            print(
                f"Skipping rmdir on '{dir_path}' because it is outside the target directory."
            )
            continue

        if os.path.isdir(full_path):
            try:
                os.rmdir(full_path)
                print(f"Removed empty directory: {full_path}")
            except OSError:
                pass
