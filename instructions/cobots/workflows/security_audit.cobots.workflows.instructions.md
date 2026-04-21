---
name: "cobots_workflows_security_audit"
description: "The 'security audit' workflow."
applyTo: "**/*.cobots.agent.md"
---

# Security Audit

## Overview

On-demand or periodic comprehensive security review of the codebase, configurations, and infrastructure. This workflow produces findings and a remediation plan — it does not implement fixes directly.

## Trigger / When to Use

* Human requests a security audit.
* Scheduled periodic review.
* Preparation for compliance.
* After a significant body of work is completed.

## Preconditions

* An existing codebase to audit.
* Ideally, a defined scope (full codebase, specific modules, or recent changes).

## Task Structure

| Task # | Task Name | Owner | Depends On | Notes |
|--------|-----------|-------|------------|-------|
| 1 | Define Audit Scope | Director | — | Director works with the human to define the scope — full codebase, specific modules, recent changes since a date/tag, or specific security domains (auth, data handling, etc.). |
| 2 | Perform Security Audit | SecurityAnalyst | 1 | SecurityAnalyst performs a comprehensive security review following OWASP guidelines. Examines secrets detection, injection flaws, auth/authz, dependency security, configuration security, cryptography, and data handling. Produces a security review report with severity-rated findings. |
| 3 | Research Remediation Approaches | Researcher | 2 | If findings require unfamiliar remediation techniques or involve external dependencies, Researcher researches best practices for addressing the findings. |
| 4 | Review Audit Report | Scrutinizer | 2 | Scrutinizer reviews the security audit report for thoroughness, accuracy, and completeness. |
| 5 | Prioritize and Plan Remediation | Director | 3, 4 | Director prioritizes findings by severity and business impact, and creates remediation tasks. Critical and high-severity findings should be addressed immediately. |
| 6 | Human Review | Director | 5 | Director presents the audit results and remediation plan to the human for approval. |

### Loops and Branches

* None in the audit itself. Remediation tasks spawn separate workflows:
    * Critical findings → [hotfix](./hotfix.cobots.workflows.instructions.md)
    * Medium/low findings → [bug fix](./bug_fix.cobots.workflows.instructions.md) or [implementation](./implementation.cobots.workflows.instructions.md)
* Steps 3–4 can run in parallel (different agents).

## Exit Criteria

* Security audit report is produced, reviewed, prioritized, and presented to the human.
* Remediation tasks are created for all findings.

## Artifacts Produced

* Audit scope definition (in task)
* Security audit report
* Remediation research (if applicable)
* Review of audit report
* Remediation task list

## Notes

* This workflow produces findings; it does not fix them. Fixes are tracked as separate tasks using the appropriate workflow.
* Recommended cadence is once per release cycle or after major feature completions.
