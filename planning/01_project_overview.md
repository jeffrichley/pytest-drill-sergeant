# pytest-drill-sergeant: Project Overview

## Mission Statement
A pytest plugin that acts as a "drill sergeant" for AI-written tests, enforcing quality standards and catching common AI coding anti-patterns with humor and personality.

## Core Problem
AI coders frequently write tests that:
- Test **HOW** something works instead of **WHAT** it does
- Create duplicate/near-duplicate tests with copy-paste setup
- Use poor fixture practices and repeated arrange blocks
- Write flaky, non-deterministic tests
- Over-mock internal implementation details
- Miss AAA (Arrange-Act-Assert) structure

## Solution Vision
A hybrid pytest plugin + CLI tool that:
1. **Detects** test quality issues through static AST analysis and dynamic runtime monitoring
2. **Educates** developers with actionable suggestions and rewrite hints
3. **Entertains** with configurable personas (Drill Sergeant Hartman, Snoop Dogg, etc.)
4. **Tracks** progress with a "Battlefield Readiness Score" and trend reporting
5. **Integrates** seamlessly into CI/CD with SARIF output for PR annotations

## Key Features
- **Behavior Integrity Score (BIS)**: Detects tests focused on implementation vs behavior
- **Duplicate Test Detection**: Finds near-identical tests using AST similarity and coverage analysis
- **Fixture Extraction Suggestions**: Recommends converting repeated setup to fixtures
- **AAA Comment Advisor**: Encourages proper test structure
- **Persona-Based Feedback**: Fun, configurable output styles
- **Battlefield Readiness Score**: Overall test suite quality metric
- **SARIF Integration**: CI/CD friendly reporting with PR annotations

## Target Users
- Development teams using AI coding assistants
- Projects with growing test suites that need quality enforcement
- Teams wanting to improve test maintainability and reduce flakiness
- Developers who appreciate humor in their tooling

## Success Metrics
- Reduction in duplicate tests across test suites
- Improved test maintainability scores
- Increased adoption of proper testing patterns
- Developer satisfaction with tooling experience
