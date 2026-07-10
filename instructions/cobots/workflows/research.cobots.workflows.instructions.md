---
name: "cobots_workflows_research"
description: "The 'research' workflow."
applyTo: "**/*.cobots.agent.md"
---

# Research and Evaluation

## Overview

Workflow for evaluating tools, libraries, approaches, or technologies to inform a decision.

## Trigger / When to Use

A decision needs to be made about a technology choice, library selection, or approach, and multiple candidates need to be compared against defined criteria.

## Preconditions

* A clear question or set of evaluation criteria from the human or Director.

## Task Structure

| Task # | Task Name | Owner | Depends On | Notes |
|--------|-----------|-------|------------|-------|
| 1 | Define Evaluation Criteria | Director | — | Director works with the human to define what matters (performance, maintainability, community support, license, security posture, etc.). |
| 2 | Research Candidates | Researcher | 1 | Researcher researches each candidate against the evaluation criteria. Produces a comprehensive comparison report. Additionally, distill any durable, reusable findings into the knowledge base (`.cobots/knowledge/`) as tagged entries. |
| 3 | Security Evaluation (conditional) | SecurityAnalyst | 2 | If security posture is an evaluation criterion or the candidates handle sensitive data, SecurityAnalyst reviews each candidate's security track record — CVE history, security practices, known vulnerabilities. |
| 4 | Review Research | Scrutinizer | 2, 3 | Scrutinizer reviews the research for thoroughness, accuracy, and balanced analysis. |
| 5 | Present Findings | Director | 4 | Director presents findings to the human for a decision. |

### Loops and Branches

* Task 3 is **conditional** — only needed when security posture is an evaluation criterion or the candidates handle sensitive data.
* Task 4 depends on both Task 2 and Task 3 (if applicable). If Task 3 is skipped, Task 4 depends only on Task 2.
* If Scrutinizer identifies gaps in the research during Task 4, the workflow may loop back to Task 2 for additional investigation.

## Exit Criteria

* Research report is produced, reviewed, and presented to the human for decision-making.

## Artifacts Produced

* Evaluation criteria (in task discussions).
* Research/comparison report.
* Distilled knowledge-base entries (when findings are reusable), stored under `.cobots/knowledge/`.
* Security evaluation (if applicable).
* Review feedback.

## Notes

This workflow is for technology *selection* decisions that happen before architecture begins. It is distinct from the built-in research step in the [Architecture workflow](./architecture.cobots.workflows.instructions.md), which is for implementation-specific investigation within an already-chosen technology direction. Use this workflow when the question is "which technology?" and the Architecture workflow's research step when the question is "how to use the chosen technology?"
