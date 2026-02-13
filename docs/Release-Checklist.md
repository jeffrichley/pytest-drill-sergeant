# Release Checklist

Release flow is split:

- `release-please` auto-opens/updates release PR from conventional commits on `main`.
- Merging that PR creates a GitHub Release and version tag.
- Trigger `release.yml` manually with `release_tag` to publish to PyPI.

## Solo Maintainer Mode (Current)

- Branch protection keeps required CI checks enabled and strict/up-to-date.
- Required approving reviews are set to `0` for single-maintainer operation.
- PR flow is still recommended for traceability, even without a review gate.
- Re-enable `required_approving_review_count = 1` when additional maintainers join.

## Pre-Release

- [ ] `main` is green in CI (`test`, `lint`, `typecheck`).
- [ ] Working tree is clean.
- [ ] `README.md` reflects current behavior.
- [ ] `docs/Decision-Log.md` updated for scope-changing decisions.
- [ ] Commit messages follow conventional style (`feat:`, `fix:`, etc.) for clean release notes.

## Local Verification

- [ ] `just verify`
- [ ] `uv run pytest -q`
- [ ] `uv run ruff check src tests`
- [ ] `uv run mypy src tests --config-file=pyproject.toml`

## Build Artifacts

- [ ] `uv build`
- [ ] Inspect `dist/` contents.
- [ ] Optional sanity install from wheel in clean environment.

## TestPyPI (Optional)

- [ ] Trigger `test-release.yml` manually (or use test tag if retained).
- [ ] Confirm publish success in GitHub Actions.
- [ ] Install from TestPyPI and run smoke import.

## Production Release

- [ ] Confirm `Release Please` has opened/updated the release PR.
- [ ] Confirm release PR from `release-please` is correct (version/changelog).
- [ ] Merge release PR to `main`.
- [ ] Confirm GitHub Release + tag were created by `release-please`.
- [ ] Trigger `Production Release (PyPI)` workflow manually with `release_tag`.
- [ ] Confirm `release.yml` completed successfully.
- [ ] Verify package visible on PyPI.

## Post-Release

- [ ] Verify README badges and links.
- [ ] Announce release / publish notes.
- [ ] Monitor first CI and install reports after release.
