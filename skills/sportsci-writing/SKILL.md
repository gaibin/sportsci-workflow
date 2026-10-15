---
name: sportsci-writing
description: Use this skill whenever the user is writing, polishing, translating, restructuring, statistically reporting, or visualizing sport science manuscripts and theses in Chinese or English. It applies to SCI/SSCI journal papers, undergraduate/master's/PhD theses, narrative reviews, systematic reviews, meta-analyses, conference abstracts, exercise physiology, sport psychology, biomechanics, sports medicine, exercise biochemistry, training science, rehabilitation, and physical activity/public health. Also use it when the user asks for data analysis for sport science writing, including t-tests, ANOVA, correlations, effect sizes, reliability statistics, Results paragraphs, Nature-style figures, or removal of AI-sounding prose such as dashes, semicolons in running prose, 「不是…而是…」 and "not X but Y" contrast frames, parenthetical asides, "首先/其次", "delve/leverage/crucial", mechanical transitions, and chat/editorial residue (second person, "课题组", 待补/TODO, meta-discourse) that makes a manuscript read like an AI conversation.
---

# Sport Science Writing & Polishing

A toolkit for producing genuinely human, journal-grade sport science writing in Chinese and English, with built-in statistics and Nature-style figure generation.

## Operating principles

Read these before doing anything else. They override any default writing instinct you may have.

### 1. Never fabricate

You may rephrase, restructure, translate, and tighten. You may **not**:
- invent numerical results, sample sizes, p-values, or effect sizes
- invent citations, DOIs, author names, or publication years
- infer a result that the data do not directly support
- change the direction of a finding to make it sound stronger

If a number, citation, or claim is missing, ask the user. Do not paper over the gap with plausible-sounding text.

### 2. The author's zero-tolerance list

The author of this skill reads three patterns as obvious AI traces and does not want them anywhere in running prose, in Chinese or in English. Published papers use them freely. This skill does not.

| 禁用 | 中文 | English | 改法 |
|---|---|---|---|
| 破折号 dashes | `——` `—` | `—`, spaced `–`, `--`, spaced ` - ` | 逗号、冒号，或拆成两句 |
| 分号 semicolons | `；` | `;` | 用句号切分 |
| 对照句 contrast frames | 不是……而是…… / 不只是（不仅是）……而是…… / 不是……，是…… / 并非……而是…… / 不再是……而是…… / 与其说……不如说…… / 不在于……而在于…… | not X but Y / It is not X, but Y, that … / not because X but because Y / not merely X but Y | 直接陈述 B。State Y directly. |

What stays allowed:

- **Semicolons inside brackets.** Grouped statistics such as `（t=2.10，P<0.05；t=2.45，P<0.05；t=2.3，P<0.05）` and citation lists such as `(refs 12; 15)` are standard. Even these should not pile up: more than one such bracket in a paragraph reads as generated.
- **Dashes in ranges and compounds.** `60–80%`, `weeks 1–4`, `muscle–bone unit` use an en-dash as a range or link mark.
- **Result statements with "but".** "The difference was not statistically significant but showed a trend (P = 0.06)" reports two findings. It is not a contrast frame.

Enumerated items get no exception. Write `1）…。2）…。` with full stops.

The same rules apply to your own replies and summaries to this user. `scripts/ai_trace_check.py` reports all three as hits marked "author rule".

### 3. Strip AI traces aggressively

The single most common failure mode of AI-written sport science is that it reads like AI. Reviewers and supervisors now spot it instantly. Before returning any polished text, mentally diff it against the AI-trace lists in `references/ai-traces-zh.md` and `references/ai-traces-en.md`, and study the concrete rewrite pairs in `references/before-after.md`. Those examples carry more information than any rule.

Removing traces is only half the job. Text with every AI word deleted can still read as generated, because it lacks what human authors add: specific anchors, evidence-calibrated hedging, field terms, and visible author judgment. For any English output (drafting, polishing, or zh→en translation), also read `references/human-voice-en.md` and rebuild paragraphs from their content instead of swapping words.

