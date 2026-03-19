---
name: "markdown"
description: "Best practices for writing markdown files"
applyTo: "**/*.md"
---

# Best Practices for Markdown

## Markdown Styling

Use headings to separate sections of content.
Please only use a single H1 heading (`# Example`) at the very top of each file to denote the title of the document.
Sub-headers should nest, such that H2s are below the H1, and H3s are below H2s (and so on).
Example:

```markdown
# Document Title

(text)

## Section 1

(text)

### Section 1a

(text)
```

Always leave an empty line before and after headers.
Example:

```markdown
Text

# Example Header

More text
```

When writing code blocks, make sure to annotate each code block to support syntax highlighting when possible.
Example:

```python
def func():
    return 1
```

If there is ever a need to leave invisible comments in the markdown documentation, please use HTML-style comments.
Example:

```markdown
<!-- One-line comment -->

<!--
Multi-line comment.
Useful for longer explanations or comments.
-->
```

Make liberal use of backticks to format variable names, function names, file names, and other code-like strings that should stand out from normal text.
Example:

```markdown
* For tests, see the `tests/` folder.
* Look for any functions that begin with `test_*`
```

When writing unordered lists, please use `*` as the bullet character, and use 4 spaces to indent.
Example:

```markdown
* Item 1
    * Item 1a
    * Item 1b
* Item 2
```

When writing ordered lists, please use individual numbers as the bullet character, and use 4 spaces to indent.
Example:

```markdown
1. Item 1
2. Item 2
```

Make use of links to point the reader to other, nearby documents that can be accessed via *relative path notation*.
Example:

```markdown
For more information see [this document](../overview.md).
```

