# pytest-drill-sergeant

A pytest plugin and CLI that catch the ways AI coding agents write bad tests:
copy-pasted setup, assertions that prove nothing, mocks asserted on instead of
behaviour, skips added to go green, sleeps, and test files too long to follow. It
reports them as findings that fail the run, in the drill-sergeant voice.

**Status:** v1 is being rebuilt from scratch. So far `drill-sergeant check <paths>`
reports tests with no real assertion (DS101), a broad `pytest.raises` with no `match=`
(DS701) and swallowed exceptions (DS702), and exits 1 when it finds any; the pytest
plugin does nothing yet. The plan is the
[v1 spec](https://github.com/jeffrichley/pytest-drill-sergeant/issues/118). Version
0.4 is archived under the tag `archive/2026-11-19/v0.4/main`.

## Development

```sh
just sync           # create .venv with the dev tools
just install-hooks  # pre-commit and commit-msg hooks
just check          # the gate: lint, format, types, dead code, tests
```

## License

MIT
