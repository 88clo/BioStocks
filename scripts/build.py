"""Rebuild index.html from pipeline/template.html + data/*.json (compact JSON)."""
import re, json, pathlib
root = pathlib.Path(__file__).resolve().parents[1]
import sys; sys.path.insert(0, str(root / "scripts")); import north_star; north_star.build()  # NORTH_STAR.md -> data/north-star.json
t = (root / "pipeline" / "template.html").read_text(encoding="utf-8")
# strip any previously saved copy of the Brief overlay (a "save notes" copy re-imported via extract.py), then inject the current one
t = re.sub(r"<!-- (BRIEF|NAV|SYNTH2?)-START.*?<!-- (BRIEF|NAV|SYNTH2?)-END -->\n?", "", t, flags=re.S)
brief = (root / "pipeline" / "brief.html").read_text(encoding="utf-8") + (root / "pipeline" / "synth.html").read_text(encoding="utf-8") + (root / "pipeline" / "synth2.html").read_text(encoding="utf-8") + (root / "pipeline" / "nav.html").read_text(encoding="utf-8")
i = t.rfind("</body>")
t = t[:i] + brief + t[i:]
def rep(m):
    p = root / "data" / f"{m.group(1)}.json"
    raw = p.read_text(encoding="utf-8") if p.exists() else ""
    if not raw.strip(): return ""
    try: txt = json.dumps(json.loads(raw), ensure_ascii=False, separators=(",", ":"))
    except json.JSONDecodeError: txt = raw
    return txt.replace("</", "<\\/")
out = re.sub(r"\{\{DATA:([A-Za-z0-9_-]+)\}\}", rep, t)
(root / "index.html").write_text(out, encoding="utf-8")
print(f"built index.html {len(out)//1024} KB")

# Thesis audit on every build (Nov 25 2026): calls are computed live from price, so a written thesis can drift out of step
# with its call. tests/thaudit.py loads the page headless and counts stale caps, missing lines, generic CEO notes and any
# hand-written thesis whose direction disagrees with the page's call. Skipped quietly if Playwright/Chrome is missing.
import subprocess, sys
if "--no-audit" not in sys.argv and (root / "tests/thaudit.py").exists():
    try:
        r = subprocess.run([sys.executable, str(root / "tests/thaudit.py")], capture_output=True, text=True, timeout=180)
        lines = [l for l in r.stdout.splitlines() if l.strip()]
        bad = [l for l in lines[1:] if l.split() and l.split()[0] in ("stale_cap", "call_mismatch", "generic_ceo", "odd_phrase", "err") and len(l.split()) > 1 and l.split()[1] != "0"]
        print("audit:", lines[0] if lines else (r.stderr.strip().splitlines() or ["no output"])[-1])
        for l in bad: print("  AUDIT WARNING:", l)
    except Exception as e:
        print("audit skipped:", e)
