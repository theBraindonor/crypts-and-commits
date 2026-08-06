---
archived: false
campaign: v0.1.7-rag-demo-application
created_by: John Hoff
created_on: '2026-08-06T16:17:47Z'
depends_on: []
name: render-markdown-chat-messages
regions:
- demo-ui
status: completed
updated_by: John Hoff
updated_on: '2026-08-06T16:54:41Z'
---

## Requirements

- Assistant chat messages are rendered as parsed Markdown (GFM: headings, emphasis/strong, inline code, fenced code blocks, links, ordered/unordered lists, blockquotes, tables, strikethrough, task lists) instead of the current raw-text `{message.content}` rendering with `white-space: pre-wrap`.
- User messages continue to render as plain text exactly as typed (no markdown parsing) — they are freeform question input, not authored markdown.
- Rendering must not execute or inject raw HTML from model output: no `dangerouslySetInnerHTML`, no `rehype-raw`. The library parses markdown directly to React elements.
- Links inside rendered markdown open in a new tab with `rel="noopener noreferrer"` (consistent with the header's GitHub link from `polish-demo-ui-chat-experience`).
- The message list continues to re-render correctly as streamed chunks arrive (`useChat`'s `onChunk` appends text to the last assistant message) — partial/incomplete markdown mid-stream (e.g. an unclosed code fence or bold marker) must not crash the app; it can render provisionally rough and resolve once the stream completes.
- Rendered markdown elements (headings, code blocks, inline code, lists, blockquotes, tables, links) are styled to fit the existing ink/parchment/brass palette in `Chat.css` — no CSS framework introduced, consistent with the region's documented "no CSS framework" convention; the markdown-rendering library itself is the one new dependency this encounter adds (confirmed with the GM — it is not a CSS framework or state-management library, so it doesn't conflict with that convention).
- Message bubble sizing/wrapping (`max-width: 80%`, background/color per role) is preserved for both roles, including block-level markdown content (e.g. tables) that must not overflow the bubble.
- No `demo-api` change — this is a `demo-ui`-only rendering concern; the wire format (newline-delimited JSON chunks of `{content}`) is unchanged.
- Automated tests cover: an assistant message with representative markdown (heading/bold/list/code/link/table) renders the corresponding semantic HTML elements; a user message containing markdown-looking text (e.g. `**not bold**`) renders literally, unparsed; links render with the new-tab/rel attributes; a partial/incomplete markdown chunk (simulating mid-stream) renders without throwing. `npm run build`, `npm run lint`, `npm test` all stay clean in `packages/demo-ui`.
- Out of scope: syntax highlighting inside code blocks (plain monospace styling only), math/LaTeX rendering, raw HTML passthrough, any change to `demo-api`, RAG grounding, conversation persistence.

## Rationale

- The most recently completed encounter (`add-chat-persona-and-context-priming`) gave the chat agent a persona plus this project's own world/lore/region/campaign context; a grounded assistant answering questions about CAC's sourcebook is likely to naturally reply with structured markdown (headings, lists, code spans referencing file paths, etc.), which the current UI displays as an unbroken wall of raw text with literal `#`/`*`/backtick characters — undermining the persona work just shipped.
- `react-markdown` + `remark-gfm` was chosen, after asking the GM directly, over a hand-rolled parser or an HTML-string + sanitizer pipeline (`marked` + DOMPurify), because it parses markdown directly to React elements with no `dangerouslySetInnerHTML` step and no raw-HTML passthrough by default — the safest option against model-output-driven XSS — while still covering GFM tables/task lists/strikethrough that a minimal hand-rolled renderer would not.
- Restricting markdown parsing to assistant messages only (not user messages) matches how the two roles are actually produced: assistant content comes from an LLM that may emit markdown; user content is raw keyboard input a person typed into a plain `<input>`, where literal `**` or `#` characters should show up exactly as typed, not be reinterpreted.
- Styling rendered elements via plain CSS (targeting the markdown container's child selectors) keeps the region's "no CSS framework" convention intact — the new dependency is a markdown parser/renderer, not a styling system.

## Plan

1. Add `react-markdown` and `remark-gfm` to `packages/demo-ui/package.json` dependencies; run `npm install` in `packages/demo-ui`.
2. In `Chat.tsx`, import `ReactMarkdown` and `remarkGfm`; for messages with `role === 'assistant'`, render `<ReactMarkdown remarkPlugins={[remarkGfm]}>{message.content}</ReactMarkdown>` wrapped in a `chat__message-content` div instead of `{message.content}` directly; for `role === 'user'`, keep rendering `{message.content}` as plain text unchanged.
3. Configure link rendering: pass a `components` prop to `ReactMarkdown` overriding `a` to render with `target="_blank"` and `rel="noopener noreferrer"` (mirroring the Header's existing GitHub-link pattern).
4. Update `Chat.css`: add scoped styles for markdown output inside `.chat__message--assistant` (via `.chat__message-content`) — headings sized down to fit the bubble, `code`/`pre` in a monospace font with a subtle background using the existing palette tokens, `blockquote` with a left border, `table`/`th`/`td` with light borders, `ul`/`ol` with normal list indentation — all using existing CSS custom properties (`--color-ink`, `--color-parchment-dim`, `--color-brass`, etc.), no new colors introduced. Ensure block-level content (e.g. tables) stays within the `.chat__message`'s `max-width: 80%` bubble rather than overflowing.
5. Update `Chat.test.tsx`: add a test asserting an assistant message with markdown (e.g. `**bold** and a [link](https://example.com)`) renders a `<strong>` element and an `<a>` with `href="https://example.com"`, `target="_blank"`, `rel="noopener noreferrer"`; add a test asserting a user message containing `**not bold**` renders that literal text with no `<strong>` element; add a test asserting a partial/unterminated markdown chunk (e.g. an assistant message ending mid code-fence) renders without throwing.
6. Run `npm run build`, `npm run lint`, `npm test` in `packages/demo-ui`; fix anything either surfaces.
7. Manual verification: run `demo-ui`'s dev server against a running `demo-api`, ask a question likely to produce a structured answer (e.g. "what is this project, in a bulleted list?"), and confirm the reply renders as actual markdown (headings/lists/code formatting) rather than literal `#`/`*`/backtick characters, that bubble/layout styling still looks correct, and that a typed message containing literal `**` characters stays literal.

## Verification

- `npm run build`, `npm run lint`, `npm test` all pass in `packages/demo-ui`, including the new/updated `Chat.test.tsx` markdown-rendering tests.
- `pdm run pytest -q` and `pdm run ruff check .` / `ruff format .` stay clean (unaffected — no Python files change).
- Manual run as in Plan step 7, confirmed in a browser: assistant replies render formatted markdown (not raw syntax characters), links open in a new tab, user-typed markdown-looking text stays literal, and the existing ink/parchment/brass bubble styling is preserved.

## Log

### Review - 2026-08-06T16:29:46Z - John Hoff

Reviewed against the single applicable lore item, clean-tests-and-lint (world-assigned): the Plan correctly and explicitly acknowledges this encounter changes only packages/demo-ui (TypeScript/npm), so the Python-specific pdm run pytest -q / ruff gate is unaffected rather than bypassed - no skip markers, --no-verify, or suppressions are introduced. Spot-checks of Chat.tsx, Chat.css, and package.json confirm the Plan's stated baseline (raw {message.content} with pre-wrap, existing --color-ink/--color-parchment-dim/--color-brass tokens, no CSS-framework/state-mgmt dependency) matches current code, and the one new dependency (react-markdown + remark-gfm) is consistent with the region's "no CSS framework" convention as the encounter itself notes was confirmed with the GM. No lore conflicts found; approved to proceed to reviewed.

### Message - 2026-08-06T16:41:30Z - John Hoff

Implementation complete. Added react-markdown + remark-gfm to packages/demo-ui/package.json; Chat.tsx now renders assistant messages via ReactMarkdown (remarkGfm plugin, a components override forcing links to target="_blank" rel="noopener noreferrer") wrapped in a new .chat__message-content div, while user messages keep rendering as plain text unchanged. Chat.css adds scoped styles for headings/paragraphs/lists/blockquotes/code/pre/tables/links inside .chat__message-content, reusing only existing palette custom properties (--color-ink, --color-ink-soft, --color-parchment, --color-parchment-dim, --color-brass, --color-brass-dark) - no new colors. Chat.test.tsx gained three tests: assistant markdown renders <strong>/<a> with correct href/target/rel, a user message containing "**not bold**" stays literal (no <strong>), and a partial/unterminated code-fence chunk renders without throwing.

Verification: npm run build, npm run lint (oxlint), and npm test (20/20 passing) all clean in packages/demo-ui. pdm run pytest -q (773 passed) and ruff check/format clean, unaffected since no Python files changed. Manual verification: ran demo-api (uvicorn, port 8000) and demo-ui (vite dev, port 5175) together in a real browser, asked "What is this project, answer in a bulleted list with a code span and a link?" and confirmed the streamed assistant reply rendered actual markdown - bold text, a bulleted list, inline code spans, and a link - styled within the existing ink/parchment/brass palette and message-bubble layout, with the rendered link carrying target="_blank" and rel="noopener noreferrer" (confirmed via DOM inspection). Also sent a user message containing literal "**not bold** and # not a heading" and confirmed via DOM inspection it rendered as literal text with no <strong>/<h1-3> elements, i.e. unparsed. Both dev servers stopped after verification.

### Completed - 2026-08-06T16:54:41Z - John Hoff

Markdown chat rendering shipped and verified: assistant replies render via react-markdown + remark-gfm within the existing ink/parchment/brass palette, user input stays literal plain text, links open safely in a new tab. npm run build/lint/test clean (20/20), pdm run pytest -q (773 passed) and ruff clean, manual browser verification confirmed correct rendering and styling.
