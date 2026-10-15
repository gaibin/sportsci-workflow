# 选题卡：8周功能性训练对大学生下肢爆发力的影响

🔴 **有红色项：调整选题或条件后再继续**  ·  2026-10-12

> 这张卡只陈述事实和计算结果；题目取舍、与既有研究的区别、引言与讨论都是作者自己的工作。

## 1. 研究问题

| 要素 | 内容 | 检索词 |
|---|---|---|
| 人群 P | 大学生 | 大学生 · 高校学生 · university students · college students |
| 干预/暴露 I | 功能性训练 | 功能性训练 · 功能训练 · functional training |
| 对照 C | 常规体育课 | 常规体育课 · 对照组 · control group |
| 结局 O | 下肢爆发力 | 下肢爆发力 · 纵跳 · countermovement jump · vertical jump · lower limb power |

## 2. 研究设计

- **parallel_prepost** — 有对照组且前后测各一次 → 平行分组前后测
- 可以说：估计干预相对对照的效应（组间差及 95% CI），在随机分组时可作因果解释
- 不能说：非随机分组时必须说明基线差异；不能写成“证明了”
- 计划分析：终测的 ANCOVA（基线为协变量）；报告组间差、95% CI、Hedges g
- 备选分析：变化量（后−前）的独立样本 t 检验
- 主要结局：纵跳高度（cm）
- 次要结局：30 m 冲刺时间

## 3. 证据地图

记录集 **30** 条（0 条缺年份）；窗口 2021–2025；覆盖度：足够（≥30）

| 组合 | 全部年份 | 近五年 |
|---|---|---|
| P+I | 4 | 2 |
| P+O | 4 | 2 |
| I+O | 4 | 2 |
| P+I+O | 2 | 1 |

**撞题判断**：有少量直接近邻（近五年直接重叠 1）

**关于记录集的事实陈述**

- 记录集中有 2 条同时涉及「大学生」「功能性训练」「下肢爆发力」（近 5 年 1 条）；题目必须说明与它们的区别

> 这些是对**记录集**的陈述，不是对全部文献的结论；是否真是缺口，要读完最接近的研究后由你判断。

**最接近的研究**

| # | 年 | 命中 | 设计 | 题名 | 期刊 | DOI |
|---|---|---|---|---|---|---|
| 1 | 2022 | P+I+O | pilot | Eight weeks of functional training improves countermovement jump in university students: a pilot study [synthetic example] | Synthetic example journal | — |
| 2 | 2019 | P+I+O | rct | Eight weeks of functional training improves countermovement jump in university students: a randomised controlled trial [synthetic example] | Synthetic example journal | — |
| 3 | 2025 | I+O | other | Effects of functional training on vertical jump height in older adults [synthetic example] | Synthetic example journal | — |
| 4 | 2024 | P+O | other | Resistance training and vertical jump height in university students [synthetic example] | Synthetic example journal | — |
| 5 | 2021 | P+I | rct | Functional training and balance in university students: a randomised controlled trial [synthetic example] | Synthetic example journal | — |
| 6 | 2019 | I+O | other | Effects of functional training on countermovement jump in older adults [synthetic example] | Synthetic example journal | — |
| 7 | 2018 | P+O | other | Resistance training and countermovement jump in 高校学生 [synthetic example] | Synthetic example journal | — |
| 8 | 2016 | P+I | review | Functional training and balance in university students: a systematic review [synthetic example] | Synthetic example journal | — |

**检索记录**：demo_records.csv → 30

## 4. 样本量

| 项目 | 值 |
|---|---|
| 效应量 | d = 0.70 |
| 效应量来源 | **未写明** |
| 需要分析的人数 | 68（每组 34） |
| 含脱落需入组 | 80 |
| 可及人数（脱落后） | 40（34） |
| 该人数下的功效 | 0.51 |
| 80% 功效可检出的最小效应 | d ≈ 0.99 |
| 假设 | ANCOVA (baseline as covariate; df - 1), 2 equal groups, two-sided α = 0.05, power = 0.80 |

- 效应量没有写明来源（文献 DOI / 预实验 / 最小有意义差异）：样本量只作示意，不能写进开题。

**敏感性示意（常规量级，不是你的效应量）**

| 效应 | 需要人数 | 可及人数下的功效 |
|---|---|---|
| d = 0.3 | 176（每组） | 0.14 |
| d = 0.5 | 64（每组） | 0.29 |
| d = 0.8 | 26（每组） | 0.62 |

## 5. 可行性

| | 项目 | 结果 | 规则 |
|---|---|---|---|
| 🔴 | 样本量 | d = 0.70：需要分析 68 人（含脱落约入组 80）；可及 40 人，脱落后约 34，功效 0.51；该人数能以 80% 功效检出的最小效应 d ≈ 0.99。 | 绿：可及人数下的功效 ≥ 0.80；黄：0.60–0.80，或没有效应量来源；红：< 0.60 |
| 🟢 | 时间 | 需要 22 周（伦理 4 + 招募 2 + 干预 8 + 测试 2 + 分析写作 6），可用 28 周，余量 6 周。 | 绿：可用周数 − 所需周数 ≥ 所需的 20%；黄：有余量但不足 20%；红：所需周数超过可用周数 |
| 🟢 | 测量与设备 | 已列出的测量都有设备 | 主要结局缺设备 = 红；次要结局缺设备 = 黄；没有写 needs 的指标不检查 |
| 🟡 | 伦理 | 伦理审批中：批准前不能招募或收集数据 | 已批准/无需 = 绿；审批中 = 黄；尚未开始 = 黄（红，若时间检查为红）；涉及未成年人或患者 = 至少黄 |
| 🟢 | 统计分析 | 计划分析：终测的 ANCOVA（基线为协变量）；报告组间差、95% CI、Hedges g | 绿：计划分析所需的统计水平 ≤ 你自评的水平；黄：高一级；红：高两级（改用备选分析） |
| 🟢 | 撞题 | 30 条记录；近 5 年直接重叠 1 条（全部年份 2）。 | 直接重叠（人群+干预+结局，近五年）：0 = 绿；1–3 = 绿（需说明差异）；4–9 = 黄；≥10 = 红；记录集 < 30 条 = 黄（只是草图） |

## 6. 变体矩阵

每次只改一个轴，重新统计与记录集的直接重叠。「不可判断」= 该变体的检索词在记录集里一条都没出现，零不代表没人做过。

| 变体 | 近五年直接重叠 | 全部年份 | 较基础题 | 判断 |
|---|---|---|---|---|
| base | 1 | 2 | — | 基础题 |
| outcome=变向能力 | 0 | 0 | -1 | 可判断 |
| population=高中生 | 0 | 0 | -1 | 不可判断 |

> 换了变体后，可及人数、设备、伦理需要重新核对；这张表只回答「撞不撞题」。

## 7. 下一步

1. 效应量没有来源：从最接近的 1–2 篇文献里读出效应量（写明 DOI 和表号），或说明是预实验 / 最小有意义差异
2. 逐篇阅读「最接近的研究」表里的前 3–5 篇，并写一句话说明你的题目与它们的区别（这一句话必须由你自己写）
3. 红色：样本量 — 需要调整
4. 主要结局已固定为「纵跳高度」，看数据前不得更改
5. 把 design_draft.json 交给 `sportsci-figures check-design` 检查列名，再进入数据采集计划
