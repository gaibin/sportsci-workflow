"""Regression tests for scripts/ai_trace_check.py.

Run from the skill directory:

    python -m unittest discover tests -v

The before/after corpus test parses references/before-after.md. Every human
rewrite there must stay free of general hits. If a rule change flags one, fix
the rule and keep the sample. The author's personal rules (dash, semicolon,
contrast frame) are stricter than published prose and are tested separately
in AuthorRules. AI-version recall is printed and held to a floor so
that rule changes cannot silently lose coverage.
"""

from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from ai_trace_check import scan_text, split_paragraphs  # noqa: E402

CJK = re.compile(r"[一-鿿]")

# Raise these when new rules catch more AI samples; never lower them.
RECALL_FLOOR = {"en": 3, "zh": 12}


def hits(text: str, lang: str = "auto") -> list:
    return [h for h in scan_text(text, lang) if h.severity == "hit"]


def warns(text: str, lang: str = "auto") -> list:
    return [h for h in scan_text(text, lang) if h.severity == "warn"]


def rules(text: str, lang: str = "auto") -> list[str]:
    return [h.rule for h in hits(text, lang)]


def general_rules(text: str, lang: str = "auto") -> list[str]:
    """Hits excluding the author's personal rules (dash, semicolon, contrast
    frame), which published human prose breaks routinely."""
    return [h.rule for h in hits(text, lang) if not h.personal]


def load_pairs() -> list[tuple[int, str, str, str]]:
    """(line number, 'AI' or '人', lang, text) for each sample line."""
    rows = []
    path = ROOT / "references" / "before-after.md"
    for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        m = re.match(r"\s*- (AI|人)[^：]*：(.*)", line)
        if not m:
            continue
        body = m.group(2).replace("**", "").strip()
        rows.append((n, m.group(1), "zh" if CJK.search(body) else "en", body))
    return rows


class KnownAIEnglish(unittest.TestCase):
    CASES = [
        ("We delve into the mechanisms of fatigue.", "delve"),
        ("Cortisol plays a key role in recovery.", "plays a key role"),
        ("These findings offer valuable insights for coaches.", "valuable insights"),
        ("This work paves the way for future trials.", "paves the way"),
        ("Further research is warranted.", "further research is warranted"),
        ("A growing body of evidence supports HIIT.", "a growing body of evidence"),
        ("Sprint time fell by 3.1%, highlighting the value of the program.", "trailing -ing"),
        ("Load was high. Notably, injuries rose.", "signposting adverb"),
        ("Load rose. This suggests that recovery matters.", "bare 'This'"),
        ("HIIT not only improved VO2max but also reduced resting heart rate.", "not only"),
        ("The benefit is not merely aesthetic but metabolic.", "not X but Y"),
        ("These results may potentially suggest an association.", "stacked hedging"),
        ("Training improved sprint time. Moreover, it improved jumps. "
         "Furthermore, it reduced soreness.", "stacked Moreover"),
        ("First, we tested. Second, we trained. Finally, we retested.", "mechanical enumeration"),
        ("High-intensity training — a popular method — improves VO2max.", "dash"),
        ("Sample size was TODO participants.", "placeholder"),
    ]

    def test_each_case_is_flagged(self):
        for text, expected in self.CASES:
            with self.subTest(text=text):
                self.assertTrue(any(expected.lower() in r.lower() for r in rules(text, "en")),
                                f"expected '{expected}' in {rules(text, 'en')}")

    def test_emphasis_density(self):
        three = "Recovery is crucial. Sleep is a key factor. Nutrition is essential."
        two = "Recovery is crucial. Sleep is a key factor. Nutrition also matters."
        self.assertTrue(any("emphasis density" in r for r in rules(three, "en")))
        self.assertFalse(any("emphasis density" in r for r in rules(two, "en")))

    def test_enumeration_across_paragraphs(self):
        text = "First, participants were tested.\n\nSecond, they trained for 8 weeks."
        self.assertIn("mechanical enumeration across paragraphs", rules(text, "en"))

    def test_single_finally_is_fine(self):
        self.assertEqual(rules("Finally, all variables were re-measured.", "en"), [])


