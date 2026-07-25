from cac.mcp import prime, world
from cac.mcp.instance import mcp

_TOOL_MODULES = (world, prime)  # imported for their @mcp.tool() registration side effects


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
