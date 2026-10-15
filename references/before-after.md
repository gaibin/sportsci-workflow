# Before / After 改写样本库

This file accumulates real AI-vs-human rewrite pairs collected during use. The model should read this when polishing. Concrete examples are more effective than abstract rules.

每对样本格式：
- **AI**：原句
- **人**：改写
- **问题类型**：归类到 `ai-traces-zh.md` / `ai-traces-en.md` 的哪一节
- **简注**：为什么这样改

---

## 中文样本

### 学究化骨架词（ai-traces-zh.md §5）

**1. 解读框架**

- AI：然而 CGM 在运动员人群中的**解读框架**仍未达成共识。
- 人：然而 CGM 在运动员人群中的**应用方法与具体机制**仍未达成共识。
- 注：'解读框架' 是空名词支架。如果作者真有一个具体框架就直接命名（如 'TIR-AT 框架'），否则换成具体动作或对象。

**2. X 学层面 + 不确定性 + 同样突出**（三连骨架）

- AI：**测量学层面的不确定性同样突出**。
- 人：**应用场景中还存在测量稳定性问题**。
- 注：原句把"测量不稳定"这个具体事实包装成三层抽象名词，既没说在什么场景，也没说什么不稳定。改写直接陈述事实。

**3. 戏剧化过渡 + 议题**

- AI：商业化推广**走在科研之前，带来了新的伦理与方法学议题**。
- 人：商业化推广**面临伦理与方法争议**。
- 注："走在……之前" 是新闻评论体，不是学术体。"议题" 一词在中文学术写作中被滥用，用 "问题" 或 "争议" 即可。

**4. 应用证据**

- AI：本综述围绕三个层面梳理 CGM 在运动员人群中的**应用证据**。
- 人：本综述围绕三个方面梳理 CGM 在运动员训练与比赛中的**研究现状**。
- 注："应用证据" 是 evidence-based 教科书翻译过来的洋骨架。中文综述用"研究现状/研究进展/已有报道"更自然。"层面" 也换成 "方面"。

**5. 抽象动作（预测一种状态）**

- AI：少数前瞻性研究尝试用 CGM **预测过度训练或赛中"撞墙"**。
- 人：少数前瞻性研究尝试用 CGM **识别过度训练征兆或比赛末段的低血糖事件**。
- 注："预测一个状态"在临床上意义不清：预测的是状态发生的时点、概率、还是严重度？改成"识别 + 具体事件"更准确，且去掉了引号包裹的"撞墙"这种媒体词。

---

### 词汇降级（用基础词替代浮夸词）

来源：运动心理学综述引言，真人写法 vs AI 常见替换

**6. 重要保证 vs 浮夸替代**

- AI：传统心理技能训练是运动员取得优异成绩的**重要基石 / 核心支柱 / 坚实保障**。
- 人：传统心理技能训练是运动员取得优异成绩的**重要保证**。
- 注：中文运动科学真人写作偏好"保证/保障/依据/基础"这类朴素词，"基石/支柱/基石/基底"是 AI 偏爱的隐喻升级，读起来像演讲稿。

**7. 发掘差异 vs 深入探讨**

- AI：进一步**深入探讨**传统心理技能训练与正念训练的**内在差异及其作用机制**。
- 人：进一步**发掘**传统心理技能训练和正念训练的**差异**。
- 注："深入探讨"是头号 AI 词，已在 §3 列出。"内在差异及其作用机制"是名词堆砌。"发掘"更动态、具体。"差异"两字够了，不用加"内在"和"机制"。

**8. 还有待研究检验 vs 仍需进一步深入探讨**

- AI：对这两种心理训练延续效果的比较**仍需进一步深入探讨与检验**。
- 人：对这两种心理训练延续效果的比较**还有待研究检验**。
- 注："进一步深入探讨与检验"是 AI 四字词叠加套路。"还有待研究检验"六个字说清楚了，朴素、直接。

**9. 局限表述：难免会存在争议 vs 存在严重局限**

- AI：这一实验设计**存在较大局限性和不足，对结果的解释力有限**。
- 人：这一实验设计对实验结果的解释**难免会存在争议**。
- 注：真人写局限时用语较轻，承认问题但不渲染。"难免"带着对领域客观情况的理解，没有贬低别人研究的意思。AI 倾向于把局限说得很严重（"存在严重不足"），反而显得不客观。

**10. 段内并列问题用 1）2）不用首先/其次**

- AI：**首先**，研究者并未设置对照组……**其次**，很少有研究者探究延续效果……
- 人：存在两个问题：**1）**研究者并未设置对照组……**2）**很少有研究者探究延续效果……
- 注：当段落内需要清点两个以上具体问题时，数字标号（1）2）3）） 比首先/其次更清晰，且更像真实作者的行文习惯。首先/其次最怕的是段落开头就用，这里是嵌在段落中间的列举，数字标号反而是对的。

---

## 英文样本（MSSE 综述引言）

### 领域习语与句式（ai-traces-en.md 补充）

**11. hallmark improvements vs 泛化形容词**

- AI：the **well-known / significant** benefits of RT on skeletal muscle
- 人：**the hallmark improvements** in skeletal muscle mass and function
- 注："hallmark"是运动科学圈内的约定搭配，意指"这一干预的定义性变化"。AI 找不到这个词，会替换成泛化形容词（significant/notable/important）。遇到某个干预最核心的结果，优先查该领域顶刊是否有约定搭配，而不是自己选形容词。

**12. are being increasingly appreciated vs has been increasingly recognized**

