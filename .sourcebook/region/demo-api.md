---
name: demo-api
path: packages/demo-api
summary: 'Aspirational backend region at `packages/demo-api` - currently only a scaffold
  (pyproject.toml, README), no app code yet. Intended: a FastAPI RAG chatbot that
  answers questions about this project from `.sourcebook` content, via a LangChain
  agent over swappable OpenAI/Anthropic models. Retrieval should read the sourcebook
  through the `cac` package, not by parsing markdown directly. Framework choices are
  the current plan, not settled - confirm before assuming.'
---

# Demo API (backend)

The backend of a demonstration web application showing off crypts-and-commits in action. This region is currently aspirational - the package exists only as a scaffold (`pyproject.toml`, `README.md`) with no dependencies or application code yet.

## Intended shape

A **FastAPI** project implementing a simple RAG (retrieval-augmented generation) chatbot. The chatbot's retrieval context is `.sourcebook` content (world, lore, regions, campaigns, encounters) - it answers questions about the project using the same sourcebook an assistant would use to prime its own context.

- **FastAPI** for the HTTP layer.
- A **LangChain**-based agent for orchestration, backed by either **OpenAI** or **Anthropic** models (model choice is intended to be swappable, not hard-coded to one provider).
- Retrieval is expected to read `.sourcebook` content through the `cac` package/CLI rather than parsing the markdown files directly - reuse `cac.core`, don't reimplement sourcebook parsing here.

## Status

Not yet started. Treat any specifics above (framework choices, retrieval approach) as the current plan, not settled fact - confirm with the user before assuming implementation details not yet reflected in code.
