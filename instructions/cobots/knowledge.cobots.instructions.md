---
name: "cobots_knowledge"
description: "A primer on managing the cobots knowledge base."
applyTo: "**/*.cobots.agent.md"
---

One of the cornerstones of the Cobots Collective is that information should be *written down* to be remembered.
If it isn't written down in a document, it will be forgotten.
As such, as a cobot, you should always look for ways to build upon the knowledge base that you have access to.

Whenever you do one of the following:

* Research a topic
* Complete a task
* Investigate a bug
* Implement code
* (Generally, with any action you take)

Consider this question: *Is there any information or context I have with me that could benefit somebody else in the future?*
If the answer is *yes*, then you must add (or update) an entry in the knowledge base.

## Knowledge Base Entries

The knowledge base's job is to store information that is more general-purpose (i.e. not project-specific information, like a [cobots report](./reports.cobots.instructions.md) that can be useful knowledge for agents or humans working on similar projects, or even completely different projects, in the future.

When writing a knowledge base entry:

* Keep the entry concise and general-purpose (not task-specific)
* Choose appropriate descriptive tags (see below for more information)
* Keep the information as concise as possible without losing any information.

### Tags

Knowledge base entries can (and should) be assigned one or more **tags**.
These tags are used to organize and categorize the various knowledge base entries.

For example, if you create an entry describing how to use Git to work with Rust code, you might tag the entry with the `git` and `rust` tags.

### Entry Formatting

Please use the cobots knowledge CLI skill to create knowledge base entry files.
The CLI tool will handle creating the file and formatting it properly; you need only generate markdown and provide it (plus other command-line parameters) through the CLI.

When creating an entry, please specify your name as the author.

### Entry Location

Please use the cobots workspace CLI skill to understand where to store these knowledge entries.
Use the workspace CLI to initialize the cobots' working directory if it hasn't already been initialized.

