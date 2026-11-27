"""Stale-data scan (Nov 27 2026) -> data/stale-flags.json.
For every covered company: 8-Ks filed in the last 60 days whose press-release headline carries thesis-changing language
(discontinued, terminated, failed / did not meet, complete response letter, clinical hold, going concern, delisting,
restructuring / wind-down, strategic alternatives, CEO exit). If our thesis, efficacy text and call reason do not mention
the same thing, the inputs may predate the news: the name is flagged and kept out of the Top-20 book until reviewed
(Record › Book › Ranking audit lists them). Reuses the 8-K caches from thesis_watch / explain_moves."""
import json, re, pathlib, datetime as dt, sys
sys.argv = [sys.argv[0]]
root = pathlib.Path(__file__).resolve().parents[1]
import importlib.util
spec = importlib.util.spec_from_file_location("tw_helpers", root / "scripts/postmortem.py")
src = (root / "scripts/postmortem.py").read_text()
helpers = src[:src.find("snaps = sorted(")]          # get(), series(), filings(), headline() without running the grading
ns = {"__file__": str(root / "scripts/postmortem.py")}; exec(compile(helpers, "pm_helpers", "exec"), ns)
D = [r for r in json.load(open(root / "data/data.json")) if r.get("ta") != "Acquired / Inactive"]
TH = json.load(open(root / "data/theses.json"))["theses"]
PAT = [("discontinu", r"discontinu"), ("terminat", r"terminat"), ("fail", r"did not meet|not meet (?:its|the) primary|failed to"), ("complete response", r"complete response|\bCRL\b"),
       ("clinical hold", r"clinical hold"), ("going concern", r"going concern"), ("delist", r"delist"), ("restructur", r"restructur|wind[- ]down|reduction in force|workforce"),
       ("strategic alternatives", r"strategic alternatives|strategic review"), ("CEO", r"chief executive officer.{0,40}(?:resign|depart|step)")]
cut = (dt.date.today() - dt.timedelta(days=60)).isoformat(); out = {}
for n, r in enumerate(D):
    t = r["ticker"]; th = TH.get(t, {})
    known = " ".join(str(x) for x in [th.get("th_view"), th.get("th_miss"), th.get("th_cat"), r.get("call_reason"), r.get("eff_short"), r.get("catalyst"), r.get("drug"), r.get("eff_caveat"), r.get("val_note"), r.get("indication")]).lower()
    for f in ns["filings"](t):
        if f["date"] < cut: continue
        h = ns["headline"](f) or ""
        for stem, rx in PAT:
            if re.search(rx, h, re.I):
                if stem.lower() in known or re.search(rx, known, re.I): continue
                out.setdefault(t, []).append({"date": f["date"], "what": stem, "headline": re.sub(r"^(?:exhibit\s?99\.?\d*|ex-?99\.?\d*|exhibit\d+)\s*", "", h, flags=re.I)[:200]})
                break
json.dump({"built": dt.date.today().isoformat(), "since": cut, "flags": out}, open(root / "data/stale-flags.json", "w"), separators=(",", ":"))
print(len(out), "names with news our inputs may not reflect:")
for t, L in out.items(): print("  ", t, "|", "; ".join(f"{x['date']} {x['what']}: {x['headline'][:90]}" for x in L[:2]))
