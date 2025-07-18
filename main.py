import logging

import typer
from dotenv import load_dotenv
from typing_extensions import Annotated

from organizer.organizer import FileOrganizer
from utils.logging_config import setup_logging

load_dotenv()
app = typer.Typer()

logger = logging.getLogger(__name__)


@app.command()
def organize(
    path: str, show_logs: Annotated[bool, typer.Option(help="Enable/Disable logs")] = False
) -> None:
    if show_logs:
        setup_logging()
    logger.info("Starting organizer under path: %s", path)
    organizer = FileOrganizer(path)
    organizer.organize()


if __name__ == "__main__":
    app()
