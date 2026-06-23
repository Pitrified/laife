# Docs maintenance

A sanity check to run when the docs or the code change, so the two stay in sync.
The writing and layout rules themselves live in [the standards](../standards.md); this page is about keeping the docs complete and consistent over time.

Work through the checklist below.
The commands assume you run them from the repo root.

## 1. Every package has a library page

The [library tree](../library/README.md) mirrors [`src/laife/`](https://github.com/Pitrified/laife/tree/main/src/laife) one to one.
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

Links to files outside `docs/` are absolute GitHub URLs on `main` (see [the standards](../standards.md)), since a relative path would break on the published site.
Those URLs are not checked by the build, so a rename or move on the code side leaves them dangling silently.
This command extracts the repo-relative path from every such URL and reports the ones that no longer exist locally.

```bash
grep -rhoE 'https://github.com/Pitrified/laife/(blob|tree)/main/[A-Za-z0-9_./-]+' docs \
  | sed -E 's#.*/main/##' | sort -u \
  | while read -r p; do [ -e "$p" ] || echo "MISSING: $p"; done
```

The `sed` strips the URL prefix up to `main/`, leaving a path relative to the repo root, so the existence test runs from where you invoke it.

## 3. New pages follow the standards

Skim new or changed pages against [the standards](../standards.md): sentence-case headers, snake_case filenames, no em dashes, relative links.
The em-dash check is the easy one to automate, but match the Unicode character, not the ASCII `--`, which is also a CLI flag and a Markdown comment:

```bash
grep -rn '—' docs
```

Headers and filenames are quick to eyeball; there is no reliable one-liner that does not also flag legitimate prose.

## 4. The site still builds strict

The build is the final gate, and it is what CI runs through [the docs workflow](https://github.com/Pitrified/laife/blob/main/.github/workflows/docs.yml).
Strict mode turns broken internal links and bad references into errors.

```bash
uv run mkdocs build --strict
```

All in-site links are relative paths between doc pages, and links to repo files are absolute GitHub URLs, so nothing points outside the site with a relative path.
A clean strict build therefore means the internal navigation and the API reference are sound; it does not check the external GitHub URLs, which is what check 2 is for.

## 5. Tricky points stay documented

Some things are easy to get wrong and worth a sentence somewhere when they change:

- the prompt templates and their versioning, see [the prompts page](../library/prompts.md);
- the environment variables that select stage and location, see [params and config](params_config.md);
- the SDL2 requirement for pygame, see [getting started](getting_started.md);
- resetting the singleton between tests, see [the meta page](../library/meta.md).

When you add a new cross-cutting concern, consider whether it belongs in a guide and whether a term belongs in [the glossary](glossary.md).
