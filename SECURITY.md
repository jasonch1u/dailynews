# Security Policy

## Reporting a Vulnerability

If you discover a security vulnerability in DailyNews, please **do not** open a
public issue. Instead, report it privately via GitHub's
[private vulnerability reporting](https://github.com/jasonch1u/dailynews/security/advisories/new).

Please include:

- A description of the vulnerability and its impact
- Steps to reproduce
- Any suggested remediation

You can expect an initial response within a few days. Once the issue is
confirmed and fixed, we will coordinate disclosure.

## Secrets & API Keys

This project relies on several third-party API keys (Supabase, Gemini, FRED).
All keys are loaded from environment variables and must **never** be committed.
`.env` is git-ignored; use `.env.example` as a template.