- AI：RT **has been increasingly recognized as** an important health-promoting activity.
- 人：The benefits of RT **are being increasingly appreciated as health-promoting behavior**.
- 注：① "appreciated"比"recognized"多一层"价值被逐渐理解"的含义。② "behavior"把 RT 纳入行为学框架，比"activity/modality/intervention"更有理论定位意识。AI 几乎不做这种范畴选择。

**13. 历史背景的精确对冲**

- AI：RT **was first proven to be beneficial** by DeLorme through his work with soldiers.
- 人：RT **were perhaps first documented to be beneficial beyond personal strength development** by Captain Thomas DeLorme, who recognized the benefits of RT in wounded soldiers.
- 注：三处细节都做了精确限定：① "perhaps"标注真实历史不确定性。② 用"first documented"（有文献记录），没用"first proven"（过度确定）。③ "beyond personal strength development"点明这条记录的历史意义是"把 RT 的价值延伸到个人力量之外"。AI 写历史背景时往往过于确定或过于笼统。

**14. 长定义句：信息递进 vs 同义词并列**

- AI：RT improves muscular strength, **enhances power output, boosts athletic performance, and promotes overall health**.
- 人：progressively increasing force output to improve **muscular strength, power, endurance, and overall health and sports performance**.
- 注：AI 长句常见问题是用并列同义动词堆砌（improve/enhance/boost/promote），每个动词后接一个宾语，看似内容丰富实则重复。真人的长定义句结构是：机制 → 动作类型 → 目标，每个分句加新维度的信息，不是重复同一层意思。

**15. "crucial"只用一次原则（密度 > 词本身）**

- 问题：本 skill 把"crucial"列为 AI 词，可这段 MSSE 第一句就用了"crucial"。
- 解释：单次、精确使用"crucial"完全可以接受。问题在于 AI 会在同一段里把 crucial / pivotal / essential / critical 叠加使用。判断标准是"200 字内出现了几个同类强调词"，单看这个词有没有出现没有意义。一个够，两个警告，三个以上重写。

**16. Beyond X, Y includes… vs Not only X but also Y**

- AI：**Not only** does RT improve muscle mass, **but it also** reduces depression and improves sleep.
- 人：**Beyond** the hallmark improvements in skeletal muscle mass and function, the benefits of engaging in RT **include** reduced mortality… reduced depression… and improved sleep quality.
- 注："Beyond X, Y includes"比"not only...but also"更简洁，且没有 AI 标志性的对仗感。同时它把"已知的核心效益"（骨骼肌）和"延伸效益"（心血管、心理等）的层次关系表达清楚了，"not only...but also"做不到这一点。

---

### 证据强度与词强度匹配（MSSE 样本 2）

**17. "may" 的精确投放 vs 全段统一对冲**

- AI（过度保守）：RT **may** improve cardiovascular function, **may** reduce risk of diabetes, and **may** prevent osteoporosis.
- AI（过度自信）：RT improves cardiovascular function, reduces risk of diabetes, **and also** prevents osteoporosis, reduces colon cancer risk, and fosters well-being.
- 人：RT improves cardiovascular function (72)... prevents osteoporosis (163), **may** reduce the risk of colon cancer (146)...
- 注："may"只放在结直肠癌那一项（证据较弱），其余用直接动词。一段里的 hedging 应该跟随证据强弱分布，而不是全段统一。

**18. 效益动词不重复**

- AI：RT **improves** cardiovascular function, **improves** bone density, **improves** insulin sensitivity, and **improves** psychological well-being.
- 人：improves / reduces / prevents / may reduce / promotes / preserves / **fosters** psychological well-being
- 注：每个效益选一个精准动词。特别是"fosters"用于心理健康："to foster"含有培育/促进生长的意思，比"improve"更准确描述心理健康的变化性质。积累：improves（功能性提升）/ reduces（风险降低）/ prevents（阻止发生）/ preserves（维持现有水平）/ fosters（培育、渐进发展）。注意：foster 本身也是新一代 AI 高频词，只在确实表达"渐进培育"时单次使用，不要当作 improve 的通用替身（见 `ai-traces-en.md` §3.1）。

**19. 先让步再推进 vs 直接给好消息**

- AI：The proper manipulation of RT variables can prevent training plateaus and continuously improve muscular fitness over time.
- 人：**Although it is impossible to improve at the same rate over long-term periods**, the proper manipulation of program variables can **limit** training plateaus and increase the ability to achieve a higher level of muscular fitness.
- 注：① "Although" 引导的让步从句主动承认真实局限。② 用"limit"（减少），不用"prevent"（阻止），词的强度与实际证据匹配。③ 用"increase the ability to achieve a higher level"，不用"maximize muscular fitness"，保持长期视角，不夸大。

**20. 引号只用于真实引文**

- AI：The "key" variables of RT include "resistance choice," "exercise selection," and "rest periods."
- 人：Progression in RT may be defined as **"the act of moving forward or advancing toward a specific goal over time until the target goal has been achieved"** (8).
- 注：引号只包裹直接引用的他人原文，且紧跟引用编号。不为强调、不为暗示"这个词有点奇怪"、不为对冲用引号。AI 把引号当作语气工具，真人把引号当作归属工具。

**21. 条件限定不省略**

- AI：RT improves cardiovascular function and reduces the risk of coronary heart disease.
- 人：RT, **when incorporated into a comprehensive fitness program**, improves cardiovascular function...
- 注："when incorporated into a comprehensive fitness program"是真实条件，不是废话。RT 单独训练 vs 作为综合计划的一部分，效果有差异，审稿人会关注这个区别。AI 写效益时倾向于省略真实条件，让结论看起来更广泛、更强，反而降低了可信度。

