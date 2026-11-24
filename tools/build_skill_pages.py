#!/usr/bin/env python3
"""Generate the dali-agent.web.cern.ch skill detail pages from `skills/<name>/SKILL.md`.

The site has no static-site generator: every page in the published tree is plain
house-style HTML (sidebar + `<main class="content">` + `style.css`). This script
is the one piece of automation for the *skill detail* pages, so that a future
edit to a `SKILL.md` can be re-synced with the same command instead of being
hand-transcribed:

    python3 tools/build_skill_pages.py --site /tmp/dali-site            # all catalogue skills
    python3 tools/build_skill_pages.py --site /tmp/dali-site --skill membrane
    python3 tools/build_skill_pages.py --site /tmp/dali-site --check    # drift check only

It renders each `SKILL.md` (front-matter `name`/`description` as a header block,
then the markdown body) into `skill-<name>.html` — flat filenames, matching the
existing site convention (`setup.html`, `demo.html`, ...; no subfolders).

Only the markdown subset actually used by the shipped skills is implemented:
ATX headings, fenced code blocks, tables, blockquotes, ordered/unordered lists
(one nesting level, plus `- [ ]` task items), inline code / bold / italic /
links, and `---` horizontal rules. Everything is HTML-escaped, so a SKILL.md can
never inject markup. If a skill starts using a construct this renderer does not
handle, the raw markdown stays visible rather than producing broken HTML — fix
the renderer, do not hand-edit the generated page.

The catalogue (`skills.html`) is hand-maintained: this script does NOT rewrite
it, it only checks that every skill it generates a page for is linked from the
catalogue. Re-link the catalogue rows by hand when adding a skill.
"""

from __future__ import annotations

import argparse
import html
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SKILLS = REPO / "skills"

# Skills listed in the skills.html catalogue, in catalogue order. `dali` is the
# orchestrator contract itself; it is published as a catalogue page too so the
# site shows the complete list of installed skills, each readable.
CATALOGUE = [
    "dali",
    "harness-tutorial",
    "_template",
    "membrane",
    "cms-higgs-opendata",
    "ap-starterkit-execution",
    "pipeline-checker",
    "timekeeper",
    "analysis-writeup-builder",
    "writing-internal-note",
    "writing-analysis-note",
    "writing-tdr",
    "reviewer-commenter",
    "reviewer-referee",
]

# ---------------------------------------------------------------- front matter


def split_front_matter(text: str) -> tuple[dict, str]:
    """Return (front-matter key/value pairs, markdown body)."""
    lines = text.replace("\r\n", "\n").split("\n")
    if not lines or lines[0].strip() != "---":
        return {}, text
    meta: dict[str, str] = {}
    key = None
    for i, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            return meta, "\n".join(lines[i + 1 :])
        m = re.match(r"^([A-Za-z0-9_-]+):\s*(.*)$", line)
        if m:
            key, value = m.group(1), m.group(2).strip()
            meta[key] = value
        elif key and line.strip():
            # folded continuation of the previous key
            meta[key] = (meta[key] + " " + line.strip()).strip()
    return {}, text  # unterminated front matter -> treat everything as body


# ------------------------------------------------------------ inline rendering

CODE_RE = re.compile(r"`([^`]+)`")
BOLD_RE = re.compile(r"\*\*(?=\S)(.+?)(?<=\S)\*\*")
EM_RE = re.compile(r"(?<![\w*])\*(?=\S)(.+?)(?<=\S)\*(?![\w*])")
LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)\s]+)\)")


def inline(text: str) -> str:
    """Escape, then apply the inline subset. Code spans win over everything."""
    out: list[str] = []
    pos = 0
    for m in CODE_RE.finditer(text):
        out.append(_inline_plain(text[pos : m.start()]))
        out.append("<code>%s</code>" % html.escape(m.group(1)))
        pos = m.end()
    out.append(_inline_plain(text[pos:]))
    return "".join(out)


