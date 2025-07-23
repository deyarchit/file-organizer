import logging
from typing import List

import typer

from organizer.disk_operations import DiskOperations
from organizer.llm import IntelligentFileOrganizer
from organizer.models import FlatFileItem, LLMResponseSchema, OrganizationStrategy

from .renderer import ConsoleRenderer, render_progress_task

logger = logging.getLogger(__name__)


class Organizer:
    def __init__(
        self,
        root_path: str,
        llm_client: IntelligentFileOrganizer,
        renderer: ConsoleRenderer | None = None,
    ):
        self.root_path = root_path
        self.llm_client = llm_client
        self.disk_ops = DiskOperations(root_path)
        self.renderer = renderer if renderer is not None else ConsoleRenderer()

    @render_progress_task("Generating options...")
    def generate_options(self, current_structure: List[FlatFileItem]) -> LLMResponseSchema:
        return self.llm_client.generate_reorganization_strategies(current_structure)

    @render_progress_task("Validating options...")
    def validate_options(
        self,
        current_structure: List[FlatFileItem],
        proposed_structures: List[OrganizationStrategy],
    ) -> bool:
        all_valid = True
        for strategy in proposed_structures:
            missing, added = DiskOperations.compare_structures(
                current_structure, strategy.items, files_only=True
            )
            if len(missing) > 0 or len(added) > 0:
                typer.echo(
                    f"Files added/removed from proposed strategy, skipping. Added: {len(added)} Removed: {len(missing)}"
                )
                all_valid = False
        return all_valid

    def apply_strategy(
        self,
        current_structure: List[FlatFileItem],
        proposed_structure: List[FlatFileItem],
    ) -> None:
        self.disk_ops.sync(current_structure, proposed_structure)

    def organize(self) -> None:
        try:
            current_structure: List[FlatFileItem] | None = DiskOperations.create_snapshot(
                self.root_path
            )
            if current_structure:
                self.renderer.render_file_tree(current_structure)
            else:
                typer.secho("No files found in the specified directory.", fg=typer.colors.YELLOW)
                return

            parsed_response = self.generate_options(current_structure)
            if self.validate_options(current_structure, parsed_response.strategies):
                self.renderer.render_organization_strategy(parsed_response.strategies)
            else:
                return

            option = self.renderer.render_strategy_selection(parsed_response.strategies)
            self.apply_strategy(current_structure, parsed_response.strategies[option].items)

            current_structure = DiskOperations.create_snapshot(self.root_path)
            if current_structure:
                self.renderer.render_file_tree(current_structure)

        except Exception as e:
            logger.error("An error occurred: %s", e)
