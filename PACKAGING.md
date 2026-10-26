# Packaging the membrane into rag-ai-scientist

`rag-ai-scientist` ships its harness skills as package data under
`rag_ai_scientist/skills/` (e.g. `harness-tutorial/`, `cms-higgs-opendata/`,
`ap-starterkit-execution/`). The membrane follows the same route: skill markdown
in `skills/`, toolkit as a sibling package-data directory.

Target layout inside the wheel:

```
rag_ai_scientist/
├── skills/
│   ├── membrane/SKILL.md          <- skills/membrane/
│   └── ...                        (existing skills untouched)
└── membrane/                      <- membrane/
    ├── README.md
    ├── bin/{membrane_check,membrane_filter,membrane_tail}.py
    ├── config/{approved-crossings.txt,pseudonymize.patterns,secrets.patterns}
    └── tests/selftest.py
```

## 1. Copy in

```bash
PKG=/path/to/rag-ai-scientist/src/rag_ai_scientist   # adjust to your layout
cp -r DALI-basic-harness/skills/membrane  $PKG/skills/
cp -r DALI-basic-harness/membrane         $PKG/membrane
cp    DALI-basic-harness/plugins/membrane-preflight.js $PKG/plugins/ 2>/dev/null || \
  { mkdir -p $PKG/plugins && cp DALI-basic-harness/plugins/membrane-preflight.js $PKG/plugins/; }
```

## 2. Declare the data files

The `config/*.patterns` and `config/*.txt` files are **not** picked up by
`include-package-data` alone - list the extensions explicitly.

`pyproject.toml`, setuptools backend:

```toml
[tool.setuptools.package-data]
rag_ai_scientist = [
  "skills/*/*.md",
  "membrane/*.md",
  "membrane/bin/*.py",
  "membrane/config/*.patterns",
  "membrane/config/*.txt",
  "membrane/tests/*.py",
  "plugins/*.js",
]
```

`pyproject.toml`, hatchling backend:

```toml
[tool.hatch.build.targets.wheel]
artifacts = [
  "src/rag_ai_scientist/skills/**/*.md",
  "src/rag_ai_scientist/membrane/**/*",
  "src/rag_ai_scientist/plugins/*.js",
]
```

`MANIFEST.in` (sdist completeness, either backend):

```
recursive-include src/rag_ai_scientist/skills *.md
recursive-include src/rag_ai_scientist/membrane *.md *.py *.patterns *.txt
recursive-include src/rag_ai_scientist/plugins *.js
```

## 3. Resolve `$MEM` at runtime

The skill markdown tells the user `$MEM` = the membrane directory. Inside the
installed package that is not `~/.config/opencode/membrane`, so resolve it:

```python
from pathlib import Path
import rag_ai_scientist

MEMBRANE_DIR = Path(rag_ai_scientist.__file__).parent / "membrane"
```

If the package has a skill-path helper already, return `MEMBRANE_DIR` from it
so `SKILL.md`'s `$MEM` and any CLI wiring agree. Keep the executable bit on
`bin/*.py` (the shebangs are `#!/usr/bin/env python3`); if your build strips
it, document `python3 -m`-style invocation instead.

## 4. Verify before releasing

```bash
python -m build && python -m twine check dist/*
# run the self-test from the INSTALLED tree (it writes only into a temp dir)
python "$(python -c 'import rag_ai_scientist,os;print(os.path.dirname(rag_ai_scientist.__file__))')/membrane/tests/selftest.py"
```

Expected: `18/18 passed`. Also confirm the wheel contains the two `.patterns`
files and `approved-crossings.txt`:

```bash
unzip -l dist/*.whl | grep -E 'membrane|preflight'
```

## 5. Notes

- Requires-Python is `>=3.10` in the distribution metadata; the toolkit only
  needs 3.9+, so no constraint change is needed.
- The membrane has zero third-party dependencies (stdlib only), so it adds
  nothing to `install_requires`.
- The pre-flight plugin is opencode-specific and optional; ship it as inert
  data and never import it.
- Do not ship any real workspace paths, account names, or run labels in
  `config/` - they are examples on purpose. Re-check with
  `grep -rn '<your-account>\|<your-campaign>' src/` before tagging.
