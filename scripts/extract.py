"""Split a dashboard index.html into data/*.json + pipeline/template.html.
Every <script type="application/json" id="X"> block becomes data/X.json and is
replaced by a {{DATA:X}} placeholder. build.py reverses this."""
import re, json, sys, pathlib
root = pathlib.Path(__file__).resolve().parents[1]
src = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else root / "index.html")
s = src.read_text(encoding="utf-8")
pat = re.compile(r'(<script type="application/json" id="([^"]+)"[^>]*>)(.*?)(</script>)', re.S)
n = 0
def rep(m):
    global n
    k, body = m.group(2), m.group(3)
    out = root / "data" / f"{k}.json"
    if body.strip():
        try:
            out.write_text(json.dumps(json.loads(body), ensure_ascii=False, indent=1), encoding="utf-8")
        except json.JSONDecodeError:
            out.write_text(body, encoding="utf-8")
    else:
        out.write_text("", encoding="utf-8")
    n += 1
    return m.group(1) + "{{DATA:" + k + "}}" + m.group(4)
t = pat.sub(rep, s)
(root / "pipeline" / "template.html").write_text(t, encoding="utf-8")
print(f"extracted {n} blocks; template {len(t)//1024} KB")
