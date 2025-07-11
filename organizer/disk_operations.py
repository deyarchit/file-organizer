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
    current_items: List[FlatFileItem], desired_items: List[FlatFileItem], root_dir: str
) -> None:
    """Apply changes to the filesystem to match desired structure."""
    if not os.path.isdir(root_dir):
        print(f"❌ Root directory '{root_dir}' does not exist.")
        return

    real_root = os.path.realpath(root_dir)
    missing_items, added_items = compare_structures(current_items, desired_items)
    handled: Set[str] = set()

    _create_directories(added_items, root_dir, handled)
    _move_files_by_hash(missing_items, added_items, root_dir, real_root, handled)
    _delete_missing_files(missing_items, root_dir, real_root, handled)
    _delete_empty_dirs(missing_items, root_dir, real_root)


def _create_directories(
    added_items: List[FlatFileItem], root_dir: str, handled: Set[str]
) -> None:
    for item in added_items:
        if item.path.endswith("/"):
            full_path = os.path.join(root_dir, item.path.replace("/", os.sep))
            if not os.path.exists(full_path):
                print(f"📁 Creating directory: {full_path}")
                os.makedirs(full_path, exist_ok=True)
            handled.add(item.path)


def _move_files_by_hash(
    missing: List[FlatFileItem],
    added: List[FlatFileItem],
    root: str,
    real_root: str,
    handled: Set[str],
) -> None:
    src_by_hash = {i.hash: i for i in missing if not i.path.endswith("/") and i.hash}
    dst_by_hash = {i.hash: i for i in added if not i.path.endswith("/") and i.hash}

    for file_hash, old in src_by_hash.items():
        if file_hash not in dst_by_hash:
            continue

        new = dst_by_hash[file_hash]
        src = os.path.join(root, old.path.replace("/", os.sep))
        dst = os.path.join(root, new.path.replace("/", os.sep))
        if not _safe_path(src, real_root) or not _safe_path(dst, real_root):
            print(f"⚠️ Skipping move from '{old.path}' to '{new.path}' (outside root).")
            continue

        os.makedirs(os.path.dirname(dst), exist_ok=True)
        print(f"📦 Moving file: {src} -> {dst}")
        shutil.move(src, dst)
        handled.update({old.path, new.path})


def _delete_missing_files(
    missing: List[FlatFileItem], root: str, real_root: str, handled: Set[str]
) -> None:
    for item in missing:
        if item.path in handled or item.path.endswith("/"):
            continue
        full = os.path.join(root, item.path.replace("/", os.sep))
        if not _safe_path(full, real_root):
            print(f"⚠️ Skipping delete of '{item.path}' (outside root).")
            continue
        if os.path.exists(full):
            print(f"🗑️ Deleting file: {full}")
            os.remove(full)
            handled.add(item.path)


def _delete_empty_dirs(missing: List[FlatFileItem], root: str, real_root: str) -> None:
    dirs = set()
    for item in missing:
        path = item.path
        current = path.strip("/") if path.endswith("/") else os.path.dirname(path)
        while current:
            dirs.add(current)
            parent = os.path.dirname(current)
            if parent == current:
                break
            current = parent

    for dir_path in sorted(
        dirs, key=lambda p: p.count("/") + p.count("\\"), reverse=True
    ):
        full = os.path.join(root, dir_path.replace("/", os.sep))
        if not _safe_path(full, real_root):
            print(f"⚠️ Skipping rmdir '{dir_path}' (outside root).")
            continue
        if os.path.isdir(full):
            try:
                os.rmdir(full)
                print(f"✅ Removed empty dir: {full}")
            except OSError:
                pass  # Not empty


def _safe_path(path: str, root: str) -> bool:
    return os.path.realpath(path).startswith(root)
