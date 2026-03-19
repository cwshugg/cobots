# shuggbots

This repository contains the AI-based tools I've written and collected.
This is primarily intended to be used with GitHub Copilot or other AI-assisted coding agent tools.

## TODOs

Instructions to create:

* General coding best practices

Agents to create:

* (DONE) **Architect:** Sole purpose is to create a design document for the project (writes *zero* code)
* (DONE) **Coder:** Sole purpose is to to write code and tests. The coder implements the design plan
* (DONE) **Scrutinizer:** Sole purpose is to argue why existing design/implementation is not good
* (DONE) **Documenter:** Sole purpose is to examine code and write documentation
* **Security Expert:** Works with the architect and coder to ensure security is upheld in system design and implementation
* **Planner:** Sole purpose is to come up with a plan of operation for all the other bots to follow.
    * The planner should set up a list of steps to carry out:
        * *Interview* - A bot interviews the human to get clarifying details
        * *Discuss* - Two or more bots should discuss with each other
        * *Implement* - A bot implements
    * Description of the planner should also include an overall process to follow. Ex:
        1. First interview the human to get idea of requirements
        2. Have the architect draft a design
        3. Have the architect, the basher, etc., discuss and refine the design
        4. Interview the human; human reviews design and makes changes
        5. ...

NOTE - I want each of these agents to always output their intermediate discussions/results in a common datetime format: `YYYY-MM-DD_HH-MM-SS_basher_report.md`. This should be written out in a `.instructions.md` file.

## Resources

* [Awesome GitHub Copilot](https://awesome-copilot.github.com/) - A collection of agents, skills, instructions, etc.
* [How to write a great `agents.md`](https://github.blog/ai-and-ml/github-copilot/how-to-write-a-great-agents-md-lessons-from-over-2500-repositories/)

