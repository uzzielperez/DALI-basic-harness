---
name: analysis-writeup-builder
description: Builds (or refreshes) the pipeline write-up of an analysis — motivation, step-by-step DAG, CI/CD, validation gates, systematic-sources section, per-bin results matrix — from the analysis code repo plus a draft (analysis note PDF, Overleaf project, internal note). Asks the user first how to track the write-up: (a) markdown in the repo (docs/), (b) an Overleaf project via the git bridge, or (c) both kept in sync with markdown as source of truth. Audits the draft against the repo, writes the document, compiles if it targets LaTeX, and optionally publishes to the project web page. Use when the user says "write up the pipeline", "build the pipeline doc", "organize everything in a document", "push this write-up to Overleaf", or after a big organizing session that must become a durable document.
---

# Analysis write-up builder

Turns the state of an analysis (code + draft + gates + results) into one
durable document. This skill is **analysis-agnostic**: it carries no
channel-specific knowledge and resolves its paths per analysis, exactly like
`pipeline-checker`. The Λb→Λγ run (`lb02lbgammabr`) is only the *reference
implementation* whose sections are the default template — every concrete value
below is an **example**, never a requirement.

## Step 0 — Resolve the anchors (ask the user for what's missing)

Same anchors as `pipeline-checker`, plus one publish target. Resolve them for
*your* analysis; nothing here is hard-coded. If an anchor is ambiguous, STOP and
ask — never guess a repo path or a reference value. Record the resolved set in
`state/anchors.yaml` so a later run does not rediscover it.

| Anchor | What it is | How to find it in a new repo | Example (Λb→Λγ run) |
|--------|------------|------------------------------|----------------------|
| `REPO` | root of the analysis/reconstruction code | dir with `Snakefile` / `python/<step>/` / `docs/` | a workspace checkout of the analysis repo |
| `DRAFT` | the draft being written up | user-provided | AN draft PDF or Overleaf project id |
| `HARNESS` | gate definitions + gated runner | dir with gate / gate-runner scripts; optional | the project's `*-harness` dir |
| `GOLD` | pinned reference values | pinned `*.json` refs, published-paper PDFs; optional | the published BR/yields/ε/syst refs |
| `WEB` | publish target | site host + a sync script; optional | `<project>.web.cern.ch` + `scripts/sync_public_html.sh` |

## Step 1 — ASK how the user wants to track it (mandatory, first question)

Use the IDE question tool with exactly these options:

1. **Markdown in the repo** — `docs/PIPELINE_OVERVIEW.md` (+ sibling docs).
   Best: code-reviewable, diffable, lives with the code.
2. **Overleaf project** — LaTeX document in a given project.
   Best: the document IS the deliverable (AN chapter, note for circulation).
3. **Both (recommended)** — markdown in the repo is the source of truth;
   the Overleaf copy is generated and pushed; a refresh re-generates it.

Record the choice in `docs/PIPELINE_OVERVIEW.md` header line
`tracking: markdown|overleaf|both (overleaf id <hex>)` so later runs skip
the question.

## Step 2 — Gather (read-only)

Same audit as `pipeline-checker` Mode 1 (reuse it if present): steps from
the draft (PDF via pymupdf / .tex via git bridge), steps from the repo
(docs, dir order, Snakemake configs, orchestrator), pipeline variants per
bin (closure vs updated — never merged), gate inventory, missing-results
matrix with golden column. Honesty rules apply: every number traces to a
source; inferred → `needs_review`; never edit a golden reference.

## Step 3 — Write the document (fixed section arc)

1. **Motivation** — 4 bullets max: physics why, why now, why a replication
   pipeline.
2. **Pipeline & DAG** — step table (what/code/outputs) + diagram
   (mermaid in markdown, TikZ in LaTeX) + hard ordering constraints called
   out explicitly.
3. **CI/CD** — what is automated today (table) + the target pipeline
   (lint → tests → gates → pages), with which gates block merges and what
   stays manual.
4. **Validation gates** — gate inventory table (id, kind, rule, on-failure),
   golden references, current honest status incl. documented GAPs.
5. **Systematic-uncertainty sources** (if the analysis has a budget) —
   per-source: what it is, reference value, method used here, status
   OK/OVER/GAP.
6. **Results matrix per bin** — headline quantities highlighted against the
   golden benchmark; FIXME cells = the to-run list.
7. **Pipeline-to-run map** — each missing quantity → concrete command.

## Step 4 — Deliver per the tracking choice

**Markdown:** write `docs/PIPELINE_OVERVIEW.md` (+ `VALIDATION_GATES*.md`,
`SYSTEMATICS_SOURCES.md`, `RESULTS_BY_YEAR.md` as siblings; cross-link).

**Overleaf round-trip (the recipe that works):**
```bash
# one-time clone via the git bridge (token in URL, no password prompt)
git clone "https://git@git.overleaf.com/<PROJECT_ID>" workdir && cd workdir
# edit main.tex, then compile-check locally before pushing
pdflatex -interaction=nonstopmode -halt-on-error main.tex   # fix until exit 0
pdflatex -interaction=nonstopmode main.tex                  # refs pass
git add -A && git commit -m "<what changed>" && git push origin main
```
Gotchas learned: `\documentclass` (not `\document`), `J/ψ` as
`$J/\psi$` (no `\jpsi`), `\checkmark` needs `amssymb`, `<`/`_` inside
`\texttt{}` need `\mbox{<YEAR>}` or escaping, always push only after a
clean local compile — Overleaf compiles whatever you push.
For **both**: markdown is edited by hand; regenerate the .tex sections from
it (keep section headings 1:1 so diffs stay readable), compile, push.

**Publish (optional, if `WEB` set):** copy the compiled PDF (or HTML) into
the repo `docs/`, add it to the site sync script + landing-page tab, run
the sync script with its strict verify.

## Step 5 — Report

Chat: 5-line summary (sections written, tracking mode, compile/publish
status, paths/URL). Detail lives in the document. End with the NEXT action
(e.g. "review on Overleaf", or "fill FIXME via the pipeline-to-run map").

## Refresh mode

Re-running the skill on an existing write-up = diff, not rewrite: re-audit,
list what changed (new results, gates flipped, new FIXMEs), update only
those sections, bump a `Updated: <date>` line. Never silently reflow text
the user has edited by hand — if the doc has hand edits, ask before
touching their sections.
