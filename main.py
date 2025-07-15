import typer
from organizer.organizer import FileOrganizer

app = typer.Typer()


@app.command()
def organize(path: str) -> None:
    organizer = FileOrganizer(path)
    organizer.organize()


if __name__ == "__main__":
    app()
