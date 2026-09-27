# The Unofficial Guide

Omarfahdi Abed, corpus: `city_guides`

---

# Unit 1

## What This Does

This is a retrieval system over `city_guides`: fourteen travel guides covering
nine towns in one invented region, plus five guides that cut across all of them
(eating, walking, regional transport, seasons, and getting around with limited
mobility). You ask it a plain question and it answers from those documents
only, naming the file the answer came from. It is built for the specific
questions a visitor would actually ask: what time the Kestrelford bakery sells
out, by when the Halden Bay car parks fill on a summer weekend, which town is
easiest to get around with limited mobility, where to eat in Brightwater
instead of the riverside strip. Ask it something the guides don't cover and a
relevance gate stops the question before the model ever sees it, and it says it
doesn't have enough information instead of inventing an answer.

## Chunking Strategy

**Chunk size:** 900 characters as a ceiling, not a target. The average chunk
comes out at 330 (shortest 206, longest 943)
**Overlap:** 150 characters, carried across only when a section exceeds the
ceiling

These numbers come out of what the documents look like rather than the other
way round. Every guide in this corpus is 1,400 to 2,500 characters and arrives
already divided into labelled sections (`## Getting there`, `## Getting
around`, `## Eat and drink`, `## What to see`, `## When to go`) that run
roughly 200 to 690 characters each. The answer to a real question sits inside
one of those sections: "by what time do the car parks fill" is one sentence in
Halden Bay's "Getting there", and nothing in "What to see" helps with it.

So the chunk is the section, not a character count. `split_documents` in
`chunker.py` splits on the `##` headings, and the size settings only handle the
two edge cases: a section over 900 characters gets split further at sentence
boundaries with 150 characters carried into the next piece, and a section under
200 characters gets merged into its neighbour instead of standing alone.

Two things I noticed in my own documents drove this:

1. **The starter's 800-character windows left a 24-character chunk.** Indexing
   `city_guides` with `fallback_split` reported *51 chunks, 650 characters on
   average (shortest 24, longest 800)*. That 24-character chunk is the tail of
   a document that didn't divide evenly into 800s. It is a fragment that can
   only ever be noise in a result list, and it is where the 200-character floor
   in criterion 4 came from.

2. **Nine of my fourteen guides have a section called "Eat and drink."** A
   chunk containing only the body of that section is indistinguishable from
   eight others once it's a vector, since "one pub, food served lunchtimes" could be
   any of nine towns. So every chunk now starts with its own header line,
   `Kestrelford — Eat and drink`, and the town name is part of what gets
   embedded and part of what the model is shown.

**Where I changed my mind:** I set the overlap to 150 characters before
checking whether it would ever be used, out of habit from the fixed-window
version. It never fires on this corpus, because the longest section body here is 691
characters, so nothing reaches the 900 ceiling and `_split_long` returns its
input untouched every time. I left the number and the code in, because the
1,200-character upper bound in criterion 4 has to hold for any document and a
guide with one long unbroken section would otherwise break it, but on
`city_guides` specifically my overlap is doing nothing at all. That seemed
worth writing down rather than quietly implying the number mattered.

Result, before and after:

| | Chunks | Average | Shortest | Longest | Function |
|---|---|---|---|---|---|
| Starter | 51 | 650 | 24 | 800 | `chunker.py::fallback_split` |
| Mine | 91 | 330 | 206 | 943 | `chunker.py::split_documents` |

## Sample Chunks

Printed with `python app.py chunks -n 5`.

**Chunk 1** | source: `guide_accessibility.md#0` | produced by: `chunker.py::split_documents`

```
Getting around the region with limited mobility — Overview

An honest assessment rather than a promotional one. Some of these places are
difficult and it is better to know in advance.

Getting around the region with limited mobility — Straightforward

**Thornby Wells** is the easiest town in the region. It is flat, compact, and
everything is within three minutes of everything else. Parking is free for two
hours anywhere in town and the station is central. The pump room and gardens
are level throughout.

**Marchwood** has a modern tram network with level boarding on all four lines,
running every 8 minutes on weekdays. The city museum and covered market are both
step-free. The distances between districts are the main consideration.

**Brightwater** is level along the river and through the centre. The mill museum
is step-free. The station is a 15-minute walk from campus on flat ground, or the
shuttle meets the four busiest arrivals.
```

This one is a merge: the two-sentence opening of the document was under my
200-character floor, so it got glued onto the section that follows it rather
than being indexed as a fragment on its own.

