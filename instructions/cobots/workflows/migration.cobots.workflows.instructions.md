---
name: "cobots_workflows_migration"
description: "The 'migration' workflow."
applyTo: "**/*.cobots.agent.md"
---

# Code Migration

## Overview

Workflow for migrating code between frameworks, languages, APIs, or platforms. Covers research, planning, execution, and verification to ensure a smooth and safe transition.

## Trigger / When to Use

* Human requests a migration (e.g., API version upgrade, framework change, language port).

## Preconditions

* Clear definition of the source and target states.

## Task Structure

| Task # | Task Name | Owner | Depends On | Notes |
|--------|-----------|-------|------------|-------|
| 1 | Research Migration Path | Researcher | — | Researcher researches the target framework/API/language, migration guides, breaking changes, and known pitfalls. Produces a research report. |
| 2 | Plan Migration | Architect | 1 | Architect creates a migration plan — what changes, in what order, with what fallbacks. |
| 3 | Review Migration Plan | Scrutinizer | 2 | Scrutinizer reviews the plan for completeness and risk. |
| 4 | Security Review Migration Plan | SecurityAnalyst | 2 | SecurityAnalyst reviews the migration plan for security implications — will the new framework/API change the security posture? Are there known vulnerabilities in the target? |
| 5 | Execute Migration | Developer | 3, 4 | Developer performs the migration according to the plan. |
| 6 | Verify Migration | Developer | 5 | Developer runs all tests and performs manual verification to ensure equivalence. |
| 7 | Review Migration | Scrutinizer | 6 | Scrutinizer reviews the migrated code for quality and correctness. |
| 8 | Security Review Migration | SecurityAnalyst | 6 | SecurityAnalyst reviews the migrated code for security regressions or new vulnerabilities introduced by the migration. |
| 9 | Address Review Feedback | Developer | 7, 8 | Developer addresses findings from both reviews. |
| 10 | Update Documentation | Documenter | 9 | Documenter updates documentation to reflect the migration. |

### Loops and Branches

* Steps 7–9 can iterate until both reviews are approved.
* If execution (step 5) reveals the plan needs revision, return to step 2 (Plan Migration) for updates, then re-review at steps 3–4.

## Exit Criteria

* Migration is complete and all tests pass.
* Code is reviewed by Scrutinizer.
* Security is reviewed by SecurityAnalyst.
* Documentation is updated.

## Artifacts Produced

* Migration research report
* Migration plan
* Code changes
* Quality review report
* Security review report
* Updated documentation

## Notes

* Steps 3–4 (plan reviews) can run in parallel across different agents. Steps 7–8 (code reviews) can also run in parallel.
* For large migrations, consider executing the migration incrementally — migrate one module or component at a time through steps 5–9, rather than migrating the entire codebase at once. This reduces risk and makes review more manageable.
* If the migration involves a framework or language the team has not used before, the Researcher's work in step 1 is especially critical. Director should ensure adequate time for thorough research.
