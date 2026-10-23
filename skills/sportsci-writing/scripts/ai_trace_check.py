#!/usr/bin/env python3
"""
Scan text for AI-generated traces in sport science writing.

Detects formulaic patterns in English and Chinese prose and prints findings
with line numbers and suggested rewrites. The rules mirror
references/ai-traces-en.md and references/ai-traces-zh.md.

Findings come in two severities:

  hit   a pattern the reference files say must be rewritten
  warn  context-dependent; read the sentence and decide

Hits marked "author rule" come from the author's own zero-tolerance list:
dashes as asides, semicolons in running prose (zh ； and en ;), and contrast
frames (不是……而是……, "not X but Y"). Published human prose uses these
often, so they are stricter than a general AI-trace rule. Semicolons inside
brackets, such as grouped statistics （t=2.10，P<0.05；t=2.45，P<0.05）, are
allowed.

Language is detected per paragraph in auto mode, so a Chinese thesis with an
English abstract gets both rule sets. Paragraphs are separated by blank lines;
if the file has no blank lines at all (typical of text exported from Word),
each line is one paragraph.

Usage
-----
python ai_trace_check.py manuscript.md
python ai_trace_check.py manuscript.txt --lang zh
python ai_trace_check.py manuscript.md --stats      # per-paragraph rhythm metrics
python ai_trace_check.py manuscript.md --no-warn    # hits only
echo "your text here" | python ai_trace_check.py -

Exit code is the number of hits (0 = clean, capped at 125), so the script can
be used in pre-commit hooks or CI. Warnings do not count.
"""

from __future__ import annotations

import argparse
import re
import statistics
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Hit:
    line: int
    col: int
    rule: str
    text: str
    suggestion: str
    severity: str = "hit"
    personal: bool = False  # from the author's zero-tolerance list


# ---------------------------------------------------------------------------
# English rules (references/ai-traces-en.md)
# ---------------------------------------------------------------------------

# Always rewrite.
EN_AI_PHRASES = [
    "delve", "delves", "delved", "delving",
    "tapestry", "landscape", "realm",
    "leverage", "leverages", "leveraging", "leveraged",
    "underscore", "underscores", "underscored", "underscoring",
    "intricate", "nuanced", "myriad", "plethora",
    "shed light on", "sheds light on", "shedding light on",
    "paradigm shift", "game-changer", "game changer",
    "holistic", "holistically",
    "it is worth noting that", "it should be noted that",
    "it is important to note that", "it is crucial to note that",
    # newer-generation tells (ai-traces-en.md §3.1)
    "highlights the importance of", "highlighting the importance of",
    "highlight the importance of",
    "plays a key role", "plays a crucial role", "plays a pivotal role",
    "plays a vital role", "plays a critical role",
    "play a key role", "play a crucial role", "play a pivotal role",
    "play a vital role", "play a critical role",
    "a growing body of evidence", "valuable insights",
    "paves the way", "paving the way", "pave the way",
    "significant step forward", "promising avenue", "new avenues",
    "further research is warranted", "the interplay between",
    "multifaceted", "elucidate", "elucidates", "elucidating", "elucidated",
    "a nuanced understanding", "a deeper understanding",
    "stands as a testament", "serves as a testament",
    "has gained increasing attention", "have gained increasing attention",
]

# Context-dependent: accurate in some sentences, generated filler in others.
EN_WARN_WORDS = [
    "comprehensive", "robust", "novel",
    "foster", "fosters", "fostering", "fostered",
    "navigate", "navigates", "navigating", "navigated",
]

# Counted by density, not presence (before-after.md #15).
EN_EMPHASIS = ["crucial", "critical", "key", "essential", "pivotal", "vital"]
EMPHASIS_WINDOW = 200   # words
EMPHASIS_LIMIT = 3      # this many inside one window = rewrite