---

### 讨论段节奏与转折词（中文流行病学样本）

**22. "这表明，"直接跟逗号 vs 加衬字**

- AI：**这一研究结果充分表明，** 随年龄增长……
- 人：**这表明，** 随年龄与学业负担的增长……
- 注：去掉"一研究结果充分"这类衬字，"这表明，"四个字直接进入解释。衬字越多，越像在给一个显而易见的结论加分量，反而显弱。

**23. "分歧" vs 名词化替代词**

- AI：国内外相关纵向研究结论间也仍存在一定**不一致性 / 差异性**。
- 人：国内外相关纵向研究结论间也仍存在一定**分歧**。
- 注："分歧"是汉语本词，比带"性"的名词化更直接。规律：凡是能用两字词表达的，不用"X性/X化"四字名词。

**24. "相悖" vs 弱化表达**

- AI：Jones等的结论与本研究**存在一定差异 / 有所不同 / 不尽一致**。
- 人：Jones等的结论与本研究**相悖**。
- 注："相悖"明确承认方向性矛盾，不是程度上的差异。真人写讨论段对矛盾文献的描述是直接的，AI 倾向于用弱化词回避冲突感，审稿人反而欣赏敢于直接承认矛盾的写法。

**25. 冒号紧跟数据，不加缓冲句**

- AI：Jones等的结论与本研究相悖。**研究结果显示，** 两种行为的平均追踪系数分别为0.39和0.52。
- 人：Jones等的结论与本研究相悖：**显示两种行为的平均追踪系数分别为0.39和0.52**。
- 注：冒号后直接给证据，省去"研究结果显示/数据表明"一类缓冲词。

**26. "即"做数据后的解释连接**

- AI：两种行为的平均追踪系数分别为0.39和0.52。**这说明，与体力活动相比，** 静态行为反而更稳定。
- 人：追踪系数分别为0.39和0.52，**即与体力活动相比，** 静态行为反而显示出更强的稳定性。
- 注："即"相当于"也就是说"，但少两个字，且不另起一句。把数据和解读压缩在同一句里，节奏更紧。

**27. "不过"用于引入轻度转折 vs "然而"**

- AI：**然而，** 因对象年龄分布等因素，国内外研究结论间也仍存在分歧。
- 人：**不过**因对象年龄分布、追踪时间跨度长短以及体力活动测量方法等因素，……也仍存在一定分歧。
- 注："不过"语气比"然而"轻，适合引入不推翻主结论的补充说明或局限。"然而"暗示接下来是重要转折，用在轻度说明上显得过重。

**28. "纵观相关研究"用在段落中部，引出他人综述**

- AI 用法（仅用于结尾）：**综上所述，** 本研究表明……
- 人用法（用于中部引出文献）：**纵观相关研究，Boreham等[7]指出……**
- 注："纵观"是俯瞰式动词，在段落中部使用，是引出某位学者对领域全局观点的前置语。AI 几乎只把"纵观/综观"放在结尾，真人学者会在讨论段中部用它引出综述性引用，节奏完全不同。

**29. 原因与结果合并一句 vs 拆开两句**

- AI：国内外相关纵向研究在研究对象年龄、追踪时间以及体力活动测量方法上存在差异。**因此，** 各研究结论间也存在一定分歧。
- 人：**不过因**对象年龄分布、追踪时间跨度长短以及体力活动测量方法**等因素，** 国内外相关纵向研究结论间也仍存在一定分歧。
- 注：把原因（因……等因素）和结果（存在分歧）压缩在一句里，用"因……等因素"做状语前置。AI 倾向于拆成两句（先陈述差异，再用"因此"承接），结构松散。

---

### 局限性段写法（中文儿童 PA 研究样本）

**30. 贡献声明：克制 vs 自夸**

- AI：本研究**首次系统地**探讨了 BMI 与儿童体适能的纵向关联，**填补了该领域的空白**。
- 人：本研究……探讨了 BMI 与儿童体适能的纵向关联，**具有一定创新性**。
- 注：用"一定"对"创新性"做主动软化，是中文学术写作对自己研究最得体的定位。"首次/填补空白/开创性"是审稿人的红色标记词，除非有强证据证明，否则一律删除。

**31. "加以..."做正式书面动词包装**

- AI：两者关联**有待未来进行更严格的实验进一步阐明**。
- 人：两者关联**有待未来进行更严格的干预性实验加以进一步阐明**。
- 注："加以"+ 动词 是中文学术正式语的特征结构，把动作对象化。AI 写中文极少自然用"加以"，而是直接用动词。学习这种结构能立刻让中文学术体气质提升。

**32. "鉴于"vs"由于/考虑到"**

- AI：**由于本研究跨越学龄前与学龄2个不同年龄段……**
- 人：**鉴于本研究跨越学龄前与学龄2个不同年龄段……**
- 注："鉴于"比"由于/因为/考虑到"更具学术正式感，适合在大段论述开头使用。AI 几乎只用"由于/考虑到"。规律：长段论述、需要凝重感时用"鉴于"。短句、轻量因果用"由于"。

**33. "不可避免地"承认局限**

- AI：本研究**虽然存在一定程度的样本流失，但比例在可控范围内**。
- 人：**不可避免地存在一定程度的样本流失**。
- 注：AI 倾向于给局限找辩护（"虽然 X 但比例可控"），反而显得遮掩。"不可避免地"承认局限的客观性，是真人学者的自信。

**34. 改进方向具体化 vs 空话**

