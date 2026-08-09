---
archived: true
campaign: v0.1.7-rag-demo-application
created_by: John Hoff
created_on: '2026-08-06T14:18:26Z'
depends_on: []
name: polish-demo-ui-chat-experience
regions:
- demo-ui
status: completed
updated_by: John Hoff
updated_on: '2026-08-09T14:09:05Z'
---

## Requirements

- The "Chat coming soon." placeholder note in `Chat.tsx`'s empty message list is removed. The message area simply renders empty (no note) until the first message exists — no replacement copy is invented.
- The chat experience (header content and the chat panel) is width-constrained on large screens: a shared `--content-max-width` (720px) applied consistently, centered via `margin: 0 auto`, with the existing side padding preserved below that width. Vertical layout (full-height flex column) is unchanged.
- The header gains a "New chat" control that clears the current conversation: resets the message list, clears any error, and forgets the current `thread_id` so the next message starts a fresh backend thread. Disabled while a response is streaming (`sending`) and when there are no messages yet (nothing to clear).
- The header gains a link to `https://github.com/theBraindonor/crypts-and-commits` (opens in a new tab, `rel="noopener noreferrer"`, accessible label), giving a way to close the loop back to the project repo from the running demo.
- The UI is re-themed to a palette derived from this project's own banner art (`docs/images/banner-xlarge.png` — parchment/aged-paper background, dark ink, brass/gold accents, teal-green glow) and cross-checked against `braindonor.net`'s published stylesheet for concrete values:
  - `--color-ink: #14172a` (primary text; also the header background, per GM direction to keep a dark header bar)
  - `--color-ink-soft: #5a5f72` (secondary text)
  - `--color-ink-muted: #787e8a` (muted/placeholder text)
  - `--color-parchment: #f4f2eb` (page/chat background)
  - `--color-parchment-dim: #d2d0c2` (borders, assistant message bubble background, dividers)
  - `--color-brass: #c98a26` (primary accent: send button, focus states, "checking" status dot)
  - `--color-brass-dark: #8a5f18` (hover/active state for brass-accented controls)
  - `--color-verdigris: #3f8f7a` (secondary accent: "online" status dot, replacing the current generic green)
  - `--color-white: #ffffff`
  - Offline status dot becomes a muted rust red (`#a13c2c`) instead of the current bright red, to stay in the aged-parchment/brass family rather than a stock semantic red.
  These become CSS custom properties in `index.css`'s `:root`, replacing the hard-coded hex values currently scattered across `Header.css` and `Chat.css` (header background, status dots, message bubble colors, input/border colors, send button). No new fonts are introduced — the existing system-font stack stays as-is; this pass is colors and layout only.
- The dashed placeholder-style border on `.chat__messages` (`1px dashed #ccc`) is replaced with a solid `--color-parchment-dim` border, since a dashed "under construction" affordance no longer fits now that the chat is a finished feature, not a stub.
- No new dependencies (no icon library, no font loading, no CSS framework, no state-management library) - the GitHub link icon is an inline SVG in `Header.tsx`, consistent with the region's existing "no CSS framework" convention.
- Automated tests cover the new/changed behavior: the empty-state note is gone, the header's New Chat button clears messages/error/thread_id and is disabled appropriately, and the GitHub link renders with the correct `href`/`target`/`rel`. `npm run build`, `npm run lint`, and `npm test` all stay clean in `packages/demo-ui`.
- Explicitly out of scope: RAG grounding, conversation persistence across reloads, any `demo-api`/backend change, production deploy/reachability, embedding the banner image itself in the UI (only its color palette is used), and any font change.

## Rationale

