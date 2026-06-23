# Docs maintenance

A sanity check to run when the docs or the code change, so the two stay in sync.
The writing and layout rules themselves live in [the standards](../standards.md); this page is about keeping the docs complete and consistent over time.

Work through the checklist below.
The commands assume you run them from the repo root.

## 1. Every package has a library page

The [library tree](../library/README.md) mirrors [`src/laife/`](../../src/laife) one to one.
When a package is added or removed, the library pages must follow.
This command lists the difference between the source packages and the library pages; empty output means they match.

```bash
comm -3 \
  <(find src/laife -mindepth 1 -maxdepth 1 -type d -printf '%f\n' | sort) \
  <(ls docs/library/*.md | xargs -n1 basename | sed 's/.md//' | grep -v README | sort)
```

How it works:
the first process substitution lists the package folder names under `src/laife`, sorted.
The second lists the library page names: `ls` the pages, strip the directory with `basename`, drop the `.md` suffix with `sed`, and remove the `README` index with `grep -v`, sorted.
`comm -3` prints only the lines that are not common to both lists, so any package without a page, or any page without a package, shows up.
A line indented with a tab comes from the second list (an extra page); a flush-left line comes from the first (a missing page).

## 2. No dead links to source files

Library pages link to source files with relative `../../src/...` paths.
A rename or move on the code side leaves those links dangling.
This command extracts every referenced source path and reports the ones that no longer exist.

```bash
grep -rhoE '\.\./\.\./src/laife[A-Za-z0-9_/]*\.py' docs/library/*.md docs/guides/*.md \
  | sed 's#\.\./\.\./##' | sort -u \
  | while read -r p; do [ -e "$p" ] || echo "MISSING: $p"; done
```

The `sed` rewrites each `../../src/...` link to a path relative to the repo root, so the existence test runs from where you invoke it.

## 3. New pages follow the standards

Skim new or changed pages against [the standards](../standards.md): sentence-case headers, snake_case filenames, no em dashes, relative links.
The em-dash check is the easy one to automate, but match the Unicode character, not the ASCII `--`, which is also a CLI flag and a Markdown comment:

```bash
grep -rn '—' docs
```

Headers and filenames are quick to eyeball; there is no reliable one-liner that does not also flag legitimate prose.

## 4. The site still builds strict

The build is the final gate, and it is what CI runs through [the docs workflow](../../.github/workflows/docs.yml).
Strict mode turns broken internal links and bad references into errors.

```bash
uv run mkdocs build --strict
```

Relative links to source files point outside the site and would warn, but [`mkdocs.yml`](../../mkdocs.yml) silences exactly those through its `validation` block, so a clean strict build means the internal navigation and the API reference are sound.

## 5. Tricky points stay documented

Some things are easy to get wrong and worth a sentence somewhere when they change:

- the prompt templates and their versioning, see [the prompts page](../library/prompts.md);
- the environment variables that select stage and location, see [params and config](params_config.md);
- the SDL2 requirement for pygame, see [getting started](getting_started.md);
- resetting the singleton between tests, see [the meta page](../library/meta.md).

When you add a new cross-cutting concern, consider whether it belongs in a guide and whether a term belongs in [the glossary](glossary.md).