def _inline_plain(text: str) -> str:
    s = html.escape(text)
    s = LINK_RE.sub(
        lambda m: '<a href="%s">%s</a>' % (html.escape(m.group(2), quote=True), m.group(1)),
        s,
    )
    s = BOLD_RE.sub(r"<strong>\1</strong>", s)
    s = EM_RE.sub(r"<em>\1</em>", s)
    return s


# ---------------------------------------------------------- block-level parser

HEAD_RE = re.compile(r"^(#{1,6})\s+(.*)$")
UL_RE = re.compile(r"^(\s*)[-*+]\s+(.*)$")
OL_RE = re.compile(r"^(\s*)\d+[.)]\s+(.*)$")
TABLE_RE = re.compile(r"^\s*\|.*\|\s*$")
FENCE_RE = re.compile(r"^\s*(```|~~~)")
TASK_RE = re.compile(r"^\[([ xX])\]\s+(.*)$")


def slugify(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug or "section"


def render_markdown(body: str) -> tuple[str, list[tuple[int, str, str]]]:
    """Render the markdown body to HTML; also return the heading outline."""
    lines = body.replace("\r\n", "\n").split("\n")
    out: list[str] = []
    toc: list[tuple[int, str, str]] = []
    used: dict[str, int] = {}
    para: list[str] = []
    i = 0

    def flush_para() -> None:
        if para:
            out.append("<p>%s</p>" % inline(" ".join(para)))
            para.clear()

    while i < len(lines):
        raw = lines[i]
        line = raw.rstrip()

        if not line.strip():
            flush_para()
            i += 1
            continue

        # fenced code block
        if FENCE_RE.match(line):
            flush_para()
            fence = FENCE_RE.match(line).group(1)
            i += 1
            buf: list[str] = []
            while i < len(lines) and not lines[i].lstrip().startswith(fence):
                buf.append(lines[i])
                i += 1
            i += 1  # closing fence (or EOF)
            out.append("<pre><code>%s</code></pre>" % html.escape("\n".join(buf)))
            continue

        # heading
        m = HEAD_RE.match(line)
        if m:
            flush_para()
            level = len(m.group(1))
            text = m.group(2).strip().rstrip("#").strip()
            slug = slugify(re.sub(r"`", "", text))
            used[slug] = used.get(slug, 0) + 1
            if used[slug] > 1:
                slug = "%s-%d" % (slug, used[slug])
            if level <= 3:
                toc.append((level, slug, text))
            out.append("<h%d id=\"%s\">%s</h%d>" % (level, slug, inline(text), level))
            i += 1
            continue

        # horizontal rule
        if re.match(r"^\s*(?:-{3,}|\*{3,}|_{3,})\s*$", line):
            flush_para()
            out.append("<hr>")
            i += 1
            continue

        # table: a pipe row followed by a |---|:--:| separator row (only pipes,
        # dashes and colons may appear in the separator)
        if TABLE_RE.match(line) and i + 1 < len(lines) and lines[i + 1].strip() \
                and set(lines[i + 1].strip()) <= set("|-: "):
            flush_para()
            rows = []
            while i < len(lines) and TABLE_RE.match(lines[i]):
                rows.append(lines[i])
                i += 1
            out.append(render_table(rows))
            continue

        # blockquote
        if line.lstrip().startswith(">"):
            flush_para()
            buf = []
            while i < len(lines) and lines[i].lstrip().startswith(">"):
                buf.append(re.sub(r"^\s*>\s?", "", lines[i]))
                i += 1
            inner, _ = render_markdown("\n".join(buf))
            out.append("<blockquote>%s</blockquote>" % inner)
            continue

        # list (unordered and/or ordered, one nesting level)
        if UL_RE.match(line) or OL_RE.match(line):
            flush_para()
            block, i = parse_list(lines, i)
            out.append(block)
            continue

        para.append(line.strip())
        i += 1

    flush_para()
    return "\n".join(out), toc


def render_table(rows: list[str]) -> str:
    def cells(row: str) -> list[str]:
        return [c.strip() for c in row.strip().strip("|").split("|")]

    header = cells(rows[0])
    aligns = []
    for cell in cells(rows[1]):
        left, right = cell.startswith(":"), cell.endswith(":")
        aligns.append("center" if left and right else "right" if right else "left")
    body = [cells(r) for r in rows[2:]]

    def tr(cells_, tag: str) -> str:
        tds = []
        for idx, cell in enumerate(cells_):
            align = aligns[idx] if idx < len(aligns) else "left"
            style = "" if align == "left" else ' style="text-align:%s"' % align
            tds.append("<%s%s>%s</%s>" % (tag, style, inline(cell), tag))
        return "<tr>%s</tr>" % "".join(tds)

    thead = "<thead>%s</thead>" % tr(header, "th")
    tbody = "<tbody>%s</tbody>" % "".join(tr(r, "td") for r in body)
    return "<table>%s%s</table>" % (thead, tbody)


def parse_list(lines: list[str], i: int) -> tuple[str, int]:
    """Parse one list block starting at line `i`; return (html, next_index).

    Handles one nesting level: top-level items plus their indented continuation
    lines (sub-lists / wrapped text), which are rendered recursively.
    """
    items: list[tuple[str, str, list[str]]] = []
    order = None
    while i < len(lines):
        line = lines[i].rstrip()
        if not line.strip():
            peek = i + 1
            while peek < len(lines) and not lines[peek].strip():
                peek += 1
            if peek < len(lines) and (UL_RE.match(lines[peek]) or OL_RE.match(lines[peek])):
                i = peek
                continue
            break
        m_ul, m_ol = UL_RE.match(line), OL_RE.match(line)
        if not (m_ul or m_ol) or (m_ul or m_ol).group(1):
            break
        m = m_ul or m_ol
        kind = "ul" if m_ul else "ol"
        if order is None:
            order = kind
        items.append((kind, m.group(2).strip(), []))
        i += 1
        while i < len(lines):
            nxt = lines[i]
            if not nxt.strip():
                peek = i + 1
                while peek < len(lines) and not lines[peek].strip():
                    peek += 1
                if peek < len(lines) and re.match(r"^\s{2,}", lines[peek]):
                    i = peek
                    continue
                break
            if re.match(r"^\s{2,}", nxt):
                items[-1][2].append(re.sub(r"^\s{2,}", "", nxt.rstrip()))
                i += 1
                continue
            break

    kind = order or "ul"
    html_out = ["<%s>" % kind]
    for _k, text, sub in items:
        # A plain (non-list, non-code) continuation block is just the item text
        # soft-wrapped in the markdown source, so join it with spaces rather
        # than emitting a nested <p>.
        if sub and not any(
            UL_RE.match(s) or OL_RE.match(s) or FENCE_RE.match(s) or not s.strip()
            for s in sub
        ):
            text = " ".join([text] + [s.strip() for s in sub])
            sub = []
        task = TASK_RE.match(text)
        if task:
            box = '<input type="checkbox" disabled%s> ' % (
                " checked" if task.group(1).lower() == "x" else ""
            )
            content = box + inline(task.group(2))
        else:
            content = inline(text)
        if sub:
            inner, _ = render_markdown("\n".join(sub))
            content += inner
        html_out.append("<li>%s</li>" % content)
    html_out.append("</%s>" % kind)
    return "".join(html_out), i


# ------------------------------------------------------------- page assembly

SIDEBAR = """<nav class="sidebar">
  <a class="brand" href="index.html">
    <img class="logo-img" src="logo-112.png" alt="DALI logo">
    <span class="brand-name">DALI</span>
  </a>
  <div class="version-badge">basic-harness</div>

  <div class="nav-group">
    <p class="nav-title">Basics</p>
    <ul>
      <li><a href="index.html#overview">Overview</a></li>
      <li><a href="setup.html">Setup</a></li>
      <li><a href="easy-setup.html">Easy Setup <span class="beta-badge">Beta</span></a></li>
      <li><a href="index.html#quickstart">Quick Start</a></li>
      <li><a href="index.html#commands">Commands</a></li>
    </ul>
  </div>

  <div class="nav-group">
    <p class="nav-title">Concepts</p>
    <ul>
      <li><a href="harness.html">The Gated Harness</a></li>
      <li><a href="membrane.html">The Membrane</a></li>
      <li><a href="sandbox.html">The Sandbox</a></li>
      <li><a href="index.html#security">Security Model</a></li>
    </ul>
  </div>

  <div class="nav-group">
    <p class="nav-title">Skills</p>
    <ul>
      <li><a href="skills.html">Skill Catalogue</a></li>
      <li><a href="skills.html#writing">Writing Skills</a></li>
      <li><a href="authoring-a-skill.html">Authoring a Skill <span class="beta-badge">New</span></a></li>
      <li><a href="skills.html#reviewers">Reviewer Agents</a></li>
      <li><a href="adapt.html">Adapting to Your Pipeline</a></li>
    </ul>
  </div>

  <div class="nav-group">
    <p class="nav-title">This skill</p>
    <ul>
{toc}
    </ul>
  </div>

  <div class="nav-group">
    <p class="nav-title">Links</p>
    <ul>
      <li><a href="https://pypi.org/project/rag-ai-scientist/">rag-ai-scientist on PyPI</a></li>
      <li><a href="https://github.com/uzzielperez/rag-ai-scientist">Source on GitHub</a></li>
    </ul>
  </div>
</nav>"""

MATOMO = """<!-- Matomo -->
<script>
  var _paq = window._paq = window._paq || [];
  /* tracker methods like "setCustomDimension" should be called before "trackPageView" */
  _paq.push(['trackPageView']);
  _paq.push(['enableLinkTracking']);
  (function() {
    var u="https://webanalytics.web.cern.ch/";
    _paq.push(['setTrackerUrl', u+'matomo.php']);
    _paq.push(['setSiteId', '1324']);
    var d=document, g=d.createElement('script'), s=d.getElementsByTagName('script')[0];
    g.async=true; g.src=u+'matomo.js'; s.parentNode.insertBefore(g,s);
  })();
</script>
<!-- End Matomo Code -->"""

PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} &mdash; DALI</title>
<link rel="stylesheet" href="style.css">
</head>
<body>
<div class="page">