**Do not optimize for AI-detector evasion.**

Do not promise to bypass GPTZero, Turnitin, 知网 AIGC, PaperPass, or any other detector. If the user asks to "lower AI detection score", "pass AI detection", or similar, redirect the task to legitimate revision: make the prose more specific, evidence-grounded, field-appropriate, and author-like. Use `references/anti-detector.md` only as a cautionary note about why mechanical detector gaming hurts readability. Do not apply detector-evasion recipes as an objective.

Besides the zero-tolerance list, watch for:

- parenthetical asides "（...）" / "(...)" used to qualify claims → fold the qualifier into the sentence or drop it
- mechanical enumeration: 首先/其次/再者/最后, First/Second/Third/Finally → use natural prose flow
- "AI tell" vocabulary: delve, navigate, tapestry, landscape, realm, leverage, underscore, crucial, pivotal, robust, comprehensive, intricate, nuanced. 深入探讨, 全面分析, 至关重要, 具有重要意义, 值得注意的是, 综上所述
- stacked transitions: Moreover/Furthermore/Additionally back-to-back. 此外/另外/同时 连续出现
- name-and-restate paragraph shape (topic sentence → body → restate topic sentence)
- Chinese "的的不休" (3+ "的" within one clause) and "性/化/度" noun-stacking
- 对仗成癖: "不仅……而且……" / "既……又……" twice in one paragraph
- **对话残留与编辑痕迹**, the class that makes a manuscript read like a chat log. 第二人称（你/您/咱们）、指示读者（下面我们/请看/需要注意的是）、口语（其实/说白了/搞定/差不多）、第一人称叙事（我认为/本研究团队/笔者/本人）、角色词（课题组/我们组）、内部讨论话术（"或经导师复核后调整" / "待与导师商定"）、占位符（待补/TODO/XXX/上一版）、孤立的标点段。完整清单与改写见 `references/ai-traces-zh.md` 第七节。

Read the full reference lists for the replacement patterns. The goal is prose that a careful human author in this field would actually write, with nothing that is merely grammatical and feels generated.

### 4. Match the genre

Sport science writing has several registers. Decide first which genre you are in, then read the corresponding section of `references/article-structures.md`:

- SCI/SSCI empirical paper (IMRaD)
- Narrative review
- Systematic review / meta-analysis (PRISMA)
- Undergraduate / Master's / PhD thesis (Chinese or English)
- Conference abstract (structured, ~250 words)

Tone, hedge level, paragraph length, and section depth differ. A thesis Methods section is far more verbose than a journal Methods section. A narrative review has no separate Introduction section.

### 5. Match the field

Sport science spans physiology, biochemistry, biomechanics, motor control, sport psychology, training science, public health, and rehabilitation. Conventions differ:

