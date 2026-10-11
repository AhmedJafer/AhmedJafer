"""Generate the GitHub profile banner and tools strip (light + dark) as SVG.

Run: python3 assets/make_svgs.py assets

Images in a GitHub README cannot load web fonts, so every headline word is its own
<text> centred at a fixed x: whatever font the viewer has, the arcs still line up.
"""
import sys
from pathlib import Path

OUT = Path(sys.argv[1])
OUT.mkdir(parents=True, exist_ok=True)

THEMES = {
    "light": dict(bg="#fafafa", line="#e6e6ea", ink="#0e0e10", ink2="#34343a", muted="#63636c", accent="#3b2bff", a="59,43,255"),
    "dark": dict(bg="#111118", line="#26262e", ink="#ededf0", ink2="#cacad0", muted="#93939c", accent="#8a80ff", a="138,128,255"),
}
SANS = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif"
MONO = "ui-monospace, SFMono-Regular, Menlo, Consolas, 'DejaVu Sans Mono', monospace"

W, H = 1200, 330
WORDS = "I build AI systems that learn, reason, and ship.".split()
# Helvetica/Arial advance widths (em) — close enough for the fonts most viewers get
EM = dict(zip("abcdefghijklmnopqrstuvwxyz", [.556,.556,.5,.556,.556,.278,.556,.556,.222,.222,.5,.222,.833,.556,.556,.556,.556,.333,.5,.278,.556,.5,.722,.5,.5,.5]))
EM.update({"A": .667, "I": .278, ",": .278, ".": .278})
GAP = 22
BASE = 232         # headline baseline


def width(w, fs):
    return sum(EM.get(c, .556) for c in w) * fs - len(w)  # letter-spacing -1px


FS = 48            # headline font size, shrunk until the line fits between the margins
while sum(width(w, FS) for w in WORDS) + GAP * (len(WORDS) - 1) > W - 120:
    FS -= 1

# word centres, laid out left to right from x=60
xs, x = [], 60
for w in WORDS:
    ww = width(w, FS)
    xs.append(x + ww / 2)
    x += ww + GAP
x -= GAP

# three query tokens the banner cycles through, with hand-written causal attention weights
STATES = [
    (2, {1: .55, 0: .30}),           # "AI" -> build, I
    (4, {3: .85, 2: .15}),           # "that" -> systems, AI
    (8, {1: .60, 3: .30, 7: .10}),   # "ship" -> build, systems, and
]
CYCLE = 3.2  # seconds per state


def clean(w):
    return w.strip(".,")


