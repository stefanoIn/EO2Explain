"""Convert plain-text EO2Explain reports (from build_report_text) to safe HTML."""

from __future__ import annotations

import re
from markupsafe import Markup, escape

REPORT_SECTIONS = frozenset(
    {
        "Summary",
        "What Happened",
        "Assessment",
        "User Assessment",
        "Supporting Evidence",
        "Caveats And Limitations",
        "Clarification",
        "Provenance",
        "Symbolic Details",
    }
)


def _section_slug(name: str) -> str:
    return re.sub(r"[^a-zA-Z0-9]+", "-", name.lower()).strip("-")


def _format_section_body(lines: list[str]) -> str:
    text = "\n".join(lines).strip()
    if not text:
        return ""
    raw_lines = text.splitlines()
    if raw_lines and all(
        ln.strip().startswith("- ") or not ln.strip() for ln in raw_lines if ln.strip()
    ):
        items = []
        for ln in raw_lines:
            s = ln.strip()
            if not s:
                continue
            if s.startswith("- "):
                frag = Markup("<li>") + escape(s[2:].strip()) + Markup("</li>")
                items.append(str(frag))
        if items:
            return str(Markup('<ul class="report-doc-list">') + Markup("".join(items)) + Markup("</ul>"))
    parts: list[str] = []
    para: list[str] = []
    for ln in raw_lines:
        if not ln.strip():
            if para:
                frag = Markup("<p>") + escape(" ".join(para)) + Markup("</p>")
                parts.append(str(frag))
                para = []
            continue
        para.append(ln.strip())
    if para:
        frag = Markup("<p>") + escape(" ".join(para)) + Markup("</p>")
        parts.append(str(frag))
    return "\n".join(parts)


def report_text_to_html(raw: str) -> Markup:
    lines = raw.strip().splitlines()
    if not lines:
        return Markup("")

    out: list[str] = []
    title = escape(lines[0].strip())
    out.append('<header class="report-doc-header">')
    out.append(f'<h1 class="report-doc-title">{title}</h1>')

    meta_i = 1
    if len(lines) > 1 and lines[1].strip().startswith("Location:"):
        out.append('<dl class="report-doc-meta">')
        while meta_i < len(lines) and lines[meta_i].strip() and ":" in lines[meta_i]:
            key, _, rest = lines[meta_i].partition(":")
            out.append(f"<dt>{escape(key.strip())}</dt>")
            out.append(f"<dd>{escape(rest.strip())}</dd>")
            meta_i += 1
        out.append("</dl>")
    out.append("</header>")

    while meta_i < len(lines) and not lines[meta_i].strip():
        meta_i += 1

    current: str | None = None
    buf: list[str] = []

    def flush() -> None:
        nonlocal current, buf
        if current is None:
            buf = []
            return
        body = _format_section_body(buf)
        sid = _section_slug(current)
        out.append(
            f'<section class="report-doc-section" aria-labelledby="report-h-{sid}">'
            f'<h2 class="report-doc-h2" id="report-h-{sid}">{escape(current)}</h2>'
            f'<div class="report-doc-body">{body}</div></section>'
        )
        buf = []

    i = meta_i
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        if stripped in REPORT_SECTIONS:
            flush()
            current = stripped
            buf = []
        else:
            buf.append(line)
        i += 1
    flush()

    return Markup("\n".join(out))
