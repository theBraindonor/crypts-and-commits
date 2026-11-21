from inspect import cleandoc

from mcp.server.mcpserver import MCPServer


class CleanDescriptionServer(MCPServer):
    """MCPServer that registers cleaned docstrings, since the SDK passes them through verbatim."""

    def tool(self, *args, description: str | None = None, **kwargs):
        def decorate(function):
            cleaned = description
            if cleaned is None and function.__doc__ is not None:
                cleaned = cleandoc(function.__doc__)
            return super(CleanDescriptionServer, self).tool(*args, description=cleaned, **kwargs)(function)

        return decorate


mcp = CleanDescriptionServer("crypts-and-commits")
