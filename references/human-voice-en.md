# Human voice in English sport science writing

`ai-traces-en.md` lists what to remove. This file lists what careful human authors put in. Removing traces without adding these features produces prose that is clean but flat, and flat prose still reads as generated.

Read this file whenever you draft, polish, or translate into English. The numbered samples cited below (#47, #59, …) are in `references/before-after.md`.

Numbers in the examples are illustrative. Never carry them into a user's manuscript.

## 0. Rewrite from the content outward

Word-swapping cannot fix a generated paragraph. Rebuild it:

1. **Name the paragraph's job in one line**: report a result, compare with prior work, justify a method choice, explain a mechanism, or state a limitation. One job per paragraph.
2. **List the concrete facts available** in the user's material: design, participants, protocol, instruments, time points, numbers, cited studies.
3. **Write sentences that carry those facts.** Each sentence should add information the previous one did not.
4. **Only then** check connectors, vocabulary, and punctuation against `ai-traces-en.md`.

If step 2 yields nothing concrete, the paragraph cannot be made human by style alone. Return the draft together with a short list of questions for the user (sample size? which scale? which comparison?). Do not invent the missing details.

## 1. The any-paper test

For every sentence, ask: could this be pasted unchanged into another paper in the field? If yes, delete it or make it specific to this study.

- ❌ Physical activity plays a key role in adolescent health.
- ❌ These findings offer valuable insights for coaches and practitioners.
- ❌ Further research is warranted to clarify these relationships.
- ✅ Coaches working with U17 players could use the 30% threshold as a simple flag for sessions that need a lighter follow-up day.
- ✅ A crossover trial with a fixed fluid intake would show whether the difference in core temperature came from hydration status rather than the cooling vest.

The last example is the fix for "further research is warranted": name the design, the population or condition, and the question it would answer.

The test applies most strongly to first and last sentences of paragraphs, where generated text puts its generic framing.

## 2. Anchor claims in specifics

Specificity is the most reliable sign that an author knows the material. Check each claim against five anchors:

| Anchor | Generic | Specific |
|---|---|---|
| Who | athletes | 24 male academy soccer players (age 17.2 ± 0.8 y) |
| What | a training program | 6 weeks of twice-weekly Nordic hamstring exercise |
| How measured | muscle strength | isometric knee-flexor torque at 90° on an isokinetic dynamometer |
| When | after the intervention | 48 h after the final session |
| How much | improved significantly | increased by 11% (95% CI 6% to 16%) |

Related patterns in the sample library:

- Cite prior studies with their size and population, not "previous studies" (#47, #48).
- Give dates, thresholds, and exclusion criteria with their reasons (#56, #58, #60).
- Explain any calculation with a worked example using real-looking numbers from the study (#59).
- Explain a model's blind spot with a concrete scenario rather than an abstract caveat (#53).

## 3. Calibrate hedging to the evidence, claim by claim

Generated text hedges uniformly: every claim gets "may", or none does. Human authors choose the strength of each verb from the strength of the evidence behind it (#17).

Rough ladder, strongest to weakest:

| Evidence behind the claim | Typical wording |
|---|---|
| Consistent meta-analytic or trial evidence | improves, reduces, prevents |
| This study's primary outcome, adequately powered | increased, was associated with (observational) |
| Secondary outcome, single study, or small sample | suggests, indicates |
| Non-significant trend with a visible pattern | appears to slightly increase (#51) |
| Mechanistic speculation | may reflect, one possible explanation is |

Rules:

- One hedge per claim. "May potentially suggest" is three hedges doing one job.
- Use the middle of the scale. "Are likely not generalizable" (#39) and "do not fully encompass" (#40) are more precise than either "may not" or "do not".
- When comparing with the literature, the verb states how close the match is: *confirms* > *corroborates* > *closely aligns with* > *is consistent with* > *partly agrees with* > *contrasts with* (#49). Do not use "is consistent with" for every comparison.
- Keep association language for observational designs. "Was associated with" does not become "led to".
- Report non-significant results in full, with the estimate and CI, and say plainly that they were not statistically significant (#50). Do not smooth irregular numbers (#46).

## 4. Start sentences with the subject and link them by information flow

In generated prose, sentences are glued together by connectors (Moreover, Furthermore, Notably). In human prose, the link is carried by content: each sentence starts with something the reader already knows and ends with the new information, which the next sentence picks up.

- ❌ Sprint times improved after training. Moreover, jump height increased. Notably, these changes were larger in the high-volume group. Overall, this suggests a dose–response relationship.
- ✅ Both groups ran faster over 20 m after training, but the high-volume group improved by roughly twice as much (−0.09 vs −0.04 s). Jump height followed the same pattern. The larger gains with more sessions per week point to a dose–response relationship, although two dose levels cannot show its shape.

Guidance:

- Connectors that carry a real logical relation are fine: *However* (contrast), *Therefore / Thus* (inference), *In contrast*, *For example*, *Because*.
- Additive connectors (*Moreover, Furthermore, Additionally, In addition*) and signposting adverbs (*Notably, Importantly, Interestingly, Crucially*) rarely carry information. If deleting one loses nothing, delete it.
- As a rough ceiling, no more than one sentence in three should open with a connector or adverb.
- Give "This" a noun. "This increase", "This threshold", "This discrepancy" tell the reader what is being referred to. A bare "This suggests…" usually hides a vague reference.

## 5. Use the precise field term, once

Generated text falls back on everyday paraphrases because it does not know the field's vocabulary (#44, #63, #65). Replace the paraphrase with the term, but only when the term is accurate.

| Everyday paraphrase | Field term |
|---|---|
| bone-promoting activities | osteogenic activities |
| how well results apply to real life | ecological validity |
| agreement with another measure | concurrent validity |
| exposure that changes over time | time-varying exposure |
| dependence between repeated measurements | nonindependence of repeated measures |
| how hard the session felt | session RPE, internal load |
| amount of running / distance / speed | external load (specify the metric) |
| tiredness | fatigue (say central or peripheral when known) |
| the smallest change that matters | smallest worthwhile change, minimal clinically important difference |
| athletes getting worse from too much training | nonfunctional overreaching (only if the criteria were met) |

Use each technical term where it belongs and do not decorate it with synonyms around it. If you are unsure whether a term applies, keep the plain wording and ask the user.

## 6. Show the author's judgment

Generated text reports and summarizes. Human authors decide, and the decisions are visible in the text.

- **Prefer one interpretation and say why.** "A more likely explanation is the lower baseline fitness of the control group, which left more room for improvement."
- **Say what you do not claim.** "We do not interpret this as evidence that the supplement improves performance, because the effect disappeared after adjusting for body mass."
- **Concede before advancing.** "Although…, …" and "Despite…, …" let the author acknowledge what was done before stating its limit (#19, #41).
- **Raise the objection before the reviewer does**, and point to where it is addressed (#61).
- **State the consequence of a limitation**, not just its existence. "Because training load was self-reported, heavy weeks were probably under-recorded, which would bias the association toward zero."

Use "we" where the target journal allows it. Active first-person sentences are standard in most current sport science journals and make decisions easier to state.

## 7. Let sentence length follow the argument

Uniform 20–25-word sentences are a strong generated-text signature. Do not fix this by inserting random short sentences. Match length to the job:

- **Longer sentences** carry method detail, conditions, and qualifications that belong together.
- **Short sentences** carry the main result, a key limitation, or a turn in the argument.

- ✅ Participants completed the Yo-Yo Intermittent Recovery Test Level 1 on an indoor surface at the same time of day, at least 72 h after their last match. Two players did not finish.

Two specific habits to break:

- **Trailing -ing clauses.** "…, highlighting the importance of recovery" / "…, suggesting that load matters" attach an interpretation to a result without committing to it. Split them off into a sentence with its own subject and a calibrated verb.
- **Symmetric pairs and triplets in every sentence.** Lists should be as long as the content. Two items, four items, or one item are all normal.

## 8. Paragraph shape

- **Open with the paragraph's specific point.** "Heat acclimation is widely used" is background. "Five days of heat acclimation reduced rectal temperature at the end of the time trial" is a point.
- **End on the last new piece of information.** Do not restate the opening sentence, and do not close each paragraph with "Overall," or "Taken together,". One summarizing sentence per Discussion is plenty.
- **Let paragraph length vary** with the amount of content. A two-sentence paragraph that states a limitation is fine.

## 9. Section-specific notes

**Introduction.** The gap statement must be specific. "The effects of X remain unclear" fails the any-paper test. "No trial has compared X and Y in female adolescent players, who show different load tolerance" passes. Each step of the funnel should cite something.

**Methods.** Write for reproducibility. Every threshold, exclusion criterion, and analytic choice gets a reason and a source (#58, #60). Name the device, software, and version. Define edge cases explicitly (#62).

**Results.** Numbers first, direction clear, no interpretation. Non-significant results are reported with the same completeness as significant ones.

**Discussion.** The first paragraph states the main finding with its size. Comparisons name the studies and their samples. Mechanisms are hedged at the level of evidence behind them. Practical recommendations are quantified and actionable (#52).

**Limitations.** Each limitation names a specific direction of non-generalizability (#43) and its likely consequence for the results.

## 10. Positive check before returning English text

Run this after the `ai-traces-en.md` checklist. A text can pass that checklist and still fail here.

1. Does any sentence pass the any-paper test? Delete it or make it specific.
2. Does every main claim carry at least one anchor (who, what, how measured, when, how much)?
3. Does hedging vary with the evidence, or is it the same everywhere?
4. Do comparisons with prior work use verbs that match how close the agreement is?
5. Are sentences linked by content, with few additive connectors or signposting adverbs?
6. Are field terms used where the paraphrase was vague?
7. Is there at least one visible author decision per Discussion paragraph (preferred interpretation, stated non-claim, limitation consequence)?
8. Does sentence length vary with the job the sentence does?
9. Does each paragraph end on new information?
10. Were missing specifics asked for rather than invented?
