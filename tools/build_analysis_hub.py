#!/usr/bin/env python3
from __future__ import annotations

import html
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "analysis-hub.html"


def md_files(root: Path):
    files = [p for p in root.rglob("*.md") if ".git" not in p.parts]
    return sorted(files, key=lambda p: str(p.relative_to(root)).lower())


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
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2" target="_blank">\1</a>', text)
    return text


def render_markdown(md: str, prefix: str) -> str:
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
            out.append('<div class="table-wrap"><table><thead><tr>' + ''.join(f'<th>{inline(h)}</th>' for h in headers) + '</tr></thead><tbody>')
            i += 2
            while i < len(lines) and lines[i].startswith("|"):
                row = [c.strip() for c in lines[i].strip().strip("|").split("|")]
                out.append('<tr>' + ''.join(f'<td>{inline(c)}</td>' for c in row) + '</tr>')
                i += 1
            out.append('</tbody></table></div>')
            continue

        m = re.match(r"^(#{1,6})\s+(.+)$", line)
        if m:
            close_ul()
            level = len(m.group(1))
            text = m.group(2).strip()
            sid = f"{prefix}-{slugify(text)}"
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

        if line.strip() == "---":
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


def file_label(rel: Path) -> str:
    parts = rel.parts
    if len(parts) > 1:
        return f"{parts[0]} / {rel.stem}"
    return rel.stem


