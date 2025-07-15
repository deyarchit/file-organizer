from typing import List, Dict, Any
from .models import FlatFileItem, OrganizationStrategy
from rich.tree import Tree
from rich.table import Table
from rich.console import Console
import os


class ConsoleRenderer:
    def __init__(self):
        self.console = Console()

    def generate_file_tree(self, items: List[FlatFileItem]) -> Tree:
        if not items:
            return Tree("📁 .")

        paths = [item.path for item in items]
        prefix = os.path.commonprefix(paths)
        if "/" in prefix:
            prefix = prefix[: prefix.rfind("/") + 1]
        else:
            prefix = ""

        root_label = f"📁 {prefix.strip('/') or '.'}"
        tree = Tree(root_label)
        fs_tree: Dict[str, Any] = {}

        for item in items:
            rel_path = os.path.relpath(item.path, prefix) if prefix else item.path
            parts = [p for p in rel_path.strip("/").split("/") if p]
            current = fs_tree
            for part in parts[:-1]:
                current = current.setdefault(part, {})
            final = parts[-1]
            if item.path.endswith("/"):
                current.setdefault(final, {})
            else:
                current[final] = item

        def build_tree(parent: Tree, node: Any, label: str) -> None:
            if isinstance(node, dict):
                folder = parent.add(f"📁 {label}" if label else "📁")
                for key in sorted(node):
                    build_tree(folder, node[key], key)
            else:
                parent.add(f"📄 {label}")

        for key in sorted(fs_tree):
            build_tree(tree, fs_tree[key], key)

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
