# pytest-drill-sergeant

A pytest plugin and CLI that catch the ways AI coding agents write bad tests. It reports them as findings that fail the run, in the drill-sergeant voice.

Follow the house handbook, the private repo [`jeffrichley/handbook`](https://github.com/jeffrichley/handbook). Before changing the gate or project setup (`pyproject.toml`, `justfile`, hooks, CI), read its [Python project standard](https://github.com/jeffrichley/handbook/blob/main/python-standard.md). Before writing or reviewing a test, read [Testing](https://github.com/jeffrichley/handbook/blob/main/testing.md). Before working with the tracker or labels, or planning from a map or spec down to tickets, read [How projects are run](https://github.com/jeffrichley/handbook/blob/main/running-projects.md). Read a page from the local handbook clone, or with `gh api repos/jeffrichley/handbook/contents/<page> -H "Accept: application/vnd.github.raw"`. The rules below are either this project's own or word-for-word copies of handbook rules that an agent needs every session.

- Ticket start: claim it on GitHub before any work, with `gh issue edit <issue> --add-assignee @me`. Already assigned to someone else? Stop and ask. Then branch off main.
- Ticket done: verify before anything leaves the machine: `just check` green, every acceptance criterion checked against what was built, and the code-review skill run over the branch with its findings fixed or reported. Then push and open a PR for Jeff to review that closes the ticket with a Conventional Commits title (`fix: ...`), and wait for its checks with `gh pr checks <pr> --watch`; on "no checks reported", run it again. A job still queued after five minutes has a stuck runner: recreate it as the handbook's `infrastructure.md` says, then watch again. Checks red: fix, push, watch again. Checks green: stop and report the PR with its full URL, so Jeff can click straight to it. Merging is Jeff's.
- Renovate: the central Renovate run merges its own grouped non-major pull request once CI is green, the one exception to "Merging is Jeff's".

## Agent skills

### Issue tracker

Issues and specs are GitHub issues on `jeffrichley/pytest-drill-sergeant`, worked with the `gh` CLI. See `docs/agents/issue-tracker.md`.

### Triage labels

The five canonical roles under their default names: `needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`. See `docs/agents/triage-labels.md`.

### Domain docs

Single-context: one `GLOSSARY.md` and `docs/adr/` at the repo root. Code, tests, issues and output use each glossary word in its glossary sense. See `docs/agents/domain.md`.
