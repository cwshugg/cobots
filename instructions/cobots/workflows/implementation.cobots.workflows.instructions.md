---
name: "cobots_workflows_implementation"
description: "The 'implementation' workflow."
applyTo: "**/*.cobots.agent.md"
---

The code implementation workflow should begin after an architecture or design report has been created.

## Task Structure

Use the following structure of tasks to accomplish this workflow:

| Task Number | Task Name | Task Owner | Notes |
|-------------|-----------|------------|-------|
| 1 | Review Architecture Report | Developer | The developer should examine the architecture report and become familiar with it. |
| 2 | Implement Architecture | Developer | Depends on 1; the developer should implement the architecture, write tests, and ensure it is working. |
| 3 | Review Implementation | Scrutinizer | Depends on 2; once the developer is finished, the scrutinizer should perform a full code review and generate a review report containing feedback. |
| 4 | Address Review Feedback | Scrutinizer | Depends on 3; the developer should address the scrutinizer's review by implementing fixes and addressing issues. |

**Note:** steps 3-4 should be repeated as many times as needed until the scrutinizer believes the implementation is in a good state.
Individual tasks should be created for each round of review+address.

