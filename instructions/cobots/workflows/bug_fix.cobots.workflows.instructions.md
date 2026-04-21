---
name: "cobots_workflows_bug_fix"
description: "The 'bug fix' workflow."
applyTo: "**/*.cobots.agent.md"
---

# Bug Triage and Fix

## Overview

Workflow for investigating, diagnosing, and fixing a reported bug. Covers the full lifecycle from reproduction through root cause analysis, fix implementation, and review.

## Trigger / When to Use

* A bug is reported by a human, discovered by an agent, or surfaced by tests/monitoring.

## Preconditions

* A bug report or description of the observed incorrect behavior.

## Task Structure

| Task # | Task Name | Owner | Depends On | Notes |
|--------|-----------|-------|------------|-------|
| 1 | Triage and Reproduce | Developer | — | Developer attempts to reproduce the bug, determines severity, and documents reproduction steps. |
| 2 | Root Cause Analysis | Developer | 1 | Developer investigates the codebase to identify the root cause. |
| 3 | Implement Fix and Tests | Developer | 2 | Developer writes the fix and adds regression tests that verify the fix. |
| 4 | Review Fix | Scrutinizer | 3 | Scrutinizer reviews the fix for correctness, side effects, and test coverage. |
| 5 | Address Review Feedback | Developer | 4 | Developer addresses any review findings. |
| 6 | Security Review (conditional) | SecurityAnalyst | 5 | If the bug has security implications or the fix touches security-sensitive code (auth, crypto, input validation, data handling), SecurityAnalyst reviews the fix. |

### Loops and Branches

* Steps 4–5 repeat until the fix is approved.
* Step 6 triggers a loop back to step 5 if SecurityAnalyst finds security issues.
* **Branch:** If the bug relates to a dependency or external system, insert a research task (Researcher) between Tasks 1 and 2 — Researcher investigates the external dependency and produces a brief research note.

## Exit Criteria

* Bug is fixed, regression test passes, and the fix is reviewed and approved.
* If security review was required, SecurityAnalyst has also approved.

## Artifacts Produced

* Bug triage notes (in task discussion)
* Code fix
* Regression tests
* Review report
* Security review report (if applicable)

## Notes

* Step 6 (SecurityAnalyst review) is conditional — it applies only when the bug or fix has security implications.
