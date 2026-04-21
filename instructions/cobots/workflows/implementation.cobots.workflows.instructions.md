---
name: "cobots_workflows_implementation"
description: "The 'implementation' workflow."
applyTo: "**/*.cobots.agent.md"
---

# Implementation

## Overview

Workflow for implementing a system from an approved architecture report. Covers planning, coding, testing, code review, security review, and documentation.

## Trigger / When to Use

* An approved architecture report exists and implementation is requested.

## Preconditions

* An approved architecture report (typically produced by the [architecture workflow](./architecture.cobots.workflows.instructions.md)).
* Optionally, a research report from Researcher.

## Task Structure

| Task # | Task Name | Owner | Depends On | Notes |
|--------|-----------|-------|------------|-------|
| 1 | Create Implementation Plan | Developer | — | Developer reads the architecture report and creates an implementation plan report. |
| 2 | Review Implementation Plan | Scrutinizer | 1 | Scrutinizer reviews the implementation plan for feasibility and completeness. |
| 3 | Revise Implementation Plan | Developer | 2 | Developer addresses feedback on the plan. |
| 4 | Implement Code and Tests | Developer | 3 | Developer implements the architecture, writes tests, and ensures they pass. |
| 5 | Review Implementation | Scrutinizer | 4 | Scrutinizer performs a full code review and produces a review report. |
| 6 | Address Review Feedback | Developer | 5 | Developer addresses the review findings. |
| 7 | Security Review | SecurityAnalyst | 6 | SecurityAnalyst reviews the implementation for security vulnerabilities (injection flaws, secrets, auth issues, etc.). Produces a security review report. |
| 8 | Address Security Findings | Developer | 7 | Developer addresses any security findings. |
| 9 | Write Documentation | Documenter | 8 | Documenter writes or updates documentation based on the final reviewed implementation. |
| 10 | Review Documentation | Scrutinizer | 9 | Scrutinizer reviews documentation quality. |

### Loops and Branches

* Steps 2–3 repeat until the plan is approved.
* Steps 5–6 repeat until code quality is satisfactory.
* Steps 7–8 repeat until SecurityAnalyst approves.
* Steps 9–10 can iterate similarly until documentation is approved.

## Exit Criteria

* Code is implemented and all tests pass.
* Code review is approved.
* Security review is approved.
* Documentation is written and reviewed.

## Artifacts Produced

* Implementation plan report
* Code changes
* Test suite
* Quality review report(s)
* Security review report(s)
* Documentation

## Notes

* Documentation (step 9) depends on completed reviews (steps 5–8) to avoid producing docs against unreviewed code that may change significantly.
* SecurityAnalyst's review runs after Scrutinizer's quality review so that obvious code issues are already resolved before the security pass.