# Standard technical terms that contain words from the lists above.
EN_WHITELIST = [
    r"(?:cluster|heteroscedasticity|heteroskedasticity)-robust",
    r"robust (?:standard errors?|regression|variance(?: estimators?)?|estimators?|"
    r"sandwich|covariance|SEs?|methods?)",
    r"comprehensive metabolic panel",
    r"landscape (?:orientation|format|mode)",
    r"critical (?:power|speed|velocity|appraisal|care|values?|difference|"
    r"illness|region|limb ischemia)",
    r"key performance indicators?",
    r"essential (?:amino acids?|fatty acids?|hypertension|tremor)",
    r"novel coronavirus",
]

ENUMERATORS = ("First", "Second", "Third", "Fourth", "Finally")
ADDITIVES = ("Moreover", "Furthermore", "Additionally", "In addition")
SIGNPOSTS = ("Notably", "Importantly", "Interestingly", "Crucially", "Remarkably")
SUMMARIZERS = ("Overall", "Taken together", "In summary", "In conclusion")
# Connectors that carry a real logical relation. They count toward the
# connector-density metric but are never flagged on their own.
LOGICAL = ("However", "Therefore", "Thus", "Hence", "In contrast",
           "Conversely", "Nevertheless", "Similarly", "Consequently",
           "For example", "For instance", "Accordingly", "Likewise")

# ", highlighting the importance of ..." inflates a result; always rewrite.
EN_TRAILING_ING = re.compile(
    r",\s+(highlighting|underscoring|emphasizing|emphasising|reinforcing|"
    r"demonstrating)\b", re.IGNORECASE)
# ", suggesting that ..." also appears in published human prose; check the
# hedge matches the evidence and that the clause is not doing a sentence's job.
EN_TRAILING_ING_EPISTEMIC = re.compile(
    r",\s+(suggesting|indicating|reflecting|implying)\b", re.IGNORECASE)
EN_BARE_THIS = re.compile(
    r"^(This|These)\s+(suggests?|indicates?|shows?|demonstrates?|highlights?|"
    r"implies|imply|means|mean|underscores?|reveals?|confirms?)\b")
# Author rule: no "not X but Y" frames in any form.
EN_CONTRAST = re.compile(
    r"\bnot (?:merely|just|simply)\b[^.;]{1,80}\bbut\b|\brather than merely\b|"
    # "is not X but Y" (result statements such as "was not significant but" excluded)
    r"\b(?:is|are|was|were|lies|lie|comes?|came|stems?|stemmed)\s+not\s+"
    r"(?!only\b|significant|statistically\b)[^,.;:!?]{1,50}?\s+but\s+(?!also\b)|"
    # "It is not X, but Y, that ..."
    r"\bit(?: is|'s| was) not\b[^.;!?]{1,60}?,? but\b|"
    r"\bnot because\b[^.;!?]{1,60}\bbut because\b",
    re.IGNORECASE)
EN_RATHER_THAN = re.compile(r"(?:^|(?<=[.!?]\s))Rather than\b")
EN_NOT_ONLY = re.compile(r"\bnot only\b[^.;]{1,80}\bbut (?:also|it also)\b",
                         re.IGNORECASE)
EN_HEDGE = re.compile(
    r"\b(?:may|might|could) (?:potentially|possibly)\b|"
    r"\bmay suggest that there (?:could|may|might)\b", re.IGNORECASE)
# §5.3 self-undermining and §5.4 project-diary structure: warns, the sentence decides.
EN_SELF_UNDERMINING = ["unfortunately", "regrettably", "admittedly",
                       "we must acknowledge", "it must be acknowledged", "we must admit",
                       "we have to admit", "serious limitations", "severe limitations"]
EN_DIARY = re.compile(r"\bwe first\b[^.!?]{1,80}\bthen\b[^.!?]{1,80}\b(?:finally|lastly)\b",
                      re.IGNORECASE)
EN_TRICOLON = re.compile(
    r"\b[A-Za-z][\w-]*(?: [\w-]+){0,2}, [A-Za-z][\w-]*(?: [\w-]+){0,2},? and [A-Za-z][\w-]*")
