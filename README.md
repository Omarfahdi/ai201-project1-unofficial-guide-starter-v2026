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

| Criterion | Target | Run 1 | Run 2 | Run 3 | Verdict |
|---|---|---|---|---|---|
| 1. Retrieved chunk contains the answer | 4 of 5 |  |  |  |  |
| 2. Every answer names a source | 5 of 5 |  |  |  |  |
| 3. Gate stops out-of-corpus questions | 4 of 5 |  |  |  |  |
| 4. Chunks 200–1,200 chars and carry their heading | all chunks | | | | |
| 5. Answers only cite retrieved sources | 5 of 5 | | | | |

## Verdicts

| # | Criterion | Verdict | How I decided |
|---|---|---|---|
| 1 |  |  |  |
| 2 |  |  |  |
| 3 |  |  |  |
| 4 |  |  |  |
| 5 |  |  |  |

## Diagnoses

## The Improvement

**What I changed:**

**Why I picked it:**

### Run Log — After

| Criterion | Target | Run 1 | Run 2 | Run 3 | Verdict |
|---|---|---|---|---|---|
| 1. Retrieved chunk contains the answer | 4 of 5 |  |  |  |  |
| 2. Every answer names a source | 5 of 5 |  |  |  |  |
| 3. Gate stops out-of-corpus questions | 4 of 5 |  |  |  |  |
| 4. Chunks 200–1,200 chars and carry their heading | all chunks | | | | |
| 5. Answers only cite retrieved sources | 5 of 5 | | | | |

**Did it help?**

## What's Still Broken

## What I'd Do Differently
