# sportsci-refs

**把 Word 论文里手打的 `[12]` 变成 Zotero 能自动刷新的引文域——之后改稿、重新编号、校验，都不会把它弄坏。**

[English](README.md)

![从手打 [n] 的草稿，到 Zotero 能自动刷新的引文](assets/pipeline_zh.png)

大多数文献工具只做到"导出一个列表"。真正麻烦的是之后：Word 里已经有引文域，你要改一句话、挪一个引文、修编号——
一次"选中整段重打"，就会悄无声息地把这一段里的所有引文毁掉。`sportsci-refs` 把 Word 的引文域当成它本来的样子来处理，
并且用机器检查来验收，而不是"看着没问题"。

- **检索与核验**：从 Crossref、Europe PMC、OpenAlex 检索候选（剔除同行评审记录、按 DOI 去重）；每个 DOI 在 Crossref 上解析并比对题名——
  "真实存在的 DOI 挂在错误的论文上"会被报为 `MISMATCH`。
- **手打列表 → Zotero**：把手打的 GB/T 7714 文献表解析成 RIS / CSL-JSON，导入后按 DOI、再按题名匹配到 Zotero 分类。
- **`[n]` → Zotero 引文域**：纯文本引用变成真正的 `ADDIN ZOTERO_ITEM` 域，文献表变成一个文献表域。
- **域安全改稿**：替换文字、把引文挪到句号前、按首次出现顺序重新编号——只有域外的普通文字会变；
  文献表即使起止标记在别的段落里，也会被识别为"在域内"。
- **13 项机检**（`verify`）：标记配对、载荷 JSON、显示与载荷一致、编号 = 首次出现顺序、引文在标点前、文献表编号/制表符/题名对应、引而未列、列而未引。
- **GB/T 7714-2015** 顺序编码制文献表生成（不用 Zotero 时），中英文条目均可。

## 快速开始

```bash
git clone https://github.com/gaibin/sportsci-refs.git
cd sportsci-refs
pip install -e .

sportsci-refs status                                    # Zotero 是否可达（需要 Zotero 7 正在运行）
sportsci-refs parse 文献表.txt -o 文献表                # 手打的 GB/T 7714 列表 -> 文献表.ris + 文献表.json
sportsci-refs check-doi 文献表.ris -o doi核验.md        # OK / EXISTS / MISMATCH / 404 / NODOI
#   Zotero：新建分类并选中 → 文件 → 导入 → 文献表.ris
sportsci-refs match 文献表.txt -c "我的论文" -o zotero_match.json
sportsci-refs fieldify 论文.docx -m zotero_match.json --superscript -o 论文_Zotero.docx
#   Word：Zotero → Document Preferences → 选学校要求的样式 → Refresh
sportsci-refs verify 论文_Zotero.docx -o 校验报告.md    # 每一项必须为 0
```

之后改稿：

```bash
sportsci-refs edit 论文_Zotero.docx -r "下降趋势=>降低趋势" -o v2.docx
sportsci-refs renumber v2.docx -o v3.docx               # 再到 Word 里点 Zotero → Refresh 重排文献表
sportsci-refs compare 论文_Zotero.docx v3.docx          # 只有 word/document.xml 应该变化
```

本机设置（Zotero 用户 ID、数据目录、联系邮箱）写在 `config/local.toml`（复制 `config/local.example.toml`，已被 git 忽略）或环境变量里。

## 为什么这样做

| 常见错误 | 后果 | 本工具的做法 |
|---|---|---|
| 把一个段落"删掉所有 run、再追加一个" | 引文无声消失；一段 70 个 run 里往往只有 25 个是普通文字 | 只改域外的 run |
| 用会提升内联命名空间的方式读写 `document.xml` | Word 报"文件已损坏"（图片在段内声明 `xmlns:a`） | 字符串拼接或 lxml，其余部件逐字节复制 |
| 把文献表当普通文字 | 改动在下次 Refresh 时被整体覆盖 | 全文档跟踪域的嵌套深度 |
| 锚点文字出现两次 | 引文插到错误的句子，且不报错 | 锚点必须唯一，否则拒绝 |
| 校验脚本报"37 处不一致" | 你去修 37 个并不存在的问题（en dash / 连字符、`instrText` 被拆分、RTF 编码的破折号） | 比较前先归一化这些误报 |
| 访问 `127.0.0.1:23119` 返回 502 | 看起来像 Zotero 坏了，实际是本机代理在应答——Zotero 没开 | 本地接口绕过代理，外网接口走代理；`status` 会解释 |

完整手册（含 Word COM 复核、开题报告方框模板、多机协作）：[`reference/ZOTERO_PLAYBOOK.md`](reference/ZOTERO_PLAYBOOK.md)。

## 作为 AI 技能使用

`SKILL.md` 给出流水线、铁律和检查项：

```bash
git clone https://github.com/gaibin/sportsci-refs.git ~/.claude/skills/sportsci-refs
pip install -e ~/.claude/skills/sportsci-refs
```

## 适用范围与限制

- 测试环境是 Windows + Word + Zotero 7；文档编辑本身是纯 OOXML 操作，不需要装 Word。
- Zotero 本地接口以读为主（搜索、取 CSL、列分类），**不能删除或修改条目**，删条目请在 Zotero 界面里做。
- 文献表的重排和补制表符由 **Word 里的 Zotero → Refresh** 完成，不是本工具。
- DOI 核验只证明"文献存在、元数据一致"，**不证明**它支持被引用的那句话。
- 被 Word 拆成多个 run 的引用（`[`、`12`、`]`）只报告，不转换。

## 开发

```bash
pip install -e ".[dev]"
python -m pytest -q          # 离线：不联网、不需要 Zotero 在运行
```

## 许可

MIT，见 [LICENSE](LICENSE)。
