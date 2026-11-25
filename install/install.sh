#!/usr/bin/env bash
# DALI harness installer — one command per IDE, like Cloudflare's agent-setup pages.
#
#   ./install.sh --ide cursor|claude-code|codex|copilot|vscode|vibe|opencode|all [--workspace DIR] [--scope user|project] [--dry-run] [--uninstall] [--check]
#
# What it does for every target (identical content, IDE-specific paths):
#   - copies skills/            -> the target's skills directory
#   - copies membrane/ + sandbox/ -> <workspace>/.dali/ (the enforcement toolkits)
#   - writes/merges DALI block  -> the target's instructions file (AGENTS.md, CLAUDE.md, ...)
#   - writes MCP snippet        -> <workspace>/.dali/mcp/<ide>.json|toml (paste/merge where needed)
#
# Idempotent: re-running updates in place; the instructions block is delimited by
# markers and replaced, never duplicated. --uninstall removes exactly what was
# installed (skills dir, .dali/, marked block, plugin file for opencode).
# --check (alias --diff) reports what an update would change — new skills, stale
# files, instructions-block drift — and writes nothing (exit 1 if anything is stale).

set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
IDE=""
WORKSPACE="$PWD"
SCOPE="user"
DRY=0
UNINSTALL=0
CHECK=0

BLOCK_BEGIN="<!-- BEGIN DALI HARNESS (managed by install.sh — do not edit inside; edit $REPO/README.md) -->"
BLOCK_END="<!-- END DALI HARNESS -->"

usage() {
  sed -n '2,15p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'
  exit "${1:-0}"
}

log()  { printf '\033[1;36m==>\033[0m %s\n' "$*"; }
warn() { printf '\033[1;33mwarn:\033[0m %s\n' "$*" >&2; }
run()  { if [ "$DRY" = 1 ]; then printf '    [dry] %s\n' "$*"; else eval "$@"; fi; }

while [ $# -gt 0 ]; do
  case "$1" in
    --ide)       IDE="${2:?--ide needs a value}"; shift 2 ;;
    --workspace) WORKSPACE="$(cd "${2:?--workspace needs a value}" && pwd)"; shift 2 ;;
    --scope)     SCOPE="${2:?}"; shift 2 ;;
    --dry-run)   DRY=1; shift ;;
    --uninstall) UNINSTALL=1; shift ;;
    --check|--diff) CHECK=1; shift ;;
    -h|--help)   usage 0 ;;
    *) warn "unknown flag: $1"; usage 1 ;;
  esac
done

[ -n "$IDE" ] || { warn "--ide is required"; usage 1; }
case "$SCOPE" in user|project) ;; *) warn "--scope must be user|project"; exit 1 ;; esac
case "$IDE" in all) IDES="opencode claude-code cursor codex copilot vscode vibe";; *) IDES="$IDE";; esac
for i in $IDES; do
  case "$i" in opencode|claude-code|cursor|codex|copilot|vscode|vibe) ;; *) warn "unknown IDE '$i'"; usage 1 ;; esac
done