class KnownHumanEnglish(unittest.TestCase):
    CLEAN = [
        # technical collocations containing listed words
        "We used robust standard errors to account for clustering within teams.",
        "Cluster-robust variance estimators were applied.",
        "Critical power was estimated from three time trials.",
        "Key performance indicators were coded from match video.",
        "Essential amino acids were provided after each session.",
        # human rewrites from human-voice-en.md
        "Sprint time decreased by 3.1%. This exceeds the smallest worthwhile change for this squad (1.8%).",
        "This delay in CK clearance suggests that 48 h was not enough recovery after eccentric work.",
        "The effect was larger in women (d = 0.71 vs 0.32), who also started with lower baseline strength.",
        "Participants completed the Yo-Yo Intermittent Recovery Test Level 1 on an indoor surface at the "
        "same time of day, at least 72 h after their last match. Two players did not finish.",
        # en-dash in ranges and compounds
        "Intensity was set at 60–80% of HRmax and the muscle–bone unit was assessed.",
    ]

    def test_no_hits(self):
        for text in self.CLEAN:
            with self.subTest(text=text):
                self.assertEqual(rules(text, "en"), [])

    def test_epistemic_trailing_clause_warns(self):
        text = "That study reported similar hazards, suggesting that a higher ACWR is associated with lower risk."
        self.assertEqual(rules(text, "en"), [])
        self.assertTrue(any("suggesting" in h.rule for h in warns(text, "en")))

    def test_context_words_warn_not_hit(self):
        text = "RT, when incorporated into a comprehensive fitness program, improves cardiovascular function."
        self.assertEqual(rules(text, "en"), [])
        self.assertTrue(any("comprehensive" in h.rule for h in warns(text, "en")))


class Chinese(unittest.TestCase):
    def test_residue_and_placeholders(self):
        for text, expected in [
            ("课题组已完成预实验。", "课题组"),
            ("你需要先确认基线血糖是否稳定。", "你"),
            ("具体剂量待商定后确定。", "待商定"),
            ("样本量为 XXX 人。", "XXX"),
        ]:
            with self.subTest(text=text):
                self.assertTrue(any(expected in r for r in rules(text, "zh")), rules(text, "zh"))

    def test_weightlifting_term_not_residue(self):
        self.assertEqual(rules("受试者完成 3 组挺举，组间休息 3 min。", "zh"), [])

    def test_first_person_group_matched_once(self):
        found = [r for r in rules("我们组前期研究发现血乳酸升高。", "zh") if "对话残留" in r]
        self.assertEqual(found, ["对话残留: '我们组'"])

    def test_punctuation_only_paragraph(self):
        self.assertIn("punctuation-only paragraph", rules("正文结束。\n\n。\n\n下一段。", "zh"))

    def test_markdown_rule_is_not_punctuation_paragraph(self):
        self.assertEqual(rules("正文结束。\n\n---\n\n下一段。", "zh"), [])

    def test_de_counted_per_clause(self):
        ai = "长期高强度的训练对运动员的心血管系统的适应性的影响是显著的。"
        self.assertTrue(any("的的不休" in r for r in rules(ai, "zh")))
        human = ("传统心理技能训练是帮助运动员取得优异成绩的重要保证，且两种训练的差异对比"
                 "是未来研究的方向之一，可以分门别类的帮助运动员应对压力。")
        self.assertFalse(any("的的不休" in r for r in rules(human, "zh")))



class AuthorRules(unittest.TestCase):
    """Zero tolerance in running prose: dashes, semicolons, contrast frames."""

    FLAGGED = [
        ("en", "HIIT — a popular method — improves VO2max.", "dash"),
        ("en", "HIIT – a popular method – improves VO2max.", "dash"),
        ("en", "HIIT -- a popular method -- improves VO2max.", "dash"),
        ("en", "HIIT - a popular method - improves VO2max.", "dash"),
        ("zh", "高强度间歇训练——一种流行方法——可提高最大摄氧量。", "dash"),
        ("en", "Strength rose; power did not.", "semicolon"),
        ("zh", "本研究采用交叉设计；受试者完成四个条件。", "semicolon"),
        ("zh", "存在两个问题：1）未设对照组；2）未探究延续效果。", "semicolon"),
        ("en", "The benefit is not aesthetic but metabolic.", "not X but Y"),
        ("en", "It is not the volume, but the intensity, that matters.", "not X but Y"),
        ("en", "Gains came not because of volume but because of intensity.", "not X but Y"),
        ("zh", "差异不是来自时长，而是来自剂量设计。", "不是"),
        ("zh", "问题不是时长，是剂量。", "不是"),
        ("zh", "这并非时长问题，而是剂量问题。", "不是"),
        ("zh", "训练不再是单纯的体能储备，而是比赛表现的基础。", "不是"),
        ("zh", "与其说是时长问题，不如说是剂量问题。", "不是"),
        ("zh", "这不只是说方法有局限，而是指出整个领域尚未解决。", "不是"),
    ]

    ALLOWED = [
        ("en", "Intensity was 60–80% of HRmax in weeks 1 – 4 and the muscle–bone unit was assessed."),
        ("en", "Results were pooled (refs 12; 15) and compared (t = 2.1, P = 0.04; t = 2.5, P = 0.02)."),
        ("en", "The difference was not statistically significant but showed a trend (P = 0.06)."),
        ("zh", "男童学习日和双休日 LPA、MVPA 时间均显著高于女童（t=2.10，P<0.05；t=2.45，P<0.05；t=2.3，P<0.05）。"),
        ("zh", "受试者不是全部完成了测试。"),
        ("zh", "正文结束。\n\n---\n\n下一段。"),
    ]

    def test_flagged_and_marked_personal(self):
        for lang, text, expected in self.FLAGGED:
            with self.subTest(text=text):
                found = [h for h in hits(text, lang) if expected in h.rule]
                self.assertTrue(found, rules(text, lang))
                self.assertTrue(all(h.personal for h in found))

    def test_allowed(self):
        for lang, text in self.ALLOWED:
            with self.subTest(text=text):
                self.assertEqual([h.rule for h in hits(text, lang) if h.personal], [])

    def test_every_semicolon_reported(self):
        text = "本研究采用随机交叉设计；受试者完成四个条件；每个条件间隔 7 天。"
        self.assertEqual(sum("semicolon" in r for r in rules(text, "zh")), 2)

    def test_rather_than_opener_warns(self):
        text = "Rather than volume, intensity drove the gains."
        self.assertEqual(rules(text, "en"), [])
        self.assertTrue(any("Rather than" in h.rule for h in warns(text, "en")))


