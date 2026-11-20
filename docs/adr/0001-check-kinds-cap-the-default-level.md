# Check kinds cap the default level

Status: accepted (Jeff, 2026-11-20). Issue #195, under #171.

## Context

The #140 false-positive review found most checks crying wolf on real suites, and #171
turned off every check not yet proven. That settled whether a check is on, not how
loud it is once on: a long test file and a test that can't fail were both at `fail`,
though only one of them lets a bug through.

## Decision

A check's default level is the lower of two answers.

1. **Its kind sets the highest level it can have.**
   - **Defect:** the test can't catch a bug, cheats, or fails at random. Highest
     level: `fail`.
   - **Smell:** the test works but costs later: hard to read, breaks on harmless
     refactors, duplicated. Highest level: `warn`.
   - **Convention:** a house rule some projects follow. Off unless the project opts
     in.
2. **Its precision decides whether it is on.** A fresh hand-judged sample of real
   suites with zero false positives allows `fail`; under 15% allows `warn`, with the
   remaining cases waived; 15% or more keeps it off. Until a check is proven this way
   it is off.

After 1.0, a minor release may raise a check from off to `warn`; only a major release
raises `warn` to `fail`.

Each `Check` in the registry carries its kind, and a registry test fails when a
check's default level is above its kind's highest. A project may still set any check
to any level in its own config.

## Each check's kind

- **Defect:** DS001, DS101, DS102, DS202, DS301, DS401, DS402, DS403, DS603, DS701,
  DS702, DS801, DS802, DS803
- **Smell:** DS103, DS104, DS105, DS106, DS107, DS201, DS203, DS302, DS303, DS501,
  DS502, DS601, DS602
- **Convention:** DS108, DS901

2026-11-20: DS103 assert-before-act moved from Defect to Smell (#182). It now flags
any act after a test's last assertion, which is either an act nothing checks or
cleanup, and the two can't be told apart structurally, so it is sometimes
legitimate. The split-out check proposed in #208 was folded into it.

## Consequences

- DS106 long-file and DS502 near-duplicate-tests, proven and on at `fail`, move to
  `warn`. Every other smell is off until proven, and can return at `warn` at most.
- DS901 is off, as #194 left it, and stays off whatever its proof; so does DS108.
- A new check, or one whose kind changes, argues its kind in its PR
  (`CODING_STANDARDS.md`).

## Prior art

- **Clippy** sorts lints into groups that set their default levels, and new lints
  start in `nursery`, off by default.
- **Ruff** and **ESLint** ship only near-zero-false-positive bug rules on by default.
- **Pylint**, with everything on, is the noisy counter-example.
