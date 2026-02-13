# Release Checklist

Use this for both TestPyPI dry-runs and production releases.

## Pre-Release

- [ ] `main` is green in CI (`test`, `lint`, `typecheck`).
- [ ] Working tree is clean.
- [ ] Version is correct and intentional.
- [ ] `README.md` reflects current behavior.
- [ ] `docs/Decision-Log.md` updated for scope-changing decisions.
- [ ] `CHANGELOG`/release notes prepared (if used).

## Local Verification

- [ ] `just verify`
- [ ] `uv run pytest -q`
- [ ] `uv run ruff check src tests`
- [ ] `uv run mypy src tests --config-file=pyproject.toml`

## Build Artifacts

- [ ] `uv build`
- [ ] Inspect `dist/` contents.
- [ ] Optional sanity install from wheel in clean environment.

## TestPyPI (Optional but Recommended)

- [ ] Push test tag (`test-v*`) or trigger test-release workflow.
- [ ] Confirm publish success in GitHub Actions.
- [ ] Install from TestPyPI and run smoke import.

## Production Release

- [ ] Create and push version tag (`v*`).
- [ ] Confirm `release.yml` completed successfully.
- [ ] Verify package visible on PyPI.

## Post-Release

- [ ] Verify README badges and links.
- [ ] Announce release / publish notes.
- [ ] Monitor first CI and install reports after release.
