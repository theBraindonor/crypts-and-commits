from cac.mcp import campaign, docs, encounter, index, lore, prime, region, world
from cac.mcp.instance import mcp

_TOOL_MODULES = (world, prime, lore, region, campaign, encounter, index, docs)  # imported for registration side effects


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
