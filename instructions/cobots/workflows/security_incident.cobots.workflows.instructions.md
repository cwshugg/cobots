---
name: "cobots_workflows_security_incident"
description: "The 'security incident' workflow."
applyTo: "**/*.cobots.agent.md"
---

# Security Incident Response

## Overview

Rapid-response workflow for security-specific incidents — vulnerability exploits, data breaches, credential leaks, or other security events. Distinct from the general [hotfix](./hotfix.cobots.workflows.instructions.md) workflow in that SecurityAnalyst leads the investigation and verification, and the workflow includes containment and security-specific triage steps.

## Trigger / When to Use

* A security vulnerability is actively being exploited.
* A data breach is discovered.
* Credentials are leaked.
* A security advisory affects the production system.
* A penetration test reveals critical findings.

## Preconditions

* A confirmed or strongly suspected security incident.

## Task Structure

| Task # | Task Name | Owner | Depends On | Notes |
|--------|-----------|-------|------------|-------|
| 1 | Assess and Classify Incident | Director | — | Director assesses the incident severity, classifies it (breach, exploit, leak, etc.), creates an urgent task, and immediately notifies the human. |
| 2 | Security Triage | SecurityAnalyst | 1 | SecurityAnalyst performs immediate triage — determines the scope of exposure, identifies affected systems/data, and assesses ongoing risk. Produces an initial triage report. |
| 3 | Contain and Mitigate | Developer | 2 | Developer implements immediate containment measures (rotate credentials, revoke tokens, block attack vectors, disable compromised features). |
| 4 | Root Cause Analysis | SecurityAnalyst | 3 | SecurityAnalyst performs a thorough analysis to identify the root cause of the security incident — how the vulnerability was introduced, how it was exploited, and what data/systems were affected. |
| 5 | Implement Permanent Fix | Developer | 4 | Developer implements a permanent fix for the root cause vulnerability. |
| 6 | Security Verification | SecurityAnalyst | 5 | SecurityAnalyst verifies the fix fully addresses the root cause and no residual vulnerabilities remain. |
| 7 | Address Remaining Findings | Developer | 6 | Developer addresses any remaining security findings. |
| 8 | Post-Incident Security Report | Documenter | 7 | Documenter documents the full incident — timeline, scope, root cause, containment actions, permanent fix, and recommendations for prevention. Researcher assists by gathering data. |
| 9 | Final Notification and Debrief | Director | 8 | Director notifies the human that the incident is resolved and the post-incident report is available. Schedules a retrospective if needed. |

### Loops and Branches

* Steps 6–7 repeat until SecurityAnalyst confirms the fix is complete.
* Steps 3–4 may iterate if initial containment proves insufficient.

## Exit Criteria

* Incident is contained.
* Root cause is identified and fixed.
* Security verification passes.
* Post-incident report is produced.

## Artifacts Produced

* Incident classification (in task)
* Security triage report
* Containment actions log
* Root cause analysis
* Code fix
* Security verification report
* Post-incident security report

## Notes

* For non-security incidents, use the [hotfix](./hotfix.cobots.workflows.instructions.md) workflow instead.
* This workflow should follow [NIST SP 800-61](https://csrc.nist.gov/pubs/sp/800-61/r2/final) guidance on incident handling.
