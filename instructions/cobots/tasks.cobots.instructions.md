---
name: "cobots_tasks"
description: "A primer on creating and managing cobots tasks"
applyTo: "**/*.cobots.agent.md"
---

**Tasks** are the primary way to track and document work.
As a cobot, you must track *every action* that you take.
For example, actions can be:

* Drafting a design
* Implementing code
* Fixing a bug
* Adjusting code/docs based on a request
* Refactoring code
* Cleaning up old code
* Linting/formatting code

Please follow these rules

## Managing Tasks

Please use the cobots tasks CLI skill to create, list, view, update, link, etc., tasks.
If you are creating the task, please specify your name as the author.

## Rules of Task Tracking

Please follow these rules when working with tasks:

### 1. Document Before Working

*Always* create a new task before you start working on it.

### 2. Update Your Progress

As you continue to work on the task, please share updates by adding to the task's discussion.
Use the cobots tasks CLI to add to the task discussion.

Additionally, when the task has reached a new status, please set the task's status accordingly.
(See the tasks CLI to understand what statuses are available.)

### 3. Never Delete Tasks

Never delete a task.
If a task is no longer to be completed, please update the status instead of deleting the file.

### 4. One at a Time

Please only work on a single task at a time.
Work on the task until its completion.

If you encounter a new problem to solve, please create another task to represent this new problem, and link it to the current task.
Then, update the current task's status, and the new one's, to reflect that you are now working on the new task.
Once the sub-task is complete, return to the original.

