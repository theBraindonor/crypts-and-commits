from pathlib import Path

import typer
from rich.console import Console

from cac.cli.common import fail
from cac.core import campaign as campaign_core
from cac.core import encounter as encounter_core
from cac.core import prime as prime_core
from cac.core import world as world_core

app = typer.Typer(
    help=(
        "Assemble cross-object context in one call instead of chaining the individual "
        "world/lore/region/campaign/encounter reads. 'get' returns the global prime bundle; "
        "'applicable-lore' resolves the enabled lore set that applies to a specific encounter."
    )
)
console = Console()

_CAMPAIGN_HELP = "Campaign the encounter belongs to. Defaults to the active (open) campaign."


def _resolve_campaign(campaign: str | None) -> str:
    try:
        return campaign_core.resolve_campaign(Path.cwd(), campaign, require_mutable=False)
    except (campaign_core.NoActiveCampaignError, campaign_core.CampaignNotFoundError) as exc:
        fail(console, str(exc))


@app.command("get")
def get_prime() -> None:
    """Show the global prime bundle: world (full) + world-assigned lore (summaries) +
    region map (summary + path + assigned-lore edges) + active campaign (full body)."""
    try:
        bundle = prime_core.assemble_prime(Path.cwd())
    except world_core.WorldNotFoundError as exc:
        fail(console, str(exc))

    console.print("[bold]== World ==[/bold]")
    for key, value in bundle.world.metadata.items():
        console.print(f"[bold]{key}[/bold]: {value}")
    console.print()
    console.print(bundle.world.body, markup=False)

    console.print()
    console.print("[bold]== World Lore ==[/bold]")
    if not bundle.world_lore:
        console.print("No enabled lore is assigned to the world.")
    for entry in bundle.world_lore:
        console.print(f"[bold]{entry.name}[/bold]:", end=" ")
        console.print(entry.summary, markup=False)

    console.print()
    console.print("[bold]== Regions ==[/bold]")
    if not bundle.regions:
        console.print("No region files found.")
    for region in bundle.regions:
        console.print(f"[bold]{region.name}[/bold] (path: {region.path})")
        console.print("  summary:", end=" ")
        console.print(region.summary, markup=False)
        console.print(f"  assigned lore: {', '.join(region.assigned_lore) or '(none)'}")

    console.print()
    console.print("[bold]== Active Campaign ==[/bold]")
    if bundle.active_campaign is None:
        console.print("No campaign is currently open.")
    else:
        console.print(f"[bold]{bundle.active_campaign}[/bold]")
        console.print()
        console.print(bundle.campaign_body, markup=False)


@app.command("applicable-lore")
def applicable_lore(
    name: str = typer.Argument(..., help="Encounter name to resolve applicable lore for."),
    campaign: str | None = typer.Option(None, "--campaign", "-c", help=_CAMPAIGN_HELP),
) -> None:
    """Resolve the enabled lore set applicable to an encounter: world-assigned lore union
    lore assigned to the encounter's region(s)."""
    resolved_campaign = _resolve_campaign(campaign)
    try:
        entries = prime_core.applicable_lore(Path.cwd(), resolved_campaign, name)
    except encounter_core.EncounterNotFoundError as exc:
        fail(console, str(exc))

    if not entries:
        console.print("No applicable enabled lore was found for this encounter.")
        return

    for entry in entries:
        console.print(f"[bold]{entry.name}[/bold] (ref: {entry.ref}):", end=" ")
        console.print(entry.summary, markup=False)
