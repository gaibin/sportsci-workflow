# 文献管理手册：Zotero 接入、引文域、改稿与交付

目标：把一份 Word 文档（学位论文 / 开题报告 / 期刊稿）的引用做到 **引文可自动更新、文献表自洽、版式能交**。
本文件是流水线说明与踩坑记录；代码在 `sportsci_refs/`，命令见 `sportsci-refs --help`。

## 三条铁律

1. **不编造**：作者、年份、卷期页、DOI，一个都不能凭记忆补。缺就问作者或查原文。
2. **域优先**：碰含域的段落，先想“只改一个 run 够不够”，永远不整段替换、不删除含域标记的段落。
3. **先备份再写回，写完必校验**：`sportsci-refs verify` 任何一项不为 0 就地修，不要说“应该没问题”。

## 阶段 0 · 环境探测

```bash
sportsci-refs status
```

| 情况 | 处理 |
|---|---|
| Zotero 未运行 | 请打开 Zotero 桌面端；Zotero 7 需在 设置 → 高级 勾选“允许此计算机上的其他应用程序与 Zotero 通信” |
| 返回 **502 Bad Gateway** | 本机 HTTP 代理（Clash 等）拦截了 127.0.0.1 的请求，**不是 Zotero 故障**——多半是 Zotero 没开。本工具访问本地接口一律绕过代理，访问 Crossref 等外网接口走代理 |
| Zotero MCP | 会话里**真的出现** Zotero 工具才算连上；“配置了”≠“连上了”。没有就直接用本地 HTTP 接口，不要反复重试 |

配置（`config/local.toml`，已被 git 忽略；模板 `config/local.example.toml`，也可用环境变量）：

| 键 | 环境变量 | 用途 |
|---|---|---|
| `zotero_user_id` | `ZOTERO_USER_ID` | 引文 URI `http://zotero.org/users/<id>/items/<KEY>`；在 zotero.org/settings/keys 查看 |
| `zotero_data_dir` | `ZOTERO_DATA_DIR` | 含 `zotero.sqlite` 的数据目录，用于读取数字 itemID |
| `contact_email` | `SPORTSCI_CONTACT_EMAIL` | 可选，Crossref / OpenAlex 的 polite pool |
| `citation_style` | `ZOTERO_CITATION_STYLE` | 学校要求的 CSL 样式（GB/T 7714-2015 数字制或学校指定版本） |

本地 HTTP 接口能力（Zotero 7 实测）：搜索、取 CSL（`?format=csljson` 返回**数组**取 `[0]`）、列分类、`/connector/saveItems` 写入（落在 Zotero 界面里**当前选中**的分类）。
`DELETE / PATCH / PUT` 一律 **501**——接口删不掉、改不了条目。**不要往真实文库写“测试条目”探测权限。**

数字 itemID 不在接口里：`ZoteroLocal.item_ids()` 把 `zotero.sqlite` 连同 `-wal` / `-journal` **拷到临时目录**再读（只拷主文件会丢最近的修改），读完即删。
**绝不直接改 `zotero.sqlite`**：会绕过 `deletedItems` / `syncDeleteLog`，下次同步可能让条目“复活”或搞乱同步状态。

## 阶段 1 · 检索候选、核验 DOI、入库

```bash
sportsci-refs search "resistance training type 2 diabetes HbA1c" --n 15 --year-from 2015 -o 候选.md
sportsci-refs check-doi 候选DOI.txt -o doi核验.md          # 也接受 .ris / CSL .json / GB/T 文本列表
```

- 检索结果是**候选**，不是文献表。“该引哪篇”必须由作者本人读过原文后决定。
- 已自动剔除 Crossref 混入的同行评审记录（`Review for …`、DOI 含 `/review`、`type=peer-review`），这类条目从题名上看不出真假。
- Crossref 的相关性排序弱于 Europe PMC / OpenAlex；中文检索词只在 Crossref / OpenAlex 有效。中文期刊常无 DOI，在知网 / 万方人工核对。
- DOI 核验状态：`OK` / `EXISTS`（有 DOI 无题名可比对，仍可能指向别的论文）/ **`MISMATCH`**（真实 DOI 挂在错误文献上，最隐蔽）/ `404` / `NODOI`。
- 核验只说明“文献存在且元数据一致”，**不说明它支持正文那句话**。