# ---------------------------------------------------------------- instructions
instructions_block() {
  cat <<EOF
$BLOCK_BEGIN
# DALI harness

You are the DALI agent: an analysis-workspace orchestrator for an LHCb physics
analysis running in this workspace. Full contract: \`.dali/AGENTS-FULL.md\`
(read it once at session start). Skills live in this IDE's skills directory
(\`dali\`, \`harness-tutorial\`, \`membrane\`, \`reviewer-referee\`, ...).

Commands: \`setup\`, \`extract\`, \`run <step>\` / \`run all\`, \`status\`, \`report\`.

Hard rules:
- Data access goes through the membrane: gate reads with
  \`python3 .dali/membrane/bin/membrane_check.py --workspace . <file>\`, quote only
  \`membrane_filter.py\` output, tail logs only via \`membrane_tail.py\`.
- EXECUTE-phase code runs confined: \`sandbox/bin/sandbox_run.sh --workspace .\`.
- Never invent a reference number; never edit an output to satisfy a gate —
  change the input or the config. Escalate to the human after 3 failed attempts.
- Be brief in chat; put detail in \`reports/workflow.md\` / \`workflow.html\`.
$BLOCK_END
EOF
}

merge_block() { # merge_block <file>
  local f="$1"
  if [ "$DRY" = 1 ]; then printf '    [dry] merge DALI block into %s\n' "$f"; return; fi
  mkdir -p "$(dirname "$f")"
  touch "$f"
  local tmp; tmp="$(mktemp)"
  if awk -v b="$BLOCK_BEGIN" -v e="$BLOCK_END" '
      $0==b {inb=1; next} $0==e {inb=1; next} !inb {print}
    ' "$f" > "$tmp"; then :; fi
  # strip old block (two-pass: skip lines strictly between markers)
  awk -v b="$BLOCK_BEGIN" -v e="$BLOCK_END" '
    $0==b {inb=1; next}
    inb && $0==e {inb=0; next}
    !inb {print}
  ' "$f" > "$tmp"
  printf '\n' >> "$tmp"
  instructions_block >> "$tmp"
  mv "$tmp" "$f"
  log "instructions block -> $f"
}

strip_block() { # strip_block <file>
  local f="$1"
  [ -f "$f" ] || return 0
  if ! grep -qF "$BLOCK_BEGIN" "$f"; then return 0; fi
  local tmp; tmp="$(mktemp)"
  awk -v b="$BLOCK_BEGIN" -v e="$BLOCK_END" '
    $0==b {inb=1; next}
    inb && $0==e {inb=0; next}
    !inb {print}
  ' "$f" > "$tmp" && mv "$tmp" "$f"
  log "removed DALI block from $f"
}

# ------------------------------------------------------------------- shared
copy_skills_to() { # copy_skills_to <dest>
  run "mkdir -p '$1' && cp -rf '$REPO/skills/.' '$1/'"
  log "skills -> $1"
}

# callable agent definitions per IDE, from install/dali-agent.md
AGENT_BEGIN="<!-- BEGIN DALI AGENT BODY (managed by install.sh"
AGENT_END="<!-- END DALI AGENT BODY -->"

install_agents() { # install_agents <ide>
  local src="$REPO/install/dali-agent.md"
  if [ ! -f "$src" ]; then warn "no $src — skipping callable agent install"; return; fi
  case "$1" in
    opencode)
      if [ "$SCOPE" = user ]; then
        run "mkdir -p '$HOME/.config/opencode/agent' && cp '$src' '$HOME/.config/opencode/agent/dali.md'"
        log "callable agent -> ~/.config/opencode/agent/dali.md  (restart IDE, then /agent dali)"
      else
        run "mkdir -p '$WORKSPACE/.opencode/agent' && cp '$src' '$WORKSPACE/.opencode/agent/dali.md'"
        log "callable agent -> $WORKSPACE/.opencode/agent/dali.md"
      fi
      ;;
    claude-code)
      local dst="$WORKSPACE/.claude/agents/dali.md"
      [ "$SCOPE" = user ] && dst="$HOME/.claude/agents/dali.md"
      run "mkdir -p '$(dirname "$dst")' && sed -e 's/^mode: primary/mode: all/' '$src' > '$dst'"
      log "callable agent -> $dst"
      ;;
    cursor)
      run "mkdir -p '$WORKSPACE/.cursor/agents' && sed -e 's/^mode: primary//' -e '/^---$/,/^---$/d' '$src' > '$WORKSPACE/.cursor/agents/dali.md'"
      log "callable agent (custom mode prompt) -> $WORKSPACE/.cursor/agents/dali.md"
      ;;
    codex)
      run "mkdir -p '$WORKSPACE/.codex/agents' && cp '$src' '$WORKSPACE/.codex/agents/dali.md'"
      log "callable agent -> $WORKSPACE/.codex/agents/dali.md"
      ;;
    copilot|vscode)
      run "mkdir -p '$WORKSPACE/.github/agents' && sed -e 's/^mode: primary//' '$src' > '$WORKSPACE/.github/agents/dali.md'"
      if [ "$DRY" = 0 ]; then
        mkdir -p "$WORKSPACE/.github/prompts"; local pr="$WORKSPACE/.github/prompts/dali.prompt.md"
        { printf '---\ndescription: Run the DALI agent (workspace orchestrator) on the current task: $ARGUMENTS\nmode: agent\n---\n\n'; cat "$src"; } > "$pr"
        log "callable prompt -> $pr (type /dali in Copilot Chat)"
      else
        printf '    [dry] write %s/.github/prompts/dali.prompt.md\n' "$WORKSPACE"
      fi
      ;;
    vibe)
      run "mkdir -p '$WORKSPACE/.agents' && cp '$src' '$WORKSPACE/.agents/dali.md'"
      log "callable agent -> $WORKSPACE/.agents/dali.md"
      ;;
  esac
}

strip_agent_block() { # strip_agent_block <file> — remove files we installed
  local f="$1"; [ -f "$f" ] || return 0
  if grep -qF "$AGENT_BEGIN" "$f"; then rm -f "$f"; log "removed callable agent $f"; fi
  return 0
}

install_shared() {
  run "mkdir -p '$WORKSPACE/.dali'"
  run "cp -rf '$REPO/membrane' '$REPO/sandbox' '$WORKSPACE/.dali/'"
  run "mkdir -p '$WORKSPACE/.dali/mcp'"
  # full contract for agents that only load a short instructions file
  if [ "$DRY" = 0 ]; then
    instructions_block | sed "1d;\$d" > "$WORKSPACE/.dali/AGENTS-FULL.md"
    cat >> "$WORKSPACE/.dali/AGENTS-FULL.md" <<'EOF'

# Full tasks

1. setup: create analysis/ docs/ validation/ reports/ state/; create
   skills/dali/SKILL.md from skills/_template/ (one section per step: command,
   inputs, outputs, checks); one Snakefile per step + top-level chain
   (`snakemake --dag` must render).
2. extract: reverse-engineer the ordered pipeline from docs/; record per step:
   inputs, outputs, command, reference numbers with source (doc + section/table)
   and tolerance; write state/pipeline.yaml as single source of truth; mark
   inferred numbers `inferred`.
3. run: execute -> validate (deviation in sigma vs reference, `acceptable`
   yes/no) -> correct (minimal change to input/config, never the output);
   max 3 attempts then escalate; log every iteration to state/log.jsonl.
4. report: regenerate reports/workflow.md (Mermaid DAG + per-step table) and
   reports/workflow.html (self-contained, colour-coded).
5. status: passed/failed/not-run counts, biggest sigma deviations, what needs
   human attention, recommended next action.
EOF
    log "full contract -> $WORKSPACE/.dali/AGENTS-FULL.md"
  else
    printf '    [dry] write %s/.dali/AGENTS-FULL.md\n' "$WORKSPACE"
  fi
}

mcp_snippet() { # mcp_snippet <ide> — optional RAG/Overleaf/GitLab servers
  local ide="$1" out="$WORKSPACE/.dali/mcp/$ide.json"
  [ "$ide" = vibe ] && out="$WORKSPACE/.dali/mcp/vibe.toml"
  if [ "$DRY" = 1 ]; then printf '    [dry] write MCP snippet %s\n' "$out"; return; fi
  mkdir -p "$(dirname "$out")"
  case "$ide" in
    vibe) cat > "$out" <<'EOF'
# Optional MCP servers for Vibe — merge into ~/.vibe/config.toml
[[mcp_servers]]
name = "gitlab-cern"
transport = "streamable-http"
url = "https://gitlab.cern.ch/api/v4/mcp"
EOF
;;
    *) cat > "$out" <<EOF
{
  "mcpServers": {
    "gitlab-cern": {
      "type": "remote",
      "url": "https://gitlab.cern.ch/api/v4/mcp",
      "headers": { "Authorization": "Bearer \${env:GITLAB_TOKEN}" }
    }
  }
}
EOF
;;
  esac
  log "optional MCP snippet -> $out"
}

# ---------------------------------------------------------------- per-IDE
# skills destination per IDE/scope (shared by install_ide and check_ide)
skills_dest() { # skills_dest <ide> -> echoes dest, or empty if none
  case "$1" in
    opencode)     if [ "$SCOPE" = user ]; then echo "$HOME/.config/opencode/skill"; else echo "$WORKSPACE/.opencode/skill"; fi ;;
    claude-code)  if [ "$SCOPE" = user ]; then echo "$HOME/.claude/skills"; else echo "$WORKSPACE/.claude/skills"; fi ;;
    cursor)       if [ "$SCOPE" = user ]; then echo "$HOME/.cursor/skills"; else echo "$WORKSPACE/.cursor/skills"; fi ;;
    codex)        if [ "$SCOPE" = user ]; then echo "$HOME/.codex/skills"; else echo "$WORKSPACE/.codex/skills"; fi ;;
    copilot|vscode) echo "$WORKSPACE/.github/skills" ;;
    vibe)         echo "$WORKSPACE/.agents/skills" ;;
  esac
}

install_ide() {
  local ide="$1"
  log "installing DALI harness for: $ide"
  case "$ide" in
    opencode)
      if [ "$SCOPE" = user ]; then
        copy_skills_to "$HOME/.config/opencode/skill"
        merge_block "$HOME/.config/opencode/AGENTS.md"
        run "mkdir -p '$HOME/.config/opencode/plugins' && cp '$REPO/plugins/membrane-preflight.js' '$HOME/.config/opencode/plugins/'"
        log "membrane-preflight plugin -> ~/.config/opencode/plugins/"
      else
        copy_skills_to "$WORKSPACE/.opencode/skill"
        merge_block "$WORKSPACE/AGENTS.md"
      fi
      ;;
    claude-code)
      if [ "$SCOPE" = user ]; then
        copy_skills_to "$HOME/.claude/skills"
        merge_block "$HOME/.claude/CLAUDE.md"
      else
        copy_skills_to "$WORKSPACE/.claude/skills"
        merge_block "$WORKSPACE/CLAUDE.md"
      fi
      ;;
    cursor)
      if [ "$SCOPE" = user ]; then
        copy_skills_to "$HOME/.cursor/skills"
        warn "Cursor reads project instructions; consider --scope project"
      else
        copy_skills_to "$WORKSPACE/.cursor/skills"
      fi
      merge_block "$WORKSPACE/AGENTS.md"
      ;;
    codex)
      if [ "$SCOPE" = user ]; then
        copy_skills_to "$HOME/.codex/skills"
        merge_block "$HOME/.codex/AGENTS.md"
      else
        copy_skills_to "$WORKSPACE/.codex/skills"
        merge_block "$WORKSPACE/AGENTS.md"
      fi
      ;;
    copilot|vscode)
      copy_skills_to "$WORKSPACE/.github/skills"
      merge_block "$WORKSPACE/AGENTS.md"
      if [ "$DRY" = 0 ]; then
        mkdir -p "$WORKSPACE/.github"
        local pin="$WORKSPACE/.github/copilot-instructions.md"
        touch "$pin"
        if ! grep -qF "skills/dali/SKILL.md" "$pin"; then
          { printf '\nFor analysis tasks follow AGENTS.md (DALI harness) and skills/dali/SKILL.md.\n'; } >> "$pin"
          log "pointer -> $pin"
        fi
      fi
      ;;
    vibe)
      copy_skills_to "$WORKSPACE/.agents/skills"
       merge_block "$WORKSPACE/AGENTS.md"
       ;;
  esac
  install_agents "$ide"
  mcp_snippet "$ide"
}

uninstall_ide() {
  local ide="$1"
  log "uninstalling DALI harness for: $ide"
  case "$ide" in
    opencode)
      run "rm -rf '$HOME/.config/opencode/skill/dali' '$WORKSPACE/.opencode/skill'"
      for s in harness-tutorial membrane reviewer-referee reviewer-commenter cms-higgs-opendata ap-starterkit-execution writing-internal-note writing-analysis-note writing-tdr _template; do
        run "rm -rf '$HOME/.config/opencode/skill/$s'"
      done
      strip_block "$HOME/.config/opencode/AGENTS.md"
      run "rm -f '$HOME/.config/opencode/plugins/membrane-preflight.js'"
      strip_agent_block "$HOME/.config/opencode/agent/dali.md"
      strip_agent_block "$WORKSPACE/.opencode/agent/dali.md"
      ;;
    claude-code)
      run "rm -rf '$HOME/.claude/skills' '$WORKSPACE/.claude/skills'"
      strip_block "$HOME/.claude/CLAUDE.md"
      strip_agent_block "$HOME/.claude/agents/dali.md"
      strip_agent_block "$WORKSPACE/.claude/agents/dali.md"
      ;;
    cursor)
      run "rm -rf '$HOME/.cursor/skills' '$WORKSPACE/.cursor/skills'"
      strip_agent_block "$WORKSPACE/.cursor/agents/dali.md"
      ;;
    codex)
      run "rm -rf '$HOME/.codex/skills' '$WORKSPACE/.codex/skills'"
      strip_block "$HOME/.codex/AGENTS.md"
      strip_agent_block "$WORKSPACE/.codex/agents/dali.md"
      ;;
    copilot|vscode)
      run "rm -rf '$WORKSPACE/.github/skills'"
      strip_agent_block "$WORKSPACE/.github/agents/dali.md"
      strip_agent_block "$WORKSPACE/.github/prompts/dali.prompt.md"
      ;;
    vibe)
      run "rm -rf '$WORKSPACE/.agents/skills'"
      strip_agent_block "$WORKSPACE/.agents/dali.md"
      ;;
  esac
  case "$ide" in cursor|codex|copilot|vscode|vibe) strip_block "$WORKSPACE/AGENTS.md";; esac
  for d in "$WORKSPACE/.opencode" "$WORKSPACE/.claude" "$WORKSPACE/.cursor" "$WORKSPACE/.codex" "$WORKSPACE/.agents"; do
    run "rmdir '$d' 2>/dev/null || true"
  done
}

# ------------------------------------------------------------------- check
CHECK_STALE=0

check_block() { # check_block <file> — is the DALI instructions block up to date?
  local f="$1"
  [ -f "$f" ] || { echo "    instructions: MISSING ($f)"; CHECK_STALE=1; return; }
  if ! grep -qF "$BLOCK_BEGIN" "$f"; then
    echo "    instructions: no DALI block in $f"; CHECK_STALE=1; return
  fi
  local tmp cur new
  tmp="$(mktemp)"; cur="$(mktemp)"; new="$(mktemp)"
  awk -v b="$BLOCK_BEGIN" -v e="$BLOCK_END" '
    $0==b {inb=1; print; next}
    inb {print; if ($0==e) inb=0; next}
  ' "$f" > "$cur"
  instructions_block > "$new"
  if diff -u "$cur" "$new" > "$tmp"; then
    echo "    instructions: up to date ($(basename "$f"))"
  else
    echo "    instructions: STALE ($(basename "$f")):"
    sed 's/^/      /' "$tmp"
    CHECK_STALE=1
  fi
  rm -f "$tmp" "$cur" "$new"
}

check_ide() { # check_ide <ide> — report drift vs the repo; write nothing
  local ide="$1" dest d_out
  log "checking DALI harness for: $ide"
  dest="$(skills_dest "$ide")"
  if [ -n "$dest" ] && [ -d "$dest" ]; then
    d_out="$(diff -rq "$REPO/skills" "$dest" 2>/dev/null || true)"
    if [ -n "$d_out" ]; then
      printf '%s\n' "$d_out" | sed 's/^/    /'
      CHECK_STALE=1
    else
      echo "    skills: up to date ($dest)"
    fi
  elif [ -n "$dest" ]; then
    echo "    skills: NOT INSTALLED ($dest)"; CHECK_STALE=1
  fi
  case "$ide:$SCOPE" in
    opencode:user)       check_block "$HOME/.config/opencode/AGENTS.md" ;;
    opencode:project)    check_block "$WORKSPACE/AGENTS.md" ;;
    claude-code:user)    check_block "$HOME/.claude/CLAUDE.md" ;;
    claude-code:project) check_block "$WORKSPACE/CLAUDE.md" ;;
    codex:user)          check_block "$HOME/.codex/AGENTS.md" ;;
    cursor|codex|copilot|vscode|vibe) check_block "$WORKSPACE/AGENTS.md" ;;
  esac
  local m_out
  m_out="$(diff -rq "$REPO/membrane" "$WORKSPACE/.dali/membrane" 2>/dev/null || true)"
  if [ ! -d "$WORKSPACE/.dali/membrane" ] || [ -n "$m_out" ]; then
    echo "    membrane (.dali/): stale or missing"; CHECK_STALE=1
  else
    echo "    membrane (.dali/): up to date"
  fi
}

if [ "$CHECK" = 1 ]; then
  for i in $IDES; do check_ide "$i"; done
  echo
  if [ "$CHECK_STALE" = 1 ]; then
    log "updates available — apply with:  $0 --ide $IDE --workspace '$WORKSPACE' --scope $SCOPE"
    exit 1
  else
    log "everything up to date."
    exit 0
  fi
fi

install_shared
for i in $IDES; do
  if [ "$UNINSTALL" = 1 ]; then uninstall_ide "$i"; else install_ide "$i"; fi
done

if [ "$UNINSTALL" = 1 ]; then
  run "rm -rf '$WORKSPACE/.dali'"
  log "uninstalled (.dali/ removed; re-check no secrets left behind)"
else
  cat <<EOF

Done. Next:
  1. cd $WORKSPACE && start your agent, then say: setup
  2. optional MCP servers: $WORKSPACE/.dali/mcp/<ide>.json|toml
  3. verify the membrane: python3 $WORKSPACE/.dali/membrane/tests/selftest.py
EOF
fi
