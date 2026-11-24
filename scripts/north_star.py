"""Render NORTH_STAR.md to data/north-star.json so the dashboard shows the same text (Record > North star)."""
import html, json, pathlib, re
root = pathlib.Path(__file__).resolve().parents[1]

def inline(s):
    s = html.escape(s, quote=False)
    s = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s)
    s = re.sub(r"(?<![\w*])[_*](?!\s)(.+?)(?<!\s)[_*](?![\w*])", r"<i>\1</i>", s)
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    return s

def render(md):
    out, lines, i = [], md.splitlines(), 0
    while i < len(lines):
        ln = lines[i]
        if not ln.strip(): i += 1; continue
        m = re.match(r"(#{1,3})\s+(.*)", ln)
        if m:
            n = len(m.group(1)); out.append(f'<h{n+1} class="ns-h{n}">{inline(m.group(2))}</h{n+1}>'); i += 1; continue
        if ln.startswith("|"):
            rows = []
            while i < len(lines) and lines[i].startswith("|"):
                cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]
                if not all(re.fullmatch(r":?-+:?", c) for c in cells): rows.append(cells)
                i += 1
            h = "<tr>" + "".join(f"<th>{inline(c)}</th>" for c in rows[0]) + "</tr>"
            b = "".join("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in r) + "</tr>" for r in rows[1:])
            out.append(f'<table class="brf-t ns-t">{h}{b}</table>'); continue
        m = re.match(r"\s*(\d+\.|[-*])\s+(.*)", ln)
        if m:
            tag = "ol" if m.group(1)[0].isdigit() else "ul"; items = []
            while i < len(lines) and re.match(r"\s*(\d+\.|[-*])\s+", lines[i]):
                items.append(re.sub(r"\s*(\d+\.|[-*])\s+", "", lines[i], count=1)); i += 1
            out.append(f"<{tag}>" + "".join(f"<li>{inline(x)}</li>" for x in items) + f"</{tag}>"); continue
        if ln.startswith(">"):
            out.append(f'<div class="brf-note">{inline(ln.lstrip("> "))}</div>'); i += 1; continue
        para = []
        while i < len(lines) and lines[i].strip() and not re.match(r"(#|\||\s*(\d+\.|[-*])\s|>)", lines[i]):
            para.append(lines[i]); i += 1
        out.append(f"<p>{inline(' '.join(para))}</p>")
    return "\n".join(out)

def build():
    md = (root / "NORTH_STAR.md").read_text(encoding="utf-8")
    (root / "data" / "north-star.json").write_text(json.dumps({"html": render(md)}, ensure_ascii=False), encoding="utf-8")

if __name__ == "__main__":
    build(); print("north-star.json written")