EN_SENTENCE_BOUNDARY = re.compile(r"(?<=[.!?])\s+(?=[A-Z])")
EN_WORD = re.compile(r"[A-Za-z][A-Za-z'-]*|\d+(?:\.\d+)?")

UNIFORM_MIN_SENTENCES = 5
UNIFORM_CV = 0.25        # coefficient of variation of sentence length
CONNECTOR_SHARE = 1 / 3  # max share of sentences opening with a connector

# ---------------------------------------------------------------------------
# Chinese rules (references/ai-traces-zh.md)
# ---------------------------------------------------------------------------

ZH_AI_WORDS = [
    "深入探讨", "深入研究", "全面分析", "全方位",
    "至关重要", "极其重要", "具有重要意义", "具有深远意义",
    "不容忽视", "值得注意的是", "值得一提的是",
    "综上所述", "总而言之",
    "为.{0,8}提供了新的视角",
    "助力", "赋能",
    "在.{1,15}领域",
    # 学究化骨架词（§5）
    "解读框架", "分析框架", "理论框架",
    ".{1,4}学层面", ".{1,4}层面的",
    "应用证据", "实证证据", "经验证据",
    ".{1,6}同样突出", ".{1,6}同样值得关注",
    "走在.{1,8}之前",
    "呈现出.{1,15}态势", "呈现出.{1,15}趋势",
    "议题", "范式",
    "在.{1,15}背景下",
    "从.{1,15}视角出发",
]

ZH_DE_LIMIT = 3  # "的" per clause

ZH_TRANSITIONS = ["首先", "其次", "再者", "此外", "另外", "最后", "与此同时"]

# §7 对话残留与编辑痕迹. Longest alternatives first so "我们组" wins over "我们".
# "挺" is left out on purpose: 挺举 is a weightlifting term.
ZH_RESIDUE = [
    "下面我们", "需要注意的是", "值得关注的是", "请看", "见下文",
    "咱们", "你们", "你", "您",
    "说白了", "搞定", "其实", "差不多",
    "本研究团队", "我们组", "课题组", "我认为", "我们", "笔者", "本人",
    "经导师", "与导师", "待商定", "再议", "待讨论", "后续沟通",
    "待补", "上一版", "初稿",
]
PLACEHOLDERS = re.compile(r"TODO|TBD|XXX|【[^】]*】|□□|\?\?|\[citation needed\]")

# §6.3 自我削弱（防御性写作）. Hits are self-deprecating frames. Warns need context:
# "效果有限" can be a fair summary of a small, precise effect.
ZH_SELF_UNDERMINING = ["遗憾的是", "令人遗憾", "很遗憾", "不得不承认", "必须承认",
                       "存在严重不足", "存在严重缺陷", "差强人意", "不尽如人意"]
ZH_SELF_UNDERMINING_WARN = ["效果有限", "作用有限", "明显落后", "仍落后于",
                            "应谨慎(?:理解|看待|解读)(?:这些|上述|该|本研究的?)?结果"]
# §6.4 工作汇报式叙述. A warn: a Methods procedure ("先热身，然后……，最后拉伸") is legitimate.
ZH_DIARY = re.compile(r"先[^。！？]{1,40}(?:然后|随后|接着)[^。！？]{1,40}(?:最后|最终)")

# Author rule: every occurrence is a hit (§4.5).
ZH_CONTRAST = re.compile(
    r"不(?:只|仅|单|光)?是[^。！？]{1,30}而是|不是[^。！？，]{1,20}[，,]\s*是|"
    r"并非[^。！？]{1,30}而是|不再是[^。！？]{1,30}而是|"
    r"与其说[^。！？]{1,30}不如说|不在于[^。！？]{1,30}而在于")

# Author rule: dashes used as asides. Numeric ranges (60–80%, 1 – 4) and
# unspaced compounds (muscle–bone) are fine.
DASH = re.compile(
    r"—+|―+|"
    r"(?<=[^\s\d]) [–-] (?=[^\s\d])|"
    r"(?<=\w)--(?=\w)|(?<=\w) -- (?=\w)")