入库：优先用 Zotero 浏览器插件或“按标识符添加”（魔术棒）输入 DOI；已有文献表时见阶段 2。

## 阶段 2 · 已有文献表 → Zotero

稿子里常常已经有一份手打的 GB/T 7714 文献表：

```bash
sportsci-refs parse 文献表.txt -o 文献表            # -> 文献表.ris + 文献表.json，并列出解析不确定的条目
#   Zotero：新建分类并选中 → 文件 → 导入 → 文献表.ris
sportsci-refs check-doi 文献表.ris -o doi核验.md
sportsci-refs match 文献表.txt -c "<分类名>" -o zotero_match.json   # DOI 优先，其次题名相似度 ≥ 0.90；< 0.97 的列入人工复核
```

## 阶段 3 · 纯文本 [n] → Zotero 引文域

```bash
sportsci-refs fieldify 论文.docx -m zotero_match.json --superscript --dry-run   # 先干跑看会转换多少
sportsci-refs fieldify 论文.docx -m zotero_match.json --superscript -o 论文_Zotero.docx
```

然后在 Word 中：Zotero → Document Preferences 选学校要求的样式 → **Refresh**（Zotero 会重排编号、重写文献表并补制表符）。

一个引文域 = 5 个 run：`fldChar(begin)` → `instrText(" ADDIN ZOTERO_ITEM CSL_CITATION {json} ")` → `fldChar(separate)` → 显示 run `[12]` → `fldChar(end)`。
文献表是**一个** `ZOTERO_BIBL` 域，跨越所有条目段落。

实现上的取舍（都来自真实翻车）：

| 坑 | 后果 | 本工具的做法 |
|---|---|---|
| 用 ElementTree 读写整个 `document.xml` 后手动还原根标签 | 内联命名空间（`<a:graphic xmlns:a=…>`）被提到根部、未用声明被删 → Word 报“文件已损坏” | `fieldify` 只对单个 run 做字符串拼接；`fieldedit` 用 lxml，保留全部命名空间声明；其余部件逐字节复制 |
| 整段重写含 `fldChar` / `instrText` 的段落 | 静默销毁引文（文字看起来没问题）。一段 70 个 run 里往往只有 25 个是普通文字，45 个属于域 | 只改域外 run；域内一律不碰 |
| 删除含域标记的段落 | 文献表域失去 end，整表损坏 | 不删；`save()` 在域计数变化时拒绝写出 |
| 文献表跨几十个段落，只看段落内的 begin / end | 把文献表条目当成普通文字去改，下次 Refresh 被整体覆盖 | 全文档跟踪域嵌套深度，文献表内的段落识别为“域内” |
| 引用被 Word 拆成多个 run（`[` `12` `]`） | 拼接替换会误伤 | 不转换，报告到 `not_converted`，人工在 Word 里重打后再转 |
| 正文“图 X / 表 X”是 `REF` 交叉引用域 | 纯文本里看不到，整段替换会抹掉 | 同上：只改 run |
| 批量删除用下标 | 删一个后下标全错位 | 用元素引用 |
| 锚点文字出现多次 | 引文插到错误位置，且不报错 | 锚点必须唯一，否则拒绝 |

编号规则：显示编号 = 该文献在全文**首次出现**的顺序；同一处多篇升序 `[10,57]`，≥ 3 篇连续用 en dash `[12–14]`；
**引文放在句末标点之前**：`……呈下降趋势[16]。`

## 阶段 3b · 改已经转换过的文档（改稿）

文档已经有引文域之后，还要改正文、挪引文位置——这时**不能**用 Word 之外的普通文本替换。

```bash
sportsci-refs edit 论文_Zotero.docx -r "下降趋势=>降低趋势" -r "显著提高=>明显提高" -o 论文_v2.docx
sportsci-refs renumber 论文_v2.docx -o 论文_v3.docx          # 正文显示编号 = 首次出现顺序，载荷同步
```

- `edit` 只改域外的普通文字，一处匹配可以跨相邻的几个普通 run；只改真正变化的那一段，匹配范围内的加粗、斜体因此保留。
  匹配不会跨过引文域（“趋势”+`[16]`+“。”不会被当成“趋势。”）。
- `renumber` 同时改显示 run 和 `plainCitation` / `formattedCitation`；只改其中一处会让校验报“载荷与显示不一致”。
  **文献表不会被重排**：改完后在 Word 里点 Zotero → Refresh。
