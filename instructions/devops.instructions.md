---
name: "devops"
description: "Foundational DevOps principles covering CALMS framework and DORA metrics"
applyTo: "**/*.yml,**/*.yaml,**/Makefile,**/makefile,**/*.mk,**/*.tf,**/Jenkinsfile,**/.github/**,**/Dockerfile,**/docker-compose*.yml"
---

<!--
Adapted from the awesome-copilot project:

https://github.com/github/awesome-copilot/blob/main/instructions/devops-core-principles.instructions.md

The original is available at the URL above. This version has been condensed and
adapted to match the cobots instruction style.
- Scribs
-->

# DevOps Core Principles

DevOps is a set of practices that combines software development (Dev) and IT operations (Ops) to shorten the development lifecycle while delivering features, fixes, and updates frequently and reliably. It emphasizes collaboration, automation, measurement, and continuous improvement.

Apply these principles when designing systems, writing CI/CD pipelines, provisioning infrastructure, and reviewing operational processes.

## The CALMS Framework

CALMS represents the five pillars of a successful DevOps culture.

### Culture

* Foster a collaborative, blameless culture with shared responsibility across development, operations, and security teams.
* When incidents occur, focus on systemic root causes and learning opportunities — not blame.
* Encourage experimentation, knowledge sharing, and a growth mindset.
* Establish fast, clear feedback channels between all stages of the delivery lifecycle.

### Automation

* Automate everything repeatable across the software delivery lifecycle: builds, tests, deployments, infrastructure provisioning, and security scans.
* Use CI/CD pipelines as the backbone of fast, reliable releases.
* Manage infrastructure through code (Terraform, Ansible, Pulumi) — not manual processes.
* Integrate automated testing (unit, integration, end-to-end, security) into the pipeline.
* Automate monitoring, alerting, and incident response where possible.

### Lean

* Eliminate waste: unnecessary approvals, manual handoffs, waiting times, and excessive documentation that doesn't add value.
* Maximize flow by reducing batch sizes — smaller commits, smaller PRs, more frequent deployments.
* Build quality in throughout the development process rather than relying on end-of-cycle testing.
* Deliver features iteratively. Prefer minimum viable implementations that can be improved based on feedback.

### Measurement

* Measure everything relevant across the delivery pipeline and application lifecycle.
* Track the four DORA metrics (see below) as primary indicators of delivery performance.
* Use structured logging, metrics, and distributed tracing for application observability.
* Build dashboards for key metrics and set up automated alerts for anomalies.
* Make data-driven decisions — use metrics to validate changes and justify architectural choices.

### Sharing

* Share common tools, platforms, and practices across teams.
* Create clear, concise, up-to-date documentation for systems, processes, and architectural decisions.
* Use runbooks that are executable by anyone on the team, not just domain experts.
* Promote collaborative practices: pair programming, cross-functional teams, internal knowledge-sharing sessions.

## DORA Metrics

The four key metrics identified by the DevOps Research and Assessment (DORA) team are strong indicators of software delivery performance. Optimize for these.

### Deployment Frequency

* **Definition**: How often the team successfully releases to production.
* **Goal**: High. Elite teams deploy multiple times per day.
* **How to improve**:
    * Design CI/CD pipelines for frequent, small, safe deployments.
    * Break down large features into smaller, independently deployable units.
    * Use feature flags to decouple deployment from release.

### Lead Time for Changes

* **Definition**: The time from code commit to successful production deployment.
* **Goal**: Low. Elite teams have lead times under one hour.
* **How to improve**:
    * Reduce bottlenecks: smaller PRs, automated testing, fast builds, efficient code review.
    * Eliminate manual handoffs and streamline approval processes.
    * Use caching strategies in CI/CD to speed up build and test phases.

### Change Failure Rate

* **Definition**: The percentage of deployments causing service degradation (rollback, hotfix, or outage).
* **Goal**: Low. Elite teams have a change failure rate of 0–15%.
* **How to improve**:
    * Invest in robust testing (unit, integration, end-to-end).
    * Integrate static analysis, dynamic analysis, and security scanning into the pipeline.
    * Implement pre-deployment health checks and post-deployment validation.
    * Design resilient architectures (circuit breakers, retries, graceful degradation).

### Mean Time to Recovery (MTTR)

* **Definition**: How long it takes to restore service after a degradation or outage.
* **Goal**: Low. Elite teams recover in under one hour.
* **How to improve**:
    * Implement clear monitoring and alerting with actionable notifications.
    * Maintain well-documented runbooks for common failure modes.
    * Enable one-click (or automated) rollbacks.
    * Build applications with observability in mind: structured logging, metrics exposition, distributed tracing.

## Applying These Principles

* When writing code, consider how it will be built, tested, deployed, and monitored.
* When designing systems, plan for failure and automated recovery.
* When reviewing changes, evaluate operational impact alongside functional correctness.
* Treat infrastructure definitions, CI/CD pipelines, and monitoring configurations with the same rigor as application code.
