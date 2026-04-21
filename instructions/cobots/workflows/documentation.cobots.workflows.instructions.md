---
name: "cobots_workflows_documentation"
description: "The 'documentation' workflow."
applyTo: "**/*.cobots.agent.md"
---

# Documentation Drive

## Overview

Workflow for creating or significantly improving documentation for an existing project. Also serves as the vehicle for creating project orientation materials (architecture decision records, component interaction guides, and historical context narratives).

## Trigger / When to Use

* Human requests documentation.
* A documentation gap is identified during another workflow.
* A new agent or human needs onboarding materials.

## Preconditions

* An existing codebase or system to document.

## Task Structure

| Task # | Task Name | Owner | Depends On | Notes |
|--------|-----------|-------|------------|-------|
| 1 | Assess Documentation State | Scrutinizer | — | Scrutinizer reviews existing documentation and identifies gaps, inaccuracies, and areas needing improvement. Produces a documentation audit report. |
| 2 | Create Knowledge Map (optional) | Researcher | 1 | If the documentation drive includes onboarding/orientation goals, Researcher reviews reports, task history, and code to assess what knowledge exists and what is missing. Produces a knowledge state assessment. |
| 3 | Prioritize Documentation | Director | 1, 2 | Director (with human input) prioritizes which documentation to create or update. |
| 4 | Write Documentation | Documenter | 3 | Documenter creates or updates documentation for the prioritized areas. |
| 5 | Review Documentation | Scrutinizer | 4 | Scrutinizer reviews the documentation for accuracy, completeness, and clarity. |
| 6 | Address Review Feedback | Documenter | 5 | Documenter addresses the review findings. |

### Loops and Branches

* Task 2 is **optional** — include it when the documentation drive has onboarding or orientation goals.
* Steps 4–6 repeat for each batch of prioritized documentation.
* Steps 5–6 iterate until Scrutinizer approves the documentation.

## Exit Criteria

* All prioritized documentation is written, reviewed, and approved.

## Artifacts Produced

* Documentation audit report.
* Knowledge state assessment (if applicable).
* New or updated documentation files.
* Review report(s).

## Notes

The optional Knowledge Map step (Task 2) covers the onboarding and orientation use case. Since agents are stateless between sessions, "onboarding" is equivalent to creating persistent documentation — which is exactly what this workflow produces. The Knowledge Map artifact adds project orientation context (architectural decisions, component relationships, historical context) when needed.