def banner(t):
    top = BASE - FS * 0.78   # top of the lowercase/cap height
    g = []
    for k, (q, ws) in enumerate(STATES):
        parts = []
        for j, w in ws.items():
            ww = width(WORDS[j], FS) + 14
            parts.append(f'<rect x="{xs[j]-ww/2:.1f}" y="{top-8:.1f}" width="{ww:.1f}" height="{FS*1.02:.1f}" rx="8" fill="rgba({t["a"]},{w*.42:.2f})"/>')
        qw = width(WORDS[q], FS)
        parts.append(f'<rect x="{xs[q]-qw/2:.1f}" y="{BASE+9}" width="{qw:.1f}" height="3.5" rx="1.75" fill="{t["accent"]}"/>')
        for j, w in sorted(ws.items(), key=lambda kv: abs(xs[kv[0]] - xs[q]), reverse=True):
            x1, x2 = xs[q], xs[j]
            lift = 18 + 4 * abs(x1 - x2) ** .5  # grows slowly: long arcs stay ordered but clear of the name row
            cy = top - 12 - lift
            parts.append(f'<path d="M{x1:.1f} {top-12:.1f} Q{(x1+x2)/2:.1f} {cy:.1f} {x2:.1f} {top-12:.1f}" fill="none" stroke="{t["accent"]}" stroke-width="{1+w*5:.1f}" stroke-linecap="round" opacity="{.3+w*.7:.2f}"/>')
            parts.append(f'<text x="{(x1+x2)/2:.1f}" y="{(top-12+cy)/2-6:.1f}" text-anchor="middle" class="w">{w:.2f}</text>')
        best = max(ws, key=ws.get)
        parts.append(f'<text x="60" y="{H-34}" class="cap">query: "{clean(WORDS[q])}" → attends most to "{clean(WORDS[best])}" ({ws[best]:.2f})</text>')
        g.append(f'<g class="s s{k}">' + "".join(parts) + "</g>")

    words = "".join(f'<text x="{x:.1f}" y="{BASE}" text-anchor="middle" class="h">{w}</text>' for x, w in zip(xs, WORDS))
    n = len(STATES)
    css = f"""
    .name {{ font: 600 26px {SANS}; fill: {t['ink']}; }}
    .role {{ font: 15px {MONO}; fill: {t['muted']}; }}
    .h {{ font: 500 {FS}px {SANS}; fill: {t['ink']}; letter-spacing: -1px; }}
    .w {{ font: 12px {MONO}; fill: {t['accent']}; paint-order: stroke; stroke: {t['bg']}; stroke-width: 5px; stroke-linejoin: round; }}
    .cap {{ font: 14px {MONO}; fill: {t['muted']}; }}
    .s {{ opacity: 0; animation: cyc {CYCLE*n}s linear infinite both; }}
    {''.join(f'.s{k} {{ animation-delay: {CYCLE*k:.1f}s; }}' for k in range(n))}
    @keyframes cyc {{ 0% {{ opacity: 0; }} {100/n*.08:.1f}% {{ opacity: 1; }} {100/n*.92:.1f}% {{ opacity: 1; }} {100/n:.1f}% {{ opacity: 0; }} 100% {{ opacity: 0; }} }}
    @media (prefers-reduced-motion: reduce) {{ .s {{ animation: none; }} .s0 {{ opacity: 1; }} }}
    """
    logo = (f'<g transform="translate(60 44)"><path d="M5 14 Q15 -3 25 14" fill="none" stroke="{t["accent"]}" stroke-width="2.4"/>'
            f'<circle cx="5" cy="14" r="3.6" fill="{t["ink"]}"/><circle cx="25" cy="14" r="3.6" fill="{t["ink"]}"/></g>')
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="Ahmed J. O. Ahmed — AI Engineer &amp; Researcher. I build AI systems that learn, reason, and ship.">
  <title>Ahmed J. O. Ahmed — AI Engineer &amp; Researcher</title>
  <style>{css}</style>
  <rect x="1" y="1" width="{W-2}" height="{H-2}" rx="20" fill="{t['bg']}" stroke="{t['line']}" stroke-width="2"/>
  {logo}
  <text x="102" y="66" class="name">Ahmed J. O. Ahmed</text>
  <text x="{W-60}" y="64" text-anchor="end" class="role">AI Engineer &amp; Researcher · London</text>
  <line x1="60" y1="{H-62}" x2="{W-60}" y2="{H-62}" stroke="{t['line']}" stroke-width="1.5"/>
  {''.join(g)}
  {words}
</svg>
"""


TOOLS = ["Python", "PyTorch", "Hugging Face", "LangChain", "LangGraph", "CrewAI", "OpenCV", "YOLO",
         "AWS", "Docker", "FastAPI", "MLflow", "Neo4j", "PostgreSQL"]


def tools(t):
    fs, cw, pad, h, gap = 14, 14 * .6, 16, 34, 10
    widths = [len(n) * cw + 2 * pad for n in TOOLS]
    # two balanced rows, each centred
    half = (sum(widths) + gap * (len(TOOLS) - 1)) / 2
    rows, cur, acc = [], [], 0
    for n, w in zip(TOOLS, widths):
        if cur and acc + w / 2 > half and len(rows) == 0:
            rows.append(cur); cur, acc = [], 0
        cur.append((n, w)); acc += w + gap
    rows.append(cur)
    rw = [sum(w for _, w in r) + gap * (len(r) - 1) for r in rows]
    maxw = max(rw) + 2
    chips = []
    for i, (r, wsum) in enumerate(zip(rows, rw)):
        x, y = (maxw - wsum) / 2, i * (h + gap) + 1
        for n, w in r:
            chips.append(f'<rect x="{x:.1f}" y="{y}" width="{w:.1f}" height="{h}" rx="{h/2}" fill="rgba({t["a"]},.08)" stroke="rgba({t["a"]},.35)"/>'
                         f'<text x="{x+w/2:.1f}" y="{y+h/2+5}" text-anchor="middle">{n}</text>')
            x += w + gap
    total_h = len(rows) * (h + gap) - gap + 2
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {maxw:.0f} {total_h}" width="{maxw:.0f}" height="{total_h}" role="img" aria-label="Tools: {', '.join(TOOLS)}">
  <title>Tools: {', '.join(TOOLS)}</title>
  <style>text {{ font: 500 {fs}px {MONO}; fill: {t['accent']}; }}</style>
  {''.join(chips)}
</svg>
"""


for name, t in THEMES.items():
    (OUT / f"banner-{name}.svg").write_text(banner(t))
    (OUT / f"tools-{name}.svg").write_text(tools(t))
print("font", FS, "headline right edge:", round(x), "of", W - 60)
