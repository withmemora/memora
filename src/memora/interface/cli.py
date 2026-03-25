"""Memora CLI interface."""

import typer

app = typer.Typer(name="memora", help="Git-style versioned memory for LLMs")


@app.command()
def version():
    """Show version information."""
    print("Memora 0.1.0")


@app.command()
def init():
    """Initialize a new Memora repository."""
    print("Memora repository initialized")


if __name__ == "__main__":
    app()
