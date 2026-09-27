"""Near-domain questions the corpus does NOT answer. Measurement only, no system change."""
import argparse, datetime as dt, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config, gate
from store import search
from generate import answer_from_chunks, usage

UNANSWERABLE = [
    "What time does the bakery in Pellew Sands sell out?",
    "Is there a cinema in Kestrelford?",
    "What is the best vegan restaurant in Halden Bay?",
    "How much is a taxi from Brightwater station to Elder Ness?",
]
PARTIAL = "How much does a hotel room in Marchwood cost per night?"  # corpus says "cheap", gives no price

def clean_refusal(a):
    a = a.lower().replace("do not", "don't")
    return a.startswith("i don't have enough information") and ".md" not in a

p = argparse.ArgumentParser()
p.add_argument("--runs", type=int, default=3)
p.add_argument("--label", default="before")
args = p.parse_args()

out = [f"# Near-domain probe ({args.label})", "",
       f"{dt.datetime.now():%Y-%m-%d %H:%M}, {args.runs} runs, cache off, produced by tools/probe.py", ""]
clean_counts, partial_ok = [], []
for run in range(1, args.runs + 1):
    clean = 0
    for q in UNANSWERABLE + [PARTIAL]:
        res = search(q, top_k=config.TOP_K, corpus=getattr(config, "CORPUS", None), variant="default")
        d = gate.check(res, threshold=config.THRESHOLD)
        ans = answer_from_chunks(q, res, cache=False) if d.passed else gate.REFUSAL
        if q in UNANSWERABLE:
            ok = clean_refusal(ans); clean += ok
            tag = "CLEAN" if ok else "LEAKY"
        else:
            ok = not any(c in ans for c in "£$0123456789"); partial_ok.append(ok)
            tag = "NO INVENTED PRICE" if ok else "INVENTED PRICE"
        out += [f"### run {run}: {q}", f"- {tag}", "", "```", ans, "```", ""]
        print(f"run {run} [{tag}] {q}")
    clean_counts.append(clean)

summary = [f"Clean refusals (of 4): " + ", ".join(f"run {i+1}: {c}/4" for i, c in enumerate(clean_counts)),
           f"Marchwood partial answer with no invented price: {sum(partial_ok)}/{len(partial_ok)} runs"]
out[4:4] = summary + [""]
path = Path("results") / f"probe_{dt.datetime.now():%Y-%m-%d_%H%M}_{args.label}.md"
path.write_text("\n".join(out), encoding="utf-8")
print("\n".join(summary)); print("Wrote", path); print(usage())
