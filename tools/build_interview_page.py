#!/usr/bin/env python3
"""Builds interview/interview.html from interview/interview-writeup.md."""
from __future__ import annotations

import html
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "interview" / "interview-writeup.md"
OUT = ROOT / "interview" / "interview.html"


def slugify(s: str) -> str:
    s = s.lower().strip()
    s = re.sub(r"[^a-z0-9\s-]", "", s)
    s = re.sub(r"\s+", "-", s)
    return s[:80] or "section"


def inline(text: str) -> str:
    text = html.escape(text)
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"\*([^*]+)\*", r"<em>\1</em>", text)
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', text)
    return text


def render_markdown(md: str) -> str:
    lines = md.splitlines()
    out = []
    i = 0
    in_code = False
    in_ul = False

    def close_ul():
        nonlocal in_ul
        if in_ul:
            out.append("</ul>")
            in_ul = False

    while i < len(lines):
        line = lines[i]

        if line.strip().startswith("```"):
            close_ul()
            if not in_code:
                in_code = True
                out.append("<pre><code>")
            else:
                in_code = False
                out.append("</code></pre>")
            i += 1
            continue

        if in_code:
            out.append(html.escape(line))
            i += 1
            continue

        if not line.strip():
            close_ul()
            i += 1
            continue

        if line.startswith("|") and i + 1 < len(lines) and lines[i + 1].lstrip().startswith("|---"):
            close_ul()
            headers = [c.strip() for c in line.strip().strip("|").split("|")]
            out.append('<table><thead><tr>' + ''.join(f'<th>{inline(h)}</th>' for h in headers) + '</tr></thead><tbody>')
            i += 2
            while i < len(lines) and lines[i].startswith("|"):
                row = [c.strip() for c in lines[i].strip().strip("|").split("|")]
                out.append('<tr>' + ''.join(f'<td>{inline(c)}</td>' for c in row) + '</tr>')
                i += 1
            out.append('</tbody></table>')
            continue

        m = re.match(r"^(#{1,6})\s+(.+)$", line)
        if m:
            close_ul()
            level = len(m.group(1))
            text = m.group(2).strip()
            sid = slugify(text)
            out.append(f'<h{level} id="{sid}">{inline(text)}</h{level}>')
            i += 1
            continue

        m = re.match(r"^\s*[-*]\s+(.+)$", line)
        if m:
            if not in_ul:
                out.append("<ul>")
                in_ul = True
            out.append(f"<li>{inline(m.group(1).strip())}</li>")
            i += 1
            continue

        if line.startswith("---"):
            close_ul()
            out.append("<hr>")
            i += 1
            continue

        close_ul()
        out.append(f"<p>{inline(line.strip())}</p>")
        i += 1

    close_ul()
    if in_code:
        out.append("</code></pre>")
    return "\n".join(out)


def build() -> None:
    md = SRC.read_text(encoding="utf-8")
    body = render_markdown(md)

    page = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>SRAM Interview — Kellogg AIML 950</title>
  <style>
    :root {{
      --sram-red: #e10600;
      --ink: #101114;
      --ink-soft: #4b5563;
      --line: #d8dde5;
      --bg: #f3f5f8;
      --panel: #ffffff;
    }}

    * {{ box-sizing: border-box; }}

    body {{
      margin: 0;
      font-family: "Avenir Next", "Segoe UI", Arial, sans-serif;
      color: var(--ink);
      background:
        radial-gradient(circle at 7% -6%, rgba(225, 6, 0, 0.10), transparent 44%),
        radial-gradient(circle at 100% 0, rgba(16, 24, 40, 0.15), transparent 35%),
        var(--bg);
      line-height: 1.6;
    }}

    header {{
      background: linear-gradient(180deg, #0f1116 0%, #141925 100%);
      border-bottom: 3px solid var(--sram-red);
      padding: 20px 32px;
      display: flex;
      align-items: center;
      justify-content: space-between;
    }}

    header .brand {{ color: #fff; font-size: 20px; font-weight: 800; margin: 0; }}
    header .sub {{ color: #9ca3af; font-size: 12px; margin: 2px 0 0; }}

    header a {{
      color: #d8e1ef;
      font-size: 13px;
      text-decoration: none;
      border: 1px solid rgba(255,255,255,0.2);
      padding: 6px 14px;
      border-radius: 999px;
    }}

    header a:hover {{ background: rgba(255,255,255,0.08); color: #fff; }}

    .wrapper {{
      max-width: 820px;
      margin: 32px auto;
      padding: 0 24px 48px;
    }}

    .toolbar {{
      display: flex;
      justify-content: flex-end;
      margin-bottom: 16px;
    }}

    button {{
      border: 1px solid #232937;
      background: #1b2130;
      color: #fff;
      border-radius: 999px;
      padding: 8px 16px;
      font-size: 12px;
      cursor: pointer;
    }}

    .card {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 14px;
      padding: 28px 32px;
      box-shadow: 0 6px 20px rgba(15, 23, 42, 0.05);
    }}

    .card h1 {{
      margin: 0 0 4px;
      font-size: 26px;
      border-bottom: 3px solid var(--sram-red);
      padding-bottom: 10px;
    }}

    .meta {{
      font-size: 13px;
      color: var(--ink-soft);
      margin: 6px 0 20px;
    }}

    hr {{ border: none; border-top: 1px solid var(--line); margin: 20px 0; }}

    h1, h2, h3, h4 {{ margin: 20px 0 8px; color: #101114; line-height: 1.3; }}
    h2 {{ font-size: 18px; border-left: 3px solid var(--sram-red); padding-left: 10px; }}
    h3 {{ font-size: 15px; color: #374151; }}
    p {{ margin: 8px 0; font-size: 15px; }}
    ul {{ margin: 8px 0 12px 22px; padding: 0; }}
    li {{ margin: 5px 0; font-size: 15px; }}

    code {{
      background: #f3f4f6;
      padding: 1px 5px;
      border-radius: 4px;
      font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
      font-size: 13px;
    }}

    strong {{ color: #0f172a; }}
    a {{ color: #1d4ed8; }}

    table {{ width: 100%; border-collapse: collapse; margin: 10px 0 14px; font-size: 14px; }}
    th, td {{ border: 1px solid var(--line); padding: 8px 10px; text-align: left; vertical-align: top; }}
    th {{ background: #f8fafc; font-weight: 600; }}

    @media print {{
      @page {{ size: Letter portrait; margin: 0.5in; }}
      body {{ background: #fff; }}
      header, .toolbar {{ display: none !important; }}
      .wrapper {{ margin: 0; padding: 0; max-width: 100%; }}
      .card {{ border: none; box-shadow: none; padding: 0; border-radius: 0; }}
      .card h1 {{ border-bottom: 2px solid #aaa; }}
      h2 {{ border-left: 2px solid #aaa; }}
    }}
  </style>
</head>
<body>
  <header>
    <div>
      <p class="brand">SRAM AI Adoption Playbook</p>
      <p class="sub">Kellogg AIML/MORS 950 &mdash; Winter 2026</p>
    </div>
    <a href="../analysis-hub.html">&larr; Back to Analysis Hub</a>
  </header>
  <div class="wrapper">
    <div class="toolbar">
      <button onclick="window.print()">Print / Save PDF</button>
    </div>
    <div class="card">
      {body}
    </div>
  </div>
</body>
</html>
"""

    OUT.write_text(page, encoding="utf-8")
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    build()
