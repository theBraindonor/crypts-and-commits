from cac.mcp import boss, campaign, docs, encounter, index, lore, prime, region, ruling, rumor, world
from cac.mcp.instance import mcp

_TOOL_MODULES = (
    world,
    prime,
    lore,
    region,
    campaign,
    encounter,
    index,
    docs,
    boss,
    rumor,
    ruling,
)  # registration side effects


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