- The "chat coming soon" note was accurate placeholder copy for the scaffold stage; `wire-demo-ui-chat-endpoint` made the chat real, so the note is now stale and should go, per the GM's explicit ask - without inventing new marketing copy to replace it, since that wasn't requested and risks scope creep into product-voice decisions that belong to the GM.
- Constraining width only (leaving the already-fine vertical flex layout alone) matches the GM's precise framing of the problem: full-bleed chat on a wide monitor reads as unfinished, not that the vertical rhythm needs rework.
- Lifting `useChat()` out of `Chat.tsx` and into `App.tsx` (passing `messages`/`sending`/`error`/`sendMessage` down as props, alongside a new `resetChat`) is the only way to give the header - a sibling of `Chat`, not a descendant - control over clearing the conversation without introducing React Context or a state-management library, both of which the region's own documented conventions rule out for a change this small.
- Disabling "New chat" during `sending` avoids a race between an in-flight stream callback (`useChat`'s `onChunk` closure) writing into a message list that's just been cleared; disabling it with zero messages is a minor polish (nothing to clear) rather than a strict requirement.
- The GitHub link closes the loop the GM described - someone using the deployed demo can reach the project that built it - and an inline SVG keeps that a zero-dependency change, consistent with the region's "no new libraries" pattern already established by the prior two `demo-ui` encounters.
- The palette is derived from two sources deliberately, not invented: the project's own banner art (the aesthetic this repo already presents to readers of its `README.md`) and `braindonor.net`'s live stylesheet (the GM's own explicitly-cited inspiration, fetched and read directly rather than guessed at), giving concrete, defensible hex values instead of a subjective color choice. The verdigris secondary accent and rust-toned offline dot are the one place this encounter extrapolates beyond directly-copied values (the site has no dark-surface or status-dot precedent to draw from), chosen to stay within the same aged-parchment-and-metal family established by the two source palettes.
- Keeping the header's dark background (retinted, not removed) was confirmed with the GM directly rather than assumed, since the two source palettes disagree on this point (the personal site has no dark header at all).
- Replacing the dashed message-list border removes a visual cue ("this is a placeholder area") that's no longer true and was never a themed color to begin with - it was `#ccc`, disconnected from either source palette.

## Plan

1. Add the palette as CSS custom properties to `index.css`'s `:root` (see the exact values in Requirements), plus `--content-max-width: 720px`.
2. Update `Header.css`: header background to `--color-ink`, title/status text to `--color-parchment`/`--color-white`, status dots to `--color-brass` (checking), `--color-verdigris` (online), `#a13c2c` (offline). Add a `.app-header__inner` wrapper (`max-width: var(--content-max-width); margin: 0 auto; width: 100%;` with the existing horizontal padding moved onto it) so header content aligns with the chat panel's width. Style the new New Chat button and GitHub link to sit legibly on the dark header (parchment/brass text, subtle hover state).
3. Update `Header.tsx`: wrap existing content in the new `.app-header__inner` div; add a `.app-header__actions` group containing (a) a "New chat" `<button>` calling a new `onNewChat` prop, `disabled={newChatDisabled}`, and (b) an `<a>` to `https://github.com/theBraindonor/crypts-and-commits` with an inline SVG icon, `target="_blank"`, `rel="noopener noreferrer"`, and an accessible label (`aria-label="View source on GitHub"`). `Header` takes two new required props: `onNewChat: () => void` and `newChatDisabled: boolean`.
4. Update `useChat.ts`: add a `resetChat` callback (`setMessages([]); setError(null); threadIdRef.current = undefined`, guarded the same way `sendMessage` already is against no-ops mid-stream by disabling the button in the UI rather than inside the hook) and return it alongside the existing fields.
5. Update `App.tsx`: call `useChat()` once here; pass `messages`, `sending`, `error`, `sendMessage` down to `<Chat>` as props, and `onNewChat={resetChat}` plus `newChatDisabled={sending || messages.length === 0}` down to `<Header>`. Wrap the app body so `.app-header__inner`'s width logic has a matching constrained container for `<Chat>` (see step 6).
6. Update `Chat.tsx` to a presentational component driven entirely by props (`messages`, `sending`, `error`, `sendMessage`) instead of calling `useChat()` itself; remove the `Chat coming soon.` note (render nothing when `messages.length === 0`); apply `--content-max-width` (centered, existing padding preserved) to the `.chat` container.
7. Update `Chat.css`: message-list border to solid `--color-parchment-dim`; user bubble to `--color-ink` bg / `--color-parchment` text; assistant bubble to `--color-parchment-dim` bg / `--color-ink` text; input border to `--color-parchment-dim` with a `--color-brass` focus ring; send button to `--color-brass` bg (hover `--color-brass-dark`); error text kept legible against parchment (adjust only if the existing `#c0392b` clashes once surrounding colors change).
8. Update `Header.test.tsx`: pass the now-required `onNewChat`/`newChatDisabled` props in every existing `render(<Header ... />)` call; add tests for the New Chat button (calls `onNewChat` on click; respects `newChatDisabled`) and the GitHub link (`href`, `target`, `rel`, accessible name).
9. Rewrite `Chat.test.tsx` as a pure prop-driven component test (no `fetch` mocking needed once `Chat` no longer owns `useChat`): renders provided `messages`; shows no empty-state note when `messages` is empty; disables input while `sending`; renders `error` text; calls the provided `sendMessage` prop on submit.
10. Add `useChat.test.ts` under `src/hooks/`: covers `resetChat` clearing `messages`/`error`/the internal `thread_id` ref (observable via the next `sendMessage` call's request body omitting `thread_id`), using the same mocked-`fetch`-with-`ReadableStream` pattern `Chat.test.tsx` used previously.
11. Add `App.test.tsx`: one integration-style test (mocked `fetch`) sending a message, clicking "New chat" in the header, and confirming the message list is empty and the next `sendMessage` call's request omits `thread_id`.
12. Run `npm run build`, `npm run lint`, `npm test` in `packages/demo-ui`.
13. Manual verification: run `demo-ui`'s dev server, confirm at a wide viewport (e.g. 1920px) that the header and chat panel are both constrained and centered rather than full-bleed, confirm the empty state shows no placeholder text, send a message, click "New chat" mid-idle and confirm the conversation clears, click the GitHub link and confirm it opens the repo in a new tab, and eyeball the palette against `docs/images/banner-xlarge.png` for a reasonable match.

## Verification

- `npm run build`, `npm run lint`, `npm test` all pass in `packages/demo-ui`, including the new/rewritten `Chat.test.tsx`, `Header.test.tsx` additions, new `useChat.test.ts`, and new `App.test.tsx`.
- `pdm run pytest -q` and `pdm run ruff check .` / `ruff format .` stay clean (unaffected - no Python files change).
- Manual run as in Plan step 13, confirmed in a browser: fixed-width layout at large viewport widths, no stale placeholder copy, working New Chat control (with correct disabled states), working GitHub link, and a palette that visibly reads as drawn from the banner/parchment-and-brass theme rather than the prior generic dark-navy/gray scheme.

## Log

### Review - 2026-08-06T14:20:28Z - John Hoff

Reviewed against the sole applicable lore item, `clean-tests-and-lint` (world-assigned; no lore is currently assigned to the `demo-ui` region). The Plan complies: Verification correctly notes `pdm run pytest -q` and `ruff check`/`format` are unaffected since this encounter touches only `packages/demo-ui` (npm/Vite, outside the PDM workspace), and instead gates on `npm run build`/`lint`/`test` as the frontend equivalent — a reasonable substitution given the tooling split, though not literally specified by any lore. No skip markers, `--no-verify`, or lint suppressions are proposed anywhere in the Plan. Since no region-specific lore is assigned to `demo-ui`, the Plan's other frontend conventions (no new dependencies, no state-management/CSS-framework libraries, width-constrained layout) are grounded in the region's own documented body text rather than a codified lore object — noted as out of scope for this lore-based review, not as a conflict. PASS-WITH-NOTES.

### Completed - 2026-08-06T14:39:05Z - John Hoff

All Requirements met and Verification passed. npm run build/lint/test all clean in packages/demo-ui (17/17 tests passing, including 3 new Header tests for New Chat/GitHub link, a rewritten prop-driven Chat.test.tsx, a new useChat.test.ts covering resetChat, and a new App.test.tsx integration test). pdm run pytest -q (771 passed) and ruff check/format stayed clean and unaffected, since no Python files changed. Manual dual-server run confirmed in a real browser at 1920px: the header and chat panel are both width-constrained (720px) and centered rather than full-bleed, the "Chat coming soon" placeholder is gone, a real streamed reply rendered correctly styled (ink/parchment bubbles), "New chat" cleared the conversation and correctly reverted to disabled, and the GitHub link opened https://github.com/theBraindonor/crypts-and-commits in a new tab. The re-themed palette (dark ink header, parchment body, brass/verdigris accents) visibly reads as drawn from the banner art and braindonor.net's stylesheet rather than the prior generic dark-navy/gray scheme. Confirmed complete with the GM.