- AI：**未来研究应进一步深入探讨**这一问题。
- 人：日后可以通过**适当缩短追踪时间、增加追踪频率**以尽可能减少上述因素影响。
- 注：给具体方法（缩短时间、增加频率），不给"进一步深入探讨"。AI 提改进方向几乎全是空话，因为它不真正懂这一具体设计的可调参数。每个局限点之后，强迫自己想出至少一项可执行的改进。

**35. 局限中嵌入领域级判断**

- AI：本研究的加速度计设置**可能存在一定偏差，影响结果准确性**。
- 人：**目前学界尚未形成一个能够同时面向学龄前和学龄儿童的加速度计采样间隔与界值点设置推荐**，本研究虽已运用了相应年龄段使用最为普遍合理的设置，但……仍是影响加速度计测量结果准确性的重要影响因素。
- 注：把"我们的方法有局限"提升为"整个领域还没有解决这个问题"。这是真人学者的视野，需要熟悉该领域文献现状才能写出来。AI 停留在"本研究使用了某设置，可能存在偏差"。

**36. "虽……但……"诚实辩护结构**

- AI（只承认）：本研究的加速度计设置存在偏差。
- AI（只辩护）：本研究采用了**最合理、最普遍**的设置。
- 人：本研究**虽已运用**了相应年龄段使用最为普遍合理的设置，**但**不同的采样间隔与界值点设置**仍是**影响加速度计测量结果准确性的重要影响因素。
- 注：三段式：承认自己尽力 → 然而 → 局限仍然存在。AI 倾向于二选一（只承认或只辩护），真人选择都说，更可信。

**37. 局限段直接引出 vs 加铺垫**

- AI：**尽管本研究取得了上述发现，但不可避免地存在一些局限性，主要表现在以下几个方面：**
- 人：**但仍存在以下一些不足有待进一步完善：**
- 注：一句话直接进入 1）2）3）的列举，省去"尽管……但是……主要表现在……"的过度铺垫。

---

### 英文 Strengths/Limitations 段（MSSE 样本）

**38. 平行起手 vs 不对等开头**

- AI：The present study has **several notable strengths**. ... However, **a few limitations** should be acknowledged.
- 人：**Strengths** of the current study include ... **Limitations** include ...
- 注：用同一动词 "include" 起手 strengths 和 limitations。AI 给 strengths 隆重铺垫、给 limitations 保守铺垫，反而拉开了语气差距。真人作者把它们当作同等地位的方法学事实陈述。

**39. "likely not generalizable"：hedging 的中间档**

- AI（太弱）：results **may not be** generalizable
- AI（太强）：results **are not** generalizable
- 人：results **are likely not** generalizable
- 注："likely not" 承担一定的概率判断（很可能不可推广）但不绝对化。AI 倾向走 hedging 的两个极端，"likely not" 这种中间档需要刻意训练。

**40. "do not fully encompass"：局限词的精度**

- AI（太强，否定自己）：force plate measurements **do not capture** the muscle-bone unit relationship
- AI（太弱，回避）：force plate measurements **may not capture** the relationship
- 人：mechanical loads ... **do not fully encompass** the muscle-bone unit relationship
- 注："fully encompass" 承认不全面，但承认已经部分捕捉。"capture" 是要么有要么没有，"encompass" 暗含"覆盖范围"概念，更适合表达"涵盖一部分但不完整"。

**41. "despite the assessment of..." 自我让步**

- AI：A limitation of this study is that force plates do not capture the full muscle-bone relationship.
- 人：**Despite the assessment of relationships between loading-related and skeletal outcomes reported in the current study**, mechanical loads assessed via a force plate **do not fully encompass** the PA-related muscle–bone unit relationship.
- 注：先承认自己做了什么（评估了负荷-骨骼关系），再说明这件事还不够。"despite + 自我贡献"是真人写局限段的成熟结构：先确认贡献，再承认贡献的边界。AI 倾向于跳过对自我工作的承认直接说局限。

**42. 同段内 transition 不重复**

- AI（同段重复）：First, ... **Moreover**, ... **Furthermore**, ... **Additionally**, ...
- 人（变体）：Strengths ... include ... **Moreover** ... **Another key strength is** ...
- 注：在同段中需要列举多个并列点时，避免连续使用同一连接词。"Another key strength is" 是 "Moreover" 的变体，"Finally" 是收尾的变体。AI 倾向用机械的相同连接词。

**43. 限定语具体到三个例子**

- AI：results may not generalize to **other populations or settings**
- 人：results are likely not generalizable to **those of other devices, or in other age-groups, or those with abnormal movement patterns**
- 注：列出三个具体的不可推广方向，不用抽象的 "other populations or settings"。具体度是真人写作的痕迹，它表明作者真的想过这三个具体场景。

**44. 领域固定术语单次精用**

- AI：bone-promoting activities ... measurement comparison ... real-world applicability ... muscle and bone interaction ... hormonal signaling
- 人：potentially **osteogenic** activities ... **concurrent validity** ... **ecological validity** ... **muscle–bone unit** ... **endocrine and paracrine signaling**
- 注：每个领域固定术语只用一次。AI 找不到这些精准词，倾向于用日常英语替换。要写好运动科学英文，每个子领域的固定术语库都需要积累。

**45. 高密度技术短语 "inherent to + 设计名"**

- AI：accounting for **the dependence of repeated measurements**
- 人：accounting for **the nonindependence inherent to multitrial validation study designs**
- 注："inherent to + 设计名"是统计学/方法学高级用法，承认某个特征是该设计内在的、不可避免的。AI 倾向于简化为日常表达。

---

