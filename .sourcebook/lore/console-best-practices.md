---
assigned_regions:
- crypts-and-commits
assigned_to_world: false
enabled: true
name: console-best-practices
---

# Console Best Practices

Conventions for using `rich.Console` in `cac/cli/*` modules.

## Body content must not be treated as markup

`rich.Console()` defaults to `markup=True`, which parses `[...]` in printed text as Rich markup tags and silently strips anything it doesn't recognize. Any text that originates from stored project content (a lore/region/campaign/encounter/world body, or any future free-form user input) must be printed with `console.print(text, markup=False)`. This was discovered the hard way: `[tool.pdm.workspace]`, `[tool.ruff]`, and a `[[wiki-link]]` all silently vanished from `cac ... get` output before the fix.

Markup is fine - and expected - for text the CLI itself constructs, such as `console.print(f"Created [bold green]{path}[/bold green]")` or frontmatter key/value lines. The rule is about the *source* of the text, not the presence of brackets: CLI-authored strings may use markup; stored/user-authored strings must not be interpreted as markup.

## When adding a new command

Before adding a `console.print()` call, ask: does this text come from a `.sourcebook` file's body (or other stored/free-form content) rather than being built by the CLI itself? If yes, pass `markup=False`.