class Paragraphs(unittest.TestCase):
    def test_one_paragraph_per_line_without_blank_lines(self):
        text = "Moreover, strength rose.\nFurthermore, power rose."
        self.assertEqual(len(split_paragraphs(text, "en")), 2)
        self.assertNotIn("stacked Moreover/Furthermore", rules(text, "en"))

    def test_blank_lines_join_wrapped_lines(self):
        text = "Moreover, strength rose.\nFurthermore, power rose.\n\nNext paragraph."
        self.assertEqual(len(split_paragraphs(text, "en")), 2)
        self.assertIn("stacked Moreover/Furthermore", rules(text, "en"))

    def test_mixed_language_auto(self):
        text = "本研究纳入 24 名运动员，测定 VO2max 与血乳酸。\n\nWe delve into fatigue."
        langs = [p.lang for p in split_paragraphs(text, "auto")]
        self.assertEqual(langs, ["zh", "en"])
        self.assertTrue(any("delve" in r for r in rules(text)))

    def test_line_numbers_point_to_source(self):
        text = "Clean sentence here.\nStill clean.\n\nWe delve into fatigue."
        self.assertEqual([h.line for h in hits(text, "en")], [4])


class BeforeAfterCorpus(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = load_pairs()

    def test_corpus_loaded(self):
        self.assertGreater(len(self.rows), 100)

    def test_human_versions_have_no_hits(self):
        for n, who, lang, body in self.rows:
            if who != "人":
                continue
            with self.subTest(line=n):
                self.assertEqual(general_rules(body, lang), [], f"before-after.md:{n} {body[:80]}")

    def test_ai_recall_floor(self):
        for lang in ("en", "zh"):
            ai = [r for r in self.rows if r[1] == "AI" and r[2] == lang]
            caught = sum(bool(rules(body, lang)) for _, _, _, body in ai)
            print(f"\n  before-after AI recall [{lang}]: {caught}/{len(ai)}", file=sys.stderr)
            self.assertGreaterEqual(caught, RECALL_FLOOR[lang])


class VoiceSampleCorpus(unittest.TestCase):
    """Quoted journal paragraphs in references/voice-samples/ are human text.

    Published prose occasionally uses a cliché the skill still wants removed.
    Those are listed here by file and line rather than weakening the rule.
    """

    KNOWN = {
        ("psychology-zh.md", 173): {"AI phrase: 'paradigm shift'"},
    }

    def test_quoted_paragraphs_have_no_unexpected_hits(self):
        folder = ROOT / "references" / "voice-samples"
        if not folder.is_dir():
            self.skipTest("references/voice-samples/ is local-only and not part of the public repository")
        files = sorted(folder.glob("*.md"))
        self.assertTrue(files)
        for path in files:
            for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                if not line.startswith(">"):
                    continue
                found = set(general_rules(line[1:].strip())) - self.KNOWN.get((path.name, n), set())
                with self.subTest(file=path.name, line=n):
                    self.assertEqual(found, set(), f"{path.name}:{n}")


if __name__ == "__main__":
    unittest.main()
