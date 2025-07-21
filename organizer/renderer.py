import os
from typing import Any, Dict, List

import typer
from rich.console import Console
from rich.table import Table
from rich.tree import Tree

from .models import FlatFileItem, OrganizationStrategy


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
        self.console.print("\n[bold cyan]Current folder structure:[/bold cyan]")
        tree = self.generate_file_tree(items)
        self.console.print(tree)

    def render_organization_strategy(self, strategies: List[OrganizationStrategy]) -> None:
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
            table.add_row(str(idx + 1), strategy.name, self.generate_file_tree(strategy.items))

        self.console.print(table)

    def select_strategy(self, proposed_structures: List["OrganizationStrategy"]) -> int:
        while True:
            self.console.print("\n[bold cyan]Available Reorganization Strategies:[/bold cyan]")
            for i, strategy in enumerate(proposed_structures, start=1):
                self.console.print(f"[cyan]{i}.[/cyan] {strategy.name}")

            selected_str = typer.prompt("Enter the number of the strategy you want to select")
            if not selected_str.isdigit():
                typer.secho("Invalid input. Please enter a number.", fg=typer.colors.RED)
                continue

            selected = int(selected_str) - 1
            if not 0 <= selected < len(proposed_structures):
                typer.secho(
                    f"Invalid selection. Enter a number between 1 and {len(proposed_structures)}.",
                    fg=typer.colors.RED,
                )
                continue

            self.console.print(f"You selected: [bold]{proposed_structures[selected].name}[/bold]")
            if typer.confirm("Are you sure you want to proceed?", abort=False):
                return selected