# Brackets are masked before counting semicolons, so grouped statistics and
# citation lists keep theirs.
BRACKETS = re.compile(r"（[^（）]*）|\([^()]*\)|\[[^\[\]]*\]")

PUNCT_ONLY = re.compile(r"^[\s。．.，,；;：:、！!？?…—\-]+$")
MD_RULE = re.compile(r"^\s*([-*_])(?:\s*\1){2,}\s*$")
CJK = re.compile(r"[一-鿿]")


# ---------------------------------------------------------------------------
# Paragraph model
# ---------------------------------------------------------------------------

class Paragraph:
    """Consecutive non-blank lines joined into one string, with offsets
    mapped back to (line, col) in the source."""

    def __init__(self, rows: list[tuple[int, str]], lang: str):
        self.rows = rows
        self.lang = lang
        joiner = "" if lang == "zh" else " "
        self.text = ""
        self._spans = []  # (start offset in self.text, line no, col offset)
        for n, raw in rows:
            stripped = raw.strip()
            if self.text:
                self.text += joiner
            self._spans.append((len(self.text), n, len(raw) - len(raw.lstrip())))
            self.text += stripped
        self.first_line = rows[0][0]
        self.opener: str | None = None  # first sentence connector (English)

    def loc(self, offset: int) -> tuple[int, int]:
        line, col0, start = self._spans[0][1], self._spans[0][2], 0
        for s, n, c in self._spans:
            if s <= offset:
                start, line, col0 = s, n, c
        return line, col0 + offset - start

    def excerpt(self, offset: int = 0) -> str:
        line, _ = self.loc(offset)
        for n, raw in self.rows:
            if n == line:
                return raw.strip()[:100]
        return self.text[:100]


def _is_block_start(line: str) -> bool:
    s = line.lstrip()
    return bool(re.match(r"(#{1,6}\s|[-*+]\s|\d+[.)]\s|\|)", s))


def split_paragraphs(text: str, lang: str) -> list[Paragraph]:
    groups: list[list[tuple[int, str]]] = []
    cur: list[tuple[int, str]] = []
    # Text exported from Word has one paragraph per line and no blank lines.
    # Only treat consecutive lines as one paragraph when blank lines exist.
    one_per_line = not re.search(r"\S[^\n]*\n[ \t]*\n[ \t]*\S", text)
    for i, line in enumerate(text.splitlines(), 1):
        if one_per_line and cur:
            groups.append(cur)
            cur = []
        if not line.strip():
            if cur:
                groups.append(cur)
                cur = []
            continue
        if cur and _is_block_start(line):
            groups.append(cur)
            cur = []
        cur.append((i, line))
        if _is_block_start(line) and line.lstrip().startswith(("#", "|")):
            groups.append(cur)
            cur = []
    if cur:
        groups.append(cur)

    paras = []
    for g in groups:
        joined = "".join(r for _, r in g)
        if lang == "auto":
            cjk = len(CJK.findall(joined))
            latin = len(re.findall(r"[A-Za-z]", joined))
            # Chinese prose carries Latin abbreviations (VO2max, CGM); an English
            # paragraph rarely carries more than a stray Chinese term.
            plang = "zh" if cjk and cjk * 4 >= latin else "en"
        else:
            plang = lang
        paras.append(Paragraph(g, plang))
    return paras


def _mask(text: str, patterns: list[str]) -> str:
    for p in patterns:
        text = re.sub(p, lambda m: " " * len(m.group()), text, flags=re.IGNORECASE)
    return text


def _en_sentences(text: str) -> list[tuple[int, str]]:
    out, start = [], 0
    for m in EN_SENTENCE_BOUNDARY.finditer(text):
        out.append((start, text[start:m.start()]))
        start = m.end()
    if text[start:].strip():
        out.append((start, text[start:]))
    return out


