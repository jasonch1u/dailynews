# Contributing to DailyNews

Thanks for your interest in improving DailyNews! Contributions of all sizes are
welcome — bug reports, new news sources, prompt improvements, and docs.

## Getting started

1. Fork the repo and clone your fork.
2. Set up the project following the [Quick Start](README.md#quick-start) guide.
3. Copy `.env.example` to `.env` and add your own API keys.
4. Run locally with `vercel dev`.

## Development workflow

- Create a feature branch: `git checkout -b feat/my-change`.
- Keep changes focused — one logical change per pull request.
- Follow the existing code style (standard library `logging`, type hints,
  `async`/`await` for I/O).
- If you touch `api/llm_utils.py` or the summarization pipeline, read
  [`AGENTS.md`](AGENTS.md) first — it documents the architectural rules.

## Adding a news source

News scrapers live in `scrapers.py`. Each source should:

- Return a normalized list of `{title, url, source, category}` items.
- Translate non-Chinese titles to Traditional Chinese before returning.
- Fail gracefully (log and return `[]`) so one broken source never blocks the run.

## Pull requests

- Describe **what** changed and **why**.
- Confirm the app still runs locally and there are no Python syntax errors
  (CI runs `python -m compileall` on every PR).
- PRs are automatically reviewed by [Codex](https://developers.openai.com/codex/);
  please address its feedback before requesting human review.

## Reporting bugs

Open an issue using the bug report template. Include repro steps, expected vs.
actual behaviour, and relevant logs (with secrets redacted).

By contributing you agree that your contributions are licensed under the
project's [MIT License](LICENSE).
