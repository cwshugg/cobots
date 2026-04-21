---
name: "cobots_workflows_architecture"
description: "The 'architecture' workflow."
applyTo: "**/*.cobots.agent.md"
---

# Architecture / System Design

## Overview

Full end-to-end workflow for designing a new system or major component, from requirements gathering through approved architecture. This workflow produces an architecture report that serves as the foundation for the [implementation workflow](./implementation.cobots.workflows.instructions.md).

## Trigger / When to Use

* A human requests a new system, feature, or major component to be designed.

## Preconditions

* A clear description of the problem or requirements from the human.

## Task Structure

| Task # | Task Name | Owner | Depends On | Notes |
|--------|-----------|-------|------------|-------|
| 1 | Clarify Requirements | Director | — | Director asks the human clarifying questions and documents final requirements as a task. |
| 2 | Research Technologies and Approaches | Researcher | 1 | Researcher researches relevant technologies, libraries, patterns, and prior art. Produces a research report. |
| 3 | Draft Architecture | Architect | 1, 2 | Architect designs the system architecture using requirements and research. Produces an architecture report. |
| 4 | Review Architecture | Scrutinizer | 3 | Scrutinizer reviews the architecture report for completeness, feasibility, and quality. Produces a review report. |
| 5 | Security Review Architecture | SecurityAnalyst | 3 | SecurityAnalyst reviews the architecture for security concerns — threat vectors, authentication/authorization design, data handling, and attack surface. Produces a security review report. |
| 6 | Revise Architecture | Architect | 4, 5 | Architect addresses feedback from both Scrutinizer and SecurityAnalyst and updates the architecture report. |
| 7 | Human Approval | Director | 6 | Director presents the final architecture to the human for approval. |

### Loops and Branches

* Steps 4–6 repeat until both Scrutinizer and SecurityAnalyst approve.
* After the review loop, step 7 gates on human approval.

## Exit Criteria

* Architecture report is approved by Scrutinizer, SecurityAnalyst, and the human.

## Artifacts Produced

* Research report
* Architecture report
* Quality review report(s)
* Security review report(s)

## Notes

* SecurityAnalyst's review at this stage catches security design flaws early (e.g., missing authentication, insecure data flows) before any code is written, when they are cheapest to fix.
