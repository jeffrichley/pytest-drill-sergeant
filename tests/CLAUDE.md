# Tests

The rules every test is written and reviewed against. A breach is a review finding;
cite the rule by its bold name. They follow the handbook's
[Testing](https://github.com/jeffrichley/handbook/blob/main/testing.md) page, whose two
house rules hold here:

- **Never test third-party code.**
- **Every layer alone with its neighbours mocked or faked, then integration on top.**
  "Mocked or faked" leans faked: prefer a fake of a port we own, and mock only when the
  call itself is the behaviour.

## This project's rules

- **Drive a public seam.** A test goes through one of three seams and observes what a
  user could: the engine (findings as data), the CLI (`drill-sergeant` through the `cli`
  fixture: exit code, output, files written) or the plugin (real pytest runs through
  `pytester`). Internal functions stay free to change.
- **A check is proven through the corpus.** Each check has bad and good corpus files
  with inline `# expect: DS###` markers; one parametrized test requires the exact set of
  (code, line) per file. No unit test per check.
- **Assert on meaning, not prose.** Compare findings as data (code and line), never as
  rendered text. When text is the fact, match the shortest fragment that identifies it
  (a code, a command name), never a sentence. Only the golden-output test reads whole
  output.
- **The golden suite stays small and fixed.** The golden-output test runs the CLI over
  `tests/golden/suite/`, never the corpus, so a new check or corpus file leaves
  `tests/golden/check.txt` alone. It changes only when the report changes or a check
  fires on the suite's files: run `just golden` and review `git diff tests/golden`.
- **A refusal is pinned by its identity.** Assert a refusal's exit code or error kind;
  its one-line message is for people.
- **The environment is pinned once.** `conftest.py` fixes colour, terminal width and CI
  detection for the whole suite, so output reads the same on a laptop and in CI. A test
  that needs a different environment sets it with `monkeypatch`, inside that test.
- **Fixtures first.** Look in `conftest.py` before writing setup. Setup a second test
  needs becomes a fixture in `conftest.py`. Temp dirs come from `tmp_path`, env changes
  from `monkeypatch`. A test body holds only what makes its case different.
  (stagehand#159)
- **Every spec line gets a test, the "unchanged" lines too.** A ticket sentence that
  says what must happen, or what must still happen, is pinned by a test that would fail
  without it. A test covers what its name says, and its name is its docstring.
  (stagehand#156, stagehand#161)
- **Our own suite passes our own checks.** Once the plugin reports findings, this suite
  runs with it on and stays clean.