**Chunk 2** | source: `guide_corry_vale.md#6` | produced by: `chunker.py::split_documents`

```
Corry Vale — When to go

May to September. Outside those months the pub in the third village closes, the farm shop reduces its hours, and several footpaths become genuinely boggy rather than merely wet. The road is not gritted above the second village and is impassable in snow.
```

**Chunk 3** | source: `guide_givens_mill.md#3` | produced by: `chunker.py::split_documents`

```
Givens Mill — Eat and drink

A tearoom attached to the mill, open 10 to 4 daily except Tuesdays, which sells bread made from the flour ground twenty metres away and is the reason most people come. One pub, food served lunchtimes and Thursday to Saturday evenings.
```

**Chunk 4** | source: `guide_kestrelford.md#6` | produced by: `chunker.py::split_documents`

```
Kestrelford — When to go

Late spring and early autumn. The Saturday market runs year-round but is much reduced from November to February. August is busy with walkers. The single-track approach road is genuinely difficult in snow and the town can be cut off for a day or two most winters.
```

**Chunk 5** | source: `guide_regional_transport.md#0` | produced by: `chunker.py::split_documents`

```
Getting around the region — The railway

The line runs along the river valley, connecting Brightwater to the regional
hub in 50 minutes. Eleven services a day on weekdays, six on Sundays. The line
north of Brightwater closed in 1963 and everything beyond it is bus or car.

Tickets are cheaper booked the day before than on the day, and considerably
cheaper than that booked a week ahead. There is no ticket office at
Brightwater station outside weekday mornings; the machine on the platform takes
cards only.
```

Chunks 2, 3 and 4 are each one whole section and answer a question on their
own: when to visit Corry Vale, when the Givens Mill tearoom is open, whether
Kestrelford is reachable in winter. Chunk 5 is a section that happens to hold
two related facts, services and tickets, and both are about the same railway,
so it still reads as one thought.

## Sample Answer

**Question:** Where in the region can I still get a meal on a Sunday evening?

This is the one my criterion 1 said would be hardest. It is the only test
question that doesn't name a town, and the answer is one sentence that exists
in exactly one file. Complete output of `python app.py ask "..."`:

```
$ python app.py ask "Where in the region can I still get a meal on a Sunday evening?"
  (best distance 0.436, cutoff 0.65)

According to `guide_eating.md`, Sunday evening meals can be found in Marchwood and Thornby Wells.

Sources retrieved: guide_corry_vale.md, guide_eating.md, guide_kestrelford.md

1 model calls this session, 690 tokens (667 in, 23 out)
```

The one file the answer names, `guide_eating.md`, is in the retrieved list, and
that is criterion 5 holding on this question. And the same command on a
question the guides don't cover stops before the model runs at all:

```
$ python app.py ask "is the housing lottery random?"
  (best distance 0.800, cutoff 0.65)

I don't have enough information about that.

0 model calls this session
```

Zero model calls on that one. The gate refused it, so nothing was ever sent.

**My relevance cutoff:** `THRESHOLD = 0.65` in `config.py`

I ran all five of my test questions and all five of the `OUT_OF_SCOPE`
questions through `python app.py retrieve "..."` and wrote down the best
distance for each. The two groups don't overlap and they aren't close:

| Question | In corpus? | Best distance |
|---|---|---|
| Where should I eat in Brightwater instead of the riverside strip? | Yes | 0.232 |
| By what time do the Halden Bay car parks fill up on a summer weekend? | Yes | 0.285 |
| What time does the bakery in Kestrelford sell out? | Yes | 0.341 |
| Where in the region can I still get a meal on a Sunday evening? | Yes | 0.436 |
| Which town in the region is the easiest to get around with limited mobility? | Yes | 0.502 |
| What is the capital of Mongolia? | No | 0.810 |
| What is the recommended dosage of ibuprofen for a headache? | No | 0.835 |
| How do I write a for loop in Rust? | No | 0.861 |
| How do I change the oil in a diesel engine? | No | 0.881 |
| Who won the 1994 World Cup? | No | 0.969 |

In-corpus runs 0.232 to 0.502. Out-of-corpus runs 0.810 to 0.969. That leaves
an empty band 0.308 wide, and 0.65 sits near the middle of it: 0.15 of headroom
above my worst real question and 0.16 below the nearest out-of-corpus one. At
0.65 the gate lets through 5 of 5 real questions and refuses 5 of 5 fake ones.