def _opener(sentence: str) -> str | None:
    s = sentence.lstrip("*_\"'( ")
    for group in (ENUMERATORS, ADDITIVES, SIGNPOSTS, SUMMARIZERS, LOGICAL):
        for w in group:
            if s.startswith(w + ",") or (w in LOGICAL and s.startswith(w + " ")):
                return w
    return None


# ---------------------------------------------------------------------------
# Scanners
# ---------------------------------------------------------------------------

def _scan_common(p: Paragraph, hits: list[Hit]):
    for m in DASH.finditer(p.text):
        line, col = p.loc(m.start())
        hits.append(Hit(line, col, f"dash '{m.group().strip()}'", p.excerpt(m.start()),
                        "Use a comma, a colon, or two sentences. 改用逗号、冒号或拆成两句。",
                        personal=True))
    body = BRACKETS.sub(lambda m: " " * len(m.group()), p.text)
    for m in re.finditer(r"[；;]", body):
        line, col = p.loc(m.start())
        hits.append(Hit(line, col, f"semicolon '{m.group()}' in running prose", p.excerpt(m.start()),
                        "Split into two sentences. 用句号切分（括号内统计量除外）。",
                        personal=True))
    for m in PLACEHOLDERS.finditer(p.text):
        line, col = p.loc(m.start())
        hits.append(Hit(line, col, f"placeholder: '{m.group()}'", p.excerpt(m.start()),
                        "Fill in or delete before submission."))
    if PUNCT_ONLY.match(p.text) and not MD_RULE.match(p.text):
        hits.append(Hit(p.first_line, 0, "punctuation-only paragraph", p.text[:20],
                        "Delete the paragraph."))


