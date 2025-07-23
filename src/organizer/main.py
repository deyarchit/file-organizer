import logging

import typer
from dotenv import load_dotenv
from typing_extensions import Annotated

from .llm import IntelligentFileOrganizer
from .logging_config import setup_logging
from .organizer import Organizer

load_dotenv()
app = typer.Typer()

logger = logging.getLogger(__name__)


@app.command()
def organize(
    path: str,
    llm_model: Annotated[
        str,
        typer.Option(
            help="llm model to use for generating options eg. gemini/gemini-2.5-flash, gemini/gemini-2.0-flash"
        ),
    ] = "gemini/gemini-2.5-flash",
    show_logs: Annotated[bool, typer.Option(help="Enable/Disable logs")] = False,
) -> None:
    if show_logs:
        setup_logging()
        logger.info("Starting organizer under path: %s", path)
    try:
        llm = IntelligentFileOrganizer(llm_model)
        organizer = Organizer(path, llm_client=llm)
        organizer.organize()
    except Exception as e:
        logger.error("Error organizing files: %s", e)
        typer.secho(f"Error organizing files: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
