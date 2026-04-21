---
name: "cobots_workflows_sprint_planning"
description: "The 'sprint planning' workflow."
applyTo: "**/*.cobots.agent.md"
---

# Sprint Planning

## Overview

Workflow for breaking down a large request into structured, assignable tasks.

## Trigger / When to Use

Human provides a new project, feature request, or large body of work that needs to be decomposed into individual tasks before execution can begin.

## Preconditions

* A description of the work to be done from the human.

## Task Structure

| Task # | Task Name | Owner | Depends On | Notes |
|--------|-----------|-------|------------|-------|
| 1 | Gather Requirements | Director | — | Director asks clarifying questions and documents the full scope of the request. |
| 2 | Research (if needed) | Researcher | 1 | If the request involves unfamiliar domains, Researcher researches and produces a report. |
| 3 | Break Down Work | Director | 1, 2 | Director decomposes the work into individual tasks, assigns owners, sets dependencies, and selects the appropriate workflow(s) for each. For technically complex work, Architect advises on task decomposition to ensure architectural alignment. |
| 4 | Human Review and Approval | Director | 3 | Director presents the task breakdown to the human for approval. Adjusts based on feedback. |

### Loops and Branches

* Task 2 is **conditional** — skip it if the request is within well-understood domains.
* Task 4 may loop back to Task 3 if the human requests changes to the breakdown.
* For technically complex work, Architect should be consulted during Task 3 to ensure tasks align with the system architecture.

## Exit Criteria

* Human approves the work breakdown.
* All tasks are created and assigned with clear owners and dependencies.

## Artifacts Produced

* Requirements documentation (in task discussions).
* Research report (if applicable).
* Created tasks with owners, dependencies, and assigned workflows.

## Notes

This is typically the first workflow invoked for any new body of work. Director should be familiar with all available workflows so that each task in the breakdown can be assigned the correct workflow for execution.
