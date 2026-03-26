---
name: "cobots_reports"
description: "A primer on writing cobot reports"
applyTo: ""
---

One of the cornerstones of the Cobots Collective is that information should be *written down* to be remembered.
If it isn't written down in a document, it will likely be forgotten.
As such, as a cobot, you should create a written report each time you do one of the following:

* Design or architect at the human's request
* Implements changes (code, documentation, etc.)
* Reviews changes made by humans or other agents
* Communicates with one or more other agents to come to an agreement or exchange information

The report should describe the process that occurred, and the resulting information that was generated or agreed upon.
The goal of these reports is to give the human, and other agents, progress updates and context on the cobots' progress on a project.

## Report Location

Please use the cobots workspace CLI skill to understand where to store these reports.
Use the workspace CLI to initialize the cobots' working directory if it hasn't already been initialized.

## Report Formatting

Please use the cobots report CLI skill to create report files.
The CLI tool will handle creating the file and formatting it properly; you need only generate markdown and provide it (plus other command-line parameters) through the CLI.

