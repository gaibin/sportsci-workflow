# Article structures

What sections to include, in what order, at what depth, for each genre. The structure differs by genre. Do not apply IMRaD to a narrative review.

---

## 1. Empirical journal article (IMRaD)

Standard for *MSSE*, *JSS*, *IJSPP*, *Eur J Appl Physiol*, *中国体育科技*, etc.

### Title
- ≤ 15 words preferred. State the population, intervention/exposure, and outcome where possible.
- Avoid "A study of…", "Investigation into…", "Effects of X on Y in Z" is the standard form.

### Abstract (200–300 words, often structured)
Sections (with subheadings if structured): Background / Purpose / Methods / Results / Conclusion. Numerical results required, not just direction.

- Methods: design, n, intervention/exposure, primary outcome.
- Results: at least one effect estimate with 95% CI or P-value for the primary outcome.
- Conclusion: one sentence that states what the data support, with no implications beyond the data.
- The opening sentences state the problem and the gap, not a textbook definition or the history of the field. A reader who stops after the first Results sentence should know what was tested and what was found.

### Keywords
3–6 terms. Use MeSH terms where possible. Avoid words already in the title.

### Introduction (3–5 paragraphs typical)

A useful internal structure (do **not** signpost it with "首先/其次"):

1. Why the topic matters (1 paragraph): broad context, real-world relevance.
2. What is known (1–2 paragraphs): the relevant literature, summarized critically.
3. What is **not** known: the gap. Be specific. "Few studies have examined…" needs a citation showing the gap is real.
4. Purpose / hypothesis (1 short paragraph): explicit aim, explicit hypothesis (directional if justified).

Reach the gap quickly. By the end of the first paragraph the reader should know which problem the study addresses. Do not narrate how the project developed (`ai-traces-zh.md` §6.4, `ai-traces-en.md` §5.4).

### Methods

