# Codex Skills Security Audit (2026-02-27)

## Source
- Official curated registry: `openai/skills` (`skills/.curated`)
- Installer used: `~/.codex/skills/.system/skill-installer/scripts/install-skill-from-github.py`

## Method
- Pre-install static audit for each curated skill:
  - scanned `SKILL.md`
  - scanned files under `scripts/`
- High-risk pattern checks:
  - destructive delete (`rm -rf`)
  - destructive git (`git reset --hard`, `git clean -fd`)
  - pipe-to-shell (`curl | bash`, PowerShell `| iex`)
  - Python shell execution (`subprocess(..., shell=True)`, `os.system`, `eval(`)

## Result
- High-risk findings: **0**
- Skills flagged for manual blocking before install: **0**
- Installed curated skills not previously present: **23**

## Installed Skills
- cloudflare-deploy
- develop-web-game
- figma
- figma-implement-design
- gh-address-comments
- gh-fix-ci
- imagegen
- jupyter-notebook
- linear
- netlify-deploy
- notion-knowledge-capture
- notion-meeting-intelligence
- notion-research-documentation
- notion-spec-to-implementation
- openai-docs
- render-deploy
- security-ownership-map
- security-threat-model
- sentry
- sora
- spreadsheet
- vercel-deploy
- yeet

