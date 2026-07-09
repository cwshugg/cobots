---
name: "code_review"
description: "Best practices when reviewing code to ensure maximum software quality"
applyTo: "**"
---

# Code Review Best Practices

This document outlines best practices to follow when reviewing code.
The goal of a code review is to maximize quality and clarity of the changes made and of the overall project.

## Things to Look For

### Testing

* Have unit tests been written to exercise the new behavior?

### Logging

* Does the project use logging?
    * If so, do the changes include usage of the logging system?
* Are log messages leaking any secrets? (They shouldn't be.)

### Leftover Stuff

* Is there code/library imports/etc that's commented out?
    * Is it really needed or should it be removed to clean things up?
* Is there code that is unused anywhere?
    * Will it be needed in the future?
    * Should it be removed?

### Commenting

* Do code comments describe the code, *only* the code, and *only* the *current state* of the code?
    * Unless for a special reason, comments should not be describing a "previous implementation" or "a recent change".
    * Comments should be timeless and apply to exactly the code in its current state.
* Are there comments that contain references to any metadata that does not belong in the code?
  These should be removed.
    * Examples:
        * The names of humans or other agents
        * Cobots task IDs
        * Code review feedback points

### Documentation and Style

* Are there outdated comments that need updating?
* Is there documentation that needs to be updated to reflect these code changes?
* Does the code follow the style conventions of the rest of the project?
* Is there a mixture of spaces and tabs in the file?
    * There should be a consistent choice.

### File Paths/Names

* Are file paths and/or names written in the PR's files up to date?
* Are the names of the files appropriate and easy to understand?
* Consider the names of new functions, classes, etc.
    * Are the names clear and easy to understand?
    * Does the format and naming style align with existing, similar names?

### Design Choices

* Is there repeated code that could be put into a function?
    * **Scenario 1:** did the developer add two copies of the same code in his/her new code?
    * **Scenario 2:** did the developer add one bit of code that copies from existing code?
    * Code should be reused when possible; perhaps the repetition should be moved to a helper function or somewhere else where both places can access it.
* How did the developer package/organize the code?
    * Is there a better way to package it such that it's more modular, more easily reusable, etc.?
    * Can functions be parameterized to save on code and reduce repetition?

### Logic Errors

* Check order of operations in code.
    * Does something need parenthesis?