def _scan_en(p: Paragraph, hits: list[Hit], tokens: list[tuple[str, Paragraph, int]]):
    text = _mask(p.text, EN_WHITELIST)

    for w in EN_AI_PHRASES:
        for m in re.finditer(rf"\b{re.escape(w)}\b", text, re.IGNORECASE):
            line, col = p.loc(m.start())
            hits.append(Hit(line, col, f"AI phrase: '{w}'", p.excerpt(m.start()),
                            f"Rewrite the sentence around the specific finding; do not just swap '{w}'."))
    for w in EN_WARN_WORDS:
        for m in re.finditer(rf"\b{re.escape(w)}\b", text, re.IGNORECASE):
            line, col = p.loc(m.start())
            hits.append(Hit(line, col, f"check word: '{w}'", p.excerpt(m.start()),
                            "Keep only if literally accurate and supported by the data.",
                            "warn"))

    for w in EN_SELF_UNDERMINING:
        for m in re.finditer(rf"\b{re.escape(w)}\b", text, re.IGNORECASE):
            line, col = p.loc(m.start())
            hits.append(Hit(line, col, f"self-undermining: '{w}'", p.excerpt(m.start()),
                            "Drop the judgement, keep the number and its CI (§5.3). Limitations stay in their paragraph.",
                            "warn"))
    for m in EN_DIARY.finditer(text):
        line, col = p.loc(m.start())
        hits.append(Hit(line, col, "project-diary structure", p.excerpt(m.start()),
                        "In Introduction/Discussion: problem, gap, approach, evidence (§5.4). Ignore in a Methods procedure.",
                        "warn"))

    for m in EN_TRAILING_ING.finditer(text):
        line, col = p.loc(m.start())
        hits.append(Hit(line, col, f"trailing -ing clause: '{m.group(1)}'", p.excerpt(m.start()),
                        "Split into its own sentence with a subject, or give the evidence."))
    for m in EN_TRAILING_ING_EPISTEMIC.finditer(text):
        line, col = p.loc(m.start())
        hits.append(Hit(line, col, f"trailing -ing clause: '{m.group(1)}'", p.excerpt(m.start()),
                        "Fine once; if frequent, give the inference its own sentence.", "warn"))
    for rx, rule, tip in (
        (EN_NOT_ONLY, "'not only ... but also'", "Use two sentences or a simple 'and'."),
        (EN_HEDGE, "stacked hedging", "One hedge per claim."),
    ):
        for m in rx.finditer(text):
            line, col = p.loc(m.start())
            hits.append(Hit(line, col, rule, p.excerpt(m.start()), tip))
    for m in EN_CONTRAST.finditer(text):
        line, col = p.loc(m.start())
        hits.append(Hit(line, col, "'not X but Y' contrast frame", p.excerpt(m.start()),
                        "State Y directly.", personal=True))
    for m in EN_RATHER_THAN.finditer(text):
        line, col = p.loc(m.start())
        hits.append(Hit(line, col, "'Rather than X, Y' opener", p.excerpt(m.start()),
                        "Often a disguised contrast frame; state Y directly.", "warn", personal=True))

    sentences = _en_sentences(text)
    openers = []
    for off, s in sentences:
        lead = len(s) - len(s.lstrip())
        o = _opener(s)
        openers.append(o)
        line, col = p.loc(off + lead)
        if o in SIGNPOSTS:
            hits.append(Hit(line, col, f"signposting adverb: '{o}'", p.excerpt(off + lead),
                            "Delete the adverb; give the reason instead."))
        elif o in SUMMARIZERS:
            hits.append(Hit(line, col, f"summary opener: '{o}'", p.excerpt(off + lead),
                            "Allowed once per Discussion; otherwise end on new information.",
                            "warn"))
        if EN_BARE_THIS.match(s.lstrip()):
            hits.append(Hit(line, col, "bare 'This' as subject", p.excerpt(off + lead),
                            "Give 'This' a noun: 'This increase suggests...'."))

    if sum(o in ADDITIVES for o in openers) >= 2:
        hits.append(Hit(p.first_line, 0, "stacked Moreover/Furthermore", p.excerpt(),
                        "Never two additive connectors in one paragraph; link by content."))
    if sum(o in ENUMERATORS for o in openers) >= 2:
        hits.append(Hit(p.first_line, 0, "mechanical enumeration", p.excerpt(),
                        "Rewrite without First/Second/Finally."))
    if len(sentences) >= 4:
        share = sum(o is not None for o in openers) / len(sentences)
        if share > CONNECTOR_SHARE:
            hits.append(Hit(p.first_line, 0, f"connector density {share:.0%}", p.excerpt(),
                            "Start more sentences with their subject.", "warn"))
    tricolons = sum(1 for _, s in sentences if EN_TRICOLON.search(s))
    if tricolons >= 2:
        hits.append(Hit(p.first_line, 0, f"{tricolons} tricolons in one paragraph", p.excerpt(),
                        "Let list length follow the content.", "warn"))
    lengths = [len(EN_WORD.findall(s)) for _, s in sentences]
    if len(lengths) >= UNIFORM_MIN_SENTENCES:
        mean = statistics.mean(lengths)
        cv = statistics.stdev(lengths) / mean if mean else 0
        if cv < UNIFORM_CV:
            hits.append(Hit(p.first_line, 0, f"uniform sentence length (CV {cv:.2f})", p.excerpt(),
                            "Short sentences for key points, longer for method detail.", "warn"))

    for m in EN_WORD.finditer(text):
        tokens.append((m.group().lower(), p, m.start()))

    p.opener = openers[0] if openers else None