Past tense. Subsections (use the journal's preferred subheadings):
- **Participants**: n, sex, age (mean ± SD), inclusion/exclusion criteria, recruitment, ethical approval (committee + reference number), informed consent statement.
- **Study design**: between/within/mixed, randomization (if used) and method, blinding (if used).
- **Procedures / Intervention**: enough detail to replicate. Equipment with manufacturer and model in parentheses on first mention.
- **Measurements**: for each variable: instrument, protocol, units, reliability if known.
- **Statistical analysis**: software with version, tests used, alpha, handling of missing data, sensitivity analyses, sample size justification.

### Results

Past tense. **No interpretation.** Order: descriptives → primary outcome → secondary outcomes → exploratory/post-hoc.

- For each test, report: descriptives, test statistic, df, P, effect size with 95% CI.
- Refer to figures/tables: "VO2max increased by 12% (Figure 2A)."
- Do not repeat in text what is already in a table.

### Discussion

Common 4-paragraph structure (again, do not signpost):

1. **Restate main finding in plain language** (no numbers in this paragraph; numbers are in Results).
2. **Comparison with prior literature**: agreements and disagreements, with citations.
3. **Mechanisms / interpretation**: why might this be the case.
4. **Strengths, limitations, future directions**: be honest. A weak limitations paragraph is a reviewer red flag.

### Conclusion (sometimes its own section, sometimes the last paragraph of Discussion)

- Two to four sentences.
- States what the study found and the most defensible practical implication.
- No new claims, no new citations.
- No new self-criticism. Limitations belong in the limitations paragraph (in a Chinese thesis, 研究局限与展望). The conclusion answers the research question and ends on the most defensible implication.

### Acknowledgments, Funding, Conflicts of interest, Data availability
Per journal template.

### References
APA 7 or Vancouver per journal. See `citations.md`.

---

## 2. Narrative review

Less structured than IMRaD. Common shape:

1. **Introduction**: scope, why this review now, what questions it addresses. Often no "Methods" section, but if you systematically searched, briefly state how (databases, dates, key terms) for credibility.
2. **Body**: organized by **theme** or by **chronology**, not by paper. Each section synthesizes multiple studies, not summarizes one paper at a time.
3. **Synthesis / integrated discussion**: what the literature collectively says, where consensus and conflict lie.
4. **Future directions**: specific gaps and how to address them.
5. **Conclusion**: short.

Common failure mode: "annotated bibliography" syndrome (paragraph-per-paper). A review's value is in synthesis. If a paragraph discusses only one study, merge or cut.

---

## 3. Systematic review / meta-analysis (PRISMA 2020)

Strict structure required. Reference: Page et al. (2021) *BMJ* 372:n71.

### Sections
1. **Title**: must contain "systematic review" and/or "meta-analysis".
2. **Abstract**: structured per PRISMA-A.
3. **Introduction**: rationale, objectives stated as PICO(S).
4. **Methods**:
   - Eligibility criteria (PICOS: Population, Intervention, Comparator, Outcomes, Study designs)
   - Information sources (databases + dates of last search)
   - Search strategy (full strategy in supplement)
   - Selection process (number of reviewers, conflict resolution)
   - Data extraction (variables, reviewers, conflict resolution)
   - Risk of bias assessment (tool: ROB 2 for RCTs, ROBINS-I for non-randomized, NOS, etc.)
   - Effect measures
   - Synthesis methods (pooling model: random/fixed effects, heterogeneity assessment)
   - Certainty assessment (GRADE)
5. **Results**:
   - PRISMA flow diagram (mandatory)
   - Study characteristics table
   - Risk of bias summary
   - Synthesis: forest plots, heterogeneity statistics ($I^2$, τ², Q with df and P)
   - Subgroup / sensitivity analyses
   - Publication bias (funnel plot if k ≥ 10)
6. **Discussion**: summary of evidence, limitations of the evidence, limitations of the review process, implications.
7. **Other**: registration (PROSPERO ID), funding, data availability.

---

## 4. Theses (BS / MS / PhD)

Far more detailed than journal articles. Same logical structure but each section much longer.

### Chinese theses (typical 国内高校结构)
1. 摘要（中文 + 英文 Abstract）
2. 关键词（中英对照）
3. 目录
4. 第一章 绪论 / 引言
   - 1.1 选题背景与意义
   - 1.2 国内外研究现状
   - 1.3 研究目的与研究问题
   - 1.4 研究意义与创新点
5. 第二章 文献综述（硕博必备；本科可与第一章合并）
6. 第三章 研究方法
   - 3.1 研究对象
   - 3.2 研究设计
   - 3.3 测试 / 实验方法
   - 3.4 数据处理与统计分析
7. 第四章 研究结果
8. 第五章 分析与讨论（中国学位论文常把 Results 与 Discussion 分开两章）
9. 第六章 结论与建议
   - 6.1 结论
   - 6.2 建议
   - 6.3 研究局限与展望
10. 参考文献（GB/T 7714-2015）
11. 附录（量表、知情同意书、原始数据等）
12. 致谢
13. 个人简历 / 攻读学位期间发表论文

### English theses (UK/US/AU style)

1. Title page
2. Abstract (single page)
3. Acknowledgments
4. Table of contents, list of figures, list of tables
5. List of abbreviations
6. **Chapter 1: Introduction**: broad context, gap, aims, thesis structure overview.
7. **Chapter 2: Literature Review**: comprehensive, critical, synthesizes prior work.
8. **Chapter 3: General Methods** (PhD; some structures): methods common across all studies.
9. **Chapters 4–N: Empirical studies**: each a self-contained mini-IMRaD, common in PhD theses by publication.
10. **Chapter N+1: General Discussion**: integrates findings across studies, addresses overall thesis aims.
11. **Chapter N+2: Conclusions**: main findings, contributions to knowledge, practical implications, limitations, future research.
12. References
13. Appendices

### Notes for thesis writing
- Methods sections are 2–3× longer than in a journal article. Include pilot work, equipment validation, full protocols.
- Discussion can include speculation that would be cut from a journal paper, **but** must be flagged as such.
- Limitations section must be genuinely critical, not formulaic.
- Avoid the "thesis tense" trap: literature review past tense ("Smith found"), present tense for established knowledge ("HIIT improves VO2max"), past for own work ("we measured").

---

## 5. Conference abstract (~250–300 words, structured)

- **Background**: 2 sentences: context + gap.
- **Purpose**: 1 sentence.
- **Methods**: n, design, primary outcome, key analysis. 3–4 sentences.
- **Results**: primary outcome with effect size and CI/P. 3–4 sentences.
- **Conclusion**: 1–2 sentences. No "future research is needed."

No references, no figures (unless the conference allows it, and most don't). Often capped at 250 or 300 words, so cut ruthlessly.

---

## 6. Section-specific verb tense quick reference

| Section | Tense |
|---|---|
| Abstract: Methods/Results | Past |
| Introduction: established knowledge | Present |
| Introduction: prior specific findings | Past ("Smith reported…") |
| Methods | Past |
| Results | Past |
| Discussion: own findings | Past ("we found that…") |
| Discussion: established mechanisms | Present |
| Discussion: implications | Present / future |
| Conclusion | Present |

Reviewers genuinely enforce this rule. Mismatched tense is one of the easiest things to flag.
