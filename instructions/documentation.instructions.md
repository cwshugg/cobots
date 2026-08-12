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
Focus on updating the documentation to describe the *current behavior* only; avoid making notes about previous or upcoming changes.

For user-facing APIs, CLI commands, configuration options, defaults, error behavior, or examples, compare the documentation with the implemented source of truth.
Do not describe planned or removed behavior as available; implement it, remove it, or qualify the documentation.
Execute examples when the project provides a practical way to do so.

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

