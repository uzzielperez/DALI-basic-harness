# Results-matrix template

Copy into `docs/RESULTS_BY_YEAR.md` (or `RESULTS_BY_<BIN>.md`) and fill.
Legend: ✅ value · 🔶 partial/needs review · ❌ FIXME (to run) · — n/a.
Headline rows (yields, BR, syst total) always carry the golden benchmark
column and must cite the source file/paper for every ✅.

## 0. Sample / bin configuration

| Item | <BIN1> | <BIN2> | ... |
|------|--------|--------|-----|
| Stripping / working point | | | |
| MC sample | | | |
| Selection model version | | | |

## 1..k. Per-stage results (one table per stage of the chain)

| Stage quantity | BIN1 | BIN2 | ... | golden |
|----------------|------|------|-----|--------|
| ε_<stage> | | | | |

## Headline observables (highlight vs golden benchmark)

| Quantity | golden | <BIN1> closure | <BIN2> closure | ... |
|----------|--------|----------------|----------------|-----|
| N_sig | **value ± err** | 🔶/❌ | | |
| N_norm | **value ± err** | 🔶/❌ | | |
| ε ratio | **value** | | | |
| Observable (BR, α_γ, ...) | **value ± stat ± syst** | | | |
| Syst total % | **value** | | | |

## Pipeline-to-run map

| Missing quantity | Step | Command | Blocker |
|------------------|------|---------|---------|
| | | | |

Rules: fill only from draft text, pipeline outputs, or pinned references;
cite the file for each ✅; inferred values get `needs_review`; never change
a golden reference to close a cell.
