---
name: "coding"
description: "Best practices for programming in any language"
applyTo: "**"
---

# Best Practices when Coding

This file describes a collection of best practices to follow when writing code.

## Code Quality and Structure

### Reuse Code

Do you see the same piece(s) of identical (or very similar) code being copy-pasted or repeated?
If so, the code should, in almost every case, be consolidated into a helper function or macro (function is preferred in most cases).

### Use If-Return Structure

When possible, make sure the author uses a code structure similar to this to handle error cases or situations where a function can be broken out of early:

```python
def validate_value(value: any) -> bool:
    if bypass_validation:
        return False

    if is_error(value):
        return False

    # Call main validation function:
    return validate(value)
```

This coding structure reduces complexity in the code, gives it a flatter logic structure, and makes it much more readable.

<!--
TODO - Add more code structure/quality advice!
-->

## Code Testing

Ensure that all new or modified features have an appropriate unit test.

## Comments and In-Code Documentation

Please comment the code following these guidelines:

* The following should have comments attached to them such that an onlooker completely unfamiliar with the code can understand their purpose:
    * All functions
    * All data structures, enums, and other objects
    * All source code files (each file should have a brief header describing the code it contains)
    * All global-scope, file-scope, etc., definitions of consts and other values
* When necessary, reference other functions or files in your comments by specifying their exact names within backticks (ex: `function_name`).
* Future areas of improvement should be documented.

## Code Style

* Unless the changes are the first in a brand new project, ensure that the new changes conform to the existing code style.
* Keep a consistent coding style throughout your changes.
* Depending on the language you're working with, there may be linting or formatting configurations set in the project.
    * Look for these, and execute them to format and check for formatting errors while making changes.
    * A few examples:
        * In Rust, `cargo fmt` is typically used to format code.
* There should be a consistent between tabs and spaces in the file.
    * Use the existing style if you are making changes to an existing project.
    * If this is a new project, please default to using 4 spaces as indentation.

## Code Semantics

* If semantic-checking tools are available for the language you are developing, please execute these to check your work for semantic errors.
    * If semantic errors are found, please correct them.
* A few examples:
    * In Rust, `cargo clippy` is typically used to format code.

