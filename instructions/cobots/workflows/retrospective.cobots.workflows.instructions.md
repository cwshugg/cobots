---
name: "cobots_workflows_retrospective"
description: "The 'retrospective' workflow."
applyTo: "**/*.cobots.agent.md"
---

# Retrospective / Post-Mortem

## Overview

Workflow for reflecting on a completed project, sprint, or incident to identify lessons learned and improvements.

## Trigger / When to Use

* After a project milestone is completed.
* After a release is shipped.
* After an incident is resolved.

## Preconditions

* A completed body of work to reflect on.

## Task Structure

| Task # | Task Name | Owner | Depends On | Notes |
|--------|-----------|-------|------------|-------|
| 1 | Gather Data | Researcher | — | Researcher collects information — tasks completed, reports produced, timelines, issues encountered, and outcomes. |
| 2 | Analyze and Identify Themes | Researcher | 1 | Researcher analyzes the data and identifies patterns — what went well, what could improve, and what should change. Produces a retrospective report. |
| 3 | Review Retrospective | Scrutinizer | 2 | Scrutinizer reviews the retrospective report for thoroughness, accuracy, and completeness. |
| 4 | Present to Human | Director | 3 | Director reviews the retrospective and presents findings to the human. |
| 5 | Create Improvement Tasks | Director | 4 | Director creates actionable tasks for the identified improvements. |

### Loops and Branches

* Task 3 may loop back to Task 2 if Scrutinizer identifies gaps or inaccuracies that need to be addressed in the retrospective report.
* Task 5 may spawn tasks that use other workflows (e.g., a process improvement might trigger a Documentation Drive, or a code quality concern might trigger a Refactoring workflow).

## Exit Criteria

* Retrospective report is produced, reviewed, and presented to the human.
* Improvement tasks are created for the identified action items.

## Artifacts Produced

* Retrospective data collection.
* Retrospective report.
* Review feedback.
* Improvement tasks.

## Notes

This workflow drives continuous improvement across the team. The improvement tasks created in Task 5 should reference the retrospective report so that the context and rationale for each improvement is preserved.