def build() -> None:
    files = md_files(ROOT)
    nav_items = []
    sections = []

    for idx, p in enumerate(files, start=1):
        rel = p.relative_to(ROOT)
        section_id = f"doc-{idx}-{slugify(rel.stem)}"
        label = file_label(rel)
        folder = rel.parts[0] if len(rel.parts) > 1 else "root"
        nav_items.append(
            f'<a class="nav-link" href="#{section_id}" data-folder="{html.escape(folder)}">'
            f'<span class="nav-label">{html.escape(label)}</span>'
            f'</a>'
        )
        rendered = render_markdown(p.read_text(encoding="utf-8"), section_id)
        sections.append(
            f'<section class="doc fade-in" id="{section_id}" data-folder="{html.escape(folder)}">'
            f'<div class="doc-header">'
            f'<span class="doc-folder">{html.escape(str(rel.parent) if len(rel.parts) > 1 else "root")}</span>'
            f'<h2 class="doc-title">{html.escape(rel.stem.replace("-", " ").replace("_", " ").title())}</h2>'
            f'</div>'
            f'<div class="doc-body">{rendered}</div>'
            f'</section>'
        )

    page = f"""<!doctype html>
<html lang="en" data-theme="light">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>SRAM AI Playbook</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
  <style>
    :root {{
      --red: #e10600;
      --red-dim: rgba(225,6,0,0.12);
      --ink: #0d1117;
      --ink-2: #374151;
      --ink-3: #6b7280;
      --bg: #f5f7fa;
      --panel: #ffffff;
      --border: #e5e8ee;
      --nav-bg: #0d1117;
      --nav-text: #c9d5e8;
      --nav-active: #ffffff;
      --nav-hover-bg: rgba(255,255,255,0.06);
      --accent: #3b82f6;
      --code-bg: #f1f3f7;
      --shadow: 0 4px 24px rgba(13,17,23,0.07);
      --shadow-lg: 0 8px 40px rgba(13,17,23,0.12);
      --transition: 200ms cubic-bezier(0.4,0,0.2,1);
    }}

    [data-theme="dark"] {{
      --ink: #f0f4f8;
      --ink-2: #cbd5e1;
      --ink-3: #94a3b8;
      --bg: #0d1117;
      --panel: #161b22;
      --border: #30363d;
      --code-bg: #1e2530;
      --shadow: 0 4px 24px rgba(0,0,0,0.3);
      --shadow-lg: 0 8px 40px rgba(0,0,0,0.4);
    }}

    * {{ box-sizing: border-box; margin: 0; padding: 0; }}

    html {{ scroll-behavior: smooth; }}

    body {{
      font-family: "Inter", "Segoe UI", system-ui, sans-serif;
      background: var(--bg);
      color: var(--ink);
      line-height: 1.6;
      font-size: 15px;
      transition: background var(--transition), color var(--transition);
    }}

    /* ── PROGRESS BAR ── */
    #progress {{
      position: fixed;
      top: 0; left: 0;
      height: 3px;
      width: 0%;
      background: var(--red);
      z-index: 9999;
      transition: width 80ms linear;
    }}

    /* ── LAYOUT ── */
    .layout {{
      display: grid;
      grid-template-columns: 280px 1fr;
      min-height: 100vh;
    }}

    /* ── SIDEBAR ── */
    nav {{
      position: sticky;
      top: 0;
      height: 100vh;
      overflow-y: auto;
      background: var(--nav-bg);
      display: flex;
      flex-direction: column;
      border-right: 1px solid rgba(225,6,0,0.3);
    }}

    nav::-webkit-scrollbar {{ width: 4px; }}
    nav::-webkit-scrollbar-thumb {{ background: rgba(255,255,255,0.1); border-radius: 2px; }}

    .nav-top {{
      padding: 20px 18px 14px;
      border-bottom: 1px solid rgba(255,255,255,0.06);
    }}

    .nav-brand {{
      font-size: 17px;
      font-weight: 800;
      color: #fff;
      letter-spacing: -0.3px;
    }}

    .nav-brand span {{ color: var(--red); }}

    .nav-sub {{
      font-size: 11px;
      color: #64748b;
      margin-top: 2px;
    }}

    .nav-search {{
      margin-top: 12px;
      position: relative;
    }}

    .nav-search input {{
      width: 100%;
      background: rgba(255,255,255,0.07);
      border: 1px solid rgba(255,255,255,0.1);
      border-radius: 8px;
      padding: 7px 10px 7px 30px;
      font-size: 12px;
      color: #fff;
      font-family: inherit;
      outline: none;
      transition: border-color var(--transition);
    }}

    .nav-search input::placeholder {{ color: #64748b; }}
    .nav-search input:focus {{ border-color: rgba(225,6,0,0.5); }}

    .nav-search svg {{
      position: absolute;
      left: 9px;
      top: 50%;
      transform: translateY(-50%);
      opacity: 0.4;
    }}

    .nav-links {{
      flex: 1;
      padding: 10px 10px 20px;
      display: flex;
      flex-direction: column;
      gap: 2px;
    }}

    .nav-group-label {{
      font-size: 10px;
      font-weight: 600;
      letter-spacing: 0.8px;
      text-transform: uppercase;
      color: #4b5563;
      padding: 10px 8px 4px;
    }}

    .nav-link {{
      display: block;
      text-decoration: none;
      color: var(--nav-text);
      font-size: 13px;
      padding: 7px 10px;
      border-radius: 7px;
      border: 1px solid transparent;
      transition: all var(--transition);
      line-height: 1.35;
    }}

    .nav-link:hover {{
      background: var(--nav-hover-bg);
      color: #fff;
      border-color: rgba(255,255,255,0.08);
    }}

    .nav-link.active {{
      background: rgba(225,6,0,0.15);
      border-color: rgba(225,6,0,0.3);
      color: var(--nav-active);
    }}

    .nav-link .nav-label {{ display: block; }}

    .nav-bottom {{
      padding: 14px 18px;
      border-top: 1px solid rgba(255,255,255,0.06);
      display: flex;
      gap: 8px;
    }}

    .btn-ghost {{
      flex: 1;
      background: rgba(255,255,255,0.07);
      border: 1px solid rgba(255,255,255,0.1);
      color: #c9d5e8;
      border-radius: 8px;
      padding: 7px 10px;
      font-size: 11px;
      font-family: inherit;
      cursor: pointer;
      transition: all var(--transition);
      text-align: center;
    }}

    .btn-ghost:hover {{ background: rgba(255,255,255,0.13); color: #fff; }}

    /* ── MAIN ── */
    main {{
      padding: 28px 32px 60px;
      max-width: 900px;
    }}

    /* ── HERO ── */
    .hero {{
      background: var(--panel);
      border: 1px solid var(--border);
      border-radius: 16px;
      padding: 28px 32px;
      margin-bottom: 20px;
      box-shadow: var(--shadow);
      position: relative;
      overflow: hidden;
    }}

    .hero::before {{
      content: "";
      position: absolute;
      top: 0; left: 0; right: 0;
      height: 3px;
      background: linear-gradient(90deg, var(--red), #ff6b35, var(--red));
      background-size: 200% 100%;
      animation: shimmer 3s infinite linear;
    }}

    @keyframes shimmer {{
      0% {{ background-position: 200% 0; }}
      100% {{ background-position: -200% 0; }}
    }}

    .hero-row {{
      display: flex;
      align-items: flex-start;
      justify-content: space-between;
      gap: 24px;
      flex-wrap: wrap;
    }}

    .hero h1 {{
      font-size: 26px;
      font-weight: 800;
      letter-spacing: -0.5px;
      color: var(--ink);
      margin-bottom: 4px;
    }}

    .hero-sub {{
      font-size: 13px;
      color: var(--ink-3);
    }}

    .hero-actions {{
      display: flex;
      gap: 8px;
      flex-shrink: 0;
      margin-top: 4px;
    }}

    .btn {{
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 9px 16px;
      border-radius: 9px;
      font-size: 13px;
      font-weight: 500;
      font-family: inherit;
      cursor: pointer;
      border: none;
      transition: all var(--transition);
      text-decoration: none;
    }}

    .btn-primary {{
      background: var(--ink);
      color: #fff;
    }}

    [data-theme="dark"] .btn-primary {{ background: #fff; color: #0d1117; }}

    .btn-primary:hover {{ opacity: 0.85; transform: translateY(-1px); }}

    .btn-outline {{
      background: transparent;
      color: var(--ink-2);
      border: 1px solid var(--border);
    }}

    .btn-outline:hover {{ background: var(--bg); transform: translateY(-1px); }}

    /* ── METRICS STRIP ── */
    .metrics {{
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 12px;
      margin-bottom: 20px;
    }}

    .metric {{
      background: var(--panel);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 16px 18px;
      box-shadow: var(--shadow);
      transition: transform var(--transition), box-shadow var(--transition);
    }}

    .metric:hover {{ transform: translateY(-2px); box-shadow: var(--shadow-lg); }}

    .metric-value {{
      font-size: 24px;
      font-weight: 800;
      letter-spacing: -0.5px;
      color: var(--red);
    }}

    .metric-label {{
      font-size: 11px;
      font-weight: 500;
      color: var(--ink-3);
      text-transform: uppercase;
      letter-spacing: 0.5px;
      margin-top: 2px;
    }}

    .metric-sub {{
      font-size: 12px;
      color: var(--ink-3);
      margin-top: 2px;
    }}

    /* ── FILTER CHIPS ── */
    .filters {{
      display: flex;
      gap: 8px;
      flex-wrap: wrap;
      margin-bottom: 18px;
    }}

    .chip {{
      padding: 6px 14px;
      border-radius: 999px;
      font-size: 12px;
      font-weight: 500;
      border: 1px solid var(--border);
      background: var(--panel);
      color: var(--ink-2);
      cursor: pointer;
      transition: all var(--transition);
    }}

    .chip:hover, .chip.active {{
      background: var(--ink);
      color: #fff;
      border-color: var(--ink);
    }}

    [data-theme="dark"] .chip:hover,
    [data-theme="dark"] .chip.active {{
      background: #fff;
      color: #0d1117;
      border-color: #fff;
    }}

    /* ── DOC CARDS ── */
    .doc {{
      background: var(--panel);
      border: 1px solid var(--border);
      border-radius: 14px;
      margin-bottom: 16px;
      box-shadow: var(--shadow);
      overflow: hidden;
      transition: box-shadow var(--transition), transform var(--transition);
    }}

    .doc:hover {{ box-shadow: var(--shadow-lg); }}

    .doc.hidden {{ display: none; }}

    .doc-header {{
      padding: 16px 20px 14px;
      border-bottom: 1px solid var(--border);
      display: flex;
      align-items: baseline;
      gap: 10px;
      cursor: pointer;
      user-select: none;
    }}

    .doc-header:hover .doc-title {{ color: var(--red); }}

    .doc-folder {{
      font-size: 10px;
      font-weight: 600;
      letter-spacing: 0.6px;
      text-transform: uppercase;
      color: var(--ink-3);
      background: var(--bg);
      border: 1px solid var(--border);
      padding: 2px 8px;
      border-radius: 999px;
      flex-shrink: 0;
    }}

    .doc-title {{
      font-size: 16px;
      font-weight: 700;
      color: var(--ink);
      transition: color var(--transition);
      flex: 1;
    }}

    .doc-toggle {{
      font-size: 18px;
      color: var(--ink-3);
      transition: transform var(--transition);
      flex-shrink: 0;
    }}

    .doc.collapsed .doc-toggle {{ transform: rotate(-90deg); }}
    .doc.collapsed .doc-body {{ display: none; }}

    .doc-body {{
      padding: 18px 20px 20px;
    }}

    /* ── TYPOGRAPHY ── */
    .doc-body h1 {{ font-size: 20px; font-weight: 700; margin: 20px 0 8px; color: var(--ink); }}
    .doc-body h2 {{ font-size: 17px; font-weight: 700; margin: 18px 0 8px; color: var(--ink); padding-left: 10px; border-left: 3px solid var(--red); }}
    .doc-body h3 {{ font-size: 14px; font-weight: 600; margin: 14px 0 6px; color: var(--ink-2); }}
    .doc-body h4 {{ font-size: 13px; font-weight: 600; margin: 10px 0 4px; color: var(--ink-2); }}
    .doc-body p {{ margin: 7px 0; font-size: 14px; color: var(--ink-2); line-height: 1.7; }}
    .doc-body ul {{ margin: 7px 0 10px 18px; }}
    .doc-body li {{ margin: 5px 0; font-size: 14px; color: var(--ink-2); line-height: 1.6; }}
    .doc-body hr {{ border: none; border-top: 1px solid var(--border); margin: 16px 0; }}
    .doc-body strong {{ color: var(--ink); font-weight: 600; }}
    .doc-body a {{ color: var(--accent); text-decoration: none; }}
    .doc-body a:hover {{ text-decoration: underline; }}

    .doc-body code {{
      background: var(--code-bg);
      padding: 2px 6px;
      border-radius: 5px;
      font-family: ui-monospace, "SF Mono", Menlo, monospace;
      font-size: 12px;
      color: var(--red);
      border: 1px solid var(--border);
    }}

    .doc-body pre {{
      background: #0d1117;
      color: #e2e8f0;
      padding: 14px 16px;
      border-radius: 10px;
      overflow: auto;
      margin: 10px 0;
      font-size: 13px;
    }}

    .doc-body pre code {{
      background: transparent;
      padding: 0;
      color: inherit;
      border: none;
      font-size: inherit;
    }}

    /* ── TABLES ── */
    .table-wrap {{ overflow-x: auto; margin: 10px 0 14px; border-radius: 10px; border: 1px solid var(--border); }}

    .doc-body table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 13px;
      min-width: 480px;
    }}

    .doc-body th, .doc-body td {{
      padding: 9px 12px;
      text-align: left;
      vertical-align: top;
      border-bottom: 1px solid var(--border);
    }}

    .doc-body th {{
      background: var(--bg);
      font-weight: 600;
      font-size: 12px;
      color: var(--ink-2);
      text-transform: uppercase;
      letter-spacing: 0.4px;
    }}

    .doc-body tr:last-child td {{ border-bottom: none; }}
    .doc-body tr:hover td {{ background: rgba(0,0,0,0.015); }}
    [data-theme="dark"] .doc-body tr:hover td {{ background: rgba(255,255,255,0.025); }}

    /* ── ANIMATIONS ── */
    .fade-in {{
      opacity: 0;
      transform: translateY(16px);
      transition: opacity 400ms ease, transform 400ms ease;
    }}

    .fade-in.visible {{
      opacity: 1;
      transform: translateY(0);
    }}

    /* ── SEARCH HIGHLIGHT ── */
    mark {{
      background: rgba(225,6,0,0.18);
      color: inherit;
      border-radius: 2px;
      padding: 0 1px;
    }}

    /* ── TOAST ── */
    .toast {{
      position: fixed;
      bottom: 24px;
      right: 24px;
      background: var(--ink);
      color: #fff;
      padding: 10px 18px;
      border-radius: 10px;
      font-size: 13px;
      font-weight: 500;
      box-shadow: var(--shadow-lg);
      opacity: 0;
      transform: translateY(8px);
      transition: all 300ms ease;
      pointer-events: none;
      z-index: 9998;
    }}

    .toast.show {{ opacity: 1; transform: translateY(0); }}

    /* ── RESPONSIVE ── */
    @media (max-width: 900px) {{
      .layout {{ grid-template-columns: 1fr; }}
      nav {{ position: relative; height: auto; }}
      main {{ padding: 16px; }}
      .metrics {{ grid-template-columns: repeat(2, 1fr); }}
    }}

    @media (max-width: 540px) {{
      .metrics {{ grid-template-columns: 1fr 1fr; }}
      .hero-row {{ flex-direction: column; }}
    }}

    /* ── PRINT ── */
    @media print {{
      @page {{ size: Letter portrait; margin: 0.45in; }}
      body {{ background: #fff; color: #000; }}
      #progress, nav, .hero-actions, .filters, .chip,
      .doc-toggle, .btn, .toast {{ display: none !important; }}
      .layout {{ grid-template-columns: 1fr; }}
      main {{ padding: 0; max-width: 100%; }}
      .doc {{ border: 1px solid #ccc; box-shadow: none; page-break-inside: avoid; margin-bottom: 12px; }}
      .doc.collapsed .doc-body {{ display: block !important; }}
      .hero {{ border: 1px solid #ccc; }}
      .metrics {{ gap: 8px; }}
      .metric {{ border: 1px solid #ccc; box-shadow: none; }}
    }}
  </style>
</head>
<body>
  <div id="progress"></div>
  <div class="toast" id="toast"></div>

  <div class="layout">
    <!-- SIDEBAR -->
    <nav>
      <div class="nav-top">
        <div class="nav-brand">SRAM <span>AI</span> Playbook</div>
        <div class="nav-sub">Kellogg AIML/MORS 950 &mdash; Winter 2026</div>
        <div class="nav-search">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/></svg>
          <input type="text" id="navSearch" placeholder="Search documents..." autocomplete="off" />
        </div>
      </div>

      <div class="nav-links" id="navLinks">
        {''.join(nav_items)}
      </div>

      <div class="nav-bottom">
        <button class="btn-ghost" onclick="toggleTheme()">&#9680; Theme</button>
        <button class="btn-ghost" onclick="expandAll()">&#9633; Expand all</button>
        <button class="btn-ghost" onclick="window.print()">&#8599; Print</button>
      </div>
    </nav>

    <!-- MAIN -->
    <main>
      <!-- HERO -->
      <div class="hero">
        <div class="hero-row">
          <div>
            <h1>Executive Analysis Workspace</h1>
            <p class="hero-sub">SRAM LLC &mdash; AI Adoption Playbook &mdash; {len(files)} documents</p>
          </div>
          <div class="hero-actions">
            <a class="btn btn-outline" href="interview/interview.html">Interview &rarr;</a>
            <button class="btn btn-primary" onclick="window.print()">Export PDF</button>
          </div>
        </div>
      </div>

      <!-- METRICS -->
      <div class="metrics">
        <div class="metric">
          <div class="metric-value">$10.2M</div>
          <div class="metric-label">Year-1 Net Value</div>
          <div class="metric-sub">Expected case</div>
        </div>
        <div class="metric">
          <div class="metric-value">3.8x</div>
          <div class="metric-label">Return on Spend</div>
          <div class="metric-sub">Year 1</div>
        </div>
        <div class="metric">
          <div class="metric-value">90d</div>
          <div class="metric-label">Pilot Timeline</div>
          <div class="metric-sub">AXS + Hammerhead</div>
        </div>
        <div class="metric">
          <div class="metric-value">{len(files)}</div>
          <div class="metric-label">Documents</div>
          <div class="metric-sub">Analysis files</div>
        </div>
      </div>

      <!-- FILTER CHIPS -->
      <div class="filters" id="filters">
        <button class="chip active" data-filter="all" onclick="filterDocs('all', this)">All</button>
        <button class="chip" data-filter="root" onclick="filterDocs('root', this)">Overview</button>
        <button class="chip" data-filter="ai adoption" onclick="filterDocs('ai adoption', this)">AI Adoption</button>
        <button class="chip" data-filter="competitors" onclick="filterDocs('competitors', this)">Competitors</button>
        <button class="chip" data-filter="revenue" onclick="filterDocs('revenue', this)">Revenue</button>
        <button class="chip" data-filter="interview" onclick="filterDocs('interview', this)">Interview</button>
      </div>

      <!-- DOCUMENTS -->
      <div id="docs">
        {''.join(sections)}
      </div>

      <p style="text-align:center;font-size:12px;color:var(--ink-3);margin-top:32px;">
        Built from {len(files)} markdown files &mdash; rebuild with <code>python3 tools/build_analysis_hub.py</code>
      </p>
    </main>
  </div>

  <script>
    // ── PROGRESS BAR ──
    const bar = document.getElementById('progress');
    window.addEventListener('scroll', () => {{
      const pct = window.scrollY / (document.documentElement.scrollHeight - window.innerHeight) * 100;
      bar.style.width = pct + '%';
    }}, {{ passive: true }});

    // ── THEME ──
    function toggleTheme() {{
      const html = document.documentElement;
      const next = html.dataset.theme === 'dark' ? 'light' : 'dark';
      html.dataset.theme = next;
      localStorage.setItem('theme', next);
    }}
    const saved = localStorage.getItem('theme');
    if (saved) document.documentElement.dataset.theme = saved;

    // ── COLLAPSE / EXPAND ──
    document.querySelectorAll('.doc-header').forEach(h => {{
      h.addEventListener('click', () => {{
        h.closest('.doc').classList.toggle('collapsed');
      }});
    }});

    function expandAll() {{
      document.querySelectorAll('.doc').forEach(d => d.classList.remove('collapsed'));
    }}

    // ── FADE IN ON SCROLL ──
    const observer = new IntersectionObserver(entries => {{
      entries.forEach(e => {{ if (e.isIntersecting) e.target.classList.add('visible'); }});
    }}, {{ threshold: 0.05 }});
    document.querySelectorAll('.fade-in').forEach(el => observer.observe(el));

    // ── ACTIVE NAV ──
    const sections = document.querySelectorAll('section.doc');
    const navLinks = document.querySelectorAll('.nav-link');

    const navObserver = new IntersectionObserver(entries => {{
      entries.forEach(e => {{
        if (e.isIntersecting) {{
          navLinks.forEach(l => l.classList.remove('active'));
          const active = document.querySelector(`.nav-link[href="#${{e.target.id}}"]`);
          if (active) {{
            active.classList.add('active');
            active.scrollIntoView({{ block: 'nearest' }});
          }}
        }}
      }});
    }}, {{ rootMargin: '-20% 0px -70% 0px' }});
    sections.forEach(s => navObserver.observe(s));

    // ── FILTER CHIPS ──
    function filterDocs(filter, btn) {{
      document.querySelectorAll('.chip').forEach(c => c.classList.remove('active'));
      btn.classList.add('active');
      document.querySelectorAll('section.doc').forEach(doc => {{
        const folder = doc.dataset.folder;
        doc.classList.toggle('hidden', filter !== 'all' && folder !== filter);
      }});
      document.querySelectorAll('.nav-link').forEach(link => {{
        const folder = link.dataset.folder;
        link.style.display = (filter === 'all' || folder === filter) ? '' : 'none';
      }});
    }}

    // ── NAV SEARCH ──
    document.getElementById('navSearch').addEventListener('input', function() {{
      const q = this.value.trim().toLowerCase();
      document.querySelectorAll('.nav-link').forEach(link => {{
        const label = link.textContent.toLowerCase();
        link.style.display = (!q || label.includes(q)) ? '' : 'none';
      }});
    }});

    // ── CONTENT SEARCH (Ctrl/Cmd+K) ──
    let searchMode = false;
    document.addEventListener('keydown', e => {{
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {{
        e.preventDefault();
        document.getElementById('navSearch').focus();
      }}
    }});

    // ── TOAST ──
    function showToast(msg) {{
      const t = document.getElementById('toast');
      t.textContent = msg;
      t.classList.add('show');
      setTimeout(() => t.classList.remove('show'), 2200);
    }}

    // Copy code blocks on click
    document.querySelectorAll('pre').forEach(pre => {{
      pre.style.cursor = 'pointer';
      pre.title = 'Click to copy';
      pre.addEventListener('click', () => {{
        navigator.clipboard.writeText(pre.textContent).then(() => showToast('Copied to clipboard'));
      }});
    }});
  </script>
</body>
</html>
"""

    OUT.write_text(page, encoding="utf-8")
    print(f"Wrote {OUT}")
    print(f"Included {len(files)} markdown files")


if __name__ == "__main__":
    build()
