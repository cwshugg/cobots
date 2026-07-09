---
name: "coding"
description: "Best practices for programming in any language"
applyTo: "**"
---

# Best Practices when Coding

This file describes a collection of best practices to follow when writing code.

## Code Quality and Structure

### General Principles

* Readability counts.
* Explicit is better than implicit.
* Simple is better than complex.
* Code is read more often than it’s written.

### Reuse Code

Do you see the same piece(s) of identical (or very similar) code being copy-pasted or repeated?
If so, the code should, in almost every case, be consolidated into a helper function or macro (function is preferred in most cases).

### Use If-Return Structure ("Fail Fast")

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

### Always Define Values - Never Hard-code

In almost every scenario where a constant value (file-scope, global-scope, etc.) is used, such as a string immediate, magic value, or specific integer, *define it as a variable, or macro*.
For example, in C, if a specific string value is used in production code:

```c
const int MAGIC_VALUE = 0xabcd1234;
const char MAGIC_STRING[] = "MY_MAGIC_STRING";

int main()
{
    // Do NOT hardcode these values:
    my_func(0xabcd1234, "MY_MAGIC_STRING");

    // Instead, use appropriately-scoped definitions:
    my_func(MAGIC_VALUE, MAGIC_STRING);
}
```

<!--
TODO - Add more code structure/quality advice!
-->

## Code Testing

Ensure that all new or modified features have an appropriate unit test.

For detailed testing guidelines, see [testing.instructions.md](./testing.instructions.md).

## Warnings & Errors

When building code, please treat all warnings and errors as signals, not noise.
Finalized code should build without a *single* compiler warning or error.

## Comments and In-Code Documentation

Please comment the code following these guidelines:

* The following should have comments attached to them such that an onlooker completely unfamiliar with the code can understand their purpose:
    * All functions
    * All data structures, enums, and other objects
    * All source code files (each file should have a brief header describing the code it contains)
    * All global-scope, file-scope, etc., definitions of consts and other values
* When necessary, reference other functions or files in your comments by specifying their exact names within backticks (ex: `function_name`).
* Future areas of improvement should be documented.

Things you must avoid while writing comments:

* You must have absolutely *zero* mentions of people, other agents, cobots task IDs, references to code review feedback points, or *any* other metadata that is in your context during the development process (unless explicitly asked to).
    * **Examples of what to avoid:**
        * `// This function now accepts an additional parameter (Code Review - 1.3a)`
        * `// This constant is used below and replaces a previously hard-coded value (P6)`
        * `// - Written by Byteboy`
        * `// This function was changed to do ... as requested by Connor`
* You must have absolutely *zero* references the previous state of the code.
  You do not need to explain the reasoning or the differences between the current state versus the old state.
    * The goal with commenting is to describe *the code*, only in its *current state*.

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

## Security

For detailed secure coding standards, see [security.instructions.md](./security.instructions.md).

* Never hardcode secrets; use environment variables or secure stores.
* Validate all external input.
* Keep dependencies up to date.

