# Coding standards

Read this when **reviewing** a diff, with the ticket and the PR description beside it.
Every rule here is a judgement call: something a person has to weigh against the change
in front of them. A rule a tool can decide lives in the gate (`just check`) instead, and
leaves this file the day the gate learns it.

Hold the **diff** to these rules, not the code around it. A breach is a finding; cite
the rule by its bold name. `stagehand#` numbers are from `jeffrichley/stagehand`, where
these rules started.

## Words

- **The glossary holds everywhere.** `GLOSSARY.md` defines the words. Code, comments,
  docstrings, the README, findings and other user-visible text use each word in its
  glossary sense and no other. A new concept gets its entry in the PR that introduces
  it.
- **A changed rule is changed everywhere it is stated.** When a behaviour change moves
  what a glossary entry or a module docstring says, every other place stating the old
  rule moves in the same PR: docstrings, comments, README, test names, help text,
  explain text and the agent guide. (stagehand#122, stagehand#159, stagehand#161)
- **The voice never costs the fact.** A finding's voice line may be snarky; its found,
  why and fix text is plain, and reads the same with the voice off.

## Code

- **A check knows a thing; it never guesses from a name.** A check decides what a
  variable, parameter or call is only from what the file shows: its imports, an
  assignment traced to its source, pytest's built-in fixtures taken as parameters, or
  its position (a method's first parameter). A name (`mock_db`, `log`, `self`,
  `expected`, a method called `close`) is never evidence. A pattern that is sometimes
  legitimate defaults to `warn` instead of gaining an exception list.
- **A check's kind is argued, not assumed.** A new check, or one whose kind changes,
  says in its PR why it is that kind. Defect means a test it flags can't catch the bug
  or cheats; anything that only costs later is a Smell.
- **One finding per problem.** When two checks report the same problem in a test, the
  more specific one wins, and only while it is enabled.
- **A helper whose job is to refuse is `require_*`.** A new function named for what it
  returns, which then raises for the caller to catch, gets renamed or returns instead.
  (stagehand#151)
- **When drill-sergeant refuses, it says so in one line naming what is missing.** The
  CLI prints the line as it stands. The same condition reads the same wherever it is
  hit, so it is raised in one place and the others call that place. (stagehand#151)
- **One of a thing stays one.** When the glossary says there is one, the code holds one,
  with no list, index or "once there are more" branch ahead of the glossary.
  (stagehand#152)
- **The engine knows nothing of pytest.** Checks, findings and config resolution take
  files and a config and return data; only the plugin imports pytest.
- **A run only reports.** Nothing in a run edits a test file, a config file or any file
  but the cache.
- **A `# noqa` or `# type: ignore` says why it is right here.** One with no reason
  beside it is an unreviewable claim.
- **A dependency arrives with a stated reason.** The PR that adds one says what it buys
  and what it costs.

## Tests

The test rules live in `tests/CLAUDE.md`. Hold every test in the diff to each of them.

## Scope

- **A removed behaviour is named.** When a rewrite drops something the old code did, the
  PR description says so. (stagehand#156)
- **Nothing the spec rules out.** Machine-readable output, scoring, env vars or command
  line flags for configuration, and automatic fixing are out of v1; a diff adding one
  cites the ticket that brought it in.