- 写 Python 时用 `sportsci_refs.fieldedit.FieldDoc`：`replace`、`insert_after_anchor` / `insert_before_anchor`（移动引文组）、
  `detach`、`set_group_display`、`refresh_numbers`、`append_text_run`。`save()` 拒绝覆盖原文件，拒绝写出域计数变化的文档。

## 阶段 4 · 校验（交付前必跑）

```bash
sportsci-refs verify 论文_Zotero.docx -o 引文校验.md
sportsci-refs compare 论文.docx 论文_Zotero.docx        # 只有 word/document.xml 应该变化；域序列是否一致
```

| 检查项 | 期望 |
|---|---|
| `fldChar` begin / separate / end | 三者相等 |
| 载荷 JSON 解析失败、citationID 重复、域显示为空 | 0 |
| `plainCitation` ≠ 屏幕显示 | 0 |
| 显示编号 ≠ 首次出现顺序 | 0 |
| 引文在句末标点之后、同段相邻两域之间无正文 | 0 |
| 文献表编号不连续、编号后缺制表符、条目与引文题名错位 | 0 |
| 引而未列 / 列而未引 | 0 |

**校验脚本也会误报**：en dash 与连字符（已归一化）、`instrText` 被拆成多个 run（已拼接）、`formattedCitation` 里 en dash 被存成 `\uc0\u8211{}`（不比对该字段）。
报告“N 处不一致”之前，先人工展开第一条看一眼。`fieldify` 刚生成、尚未在 Word 里 Refresh 的文档，“缺制表符”和“题名错位”属预期。

## 阶段 5 · 交付与排版

1. **备份**：另存一份改动前的副本，核对 MD5（`docx_fields.diagnose` 给出 md5）。
2. 写回用复制覆盖，不要“先删再写”；写回前关闭 Word（残留的隐藏 WINWORD 进程会锁文件）。
3. Word 复核：域数、页数、图数、域结果为空的个数；导出 PDF 逐页看。
4. **Word 重存会静默改文件**（新增 numbering.xml、规范化 document.xml、清 proofState）。重存后复查：`docProps/custom.xml` 字节不变（Zotero 样式与偏好在里面）、域计数相等、文献表条目的制表符仍在。

Word COM 复核（PowerShell，只读打开）：

```powershell
$w = New-Object -ComObject Word.Application; $w.Visible = $false; $w.DisplayAlerts = 0
$d = $w.Documents.Open($path, $false, $true)
"Fields=$($d.Fields.Count) Pages=$($d.ComputeStatistics(2))"      # 域类型码：81 = ADDIN（Zotero），12 = SEQ，3 = QUOTE
$d.Close(0); $w.Quit()                                            # Quit 不带参数
[System.Runtime.InteropServices.Marshal]::ReleaseComObject($d) | Out-Null
[System.Runtime.InteropServices.Marshal]::ReleaseComObject($w) | Out-Null
[GC]::Collect()
```

### 开题报告的“每页方框”

部分学校模板把正文放在封面表格最后一行的单元格里，方框来自行级 `w:tblPrEx` 的表格属性例外。Word 认，**腾讯文档、WPS 网页版等在线渲染器不认**——“方框没了”通常是渲染器问题，不是文档损坏。
修法：给正文单元格补一份同规格的 `w:tcBorders`（`tblPrEx` 原样保留）；不要改成整表 `w:tblBorders`（封面上面几行会多出竖线）。
逐页检查：导出 PDF 后 `sportsci-refs frames 论文.pdf`（需 `pip install pymupdf`）。缺口以**版心底边**（页高 − 下边距）为基准，不是页边；
封面无框、末页短收口属正常。中间页缺口多因图表放不下被推到下一页，属版式改动，**先告知作者、取得同意再改**。

## 多台电脑 / 云盘同步协作

- 换机器前在 Zotero 点一次同步；确认目标分类条目数正确。
- **库不完整时不要点 Refresh**：缺失的条目会变成 `[?]`，编号整体错位。
- 另一台机器打开后“引用看着乱”的常见原因：打开的是旧副本；该机 Zotero 没运行或没装 Word 插件（显示原始域代码）；该机文库未同步完整；文档设置了延迟更新。前三条都不是文档坏了，别急着改文档。
- 删条目只能在 Zotero 界面里做（移到回收站 → 从回收站删除），然后同步。
