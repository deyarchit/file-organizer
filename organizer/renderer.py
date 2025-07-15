from typing import List, Union, Dict
from .models import FlatFileItem, OrganizationStrategy
from rich.tree import Tree
from rich.table import Table
from rich.console import Console
import os


class ConsoleRenderer:
    def __init__(self):
        self.console = Console()

    def generate_file_tree(self, items: List[FlatFileItem]) -> Tree:
        # Find common prefix directory
        raw_paths = [item.path for item in items]
        prefix = os.path.commonprefix(raw_paths)

        # Ensure we only use directory boundaries (not partial filenames)
        prefix = prefix[: prefix.rfind("/") + 1] if "/" in prefix else ""

        # Use cleaned-up prefix for the tree label
        root_label = f"📁 {prefix.strip('/') or '.'}"
        tree = Tree(root_label)

        def insert_path(root: Dict, parts: List[str], item: FlatFileItem) -> None:
            for part in parts[:-1]:
                root = root.setdefault(part, {})
            final_part = parts[-1]
            if item.path.endswith("/"):
                root.setdefault(final_part, {})
            else:
                root[final_part] = item

        fs_tree: Dict[str, Union[FlatFileItem, dict]] = {}
        for item in items:
            relative_path = os.path.relpath(item.path, prefix) if prefix else item.path
            parts = [p for p in relative_path.strip("/").split("/") if p]
            if parts:
                insert_path(fs_tree, parts, item)

        def add_to_tree(
            parent: Tree, node: Union[Dict, FlatFileItem], label: str = ""
        ) -> None:
            if isinstance(node, dict):
                folder_tree = parent.add(f"📁 {label}" if label else "📁")
                for name in sorted(node):
                    add_to_tree(folder_tree, node[name], name)
            else:
                desc = f"📄 {label}"
                parent.add(desc)

        for name in sorted(fs_tree):
            add_to_tree(tree, fs_tree[name], name)
        return tree

    def render_file_tree(self, items: List[FlatFileItem]) -> None:
        tree = self.generate_file_tree(items)
        self.console.print(tree)

    def render_organization_strategy(
        self, strategies: List[OrganizationStrategy]
    ) -> None:
        table = Table(
            title="Organization Strategies",
            show_header=True,
            header_style="bold magenta",
            show_lines=True,
        )
        table.add_column("No.")
        table.add_column("Strategy")
        table.add_column("Proposed Structure")
        for idx, strategy in enumerate(strategies):
            table.add_row(
                str(idx), strategy.name, self.generate_file_tree(strategy.items)
            )

        self.console.print(table)