- Physiology / biochemistry: VO2max, lactate, HR, hormones. Report mean ± SD, percent change, effect size (Cohen's d or Hedges' g)
- Psychology: scale scores, reliability (Cronbach's α), report 95% CI, prefer mixed-effects models for repeated measures
- Biomechanics: kinematic/kinetic variables, often n is small, report individual data alongside group means
- Training studies: pre/post designs, report ICC for reliability. Magnitude-based inference is now discouraged, so use standard NHST + ES
- Epidemiology / public health: OR, RR, HR (hazard ratio), adjust for confounders, report 95% CI

If the user does not specify the field, infer it from the variables they mention and confirm before drafting.

## Workflow

### When the user gives you raw text to polish

1. Read the text. Identify: language (zh / en / mixed), genre, field, target journal style if mentioned.
2. If the user asks for logic, rigor, argumentation, consistency, evidence alignment, or overclaiming checks, read `references/logic-check.md`. Audit the reasoning before polishing the prose.
3. Run a mental pass against the zero-tolerance list and the AI-trace checklist. If the text is heavily AI-generated, plan a deeper rewrite instead of word substitution. For English, follow the content-outward procedure in `references/human-voice-en.md` §0. If the source lacks the specifics a paragraph needs (sample, protocol, instrument, effect size), ask the user for them in a separate list instead of writing around the gap.
4. Polish in place. Preserve every verified number, citation, and factual claim verbatim. Do not preserve wording that overstates what the evidence supports.
5. If the text is in a file or can be saved to a temporary file, run `python scripts/ai_trace_check.py <file>` or `py scripts/ai_trace_check.py <file>` from the skill directory to catch missed formulaic patterns. Fix every HIT. Read each warn in context: it marks a pattern that is fine once but formulaic when repeated. The script only sees surface patterns. The specificity and hedging checks in `references/human-voice-en.md` still have to be done by reading. If Python is unavailable, perform the same checklist manually and keep writing.
6. Return the polished text. If you made structural changes (merged paragraphs, reordered sentences), say so in one line at the end. Do not produce a long change-log unless asked.

### When the user asks for a logic or rigor review

1. Read `references/logic-check.md`.
2. Identify the manuscript section, study design, research question, primary outcomes, and available evidence.
3. Check the chain from rationale and objective through methods, results, interpretation, and conclusion.
4. Report major, moderate, and minor logic issues before rewriting. Distinguish confirmed errors from likely problems and missing information.
5. Rewrite only after the audit unless the user explicitly asks for a direct rewrite.
6. After the reasoning is sound, apply the relevant language, genre, field, and AI-trace guidance.

### When the user gives you data to analyze and write up

1. Inspect the data file (Excel / CSV). Confirm with the user: what is the design (between-subjects, within-subjects, mixed)? What are the dependent variables? What comparison do they want?
2. Run `python scripts/stats.py` or `py scripts/stats.py` with the appropriate test when the required packages are installed. The script outputs descriptives, the test result, effect size, and a Results-section paragraph in the requested language.
3. Review the auto-generated paragraph. Tighten it, strip any AI traces, adjust hedging to match the field's convention.
4. If a figure is needed, use `scripts/nature_plot.py` (see "Figures" below).

### When the user asks for a figure

1. Confirm: which variables, which comparison, what figure type (bar with error bars, box+jitter, scatter+regression, line with shaded CI, forest plot for meta-analysis).
2. Use `python scripts/nature_plot.py` or `py scripts/nature_plot.py` from the skill directory when the required packages are installed. It loads `assets/matplotlibrc` automatically, which enforces Nature-style defaults: Helvetica/Arial, 7-8pt, no gridlines, outward ticks, left+bottom spines only, colorblind-safe palette, 300 DPI.
3. Always show individual data points overlaid on summary statistics for n ≤ 30 (box+jitter or violin+strip). Sport science samples are usually small enough that individual variability matters.
4. Mark significance with explicit p-values where space allows. Use `*` `**` `***` only when there are many comparisons. Always state in the caption what the asterisks mean and what the error bars represent (SD, SEM, or 95% CI). Vague error bars are a reviewer red flag.
5. Export to both PDF (vector, for submission) and PNG at 300 DPI (for preview). See `references/nature-figures.md` for the full spec.

### When the user asks for a translation (zh ↔ en)

Translate by rewriting in the target language's natural scientific register. Word-for-word mapping produces both translationese and AI tone. After translating:
- pass the output through the zero-tolerance list and the target-language AI-trace checklist. For zh→en, also run the positive check in `references/human-voice-en.md` §10
- check that hedging strength is preserved. Chinese tends to under-hedge and English tends to over-hedge, so calibrate
- check that citation format matches the target genre: 国标 for Chinese, APA7/Vancouver for English (see `references/citations.md`)

## Citation formats

- **English journals (most sport science)**: APA 7 (author-date) or Vancouver (numbered). Default to APA 7 unless the target journal is medical (then Vancouver). Full rules and examples in `references/citations.md`.
- **Chinese journals and theses**: GB/T 7714-2015. Format is strict. See `references/citations.md`.

Do not invent DOIs or fill in missing fields. If the user's reference is incomplete, flag it and ask.

## Statistics

The most common tests in sport science and how to report them are in `references/sport-stats.md`. The `scripts/stats.py` helper covers:

- descriptives (mean, SD, median, IQR, 95% CI)
- independent and paired t-tests with Cohen's d / Hedges' g
- one-way and repeated-measures ANOVA with η²p
- Pearson and Spearman correlation
- reliability (ICC, Cronbach's α)
- normality checks (Shapiro-Wilk) and non-parametric alternatives

For mixed-effects models, meta-analysis, or other advanced methods, use Python (`statsmodels`, `pingouin`) or R directly and write the script ad hoc. Still report results following the conventions in `references/sport-stats.md`.

## Files in this skill

```
SKILL.md                       this file
references/
  ai-traces-zh.md              Chinese AI-trace patterns + rewrites
  ai-traces-en.md              English AI-trace patterns + rewrites
  human-voice-en.md            what human English sport science prose contains (read for any English output)
  before-after.md              real AI→human rewrite pairs (read for in-context examples)
  anti-detector.md             cautionary response guidance for detector-focused requests
  voice-samples/               optional, local only (not distributed): real journal paragraphs by subfield, read for register and vocabulary
  nature-figures.md            full Nature-style figure spec
  citations.md                 APA7 / Vancouver / GB/T 7714
  article-structures.md        IMRaD, thesis, review section templates
  logic-check.md               research logic, evidence boundaries, and internal consistency audit
  sport-stats.md               common tests + how to report them
scripts/
  stats.py                     descriptive + inferential statistics
  nature_plot.py               Nature-style plotting helpers
  ai_trace_check.py            scan text for AI traces (hits must be fixed, warnings need judgment)
tests/
  test_ai_trace_check.py       regression tests. Run after changing any rule
assets/
  matplotlibrc                 Nature-style matplotlib defaults
```

`README.md`, `LICENSE`, and `requirements.txt` are repository packaging files, not runtime instructions. Read reference files only when the current task needs them. Do not preload everything.

Quoted journal paragraphs in a local `voice-samples/` folder (if you keep one) and in `before-after.md` are real published text and may contain dashes or semicolons. Learn their vocabulary and argument structure. Their punctuation does not override principle 2.

## Related skills in this repository

| Need | Use |
|---|---|
| choosing a topic, design and sample size | `sportsci-topic` |
| analysing data from a design spec, figures, three-line tables, Results document | `sportsci-figures` (`scripts/stats.py` and `scripts/nature_plot.py` here are light helpers for ad-hoc checks inside a writing task) |
| references, DOI checks, Zotero citation fields in Word | `sportsci-refs` |

## Final reminder

The bar is: a careful human reviewer in sport science cannot tell this text was AI-assisted. If the polished output still contains any of the following, you have not finished the job. Re-read and fix before returning:

- 破折号 / dashes of any kind used as asides
- 正文分号 / semicolons outside brackets
- 对照句：「不是……而是……」及其变体，"not X but Y" 及其变体
- parentheses holding anything other than 缩写/单位/统计量/引文
- "首先/其次/再者/最后/综上所述", "delve into", "值得注意的是"
- 同段内两次「不仅……而且……」/「既……又……」
- 任何对话残留：第二人称、指示读者、口语、第一人称叙事、"课题组/我们组"、内部讨论话术、待补/TODO/XXX、孤立标点段
- 段尾换种说法重复段首
- English: trailing `, highlighting / suggesting …` clauses, sentence-initial `Notably / Importantly / Overall`, "plays a key role", "offers valuable insights", "further research is warranted"
- English: any sentence that would fit unchanged into another paper (the any-paper test in `references/human-voice-en.md` §1)
