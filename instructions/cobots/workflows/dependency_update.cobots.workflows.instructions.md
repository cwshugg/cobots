---
name: "cobots_workflows_dependency_update"
description: "The 'dependency update' workflow."
applyTo: "**/*.cobots.agent.md"
---

# Dependency Update

## Overview

Workflow for updating project dependencies (libraries, tools, runtimes). Includes security assessment to prioritize updates with known vulnerabilities.

## Trigger / When to Use

* New dependency versions are available.
* A security vulnerability is discovered in a dependency.
* Routine maintenance schedule.

## Preconditions

* An existing project with managed dependencies.

## Task Structure

| Task # | Task Name | Owner | Depends On | Notes |
|--------|-----------|-------|------------|-------|
| 1 | Audit Dependencies | Researcher | — | Researcher reviews current dependencies, checks for outdated versions, security advisories, and breaking changes in new versions. Produces an audit report. |
| 2 | Security Assessment of Dependencies | SecurityAnalyst | 1 | SecurityAnalyst reviews the dependency audit for known CVEs, supply chain risks, and security advisories. Prioritizes updates with security implications. |
| 3 | Plan Updates | Developer | 1, 2 | Developer determines which dependencies to update and in what order, considering compatibility, risk, and security priority. Architect advises only if updates involve major breaking changes or architectural implications. |
| 4 | Apply Updates | Developer | 3 | Developer updates dependency files and resolves any immediate breakages. |
| 5 | Run Tests and Validate | Developer | 4 | Developer runs the full test suite and validates that everything works with the new dependencies. |
| 6 | Review Changes | Scrutinizer | 5 | Scrutinizer reviews the dependency changes and any code modifications required for compatibility. |
| 7 | Address Review Feedback | Developer | 6 | Developer addresses any findings from the review. |

### Loops and Branches

* Steps 6–7 repeat until approved.

## Exit Criteria

* Dependencies are updated and all tests pass.
* Changes are reviewed.
* Any security-flagged dependencies are resolved.

## Artifacts Produced

* Dependency audit report
* Security assessment
* Updated dependency files
* Review report

## Notes

* SecurityAnalyst's involvement (step 2) is particularly important when the trigger is a security vulnerability. For routine maintenance updates, SecurityAnalyst's review may be brief.
* Architect's involvement in step 3 is conditional — only needed for major version bumps with breaking changes.
* For focused security vulnerability remediation, see the [dependency vulnerability](./dependency_vulnerability.cobots.workflows.instructions.md) workflow.
