# Split a sometimes-legitimate pattern into its own check, don't drop it

Status: accepted (Jeff, 2026-11-27). Issue #231, under #171.

## Context

Proving checks under ADR 0001 keeps turning up a pattern inside a check that is
legitimate in some projects and real in others. DS201's `is not None` was 10 false
positives on home-assistant, while bookwright's hits were true positives: the same
pattern is noise on a library suite and a real failure mode on an agent-written one.
Deleting the pattern rescues the parent check's precision, but throws away a claim
that holds where agents write the tests.

## Decision

When part of a check is legitimate in some projects but is still a real claim, with
its own precision, it is **split**: it becomes its own check, with its own code, kind
and default level, set by its own proof under ADR 0001's kinds and graduation rule.
It is not deleted to rescue the parent's precision.

- **Threshold instead.** When the variation is how much of one claim is too much, the
  check takes a threshold the project sets, not a split: `drill_sergeant_max_act_assert_cycles`
  for DS104 (#228), `drill_sergeant_max_mock_setup` for DS303 (#230).
- **Drop only what has no value.** A pattern is dropped only when it is no claim worth
  making, as DS202's multiply-by-zero rule, which isn't an agent idiom and whose hits
  were all legitimate (#190).
- **One finding per problem.** A split check and its parent never both report one
  problem: one yields to the other (`yields_to`).

A split check is off by default until it is proven, like any new check.

## First application

DS202's `==` / `!=` self-comparison (`x == x`) is split into its own new check, off
by default until it is proven, filed as its own ticket (#190's decisions). DS202
keeps `is` / `is not` on the same bare name and comparisons of literals only.

## Consequences

- The code list grows with narrow checks, some of them off by default for projects
  to opt into.
- Splits are cheaper before 1.0: after it, codes are public and a project's config
  names them. A new check off by default fits ADR 0001's release rule, since a minor
  release may raise it from off to `warn`.
- A check whose precision falls short because of one pattern has three answers, in
  order: a threshold if the pattern is a matter of degree, a split if it is a real
  claim of its own, a drop only if it is neither.

## Prior art

- **Clippy**, **Ruff** and **Error Prone** all ship many narrow lints with per-lint
  defaults, the noisy ones off for projects to opt into.
