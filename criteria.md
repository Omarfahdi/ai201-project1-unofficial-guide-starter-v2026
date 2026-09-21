# Acceptance criteria — The Unofficial Guide

Five criteria that say what "working" means for this system, written in unit 1
**before** any results existed.

An acceptance criterion names a target: a number, a count, a rate, or something
a person could plainly observe. *"Retrieval works"* is an opinion. *"For at
least 4 of my 5 test questions, the top results include a chunk containing the
answer"* is a criterion.

Under each one, write a sentence or two on **why that target** and not a
stricter or looser one. A reason that says something about your corpus or your
pipeline earns credit; *"80% seemed reasonable"* does not.

> Missing your own targets next unit costs you nothing. Setting a target so
> easy you can't miss it does.

---

## 1. Retrieved chunks contain the answer

For at least 4 of my 5 test questions, the retrieved chunks include one that
contains the answer.

**Why this target:**
Four of my five answers sit inside a single labelled section of a single guide
— the bakery time is in the "Eat and drink" section of `guide_kestrelford.md`,
the parking time is in "Getting there" in `guide_halden_bay.md` — so retrieval
only has to land on the right section. The fifth, where to get a meal on a
Sunday evening, is one sentence in `guide_eating.md` and nowhere else, and it
is the only one of my questions that doesn't name a town for the embedding to
latch onto. Setting this at 5 of 5 would be betting that a question with no
proper noun in it still finds one sentence out of fourteen documents.

---

## 2. Every answer names a source

Every answer the system produces names at least one source document.

**Why this target:**
The filename survives every stage of this pipeline — `ingest.py` stores it on
the `Document`, `chunker.py` copies it onto each `Chunk`, `store.py` returns it
on each `Result`, and `build_prompt` in `generate.py` labels every excerpt
`[from <filename>]` before the model sees it. The model is shown the filename
on every single excerpt, so there is no path to an answer that doesn't have one
available, and a refusal is not an answer. That leaves no honest reason to
allow a miss, so this one is 5 of 5 and not 4.

---

## 3. The relevance gate stops out-of-corpus questions

When I ask a question my documents clearly don't cover, the relevance gate
stops it and the system returns "I don't have enough information about that" —
in at least 4 of 5 tries.

<!-- The five questions are the ones in `OUT_OF_SCOPE` at the bottom of
     `questions.py`, and `run_eval.py` puts them through the gate and writes
     what happened into your run log. -->

**Why this target:**
My corpus is fourteen travel guides about nine towns in one invented region,
and the five `OUT_OF_SCOPE` questions are about Mongolia, diesel engines, the
1994 World Cup, ibuprofen and Rust — none of them shares vocabulary with a
single guide, so I expect the distances to separate cleanly. I left one of five
to spare because the ibuprofen question is the risky one: `guide_accessibility.md`
talks about hospitals and minor injuries units in six of the nine towns, which
is the closest anything in my corpus gets to medicine.

---

## 4. Chunks are section-sized and say which section they are

Every chunk my chunker produces is between 200 and 1,200 characters long, and
the first line of every chunk names the guide it came from and the `##` section
heading it sits under. Checkable in one command: `python app.py chunks -n 40`
prints the chunks, their lengths and their sources.

**Why this target:**
These guides are 1,400 to 2,500 characters each and are already divided into
labelled sections — Getting there, Getting around, Eat and drink, When to go —
that run roughly 200 to 600 characters apiece, so the section is the unit that
holds a whole thought here. The starter's fixed 800-character windows ignored
those headings entirely and left a 24-character tail chunk on this corpus,
which is where the 200 floor comes from; the 1,200 ceiling is high enough to
let me glue a short section onto its neighbour and low enough that a whole
guide can never collapse into one chunk. The heading has to be inside the chunk
text because nine of my fourteen documents have a section called "Eat and
drink" — without its title, a chunk is indistinguishable from eight others.

---

## 5. Answers only cite sources that were actually retrieved

For all 5 of my test questions, every filename that appears in the answer text
also appears in the Sources list that `python app.py ask "..."` prints for that
same question. The system never cites a guide it didn't retrieve.

**Why this target:**
My nine town guides use the same section headings and repeat each other's
facts — the Kestrelford bakery selling out by 11am appears in both
`guide_kestrelford.md` and `guide_eating.md`, and the Halden Bay parking time
appears in three separate files. When five near-identical excerpts go into one
prompt, the plausible failure isn't "no source named", it's the right fact
attached to the wrong filename, and criterion 2 would still pass while that
happened. 5 of 5 rather than 4 because this is a copy-the-label task with the
labels sitting in the prompt, not a retrieval judgement call.

---

<!-- ─────────────────────────────────────────────────────────────────────────
     UNIT 2 — read this before you change anything above.

     If a criterion turns out to be BROKEN rather than merely unmet, you can
     revise it, and that earns credit. But never delete or edit the original
     line. Add the revision underneath it, like this:

         ## 1. Retrieved chunks contain the answer

         For at least 4 of my 5 test questions, the retrieved chunks include
         one that contains the answer.

         **Why this target:** ...

         > **Revised in unit 2:** For at least 4 of 5 questions, the top three
         > results contain the answer.
         >
         > **Why revised:** I couldn't judge "the chunks include one that
         > contains the answer" the same way twice — I scored two questions
         > differently on Monday than on Wednesday. The new version is
         > something I can actually check.

     That's a revision because the criterion couldn't be MEASURED.

     Lowering a target because you missed it is not a revision, and it costs
     you the point:

         ✗ "I said 4 of 5 but got 2 of 5, so 2 of 5 is more realistic."

     A number you missed stays where it is, gets diagnosed, and gets a fix
     attempted. That's where the points are.

     The whole reason the originals stay visible is so someone can see what you
     said before you knew the answer.
     ───────────────────────────────────────────────────────────────────────── -->