### 英文 Discussion 开篇（BJSM 风格运动损伤样本）

**46. 诚实报告非单调剂量-反应**

- AI（修缮）：Increased hazards of 64%, **78%** and 128% for small, moderate, and large spikes were found, respectively.
- 人（照实）：Increased hazards of **64%, 52% and 128%** for small, moderate and large spikes were found, respectively.
- 注：真实数据中间档（52%）低于小档（64%），剂量-反应不完全单调。AI 几乎一定会"修缮"，让数字看起来递增。真人作者照实写。真实剂量-反应关系本来就有起伏，照实写反而专业。

**47. "To the best of our knowledge" + 具体样本量**

- AI：To our knowledge, **few studies have** examined this association.
- 人：To the best of our knowledge, **only one 435-runner cohort study** has previously examined the link...
- 注：三处精度叠加：① "To the best of our knowledge" 做合理对冲。② "only one" 给出准确数量。③ "435-runner" 给出研究规模。AI 写"few studies have"，既无样本量也无具体数。

**48. 援引文献时给出每项研究的具体规模**

- AI：This finding corroborates results from **previous cohort studies of novice runners and youth runners**.
- 人：This finding also corroborates results in **an 874-person cohort of novice runners and a study on 434 youth cross-country runners**.
- 注：逐一标出每项研究的样本量。这表明作者真的读过这些文献，记得它们的规模。AI 几乎做不到这种精度。

**49. 比较强度词的精确选择**

- AI（万用同一动词）：Our findings **are consistent with** previous research. ... Other studies **are consistent with** these results.
- 人（差异化动词）：findings **closely align with** ... results **corroborate** ... evidence **confirms**...
- 注：根据证据强弱挑动词。"closely align with"（紧密契合，结果很像）、"corroborates"（印证，独立支持）、"confirms"（证实，最强）。AI 反复用 "is consistent with" 因为最安全，真人作者根据每条证据的强度选不同动词。

**50. 诚实报告非显著趋势的完整统计**

- AI（隐藏）：A non-significant trend was observed for progressions between 1% and 10%.
- 人（透明）：**Although not statistically significant**, a progression between 1% and 10% translated into **an increased rate of 19% (95% CI: −10% to 57%, p=0.22)**.
- 注：报告非显著结果时给出完整 95% CI 和 p 值，并明确标注"not statistically significant"。审稿人最看重的就是非显著趋势的诚实报告。隐藏非显著结果是 AI 和粗心作者的共同毛病。

**51. 非显著趋势的三层 hedging**

- AI（太确定）：Progressions up to 10% **showed an increase** in injury risk.
- AI（太回避）：Progressions up to 10% **may possibly suggest some potential increase** in risk.
- 人（精确）：progressions up to 10% **appear to slightly increase** the risk of injury.
- 注：三层叠加但每层做不同工作：① "appear to"（视觉证据）② "slightly"（程度小）③ "increase"（方向明确）。是描述非显著但有趋势的图形证据时的标准措辞。

**52. 实践建议用具体数字 + 祈使句**

- AI：**It is recommended that runners exercise caution** when increasing running distance.
- 人：**Runners should avoid running a distance in their current session that exceeds 10% of the longest distance covered in the previous 30 days.**
- 注：直接、可执行、有具体数字（10%、30 天、当前 session）。Discussion 段的实践建议必须可量化、可执行。空话级别的建议是 AI 的标志。

**53. 用具体数值场景说明模型局限**

- AI（抽象）：The model may not capture cumulative effects across multiple sessions.
- 人（具体）：For example, **if the longest distance covered by a runner in the past 30 days was 10 km, then running 11 km, 12.1 km and 13.3 km in subsequent sessions within the same week**, despite each reflecting a 10% increase, may still be considered excessive due to insufficient recovery time.
- 注：用一个具体数值场景（10 km → 11 / 12.1 / 13.3）说明模型盲点。AI 写局限时几乎不会自己造数值场景，倾向于抽象说明。具体数值场景比任何抽象描述都更让审稿人理解作者的思考深度。

**54. "in the context of" 做精确范围限定**

- AI：This study **challenges the ACWR** for monitoring training load.
- 人：This study challenges the use of traditional load monitoring approaches, including the **ACWR in the context of running-related injury occurrence**.
- 注："in the context of"把批评精确限定在跑步损伤场景，不泛化否定 ACWR（ACWR 在团队项目中仍可能有效）。AI 写 challenges/critiques 时倾向于不加范围限定，听起来更彻底但反而显得不严谨。

**55. "paucity of knowledge" 等精确学术词**

- AI：There is a **lack of studies / limited research** on this topic.
- 人：there is a **paucity of knowledge** on the association between...
- 注："paucity"（少而稀缺）是精确学术词。同类还有：dearth（缺乏）、scarcity（稀少）、absence（缺失）、scant（贫乏的）。每个英文综述里多记一个这类词，下次写作就更地道。

---

### 英文 Methods 段（BJSM 风格前瞻队列样本）

**56. 日期精确到日 vs 月份概括**

- AI：Enrolment occurred **between July and December 2019**, with follow-up **until 2021**.
- 人：Enrolment occurred **between 4 July 2019 and 1 December 2019**, and the study followed up **until January 2021**.
- 注：方法学描述中的时间精度直接关系到可复现性。AI 倾向于写到月份级别，真人作者会精确到日（招募）+ 月（follow-up）。审稿人会注意这个细节。

**57. 报告规范带全称展开**

