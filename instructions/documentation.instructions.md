---
name: "documentation"
description: "Best practices for writing documentation"
applyTo: "**"
---

# Best Practices in Documentation

Documentation is an important piece of a software project.
It should be concise, but present all information necessary for a high-level understanding from an onlooker who is not familiar with the project.

## Documenting New Changes

When writing documentation for new additions or changes, ensure all new changes are properly documented in the existing documentation.

## File Structure

Unless otherwise requested, please create documentation under `docs/` directory at the top of the project's file tree.
Individual files should describe individual concepts.
If needed, you may create sub-directories underneath `docs/` to better organize documentation into groups.

## Documentation Format

Unless otherwise requested, please write documentation in markdown (`.md`).
See the [markdown instructions](./markdown.instructions.md) to learn how to write effective markdown.

## Diagrams

When creating diagrams, use mermaid flowcharts rather than ASCII art, when possible.
See the [mermaid syntax reference](https://mermaid.ai/open-source/intro/syntax-reference.html) for more information.