The gap is this clean because of what the corpus is: fourteen guides about one
invented region, with no medicine, no sport, no cars and no code anywhere in
them. The question I expected to be tight was the ibuprofen one, since
`guide_accessibility.md` talks about hospitals and minor injuries units, and it
did land closest of the five at 0.835, but that is still 0.19 clear of the
cutoff.

I left `TOP_K` at 5. The answer was the top result for four of my five
questions and the top two for the fifth, so fewer would put the accessibility
question at risk, and more would only pull in near-identical "Eat and drink"
sections from other towns.

## How I Used AI

I used Claude as a coding assistant, for scaffolding, for the git commits and for debugging, but I read every line before it went in, wrote a lot of the chunker myself, and kept the design decisions with me.

**1.** I asked it what the starter's 800-character windows were doing to documents shaped like mine. It gave me the baseline (51 chunks, shortest 24 characters) plus something I had missed: nine of my fourteen guides have a section headed "Eat and drink", so that section's text on its own never says which town it is about. That is why every chunk now carries its town and heading on the first line.

**2.** I gave it my three rules (split on `##`, merge under 200, cap at 1,200) and had it draft `split_documents`. The code was fine, but its comment claimed three sections were long enough to need splitting. I checked, and the real number is zero: the longest section here is 691 characters, so my 150-character overlap never fires at all, which is worth knowing before I start tuning numbers in unit 2.

<!-- No stretch features attempted this unit. -->

---

# Unit 2

<!-- These sections get ADDED to what's already above. Don't delete or rewrite
     unit 1 — the point is that someone can see what you said before you knew
     how it went. -->

## Run Log — Before

From `results/run_2026-09-27_1900_before.md`, produced by `python run_eval.py --label before` (cache off, 15 model calls). There's no scorer.py, so I judged each answer by reading it against the `expects` value in `questions.py` and the source text.

| Criterion | Target | Run 1 | Run 2 | Run 3 | Verdict |
|---|---|---|---|---|---|
| 1. Retrieved chunk contains the answer | 4 of 5 | 5/5 | 5/5 | 5/5 | MET |
| 2. Every answer names a source | 5 of 5 | 5/5 | 5/5 | 5/5 | MET |
| 3. Gate stops out-of-corpus questions | 4 of 5 | 5/5 | 5/5 | 5/5 | MET |
| 4. Chunks 200–1,200 chars and carry their heading | all chunks | 91/91 | 91/91 | 91/91 | MET |
| 5. Answers only cite retrieved sources | 5 of 5 | 5/5 | 5/5 | 5/5 | MET |

Criteria 1, 3 and 4 can't vary between runs. Retrieval is deterministic (every question had the same best distance on all three runs), the gate is a comparison against a fixed number, and chunking happens once at index time. So one number goes in all three columns. Criteria 2 and 5 depend on the generated text, which changed wording between runs but never changed the result.

### Criterion 1: real output

`python app.py retrieve "Where in the region can I still get a meal on a Sunday evening?"` (`app.py`, retrieve command):

```
#   distance   source                           preview
1   0.4355     guide_eating.md                  Eating across the region — Opening hours  This catch...
2   0.4634     guide_eating.md                  Eating across the region — Local specifics  Halden B...
3   0.4812     guide_kestrelford.md             Kestrelford — Eat and drink  Four pubs, two cafés, a...
4   0.4927     guide_corry_vale.md              Corry Vale — Eat and drink  One pub in the largest v...
5   0.5186     guide_eating.md                  Eating across the region — Practical  Cash is still ...
```

The top chunk holds the answer sentence from `guide_eating.md`: "Sunday evening is the hardest meal to find anywhere except Marchwood and Thornby Wells."

### Criteria 2 and 5: real output (run 1, `run_eval.py`)

| Question | Sources retrieved | Answer |
|---|---|---|
| Kestrelford bakery | guide_eating.md, guide_kestrelford.md | The bakery in Kestrelford sells out by 11am (according to guide_kestrelford.md and guide_eating.md). |
| Halden Bay parking | guide_halden_bay.md, guide_regional_transport.md, guide_seasons.md | On summer weekends, the Halden Bay car parks fill up by 10am, as stated in *guide_halden_bay.md* and *guide_regional_transport.md* (and additionally mentioned in *guide_seasons.md*). |
| Limited mobility | guide_accessibility.md, guide_corry_vale.md, guide_walking.md | According to **guide_accessibility.md**, Thornby Wells is the easiest town in the region to get around with limited mobility because it is flat, compact, and everything is within three minutes of everything else. |
| Brightwater eating | guide_brightwater.md, guide_eating.md, guide_regional_transport.md | You should eat on Corry Lane, which is located two streets back (or inland) from the riverside strip (*guide_brightwater.md* and *guide_eating.md*). |
| Sunday evening | guide_corry_vale.md, guide_eating.md, guide_kestrelford.md | You can still find a meal on a Sunday evening in Marchwood and Thornby Wells, according to guide_eating.md. |