- AI：Reporting followed STROBE guidelines.
- 人：Reporting followed the **STROBE (Strengthening the Reporting of Observational Studies in Epidemiology)** guideline and statistics, interpretation and reporting was checked for consistency using the **CHAMP (CHecklist for statistical Assessment of Medical Papers)** checklist.
- 注：① 报告规范缩写要展开全称（首次出现）。② 用多个互补规范（STROBE + CHAMP）显示方法学严谨。AI 通常只知道 STROBE / CONSORT / PRISMA 等知名规范，不知道 CHAMP（统计学专用 checklist）。

**58. 排除标准给出原因**

- AI：Participants were excluded if they ran sessions below 500 m or above 100 km.
- 人：Participants were excluded if they ... only ran sessions below the distance of 500 m or above the distance of 100 km **due to the risk of data error**.
- 注：每条排除标准都是方法学权衡，不写原因等于放弃和审稿人对话。给原因的方式很简单：句末加 "due to / because / to avoid + 原因"。

**59. Worked example 用真实数字**

- AI（抽象）：The relative change was calculated as the current session distance divided by the longest session distance in the past 30 days.
- 人（带 worked example）：The distance covered in a single running session, **for example, 12 000 m**, was divided by the longest distance covered in each session undertaken in the 30-day period **(eg, 8000 m)** preceding the current running day. In the above example, the calculation **12 000 m/8000 m resulted in a ratio of 1.5, signifying a 50% increase** in running distance.
- 注：用真实数字举例（12 000 m / 8000 m = 1.5）把抽象公式变成具体场景。AI 写 Methods 几乎从不主动造数字示例。每个有计算的 Methods 段都应该有一个 worked example，这是直接体现透明度的方式。

**60. 每个 cut-off 独立给出理由**

- AI：Three cut-offs (10%, 30%, 100%) were chosen based on prior literature.
- 人：A 10% cut-off was used **given the significance of the '10% rule' in running communities**,20 whereas a 30% increase was selected **since progression in weekly averaged running distance exceeding this amount has been associated with increased risk of injury**.17 18 27 A 100% cut-off was chosen **as it represents doubling in running distance**.
- 注：每个 cut-off 单独给独立理由：① 社区惯例（引文）② 既往研究（三个引文）③ 数学含义（翻倍）。AI 倾向于一笔带过。规律：方法学中的每个数字阈值都需要一句话解释来源。

**61. 承认方法学选择的可争议性 + 提前给出补充分析**

- AI：These cut-off values were used in the analysis.
- 人：**As cut-off values can be discussed**, the relative injury hazard as a function of change in running distance **as a continuous variable will be visualised in the results section**.
- 注：① 承认 cut-off 是可被质疑的方法学选择（"can be discussed"）。② 提前指出"我们用连续变量也做了，结果在 Results"。这种"知道审稿人会问什么、提前回答"的姿态是成熟作者的标志。AI 不会主动揭示自己方法的脆弱处。

**62. 边缘情况显式处理**

- AI（隐去）：Sessions where calculation was not possible were removed from analysis.
- 人（显式）：(5) **not possible (NP) to calculate** a relative change since the denominator was zero **(NP-state)**.
- 注：当 30 天内无跑步记录时分母为 0，这是真实数据中的边缘情况。显式定义为单独类别（NP-state）比删除更透明。AI 处理分类时经常忘掉边缘 case，或选择"silently dropping"。

**63. "time-varying" 等统计专业术语**

- AI：The exposure could change over time as runners completed sessions.
- 人：The exposure was **time-varying**. Runners could therefore change their exposure status each time they completed a running session.
- 注："time-varying"在生存分析/流行病学中是精确术语（时间依赖暴露）。AI 倾向于用日常语义"could change over time"，意思相近但失去统计含义。Methods 段中精准的统计学术语是审稿人快速判断作者方法学水平的指标。

**64. "as described by Author et al" 引前人方法**

- AI：Following the methods of Gabbett et al, we calculated ACWR.
- 人：the uncoupled ACWR was calculated using ... **as described by Gabbett et al.**28
- 注：引前人方法的标准格式是 "X was calculated ... **as described by [Author] et al**.[ref]"。AI 经常写 "Following / Based on the methods of..."，意思相近但格式不规范。

**65. 技术变体的精确名（如 "uncoupled" ACWR）**

- AI：ACWR was calculated as 1-week acute load divided by 3-week chronic load.
- 人：the **uncoupled** ACWR was calculated using the most recent 1-week acute workload ... and the **prior** 3-week chronic workload as described by Gabbett et al.
- 注："uncoupled"区分于"coupled" ACWR：前者分子分母时间窗不重叠，后者重叠。这是 ACWR 文献中已被讨论的方法学争议。"prior 3-week"明确不包含当前周。AI 写 ACWR 通常不区分 coupled / uncoupled，因为不熟悉这一文献争议。每个领域都有这样的"内行词"，要靠读专业文献积累。

---

### 中文 Results 段（儿童 PA 追踪研究样本）

**66. 冒号式时段组织 vs"在……阶段中"铺垫**

- AI：**在基线阶段中**，结果显示儿童总静态行为时间不存在性别差异。**而在追踪阶段中**，结果显示女童总静态行为时间显著高于男童。
- 人：基线阶段：儿童的总静态行为时间不存在性别差异（t=0.828，P＞0.05）……追踪阶段：女童总静态行为时间……显著高于男童……
- 注：用冒号把两个时间段并列展示，不需要"首先报告基线、其次报告追踪"。Results 段不是论证，是数据展示，冒号是最直接的并列工具。

**67. 多统计量集中报告**

