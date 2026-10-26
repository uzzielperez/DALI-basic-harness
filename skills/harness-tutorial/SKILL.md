---
name: harness-tutorial
description: Teaches the domain-free `ras` verification harness end to end. Use when the user asks how `ras` works, how to index a corpus and answer questions with citations, what gates/remedies/golden sets are, or wants a guided first run of the rag-ai-scientist harness.
---

# Harness Tutorial (Packaged Skill)

`ras` answers questions from a corpus and is only allowed to say "done" when deterministic gates agree. Retrieval is lexical (BM25 over a local index): no model, no network, no API keys, and the same input always produces the same verdict.

## Mental model

```
corpus ──index──▶ chunks ──retrieve──▶ citations ──validate──▶ gates decide
                                                              │
                                             pass ◀───────────┤──────────── fail
                                                               ▼
                                                          correct + retry
```

You never grade the answer. You write the **golden set** (the exam) and the **gates** (the rules); the loop does the rest and journals everything into `runs/<run-id>/`.

## Step 0 — watch it first

`ras demo` runs the whole thing against a throwaway project (`--fast` for instant output, `--slow` or `--speed N` to slow the pacing down, `--keep` to inspect afterwards). Do this before touching a real project.

## Step 1 — scaffold

```bash
ras init-project --project-root ~/my-paper
```

Writes `configs/harness.yaml`, `docs/references/papers/` and `evals/golden/`.

## Step 2 — corpus

Drop `.pdf`, `.md` or `.txt` files in `docs/references/papers/`. Keep one fact per file when you can: the gates require a term to appear in at most `gates.min_terms` of the chunks, so a fact that lives in exactly one file is easy to pin down.

## Step 3 — the golden set

One JSON/YAML file in `evals/golden/` (or point `questions.path` at it):

```json
{"name": "my-questions", "questions": [
  {"id": "Q01", "tier": 1, "question": "What integrated luminosity was recorded?",
   "expect": "supported", "expect_keywords": ["9 fb", "luminosity"]},
  {"id": "Q99", "tier": 1, "question": "What was the solenoid field strength?",
   "expect": "unresolved", "expect_keywords": ["tesla"]}
]}
```

- `tier: 1` must resolve (`questions.tier1_min`, default 1.0); tiers 2-3 may miss up to `tier23_min`.
- `expect: unresolved` is a **negative control** — the corpus deliberately lacks it. A harness that invents the answer fails the gate. Include at least one.
- `expect_keywords` must be terms that literally appear in the retrieved text.

## Step 4 — index

```bash
ras index --project-root ~/my-paper
```

Chunks by `index.chunk_chars` with `chunk_overlap`. The chunk fingerprint is recorded so a later run can prove the index did not drift.

## Step 5 — the loop

```bash
ras run --project-root ~/my-paper
```

PLAN → EXECUTE → VALIDATE → (CORRECT → retry, up to `run.max_attempts`). `ras run --json` for machine output; `--resume` continues a run.

## Step 6 — read the verdict

```bash
ras eval --project-root ~/my-paper      # tier pass rates, citation validity
ras report --project-root ~/my-paper    # re-render report.md
```

`report.md` is the reproducible one-pager: config hash, corpus/index inventory, plan table, gate results, and the exact commands to re-run everything.

## Gate → meaning → remedy

| Gate | It means | If it fails |
|---|---|---|
| `index_files`, `index_integrity`, `index_deterministic` | corpus found, chunked, reproducible | add files; check `corpus.paths`/`extensions`; re-run `ras index` |
| `analysis_map_shape`, `analysis_map_nonempty` | every question produced a status | lower `retrieval.min_score` or raise `top_k` (the loop already tries this remedy) |
| `citations_resolve` | every claim points at retrieved text | do not hand-edit answers; fix the corpus so the fact is retrievable |
| `claim_status_valid` | supported/unresolved is honest | check `min_terms` — too low and trivia passes as support |
| `golden_tiers` | the exam was passed | add the missing fact to the corpus, never to the answer |

A failing gate is information about the **corpus and config**, never something to argue with. Remedies are pre-declared in `configs/harness.yaml`; the loop is not allowed to improvise.

## Step 7 — keep the skill

A passing run generates a skill (SKILL.md + one file per planned step). `ras skills list|show|promote` — `promote` is the human gate that moves a run-scoped skill into the project so later runs and IDE clients reuse it. Resolution order: run → project → `.cursor/skills` → packaged defaults.

## Rules

1. Never edit an answer to satisfy a gate; change the corpus or the config.
2. Always keep a negative control in the golden set.
3. Re-run before you trust: determinism is a claim the harness verifies, not assumes.
4. Everything needed to reproduce a run lives in `runs/<run-id>/`.

Human walkthrough with expected output: `docs/TUTORIAL.md` in the repository.