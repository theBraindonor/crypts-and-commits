from pathlib import Path

from cac.core import docs as docs_core
from langchain_core.tools import BaseTool, tool


def build_tools(root: Path) -> list[BaseTool]:
    def list_docs() -> list[dict]:
        """List all packaged reference docs by name and summary."""
        return [{"name": name, "summary": summary} for name, summary in docs_core.list_docs()]

    def get_doc(name: str) -> dict:
        """Get a packaged reference doc's summary and full body by name."""
        return {"name": name, "summary": docs_core.doc_summary(name), "body": docs_core.read_doc(name)}

    return [tool(list_docs), tool(get_doc)]