- AI（散开）：男童学习日LPA时间显著高于女童(t=2.10，P＜0.05)。**此外，** 男童双休日LPA时间也显著高于女童(t=2.45，P＜0.05)。**同时，** 男童学习日MVPA时间显著高于女童(t=2.3，P＜0.05)。**最后，** 男童双休日MVPA时间也显著高于女童(t=2.49，P＜0.05)。
- 人（集中）：男童学习日和双休日LPA、MVPA时间**均显著高于女童（t=2.10，P＜0.05；t=2.45，P＜0.05；t=2.3，P＜0.05；t=2.49，P＜0.05）**。
- 注：当多个比较走同一逻辑（都是性别差异）时，把统计量放在一个括号里用分号分隔。一句替代 AI 的四句，且对应关系更清晰。

**68. "呈显著上升/下降趋势" vs"显著增加/降低"**

- AI：儿童学习日静态行为时间**显著增加**（t=-2.71，P＜0.01）。
- 人：儿童学习日静态行为时间**呈显著上升趋势**（t=-2.71，P＜0.01）。
- 注："呈……趋势"是中文统计学描述方向变化的固定搭配。"显著增加/降低/提高"是单字动词，更口语。"呈显著上升趋势"是更书面的统计学语感。中文期刊偏好后者。

**69. 复合句压缩整个统计模型**

- AI（拆开）：本研究采用追踪阶段各体适能数据作为因变量。同时，将MVPA变化趋势分组与BMI分组作为自变量。**此外，** 各体适能基线数据被作为协变量。**最终采用** 多因素协方差分析进行检验。
- 人（一句）：**以追踪阶段各体适能数据为因变量，MVPA变化趋势分组、BMI分组为自变量，各体适能基线数据为协变量，进行多因素协方差分析。**
- 注：中文统计学方法陈述的标准模板："以 X 为因变量，Y 为自变量，Z 为协变量，进行 W 检验"。一句讲清整个模型。AI 拆三句不仅啰嗦，还失去了模型四要素的整体感。

**70. 国家/行业标准给完整书名 + 年份**

- AI：依据国内常用的BMI分类标准对儿童BMI进行二分类。
- 人：依据**《中国学龄儿童青少年超重、肥胖筛查BMI分类标准（2004）》** 中不同性别相应年龄段BMI界值。
- 注：完整书名号 + 年份。中文学位论文和期刊要求引用国家标准时给全名。"国内常用"一类模糊措辞会被审稿人退回。

**71. "考虑到 + 原因[ref]"做精炼引入**

- AI：**由于** BMI同样是儿童体适能的重要影响因素之一[17]，**因此** 本研究将BMI纳入分析。
- 人：**考虑到BMI也是体适能的重要影响因素[17]**，依据……界值，对追踪阶段儿童BMI数据进行二分类处理。
- 注："考虑到 + 简短原因 + 引文"是中文加入新变量的标准引入方式。"由于……因此"句式臃肿且头重脚轻。

**72. F + 主效应 + 交互 + post-hoc 一句话**

- AI（拆四句）：方差分析显示，MVPA趋势分组的主效应显著(F=2.736，P＜0.05)。**同时，** BMI分组的主效应也显著(F=4.753，P＜0.05)。**两者之间** 不存在交互作用(F=1.137，P＞0.05)。**进一步分析显示**，持续活跃组的握力水平显著高于持续不足组。
- 人（一句）：MVPA趋势分组、BMI分组对于男童握力的**主效应均显著**（F=2.736，P＜0.05；F=4.753，P＜0.05），**两者间不存在交互作用**（F=1.137，P＞0.05），持续活跃组的握力水平显著高于持续不足组，超重肥胖组的握力水平显著高于正常体重组。
- 注：把主效应、交互、post-hoc 装进一个长句的中文标准节奏。逗号分隔不同分析层。

**73. 反直觉结果照实写 vs 软化措辞**

- AI（软化）：超重肥胖组的握力水平**略高于** 正常体重组，**这一差异需要进一步研究证实**。
- 人（照实）：**超重肥胖组的握力水平显著高于正常体重组**。
- 注：Results 段就是数据展示。反直觉发现照实写，解释留到 Discussion。AI 看到反直觉结果倾向于：① 改用更弱措辞（"略高于"），② 提前在 Results 中给解释，③ 模糊化（"两组间存在差异"）。这些都是对数据不诚实的表现。

**74. 负结果干净收尾**

- AI：**虽然** MVPA趋势分组、BMI分组对于柔韧素质的主效应及交互作用均不显著，**但** 这一结果可能与样本量、测量方法等因素有关，**未来研究可进一步……**
- 人：MVPA趋势分组、BMI分组对于男、女童柔韧素质的**主效应及交互作用均不显著**。
- 注：Results 段的负结果不需要任何包装、缓和、转折。一句话报完。AI 倾向于在负结果后加"虽然……但是……未来研究"，这是 Discussion 内容混进了 Results。

**75. 中文期刊统计量格式（全角逗号 + 无空格）**

- AI（英式）：(t = 2.10, P < 0.05)
- 人（中式）：（t=2.10，P＜0.05）
- 注：中文期刊用全角括号、全角逗号、半角等号 + 数字，中间无空格。AI 写中文时常用半角符号 + 空格，这是英文格式直译。这是一个微小但显眼的格式差异。

---

### 中文博士论文 Discussion / 运动生化机制讨论

**76. 机制效应用逗号串联 vs"不仅……而且"对仗**

