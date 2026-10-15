# sport-science-writing

A portable agent skill for writing, polishing, and translating sport science manuscripts (journal papers, theses, reviews) in Chinese and English, with built-in statistics and Nature-style figure generation.

Designed to work with **any agent CLI** that can read a markdown instruction file and execute Python:

- Claude Code
- OpenAI Codex CLI
- Cursor / Cline / Continue
- Aider
- Custom agents built on the Anthropic / OpenAI SDKs

## What it does

- Polishes Chinese or English sport science prose so it does **not** read like AI output (strips em-dashes used as asides, mechanical "首先/其次", "delve/leverage/crucial", overused parentheses, name-and-restate paragraph shapes, etc.)
- Drafts and restructures sections of empirical papers (IMRaD), narrative/systematic reviews, and BS/MS/PhD theses
- Translates between Chinese and English in the natural register of the target language, not word-for-word
- Audits research logic from the research question through methods, results, discussion, and conclusion
- Runs descriptive and inferential statistics (t-test, ANOVA, correlation, effect sizes, reliability) and writes the Results paragraph for you
- Produces Nature-quality figures (box+jitter, violin+strip, bar+error, scatter+regression, forest plot) with sane defaults
- Formats references in APA 7, Vancouver, or GB/T 7714 (国标)

It will **not** fabricate data, citations, p-values, or DOIs. If something is missing it asks.

## Install

Drop the `sport-science-writing/` directory anywhere your agent can read it.

### Claude Code

```bash
# project-scoped
mv sport-science-writing .claude/skills/

# or user-scoped (all projects)
mv sport-science-writing ~/.claude/skills/
```

Claude Code auto-discovers `SKILL.md` files in those locations.

### Codex / Cursor / other agents

Point your agent at `sport-science-writing/SKILL.md` as system context, or symlink it into whatever instruction directory the tool uses (`.cursor/rules/`, `AGENTS.md` include, etc.). The skill is plain markdown plus Python, with no Claude-specific APIs.

### Python dependencies (for scripts/)

```bash
pip install pandas numpy scipy statsmodels pingouin matplotlib openpyxl
```

## Usage

Just talk to the agent. Examples:

- "帮我把这段方法部分润色一下" → polish + AI-trace scrub
- "Translate the discussion to English, target journal is *MSSE*" → translate + journal-style adjustments
- "Run a paired t-test on `pre_post.xlsx` (column A = pre, B = post) and write the Results paragraph in Chinese" → stats + auto-drafted paragraph
- "Make a Nature-style box plot comparing VO2max across three training groups" → figure with proper defaults
- "这篇综述的引言读起来太 AI 了，重写" → full rewrite, stripping AI tells

## Layout

```
sport-science-writing/
├── SKILL.md                    entry point — agent reads this first
├── README.md                   this file
├── references/                 loaded on demand by the agent
│   ├── ai-traces-zh.md
│   ├── ai-traces-en.md
│   ├── human-voice-en.md
│   ├── before-after.md
│   ├── anti-detector.md
│   ├── voice-samples/          optional, local only (not distributed: real journal text)
│   ├── nature-figures.md
│   ├── citations.md
│   ├── article-structures.md
│   ├── logic-check.md
│   └── sport-stats.md
├── scripts/                    runnable helpers
│   ├── stats.py
│   ├── nature_plot.py
│   └── ai_trace_check.py
├── tests/
│   └── test_ai_trace_check.py  regression tests for the trace checker
└── assets/
    └── matplotlibrc            Nature-style matplotlib defaults
```

## Tests

The trace checker is tested against the human rewrites in `references/before-after.md` and, when you keep a local `references/voice-samples/` folder, the journal paragraphs in it: none of them may produce a hit. The author's personal rules (dashes, semicolons, contrast frames) are excluded from that check because published prose uses them routinely. They have their own test cases. Run after changing any rule:

```bash
python -m unittest discover tests -v
```

No extra dependencies. pytest also works if installed.

## License

MIT. Use, fork, modify freely. Contributions welcome.
