import typer

from cac.cli.common import configure_output_encoding
from cac.cli.bootstrap import app as bootstrap_app
from cac.cli.campaign import app as campaign_app
from cac.cli.encounter import app as encounter_app
from cac.cli.lore import app as lore_app
from cac.cli.prime import app as prime_app
from cac.cli.region import app as region_app
from cac.cli.world import app as world_app

app = typer.Typer(
    name="cac",
    help="Crypts and Commits CLI.",
    context_settings={"help_option_names": ["-h", "--help"]},
)
app.add_typer(bootstrap_app, name="bootstrap")
app.add_typer(campaign_app, name="campaign")
app.add_typer(encounter_app, name="encounter")
app.add_typer(lore_app, name="lore")
app.add_typer(prime_app, name="prime")
app.add_typer(region_app, name="region")
app.add_typer(world_app, name="world")


@app.callback()
def main() -> None:
    """Crypts and Commits - a Coding Assistant Continuity Framework."""
    configure_output_encoding()
