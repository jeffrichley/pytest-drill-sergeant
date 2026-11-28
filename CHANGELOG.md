# Changelog

## [1.1.0-alpha.1](https://github.com/jeffrichley/pytest-drill-sergeant/compare/pytest-drill-sergeant-v1.0.0-alpha.1...pytest-drill-sergeant-v1.1.0-alpha.1) (2026-11-28)


### Features

* add just try to run the checkout on another project's tests ([#206](https://github.com/jeffrichley/pytest-drill-sergeant/issues/206)) ([293d8df](https://github.com/jeffrichley/pytest-drill-sergeant/commit/293d8df3af615488c4d6876d6a3b05a350d8877b))
* check kinds set the highest default level ([#196](https://github.com/jeffrichley/pytest-drill-sergeant/issues/196)) ([7ff5d5e](https://github.com/jeffrichley/pytest-drill-sergeant/commit/7ff5d5e65a3b61570a65db20a2bd2c5bfcf5a893))
* explain, agent guide and DS602 assertion libraries ([#156](https://github.com/jeffrichley/pytest-drill-sergeant/issues/156)) ([88d5a46](https://github.com/jeffrichley/pytest-drill-sergeant/commit/88d5a46c2058c0be8fbfbdf0cf66531389c7ee7e))
* turn off by default every check not yet proven ([#194](https://github.com/jeffrichley/pytest-drill-sergeant/issues/194)) ([f2c6aa3](https://github.com/jeffrichley/pytest-drill-sergeant/commit/f2c6aa358b41127902ecbbc8360020fcf17efb5e))


### Bug Fixes

* bump the project's version in uv.lock on release PRs ([#223](https://github.com/jeffrichley/pytest-drill-sergeant/issues/223)) ([3af7ca3](https://github.com/jeffrichley/pytest-drill-sergeant/commit/3af7ca3970a153a4ec8f06380259374c037bbabe))
* compare release versions as PEP 440 in the publish check ([#154](https://github.com/jeffrichley/pytest-drill-sergeant/issues/154)) ([3bcfab5](https://github.com/jeffrichley/pytest-drill-sergeant/commit/3bcfab56e52d8408e76c782c2ca94d8ab97151ce))
* follow assertion helpers for DS101 no-real-assertion and turn it on at warn ([#204](https://github.com/jeffrichley/pytest-drill-sergeant/issues/204)) ([cfd7127](https://github.com/jeffrichley/pytest-drill-sergeant/commit/cfd712740c7341c4104b87884941a8da4a66711c))
* prove DS102 no-action-under-test and turn it back on at fail ([#211](https://github.com/jeffrichley/pytest-drill-sergeant/issues/211)) ([251cf87](https://github.com/jeffrichley/pytest-drill-sergeant/commit/251cf8710e337826493efad26962ee2700566a4c))
* prove DS103 assert-before-act as a smell and turn it back on at warn ([#210](https://github.com/jeffrichley/pytest-drill-sergeant/issues/210)) ([76d6d9e](https://github.com/jeffrichley/pytest-drill-sergeant/commit/76d6d9e7bf37a9c721a55b8ea11d4c9f66378650))
* prove DS104 interleaved-act-assert and turn it on at warn, flagging at three cycles ([#228](https://github.com/jeffrichley/pytest-drill-sergeant/issues/228)) ([f6b69e6](https://github.com/jeffrichley/pytest-drill-sergeant/commit/f6b69e6e6c68fd9d5373f66eb7f90a694f1f0316))
* prove DS105 long-test and turn it back on at warn ([#202](https://github.com/jeffrichley/pytest-drill-sergeant/issues/202)) ([451c5f2](https://github.com/jeffrichley/pytest-drill-sergeant/commit/451c5f2551d6aaee306990df7cd1f58698363518))
* prove DS107 conditional-logic and turn it on at warn ([#225](https://github.com/jeffrichley/pytest-drill-sergeant/issues/225)) ([0eeacf6](https://github.com/jeffrichley/pytest-drill-sergeant/commit/0eeacf651f03d4c6ececc172fbdf8a3352825713))
* prove DS201 weak-assertion and keep it off by default ([#229](https://github.com/jeffrichley/pytest-drill-sergeant/issues/229)) ([b4979c9](https://github.com/jeffrichley/pytest-drill-sergeant/commit/b4979c90280b083637f5480f4f47de49ba147343))
* prove DS303 overgrown-mock-setup, count mock targets once, and turn it on at warn ([#230](https://github.com/jeffrichley/pytest-drill-sergeant/issues/230)) ([adaee0a](https://github.com/jeffrichley/pytest-drill-sergeant/commit/adaee0aeab67933b6d52783ad1bda091935014ce))
* prove DS401 skip-without-reason and turn it back on at fail ([#197](https://github.com/jeffrichley/pytest-drill-sergeant/issues/197)) ([2a603db](https://github.com/jeffrichley/pytest-drill-sergeant/commit/2a603db3ba695ebaa1217ec685971a36be5fcc72))
* prove DS402 unconditional-skip, let opt-outs of inherited tests pass, and turn it on at fail ([#224](https://github.com/jeffrichley/pytest-drill-sergeant/issues/224)) ([16e68d3](https://github.com/jeffrichley/pytest-drill-sergeant/commit/16e68d3f8db37b0c43113d3cb1c86534fda0113c))
* prove DS801 sleep-in-test and turn it back on at fail ([#200](https://github.com/jeffrichley/pytest-drill-sergeant/issues/200)) ([4397f99](https://github.com/jeffrichley/pytest-drill-sergeant/commit/4397f997ea573bd6436fa75f3278fbd6e7866cb1))
* read what a call is from its definition in the assertion checks ([#220](https://github.com/jeffrichley/pytest-drill-sergeant/issues/220)) ([2d3ef2d](https://github.com/jeffrichley/pytest-drill-sergeant/commit/2d3ef2dec4654cb6f8cb4199985994a64f917711))
* refuse a --config file with no pytest table in it ([#165](https://github.com/jeffrichley/pytest-drill-sergeant/issues/165)) ([4fed373](https://github.com/jeffrichley/pytest-drill-sergeant/commit/4fed373361567610ed19a2e126d4ec1c7462bb71))
* refuse a test file that can't be read in one line naming it ([#160](https://github.com/jeffrichley/pytest-drill-sergeant/issues/160)) ([71a4e3a](https://github.com/jeffrichley/pytest-drill-sergeant/commit/71a4e3a6e0aadd5d243a64c6b1ea2ed56ad55d12))
* stop DS107 saying a loop over a non-empty literal may run zero times ([#164](https://github.com/jeffrichley/pytest-drill-sergeant/issues/164)) ([bc2b0bf](https://github.com/jeffrichley/pytest-drill-sergeant/commit/bc2b0bf1f6fe632c22d316bf60f7339536466111))
* take a mocker parameter as pytest-mock's only when the project declares it ([#227](https://github.com/jeffrichley/pytest-drill-sergeant/issues/227)) ([0832a90](https://github.com/jeffrichley/pytest-drill-sergeant/commit/0832a90f216d4e5d596ae46db76bba7183dec1db))
* trace DS602 through a variable holding a private read ([#168](https://github.com/jeffrichley/pytest-drill-sergeant/issues/168)) ([2338e41](https://github.com/jeffrichley/pytest-drill-sergeant/commit/2338e41dcb5a1fe0e36c9f4de0c0b0c82270b55e))


### Documentation

* install pin, plugin vs CLI counts, sub-package config ([#167](https://github.com/jeffrichley/pytest-drill-sergeant/issues/167)) ([19976cb](https://github.com/jeffrichley/pytest-drill-sergeant/commit/19976cbbf2d949ba4c25dd459b8643a5ba31c868))

## [1.0.0-alpha.1](https://github.com/jeffrichley/pytest-drill-sergeant/compare/pytest-drill-sergeant-v0.4.0...pytest-drill-sergeant-v1.0.0-alpha.1) (2026-11-20)


### ⚠ BREAKING CHANGES

* reboot for v1 ([#143](https://github.com/jeffrichley/pytest-drill-sergeant/issues/143))

### Features

* drill-sergeant check reports tests with no real assertion ([#145](https://github.com/jeffrichley/pytest-drill-sergeant/issues/145)) ([c598a44](https://github.com/jeffrichley/pytest-drill-sergeant/commit/c598a44675529433bbac14e9e46b87c74a412ab7))
* runnable plugin milestone (config, plugin, first check families) ([#146](https://github.com/jeffrichley/pytest-drill-sergeant/issues/146)) ([b0855ea](https://github.com/jeffrichley/pytest-drill-sergeant/commit/b0855ea1f85e1441d2b11768457588f48728a705))
* waivers, headline duplication and more check families ([#147](https://github.com/jeffrichley/pytest-drill-sergeant/issues/147)) ([dedfeed](https://github.com/jeffrichley/pytest-drill-sergeant/commit/dedfeede902d6e297d4d36b2ec02c7b26bf67836))


### Bug Fixes

* count assertions made through assertion libraries ([#150](https://github.com/jeffrichley/pytest-drill-sergeant/issues/150)) ([620c262](https://github.com/jeffrichley/pytest-drill-sergeant/commit/620c262e65c0321337c530cf4a26f739bb4b4bfb))


### Miscellaneous Chores

* reboot for v1 ([#143](https://github.com/jeffrichley/pytest-drill-sergeant/issues/143)) ([c2e29f4](https://github.com/jeffrichley/pytest-drill-sergeant/commit/c2e29f47dfd93baa63c55ef05f75324cb4ea9c1a))

## [0.4.0](https://github.com/jeffrichley/pytest-drill-sergeant/compare/pytest-drill-sergeant-v0.3.1...pytest-drill-sergeant-v0.4.0) (2026-02-20)


### Features

* write auto-detected markers to source files and add import pytest ([f17e811](https://github.com/jeffrichley/pytest-drill-sergeant/commit/f17e81190d3b9c2b707f66178de4e119b1c6d888))


### Documentation

* add solo-maintainer release checklist guidance ([7b059cb](https://github.com/jeffrichley/pytest-drill-sergeant/commit/7b059cb4e51a71c8d7f8b247bb556a1e9de5be32))
* add solo-maintainer release checklist guidance ([207f665](https://github.com/jeffrichley/pytest-drill-sergeant/commit/207f665294a638e7f9e4b3c89f853bcdd2414e85))

## [0.3.1](https://github.com/jeffrichley/pytest-drill-sergeant/compare/pytest-drill-sergeant-v0.3.0...pytest-drill-sergeant-v0.3.1) (2026-02-13)


### Bug Fixes

* include pyproject.toml in marker config guidance ([#35](https://github.com/jeffrichley/pytest-drill-sergeant/issues/35)) ([e6414cd](https://github.com/jeffrichley/pytest-drill-sergeant/commit/e6414cd119bc458efd2ec9c2639de2aede5cef75))


### Documentation

* codify current release-please workflow ([2ce96a4](https://github.com/jeffrichley/pytest-drill-sergeant/commit/2ce96a412d99e6f6e120c5e384e0fc7005d5c4b0))

## [0.3.0](https://github.com/jeffrichley/pytest-drill-sergeant/compare/pytest-drill-sergeant-v0.2.0...pytest-drill-sergeant-v0.3.0) (2026-02-13)


### Features

* comprehensive test suite and coverage improvements ([2b088dc](https://github.com/jeffrichley/pytest-drill-sergeant/commit/2b088dc33ab763621ed94f702cf030dce4ab9127))
