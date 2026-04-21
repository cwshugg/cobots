---
name: "cobots_workflows_performance"
description: "The 'performance' workflow."
applyTo: "**/*.cobots.agent.md"
---

# Performance Optimization

## Overview

Workflow for identifying and resolving performance bottlenecks. Uses profiling and benchmarking to establish baselines, plan optimizations, and measure improvement.

## Trigger / When to Use

* Performance issues observed.
* Benchmarks degraded.
* Human requests optimization of a specific area.

## Preconditions

* A running system with observable performance characteristics.

## Task Structure

| Task # | Task Name | Owner | Depends On | Notes |
|--------|-----------|-------|------------|-------|
| 1 | Research Performance Approaches (conditional) | Researcher | — | If the tech stack is unfamiliar or novel profiling approaches are needed, Researcher researches profiling tools, optimization techniques, and benchmarking approaches. Skip if the team is already familiar with profiling tools for this stack. |
| 2 | Profile and Benchmark | Developer | 1 (or —) | Developer profiles the system, establishes baseline benchmarks, and identifies bottlenecks. Documents findings. |
| 3 | Plan Optimizations | Architect | 2 | Architect designs optimization approaches for the identified bottlenecks. |
| 4 | Implement Optimizations | Developer | 3 | Developer implements the optimizations. |
| 5 | Benchmark After Optimization | Developer | 4 | Developer re-runs benchmarks to measure improvement. Documents before/after comparison. |
| 6 | Review Optimizations | Scrutinizer | 5 | Scrutinizer reviews the changes for correctness, maintainability, and measured improvement. |
| 7 | Address Review Feedback | Developer | 6 | Developer addresses any review findings. |

### Loops and Branches

* Steps 3–7 can repeat for each bottleneck or optimization round.
* Step 1 is conditional — skip when the profiling tools are well-known for the project's tech stack.

## Exit Criteria

* Performance targets are met (or best achievable improvement is reached).
* Benchmarks document the improvement.
* Code is reviewed.

## Artifacts Produced

* Research report (if applicable)
* Baseline benchmarks
* Optimization plan
* Benchmark comparison (before/after)
* Review report

## Notes

* SecurityAnalyst is not a default participant, but if optimizations involve weakening security controls for performance (e.g., reducing encryption, caching sensitive data), Director should add a SecurityAnalyst review step.