- AI：有氧运动**不仅** 能减轻体重、改善血脂，**而且** 能增强胰岛素敏感性。**同时也** 能改善代谢紊乱状态，**并且** 提升血糖调控能力。
- 人：有氧运动能**有效减轻或控制体重，改善血脂代谢，通过不同途径增强组织的胰岛素敏感性和葡萄糖摄取，改善机体代谢紊乱状态，提升血糖调控能力，减轻并延缓疾病的发生发展**[206, 207]。
- 注：六个机制效应用逗号串成一句，每个短语都是一个具体生理通路。"不仅……而且……同时……并且"是 AI 对仗结构，把多机制的密度感破坏掉。机制讨论的力量在于密度，不在于排比。

**77. 领域缩写一次性建立后反复使用**

- AI：DIO小鼠（饮食诱导肥胖小鼠）的BCAAs（支链氨基酸）水平在长期有氧运动后下降，且这一变化与IR（胰岛素抵抗）状态相关。
- 人：长期有氧运动有效降低了**DIO小鼠**血浆**BCAAs**和**BCKAs**水平 …… 改善**IR**……
- 注：缩写第一次出现给中文全称（在前文 Methods 章已建立），之后全文反复使用不再展开。AI 写中文时常每次都展开括号，破坏阅读节奏。

**78. "回补"等领域专有动词**

- AI：长期**补充**BCAAs 对运动小鼠的体重增长产生影响。
- 人：长期**回补**BCAAs 的小鼠相比于不补充小鼠的体重增长程度更大。
- 注："回补"在营养/生化中是 replenishment 的对应词，特指在已知缺乏或代谢异常背景下的补充。AI 倾向于用通用的"补充"，意思相近但失去专业含义。每个子领域都有这种专有动词。

**79. "反映了"做弱化推断动词**

- AI：以上结果**证明了/表明** 单纯有氧运动在改善DIO小鼠体成分方面**存在局限**。
- 人：以上结果**反映了**单纯有氧运动在改善DIO小鼠体成分方面的**作用局限性**。
- 注："反映了"比"证明/表明"弱，比"暗示"具体，是中文 Discussion 中处理"数据→推论"的成熟弱化动词。配合"作用局限性"这种名词化结论，是机制讨论的标志语感。

**80. "有趣的是"引非典型发现 vs"值得注意的是"**

- AI：**值得注意的是**，有氧运动降低了肝脏重量。
- 人：**有趣的是**，有氧运动降低了肝脏重量，但是否回补BCAAs 对其未产生影响。
- 注："值得注意的是"已被本 skill 标记为 AI 词（见 ai-traces-zh.md §3）。"有趣的是"在 Discussion 中节制使用是可以的，用于标注与预期或主流不符的发现。规律：每段最多一次"有趣的是"。

**81. "独立于" vs"与……无关"**

- AI：长期运动改善IR的作用**与体重和体成分变化无关**。
- 人：长期运动改善IR的作用**独立于体重和体成分变化**。
- 注："独立于"是科学精确连接词，含统计/机制层面的"互不依赖"含义。"与……无关"较口语，且暗示完全没关系。"独立于"更适合表达"作用机制不需要中介变量"。

**82. 作者引文一句话压缩 5 类信息**

- AI：Zhang等[152]进行了一项研究。**该研究的对象是肥胖小鼠，研究持续了12周，采用有氧运动训练。** 研究结果显示血清BCAAs降低。
- 人：**Zhang等[152]对肥胖小鼠进行12周有氧运动训练后发现血清BCAAs降低**。
- 注：一句装下"作者 + 引文 + 研究对象 + 干预时间 + 干预方式 + 主要结果"。机制讨论中文献综述的标准压缩格式。AI 倾向于拆成多句加铺垫词。

**83. 同一研究的双结果一并报告**

- AI：Glynn等[174]在超重人群中进行6个月有氧和抗阻训练，**未观察到血浆BCAAs的变化**。**然而，** 该研究还发现训练**降低了BCAAs分解代谢有毒产物的堆积**。
- 人：Glynn等[174]在超重人群中进行6个月有氧和抗阻训练**没有改变血浆BCAAs，但是降低了BCAAs分解代谢有毒产物的堆积**。
- 注：同一项研究里的阴性 + 阳性结果合在一句报告，用"但是"做内部转折，不拆成两句。一项研究 = 一句话原则。

**84. 文献矛盾的系统化分类**

- AI：以上结论不一致**可能与多种因素有关，包括研究对象、营养状态、运动方式等**。
- 人：推测以上结论不一致的原因可能涉及到**研究对象（人、小鼠、大鼠等）、营养状态（瘦、肥胖、IR状态、病理状态等）、运动干预方案（有氧、抗阻、联合运动等）等方面**。
- 注：把矛盾文献的成因系统分类，每类括号里给具体例子。AI 列因素只给类目（"研究对象、营养状态、运动方式"），不给类内例子，等于没说。规律：每个矛盾因素至少给 2-3 个具体例子。

**85. 概念二分法做哲学化收尾**

- AI：综上所述，循环BCAAs与健康的关系仍需进一步研究。
- 人：**循环BCAAs是健康的正标志还是负标志**，需要考虑研究对象的营养状态，这反映了个性化和精准化运动方案的必要性。
- 注：把矛盾文献的本质升级为概念定义问题（正标志 vs 负标志），不停在"需要进一步研究"。这是博士论文 Discussion 收尾的高级写法：把局部争议提升到概念层。AI 几乎只会用"需要进一步研究"收尾。

---

## How to add to this file

每次润色一篇真实稿件时，挑出 3–5 处最典型的改写，按上面格式追加。三个月内累积 30+ 对，就能用作 in-context examples 直接喂给模型，比抽象规则有效得多。