def _scan_zh(p: Paragraph, hits: list[Hit]):
    text = p.text
    for w in ZH_AI_WORDS:
        for m in re.finditer(w, text):
            line, col = p.loc(m.start())
            hits.append(Hit(line, col, f"AI 词: '{m.group()}'", p.excerpt(m.start()),
                            f"删除或用动词重写 '{m.group()}'。"))
    stripped = text.lstrip("*_ ")
    for w in ZH_TRANSITIONS:
        if stripped.startswith(w):
            hits.append(Hit(p.first_line, 0, f"机械分点: '{w}'", p.excerpt(),
                            "改写为自然过渡，或合并到上一句。"))
    # Counted per clause: long human sentences reach 4+ "的" in total but
    # rarely 3 inside one clause; generated noun chains do.
    for m in re.finditer(r"[^。！？，；：,;:]+", text):
        n_de = m.group().count("的")
        if n_de >= ZH_DE_LIMIT:
            line, col = p.loc(m.start())
            hits.append(Hit(line, col, f"的的不休 (分句内 {n_de} 个 '的')",
                            m.group().strip()[:100], "删除修饰性 '的'，重构句子。"))
    if re.search(r"不仅.{1,40}而且", text) or re.search(r"既.{1,30}又", text):
        hits.append(Hit(p.first_line, 0, "对仗句式", p.excerpt(), "拆成两句或改用并列。"))
    for m in re.finditer(r"（([^）]{2,40})）", text):
        inside = m.group(1)
        if (CJK.search(inside) and not re.search(r"[=<>]|\d", inside)
                and "VO" not in inside):
            line, col = p.loc(m.start())
            hits.append(Hit(line, col, "括号补充说明", p.excerpt(m.start()),
                            "把括号内容并入句子或删除。", "warn"))

    # 正文分号由 _scan_common 处理（§1.5）。统计量括号本身不宜在一段里出现多个。
    stat_brackets = [m for m in BRACKETS.finditer(text)
                     if "；" in m.group() and re.search(r"[PpFtr]\s*[=<>]", m.group())]
    if len(stat_brackets) >= 2:
        line, col = p.loc(stat_brackets[1].start())
        hits.append(Hit(line, col, f"统计量分号括号 {len(stat_brackets)} 处", p.excerpt(stat_brackets[1].start()),
                        "一段内这类括号不宜多个。", "warn"))

    for m in ZH_CONTRAST.finditer(text):
        line, col = p.loc(m.start())
        hits.append(Hit(line, col, "「不是……而是……」", p.excerpt(m.start()),
                        "直接陈述 B（§4.5）。", personal=True))

    for w in ZH_SELF_UNDERMINING:
        for m in re.finditer(w, text):
            line, col = p.loc(m.start())
            hits.append(Hit(line, col, f"自我削弱: '{m.group()}'", p.excerpt(m.start()),
                            "删掉评价，留下数字和置信区间（§6.3）。局限照常写在局限段。"))
    for w in ZH_SELF_UNDERMINING_WARN:
        for m in re.finditer(w, text):
            line, col = p.loc(m.start())
            hits.append(Hit(line, col, f"自我削弱?: '{m.group()}'", p.excerpt(m.start()),
                            "是对效应量的如实概括就保留，是替读者下的负面判断就删（§6.3）。", "warn"))
    for m in ZH_DIARY.finditer(text):
        line, col = p.loc(m.start())
        hits.append(Hit(line, col, "工作汇报式叙述", p.excerpt(m.start()),
                        "引言和讨论改成问题、缺口、做法、证据（§6.4）。方法部分描述操作步骤时忽略。", "warn"))

    residue = re.compile("|".join(map(re.escape, ZH_RESIDUE)))
    for m in residue.finditer(text):
        line, col = p.loc(m.start())
        hits.append(Hit(line, col, f"对话残留: '{m.group()}'", p.excerpt(m.start()),
                        "论文正文必须为 0，看上下文后改写（§7）。"))


