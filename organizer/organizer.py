from litellm import completion
from typing import List, Callable
from functools import wraps
from organizer.disk_operations import DiskOperations
from dotenv import load_dotenv
from organizer.models import FlatFileItem, LLMResponseSchema, OrganizationStrategy
from .renderer import ConsoleRenderer
from rich.progress import Progress, SpinnerColumn, TextColumn
import typer

load_dotenv()


def progress_task(description: str) -> Callable:
    """A decorator to show a progress spinner for a function call."""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                transient=True,
            ) as progress:
                task_id = progress.add_task(description=description, total=None)
                try:
                    return func(*args, **kwargs)
                finally:
                    progress.remove_task(task_id)

        return wrapper

    return decorator


class FileOrganizer:
    def __init__(self, root_path: str, renderer: ConsoleRenderer | None = None):
        self.root_path = root_path
        self.disk_ops = DiskOperations(root_path)
        self.renderer = renderer if renderer is not None else ConsoleRenderer()

    @progress_task("Generating options...")
    def generate_options(
        self, current_structure: List[FlatFileItem]
    ) -> LLMResponseSchema:
        response = completion(
            model="gemini/gemini-2.5-flash",
            response_format=LLMResponseSchema,
            messages=[
                {"content": system_prompt, "role": "system"},
                {"content": str(current_structure), "role": "user"},
            ],
            temperature=0.0,
        )

        parsed_response: LLMResponseSchema = LLMResponseSchema.model_validate_json(
            response.choices[0].message.content
        )
        return parsed_response

    @progress_task("Validating options...")
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

    def select_strategy(self, proposed_structures: List[OrganizationStrategy]) -> int:
        while True:
            try:
                selected = typer.prompt(
                    "Select the reorganization strategy no.", type=int
                )
                if not 0 <= selected < len(proposed_structures):
                    typer.secho(
                        f"Invalid selection. Enter a number between 0 and {len(proposed_structures) - 1}.",
                        fg=typer.colors.RED,
                    )
                    continue

                typer.echo(f"You selected: {proposed_structures[selected].name}")
                if typer.confirm("Are you sure you want to proceed?", abort=False):
                    return selected

            except ValueError:
                typer.echo("Invalid input. Please enter a number.")

    def apply_strategy(
        self,
        current_structure: List[FlatFileItem],
        proposed_structure: List[FlatFileItem],
    ) -> None:
        self.disk_ops.sync(current_structure, proposed_structure)

    def organize(self) -> None:
        try:
            current_structure: List[FlatFileItem] | None = (
                DiskOperations.create_snapshot(self.root_path)
            )
            if current_structure:
                self.renderer.render_file_tree(current_structure)
            else:
                typer.secho(
                    "No files found in the specified directory.", fg=typer.colors.YELLOW
                )
                return

            parsed_response = self.generate_options(current_structure)
            if self.validate_options(current_structure, parsed_response.strategies):
                self.renderer.render_organization_strategy(parsed_response.strategies)
            else:
                return

            option = self.select_strategy(parsed_response.strategies)
            self.apply_strategy(
                current_structure, parsed_response.strategies[option].items
            )

        except Exception as e:
            print(f"An error occurred: {e}")


system_prompt = """
You are an expert file system organizer. Your task is to analyze the provided directory structure and propose up to three distinct, logical, and practical reorganization plans. Each plan should aim to improve clarity, accessibility, and reduce clutter.

For each proposed plan, you must output a JSON object that adheres strictly to the defined `response_schema`.

Your proposed plans could provide suggestions that:
* **Group similar file types** (e.g., all `.csv` files, all `.xml` files).
* **Consolidate files related to the same project or client**
* **Reduce unnecessary nested subfolders.**
* **You are encouraged to rename folders to improve organization but do not rename files.**


Present your suggestions as a JSON array, where each element is one of your proposed organization strategy JSON object.
    """
