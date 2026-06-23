# Standards for `/docs` directory

Follow these guidelines when maintaining the docs.

## Writing style

- Never use em dashes (`--`, `---`, or Unicode `—`). Use a hyphen `-` or rewrite the sentence.
- Prefer clear, specific writing over filler.
- Avoid hype adjectives/adverbs (bold, brutal, honest, quietly, seamless, ...) that add tone but no information;
  cut them or state the concrete fact instead.
- Headers are plain labels in sentence case, no parentheticals.
  Don't start a header with an article or filler: write `Folder structure`, not `The folder structure`.
- Do not format md files by wrapping text to a certain line length;
  add newlines on logical breaks, even within paragraphs or bullet points, eg after a period/semicolon or between clauses.
  This file is a sample of this style.
- State each fact once, in the most specific page that owns it; link to it from elsewhere rather than restating.
  Index and overview pages may summarize; detail pages own the canonical statement.
- Explain functionality, concepts, usage patterns, not code details unless necessary. Link to code files for details.

## Markdown & links

- Links are relative paths between pages, so they resolve on GitHub as well as the built site.
- Link to code files with relative paths too, for the same reason.
- Guides should not be full of code blocks; explain the concept in prose and link to the code.
  Reserve fenced blocks for short commands or snippets the reader needs verbatim.
- Tag every fenced block with its language.
- Filenames are snake_case (`README.md` is the one exception).

## Folder structure

- Use `docs/README.md` as the main entry point for the documentation.
- `mkdocs` will handle the creation of `reference` folder for API reference, do not create it manually.
- `docs/guides`: overarching guides for the project, with explanations about cross-cutting concerns, dependencies, and usage patterns.
- `docs/library`: matches the `src` folder structure, contains high level documentation for each module, with links to code files for details.
