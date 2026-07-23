import typer

from cac.cli.bootstrap import app as bootstrap_app

app = typer.Typer(
    name="cac",
    help="Crypts and Commits CLI.",
    context_settings={"help_option_names": ["-h", "--help"]},
)
app.add_typer(bootstrap_app, name="bootstrap")


@app.callback()
def main() -> None:
    """Crypts and Commits - a Coding Assistant Continuity Framework."""
