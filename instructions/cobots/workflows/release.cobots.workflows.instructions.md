---
name: "cobots_workflows_release"
description: "The 'release' workflow."
applyTo: "**/*.cobots.agent.md"
---

# Release Preparation

## Overview

Workflow for preparing a software release, including final quality and security checks, changelog generation, documentation updates, and human approval before tagging.

## Trigger / When to Use

* The team is ready to cut a release (human decision or milestone reached).

## Preconditions

* All planned features and fixes are implemented and reviewed.
* Tests pass.

## Task Structure

| Task # | Task Name | Owner | Depends On | Notes |
|--------|-----------|-------|------------|-------|
| 1 | Pre-Release Quality Audit | Scrutinizer | — | Scrutinizer performs a final review pass on all changes since the last release. Checks for quality, consistency, and any overlooked issues. |
| 2 | Pre-Release Security Review | SecurityAnalyst | — | SecurityAnalyst performs a security review of all changes since the last release. Checks for vulnerabilities, secrets, dependency issues, and configuration security. Produces a security review report. |
| 3 | Update Documentation | Documenter | 1, 2 | Documenter ensures all documentation (README, API docs, guides) is up to date with the current state. |
| 4 | Generate Changelog | Documenter | 3 | Documenter compiles a changelog from tasks, commits, and reports since the last release. |
| 5 | Review Release Artifacts | Scrutinizer | 4 | Scrutinizer reviews the documentation updates and changelog for accuracy and completeness. |
| 6 | Human Approval | Director | 5 | Director presents the release artifacts (audit results, security review, docs, changelog) to the human for final approval before tagging. |
| 7 | Tag and Release | Developer | 6 | Developer creates the release tag, builds release artifacts, and publishes. |
| 8 | Post-Release Verification | Developer | 7 | Developer verifies the release is functional (smoke tests, basic validation). |

### Loops and Branches

* Steps 1–2 can run in parallel (different agents).
* Steps 3–4 are sequential (both assigned to Documenter, respecting the one-task-at-a-time rule).

## Exit Criteria

* Release is tagged and artifacts are published.
* Documentation is updated and changelog is generated.
* Security review is clean.
* Human has approved.
* Post-release checks pass.

## Artifacts Produced

* Pre-release quality audit report
* Pre-release security review report
* Updated documentation
* Changelog
* Release tag/artifacts

## Notes

* The human approval gate (step 6) ensures no release ships without explicit human sign-off.
* SecurityAnalyst's pre-release security review (step 2) is a final safety net to catch any security issues that may have been missed during individual feature reviews.
