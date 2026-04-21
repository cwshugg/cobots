---
name: "makefile"
description: "GNU Make best practices for writing clean and maintainable Makefiles"
applyTo: "**/Makefile,**/makefile,**/*.mk"
---

<!--
Adapted from the awesome-copilot project:

https://github.com/github/awesome-copilot/blob/main/instructions/makefile.instructions.md

The original is available at the URL above. This version has been adapted to
match the cobots instruction style.
- Scribs
-->

# Makefile Best Practices

Follow these guidelines when writing GNU Make Makefiles. These instructions are based on the [GNU Make manual](https://www.gnu.org/software/make/manual/).

## General Principles

* Use descriptive target names that clearly indicate their purpose.
* Keep the default goal (first target) as the most common build operation.
* Prioritize readability over brevity when writing rules and recipes.
* Add comments to explain complex rules, variables, or non-obvious behavior.

## Naming Conventions

* Name your makefile `Makefile` (recommended for visibility) or `makefile`.
* Use `GNUmakefile` only for GNU Make-specific features incompatible with other `make` implementations.
* Use uppercase for built-in variable names (e.g., `CC`, `CFLAGS`, `LDFLAGS`).
* Use descriptive target names that reflect their action (e.g., `clean`, `install`, `test`).

## File Structure

* Place the default goal (primary build target) as the first rule.
* Define variables at the top of the makefile before rules.
* Group related targets together logically.
* Use `.PHONY` to declare targets that don't represent files.
* Structure makefiles as: variables → rules → phony targets.

```makefile
# Variables
CC = gcc
CFLAGS = -Wall -g
objects = main.o utils.o

# Default goal
all: program

# Rules
program: $(objects)
	$(CC) -o program $(objects)

%.o: %.c
	$(CC) $(CFLAGS) -c $< -o $@

# Phony targets
.PHONY: clean all
clean:
	rm -f program $(objects)
```

## Variables

* Use variables to avoid duplication and improve maintainability.
* Use `:=` (simple expansion) for immediate evaluation; `=` for recursive expansion.
* Use `?=` to set default values that can be overridden from the command line.
* Use `+=` to append to existing variables.
* Reference variables with `$(VARIABLE)`, not `$VARIABLE` (unless single character).
* Use automatic variables (`$@`, `$<`, `$^`, `$?`, `$*`) in recipes to keep rules generic.

```makefile
# Simple expansion (evaluates immediately)
CC := gcc

# Recursive expansion (evaluates when used)
CFLAGS = -Wall $(EXTRA_FLAGS)

# Conditional assignment (set only if not already defined)
PREFIX ?= /usr/local

# Append
CFLAGS += -g
```

## Rules and Prerequisites

* List prerequisites in logical order (normal prerequisites before order-only).
* Use order-only prerequisites (after `|`) for directories that should not trigger rebuilds.
* Include all actual dependencies to ensure correct rebuilds.
* Avoid circular dependencies between targets.

```makefile
# Order-only prerequisite for directory creation
obj/%.o: %.c | obj
	$(CC) $(CFLAGS) -c $< -o $@

obj:
	mkdir -p obj
```

## Recipes

* Start every recipe line with a **tab character** (not spaces).
* Use `@` prefix to suppress command echoing when appropriate.
* Use `-` prefix to ignore errors for specific commands (use sparingly).
* Break long commands across multiple lines with backslash continuation (`\`).

```makefile
clean:
	@echo "Cleaning up..."
	@rm -f $(objects)

install: program
	install -d $(PREFIX)/bin && \
		install -m 755 program $(PREFIX)/bin
```

## Phony Targets

* Always declare phony targets with `.PHONY` to avoid conflicts with files of the same name.
* Use phony targets for actions like `clean`, `install`, `test`, `all`.

```makefile
.PHONY: all clean test install

all: program

clean:
	rm -f program $(objects)

test: program
	./run-tests.sh

install: program
	install -m 755 program $(PREFIX)/bin
```

## Pattern Rules

* Use pattern rules (`%.o: %.c`) for generic transformations.
* Leverage built-in implicit rules when appropriate (GNU Make knows how to compile `.c` to `.o`).
* Override implicit rule variables (`CC`, `CFLAGS`) rather than rewriting the rules.

```makefile
# Custom pattern rule
%.pdf: %.md
	pandoc $< -o $@
```

## Automatic Dependencies

* Generate header dependencies automatically rather than maintaining them manually.
* Use compiler flags like `-MMD` and `-MP` to generate `.d` files.
* Include generated dependency files with `-include`.

```makefile
objects = main.o utils.o
deps = $(objects:.o=.d)

-include $(deps)

%.o: %.c
	$(CC) $(CFLAGS) -MMD -MP -c $< -o $@
```

## Conditional Directives

* Use `ifeq`, `ifneq`, `ifdef`, and `ifndef` for platform or configuration-specific rules.
* Place conditionals at the makefile level, not within recipes (use shell conditionals in recipes).

```makefile
ifeq ($(OS),Windows_NT)
    EXE_EXT = .exe
else
    EXE_EXT =
endif
```

## Error Handling and Debugging

* Use `$(error text)` or `$(warning text)` for build-time diagnostics.
* Validate required variables and tools at the top of the makefile.
* Test makefiles with `make -n` (dry run) to preview commands without executing them.

```makefile
ifeq ($(shell which gcc),)
    $(error "gcc is not installed or not in PATH")
endif

ifndef VERSION
    $(error VERSION is not defined)
endif
```

## Clean Targets

* Always provide a `clean` target to remove generated files.
* Consider separate `clean` (removes build artifacts) and `distclean` (removes all generated files) targets.

```makefile
.PHONY: clean distclean

clean:
	-rm -f $(objects) $(deps)

distclean: clean
	-rm -f program config.mk
```

## Documentation

* Add a header comment explaining the makefile's purpose and usage.
* Document non-obvious variable settings.

```makefile
# Makefile for building the example application
#
# Usage:
#   make          - Build the program
#   make clean    - Remove generated files
#   make install  - Install to $(PREFIX)
#
# Variables:
#   CC       - C compiler (default: gcc)
#   PREFIX   - Installation prefix (default: /usr/local)
```

## Patterns to Avoid

* Don't start recipe lines with spaces instead of tabs.
* Don't use `$(shell ls ...)` to get file lists — use `$(wildcard ...)` instead.
* Don't forget to declare phony targets with `.PHONY`.
* Avoid complex shell scripts in recipes — move them to separate script files.
* Avoid recursive make (`$(MAKE) -C subdir`) unless absolutely necessary.
* Don't hardcode file lists when they can be generated with wildcards or functions.