### Criterion 3: real output (`run_eval.py::check_out_of_scope`, cutoff 0.65)

| Out-of-scope question | Best distance | Gate |
|---|---|---|
| What is the capital of Mongolia? | 0.810 | refused |
| How do I change the oil in a diesel engine? | 0.881 | refused |
| Who won the 1994 World Cup? | 0.969 | refused |
| What is the recommended dosage of ibuprofen for a headache? | 0.835 | refused |
| How do I write a for loop in Rust? | 0.861 | refused |

### Criterion 4: real output (`tools/check_chunks.py`, chunks from `chunker.py::split_documents`)

```
city_guides__default: 91 chunks, min 206, max 943
  outside 200-1200: 0 []
  first line missing 'Guide — Section': 0 []
```

## Verdicts

| # | Criterion | Verdict | How I decided |
|---|---|---|---|
| 1 | Retrieved chunk contains the answer (4 of 5) | MET | 5/5 on every run. The Sunday question, which I flagged as risky because it names no town, still ranked the right chunk (Opening hours in `guide_eating.md`) first at 0.436. The other four answers sit in chunks I read directly. |
| 2 | Every answer names a source (5 of 5) | MET | All 15 answers named at least one file. Not close. |
| 3 | Gate stops out-of-corpus questions (4 of 5) | MET | 5 of 5 refused. Closest was Mongolia at 0.810, 0.16 above the cutoff. Ibuprofen, which I expected to be the risky one, came in at 0.835. |
| 4 | Chunks 200 to 1,200 chars with heading (all) | MET | All 91 chunks are 206 to 943 characters and start with guide and section. I revised how this is measured (see criteria.md) because the command I named only showed 40 of 91 chunks and no lengths. The target didn't change. |
| 5 | Answers only cite retrieved sources (5 of 5) | MET | I checked every filename in all 15 answers against that question's Sources list. No stray citations. Closest call: Halden Bay run 2 cited `guide_seasons.md` for a slightly different fact ("arriving before 10am in August"). It was retrieved so it passes, but it's the model blending near-duplicate sources, which is what this criterion was written to catch. |

One note on judging by hand: my `expects` for the Sunday question was "Marchwood", but the source says "Marchwood and Thornby Wells". All 15 answers gave both, so they're correct, but a keyword scorer using my `expects` value would also pass an answer that dropped Thornby Wells.

## Diagnoses

No criterion missed, so there's nothing to diagnose in the strict sense. The honest reading is that my targets were safe:

- **Criteria 2 and 5** were close to guaranteed. I said as much in criteria.md: the filename is on every excerpt and the prompt tells the model to use it. They guard against a regression; they don't test anything hard.
- **Criterion 1** hedged at 4 of 5 for the Sunday question, which then ranked first on every run. It should have been 5 of 5.
- **Criterion 3** is the weak one. Mongolia, diesel engines, the World Cup, ibuprofen and Rust share no vocabulary with a travel guide, so the closest landed at 0.810. They tested whether the gate can tell travel from programming, not whether it can tell an answerable travel question from an unanswerable one.

### Probing what criterion 3 didn't test

So I asked five questions that sound like my corpus but that it doesn't answer. Best distances from `python app.py retrieve "..."`:

| Near-domain question (not answered by the corpus) | Best distance | Gate |
|---|---|---|
| Is there a cinema in Kestrelford? | 0.366 | passed |
| What is the best vegan restaurant in Halden Bay? | 0.407 | passed |
| How much is a taxi from Brightwater station to Elder Ness? | 0.408 | passed |
| How much does a hotel room in Marchwood cost per night? | 0.490 | passed |
| What time does the bakery in Pellew Sands sell out? | 0.499 | passed |

