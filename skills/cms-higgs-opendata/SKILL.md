---
name: cms-higgs-opendata
description: Guides replication of the CMS 125 GeV Higgs discovery physics story using CMS open data, rag-ai-scientist RAG retrieval, and the official HiggsExample20112012 tutorial. Use when the user wants CMS Run-1 open data, H→γγ or H→ZZ→4ℓ pedagogy, dataset pointers, or clarification on educational vs official CMS results.
---

# CMS Higgs open data — same physics story with rag-ai-scientist

## Goal

Help the user **tell the same physics story** as the Run-1 CMS observation of a new boson near **125 GeV**, using **public CMS open data and documented tutorials**, while being honest about **scope** (educational replication, not a bit-identical reproduction of CMS-HIG-12-028).

## Before you improvise

1. Prefer **retrieval-augmented answers**: call **`query_analysis_knowledge`** with concrete questions once the project has indexed docs (see below).
2. Indexable narrative lives at **`docs/examples/cms_higgs_opendata_physics_story.md`** in the **source tree** of `rag-ai-scientist`; PyPI-only installs should **copy** that file into their `--references-dir` or add its path under `configs/references.yaml`, then run **`rag-ai-scientist setup-rag --project-root ...`**.

## Canonical external assets (cite these to the user)

| Asset | URL |
|-------|-----|
| Higgs rediscovery-style tutorial (2011–2012) | https://github.com/cms-opendata-analyses/HiggsExample20112012 |
| CERN Open Data Portal | https://opendata.cern.ch/ |
| CMS Open Data Guide | https://cms-opendata-guide.web.cern.ch/ |
| CMS guide for education | https://opendata.cern.ch/docs/cms-guide-for-education |
| CMS publication CMS-HIG-12-028 (public page) | https://cms-results.web.cern.ch/cms-results/public-results/publications/HIG-12-028/ |

## Suggested user journey

1. **Choose channel emphasis**
   - **Four leptons** \(H \to ZZ \to 4\ell\) — matches the official GitHub example narrative; good for a clean mass peak story.
   - **Diphoton** \(H \to \gamma\gamma\) — classic discovery plot; check portal for available **reduced** datasets/notebooks for the user’s environment.

2. **Environment**
   - Short path: follow repository README in **HiggsExample20112012** for notebook/ROOT level.
   - Full CMSSW path: align **release and conditions** with the **specific open-data record** the user selects (see CMS Open Data Guide).

3. **Analysis skeleton**
   - Apply **selections** as in the tutorial (lepton \(p_T\), pairing, Z constraints).
   - Build **invariant mass** of the four-lepton system (or diphoton mass).
   - Compare **signal+background** expectation vs data; discuss excess near **125 GeV**.

4. **Documentation the user should produce**
   - **Dataset DOIs** from each portal record used.
   - **Figure captions** stating simplified/educational nature.
   - **One paragraph** comparing qualitatively to CMS-HIG-12-028 without copying unpublished numbers.

## pip-install integration

- **`get_skill`** with `skill=cms-higgs-opendata` works immediately after **`pip install rag-ai-scientist`** (packaged markdown).
- **`query_analysis_knowledge`** needs **`rag-ai-scientist setup-rag`** to have built the database for that `--project-root`; include the physics-story markdown in indexed paths.
- Project overrides can live under **`.rag-ai-scientist/skills/cms-higgs-opendata/SKILL.md`**. Existing **`.cursor/skills/`** overrides continue to work.

## Validation

- User can name **which open-data records** they downloaded (record IDs or DOIs).
- At least one **mass spectrum plot** (or notebook cell output) exists for the chosen final state.
- Written summary includes **limitations** (statistics, simplified systematics).

## Failure recovery

| Issue | Action |
|-------|--------|
| CMSSW release mismatch | Use the release documented on the **exact dataset record**; do not guess. |
| Huge downloads | Prefer **pre-reduced** files from examples or smaller teaching skims linked from the portal. |
| RAG returns empty | Confirm indexed sources include the CMS example doc; rerun **`setup-rag --force`**. |
