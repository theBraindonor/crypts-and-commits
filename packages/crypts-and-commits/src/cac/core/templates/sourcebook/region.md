---
name: ""
path: ""
---

# Region

This region has not been described yet.

## Example

A region documents a path within the repository that needs its own conventions, tech
stack, or tooling described, and to which specific lore rules can be applied. For
example, a "frontend" region covering `src/frontend` might contain:

> This region is a React 18 + TypeScript single-page application built with Vite. State
> is managed with Zustand, styling uses Tailwind CSS, and API calls go through the
> generated OpenAPI client in `src/frontend/api`. Components are function components
> with PascalCase filenames, and each component colocates its test as `*.test.tsx`. Run
> `npm run lint` and `npm run test` from `src/frontend` before considering any change
> complete.
