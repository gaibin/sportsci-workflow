# English AI traces in sport science writing

This is a hard checklist, not a style suggestion. If polished output contains any of these patterns, the job is not done: rewrite.

Each entry gives **AI version → human version**. Imitate the human version.

This file only tells you what to remove. Clean text can still read as generated. After this checklist, run the positive check in `references/human-voice-en.md`.

## 1. Punctuation overuse

### 1.1 Em-dashes as parenthetical inserts

The single most reliable AI tell in English. Sport science journals rarely use em-dashes this way. They belong to magazine writing.

- ❌ High-intensity interval training — a method that has gained increasing attention in recent years — significantly improves VO2max.
- ✅ High-intensity interval training, which has gained attention in recent years, significantly improves VO2max.
- ✅ High-intensity interval training significantly improves VO2max. This method has gained attention in recent years.

**Rule (author's zero-tolerance list, SKILL.md principle 2):** polished output contains no dashes used as asides. That covers the em-dash `—`, a spaced en-dash ` – `, a double hyphen `--`, and a spaced hyphen ` - `. The only allowed dash is the unspaced en-dash in ranges and compounds: `60–80%`, `weeks 1–4`, `muscle–bone unit`.

### 1.2 Parentheses as qualifying asides

AI loves to drop hedges and clarifications into parentheses. In a journal article, parentheses should hold: abbreviation expansions, units, statistical values, citations. If a parenthetical contains a qualification or commentary, fold it into the sentence or drop it.

- ❌ Participants (all male university students) completed three trials (each separated by 48 h).
- ✅ Thirty male university students completed three trials separated by 48 h.

Acceptable parentheses:
- maximal oxygen uptake (VO2max): abbreviation
- heart rate (beats·min⁻¹): units
- (P < 0.05): statistic
- (Smith et al., 2021): citation

### 1.3 Serial comma chains of nouns

- ❌ We measured heart rate, blood pressure, lactate, cortisol, testosterone, creatine kinase, leukocyte count, and IgA.
- ✅ We measured cardiovascular variables (heart rate, blood pressure), metabolic and endocrine markers (lactate, cortisol, testosterone, creatine kinase), and immune markers (leukocyte count, IgA).

Group long lists into categories.

## 2. Mechanical enumeration

`First, … Second, … Third, … Finally, …` at the start of consecutive sentences or paragraphs is the second-most-reliable AI tell. It is allowed once per Discussion if the structure genuinely calls for it, and never as a section-by-section template.

- ❌ First, participants completed baseline testing. Second, they underwent 8 weeks of training. Third, all variables were re-tested. Finally, statistical analyses were performed.
- ✅ After baseline testing, participants completed 8 weeks of training. All variables were then re-measured and analyzed.

## 3. AI vocabulary

These words appear far more often in AI output than in published sport science.

**Rewrite the sentence. Do not swap the word.** A one-for-one substitution leaves the generated sentence structure in place and creates a new fingerprint. "Underscores the importance of" → "highlights the importance of" is still an AI sentence. Ask what the sentence actually claims, then say that with the study's specifics (see `references/human-voice-en.md` §1).

**Density matters more than presence** (sample #15 in `before-after.md`). One precise "crucial" in a paper is fine. Within about 200 words: one emphasis word (crucial, critical, key, essential, pivotal, vital) is fine, two is a warning, three or more means rewrite.

**Technical collocations are exempt.** These are standard terms, not AI tells: robust standard errors, robust regression, robust variance estimator, comprehensive metabolic panel, landscape orientation (figures).

| AI favorite | Replace with |
|---|---|
| delve into | examine, investigate, study |
| navigate (used metaphorically) | address, manage, work through |
| tapestry | (delete the metaphor entirely) |
| landscape (used metaphorically) | field, area, literature |
| realm | field, area |
| leverage (as a verb) | use, draw on, apply |
| underscore | show, support, or state the specific finding |
| crucial / pivotal | important, central, or say why it matters |
| comprehensive | full, complete, multicomponent, or just delete |
| robust | strong, consistent (and only when supported by data). See exemptions above |
| intricate / nuanced | complex, detailed, or specify what is complex |
| myriad / plethora | many, numerous, several |
| in the realm of / in the landscape of | in [field name] |
| shed light on | show, clarify, demonstrate |
| paradigm shift | change, departure (rarely justified, usually delete) |
| game-changer | (delete; not academic) |
| holistic | whole-body, integrated, multi-component |

### 3.1 Newer-generation tells

Current models rarely write "delve" or "tapestry" any more. These phrases have taken their place, and the table above does not catch them.

| Pattern | What to do instead |
|---|---|
| highlights / underscores the importance of X | State the finding that shows X matters, with numbers |
| underscores / highlights the need for | Name the specific study, measure, or practice that is needed |
| plays a key / crucial / pivotal / vital role in | Say what X does: predicts, mediates, limits, accounts for n% of |
| a growing body of evidence suggests | Cite the studies and say what they found |
| has gained increasing attention in recent years | Delete, or say who uses it and since when |
| offers / provides valuable insights into | Say what was learned |
| paves the way for / opens new avenues for | Name the next study or application |
| represents a significant step forward | Delete |
| holds promise / a promising avenue / promising tool | State the evidence and its limits |
| further research is warranted / needed | Name the design, population, and question (`human-voice-en.md` §1) |
| remains unclear / poorly understood (no specific gap) | State exactly which comparison or population is missing |
| the interplay between X and Y | the relationship between X and Y, or name the mechanism |
| multifaceted | Name the facets, or delete |
| elucidate | show, clarify, identify |
| foster / bolster / harness | Use the precise verb: increase, support, use. "Foster" is acceptable once when it really means gradual development (#18) |
| serves as / stands as | is |
| ensure / ensuring (repeated in Methods) | Say what was done ("Sessions were supervised"). One "to ensure" per section is fine |
| a nuanced / deeper understanding of | Say what is now understood |
| valuable, meaningful, novel (as praise) | Delete, or give the evidence |

### 3.2 Template sentences to delete

- ❌ It is worth noting that the present study sheds light on the intricate relationship between X and Y.
- ✅ The present study clarifies the relationship between X and Y.

- ❌ This study underscores the crucial importance of comprehensive training programs.
- ✅ Multicomponent training programs improved [specific outcome] in this sample.

- ❌ In conclusion, our findings provide a new perspective on this important topic.
- ✅ Our findings show [specific result], which suggests [specific implication].

## 4. Sentence- and paragraph-level patterns

### 4.1 Tricolons (rule of three)

AI almost reflexively groups things in threes, with parallel structure.

- ❌ The intervention improved performance, enhanced recovery, and promoted adaptation.
- ✅ The intervention improved performance and shortened recovery time. Adaptation markers also rose.

Three is fine occasionally. Three in every paragraph is a giveaway.

### 4.2 "Not only X, but also Y"

Overused. Replace with two sentences or a simple "and".

- ❌ HIIT not only improved VO2max but also reduced resting heart rate.
- ✅ HIIT improved VO2max and reduced resting heart rate.

### 4.3 Stacked transitions

`Moreover. Furthermore. Additionally. In addition.` Never use two of these in the same paragraph.

- ❌ Moreover, the training improved strength. Furthermore, it enhanced power. Additionally, it reduced injury risk.
- ✅ The training improved strength and power, and was associated with fewer injuries.

### 4.4 Topic-sentence-and-restatement paragraph shape

AI paragraphs often begin with a thesis statement and end by restating it in different words. Strip the closing restatement; let paragraphs end on the last piece of new information.

### 4.5 Excessive hedging

Sport science hedges with statistics. Stacked modal verbs add nothing.

- ❌ These results may potentially suggest that there could possibly be an association between X and Y.
- ✅ These results suggest an association between X and Y (r = 0.42, P = 0.03).

One hedge per claim, max.

### 4.6 Trailing -ing clauses

The most frequent sentence-level pattern in current AI output: a result followed by a comma and a participle that attaches an interpretation without committing to it.

- ❌ Sprint time decreased by 3.1%, highlighting the effectiveness of the program.
- ❌ Adherence was 92%, suggesting that the protocol was feasible.
- ✅ Sprint time decreased by 3.1%. This exceeds the smallest worthwhile change for this squad (1.8%).
- ✅ Adherence was 92%, and no session was stopped early for discomfort.

Split the interpretation into its own sentence with a subject and a calibrated verb, or replace it with the evidence that supports it. Always rewrite the value-inflating ones: highlighting, underscoring, emphasizing, reinforcing, demonstrating. The inferential ones (suggesting, indicating, reflecting, implying) do appear in published human prose. One per paragraph is fine if the hedge matches the evidence. A paragraph built on them reads as generated.

### 4.7 Sentence-initial signposting adverbs

`Notably, / Importantly, / Interestingly, / Crucially, / Remarkably, / Overall, / Taken together,` tell the reader how to feel about the next sentence instead of giving a reason. Delete them. If the sentence then seems unimportant, the problem is the sentence.

- ❌ Notably, the effect was larger in women.
- ✅ The effect was larger in women (d = 0.71 vs 0.32), who also started with lower baseline strength.

"Taken together" or "Overall" may open the one summarizing sentence of a Discussion. Not every paragraph.

### 4.8 Bare "This" as subject

- ❌ This suggests that recovery matters.
- ✅ This delay in CK clearance suggests that 48 h was not enough recovery after eccentric work.

Give the demonstrative a noun so the reference is explicit.

### 4.9 Contrast frames: "not X but Y" in any form

On the author's zero-tolerance list (SKILL.md principle 2). Every form counts:

- ❌ The benefit of RT is not merely aesthetic but fundamentally metabolic.
- ❌ The benefit of RT is not aesthetic but metabolic.
- ❌ It is not the volume, but the intensity, that drives adaptation.
- ❌ Injuries occurred not because of weekly volume but because of single-session spikes.
- ✅ RT also improves insulin sensitivity (refs).
- ✅ Intensity drove adaptation more than volume did (d = 0.82 vs 0.31).
- ✅ Most injuries followed single-session spikes in distance.

State Y directly, with its evidence. If a cited study really argued X, name it and report what it found, as a separate sentence.

Not a contrast frame: a result statement with "but", such as "The difference was not statistically significant but showed a trend (P = 0.06)." Sentence-initial "Rather than X, Y" is often a disguised frame, and the checker warns on it.

### 4.10 Semicolons in running prose

Also on the zero-tolerance list. Split into two sentences.

- ❌ Sprint time improved; jump height did not change.
- ✅ Sprint time improved. Jump height did not change.
- ✅ Sprint time improved, whereas jump height did not change.

Semicolons inside brackets stay: grouped statistics `(t = 2.10, P = 0.04; t = 2.45, P = 0.02)` and citation lists `(refs 12; 15)`.

## 5. Stance / tone

### 5.1 Self-aggrandizing claims

- ❌ This is the first study to comprehensively investigate…
- ✅ This study extends prior work [refs] by examining [specific addition].

"First to," "comprehensive," "groundbreaking," "novel paradigm": delete unless you can cite the prior literature gap explicitly. Reviewers flag these immediately.

### 5.2 Section-closing summaries that just restate

- ❌ In summary, this section has discussed the methods used in the present study.
- ✅ (delete the sentence. The section is over.)

### 5.3 Self-undermining (defensive writing)

The author lists the weaknesses before the reviewer has said anything.

- ❌ Unfortunately, the intervention produced only a modest improvement, and we must acknowledge serious limitations.
- ✅ After 12 weeks, grip strength increased by 2.1 kg more in the intervention group than in controls (95% CI 0.4 to 3.8).

Tells: `unfortunately`, `regrettably`, `admittedly`, `we must acknowledge / admit`, `serious limitations`, `only` in front of an effect. Let the effect size and its interval carry the judgement.

**Boundary: the tone stops defending, the content keeps everything.** Pre-specified primary outcomes are reported whatever they show and are never swapped for a better-looking one. A null result is written as "did not differ" with P and the CI. Limitations stay in the limitations paragraph, each with its consequence for the conclusion (`logic-check.md` §6). Only the self-deprecating frame goes.

### 5.4 Project-diary structure

- ❌ We first surveyed current practice, then reviewed the literature to design the programme, and finally ran an 8-week intervention.
- ✅ Lower-limb power is low in university students [refs], and standard PE classes do little to change it. This trial tested whether 8 weeks of functional training improves jump height without adding class time.

Keep only the logic that stands at the end: why the problem matters, what is missing, what this study did, what the evidence shows. How the project developed belongs in the lab notebook.

## 6. Field-specific notes

- **Methods:** past tense, passive voice acceptable but not required. Modern style favors active voice ("We measured…") in many journals. Check the target journal.
- **Results:** past tense, no interpretation. State what was found, not what it means.
- **Discussion:** present tense for established knowledge ("HIIT improves VO2max"), past tense for the present study's findings ("HIIT improved VO2max in our sample").
- Avoid "significant" without "statistically significant" or a P-value. Avoid "trending toward significance". Say `P = 0.06` and let the reader judge.

## 7. Final self-check (run after polishing)

1. Any dash used as an aside (`—`, ` – `, `--`, ` - `)? → rewrite. Any semicolon outside brackets? → split.
2. Parentheses contain qualifications rather than abbreviations/units/citations/stats? → fold or drop.
3. Consecutive sentences starting `First, / Second, / Third, / Finally,`? → restructure.
4. Any words from the tables in §3 or §3.1 appear? → rewrite the sentence, do not swap the word.
5. Three or more emphasis words (crucial, critical, key, essential, pivotal, vital) within ~200 words? → rewrite.
6. Any "not X but Y" frame in any form? → state Y directly. Any "not only … but also" or tricolons in consecutive sentences? → break up.
7. Two `Moreover/Furthermore/Additionally` in the same paragraph? → cut one.
8. A result followed by `, highlighting / suggesting / underscoring …`? → split or replace with evidence.
9. Sentences opening with `Notably / Importantly / Interestingly / Overall`? → delete the adverb.
10. Bare "This suggests / This indicates"? → give "This" a noun.
11. Paragraph ends by restating its first sentence? → delete the ending.
12. "First to," "comprehensive," "novel," "groundbreaking" without citation support? → delete.
13. Stacked hedging (`may potentially suggest there could be`)? → simplify.
14. Self-undermining (`unfortunately`, `we must acknowledge`, `serious limitations`)? → drop the judgement, keep the number. Primary outcomes, null results and limitations stay. (§5.3)
15. Organised as a project diary (`first we… then we… finally we…`)? → problem, gap, approach, evidence. (§5.4)

If any check still fires, rewrite. Then run the positive check in `references/human-voice-en.md` §10.