def scan_text(text: str, lang: str = "auto") -> list[Hit]:
    hits: list[Hit] = []
    tokens: list[tuple[str, Paragraph, int]] = []
    paras = split_paragraphs(text, lang)

    for p in paras:
        _scan_common(p, hits)
        if p.lang == "en":
            _scan_en(p, hits, tokens)
        else:
            _scan_zh(p, hits)

    # First, / Second, opening consecutive English paragraphs
    en_paras = [p for p in paras if p.lang == "en"]
    for a, b in zip(en_paras, en_paras[1:]):
        if a.opener in ENUMERATORS and b.opener in ENUMERATORS:
            hits.append(Hit(b.first_line, 0, "mechanical enumeration across paragraphs",
                            f"line {a.first_line} and line {b.first_line}",
                            "Rewrite without First/Second/Finally."))

    # Emphasis-word density over a sliding window of words
    idx = [i for i, (w, _, _) in enumerate(tokens) if w in EN_EMPHASIS]
    i = 0
    while i < len(idx):
        j = i
        while j + 1 < len(idx) and idx[j + 1] - idx[i] < EMPHASIS_WINDOW:
            j += 1
        if j - i + 1 >= EMPHASIS_LIMIT:
            _, p, off = tokens[idx[i]]
            line, col = p.loc(off)
            words = ", ".join(tokens[k][0] for k in idx[i:j + 1])
            hits.append(Hit(line, col, f"emphasis density: {j - i + 1} in {EMPHASIS_WINDOW} words",
                            words, "One emphasis word is fine; rewrite the rest."))
            i = j + 1
        else:
            i += 1

    hits.sort(key=lambda h: (h.line, h.col))
    return hits


def paragraph_stats(text: str, lang: str = "auto") -> list[dict]:
    out = []
    for p in split_paragraphs(text, lang):
        if p.lang == "en":
            sents = [s for _, s in _en_sentences(p.text)]
            lengths = [len(EN_WORD.findall(s)) for s in sents]
            unit = "words"
            openers = sum(_opener(s) is not None for s in sents)
        else:
            sents = [s for s in re.split(r"[。！？]", p.text) if s.strip()]
            lengths = [len(s) for s in sents]
            unit = "chars"
            openers = None
        if not lengths:
            continue
        mean = statistics.mean(lengths)
        sd = statistics.stdev(lengths) if len(lengths) > 1 else 0.0
        out.append({"line": p.first_line, "lang": p.lang, "sentences": len(lengths),
                    "mean": mean, "sd": sd, "cv": sd / mean if mean else 0.0,
                    "unit": unit, "connector_openers": openers})
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("file", help="path to text file, or '-' for stdin")
    ap.add_argument("--lang", default="auto", choices=["auto", "en", "zh"])
    ap.add_argument("--no-warn", action="store_true", help="print hits only")
    ap.add_argument("--stats", action="store_true", help="print per-paragraph sentence-length metrics")
    args = ap.parse_args()

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if args.file == "-":
        text = sys.stdin.read()
    else:
        text = Path(args.file).read_text(encoding="utf-8")

    hits = scan_text(text, args.lang)
    n_hit = sum(h.severity == "hit" for h in hits)
    n_warn = len(hits) - n_hit
    shown = [h for h in hits if h.severity == "hit" or not args.no_warn]

    if args.stats:
        print("Paragraph rhythm (line / lang / sentences / mean ± SD / CV / connector openers):")
        for s in paragraph_stats(text, args.lang):
            conn = "" if s["connector_openers"] is None else f"  openers {s['connector_openers']}"
            print(f"  line {s['line']:>4} {s['lang']}  n={s['sentences']:<3} "
                  f"{s['mean']:.1f} ± {s['sd']:.1f} {s['unit']}  CV {s['cv']:.2f}{conn}")
        print()

    if not shown:
        print("Clean: no AI traces detected." if not hits else
              f"No hits. {n_warn} warning(s) hidden by --no-warn.")
        sys.exit(0)

    n_personal = sum(h.severity == "hit" and h.personal for h in hits)
    print(f"{n_hit} hit(s) ({n_personal} from author rules), {n_warn} warning(s):\n")
    for h in shown:
        tag = "HIT " if h.severity == "hit" else "warn"
        who = " (author rule)" if h.personal else ""
        print(f"  line {h.line}: {tag} [{h.rule}]{who}")
        print(f"    > {h.text}")
        print(f"    -> {h.suggestion}\n")

    sys.exit(min(n_hit, 125))


if __name__ == "__main__":
    main()
