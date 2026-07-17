# Contributing to skills

Thanks for your interest. Contributions of all sizes are welcome — a
typo fix is just as useful as a feature. This document describes how
to get from "I want to help" to "my change is merged".

## Filing issues

- Search [open issues](https://github.com/kevinlin/skills/issues)
  before opening a new one.
- Use the bug-report or feature-request template.
- For security vulnerabilities, do **not** open a public issue — see
  [`SECURITY.md`](./SECURITY.md).

## Setting up locally

```sh
git clone https://github.com/kevinlin/skills.git
cd skills
# This repo is a collection of self-contained agent skills. There is no
# root build system — each skill ships its own scripts (Python, stdlib
# only) under its own directory.
```

## Running tests

```sh
# There is no top-level test suite. Skills that ship helper scripts run
# them directly, e.g.:
#   python agent-insights/scripts/agent_insights.py --help
# Test the specific skill you touched.
```

Please exercise the skill you changed before opening a PR.

## Submitting a pull request

1. Fork the repo and create a topic branch from `main`.
2. Make your change. Keep commits focused; one concern per commit is
   easier to review than a kitchen-sink commit.
3. Use [Conventional Commits](https://www.conventionalcommits.org)
   for the PR title (e.g. `feat: add X`, `fix: handle Y`,
   `docs: explain Z`). Squash-merge will use the PR title as the
   commit subject.
4. Fill out the PR template — the "why" matters more than the "what".
5. When you change a skill's behaviour, bump `metadata.version` in its
   `SKILL.md` **and** its entry in `versions.json` (they must stay in
   sync).
6. Wait for CI to go green and address review feedback.

## Code of Conduct

Participation in this project is governed by the
[Contributor Covenant](./CODE_OF_CONDUCT.md). By contributing you
agree to abide by it.

## Licensing

By submitting a contribution you agree that it will be licensed under
the same terms as the project itself (see [`LICENSE`](./LICENSE)).