**Stage: retrieval (the relevance gate in `gate.py`).** Cosine distance measures whether a question shares topic and vocabulary with a chunk (a town name, "bakery", "restaurant"), not whether the chunk contains an answer. These five land between 0.366 and 0.499, inside my real questions' range of 0.232 to 0.502. "Is there a cinema in Kestrelford?" is closer than my real Sunday question (0.436), and the Pellew Sands question is closer than my real accessibility question (0.502). No cutoff separates them: anything below 0.499 starts refusing real questions. The gate can't fix this, so for these questions the grounding prompt is the only guard.

To see how well it guards, `tools/probe.py` asked each question three times with the cache off (`results/probe_2026-09-27_1920_before.md`). The Marchwood question is partly answerable (the guide says hotels are "cheap" outside conference weeks but gives no price), so it's scored on whether it invents a price. The other four should be plain refusals.

- Clean refusals: run 1 2/4, run 2 2/4, run 3 2/4
- Marchwood with no invented price: 3/3

The same two leaked every run. Real output from `python app.py ask` (`generate.py::answer_from_chunks`):

```
=== What time does the bakery in Pellew Sands sell out?
I do not have enough information to answer what time the bakery in Pellew Sands sells out, as the provided documents only mention that Kestrelford's bakery sells out by 11am (guide_eating.md).

=== Is there a cinema in Kestrelford?
I do not have enough information to answer whether there is a cinema in Kestrelford (guide_kestrelford.md).
```

**Stage: generation (`GROUNDING_INSTRUCTION` in `generate.py`).** The refusal rule is loose ("say you don't have enough information") and sits right next to "Name the document your answer came from". The model treats a refusal as an answer that still needs a source. On Pellew Sands it refuses, then offers the Kestrelford bakery time from `guide_eating.md` with a citation, which is exactly the "detail carried from one town to another" my last prompt rule was written to stop. On the cinema question it cites `guide_kestrelford.md` for a refusal, as if the file said there's no cinema. Nothing was invented, but both leaks are the same pattern: the citation rule firing on a refusal.

**Criterion I'd tighten:** criterion 3 should include near-domain questions like these five, scored on the full system's response (gate or model), not just the gate.

## The Improvement

**What I changed:** one rule in `GROUNDING_INSTRUCTION` in `generate.py` (commit "refusals are one fixed sentence in the grounding prompt"). The old rule said "If the documents don't cover the question, say you don't have enough information." The new version:

```
- If the documents don't answer the question at all, reply with exactly this sentence and nothing else: I don't have enough information about that. A refusal names no file and adds no facts about other places.
- If the documents answer only part of the question, give that part, name the file, and say what the documents don't cover.
- When you do answer, name the document your answer came from, using the filename given in each excerpt.
```

Nothing else changed: same corpus, chunking, index, top-k, cutoff and model.

**Why I picked it:** my diagnosis found two stages involved. The gate can't be fixed with a cutoff, because near-domain questions overlap my real questions' distances. So the fix had to go where the leak actually happened, which was generation: the citation rule firing on refusals. The partial-answer line is there so the Marchwood question keeps answering what the guide does say instead of being forced into a flat refusal.

### Run Log — After

From `results/run_2026-09-27_1924_after.md`, `python run_eval.py --label after`, cache off, 15 model calls.

| Criterion | Target | Run 1 | Run 2 | Run 3 | Verdict |
|---|---|---|---|---|---|
| 1. Retrieved chunk contains the answer | 4 of 5 | 5/5 | 5/5 | 5/5 | MET |
| 2. Every answer names a source | 5 of 5 | 5/5 | 5/5 | 5/5 | MET |
| 3. Gate stops out-of-corpus questions | 4 of 5 | 5/5 | 5/5 | 5/5 | MET |
| 4. Chunks 200–1,200 chars and carry their heading | all chunks | 91/91 | 91/91 | 91/91 | MET |
| 5. Answers only cite retrieved sources | 5 of 5 | 5/5 | 5/5 | 5/5 | MET |

Criteria 1, 3 and 4 can't have moved, since the change only touches generation and the distances came out identical. Criteria 2 and 5 are the ones that could have regressed, and didn't. Real output, run 1 of the after file:

```
Kestrelford bakery: The bakery in Kestrelford sells out by 11am, according to `guide_kestrelford.md` and `guide_eating.md`.
Halden Bay parking: On summer weekends, the Halden Bay car parks fill up by 10am, according to both `guide_halden_bay.md` and `guide_regional_transport.md` (and also mentioned in `guide_seasons.md`).
Limited mobility: According to guide_accessibility.md, Thornby Wells is the easiest town in the region to get around with limited mobility because it is flat, compact, and everything is within three minutes of everything else.
Brightwater eating: You should eat on Corry Lane, which is located two streets back from the riverside strip. Sources: `guide_brightwater.md` and `guide_eating.md`
Sunday evening: According to guide_eating.md, Sunday evening is hardest to find anywhere except Marchwood and Thornby Wells.
```

### Near-domain probe, before and after

From `tools/probe.py`, 3 runs each, cache off.

| Measure | Before | After |
|---|---|---|
| Clean refusals (of 4 unanswerable) | 2/4, 2/4, 2/4 | 4/4, 4/4, 4/4 |
| Marchwood partial answer, no invented price | 3/3 | 3/3 |
| Output tokens for the 15 probe calls | 428 | 254 |

Real output after the change (`results/probe_2026-09-27_1927_after.md`, run 1):

```
=== What time does the bakery in Pellew Sands sell out?
I don't have enough information about that.

=== Is there a cinema in Kestrelford?
I don't have enough information about that.

=== How much does a hotel room in Marchwood cost per night?
According to guide_marchwood.md, hotel prices in Marchwood are cheap outside of conference weeks, but conference weeks in March and October double the prices. The documents do not state the exact monetary cost per night.
```

**Did it help?** Yes, on the thing it targeted, and without breaking anything. Clean refusals went from 2 of 4 to 4 of 4 on every run, and the two that leaked before (Pellew Sands and the cinema) now give only the refusal line. Marchwood got slightly better too: it still reports what the guide says, and now it also says the exact price isn't in the documents. The five original criteria held at 5/5 on every run, so the stricter prompt didn't start refusing real questions, which was the risk I was watching for on the Sunday and accessibility questions. A side effect I like: the model's refusal is now the same sentence the gate uses, so the user sees one consistent message whichever layer refused.

I can't claim the five criteria improved, because they were already all met. The evidence that the change helped comes from the probe, which isn't one of my five criteria. That's a gap in the criteria, covered below.

## What's Still Broken

Nothing is missed against my five criteria, before or after. What's still broken is what they didn't measure:

- **The gate still lets near-domain questions through.** All five probe questions pass at 0.366 to 0.499, and every one costs a model call and relies on the model obeying the prompt. A cutoff can't fix this. What I'd try next is a second signal alongside distance, like a keyword check: "cinema" appears nowhere in the corpus, and BM25 would score it at zero even though the embedding calls it close. I stopped here because that's a second change, and this unit allows one.
- **The probe is small and I wrote it.** Five questions, one corpus, and a string-match check for "clean". I also read every answer myself, but five questions I picked aren't strong evidence the fix generalizes.
- **No scorer.py, and one `expects` value is incomplete.** Every verdict here was judged by hand. The Sunday `expects` is "Marchwood" when the source says "Marchwood and Thornby Wells", so a scorer built on it would pass a half-right answer.
- **Citation formatting is inconsistent.** Filenames show up plain, in backticks, bold or italic depending on the run. It doesn't affect any criterion, so I left it.

## What I'd Do Differently

- **Criterion 3** is the one I'd rewrite. Keep the five far-away questions, add five near-domain ones like my probe, and score what the whole system returns (gate refusal or a clean model refusal), with a target of at least 4 of 5 on each set. As written, it only tested whether the gate can tell travel from programming.
- **Criterion 1** should have been 5 of 5. I hedged for the Sunday question and it ranked first every time.
- **Criteria 2 and 5** were close to guaranteed by the pipeline. I'd keep one as a regression check and spend the other slot on refusal quality, which is where the real failure turned up.
- I'd fix the Sunday `expects` to require both towns before building a scorer on it.

## How I Used AI (Unit 2)

I used Claude to get the project running on my Mac, to write the two measurement scripts (`tools/check_chunks.py` and `tools/probe.py`), and to handle the README edits and commits. The idea of probing with near-domain questions came from Claude after I pointed out that my out-of-scope questions were never close to the cutoff.

The judgment calls I checked myself. Claude initially flagged the Marchwood answer's "cheap" as possibly invented; I grepped `guide_marchwood.md`, found "cheap" is in the source, and didn't count it as a leak. I also checked the Sunday answer's "Thornby Wells" against `guide_eating.md` before marking it correct, and read the after answers to confirm the stricter prompt hadn't started refusing real questions before calling the change a success.
