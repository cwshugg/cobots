---
name: "cobots_workflows_refactoring"
description: "The 'refactoring' workflow."
applyTo: "**/*.cobots.agent.md"
---

# Refactoring / Tech Debt Reduction

## Overview

Structured approach to improving code quality without changing external behavior. Ensures refactoring is planned, tested, and reviewed so that no regressions are introduced.

## Trigger / When to Use

* Code smell identified during review.
* Accumulated tech debt.
* Human request to improve a specific area.

## Preconditions

* Identification of the area(s) to refactor.
* Existing tests that verify current behavior (or tests must be written first).

## Task Structure

| Task # | Task Name | Owner | Depends On | Notes |
|--------|-----------|-------|------------|-------|
| 1 | Identify Refactoring Targets | Scrutinizer | — | Scrutinizer analyzes the codebase and produces a report identifying tech debt, code smells, and refactoring opportunities, prioritized by impact. |
| 2 | Research Patterns and Approaches | Researcher | 1 | If the refactoring involves new patterns or unfamiliar code areas, Researcher researches best approaches. |
| 3 | Plan Refactoring | Architect | 1, 2 | Architect creates a refactoring plan describing what changes to make and why, ensuring no behavior changes. |
| 4 | Ensure Test Coverage | Developer | 3 | Developer writes or verifies tests for the existing behavior of the code to be refactored. |
| 5 | Execute Refactoring | Developer | 4 | Developer performs the refactoring according to the plan. All existing tests must continue to pass. |
| 6 | Review Refactoring | Scrutinizer | 5 | Scrutinizer reviews the refactored code for quality, adherence to the plan, and test passage. |
| 7 | Address Review Feedback | Developer | 6 | Developer addresses any findings. |

### Loops and Branches

* Steps 6–7 repeat until approved.

## Exit Criteria

* Refactoring is complete, all tests pass (no behavior changes), and code review is approved.

## Artifacts Produced

* Tech debt analysis report
* Refactoring plan
* Code changes
* Review report

## Notes

* SecurityAnalyst is not a default participant in refactoring workflows since behavior should not change. However, if refactoring touches security-sensitive code (auth, crypto, input handling), Director should add a SecurityAnalyst security review task between steps 6 and 7.
