import os
import shutil
from typing import List, Optional, Tuple, Set
from .models import FlatFileItem
from .utils import _calculate_short_sha256


class FileSystemSync:
    def __init__(self, root_dir: str):
        if not os.path.isdir(root_dir):
            raise ValueError(f"❌ Root directory '{root_dir}' does not exist.")
        self.root_dir = root_dir
        self.real_root = os.path.realpath(root_dir)
        self.handled_paths: Set[str] = set()

    def sync(
        self, current_items: List[FlatFileItem], desired_items: List[FlatFileItem]
    ) -> None:
        """Apply changes to match the desired file structure."""
        missing, added = self.compare_structures(current_items, desired_items)
        self._create_directories(added)
        self._move_files_by_hash(missing, added)
        self._delete_missing_files(missing)
        self._delete_empty_dirs(missing)

    def _create_directories(self, added: List[FlatFileItem]) -> None:
        for item in added:
            if item.path.endswith("/"):
                full_path = self._to_abs(item.path)
                if not os.path.exists(full_path):
                    print(f"📁 Creating directory: {full_path}")
                    os.makedirs(full_path, exist_ok=True)
                self.handled_paths.add(item.path)

    def _move_files_by_hash(
        self, missing: List[FlatFileItem], added: List[FlatFileItem]
    ) -> None:
        src_by_hash = {
            i.hash: i for i in missing if not i.path.endswith("/") and i.hash
        }
        dst_by_hash = {i.hash: i for i in added if not i.path.endswith("/") and i.hash}

        for file_hash, src_item in src_by_hash.items():
            if file_hash not in dst_by_hash:
                continue

            dst_item = dst_by_hash[file_hash]
            src = self._to_abs(src_item.path)
            dst = self._to_abs(dst_item.path)

            if not self._is_safe(src) or not self._is_safe(dst):
                print(
                    f"⚠️ Skipping move from '{src_item.path}' to '{dst_item.path}' (outside root)."
                )
                continue

            os.makedirs(os.path.dirname(dst), exist_ok=True)
            print(f"📦 Moving file: {src} -> {dst}")
            shutil.move(src, dst)
            self.handled_paths.update({src_item.path, dst_item.path})

    def _delete_missing_files(self, missing: List[FlatFileItem]) -> None:
        for item in missing:
            if item.path in self.handled_paths or item.path.endswith("/"):
                continue

            full = self._to_abs(item.path)
            if not self._is_safe(full):
                print(f"⚠️ Skipping delete of '{item.path}' (outside root).")
                continue

            if os.path.exists(full):
                print(f"🗑️ Deleting file: {full}")
                os.remove(full)
                self.handled_paths.add(item.path)

    def _delete_empty_dirs(self, missing: List[FlatFileItem]) -> None:
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
            full = self._to_abs(dir_path)
            if not self._is_safe(full):
                print(f"⚠️ Skipping rmdir '{dir_path}' (outside root).")
                continue
            if os.path.isdir(full):
                try:
                    os.rmdir(full)
                    print(f"✅ Removed empty dir: {full}")
                except OSError:
                    pass  # Not empty

    def _to_abs(self, rel_path: str) -> str:
        return os.path.join(self.root_dir, rel_path.replace("/", os.sep))

    def _is_safe(self, path: str) -> bool:
        return os.path.realpath(path).startswith(self.real_root)

    @staticmethod
    def create_snapshot(root_dir: str) -> Optional[List[FlatFileItem]]:
        """Creates a flat list of all files and empty directories."""
        if not os.path.isdir(root_dir):
            print(f"Error: Directory '{root_dir}' does not exist.")
            return None

        items: List[FlatFileItem] = []
        for dirpath, dirnames, filenames in os.walk(root_dir):
            if not filenames and not dirnames:
                rel_path = os.path.relpath(dirpath, root_dir)
                if rel_path != ".":
                    items.append(FlatFileItem(path=rel_path.replace(os.sep, "/") + "/"))

            for filename in filenames:
                full_path = os.path.join(dirpath, filename)
                rel_path = os.path.relpath(full_path, root_dir)
                items.append(
                    FlatFileItem(
                        path=rel_path.replace(os.sep, "/"),
                        hash=_calculate_short_sha256(full_path),
                        size=os.path.getsize(full_path),
                    )
                )
        return sorted(items, key=lambda x: x.path)

    @staticmethod
    def compare_structures(
        current_items: List[FlatFileItem],
        desired_items: List[FlatFileItem],
        files_only: bool = False,
    ) -> Tuple[List[FlatFileItem], List[FlatFileItem]]:
        def item_key(item: FlatFileItem) -> str:
            if files_only and not item.path.endswith("/"):
                filename = os.path.basename(item.path)
                return f"{filename}::{item.hash}"
            return item.path if item.path.endswith("/") else f"{item.path}::{item.hash}"

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

        missing_keys = current_map.keys() - desired_map.keys()
        added_keys = desired_map.keys() - current_map.keys()

        missing = sorted([current_map[k] for k in missing_keys], key=lambda x: x.path)
        added = sorted([desired_map[k] for k in added_keys], key=lambda x: x.path)
        return missing, added
