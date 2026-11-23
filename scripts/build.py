"""Rebuild index.html from pipeline/template.html + data/*.json (compact JSON)."""
import re, json, pathlib
root = pathlib.Path(__file__).resolve().parents[1]
t = (root / "pipeline" / "template.html").read_text(encoding="utf-8")
# strip any previously saved copy of the Brief overlay (a "save notes" copy re-imported via extract.py), then inject the current one
t = re.sub(r"<!-- (BRIEF|NAV|SYNTH)-START.*?<!-- (BRIEF|NAV|SYNTH)-END -->\n?", "", t, flags=re.S)
brief = (root / "pipeline" / "brief.html").read_text(encoding="utf-8") + (root / "pipeline" / "synth.html").read_text(encoding="utf-8") + (root / "pipeline" / "nav.html").read_text(encoding="utf-8")
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