{sidebar}

<main class="content">

<!-- GENERATED by tools/build_skill_pages.py from {src}; do not hand-edit. -->

<h1>{heading}</h1>

<p class="meta"><a href="skills.html">&larr; Skill Catalogue</a>
&nbsp;&middot;&nbsp; source: <code>{src}</code></p>

<div class="skill-desc">
<p><strong>{name}</strong> &mdash; {description}</p>
</div>

{body}

<footer>
  <p><a href="skills.html">&larr; Back to the Skill Catalogue</a> &nbsp;&middot;&nbsp;
     <a href="index.html">DALI home</a></p>
  <p>Generated from <code>{src}</code> in the
     <a href="https://github.com/uzzielperez/rag-ai-scientist">DALI harness repo</a>;
     re-run <code>tools/build_skill_pages.py</code> after editing the skill.</p>
</footer>

</main>
</div>
{matomo}
</body>
</html>
"""


def render_toc(toc: list[tuple[int, str, str]]) -> str:
    """Sidebar outline: h2 entries, with h3 entries nested one level underneath."""
    if not toc:
        return '<li><a href="skills.html">Skill Catalogue</a></li>'
    if toc and all(level > 2 for level, _s, _t in toc):
        toc = [(2, slug, text) for _level, slug, text in toc]
    out: list[str] = []
    open_sub = False
    for level, slug, text in toc:
        entry = '<li><a href="#%s">%s</a></li>' % (slug, html.escape(text))
        if level == 2 or not out:
            if open_sub:
                out.append("</ul></li>")
                open_sub = False
            out.append(entry)
        elif open_sub:
            out.append(entry)
        else:
            out[-1] = out[-1][: -len("</li>")] + "<ul>"
            out.append(entry)
            open_sub = True
    if open_sub:
        out.append("</ul></li>")
    return "\n".join(out)


def build_page(name: str, src_rel: str, markdown_text: str) -> str:
    meta, body = split_front_matter(markdown_text)
    body_html, toc = render_markdown(body)

    # The SKILL.md's own top-level heading becomes the page <h1>; drop it from
    # the body so the title is not duplicated.
    heading = meta.get("name") or name
    body_lines = body_html.split("\n")
    for idx, line in enumerate(body_lines):
        if "<h1" in line:
            inner = re.sub(r"^<h1[^>]*>|</h1>$", "", line)
            # unescape what inline() escaped, so stripping the tags cannot create
            # new markup and the title can be escaped once, at the end
            heading = html.unescape(re.sub(r"<[^>]+>", "", inner))
            del body_lines[idx]
            break
    body_html = "\n".join(body_lines)
    # the h1 became the page title: drop it from the sidebar outline too
    toc = [entry for entry in toc if entry[0] > 1]

    toc_html = render_toc(toc)

    title = "%s skill" % (meta.get("name") or name)
    if title.startswith("<"):  # _template front-matter is a placeholder
        title = "%s (template)" % name
    description = meta.get("description") or ""
    if not description:
        description = "No description in the skill front matter."

    return PAGE.format(
        title=html.escape(title),
        sidebar=SIDEBAR.format(toc=toc_html),
        src=html.escape(src_rel),
        heading=html.escape(heading),
        name=html.escape(meta.get("name") or name),
        description=html.escape(description),
        body=body_html,
        matomo=MATOMO,
    )


# ------------------------------------------------------------------- driver


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--site", required=True, help="path to the site edit copy (e.g. /tmp/dali-site)")
    ap.add_argument("--skill", action="append", help="only this skill name (repeatable)")
    ap.add_argument("--all", action="store_true", help="every skills/*/SKILL.md, not just the catalogue")
    ap.add_argument("--check", action="store_true", help="report drift, write nothing")
    args = ap.parse_args(argv)

    site = Path(args.site)
    if not site.is_dir():
        print("site dir not found: %s (run: ~/bin/dali pull)" % site, file=sys.stderr)
        return 1

    names = args.skill or ([] if args.all else CATALOGUE)
    if args.all:
        names = sorted(p.parent.name for p in SKILLS.glob("*/SKILL.md"))

    catalogue_html = (site / "skills.html").read_text(encoding="utf-8") if (site / "skills.html").exists() else ""
    rc = 0
    for name in names:
        src = SKILLS / name / "SKILL.md"
        if not src.is_file():
            print("SKIP %-26s no repo file %s" % (name, src.relative_to(REPO)))
            rc = 1
            continue
        src_rel = "skills/%s/SKILL.md" % name
        page = build_page(name, src_rel, src.read_text(encoding="utf-8"))
        out = site / ("skill-%s.html" % name)
        if args.check:
            same = out.exists() and out.read_text(encoding="utf-8") == page
            print("%-8s %s" % ("in sync" if same else "STALE", out.name))
            rc = rc or (0 if same else 1)
            continue
        out.write_text(page, encoding="utf-8")
        linked = ('href="skill-%s.html"' % name) in catalogue_html
        print("wrote %-34s %6d bytes  catalogue link: %s"
              % (out.name, len(page), "yes" if linked else "MISSING"))
        if catalogue_html and not linked:
            rc = 1

    if catalogue_html and not args.check:
        print("\n%d page(s) written. Publish with: ~/bin/dali publish <pages>" % len(names))
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
