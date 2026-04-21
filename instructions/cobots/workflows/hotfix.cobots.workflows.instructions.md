---
name: "cobots_workflows_hotfix"
description: "The 'hotfix' workflow."
applyTo: "**/*.cobots.agent.md"
---

# Hotfix / Incident Response

## Overview

Rapid-response workflow for critical production issues that require immediate attention. Prioritizes speed and correctness over thoroughness, with parallel reviews to minimize delay.

## Trigger / When to Use

* A critical bug or outage is reported that requires urgent resolution.

## Preconditions

* A critical issue has been identified and confirmed.

## Task Structure

| Task # | Task Name | Owner | Depends On | Notes |
|--------|-----------|-------|------------|-------|
| 1 | Assess and Communicate | Director | — | Director assesses severity, creates an urgent task, assigns it, and notifies the human. |
| 2 | Diagnose Issue | Developer | 1 | Developer rapidly investigates and identifies the root cause. |
| 3 | Implement Hotfix | Developer | 2 | Developer implements the minimal fix to resolve the issue. Focus on correctness over elegance. |
| 4 | Expedited Review | Scrutinizer | 3 | Scrutinizer performs a focused review of the hotfix for correctness and unintended side effects. Review scope is narrowed to the fix only. |
| 5 | Expedited Security Review | SecurityAnalyst | 3 | SecurityAnalyst performs a focused security review of the hotfix in parallel with Scrutinizer. Ensures the fix doesn't introduce new vulnerabilities and, if the incident was security-related, that the vulnerability is fully remediated. |
| 6 | Address Critical Feedback | Developer | 4, 5 | Developer addresses only critical findings from both reviews. |
| 7 | Post-Incident Report | Documenter | 6 | Documenter documents the incident — what happened, root cause, fix applied, timeline, and recommendations to prevent recurrence. Researcher assists by gathering data (task history, timelines, related reports). |
| 8 | Final Notification | Director | 7 | Director notifies the human that the hotfix has been applied and the post-incident report is available. |

### Loops and Branches

* Steps 4–6 may iterate, but should be kept to a minimum (1–2 rounds max) given urgency.
* Steps 4 and 5 run in parallel (different agents) to minimize delay.

## Exit Criteria

* Hotfix is applied and reviewed by both Scrutinizer and SecurityAnalyst.
* Post-incident report is produced.
* The human is notified.

## Artifacts Produced

* Hotfix code changes
* Expedited review report
* Expedited security review report
* Post-incident report

## Notes

* This workflow prioritizes speed over thoroughness. A follow-up [refactoring](./refactoring.cobots.workflows.instructions.md) or [bug fix](./bug_fix.cobots.workflows.instructions.md) workflow should be used to properly harden the fix if needed.
* SecurityAnalyst's involvement is especially critical when the incident has security implications (data breach, exploit, etc.).
* For security-specific incidents, use the [security incident response](./security_incident.cobots.workflows.instructions.md) workflow instead.
