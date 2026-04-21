---
name: "cobots_workflows_testing"
description: "The 'testing' workflow."
applyTo: "**/*.cobots.agent.md"
---

# Testing / QA

## Overview

Dedicated workflow for improving test coverage or conducting a quality audit of an existing codebase. Focuses on identifying gaps in test coverage and systematically filling them.

## Trigger / When to Use

* Human requests a test coverage improvement.
* Scrutinizer identifies insufficient test coverage during a review.

## Preconditions

* An existing codebase with identifiable gaps in test coverage.

## Task Structure

| Task # | Task Name | Owner | Depends On | Notes |
|--------|-----------|-------|------------|-------|
| 1 | Assess Test Coverage | Scrutinizer | — | Scrutinizer analyzes the codebase and identifies areas with insufficient or missing test coverage. Produces a coverage assessment report. |
| 2 | Prioritize Test Targets | Director | 1 | Director (with human input) prioritizes which areas to test first based on risk and importance. |
| 3 | Write Tests | Developer | 2 | Developer writes tests for the prioritized areas. |
| 4 | Review Tests | Scrutinizer | 3 | Scrutinizer reviews the tests for quality, correctness, and coverage adequacy. |
| 5 | Address Test Review Feedback | Developer | 4 | Developer addresses findings. |

### Loops and Branches

* Steps 3–5 repeat for each batch of prioritized test targets.
* Steps 4–5 iterate until tests are approved.

## Exit Criteria

* All prioritized areas have adequate test coverage.
* Test review is approved.

## Artifacts Produced

* Coverage assessment report
* New test files
* Test review report

## Notes

* SecurityAnalyst is not a default participant but may be brought in if Scrutinizer's assessment identifies that security-sensitive areas (auth, crypto, input validation) lack test coverage. In that case, SecurityAnalyst can advise on security-specific test scenarios.
