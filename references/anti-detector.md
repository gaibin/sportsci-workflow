# Detector-focused requests: legitimate revision guide

Use this file only when the user explicitly mentions AI-detection scores, AIGC rate, Turnitin AI, GPTZero, PaperPass, 知网 AIGC, "降 AI 痕迹", "降低 AIGC", "过检测", or similar wording.

Do not promise to pass a detector, lower a score, or evade a system. AI detectors are unreliable and can flag normal academic writing. The legitimate goal is to make the text more author-owned, field-specific, evidence-grounded, and less formulaic.

A useful response frame:

> I cannot guarantee or optimize for an AI-detection score. I can revise the text so it is more specific to your study, less formulaic, and more defensible as academic writing.

## What detectors often react to

Treat these as weak warning signs, not rules to game:

| Signal | Common AI-like pattern | Legitimate revision target |
|---|---|---|
| Uniform sentence length | Every sentence has the same rhythm | Vary sentence length only when the argument needs emphasis |
| Predictable vocabulary | Generic verbs and abstract nouns | Use precise field terms tied to the study design |
| Balanced paragraph blocks | Every paragraph has the same template | Let paragraph length follow the logic |
| Empty transitions | First, second, moreover, furthermore | Use causal, contrastive, or result-based links |
| Low source anchoring | Claims float without data/citation | Anchor claims to variables, results, methods, or cited studies |

## Revision principles

### 1. Add study-specific anchors

Generic text is the strongest AI trace. Add details the model would not know unless it had the user's actual material:

- participant group, age range, sport level, intervention duration
- actual variables, instruments, scales, sampling time points
- statistical model, covariates, effect direction, confidence interval
- concrete comparison group or baseline condition
- specific limitation caused by the design or measurement method

Weak:

> Exercise intervention improved physical fitness and psychological health.

Better:

> After the 12-week intervention, the experimental group showed higher cardiorespiratory fitness than the control group, while the change in anxiety scores was smaller and should be interpreted cautiously because baseline symptoms were already low.

### 2. Vary sentence rhythm for emphasis, not randomness

Do not insert short sentences just to create "burstiness". Use short sentences when they carry a real point:

- to state a key limitation
- to mark a contrast
- to end a paragraph with a restrained conclusion
- to separate method detail from interpretation

Mechanical:

> This is important. The finding has meaning. It supports the study.

Natural:

> The finding is useful, but it is not conclusive. The sample was small, and the outcome was measured only once after the intervention.

### 3. Replace generic words with domain-specific words

Do not force rare words. Replace vague verbs only when the replacement is accurate:

| Generic | Better when accurate |
|---|---|
| improve | increase, reduce, attenuate, restore, enhance, preserve |
| affect | predict, mediate, moderate, explain, alter, constrain |
| show | indicate, suggest, reveal, correspond to, differ from |
| important | clinically relevant, practically meaningful, statistically significant, theoretically consistent |
| many factors | training load, recovery status, baseline fitness, sex, age, measurement error |

Chinese equivalents:

| Generic | Better when accurate |
|---|---|
| 提高 | 提升、增加、改善、增强、维持、恢复 |
| 影响 | 预测、调节、中介、解释、改变、限制 |
| 表明 | 提示、反映、说明、支持、与……一致 |
| 重要 | 具有实践意义、具有临床相关性、与理论预期一致 |
| 相关因素 | 训练负荷、恢复状态、基线体能、性别、年龄、测量误差 |

### 4. Break template paragraph shapes

AI-like paragraphs often follow this pattern:

1. broad topic sentence
2. generic explanation
3. "therefore this is important"

For sport science manuscripts, prefer a field logic:

- finding -> comparison with prior work -> mechanism or measurement explanation -> limitation
- method choice -> why it fits the design -> what it cannot answer
- conflicting evidence -> possible reason for inconsistency -> cautious interpretation

Example:

AI-like:

> Physical activity plays an important role in adolescent health. Many studies have shown that exercise can improve physical and mental health. Therefore, school-based exercise interventions are very important.

Better:

> School-based exercise interventions are attractive because they reach students who may not join organized sport. However, their effects are usually modest. In this study, the intervention improved fitness-related outcomes, but the psychological outcomes changed less clearly, which may reflect the short intervention period and the low baseline symptom level.

### 5. Use author-position markers carefully

Author-owned writing does not mean adding personal stories everywhere. In academic writing, author position usually appears through:

- why a design choice was made
- why one interpretation is preferred over another
- why a limitation matters
- why a result should not be overstated

Useful phrases:

- "In this dataset, ..."
- "Given the baseline imbalance, ..."
- "This interpretation is cautious because ..."
- "A more likely explanation is ..."
- "For this reason, we do not claim that ..."

Chinese:

- "在本研究样本中，..."
- "考虑到基线差异，..."
- "这一解释需要谨慎，因为..."
- "更可能的原因是..."
- "因此，本文不宜将该结果解释为..."

### 6. Remove hollow transitions

Replace mechanical transitions with logical relations:

| Mechanical | Better relation |
|---|---|
| Moreover | This extends the finding by... |
| Furthermore | A second explanation is... |
| Additionally | The same pattern appeared in... |
| First/Second/Finally | Use section logic or topic-specific openings |
| 首先/其次/最后 | 直接进入论点，或用"与此相反""这一差异可能来自..." |

### 7. Keep statistics exact

Never change p-values, confidence intervals, sample sizes, or effect sizes to make prose sound more natural. For Results sections:

- preserve statistical symbols and values exactly
- keep direction consistent with the table or output
- state non-significant findings plainly
- do not turn "association" into "effect"
- do not turn "may suggest" into "demonstrates"

## Bad practices

Do not:

- insert random short sentences only to vary rhythm
- replace clear words with obscure words that do not fit the field
- add fake personal voice or fake methodological rationale
- invent citations or mechanisms
- claim "this will pass AI detection"
- rewrite statistical results to sound stronger

## Final check before returning text

Ask:

1. Are the claims tied to the user's actual study, data, or citations?
2. Are the methods and variables named concretely?
3. Are transitions based on logic rather than stock connectors?
4. Are limitations specific rather than generic?
5. Are all numbers and citations preserved?
6. Would a supervisor see this as clearer academic writing, not just "less AI"?
